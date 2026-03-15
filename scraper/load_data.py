import json
import sqlite3


def load_data_to_db():

    with open("data/compe.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect("db/database.db")
    c = conn.cursor()

    for item in data["matches"]:
        pid = item["our_product_id"]

        for comp in item["competitors"]:
            c.execute("""
            INSERT INTO competitor_data
            (product_id, platform, price, discount, rating, delivery_days)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pid,
                comp["platform"],
                comp["price"],
                comp["discount"],
                comp["rating"],
                comp["delivery_days"]
            ))

    conn.commit()
    conn.close()

    print("📥 Data loaded into DB")