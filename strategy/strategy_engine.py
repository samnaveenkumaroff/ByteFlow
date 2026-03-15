def generate_strategies(product, competitor):
    """
    Generate condition-based strategies by comparing our product against a single competitor.
    Returns a list of strategy dicts with category, severity, action, and rationale.
    """

    strategies = []

    comp_price    = competitor.get("price", 0)
    comp_delivery = competitor.get("delivery_days", 0)
    comp_rating   = competitor.get("rating", 0)
    comp_discount = competitor.get("discount", 0)
    comp_platform = competitor.get("platform", "competitor")

    our_price    = product.get("our_price", product.get("price", 0))
    our_delivery = product.get("our_delivery_days", product.get("delivery_days", 0))
    our_rating   = product.get("our_rating", product.get("rating", 0))
    our_discount = product.get("our_discount", product.get("discount", 0))

    price_gap    = our_price - comp_price
    delivery_gap = our_delivery - comp_delivery
    rating_gap   = our_rating - comp_rating
    discount_gap = our_discount - comp_discount

    # -- Pricing --
    if price_gap > 2000:
        strategies.append({
            "strategy": "pricing",
            "severity": "high",
            "action": f"Reduce price by ₹{price_gap:,} to match {comp_platform}",
            "rationale": f"{comp_platform.title()} is listing at ₹{comp_price:,}, making us ₹{price_gap:,} more expensive."
        })
    elif 500 < price_gap <= 2000:
        strategies.append({
            "strategy": "pricing",
            "severity": "medium",
            "action": f"Consider a ₹{price_gap:,} price reduction or equivalent coupon offer",
            "rationale": f"Moderate price gap vs {comp_platform.title()}. A targeted coupon can close this without a permanent price cut."
        })
    elif price_gap < -1000:
        strategies.append({
            "strategy": "pricing",
            "severity": "low",
            "action": "Leverage price advantage in listings and ad copy",
            "rationale": f"We are ₹{abs(price_gap):,} cheaper than {comp_platform.title()}. Highlight this in search ads and product banners."
        })

    # -- Discount --
    if discount_gap < -5:
        strategies.append({
            "strategy": "discount",
            "severity": "medium",
            "action": f"Increase discount from {our_discount}% to at least {comp_discount}% to stay competitive",
            "rationale": f"{comp_platform.title()} offers {comp_discount}% off. Our {our_discount}% discount will appear inferior to deal-seeking buyers."
        })
    elif discount_gap > 5:
        strategies.append({
            "strategy": "discount",
            "severity": "low",
            "action": "Use higher discount percentage as a marketing signal",
            "rationale": f"Our {our_discount}% discount beats {comp_platform.title()}'s {comp_discount}%. Prominently display the savings amount in rupees."
        })

    # -- Delivery --
    if delivery_gap >= 2:
        strategies.append({
            "strategy": "delivery",
            "severity": "high",
            "action": f"Reduce delivery time to match {comp_platform.title()}'s {comp_delivery}-day fulfilment",
            "rationale": f"We deliver in {our_delivery} days vs {comp_delivery} days on {comp_platform.title()}. Customers consistently prefer faster delivery options."
        })
    elif delivery_gap == 1:
        strategies.append({
            "strategy": "delivery",
            "severity": "medium",
            "action": "Introduce an express shipping option to close the 1-day delivery gap",
            "rationale": f"{comp_platform.title()} delivers 1 day faster. An optional express tier retains time-sensitive customers."
        })
    elif delivery_gap < 0:
        strategies.append({
            "strategy": "delivery",
            "severity": "low",
            "action": "Promote faster delivery prominently in product listings",
            "rationale": f"We deliver {abs(delivery_gap)} day(s) faster than {comp_platform.title()}. This is a tangible advantage worth advertising."
        })

    # -- Rating --
    if rating_gap < -0.3:
        strategies.append({
            "strategy": "rating",
            "severity": "high",
            "action": "Launch a post-purchase review collection campaign",
            "rationale": f"Our rating of {our_rating} lags {comp_platform.title()}'s {comp_rating}. A structured follow-up sequence can recover this gap within 60 days."
        })
    elif -0.3 <= rating_gap < 0:
        strategies.append({
            "strategy": "rating",
            "severity": "medium",
            "action": "Address the top negative review themes in product description",
            "rationale": f"Small rating gap vs {comp_platform.title()}. Proactively answering common complaints in the listing reduces buyer hesitation."
        })
    elif rating_gap > 0.3:
        strategies.append({
            "strategy": "rating",
            "severity": "low",
            "action": "Showcase superior rating in ad creatives and social proof banners",
            "rationale": f"Our {our_rating} rating outperforms {comp_platform.title()}'s {comp_rating}. Use this as a trust signal in all marketing touchpoints."
        })

    # -- Fully competitive: no gaps detected --
    if not strategies:
        strategies.append({
            "strategy": "positioning",
            "severity": "info",
            "action": "Position on brand trust and seller reliability rather than price",
            "rationale": f"We are at parity with {comp_platform.title()} across price, delivery, and rating. Differentiate through exclusive bundles, warranty messaging, and loyalty offers."
        })

    return strategies