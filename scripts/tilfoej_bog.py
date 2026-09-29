#!/usr/bin/env python3
"""Tilføjer en lærebog (PDF) til et fag: kopi i fag/<fag>/kilder/Bøger/ + upload til fagets notebook.

Teksten uploades med markører "--- Side N ---" (N = PDF-sidetal, samme som billede.py bruger),
så citater kan føres tilbage til en side. Bøger over MAKS_ORD deles i flere kilder.
Scannede bøger uden tekstlag uploades som PDF (NotebookLM forsøger selv OCR).

Brug:
    uv run --with pymupdf scripts/tilfoej_bog.py --fag Radiologi --fil ~/Downloads/bog.pdf \
        --titel "White & Pharoah's Oral Radiology, 8. udg. (2019)" [--dry-run]
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_sync import find_id, nlm_json, normaliser  # noqa: E402

ROD = Path(__file__).resolve().parent.parent
MAKS_ORD = 350_000  # NotebookLM: ca. 500.000 ord pr. kilde – god margin


def del_op(sider):
    """Grupperer sider i dele på højst MAKS_ORD ord. Returnerer [(fra, til), ...] (1-indekseret)."""
    dele, start, ord_ = [], 1, 0
    for i, tekst in enumerate(sider, 1):
        n = len(tekst.split())
        if ord_ + n > MAKS_ORD and i > start:
            dele.append((start, i - 1))
            start, ord_ = i, 0
        ord_ += n
    dele.append((start, len(sider)))
    return dele


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fag", required=True)
    p.add_argument("--fil", required=True)
    p.add_argument("--titel", required=True, help="læsbar titel inkl. udgave, fx 'Robbins Basic Pathology, 11. udg. (2022)'")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    cfg = json.loads((ROD / "config" / "fag.json").read_text())
    nb = cfg["fag"][args.fag]["notebook_id"]
    kilder = ROD / "fag" / args.fag / "kilder"
    manifest_sti = kilder / ".manifest.json"
    manifest = json.loads(manifest_sti.read_text()) if manifest_sti.exists() else {}
    noegle = "bog:" + normaliser(args.titel)[:60]
    if manifest.get(noegle, {}).get("notebooklm_source_id"):
        sys.exit(f"'{args.titel}' er allerede tilføjet til {args.fag}.")

    kilde = Path(args.fil).expanduser()
    with pymupdf.open(kilde) as doc:
        sider = [s.get_text() for s in doc]
    ord_i_alt = sum(len(s.split()) for s in sider)
    scannet = ord_i_alt < 2 * len(sider)  # i snit under 2 ord pr. side → scannet uden tekstlag
    dele = [(1, len(sider))] if scannet else del_op(sider)
    print(f"{args.titel}: {len(sider)} sider, {ord_i_alt} ord → "
          f"{'scannet: uploades som PDF' if scannet else f'{len(dele)} del(e)'}")
    if args.dry_run:
        for fra, til in dele:
            print(f"  s. {fra}–{til}")
        return

    maal = kilder / "Bøger" / (re.sub(r'[/\\:*?"<>|]', "-", args.titel) + ".pdf")
    maal.parent.mkdir(parents=True, exist_ok=True)
    if not maal.exists():
        shutil.copy2(kilde, maal)

    ids, del_info = [], []
    for i, (fra, til) in enumerate(dele, 1):
        titel = args.titel if len(dele) == 1 else f"{args.titel} (del {i}/{len(dele)} · s. {fra}–{til})"
        if scannet:
            res = nlm_json("source", "add", nb, "--file", str(maal), "--title", titel, "--wait")
        else:
            # som .txt-fil: store tekster kan ikke sendes som kommandolinje-argument (ARG_MAX ~1 MB)
            tekst = f"{args.titel}\n\n" + "\n\n".join(f"--- Side {n} ---\n{sider[n - 1]}" for n in range(fra, til + 1))
            txt = ROD / ".cache" / "boeger" / f"{normaliser(args.titel)[:50]}_del{i}.txt"
            txt.parent.mkdir(parents=True, exist_ok=True)
            txt.write_text(tekst)
            res = nlm_json("source", "add", nb, "--file", str(txt), "--title", titel, "--wait")
        ids.append(find_id(res) or "ukendt")
        del_info.append({"titel": titel, "fra_side": fra, "til_side": til})
        print(f"  ✓ {titel}")

    manifest[noegle] = {
        "sti": str(maal.relative_to(kilder)),
        "navn": args.titel,
        "updated_at": None,
        "stoerrelse": maal.stat().st_size,
        "modul": "Bøger",
        "notebooklm_source_id": ids[0],
        "notebooklm_source_ids": ids,
        "dele": del_info,
    }
    manifest_sti.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
