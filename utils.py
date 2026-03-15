# utils.py — Shared utilities for ByteFlow Mart

import json
import os
import re
from datetime import datetime, timedelta

DATA_DIR = "data"


# ─── JSON I/O ────────────────────────────────────────────────────────────────

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Product Matching ────────────────────────────────────────────────────────

def match_competitor(product_name, attributes, compe_data):
    """
    Match a product name + attributes against competitor JSON.
    Returns list of competitor match dicts.
    """
    name_lower = product_name.lower()
    attr_values = [str(v).lower() for v in attributes.values()] if attributes else []

    results = []
    for match in compe_data.get("matches", []):
        cname = match.get("our_product_name", "").lower()
        score = 0

        # Token overlap on product name
        name_tokens = set(re.split(r'\W+', name_lower))
        comp_tokens = set(re.split(r'\W+', cname))
        overlap = name_tokens & comp_tokens
        if len(overlap) >= 2:
            score += len(overlap)

        # Attribute overlap
        for attr in attr_values:
            if attr in cname:
                score += 1

        if score >= 2:
            results.append({
                "match": match,
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return [r["match"] for r in results[:3]]


# ─── Price Strategy ──────────────────────────────────────────────────────────

def suggest_price_strategy(our_price, matched_compe):
    """Suggest competitive price and discount based on competitor data."""
    if not matched_compe:
        return our_price, 10

    all_compe_prices = []
    for match in matched_compe:
        for c in match.get("competitors", []):
            all_compe_prices.append(c.get("price", 0))

    if not all_compe_prices:
        return our_price, 10

    min_comp = min(all_compe_prices)
    avg_comp = sum(all_compe_prices) / len(all_compe_prices)

    # Beat lowest by ₹100–₹500 based on range
    suggested_price = max(int(min_comp - 200), int(avg_comp * 0.97))

    # Compute discount vs original_price if available
    original = matched_compe[0].get("competitors", [{}])[0].get("original_price", suggested_price * 1.15)
    if original > 0:
        discount = round(((original - suggested_price) / original) * 100)
        discount = max(5, min(discount, 35))
    else:
        discount = 12

    return suggested_price, discount


# ─── Delivery Estimation ─────────────────────────────────────────────────────

ZONE_MAP = {
    # (seller_state, buyer_state): days
    ("Karnataka", "Karnataka"): 1,
    ("Karnataka", "Tamil Nadu"): 2,
    ("Karnataka", "Andhra Pradesh"): 2,
    ("Karnataka", "Kerala"): 2,
    ("Karnataka", "Telangana"): 2,
    ("Karnataka", "Maharashtra"): 3,
    ("Karnataka", "Goa"): 2,
}

DEFAULT_INTER_STATE = 4
DEFAULT_SAME_STATE = 2
DEFAULT_FAR = 6


def estimate_delivery(seller_state, buyer_state, seller_pincode, buyer_pincode):
    """Estimate delivery days based on seller and buyer location."""
    if seller_state == buyer_state:
        base_days = DEFAULT_SAME_STATE
    else:
        key = (seller_state, buyer_state)
        base_days = ZONE_MAP.get(key, DEFAULT_INTER_STATE)

    # Add 1 day buffer for distant pincodes (rough heuristic)
    try:
        pin_diff = abs(int(str(seller_pincode)[:3]) - int(str(buyer_pincode)[:3]))
        if pin_diff > 200:
            base_days += 1
    except Exception:
        pass

    delivery_date = datetime.now() + timedelta(days=base_days)
    return base_days, delivery_date.strftime("%a, %d %b %Y")


# ─── Change Detection ────────────────────────────────────────────────────────

def detect_product_changes(product, compe_data):
    """
    Compare current competitor prices vs last_checked snapshot.
    Returns list of change dicts.
    """
    changes = []
    matched = match_competitor(
        product.get("search_query", product["product_name"]),
        product.get("attributes", {}),
        compe_data
    )

    for match in matched:
        for comp in match.get("competitors", []):
            # Simulate change detection by comparing with stored our_price gap
            comp_price = comp.get("price", 0)
            our_price = product.get("our_price", 0)
            comp_discount = comp.get("discount", 0)

            if comp_price > 0 and our_price > comp_price + 500:
                changes.append({
                    "platform": comp["platform"],
                    "type": "price_undercut",
                    "message": f"Competitor {comp['platform']} is ₹{our_price - comp_price:,} cheaper",
                    "old_value": our_price,
                    "new_value": comp_price,
                    "severity": "high"
                })
            elif comp_discount > product.get("discount", 0) + 5:
                changes.append({
                    "platform": comp["platform"],
                    "type": "discount_change",
                    "message": f"{comp['platform']} increased discount to {comp_discount}% (ours: {product.get('discount', 0)}%)",
                    "old_value": product.get("discount", 0),
                    "new_value": comp_discount,
                    "severity": "medium"
                })

    return changes


# ─── Bundle Lookup ───────────────────────────────────────────────────────────

def get_bundles_for_product(product_id, product_name):
    """Find bundle items matching a product."""
    try:
        bundle_data = load_json("bundles.json")
        name_lower = product_name.lower()
        for bundle in bundle_data.get("bundles", []):
            if bundle["trigger_product_id"] == product_id:
                return bundle["bundle_items"]
            for kw in bundle.get("trigger_keywords", []):
                if kw.lower() in name_lower:
                    return bundle["bundle_items"]
    except Exception:
        pass
    return []


# ─── AI via Ollama ───────────────────────────────────────────────────────────

def _strip_markdown(text):
    """Remove all markdown formatting so the UI always receives clean plain text."""
    import re
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)          # bold / italic
    text = re.sub(r"`+([^`]*)`+", r"\1", text)                   # inline code
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)   # headings
    text = re.sub(r"^[-_*]{3,}\s*$", "", text, flags=re.MULTILINE)  # hr
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)  # unordered list
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE) # numbered list
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def call_ollama(prompt, timeout=120):
    """Call local Ollama LLM. Returns clean plain-text response (markdown stripped)."""
    import requests
    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "qcwind/qwen3-8b-instruct-Q4-K-M"
    try:
        r = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=timeout)
        if r.status_code == 200:
            raw = r.json().get("response", "No response from model.")
            return _strip_markdown(raw)
        return "LLM service returned an error. Please ensure Ollama is running."
    except requests.exceptions.ConnectionError:
        return "Unable to reach Ollama. Run 'ollama serve' and ensure the model is loaded."
    except Exception as e:
        return f"Unexpected error while calling LLM: {e}"


def generate_title_description(product_name, attributes):
    """Use LLM to generate product title and description."""
    attr_str = ", ".join([f"{k}: {v}" for k, v in attributes.items()]) if attributes else ""
    prompt = f"""You are an expert e-commerce product copywriter for an Indian marketplace.

Product: {product_name}
Attributes: {attr_str}

Generate:
1. A compelling product title (max 80 chars) — include key specs inline
2. A 3-sentence product description — highlight key features, performance, and value

Respond in this exact format:
TITLE: <title here>
DESCRIPTION: <description here>
"""
    response = call_ollama(prompt, timeout=60)
    title = product_name
    description = f"Premium {product_name} with {attr_str}."

    if "TITLE:" in response and "DESCRIPTION:" in response:
        try:
            title = response.split("TITLE:")[1].split("DESCRIPTION:")[0].strip()
            description = response.split("DESCRIPTION:")[1].strip()
        except Exception:
            pass

    return title, description


def get_strategy_suggestions(product, changes, competitors):
    """
    Generate a plain-prose advisory for a product based on detected competitor changes.
    The LLM receives structured context and is instructed to return clean sentences only.
    """
    change_text = "\n".join([c["message"] for c in changes]) if changes else "No price or discount changes detected."

    comp_lines = []
    for match in competitors:
        for c in match.get("competitors", []):
            comp_lines.append(
                f"  {c['platform'].title()}: Rs.{c['price']:,} | {c.get('discount',0)}% off | "
                f"{c.get('delivery_days',3)}-day delivery | Rating {c.get('rating',0)}"
            )
    comp_text = "\n".join(comp_lines) if comp_lines else "No competitor data available."

    prompt = (
        "You are a senior e-commerce business consultant advising a seller on an Indian marketplace.\n\n"
        "Write a focused advisory of exactly 4 to 5 sentences based on the product and market data below.\n\n"
        "Strict output rules:\n"
        "  - Plain sentences only. Zero bullet points. Zero numbered lists. Zero asterisks. Zero stars.\n"
        "  - Every sentence must reference a specific number from the data (price, discount %, days, rating).\n"
        "  - Sentence 1: the most urgent pricing or discount action given the detected changes.\n"
        "  - Sentences 2-3: delivery and rating actions if gaps exist.\n"
        "  - Sentence 4-5: bundle or promotional tactic to strengthen competitiveness.\n"
        "  - No headings. No introductions. No summaries. Start directly with the first action.\n\n"
        f"Product: {product.get('product_name', '')}\n"
        f"Our price: Rs.{product.get('our_price', 0):,} | "
        f"Discount: {product.get('discount', 0)}% | "
        f"Delivery: {product.get('delivery_days', 0)} days | "
        f"Stock: {product.get('stock', 0)} units\n\n"
        f"Detected market changes:\n{change_text}\n\n"
        f"Competitor landscape:\n{comp_text}\n\n"
        "Advisory:"
    )
    return call_ollama(prompt, timeout=120)


# ─── Auth helpers ────────────────────────────────────────────────────────────

def verify_login(email, password):
    """Check credentials against users.json. Returns user dict or None."""
    try:
        users_data = load_json("users.json")
        for user in users_data.get("users", []):
            if user["email"] == email and user["password"] == password:
                return user
    except Exception:
        pass
    return None


def get_user_orders(user_id):
    try:
        orders_data = load_json("orders.json")
        return [o for o in orders_data.get("orders", []) if o.get("user_id") == user_id]
    except Exception:
        return []


def place_order(user_id, product_id, quantity, buyer_location):
    products_data = load_json("our_products.json")
    orders_data = load_json("orders.json")
    seller = load_json("seller_profile.json")

    product = next((p for p in products_data["products"] if p["id"] == product_id), None)
    if not product or product["stock"] < quantity:
        return None, "Insufficient stock"

    # Update stock
    for p in products_data["products"]:
        if p["id"] == product_id:
            p["stock"] -= quantity

    days, delivery_date = estimate_delivery(
        seller["store_location"]["state"],
        buyer_location.get("state", "Unknown"),
        seller["store_location"]["pincode"],
        buyer_location.get("pincode", "000000")
    )

    order = {
        "order_id": f"BF{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product["product_name"],
        "quantity": quantity,
        "price": product["our_price"],
        "total": product["our_price"] * quantity,
        "status": "Confirmed",
        "placed_at": datetime.now().isoformat(),
        "delivery_date": delivery_date,
        "delivery_days": days,
        "buyer_location": buyer_location
    }

    orders_data["orders"].append(order)
    save_json("orders.json", orders_data)
    save_json("our_products.json", products_data)
    return order, None