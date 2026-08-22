import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/catalog.db")

PRODUCTS = [
    # Laptops
    {"id": 1, "name": "AtlasBook Pro 14", "category": "laptops", "price": 999.00, "margin_pct": 20, "compatible_with": [21,22,23]},
    {"id": 2, "name": "AtlasBook Air 13", "category": "laptops", "price": 749.00, "margin_pct": 18, "compatible_with": [21,24]},
    {"id": 3, "name": "WorkMate 15", "category": "laptops", "price": 1199.00, "margin_pct": 22, "compatible_with": [21,22,25]},
    {"id": 4, "name": "StudentPad 11", "category": "laptops", "price": 399.00, "margin_pct": 15, "compatible_with": [24,26]},

    # Accessories (mice, keyboards, stands)
    {"id": 21, "name": "MagTrack Wireless Mouse", "category": "accessories", "price": 39.00, "margin_pct": 45, "compatible_with": []},
    {"id": 22, "name": "Slim Portable Dock", "category": "accessories", "price": 129.00, "margin_pct": 40, "compatible_with": []},
    {"id": 23, "name": "USB-C Hub 7-in-1", "category": "accessories", "price": 59.00, "margin_pct": 38, "compatible_with": []},
    {"id": 24, "name": "Compact Bluetooth Keyboard", "category": "accessories", "price": 49.00, "margin_pct": 42, "compatible_with": []},
    {"id": 25, "name": "Ergo Laptop Stand", "category": "accessories", "price": 89.00, "margin_pct": 35, "compatible_with": []},
    {"id": 26, "name": "Protective Sleeve 13-inch", "category": "accessories", "price": 29.00, "margin_pct": 50, "compatible_with": []},

    # Phones
    {"id": 31, "name": "Photon X 6.5", "category": "phones", "price": 699.00, "margin_pct": 25, "compatible_with": [41,42]},
    {"id": 32, "name": "Photon Mini 5.8", "category": "phones", "price": 499.00, "margin_pct": 23, "compatible_with": [42]},
    {"id": 33, "name": "BudgetOne 6.1", "category": "phones", "price": 199.00, "margin_pct": 12, "compatible_with": [43]},

    # Phone accessories
    {"id": 41, "name": "FastCharge 30W Adapter", "category": "phone_accessories", "price": 29.00, "margin_pct": 55, "compatible_with": []},
    {"id": 42, "name": "ClearGuard Screen Protector", "category": "phone_accessories", "price": 15.00, "margin_pct": 60, "compatible_with": []},
    {"id": 43, "name": "Basic Earbuds", "category": "phone_accessories", "price": 19.00, "margin_pct": 40, "compatible_with": []},

    # Peripherals / other
    {"id": 51, "name": "Portable SSD 1TB", "category": "peripherals", "price": 119.00, "margin_pct": 30, "compatible_with": []},
    {"id": 52, "name": "USB-C to HDMI Cable", "category": "peripherals", "price": 19.00, "margin_pct": 48, "compatible_with": []},
    {"id": 53, "name": "Webcam HD 1080p", "category": "peripherals", "price": 59.00, "margin_pct": 33, "compatible_with": []},
    {"id": 54, "name": "Noise-Cancelling Headset", "category": "peripherals", "price": 149.00, "margin_pct": 28, "compatible_with": []},

    # Bundles / misc (to reach ~32)
    {"id": 61, "name": "Laptop Care Kit", "category": "bundles", "price": 39.00, "margin_pct": 50, "compatible_with": []},
    {"id": 62, "name": "Wireless Presenter", "category": "peripherals", "price": 24.00, "margin_pct": 45, "compatible_with": []},
    {"id": 63, "name": "Laptop Backpack", "category": "accessories", "price": 79.00, "margin_pct": 34, "compatible_with": []},
    {"id": 64, "name": "Privacy Filter 14-inch", "category": "accessories", "price": 49.00, "margin_pct": 47, "compatible_with": []},
]


def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Create tables
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            margin_pct REAL NOT NULL,
            compatible_with TEXT
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            interaction_trust INTEGER NOT NULL DEFAULT 100,
            business_goal TEXT CHECK(business_goal IN ('increase_aov','increase_conversion')) DEFAULT 'increase_aov',
            cart_total REAL NOT NULL DEFAULT 0,
            budget_stated REAL
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            action TEXT CHECK(action IN ('UPSELL','NO_UPSELL')) NOT NULL,
            trust_score_at_decision INTEGER NOT NULL,
            candidate_product_id INTEGER,
            reasons TEXT,
            business_goal TEXT,
            cart_value_at_decision REAL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
        """
    )

    # Seed products if table empty
    c.execute("SELECT COUNT(1) as cnt FROM products")
    row = c.fetchone()
    if row and row[0] > 0:
        print("Products already seeded; skipping.")
    else:
        for p in PRODUCTS:
            c.execute(
                "INSERT INTO products (id, name, category, price, margin_pct, compatible_with) VALUES (?, ?, ?, ?, ?, ?)",
                (p["id"], p["name"], p["category"], p["price"], p["margin_pct"], json.dumps(p["compatible_with"]))
            )
        print(f"Inserted {len(PRODUCTS)} products.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    ensure_db()
    print("DB initialized at", DB_PATH)
