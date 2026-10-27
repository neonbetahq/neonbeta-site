#!/usr/bin/env python3
"""Send or edit a bot message from a template in bot/messages.json, or a quick custom one.
Run from GitHub Actions (Send or edit message)."""
import json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
CHANNEL = os.environ.get("CHANNEL_ID", "").strip()
NAME = (os.environ.get("MESSAGE_NAME", "") or "custom").strip()
EDIT_ID = os.environ.get("MESSAGE_ID", "").strip()
COLOR = 8141549
ALLOWED_BUTTON_IDS = {"verify", "ticket_open"}  # buttons the bot knows how to handle


def fail(msg):
    sys.exit("Error: " + msg)


def build():
    if NAME == "custom":
        title = os.environ.get("TITLE", "").strip()
        desc = os.environ.get("DESCRIPTION", "").replace("\\n", "\n").strip()
        if not (title or desc):
            fail("custom messages need a title or a description")
        embed = {"color": COLOR}
        if title:
            embed["title"] = title[:256]
        if desc:
            embed["description"] = desc[:4000]
        return {"embeds": [embed]}
    try:
        with open(os.path.join(ROOT, "messages.json"), encoding="utf-8") as f:
            templates = json.load(f)
    except Exception as e:
        fail(f"could not read bot/messages.json ({e})")
    if NAME not in templates:
        fail(f"no template called '{NAME}'. Available: {', '.join(sorted(templates))}, or use custom")
    return templates[NAME]


def check(payload):
    extra = set(payload) - {"content", "embeds", "components"}
    if extra:
        fail(f"unsupported keys in template: {', '.join(sorted(extra))}")
    for row in payload.get("components", []):
        for c in row.get("components", []):
            if c.get("type") != 2:
                fail("only buttons are supported")
            if c.get("style") == 5:
                if not str(c.get("url", "")).startswith("https://"):
                    fail("link buttons need an https:// url")
            elif c.get("custom_id") not in ALLOWED_BUTTON_IDS:
                fail(f"button custom_id must be one of: {', '.join(sorted(ALLOWED_BUTTON_IDS))}")
    for e in payload.get("embeds", []):
        if len(json.dumps(e)) > 5500:
            fail("an embed is too long")


def main():
    if not TOKEN:
        fail("DISCORD_BOT_TOKEN secret is missing")
    if not re.fullmatch(r"\d{15,25}", CHANNEL):
        fail("channel_id must be the numeric channel ID")
    if EDIT_ID and not re.fullmatch(r"\d{15,25}", EDIT_ID):
        fail("message_id must be the numeric message ID")
    payload = dict(build())
    check(payload)
    payload["allowed_mentions"] = {"parse": []}  # never ping @everyone or roles from templates
    base = f"https://discord.com/api/v10/channels/{CHANNEL}/messages"
    url, method = (f"{base}/{EDIT_ID}", "PATCH") if EDIT_ID else (base, "POST")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method=method,
        headers={"Authorization": "Bot " + TOKEN, "Content-Type": "application/json",
                 "User-Agent": "DiscordBot (https://github.com/neonbetahq/neonbeta-site, 1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        fail(f"Discord refused it (status {e.code}): {e.read().decode()[:300]}")
    print(("Edited" if EDIT_ID else "Posted") + f" message. Message ID: {data.get('id')}  (keep this to edit it later)")


if __name__ == "__main__":
    main()
