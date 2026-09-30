# full-uni-package

**Et studiesystem til Claude Code, der binder dit universitets LMS (Canvas, Moodle, Brightspace eller itslearning), NotebookLM, Anki og Apple Kalender sammen.**

> 🇬🇧 *A Claude Code study system for university students: syncs course files from Canvas LMS, archives them in one NotebookLM notebook per course (source-grounded answers with citations), creates spaced-repetition cards directly in Anki, and plans study blocks around your timetable in Apple Calendar (Motion-style). Built for dentistry at the University of Copenhagen; supports Canvas, Moodle, Brightspace and itslearning (plus a manual/iCal fallback), so it works for any study programme. Docs are in Danish.*

```
LMS (Canvas/…)  ──sync──▶ fag/<fag>/kilder/ ──upload──▶ NotebookLM (1 notebook pr. fag)
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
  lms_sync.py          LMS → fag/<fag>/kilder/ (kun nye/ændrede, manifest) + filer fra kilder/Manuel/
  lms/                 adaptere: canvas, moodle, brightspace, itslearning + ical (deadlines fra kalender-feed)
  lms_test.py          diagnose af LMS-forbindelsen (udskriver ingen hemmeligheder)
  notebook_sync.py     kilder → NotebookLM (opretter notebooks, undgår dubletter, store PPTX som tekst)
  sync_all.sh          begge ovenstående
  deadlines.py         kommende deadlines fra LMS'et og/eller kalender-feed
  indbakke.py          Påmindelser-liste "Påmindelser" som indbakke (Siri-diktat), tjekkes ved session-start
  tilfoej_bog.py       lærebog → notebook (tekst med sidemarkører, deles over ~350.000 ord)
  billede.py           figur fra citeret PDF-side/PPTX-slide → Anki-kortets Billede-felt
  kalender.py          planlægger (Apple Kalender via AppleScript)
  install_planner.sh   kør planlæggeren automatisk hver 30. min (launchd)
  canvas_mcp.sh        starter Canvas MCP med token fra .env
CLAUDE.example.md      skabelon til din personlige CLAUDE.md
```

## Universiteter
| Universitet | Platform | `lms` | Status |
|---|---|---|---|
| KU (Absalon), CBS | Canvas | `canvas` | ✅ Brugt dagligt (KU Odontologi) |
| AAU, RUC, ITU | Moodle | `moodle` | 🧪 Bygget efter API-dokumentationen, mangler test med rigtig konto |
| AU (Brightspace), DTU (DTU Learn) | Brightspace | `brightspace` | 🧪 Mangler test. Officielt token kræver typisk universitetets godkendelse, ellers browser-cookie |
| SDU | itslearning | `itslearning` | 🧪 Eksperimentel (uofficielt mobilapp-API), mangler test |
| Alle andre | – | `manuel` | ✅ Læg PDF'er i `fag/<fag>/kilder/Manuel/`, og få deadlines fra et kalender-feed (`ICAL_URL`) |

Platformene er noteret efter bedste viden; tjek dit eget universitet. **Studerer du på AAU, AU, DTU, SDU, RUC eller ITU?**
Hjælp med at teste: Følg opsætningen, kør `scripts/lms_test.py` (udskriver ingen hemmeligheder) og opret et issue
med resultatet. Adapterne ligger i [`scripts/lms/`](scripts/lms) og har samme fire funktioner: kurser, filer, download og deadlines.

## Krav
- macOS (kalenderdelen bruger Apple Kalender), [Claude Code](https://claude.com/claude-code)
- [Homebrew](https://brew.sh), `uv`, `node`, Google Chrome
- [Anki](https://apps.ankiweb.net) **25.07+** med add-on'et [AnkiMCP Server](https://github.com/ankimcp/anki-mcp-server-addon) (kode `124672614`)
- Adgang til dit LMS (token, app-token eller cookie – se `.env.example`) og en Google-konto til NotebookLM
- Kalenderplanlægning og Siri-indbakke kræver macOS; resten virker også uden

## Opsætning
**Nemmest:** klon repoet, åbn Claude Code i mappen, og skriv **`opsæt`**. Så guider Claude dig trin for trin
(platform, token, kurser, NotebookLM, Anki). Nedenfor står de samme trin manuelt.
Læs altid den aktuelle README for hvert af MCP-projekterne. Kommandoerne nedenfor kan være forældede.

1. **Klon og konfigurér**
   ```bash
   git clone https://github.com/alrawi10/full-uni-package ~/Studie && cd ~/Studie
   cp .env.example .env && chmod 600 .env        # udfyld blokken for din platform
   cp config/fag.example.json config/fag.json
   cp config/planlaegning.example.json config/planlaegning.json
   cp CLAUDE.example.md CLAUDE.md                 # tilpas "Hvem jeg er"
   # sæt "studie" og "lms" i config/fag.json, og test forbindelsen:
   uv run -q --python 3.12 --with requests --with python-dotenv --with icalendar scripts/lms_test.py
   ```
   Læg ikke mappen i `~/Desktop`, `~/Documents` eller `~/Downloads`. macOS blokerer baggrundsjob dér.
2. **Kun Canvas, valgfrit: Canvas MCP** ([vishalsachdev/canvas-mcp](https://github.com/vishalsachdev/canvas-mcp))
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
   Opret note-typerne `<Studie>-Basic` (Forside, Bagside, Uddybning, Kilde, Billede) og
   `<Studie>-Cloze` (Tekst, Uddybning, Kilde, Billede), fx `Jura-Basic` – eller bed Claude om det.
5. **Fyld `config/fag.json`** med dine kursus-id'er: `scripts/lms_sync.py --kurser` viser dine aktive kurser.
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
