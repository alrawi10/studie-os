# Odontologi – studieprojekt

## Hvem jeg er
<Uddannelse> på <universitet> (<årgang>, semester <XX>).  ← tilpas
Jeg foretrækker **dybe, præcise faglige forklaringer i professorniveau**, forankret i pensum.
**Svar altid på dansk.** Brug dansk fagsprog med latinsk/engelsk term i parentes første gang.

## Kildehierarki
1. **NotebookLM** (pensum, én notebook pr. fag): svar med citater (kildetitel + side/slide)
2. **Mine noter** i `fag/<fag>/noter/`
3. **Din egen viden**, altid tydeligt markeret som **[uden for pensum]**

Hvis NotebookLM ikke dækker spørgsmålet, så sig det, før du svarer fra egen viden.

## Systemet
- **Absalon/Canvas** (`CANVAS_API_URL` i `.env`) er kilden til fag, filer, moduler og deadlines. MCP: `canvas-api`.
- **NotebookLM** er et kildebundet arkiv. MCP: `gemini-notebook-mcp` (CLI: `~/.local/bin/nlm`). Uofficielt API
  med mine browser-cookies, så det bruges kun til studieformål.
- **Anki** er spaced repetition. MCP: `anki` (add-on AnkiMCP på `http://127.0.0.1:3141/`).

## Hvor tingene ligger
```
<projektmappe>/
├── CLAUDE.md
├── .env                   # CANVAS_API_TOKEN, CANVAS_API_URL – chmod 600, print ALDRIG indholdet
├── config/
│   ├── fag.json           # kort fagnavn → kursus_id, notebook_id, notebook_titel, anki_deck
│   └── kortregler.md      # bindende regler for Anki-kort
├── fag/<fag>/
│   ├── kilder/            # synk. fra Absalon (+ .manifest.json med fil-id, updated_at, notebooklm_source_id)
│   ├── noter/             # mine egne noter
│   ├── eksamen/           # eksamenssvar (<emne>.md)
│   └── fejllog.md         # svage emner fra Anki-statistik
├── scripts/
│   ├── sync_all.sh        # Absalon → kilder/ → NotebookLM
│   ├── absalon_sync.py    # henter nye/ændrede PDF/PPTX/DOCX fra Files + Modules
│   ├── notebook_sync.py   # uploader nye filer til fagets notebook (opretter notebook ved behov)
│   ├── deadlines.py       # kommende deadlines fra Absalon
│   ├── indbakke.py        # Påmindelser-indbakke (Siri-diktat)
│   ├── billede.py         # figur fra citeret side/slide → Anki (bruges af anki-kort)
│   └── canvas_mcp.sh      # starter Canvas MCP med .env
└── .claude/skills/        # anki-kort, eksamenssvar, fejlanalyse
```
Fag (kort navn): se `config/fag.json`. Slå altid id'er op dér.

## Skills
| Skill | Bruges når |
|---|---|
| `anki-kort` | Der skal laves Anki-kort ud fra pensum (NotebookLM → tabel → ok → Anki) |
| `eksamenssvar` | Et eksamensspørgsmål/en aflevering skal besvares dybt med citater; gemmes i `fag/<fag>/eksamen/` |
| `fejlanalyse` | Svage emner skal findes ud fra Anki-lapses/difficulty; opdaterer `fejllog.md` |

## Hurtigkommandoer (naturligt sprog)
| Jeg skriver | Du gør |
|---|---|
| `sync` | Kør `scripts/sync_all.sh` og opsummér nye filer pr. fag og hvad der blev uploadet/udeladt |
| `læst <fag> <emne/forelæsning>` | Min faste arbejdsgang: jeg har netop læst emnet → skill `anki-kort`, afgrænset til præcis de kilder, jeg har læst |
| `kort <fag> <emne>` | Skill `anki-kort`. Tilføjer jeg "direkte", må kortene oprettes uden godkendelse |
| `eksamen <fag> <spørgsmål>` | Skill `eksamenssvar` |
| `fejl` | Skill `fejlanalyse` |
| `deadlines` | Kør `uv run -q --python 3.12 --with requests --with python-dotenv scripts/deadlines.py` (14 dage) og opsummér |

### Planlægning (Apple Kalender, Motion-lignende)
Beskriv her, hvilke skemaaktiviteter du møder op til (fx kun klinik/obligatorisk) og hvilke
andre kalendere der er optaget tid. Læseblokke lægges kun i kalenderen "Studieplan".
| Jeg skriver | Du gør |
|---|---|
| "tilføj opgave …" / "jeg skal nå …" | Tilføj til `planlaegning/opgaver.json` (id, titel, fag, minutter = rest_minutter, deadline, prioritet 1–3, status "aaben"). Estimér tid, hvis jeg ikke angiver den |
| `planlæg` | `uv run -q --python 3.12 --with python-dateutil scripts/kalender.py planlaeg`, vis planen, og skriv med `--skriv` når jeg siger ok |
| "nåede ikke X" | Læg de mistede minutter til opgavens `rest_minutter`, og planlæg igen |
| "færdig med X" | Sæt status "faerdig", og planlæg igen |
Rammer (arbejdstid, bloklængde, Anki-tid, fridage) står i `config/planlaegning.json`.

### Indbakke (Siri → Påmindelser › "Studie")
Jeg dikterer på farten: *"Hey Siri, tilføj 'har læst paro F4' til Studie"*. Ved session-start vises antal ubehandlede punkter.
`indbakke` → `python3 scripts/indbakke.py hent` (JSON), tolk hvert punkt, og vis en kort plan, før du handler:
| Punktet betyder | Handling |
|---|---|
| har læst / er færdig med at læse X | `læst`-workflow (skill `anki-kort`) – ét emne ad gangen |
| skal nå / skal lave / husk X (evt. deadline, tid) | ny opgave i `planlaegning/opgaver.json` (estimér tid hvis ikke nævnt) |
| nåede ikke X | læg minutter tilbage på opgaven |
| færdig med opgave X | status "faerdig" |
| spørgsmål / "forklar …" | besvar ud fra pensum (NotebookLM) |
Kør derefter `planlæg --skriv`, hvis opgaver ændrede sig, og afkryds de behandlede punkter med
`python3 scripts/indbakke.py afslut <id> …`. Uklare punkter: spørg, og lad dem stå. Slet aldrig punkter.

Python-scripts køres altid med `uv run -q --python 3.12 --with <pakker> scripts/<script>.py`
(systemets python3 er 3.9).

## Regler
- Hemmeligheder står kun i `.env`. Print dem aldrig, og skriv dem aldrig i andre filer.
- Slet aldrig Anki-kort, notebooks eller kilder uden mit udtrykkelige ja.
- Kort uden kildebelæg fra NotebookLM oprettes ikke (listes som "ubekræftet").

## Vedligehold
- **NotebookLM-login** udløber hver 2.–4. uge. Symptom: auth-fejl. Løsning: `nlm login` i terminalen.
  Tjek status med `nlm login --check`.
- **Canvas-token** udløber **<dato>**. Forny det i Absalon → Konto → Indstillinger → "+ Nyt adgangstoken",
  og indsæt det i `.env`.
- **Anki skal være åben**, når der laves kort eller køres fejlanalyse (MCP-serveren kører i Anki).
- NotebookLM-grænse: 300 kilder pr. notebook (Pro) og 200 MB pr. fil. Store PPTX uploades som tekst.
- Nye MCP-servere/skills kræver en ny Claude Code-session for at blive indlæst.
