#!/usr/bin/env python3
"""Viser kommende afleveringer, quizzer og begivenheder fra Absalon for fagene i config/fag.json.

Brug:
    uv run --with requests --with python-dotenv scripts/deadlines.py [--dage 14]
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROD = Path(__file__).resolve().parent.parent
load_dotenv(ROD / ".env")
API = os.environ["CANVAS_API_URL"].rstrip("/")
H = {"Authorization": f"Bearer {os.environ['CANVAS_API_TOKEN']}"}
DK = ZoneInfo("Europe/Copenhagen")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dage", type=int, default=14)
    args = p.parse_args()

    fag = json.loads((ROD / "config" / "fag.json").read_text())["fag"]
    navn = {v["kursus_id"]: k for k, v in fag.items()}
    nu = datetime.now(timezone.utc)
    params = {
        "start_date": nu.isoformat(),
        "end_date": (nu + timedelta(days=args.dage)).isoformat(),
        "context_codes[]": [f"course_{cid}" for cid in navn],
        "per_page": 100,
    }
    url, poster = f"{API}/planner/items", []
    while url:
        r = requests.get(url, headers=H, params=params, timeout=60)
        r.raise_for_status()
        poster += r.json()
        url, params = r.links.get("next", {}).get("url"), None

    print(f"Deadlines og begivenheder de næste {args.dage} dage:\n")
    if not poster:
        print("  (ingen)")
    for p in sorted(poster, key=lambda p: p.get("plannable_date") or ""):
        tid = datetime.fromisoformat(p["plannable_date"].replace("Z", "+00:00")).astimezone(DK)
        titel = (p.get("plannable") or {}).get("title") or (p.get("plannable") or {}).get("name") or "?"
        indleveret = (p.get("submissions") or {}).get("submitted") if isinstance(p.get("submissions"), dict) else None
        status = " ✅ afleveret" if indleveret else ""
        fagnavn = navn.get(p.get("course_id"), p.get("context_name", ""))
        print(f"  {tid:%a %d/%m %H:%M}  {fagnavn:18} {p.get('plannable_type', ''):16} {titel}{status}")


if __name__ == "__main__":
    main()
