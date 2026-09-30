#!/usr/bin/env python3
"""Diagnose af LMS-forbindelsen – til opsætning og til testpersoner på nye universiteter.

Udskriver kun antal, filtyper og API-strukturer (nøglenavne) – aldrig tokens, cookies eller filindhold,
så resultatet trygt kan sendes til projektet, når en adapter skal rettes til.

Brug:
    uv run --with requests --with python-dotenv --with icalendar scripts/lms_test.py [--lms moodle]
    uv run ... scripts/lms_test.py --raa /restapi/personal/courses/v2    # vis struktur af et råt API-svar
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from lms import LMSFejl, hent_adapter
from lms import ical

ROD = Path(__file__).resolve().parent.parent
load_dotenv(ROD / ".env")


def skelet(d, dybde=0):
    """Struktur uden værdier: {"Items": [{"OrgUnit": {"Id": "int", …}}]}."""
    if dybde > 5:
        return "…"
    if isinstance(d, dict):
        return {k: skelet(v, dybde + 1) for k, v in list(d.items())[:25]}
    if isinstance(d, list):
        return [skelet(d[0], dybde + 1)] if d else []
    return type(d).__name__


def trin(navn, fn):
    try:
        res = fn()
        print(f"✅ {navn}: {res}")
        return True
    except (LMSFejl, NotImplementedError) as e:
        print(f"❌ {navn}: {e}")
    except Exception as e:
        print(f"❌ {navn}: {type(e).__name__}: {str(e)[:200]}")
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lms", help="platform (standard: 'lms' i config/fag.json)")
    p.add_argument("--raa", help="API-sti, hvis struktur skal vises (fx /d2l/api/versions/)")
    args = p.parse_args()

    cfg_sti = ROD / "config" / "fag.json"
    platform = args.lms or (json.loads(cfg_sti.read_text()).get("lms") if cfg_sti.exists() else "canvas")
    print(f"Platform: {platform}   ({datetime.now():%Y-%m-%d %H:%M})\n")
    try:
        lms = hent_adapter(platform)
    except LMSFejl as e:
        sys.exit(f"❌ Opsætning: {e}")
    if lms is None:
        print("LMS er 'manuel': læg filer i fag/<fag>/kilder/Manuel/.")
    else:
        print(f"{'Officielt API' if lms.officiel else '⚠️  Uofficiel adgang'}\n")
        if args.raa:
            base = getattr(lms, "url", None) or getattr(lms, "api", "")
            r = lms.session.get(f"{base}{args.raa}", timeout=60)
            print(f"HTTP {r.status_code}, Content-Type: {r.headers.get('Content-Type')}")
            try:
                print(json.dumps(skelet(r.json()), indent=1, ensure_ascii=False))
            except ValueError:
                print("(ikke JSON)")
            return
        kurser = []
        trin("Kurser", lambda: (kurser.extend(lms.kurser()), f"{len(kurser)} aktive kurser")[1])
        if kurser:
            k = kurser[0]
            filer = []
            trin(f"Filer i første kursus (id {k.id})", lambda: (filer.extend(lms.filer(k.id)),
                 f"{len(filer)} filer – {dict(Counter(Path(f.navn).suffix.lower() for f in filer))}, "
                 f"{sum(f.laast for f in filer)} låste, {len({f.mappe for f in filer})} mapper")[1])
            if filer:
                lille = min((f for f in filer if not f.laast), key=lambda f: f.stoerrelse or 10**9, default=None)
                if lille:
                    maal = ROD / ".cache" / "lms_test" / "testfil"
                    trin("Download af én fil", lambda: (lms.download(lille, maal),
                         f"{maal.stat().st_size} bytes, starter med {maal.read_bytes()[:4]!r}")[1])
                    maal.unlink(missing_ok=True)
        nu = datetime.now(timezone.utc)
        trin("Deadlines (30 dage)", lambda: f"{len(lms.deadlines(nu, nu + timedelta(days=30), [k.id for k in kurser]))} fundet")
    nu = datetime.now(timezone.utc)
    trin("Kalender-feed (ICAL_URL)", lambda: f"{len(ical.deadlines(nu, nu + timedelta(days=30)))} begivenheder")


if __name__ == "__main__":
    main()
