# <Studie> – studieprojekt  ← tilpas (fx Odontologi, Jura, Medicin)

## Hvem jeg er
<Uddannelse> på <universitet> (<årgang>, semester <XX>).  ← tilpas
Jeg foretrækker **dybe, præcise faglige forklaringer i professorniveau**, forankret i pensum.
**Svar altid på dansk.** Brug dansk fagsprog med latinsk/engelsk term i parentes første gang.

## Første opsætning (når jeg skriver `opsæt`, eller `config/fag.json` mangler)
Guid mig trin for trin, og stop ved alt jeg selv skal gøre (login, tokens, installationer):
1. **Universitet → platform** (tjek altid, hvis i tvivl): KU og CBS = `canvas` · AAU, RUC, ITU = `moodle` ·
   AU og DTU = `brightspace` · SDU = `itslearning` (eksperimentel) · ukendt/intet API = `manuel`.
2. `cp .env.example .env && chmod 600 .env`. Forklar præcis, hvor jeg finder token/cookie til min platform
   (se kommentaren øverst i `scripts/lms/<platform>.py`), og lad mig selv indsætte det. Bed aldrig om det i chatten.
3. `cp config/fag.example.json config/fag.json`, sæt `studie` og `lms`, og kør
   `uv run -q --python 3.12 --with requests --with python-dotenv --with icalendar scripts/lms_test.py`.
   Ved ❌: læs fejlen, ret opsætningen, eller brug `lms_test.py --raa <sti>` til at se API-strukturen.
4. `scripts/lms_sync.py --kurser` → lad mig vælge fagene, og skriv dem i `config/fag.json`
   (`kursus_id`, `kursusnavn`, `notebook_titel`, `anki_deck` = `<Studie>::<Fag>`).
5. NotebookLM (`nlm login`), Anki-add-on og note-typerne `<Studie>-Basic`/`<Studie>-Cloze` som i README,
   derefter `scripts/sync_all.sh`. Kalender og Siri-indbakke er valgfrie (kun macOS).
6. Udfyld "Hvem jeg er" ovenfor sammen med mig.

## Kildehierarki
1. **NotebookLM** (pensum, én notebook pr. fag): svar med citater (kildetitel + side/slide)
2. **Mine noter** i `fag/<fag>/noter/`
3. **Din egen viden**, altid tydeligt markeret som **[uden for pensum]**

Hvis NotebookLM ikke dækker spørgsmålet, så sig det, før du svarer fra egen viden.

## Systemet
- **LMS** (platform = `lms` i `config/fag.json`: canvas / moodle / brightspace / itslearning / manuel) er kilden til
  fag, filer og deadlines via `scripts/lms_sync.py`. Filer kan altid lægges manuelt i `fag/<fag>/kilder/Manuel/`.
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
│   ├── lms_sync.py        # henter nye/ændrede PDF/PPTX/DOCX fra LMS'et + kilder/Manuel/
│   ├── lms/               # adaptere: canvas, moodle, brightspace, itslearning, ical
│   ├── lms_test.py        # diagnose af LMS-forbindelsen
│   ├── notebook_sync.py   # uploader nye filer til fagets notebook (opretter notebook ved behov)
│   ├── deadlines.py       # kommende deadlines fra LMS'et (+ evt. kalender-feed ICAL_URL)
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
**Ét fælles ordforråd:** de samme korte ord virker i Claude *og* som første ord i en Siri-diktat til Påmindelser.
Første ord afgør, hvad punktet er; resten er fag, emne, tid og deadline i fri tekst (fag kan forkortes).
Gamle formuleringer ("har læst …", "skal nå …", "færdig med …") virker stadig som synonymer.
| Jeg skriver | Du gør |
|---|---|
| `læst <fag> <emne>` | Jeg har netop læst emnet → skill `anki-kort`, afgrænset til præcis de kilder, jeg har læst |
| `kort <fag> <emne>` | Skill `anki-kort`. Tilføjer jeg "direkte", må kortene oprettes uden godkendelse |
| `opgave <titel> [fag] [tid] [deadline]` | Ny opgave i `planlaegning/opgaver.json` (id, titel, fag, minutter = rest_minutter, deadline, prioritet 1–3, status "aaben"). Estimér tid/prioritet, hvis jeg ikke angiver dem, og fortæl hvad du valgte |
| `nåede ikke <X>` | Læg de mistede minutter til opgavens `rest_minutter`, og planlæg igen |
| `færdig <X>` | Sæt status "faerdig", og planlæg igen |
| `plan` | `uv run -q --python 3.12 --with python-dateutil scripts/kalender.py planlaeg`, vis planen, og skriv med `--skriv` når jeg siger ok |
| `status` | Kort overblik: dagens/morgendagens blokke, åbne opgaver med rest og deadline, forsinkede opgaver, ubehandlet indbakke |
| `spørgsmål <emne>` (også `forklar …`) | Besvar ud fra pensum (NotebookLM) med citater |
| `eksamen <fag> <spørgsmål>` | Skill `eksamenssvar` |
| `fejl` | Skill `fejlanalyse` |
| `deadlines` | Kør `uv run -q --python 3.12 --with requests --with python-dotenv --with icalendar scripts/deadlines.py` (14 dage) og opsummér |
| `sync` | Kør `scripts/sync_all.sh` og opsummér nye filer pr. fag og hvad der blev uploadet/udeladt |
| `indbakke` | Behandl Påmindelser-indbakken (se nedenfor) |
Eksempler: `læst paro F4` · `opgave KOF epikrise 3 timer fredag` · `nåede ikke KOF læsning` · `færdig KOF opslag` · `spørgsmål DC-TMD akse 2`.

### Planlægning (Apple Kalender, Motion-lignende)
Beskriv her, hvilke skemaaktiviteter du møder op til (fx kun klinik/obligatorisk) og hvilke
andre kalendere der er optaget tid. Læseblokke lægges kun i kalenderen "Studieplan".
Kommandoerne `opgave`, `nåede ikke`, `færdig` og `plan` står i tabellen ovenfor
(synonymer: "tilføj opgave …", "jeg skal nå …", `planlæg`, "færdig med …").
Rammer (arbejdstid, bloklængde, Anki-tid, fridage) står i `config/planlaegning.json`.

### Indbakke (Siri → Påmindelser › listen "Påmindelser")
Jeg dikterer på farten: *"Hey Siri, tilføj 'læst paro F4' til Påmindelser"*. Ved session-start vises antal ubehandlede punkter.
`indbakke` → `python3 scripts/indbakke.py hent` (JSON), tolk hvert punkt efter **første ord** (`læst`, `opgave`,
`nåede ikke`, `færdig`, `spørgsmål`, `kort`, `eksamen`) som i hurtigkommando-tabellen, og vis en kort plan, før du handler.
Punkter uden kendt første ord tolkes efter betydning ("har læst …" = `læst`, "skal nå/husk …" = `opgave`, "forklar …" = `spørgsmål`).
Ét `læst`-emne ad gangen. Kør derefter `planlæg --skriv`, hvis opgaver ændrede sig, og afkryds de behandlede punkter med
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
