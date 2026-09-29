---
name: anki-kort
description: Bruges når der skal laves Anki-kort til odontologi ud fra pensum
---

# Anki-kort fra pensum

Laver kildebelagte Anki-kort ud fra NotebookLM og opretter dem i `Odontologi::<Fag>::<Emne>`.
Læs altid `config/kortregler.md` først. Reglerne dér er bindende.

## Værktøjer
- **NotebookLM:** MCP `gemini-notebook-mcp` (`notebook_query`, `source_list`).
  Fallback: `~/.local/bin/nlm notebook query <notebook_id> "<spørgsmål>" --json`.
- **Anki:** MCP `anki` (`find_notes`, `notes_info`, `create_deck`, `add_notes`). Anki skal være åben.
  Note-typer: `Odontologi-Basic` (Forside, Bagside, Uddybning, Kilde, Billede) og
  `Odontologi-Cloze` (Tekst, Uddybning, Kilde, Billede).

## Arbejdsgang
1. **Afklar fag og emne.** Slå faget op i `config/fag.json` → `notebook_id`, `notebook_titel`, `anki_deck`.
   Er emnet en bestemt forelæsning, så find kildens titel med `source_list`.
   **"læst <fag> <emne>"** (brugerens faste arbejdsgang: kort laves løbende, lige efter at et emne er læst):
   afgræns NotebookLM-forespørgslen til præcis de kilder, der hører til det læste (`source_ids`),
   og lav ikke kort om stof, brugeren ikke har læst endnu.
   Deck = `<anki_deck>::<Emne>`, fx `Odontologi::KOF::Tyggemuskler`.
2. **Spørg NotebookLM** (evt. afgrænset til relevante `source_ids`). Brug fx:
   > "Giv mig de centrale fakta, definitioner, mekanismer, klassifikationer, tal/grænseværdier og kliniske pointer om <emne>. Angiv for hvert punkt det præcise citat, kildens titel og side-/slidenummer."

   Stil opfølgende spørgsmål, hvis citater eller sidetal mangler.
3. **Tjek for dubletter** i hele samlingen, også brugerens egne, ældre decks uden for `Odontologi::`:
   `find_notes` med `tag:emne::<emne>` og derefter med 2–4 centrale nøgleord (fx `"parodontitis" "pochedybde"`)
   → `notes_info`. Spring over, hvad der allerede er dækket. Nævn dem kort med deck-navn.
4. **Lav kortene** efter `config/kortregler.md`: ét faktum pr. kort, cloze til definitioner/tal/sekvenser,
   basic til hvorfor/hvordan og klinik, dansk fagsprog med latinsk/engelsk term i parentes første gang,
   bagside ≤ ca. 25 ord, uddybning i `Uddybning`, ca. 8–15 kort pr. forelæsning/kapitel.
5. **Kvalitetstjek.** Hvert kort skal pege på et konkret citat fra trin 2.
   Kort uden kildebelæg oprettes **ikke**. De vises i en separat liste "Ubekræftet".
   Tjek også: ingen ja/nej, ingen multiple choice, svaret står ikke i spørgsmålet, én ting pr. kort.
6. **Vis en tabel** til godkendelse:

   | # | Type | Forside / Tekst | Bagside | Kilde | Tags |
   |---|---|---|---|---|---|

   Opret først, når brugeren skriver **ok** (eller rettelser → opdatér tabellen).
   Hvis brugeren har skrevet **"direkte"** i sin anmodning, må kortene oprettes uden godkendelse.
7. **Opret i Anki.** `create_deck` (hvis nødvendigt), derefter ét `add_notes`-kald pr. note-type med
   `tags: ["fag::<fag>", "emne::<emne>", "ai-genereret", …]`. Rapportér antal oprettede note-id'er
   og eventuelle dubletter/fejl.

## Feltformat
- `Kilde`: `<notebook_titel> · <kildetitel> · s./slide <nr>`
- `Uddybning`: 1–4 sætninger om mekanisme/kontekst. Må gerne indeholde det ordrette citat i kursiv.
- `Billede`: tom, medmindre brugeren leverer et billede (så `store_media_file` og `<img src="…">`).
- Cloze: `{{c1::…}}`. Brug flere huller (c1, c2 …) i samme note til sekvenser i stedet for én lang liste.
