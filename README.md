# full-uni-package

**Et studiesystem til Claude Code, der binder Canvas (fx KU's Absalon), NotebookLM, Anki og Apple Kalender sammen.**

> 🇬🇧 *A Claude Code study system for university students: syncs course files from Canvas LMS, archives them in one NotebookLM notebook per course (source-grounded answers with citations), creates spaced-repetition cards directly in Anki, and plans study blocks around your timetable in Apple Calendar (Motion-style). Built for dentistry at the University of Copenhagen, but works with any Canvas institution. Docs are in Danish.*

```
Absalon/Canvas ──sync──▶ fag/<fag>/kilder/ ──upload──▶ NotebookLM (1 notebook pr. fag)
                                                          │ citater
Apple Kalender ◀──planlæg── Claude Code ◀─────────────────┘
                                  │ kildebelagte kort
                                  ▼
                                Anki
```

## Hvad den kan
| Du skriver i Claude Code | Hvad der sker |
|---|---|
| `læst <fag> <emne>` | Laver 8–15 kildebelagte Anki-kort fra præcis det, du har læst (NotebookLM → tabel → ok → Anki) |
| `kort <fag> <emne>` | Kort til et vilkårligt emne (`direkte` = uden godkendelse) |
| `eksamen <fag> <spørgsmål>` | Svar i professorniveau med citater fra pensum (Vancouver-referencer til afleveringer) |
| `fejl` | Finder svage emner ud fra Anki-lapses/FSRS-difficulty, forklarer dem og giver eksamensspørgsmål |
| `sync` | Henter nye/ændrede filer fra Canvas og uploader dem til fagets notebook |
| `deadlines` | Afleveringer og quizzer de næste 14 dage |
| `opgave <titel> [fag] [tid] [deadline]` | Ny opgave; læseblokke planlægges Motion-lignende i Apple Kalender |
| `nåede ikke <X>` / `færdig <X>` | Lægger minutter tilbage på opgaven / afslutter den, og planlægger igen |
| `plan` / `status` | Viser og skriver planen / kort overblik over blokke, opgaver og deadlines |
| `spørgsmål <emne>` | Svar ud fra pensum (NotebookLM) med citater |
| `indbakke` | Behandler det, du har dikteret til Siri (*"tilføj 'læst paro F4' til Påmindelser"*). Første ord er de samme som ovenfor: `læst`, `opgave`, `nåede ikke`, `færdig`, `spørgsmål` |

Alle Anki-kort følger [`config/kortregler.md`](config/kortregler.md): ét faktum pr. kort, cloze til definitioner og tal, basic til hvorfor/hvordan, og altid en kildehenvisning. Kort uden belæg i pensum oprettes ikke. Kort om noget visuelt (histologi, røntgen, kliniske fotos) får automatisk den citerede figur fra pensum med.

## Indhold
```
.claude/skills/        anki-kort, eksamenssvar, fejlanalyse (Claude Code-skills)
config/                kortregler.md + *.example.json (kopiér til fag.json / planlaegning.json)
scripts/
  absalon_sync.py      Canvas Files + Modules → fag/<fag>/kilder/ (kun nye/ændrede, manifest)
  notebook_sync.py     kilder → NotebookLM (opretter notebooks, undgår dubletter, store PPTX som tekst)
  sync_all.sh          begge ovenstående
  deadlines.py         kommende deadlines fra Canvas
  indbakke.py          Påmindelser-liste "Påmindelser" som indbakke (Siri-diktat), tjekkes ved session-start
  tilfoej_bog.py       lærebog → notebook (tekst med sidemarkører, deles over ~350.000 ord)
  billede.py           figur fra citeret PDF-side/PPTX-slide → Anki-kortets Billede-felt
  kalender.py          planlægger (Apple Kalender via AppleScript)
  install_planner.sh   kør planlæggeren automatisk hver 30. min (launchd)
  canvas_mcp.sh        starter Canvas MCP med token fra .env
CLAUDE.example.md      skabelon til din personlige CLAUDE.md
```

## Krav
- macOS (kalenderdelen bruger Apple Kalender), [Claude Code](https://claude.com/claude-code)
- [Homebrew](https://brew.sh), `uv`, `node`, Google Chrome
- [Anki](https://apps.ankiweb.net) **25.07+** med add-on'et [AnkiMCP Server](https://github.com/ankimcp/anki-mcp-server-addon) (kode `124672614`)
- En Canvas-konto, hvor du må oprette adgangstokens, og en Google-konto til NotebookLM

## Opsætning
Læs altid den aktuelle README for hvert af de tre MCP-projekter. Kommandoerne nedenfor kan være forældede.

1. **Klon og konfigurér**
   ```bash
   git clone https://github.com/alrawi10/full-uni-package ~/Studie && cd ~/Studie
   cp .env.example .env && chmod 600 .env        # indsæt dit Canvas-token i .env
   cp config/fag.example.json config/fag.json
   cp config/planlaegning.example.json config/planlaegning.json
   cp CLAUDE.example.md CLAUDE.md                 # tilpas "Hvem jeg er"
   ```
   Læg ikke mappen i `~/Desktop`, `~/Documents` eller `~/Downloads`. macOS blokerer baggrundsjob dér.
2. **Canvas MCP** ([vishalsachdev/canvas-mcp](https://github.com/vishalsachdev/canvas-mcp))
   ```bash
   git clone https://github.com/vishalsachdev/canvas-mcp ~/.local/share/canvas-mcp
   cd ~/.local/share/canvas-mcp && uv venv --python 3.12 && uv pip install -e .
   claude mcp add --scope user canvas-api -- ~/Studie/scripts/canvas_mcp.sh
   ```
3. **NotebookLM** ([jacob-bd/notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli))
   ```bash
   uv tool install notebooklm-mcp-cli && nlm login
   claude mcp add --scope user gemini-notebook-mcp \
     -e NOTEBOOKLM_DISABLED_GROUPS=organization,automation,notes,sharing,research -- ~/.local/bin/notebooklm-mcp
   nlm skill install claude-code
   ```
4. **Anki**: installér add-on'et, genstart Anki, og kør så
   `claude mcp add --scope user --transport http anki http://127.0.0.1:3141/`.
   Opret note-typerne `Odontologi-Basic` (Forside, Bagside, Uddybning, Kilde, Billede) og
   `Odontologi-Cloze` (Tekst, Uddybning, Kilde, Billede), eller bed Claude om det.
5. **Fyld `config/fag.json`** med dine kursus-id'er. Du kan bede Claude om at hente dine aktive kurser.
   Kør derefter `scripts/sync_all.sh`.
6. **Planlægning (valgfrit)**: Tilpas kalendernavnene i `config/planlaegning.json`, opret en kalender
   ved navn "Studieplan", og kør `scripts/install_planner.sh`.

Åbn derefter Claude Code i mappen og skriv fx `deadlines`.

## Vigtigt om data, ophavsret og ansvar
- **Undervisningsmateriale må ikke deles.** Filerne i `fag/` tilhører universitet og forlag og er udelukket i `.gitignore`. Del aldrig din `fag/`-mappe.
- **Hemmeligheder** ligger kun i `.env` (`chmod 600`) og committes aldrig.
- **NotebookLM-værktøjet bruger et uofficielt API** og dine browser-cookies. Det kan holde op med at virke uden varsel. Brug det kun til dit eget studie og på eget ansvar.
- AI-genererede kort og svar kan indeholde fejl. Kildekravet mindsker risikoen, men du har selv ansvaret for at kontrollere dem mod pensum.

## Tak til
[canvas-mcp](https://github.com/vishalsachdev/canvas-mcp) · [notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli) · [anki-mcp-server-addon](https://github.com/ankimcp/anki-mcp-server-addon)

## Licens
[MIT](LICENSE)
