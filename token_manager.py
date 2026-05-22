"""
Vektro IT — Meta access token extender.

Exchanges the current short/long-lived Instagram access token for a new
long-lived token (60-day validity) via the Meta Graph API.

On success  → prints ONLY the new token to stdout (no other output).
On failure  → logs to stderr and exits with code 1.

The GitHub Actions workflow captures stdout and pipes it to:
    gh secret set ACCESS_TOKEN

Required environment variables:
  ACCESS_TOKEN    — current Instagram Graph API access token
  META_APP_ID     — Facebook App ID
  META_APP_SECRET — Facebook App Secret
"""

import logging
import os
import sys

import requests

# All logging goes to stderr so stdout stays clean for token capture
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v19.0"


def extend_token(current_token: str, app_id: str, app_secret: str) -> str:
    """Exchange current token for a new long-lived token."""
    log.info("Requesting long-lived token from Meta…")
    resp = requests.get(
        f"{GRAPH_API}/oauth/access_token",
        params={
            "grant_type":       "fb_exchange_token",
            "client_id":        app_id,
            "client_secret":    app_secret,
            "fb_exchange_token": current_token,
        },
        timeout=20,
    )

    if not resp.ok:
        try:
            err = resp.json().get("error", {})
        except Exception:
            err = {}
        code = err.get("code", 0)
        msg  = err.get("message", resp.text)

        if code in (190, 102) or "token" in msg.lower():
            log.error(
                "Current access token is INVALID or EXPIRED.\n"
                "  → Generate a fresh token at https://developers.facebook.com/tools/explorer/\n"
                "  → Update the ACCESS_TOKEN secret manually, then re-run this workflow."
            )
        else:
            log.error("Meta API error [%d]: %s", resp.status_code, msg)
        sys.exit(1)

    body = resp.json()
    new_token = body.get("access_token", "").strip()
    if not new_token:
        log.error("Meta returned an empty access_token: %s", body)
        sys.exit(1)

    expires_in = body.get("expires_in", "unknown")
    log.info("New token received (expires_in=%s seconds ≈ %s days)",
             expires_in,
             round(int(expires_in) / 86400) if str(expires_in).isdigit() else "?")
    return new_token


def verify_token(token: str) -> None:
    """Check that the new token is valid by hitting /me."""
    log.info("Verifying new token…")
    resp = requests.get(
        f"{GRAPH_API}/me",
        params={"fields": "id,name", "access_token": token},
        timeout=15,
    )
    if resp.ok:
        data = resp.json()
        log.info("Token valid for user: %s (id=%s)", data.get("name", "?"), data.get("id", "?"))
    else:
        log.warning("Token verification call returned %d — proceeding anyway", resp.status_code)


def main() -> None:
    token      = os.environ.get("ACCESS_TOKEN",    "").strip()
    app_id     = os.environ.get("META_APP_ID",     "").strip()
    app_secret = os.environ.get("META_APP_SECRET", "").strip()

    missing = [k for k, v in {
        "ACCESS_TOKEN":    token,
        "META_APP_ID":     app_id,
        "META_APP_SECRET": app_secret,
    }.items() if not v]
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    new_token = extend_token(token, app_id, app_secret)
    verify_token(new_token)

    # Print ONLY the token to stdout — captured by the workflow
    print(new_token, end="")


if __name__ == "__main__":
    main()
