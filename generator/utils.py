"""Shared constants, font loading, and drawing primitives for all templates."""

import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# Brand palette — neon green + black
BG       = (5,   8,   5)     # #050805  near-black with green whisper
GREEN    = (57,  255, 20)    # #39FF14  neon green (primary)
LIME     = (0,   255, 140)   # #00FF8C  spring green (secondary accent)
WHITE    = (255, 255, 255)   # #FFFFFF
MUTED    = (120, 148, 120)   # #789478  grey-green for secondary text
CARD     = (12,  20,  12)    # #0C140C  dark green-tinted card bg


# ── Typographic scale — Perfect Fourth ratio (×1.333), base 34 px ─────────────
# Each step = previous × 1.333. Use these instead of arbitrary sizes.
T_XS  = 34   # hashtags, footnotes, labels pequeños
T_SM  = 45   # subtext, muted, source, tagline
T_MD  = 60   # body copy, author attribution, descriptions
T_LG  = 80   # subheadline, section title, primary title
T_XL  = 107  # hero headline, main quote text
T_2XL = 143  # oversized hero (usar con moderación)

# ── Spacing system — multiples of 8 px ───────────────────────────────────────
S_XS  = 16   # internal badge padding
S_SM  = 24   # internal card / code block padding
S_MD  = 40   # between sibling elements
S_LG  = 64   # between distinct sections
S_XL  = 80   # canvas lateral margin
S_2XL = 96   # between major layout zones

OUTPUT_PATH = Path("/tmp/ig_story_output.jpg")

BACKGROUNDS_DIR = Path(__file__).parent.parent / "backgrounds"


def _crop_photo(path: Path) -> Image.Image:
    """Load, cover-crop, and return a 1080×1920 RGBA photo."""
    src = Image.open(path).convert("RGB")
    src_ratio = src.width / src.height
    target_ratio = W / H
    if src_ratio > target_ratio:
        new_h, new_w = H, int(H * src_ratio)
    else:
        new_w, new_h = W, int(W / src_ratio)
    src = src.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - W) // 2, (new_h - H) // 2
    return src.crop((left, top, left + W, top + H)).convert("RGBA")


def _pick_photo() -> Path | None:
    """Return a random photo path from backgrounds/, or None."""
    if not BACKGROUNDS_DIR.is_dir():
        return None
    photos = [p for ext in ("*.jpg", "*.jpeg", "*.png") for p in BACKGROUNDS_DIR.glob(ext)]
    return random.choice(photos) if photos else None


def load_background(scrim_top_h: int = 420, scrim_bot_h: int = 460,
                    mid_alpha: int = 90) -> Image.Image | None:
    """Full-bleed photo with top + bottom scrims and a uniform mid-tone overlay.

    Good for: quote template where the photo fills the entire canvas.
    Returns None if no photos exist so templates can fall back.
    """
    photo = _pick_photo()
    if photo is None:
        return None
    img = _crop_photo(photo)

    mid = Image.new("RGBA", (W, H), (0, 0, 0, mid_alpha))
    img = Image.alpha_composite(img, mid)

    top_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(top_layer)
    for i in range(scrim_top_h):
        a = int(215 * (1.0 - i / scrim_top_h) ** 0.65)
        td.line([(0, i), (W, i)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, top_layer)

    bot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bot_layer)
    for i in range(scrim_bot_h):
        a = int(235 * (i / scrim_bot_h) ** 0.65)
        y = H - scrim_bot_h + i
        bd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, bot_layer)

    return img.convert("RGB")


def load_background_hero(split_y: int = 1150, fade_h: int = 420,
                         top_mid_alpha: int = 55,
                         top_scrim_h: int = 440) -> Image.Image | None:
    """Hero-split background: vivid photo at top, fades to near-solid dark below.

    Ideal for content-heavy templates (tech_tip, service_promo, data_viz):
    - The photo acts as a dramatic header/hero image.
    - Below split_y the canvas fades to solid dark so ALL text is readable.
    Returns None if no photos exist so templates can fall back.
    """
    photo = _pick_photo()
    if photo is None:
        return None
    img = _crop_photo(photo)

    # Mild overall overlay so the hero photo pops but isn't too harsh
    mid = Image.new("RGBA", (W, H), (0, 0, 0, top_mid_alpha))
    img = Image.alpha_composite(img, mid)

    # Top scrim — keeps logo area readable
    top_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(top_layer)
    for i in range(top_scrim_h):
        a = int(200 * (1.0 - i / top_scrim_h) ** 0.70)
        td.line([(0, i), (W, i)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, top_layer)

    # Fade to dark starting at split_y
    fade_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade_layer)
    for i in range(fade_h):
        a = int(248 * (i / fade_h) ** 0.55)
        y = split_y + i
        if y < H:
            fd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, fade_layer)

    # Solid near-black below the fade zone
    solid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(solid_layer)
    solid_bottom = split_y + fade_h
    if solid_bottom < H:
        sd.rectangle([0, solid_bottom, W, H], fill=(*BG, 248))
    img = Image.alpha_composite(img, solid_layer)

    return img.convert("RGB")


def draw_text_card(img: Image.Image,
                   x: int, y: int, w: int, h: int,
                   radius: int = 20,
                   fill_alpha: int = 210,
                   border_alpha: int = 55) -> Image.Image:
    """Glassmorphism-style dark card guaranteeing text legibility on any background.

    Composites a rounded rect with a dark semi-transparent fill and a subtle
    GREEN border onto `img`. Returns the updated RGB image.
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x, y, x + w, y + h],
                        radius=radius,
                        fill=(*BG, fill_alpha))
    d.rounded_rectangle([x, y, x + w, y + h],
                        radius=radius,
                        outline=(*GREEN, border_alpha),
                        width=1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

# ── Font loading ──────────────────────────────────────────────────────────────

_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "arialbd.ttf",
]
_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "arial.ttf",
]
_MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/System/Library/Fonts/Courier.ttc",
    "cour.ttf",
]


def load_font(size: int, style: str = "regular") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = {
        "bold": _BOLD_CANDIDATES,
        "mono": _MONO_CANDIDATES,
    }.get(style, _REGULAR_CANDIDATES)

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


# ── Text helpers ──────────────────────────────────────────────────────────────

def text_width(font, text: str) -> int:
    if hasattr(font, "getlength"):
        return int(font.getlength(text))
    if hasattr(font, "getbbox"):
        bb = font.getbbox(text)
        return bb[2] - bb[0]
    return len(text) * 10


def line_height(font, spacing: int = 10) -> int:
    if hasattr(font, "getbbox"):
        bb = font.getbbox("Ay")
        return bb[3] - bb[1] + spacing
    return 20 + spacing


def wrap_text(text: str, font, max_width: int) -> list[str]:
    """Word-wrap text respecting explicit \\n breaks."""
    result: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            result.append("")
            continue
        words = paragraph.split()
        line_words: list[str] = []
        for word in words:
            candidate = " ".join(line_words + [word])
            if text_width(font, candidate) <= max_width:
                line_words.append(word)
            else:
                if line_words:
                    result.append(" ".join(line_words))
                line_words = [word]
        if line_words:
            result.append(" ".join(line_words))
    return result or [""]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font,
    fill: tuple,
    y_start: int,
    lh: int | None = None,
) -> int:
    """Draw lines centered horizontally. Returns y after last line."""
    lh = lh or line_height(font)
    y = y_start
    for line in lines:
        w = text_width(font, line)
        x = (W - w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


# ── Brand primitives ──────────────────────────────────────────────────────────

def draw_logo(draw: ImageDraw.ImageDraw, x: int = 60, y: int = 65) -> None:
    """Render 'VEKTRO IT' wordmark with GREEN/LIME accent bars."""
    font_bold = load_font(38, "bold")
    font_reg  = load_font(38, "regular")
    # Two thin vertical bars (brand mark)
    draw.rectangle([x,     y + 4, x + 7,  y + 40], fill=GREEN)
    draw.rectangle([x + 13, y + 4, x + 17, y + 40], fill=LIME)
    tx = x + 30
    draw.text((tx, y), "VEKTRO", font=font_bold, fill=WHITE)
    vw = text_width(font_bold, "VEKTRO")
    draw.text((tx + vw + 8, y), "IT", font=font_reg, fill=GREEN)


def draw_accent_line(draw: ImageDraw.ImageDraw, y: int, alpha: int = 255) -> None:
    """Full-width gradient line from GREEN → LIME."""
    for i in range(W):
        t = i / W
        r = int(GREEN[0] + (LIME[0] - GREEN[0]) * t)
        g = int(GREEN[1] + (LIME[1] - GREEN[1]) * t)
        b = int(GREEN[2] + (LIME[2] - GREEN[2]) * t)
        draw.line([(i, y), (i, y + 3)], fill=(r, g, b))


def draw_hashtags(
    draw: ImageDraw.ImageDraw, tags: list[str], y: int, size: int = 34
) -> None:
    """Centered hashtag row in muted color."""
    font = load_font(size)
    text = "  ".join(f"#{t}" for t in tags)
    x = (W - text_width(font, text)) // 2
    draw.text((x, y), text, font=font, fill=MUTED)


def draw_badge(
    draw: ImageDraw.ImageDraw,
    label: str,
    x: int,
    y: int,
    bg: tuple = GREEN,
    fg: tuple = WHITE,
    pad_x: int = 24,
    pad_y: int = 10,
    font_size: int = 30,
) -> tuple[int, int]:
    """Filled rounded-rect badge. Returns (width, height)."""
    font = load_font(font_size, "bold")
    tw = text_width(font, label)
    bw = tw + pad_x * 2
    bh = line_height(font, 0) + pad_y * 2
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=8, fill=bg)
    draw.text((x + pad_x, y + pad_y), label, font=font, fill=fg)
    return bw, bh


def save_image(img: Image.Image) -> Path:
    img.save(OUTPUT_PATH, "JPEG", quality=95)
    return OUTPUT_PATH
