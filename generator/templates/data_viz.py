"""
Data Viz template.
Renders a vertical bar chart using only Pillow (no matplotlib).
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, GREEN, LIME, WHITE, MUTED,
    T_LG, T_SM, T_XS,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_text_card,
    save_image, load_background_hero,
)

# Chart geometry — _CHART_TOP is pushed well below the title/subtitle area
# so labels and bars never overlap with the text above the card.
_CHART_LEFT   = 120
_CHART_RIGHT  = W - 60
_CHART_TOP    = 860
_CHART_BOTTOM = 1580
_CHART_W      = _CHART_RIGHT - _CHART_LEFT
_CHART_H      = _CHART_BOTTOM - _CHART_TOP

_PAD = 70

_BAR_COLORS = [GREEN, LIME, GREEN, LIME, GREEN, LIME]


def _value_to_y(value: float, max_val: float) -> int:
    ratio = value / max_val if max_val else 0
    return int(_CHART_BOTTOM - ratio * _CHART_H)


def _draw_gridlines(draw: ImageDraw.ImageDraw, max_val: float, ticks: int = 5) -> None:
    axis_font = load_font(30)
    lh = line_height(axis_font, 0)
    for i in range(ticks + 1):
        ratio = i / ticks
        val = max_val * ratio
        y = int(_CHART_BOTTOM - ratio * _CHART_H)
        draw.line([(_CHART_LEFT, y), (_CHART_RIGHT, y)], fill=(*MUTED, 40), width=1)
        label = f"{int(val)}%"
        lw = text_width(axis_font, label)
        draw.text((_CHART_LEFT - lw - 10, y - lh // 2), label, font=axis_font, fill=MUTED)


def render(entry: dict) -> Path:
    img = load_background_hero() or Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Chart section card — full-width, rounded top, extends to canvas bottom ──
    # Goes edge-to-edge so there's no floating box with hard cutoffs on the photo.
    _card_top = _CHART_TOP - 64
    img = draw_text_card(img, 0, _card_top, W, H - _card_top,
                         radius=28, fill_alpha=230, border_alpha=0)
    draw = ImageDraw.Draw(img)
    # GREEN→LIME gradient accent at the top edge of the card
    draw_accent_line(draw, y=_card_top)

    # ── Logo — below the Instagram safe zone (top 250 px) ────────────────────
    draw_logo(draw, x=_PAD, y=275)
    draw_accent_line(draw, y=355)

    # ── Title — T_LG (80 px bold) ────────────────────────────────────────────
    title_font = load_font(T_LG, "bold")
    title_lines = wrap_text(entry.get("text", ""), title_font, W - _PAD * 2)
    y = 430
    for line in title_lines:
        w = text_width(title_font, line)
        draw.text(((W - w) // 2, y), line, font=title_font, fill=WHITE)
        y += line_height(title_font, 16)

    # ── Subtitle — T_SM (45 px) ───────────────────────────────────────────────
    sub = entry.get("subtext", "")
    if sub:
        sf = load_font(T_SM)
        sw = text_width(sf, sub)
        draw.text(((W - sw) // 2, y + 20), sub, font=sf, fill=MUTED)

    # ── Chart data ────────────────────────────────────────────────────────────
    data: list[dict] = entry.get("data", [])
    if not data:
        return save_image(img)

    max_val = max((d.get("value", 0) for d in data), default=100)
    max_val = max(20.0, (max_val // 20 + 1) * 20)

    draw.line([(_CHART_LEFT, _CHART_TOP - 10), (_CHART_LEFT, _CHART_BOTTOM)], fill=MUTED, width=2)
    draw.line([(_CHART_LEFT, _CHART_BOTTOM), (_CHART_RIGHT, _CHART_BOTTOM)], fill=MUTED, width=2)

    _draw_gridlines(draw, max_val)

    n = len(data)
    bar_area_w = _CHART_W
    gap_ratio = 0.4
    slot_w = bar_area_w / n
    bar_w = int(slot_w * (1 - gap_ratio))

    label_font = load_font(36, "bold")
    value_font = load_font(38, "bold")

    for i, item in enumerate(data):
        val   = item.get("value", 0)
        label = item.get("label", "")
        color = _BAR_COLORS[i % len(_BAR_COLORS)]

        bar_x = int(_CHART_LEFT + i * slot_w + (slot_w - bar_w) / 2)
        bar_y = _value_to_y(val, max_val)

        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_w, _CHART_BOTTOM],
            radius=6,
            fill=color,
        )

        glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.rounded_rectangle(
            [bar_x - 4, bar_y, bar_x + bar_w + 4, _CHART_BOTTOM],
            radius=8,
            fill=(*color, 35),
        )
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_w, _CHART_BOTTOM],
            radius=6,
            fill=color,
        )

        val_text = f"{int(val)}%"
        vw = text_width(value_font, val_text)
        draw.text((bar_x + (bar_w - vw) // 2, bar_y - 46), val_text, font=value_font, fill=color)

        lw = text_width(label_font, label)
        lx = bar_x + (bar_w - lw) // 2
        draw.text((lx, _CHART_BOTTOM + 16), label, font=label_font, fill=WHITE)

    # ── Source attribution ────────────────────────────────────────────────────
    src_font = load_font(T_XS)
    src = f"Source: {entry.get('source', 'Vektro IT Research')}"
    draw.text((_CHART_LEFT, _CHART_BOTTOM + 80), src, font=src_font, fill=MUTED)

    return save_image(img)
