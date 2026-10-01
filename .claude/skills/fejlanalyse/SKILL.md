---
name: fejlanalyse
description: Bruges når brugeren vil finde og arbejde med sine svage emner ud fra Anki-statistik (lapses, "Igen"-svar, FSRS-difficulty) – fx "fejl" eller "hvad har jeg svært ved?". Giver forklaringer fra pensum, eksamensspørgsmål og forslag til bedre kort.
---

# Fejlanalyse ud fra Anki

## 0. Datakilde
- **Anki-værktøjer findes** (`find_notes`, Anki skal være åben): brug trin 1 direkte.
- **Ingen Anki-værktøjer** (fx almindelig chat): bed brugeren eksportere de svære kort:
  Anki → **Gennemse** → søg `deck:<Studie>::* (rated:30:1 OR prop:lapses>=3)` → markér alle (⌘A) →
  **Noter → Eksportér noter** → "Noter i almindelig tekst" med tags → upload filen her. Fortsæt fra trin 2.
- Deck-roden `<Studie>` står som `studie` i `config/fag.json` (projektmappen) – ellers spørg (fx `Odontologi`).

## 1. Find de svære kort (sidste 30 dage)
- `find_notes` med disse søgninger (hver for sig, saml note-id'erne):
  - `deck:<Studie>::* rated:30:1`: kort svaret "Igen" inden for 30 dage
  - `deck:<Studie>::* prop:lapses>=3`: mange lapses
  - `deck:<Studie>::* prop:d>0.7`: høj FSRS-difficulty (kun med FSRS; ellers `prop:ease<2.1`)
- `notes_info` → felter og tags. Evt. `cards_stats` og `get_card_memory_state` for difficulty/stability.

## 2. Gruppér og log
- Gruppér efter `fag::`- og `emne::`-tags (uden emne-tag: deck-navnets sidste led).
- Rangér emner efter (antal "Igen" + lapses) og gennemsnitlig difficulty.
- **Projektmappe:** opdatér `fag/<fag>/fejllog.md` – én række pr. emne i
  `| Emne | Kort m. lapses | Seneste analyse | Status |` (dato ÅÅÅÅ-MM-DD, status `ny`/`i gang`/`bedre`);
  opdatér eksisterende rækker i stedet for at duplikere. **Ellers:** vis tabellen, og tilbyd den som fil.

## 3. For de 3 svageste emner
1. **Kort forklaring** (5–10 linjer) fra pensum med citater (NotebookLM eller projektets filer).
   Fokus på det, kortene viser, at der er misforstået.
2. **5 åbne eksamensspørgsmål** (hvorfor/hvordan/sammenlign/begrund klinisk). Ingen ja/nej.
3. **Kortkritik:** vurder de svære kort mod kortreglerne (`config/kortregler.md` eller skill'en `anki-kort`s
   `references/kortregler.md`). Foreslå omformulering/opdeling som tabel. Ændringer i Anki
   (`update_note_fields` / nye kort via `anki-kort`) først efter brugerens **ok**.
   Slet aldrig kort – foreslå højst at suspendere dem.

4. **Egen note** (hvis der findes en: `python3 scripts/noter.py laes --fag <Fag> --emne "<emne>"` / `studie.note_laes`):
   sæt `noter.py marker --svag ja`, og tilføj i Claudes sektion (bevar resten af sektionen) et afsnit
   `### ⚠️ Svært i Anki (ÅÅÅÅ-MM-DD)` med forklaringen, de 5 spørgsmål og en anbefaling om, hvad der skal genlæses.
   Peg på det i brugerens egen tekst, der ser ud til at være kilden til misforståelsen. Ret aldrig brugerens tekst.
   Når emnet ikke længere er svært ved en senere analyse: `--svag nej`, og fjern afsnittet.

## Output
Kort rapport: top-emner med tal → forklaringer → spørgsmål → foreslåede kortændringer → links til de berørte noter.
I projektmappen gemmes forklaring og spørgsmål i `fejllog.md` under `## <emne> (<dato>)`.
