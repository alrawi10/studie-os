---
name: fejlanalyse
description: Bruges når brugeren vil finde og arbejde med sine svage emner i odontologi ud fra Anki-statistik (lapses, FSRS-difficulty)
---

# Fejlanalyse ud fra Anki

## 1. Find de svære kort (sidste 30 dage)
Brug MCP `anki` (Anki skal være åben):
- `find_notes` med disse søgninger (kør hver for sig, og saml note-id'erne):
  - `deck:Odontologi::* rated:30:1`: kort svaret "Igen" inden for 30 dage
  - `deck:Odontologi::* prop:lapses>=3`: mange lapses
  - `deck:Odontologi::* prop:d>0.7`: høj FSRS-difficulty (kun hvis FSRS er slået til; ellers `prop:ease<2.1`)
- `notes_info` → felter og tags. Evt. `cards_stats` (deck `Odontologi`) for interval og kø, og
  `get_card_memory_state` for difficulty/stability på de udvalgte kort.

## 2. Gruppér og log
- Gruppér efter `fag::` og `emne::`-tags. Kort uden emne-tag grupperes under deck-navnets sidste led.
- Rangér emner efter (antal "Igen" + lapses) og gennemsnitlig difficulty.
- Opdatér `fag/<fag>/fejllog.md`: én række pr. emne i tabellen
  `| Emne | Kort m. lapses | Seneste analyse | Status |` (dato ÅÅÅÅ-MM-DD, status: `ny`/`i gang`/`bedre`).
  Eksisterende rækker opdateres i stedet for at blive duplikeret.

## 3. For de 3 svageste emner
1. **Kort forklaring** (5–10 linjer) via NotebookLM (`notebook_query` på fagets notebook fra
   `config/fag.json`) med citater. Fokus på det, kortene viser, at der er misforstået.
2. **5 åbne eksamensspørgsmål** (hvorfor/hvordan/sammenlign/begrund klinisk). Ingen ja/nej.
3. **Kortkritik:** Vurder de svære kort mod `config/kortregler.md`. Er et kort dårligt formuleret
   (flere fakta, tvetydigt, for lang bagside), så foreslå en omformulering eller opdeling som tabel.
   Ændringer i Anki (`update_note_fields` / nye kort via `anki-kort`) laves først efter brugerens **ok**.
   Slet aldrig kort. Foreslå højst at suspendere dem.

## Output
Kort rapport: top-emner med tal → forklaringer → spørgsmål → foreslåede kortændringer.
Gem forklaring og spørgsmål under emnets række i `fejllog.md` (sektion `## <emne> (<dato>)`).
