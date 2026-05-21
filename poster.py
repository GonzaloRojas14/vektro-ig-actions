"""
Instagram Stories automation poster.
Reads stories/content.json, finds the story scheduled for the current hour,
generates a 1080x1920 image with Pillow, uploads to ImgBB, and publishes
via the Instagram Graph API.
"""

import json
import os
import sys
import time
import base64
import textwrap
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

CANVAS_W, CANVAS_H = 1080, 1920
GRAPH_API = "https://graph.facebook.com/v19.0"

# ── Config ────────────────────────────────────────────────────────────────────

def load_config(path: str = "stories/content.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("content.json must be a JSON array")
    return data


def find_story_for_now(stories: list[dict], now: datetime) -> dict | None:
    """Return the first story whose HH:MM hour matches the current UTC hour."""
    current_hour = now.strftime("%H")
    for story in stories:
        scheduled = story.get("time", "")
        if len(scheduled) >= 2 and scheduled[:2] == current_hour:
            return story
    return None


# ── Image generation ──────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return r, g, b


def luminance(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a clean sans-serif font; fall back to PIL default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "arial.ttf",
        "Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    log.warning("No TrueType font found, using PIL built-in (text quality reduced)")
    return ImageFont.load_default()


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
    canvas_w: int,
    canvas_h: int,
    padding: int = 80,
) -> None:
    """Draw text centered on the canvas with automatic word-wrap."""
    max_width = canvas_w - padding * 2
    # Wrap text to fit within max_width
    avg_char_w = font.getbbox("A")[2] if hasattr(font, "getbbox") else 10
    chars_per_line = max(1, max_width // max(avg_char_w, 1))
    lines = []
    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=chars_per_line) or [""]
        lines.extend(wrapped)

    # Measure total block height
    line_height = (
        font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 12
        if hasattr(font, "getbbox")
        else 20
    )
    total_h = line_height * len(lines)
    y = (canvas_h - total_h) // 2

    for line in lines:
        if hasattr(font, "getbbox"):
            bbox = font.getbbox(line)
            line_w = bbox[2] - bbox[0]
        else:
            line_w = len(line) * 8
        x = (canvas_w - line_w) // 2
        # Subtle drop shadow for legibility
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 80))
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height


def generate_image_solid(story: dict) -> Path:
    """Solid color background with centered text."""
    bg_hex = story.get("background_color", "#1a1a2e")
    text = story.get("text", "")
    rgb = hex_to_rgb(bg_hex)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color=rgb)
    draw = ImageDraw.Draw(img, "RGBA")

    if text:
        font = _load_font(72)
        # Pick text color based on background luminance
        text_color = (255, 255, 255) if luminance(*rgb) < 128 else (20, 20, 20)
        draw_wrapped_text(draw, text, font, text_color, CANVAS_W, CANVAS_H)

    out_path = Path("/tmp/ig_story_output.jpg")
    img.save(out_path, "JPEG", quality=95)
    log.info("Generated solid-color image → %s", out_path)
    return out_path


def generate_image_with_overlay(story: dict) -> Path:
    """Image file as background with a semi-transparent text overlay."""
    image_file = story["image_file"]
    text = story.get("text", "")

    img = Image.open(image_file).convert("RGB")
    img = img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)

    draw = ImageDraw.Draw(img, "RGBA")

    if text:
        # Dark gradient-like overlay across the center third for legibility
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        band_top = CANVAS_H // 3
        band_bot = CANVAS_H * 2 // 3
        ov_draw.rectangle([0, band_top, CANVAS_W, band_bot], fill=(0, 0, 0, 140))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(img)
        font = _load_font(72)
        draw_wrapped_text(draw, text, font, (255, 255, 255), CANVAS_W, CANVAS_H)

    out_path = Path("/tmp/ig_story_output.jpg")
    img.save(out_path, "JPEG", quality=95)
    log.info("Generated image-overlay story → %s", out_path)
    return out_path


def generate_image(story: dict) -> Path:
    if story.get("image_file"):
        return generate_image_with_overlay(story)
    return generate_image_solid(story)


# ── ImgBB upload ──────────────────────────────────────────────────────────────

def upload_to_imgbb(image_path: Path, api_key: str) -> str:
    """Upload image to ImgBB and return the public URL."""
    log.info("Uploading image to ImgBB…")
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": encoded},
        timeout=30,
    )

    if not resp.ok:
        raise RuntimeError(f"ImgBB upload failed [{resp.status_code}]: {resp.text}")

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"ImgBB returned failure: {data}")

    url = data["data"]["url"]
    log.info("Image uploaded: %s", url)
    return url


# ── Instagram Graph API ───────────────────────────────────────────────────────

def _check_token_error(resp: requests.Response) -> None:
    """Raise a clear error if the response indicates a token problem."""
    if resp.status_code in (400, 401, 403):
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        code = err.get("code", 0)
        msg = err.get("message", "")
        if code in (190, 102) or "token" in msg.lower() or "oauth" in msg.lower():
            log.error(
                "Instagram access token is invalid or expired. "
                "Regenerate the token at developers.facebook.com and update the "
                "ACCESS_TOKEN repository secret."
            )
            sys.exit(1)


def create_media_container(image_url: str, user_id: str, access_token: str) -> str:
    """Create a Stories media container and return the container ID."""
    log.info("Creating Instagram media container…")
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media",
        params={
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": access_token,
        },
        timeout=30,
    )
    _check_token_error(resp)

    if not resp.ok:
        raise RuntimeError(
            f"Failed to create media container [{resp.status_code}]: {resp.text}"
        )

    container_id = resp.json().get("id")
    if not container_id:
        raise RuntimeError(f"No container ID in response: {resp.text}")

    log.info("Media container created: %s", container_id)
    return container_id


def wait_for_container_ready(
    container_id: str, access_token: str, retries: int = 10, delay: int = 5
) -> None:
    """Poll until the media container status is FINISHED."""
    log.info("Waiting for container to be ready…")
    for attempt in range(1, retries + 1):
        resp = requests.get(
            f"{GRAPH_API}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=15,
        )
        _check_token_error(resp)
        if resp.ok:
            status = resp.json().get("status_code", "")
            log.info("Container status [%d/%d]: %s", attempt, retries, status)
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError("Media container processing failed with ERROR status")
        time.sleep(delay)
    raise RuntimeError("Media container did not reach FINISHED state in time")


def publish_story(container_id: str, user_id: str, access_token: str) -> str:
    """Publish the media container as a Story."""
    log.info("Publishing story…")
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    _check_token_error(resp)

    if not resp.ok:
        raise RuntimeError(f"Failed to publish story [{resp.status_code}]: {resp.text}")

    media_id = resp.json().get("id")
    log.info("Story published successfully! Media ID: %s", media_id)
    return media_id


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    access_token = os.environ.get("ACCESS_TOKEN", "").strip()
    user_id = os.environ.get("USER_ID", "").strip()
    imgbb_api_key = os.environ.get("IMGBB_API_KEY", "").strip()

    missing = [k for k, v in {
        "ACCESS_TOKEN": access_token,
        "USER_ID": user_id,
        "IMGBB_API_KEY": imgbb_api_key,
    }.items() if not v]

    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    stories = load_config()
    now = datetime.now(timezone.utc)
    log.info("Current UTC time: %s", now.strftime("%Y-%m-%d %H:%M"))

    story = find_story_for_now(stories, now)
    if story is None:
        log.info("No story scheduled for hour %s UTC — nothing to post.", now.strftime("%H:xx"))
        return

    log.info("Found scheduled story: time=%s text=%r", story.get("time"), story.get("text", "")[:60])

    image_path = generate_image(story)
    image_url = upload_to_imgbb(image_path, imgbb_api_key)
    container_id = create_media_container(image_url, user_id, access_token)
    wait_for_container_ready(container_id, access_token)
    publish_story(container_id, user_id, access_token)
    log.info("Done.")


if __name__ == "__main__":
    main()
