"""
Claxxic India — Flask Backend (Phase 2)
Products API + Order saving + Admin dashboard
"""

from flask import Flask, jsonify, render_template, request, abort, session, redirect, url_for
from flask_cors import CORS
from models import db, Order, OrderItem
import json, os, copy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"]        = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'claxxic.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"]                     = os.environ.get("SECRET_KEY", "claxxic-secret-2026")
ADMIN_PASSWORD                               = os.environ.get("ADMIN_PASSWORD", "claxxic@admin")
PRODUCTS_FILE                                = os.path.join(BASE_DIR, "data", "products.json")

db.init_app(app)

with app.app_context():
    db.create_all()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

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


# ── ADMIN ROUTES ──────────────────────────────────────────────────────────────

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

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    status_filter = request.args.get("status", "all")
    orders = Order.query.order_by(Order.created_at.desc())
    if status_filter != "all":
        orders = orders.filter_by(status=status_filter)
    orders = orders.all()

    # Stats
    all_orders   = Order.query.all()
    total_orders = len(all_orders)
    total_rev    = sum(o.total for o in all_orders)
    pending      = Order.query.filter_by(status="Pending").count()
    confirmed    = Order.query.filter_by(status="Confirmed").count()
    shipped      = Order.query.filter_by(status="Shipped").count()
    delivered    = Order.query.filter_by(status="Delivered").count()

    return render_template("admin.html",
        orders=orders,
        status_filter=status_filter,
        total_orders=total_orders,
        total_rev=format_inr(total_rev),
        pending=pending,
        confirmed=confirmed,
        shipped=shipped,
        delivered=delivered,
    )


# ── API ROUTES ────────────────────────────────────────────────────────────────

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
        abort(404, description=f"Product {product_id} not found")
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


@app.route("/api/orders", methods=["POST"])
def create_order():
    """
    Called from frontend when customer clicks 'Order via WhatsApp'.
    Saves the order to SQLite before opening WhatsApp.
    Body: { address: {...}, items: [...], total: 0 }
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No data received"}), 400

    addr  = data.get("address", {})
    items = data.get("items", [])
    total = data.get("total", 0)

    if not addr or not items:
        return jsonify({"error": "Missing address or items"}), 400

    try:
        order = Order(
            name     = addr.get("name", ""),
            phone    = addr.get("phone", ""),
            line1    = addr.get("line1", ""),
            line2    = addr.get("line2", ""),
            city     = addr.get("city", ""),
            state    = addr.get("state", ""),
            pin      = addr.get("pin", ""),
            landmark = addr.get("landmark", ""),
            total    = total,
            status   = "Pending",
        )
        db.session.add(order)
        db.session.flush()  # get order.id before commit

        for item in items:
            order_item = OrderItem(
                order_id   = order.id,
                product_id = item.get("id", 0),
                name       = item.get("name", ""),
                brand      = item.get("brand", ""),
                size       = item.get("size", ""),
                color      = item.get("color", ""),
                qty        = item.get("qty", 1),
                price      = item.get("price", 0),
                image      = item.get("image", ""),
            )
            db.session.add(order_item)

        db.session.commit()
        return jsonify({"success": True, "order_id": order.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/orders/<int:order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    """Admin — update order status"""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    order = Order.query.get_or_404(order_id)
    data  = request.get_json(force=True)
    new_status = data.get("status")

    valid = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]
    if new_status not in valid:
        return jsonify({"error": f"Invalid status. Must be one of: {valid}"}), 400

    order.status     = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "order_id": order_id, "status": new_status})


@app.route("/api/orders/<int:order_id>/notes", methods=["PATCH"])
def update_order_notes(order_id):
    """Admin — save notes on an order"""
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    order = Order.query.get_or_404(order_id)
    data  = request.get_json(force=True)
    order.notes      = data.get("notes", "")
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
