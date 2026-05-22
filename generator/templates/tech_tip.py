"""
Tech Tip template.
Layout: logo → accent line → TECH TIP badge → title → code block → subtext → hashtags.
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, VIOLET, CYAN, WHITE, MUTED, CARD,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_hashtags, draw_badge,
    draw_centered_text, save_image,
)

_PAD = 70          # horizontal padding
_CODE_PAD_X = 36   # inside code block
_CODE_PAD_Y = 28
_MAX_CODE_LINES = 10


def render(entry: dict) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Decorative corner dots ────────────────────────────────────────────────
    dot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot_layer)
    for gx in range(0, W, 80):
        for gy in range(0, H, 80):
            dd.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(*VIOLET, 18))
    img = Image.alpha_composite(img.convert("RGBA"), dot_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Logo ──────────────────────────────────────────────────────────────────
    draw_logo(draw, x=_PAD, y=68)

    # ── Accent line ───────────────────────────────────────────────────────────
    draw_accent_line(draw, y=148)

    # ── TECH TIP badge ────────────────────────────────────────────────────────
    bw, bh = draw_badge(draw, "TECH TIP", x=_PAD, y=192, bg=CYAN, fg=BG, font_size=28)

    # ── Title ─────────────────────────────────────────────────────────────────
    title_font = load_font(72, "bold")
    title_lines = wrap_text(entry.get("text", ""), title_font, W - _PAD * 2)
    lh_title = line_height(title_font, 14)
    y = 192 + bh + 42
    for line in title_lines:
        draw.text((_PAD, y), line, font=title_font, fill=WHITE)
        y += lh_title

    # ── Code block ───────────────────────────────────────────────────────────
    code = entry.get("code", "").strip()
    if code:
        code_font = load_font(36, "mono")
        lh_code = line_height(code_font, 8)
        raw_lines = code.split("\n")[:_MAX_CODE_LINES]

        box_w = W - _PAD * 2
        box_h = len(raw_lines) * lh_code + _CODE_PAD_Y * 2
        box_x = _PAD
        box_y = y + 36

        # Card background
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=CARD)
        # Violet left accent bar
        draw.rectangle([box_x, box_y, box_x + 6, box_y + box_h], fill=VIOLET)
        # Cyan top line
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + 3], fill=CYAN)

        cy = box_y + _CODE_PAD_Y
        for line in raw_lines:
            # Keyword coloring: lines starting with # in muted
            color = MUTED if line.lstrip().startswith("#") else WHITE
            draw.text((box_x + _CODE_PAD_X, cy), line, font=code_font, fill=color)
            cy += lh_code

        y = box_y + box_h

    # ── Subtext ───────────────────────────────────────────────────────────────
    subtext = entry.get("subtext", "")
    if subtext:
        sub_font = load_font(42)
        sub_lines = wrap_text(subtext, sub_font, W - _PAD * 2)
        y += 44
        for line in sub_lines:
            draw.text((_PAD, y), line, font=sub_font, fill=MUTED)
            y += line_height(sub_font, 8)

    # ── Bottom accent + hashtags ──────────────────────────────────────────────
    draw_accent_line(draw, y=1772)
    tags = entry.get("hashtags", [])
    if tags:
        draw_hashtags(draw, tags, y=1800)

    return save_image(img)
