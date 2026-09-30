# Studie OS

**Et studiesystem til Claude (Claude Code, Claude Desktop og Cowork), der binder dit universitets LMS (Canvas, Moodle, Brightspace eller itslearning), NotebookLM, Anki, Apple Kalender og Siri sammen.**

> 🇬🇧 *A study system for Claude (Claude Code, Claude Desktop and Cowork): syncs course files from your LMS (Canvas, Moodle, Brightspace, itslearning or a manual folder), archives them in one NotebookLM notebook per course for source-grounded answers with citations, creates spaced-repetition cards directly in Anki (with figures from the cited page), plans study blocks around your timetable in Apple Calendar (Motion-style) and takes voice notes via Siri. Built for dentistry at the University of Copenhagen, but works for any study programme. Docs are in Danish.*

```
LMS (Canvas/Moodle/…) ──sync──▶ fag/<fag>/kilder/ ──upload──▶ NotebookLM (1 notebook pr. fag)
                                                                  │ citater
Siri ──▶ Påmindelser ──indbakke──▶  Claude Code / Desktop / Cowork ◀─┘
                                     │                  │
                    planlæg (hver 30. min)        kildebelagte kort (+ figur)
                                     ▼                  ▼
                        Apple Kalender "Studieplan"    Anki
```

## Hvad den kan
Samme korte ord virker i Claude Code, i Claude Desktop/Cowork og som første ord i en Siri-diktat.

| Du skriver | Hvad der sker |
|---|---|
| `status` | Overblik: dagens blokke, åbne opgaver, deadlines og ubehandlede indbakke-punkter |
| `læst <fag> <emne>` | 8–15 kildebelagte Anki-kort fra præcis det, du har læst (pensum → tabel → **ok** → Anki) |
| `kort <fag> <emne>` | Kort til et vilkårligt emne (`direkte` = uden godkendelse) |
| `spørgsmål <emne>` / `forklar …` | Svar ud fra pensum med citater (kildetitel + side/slide) |
| `eksamen <fag> <spørgsmål>` | Svar i professorniveau med citater; Vancouver-referencer til afleveringer |
| `fejl` | Svage emner ud fra Anki (lapses, "Igen", FSRS-difficulty) med forklaring og eksamensspørgsmål |
| `opgave <titel> [fag] [tid] [deadline]` | Ny opgave; læseblokke planlægges i Apple Kalender uden om skema og aftaler |
| `nåede ikke <X>` / `færdig <X>` | Lægger tid tilbage / afslutter opgaven, og planen følger med |
| `plan` | Viser planen og skriver den i kalenderen "Studieplan", når du siger ok |
| `sync` / `deadlines` | Nye filer fra LMS'et → NotebookLM / afleveringer og quizzer de næste 14 dage |
| `indbakke` | Behandler det, du har dikteret til Siri (*"Hey Siri, tilføj 'læst paro F4' til Påmindelser"*) |
| `figur <fag> <kilde> s. <nr>` | Henter figuren fra den side/slide – til kort om histologi, røntgen, kliniske fotos osv. |

Alle Anki-kort følger [`config/kortregler.md`](config/kortregler.md): ét faktum pr. kort, cloze til definitioner og tal, basic til hvorfor/hvordan, og altid en kildehenvisning. Kort uden belæg i pensum oprettes ikke.

## En almindelig dag
1. **Morgen:** `status` → dagens læseblokke (📚) og den daglige Anki-blok (🔁) ligger i kalenderen "Studieplan".
2. **Repetér** dine forfaldne Anki-kort, og **læs** i blokkene. Spørg NotebookLM (eller `spørgsmål …`) undervejs.
3. **Efter hvert emne:** `læst <fag> <emne>` → godkend tabellen → kortene ligger i Anki.
4. **Når dagen skrider:** `nåede ikke …` / `færdig …` – kalenderen omplanlægges automatisk.
5. **På farten:** diktér til Siri; skriv `indbakke`, næste gang du åbner Claude.

Hver uge: `sync`, `deadlines` og `fejl`. Op til eksamen: `eksamen …`.

## Hvor kan det køre?
| | Claude Code | Claude Desktop: Chat og Cowork | claude.ai web/mobil |
|---|---|---|---|
| Kort, eksamenssvar, fejlanalyse, spørgsmål | ✅ | ✅ | ✅ kort som Anki-importfil, pensum fra projektfiler |
| NotebookLM og Anki direkte | ✅ | ✅ | ❌ |
| Sync, deadlines, planlægning, opgaver, Siri-indbakke, figurer | ✅ | ✅ via MCP-serveren `studie` | ❌ kræver din Mac |
| Automatisk indbakke-besked ved start | ✅ | ❌ skriv `status`/`indbakke` | ❌ |
| Ændringer i selve systemet (scripts, GitHub) | ✅ | – | – |

Kalenderplanlægningen kører desuden **automatisk hver 30. minut** (launchd), uanset hvor du arbejder.

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
- macOS (kalender, Siri-indbakke og Desktop-værktøjer), [Claude Code](https://claude.com/claude-code) og/eller Claude Desktop
- [Homebrew](https://brew.sh), `uv`, `node`, Google Chrome
- [Anki](https://apps.ankiweb.net) **25.07+** med add-on'et [AnkiMCP Server](https://github.com/ankimcp/anki-mcp-server-addon) (kode `124672614`)
- Adgang til dit LMS (token, app-token eller cookie – se `.env.example`) og en Google-konto til NotebookLM
  (NotebookLM har en grænse for antal kilder pr. notebook, som afhænger af din plan)

## Opsætning
**Nemmest:** klon repoet, åbn Claude Code i mappen, og skriv **`opsæt`**. Så guider Claude dig trin for trin
(platform, token, kurser, NotebookLM, Anki). Nedenfor står de samme trin manuelt.
Læs altid den aktuelle README for hvert af MCP-projekterne. Kommandoerne nedenfor kan være forældede.

1. **Klon og konfigurér**
   ```bash
   git clone https://github.com/alrawi10/studie-os ~/Studie && cd ~/Studie
   cp .env.example .env && chmod 600 .env        # udfyld blokken for din platform
   cp config/fag.example.json config/fag.json    # sæt "studie" og "lms"
   cp config/planlaegning.example.json config/planlaegning.json
   cp CLAUDE.example.md CLAUDE.md                 # tilpas "Hvem jeg er" og dit skema
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
5. **Fag og første sync:** `scripts/lms_sync.py --kurser` viser dine aktive kurser → skriv dem i `config/fag.json`
   → kør `scripts/sync_all.sh`. Notebooks oprettes automatisk.
6. **Lærebøger (valgfrit):** tjek dem mod kursernes litteraturlister, og tilføj med
   `scripts/tilfoej_bog.py --fag <Fag> --fil <bog.pdf> --titel "<Titel, udgave>"`
   (tekst med sidemarkører; store bøger deles automatisk op; scannede bøger uploades som PDF).
7. **Planlægning (valgfrit):** tilpas kalendernavnene i `config/planlaegning.json`, opret en kalender
   ved navn "Studieplan", og kør `scripts/install_planner.sh` (planlægger hver 30. min).
8. **Siri-indbakke (valgfrit):** intet at installere – diktér *"Hey Siri, tilføj '…' til Påmindelser"*.
   Claude Code viser ubehandlede punkter ved start (hook i `.claude/settings.json`). Anden liste: `INDBAKKE_LISTE`.

## Brug i Claude Desktop, Cowork og projekter
1. **Pak:** `python3 scripts/pak_portable.py` → `dist/skills/*.zip` + `dist/projekt-instruktioner.md`
   (udfyldt med dit studie og dine fag).
2. **Skills:** Claude → Tilpas → Skills → Tilføj → upload hver zip.
3. **Instruktioner:** indsæt `dist/projekt-instruktioner.md` i et projekt eller i Cowork.
   På claude.ai uden Desktop: læg fagets PDF'er i projektets viden, så de bruges som pensum.
4. **Desktop-værktøjer (macOS):** luk Claude helt (⌘Q), og kør i Terminal: `scripts/desktop_mcp.sh`.
   Det registrerer `studie` ([`scripts/studie_mcp.py`](scripts/studie_mcp.py)), `anki` og NotebookLM i Claude Desktop
   (sikkerhedskopi tages først; fjern igen med `--fjern`).
5. **I en ny chat:** slå `studie`, `anki` og NotebookLM til under værktøjer, og vælg "Tillad altid" første gang.
   Mac'en skal være tændt, Claude Desktop åben – og Anki åben, når der laves kort.

## Indhold
```
.claude/skills/        anki-kort, eksamenssvar, fejlanalyse (virker i Claude Code og – pakket – i Chat/Cowork)
.claude/settings.json  session-start-hook: viser ubehandlede Siri-punkter
config/                kortregler.md + *.example.json (kopiér til fag.json / planlaegning.json)
portable/              skabelon til projektinstruktioner (Chat/Projekter/Cowork)
scripts/
  lms_sync.py          LMS → fag/<fag>/kilder/ (kun nye/ændrede, manifest) + filer fra kilder/Manuel/
  lms/                 adaptere: canvas, moodle, brightspace, itslearning + ical (deadlines fra kalender-feed)
  lms_test.py          diagnose af LMS-forbindelsen (udskriver ingen hemmeligheder)
  notebook_sync.py     kilder → NotebookLM (opretter notebooks, undgår dubletter, store filer som tekst)
  sync_all.sh          begge ovenstående
  tilfoej_bog.py       lærebog → notebook (tekst med sidemarkører, deles over ~350.000 ord)
  deadlines.py         kommende deadlines fra LMS'et og/eller kalender-feed
  kalender.py          planlægger (Apple Kalender via AppleScript)
  install_planner.sh   kør planlæggeren automatisk hver 30. min (launchd)
  indbakke.py          Påmindelser som indbakke (Siri-diktat)
  billede.py           figur fra citeret PDF-side/PPTX-slide → Anki-kortets Billede-felt
  studie_mcp.py        MCP-server: sync, deadlines, planlægning, opgaver, indbakke og figurer til Claude Desktop
  desktop_mcp.sh       registrerer studie-, Anki- og NotebookLM-MCP i Claude Desktop
  pak_portable.py      pakker skills + projektinstruktioner (dist/)
  canvas_mcp.sh        starter Canvas MCP med token fra .env
tests/                 adapter-tests med simulerede API-svar
CLAUDE.example.md      skabelon til din personlige CLAUDE.md (inkl. "opsæt"-guide)
```

## Vedligehold og fejlfinding
| Problem | Løsning |
|---|---|
| NotebookLM-fejl om login (sker hver 2.–4. uge) | `nlm login`; tjek med `nlm login --check` |
| LMS-token udløbet / `sync` fejler | Lav et nyt token (se `.env.example`), og kør `scripts/lms_test.py` |
| Anki-værktøjer svarer ikke | Anki skal være åben med add-on'et; tjek `http://127.0.0.1:3141/` |
| Planen opdateres ikke | Se `planlaegning/auto.log`; geninstallér med `scripts/install_planner.sh` |
| Desktop-værktøjer mangler | Luk Claude (⌘Q), kør `scripts/desktop_mcp.sh` igen, og slå værktøjerne til i chatten |
| Skill-upload afvises ("cannot contain XML tags") | Ingen `<` eller `>` i en skills `description`; `pak_portable.py` tjekker det |

Tests: `uv run --with pytest --with requests --with python-dotenv --with icalendar pytest tests -q`

## Vigtigt om data, ophavsret og ansvar
- **Undervisningsmateriale og lærebøger må ikke deles.** Filerne i `fag/` tilhører universitet og forlag og er udelukket i `.gitignore`. Del aldrig din `fag/`-mappe eller Anki-decks med figurer fra pensum.
- **Hemmeligheder** ligger kun i `.env` (`chmod 600`) og committes aldrig.
- **NotebookLM-værktøjet og itslearning-/Brightspace-cookie-adgangen bruger uofficielle API'er.** De kan holde op med at virke uden varsel. Brug dem kun til dit eget studie og på eget ansvar.
- AI-genererede kort og svar kan indeholde fejl. Kildekravet mindsker risikoen, men du har selv ansvaret for at kontrollere dem mod pensum.

## Tak til
[canvas-mcp](https://github.com/vishalsachdev/canvas-mcp) · [notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli) · [anki-mcp-server-addon](https://github.com/ankimcp/anki-mcp-server-addon)

## Licens
[MIT](LICENSE)
