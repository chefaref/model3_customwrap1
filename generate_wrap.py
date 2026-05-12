"""Tesla Model 3 (2024+ base) — Chase Paw Patrol custom wrap generator.

Fills the official Tesla UV template (model3_template.png) with a Chase-themed
design, then saves a correctly-spec'd PNG to Wraps/Chase_Wrap.png ready for:
  USB (Wraps/ folder, exFAT/FAT32) → car Toybox → Paint Shop → Wraps tab
"""

import math
import os
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops

HERE          = Path(__file__).parent
TEMPLATE_PATH = HERE / "model3_template.png"
CHASE_PATH    = HERE / "paw_patrol_chase.jpg"
OUTPUT_DIR    = HERE / "Wraps"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH   = OUTPUT_DIR / "Chase_Wrap.png"

SIZE = 1024   # Tesla requires 512–1024; we use max for quality

# ── Chase / Paw Patrol palette ─────────────────────────────────────────────
BLUE_BG    = (14,  143, 204)
BLUE_MID   = (10,  100, 160)
BLUE_DARK  = (6,   42,  86)
BLUE_LIGHT = (80,  190, 235)
NAVY       = (20,  36,  78)
GOLD       = (255, 200,  0)
GOLD_DARK  = (170, 125,  0)
WHITE      = (255, 255, 255)


# ── Helpers ────────────────────────────────────────────────────────────────

def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ── Layer 1: background gradient ──────────────────────────────────────────

def make_background() -> Image.Image:
    """Radial gradient: bright Chase-blue at centre fading to deep navy at edges."""
    img = Image.new("RGBA", (SIZE, SIZE))
    cx, cy = SIZE // 2, SIZE // 2
    arr = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    ys, xs = np.mgrid[0:SIZE, 0:SIZE]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    max_d = math.sqrt(2) * cx
    t = np.clip(dist / max_d, 0, 1)
    for ch, (a, b) in enumerate(zip(BLUE_BG, BLUE_DARK)):
        arr[:, :, ch] = (a * (1 - t) + b * t).astype(np.uint8)
    arr[:, :, 3] = 255
    return Image.fromarray(arr, "RGBA")


# ── Layer 2: radar tech rings (Chase's background motif) ──────────────────

def add_radar_rings(img: Image.Image) -> None:
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx = cy = SIZE // 2
    for r in range(50, 560, 48):
        alpha = max(8, 55 - int(r / 560 * 50))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(*BLUE_LIGHT, alpha), width=2)
    img.alpha_composite(overlay)


# ── Layer 3: diagonal speed stripes ───────────────────────────────────────

def add_speed_stripes(img: Image.Image) -> None:
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Bottom quarter: dark navy base
    draw.rectangle([0, int(SIZE * 0.76), SIZE, SIZE], fill=(*NAVY, 220))
    # Gold diagonal stripes over it
    for x in range(-SIZE, SIZE * 2, 95):
        pts = [(x, int(SIZE * 0.76)), (x + 55, int(SIZE * 0.76)),
               (x + 55 - int(SIZE * 0.24), SIZE),
               (x     - int(SIZE * 0.24), SIZE)]
        draw.polygon(pts, fill=(*GOLD, 170))
    img.alpha_composite(overlay)


# ── Layer 4: paw prints ────────────────────────────────────────────────────

def _paw(canvas: Image.Image, cx, cy, sz, color, alpha, angle):
    tmp = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d   = ImageDraw.Draw(tmp)
    r, g, b = color
    f = (r, g, b, alpha)
    pw, ph = int(sz * 0.55), int(sz * 0.45)
    d.ellipse([cx - pw, cy - ph // 2, cx + pw, cy + ph + ph // 2], fill=f)
    tr = int(sz * 0.22)
    for dx, dy in [(-sz*.45, -sz*.80), (-sz*.15, -sz*1.0),
                   ( sz*.15, -sz*1.0), ( sz*.45, -sz*.80)]:
        tx, ty = int(cx + dx), int(cy + dy)
        d.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill=f)
    canvas.alpha_composite(tmp.rotate(angle, center=(cx, cy),
                                       resample=Image.BICUBIC))


def add_paw_prints(img: Image.Image, rng: random.Random) -> None:
    for _ in range(60):
        _paw(img,
             cx=rng.randint(20, SIZE - 20),
             cy=rng.randint(20, SIZE - 20),
             sz=rng.randint(18, 44),
             color=rng.choice([WHITE, NAVY, GOLD, BLUE_DARK]),
             alpha=rng.randint(45, 160),
             angle=rng.uniform(-45, 45))


# ── Layer 5: gold star badge ───────────────────────────────────────────────

def draw_star(img: Image.Image, cx, cy, r, fill=GOLD, outline=GOLD_DARK,
              fill_alpha=220, outline_alpha=255):
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    pts = []
    for i in range(10):
        ang = math.radians(i * 36 - 90)
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.polygon(pts, fill=(*fill, fill_alpha), outline=(*outline, outline_alpha))
    draw.ellipse([cx - r * .26, cy - r * .26, cx + r * .26, cy + r * .26],
                 fill=(*NAVY, 240))
    img.alpha_composite(overlay)


# ── Layer 6: Chase hero image ──────────────────────────────────────────────

def paste_chase(img: Image.Image) -> None:
    """
    Place Chase so his face sits prominently on the left door panels
    (the large rectangular zone at roughly cols 30-210, rows 340-730 in the UV map).
    We mirror him to the right door panels too so both sides of the car match.
    """
    chase_src = Image.open(CHASE_PATH).convert("RGBA")
    # Boost colour and contrast slightly
    chase_src = ImageEnhance.Color(chase_src).enhance(1.2)
    chase_src = ImageEnhance.Contrast(chase_src).enhance(1.1)

    def _paste_instance(target_w, target_h, dest_x, dest_y, flip=False):
        chase = chase_src.copy()
        if flip:
            chase = chase.transpose(Image.FLIP_LEFT_RIGHT)
        chase = chase.resize((target_w, target_h), Image.LANCZOS)

        # Soft left/right fade so Chase blends into the background
        mask = Image.new("L", chase.size, 255)
        md   = ImageDraw.Draw(mask)
        fw   = int(target_w * 0.18)
        for i in range(fw):
            a = int(255 * (i / fw) ** 2)
            md.line([(i, 0), (i, target_h)], fill=a)
            md.line([(target_w - 1 - i, 0), (target_w - 1 - i, target_h)], fill=a)
        # Top fade
        fh = int(target_h * 0.12)
        for i in range(fh):
            a = int(255 * (i / fh) ** 2)
            md.line([(0, i), (target_w, i)], fill=a)
        mask = mask.filter(ImageFilter.GaussianBlur(10))

        r, g, b, a = chase.split()
        a = ImageChops.multiply(a, mask)
        chase = Image.merge("RGBA", (r, g, b, a))
        img.alpha_composite(chase, dest=(dest_x, dest_y))

    # Left door area: roughly 180 × 390 px at (30, 340)
    # Scale Chase to fill that zone (let him bleed a bit)
    _paste_instance(target_w=230, target_h=430, dest_x=18, dest_y=318, flip=False)

    # Right door area: mirrored, roughly same size at (~790, 340)
    _paste_instance(target_w=230, target_h=430, dest_x=790, dest_y=318, flip=True)

    # Also place a smaller Chase on the rear deck panel area (centre-bottom)
    _paste_instance(target_w=180, target_h=200, dest_x=420, dest_y=750, flip=False)


# ── Layer 7: "PAW PATROL" text on the hood/roof panels ────────────────────

def add_text(img: Image.Image) -> None:
    from PIL import ImageFont
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    font_large = font_small = None
    for path in [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            try:
                font_large = ImageFont.truetype(path, 68)
                font_small = ImageFont.truetype(path, 28)
                break
            except Exception:
                pass
    if font_large is None:
        font_large = font_small = ImageFont.load_default()

    # Hood area is roughly centre of canvas, rows 200-380 — place text there
    cx = SIZE // 2
    # Shadow
    draw.text((cx - 138, 222), "PAW PATROL", font=font_large, fill=(*BLUE_DARK, 180))
    # Gold text
    draw.text((cx - 140, 220), "PAW PATROL", font=font_large, fill=(*GOLD, 230))
    draw.text((cx - 78, 298), "CHASE · K-9 UNIT", font=font_small, fill=(*WHITE, 200))
    img.alpha_composite(overlay)


# ── Layer 8: accent stars ─────────────────────────────────────────────────

def add_accent_stars(img: Image.Image) -> None:
    # Small stars scattered around panel edges
    positions = [
        (100, 110, 28), (920, 110, 28),
        (100, 880, 24), (920, 880, 24),
        (512, 150, 22), (512, 870, 20),
        (55,  512, 20), (965, 512, 20),
    ]
    for cx, cy, r in positions:
        draw_star(img, cx, cy, r)


# ── Mask to template + overlay outlines ──────────────────────────────────

def apply_template(design: Image.Image, template: Image.Image) -> Image.Image:
    """
    Keep design pixels only where the template has opaque (panel) pixels.
    Then composite the dark outline pixels from the template on top so panel
    borders stay crisp on the car's 3D display.
    """
    t_arr  = np.array(template)
    d_arr  = np.array(design)
    out    = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)

    t_alpha = t_arr[:, :, 3]
    t_r, t_g, t_b = t_arr[:,:,0], t_arr[:,:,1], t_arr[:,:,2]
    is_dark    = (t_r < 60) & (t_g < 60) & (t_b < 60) & (t_alpha > 100)
    is_panel   = (t_alpha > 0) & ~is_dark      # white fill areas

    # Panel areas → design colour
    out[is_panel] = d_arr[is_panel]
    # Outline pixels → keep the dark template lines
    out[is_dark] = t_arr[is_dark]
    # Everywhere else → transparent
    return Image.fromarray(out, "RGBA")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    rng      = random.Random(42)
    template = Image.open(TEMPLATE_PATH).convert("RGBA")

    # Build design layers (all on a full 1024×1024 canvas)
    img = make_background()
    add_radar_rings(img)
    add_speed_stripes(img)
    add_paw_prints(img, rng)
    paste_chase(img)
    add_text(img)
    add_accent_stars(img)

    # Mask to the UV template shape and restore panel outlines
    result = apply_template(img, template)

    # Save — must be PNG ≤ 1 MB, 512–1024 px
    result.save(str(OUTPUT_PATH), "PNG", optimize=True)
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"Saved  →  {OUTPUT_PATH}  ({size_kb:.1f} KB)")
    assert size_kb < 1024, f"File too large: {size_kb:.1f} KB (limit 1024 KB)"
    print("✓ Ready — copy Wraps/Chase_Wrap.png to USB Wraps/ folder")
    print("  In car: Toybox → Paint Shop → Wraps tab")


if __name__ == "__main__":
    main()
