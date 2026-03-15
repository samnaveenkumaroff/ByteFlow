from utils import call_ollama


def _best_competitor(competitors):
    """Return the competitor with the lowest price among all listed platforms."""
    if not competitors:
        return None
    return min(competitors, key=lambda c: c.get("price", float("inf")))


def _extract_review_themes(competitors):
    """Scan competitor reviews and return a short summary of recurring complaints."""
    complaints = []
    for comp in competitors:
        for review in comp.get("reviews", []):
            if review.get("rating", 5) <= 3:
                complaints.append(review.get("text", ""))
    if not complaints:
        return "No notable complaints found in competitor reviews."
    sample = complaints[:6]
    combined = " | ".join(sample)
    return combined[:600]


def generate_product_recommendations(item):
    """
    Produce structured, condition-based recommendations for a single product.
    Compares against the best (lowest-price) competitor and returns a list of
    plain-text recommendation strings — no bullets, stars, or filler phrases.
    """

    competitors = item.get("competitors", [])
    if not competitors:
        return ["No competitor data available for this product."]

    comp = _best_competitor(competitors)

    our_price      = item.get("our_price", 0)
    our_discount   = item.get("our_discount", 0)
    our_delivery   = item.get("our_delivery_days", 3)
    our_rating     = item.get("our_rating", 0)

    comp_price     = comp.get("price", 0)
    comp_discount  = comp.get("discount", 0)
    comp_delivery  = comp.get("delivery_days", 3)
    comp_rating    = comp.get("rating", 0)
    comp_platform  = comp.get("platform", "competitor").title()

    price_gap    = our_price - comp_price
    discount_gap = our_discount - comp_discount
    delivery_gap = our_delivery - comp_delivery
    rating_gap   = comp_rating - our_rating

    recs = []

    # -- Pricing --
    if price_gap > 2000:
        recs.append(
            f"Reduce the listed price by ₹{price_gap:,} to align with {comp_platform} "
            f"(currently ₹{comp_price:,}). A gap this large will drive price-sensitive buyers away."
        )
        recs.append(
            "If a permanent price cut is not feasible, introduce a bank-specific or app-exclusive coupon "
            "that brings the effective price within ₹500 of the market leader."
        )
    elif 500 < price_gap <= 2000:
        recs.append(
            f"A ₹{price_gap:,} price difference vs {comp_platform} is noticeable on comparison pages. "
            "Consider a limited-period discount or bundle add-on to neutralise the gap."
        )
    elif price_gap < -1000:
        recs.append(
            f"At ₹{abs(price_gap):,} below {comp_platform}, we hold a clear price advantage. "
            "Feature the 'lowest price' message on the listing thumbnail and in sponsored ad copy."
        )

    # -- Discount --
    if discount_gap < -5:
        recs.append(
            f"{comp_platform} advertises {comp_discount}% off vs our {our_discount}%. "
            "Raise the displayed discount to at least match, or frame our price differently "
            "(e.g. show MRP strikethrough more prominently)."
        )
    elif discount_gap > 8:
        recs.append(
            f"Our {our_discount}% discount exceeds {comp_platform}'s {comp_discount}%. "
            "Show the exact rupee savings (e.g. 'Save ₹X') rather than just the percentage — "
            "absolute savings figures convert better."
        )

    # -- Delivery --
    if delivery_gap >= 2:
        recs.append(
            f"{comp_platform} delivers in {comp_delivery} day(s); we take {our_delivery}. "
            "Negotiate faster SLAs with the logistics partner for this category, or designate a "
            "nearby fulfilment centre to bring delivery within 1–2 days."
        )
    elif delivery_gap == 1:
        recs.append(
            f"We are 1 day slower than {comp_platform}. Adding an optional express delivery tier "
            "at a marginal surcharge will retain time-sensitive customers without restructuring "
            "the standard fulfilment process."
        )
    elif delivery_gap <= -1:
        recs.append(
            f"We deliver {abs(delivery_gap)} day(s) faster than {comp_platform}. "
            "Highlight this in the product page subtitle and in retargeting ads as a service differentiator."
        )

    # -- Rating --
    if rating_gap > 0.3:
        review_themes = _extract_review_themes(competitors)
        recs.append(
            f"Our rating ({our_rating}) is below {comp_platform}'s ({comp_rating}). "
            "Send a post-delivery follow-up message at day 3 and day 7 requesting a review. "
            f"Recurring themes in competitor reviews: {review_themes[:200]}"
        )
    elif rating_gap > 0:
        recs.append(
            f"Small rating gap vs {comp_platform} ({our_rating} vs {comp_rating}). "
            "Address the most common 3-star complaint themes directly in the product description "
            "to reduce pre-purchase hesitation."
        )
    elif rating_gap <= -0.3:
        recs.append(
            f"Our rating of {our_rating} is higher than {comp_platform}'s {comp_rating}. "
            "Include a social proof line in the listing headline such as 'Rated {our_rating}/5 by verified buyers'."
        )

    # -- Discount vs all competitors --
    all_discounts = [c.get("discount", 0) for c in competitors]
    max_comp_discount = max(all_discounts) if all_discounts else 0
    if our_discount < max_comp_discount - 3:
        best_disc_platform = next(
            (c.get("platform", "").title() for c in competitors if c.get("discount") == max_comp_discount), ""
        )
        recs.append(
            f"{best_disc_platform} leads the market with {max_comp_discount}% off. "
            "Run a 72-hour flash sale at that discount level to capture deal-aggregator traffic "
            "without permanently altering your pricing structure."
        )

    # -- Fully competitive --
    if not recs:
        recs.append(
            "All key metrics — price, delivery, rating, and discount — are at or above the market benchmark. "
            "Focus on top-of-funnel visibility: invest in sponsored listings, Google Shopping, and "
            "influencer seeding to grow market share without sacrificing margin."
        )
        recs.append(
            "Introduce a value-add bundle (e.g. protective case + screen guard) at a marginal premium "
            "to increase average order value and create a listing variant that competitors cannot directly price-match."
        )

    return recs


def apply_global_strategies(data):
    """
    Apply data-driven pricing, delivery, and rating adjustments across all products.
    Uses the best (lowest-price) competitor as the benchmark for each item.
    Adjustments are proportional and capped to avoid unrealistic values.
    """

    for item in data.get("matches", []):
        competitors = item.get("competitors", [])
        if not competitors:
            continue

        comp = _best_competitor(competitors)

        comp_price    = comp.get("price", 0)
        comp_delivery = comp.get("delivery_days", 3)
        comp_rating   = comp.get("rating", 0)
        comp_discount = comp.get("discount", 0)

        our_price    = item.get("our_price", 0)
        our_delivery = item.get("our_delivery_days", 3)
        our_rating   = item.get("our_rating", 0)
        our_discount = item.get("our_discount", 0)

        # Pricing: undercut by ₹99 if we are more expensive, with a floor of 85% of competitor price
        if our_price > comp_price:
            target = comp_price - 99
            floor  = int(comp_price * 0.85)
            item["our_price"] = max(target, floor)

        # Delivery: match competitor if we are slower, minimum 1 day
        if our_delivery > comp_delivery:
            item["our_delivery_days"] = max(comp_delivery, 1)

        # Rating: increment by 0.1 if below competitor, cap at 5.0
        if our_rating < comp_rating:
            item["our_rating"] = min(round(our_rating + 0.1, 2), 5.0)

        # Discount: match competitor discount if we are more than 3 points behind
        if our_discount < comp_discount - 3:
            item["our_discount"] = comp_discount

    return data