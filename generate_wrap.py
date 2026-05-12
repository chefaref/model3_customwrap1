"""Tesla Model 3 — Chase (Paw Patrol) custom wrap generator.

Produces a landscape-format wrap panel (2400 × 900 px) designed to tile across
the side panels of a Model 3.  Chase is the hero image; his factory blue
background blends seamlessly into the wrap gradient.
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

# ── Paths ──────────────────────────────────────────────────────────────────
HERE       = Path(__file__).parent
CHASE_PATH = HERE / "paw_patrol_chase.jpg"
OUTPUT_DIR = HERE / "Wraps"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "Chase_Wrap.png"

# ── Canvas ─────────────────────────────────────────────────────────────────
W, H = 2400, 900

# ── Chase colour palette ────────────────────────────────────────────────────
BLUE_BG     = (14,  143, 204)   # Chase's bright BG blue
BLUE_MID    = (10,  107, 163)   # mid police blue
BLUE_DARK   = (8,   45,  90)    # very dark navy
BLUE_LIGHT  = (80,  185, 230)   # highlight sky blue
NAVY        = (22,  38,  80)    # Chase's uniform navy
GOLD        = (255, 200, 0)     # badge star / cap stripe
GOLD_DARK   = (180, 130, 0)
WHITE       = (255, 255, 255)
BLACK       = (10,  10,  10)
GREY_LIGHT  = (200, 210, 220)


# ── Helpers ────────────────────────────────────────────────────────────────

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_background() -> Image.Image:
    """Horizontal gradient: deep navy (left) → Chase blue (centre) → lighter blue (right)."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for x in range(W):
        t = x / (W - 1)
        if t < 0.45:
            c = lerp_color(BLUE_DARK, BLUE_MID, t / 0.45)
        else:
            c = lerp_color(BLUE_MID, BLUE_BG, (t - 0.45) / 0.55)
        draw.line([(x, 0), (x, H)], fill=c)
    return img.convert("RGBA")


def add_radar_rings(img: Image.Image, cx: int, cy: int, max_r: int) -> None:
    """Concentric semi-transparent tech circles — like Chase's background."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(60, max_r, 55):
        alpha = max(10, 50 - int(r / max_r * 45))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(*BLUE_LIGHT, alpha), width=2)
    img.alpha_composite(overlay)


def add_diagonal_stripes(img: Image.Image) -> None:
    """Navy + gold diagonal speed stripes across the bottom third."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    stripe_h = H // 4
    y_start = H - stripe_h
    # navy base band
    draw.rectangle([0, y_start, W, H], fill=(*NAVY, 230))
    # gold accent stripes
    spacing = 110
    for x in range(-H, W + H, spacing):
        pts = [(x, y_start), (x + 70, y_start),
               (x + 70 - stripe_h, H),   (x - stripe_h, H)]
        draw.polygon(pts, fill=(*GOLD, 180))
    overlay = overlay.filter(ImageFilter.GaussianBlur(1))
    img.alpha_composite(overlay)


def add_paw_prints(img: Image.Image, rng: random.Random) -> None:
    """Scatter white + navy paw prints at varying sizes and rotations."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for _ in range(55):
        cx = rng.randint(30, W - 30)
        cy = rng.randint(30, H - 30)
        sz = rng.randint(22, 55)
        color = rng.choice([WHITE, NAVY, GOLD, BLUE_DARK])
        alpha = rng.randint(60, 180)
        angle = rng.uniform(-40, 40)
        _draw_paw_onto(overlay, cx, cy, sz, color, alpha, angle)

    img.alpha_composite(overlay)


def _draw_paw_onto(img: Image.Image, cx, cy, sz, color, alpha, angle) -> None:
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    r, g, b = color
    fill = (r, g, b, alpha)
    pad_w, pad_h = int(sz * 0.55), int(sz * 0.45)
    d.ellipse([cx - pad_w, cy - pad_h // 2, cx + pad_w, cy + pad_h + pad_h // 2], fill=fill)
    toe_r = int(sz * 0.22)
    for dx, dy in [(-sz * 0.45, -sz * 0.8), (-sz * 0.15, -sz * 1.0),
                   (sz * 0.15, -sz * 1.0),  (sz * 0.45, -sz * 0.8)]:
        tx, ty = int(cx + dx), int(cy + dy)
        d.ellipse([tx - toe_r, ty - toe_r, tx + toe_r, ty + toe_r], fill=fill)
    rotated = tmp.rotate(angle, center=(cx, cy), resample=Image.BICUBIC)
    img.alpha_composite(rotated)


def draw_police_badge(img: Image.Image, cx: int, cy: int, r: int) -> None:
    """Gold star badge — Chase's chest badge, large decorative version."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    pts = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        radius = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius))
    draw.polygon(pts, fill=(*GOLD, 220), outline=(*GOLD_DARK, 255))
    # Inner circle
    draw.ellipse([cx - r * 0.28, cy - r * 0.28, cx + r * 0.28, cy + r * 0.28],
                 fill=(*NAVY, 240))
    img.alpha_composite(overlay)


def draw_paw_badge(img: Image.Image, cx: int, cy: int, r: int) -> None:
    """Shield with paw — like Chase's cap badge."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    hw = r
    shield = [(cx - hw, cy - hw), (cx + hw, cy - hw),
              (cx + hw, cy + hw * 0.4), (cx, cy + hw),
              (cx - hw, cy + hw * 0.4)]
    draw.polygon(shield, fill=(*NAVY, 240), outline=(*GOLD, 255))
    # Paw pad in the shield
    pw = int(r * 0.38)
    ph = int(r * 0.32)
    py_off = int(r * 0.12)
    draw.ellipse([cx - pw, cy + py_off - ph // 2, cx + pw, cy + py_off + ph], fill=(*WHITE, 230))
    tr = int(r * 0.14)
    for dx, dy in [(-r * 0.30, py_off - r * 0.52), (-r * 0.10, py_off - r * 0.62),
                   (r * 0.10, py_off - r * 0.62),  (r * 0.30, py_off - r * 0.52)]:
        draw.ellipse([cx + dx - tr, cy + dy - tr, cx + dx + tr, cy + dy + tr], fill=(*WHITE, 230))
    img.alpha_composite(overlay)


def add_paw_patrol_text(img: Image.Image) -> None:
    """'PAW PATROL' in big bold lettering on the left panel."""
    from PIL import ImageFont
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to load a bold system font; fall back to default
    font_big = font_small = None
    for path in [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(path):
            try:
                font_big   = ImageFont.truetype(path, 120)
                font_small = ImageFont.truetype(path, 46)
                break
            except Exception:
                continue

    if font_big is None:
        font_big = font_small = ImageFont.load_default()

    # Main title: "PAW PATROL"
    for offset, color in [((4, 4), (*BLUE_DARK, 200)), ((0, 0), (*GOLD, 255))]:
        draw.text((110 + offset[0], 160 + offset[1]), "PAW PATROL",
                  font=font_big, fill=color)
    # Sub-line
    draw.text((115, 295), "CHASE  ·  K-9  UNIT", font=font_small, fill=(*WHITE, 220))
    img.alpha_composite(overlay)


def paste_chase(img: Image.Image) -> None:
    """Scale Chase to fill the right ~45% of the canvas and blend him in.

    Chase's background is the same electric blue as our gradient, so we
    blend with Screen mode at the edges to make it seamless.
    """
    chase_src = Image.open(CHASE_PATH).convert("RGBA")
    src_w, src_h = chase_src.size   # 830 × 830

    # Target: fill the right portion of the wrap
    target_h = int(H * 1.08)        # slightly taller than canvas → crop top
    target_w = int(src_w * target_h / src_h)
    chase = chase_src.resize((target_w, target_h), Image.LANCZOS)

    # Right-justify with a bit of bleed; vertically align bottom
    paste_x = W - target_w + int(target_w * 0.08)
    paste_y = H - target_h + int(target_h * 0.04)

    # Build a soft-edge alpha mask so Chase blends into the background
    mask = Image.new("L", chase.size, 255)
    mask_draw = ImageDraw.Draw(mask)
    fade_w = int(target_w * 0.22)   # left-side fade
    for i in range(fade_w):
        alpha = int(255 * (i / fade_w) ** 1.8)
        mask_draw.line([(i, 0), (i, target_h)], fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(18))

    # Boost Chase's saturation and contrast slightly
    chase = ImageEnhance.Color(chase).enhance(1.15)
    chase = ImageEnhance.Contrast(chase).enhance(1.08)

    # Apply edge mask to Chase's own alpha
    r, g, b, a = chase.split()
    a = ImageChops.multiply(a, mask)
    chase = Image.merge("RGBA", (r, g, b, a))

    img.alpha_composite(chase, dest=(paste_x, paste_y))


def add_glow(img: Image.Image, cx: int, cy: int, radius: int) -> None:
    """Soft radial glow behind Chase to make him pop."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = 30
    for i in range(steps, 0, -1):
        t = i / steps
        r_cur = int(radius * t)
        alpha = int(35 * (1 - t) ** 0.6)
        draw.ellipse([cx - r_cur, cy - r_cur, cx + r_cur, cy + r_cur],
                     fill=(*BLUE_LIGHT, alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(overlay)


def add_top_stripe(img: Image.Image) -> None:
    """Thin gold + white stripe along the top edge."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([0, 0, W, 10], fill=(*GOLD, 220))
    draw.rectangle([0, 10, W, 18], fill=(*WHITE, 160))
    img.alpha_composite(overlay)


def add_bottom_badge_row(img: Image.Image) -> None:
    """Row of small star badges along the bottom stripe."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x in range(80, W - 40, 140):
        pts = []
        cx, cy, r = x, H - 30, 16
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        draw.polygon(pts, fill=(*GOLD, 180))
    img.alpha_composite(overlay)


def main() -> None:
    rng = random.Random(7)

    # 1. Background gradient
    img = make_background()

    # 2. Radar rings — centred behind Chase (right side)
    add_radar_rings(img, cx=int(W * 0.75), cy=int(H * 0.48), max_r=520)

    # 3. Diagonal speed stripes (bottom)
    add_diagonal_stripes(img)

    # 4. Top accent stripe
    add_top_stripe(img)

    # 5. Scattered paw prints
    add_paw_prints(img, rng)

    # 6. Decorative badges — left panel area
    draw_police_badge(img, cx=80,  cy=int(H * 0.20), r=48)
    draw_police_badge(img, cx=950, cy=int(H * 0.15), r=35)
    draw_paw_badge(img,   cx=80,  cy=int(H * 0.78), r=52)
    draw_paw_badge(img,   cx=920, cy=int(H * 0.80), r=36)

    # 7. "PAW PATROL" text
    add_paw_patrol_text(img)

    # 8. Glow behind where Chase will sit
    add_glow(img, cx=int(W * 0.74), cy=int(H * 0.44), radius=480)

    # 9. Paste Chase as the hero
    paste_chase(img)

    # 10. Bottom badge row
    add_bottom_badge_row(img)

    # 11. Save
    final = img.convert("RGB")
    final.save(str(OUTPUT_PATH), "PNG", optimize=True)

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"Saved  →  {OUTPUT_PATH}  ({size_kb:.1f} KB)")
    assert size_kb < 8192, f"Too large: {size_kb:.1f} KB"
    print("✓ Wrap ready.")


if __name__ == "__main__":
    main()
