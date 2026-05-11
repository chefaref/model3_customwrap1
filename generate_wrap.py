"""Generates a Paw Patrol themed custom wrap for Tesla Model 3."""

import math
import random
from PIL import Image, ImageDraw, ImageFilter

TEMPLATE_PATH = "/tmp/model3_template.png"
OUTPUT_PATH = "/home/user/model3_customwrap1/Paw_Patrol.png"
SIZE = 1024

# Paw Patrol color palette
BLUE        = (91,  191, 239)   # sky blue (main)
BLUE_DARK   = (30,  120, 190)   # deep blue
RED         = (224, 52,  52)    # Marshall red
YELLOW      = (255, 210, 40)    # Rubble yellow
ORANGE      = (240, 130, 30)    # Zuma orange
GREEN       = (60,  180, 75)    # Rocky green
PURPLE      = (140, 80,  200)   # Skye purple
TEAL        = (0,   180, 170)   # Everest teal
PAW_BROWN   = (120, 70,  30)    # paw print brown
PAW_LIGHT   = (200, 140, 90)    # paw print light
WHITE       = (255, 255, 255)


def draw_paw(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int,
             color: tuple, alpha: int = 200) -> None:
    """Draw a single paw print (main pad + 4 toe pads)."""
    r, g, b = color
    fill = (r, g, b, alpha)

    # Main pad (rounded rectangle approximated as ellipse)
    pad_w = int(size * 0.55)
    pad_h = int(size * 0.45)
    draw.ellipse(
        [cx - pad_w, cy - pad_h // 2, cx + pad_w, cy + pad_h + pad_h // 2],
        fill=fill,
    )

    # Four toe pads arranged in a slight arc above the main pad
    toe_r = int(size * 0.22)
    offsets = [(-size * 0.45, -size * 0.8), (-size * 0.15, -size * 1.0),
               (size * 0.15, -size * 1.0), (size * 0.45, -size * 0.8)]
    for dx, dy in offsets:
        tx, ty = int(cx + dx), int(cy + dy)
        draw.ellipse([tx - toe_r, ty - toe_r, tx + toe_r, ty + toe_r], fill=fill)


def draw_shield(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    """Draw a Paw Patrol badge shield outline."""
    hw = size // 2
    pts = [
        (cx - hw, cy - hw),
        (cx + hw, cy - hw),
        (cx + hw, cy + hw // 3),
        (cx, cy + hw),
        (cx - hw, cy + hw // 3),
    ]
    draw.polygon(pts, fill=(RED[0], RED[1], RED[2], 230),
                 outline=(WHITE[0], WHITE[1], WHITE[2], 255))


def make_background(size: int) -> Image.Image:
    """Create a blue radial-gradient background."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient bands: dark blue at edges → bright sky-blue at centre
    steps = 60
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(BLUE_DARK[0] * (1 - t) + BLUE[0] * t)
        g = int(BLUE_DARK[1] * (1 - t) + BLUE[1] * t)
        b = int(BLUE_DARK[2] * (1 - t) + BLUE[2] * t)
        margin = int((size // 2) * (1 - t))
        draw.rectangle([margin, margin, size - margin, size - margin],
                       fill=(r, g, b, 255))
    return img


def scatter_paws(draw: ImageDraw.ImageDraw, rng: random.Random) -> None:
    """Randomly scatter paw prints across the image."""
    colors = [PAW_BROWN, PAW_LIGHT, RED, YELLOW, ORANGE, GREEN, PURPLE, TEAL, WHITE]
    for _ in range(55):
        cx = rng.randint(40, SIZE - 40)
        cy = rng.randint(40, SIZE - 40)
        sz = rng.randint(14, 38)
        color = rng.choice(colors)
        alpha = rng.randint(120, 210)
        angle = rng.uniform(-40, 40)

        # Rotate a temp image and paste
        tmp = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        draw_paw(tmp_draw, cx, cy, sz, color, alpha)
        rotated = tmp.rotate(angle, center=(cx, cy), resample=Image.BICUBIC)
        draw._image.alpha_composite(rotated)


def add_stars(draw: ImageDraw.ImageDraw, rng: random.Random) -> None:
    """Add small sparkle dots for a lively feel."""
    for _ in range(80):
        x = rng.randint(0, SIZE)
        y = rng.randint(0, SIZE)
        r = rng.randint(1, 4)
        a = rng.randint(80, 200)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(255, 255, 255, a))


def add_stripes(img: Image.Image) -> None:
    """Add subtle diagonal colour stripes for depth."""
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    stripe_colors = [RED, YELLOW, ORANGE, GREEN, PURPLE, TEAL]
    for i, color in enumerate(stripe_colors):
        offset = i * (SIZE // len(stripe_colors)) + SIZE // (2 * len(stripe_colors))
        r, g, b = color
        for width_offset in range(-8, 9):
            x = offset + width_offset
            draw.line([(x, 0), (x - SIZE // 2, SIZE)],
                      fill=(r, g, b, 18), width=1)
    overlay = overlay.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(overlay)


def add_shields(img: Image.Image) -> None:
    """Place a few small shields as accent motifs."""
    positions = [(200, 160), (820, 160), (200, 860), (820, 860), (512, 512)]
    sizes =     [45, 45, 45, 45, 70]
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for (cx, cy), sz in zip(positions, sizes):
        draw_shield(draw, cx, cy, sz)
    img.alpha_composite(overlay)


def add_large_center_paw(img: Image.Image) -> None:
    """Place a large hero paw print at the centre."""
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw_paw(draw, SIZE // 2, SIZE // 2 + 20, 90, WHITE, 230)
    draw_paw(draw, SIZE // 2, SIZE // 2 + 20, 78, PAW_BROWN, 240)
    img.alpha_composite(overlay)


def apply_template_mask(design: Image.Image, template: Image.Image) -> Image.Image:
    """
    Keep only the parts of the design that fall inside the car body shape
    defined by the template's alpha channel. The template pixels themselves
    are pure white, so we use only the alpha as a cutout mask.
    """
    result = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    template_alpha = template.split()[3]
    result.paste(design, mask=template_alpha)
    return result


def main() -> None:
    rng = random.Random(42)  # fixed seed for reproducibility

    # 1. Build background
    img = make_background(SIZE)
    draw = ImageDraw.Draw(img)

    # 2. Diagonal colour stripes
    add_stripes(img)

    # 3. Scattered paw prints (mutates img via alpha_composite inside)
    scatter_paws(draw, rng)

    # 4. Shield motifs
    add_shields(img)

    # 5. Hero centre paw
    add_large_center_paw(img)

    # 6. Star sparkles
    draw = ImageDraw.Draw(img)
    add_stars(draw, rng)

    # 7. Apply template mask
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    wrapped = apply_template_mask(img, template)

    # 8. Save — optimise to stay well under the 1 MB limit
    wrapped.save(OUTPUT_PATH, "PNG", optimize=True)

    size_kb = __import__("os").path.getsize(OUTPUT_PATH) / 1024
    print(f"Saved {OUTPUT_PATH}  ({size_kb:.1f} KB)")
    assert size_kb < 1024, f"File too large: {size_kb:.1f} KB (max 1024 KB)"
    print("✓ All checks passed — ready for USB transfer.")


if __name__ == "__main__":
    main()
