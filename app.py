"""
Claxxic India — Flask Backend (Supabase Edition, hardened startup)
- Falls back to products.json if DATABASE_URL is missing
- Logs clearly what mode it's running in
"""

from flask import (Flask, jsonify, render_template, request,
                   abort, session, redirect, url_for)
from flask_cors import CORS
from models import db, Product, Setting, Order, OrderItem
import json, os, copy, re
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR   = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
OFFER_FILE    = os.path.join(DATA_DIR, "offer.json")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_DB = bool(DATABASE_URL)

if USE_DB:
    print(f"[claxxic] ✅ DATABASE_URL found — using Supabase PostgreSQL")
    app.config["SQLALCHEMY_DATABASE_URI"]   = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle":  300,
        "connect_args":  {"connect_timeout": 10},
    }
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            print("[claxxic] ✅ Database tables ready")
        except Exception as e:
            print(f"[claxxic] ❌ DB init failed: {e}")
            USE_DB = False
else:
    print("[claxxic] ⚠️  No DATABASE_URL — falling back to products.json (READ ONLY)")
    # Still need to init db with a dummy URI so imports don't fail
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

app.config["SECRET_KEY"]         = os.environ.get("SECRET_KEY", "claxxic-secret-2026")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "claxxic@admin")
ALLOWED_EXT    = {"png", "jpg", "jpeg", "webp"}


# ── FILE FALLBACKS (used when USE_DB is False) ────────────────────────────────

def load_products_file():
    try:
        with open(PRODUCTS_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"[claxxic] ❌ Could not read products.json: {e}")
        return []

def load_offer_file():
    try:
        with open(OFFER_FILE) as f:
            return json.load(f)
    except:
        return {"active": False, "text": "", "bg_color": "#FF6B35", "text_color": "#ffffff"}

def save_offer_file(data):
    try:
        with open(OFFER_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[claxxic] ❌ Could not write offer.json: {e}")


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def get_offer():
    if USE_DB:
        row = Setting.query.get("offer")
        if row:
            try: return json.loads(row.value)
            except: pass
        return {"active": False, "text": "", "bg_color": "#FF6B35", "text_color": "#ffffff"}
    return load_offer_file()

def set_offer(data):
    if USE_DB:
        row = Setting.query.get("offer")
        if row:
            row.value = json.dumps(data)
        else:
            db.session.add(Setting(key="offer", value=json.dumps(data)))
        db.session.commit()
    else:
        save_offer_file(data)

def fix_image_paths(products_list):
    result = copy.deepcopy(products_list)
    for p in result:
        if p.get("image") and not p["image"].startswith(("/static/", "http")):
            p["image"] = "/static/" + p["image"]
        for c in p.get("colors", []):
            if c.get("image") and not c["image"].startswith(("/static/", "http")):
                c["image"] = "/static/" + c["image"]
    return result

def allowed_file(f): return "." in f and f.rsplit(".",1)[1].lower() in ALLOWED_EXT
def slugify(t): return re.sub(r"[^a-z0-9]+"," ",t.lower()).strip("-")
def format_inr(n): return f"₹{int(n):,}"

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ── PAGE ROUTES ───────────────────────────────────────────────────────────────

@app.route("/")
def index(): return render_template("index.html")

@app.route("/product")
def product(): return render_template("product.html")

@app.route("/brand")
def brand(): return render_template("brand.html")

@app.route("/cart")
def cart(): return render_template("cart.html")


# ── ADMIN AUTH ────────────────────────────────────────────────────────────────

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password."
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    if USE_DB:
        sf = request.args.get("status","all")
        q  = Order.query.order_by(Order.created_at.desc())
        if sf != "all": q = q.filter_by(status=sf)
        orders     = q.all()
        all_orders = Order.query.all()
        total_rev  = sum(o.total for o in all_orders)
        return render_template("admin.html",
            orders=orders, status_filter=sf,
            total_orders=len(all_orders), total_rev=format_inr(total_rev),
            pending=Order.query.filter_by(status="Pending").count(),
            confirmed=Order.query.filter_by(status="Confirmed").count(),
            shipped=Order.query.filter_by(status="Shipped").count(),
            delivered=Order.query.filter_by(status="Delivered").count(),
            offer=get_offer(),
        )
    return render_template("admin.html",
        orders=[], status_filter="all",
        total_orders=0, total_rev="₹0",
        pending=0, confirmed=0, shipped=0, delivered=0,
        offer=get_offer(),
    )


# ── ADMIN PRODUCTS ────────────────────────────────────────────────────────────

@app.route("/admin/products")
@admin_required
def admin_products():
    if USE_DB:
        products = [p.to_dict() for p in Product.query.order_by(Product.brand, Product.name).all()]
    else:
        products = load_products_file()
    brands = sorted(set(p["brand"] for p in products))
    return render_template("admin_products.html",
        products=products, brands=brands, offer=get_offer())


# ── PUBLIC API — PRODUCTS ─────────────────────────────────────────────────────

@app.route("/api/products")
def get_products():
    brand     = request.args.get("brand")
    tag       = request.args.get("tag")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    search    = request.args.get("q","").lower().strip()

    if USE_DB:
        q = Product.query
        if brand:     q = q.filter(db.func.lower(Product.brand) == brand.lower())
        if tag:       q = q.filter(Product.tag == tag)
        if min_price: q = q.filter(Product.price >= min_price)
        if max_price: q = q.filter(Product.price <= max_price)
        if search:    q = q.filter(db.or_(Product.name.ilike(f"%{search}%"), Product.brand.ilike(f"%{search}%")))
        products = [p.to_dict() for p in q.all()]
    else:
        products = load_products_file()
        if brand:     products = [p for p in products if p["brand"].lower() == brand.lower()]
        if tag:       products = [p for p in products if p.get("tag") == tag]
        if min_price: products = [p for p in products if p["price"] >= min_price]
        if max_price: products = [p for p in products if p["price"] <= max_price]
        if search:    products = [p for p in products if search in p["name"].lower() or search in p["brand"].lower()]

    return jsonify(fix_image_paths(products))

@app.route("/api/products/trending")
def get_trending():
    if USE_DB:
        products = [p.to_dict() for p in Product.query.filter_by(tag="trending").all()]
    else:
        products = [p for p in load_products_file() if p.get("tag") == "trending"]
    return jsonify(fix_image_paths(products))

@app.route("/api/products/<int:product_id>")
def get_product(product_id):
    if USE_DB:
        p = Product.query.get(product_id)
        if not p: abort(404)
        return jsonify(fix_image_paths([p.to_dict()])[0])
    else:
        p = next((p for p in load_products_file() if p["id"] == product_id), None)
        if not p: abort(404)
        return jsonify(fix_image_paths([p])[0])

@app.route("/api/brands")
def get_brands():
    if USE_DB:
        from sqlalchemy import func
        rows = db.session.query(Product.brand, func.count(Product.id)).group_by(Product.brand).all()
        return jsonify([{"name": b, "count": c} for b, c in rows])
    else:
        bmap = {}
        for p in load_products_file():
            bmap[p["brand"]] = bmap.get(p["brand"], 0) + 1
        return jsonify([{"name": b, "count": c} for b, c in bmap.items()])

@app.route("/api/search")
def search_products():
    q = request.args.get("q","").lower().strip()
    if not q: return jsonify([])
    if USE_DB:
        products = [p.to_dict() for p in Product.query.filter(
            db.or_(Product.name.ilike(f"%{q}%"), Product.brand.ilike(f"%{q}%"))).all()]
    else:
        products = [p for p in load_products_file()
                    if q in p["name"].lower() or q in p["brand"].lower()]
    return jsonify(fix_image_paths(products))

@app.route("/api/offer")
def api_get_offer():
    return jsonify(get_offer())


# ── ADMIN API — PRODUCTS CRUD ─────────────────────────────────────────────────

@app.route("/api/admin/products", methods=["POST"])
@admin_required
def api_add_product():
    if not USE_DB:
        return jsonify({"error": "Database not connected. Set DATABASE_URL on Render."}), 503
    data  = request.get_json(force=True)
    name  = data.get("name","").strip()
    brand = data.get("brand","").strip()
    price = int(data.get("price", 0))
    if not name or not brand or not price:
        return jsonify({"error": "name, brand and price are required"}), 400
    p = Product(name=name, brand=brand, price=price,
                image=data.get("image",""), tag=data.get("tag",""),
                sizes=json.dumps(data.get("sizes",[])),
                colors=json.dumps(data.get("colors",[])))
    db.session.add(p)
    db.session.commit()
    return jsonify({"success": True, "product": p.to_dict()}), 201

@app.route("/api/admin/products/<int:product_id>", methods=["PUT"])
@admin_required
def api_update_product(product_id):
    if not USE_DB:
        return jsonify({"error": "Database not connected"}), 503
    p = Product.query.get(product_id)
    if not p: return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    p.name   = data.get("name",   p.name)
    p.brand  = data.get("brand",  p.brand)
    p.price  = int(data.get("price", p.price))
    p.image  = data.get("image",  p.image)
    p.tag    = data.get("tag",    p.tag or "")
    p.sizes  = json.dumps(data.get("sizes",  json.loads(p.sizes  or "[]")))
    p.colors = json.dumps(data.get("colors", json.loads(p.colors or "[]")))
    db.session.commit()
    return jsonify({"success": True, "product": p.to_dict()})

@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def api_delete_product(product_id):
    if not USE_DB:
        return jsonify({"error": "Database not connected"}), 503
    p = Product.query.get(product_id)
    if not p: return jsonify({"error": "Not found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/admin/upload-image", methods=["POST"])
@admin_required
def api_upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No file"}), 400
    file  = request.files["image"]
    brand = request.form.get("brand","misc")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    brand_slug = slugify(brand)
    upload_dir = os.path.join(STATIC_DIR, "shoes", brand_slug)
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    file.save(os.path.join(upload_dir, filename))
    path = f"shoes/{brand_slug}/{filename}"
    return jsonify({"success": True, "path": path, "url": f"/static/{path}"})


# ── ADMIN API — OFFER ─────────────────────────────────────────────────────────

@app.route("/api/admin/offer", methods=["POST"])
@admin_required
def api_save_offer():
    data = request.get_json(force=True)
    offer = {
        "active":     bool(data.get("active", False)),
        "text":       data.get("text","").strip(),
        "bg_color":   data.get("bg_color","#FF6B35"),
        "text_color": data.get("text_color","#ffffff"),
    }
    set_offer(offer)
    return jsonify({"success": True, "offer": offer})


# ── API — ORDERS ──────────────────────────────────────────────────────────────

@app.route("/api/orders", methods=["POST"])
def create_order():
    if not USE_DB:
        return jsonify({"success": True, "order_id": 0})  # silently skip
    data  = request.get_json(force=True)
    addr  = data.get("address",{})
    items = data.get("items",[])
    total = data.get("total",0)
    if not addr or not items:
        return jsonify({"error": "Missing address or items"}), 400
    try:
        order = Order(
            name=addr.get("name",""),   phone=addr.get("phone",""),
            line1=addr.get("line1",""), line2=addr.get("line2",""),
            city=addr.get("city",""),   state=addr.get("state",""),
            pin=addr.get("pin",""),     landmark=addr.get("landmark",""),
            total=total, status="Pending",
        )
        db.session.add(order)
        db.session.flush()
        for item in items:
            db.session.add(OrderItem(
                order_id=order.id, product_id=item.get("id",0),
                name=item.get("name",""), brand=item.get("brand",""),
                size=item.get("size",""), color=item.get("color",""),
                qty=item.get("qty",1), price=item.get("price",0),
                image=item.get("image",""),
            ))
        db.session.commit()
        return jsonify({"success": True, "order_id": order.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    if not USE_DB: return jsonify({"error": "No DB"}), 503
    order = Order.query.get_or_404(order_id)
    new_status = request.get_json(force=True).get("status")
    if new_status not in ["Pending","Confirmed","Shipped","Delivered","Cancelled"]:
        return jsonify({"error": "Invalid status"}), 400
    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "status": new_status})

@app.route("/api/orders/<int:order_id>/notes", methods=["PATCH"])
@admin_required
def update_order_notes(order_id):
    if not USE_DB: return jsonify({"error": "No DB"}), 503
    order = Order.query.get_or_404(order_id)
    order.notes = request.get_json(force=True).get("notes","")
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


# ── ERRORS ────────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e): return jsonify({"error": str(e)}), 404

@app.errorhandler(500)
def server_error(e): return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
