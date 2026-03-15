"""
migrate_to_supabase.py
──────────────────────
One-time script: seeds all products from products.json into Supabase.
Also sets up default offer settings.

HOW TO RUN (locally, once):
  1. pip install flask flask-sqlalchemy flask-cors psycopg2-binary
  2. set DATABASE_URL=your_supabase_connection_string
     (Windows)  set DATABASE_URL=postgresql://...
     (Mac/Linux) export DATABASE_URL=postgresql://...
  3. python migrate_to_supabase.py
"""

import os, json, sys

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌  ERROR: DATABASE_URL environment variable is not set.")
    print("   Set it to your Supabase connection string and re-run.")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Bootstrap Flask app ───────────────────────────────────────────────────────
from flask import Flask
from models import db, Product, Setting

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]   = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
db.init_app(app)

# ── Load products.json ────────────────────────────────────────────────────────
PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "data", "products.json")
if not os.path.exists(PRODUCTS_FILE):
    print(f"❌  products.json not found at: {PRODUCTS_FILE}")
    sys.exit(1)

with open(PRODUCTS_FILE, "r") as f:
    raw_products = json.load(f)

# ── Run migration ─────────────────────────────────────────────────────────────
with app.app_context():
    print("📦  Creating tables if they don't exist...")
    db.create_all()

    existing = Product.query.count()
    if existing > 0:
        print(f"⚠️   Found {existing} products already in DB.")
        answer = input("   Do you want to wipe and re-seed? [y/N]: ").strip().lower()
        if answer != "y":
            print("   Skipping product seeding. Tables already have data.")
        else:
            Product.query.delete()
            db.session.commit()
            print("   Cleared existing products.")
            existing = 0

    if existing == 0:
        print(f"🌱  Seeding {len(raw_products)} products...")
        for p in raw_products:
            product = Product(
                id     = p["id"],
                name   = p["name"],
                brand  = p["brand"],
                price  = int(p["price"]),
                image  = p.get("image", ""),
                tag    = p.get("tag", ""),
                sizes  = json.dumps(p.get("sizes", [])),
                colors = json.dumps(p.get("colors", [])),
            )
            db.session.add(product)
        db.session.commit()
        print(f"   ✅  {len(raw_products)} products inserted.")

    # Default offer setting
    if not Setting.query.get("offer"):
        db.session.add(Setting(
            key   = "offer",
            value = json.dumps({
                "active":     False,
                "text":       "🔥 Limited Time Offer — Free Shipping on orders above ₹999!",
                "bg_color":   "#FF6B35",
                "text_color": "#ffffff"
            })
        ))
        db.session.commit()
        print("   ✅  Default offer setting created.")
    else:
        print("   ℹ️   Offer setting already exists, skipping.")

    print("\n🎉  Migration complete! Your Supabase database is ready.")
    print("   You can now deploy app.py + models.py to Render.")
