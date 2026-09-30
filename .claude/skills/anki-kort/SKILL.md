---
name: anki-kort
description: Bruges når der skal laves Anki-kort ud fra pensum – fx "læst <fag> <emne>", "kort <fag> <emne>" eller "lav kort om …". Kildebelagte kort efter faste kortregler; oprettes direkte i Anki eller leveres som importfil.
---

# Anki-kort fra pensum

Laver kildebelagte Anki-kort og opretter dem i `<Studie>::<Fag>::<Emne>`.
**Kortreglerne er bindende:** `config/kortregler.md` (projektmappen) eller `references/kortregler.md` (denne skill).

## 0. Find ud af, hvor du kører (gør det stille, ét tjek)
| Tjek | Ja → | Nej → |
|---|---|---|
| Projektmappe med `config/fag.json`? (Claude Code) | Slå fag op dér (`studie`, `notebook_id`, `notebook_titel`, `anki_deck`) | Spørg om studie/fag, eller brug projektets instruktioner |
| NotebookLM-værktøjer (`notebook_query`)? | Pensum hentes med citater fra NotebookLM | Brug projektets filer/vedhæftede PDF'er. Mangler de, så bed om kilden (upload/indsæt) |
| Anki-værktøjer (`add_notes`)? | Opret kortene direkte (trin 7) | Lever en **importfil** (trin 7b) |
| Terminal + `scripts/billede.py`? | Figurer fra pensum (trin 5b) | Ingen billeder, medmindre brugeren selv vedhæfter et |

## Arbejdsgang
1. **Afklar fag og emne.** Deck = `<anki_deck eller Studie::Fag>::<Emne>`, fx `Odontologi::KOF::Tyggemuskler`.
   **"læst <fag> <emne>"** er brugerens faste arbejdsgang (kort laves lige efter, at et emne er læst):
   afgræns til præcis de kilder, der hører til det læste (NotebookLM: `source_ids` fundet med `source_list`),
   og lav ikke kort om stof, brugeren ikke har læst endnu.
2. **Hent stoffet med citater.** NotebookLM (evt. afgrænset), ellers projektets filer:
   > "Giv mig de centrale fakta, definitioner, mekanismer, klassifikationer, tal/grænseværdier og kliniske pointer om <emne>. Angiv for hvert punkt det præcise citat, kildens titel og side-/slidenummer."

   Stil opfølgende spørgsmål, hvis citater eller sidetal mangler.
3. **Tjek for dubletter** (kun med Anki-værktøjer): `find_notes` med `tag:emne::<emne>` og derefter 2–4 centrale
   nøgleord i hele samlingen → `notes_info`. Spring over, hvad der er dækket, og nævn det kort med deck-navn.
   Uden Anki: spørg, om der allerede findes kort om emnet.
4. **Lav kortene** efter kortreglerne: ét faktum pr. kort, cloze til definitioner/tal/sekvenser, basic til
   hvorfor/hvordan og klinik, fagsprog med latinsk/engelsk term i parentes første gang, bagside ≤ ca. 25 ord,
   mekanisme i `Uddybning`, ca. 8–15 kort pr. forelæsning/kapitel.
5. **Kvalitetstjek.** Hvert kort skal pege på et konkret citat fra trin 2. Kort uden kildebelæg oprettes **ikke**,
   men vises i en separat liste "Ubekræftet". Ingen ja/nej, ingen multiple choice, svaret står ikke i spørgsmålet.
5b. **Billeder** (kun i projektmappen) til kort om noget visuelt (histologi, røntgen, kliniske fotos, anatomi,
   klassifikationsfigurer). Brug den citerede kilde og side/slide:
   ```bash
   uv run -q --python 3.12 --with pymupdf --with python-pptx --with pillow --with requests \
     scripts/billede.py --fag <Fag> --kilde "<kildetitel>" --side <nr> --figur 1
   ```
   (`--figur N` beskærer til figur N på en PDF-side, `--beskaer x0,y0,x1,y1` manuelt, PPTX giver det største billede.)
   **Se altid selv på PNG'en**, før den bruges. Den skal vise det, kortet spørger om, og ikke afsløre svaret.
   Ikke på rene definitionskort. Når kortet er godkendt: kør igen med `--anki`, og sæt `<img src="…">` i `Billede`.
   Mange strukturer på én figur → foreslå Ankis indbyggede Image Occlusion med stien til PNG'en.
6. **Vis en tabel** til godkendelse:

   | # | Type | Forside / Tekst | Bagside | Billede | Kilde | Tags |
   |---|---|---|---|---|---|---|

   Opret først, når brugeren skriver **ok** (eller rettelser → opdatér tabellen). Har brugeren skrevet
   **"direkte"**, må kortene oprettes uden godkendelse.
7. **Opret i Anki** (Anki-værktøjer): `create_deck` ved behov, derefter ét `add_notes` pr. note-type med
   `tags: ["fag::<fag>", "emne::<emne>", "ai-genereret", …]`. Rapportér antal oprettede og eventuelle fejl.
7b. **Importfil** (uden Anki-værktøjer): lav én tekstfil pr. note-type som downloadbar fil
   (`<emne>-basic.txt` og `<emne>-cloze.txt`; kan filer ikke oprettes, så som kodeblokke). Tabulator mellem felter,
   HTML tilladt, ingen tabulatorer/linjeskift inde i felterne (brug `<br>`):
   ```
   #separator:tab
   #html:true
   #notetype:<Studie>-Basic
   #deck:<Studie>::<Fag>::<Emne>
   #tags column:6
   <Forside>	<Bagside>	<Uddybning>	<Kilde>		fag::<fag> emne::<emne> ai-genereret
   ```
   Cloze-filen: `#notetype:<Studie>-Cloze`, kolonnerne `Tekst, Uddybning, Kilde, Billede, tags` og `#tags column:5`.
   Forklar importen: **Anki → Filer → Importér → vælg filen**. Findes note-typen ikke, så vælg en note-type med
   samme antal felter i importdialogen (fx den indbyggede Basic/Grundlæggende eller Cloze) – eller opret
   `<Studie>-Basic`/`-Cloze` først (felterne står i kortreglerne).

## Feltformat
- `Kilde`: `<notebook- eller projektnavn> · <kildetitel> · s./slide <nr>`
- `Uddybning`: 1–4 sætninger om mekanisme/kontekst. Må gerne indeholde det ordrette citat i kursiv.
- `Billede`: `<img src="…">` fra trin 5b eller et billede, brugeren leverer (`store_media_file`). Ellers tomt.
- Cloze: `{{c1::…}}`. Brug flere huller (c1, c2 …) i samme note til sekvenser i stedet for én lang liste.
