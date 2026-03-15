import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qcwind/qwen3-8b-instruct-Q4-K-M"


def _clean(text: str) -> str:
    """Strip all markdown from LLM output — bold, italic, bullets, numbers, headers."""
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"`+([^`]*)`+", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-_*]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _review_sentiment(competitors: list) -> tuple:
    """
    Pull up to 3 low-rated and 3 high-rated review texts from all competitors.
    Returns (positive_themes, negative_themes) as short strings.
    """
    pos, neg = [], []
    for comp in competitors:
        for review in comp.get("reviews", []):
            rating = review.get("rating", 3)
            text   = review.get("text", "").strip()
            if not text:
                continue
            if rating >= 4 and len(pos) < 3:
                pos.append(text)
            elif rating <= 2 and len(neg) < 3:
                neg.append(text)
    return (
        " / ".join(pos)[:350] if pos else "No positive reviews found.",
        " / ".join(neg)[:350] if neg else "No negative reviews found.",
    )


def _best_competitor(competitors: list) -> dict:
    """Return the competitor with the lowest listed price."""
    return min(competitors, key=lambda c: c.get("price", float("inf")))


def get_llm_recommendation(item: dict, competitors: list) -> str:
    """
    Build a data-rich prompt from product metrics, all competitor prices/ratings,
    and real customer review sentiment. Returns a professional advisory paragraph —
    plain prose, no markdown, no bullet points, no stars.
    """
    if not competitors:
        return "No competitor data is available to generate a recommendation for this product."

    best             = _best_competitor(competitors)
    pos_themes, neg_themes = _review_sentiment(competitors)

    our_price    = item.get("our_price", 0)
    our_discount = item.get("our_discount", 0)
    our_rating   = item.get("our_rating", 0)
    our_delivery = item.get("our_delivery_days", 3)

    best_price    = best.get("price", 0)
    best_platform = best.get("platform", "competitor").title()

    price_gap    = our_price - best_price
    delivery_gap = our_delivery - best.get("delivery_days", 3)
    rating_gap   = best.get("rating", 0) - our_rating

    comp_rows = "\n".join(
        f"  {c.get('platform','').title()}: Rs.{c.get('price',0):,} | "
        f"{c.get('discount',0)}% off | "
        f"Rating {c.get('rating',0)} ({c.get('rating_count',0):,} reviews) | "
        f"{c.get('delivery_days',0)}-day delivery"
        for c in competitors
    )

    prompt = (
        "You are a senior e-commerce business consultant advising a seller on an Indian marketplace.\n\n"
        "Write a focused advisory of exactly 5 to 6 sentences based on the product data below.\n\n"
        "Strict output rules:\n"
        "  - Plain sentences only. Zero bullet points. Zero numbered lists. Zero asterisks. Zero stars.\n"
        "  - Every sentence must reference a specific number from the data.\n"
        "  - Sentence 1: address the single largest gap first (price, delivery, or rating).\n"
        "  - Sentences 2-4: secondary tactical actions grounded in the exact numbers.\n"
        "  - Sentence 5: use the buyer review data to suggest one specific product or messaging fix.\n"
        "  - Sentence 6: one marketing action that turns an existing advantage into visibility.\n"
        "  - No headings. No introductions. No summaries. No sign-offs. Start directly with the first action.\n\n"
        f"Product: {item.get('our_product_name', 'Unknown')}\n"
        f"Our listing: Rs.{our_price:,} | {our_discount}% discount | "
        f"Rating {our_rating} | Delivery {our_delivery} day(s)\n\n"
        f"All competitors:\n{comp_rows}\n\n"
        f"Gap vs best-priced competitor ({best_platform} at Rs.{best_price:,}):\n"
        f"  Price: Rs.{abs(price_gap):,} {'above' if price_gap > 0 else 'below'} market\n"
        f"  Delivery: {abs(delivery_gap)} day(s) {'slower' if delivery_gap > 0 else 'faster'} "
        f"than {best_platform}\n"
        f"  Rating: {abs(rating_gap):.1f} pts {'behind' if rating_gap > 0 else 'ahead of'} "
        f"{best_platform}\n\n"
        f"Buyer praise about competitors: {pos_themes}\n"
        f"Buyer complaints about competitors: {neg_themes}\n\n"
        "Advisory:"
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=180,
        )
        if resp.status_code != 200:
            return "LLM service is unavailable. Please ensure Ollama is running and the model is loaded."
        raw = resp.json().get("response", "")
        if not raw:
            return "No recommendation could be generated. The model returned an empty response."
        return _clean(raw)
    except requests.exceptions.ConnectionError:
        return "Unable to reach Ollama. Run 'ollama serve' and ensure the model is loaded."
    except requests.exceptions.Timeout:
        return "The model took too long to respond. Try a lighter model or increase the timeout."
    except Exception as exc:
        return f"Unexpected error while calling LLM: {exc}"