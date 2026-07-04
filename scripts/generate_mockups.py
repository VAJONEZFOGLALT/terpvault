"""
Generate premium PNG mockup concepts for TerpVault redesign.
Each mockup is a full-page 1440x900 concept rendered to review/design/.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT = Path(__file__).resolve().parent.parent / "review" / "design"
OUTPUT.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. PORTAL MOCKUP — Premium TerpVault landing
# ─────────────────────────────────────────────
PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: linear-gradient(160deg, #0a0f0a 0%, #0f1a0f 40%, #0a0f0a 100%);
    color: #e8e4de;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    -webkit-font-smoothing: antialiased;
  }

  .brand {
    text-align: center;
    margin-bottom: 80px;
  }

  .brand .icon {
    width: 64px; height: 64px;
    background: linear-gradient(135deg, #3d9a3e, #2C5F2D);
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 24px;
    font-size: 28px;
    color: #fff;
    box-shadow: 0 8px 32px rgba(61,154,62,0.25);
  }

  .brand h1 {
    font-family: 'DM Sans', sans-serif;
    font-size: 32px;
    font-weight: 500;
    letter-spacing: -0.5px;
    color: #fff;
    margin-bottom: 8px;
  }

  .brand p {
    font-size: 15px;
    color: rgba(255,255,255,0.45);
    font-weight: 400;
  }

  .supplier-card {
    width: 480px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 32px;
    transition: all 0.3s ease;
    cursor: pointer;
    backdrop-filter: blur(12px);
  }

  .supplier-card:hover {
    border-color: rgba(61,154,62,0.4);
    background: rgba(255,255,255,0.06);
    transform: translateY(-3px);
    box-shadow: 0 12px 48px rgba(0,0,0,0.3);
  }

  .supplier-card .top {
    display: flex; align-items: center; gap: 20px; margin-bottom: 20px;
  }

  .supplier-card .logo-placeholder {
    width: 56px; height: 56px; border-radius: 14px;
    background: linear-gradient(135deg, #3d9a3e, #2C5F2D);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 20px; color: #fff; flex-shrink: 0;
  }

  .supplier-card .info h2 {
    font-family: 'DM Sans', sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 4px;
  }

  .supplier-card .info p {
    font-size: 14px;
    color: rgba(255,255,255,0.45);
    line-height: 1.5;
  }

  .supplier-card .stats {
    display: flex; gap: 24px; margin-bottom: 24px;
  }

  .supplier-card .stat {
    text-align: center;
  }

  .supplier-card .stat .num {
    font-size: 22px;
    font-weight: 700;
    color: #3d9a3e;
    font-family: 'DM Sans', sans-serif;
  }

  .supplier-card .stat .lbl {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: rgba(255,255,255,0.3);
    margin-top: 2px;
  }

  .supplier-card .open-btn {
    display: block; width: 100%; padding: 14px;
    background: #3d9a3e; color: #fff; border: none; border-radius: 12px;
    font-size: 15px; font-weight: 600; cursor: pointer;
    text-align: center;
    transition: background 0.2s;
  }

  .supplier-card .open-btn:hover { background: #4dba4e; }

  .footer-note {
    margin-top: 60px;
    font-size: 13px;
    color: rgba(255,255,255,0.2);
  }
</style></head>
<body>
  <div class="brand">
    <div class="icon">&#x1F331;</div>
    <h1>TerpVault</h1>
    <p>Digital Catalogue Platform</p>
  </div>

  <div class="supplier-card">
    <div class="top">
      <div class="logo-placeholder">TU</div>
      <div class="info">
        <h2>Terpenes UK</h2>
        <p>Premium botanical &amp; cannabis-derived terpenes</p>
      </div>
    </div>
    <div class="stats">
      <div class="stat"><div class="num">337</div><div class="lbl">Products</div></div>
      <div class="stat"><div class="num">13</div><div class="lbl">Brands</div></div>
      <div class="stat"><div class="num">15</div><div class="lbl">Sections</div></div>
      <div class="stat"><div class="num">V20</div><div class="lbl">Build</div></div>
    </div>
    <div class="open-btn">Open Catalogue &rarr;</div>
  </div>

  <div class="footer-note">1 supplier &middot; Built by TerpVault Engine</div>
</body></html>
"""

# ─────────────────────────────────────────────
# 2. DASHBOARD MOCKUP
# ─────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #0f0f0e;
    color: #e8e4de;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  .nav {
    padding: 20px 40px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }

  .nav .logo {
    display: flex; align-items: center; gap: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600; font-size: 17px;
    color: #fff;
  }

  .nav .logo .dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #3d9a3e;
  }

  .container {
    max-width: 960px; margin: 0 auto; padding: 48px 24px;
  }

  .back {
    font-size: 13px; color: rgba(255,255,255,0.3);
    margin-bottom: 32px; display: block;
  }

  .back:hover { color: #3d9a3e; }

  .hero {
    margin-bottom: 48px;
  }

  .hero .logo-badge {
    width: 48px; height: 48px; border-radius: 14px;
    background: linear-gradient(135deg, #3d9a3e, #2C5F2D);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 18px; color: #fff;
    margin-bottom: 16px;
  }

  .hero h1 {
    font-family: 'DM Sans', sans-serif;
    font-size: 28px;
    font-weight: 500;
    color: #fff;
    margin-bottom: 6px;
  }

  .hero .desc {
    font-size: 14px;
    color: rgba(255,255,255,0.45);
    margin-bottom: 12px;
  }

  .hero .meta-line {
    font-size: 13px;
    color: rgba(255,255,255,0.3);
    display: flex; gap: 24px;
  }

  .hero .meta-line strong { color: rgba(255,255,255,0.6); font-weight: 500; }

  .latest-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px 28px;
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 40px;
  }

  .latest-card .left { display: flex; align-items: center; gap: 16px; }

  .latest-card .glow {
    width: 10px; height: 10px; border-radius: 50%;
    background: #3d9a3e; box-shadow: 0 0 12px rgba(61,154,62,0.4);
  }

  .latest-card .lbl { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.3); margin-bottom: 2px; }
  .latest-card .title { font-size: 16px; font-weight: 600; color: #fff; }
  .latest-card .sub { font-size: 13px; color: rgba(255,255,255,0.4); }

  .latest-card .btn {
    padding: 10px 24px; background: #3d9a3e; color: #fff;
    border: none; border-radius: 10px; font-size: 14px; font-weight: 600;
    cursor: pointer;
  }

  .latest-card .btn.outline {
    background: transparent; border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.6);
  }

  .section-label {
    font-size: 12px; text-transform: uppercase; letter-spacing: 1px;
    color: rgba(255,255,255,0.25); margin-bottom: 16px;
  }

  .action-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
    margin-bottom: 48px;
  }

  .action {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px; text-align: center;
    transition: all 0.2s;
    cursor: pointer;
  }

  .action:hover { border-color: rgba(61,154,62,0.3); background: rgba(255,255,255,0.05); }

  .action .icon { font-size: 24px; margin-bottom: 8px; }
  .action .name { font-size: 14px; font-weight: 600; color: #fff; }
  .action .desc { font-size: 12px; color: rgba(255,255,255,0.35); margin-top: 2px; }

  .highlights { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 48px; }

  .highlight {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 20px;
  }

  .highlight .hlbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.25); margin-bottom: 8px; }
  .highlight .hval { font-size: 15px; font-weight: 500; color: #fff; }
  .highlight .hsub { font-size: 12px; color: rgba(255,255,255,0.3); margin-top: 2px; }

  .section-pills { display: flex; flex-wrap: wrap; gap: 8px; }
  .pill {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 100px;
    padding: 8px 18px;
    font-size: 13px;
    color: rgba(255,255,255,0.6);
    cursor: pointer;
    transition: all 0.2s;
  }

  .pill:hover { border-color: rgba(61,154,62,0.3); color: #fff; }
</style></head>
<body>
  <div class="nav">
    <div class="logo"><span class="dot"></span> TerpVault</div>
  </div>

  <div class="container">
    <div class="back">&larr; All Catalogues</div>

    <div class="hero">
      <div class="logo-badge">TU</div>
      <h1>Terpenes UK</h1>
      <div class="desc">Premium botanical &amp; cannabis-derived terpenes</div>
      <div class="meta-line">
        <span>Latest build: <strong>V20</strong></span>
        <span><strong>337</strong> products</span>
        <span><strong>13</strong> brands</span>
        <span><strong>1,815</strong> variants</span>
      </div>
    </div>

    <div class="latest-card">
      <div class="left">
        <div class="glow"></div>
        <div>
          <div class="lbl">Latest Build</div>
          <div class="title">Catalogue V20</div>
          <div class="sub">337 products &middot; 15 sections &middot; Built 2 Jul 2026</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;">
        <div class="btn outline">JSON</div>
        <div class="btn">Browse &rarr;</div>
      </div>
    </div>

    <div class="section-label">Quick Actions</div>
    <div class="action-grid">
      <div class="action"><div class="icon">&#x1F4D6;</div><div class="name">Catalogue</div><div class="desc">Browse products</div></div>
      <div class="action"><div class="icon">&#x1F3F4;</div><div class="name">Brands</div><div class="desc">13 brands</div></div>
      <div class="action"><div class="icon">&#x1F50D;</div><div class="name">Search</div><div class="desc">Find products</div></div>
      <div class="action"><div class="icon">&#x1F4E5;</div><div class="name">Downloads</div><div class="desc">PDF &amp; JSON</div></div>
    </div>

    <div class="section-label">Highlights</div>
    <div class="highlights">
      <div class="highlight">
        <div class="hlbl">Latest PDF</div>
        <div class="hval">catalog-v20.pdf</div>
        <div class="hsub">Download &rarr;</div>
      </div>
      <div class="highlight">
        <div class="hlbl">Last Sync</div>
        <div class="hval">2 Jul 2026</div>
        <div class="hsub">No changes detected</div>
      </div>
      <div class="highlight">
        <div class="hlbl">Recent Changes</div>
        <div class="hval">No changes</div>
        <div class="hsub">Since last build</div>
      </div>
    </div>

    <div class="section-label">Browse Sections</div>
    <div class="section-pills">
      <span class="pill">Strain Profiles</span>
      <span class="pill">Live Resin</span>
      <span class="pill">Infusion</span>
      <span class="pill">Isolates</span>
      <span class="pill">Hardware &amp; Ingredients</span>
      <span class="pill">Sample Packs</span>
      <span class="pill">New Releases</span>
      <span class="pill">Clearance</span>
    </div>
  </div>
</body></html>
"""

# ─────────────────────────────────────────────
# 3. PRODUCT PAGE MOCKUP (magazine/editorial)
# ─────────────────────────────────────────────
PRODUCT_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #0f0f0e;
    color: #e8e4de;
    -webkit-font-smoothing: antialiased;
  }

  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px 60px; }

  .breadcrumbs {
    display: flex; gap: 8px; font-size: 13px; color: rgba(255,255,255,0.3);
    margin-bottom: 40px;
  }
  .breadcrumbs a { color: rgba(255,255,255,0.3); }
  .breadcrumbs a:hover { color: #3d9a3e; }
  .breadcrumbs .sep { color: rgba(255,255,255,0.12); }
  .breadcrumbs .current { color: rgba(255,255,255,0.6); }

  .product-layout {
    display: grid; grid-template-columns: 1fr 1fr; gap: 60px;
  }

  .gallery {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    aspect-ratio: 1;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
  }

  .gallery .placeholder {
    width: 60%; height: 60%;
    background: linear-gradient(135deg, rgba(61,154,62,0.1), rgba(44,95,45,0.05));
    border-radius: 12px;
  }

  .thumbs { display: flex; gap: 8px; margin-top: 12px; }
  .thumb {
    width: 56px; height: 56px; border-radius: 10px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    cursor: pointer;
  }
  .thumb.active { border-color: #3d9a3e; }

  .info .brand {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;
    color: #3d9a3e; font-weight: 600; margin-bottom: 12px;
  }

  .info h1 {
    font-family: 'DM Sans', sans-serif;
    font-size: 32px; font-weight: 500; color: #fff;
    line-height: 1.15; margin-bottom: 16px;
  }

  .info .price {
    font-family: 'DM Sans', sans-serif;
    font-size: 28px; font-weight: 700; color: #3d9a3e;
    margin-bottom: 24px;
  }

  .info .desc {
    font-size: 15px; line-height: 1.7;
    color: rgba(255,255,255,0.5);
    margin-bottom: 32px;
  }

  .meta-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    margin-bottom: 32px;
  }

  .meta-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 14px 16px;
  }

  .meta-item .mlbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.25); margin-bottom: 4px; }
  .meta-item .mval { font-size: 14px; font-weight: 500; color: #fff; }

  .variant-table { width: 100%; border-collapse: collapse; }
  .variant-table th { text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.25); padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }
  .variant-table td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 14px; }
  .in-stock { color: #3d9a3e; }

  .related { border-top: 1px solid rgba(255,255,255,0.06); margin-top: 60px; padding-top: 40px; }
  .related h2 { font-family: 'DM Sans', sans-serif; font-size: 18px; font-weight: 500; color: #fff; margin-bottom: 20px; }
  .related-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .related-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .related-card:hover { border-color: rgba(61,154,62,0.3); }
  .related-card .thumb-sm {
    width: 100%; aspect-ratio: 1;
    background: rgba(255,255,255,0.03);
    border-radius: 8px; margin-bottom: 10px;
  }
  .related-card .rname { font-size: 13px; font-weight: 500; color: #fff; }
  .related-card .rprice { font-size: 14px; font-weight: 600; color: #3d9a3e; margin-top: 4px; }
</style></head>
<body>
  <div class="container">
    <div class="breadcrumbs">
      <a href="#">TerpVault</a><span class="sep">/</span>
      <a href="#">Terpenes UK</a><span class="sep">/</span>
      <a href="#">Catalogue</a><span class="sep">/</span>
      <a href="#">Eybna</a><span class="sep">/</span>
      <span class="current">Permanent Marker</span>
    </div>

    <div class="product-layout">
      <div>
        <div class="gallery"><div class="placeholder"></div></div>
        <div class="thumbs">
          <div class="thumb active"></div>
          <div class="thumb"></div>
          <div class="thumb"></div>
        </div>
      </div>
      <div class="info">
        <div class="brand">Eybna</div>
        <h1>Permanent Marker</h1>
        <div class="price">&pound;9.50</div>
        <div class="desc">
          A premium cultivar-specific terpene profile from Eybna's renowned Palate &amp; Live line. Designed to replicate the complex aromatic signature of the original genetics with high fidelity.
        </div>
        <div class="meta-grid">
          <div class="meta-item"><div class="mlbl">Brand</div><div class="mval">Eybna</div></div>
          <div class="meta-item"><div class="mlbl">Category</div><div class="mval">Terpene</div></div>
          <div class="meta-item"><div class="mlbl">Collection</div><div class="mval">Strain Profiles</div></div>
          <div class="meta-item"><div class="mlbl">SKU</div><div class="mval">PM-10ML</div></div>
        </div>

        <h3 style="font-size:13px;margin-bottom:12px;color:rgba(255,255,255,0.4);">Available Sizes</h3>
        <table class="variant-table">
          <thead><tr><th>Size</th><th>Price</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>10ml</td><td>&pound;9.50</td><td class="in-stock">In Stock</td></tr>
            <tr><td>30ml</td><td>&pound;22.00</td><td class="in-stock">In Stock</td></tr>
            <tr><td>100ml</td><td>&pound;48.00</td><td class="in-stock">In Stock</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="related">
      <h2>Related Products</h2>
      <div class="related-grid">
        <div class="related-card"><div class="thumb-sm"></div><div class="rname">Blue Dream</div><div class="rprice">&pound;9.50</div></div>
        <div class="related-card"><div class="thumb-sm"></div><div class="rname">Gelato</div><div class="rprice">&pound;9.50</div></div>
        <div class="related-card"><div class="thumb-sm"></div><div class="rname">Zkittlez</div><div class="rprice">&pound;9.50</div></div>
        <div class="related-card"><div class="thumb-sm"></div><div class="rname">Wedding Cake</div><div class="rprice">&pound;9.50</div></div>
      </div>
    </div>
  </div>
</body></html>
"""

# ─────────────────────────────────────────────
# 4. DOWNLOADS MOCKUP (clean, latest-first)
# ─────────────────────────────────────────────
DOWNLOADS_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #0f0f0e;
    color: #e8e4de;
    -webkit-font-smoothing: antialiased;
  }

  .container { max-width: 720px; margin: 0 auto; padding: 48px 24px; }

  h1 {
    font-family: 'DM Sans', sans-serif;
    font-size: 24px; font-weight: 500; color: #fff;
    margin-bottom: 32px;
  }

  .card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 12px;
    display: flex; align-items: center; justify-content: space-between;
    transition: all 0.2s;
  }

  .card:hover { border-color: rgba(61,154,62,0.3); }

  .card .badge {
    width: 44px; height: 44px; border-radius: 12px;
    background: rgba(61,154,62,0.12);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: #3d9a3e;
    flex-shrink: 0;
  }

  .card .info { margin-left: 16px; flex: 1; }
  .card .info .name { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 2px; }
  .card .info .meta { font-size: 13px; color: rgba(255,255,255,0.35); }
  .card .btn {
    padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 600;
    background: #3d9a3e; color: #fff; border: none; cursor: pointer;
    flex-shrink: 0; text-decoration: none;
  }

  .card .btn.outline {
    background: transparent; border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.5);
  }

  .archive-toggle {
    margin-top: 32px;
    font-size: 13px;
    color: rgba(255,255,255,0.25);
    cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px;
  }

  .archive-toggle:hover { color: rgba(255,255,255,0.5); }

  .archive-note {
    margin-top: 40px;
    padding: 20px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    font-size: 13px;
    color: rgba(255,255,255,0.25);
    line-height: 1.6;
  }
</style></head>
<body>
  <div class="container">
    <h1>Catalogue Downloads</h1>

    <div class="card">
      <div style="display:flex;align-items:center;">
        <div class="badge">&#x1F4D1;</div>
        <div class="info">
          <div class="name">PDF Catalogue — Latest</div>
          <div class="meta">337 products &middot; 1,815 variants &middot; 15 sections</div>
        </div>
      </div>
      <a class="btn">Download PDF</a>
    </div>

    <div class="card">
      <div style="display:flex;align-items:center;">
        <div class="badge" style="background:rgba(77,138,170,0.12);color:#4d8aaa;">{ }</div>
        <div class="info">
          <div class="name">JSON Data — Latest</div>
          <div class="meta">Full catalogue structure for developers</div>
        </div>
      </div>
      <a class="btn outline">Download JSON</a>
    </div>

    <span class="archive-toggle">&#x25B6; Show archive (48 previous versions)</span>

    <div class="archive-note">
      The PDF and JSON are automatically regenerated every 6 hours.<br>
      If no changes are detected, the existing files are preserved.
    </div>
  </div>
</body></html>
"""

mockups = [
    ("portal_concept", PORTAL_HTML),
    ("dashboard_concept", DASHBOARD_HTML),
    ("product_concept", PRODUCT_HTML),
    ("downloads_concept", DOWNLOADS_HTML),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, html in mockups:
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(500)
        path = OUTPUT / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        kb = path.stat().st_size // 1024
        print(f"  OK  {name:30s} {kb}KB")
        page.close()
    browser.close()

print(f"\nMockups saved to {OUTPUT}")
