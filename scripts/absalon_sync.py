#!/usr/bin/env python3
"""Synkroniserer kursusfiler (PDF/PPTX/DOCX) fra Absalon til fag/<fag>/kilder/.

Filer, der ligger i et modul, gemmes under kilder/<NN Modulnavn>/.
Filer, der kun findes under kursets Files, gemmes under kilder/Filer/<mappe>/.
Kun nye eller ændrede filer hentes (manifest: fag/<fag>/kilder/.manifest.json).

Brug:
    uv run --with requests --with python-dotenv scripts/absalon_sync.py [--fag KOF] [--dry-run]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROD = Path(__file__).resolve().parent.parent
TILLADTE = {".pdf", ".pptx", ".docx"}

load_dotenv(ROD / ".env")
API = os.environ.get("CANVAS_API_URL", "").rstrip("/")
TOKEN = os.environ.get("CANVAS_API_TOKEN", "")

session = requests.Session()
session.headers["Authorization"] = f"Bearer {TOKEN}"


def hent_alle(url, **params):
    """GET med Canvas-paginering. Returnerer None ved 401/403/404 (fx skjult Files-fane)."""
    params.setdefault("per_page", 100)
    ud = []
    while url:
        r = session.get(url, params=params, timeout=60)
        if r.status_code in (401, 403, 404):
            return None
        r.raise_for_status()
        ud += r.json()
        url, params = r.links.get("next", {}).get("url"), None
    return ud


def rent_navn(navn, maks=90):
    navn = re.sub(r'[/\\:*?"<>|\x00-\x1f]', "-", navn).strip().strip(".")
    navn = re.sub(r"\s+", " ", navn)
    endelse = Path(navn).suffix if Path(navn).suffix.lower() in TILLADTE else ""
    stamme = navn[: len(navn) - len(endelse)] if endelse else navn
    return (stamme[: maks - len(endelse)].rstrip() or "uden-navn") + endelse


def filtype_ok(fil):
    return Path(fil.get("display_name") or fil.get("filename") or "").suffix.lower() in TILLADTE


def saml_filer(kursus_id):
    """Returnerer {fil_id: (fil-metadata, relativ mappe)}. Moduler har forrang for Files."""
    filer = {}

    moduler = hent_alle(f"{API}/courses/{kursus_id}/modules", **{"include[]": "items"}) or []
    for i, modul in enumerate(sorted(moduler, key=lambda m: m.get("position", 0)), 1):
        mappe = f"{i:02d} {rent_navn(modul.get('name', 'Modul'), 60)}"
        items = modul.get("items")
        if items is None:  # store moduler returnerer ikke items inline
            items = hent_alle(f"{API}/courses/{kursus_id}/modules/{modul['id']}/items") or []
        for item in items:
            if item.get("type") != "File" or item.get("content_id") in filer:
                continue
            r = session.get(f"{API}/courses/{kursus_id}/files/{item['content_id']}", timeout=60)
            if r.ok and filtype_ok(r.json()):
                filer[item["content_id"]] = (r.json(), mappe)

    mapper = {m["id"]: m.get("full_name", "") for m in (hent_alle(f"{API}/courses/{kursus_id}/folders") or [])}
    for fil in hent_alle(f"{API}/courses/{kursus_id}/files") or []:
        if fil["id"] in filer or not filtype_ok(fil):
            continue
        sti = re.sub(r"^course files/?", "", mapper.get(fil.get("folder_id"), ""))
        dele = [rent_navn(d, 60) for d in sti.split("/") if d]
        filer[fil["id"]] = (fil, str(Path("Filer", *dele)))
    return filer


def synk_fag(fag, info, dry_run):
    kilder = ROD / "fag" / fag / "kilder"
    kilder.mkdir(parents=True, exist_ok=True)
    manifest_sti = kilder / ".manifest.json"
    manifest = json.loads(manifest_sti.read_text()) if manifest_sti.exists() else {}

    nye, fejl = [], []
    for fil_id, (fil, mappe) in saml_filer(info["kursus_id"]).items():
        noegle = str(fil_id)
        rel = Path(mappe) / rent_navn(fil.get("display_name") or fil["filename"])
        gammel = manifest.get(noegle)
        uaendret = gammel and gammel["updated_at"] == fil.get("updated_at") and (kilder / gammel["sti"]).exists()
        if uaendret:
            continue
        if fil.get("locked_for_user") or not fil.get("url"):
            fejl.append(f"{rel} (låst/ingen adgang)")
            continue
        status = "ændret" if gammel else "ny"
        if not dry_run:
            maal = kilder / rel
            maal.parent.mkdir(parents=True, exist_ok=True)
            try:
                with session.get(fil["url"], stream=True, timeout=300) as r:
                    r.raise_for_status()
                    tmp = maal.with_suffix(maal.suffix + ".part")
                    with open(tmp, "wb") as f:
                        for bid in r.iter_content(1 << 16):
                            f.write(bid)
                    tmp.replace(maal)
            except requests.RequestException as e:
                fejl.append(f"{rel} ({type(e).__name__})")
                continue
            if gammel and gammel["sti"] != str(rel):
                (kilder / gammel["sti"]).unlink(missing_ok=True)
            manifest[noegle] = {
                "sti": str(rel),
                "navn": fil.get("display_name"),
                "updated_at": fil.get("updated_at"),
                "stoerrelse": fil.get("size"),
                "modul": mappe,
                # nulstilles ved ændring, så sync_all.sh uploader den nye version til NotebookLM
                "notebooklm_source_id": None,
                "notebooklm_forrige_source_id": (gammel or {}).get("notebooklm_source_id"),
            }
        nye.append(f"[{status}] {rel}")

    if not dry_run:
        manifest_sti.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return nye, fejl, len(manifest)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fag", help="kun dette fag (kort navn fra config/fag.json)")
    p.add_argument("--dry-run", action="store_true", help="vis hvad der ville blive hentet")
    args = p.parse_args()
    if not TOKEN or not API:
        sys.exit("CANVAS_API_TOKEN/CANVAS_API_URL mangler i .env")

    alle_fag = json.loads((ROD / "config" / "fag.json").read_text())["fag"]
    valgte = {args.fag: alle_fag[args.fag]} if args.fag else alle_fag

    total = 0
    for fag, info in valgte.items():
        nye, fejl, i_alt = synk_fag(fag, info, args.dry_run)
        total += len(nye)
        print(f"\n== {fag} ({info['kursusnavn']}): {len(nye)} nye/ændrede, {i_alt} i alt")
        for linje in nye:
            print("  " + linje)
        for linje in fejl:
            print("  [sprunget over] " + linje)
    print(f"\nI alt {total} nye/ændrede filer{' (dry-run)' if args.dry_run else ''}.")


if __name__ == "__main__":
    main()
