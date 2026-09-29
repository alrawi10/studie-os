---
name: eksamenssvar
description: Bruges når der skal skrives et dybt, pensumforankret eksamenssvar eller en aflevering i et odontologifag
---

# Eksamenssvar i professorniveau

## Principper
- Dybt, præcist og fagligt stringent, på niveau med en censor/professor. Dansk fagsprog
  med latinske/engelske termer i parentes første gang.
- **Forankret i kurslitteraturen.** Hent altid stoffet via NotebookLM med citater
  (MCP `gemini-notebook-mcp` → `notebook_query`; fallback `~/.local/bin/nlm notebook query <id> "<spørgsmål>" --json`).
  Notebook-id står i `config/fag.json`.
- Kildehierarki: 1) NotebookLM (pensum) → 2) `fag/<fag>/noter/` → 3) egen viden, tydeligt markeret
  med **[uden for pensum]**.

## Arbejdsgang
1. Afklar fag og spørgsmål. Find notebook'en i `config/fag.json`.
2. Stil 2–4 målrettede spørgsmål til NotebookLM (definition, mekanisme, klinik, diagnostik/behandling),
   og kræv citater med kildetitel og side/slide. Tjek `fag/<fag>/noter/` for egne noter.
3. Skriv svaret i denne struktur:
   1. **Definition**, præcis og afgrænsende
   2. **Mekanisme / patofysiologi**, kausalkæde trin for trin
   3. **Klinisk betydning**: symptomer, fund, risikofaktorer, prognose
   4. **Diagnostik og behandling** (når relevant): undersøgelser, differentialdiagnoser, behandlingsvalg og begrundelse
   5. **Konklusion**: 3–5 linjer, der besvarer spørgsmålet direkte
4. Citér løbende med `[n]`. Afslut med en referenceliste:
   - Til eksamensforberedelse: `[n] <notebook_titel> · <kildetitel> · s./slide <nr>`
   - Til **afleveringer**: Vancouver-format, fx
     `1. Lindhe J, Lang NP, Berglundh T, et al. Clinical periodontology and implant dentistry. 6th ed. Chichester: Wiley Blackwell; 2015. p. 123-45.`
     (Forfattere/år/sider tages fra kildens titelblad. Mangler de, så skriv hvad der mangler i stedet for at gætte.)
5. Gem svaret i `fag/<fag>/eksamen/<emne-med-bindestreger>.md` med overskrift, dato og spørgsmålet øverst.
6. **Tilbyd bagefter** at lave Anki-kort ud fra svaret via skill'en `anki-kort` (de citerede kilder genbruges).
