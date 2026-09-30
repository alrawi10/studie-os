#!/usr/bin/env python3
"""Pakker studiesystemet til brug uden for Claude Code (Chat, Projekter og Cowork i Claude).

Bygger i dist/:
  skills/<navn>.zip          upload i Claude → Tilpas → Skills → Tilføj (én zip pr. skill)
  projekt-instruktioner.md   indsæt i et Claude-projekt (Instruktioner) eller i Cowork
Kortreglerne lægges med i skills (references/kortregler.md), så de virker uden projektmappen.

Brug:  python3 scripts/pak_portable.py
"""
import json
import re
import shutil
import zipfile
from pathlib import Path

ROD = Path(__file__).resolve().parent.parent
DIST = ROD / "dist"


def hvem_jeg_er():
    for fil in ("CLAUDE.md", "CLAUDE.example.md"):
        p = ROD / fil
        if p.exists():
            m = re.search(r"## Hvem jeg er\n(.*?)(?=\n## )", p.read_text(), re.S)
            if m:
                return m.group(1).strip()
    return "<Uddannelse> på <universitet>. Jeg foretrækker dybe, præcise forklaringer forankret i pensum."


def fag_tabel(cfg):
    fag = cfg.get("fag", {})
    if not fag:
        return "(Udfyld: fag, kursusnavn, NotebookLM-notebook og Anki-deck.)"
    linjer = ["| Fag (kort navn) | Kursus | NotebookLM-notebook | Anki-deck |", "|---|---|---|---|"]
    for navn, i in fag.items():
        linjer.append(f"| {navn} | {i.get('kursusnavn', '')} | {i.get('notebook_titel', '')} | `{i.get('anki_deck', '')}` |")
    return "\n".join(linjer)


def main():
    cfg_sti = ROD / "config" / "fag.json"
    cfg = json.loads(cfg_sti.read_text()) if cfg_sti.exists() else json.loads((ROD / "config" / "fag.example.json").read_text())
    studie = cfg.get("studie", "Studie")

    shutil.rmtree(DIST, ignore_errors=True)
    (DIST / "skills").mkdir(parents=True)
    kortregler = (ROD / "config" / "kortregler.md").read_text()
    for skill in sorted((ROD / ".claude" / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        forside = (skill / "SKILL.md").read_text().split("---")[1]
        if re.search(r"[<>]", forside):  # claude.ai afviser XML-lignende tegn i name/description
            raise SystemExit(f"❌ {skill.name}/SKILL.md: frontmatter må ikke indeholde < eller >")
        with zipfile.ZipFile(DIST / "skills" / f"{skill.name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in skill.rglob("*"):
                if f.is_file():
                    z.write(f, f"{skill.name}/{f.relative_to(skill)}")
            if skill.name in ("anki-kort", "fejlanalyse"):
                z.writestr(f"{skill.name}/references/kortregler.md", kortregler)
        print(f"✓ dist/skills/{skill.name}.zip")

    nlm = Path.home() / ".local" / "bin" / "nlm"  # NotebookLM-værktøjets egen skill (hvordan NotebookLM bruges)
    if nlm.exists():
        import subprocess
        r = subprocess.run([str(nlm), "skill", "package", "--output", str(DIST / "skills")], capture_output=True, text=True)
        print("✓ dist/skills/nlm-skill.zip" if r.returncode == 0 else "⚠️  nlm-skill kunne ikke pakkes (valgfri)")

    skabelon = (ROD / "portable" / "projekt-instruktioner.md").read_text()
    tekst = skabelon.replace("{{STUDIE}}", studie).replace("{{HVEM}}", hvem_jeg_er()).replace("{{FAG_TABEL}}", fag_tabel(cfg))
    (DIST / "projekt-instruktioner.md").write_text(tekst)
    print("✓ dist/projekt-instruktioner.md")
    print("\nNæste skridt: Claude → Tilpas → Skills → Tilføj (upload hver zip), og indsæt instruktionerne i et projekt/Cowork.")


if __name__ == "__main__":
    main()
