"""
Tech Tip template.
Layout: logo → accent line → TECH TIP badge → title → code block → subtext.
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, GREEN, LIME, WHITE, MUTED, CARD,
    T_LG, T_SM,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_badge,
    save_image, load_background_hero,
)

_PAD = 70
_CODE_PAD_X = 36
_CODE_PAD_Y = 28
_MAX_CODE_LINES = 10


def render(entry: dict) -> Path:
    img = load_background_hero()
    if img is None:
        img = Image.new("RGB", (W, H), BG)
        dot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dot_layer)
        for gx in range(0, W, 80):
            for gy in range(0, H, 80):
                dd.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(*GREEN, 18))
        img = Image.alpha_composite(img.convert("RGBA"), dot_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Logo — below the Instagram safe zone (top 250 px) ────────────────────
    draw_logo(draw, x=_PAD, y=275)
    draw_accent_line(draw, y=355)

    # ── TECH TIP badge ────────────────────────────────────────────────────────
    bw, bh = draw_badge(draw, "TECH TIP", x=_PAD, y=455, bg=LIME, fg=BG, font_size=28)

    # ── Title — T_LG (80 px bold) ────────────────────────────────────────────
    title_font = load_font(T_LG, "bold")
    title_lines = wrap_text(entry.get("text", ""), title_font, W - _PAD * 2)
    lh_title = line_height(title_font, 24)
    y = 455 + bh + 72
    for line in title_lines:
        draw.text((_PAD, y), line, font=title_font, fill=WHITE)
        y += lh_title

    # ── Code block ────────────────────────────────────────────────────────────
    code = entry.get("code", "").strip()
    if code:
        code_font = load_font(38, "mono")          # slightly bigger mono font
        lh_code = line_height(code_font, 14)
        raw_lines = code.split("\n")[:_MAX_CODE_LINES]

        box_w = W - _PAD * 2
        box_h = len(raw_lines) * lh_code + _CODE_PAD_Y * 2 + 16
        box_x = _PAD
        box_y = y + 80

        draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=CARD)
        draw.rectangle([box_x, box_y, box_x + 6, box_y + box_h], fill=GREEN)
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + 3], fill=LIME)

        cy = box_y + _CODE_PAD_Y + 8
        for line in raw_lines:
            color = MUTED if line.lstrip().startswith("#") else WHITE
            draw.text((box_x + _CODE_PAD_X, cy), line, font=code_font, fill=color)
            cy += lh_code

        y = box_y + box_h

    # ── Subtext — T_SM (45 px), muted ────────────────────────────────────────
    subtext = entry.get("subtext", "")
    if subtext:
        sub_font = load_font(T_SM)
        sub_lines = wrap_text(subtext, sub_font, W - _PAD * 2)
        y += 96
        for line in sub_lines:
            draw.text((_PAD, y), line, font=sub_font, fill=MUTED)
            y += line_height(sub_font, 16)

    return save_image(img)
