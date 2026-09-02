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


def find_font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    raise FileNotFoundError(
        f"None of the candidate fonts were found on this machine: {FONT_CANDIDATES}"
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


def generate_quote_image(text: str, style: str, out_path: str, seed: int | None = None) -> None:
    if style not in STYLES:
        raise ValueError(f"Unknown style '{style}', expected one of {list(STYLES)}")
    font_path = find_font()
    img = make_textured_background(style, seed=seed)
    draw_centered_text(img, text, STYLES[style]["text_color"], font_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Quote text to render")
    parser.add_argument("--style", choices=list(STYLES), default="wall")
    parser.add_argument("--out", default="scripts/quote_output.jpg")
    parser.add_argument("--seed", type=int, default=None, help="Background texture seed (for reproducibility)")
    args = parser.parse_args()

    generate_quote_image(args.text, args.style, args.out, seed=args.seed)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
