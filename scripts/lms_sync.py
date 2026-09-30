#!/usr/bin/env python3
"""Synkroniserer kursusfiler (PDF/PPTX/DOCX) fra universitetets LMS til fag/<fag>/kilder/.

Platform vælges med "lms" i config/fag.json: canvas | moodle | brightspace | itslearning | manuel.
Filer lagt i fag/<fag>/kilder/Manuel/ registreres også (virker på alle universiteter).
Kun nye eller ændrede filer hentes (manifest: fag/<fag>/kilder/.manifest.json).

Brug:
    uv run --with requests --with python-dotenv scripts/lms_sync.py [--fag KOF] [--dry-run]
    uv run --with requests --with python-dotenv scripts/lms_sync.py --kurser   # vis aktive kurser
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from lms import LMSFejl, hent_adapter
from lms.base import filtype_ok, rent_navn

ROD = Path(__file__).resolve().parent.parent
load_dotenv(ROD / ".env")


def ny_post(fil_navn, sti, updated_at, stoerrelse, modul, gammel):
    return {
        "sti": str(sti), "navn": fil_navn, "updated_at": updated_at, "stoerrelse": stoerrelse, "modul": modul,
        # nulstilles ved ændring, så notebook_sync uploader den nye version til NotebookLM
        "notebooklm_source_id": None,
        "notebooklm_forrige_source_id": (gammel or {}).get("notebooklm_source_id"),
    }


def synk_lms(lms, info, kilder, manifest, dry_run):
    nye, fejl = [], []
    for fil in lms.filer(str(info["kursus_id"])):
        rel = Path(fil.mappe) / rent_navn(fil.navn)
        gammel = manifest.get(fil.id)
        if gammel and gammel["updated_at"] == fil.updated_at and (kilder / gammel["sti"]).exists():
            continue
        if fil.laast:
            fejl.append(f"{rel} (låst/ingen adgang)")
            continue
        if not dry_run:
            try:
                lms.download(fil, kilder / rel)
            except (requests.RequestException, LMSFejl, KeyError) as e:
                fejl.append(f"{rel} ({e})")
                continue
            if gammel and gammel["sti"] != str(rel):
                (kilder / gammel["sti"]).unlink(missing_ok=True)
            manifest[fil.id] = ny_post(fil.navn, rel, fil.updated_at, fil.stoerrelse, fil.mappe, gammel)
        nye.append(f"[{'ændret' if gammel else 'ny'}] {rel}")
    return nye, fejl


def synk_manuel(kilder, manifest, dry_run):
    """Filer brugeren selv har lagt i kilder/Manuel/ (fx fra itslearning eller en USB-nøgle)."""
    nye = []
    manuel = kilder / "Manuel"
    manuel.mkdir(parents=True, exist_ok=True)
    for f in sorted(manuel.rglob("*")):
        if not f.is_file() or not filtype_ok(f.name):
            continue
        rel = f.relative_to(kilder)
        noegle = f"manuel:{rel}"
        aendret = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
        gammel = manifest.get(noegle)
        if gammel and gammel["updated_at"] == aendret:
            continue
        if not dry_run:
            manifest[noegle] = ny_post(f.name, rel, aendret, f.stat().st_size, str(rel.parent), gammel)
        nye.append(f"[{'ændret' if gammel else 'ny'}, manuel] {rel}")
    return nye


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fag", help="kun dette fag (kort navn fra config/fag.json)")
    p.add_argument("--dry-run", action="store_true", help="vis hvad der ville blive hentet")
    p.add_argument("--kurser", action="store_true", help="vis dine aktive kurser (til config/fag.json)")
    args = p.parse_args()

    cfg = json.loads((ROD / "config" / "fag.json").read_text()) if (ROD / "config" / "fag.json").exists() else {}
    try:
        lms = hent_adapter(cfg.get("lms", "canvas"))
    except LMSFejl as e:
        sys.exit(f"❌ {e}")
    if lms and not lms.officiel:
        print(f"⚠️  {lms.navn}: uofficiel adgang – kan holde op med at virke uden varsel.\n")

    if args.kurser:
        if not lms:
            sys.exit("LMS er 'manuel' – der er ingen kurser at hente.")
        for k in lms.kurser():
            print(f"{k.id:>10} | {k.kode[:25]:25} | {k.navn[:70]:70} | {k.termin}")
        return

    fag = cfg.get("fag", {})
    valgte = {args.fag: fag[args.fag]} if args.fag else fag
    total = 0
    for navn, info in valgte.items():
        kilder = ROD / "fag" / navn / "kilder"
        kilder.mkdir(parents=True, exist_ok=True)
        manifest_sti = kilder / ".manifest.json"
        manifest = json.loads(manifest_sti.read_text()) if manifest_sti.exists() else {}
        nye, fejl = [], []
        if lms and info.get("kursus_id"):
            try:
                nye, fejl = synk_lms(lms, info, kilder, manifest, args.dry_run)
            except LMSFejl as e:
                fejl = [f"hele faget sprunget over: {e}"]
        nye += synk_manuel(kilder, manifest, args.dry_run)
        if not args.dry_run:
            manifest_sti.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        total += len(nye)
        print(f"\n== {navn} ({info.get('kursusnavn', '')}): {len(nye)} nye/ændrede, {len(manifest)} i alt")
        for linje in nye:
            print("  " + linje)
        for linje in fejl:
            print("  [sprunget over] " + linje)
    print(f"\nI alt {total} nye/ændrede filer{' (dry-run)' if args.dry_run else ''}.")


if __name__ == "__main__":
    main()
