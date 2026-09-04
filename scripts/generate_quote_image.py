"""
Generates a motivational quote image (textured background + centered text) for the
motivational Instagram page. No external API/account needed — the background texture
is generated procedurally (noise + gradient), not downloaded, so this works fully
offline and doesn't depend on any new credentials.

Usage:
    python scripts/generate_quote_image.py "Текст цитаты" --style wall --out out.jpg
    python scripts/generate_quote_image.py "Текст цитаты" --style sand --out out.jpg
"""

import argparse
import random
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1080, 1350  # Instagram feed portrait (4:5)

STYLES = {
    "wall": {
        # cool concrete-gray tones
        "base_low": (58, 58, 62),
        "base_high": (92, 92, 98),
        "noise_strength": 14,
        "text_color": (245, 245, 240),
    },
    "sand": {
        # warm beige/tan tones
        "base_low": (156, 128, 92),
        "base_high": (206, 178, 138),
        "noise_strength": 12,
        "text_color": (255, 250, 240),
    },
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\georgiab.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    r"C:\Windows\Fonts\Montserrat-Regular.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]

# A script/cursive face reads as "handwritten" far better than a print face for the
# beach_sunset style's "written with a stick in the sand" text — kept as a SEPARATE
# candidate list from FONT_CANDIDATES (used by wall/sand) rather than reordering that
# one, so the existing styles' typography is untouched.
HANDWRITING_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoescb.ttf",
    r"C:\Windows\Fonts\segoesc.ttf",
    r"C:\Windows\Fonts\comici.ttf",
] + FONT_CANDIDATES


def find_font(candidates: list[str] = FONT_CANDIDATES) -> str:
    for path in candidates:
        if Path(path).exists():
            return path
    raise FileNotFoundError(
        f"None of the candidate fonts were found on this machine: {candidates}"
    )


def make_textured_background(style: str, seed: int | None = None) -> Image.Image:
    cfg = STYLES[style]
    rng = random.Random(seed)

    # Diagonal gradient base.
    base = Image.new("RGB", (WIDTH, HEIGHT))
    low, high = cfg["base_low"], cfg["base_high"]
    for y in range(HEIGHT):
        t = y / HEIGHT
        row_color = tuple(int(low[i] + (high[i] - low[i]) * t) for i in range(3))
        for x_chunk in range(0, WIDTH, 4):
            base.paste(row_color, (x_chunk, y, min(x_chunk + 4, WIDTH), y + 1))

    # Noise layer for texture (grain), blurred slightly so it reads as a surface,
    # not digital static.
    noise = Image.effect_noise((WIDTH, HEIGHT), cfg["noise_strength"]).convert("L")
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    textured = Image.blend(base, noise_rgb, alpha=0.18)
    textured = textured.filter(ImageFilter.GaussianBlur(radius=0.6))

    # Vignette for text contrast: darken edges.
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse(
        (-WIDTH * 0.3, -HEIGHT * 0.2, WIDTH * 1.3, HEIGHT * 1.2), fill=255
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=180))
    dark = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    textured = Image.composite(textured, dark, vignette)

    return textured


def line_step(font: ImageFont.FreeTypeFont) -> int:
    # Fixed line pitch based on font size (standard ~1.35x leading), rather than
    # per-line glyph bounding boxes — bbox heights vary with ascenders/descenders
    # ("у", "р", "б", "й") and using them directly caused overlapping lines.
    return int(font.size * 1.35)


def wrap_text_to_fit(draw: ImageDraw.ImageDraw, text: str, font_path: str, max_width: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    size = 96
    min_size = 40
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        avg_char_w = draw.textlength("Абвгдежклмнопрст", font=font) / 16
        wrap_width = max(10, int(max_width / max(avg_char_w, 1)))
        lines = textwrap.wrap(text, width=wrap_width)
        total_h = line_step(font) * len(lines)
        widest = max(draw.textlength(line, font=font) for line in lines) if lines else 0
        if total_h <= HEIGHT * 0.62 and widest <= max_width:
            return font, lines
        size -= 4
    font = ImageFont.truetype(font_path, min_size)
    return font, textwrap.wrap(text, width=30)


def draw_centered_text(img: Image.Image, text: str, text_color: tuple[int, int, int], font_path: str) -> None:
    draw = ImageDraw.Draw(img)
    max_width = int(WIDTH * 0.82)
    font, lines = wrap_text_to_fit(draw, text, font_path, max_width)

    step = line_step(font)
    total_h = step * len(lines)
    y = (HEIGHT - total_h) / 2

    shadow_offset = max(2, font.size // 40)
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (WIDTH - w) / 2
        # Soft shadow for legibility over the textured background.
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=font, fill=text_color)
        y += step


def _lerp_color(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _vertical_gradient(width: int, height: int, stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """`stops` is a list of (position 0..1, color), sorted by position. Paints in 4px row
    chunks like make_textured_background already does — cheap and plenty smooth at this
    resolution, no need for a slower per-pixel loop."""
    img = Image.new("RGB", (width, height))
    for y in range(height):
        t = y / max(height - 1, 1)
        # find the two stops t falls between
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1 or i == len(stops) - 2:
                local_t = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                local_t = max(0.0, min(1.0, local_t))
                color = _lerp_color(c0, c1, local_t)
                break
        for x_chunk in range(0, width, 4):
            img.paste(color, (x_chunk, y, min(x_chunk + 4, width), y + 1))
    return img


def _draw_ship_silhouette(img: Image.Image, cx: int, horizon_y: int, scale: float) -> None:
    """A large sailing ship silhouette sitting ON the horizon line, backlit by the sunset —
    pure dark silhouette (no interior detail), which is both how a real distant ship reads
    against a sunset and the only realistic way to render one without a photo/asset."""
    draw = ImageDraw.Draw(img, "RGBA")
    color = (25, 18, 22, 235)

    hull_w = int(220 * scale)
    hull_h = int(34 * scale)
    hull = [
        (cx - hull_w // 2, horizon_y),
        (cx - hull_w // 2 + 14 * scale, horizon_y + hull_h),
        (cx + hull_w // 2 - 14 * scale, horizon_y + hull_h),
        (cx + hull_w // 2, horizon_y),
    ]
    draw.polygon(hull, fill=color)

    # Three masts of decreasing height toward the bow, each with a quadrilateral sail —
    # a classic tall-ship silhouette, not a single generic triangle.
    mast_defs = [(-0.30, 1.0), (0.0, 1.35), (0.30, 0.85)]
    for rel_x, height_mul in mast_defs:
        mx = cx + int(rel_x * hull_w)
        mast_h = int(150 * scale * height_mul)
        mast_top = horizon_y - mast_h
        draw.line([(mx, horizon_y), (mx, mast_top)], fill=color, width=max(2, int(3 * scale)))
        sail_w = int(46 * scale * height_mul)
        sail = [
            (mx, mast_top + int(8 * scale)),
            (mx + sail_w, mast_top + int(30 * scale)),
            (mx + sail_w * 0.7, horizon_y - int(20 * scale)),
            (mx, horizon_y - int(4 * scale)),
        ]
        draw.polygon(sail, fill=color)

    # Slight blur = atmospheric haze at distance, not a crisp cardboard cutout.
    haze = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(hull, fill=255)
    for rel_x, height_mul in mast_defs:
        mx = cx + int(rel_x * hull_w)
        ImageDraw.Draw(mask).line(
            [(mx, horizon_y), (mx, horizon_y - int(150 * scale * height_mul))], fill=255, width=6,
        )
    img.paste(haze, (0, 0), mask)


def make_sunset_ocean_scene(width: int, height: int, seed: int | None = None) -> tuple[Image.Image, int, int]:
    """Sky + sun + ocean + ship + wet-sand base, all procedural (gradients/noise/shapes —
    no downloaded photo, per the hard requirement). Returns (image, horizon_y, sand_top_y)
    so the caller knows where to place footprints/text without recomputing the layout."""
    rng = random.Random(seed)
    horizon_y = int(height * 0.40)
    sand_top_y = int(height * 0.58)

    sky = _vertical_gradient(width, horizon_y, [
        (0.0, (35, 20, 58)),
        (0.35, (120, 55, 68)),
        (0.7, (224, 108, 62)),
        (1.0, (255, 197, 130)),
    ])

    ocean = _vertical_gradient(width, sand_top_y - horizon_y, [
        (0.0, (255, 190, 130)),
        (0.12, (233, 140, 96)),
        (0.4, (120, 108, 108)),
        (1.0, (28, 58, 78)),
    ])
    # Wave texture: rows of subtle brightness noise, blurred so it reads as ripples,
    # not digital static — same trick make_textured_background already uses for sand/wall.
    wave_noise = Image.effect_noise((width, sand_top_y - horizon_y), 22).convert("L")
    wave_rgb = Image.merge("RGB", (wave_noise, wave_noise, wave_noise))
    ocean = Image.blend(ocean, wave_rgb, alpha=0.10)
    ocean = ocean.filter(ImageFilter.GaussianBlur(radius=0.8))

    img = Image.new("RGB", (width, height), (0, 0, 0))
    img.paste(sky, (0, 0))
    img.paste(ocean, (0, horizon_y))

    # Sun: bright core + soft glow, straddling the horizon like a real sunset.
    sun_x = int(width * 0.62)
    sun_r = int(height * 0.045)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((sun_x - sun_r * 3, horizon_y - sun_r * 3, sun_x + sun_r * 3, horizon_y + sun_r * 3),
                  fill=(255, 214, 150, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=sun_r * 0.8))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((sun_x - sun_r, horizon_y - sun_r, sun_x + sun_r, horizon_y + sun_r), fill=(255, 238, 205))

    # Sun's reflection on the water: real sunset-shimmer is a BROKEN cluster of short
    # glinting streaks (rippled water), not a solid wedge — a handful of independently
    # blurred, randomly-offset strokes within a tapering envelope reads far more like
    # light-on-water than one uniform triangle did.
    refl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    band_span = sand_top_y - horizon_y
    for _ in range(70):
        t = rng.uniform(0, 1)
        y = horizon_y + int(t * band_span)
        band_w = sun_r * (1.5 - t * 1.0)
        sx = sun_x + rng.uniform(-band_w, band_w)
        seg_len = rng.uniform(10, 34) * (1 - t * 0.4)
        alpha = int(rng.uniform(70, 170) * (1 - t * 0.6))
        stroke = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sdraw2 = ImageDraw.Draw(stroke)
        sdraw2.line([(sx, y), (sx, y + seg_len)], fill=(255, 228, 178, alpha), width=max(2, int(3 - t)))
        stroke = stroke.filter(ImageFilter.GaussianBlur(radius=rng.uniform(1.0, 2.6)))
        refl = Image.alpha_composite(refl, stroke)
    img = Image.alpha_composite(img.convert("RGBA"), refl).convert("RGB")

    _draw_ship_silhouette(img, int(width * 0.28), horizon_y, scale=width / 1080)

    # Wet sand strip: base gradient (dark/wet near the water, lighter/drier toward the
    # bottom edge), textured, with a thin reflective sheen right at the waterline.
    sand = _vertical_gradient(width, height - sand_top_y, [
        (0.0, (94, 72, 52)),
        (0.15, (150, 120, 88)),
        (1.0, (206, 176, 138)),
    ])
    grain = Image.effect_noise((width, height - sand_top_y), 16).convert("L")
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    sand = Image.blend(sand, grain_rgb, alpha=0.14)
    # Larger, low-frequency blotches for real unevenness (damp patches, shallow dips) —
    # a second, heavily-blurred noise layer at low opacity, distinct from the fine grain.
    blotch = Image.effect_noise((width, height - sand_top_y), 40).convert("L").filter(ImageFilter.GaussianBlur(radius=18))
    blotch_rgb = Image.merge("RGB", (blotch, blotch, blotch))
    sand = Image.blend(sand, blotch_rgb, alpha=0.10)
    img.paste(sand, (0, sand_top_y))

    # Wet-sheen band exactly on the sand/water seam — wet sand mirrors the sky faintly.
    sheen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(sheen)
    sdraw.rectangle((0, sand_top_y - 6, width, sand_top_y + 26), fill=(255, 214, 168, 70))
    sheen = sheen.filter(ImageFilter.GaussianBlur(radius=10))
    img = Image.alpha_composite(img.convert("RGBA"), sheen).convert("RGB")

    return img, horizon_y, sand_top_y


def draw_footprints(img: Image.Image, sand_top_y: int, height: int, width: int, rng: random.Random) -> None:
    """A barefoot trail crossing the sand — paired ellipses (heel->ball) plus toe dots,
    alternating left/right, each footprint slightly rotated and irregular like a real
    footfall (not a stamped, identical repeat)."""
    draw = ImageDraw.Draw(img, "RGBA")
    shadow = (60, 42, 28, 130)
    trail_y0 = sand_top_y + int((height - sand_top_y) * 0.10)
    trail_y1 = height - int((height - sand_top_y) * 0.08)
    steps = 6
    path_x = [int(width * 0.06 + (width * 0.26) * (i / steps) + rng.uniform(-10, 10)) for i in range(steps)]
    path_y = [int(trail_y0 + (trail_y1 - trail_y0) * (i / steps)) for i in range(steps)]

    for i in range(steps):
        cx, cy = path_x[i], path_y[i]
        side = 1 if i % 2 == 0 else -1  # alternating left/right foot offset + rotation
        fx = cx + side * 22
        angle = rng.uniform(-10, 10) + side * 10
        foot_w, foot_h = rng.randint(46, 54), rng.randint(88, 100)

        pad = foot_w
        canvas_w, canvas_h = foot_w + pad * 2, foot_h + pad * 2
        foot = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        fdraw = ImageDraw.Draw(foot)
        ox, oy = pad, pad
        # One continuous sole outline (not two overlapping circles) — wider/rounder at the
        # ball (top), narrowing toward the heel (bottom), like an actual pressed footprint.
        sole = [
            (ox + foot_w * 0.50, oy + foot_h * 0.00),
            (ox + foot_w * 0.92, oy + foot_h * 0.16),
            (ox + foot_w * 1.00, oy + foot_h * 0.40),
            (ox + foot_w * 0.86, oy + foot_h * 0.62),
            (ox + foot_w * 0.66, oy + foot_h * 0.80),
            (ox + foot_w * 0.60, oy + foot_h * 0.97),
            (ox + foot_w * 0.40, oy + foot_h * 0.97),
            (ox + foot_w * 0.34, oy + foot_h * 0.80),
            (ox + foot_w * 0.14, oy + foot_h * 0.62),
            (ox + foot_w * 0.00, oy + foot_h * 0.40),
            (ox + foot_w * 0.08, oy + foot_h * 0.16),
        ]
        fdraw.polygon(sole, fill=shadow)
        # Toes: a tight, gently curved cluster ABOVE the ball of the foot with a small gap
        # separating them from the sole outline (a real footprint's toes don't fuse into the
        # sole silhouette) — drawn a shade darker so they stay visually distinct even small.
        toe_shadow = (44, 30, 18, 190)
        toe_cy = oy - foot_h * 0.10
        toe_cx = ox + foot_w * 0.5
        toe_r = foot_w * 0.135
        for t in range(5):
            frac = (t - 2) / 2  # -1..1 across the 5 toes
            tx = toe_cx + frac * foot_w * 0.40
            ty = toe_cy + abs(frac) * foot_h * 0.05  # slight arc, big-toe-highest
            r = toe_r * (1.35 - t * 0.16)  # big toe (t=0) largest, tapering to the pinky (t=4)
            fdraw.ellipse((tx - r, ty - r, tx + r, ty + r), fill=toe_shadow)
        foot = foot.filter(ImageFilter.GaussianBlur(radius=0.6))
        foot = foot.rotate(angle, resample=Image.BICUBIC, expand=True)
        img.paste(foot, (fx - foot.width // 2, cy - foot.height // 2), foot)


def _draw_jittered_text_groove(
    img: Image.Image,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    start_y: int,
    step: int,
    width: int,
    rng: random.Random,
) -> None:
    """Renders each CHARACTER as its own slightly rotated/jittered glyph with a carved-groove
    shading (dark shadow on the dug side, light highlight on the raised sand lip) instead of
    one flat string draw — this is what actually sells "written by hand with a stick in sand"
    rather than "text pasted on a photo"."""
    draw = ImageDraw.Draw(img)
    dark = (58, 40, 26, 235)     # shadowed groove wall
    light = (232, 205, 168, 200)  # sand lip catching the sunset light
    fill = (86, 60, 38, 255)     # exposed damp sand at the bottom of the groove

    for li, line in enumerate(lines):
        line_w = draw.textlength(line, font=font)
        x = (width - line_w) / 2
        y = start_y + li * step
        for ch in line:
            ch_w = draw.textlength(ch, font=font) if ch != " " else font.size * 0.32
            if ch == " ":
                x += ch_w
                continue
            # Desired on-screen CENTER for this glyph — advancing by the center (not a
            # top-left corner) is what makes the expand=True rotation below land correctly.
            center_x = x + ch_w / 2
            center_y = y + font.size * 0.42

            margin = int(font.size * 0.6)
            canvas_w, canvas_h = int(ch_w) + margin * 2, font.size + margin * 2
            glyph = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glyph)
            # Drawn centered in ITS OWN canvas — text draws from the top-left of the glyph's
            # bbox, so offset by half the (canvas - char) span on each axis.
            gx, gy = margin, margin
            gdraw.text((gx + 2, gy + 3), ch, font=font, fill=dark)
            gdraw.text((gx - 1, gy - 1), ch, font=font, fill=light)
            gdraw.text((gx, gy), ch, font=font, fill=fill)

            angle = rng.uniform(-7, 7)
            jitter_y = rng.uniform(-4, 4)
            # rotate(expand=True) pivots around THIS canvas's own center and grows outward
            # symmetrically — so as long as we paste the new (bigger) canvas centered on the
            # same on-screen point, the glyph's visual position is rotation-angle-independent.
            glyph = glyph.rotate(angle, resample=Image.BICUBIC, expand=True)
            paste_x = int(center_x - glyph.width / 2)
            paste_y = int(center_y + jitter_y - glyph.height / 2)
            img.paste(glyph, (paste_x, paste_y), glyph)
            x += ch_w + rng.uniform(0, 2)  # slightly uneven letter spacing, like real handwriting — never negative


def draw_sand_written_text(img: Image.Image, text: str, sand_top_y: int, height: int, width: int, font_path: str, rng: random.Random) -> None:
    draw = ImageDraw.Draw(img)
    max_width = int(width * 0.8)
    size = min(120, int(width * 0.09))
    min_size = 34
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        avg_char_w = draw.textlength("Абвгдежклмнопрст", font=font) / 16
        wrap_width = max(8, int(max_width / max(avg_char_w, 1)))
        lines = textwrap.wrap(text, width=wrap_width)
        step = int(size * 1.3)
        total_h = step * len(lines)
        widest = max(draw.textlength(line, font=font) for line in lines) if lines else 0
        if total_h <= (height - sand_top_y) * 0.55 and widest <= max_width:
            break
        size -= 4
    else:
        font = ImageFont.truetype(font_path, min_size)
        lines = textwrap.wrap(text, width=30)
        step = int(min_size * 1.3)
        total_h = step * len(lines)

    sand_area_h = height - sand_top_y
    start_y = sand_top_y + int(sand_area_h * 0.30)

    _draw_jittered_text_groove(img, lines, font, start_y, step, width, rng)

    # A few displaced-sand piles and short stick-drag marks near the writing — small
    # authenticity details a flat text overlay would never have.
    rgba_draw = ImageDraw.Draw(img, "RGBA")
    pile_color_hi = (222, 194, 152, 210)
    pile_color_lo = (110, 82, 54, 160)
    text_bottom = start_y + total_h
    for _ in range(10):
        px = rng.uniform(width * 0.15, width * 0.85)
        py = rng.uniform(text_bottom + 6, height - 24)
        r = rng.uniform(4, 11)
        rgba_draw.ellipse((px - r, py - r + 3, px + r, py + r + 3), fill=pile_color_lo)
        rgba_draw.ellipse((px - r, py - r, px + r, py + r), fill=pile_color_hi)
    for _ in range(4):
        sx = rng.uniform(width * 0.1, width * 0.9)
        sy = rng.uniform(text_bottom + 10, height - 30)
        length = rng.uniform(30, 70)
        angle = rng.uniform(0, 3.14159)
        ex, ey = sx + length * 0.7, sy + length * 0.15
        rgba_draw.line([(sx, sy), (ex, ey)], fill=pile_color_lo, width=3)
        rgba_draw.line([(sx, sy - 2), (ex, ey - 2)], fill=pile_color_hi, width=2)


def generate_quote_image(text: str, style: str, out_path: str, seed: int | None = None, width: int = WIDTH, height: int = HEIGHT) -> None:
    if style == "beach_sunset":
        rng = random.Random(seed)
        font_path = find_font(HANDWRITING_FONT_CANDIDATES)
        img, horizon_y, sand_top_y = make_sunset_ocean_scene(width, height, seed=seed)
        draw_footprints(img, sand_top_y, height, width, rng)
        draw_sand_written_text(img, text, sand_top_y, height, width, font_path, rng)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, quality=92)
        return

    if style not in STYLES:
        raise ValueError(f"Unknown style '{style}', expected one of {list(STYLES) + ['beach_sunset']}")
    font_path = find_font()
    img = make_textured_background(style, seed=seed)
    draw_centered_text(img, text, STYLES[style]["text_color"], font_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)


FORMATS = {
    "portrait": (WIDTH, HEIGHT),       # unchanged default — existing wall/sand behavior
    "square": (1080, 1080),
    "horizontal": (1920, 1080),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Quote text to render")
    parser.add_argument("--style", choices=list(STYLES) + ["beach_sunset"], default="wall")
    parser.add_argument("--out", default="scripts/quote_output.jpg")
    parser.add_argument("--seed", type=int, default=None, help="Background texture seed (for reproducibility)")
    parser.add_argument(
        "--format", choices=list(FORMATS) + ["both"], default="portrait",
        help="'both' writes two files (square + horizontal), suffixing --out with _square/_horizontal",
    )
    args = parser.parse_args()

    if args.format == "both":
        for fmt_name in ("square", "horizontal"):
            w, h = FORMATS[fmt_name]
            stem, dot, ext = args.out.rpartition(".")
            out_path = f"{stem}_{fmt_name}.{ext}" if dot else f"{args.out}_{fmt_name}"
            generate_quote_image(args.text, args.style, out_path, seed=args.seed, width=w, height=h)
            print(f"Saved: {out_path}")
        return

    w, h = FORMATS[args.format]
    generate_quote_image(args.text, args.style, args.out, seed=args.seed, width=w, height=h)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
