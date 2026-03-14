/* =================================================
   BRAND DEFINITIONS — local logo images
   All logos go in: logo/brands/<slug>.png
================================================= */
const BRANDS = [
    { name: "Nike",          slug: "Nike",          color: "#FF6B35", logo: "/static/logo/brands/nike.png" },
    { name: "Adidas",        slug: "Adidas",        color: "#00B4D8", logo: "/static/logo/brands/adidas.png" },
    { name: "New Balance",   slug: "New Balance",   color: "#4CAF50", logo: "/static/logo/brands/newbalance.png" },
    { name: "Vans",          slug: "Vans",          color: "#FF3CAC", logo: "/static/logo/brands/vans.png" },
    { name: "Converse",      slug: "Converse",      color: "#F72585", logo: "/static/logo/brands/converse.png" },
    { name: "Puma",          slug: "Puma",          color: "#FFD60A", logo: "/static/logo/brands/puma.png" },
    { name: "Reebok",        slug: "Reebok",        color: "#7B2FBE", logo: "/static/logo/brands/reebok.png" },
    { name: "Asics",         slug: "Asics",         color: "#E63946", logo: "/static/logo/brands/asics.png" },
    { name: "Sketchers",     slug: "Sketchers",     color: "#2EC4B6", logo: "/static/logo/brands/sketchers.png" },
    { name: "On",            slug: "On",            color: "#F4A261", logo: "/static/logo/brands/on.png" },
    { name: "Onitsuka",      slug: "Onitsuka",      color: "#C77DFF", logo: "/static/logo/brands/onitsuka.png" },
    { name: "Lacoste",       slug: "Lacoste",       color: "#52B788", logo: "/static/logo/brands/lacoste.png" },
    { name: "Brooks",        slug: "Brooks",        color: "#FF6B6B", logo: "/static/logo/brands/brooks.png" },
    { name: "Timb",          slug: "Timb",          color: "#D4A373", logo: "/static/logo/brands/timb.png" },
    { name: "Brik",          slug: "Brik",          color: "#ADB5BD", logo: "/static/logo/brands/brik.png" },
    { name: "Alo",           slug: "Alo",           color: "#9BF5C8", logo: "/static/logo/brands/alo.png" },
    { name: "Louis Vuitton", slug: "Louis Vuitton", color: "#C9A84C", logo: "/static/logo/brands/louisvuitton.png" },
];

function getBrandConfig(name) {
    return BRANDS.find(b => b.slug.toLowerCase() === name.toLowerCase())
        || { initials: name.slice(0,2).toUpperCase(), color: "#7CFFB2" };
}


/* =================================================
   CART SYSTEM — localStorage persistence
================================================= */

const WHATSAPP_NUMBER = "918606466821"; // ← change to your number

function getCart() {
    return JSON.parse(localStorage.getItem("claxxic_cart") || "[]");
}

function saveCart(cart) {
    localStorage.setItem("claxxic_cart", JSON.stringify(cart));
    updateCartBadge();
}

function updateCartBadge() {
    const cart = getCart();
    const total = cart.reduce((sum, item) => sum + item.qty, 0);
    document.querySelectorAll("#cart-count").forEach(el => el.textContent = total);
}

/* helper — get currently selected color name */
function getSelectedColor() {
    const active = document.querySelector(".color-swatch.active");
    return active ? active.title : "";
}

/* helper — read live displayed price (updates when color changes) */
function getCurrentPrice() {
    const raw = document.getElementById("product-price")?.innerText || "₹0";
    return parseInt(raw.replace(/[^0-9]/g, "")) || 0;
}

function addToCartWithSize() {
    const size = document.getElementById("size-select").value;
    if (!size) { showToast("Please select a size first"); return; }

    const id    = parseInt(localStorage.getItem("productId"));
    const name  = document.getElementById("product-name")?.innerText || "";
    const image = document.getElementById("product-img")?.src || "";
    const brand = name.split(" ")[0];
    const color = getSelectedColor();
    const numericPrice = getCurrentPrice(); // reads live color price

    const cart     = getCart();
    const existing = cart.find(i => i.id === id && i.size === size && i.color === color);

    if (existing) {
        existing.qty++;
    } else {
        cart.push({ id, name, brand, price: numericPrice, image, size, color, qty: 1 });
    }

    saveCart(cart);
    showToast(`Added to cart — ${size}${color ? " · " + color : ""}`);
}

/* Buy Now — add to cart then go straight to cart page */
function buyNow() {
    const size = document.getElementById("size-select").value;
    if (!size) { showToast("Please select a size first"); return; }

    const id    = parseInt(localStorage.getItem("productId"));
    const name  = document.getElementById("product-name")?.innerText || "";
    const image = document.getElementById("product-img")?.src || "";
    const brand = name.split(" ")[0];
    const color = getSelectedColor();
    const numericPrice = getCurrentPrice();

    const cart     = getCart();
    const existing = cart.find(i => i.id === id && i.size === size && i.color === color);

    if (existing) {
        existing.qty++;
    } else {
        cart.push({ id, name, brand, price: numericPrice, image, size, color, qty: 1 });
    }

    saveCart(cart);
    window.location.href = "/cart";
}

/* ── TOAST ── */
function showToast(msg) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2500);
}

/* ── FORMAT PRICE ── */
function formatPrice(num) {
    return "₹" + num.toLocaleString("en-IN");
}

/* =================================================
   CART PAGE RENDERING
================================================= */
function renderCartPage() {
    const listEl      = document.getElementById("cart-items-list");
    const emptyEl     = document.getElementById("cart-empty");
    const layoutEl    = document.getElementById("cart-layout");
    const subtitleEl  = document.getElementById("cart-subtitle");

    if (!listEl) return; // Not on cart page

    const cart = getCart();
    updateCartBadge();

    if (cart.length === 0) {
        emptyEl.style.display  = "block";
        layoutEl.style.display = "none";
        if (subtitleEl) subtitleEl.textContent = "";
        return;
    }

    emptyEl.style.display  = "none";
    layoutEl.style.display = "grid";

    const totalItems = cart.reduce((s, i) => s + i.qty, 0);
    if (subtitleEl) subtitleEl.textContent = `${totalItems} item${totalItems !== 1 ? "s" : ""} in your cart`;

    listEl.innerHTML = "";
    cart.forEach((item, idx) => {
        const row = document.createElement("div");
        row.className = "cart-item fade-in";

        const colorChip = item.color
            ? `<span class="cart-item-color">
                   <span class="cart-color-dot" style="background:${getColorHex(item.color)}"></span>
                   ${item.color}
               </span>`
            : "";

        row.innerHTML = `
            <img class="cart-item-img"
                 src="${item.image}"
                 alt="${item.name}"
                 onerror="this.src='https://placehold.co/90x90/eaf3fa/2B9FD8?text=👟'">

            <div class="cart-item-details">
                <span class="cart-item-brand">${item.brand}</span>
                <span class="cart-item-name">${item.name}</span>
                <span class="cart-item-size">Size: <span>${item.size}</span></span>
                ${colorChip}
                <span class="cart-item-price">${formatPrice(item.price)}</span>
            </div>

            <div class="cart-item-controls">
                <div class="qty-control">
                    <button class="qty-btn" onclick="changeQty(${idx}, -1)">−</button>
                    <span class="qty-value">${item.qty}</span>
                    <button class="qty-btn" onclick="changeQty(${idx}, 1)">+</button>
                </div>
                <button class="remove-btn" onclick="removeItem(${idx})">Remove</button>
            </div>
        `;
        listEl.appendChild(row);
    });

    updateSummary(cart);
    initScrollAnimation();
}

function changeQty(idx, delta) {
    const cart = getCart();
    cart[idx].qty += delta;
    if (cart[idx].qty <= 0) cart.splice(idx, 1);
    saveCart(cart);
    renderCartPage();
}

function removeItem(idx) {
    const cart = getCart();
    const removed = cart.splice(idx, 1)[0];
    saveCart(cart);
    showToast(`${removed.name} removed`);
    renderCartPage();
}

/* helper — get color hex from cached products for cart color dot */
function getColorHex(colorName) {
    try {
        const cached = JSON.parse(localStorage.getItem("claxxic_products") || "[]");
        for (const p of cached) {
            if (!p.colors) continue;
            const match = p.colors.find(c => c.name === colorName);
            if (match) return match.hex;
        }
    } catch {}
    return "#aaa";
}

function updateSummary(cart) {
    const subtotal   = cart.reduce((sum, i) => sum + i.price * i.qty, 0);
    const totalItems = cart.reduce((sum, i) => sum + i.qty, 0);

    const countEl    = document.getElementById("summary-count");
    const subtotalEl = document.getElementById("summary-subtotal");
    const totalEl    = document.getElementById("summary-total");
    const waBtn      = document.getElementById("whatsapp-checkout");
    const noteEl     = document.getElementById("address-required-note");

    if (countEl)    countEl.textContent    = totalItems;
    if (subtotalEl) subtotalEl.textContent = formatPrice(subtotal);
    if (totalEl)    totalEl.textContent    = formatPrice(subtotal);

    // Always re-render address display
    const addr = getSavedAddress();
    renderAddressDisplay(addr);

    if (waBtn) {
        if (!addr) {
            // No address — block WhatsApp button
            waBtn.style.opacity       = "0.45";
            waBtn.style.pointerEvents = "none";
            waBtn.style.cursor        = "not-allowed";
            if (noteEl) noteEl.style.display = "block";
        } else {
            waBtn.style.opacity       = "1";
            waBtn.style.pointerEvents = "auto";
            waBtn.style.cursor        = "pointer";
            if (noteEl) noteEl.style.display = "none";

            // Rich WhatsApp message with color + image + address
            let msg = "🛒 *New Order — Claxxic India*\n\n";
            msg += "👟 *Items Ordered:*\n";
            cart.forEach((item, i) => {
                msg += `\n${i + 1}. *${item.name}*\n`;
                msg += `   Brand: ${item.brand}\n`;
                msg += `   Size: ${item.size}\n`;
                if (item.color) msg += `   Color: ${item.color}\n`;
                msg += `   Qty: ${item.qty}\n`;
                msg += `   Price: ${formatPrice(item.price * item.qty)}\n`;
                if (item.image) {
                    const imgUrl = item.image.startsWith("http")
                        ? item.image
                        : `${window.location.origin}${item.image}`;
                    msg += `   🖼 Image: ${imgUrl}\n`;
                }
            });
            msg += `\n━━━━━━━━━━━━━\n`;
            msg += `💰 *Total: ${formatPrice(subtotal)}*\n`;
            msg += `🚚 Shipping: FREE\n\n`;
            msg += `📍 *Delivery Address:*\n`;
            msg += `${addr.name}\n`;
            msg += `${addr.phone}\n`;
            msg += `${addr.line1}${addr.line2 ? ", " + addr.line2 : ""}\n`;
            msg += `${addr.city}, ${addr.state} — ${addr.pin}\n`;
            if (addr.landmark) msg += `Landmark: ${addr.landmark}\n`;
            msg += `\nPlease confirm my order! 🙏`;

            const waUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
            waBtn.href = waUrl;

            // Also intercept click to save order to database first
            waBtn.onclick = async function(e) {
                e.preventDefault();
                await saveOrderToServer(cart, addr, subtotal);
                window.open(waUrl, "_blank");
            };
        }
    }
}


/* =================================================
   SAVE ORDER TO SERVER (Phase 2)
   Called when customer clicks Order via WhatsApp
================================================= */
async function saveOrderToServer(cart, addr, total) {
    try {
        await fetch("/api/orders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ address: addr, items: cart, total })
        });
    } catch (e) {
        console.warn("Could not save order to server:", e);
        // Still let WhatsApp open even if server save fails
    }
}


/* =================================================
   ADDRESS SYSTEM — localStorage
================================================= */
function getSavedAddress() {
    try {
        const raw = localStorage.getItem("claxxic_address");
        return raw ? JSON.parse(raw) : null;
    } catch { return null; }
}

function saveAddress() {
    const get = id => document.getElementById(id)?.value.trim() || "";
    const name     = get("addr-name");
    const phone    = get("addr-phone");
    const line1    = get("addr-line1");
    const line2    = get("addr-line2");
    const city     = get("addr-city");
    const state    = get("addr-state");
    const pin      = get("addr-pin");
    const landmark = get("addr-landmark");

    if (!name || !phone || !line1 || !city || !state || !pin) {
        showToast("Please fill all required (*) fields");
        return;
    }
    localStorage.setItem("claxxic_address", JSON.stringify(
        { name, phone, line1, line2, city, state, pin, landmark }
    ));
    document.getElementById("address-form")?.classList.remove("open");
    showToast("✓ Address saved");
    updateSummary(getCart());
}

function renderAddressDisplay(addr) {
    const displayEl = document.getElementById("address-display");
    const editBtn   = document.getElementById("address-edit-btn");
    if (!displayEl) return;
    if (!addr) {
        displayEl.innerHTML = `<p class="address-missing">No address saved. Add your delivery address to place an order.</p>`;
        if (editBtn) editBtn.textContent = "+ Add Address";
    } else {
        displayEl.innerHTML = `
            <div class="address-display">
                <strong>${addr.name} &nbsp;·&nbsp; ${addr.phone}</strong>
                ${addr.line1}${addr.line2 ? ", " + addr.line2 : ""}<br>
                ${addr.city}, ${addr.state} — ${addr.pin}
                ${addr.landmark ? `<br><span style="color:var(--text-light);font-size:0.82rem;">Near: ${addr.landmark}</span>` : ""}
            </div>`;
        if (editBtn) editBtn.textContent = "✏️ Edit";
    }
}

function toggleAddressForm() {
    const form = document.getElementById("address-form");
    if (!form) return;
    const isOpen = form.classList.contains("open");
    if (!isOpen) {
        const addr = getSavedAddress();
        if (addr) {
            document.getElementById("addr-name").value     = addr.name     || "";
            document.getElementById("addr-phone").value    = addr.phone    || "";
            document.getElementById("addr-line1").value    = addr.line1    || "";
            document.getElementById("addr-line2").value    = addr.line2    || "";
            document.getElementById("addr-city").value     = addr.city     || "";
            document.getElementById("addr-state").value    = addr.state    || "";
            document.getElementById("addr-pin").value      = addr.pin      || "";
            document.getElementById("addr-landmark").value = addr.landmark || "";
        }
        form.classList.add("open");
    } else {
        form.classList.remove("open");
    }
}


/* =================================================
   THREE.JS 3D SNEAKER SCENE (HOMEPAGE ONLY)
================================================= */
const container = document.getElementById("sneaker-container");

if (container) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, precision: "mediump" });

    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 1.4));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    let sneaker;
    const loader = new THREE.GLTFLoader();
    loader.setMeshoptDecoder(MeshoptDecoder);
    loader.load("/static/sneaker.glb",
        gltf => { sneaker = gltf.scene; sneaker.scale.set(3, 3, 3); scene.add(sneaker); },
        undefined,
        err => console.error("Model loading error:", err)
    );

    camera.position.set(0, 0.8, 12);
    let introAnimation = true, introProgress = 0, floatTime = 0;
    let mouseX = 0, mouseY = 0;

    document.addEventListener("mousemove", e => {
        const rect = container.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / rect.width) - 0.5;
        mouseY = ((e.clientY - rect.top) / rect.height) - 0.5;
    });

    function animate() {
        requestAnimationFrame(animate);
        if (sneaker) {
            if (introAnimation) {
                introProgress += 0.02;
                camera.position.z = 12 - introProgress * 8;
                sneaker.rotation.y += 0.006;
                if (camera.position.z <= 4) { camera.position.z = 4; introAnimation = false; }
            } else {
                sneaker.rotation.y += 0.001 + mouseX * 0.02;
                sneaker.rotation.x = -mouseY * 0.2;
                floatTime += 0.03;
                sneaker.position.y = Math.sin(floatTime) * 0.15;
            }
        }
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener("resize", () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}


function getBrandConfig(name) {
    return BRANDS.find(b => b.slug.toLowerCase() === name.toLowerCase())
        || { logo: null, color: "#2B9FD8", name };
}

/* =================================================
   BRAND TILES (HOMEPAGE)
================================================= */
function renderBrandTiles() {
    const grid = document.getElementById("brand-tiles-grid");
    if (!grid) return;
    grid.innerHTML = "";

    BRANDS.forEach((brand, i) => {
        const tile = document.createElement("a");
        tile.className = "brand-tile fade-in";
        tile.href = `/brand?brand=${encodeURIComponent(brand.slug)}`;
        tile.style.transitionDelay = `${i * 0.04}s`;

        const initials = brand.name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

        tile.innerHTML = `
            <div class="brand-tile-icon" style="border:1.5px solid ${brand.color}44;">
                <img src="${brand.logo}"
                     alt="${brand.name}"
                     class="brand-logo-img"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <span class="brand-logo-fallback" style="display:none; color:${brand.color}; font-weight:900; font-size:1.1rem; background:${brand.color}18; width:100%; height:100%; border-radius:10px;">
                    ${initials}
                </span>
            </div>
            <span class="brand-tile-name">${brand.name}</span>
            <span class="brand-tile-arrow" style="color:${brand.color}80">→</span>
        `;
        grid.appendChild(tile);
    });

    initScrollAnimation();
}


/* =================================================
   PRODUCT UTILITIES
================================================= */
async function fetchProducts() {
    const res  = await fetch("/api/products");
    const data = await res.json();
    try { localStorage.setItem("claxxic_products", JSON.stringify(data)); } catch {}
    return data;
}

/* =================================================
   RATING SYSTEM
   Deterministic per product ID so rating stays
   consistent across page visits
================================================= */
function getRating(id) {
    // Seeded pseudo-random so same product always gets same rating
    const seed  = (id * 9301 + 49297) % 233280;
    const rand  = seed / 233280;
    // Score between 3.5 and 5.0, one decimal place
    const score = Math.round((3.5 + rand * 1.5) * 10) / 10;
    // Review count between 18 and 420
    const count = 18 + Math.floor(((id * 6271 + 28411) % 233280) / 233280 * 402);
    return { score, count };
}

function buildStars(score, size = "sm") {
    const full  = Math.floor(score);
    const half  = score % 1 >= 0.5 ? 1 : 0;
    const empty = 5 - full - half;
    const cls   = `star star-${size}`;
    let html = "";
    for (let i = 0; i < full;  i++) html += `<span class="${cls} star-full">★</span>`;
    if (half)                        html += `<span class="${cls} star-half">★</span>`;
    for (let i = 0; i < empty; i++) html += `<span class="${cls} star-empty">★</span>`;
    return html;
}

function buildProductCard(shoe) {
    const { score, count } = getRating(shoe.id);
    return `
    <div class="card fade-in">
        <img src="${shoe.image}" alt="${shoe.name}"
             onerror="this.src='https://placehold.co/280x180/eaf3fa/2B9FD8?text=No+Image'">
        <div class="card-info">
            <p class="brand-label">${shoe.brand}</p>
            <h3>${shoe.name}</h3>
            <div class="card-rating">
                <div class="stars">${buildStars(score, "sm")}</div>
                <span class="card-rating-score">${score} (${count})</span>
            </div>
            <span class="price">${formatPrice(shoe.price)}</span>
            <button onclick="openProduct(${shoe.id})">View Product</button>
        </div>
    </div>`;
}


/* =================================================
   TRENDING PRODUCTS (HOMEPAGE)
================================================= */
async function renderTrendingShoes() {
    const grid = document.getElementById("main-product-grid");
    if (!grid) return;

    try {
        const products = await fetchProducts();
        const trending = products.filter(p => p.tag === "trending");
        grid.innerHTML = "";
        trending.forEach(shoe => { grid.innerHTML += buildProductCard(shoe); });
        initScrollAnimation();
    } catch (err) {
        console.error("Failed to load trending shoes:", err);
    }
}


/* =================================================
   BRAND PAGE
================================================= */
async function renderBrandPage() {
    const monogramEl   = document.getElementById("brand-monogram");
    const titleEl      = document.getElementById("brand-title");
    const countEl      = document.getElementById("brand-count");
    const sectionTitle = document.getElementById("brand-section-title");
    const grid         = document.getElementById("brand-product-grid");
    if (!grid) return;

    const params    = new URLSearchParams(window.location.search);
    const brandName = params.get("brand") || "";
    const brandCfg  = getBrandConfig(brandName);

    document.title = `${brandName} — Claxxic India`;

    // Show logo in hero
    if (monogramEl) {
        const initials = brandName.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase();
        monogramEl.style.background = `${brandCfg.color}18`;
        monogramEl.style.border     = `1px solid ${brandCfg.color}44`;
        monogramEl.style.padding    = "14px";
        monogramEl.innerHTML = brandCfg.logo
            ? `<img src="${brandCfg.logo}" alt="${brandName}"
                    style="width:100%;height:100%;object-fit:contain;"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
               <span style="display:none;font-weight:900;color:${brandCfg.color};font-size:1.4rem;">${initials}</span>`
            : `<span style="font-weight:900;color:${brandCfg.color};font-size:1.4rem;">${initials}</span>`;
    }
    if (titleEl)       titleEl.textContent      = brandName;
    if (sectionTitle)  sectionTitle.textContent = `All ${brandName} Styles`;

    try {
        const products = await fetchProducts();
        const filtered = products.filter(p => p.brand.toLowerCase() === brandName.toLowerCase());

        if (countEl) countEl.textContent = filtered.length;

        grid.innerHTML = "";
        if (filtered.length === 0) {
            grid.innerHTML = `<p style="color:#bbb;text-align:center;grid-column:1/-1;padding:60px;">
                No products found for ${brandName}.
            </p>`;
            return;
        }
        filtered.forEach(shoe => { grid.innerHTML += buildProductCard(shoe); });
        initScrollAnimation();
    } catch (err) {
        console.error("Failed to load brand products:", err);
    }
}


/* =================================================
   PRODUCT DESCRIPTION GENERATOR
   Deterministic per product ID — same shoe always
   gets the same description across visits
================================================= */

const DESC_TEMPLATES = {

    comfort: [
        "engineered with responsive foam cushioning that absorbs impact and returns energy with every step",
        "built on a plush midsole that cradles your foot in cloud-like comfort all day long",
        "featuring a padded collar and cushioned insole that keep fatigue at bay during long wear",
        "designed with multi-zone cushioning that adapts to your stride for a personalised fit",
        "equipped with a contoured footbed that provides arch support and all-day softness",
        "constructed with a lightweight foam base that delivers a barely-there feel without sacrificing support",
        "lined with breathable mesh padding that wicks moisture and keeps your feet fresh for hours",
        "built for maximum underfoot comfort with a dual-density midsole that softens every landing",
    ],

    material: [
        "crafted from premium full-grain leather upper that ages beautifully and resists daily wear",
        "made with engineered mesh that offers superior breathability while keeping its structure",
        "constructed from high-abrasion rubber on the outsole for lasting grip on any surface",
        "featuring a reinforced toe cap and heel counter built to handle the demands of daily use",
        "assembled with vulcanised rubber and canvas that deliver timeless durability",
        "built with a seamless knit upper that moves with your foot and resists tearing",
        "using premium suede panels and tonal stitching that speak to quality in every detail",
        "finished with a textured rubber outsole that bites into surfaces for confident traction",
    ],

    style: [
        "its clean silhouette and tonal colourway make it an effortless match for any outfit",
        "the bold profile and contrasting sole unit command attention on the street and off it",
        "a minimalist design language keeps it versatile enough to pair with casual or smart looks",
        "retro-inspired lines and modern proportions give it a timeless appeal that never goes out of style",
        "the sleek low-profile shape transitions seamlessly from the gym to the streets",
        "subtle branding and a refined palette keep the aesthetic understated yet distinctive",
        "oversized panels and a chunky outsole lean into the premium streetwear aesthetic",
        "clean toe box and tonal eyelets give the silhouette a polished, put-together finish",
    ],
};

// Seeded pick — deterministic so same product = same description
function seededPick(arr, seed) {
    return arr[seed % arr.length];
}

function getProductDescription(shoe) {
    const id = shoe.id;

    // Three different seeds for three different template pools
    const s1 = (id * 7919)  % 233280;
    const s2 = (id * 6271 + 1000) % 233280;
    const s3 = (id * 9301 + 49297) % 233280;

    const comfort  = seededPick(DESC_TEMPLATES.comfort,  s1);
    const material = seededPick(DESC_TEMPLATES.material, s2);
    const style    = seededPick(DESC_TEMPLATES.style,    s3);

    // Combine into two natural sentences
    const sentence1 = `The ${shoe.name} is ${comfort}, while ${material}.`;
    const sentence2 = `${style.charAt(0).toUpperCase() + style.slice(1)} — making it a standout addition to any rotation.`;

    return `${sentence1} ${sentence2}`;
}


/* =================================================
   PRODUCT DETAIL PAGE
================================================= */
async function loadProductPage() {
    const nameEl  = document.getElementById("product-name");
    const priceEl = document.getElementById("product-price");
    const imgEl   = document.getElementById("product-img");
    if (!nameEl || !priceEl || !imgEl) return;

    const id = parseInt(localStorage.getItem("productId"));
    try {
        const products = await fetchProducts();
        const shoe = products.find(p => p.id === id);
        if (!shoe) { nameEl.innerText = "Product not found"; return; }

        nameEl.innerText  = shoe.name;
        priceEl.innerText = formatPrice(shoe.price);
        imgEl.src         = shoe.image;
        imgEl.onerror     = () => imgEl.src = "https://placehold.co/400x300/eaf3fa/2B9FD8?text=No+Image";

        // Update page title
        document.title = `${shoe.name} — Claxxic India`;

        // Inject rating
        const { score, count } = getRating(shoe.id);
        const starsEl  = document.getElementById("rating-stars");
        const scoreEl  = document.getElementById("rating-score");
        const countEl  = document.getElementById("rating-count");
        if (starsEl) starsEl.innerHTML = buildStars(score, "lg");
        if (scoreEl) scoreEl.textContent = score.toFixed(1);
        if (countEl) countEl.textContent = `(${count.toLocaleString()} reviews)`;

        // Inject description
        const descEl = document.querySelector(".description");
        if (descEl) descEl.textContent = getProductDescription(shoe);

        // Render color swatches
        renderColorSwatches(shoe);

        const sizeSelect = document.getElementById("size-select");
        if (sizeSelect && shoe.sizes) {
            sizeSelect.innerHTML = `<option value="">Select Size</option>`;
            shoe.sizes.forEach(s => { sizeSelect.innerHTML += `<option>${s}</option>`; });
        }

        // Render similar products
        renderSimilarProducts(shoe, products);

    } catch (err) {
        console.error("Failed to load product:", err);
        if (nameEl) nameEl.innerText = "Error loading product";
    }
}

/* =================================================
   COLOR SWATCHES
================================================= */
function renderColorSwatches(shoe) {
    const section     = document.getElementById("color-section");
    const swatchesEl  = document.getElementById("color-swatches");
    const colorNameEl = document.getElementById("selected-color-name");
    const imgEl       = document.getElementById("product-img");
    const priceEl     = document.getElementById("product-price");

    if (!section || !swatchesEl || !shoe.colors || shoe.colors.length === 0) {
        if (section) section.style.display = "none";
        return;
    }

    section.style.display = "block";
    swatchesEl.innerHTML  = "";

    // Set first color as default — update name + price
    const firstColor = shoe.colors[0];
    if (colorNameEl) colorNameEl.textContent = firstColor.name;
    if (priceEl && firstColor.price) {
        priceEl.textContent = formatPrice(firstColor.price);
    }

    shoe.colors.forEach((color, i) => {
        const swatch = document.createElement("button");
        swatch.className = "color-swatch" + (i === 0 ? " active" : "");
        swatch.title     = color.name;
        swatch.style.setProperty("--swatch-color", color.hex);

        // Show price badge on swatch if different from base price
        const hasDifferentPrice = color.price && color.price !== shoe.price;

        const isLight = ["#ffffff","#fff","#f5f5f5","#fafafa","#f0f0f0"].includes(color.hex.toLowerCase());
        if (isLight) swatch.classList.add("color-swatch-light");

        swatch.addEventListener("click", () => {
            // Update active swatch
            swatchesEl.querySelectorAll(".color-swatch").forEach(s => s.classList.remove("active"));
            swatch.classList.add("active");

            // Update color name label
            if (colorNameEl) colorNameEl.textContent = color.name;

            // Update price — use color's price if set, else fall back to base
            if (priceEl) {
                const newPrice = color.price || shoe.price;
                // Animate price change
                priceEl.style.transform = "scale(1.12)";
                priceEl.style.color     = "var(--primary)";
                priceEl.textContent     = formatPrice(newPrice);
                setTimeout(() => {
                    priceEl.style.transform = "scale(1)";
                }, 250);
            }

            // Swap image with smooth fade
            if (imgEl) {
                imgEl.style.opacity   = "0";
                imgEl.style.transform = "scale(0.97)";
                setTimeout(() => {
                    imgEl.src = color.image;
                    imgEl.onerror = () => imgEl.src = "https://placehold.co/400x300/eaf3fa/2B9FD8?text=No+Image";
                    imgEl.style.opacity   = "1";
                    imgEl.style.transform = "scale(1)";
                }, 200);
            }
        });

        swatchesEl.appendChild(swatch);
    });
}

/* =================================================
   SIMILAR PRODUCTS
   Logic: same brand first, then fill with similar
   price range (±₹2000), excluding current product,
   max 4 cards total
================================================= */
function renderSimilarProducts(current, allProducts) {
    const section    = document.getElementById("similar-section");
    const grid       = document.getElementById("similar-grid");
    const subtitleEl = document.getElementById("similar-subtitle");
    if (!section || !grid) return;

    const PRICE_RANGE = 2000;
    const MAX = 8;

    // 1. Same brand, exclude current
    const sameBrand = allProducts.filter(p =>
        p.id !== current.id &&
        p.brand.toLowerCase() === current.brand.toLowerCase()
    );

    // 2. Similar price range, exclude current & already picked
    const sameBrandIds = new Set(sameBrand.map(p => p.id));
    const similarPrice = allProducts.filter(p =>
        p.id !== current.id &&
        !sameBrandIds.has(p.id) &&
        Math.abs(p.price - current.price) <= PRICE_RANGE
    );

    // 3. If still not enough, grab any other products as fallback
    const pickedIds = new Set([current.id, ...sameBrand.map(p => p.id), ...similarPrice.map(p => p.id)]);
    const fallback  = allProducts.filter(p => !pickedIds.has(p.id));

    // 4. Shuffle each group so it feels fresh every visit
    const shuffle = arr => arr.sort(() => Math.random() - 0.5);

    // Fill up to MAX: same brand → price similar → fallback
    const picked = [
        ...shuffle(sameBrand),
        ...shuffle(similarPrice),
        ...shuffle(fallback)
    ].slice(0, MAX);

    if (picked.length === 0) return; // nothing to show

    // Subtitle tells the user why these were picked
    const brandCount = picked.filter(p => p.brand === current.brand).length;
    if (subtitleEl) {
        if (brandCount === picked.length) {
            subtitleEl.textContent = `More from ${current.brand}`;
        } else if (brandCount === 0) {
            subtitleEl.textContent = `Similar price range`;
        } else {
            subtitleEl.textContent = `More from ${current.brand} & similar picks`;
        }
    }

    grid.innerHTML = "";
    picked.forEach(shoe => { grid.innerHTML += buildProductCard(shoe); });

    section.style.display = "block";
    initScrollAnimation();
}


/* =================================================
   SCROLL ANIMATION
================================================= */
function initScrollAnimation() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("show"); });
    });
    document.querySelectorAll(".fade-in").forEach(el => observer.observe(el));
}

function openProduct(id) {
    localStorage.setItem("productId", id);
    window.scrollTo({ top: 0, behavior: "smooth" });
    // Small delay so scroll feels intentional before page reload
    setTimeout(() => { window.location.href = "/product"; }, 150);
}


/* =================================================
   OFFER RIBBON
================================================= */
async function loadOfferRibbon() {
    try {
        const res  = await fetch("/api/offer");
        const data = await res.json();
        if (!data.active || !data.text) return;

        const ribbon = document.createElement("div");
        ribbon.id = "offer-ribbon";
        ribbon.style.cssText = `
            background: ${data.bg_color};
            color: ${data.text_color};
            text-align: center;
            padding: 10px 20px;
            font-size: 0.92rem;
            font-weight: 700;
            letter-spacing: 0.3px;
            position: relative;
            z-index: 50;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            animation: ribbonSlide 0.4s ease;
        `;
        ribbon.textContent = data.text;

        // Add animation keyframe once
        if (!document.getElementById("ribbon-style")) {
            const style = document.createElement("style");
            style.id = "ribbon-style";
            style.textContent = `@keyframes ribbonSlide { from { opacity:0; transform:translateY(-100%); } to { opacity:1; transform:translateY(0); } }`;
            document.head.appendChild(style);
        }

        // Insert after <header>, before .hero
        const header = document.querySelector("header");
        if (header && header.nextSibling) {
            header.parentNode.insertBefore(ribbon, header.nextSibling);
        } else {
            document.body.prepend(ribbon);
        }
    } catch (e) {
        // Silently fail — ribbon is optional
    }
}

/* =================================================
   PAGE INITIALIZATION
================================================= */
document.addEventListener("DOMContentLoaded", () => {
    initScrollAnimation();
    updateCartBadge(); // always sync cart count in header

    const onHome    = !!document.getElementById("brand-tiles-grid");
    const onBrand   = !!document.getElementById("brand-product-grid");
    const onProduct = !!document.getElementById("product-name");
    const onCart    = !!document.getElementById("cart-items-list");

    if (onHome)    { renderBrandTiles(); renderTrendingShoes(); loadOfferRibbon(); }
    if (onBrand)   renderBrandPage();
    if (onProduct) loadProductPage();
    if (onCart)    renderCartPage();
});
