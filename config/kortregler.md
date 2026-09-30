# Kortregler – Odontologi (Anki)

Gælder for alle kort, der oprettes via skill'en `anki-kort`.

## Grundprincipper
1. **Ét faktum pr. kort** (minimum information principle). Ingen "nævn alle 8"-kort.
   Lister deles op i flere cloze-huller (`{{c1::…}}`, `{{c2::…}}`) eller flere kort.
2. **Cloze** til definitioner, tal, grænseværdier og sekvenser.
   **Basic** til "hvorfor/hvordan"-spørgsmål og kliniske ræsonnementer.
3. **Dansk fagsprog.** Latinsk eller engelsk term i parentes første gang, fx
   "tandkødslomme (gingival pocket)".
4. **Bagsiden er kort**: højst ca. 25 ord. Mekanisme, kontekst og nuancer hører til i `Uddybning`.
5. **Forbudt:** multiple choice, ja/nej-spørgsmål og spørgsmål, hvor svaret står i spørgsmålet.
6. **Omfang:** ca. 8–15 kort pr. forelæsning/kapitel, medmindre andet ønskes.

## Kildekrav
- Hvert kort skal kunne føres tilbage til et **citat fra NotebookLM**.
- Kort uden kildebelæg oprettes **ikke**. De listes separat som "ubekræftet".
- `Kilde`-feltet: `<Notebook> · <kildetitel> · s./slide <nr>`
  fx `KOF · KOF1 F 1-26.pdf · slide 14`. Kendes siden/sliden ikke, skrives `s. ?`.

## Note-typer
| Note-type | Felter | Bruges til |
|---|---|---|
| `<Studie>-Basic` (fx `Odontologi-Basic`) | Forside, Bagside, Uddybning, Kilde, Billede | hvorfor/hvordan, klinisk ræsonnement |
| `<Studie>-Cloze` | Tekst, Uddybning, Kilde, Billede | definitioner, tal, sekvenser |

## Decks og tags
- Deck: `<Studie>::<Fag>::<Emne>` (fx `Odontologi::KOF::Tyggemuskler`). Fag = kort navn fra `config/fag.json`, Emne = kort navn uden `::`.
- Tags (altid): `fag::<fag>` `emne::<emne>` `ai-genereret`
- Tags (når relevant): `klinisk` (patientsituation/behandlingsvalg), `eksamensrelevant` (fremhævet i pensum/eksamensspørgsmål).
- Emne-tags skrives med små bogstaver og bindestreger, fx `emne::parodontitis-patogenese`.

## Eksempler
**Godt Basic-kort**
- Forside: Hvorfor øger rygning risikoen for parodontitis, selvom gingival blødning ofte er nedsat?
- Bagside: Nikotin giver vasokonstriktion, der maskerer blødning, mens neutrofilfunktion og heling er svækket.
- Uddybning: (mekanisme i 2–4 sætninger)

**Godt Cloze-kort**
- Tekst: Normal pochedybde (probing depth) hos en rask patient er {{c1::1–3 mm}}.

**Dårlige kort (undgå)**
- "Nævn de 6 faktorer ved …" → opdel i cloze-huller.
- "Er plak en biofilm?" → ja/nej.
- "Hvad er gingivitis (betændelse i gingiva)?" → svaret står i spørgsmålet.
