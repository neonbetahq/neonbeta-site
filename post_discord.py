#!/usr/bin/env python3
"""Post new historical-low deals to Discord through a webhook (kept in a secret)."""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
DEALS = os.path.join(ROOT, "data", "deals.json")
POSTED = os.path.join(ROOT, "data", "posted.json")
HOOK = os.environ.get("DISCORD_WEBHOOK_LOWS", "").strip()
ROLE = os.environ.get("DISCORD_ROLE_PRICE_DROP", "").strip()
MAX_POSTS = 5
REDIRECT = "https://www.cheapshark.com/redirect?dealID="


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def send(payload):
    req = urllib.request.Request(HOOK, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "NeonBeta/1.0"})
    with urllib.request.urlopen(req, timeout=30):
        pass


def main():
    if not HOOK:
        print("no webhook configured; skipping Discord posts")
        return
    deals = load(DEALS, {}).get("deals", [])
    posted = load(POSTED, [])
    todo = [d for d in deals if d.get("hl") and d["id"] not in posted
            and str(d.get("url", "")).startswith(REDIRECT)][:MAX_POSTS]
    for n, d in enumerate(todo):
        embed = {
            "title": "\U0001F4C9 " + d["title"], "url": d["url"], "color": 8141549,
            "description": f"**${d['price']:.2f}** (was ${d['regular']:.2f}, -{d['savings']}%)\n"
                           f"Lowest price on record \u00b7 {d['store']}",
            "footer": {"text": "Prices via CheapShark \u00b7 they change fast, so check the store"},
        }
        if str(d.get("thumb", "")).startswith("https://"):
            embed["thumbnail"] = {"url": d["thumb"]}
        payload = {"username": "NeonBeta", "embeds": [embed],
                   "allowed_mentions": {"roles": [ROLE]} if (ROLE and n == 0) else {"parse": []}}
        if ROLE and n == 0:
            payload["content"] = f"<@&{ROLE}>"
        try:
            send(payload)
        except Exception as e:
            print(f"warn: Discord post failed ({e}); will retry next run", file=sys.stderr)
            break
        posted.append(d["id"])
        time.sleep(1.5)
    with open(POSTED, "w", encoding="utf-8") as f:
        json.dump(posted[-500:], f)
    print(f"posted {len(todo)} deal(s)")


if __name__ == "__main__":
    main()
