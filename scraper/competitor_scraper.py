
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# ── Ensure local packages are importable ─────────────────────────────────────
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bs4 import BeautifulSoup

from platform_detector import detect_platform
from extractors.jsonld_extractor import extract_from_jsonld
from extractors.generic_extractor import (
    extract_opengraph,
    extract_heuristic,
    extract_reviews_heuristic,
    extract_price_regex_fallback,
)


# ── Optional stealth import (soft dependency) ──────────────────────────────
try:
    from playwright_stealth import stealth_async as _stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False


# ─────────────────────────────────────────────────────────────────────────────
# Requests-based fast fetch (used for Croma, generic sites, and as pre-check)
# ─────────────────────────────────────────────────────────────────────────────

_BLOCKED_SIGNALS = [
    "access denied", "robot check", "captcha", "are you a human",
    "just a moment", "403 forbidden", "enable javascript",
    "checking your browser", "please wait",
]

def _is_blocked(html: str, status: int = 200) -> bool:
    """Return True if the response looks like a bot block page."""
    if status in (403, 429, 503, 401):
        return True
    if not html or len(html) < 1500:
        return True
    snippet = html.lower()[:3000]
    return any(sig in snippet for sig in _BLOCKED_SIGNALS)


def _fetch_curl_cffi(url: str) -> str:
    """
    Layer 1: curl_cffi — impersonates real Chrome TLS fingerprint (JA3/JA4).
    This is the most effective method against Cloudflare.
    Install: pip install curl_cffi
    """
    try:
        from curl_cffi import requests as cffi_req
        import time, random as _rand
        time.sleep(_rand.uniform(0.3, 0.8))
        resp = cffi_req.get(
            url,
            impersonate="chrome124",   # exact Chrome 124 TLS fingerprint
            headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Referer": "https://www.google.com/",
            },
            timeout=20,
            allow_redirects=True,
        )
        html = resp.text
        if not _is_blocked(html, resp.status_code):
            print("[INFO] curl_cffi fetch succeeded", file=sys.stderr)
            return html
    except ImportError:
        pass   # not installed — silently skip
    except Exception as e:
        print(f"[INFO] curl_cffi failed: {e}", file=sys.stderr)
    return ""


def _fetch_cloudscraper(url: str) -> str:
    """
    Layer 2: cloudscraper — solves Cloudflare JS challenges.
    Install: pip install cloudscraper
    """
    try:
        import cloudscraper as _cs
        import time, random as _rand
        time.sleep(_rand.uniform(0.5, 1.0))
        scraper = _cs.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        resp = scraper.get(url, timeout=25)
        html = resp.text
        if not _is_blocked(html, resp.status_code):
            print("[INFO] cloudscraper fetch succeeded", file=sys.stderr)
            return html
    except ImportError:
        pass
    except Exception as e:
        print(f"[INFO] cloudscraper failed: {e}", file=sys.stderr)
    return ""


def _fetch_with_requests(url: str) -> str:
    """
    Layer 3: plain requests with full browser headers. Works for sites with
    basic bot protection (not Cloudflare JS challenge).
    """
    try:
        import requests as _req
        import time, random as _rand
        time.sleep(_rand.uniform(0.5, 1.2))
        headers = {
            "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language":           "en-IN,en;q=0.9",
            "Accept-Encoding":           "gzip, deflate, br",
            "Referer":                   "https://www.google.com/",
            "DNT":                       "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest":            "document",
            "Sec-Fetch-Mode":            "navigate",
            "Sec-Fetch-Site":            "cross-site",
            "Cache-Control":             "max-age=0",
        }
        resp = _req.get(url, headers=headers, timeout=20, allow_redirects=True)
        html = resp.text
        if not _is_blocked(html, resp.status_code):
            return html
    except Exception as e:
        print(f"[INFO] requests fetch failed: {e}", file=sys.stderr)
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Browser helper
# ─────────────────────────────────────────────────────────────────────────────

# Rotate through several realistic user-agent strings
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Realistic viewport sizes
_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
]


async def _fetch_page(url: str) -> str:
    """
    Launch a stealth Playwright Chromium browser, navigate to `url`, wait for
    dynamic content to settle, and return the rendered HTML.
    """
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout

    ua = random.choice(_USER_AGENTS)
    vp = random.choice(_VIEWPORTS)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--flag-switches-begin",
                "--disable-site-isolation-trials",
                "--flag-switches-end",
                # Reduce automation fingerprint
                "--disable-automation",
                "--password-store=basic",
                "--use-mock-keychain",
            ],
        )
        context = await browser.new_context(
            user_agent=ua,
            viewport=vp,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            # Accept common cookie consent automatically
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "DNT":             "1",
            },
        )

        # Add storage state to look like a returning visitor
        page = await context.new_page()

        # Apply stealth patches if available
        if HAS_STEALTH:
            await _stealth(page)

        # Patch all common headless browser fingerprint leaks
        await page.add_init_script("""
            // Core webdriver flag
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Plugins — real Chrome has 3+
            Object.defineProperty(navigator, 'plugins', {get: () => [
                {name:'Chrome PDF Plugin'},{name:'Chrome PDF Viewer'},{name:'Native Client'}
            ]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-IN', 'en-US', 'en']});
            // Chrome runtime object
            window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
            // Permissions API
            const origQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (params) =>
                params.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : origQuery(params);
            // Remove automation-related properties
            delete navigator.__proto__.webdriver;
            // Canvas fingerprint noise (slight randomisation)
            const origGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {
                const ctx = origGetContext.call(this, type, ...args);
                if (type === '2d' && ctx) {
                    const orig = ctx.getImageData;
                    ctx.getImageData = function(...a) {
                        const d = orig.apply(this, a);
                        d.data[0] = d.data[0] ^ 1;  // 1-bit noise
                        return d;
                    };
                }
                return ctx;
            };
        """)

        html = ""
        try:
            print(f"[INFO] Navigating to: {url}", file=sys.stderr)
            # Croma needs networkidle wait to fully render React SSR content
            platform = detect_platform(url)
            wait_event = "networkidle" if platform in ("croma", "reliancedigital") else "domcontentloaded"
            await page.goto(url, wait_until=wait_event, timeout=50_000)

            # Human-like pause — longer for sites with aggressive bot detection
            delay = random.uniform(2.5, 4.0) if platform in ("croma", "reliancedigital") else random.uniform(1.5, 3.0)
            await asyncio.sleep(delay)

            # Scroll a bit to trigger lazy-loading
            await page.evaluate("window.scrollBy(0, window.innerHeight * 0.6)")
            await asyncio.sleep(random.uniform(0.8, 1.5))

            # Wait for a meaningful selector on each platform (best-effort)
            selectors_to_wait = {
                "amazon":          "#productTitle",
                "flipkart":        "h1",          # B_NuCI is old; h1 always present
                "croma":           "h1.pd-title, h1[class*='title'], h1",
                "reliancedigital": "h1",
                "generic":         "h1",
            }
            wait_sel = selectors_to_wait.get(platform, "h1")
            try:
                await page.wait_for_selector(wait_sel, timeout=12_000)
            except PWTimeout:
                print(f"[WARN] Timeout waiting for '{wait_sel}', using page as-is", file=sys.stderr)

            html = await page.content()
        except Exception as exc:
            print(f"[ERROR] Playwright navigation failed: {exc}", file=sys.stderr)
        finally:
            await browser.close()

    return html


# ─────────────────────────────────────────────────────────────────────────────
# Platform adapter dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _run_platform_extractor(platform: str, soup) -> dict:
    """
    Dynamically import and run the platform-specific adapter if it exists.
    Returns an empty dict if no adapter is found or if it raises.
    """
    adapter_map = {
        "amazon":          "extractors.platforms.amazon",
        "flipkart":        "extractors.platforms.flipkart",
        "croma":           "extractors.platforms.croma",
        "reliancedigital": "extractors.platforms.croma",   # shared adapter
    }
    module_path = adapter_map.get(platform)
    if not module_path:
        return {}
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return mod.extract(soup)
    except Exception as exc:
        print(f"[WARN] Platform extractor '{platform}' failed: {exc}", file=sys.stderr)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Result merger
# ─────────────────────────────────────────────────────────────────────────────

def _merge(base: dict, patch: dict) -> dict:
    """
    Merge `patch` into `base`, only filling keys that are None / missing.
    """
    for key, value in patch.items():
        if value is None:
            continue
        if key not in base or base[key] is None:
            base[key] = value
    return base


# ─────────────────────────────────────────────────────────────────────────────
# Main extraction pipeline
# ─────────────────────────────────────────────────────────────────────────────

def extract_product(html: str, url: str) -> dict:
    """
    Run the full extraction pipeline on rendered HTML.
    Returns the normalised product dict.
    """
    soup = BeautifulSoup(html, "lxml")
    platform = detect_platform(url)

    # Initialise schema with all fields as None
    result: dict = {
        "platform":     platform,
        "url":          url,
        "product_name": None,
        "price":        None,
        "discount":     None,
        "rating":       None,
        "rating_count": None,
        "delivery_days": None,
        "delivery_text": None,
        "reviews":      None,
        "availability": None,
    }

    # ── 1. JSON-LD (highest fidelity) ────────────────────────────────────────
    print("[INFO] Trying JSON-LD extraction …", file=sys.stderr)
    jsonld_data = extract_from_jsonld(soup)
    _merge(result, jsonld_data)

    # ── 2. Platform-specific adapter ─────────────────────────────────────────
    print(f"[INFO] Trying platform adapter: {platform} …", file=sys.stderr)
    platform_data = _run_platform_extractor(platform, soup)
    _merge(result, platform_data)

    # ── 3. OpenGraph meta tags ───────────────────────────────────────────────
    print("[INFO] Trying OpenGraph extraction …", file=sys.stderr)
    og_data = extract_opengraph(soup)
    _merge(result, og_data)

    # ── 4. Generic heuristic selectors ───────────────────────────────────────
    print("[INFO] Trying generic heuristic extraction …", file=sys.stderr)
    generic_data = extract_heuristic(soup)
    _merge(result, generic_data)

    # ── 5. Generic review extraction ─────────────────────────────────────────
    if not result.get("reviews"):
        reviews = extract_reviews_heuristic(soup)
        if reviews:
            result["reviews"] = reviews

    # ── 6. Regex price fallback ───────────────────────────────────────────────
    if not result.get("price"):
        print("[INFO] Trying regex price fallback …", file=sys.stderr)
        result["price"] = extract_price_regex_fallback(soup)

    # ── Captcha / block detection ─────────────────────────────────────────────
    page_text = soup.get_text().lower()
    captcha_signals = ["robot check", "captcha", "are you a human", "access denied",
                       "unusual traffic", "verify you are human", "cloudflare"]
    if any(sig in page_text for sig in captcha_signals) and not result.get("product_name"):
        result["_error"] = "Possible CAPTCHA or bot-block detected. Try a residential proxy."

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Flipkart review page helper
# ─────────────────────────────────────────────────────────────────────────────

def _flipkart_reviews_url(product_url: str) -> str | None:
    """
    Convert a Flipkart product URL to its reviews sub-page URL.
    e.g. /vivo-t3.../p/itmXXX?pid=YYY  →  /vivo-t3.../product-reviews/itmXXX?pid=YYY
    """
    import re
    m = re.search(r'(flipkart\.com)(/[^?]+)/p/(\w+)(.*)', product_url)
    if m:
        return f"https://www.{m.group(1)}{m.group(2)}/product-reviews/{m.group(3)}{m.group(4)}"
    return None


def _extract_flipkart_reviews(html: str) -> list[dict]:
    """Parse up to 3 reviews from a Flipkart product-reviews page."""
    from utils.text_cleaner import clean_text, to_float
    soup = BeautifulSoup(html, "lxml")
    reviews = []

    # All known review container selectors across Flipkart redesigns
    CONTAINERS = [
        "div.RcXBOT", "div._3BSf6", "div.col.EPCmJX",
        "div._27M-vq", "[class*='review-container']",
    ]
    BODY_SELS    = ["div.ZmyHeo", "div.t-ZTKy", "div._6K-7Co", "p._2-N8zT", "p"]
    AUTHOR_SELS  = ["p.s2U1AS", "p._2sc7ZR", "span._1WkVV5", "[class*='author']"]
    RATING_SELS  = ["div.XQDdHH", "div._3LWZlK", "div.ipqd2A"]

    containers = []
    for sel in CONTAINERS:
        try:
            containers = soup.select(sel)
            if containers:
                break
        except Exception:
            continue

    for rev in containers[:3]:
        body = author = rating = None
        for sel in BODY_SELS:
            try:
                t = rev.select_one(sel)
                if t:
                    txt = clean_text(t.get_text())
                    if txt and len(txt) > 10:
                        body = txt
                        break
            except Exception:
                continue
        for sel in AUTHOR_SELS:
            try:
                t = rev.select_one(sel)
                if t:
                    author = clean_text(t.get_text())
                    break
            except Exception:
                continue
        for sel in RATING_SELS:
            try:
                t = rev.select_one(sel)
                if t:
                    v = to_float(t.get_text())
                    if v and 1.0 <= v <= 5.0:
                        rating = v
                        break
            except Exception:
                continue
        if body or author:
            reviews.append({"author": author, "rating": rating, "body": body})

    return reviews


# ─────────────────────────────────────────────────────────────────────────────
# Scrape a single URL — shared by both CLI and interactive modes
# ─────────────────────────────────────────────────────────────────────────────

def scrape_url(url: str) -> None:
    """Fetch, extract, and print JSON for one URL."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        print(f"[ERROR] Invalid URL: {url!r}  (include https://)")
        return

    platform = detect_platform(url)
    html = ""

    # ── Layer 1: curl_cffi — best Cloudflare bypass (TLS fingerprint) ─────────
    if platform in ("croma", "reliancedigital", "generic"):
        html = _fetch_curl_cffi(url)

    # ── Layer 2: cloudscraper — solves JS challenges ───────────────────────
    if not html and platform in ("croma", "reliancedigital", "generic"):
        print(f"[INFO] Trying cloudscraper for {platform} …", file=sys.stderr)
        html = _fetch_cloudscraper(url)

    # ── Layer 3: plain requests — fast, works for non-Cloudflare sites ────
    if not html and platform in ("croma", "reliancedigital", "generic"):
        print(f"[INFO] Trying requests fetch for {platform} …", file=sys.stderr)
        html = _fetch_with_requests(url)
        if html:
            print(f"[INFO] requests fetch succeeded ({len(html):,} bytes)", file=sys.stderr)

    # ── Layer 4: Playwright — full browser, handles any JS rendering ───────
    if not html:
        html = asyncio.run(_fetch_page(url))

    if not html or len(html) < 500:
        print("[ERROR] Received empty or too-short HTML. The site may have blocked the request.",
              file=sys.stderr)
        html = html or "<html></html>"

    product = extract_product(html, url)

    # ── Flipkart: fetch reviews from separate reviews sub-page ───────────────
    if product.get("platform") == "flipkart" and not product.get("reviews"):
        reviews_url = _flipkart_reviews_url(url)
        if reviews_url:
            print("[INFO] Fetching Flipkart reviews page …", file=sys.stderr)
            rev_html = asyncio.run(_fetch_page(reviews_url))
            if rev_html and len(rev_html) > 500:
                reviews = _extract_flipkart_reviews(rev_html)
                if reviews:
                    product["reviews"] = reviews

    print(json.dumps(product, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── If a URL was passed on the command line, use it and exit ────────────
    if len(sys.argv) >= 2:
        scrape_url(sys.argv[1].strip())
        return

    # ── Otherwise enter interactive loop ────────────────────────────────────
    print("╔══════════════════════════════════════════════════════╗")
    print("║      Universal E-Commerce Product Scraper            ║")
    print("║  Paste any product URL and press Enter to scrape.    ║")
    print("║  Type  q  or  exit  to quit.                         ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    while True:
        try:
            url = input("🔗 Product URL: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Bye!]")
            break

        if not url:
            continue
        if url.lower() in ("q", "quit", "exit"):
            print("[Bye!]")
            break

        scrape_url(url)
        print()   # blank line between results


if __name__ == "__main__":
    main()