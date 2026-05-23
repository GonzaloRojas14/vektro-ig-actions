"""
Quote template.
Hero-split background (identical to all other templates) + glassmorphism
card behind the quote block so text is always legible over any photo.
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, GREEN, LIME, WHITE,
    T_XL, T_MD, S_LG, S_MD,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_text_card,
    save_image, load_background_hero,
)

_PAD = 80


def render(entry: dict) -> Path:
    img = load_background_hero()
    if img is None:
        img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Logo ─ below the Instagram safe zone (top 250 px) ──────────────────────
    draw_logo(draw, x=_PAD, y=275)
    draw_accent_line(draw, y=355)

    # ── Pre-compute quote layout so the glassmorphism card is drawn first ─────
    quote_text = entry.get("text", "")
    q_font2 = load_font(T_XL, "bold")
    q_lines = wrap_text("\u201c" + quote_text + "\u201d", q_font2, W - _PAD * 2)
    lh_q = line_height(q_font2, 28)
    total_h = len(q_lines) * lh_q
    # Centre quote in the lower safe zone (y 420-1670)
    y_quote = max(720, (420 + 1670 - total_h) // 2)

    author   = entry.get("subtext", "")
    a_font   = load_font(T_MD)
    author_h = line_height(a_font) if author else 0

    # Card bounds ─ quote block + divider + author + internal padding
    _CPAD       = 64
    card_top    = y_quote - _CPAD
    card_bottom = min(y_quote + total_h + S_LG + 4 + S_MD + author_h + _CPAD, 1670)
    card_x      = _PAD - 16
    card_w      = W - (_PAD - 16) * 2

    # ── Glassmorphism card ─────────────────────────────────────────
    img = draw_text_card(img, card_x, card_top, card_w, card_bottom - card_top,
                         radius=24, fill_alpha=210, border_alpha=65)
    draw = ImageDraw.Draw(img)

    # ── Decorative oversized open-quote mark (inside the card, very subtle) ──
    q_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    qd      = ImageDraw.Draw(q_layer)
    q_font  = load_font(320, "bold")
    qmark   = "\u201c"
    qw      = text_width(q_font, qmark)
    qd.text(((W - qw) // 2, card_top + 10), qmark, font=q_font, fill=(*GREEN, 28))
    img  = Image.alpha_composite(img.convert("RGBA"), q_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Quote text — T_XL (107 px) ───────────────────────────────────────
    y = y_quote
    for line in q_lines:
        w = text_width(q_font2, line)
        draw.text(((W - w) // 2, y), line, font=q_font2, fill=WHITE)
        y += lh_q

    y += S_LG

    # ── Divider ─────────────────────────────────────────────────────
    div_w = 200
    draw.rectangle([(W - div_w) // 2, y, (W + div_w) // 2, y + 4], fill=LIME)
    y += S_MD

    # ── Author — T_MD (60 px) ─────────────────────────────────────────
    if author:
        aw = text_width(a_font, author)
        draw.text(((W - aw) // 2, y), author, font=a_font, fill=LIME)

    return save_image(img)
