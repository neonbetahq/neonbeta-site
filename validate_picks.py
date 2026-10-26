#!/usr/bin/env python3
"""Check data/picks.json and print clear, plain-English problems."""
import json, os, sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "picks.json")
STATUSES = ["lowest-ever", "great", "solid", "small", "wait", "free", "must-play",
            "hidden-gem", "co-op", "cozy", "short"]
TYPES = ["game", "dlc", "bundle"]


def main():
    try:
        with open(PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        sys.exit(f"data/picks.json is not valid JSON: {e}\n"
                 "Common causes: a missing comma, a trailing comma, curly quotes, or a missing bracket.")
    picks = data.get("picks") if isinstance(data, dict) else None
    if not isinstance(picks, list):
        sys.exit('data/picks.json needs a "picks" list, like {"picks": [ ... ]}')
    errors = []

    def num(label, v):
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
            errors.append(f'{label}: must be a number like 13.49 (no quotes, no $ sign)')

    def https(label, v):
        if v and not str(v).startswith("https://"):
            errors.append(f"{label}: link must start with https://")

    for i, p in enumerate(picks, 1):
        name = p.get("title") or f"pick #{i}"
        if not p.get("title"):
            errors.append(f"pick #{i}: missing \"title\"")
        num(f"{name} price", p.get("price"))
        num(f"{name} regular", p.get("regular"))
        num(f"{name} hours", p.get("hours"))
        https(f"{name} url", p.get("url"))
        if p.get("status") and p["status"] not in STATUSES:
            errors.append(f"{name}: unknown status \"{p['status']}\". Use one of: {', '.join(STATUSES)}")
        if p.get("type") and p["type"] not in TYPES:
            errors.append(f"{name}: unknown type \"{p['type']}\". Use one of: {', '.join(TYPES)}")
        for e in p.get("editions", []) or []:
            en = f"{name} / {e.get('name', 'edition')}"
            if not e.get("name"):
                errors.append(f"{name}: an edition is missing \"name\"")
            num(f"{en} price", e.get("price"))
            num(f"{en} regular", e.get("regular"))
            https(f"{en} url", e.get("url"))
            if e.get("price") is None:
                errors.append(f"{en}: missing \"price\"")
    if errors:
        print("Problems in data/picks.json:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"picks ok ({len(picks)} entries)")


if __name__ == "__main__":
    main()
