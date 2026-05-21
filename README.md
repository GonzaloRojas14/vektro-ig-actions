# Vekrto IG Actions — Instagram Stories Automation

Automatically posts Instagram Stories on a schedule using the Instagram Graph API, ImgBB for hosting, and GitHub Actions as the cron runner.

---

## How it works

1. GitHub Actions triggers `poster.py` on the cron schedule defined in the workflow.
2. `poster.py` reads `stories/content.json` and finds the entry whose `time` matches the current UTC hour.
3. It generates a 1080×1920 JPEG with Pillow (solid color or image + text overlay).
4. The image is uploaded to ImgBB to get a public URL.
5. The URL is passed to the Instagram Graph API to create a Stories media container, which is then published.

---

## Setup

### 1. Prerequisites

- An Instagram **Professional account** (Creator or Business) connected to a Facebook Page.
- A **Facebook App** with `instagram_basic`, `instagram_content_publish`, and `pages_read_engagement` permissions approved.
- A **long-lived access token** (60-day expiry). Generate one at [developers.facebook.com](https://developers.facebook.com/tools/explorer/).
- A free [ImgBB](https://imgbb.com) account and API key (Settings → API).

### 2. Add GitHub repository secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name    | Value                                          |
|----------------|------------------------------------------------|
| `ACCESS_TOKEN` | Your Instagram long-lived access token         |
| `USER_ID`      | Your Instagram user ID (numeric, e.g. `17841…`)|
| `IMGBB_API_KEY`| Your ImgBB API key                             |

### 3. Enable GitHub Actions

Make sure Actions are enabled for the repo (**Settings → Actions → Allow all actions**).

---

## Scheduling

The workflow (`post_story.yml`) fires at the exact UTC hours listed in its `cron` entries. Those entries mirror the `time` values in `content.json`.

**If you add or change posting times**, update both files:

- `stories/content.json` — the `"time": "HH:MM"` field
- `.github/workflows/post_story.yml` — add/edit a `cron: "0 HH * * *"` line

GitHub Actions cron uses **UTC**. Convert your local times accordingly.

---

## Adding or editing stories

Edit `stories/content.json`. Each object supports:

```jsonc
{
  "time": "14:00",            // UTC hour to post (HH:MM — only the hour is matched)
  "background_color": "#ff6b6b", // Hex color for solid background (required if no image_file)
  "text": "Your caption here.\nSupports newlines.",
  "image_file": "stories/assets/photo.jpg" // Optional — omit for solid color
}
```

**Solid color story** (no `image_file`):
```json
{
  "time": "10:00",
  "background_color": "#1a1a2e",
  "text": "Morning drop. Shop now."
}
```

**Image with text overlay** (include `image_file`):
```json
{
  "time": "20:00",
  "image_file": "stories/assets/campaign.jpg",
  "text": "New collection out now."
}
```

Place image assets inside `stories/assets/` and commit them to the repo.

---

## Token expiry

Instagram long-lived tokens expire after **60 days**. When the token expires, `poster.py` will log:

```
[ERROR] Instagram access token is invalid or expired.
Regenerate the token at developers.facebook.com and update the
ACCESS_TOKEN repository secret.
```

Regenerate at [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer/) and update the secret.

---

## Manual trigger

You can post immediately without waiting for the scheduled cron by going to:

**Actions → Post Instagram Story → Run workflow**

This runs `poster.py` against the current UTC hour, so make sure a story is scheduled for that hour in `content.json`, or the script will exit with "nothing to post."

---

## Local testing

```bash
pip install -r requirements.txt

export ACCESS_TOKEN="your_token"
export USER_ID="your_user_id"
export IMGBB_API_KEY="your_imgbb_key"

python poster.py
```
