#!/usr/bin/env python3
"""Post the Verify or Ticket button message with the bot token (run from GitHub Actions)."""
import json, os, re, sys, urllib.request

KIND = os.environ.get("KIND", "").strip()
CHANNEL = os.environ.get("CHANNEL_ID", "").strip()
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
COLOR = 8141549
MESSAGES = {
    "verify": {
        "embeds": [{"title": "Verify", "color": COLOR,
                    "description": "Press the button below to confirm that you have read, understand and will follow the server rules. You will get the **Verified** role."}],
        "components": [{"type": 1, "components": [{"type": 2, "style": 3, "label": "I agree, verify me", "custom_id": "verify"}]}],
    },
    "ticket": {
        "embeds": [{"title": "Need help?", "color": COLOR,
                    "description": "Press the button to open a private ticket. Only you and the NeonBeta team can see it. Please don’t share passwords or private details."}],
        "components": [{"type": 1, "components": [{"type": 2, "style": 1, "label": "Open a ticket", "custom_id": "ticket_open"}]}],
    },
}


def main():
    if KIND not in MESSAGES:
        sys.exit("kind must be 'verify' or 'ticket'")
    if not re.fullmatch(r"\d{15,25}", CHANNEL):
        sys.exit("channel_id must be the numeric channel ID")
    if not TOKEN:
        sys.exit("DISCORD_BOT_TOKEN secret is missing")
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{CHANNEL}/messages",
        data=json.dumps(MESSAGES[KIND]).encode(), method="POST",
        headers={"Authorization": "Bot " + TOKEN, "Content-Type": "application/json",
                 "User-Agent": "DiscordBot (https://github.com/neonbetahq/neonbeta-site, 1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("posted, status", r.status)
    except urllib.error.HTTPError as e:
        sys.exit(f"Discord refused it (status {e.code}): {e.read().decode()[:300]}")


if __name__ == "__main__":
    main()
