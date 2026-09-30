#!/usr/bin/env python3
"""Kommende afleveringer, quizzer og begivenheder fra LMS'et (og evt. kalender-feed i ICAL_URL).

Brug:
    uv run --with requests --with python-dotenv --with icalendar scripts/deadlines.py [--dage 14]
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from lms import LMSFejl, hent_adapter
from lms import ical

ROD = Path(__file__).resolve().parent.parent
load_dotenv(ROD / ".env")
DK = ZoneInfo("Europe/Copenhagen")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dage", type=int, default=14)
    args = p.parse_args()

    cfg = json.loads((ROD / "config" / "fag.json").read_text())
    navn = {str(v["kursus_id"]): k for k, v in cfg["fag"].items() if v.get("kursus_id")}
    fra = datetime.now(timezone.utc)
    til = fra + timedelta(days=args.dage)

    poster, advarsler = [], []
    try:
        lms = hent_adapter(cfg.get("lms", "canvas"))
        if lms:
            poster += lms.deadlines(fra, til, list(navn))
    except (LMSFejl, NotImplementedError) as e:
        advarsler.append(f"LMS: {e}")
    try:
        poster += ical.deadlines(fra, til)
    except Exception as e:  # kalender-feed er valgfrit
        advarsler.append(f"kalender-feed: {e}")

    set_ = set()
    print(f"Deadlines og begivenheder de næste {args.dage} dage:\n")
    for d in sorted(poster, key=lambda d: d.tid):
        noegle = (d.titel, d.tid.replace(second=0, microsecond=0))
        if noegle in set_:
            continue  # samme deadline fra både LMS og kalender-feed
        set_.add(noegle)
        fag = navn.get(d.kursus_id or "", d.kursus_id or "")
        status = " ✅ afleveret" if d.afleveret else ""
        print(f"  {d.tid.astimezone(DK):%a %d/%m %H:%M}  {fag[:18]:18} {d.type[:16]:16} {d.titel}{status}")
    if not set_:
        print("  (ingen)")
    for a in advarsler:
        print(f"\n⚠️  {a}")


if __name__ == "__main__":
    main()
