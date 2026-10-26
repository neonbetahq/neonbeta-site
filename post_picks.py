#!/usr/bin/env python3
"""Post new hand-picked deals from data/picks.json to Discord (webhook kept in a secret)."""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PICKS = os.path.join(ROOT, "data", "picks.json")
POSTED = os.path.join(ROOT, "data", "posted_picks.json")
HOOK = os.environ.get("DISCORD_WEBHOOK_PICKS", "").strip()
MAX_POSTS = 5
STATUS = {"lowest-ever": "\u2705 Lowest price we\u2019ve seen", "great": "\U0001F525 Great discount",
          "solid": "\U0001F44D Solid discount", "small": "\u23F3 Small discount \u00b7 worth waiting for",
          "wait": "\u23F3 Wait for a better price", "free": "\U0001F381 Free to keep",
          "must-play": "\u2B50 Must play", "hidden-gem": "\U0001F48E Hidden gem",
          "co-op": "\U0001F91D Great with friends", "cozy": "\U0001F33F Cozy pick",
          "short": "\u23F1 Short and sweet"}


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def key(p):
    return p.get("id") or f"{p.get('title', '')}|{p.get('store', '')}|{p.get('date', '')}"


def money(v, sym="$"):
    return f"{sym}{v:,.2f}"


def build(p):
    sym = "\u20AC" if str(p.get("currency", "")).upper() == "EUR" else "$"
    lines = []
    if STATUS.get(p.get("status")):
        lines.append(STATUS[p["status"]])
    price, reg = p.get("price"), p.get("regular")
    if isinstance(price, (int, float)):
        if price == 0:
            lines.append("**Free**" + (f" ({p['until']})" if p.get("until") else ""))
        elif isinstance(reg, (int, float)) and reg > price:
            lines.append(f"**{money(price, sym)}** (was {money(reg, sym)}, -{round((1 - price / reg) * 100)}%)")
        else:
            lines.append(f"**{money(price, sym)}**")
    for e in p.get("editions") or []:
        if e.get("name") and isinstance(e.get("price"), (int, float)):
            lines.append(f"\u2022 {e['name']}: {money(e['price'], sym)}")
    meta = " \u00b7 ".join(x for x in [p.get("store"), p.get("edition"),
                                         (p.get("type") or "").upper() if p.get("type") not in (None, "", "game") else ""] if x)
    if meta:
        lines.append(meta)
    if p.get("note"):
        lines.append(p["note"])
    embed = {"title": "\u2B50 " + p["title"], "description": "\n".join(lines)[:3500], "color": 8141549,
             "footer": {"text": "NeonBeta Pick \u00b7 Prices change fast, so check the store. Some links are affiliate links."}}
    if str(p.get("url", "")).startswith("https://"):
        embed["url"] = p["url"]
    return embed


def main():
    if not HOOK:
        print("no picks webhook configured; skipping")
        return
    picks = load(PICKS, {}).get("picks", [])
    posted = load(POSTED, [])
    todo = [p for p in picks if p.get("active") is not False and p.get("title") and key(p) not in posted][:MAX_POSTS]
    for p in todo:
        payload = {"username": "NeonBeta", "embeds": [build(p)], "allowed_mentions": {"parse": []}}
        req = urllib.request.Request(HOOK, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "NeonBeta/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except Exception as e:
            print(f"warn: Discord post failed ({e}); will retry next run", file=sys.stderr)
            break
        posted.append(key(p))
        time.sleep(1.5)
    with open(POSTED, "w", encoding="utf-8") as f:
        json.dump(posted[-500:], f)
    print(f"posted {len(todo)} pick(s)")


if __name__ == "__main__":
    main()
