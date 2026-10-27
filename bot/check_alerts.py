#!/usr/bin/env python3
"""Check members' price alerts against CheapShark and ping them in Discord (webhook kept in a secret).
CheapShark's terms: deal links must use its redirect links, which this does."""
import json, os, re, sys, time, urllib.parse, urllib.request

API = "https://www.cheapshark.com/api/1.0"
REDIRECT = "https://www.cheapshark.com/redirect?dealID="
UA = "NeonBeta/1.0 (neonbeta.hq@gmail.com)"
SAFE_ID = re.compile(r"^[A-Za-z0-9%._~-]+$")
EUR_PER_USD = 0.87
MAX_ALERTS = 40
ALERTS_URL = os.environ.get("ALERTS_URL", "").rstrip("/")
ADMIN_KEY = os.environ.get("ALERTS_ADMIN_KEY", "")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_ALERTS", "").strip()


def http(url, data=None, headers=None, method=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        return json.loads(body) if body else None


def cs(path, **params):
    for attempt in range(3):
        try:
            return http(f"{API}/{path}?" + urllib.parse.urlencode(params))
        except Exception as e:
            print(f"warn: CheapShark {path} failed ({e})", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return None


def find(alert, stores):
    words = re.findall(r"[a-z0-9]+", alert["game"].lower())
    if not words:
        return None
    games = cs("games", title=alert["game"], limit=10) or []
    cands = [g for g in games if all(w in str(g.get("external", "")).lower() for w in words)]
    if not cands:
        return None
    g = min(cands, key=lambda x: len(x["external"]))
    price = float(g["cheapest"])
    limit = alert["max"] / EUR_PER_USD if alert.get("cur") == "EUR" else alert["max"]
    deal_id = str(g.get("cheapestDealID", ""))
    if price > limit + 0.005 or not SAFE_ID.match(deal_id):
        return None
    info = (cs("deals", id=deal_id) or {}).get("gameInfo", {})
    time.sleep(0.5)
    return {"title": g["external"], "price": price, "regular": float(info.get("retailPrice") or 0),
            "store": stores.get(info.get("storeID"), "a store"), "url": REDIRECT + deal_id}


def notify(alert, hit):
    price = f"**${hit['price']:.2f}**" + (f" (about €{hit['price'] * EUR_PER_USD:.2f})" if alert.get("cur") == "EUR" else "")
    was = f" (was ${hit['regular']:.2f})" if hit["regular"] > hit["price"] else ""
    payload = {"username": "NeonBeta", "content": f"<@{alert['user']}> your price alert hit! 🔔",
        "allowed_mentions": {"users": [alert["user"]]},
        "embeds": [{"title": hit["title"], "url": hit["url"], "color": 8141549,
            "description": f"{price} at {hit['store']}{was}",
            "footer": {"text": "Price data courtesy of CheapShark · prices change fast, so check the store"}}]}
    try:
        http(WEBHOOK, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        return True
    except Exception as e:
        print(f"warn: Discord post failed ({e})", file=sys.stderr)
        return False


def main():
    if not (ALERTS_URL and ADMIN_KEY and WEBHOOK):
        print("alerts not configured (need ALERTS_URL, ALERTS_ADMIN_KEY, DISCORD_WEBHOOK_ALERTS); skipping")
        return
    try:
        alerts = http(ALERTS_URL + "/alerts", headers={"Authorization": "Bearer " + ADMIN_KEY}) or []
    except Exception as e:
        sys.exit(f"could not read alerts from the bot ({e})")
    if not alerts:
        print("no alerts to check")
        return
    stores = {s["storeID"]: s["storeName"] for s in (cs("stores") or [])}
    fired = []
    for a in alerts[:MAX_ALERTS]:
        try:
            hit = find(a, stores)
        except Exception as e:
            print("warn: skipped one alert:", e, file=sys.stderr)
            continue
        if hit and notify(a, hit):
            fired.append(a["key"])
        time.sleep(0.6)
    if fired:
        http(ALERTS_URL + "/alerts/delete", data=json.dumps({"keys": fired}).encode(),
             headers={"Authorization": "Bearer " + ADMIN_KEY, "Content-Type": "application/json"}, method="POST")
    print(f"checked {min(len(alerts), MAX_ALERTS)} alert(s), pinged {len(fired)}")


if __name__ == "__main__":
    main()
