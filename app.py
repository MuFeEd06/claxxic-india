"""
Claxxic India — Flask Backend (Phase 2 + Product Editor + Offer Ribbon)
"""

from flask import (Flask, jsonify, render_template, request,
                   abort, session, redirect, url_for)
from flask_cors import CORS
from models import db, Order, OrderItem
import json, os, copy, re
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(BASE_DIR, "data")
STATIC_DIR    = os.path.join(BASE_DIR, "static")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
OFFER_FILE    = os.path.join(DATA_DIR, "offer.json")

app.config["SQLALCHEMY_DATABASE_URI"]        = f"sqlite:///{os.path.join(DATA_DIR, 'claxxic.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"]                     = os.environ.get("SECRET_KEY", "claxxic-secret-2026")
app.config["MAX_CONTENT_LENGTH"]             = 5 * 1024 * 1024  # 5MB max upload

ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "claxxic@admin")
ALLOWED_EXT     = {"png", "jpg", "jpeg", "webp"}

db.init_app(app)
with app.app_context():
    db.create_all()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def load_offer():
    try:
        with open(OFFER_FILE, "r") as f:
            return json.load(f)
    except:
        return {"active": False, "text": "", "bg_color": "#FF6B35", "text_color": "#ffffff"}

def save_offer(data):
    with open(OFFER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fix_image_paths(products):
    result = copy.deepcopy(products)
    for p in result:
        if p.get("image") and not p["image"].startswith(("/static/", "http")):
            p["image"] = "/static/" + p["image"]
        if p.get("colors"):
            for c in p["colors"]:
                if c.get("image") and not c["image"].startswith(("/static/", "http")):
                    c["image"] = "/static/" + c["image"]
    return result

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def format_inr(amount):
    return f"₹{int(amount):,}"

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ── PAGE ROUTES ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/product")
def product():
    return render_template("product.html")

@app.route("/brand")
def brand():
    return render_template("brand.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")


# ── ADMIN AUTH ────────────────────────────────────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password. Try again."
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    status_filter = request.args.get("status", "all")
    orders = Order.query.order_by(Order.created_at.desc())
    if status_filter != "all":
        orders = orders.filter_by(status=status_filter)
    orders = orders.all()

    all_orders   = Order.query.all()
    total_orders = len(all_orders)
    total_rev    = sum(o.total for o in all_orders)

    return render_template("admin.html",
        orders        = orders,
        status_filter = status_filter,
        total_orders  = total_orders,
        total_rev     = format_inr(total_rev),
        pending       = Order.query.filter_by(status="Pending").count(),
        confirmed     = Order.query.filter_by(status="Confirmed").count(),
        shipped       = Order.query.filter_by(status="Shipped").count(),
        delivered     = Order.query.filter_by(status="Delivered").count(),
        offer         = load_offer(),
    )


# ── ADMIN — PRODUCT EDITOR ────────────────────────────────────────────────────

@app.route("/admin/products")
@admin_required
def admin_products():
    products = load_products()
    brands   = sorted(set(p["brand"] for p in products))
    return render_template("admin_products.html",
        products = products,
        brands   = brands,
        offer    = load_offer(),
    )


# ── API — PRODUCTS (public) ───────────────────────────────────────────────────

@app.route("/api/products")
def get_products():
    products  = load_products()
    brand     = request.args.get("brand")
    tag       = request.args.get("tag")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    search    = request.args.get("q", "").lower().strip()

    if brand:     products = [p for p in products if p["brand"].lower() == brand.lower()]
    if tag:       products = [p for p in products if p.get("tag") == tag]
    if min_price: products = [p for p in products if p["price"] >= min_price]
    if max_price: products = [p for p in products if p["price"] <= max_price]
    if search:    products = [p for p in products if search in p["name"].lower() or search in p["brand"].lower()]

    return jsonify(fix_image_paths(products))

@app.route("/api/products/trending")
def get_trending():
    return jsonify(fix_image_paths([p for p in load_products() if p.get("tag") == "trending"]))

@app.route("/api/products/<int:product_id>")
def get_product(product_id):
    product = next((p for p in load_products() if p["id"] == product_id), None)
    if not product:
        abort(404)
    return jsonify(fix_image_paths([product])[0])

@app.route("/api/brands")
def get_brands():
    brand_map = {}
    for p in load_products():
        brand_map[p["brand"]] = brand_map.get(p["brand"], 0) + 1
    return jsonify([{"name": b, "count": c} for b, c in brand_map.items()])

@app.route("/api/search")
def search_products():
    q = request.args.get("q", "").lower().strip()
    if not q:
        return jsonify([])
    return jsonify(fix_image_paths([p for p in load_products()
                                    if q in p["name"].lower() or q in p["brand"].lower()]))

@app.route("/api/offer")
def get_offer():
    return jsonify(load_offer())


# ── API — PRODUCTS CRUD (admin) ───────────────────────────────────────────────

@app.route("/api/admin/products", methods=["POST"])
@admin_required
def api_add_product():
    """Add a new product"""
    data     = request.get_json(force=True)
    products = load_products()
    new_id   = max((p["id"] for p in products), default=0) + 1

    product = {
        "id":     new_id,
        "name":   data.get("name", "").strip(),
        "brand":  data.get("brand", "").strip(),
        "price":  int(data.get("price", 0)),
        "image":  data.get("image", ""),
        "sizes":  data.get("sizes", []),
        "tag":    data.get("tag", ""),
        "colors": data.get("colors", []),
    }

    if not product["name"] or not product["brand"] or not product["price"]:
        return jsonify({"error": "name, brand and price are required"}), 400

    products.append(product)
    save_products(products)
    return jsonify({"success": True, "product": product}), 201


@app.route("/api/admin/products/<int:product_id>", methods=["PUT"])
@admin_required
def api_update_product(product_id):
    """Update an existing product"""
    data     = request.get_json(force=True)
    products = load_products()
    idx      = next((i for i, p in enumerate(products) if p["id"] == product_id), None)

    if idx is None:
        return jsonify({"error": "Product not found"}), 404

    p = products[idx]
    p["name"]   = data.get("name",   p["name"])
    p["brand"]  = data.get("brand",  p["brand"])
    p["price"]  = int(data.get("price", p["price"]))
    p["image"]  = data.get("image",  p["image"])
    p["sizes"]  = data.get("sizes",  p["sizes"])
    p["tag"]    = data.get("tag",    p.get("tag", ""))
    p["colors"] = data.get("colors", p.get("colors", []))

    products[idx] = p
    save_products(products)
    return jsonify({"success": True, "product": p})


@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def api_delete_product(product_id):
    """Delete a product"""
    products = load_products()
    original = len(products)
    products = [p for p in products if p["id"] != product_id]

    if len(products) == original:
        return jsonify({"error": "Product not found"}), 404

    save_products(products)
    return jsonify({"success": True})


@app.route("/api/admin/upload-image", methods=["POST"])
@admin_required
def api_upload_image():
    """Upload a product image — saves to static/shoes/<brand_slug>/"""
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file  = request.files["image"]
    brand = request.form.get("brand", "misc")

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Use JPG, PNG or WEBP"}), 400

    brand_slug = slugify(brand)
    upload_dir = os.path.join(STATIC_DIR, "shoes", brand_slug)
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    relative_path = f"shoes/{brand_slug}/{filename}"
    return jsonify({"success": True, "path": relative_path,
                    "url": f"/static/{relative_path}"})


# ── API — OFFER (admin) ───────────────────────────────────────────────────────

@app.route("/api/admin/offer", methods=["POST"])
@admin_required
def api_save_offer():
    data = request.get_json(force=True)
    offer = {
        "active":     bool(data.get("active", False)),
        "text":       data.get("text", "").strip(),
        "bg_color":   data.get("bg_color", "#FF6B35"),
        "text_color": data.get("text_color", "#ffffff"),
    }
    save_offer(offer)
    return jsonify({"success": True, "offer": offer})


# ── API — ORDERS ──────────────────────────────────────────────────────────────

@app.route("/api/orders", methods=["POST"])
def create_order():
    data  = request.get_json(force=True)
    addr  = data.get("address", {})
    items = data.get("items", [])
    total = data.get("total", 0)

    if not addr or not items:
        return jsonify({"error": "Missing address or items"}), 400

    try:
        order = Order(
            name=addr.get("name",""), phone=addr.get("phone",""),
            line1=addr.get("line1",""), line2=addr.get("line2",""),
            city=addr.get("city",""), state=addr.get("state",""),
            pin=addr.get("pin",""), landmark=addr.get("landmark",""),
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
    order      = Order.query.get_or_404(order_id)
    new_status = request.get_json(force=True).get("status")
    valid      = ["Pending","Confirmed","Shipped","Delivered","Cancelled"]
    if new_status not in valid:
        return jsonify({"error": f"Invalid status"}), 400
    order.status     = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "status": new_status})


@app.route("/api/orders/<int:order_id>/notes", methods=["PATCH"])
@admin_required
def update_order_notes(order_id):
    order        = Order.query.get_or_404(order_id)
    order.notes  = request.get_json(force=True).get("notes", "")
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True})


# ── ERROR HANDLERS ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
