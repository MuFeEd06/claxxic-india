# Claxxic India — Flask Deployment Guide

## Project Structure

```
claxxic-india/
├── app.py                    ← Flask application (API + routing)
├── requirements.txt          ← Python packages
├── Procfile                  ← Render start command
├── render.yaml               ← Render auto-config
├── .gitignore
├── data/
│   └── products.json         ← All your products
├── templates/                ← HTML pages (Flask format)
│   ├── base.html
│   ├── index.html
│   ├── product.html
│   ├── brand.html
│   └── cart.html
└── static/                   ← All frontend files
    ├── script.js
    ├── style.css
    ├── sneaker.glb           ← copy your 3D model here
    ├── logo/
    │   ├── logo.png          ← copy your logo here
    │   ├── whatsapp.png      ← copy your whatsapp icon here
    │   └── brands/           ← copy all brand logos here
    │       ├── nike.png
    │       ├── adidas.png
    │       └── ...
    └── shoes/                ← copy all shoe images here
        ├── nike/
        ├── adidas/
        └── ...
```

---

## STEP 1 — Add Your Files

Before anything else, copy these into the `static/` folder:

```
static/sneaker.glb
static/logo/logo.png
static/logo/whatsapp.png
static/logo/brands/nike.png
static/logo/brands/adidas.png
... (all brand logos)
static/shoes/nike/nike-air-jordan-1-high.jpg
... (all product images)
```

---

## STEP 2 — Test Locally

```bash
# 1. Open terminal inside the claxxic-india folder

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install packages
pip install -r requirements.txt

# 5. Run
python app.py
```

Open browser → **http://localhost:5000**
Site should look exactly like your GitHub Pages version ✅

---

## STEP 3 — Push to GitHub (Manual Upload)

### 3a. Create repository
1. Go to **github.com** → sign in
2. Click **"+"** (top right) → **"New repository"**
3. Name: `claxxic-india`
4. Set to **Public**
5. ✅ Check **"Add a README file"**
6. Click **"Create repository"**

### 3b. Upload files
1. Inside your repo → click **"Add file"** → **"Upload files"**
2. **Drag your entire `claxxic-india` folder** into the upload box
   GitHub will preserve all subfolders automatically
3. Write commit message: `Initial Flask deployment`
4. Click **"Commit changes"**

> ✅ Done! All files are now on GitHub.

---

## STEP 4 — Deploy on Render

1. Go to **https://render.com** → Sign up / Log in (free)

2. Click **"New +"** → **"Web Service"**

3. Click **"Connect GitHub"** → Authorize → select `claxxic-india`

4. Render auto-detects `render.yaml` — settings fill automatically:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app ...`

5. Click **"Create Web Service"**

6. Wait ~2-3 minutes for first build

7. Your site is live at:
   **https://claxxic-india.onrender.com** 🚀

---

## STEP 5 — Adding New Products

Edit `data/products.json` and add a new entry:

```json
{
  "id": 57,
  "name": "Nike Air Max Plus",
  "brand": "Nike",
  "price": 14500,
  "image": "shoes/nike/nike-air-max-plus.jpg",
  "sizes": ["UK 6","UK 7","UK 8","UK 9","UK 10"],
  "tag": "",
  "colors": [
    { "name": "Black", "hex": "#111111", "price": 14500,
      "image": "shoes/nike/nike-air-max-plus-black.jpg" },
    { "name": "White", "hex": "#f5f5f5", "price": 13500,
      "image": "shoes/nike/nike-air-max-plus-white.jpg" }
  ]
}
```

Then on GitHub → go to `data/products.json` → click ✏️ Edit → paste → commit.
Render redeploys automatically within 2 minutes.

---

## API Endpoints (for testing)

| URL | What it returns |
|-----|-----------------|
| `/api/products` | All products |
| `/api/products?brand=Nike` | Nike only |
| `/api/products?tag=trending` | Trending only |
| `/api/products?q=dunk` | Search results |
| `/api/products/1` | Single product |
| `/api/brands` | All brands + counts |

---

## Important Notes

- **Cart & Address** — still stored in browser `localStorage` (works perfectly)
- **WhatsApp** — WHATSAPP_NUMBER is set in `static/script.js` line ~35
- **Free tier** — Render free tier sleeps after 15 min inactivity, wakes in ~30 sec
- **Phase 2** (future) — Orders saved to database, admin panel
