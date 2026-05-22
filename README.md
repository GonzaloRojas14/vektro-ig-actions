# Vektro IT — Instagram Stories Automation

Automatically publishes branded Instagram Stories on a weekly schedule using
Python + GitHub Actions + Instagram Graph API + ImgBB.

---

## Architecture

```
poster.py              ← entry point: reads schedule, orchestrates posting
token_manager.py       ← extends the Meta access token every 45 days
generator/
  render.py            ← picks the right template from entry["type"]
  utils.py             ← shared colors, fonts, drawing helpers
  templates/
    tech_tip.py        ← dark bg, code block, violet/cyan accents
    service_promo.py   ← circuit-grid bg, services list, CTA
    quote.py           ← gradient bg, large quote mark, attribution
    data_viz.py        ← Pillow-only bar chart, brand colors
stories/
  content.json         ← weekly posting schedule
.github/workflows/
  post_story.yml       ← cron per content.json entry + manual trigger
  refresh_token.yml    ← token renewal every 45 days
```

---

## GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Description |
|---|---|
| `ACCESS_TOKEN` | Instagram long-lived access token (60-day expiry) |
| `USER_ID` | Your Instagram user ID (numeric, e.g. `17841…`) |
| `IMGBB_API_KEY` | ImgBB API key — get it at [imgbb.com](https://imgbb.com) |
| `META_APP_ID` | Facebook App ID (for token refresh) |
| `META_APP_SECRET` | Facebook App Secret (for token refresh) |
| `GH_PAT` | GitHub Personal Access Token with `repo` scope (for token refresh) |

---

## Prerequisites

1. **Instagram Professional account** (Creator or Business) connected to a Facebook Page.
2. **Facebook App** with these permissions approved:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
3. **Long-lived access token** — generate at [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer/).
4. **ImgBB account** — free tier is fine. API key under *Settings → API*.
5. **GitHub PAT** — [github.com/settings/tokens](https://github.com/settings/tokens) → Tokens (classic) → `repo` scope.

---

## Adding or editing stories

Edit `stories/content.json`. Each entry supports:

```jsonc
{
  "day":      "monday",         // weekday, lowercase
  "time":     "09:00",          // UTC time (±30 min match window)
  "type":     "tech_tip",       // tech_tip | service_promo | quote | data_viz
  "text":     "Main headline",
  "subtext":  "Supporting copy or author attribution",
  "code":     "# Only for tech_tip\nclient = ...",
  "data":     [                 // Only for data_viz
    { "label": "Azure", "value": 78 }
  ],
  "source":   "Vektro IT Research",  // Only for data_viz
  "hashtags": ["VektroIT", "Cloud"]
}
```

**Also update the cron in `.github/workflows/post_story.yml`** to match any new times.

### Template reference

| Type | Key fields | Visual style |
|---|---|---|
| `tech_tip` | `text`, `code`, `subtext`, `hashtags` | Dark bg, violet code block |
| `service_promo` | `text`, `subtext`, `hashtags` | Circuit-grid bg, services list |
| `quote` | `text` (quote), `subtext` (author), `hashtags` | Gradient bg, large quote mark |
| `data_viz` | `text`, `data[]`, `source`, `hashtags` | Pillow bar chart |

---

## Scheduling

The workflow fires at exact UTC hours matching `content.json`. If your local
time differs, convert at [time.is/UTC](https://time.is/UTC).

| Entry | Cron | UTC time |
|---|---|---|
| Monday tech tip | `0 9 * * 1` | Mon 09:00 |
| Tuesday promo | `0 12 * * 2` | Tue 12:00 |
| Wednesday quote | `0 18 * * 3` | Wed 18:00 |
| Thursday tech tip | `0 9 * * 4` | Thu 09:00 |
| Friday data viz | `0 15 * * 5` | Fri 15:00 |
| Saturday quote | `0 11 * * 6` | Sat 11:00 |

---

## Token renewal

Instagram tokens expire after **60 days**. The `refresh_token.yml` workflow
runs automatically every 45 days and updates `ACCESS_TOKEN` via `gh secret set`.

To trigger manually: **Actions → Refresh Instagram Access Token → Run workflow**

If a token expires before renewal, `poster.py` logs:
```
[ERROR] Instagram access token is INVALID or EXPIRED.
  → Regenerate it at https://developers.facebook.com/tools/explorer/
  → Then update the ACCESS_TOKEN secret in your GitHub repository.
```

---

## Local testing

```bash
pip install -r requirements.txt

export ACCESS_TOKEN="your_token"
export USER_ID="your_user_id"
export IMGBB_API_KEY="your_imgbb_key"

# Test full flow (posts first story in content.json)
python poster.py --force

# Test token refresh
export META_APP_ID="your_app_id"
export META_APP_SECRET="your_app_secret"
python token_manager.py
```
