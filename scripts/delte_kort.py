#!/usr/bin/env python3
"""Importerede Anki-decks fra andre studerende: saml dem under <Studie>::<Fag> og aktivér kort emne for emne.

Princip: importerede NYE kort sættes på pause (suspenderes) og aktiveres først, når emnet er læst
(`læst …` i Claude vurderer dem mod pensum). Kort, der allerede er i gang, røres ikke. Intet slettes.
Flytning bevarer fremskridt (Anki 26.09+), og de importerede kapitler/underdecks bevares under målet.

Konfiguration: config/delte_decks.json
  [{"kilde": "5. Semester: Farmakologi", "maal": "Odontologi::Farmakologi", "fag": "Farmakologi",
    "aktivering": "emne"}]          # "emne" = aktiveres ved læst; "pause" = forbliver på pause (fx eksamenssæt)

Kommandoer:
  delte_kort.py plan                 vis flytninger og pauser (ændrer intet)
  delte_kort.py udfoer               gennemfør planen
  delte_kort.py kandidater --fag Farmakologi [--deck Smerte] [--soeg "nsaid paracetamol"]
                                     kort på pause, der passer til et emne (JSON til vurdering)
  delte_kort.py aktiver ID [ID ...]  aktivér (unsuspend) valgte kort-id'er
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

ROD = Path(__file__).resolve().parent.parent
KONFIG = ROD / "config" / "delte_decks.json"
PLAN = ROD / ".cache" / "delte_plan.json"
ANKI = "http://127.0.0.1:3141/"


# ---------- Anki ----------

def anki(navn, **args):
    try:
        r = requests.post(ANKI, timeout=300, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                    "params": {"name": navn, "arguments": args}},
                          headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    except requests.ConnectionError:
        sys.exit("❌ Kan ikke forbinde til Anki – åbn Anki (med AnkiMCP-add-on'et) og prøv igen.")
    tekst = r.content.decode("utf-8")
    svar = next((json.loads(l[5:]) for l in tekst.splitlines() if l.startswith("data:")), None) or r.json()
    if "error" in svar:
        raise RuntimeError(f"{navn}: {svar['error']}")
    res = svar["result"]
    if res.get("isError"):
        raise RuntimeError(f"{navn}: {' '.join(c.get('text', '') for c in res.get('content', []))[:300]}")
    if res.get("structuredContent"):
        return res["structuredContent"]
    txt = "\n".join(c.get("text", "") for c in res.get("content", []))
    try:
        return json.loads(txt)
    except ValueError:
        return txt


def kort_i_deck(deck):
    """Alle kort i decket inkl. underdecks: [{cid, nid, type, queue, ...}]."""
    ud, off = [], 0
    while True:
        r = anki("cards_stats", deck=deck, limit=1000, offset=off)
        blok = r.get("cards", [])
        ud += blok
        if len(blok) < 1000:
            return ud
        off += 1000


def i_bidder(liste, n=400):
    for i in range(0, len(liste), n):
        yield liste[i:i + n]


def ren(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (t or "").replace("&nbsp;", " "))).strip()


# ---------- plan og udførelse ----------

def laes_konfig():
    if not KONFIG.exists():
        sys.exit(f"Mangler {KONFIG.relative_to(ROD)} – se config/delte_decks.example.json")
    return json.loads(KONFIG.read_text())


def lav_plan():
    decks = [d["name"] for d in anki("list_decks")["decks"]]
    plan = []
    for post in laes_konfig():
        kilde, maal = post["kilde"], post["maal"]
        egne = sorted(d for d in decks if d == kilde or d.startswith(kilde + "::"))
        if not egne:
            print(f"⚠️  '{kilde}' findes ikke i Anki (allerede flyttet?) – springes over")
            continue
        # kort direkte i hvert deck = alle kort i decket minus kortene i dets underdecks
        alle = {d: {k["cid"]: k for k in kort_i_deck(d)} for d in egne}
        for d in egne:
            boern = [b for b in egne if b.startswith(d + "::")]
            direkte = dict(alle[d])
            for b in boern:
                for cid in alle[b]:
                    direkte.pop(cid, None)
            if not direkte:
                continue
            nye = [c for c, k in direkte.items() if k.get("type") == 0 and k.get("queue") == 0]
            plan.append({"fra": d, "til": maal + d[len(kilde):], "fag": post["fag"],
                         "oprindelse": re.sub(r"[^a-zæøå0-9]+", "-", kilde.lower()).strip("-"),
                         "kort": list(direkte), "noter": sorted({k["nid"] for k in direkte.values()}),
                         "pause": nye, "i_gang": len(direkte) - len(nye) - sum(1 for k in direkte.values() if k.get("queue") == -1),
                         "aktivering": post.get("aktivering", "emne")})
    return plan


def vis_plan(plan):
    i_alt = sum(len(p["kort"]) for p in plan)
    print(f"Plan: {i_alt} kort i {len(plan)} decks flyttes; {sum(len(p['pause']) for p in plan)} nye kort sættes på pause; "
          f"{sum(p['i_gang'] for p in plan)} kort i gang fortsætter uændret.\n")
    sidste_fag = None
    for p in plan:
        if p["fag"] != sidste_fag:
            sidste_fag = p["fag"]
            print(f"■ {p['fag']}")
        print(f"   {len(p['kort']):4} kort  {p['fra']}\n         → {p['til']}"
              + (f"   ({p['i_gang']} i gang)" if p["i_gang"] else ""))


def udfoer(plan):
    for p in plan:
        for bid in i_bidder(p["kort"]):
            anki("card_change_deck", card_ids=bid, deck=p["til"])
        for bid in i_bidder(p["noter"]):
            anki("tag_add", note_ids=bid, tags=f"kilde::delt delt::{p['oprindelse']} fag::{p['fag'].lower()}")
        for bid in i_bidder(p["pause"]):
            anki("card_suspend", card_ids=bid)
        print(f"✓ {len(p['kort']):4} kort → {p['til']} ({len(p['pause'])} på pause)")
    kfg = laes_konfig()
    for post in kfg:
        post["flyttet"] = date.today().isoformat()
    KONFIG.write_text(json.dumps(kfg, indent=2, ensure_ascii=False) + "\n")


# ---------- aktivering emne for emne ----------

def kandidater(fag, deck_moenster, soeg):
    kfg = [p for p in laes_konfig() if p["fag"].lower() == fag.lower() and p.get("aktivering", "emne") == "emne"]
    if not kfg:
        sys.exit(f"Ingen delte decks med aktivering 'emne' for faget {fag}.")
    decks = [d["name"] for d in anki("list_decks")["decks"]]
    ud = []
    for post in kfg:
        for d in sorted(d for d in decks if d == post["maal"] or d.startswith(post["maal"] + "::")):
            if deck_moenster and deck_moenster.lower() not in d.lower():
                continue
            q = f'"deck:{d}" -"deck:{d}::*" tag:kilde::delt is:suspended'
            if soeg:
                q += " (" + " or ".join(soeg.split()) + ")"
            ids = anki("find_notes", query=q, limit=500).get("noteIds", [])
            if not ids:
                continue
            for n in anki("notes_info", notes=ids)["notes"]:
                felter = list(n["fields"].values())
                tekst = [ren(f["value"]) for f in felter]
                ud.append({"deck": d, "note_id": n["noteId"], "kort_ids": n["cards"], "type": n["modelName"],
                           "forside": tekst[0][:400], "bagside": " | ".join(t for t in tekst[1:] if t)[:600],
                           "billede": any("<img" in (f["value"] or "") for f in felter)})
    print(json.dumps({"antal": len(ud), "kort": ud}, ensure_ascii=False, indent=1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kommando", choices=["plan", "udfoer", "kandidater", "aktiver"])
    p.add_argument("ids", nargs="*", type=int)
    p.add_argument("--fag")
    p.add_argument("--deck", help="del af deck-navnet, fx 'Smerte' eller '3.3'")
    p.add_argument("--soeg", help="nøgleord (OR), fx 'nsaid paracetamol'")
    a = p.parse_args()

    if a.kommando == "plan":
        plan = lav_plan()
        PLAN.parent.mkdir(exist_ok=True)
        PLAN.write_text(json.dumps(plan, ensure_ascii=False))
        vis_plan(plan)
        print("\n(intet ændret – kør 'udfoer' for at gennemføre)")
    elif a.kommando == "udfoer":
        plan = lav_plan()  # altid frisk, så kort ændret siden 'plan' håndteres korrekt
        vis_plan(plan)
        print()
        udfoer(plan)
    elif a.kommando == "kandidater":
        if not a.fag:
            sys.exit("--fag skal angives")
        kandidater(a.fag, a.deck, a.soeg)
    elif a.kommando == "aktiver":
        if not a.ids:
            sys.exit("Angiv kort-id'er")
        r = anki("card_unsuspend", card_ids=a.ids)
        print(f"✓ {r.get('unsuspended_count', len(a.ids))} kort aktiveret")


if __name__ == "__main__":
    main()
