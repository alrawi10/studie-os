---
name: Testresultat fra mit universitet
about: Del resultatet af scripts/lms_test.py, så adapteren til dit universitet kan rettes til
title: "LMS-test: <universitet> (<platform>)"
labels: lms-test
---

**Universitet og studie:** (fx AAU, Medicin)
**Platform (`lms` i config/fag.json):** canvas / moodle / brightspace / itslearning / manuel
**Adgang:** (fx Moodle-sikkerhedsnøgle, Brightspace-cookie, itslearning refresh-token)

### Output fra `scripts/lms_test.py`
Scriptet udskriver ingen tokens, cookies eller filindhold. Tjek det alligevel, før du indsætter det.
```
(indsæt her)
```

### Hvis noget fejlede: API-struktur
Kør `scripts/lms_test.py --raa <sti>` for den del, der fejlede (fx `/restapi/personal/courses/v2`),
og indsæt resultatet. Det viser kun feltnavne, ingen værdier.
```
(indsæt her)
```

**Andet, der er værd at vide:** (fx SSO-login, filer der ikke kunne hentes)
