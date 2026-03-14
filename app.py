"""
Claxxic India — Flask Backend (Phase 1)
Products served via API. Cart + Address stay in localStorage.
"""

from flask import Flask, jsonify, render_template, request, abort
from flask_cors import CORS
import json, os, copy

app = Flask(__name__)
CORS(app)

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "data", "products.json")

def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def fix_image_paths(products):
    """
    Prefix all image paths with /static/ so Flask serves them correctly.
    products.json stores: "shoes/nike/nike-air-jordan.jpg"
    Flask needs:          "/static/shoes/nike/nike-air-jordan.jpg"
    """
    result = copy.deepcopy(products)
    for p in result:
        if p.get("image") and not p["image"].startswith(("/static/", "http")):
            p["image"] = "/static/" + p["image"]
        if p.get("colors"):
            for c in p["colors"]:
                if c.get("image") and not c["image"].startswith(("/static/", "http")):
                    c["image"] = "/static/" + c["image"]
    return result


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


# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.route("/api/products")
def get_products():
    products  = load_products()
    brand     = request.args.get("brand")
    tag       = request.args.get("tag")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    search    = request.args.get("q", "").lower().strip()

    if brand:
        products = [p for p in products if p["brand"].lower() == brand.lower()]
    if tag:
        products = [p for p in products if p.get("tag") == tag]
    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if search:
        products = [p for p in products
                    if search in p["name"].lower() or search in p["brand"].lower()]

    return jsonify(fix_image_paths(products))


@app.route("/api/products/trending")
def get_trending():
    products = [p for p in load_products() if p.get("tag") == "trending"]
    return jsonify(fix_image_paths(products))


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
    products = [p for p in load_products()
                if q in p["name"].lower() or q in p["brand"].lower()]
    return jsonify(fix_image_paths(products))


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
