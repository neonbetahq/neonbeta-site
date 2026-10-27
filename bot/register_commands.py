#!/usr/bin/env python3
"""Register the /alert slash commands for the NeonBeta server (run once, or after changing them)."""
import json, os, re, sys, urllib.request

TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
APP = os.environ.get("DISCORD_APP_ID", "").strip()
GUILD = os.environ.get("DISCORD_GUILD_ID", "").strip()
COMMANDS = [{
    "name": "alert", "description": "Get pinged when a game drops to your price",
    "options": [
        {"type": 1, "name": "add", "description": "Add a price alert", "options": [
            {"type": 3, "name": "game", "description": "Full game name", "required": True, "max_length": 80},
            {"type": 10, "name": "max_price", "description": "Ping me at or below this price", "required": True, "min_value": 0.5, "max_value": 500},
            {"type": 3, "name": "currency", "description": "USD (default) or EUR",
             "choices": [{"name": "USD", "value": "USD"}, {"name": "EUR", "value": "EUR"}]}]},
        {"type": 1, "name": "list", "description": "Show your alerts"},
        {"type": 1, "name": "remove", "description": "Remove one of your alerts", "options": [
            {"type": 4, "name": "number", "description": "The number shown by /alert list", "required": True, "min_value": 1}]},
    ]}]


def main():
    if not TOKEN or not re.fullmatch(r"\d{15,25}", APP) or not re.fullmatch(r"\d{15,25}", GUILD):
        sys.exit("Error: set DISCORD_BOT_TOKEN, DISCORD_APP_ID and DISCORD_GUILD_ID (IDs are numbers)")
    req = urllib.request.Request(f"https://discord.com/api/v10/applications/{APP}/guilds/{GUILD}/commands",
        data=json.dumps(COMMANDS).encode(), method="PUT",
        headers={"Authorization": "Bot " + TOKEN, "Content-Type": "application/json",
                 "User-Agent": "DiscordBot (https://github.com/neonbetahq/neonbeta-site, 1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("registered:", ", ".join(c["name"] for c in json.load(r)))
    except urllib.error.HTTPError as e:
        sys.exit(f"Discord refused it (status {e.code}): {e.read().decode()[:300]}")


if __name__ == "__main__":
    main()
