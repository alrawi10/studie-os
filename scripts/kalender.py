#!/usr/bin/env python3
"""Studieplanlægger oven på Apple Kalender (Motion-lignende).

Læser optaget tid fra kalenderne i config/planlaegning.json (fx universitetsskemaet, hvor kun
klinik/obligatorisk tæller, samt arbejde og privat) og lægger læseblokke for opgaverne i
planlaegning/opgaver.json ind i kalenderen "Studieplan".

Kommandoer:
    kalender.py optaget [--dage 7]         vis optaget tid
    kalender.py planlaeg [--dage 7]        vis forslag til plan (skriver intet)
    kalender.py planlaeg --skriv           erstat fremtidige blokke i Studieplan med den nye plan

Tidligere planlagte blokke, der er overstået, antages gennemført og trækkes fra opgavens
rest_minutter (Motion-princippet). "Nåede ikke" håndteres ved at lægge minutterne til igen.

Brug:
    uv run --with python-dateutil scripts/kalender.py planlaeg
"""
import argparse
import json
import subprocess
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr

ROD = Path(__file__).resolve().parent.parent
CFG = json.loads((ROD / "config" / "planlaegning.json").read_text())
OPGAVER = ROD / "planlaegning" / "opgaver.json"
DK = ZoneInfo("Europe/Copenhagen")
US, RS = "\x1f", "\x1e"  # felt- og postseparator i AppleScript-output
MARKOER = "[auto-studieplan]"


def osa(script):
    r = subprocess.run(["osascript", "-"], input=script, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.rstrip("\n")


def as_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------- læs kalendere ----------

def til_minut(t):
    """AppleScript-tider regnes som sekunder fra 'nu' og kan være ±1 s skæve – rund til nærmeste minut."""
    return (t + timedelta(seconds=30)).replace(second=0, microsecond=0)

def hent_begivenheder(fra, til, kalendere=None):
    """Returnerer liste af dicts {kal, start, slut, titel, heldag, noter} i lokal tid.

    Kalendere med reglen "optaget" (små, private) læses helt, så gentagne aftaler kommer med;
    øvrige (KU-abonnementet, Studieplan) læses kun i datointervallet.
    """
    nu = datetime.now(timezone.utc)
    kalendere = kalendere or list(CFG["kalendere"])
    kal = "{" + ", ".join(as_str(k) for k in kalendere) + "}"
    fuld = "{" + ", ".join(as_str(k) for k, r in CFG["kalendere"].items() if r == "optaget") + "}"
    script = f"""
set nu to current date
set t0 to nu + ({int((fra - nu).total_seconds())})
set t1 to nu + ({int((til - nu).total_seconds())})
set US to ASCII character 31
set RS to ASCII character 30
set out to ""
repeat with n in {kal}
  set n to n as string
  -- én samlet forespørgsel pr. kalender (Kalender-appen er langsom pr. forespørgsel på abonnementer)
  tell application "Calendar"
    if not (exists calendar n) then
      set pL to {{}}
    else if {fuld} contains n then
      set pL to properties of every event of calendar n
    else
      set pL to properties of (every event of calendar n whose start date ≥ t0 and start date ≤ t1)
    end if
  end tell
  using terms from application "Calendar"
  repeat with p in pL
    set r to ""
    try
      set r to recurrence of p
    end try
    if r is missing value then set r to ""
    set d to ""
    try
      set d to description of p
    end try
    if d is missing value then set d to ""
    if length of d > 300 then set d to text 1 thru 300 of d
    set s to start date of p
    if r is not "" or (s ≥ t0 and s ≤ t1) then
      set out to out & n & US & ((s - nu) as integer) & US & (((end date of p) - nu) as integer) & US & (summary of p) & US & (allday event of p) & US & r & US & d & RS
    end if
  end repeat
  end using terms from
end repeat
return out
"""
    ud = []
    for post in osa(script).split(RS):
        if not post.strip():
            continue
        kal, s, e, titel, heldag, rrule, noter = (post.split(US) + [""] * 7)[:7]
        start = til_minut((nu + timedelta(seconds=int(s))).astimezone(DK))
        slut = til_minut((nu + timedelta(seconds=int(e))).astimezone(DK))
        base = dict(kal=kal.strip(), titel=titel, heldag=heldag.strip() == "true", noter=noter)
        if rrule:
            varighed = slut - start
            for forekomst in rrulestr(rrule, dtstart=start).between(fra - varighed, til, inc=True):
                ud.append(base | dict(start=forekomst, slut=forekomst + varighed))
        else:
            ud.append(base | dict(start=start, slut=slut))
    return ud


def er_optaget(b):
    regel = CFG["kalendere"].get(b["kal"], "ignorer")
    if regel == "optaget":
        return True
    if regel == "kun_klinik_og_obligatorisk":
        tekst = f"{b['titel']} {b['noter']}".lower()
        return any(ord_ in tekst for ord_ in CFG["ku_optaget_hvis_indeholder"])
    return False


def optagede_intervaller(fra, til):
    buf = timedelta(minutes=CFG["buffer_omkring_optaget_min"])
    iv = []
    for b in hent_begivenheder(fra, til):
        if not er_optaget(b):
            continue
        if b["heldag"]:
            dag0 = datetime.combine(b["start"].date(), time(0), DK)
            iv.append((dag0, dag0 + timedelta(days=max(1, (b["slut"].date() - b["start"].date()).days)), b))
        else:
            iv.append((b["start"] - buf, b["slut"] + buf, b))
    return sorted(iv, key=lambda x: x[0])


# ---------- planlægning ----------

def hhmm(s):
    h, m = map(int, s.split(":"))
    return time(h, m)


def ledige_huller(dag, optaget, tidligst):
    start = max(datetime.combine(dag, hhmm(CFG["dag_start"]), DK), tidligst)
    slut = datetime.combine(dag, hhmm(CFG["dag_slut"]), DK)
    huller, t = [], start
    for a, b, _ in optaget:
        if b <= t or a >= slut:
            continue
        if a > t:
            huller.append((t, min(a, slut)))
        t = max(t, b)
    if t < slut:
        huller.append((t, slut))
    minimum = timedelta(minutes=CFG["min_blok_min"])
    return [(a, b) for a, b in huller if b - a >= minimum]


def indlaes_opgaver():
    if OPGAVER.exists():
        return json.loads(OPGAVER.read_text())
    return {"opgaver": [], "blokke": []}


def bogfoer_overstaaede(data, nu):
    """Påbegyndte/overståede, ikke-bogførte blokke trækkes fra opgavernes rest (antages gennemført)."""
    opg = {o["id"]: o for o in data["opgaver"]}
    for blok in data["blokke"]:
        start = datetime.fromisoformat(blok["start"]).replace(tzinfo=DK)
        slut = datetime.fromisoformat(blok["slut"]).replace(tzinfo=DK)
        if not blok.get("bogfoert") and start <= nu and blok["opgave_id"] in opg:
            o = opg[blok["opgave_id"]]
            minutter = (slut - start).seconds // 60
            o["rest_minutter"] = max(0, o["rest_minutter"] - minutter)
            if o["rest_minutter"] == 0:
                o["status"] = "faerdig"
            blok["bogfoert"] = True
    data["blokke"] = [b for b in data["blokke"] if b.get("bogfoert")]  # fremtidige planlægges forfra


def lav_plan(data, dage, laaste=()):
    """laaste: Studieplan-blokke, der allerede er begyndt i dag. De flyttes ikke og tæller som optaget."""
    nu = datetime.now(DK)
    tidligst = (nu + timedelta(minutes=15)).replace(second=0, microsecond=0)
    tidligst += timedelta(minutes=(-tidligst.minute) % 15)  # rund op til kvarter
    horisont = datetime.combine(nu.date() + timedelta(days=dage), time(23, 59), DK)
    optaget = optagede_intervaller(nu - timedelta(days=1), horisont)
    pause_td = timedelta(minutes=CFG["pause_min"])
    optaget = sorted(optaget + [(b["start"], b["slut"] + pause_td, b) for b in laaste], key=lambda x: x[0])
    anki_dage = {b["start"].date() for b in laaste if "Anki" in b["titel"]}

    aabne = [dict(o) for o in data["opgaver"] if o["status"] != "faerdig" and o["rest_minutter"] > 0]
    aabne.sort(key=lambda o: (o.get("deadline") or "9999-12-31", o.get("prioritet", 2)))
    blok, pause = timedelta(minutes=CFG["bloklaengde_min"]), timedelta(minutes=CFG["pause_min"])
    plan = []

    for d in range(dage + 1):
        dag = nu.date() + timedelta(days=d)
        if dag.weekday() in CFG["fri_dage"]:
            continue
        brugt = 0
        huller = ledige_huller(dag, optaget, tidligst)
        anki_mangler = CFG["anki_min_dagligt"] > 0 and dag not in anki_dage
        for a, b in huller:
            t = a
            if anki_mangler and b - t >= timedelta(minutes=CFG["anki_min_dagligt"]):
                slut = t + timedelta(minutes=CFG["anki_min_dagligt"])
                plan.append(dict(opgave_id=None, titel="🔁 Anki-repetition", start=t, slut=slut))
                t, anki_mangler = slut + pause, False
            while aabne and brugt < CFG["max_studie_min_pr_dag"]:
                o = aabne[0]
                if o.get("deadline") and dag > date.fromisoformat(o["deadline"]):
                    o["forsinket"] = True
                laengde = min(blok, b - t, timedelta(minutes=o["rest_minutter"]),
                              timedelta(minutes=CFG["max_studie_min_pr_dag"] - brugt))
                if laengde <= timedelta(0):
                    break
                if laengde < timedelta(minutes=CFG["min_blok_min"]) and laengde < timedelta(minutes=o["rest_minutter"]):
                    break
                titel = f"📚 {o['fag']}: {o['titel']}" if o.get("fag") else f"📚 {o['titel']}"
                plan.append(dict(opgave_id=o["id"], titel=titel, start=t, slut=t + laengde, forsinket=o.get("forsinket", False)))
                minutter = int(laengde.total_seconds() // 60)
                o["rest_minutter"] -= minutter
                brugt += minutter
                t += laengde + pause
                if o["rest_minutter"] <= 0:
                    aabne.pop(0)
                if b - t < timedelta(minutes=CFG["min_blok_min"]):
                    break
    return plan, aabne, optaget


# ---------- skriv til Studieplan ----------

def skriv_plan(plan):
    nu = datetime.now(timezone.utc)
    kal = as_str(CFG["studiekalender"])
    linjer = [f"""set nu to current date
tell application "Calendar"
  set k to calendar {kal}
  set gamle to (every event of k whose start date ≥ nu)
  repeat with e in gamle
    set d to ""
    try
      set d to description of e
    end try
    if d is not missing value and d contains {as_str(MARKOER)} then delete e
  end repeat"""]
    for p in plan:
        s = int((p["start"] - nu).total_seconds())
        e = int((p["slut"] - nu).total_seconds())
        noter = f"{MARKOER} opgave={p['opgave_id'] or 'anki'}"
        linjer.append(f"  make new event at end of events of k with properties "
                      f"{{summary:{as_str(p['titel'])}, start date:(nu + ({s})), end date:(nu + ({e})), description:{as_str(noter)}}}")
    linjer.append("end tell")
    osa("\n".join(linjer))


def vis_plan(plan, rest):
    dag = None
    for p in plan:
        if p["start"].date() != dag:
            dag = p["start"].date()
            print(f"\n{p['start']:%A %d/%m}")
        advarsel = "  ⚠️ efter deadline" if p.get("forsinket") else ""
        print(f"  {p['start']:%H:%M}–{p['slut']:%H:%M}  {p['titel']}{advarsel}")
    if rest:
        print("\nIkke plads i horisonten:")
        for o in rest:
            print(f"  - {o['titel']} ({o['rest_minutter']} min tilbage, deadline {o.get('deadline') or '–'})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kommando", choices=["optaget", "planlaeg"])
    p.add_argument("--dage", type=int, default=CFG["horisont_dage"])
    p.add_argument("--skriv", action="store_true", help="skriv planen i Studieplan-kalenderen")
    p.add_argument("--stille", action="store_true", help="kun statuslinje (til automatisk kørsel)")
    args = p.parse_args()

    if args.kommando == "optaget":
        nu = datetime.now(DK)
        for a, b, bg in optagede_intervaller(nu, nu + timedelta(days=args.dage)):
            print(f"  {bg['start']:%a %d/%m %H:%M}–{bg['slut']:%H:%M}  [{bg['kal']}] {bg['titel']}")
        return

    nu = datetime.now(DK)
    data = indlaes_opgaver()
    bogfoer_overstaaede(data, nu)
    dagstart = datetime.combine(nu.date(), time(0), DK)
    studie = [b for b in hent_begivenheder(dagstart, nu + timedelta(days=args.dage + 1), [CFG["studiekalender"]])
              if MARKOER in b["noter"]]
    laaste = [b for b in studie if b["start"] <= nu]
    plan, rest, _ = lav_plan(data, args.dage, laaste)
    if not args.stille:
        vis_plan(plan, rest)
    if args.skriv:
        nuvaerende = sorted((b["titel"], b["start"].strftime("%Y-%m-%dT%H:%M"), b["slut"].strftime("%H:%M"))
                            for b in studie if b["start"] > nu)
        ny = sorted((p["titel"], p["start"].strftime("%Y-%m-%dT%H:%M"), p["slut"].strftime("%H:%M")) for p in plan)
        aendret = nuvaerende != ny
        if aendret:
            skriv_plan(plan)
        data["blokke"] += [dict(opgave_id=p["opgave_id"], start=p["start"].strftime("%Y-%m-%dT%H:%M"),
                                slut=p["slut"].strftime("%Y-%m-%dT%H:%M"), bogfoert=False)
                           for p in plan if p["opgave_id"]]
        OPGAVER.parent.mkdir(exist_ok=True)
        OPGAVER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        status = f"{len(plan)} blokke skrevet" if aendret else "plan uændret – intet skrevet"
        print(f"{nu:%Y-%m-%d %H:%M} ✓ {status} ({CFG['studiekalender']})")
    else:
        print("\n(forslag – intet skrevet; brug --skriv)")


if __name__ == "__main__":
    main()
