#!/usr/bin/env python3
"""Fetch PC game deals from the CheapShark API and write data/deals.json.

CheapShark is free, but its terms say deal links must go through CheapShark's
redirect URLs, so this script builds links that way. Standard library only.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

API = "https://www.cheapshark.com/api/1.0"
UA = "NeonBeta/1.0 (neonbeta.hq@gmail.com)"
WANTED = {"Steam", "GOG", "Humble Store", "Fanatical", "GreenManGaming", "Epic Games Store"}
PRETTY = {"Humble Store": "Humble", "GreenManGaming": "Green Man Gaming", "Epic Games Store": "Epic"}
SAFE_ID = re.compile(r"^[A-Za-z0-9%._~-]+$")   # only plain, URL-safe deal IDs are accepted
REDIRECT = "https://www.cheapshark.com/redirect?dealID="
MAX_LOOKUPS = 50          # per-game historical-low lookups per run
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "deals.json")


def get(path, **params):
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # network, rate limit, bad JSON
            print(f"warn: {url} failed ({e}); retry {attempt + 1}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return None


def main():
    stores = get("stores") or []
    names = {s["storeID"]: s["storeName"] for s in stores if str(s.get("isActive")) == "1"}
    ids = [i for i, n in names.items() if n in WANTED]
    if not ids:
        sys.exit("error: could not load store list from CheapShark")
    label = {i: PRETTY.get(names[i], names[i]) for i in ids}

    def fetch(sort, size, desc=0):
        out = get("deals", storeID=",".join(ids), onSale=1, sortBy=sort,
                  pageSize=size, pageNumber=0, upperPrice=60, desc=desc) or []
        time.sleep(0.6)
        return [d for d in out if SAFE_ID.match(str(d.get("dealID", "")))]

    by_savings = fetch("Savings", 60, 1)
    by_rating = fetch("Deal Rating", 40, 1)
    by_release = fetch("Release", 40, 1)
    by_reviews = fetch("Reviews", 20, 1)
    if not (by_savings or by_rating):
        sys.exit("error: no deals returned; keeping previous data")

    # historical lows: one lookup per distinct game, best discounts first
    lows, seen = {}, 0
    for d in by_savings + by_rating:
        gid = d.get("gameID")
        if gid in lows or seen >= MAX_LOOKUPS:
            continue
        seen += 1
        g = get("games", id=gid)
        try:
            lows[gid] = float(g["cheapestPriceEver"]["price"])
        except Exception:
            lows[gid] = None
        time.sleep(0.5)

    def norm(d):
        price, reg = float(d["salePrice"]), float(d["normalPrice"])
        low = lows.get(d.get("gameID"))
        rel = int(d.get("releaseDate") or 0)
        return {
            "id": d["dealID"], "title": d["title"], "store": label.get(d["storeID"], "Store"),
            "price": price, "regular": reg, "savings": round(float(d["savings"])),
            "hl": bool(low is not None and price <= low + 0.005), "low": low,
            "release": datetime.fromtimestamp(rel, timezone.utc).strftime("%Y-%m-%d") if rel > 0 else None,
            "url": REDIRECT + d["dealID"],
            "thumb": d["thumb"] if str(d.get("thumb", "")).startswith("https://") else None,
        }

    unique = {}
    for d in by_savings + by_rating:
        unique.setdefault(d["dealID"], norm(d))
    deals = sorted(unique.values(), key=lambda x: -x["savings"])[:80]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
    new = [x for x in map(norm, by_release) if x["release"] and x["release"] >= cutoff][:20]
    popular = [norm(d) for d in by_reviews][:20]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "source": "CheapShark", "deals": deals, "new": new, "popular": popular},
                  f, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    print(f"ok: {len(deals)} deals, {sum(x['hl'] for x in deals)} historical lows, "
          f"{len(new)} new, {len(popular)} popular")


if __name__ == "__main__":
    main()
