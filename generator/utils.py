"""Shared constants, font loading, and drawing primitives for all templates."""

import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

# Brand palette
BG       = (10,  10,  15)    # #0A0A0F
VIOLET   = (108, 99,  255)   # #6C63FF
CYAN     = (0,   212, 255)   # #00D4FF
WHITE    = (255, 255, 255)   # #FFFFFF
MUTED    = (139, 139, 158)   # #8B8B9E
CARD     = (18,  18,  28)    # code/card box background

OUTPUT_PATH = Path("/tmp/ig_story_output.jpg")

BACKGROUNDS_DIR = Path(__file__).parent.parent / "backgrounds"


def load_background(overlay_alpha: int = 155) -> Image.Image | None:
    """Return a randomly chosen photo from backgrounds/, resized to story dimensions with a
    dark overlay applied. Returns None if the folder is empty, so templates can fall back
    to their programmatic backgrounds."""
    if not BACKGROUNDS_DIR.is_dir():
        return None
    photos = [
        p for ext in ("*.jpg", "*.jpeg", "*.png")
        for p in BACKGROUNDS_DIR.glob(ext)
    ]
    if not photos:
        return None
    src = Image.open(random.choice(photos)).convert("RGB")
    # Cover-crop to 1080×1920
    src_ratio = src.width / src.height
    target_ratio = W / H
    if src_ratio > target_ratio:
        new_h, new_w = H, int(H * src_ratio)
    else:
        new_w, new_h = W, int(W / src_ratio)
    src = src.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - W) // 2, (new_h - H) // 2
    src = src.crop((left, top, left + W, top + H))
    # Dark overlay so text stays readable
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, overlay_alpha))
    return Image.alpha_composite(src.convert("RGBA"), overlay).convert("RGB")

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
    """Render 'VEKTRO IT' wordmark with violet/cyan accent bars."""
    font_bold = load_font(38, "bold")
    font_reg  = load_font(38, "regular")
    # Two thin vertical bars (brand mark)
    draw.rectangle([x,     y + 4, x + 7,  y + 40], fill=VIOLET)
    draw.rectangle([x + 13, y + 4, x + 17, y + 40], fill=CYAN)
    tx = x + 30
    draw.text((tx, y), "VEKTRO", font=font_bold, fill=WHITE)
    vw = text_width(font_bold, "VEKTRO")
    draw.text((tx + vw + 8, y), "IT", font=font_reg, fill=VIOLET)


def draw_accent_line(draw: ImageDraw.ImageDraw, y: int, alpha: int = 255) -> None:
    """Full-width gradient line from violet → cyan."""
    for i in range(W):
        t = i / W
        r = int(VIOLET[0] + (CYAN[0] - VIOLET[0]) * t)
        g = int(VIOLET[1] + (CYAN[1] - VIOLET[1]) * t)
        b = int(VIOLET[2] + (CYAN[2] - VIOLET[2]) * t)
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
    bg: tuple = VIOLET,
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
