# scheduler/scheduler.py — 24-hour competitor alert scan

import schedule
import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_json, save_json, detect_product_changes


def run_competitor_scan():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running 24h competitor scan...")
    try:
        products_data = load_json("our_products.json")
        compe_file = "compe_optimized.json" if os.path.exists("data/compe_optimized.json") else "compe.json"
        compe_data = load_json(compe_file)
        total_changes = 0

        for product in products_data.get("products", []):
            changes = detect_product_changes(product, compe_data)
            product["last_checked"] = datetime.now().isoformat()
            if changes:
                existing_msgs = [a["message"] for a in product.get("alerts", [])]
                for ch in changes:
                    if ch["message"] not in existing_msgs:
                        product.setdefault("alerts", []).append(ch)
                        total_changes += 1
                        print(f"  ⚠ [{product['id']}] {ch['message']}")

        products_data["last_scanned"] = datetime.now().isoformat()
        save_json("our_products.json", products_data)
        print(f"  ✅ Scan complete. {total_changes} new alert(s) written.\n")
    except Exception as e:
        print(f"  ❌ Scan error: {e}\n")


schedule.every(24).hours.do(run_competitor_scan)
run_competitor_scan()  # Run on startup

print("⏰ ByteFlow Mart scheduler running (every 24 hours). Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)