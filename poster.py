"""
Vektro IT — Instagram Stories poster.

Reads stories/content.json, finds the entry scheduled for the current
day + hour (UTC), generates the image via the generator package, uploads
to ImgBB, and publishes as an Instagram Story via the Graph API.

Usage:
  python poster.py           # normal scheduled run
  python poster.py --force   # post the first entry regardless of schedule
"""

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from generator import render as generator_render

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v19.0"
CONTENT_PATH = "stories/content.json"

_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# ── Config ────────────────────────────────────────────────────────────────────

def load_content() -> list[dict]:
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("content.json must be a JSON array")
    return data


def find_story(stories: list[dict], now: datetime) -> dict | None:
    """Match by current UTC weekday name and hour (±30 min window)."""
    current_day  = _DAYS[now.weekday()]
    current_hour = now.hour
    current_min  = now.minute

    for story in stories:
        day = story.get("day", "").lower()
        if day != current_day:
            continue
        t = story.get("time", "00:00")
        try:
            sh, sm = int(t[:2]), int(t[3:5])
        except (ValueError, IndexError):
            log.warning("Invalid time format '%s' in content.json — skipping", t)
            continue
        # How many minutes from now to the scheduled time
        delta = abs((current_hour * 60 + current_min) - (sh * 60 + sm))
        if delta <= 30:
            return story

    return None


# ── ImgBB ─────────────────────────────────────────────────────────────────────

def upload_to_imgbb(image_path: Path, api_key: str) -> str:
    log.info("Uploading image to ImgBB…")
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": encoded},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"ImgBB upload failed [{resp.status_code}]: {resp.text}")

    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"ImgBB returned failure: {body}")

    url = body["data"]["url"]
    log.info("Uploaded: %s", url)
    return url


# ── Instagram Graph API ───────────────────────────────────────────────────────

def _guard_token_error(resp: requests.Response) -> None:
    if resp.status_code in (400, 401, 403):
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        code = err.get("code", 0)
        msg  = err.get("message", "")
        if code in (190, 102) or "token" in msg.lower() or "oauth" in msg.lower():
            log.error(
                "Instagram access token is INVALID or EXPIRED.\n"
                "  → Regenerate it at https://developers.facebook.com/tools/explorer/\n"
                "  → Then update the ACCESS_TOKEN secret in your GitHub repository."
            )
            sys.exit(1)


def create_container(image_url: str, user_id: str, token: str) -> str:
    log.info("Creating Instagram media container…")
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media",
        params={"image_url": image_url, "media_type": "STORIES", "access_token": token},
        timeout=30,
    )
    _guard_token_error(resp)
    if not resp.ok:
        raise RuntimeError(f"Create container failed [{resp.status_code}]: {resp.text}")
    cid = resp.json().get("id")
    if not cid:
        raise RuntimeError(f"No container ID in response: {resp.text}")
    log.info("Container ID: %s", cid)
    return cid


def wait_ready(cid: str, token: str, retries: int = 12, delay: int = 5) -> None:
    log.info("Waiting for container to be ready…")
    for attempt in range(1, retries + 1):
        resp = requests.get(
            f"{GRAPH_API}/{cid}",
            params={"fields": "status_code", "access_token": token},
            timeout=15,
        )
        _guard_token_error(resp)
        if resp.ok:
            status = resp.json().get("status_code", "")
            log.info("[%d/%d] status: %s", attempt, retries, status)
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError("Media container processing returned ERROR")
        time.sleep(delay)
    raise RuntimeError("Container did not reach FINISHED in time")


def publish(cid: str, user_id: str, token: str) -> str:
    log.info("Publishing story…")
    resp = requests.post(
        f"{GRAPH_API}/{user_id}/media_publish",
        params={"creation_id": cid, "access_token": token},
        timeout=30,
    )
    _guard_token_error(resp)
    if not resp.ok:
        raise RuntimeError(f"Publish failed [{resp.status_code}]: {resp.text}")
    mid = resp.json().get("id")
    log.info("Published! Media ID: %s", mid)
    return mid


# ── Main ──────────────────────────────────────────────────────────────────────

def _parse_args() -> tuple[bool, str, str]:
    """Return (force, target_day, target_time) from sys.argv."""
    force = "--force" in sys.argv
    day, time_ = "", ""
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--day"  and i + 1 < len(args):
            day   = args[i + 1].lower()
        if arg == "--time" and i + 1 < len(args):
            time_ = args[i + 1]
    return force, day, time_


def main() -> None:
    force, target_day, target_time = _parse_args()

    token     = os.environ.get("ACCESS_TOKEN",  "").strip()
    user_id   = os.environ.get("USER_ID",       "").strip()
    imgbb_key = os.environ.get("IMGBB_API_KEY", "").strip()

    missing = [k for k, v in {
        "ACCESS_TOKEN":  token,
        "USER_ID":       user_id,
        "IMGBB_API_KEY": imgbb_key,
    }.items() if not v]
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    stories = load_content()
    now = datetime.now(timezone.utc)
    log.info("UTC time: %s (%s)", now.strftime("%Y-%m-%d %H:%M"), _DAYS[now.weekday()])

    if force:
        story = stories[0]
        log.info("--force: posting first entry (day=%s time=%s type=%s)",
                 story.get("day"), story.get("time"), story.get("type"))
    elif target_day and target_time:
        # Workflow passes exact day+time so clock drift doesn't matter
        story = next(
            (s for s in stories
             if s.get("day", "").lower() == target_day
             and s.get("time", "")[:5] == target_time[:5]),
            None,
        )
        if story is None:
            log.error("No entry found for day=%s time=%s in content.json", target_day, target_time)
            sys.exit(1)
        log.info("Pinned story: day=%s time=%s type=%s",
                 story.get("day"), story.get("time"), story.get("type"))
    else:
        story = find_story(stories, now)
        if story is None:
            log.info("No story scheduled for %s %s UTC — nothing to post.",
                     _DAYS[now.weekday()], now.strftime("%H:%M"))
            return
        log.info("Matched story: day=%s time=%s type=%s",
                 story.get("day"), story.get("time"), story.get("type"))

    image_path  = generator_render.render(story)
    image_url   = upload_to_imgbb(image_path, imgbb_key)
    cid         = create_container(image_url, user_id, token)
    wait_ready(cid, token)
    publish(cid, user_id, token)
    log.info("Done.")


if __name__ == "__main__":
    main()
