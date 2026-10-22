#!/usr/bin/env python3
"""MCP-server "studie": projektets lokale værktøjer til Claude Desktop (Chat og Cowork).

Giver sync, deadlines, kalenderplanlægning, opgaver, Siri-indbakke og figurer fra pensum-PDF'er
som værktøjer – så det, der ellers kræver Claude Code, også virker i Desktop-appen.
Er et tyndt lag oven på scripts/ (ingen dobbelt logik).

Registrering (macOS, Claude Desktop lukket): scripts/desktop_mcp.sh
Manuel test:  uv run --python 3.12 --with "mcp>=2.2,<3" ... scripts/studie_mcp.py   (taler stdio)
"""
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from mcp.server.mcpserver import Image, MCPServer

ROD = Path(__file__).resolve().parent.parent
SCRIPTS = ROD / "scripts"
CACHE = ROD / ".cache"
OPGAVER = ROD / "planlaegning" / "opgaver.json"
MILJOE = {**os.environ, "PATH": f"{Path.home()}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"}

server = MCPServer(
    "studie",
    instructions=(
        "Lokale værktøjer til brugerens studiesystem (Absalon/LMS → NotebookLM → Anki, Apple Kalender, Siri-indbakke). "
        "Svar på dansk. Kør altid planlaeg(skriv=False) og vis planen, før du skriver i kalenderen, medmindre brugeren "
        "har bedt om det. Kortregler til Anki-kort: kald kortregler()."
    ),
)


def koer(*args, timeout=300):
    """Kør et script med samme Python-miljø som serveren (har alle afhængigheder)."""
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROD, capture_output=True, text=True,
                       timeout=timeout, env=MILJOE)
    ud = r.stdout.strip()
    if r.returncode:
        ud += f"\n[fejl, kode {r.returncode}] {r.stderr.strip()[-1500:]}"
    return ud[-8000:] or "(intet output)"


def laes_opgaver():
    return json.loads(OPGAVER.read_text()) if OPGAVER.exists() else {"opgaver": [], "blokke": []}


def gem_opgaver(data):
    OPGAVER.parent.mkdir(exist_ok=True)
    OPGAVER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------- fag og regler ----------

@server.tool(description="Fagene i studiesystemet (kort navn, kursusnavn, NotebookLM-notebook-id, Anki-deck) og antal filer pr. fag.")
def fag() -> str:
    cfg = json.loads((ROD / "config" / "fag.json").read_text())
    for navn, info in cfg.get("fag", {}).items():
        m = ROD / "fag" / navn / "kilder" / ".manifest.json"
        info["antal_filer"] = len(json.loads(m.read_text())) if m.exists() else 0
    return json.dumps(cfg, indent=1, ensure_ascii=False)


@server.tool(description="De bindende regler for Anki-kort (skal læses før der laves kort).")
def kortregler() -> str:
    return (ROD / "config" / "kortregler.md").read_text()


# ---------- sync og deadlines ----------

@server.tool(description="Start synkronisering: nye/ændrede filer fra universitetets LMS → fag/<fag>/kilder/ → NotebookLM. "
                         "Kører i baggrunden (kan tage minutter); følg med sync_status(). Valgfrit kun ét fag (kort navn).")
def sync(fag: str | None = None) -> str:
    pid_fil = CACHE / "sync.pid"
    if pid_fil.exists():
        try:
            os.kill(int(pid_fil.read_text()), 0)
            return "En sync kører allerede – brug sync_status()."
        except (OSError, ValueError):
            pass
    CACHE.mkdir(exist_ok=True)
    cmd = ["/bin/bash", str(SCRIPTS / "sync_all.sh")] + (["--fag", fag] if fag else [])
    with open(CACHE / "sync.log", "w") as log:
        p = subprocess.Popen(cmd, cwd=ROD, stdout=log, stderr=subprocess.STDOUT, env=MILJOE, start_new_session=True)
    pid_fil.write_text(str(p.pid))
    return f"Sync startet{' for ' + fag if fag else ''} (pid {p.pid}). Tjek fremdrift med sync_status()."


@server.tool(description="Status på seneste sync: kører den stadig, og hvilke filer er nye/uploadet/sprunget over.")
def sync_status() -> str:
    log = CACHE / "sync.log"
    if not log.exists():
        return "Ingen sync er kørt fra Desktop endnu."
    koerer = False
    try:
        os.kill(int((CACHE / "sync.pid").read_text()), 0)
        koerer = True
    except (OSError, ValueError, FileNotFoundError):
        pass
    linjer = [l for l in log.read_text().splitlines()
              if re.search(r"^###|^==|I alt|uploadet|sprunget|^  [-+\[]|fejl|udløbet|❌|⚠️", l)]
    return ("⏳ Kører stadig.\n" if koerer else "✅ Færdig.\n") + "\n".join(linjer[-120:])


@server.tool(description="Kommende afleveringer, quizzer og deadlines fra LMS'et (og evt. kalender-feed) de næste N dage.")
def deadlines(dage: int = 14) -> str:
    return koer(SCRIPTS / "deadlines.py", "--dage", dage, timeout=180)


# ---------- planlægning ----------

@server.tool(description="Planlæg læseblokke i Apple Kalender ('Studieplan') ud fra opgaverne, uden om klinik/obligatorisk "
                         "undervisning og andre aftaler. skriv=False viser kun forslaget; skriv=True erstatter de fremtidige blokke.")
def planlaeg(skriv: bool = False, dage: int = 7) -> str:
    args = [SCRIPTS / "kalender.py", "planlaeg", "--dage", dage] + (["--skriv"] if skriv else [])
    return koer(*args, timeout=300)


@server.tool(description="Alle åbne opgaver (id, titel, fag, rest_minutter, deadline, prioritet).")
def opgaver() -> str:
    aabne = [o for o in laes_opgaver()["opgaver"] if o.get("status") != "faerdig"]
    return json.dumps(aabne, indent=1, ensure_ascii=False) if aabne else "Ingen åbne opgaver."


@server.tool(description="Tilføj en opgave til planen. deadline som ÅÅÅÅ-MM-DD (valgfri), prioritet 1 (høj) – 3 (lav). "
                         "Kør bagefter planlaeg() for at få den i kalenderen.")
def opgave_tilfoej(titel: str, minutter: int, fag: str = "", deadline: str | None = None, prioritet: int = 2) -> str:
    if deadline:
        date.fromisoformat(deadline)  # validér formatet
    data = laes_opgaver()
    nr = max([int(o["id"][1:]) for o in data["opgaver"] if re.fullmatch(r"t\d+", o["id"])] + [0]) + 1
    opg = {"id": f"t{nr}", "titel": titel, "fag": fag, "minutter": minutter, "rest_minutter": minutter,
           "deadline": deadline, "prioritet": prioritet, "status": "aaben"}
    data["opgaver"].append(opg)
    gem_opgaver(data)
    return f"Tilføjet: {json.dumps(opg, ensure_ascii=False)}"


@server.tool(description="Opdatér en opgave: status='faerdig' når den er færdig; laeg_til_minutter ved 'nåede ikke' "
                         "(lægger tid tilbage); eller sæt rest_minutter direkte.")
def opgave_opdater(id: str, status: str | None = None, laeg_til_minutter: int = 0, rest_minutter: int | None = None) -> str:
    data = laes_opgaver()
    opg = next((o for o in data["opgaver"] if o["id"] == id), None)
    if not opg:
        return f"Ingen opgave med id {id}."
    if status:
        opg["status"] = status
    if rest_minutter is not None:
        opg["rest_minutter"] = rest_minutter
    if laeg_til_minutter:
        opg["rest_minutter"] += laeg_til_minutter
        opg["status"] = "aaben"
    gem_opgaver(data)
    return f"Opdateret: {json.dumps(opg, ensure_ascii=False)}"


# ---------- Siri-indbakke ----------

@server.tool(description="Ubehandlede punkter brugeren har dikteret til Siri (Påmindelser-indbakken): 'har læst …', "
                         "'skal nå …', 'nåede ikke …' osv. Afkryds dem med indbakke_afslut() når de er behandlet.")
def indbakke() -> str:
    return koer(SCRIPTS / "indbakke.py", "hent", timeout=120)


@server.tool(description="Afkryds behandlede indbakke-punkter (id'er fra indbakke()). Sletter intet.")
def indbakke_afslut(ids: list[str]) -> str:
    return koer(SCRIPTS / "indbakke.py", "afslut", *ids, timeout=120)


# ---------- figurer fra pensum ----------

@server.tool(description="Hent en figur fra pensum til et Anki-kort: side (PDF) eller slide (PPTX) fra en kilde i faget. "
                         "figur=N beskærer automatisk til figur N på siden; beskaer='x0,y0,x1,y1' (brøkdele) manuelt. "
                         "Returnerer billedet, så du kan se det. gem_i_anki=True gemmer det i Anki og giver <img>-HTML til feltet Billede.")
def billede(fag: str, kilde: str, side: int, figur: int | None = None, beskaer: str | None = None,
            gem_i_anki: bool = False) -> list:
    args = [SCRIPTS / "billede.py", "--fag", fag, "--kilde", kilde, "--side", side]
    if figur:
        args += ["--figur", figur]
    if beskaer:
        args += ["--beskaer", beskaer]
    if gem_i_anki:
        args += ["--anki"]
    ud = koer(*args, timeout=180)
    sti = re.search(r"^fil: (.+)$", ud, re.M)
    if not sti:
        return [ud]
    return [Image(path=sti.group(1)), ud]


if __name__ == "__main__":
    server.run()
