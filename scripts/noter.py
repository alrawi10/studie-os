#!/usr/bin/env python3
"""Egne noter i Obsidian (Markdown i fag/<Fag>/noter/) – læses og suppleres af Claude.

Regel: brugerens egen tekst ændres ALDRIG. Claude skriver kun mellem markørerne
<!-- claude:start --> og <!-- claude:end --> nederst i noten (erstattes ved hver opdatering).

Kommandoer:
    noter.py liste [--fag Parodontologi]
    noter.py opret --fag Parodontologi --emne "F4 Patogenese" [--kilde "F4 Parodontitis.pdf" ...]
    noter.py laes --fag Parodontologi --emne "F4"            (finder noten på delvist navn)
    noter.py supplement --fag Parodontologi --emne "F4" --fil supplement.md
    noter.py marker --fag Parodontologi --emne "F4" [--svag ja|nej] [--status læser|læst|repeteret]
    noter.py link --fag Parodontologi --emne "F4"            (obsidian://-link til noten)
"""
import argparse
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROD = Path(__file__).resolve().parent.parent
VAULT = ROD / "fag"  # Obsidian-vault = fag/ (noter, pensum-PDF'er, eksamenssvar og fejllog samlet)
START, SLUT = "<!-- claude:start -->", "<!-- claude:end -->"
SKABELON = ROD / "portable" / "obsidian" / "Emne.md"


def _norm(s):
    s = unicodedata.normalize("NFC", s).lower()
    return re.sub(r"[^a-zæøå0-9]+", "", s)


def noter_mappe(fag):
    if not (VAULT / fag).is_dir():
        kendte = ", ".join(p.name for p in VAULT.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
        raise SystemExit(f"Ukendt fag '{fag}'. Kendte fag: {kendte}")
    m = VAULT / fag / "noter"
    m.mkdir(exist_ok=True)
    return m


def find(fag, emne):
    """Finder en note på (delvist) navn. Returnerer stien eller None."""
    soeg = _norm(emne)
    noter = sorted(noter_mappe(fag).rglob("*.md"))
    eksakt = [n for n in noter if _norm(n.stem) == soeg]
    if eksakt:
        return eksakt[0]
    delvis = [n for n in noter if soeg in _norm(n.stem)]
    return min(delvis, key=lambda n: len(n.stem)) if delvis else None


def opret(fag, emne, kilder=()):
    eksisterende = find(fag, emne)
    if eksisterende and _norm(eksisterende.stem) == _norm(emne):
        return eksisterende, False
    sti = noter_mappe(fag) / (re.sub(r'[\\/:*?"<>|]', "-", emne).strip() + ".md")
    tekst = SKABELON.read_text() if SKABELON.exists() else "# {{title}}\n\n## Mine noter\n\n" + START + "\n" + SLUT + "\n"
    kilde_yaml = "".join(f'\n  - "{k}"' for k in kilder) or " []"
    tekst = (tekst.replace("{{title}}", emne).replace("{{date}}", date.today().isoformat())
             .replace("{{fag}}", fag).replace("kilder: []", f"kilder:{kilde_yaml}"))
    sti.write_text(tekst)
    return sti, True


def del_op(tekst):
    """(brugerens tekst, Claudes sektion) – Claudes sektion er tom, hvis markørerne mangler."""
    if START in tekst and SLUT in tekst:
        før, rest = tekst.split(START, 1)
        claude, efter = rest.split(SLUT, 1)
        return før.rstrip() + ("\n\n" + efter.strip() if efter.strip() else ""), claude.strip()
    return tekst.rstrip(), ""


def skriv_supplement(sti, markdown):
    """Erstatter Claudes sektion; brugerens tekst bevares byte for byte."""
    tekst = sti.read_text()
    if START in tekst and SLUT in tekst:
        før, rest = tekst.split(START, 1)
        _, efter = rest.split(SLUT, 1)
        ny = f"{før}{START}\n{markdown.strip()}\n{SLUT}{efter}"
    else:
        ny = f"{tekst.rstrip()}\n\n{START}\n{markdown.strip()}\n{SLUT}\n"
    assert del_op(ny)[0] == del_op(tekst)[0], "brugerens tekst ville blive ændret – afbrudt"
    sti.write_text(ny)


def saet_frontmatter(sti, felt, vaerdi):
    tekst = sti.read_text()
    if tekst.startswith("---\n") and "\n---" in tekst[4:]:
        slut = tekst.index("\n---", 4)
        hoved, krop = tekst[4:slut], tekst[slut:]
        if re.search(rf"^{felt}:.*$", hoved, re.M):
            hoved = re.sub(rf"^{felt}:.*$", f"{felt}: {vaerdi}", hoved, flags=re.M)
        else:
            hoved += f"\n{felt}: {vaerdi}"
        sti.write_text(f"---\n{hoved}{krop}")
    else:
        sti.write_text(f"---\n{felt}: {vaerdi}\n---\n{tekst}")


def obsidian_link(sti):
    rel = sti.relative_to(VAULT).with_suffix("")
    return f"obsidian://open?vault={quote(VAULT.name)}&file={quote(str(rel))}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kommando", choices=["liste", "opret", "laes", "supplement", "marker", "link"])
    p.add_argument("--fag")
    p.add_argument("--emne")
    p.add_argument("--kilde", action="append", default=[])
    p.add_argument("--fil", help="Markdown med Claudes supplement (til 'supplement')")
    p.add_argument("--svag", choices=["ja", "nej"])
    p.add_argument("--status", choices=["læser", "læst", "repeteret"])
    a = p.parse_args()

    if a.kommando == "liste":
        fag = [a.fag] if a.fag else sorted(d.name for d in VAULT.iterdir() if (d / "noter").is_dir())
        for f in fag:
            noter = sorted(noter_mappe(f).rglob("*.md"))
            print(f"{f}: {len(noter)} noter")
            for n in noter:
                _, claude = del_op(n.read_text())
                print(f"   - {n.stem}{'  [suppleret]' if claude else ''}")
        return
    if not (a.fag and a.emne):
        sys.exit("--fag og --emne skal angives")
    if a.kommando == "opret":
        sti, ny = opret(a.fag, a.emne, a.kilde)
        print(f"{'Oprettet' if ny else 'Findes allerede'}: {sti}\n{obsidian_link(sti)}")
        return
    sti = find(a.fag, a.emne)
    if not sti:
        sys.exit(f"Ingen note om '{a.emne}' i {a.fag}/noter/ – opret den med: noter.py opret --fag {a.fag} --emne \"{a.emne}\"")
    if a.kommando == "laes":
        egen, claude = del_op(sti.read_text())
        print(f"# Fil: {sti.relative_to(ROD)}\n\n## BRUGERENS EGEN TEKST\n{egen}\n\n## CLAUDES NUVÆRENDE SEKTION\n{claude or '(ingen endnu)'}")
    elif a.kommando == "supplement":
        skriv_supplement(sti, Path(a.fil).read_text() if a.fil else sys.stdin.read())
        print(f"✓ Supplement opdateret i {sti.relative_to(ROD)} (din egen tekst er uændret)")
    elif a.kommando == "marker":
        if a.svag:
            saet_frontmatter(sti, "svag", "true" if a.svag == "ja" else "false")
        if a.status:
            saet_frontmatter(sti, "status", a.status)
        print(f"✓ {sti.stem}: " + ", ".join(f"{k} = {v}" for k, v in (("svag", a.svag), ("status", a.status)) if v))
    elif a.kommando == "link":
        print(obsidian_link(sti))


if __name__ == "__main__":
    main()
