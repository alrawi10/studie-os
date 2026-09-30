---
name: eksamenssvar
description: Bruges når der skal skrives et dybt, pensumforankret eksamenssvar, en mundtlig eksamensdisposition eller en aflevering – fx "eksamen <fag> <spørgsmål>". Svar i professorniveau med citater fra kurslitteraturen.
---

# Eksamenssvar i professorniveau

## Principper
- Dybt, præcist og fagligt stringent, på niveau med en censor/professor. Fagsprog med latinske/engelske
  termer i parentes første gang. Svar på brugerens sprog (standard: dansk).
- **Forankret i kurslitteraturen** – altid med citater (kildetitel + side/slide):
  NotebookLM-værktøjer (`notebook_query`) hvis de findes; ellers projektets filer/vedhæftede PDF'er.
  I projektmappen (Claude Code) står notebook-id i `config/fag.json`, og CLI-fallback er
  `~/.local/bin/nlm notebook query <id> "<spørgsmål>" --json`.
- Kildehierarki: 1) pensum (NotebookLM/projektfiler) → 2) brugerens egne noter (`fag/<fag>/noter/` eller
  vedhæftede noter) → 3) egen viden, tydeligt markeret med **[uden for pensum]**.
  Dækker pensum ikke spørgsmålet, så sig det, før du svarer fra egen viden.

## Arbejdsgang
1. Afklar fag og spørgsmål (og om det er til eksamenslæsning, mundtlig disposition eller en aflevering).
2. Stil 2–4 målrettede spørgsmål til pensum (definition, mekanisme, klinik, diagnostik/behandling),
   og kræv citater med kildetitel og side/slide.
3. Skriv svaret i denne struktur (tilpas ikke-kliniske fag: definition → teori/mekanisme → betydning/anvendelse → konklusion):
   1. **Definition**, præcis og afgrænsende
   2. **Mekanisme / patofysiologi**, kausalkæde trin for trin
   3. **Klinisk betydning**: symptomer, fund, risikofaktorer, prognose
   4. **Diagnostik og behandling** (når relevant): undersøgelser, differentialdiagnoser, behandlingsvalg og begrundelse
   5. **Konklusion**: 3–5 linjer, der besvarer spørgsmålet direkte
4. Citér løbende med `[n]`. Afslut med en referenceliste:
   - Til eksamensforberedelse: `[n] <notebook/projekt> · <kildetitel> · s./slide <nr>`
   - Til **afleveringer**: Vancouver-format, fx
     `1. Lindhe J, Lang NP, Berglundh T, et al. Clinical periodontology and implant dentistry. 6th ed. Chichester: Wiley Blackwell; 2015. p. 123-45.`
     (Forfattere/år/sider tages fra kildens titelblad. Mangler de, så skriv hvad der mangler i stedet for at gætte.)
5. **Gem svaret:** i projektmappen som `fag/<fag>/eksamen/<emne-med-bindestreger>.md` (overskrift, dato og
   spørgsmålet øverst); ellers som et dokument/en downloadbar fil, brugeren kan gemme.
6. **Tilbyd bagefter** at lave Anki-kort ud fra svaret via skill'en `anki-kort` (de citerede kilder genbruges).
