"""
Service Promo template.
Tech grid background drawn with Pillow. Showcases Vektro IT services with a CTA.
"""

import random
from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, VIOLET, CYAN, WHITE, MUTED, CARD,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_hashtags, draw_badge,
    draw_centered_text, save_image,
)

_PAD = 70

_SERVICES = [
    ("Azure Cloud",           "Infrastructure & migrations"),
    ("PySpark & Big Data",    "Distributed data pipelines"),
    ("SQL & Data Engineering","Warehouses, ETL, analytics"),
    ("Software Development",  "APIs, backends, automation"),
    ("Cloud Architecture",    "Design, costs & scalability"),
]


def _draw_grid(img: Image.Image) -> Image.Image:
    """Dot grid + circuit-style connecting lines, deterministic."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    step = 72
    # Dots
    for gy in range(0, H + step, step):
        for gx in range(0, W + step, step):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(*VIOLET, 22))

    # Horizontal/vertical segments between adjacent dots
    rng = random.Random(42)
    for _ in range(90):
        gx = rng.randrange(0, W // step) * step
        gy = rng.randrange(0, H // step) * step
        if rng.random() > 0.5:
            x2 = gx + rng.choice([step, step * 2])
            d.line([(gx, gy), (x2, gy)], fill=(*CYAN, 12), width=1)
        else:
            y2 = gy + rng.choice([step, step * 2])
            d.line([(gx, gy), (gx, y2)], fill=(*VIOLET, 12), width=1)

    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def render(entry: dict) -> Path:
    img = Image.new("RGB", (W, H), BG)
    img = _draw_grid(img)
    draw = ImageDraw.Draw(img)

    # ── Logo ──────────────────────────────────────────────────────────────────
    draw_logo(draw, x=_PAD, y=68)
    draw_accent_line(draw, y=148)

    # ── Headline ──────────────────────────────────────────────────────────────
    h1_font = load_font(96, "bold")
    headline = entry.get("text", "WE BUILD WHAT YOU SCALE")
    h1_lines = wrap_text(headline, h1_font, W - _PAD * 2)
    lh1 = line_height(h1_font, 10)
    y = 220
    for line in h1_lines:
        draw.text((_PAD, y), line, font=h1_font, fill=WHITE)
        y += lh1

    # ── Subheading ────────────────────────────────────────────────────────────
    sub = entry.get("subtext", "")
    if sub:
        sf = load_font(44)
        sl = wrap_text(sub, sf, W - _PAD * 2)
        y += 14
        for line in sl:
            draw.text((_PAD, y), line, font=sf, fill=MUTED)
            y += line_height(sf, 6)

    # ── Services card ─────────────────────────────────────────────────────────
    card_x = _PAD
    card_y = y + 50
    card_w = W - _PAD * 2
    item_h = 112
    card_h = len(_SERVICES) * item_h + 24

    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + card_h],
        radius=16,
        fill=CARD,
    )
    # Cyan top border
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_w, card_y + 4],
        radius=2,
        fill=CYAN,
    )

    name_font = load_font(40, "bold")
    desc_font = load_font(34)
    iy = card_y + 16
    for i, (name, desc) in enumerate(_SERVICES):
        # Violet bullet dot
        dot_x = card_x + 28
        dot_cy = iy + item_h // 2 - 8
        draw.ellipse([dot_x, dot_cy, dot_x + 16, dot_cy + 16], fill=VIOLET)
        tx = dot_x + 32
        draw.text((tx, iy + 10), name, font=name_font, fill=WHITE)
        draw.text((tx, iy + 10 + line_height(name_font, 2)), desc, font=desc_font, fill=MUTED)
        iy += item_h
        # Divider between items
        if i < len(_SERVICES) - 1:
            draw.line(
                [(card_x + 20, iy), (card_x + card_w - 20, iy)],
                fill=(*VIOLET, 40),
                width=1,
            )

    y = card_y + card_h

    # ── CTA box ───────────────────────────────────────────────────────────────
    cta_y = y + 48
    cta_h = 100
    draw.rounded_rectangle(
        [_PAD, cta_y, W - _PAD, cta_y + cta_h],
        radius=12,
        outline=CYAN,
        width=2,
    )
    cta_font = load_font(42, "bold")
    cta_text = "vektro.it  ·  Let's build together"
    cta_w = text_width(cta_font, cta_text)
    draw.text(((W - cta_w) // 2, cta_y + 26), cta_text, font=cta_font, fill=CYAN)

    y = cta_y + cta_h

    # ── Hashtags ──────────────────────────────────────────────────────────────
    draw_accent_line(draw, y=1772)
    tags = entry.get("hashtags", [])
    if tags:
        draw_hashtags(draw, tags, y=1800)

    return save_image(img)
