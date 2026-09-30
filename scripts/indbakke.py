#!/usr/bin/env python3
"""Indbakke via Apple Påmindelser: ting dikteret til Siri ("Tilføj … til Påmindelser") behandles af Claude.

Kommandoer:
    indbakke.py hent            ubehandlede punkter som JSON
    indbakke.py status          én linje til session-start (antal ubehandlede punkter)
    indbakke.py afslut ID ...   afkryds behandlede punkter (sletter intet)

Listens navn kan ændres med miljøvariablen INDBAKKE_LISTE (standard "Påmindelser").
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

LISTE = os.environ.get("INDBAKKE_LISTE", "Påmindelser")
DK = ZoneInfo("Europe/Copenhagen")
US, RS = "\x1f", "\x1e"


def osa(script):
    r = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.rstrip("\n")


def as_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def hent():
    nu = datetime.now(timezone.utc)
    ud = osa(f"""
set nu to current date
set US to ASCII character 31
set RS to ASCII character 30
set out to ""
tell application "Reminders"
  if not (exists list {as_str(LISTE)}) then return ""
  set pL to properties of (every reminder of list {as_str(LISTE)} whose completed is false)
end tell
using terms from application "Reminders"
  repeat with p in pL
    set b to body of p
    if b is missing value then set b to ""
    set f to due date of p
    if f is missing value then
      set fs to ""
    else
      set fs to ((f - nu) as integer) as string
    end if
    set out to out & (id of p) & US & (name of p) & US & b & US & (((creation date of p) - nu) as integer) & US & fs & RS
  end repeat
end using terms from
return out
""")
    punkter = []
    for post in ud.split(RS):
        if not post.strip():
            continue
        rid, tekst, noter, oprettet, forfald = (post.split(US) + [""] * 5)[:5]
        tid = lambda s: (nu + timedelta(seconds=int(s))).astimezone(DK).strftime("%Y-%m-%dT%H:%M")
        punkter.append({"id": rid.strip(), "tekst": tekst.strip(), "noter": noter.strip(),
                        "oprettet": tid(oprettet), "forfald": tid(forfald) if forfald.strip() else None})
    return sorted(punkter, key=lambda p: p["oprettet"])


def afslut(ids):
    linjer = [f'tell application "Reminders"']
    for rid in ids:
        linjer.append(f"  set completed of (first reminder of list {as_str(LISTE)} whose id is {as_str(rid)}) to true")
    linjer.append("end tell")
    osa("\n".join(linjer))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("hent", "status", "afslut"):
        sys.exit(__doc__)
    if sys.argv[1] == "afslut":
        afslut(sys.argv[2:])
        print(f"✓ {len(sys.argv) - 2} punkt(er) afkrydset i '{LISTE}'.")
        return
    try:
        punkter = hent()
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        if sys.argv[1] == "status":
            return  # session-start må aldrig fejle højlydt
        raise SystemExit(f"Kunne ikke læse Påmindelser: {e}")
    if sys.argv[1] == "status":
        if punkter:
            print(f"📥 Indbakke: {len(punkter)} ubehandlede punkt(er) i Påmindelser › {LISTE}: "
                  + "; ".join(p["tekst"] for p in punkter[:5])
                  + (" …" if len(punkter) > 5 else "")
                  + ". Nævn det for brugeren og tilbyd at køre 'indbakke'.")
        return
    print(json.dumps(punkter, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
