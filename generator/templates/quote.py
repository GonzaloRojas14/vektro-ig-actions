"""
Quote template.
Dark gradient background, large decorative quotation mark, centered quote + attribution.
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, VIOLET, CYAN, WHITE, MUTED,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_hashtags,
    draw_centered_text, save_image, load_background,
)

_PAD = 80
_GRAD_TOP = (10,  10,  15)   # #0A0A0F
_GRAD_BOT = (21,  15,  48)   # deep violet-dark


def _draw_gradient(draw: ImageDraw.ImageDraw) -> None:
    for y in range(H):
        t = y / H
        r = int(_GRAD_TOP[0] + (_GRAD_BOT[0] - _GRAD_TOP[0]) * t)
        g = int(_GRAD_TOP[1] + (_GRAD_BOT[1] - _GRAD_TOP[1]) * t)
        b = int(_GRAD_TOP[2] + (_GRAD_BOT[2] - _GRAD_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def render(entry: dict) -> Path:
    img = load_background()
    if img is None:
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        _draw_gradient(draw)
    draw = ImageDraw.Draw(img)

    # ── Logo ──────────────────────────────────────────────────────────────────
    draw_logo(draw, x=_PAD, y=68)
    draw_accent_line(draw, y=148)

    # ── Giant decorative open-quote ───────────────────────────────────────────
    q_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    qd = ImageDraw.Draw(q_layer)
    q_font = load_font(340, "bold")
    qmark = "“"  # "
    qw = text_width(q_font, qmark)
    qd.text(((W - qw) // 2, 240), qmark, font=q_font, fill=(*VIOLET, 35))
    img = Image.alpha_composite(img.convert("RGBA"), q_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Quote text ────────────────────────────────────────────────────────────
    quote_text = entry.get("text", "")
    q_font2 = load_font(68, "bold")
    q_lines = wrap_text(f"“{quote_text}”", q_font2, W - _PAD * 2)
    lh_q = line_height(q_font2, 16)
    total_h = len(q_lines) * lh_q
    y = max(580, (H - total_h) // 2 - 80)
    for line in q_lines:
        w = text_width(q_font2, line)
        draw.text(((W - w) // 2, y), line, font=q_font2, fill=WHITE)
        y += lh_q

    y += 50

    # ── Divider ───────────────────────────────────────────────────────────────
    div_w = 160
    draw.rectangle([(W - div_w) // 2, y, (W + div_w) // 2, y + 3], fill=CYAN)
    y += 36

    # ── Author ────────────────────────────────────────────────────────────────
    author = entry.get("subtext", "")
    if author:
        a_font = load_font(52)
        aw = text_width(a_font, author)
        draw.text(((W - aw) // 2, y), author, font=a_font, fill=CYAN)
        y += line_height(a_font, 8)

    # ── Bottom: Vektro IT tagline ─────────────────────────────────────────────
    draw_accent_line(draw, y=1772)
    tag_font = load_font(36)
    tag = "vektro.it  ·  Technology & Data Consulting"
    tw = text_width(tag_font, tag)
    draw.text(((W - tw) // 2, 1800), tag, font=tag_font, fill=MUTED)

    tags = entry.get("hashtags", [])
    if tags:
        draw_hashtags(draw, tags, y=1856, size=30)

    return save_image(img)
