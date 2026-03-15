# server.py — ByteFlow Mart FastAPI Backend
# Run: python server.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json, os, uuid, re
from datetime import datetime, timedelta

# ── path setup so utils imports work ──
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    load_json, save_json, match_competitor, suggest_price_strategy,
    estimate_delivery, detect_product_changes, get_bundles_for_product,
    generate_title_description, get_strategy_suggestions,
    verify_login, get_user_orders, place_order, call_ollama
)

app = FastAPI(title="ByteFlow Mart API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ══════════════════════════════════════════════════════
# SERVE FRONTEND
# ══════════════════════════════════════════════════════

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.get("/seller")
def serve_seller():
    return FileResponse("static/seller.html")

@app.get("/customer")
def serve_customer():
    return FileResponse("static/customer.html")


# ══════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    user = verify_login(req.email.strip(), req.password.strip())
    if not user:
        raise HTTPException(401, "Invalid credentials")
    safe = {k: v for k, v in user.items() if k != "password"}
    return {"user": safe}


# ══════════════════════════════════════════════════════
# SELLER — PRODUCTS
# ══════════════════════════════════════════════════════

@app.get("/api/seller/products")
def get_seller_products():
    data = load_json("our_products.json")
    return data

@app.get("/api/seller/profile")
def get_seller_profile():
    return load_json("seller_profile.json")

@app.post("/api/seller/profile")
async def update_seller_profile(req: Request):
    body = await req.json()
    save_json("seller_profile.json", body)
    return {"status": "saved"}

@app.delete("/api/seller/products/{pid}")
def delete_product(pid: str):
    data = load_json("our_products.json")
    data["products"] = [p for p in data["products"] if p["id"] != pid]
    save_json("our_products.json", data)
    return {"status": "deleted"}

@app.post("/api/seller/products/{pid}/update")
async def update_product(pid: str, req: Request):
    body = await req.json()
    data = load_json("our_products.json")
    for i, p in enumerate(data["products"]):
        if p["id"] == pid:
            data["products"][i].update(body)
    save_json("our_products.json", data)
    return {"status": "updated"}


# ══════════════════════════════════════════════════════
# SELLER — ADD PRODUCT / ANALYZE
# ══════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    product_name: str
    attributes: Dict[str, str] = {}
    search_query: str = ""
    stock: int = 1
    category: str = "Smartphones"

@app.post("/api/seller/analyze")
def analyze_product(req: AnalyzeRequest):
    compe_data = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
                 else load_json("compe.json")
    seller = load_json("seller_profile.json")

    sq = req.search_query or req.product_name
    matched = match_competitor(sq, req.attributes, compe_data)
    suggested_price, suggested_discount = suggest_price_strategy(60000, matched)
    title, description = generate_title_description(req.product_name, req.attributes)
    days, delivery_date = estimate_delivery(
        seller["store_location"]["state"],
        seller["store_location"]["state"],
        seller["store_location"]["pincode"],
        seller["warehouse_pincode"]
    )
    bundles = get_bundles_for_product("NEW", req.product_name)

    # Build competitor summary
    competitor_summary = []
    for match in matched:
        for comp in match.get("competitors", []):
            competitor_summary.append({
                "platform":      comp["platform"],
                "price":         comp["price"],
                "discount":      comp.get("discount", 0),
                "rating":        comp.get("rating", 0),
                "delivery_days": comp.get("delivery_days", 3),
                "url":           comp.get("url", "")
            })

    return {
        "title":              title,
        "description":        description,
        "suggested_price":    suggested_price,
        "suggested_discount": suggested_discount,
        "delivery_days":      days,
        "delivery_date":      delivery_date,
        "competitors":        competitor_summary,
        "bundles":            bundles
    }

class AddProductRequest(BaseModel):
    product_name: str
    search_query: str = ""
    category: str = "Smartphones"
    stock: int = 1
    attributes: Dict[str, str] = {}
    image_url: str = ""
    title: str = ""
    description: str = ""
    our_price: int = 0
    discount: int = 0
    delivery_days: int = 3
    editing_id: Optional[str] = None

@app.post("/api/seller/products/add")
def add_product(req: AddProductRequest):
    data = load_json("our_products.json")
    original_price = int(req.our_price / (1 - req.discount/100)) if req.discount > 0 else req.our_price
    retail_price   = int(req.our_price * 0.97)
    pid = req.editing_id or f"P{str(uuid.uuid4())[:6].upper()}"

    product = {
        "id":            pid,
        "product_name":  req.product_name,
        "search_query":  req.search_query or req.product_name,
        "our_price":     req.our_price,
        "retail_price":  retail_price,
        "original_price":original_price,
        "discount":      req.discount,
        "rating":        4.5,
        "rating_count":  0,
        "delivery_days": req.delivery_days,
        "stock":         req.stock,
        "image_url":     req.image_url,
        "category":      req.category,
        "brand":         req.product_name.split()[0],
        "attributes":    req.attributes,
        "title":         req.title,
        "description":   req.description,
        "last_checked":  datetime.now().isoformat(),
        "alerts":        [],
        "reviews":       []
    }

    if req.editing_id:
        data["products"] = [product if p["id"] == req.editing_id else p for p in data["products"]]
    else:
        data["products"].append(product)

    data["last_updated"] = datetime.now().isoformat()
    save_json("our_products.json", data)
    return {"status": "saved", "product": product}


# ══════════════════════════════════════════════════════
# ALERTS
# ══════════════════════════════════════════════════════

@app.get("/api/seller/alerts")
def get_alerts():
    data      = load_json("our_products.json")
    compe     = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
                else load_json("compe.json")
    result    = []
    for p in data["products"]:
        result.append({
            "id":           p["id"],
            "product_name": p["product_name"],
            "our_price":    p["our_price"],
            "discount":     p.get("discount", 0),
            "last_checked": p.get("last_checked", ""),
            "alerts":       p.get("alerts", [])
        })
    return {"products": result, "last_scanned": data.get("last_scanned", "")}

@app.post("/api/seller/alerts/scan/{pid}")
def scan_product(pid: str):
    data  = load_json("our_products.json")
    compe = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
            else load_json("compe.json")
    for p in data["products"]:
        if p["id"] == pid:
            changes = detect_product_changes(p, compe)
            p["last_checked"] = datetime.now().isoformat()
            existing = [a["message"] for a in p.get("alerts", [])]
            for ch in changes:
                if ch["message"] not in existing:
                    p.setdefault("alerts", []).append(ch)
            save_json("our_products.json", data)
            return {"changes": changes, "alerts": p.get("alerts", [])}
    raise HTTPException(404, "Product not found")

@app.post("/api/seller/alerts/scan-all")
def scan_all():
    data  = load_json("our_products.json")
    compe = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
            else load_json("compe.json")
    total = 0
    for p in data["products"]:
        changes = detect_product_changes(p, compe)
        p["last_checked"] = datetime.now().isoformat()
        existing = [a["message"] for a in p.get("alerts", [])]
        for ch in changes:
            if ch["message"] not in existing:
                p.setdefault("alerts", []).append(ch)
                total += 1
    data["last_scanned"] = datetime.now().isoformat()
    save_json("our_products.json", data)
    return {"total_new": total}

@app.post("/api/seller/alerts/clear/{pid}")
def clear_alerts(pid: str):
    data = load_json("our_products.json")
    for p in data["products"]:
        if p["id"] == pid:
            p["alerts"] = []
    save_json("our_products.json", data)
    return {"status": "cleared"}

@app.post("/api/seller/alerts/one-click-update/{pid}")
def one_click_update(pid: str):
    data  = load_json("our_products.json")
    compe = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
            else load_json("compe.json")
    for p in data["products"]:
        if p["id"] == pid:
            matched = match_competitor(p.get("search_query", p["product_name"]),
                                       p.get("attributes", {}), compe)
            new_price, new_disc = suggest_price_strategy(p["our_price"], matched)
            old_price = p["our_price"]
            p["our_price"]    = new_price
            p["discount"]     = new_disc
            p["retail_price"] = int(new_price * 0.97)
            p["alerts"]       = []
            p["last_checked"] = datetime.now().isoformat()
            save_json("our_products.json", data)
            return {"old_price": old_price, "new_price": new_price, "new_discount": new_disc}
    raise HTTPException(404, "Product not found")

@app.post("/api/seller/alerts/ai-strategy/{pid}")
def ai_strategy(pid: str):
    from strategy.strategy_engine import generate_strategies

    data  = load_json("our_products.json")
    compe = load_json("compe_optimized.json") if os.path.exists("data/compe_optimized.json") \
            else load_json("compe.json")

    for p in data["products"]:
        if p["id"] == pid:
            matched = match_competitor(p.get("search_query", p["product_name"]),
                                       p.get("attributes", {}), compe)

            # ── Step 1: condition-based strategies (instant, always works) ──
            strategies = []
            seen_actions = set()
            for match in matched:
                for comp in match.get("competitors", []):
                    for s in generate_strategies(p, comp):
                        if s["action"] not in seen_actions:
                            seen_actions.add(s["action"])
                            strategies.append(s)

            strategies.sort(key=lambda x: {"high":0,"medium":1,"low":2,"info":3}.get(x.get("severity","info"),3))
            strategies = strategies[:6]

            # ── Step 2: short LLM insight (30s, fails gracefully) ──
            comp_summary = []
            for match in matched:
                for c in match.get("competitors", []):
                    comp_summary.append(
                        f"{c['platform'].title()}: Rs.{c.get('price',0):,} | "
                        f"{c.get('discount',0)}% off | {c.get('delivery_days',3)}-day delivery | "
                        f"Rating {c.get('rating',0)}"
                    )
            comp_text = "\n".join(comp_summary[:4])
            alerts    = p.get("alerts", [])
            alert_text = "; ".join([a["message"] for a in alerts]) if alerts else "No active alerts."

            prompt = (
                "You are a senior e-commerce consultant. Write exactly 2 plain sentences with no bullets, "
                "no stars, no markdown. Give the most critical pricing action and one promotional tactic. "
                "Reference actual rupee figures.\n\n"
                f"Product: {p.get('product_name','')}\n"
                f"Our price: Rs.{p.get('our_price',0):,} | Discount: {p.get('discount',0)}% | "
                f"Stock: {p.get('stock',0)} units\n"
                f"Active market alerts: {alert_text}\n"
                f"Competitors:\n{comp_text}\n\nAdvisory:"
            )
            llm_note = call_ollama(prompt, timeout=30)
            llm_ok   = llm_note and not llm_note.startswith("Unable") \
                       and not llm_note.startswith("Unexpected") \
                       and not llm_note.startswith("LLM")

            return {
                "strategies": strategies,
                "llm_insight": llm_note if llm_ok else None
            }

    raise HTTPException(404, "Product not found")


# ══════════════════════════════════════════════════════
# STRATEGY DASHBOARD
# ══════════════════════════════════════════════════════

@app.get("/api/strategy/data")
def strategy_data():
    import shutil
    f = "data/compe_optimized.json"
    data  = load_json("compe_optimized.json" if os.path.exists(f) else "compe.json")
    prods = load_json("our_products.json")
    is_opt = os.path.exists(f)
    return {"data": data, "our_products": prods["products"], "is_optimized": is_opt}

@app.post("/api/strategy/apply-all")
def apply_all_strategies():
    from strategy.apply_engine import apply_global_strategies
    import shutil
    f = "data/compe_optimized.json"
    data = load_json("compe_optimized.json" if os.path.exists(f) else "compe.json")
    new_data = apply_global_strategies(data)
    save_json("compe_optimized.json", new_data)
    return {"status": "applied"}

@app.post("/api/strategy/reset")
def reset_strategy():
    import shutil
    shutil.copy("data/compe.json", "data/compe_optimized.json")
    return {"status": "reset"}

@app.post("/api/strategy/save-item")
async def save_strategy_item(req: Request):
    body = await req.json()
    f    = "data/compe_optimized.json"
    data = load_json("compe_optimized.json" if os.path.exists(f) else "compe.json")
    for item in data["matches"]:
        if item["our_product_id"] == body["pid"]:
            item["our_price"]         = body.get("our_price", item["our_price"])
            item["our_discount"]      = body.get("our_discount", item.get("our_discount", 0))
            item["our_delivery_days"] = body.get("our_delivery_days", item.get("our_delivery_days", 3))
            item["our_rating"]        = body.get("our_rating", item.get("our_rating", 4.0))
    save_json("compe_optimized.json", data)
    return {"status": "saved"}

@app.post("/api/strategy/ai/{pid}")
def strategy_ai(pid: str):
    from strategy.strategy_engine import generate_strategies

    f    = "data/compe_optimized.json"
    data = load_json("compe_optimized.json" if os.path.exists(f) else "compe.json")
    item = next((m for m in data["matches"] if m["our_product_id"] == pid), None)
    if not item:
        raise HTTPException(404)

    competitors = item.get("competitors", [])

    # ── Step 1: condition-based strategies (instant) ──
    strategies   = []
    seen_actions = set()
    for comp in competitors:
        for s in generate_strategies(item, comp):
            if s["action"] not in seen_actions:
                seen_actions.add(s["action"])
                strategies.append(s)

    strategies.sort(key=lambda x: {"high":0,"medium":1,"low":2,"info":3}.get(x.get("severity","info"),3))
    strategies = strategies[:6]

    # ── Step 2: short LLM insight (30s, fails gracefully) ──
    comp_text = "\n".join(
        f"  {c.get('platform','').title()}: Rs.{c.get('price',0):,} | "
        f"{c.get('discount',0)}% off | {c.get('delivery_days',3)}-day delivery | "
        f"Rating {c.get('rating',0)}"
        for c in competitors[:4]
    )
    prompt = (
        "You are a senior e-commerce consultant. Write exactly 2 plain sentences with no bullets, "
        "no stars, no markdown. Give the most critical pricing action and one promotional tactic. "
        "Reference actual rupee figures.\n\n"
        f"Product: {item['our_product_name']}\n"
        f"Our listing: Rs.{item['our_price']:,} | Discount: {item.get('our_discount',0)}% | "
        f"Rating: {item.get('our_rating',0)} | Delivery: {item.get('our_delivery_days',3)} day(s)\n"
        f"Competitors:\n{comp_text}\n\nAdvisory:"
    )
    llm_note = call_ollama(prompt, timeout=30)
    llm_ok   = llm_note and not llm_note.startswith("Unable") \
               and not llm_note.startswith("Unexpected") \
               and not llm_note.startswith("LLM")

    return {
        "strategies": strategies,
        "llm_insight": llm_note if llm_ok else None
    }


# ══════════════════════════════════════════════════════
# CUSTOMER
# ══════════════════════════════════════════════════════

@app.get("/api/customer/products")
def customer_products():
    data   = load_json("our_products.json")
    seller = load_json("seller_profile.json")
    return {"products": data["products"], "seller": seller}

@app.get("/api/customer/product/{pid}")
def customer_product_detail(pid: str):
    data   = load_json("our_products.json")
    seller = load_json("seller_profile.json")
    p = next((x for x in data["products"] if x["id"] == pid), None)
    if not p:
        raise HTTPException(404)
    bundles = get_bundles_for_product(pid, p["product_name"])
    return {"product": p, "seller": seller, "bundles": bundles}

class OrderRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int
    buyer_location: Dict[str, str]

@app.post("/api/customer/order")
def create_order(req: OrderRequest):
    order, err = place_order(req.user_id, req.product_id, req.quantity, req.buyer_location)
    if err:
        raise HTTPException(400, err)
    return {"order": order}

@app.get("/api/customer/orders/{user_id}")
def customer_orders(user_id: str):
    return {"orders": get_user_orders(user_id)}

@app.get("/api/customer/delivery-estimate")
def delivery_estimate(buyer_state: str, buyer_pincode: str):
    seller = load_json("seller_profile.json")
    days, date = estimate_delivery(
        seller["store_location"]["state"], buyer_state,
        seller["store_location"]["pincode"], buyer_pincode
    )
    return {"days": days, "date": date}


# ══════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)