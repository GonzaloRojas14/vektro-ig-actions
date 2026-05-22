"""
Data Viz template.
Renders a vertical bar chart using only Pillow (no matplotlib).
"""

from pathlib import Path
from PIL import Image, ImageDraw

from generator.utils import (
    W, H, BG, VIOLET, CYAN, WHITE, MUTED, CARD,
    load_font, text_width, line_height, wrap_text,
    draw_logo, draw_accent_line, draw_hashtags, save_image, load_background,
)

# Chart geometry (pixels)
_CHART_LEFT   = 120   # space for y-axis labels
_CHART_RIGHT  = W - 60
_CHART_TOP    = 460
_CHART_BOTTOM = 1480
_CHART_W      = _CHART_RIGHT - _CHART_LEFT
_CHART_H      = _CHART_BOTTOM - _CHART_TOP

_PAD = 70

# Alternating bar colors: violet / cyan
_BAR_COLORS = [VIOLET, CYAN, VIOLET, CYAN, VIOLET, CYAN]


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
        # Gridline
        draw.line([(_CHART_LEFT, y), (_CHART_RIGHT, y)], fill=(*MUTED, 40), width=1)
        # Y label
        label = f"{int(val)}%"
        lw = text_width(axis_font, label)
        draw.text((_CHART_LEFT - lw - 10, y - lh // 2), label, font=axis_font, fill=MUTED)


def render(entry: dict) -> Path:
    img = load_background() or Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Subtle background card for chart area ─────────────────────────────────
    draw.rectangle(
        [_CHART_LEFT - 20, _CHART_TOP - 20, _CHART_RIGHT + 20, _CHART_BOTTOM + 20],
        fill=CARD,
    )

    # ── Logo + accent ─────────────────────────────────────────────────────────
    draw_logo(draw, x=_PAD, y=68)
    draw_accent_line(draw, y=148)

    # ── Title ─────────────────────────────────────────────────────────────────
    title_font = load_font(66, "bold")
    title_lines = wrap_text(entry.get("text", ""), title_font, W - _PAD * 2)
    y = 190
    for line in title_lines:
        w = text_width(title_font, line)
        draw.text(((W - w) // 2, y), line, font=title_font, fill=WHITE)
        y += line_height(title_font, 10)

    # ── Subtitle ──────────────────────────────────────────────────────────────
    sub = entry.get("subtext", "")
    if sub:
        sf = load_font(40)
        sw = text_width(sf, sub)
        draw.text(((W - sw) // 2, y + 6), sub, font=sf, fill=MUTED)

    # ── Chart data ────────────────────────────────────────────────────────────
    data: list[dict] = entry.get("data", [])
    if not data:
        return save_image(img)

    max_val = max((d.get("value", 0) for d in data), default=100)
    # Round up to nearest 20 for clean grid
    max_val = max(20.0, (max_val // 20 + 1) * 20)

    # Axes
    draw.line([(_CHART_LEFT, _CHART_TOP - 10), (_CHART_LEFT, _CHART_BOTTOM)], fill=MUTED, width=2)
    draw.line([(_CHART_LEFT, _CHART_BOTTOM), (_CHART_RIGHT, _CHART_BOTTOM)], fill=MUTED, width=2)

    _draw_gridlines(draw, max_val)

    # Bars
    n = len(data)
    bar_area_w = _CHART_W
    gap_ratio = 0.4   # 40 % of slot is gap
    slot_w = bar_area_w / n
    bar_w = int(slot_w * (1 - gap_ratio))

    label_font  = load_font(36, "bold")
    value_font  = load_font(38, "bold")

    for i, item in enumerate(data):
        val   = item.get("value", 0)
        label = item.get("label", "")
        color = _BAR_COLORS[i % len(_BAR_COLORS)]

        bar_x = int(_CHART_LEFT + i * slot_w + (slot_w - bar_w) / 2)
        bar_y = _value_to_y(val, max_val)

        # Bar with rounded top
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_w, _CHART_BOTTOM],
            radius=6,
            fill=color,
        )

        # Glow: semi-transparent wider rect behind bar
        glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.rounded_rectangle(
            [bar_x - 4, bar_y, bar_x + bar_w + 4, _CHART_BOTTOM],
            radius=8,
            fill=(*color, 35),
        )
        img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
        draw = ImageDraw.Draw(img)
        # Redraw bar on top after compositing
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + bar_w, _CHART_BOTTOM],
            radius=6,
            fill=color,
        )

        # Value label above bar
        val_text = f"{int(val)}%"
        vw = text_width(value_font, val_text)
        draw.text((bar_x + (bar_w - vw) // 2, bar_y - 46), val_text, font=value_font, fill=color)

        # X label below axis
        lw = text_width(label_font, label)
        lx = bar_x + (bar_w - lw) // 2
        draw.text((lx, _CHART_BOTTOM + 16), label, font=label_font, fill=WHITE)

    # ── Source attribution ────────────────────────────────────────────────────
    src_font = load_font(32)
    src = f"Source: {entry.get('source', 'Vektro IT Research')}"
    draw.text((_CHART_LEFT, _CHART_BOTTOM + 80), src, font=src_font, fill=MUTED)

    # ── Bottom branding ───────────────────────────────────────────────────────
    draw_accent_line(draw, y=1772)
    tags = entry.get("hashtags", [])
    if tags:
        draw_hashtags(draw, tags, y=1800)

    return save_image(img)
