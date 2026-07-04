"""
Final TerpVault logo — hexagon core mark with custom TV monogram.
Combines #04 shape + #10 proportions.
One SVG source of truth. All assets derived from it.
"""
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "review" / "logo-concepts"
OUTPUT.mkdir(parents=True, exist_ok=True)

# ———————— Core mark: hexagon with custom T/V monogram ————————
# The T is the vertical + left half of crossbar.
# The V is formed by the right diagonal.
# Together they interlock cleanly inside the hexagon.

CORE = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" fill="none">
  <!-- Hexagon outline -->
  <polygon points="32,4 56,18 56,46 32,58 8,46 8,18" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linejoin="round"/>
  <!-- T vertical + left crossbar -->
  <line x1="20" y1="20" x2="32" y2="20" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  <line x1="26" y1="20" x2="26" y2="44" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  <!-- V right diagonal -->
  <line x1="26" y1="44" x2="44" y2="24" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
</svg>"""

# ———————— Full logo with wordmark ————————
FULL = """<svg xmlns="http://www.w3.org/2000/svg" width="152" height="40" viewBox="0 0 152 40" fill="none">
  <!-- Icon -->
  <polygon points="20,3 35,14 35,26 20,37 5,26 5,14" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
  <line x1="12" y1="14" x2="20" y2="14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="16" y1="14" x2="16" y2="28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="16" y1="28" x2="28" y2="16" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Wordmark -->
  <text x="44" y="27" font-family="'DM Sans','Helvetica Neue',Arial,sans-serif" font-weight="700" font-size="17" fill="currentColor" letter-spacing="-0.4">TerpVault</text>
</svg>"""

# ———————— Favicon (32x32) ————————
FAV = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32" fill="none">
  <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="currentColor" stroke-width="2" fill="none" stroke-linejoin="round"/>
  <line x1="10" y1="10" x2="16" y2="10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <line x1="13" y1="10" x2="13" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <line x1="13" y1="22" x2="22" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
</svg>"""

# ———————— Write all variants ————————
variants = {
    "core-mark.svg": CORE,                      # Source of truth, 64x64
    "icon.svg": CORE.replace('width="64" height="64"', 'width="64" height="64"'),
    "favicon.svg": FAV,
    "logo.svg": FULL,                           # Full logo + wordmark
}

# Dark variants (stroke = white)
for name, content in list(variants.items()):
    base = name.replace(".svg", "")
    variants[f"{base}-dark.svg"] = content.replace('currentColor', '#fff')

# Light variants (stroke = black — same as default but explicit)
for name, content in list(variants.items()):
    base = name.replace(".svg", "")
    if "-dark" not in name:
        variants[f"{base}-light.svg"] = content.replace('currentColor', '#000')

# Write to logo-concepts folder
for name, content in variants.items():
    (OUTPUT / name).write_text(content)
    print(f"  {name}")

# Also write core-mark.svg as the live site logo
SITE_LOGO = CORE.replace('currentColor', 'currentColor')
(Path(__file__).resolve().parent.parent / "terpvault" / "web" / "assets" / "logo.svg").write_text(CORE)

# Write favicon
(Path(__file__).resolve().parent.parent / "terpvault" / "web" / "assets" / "favicon.svg").write_text(FAV)

print(f"\n  -> assets/logo.svg (site-ready)")
print(f"  -> assets/favicon.svg (site-ready)")
print(f"\nTotal: {len(variants)} files in {OUTPUT}")
