"""itslearning (fx SDU) – EKSPERIMENTEL. Bruger det REST-API, itslearning-mobilappen bruger (uofficielt).

.env: ITSLEARNING_URL=https://<site>.itslearning.com
      ITSLEARNING_REFRESH_TOKEN=<refresh token>   (foretrukket – fornys automatisk og gemmes tilbage i .env)
  ELLER ITSLEARNING_ACCESS_TOKEN=<access token>  (udløber efter ca. 1 time)
      ITSLEARNING_CLIENT_ID=<valgfri; standard er mobilappens offentlige klient-id>
Ikke testet mod en rigtig konto endnu: kør scripts/lms_test.py og send resultatet (indeholder ingen
hemmeligheder) til projektet, så adapteren kan rettes til. Filer der ikke kan hentes direkte,
lægges manuelt i fag/<fag>/kilder/Manuel/.
"""
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .base import LMS, Deadline, Fil, Kursus, LMSFejl, filtype_ok, rent_navn

MOBIL_KLIENT_ID = "10ae9d30-1853-48ff-81cb-47b58a325685"
ROD = Path(__file__).resolve().parents[2]


def _dato(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


class Itslearning(LMS):
    navn = "itslearning"
    officiel = False

    def __init__(self):
        super().__init__()
        self.url = os.environ.get("ITSLEARNING_URL", "").rstrip("/")
        self.klient = os.environ.get("ITSLEARNING_CLIENT_ID", MOBIL_KLIENT_ID)
        self.refresh = os.environ.get("ITSLEARNING_REFRESH_TOKEN", "")
        access = os.environ.get("ITSLEARNING_ACCESS_TOKEN", "")
        if not self.url or not (self.refresh or access):
            raise LMSFejl("ITSLEARNING_URL og ITSLEARNING_REFRESH_TOKEN (eller _ACCESS_TOKEN) mangler i .env")
        if self.refresh:
            access = self._forny()
        self.session.headers["Authorization"] = f"Bearer {access}"

    def _forny(self):
        r = self.session.post(f"{self.url}/restapi/oauth2/token", timeout=60, data={
            "grant_type": "refresh_token", "refresh_token": self.refresh, "client_id": self.klient})
        if not r.ok:
            raise LMSFejl(f"itslearning afviste refresh-tokenet ({r.status_code}) – hent et nyt")
        d = r.json()
        if d.get("refresh_token") and d["refresh_token"] != self.refresh:
            self._gem_refresh(d["refresh_token"])  # tokenet roterer: gem det nye, ellers virker næste kørsel ikke
        return d["access_token"]

    @staticmethod
    def _gem_refresh(token):
        env = ROD / ".env"
        tekst = env.read_text()
        tekst = re.sub(r"^ITSLEARNING_REFRESH_TOKEN=.*$", f"ITSLEARNING_REFRESH_TOKEN={token}", tekst, flags=re.M)
        env.write_text(tekst)
        os.chmod(env, 0o600)

    def _get(self, sti, **params):
        r = self.session.get(f"{self.url}{sti}", params=params, timeout=60)
        if r.status_code in (401, 403):
            raise LMSFejl("itslearning afviste adgangen (token udløbet?)")
        r.raise_for_status()
        return r.json()

    def _sider(self, sti, **params):
        ud, side = [], 0
        while True:
            d = self._get(sti, PageIndex=side, PageSize=100, **params)
            blok = d.get("EntityArray", d.get("Resources", {}).get("EntityArray", [])) if isinstance(d, dict) else d
            ud += blok
            if len(blok) < 100 or len(ud) >= (d.get("Total", 0) if isinstance(d, dict) else 0):
                return ud
            side += 1

    def kurser(self):
        return [Kursus(str(c.get("CourseId")), c.get("Title", ""), c.get("CourseCode") or c.get("FriendlyName") or "")
                for c in self._sider("/restapi/personal/courses/v2")]

    def filer(self, kursus_id):
        ud = []

        def gaa(elementer, mappe):
            for e in elementer:
                titel = e.get("Title") or ""
                typ = str(e.get("ElementType", "")).lower()
                if typ == "folder" or e.get("IsFolder"):
                    under = self._sider(f"/restapi/personal/courses/{kursus_id}/folders/{e['ElementId']}/resources/v1")
                    gaa(under, mappe / rent_navn(titel, 60))
                    continue
                url = e.get("ContentUrl") or e.get("Url") or ""
                navn = titel if filtype_ok(titel) else titel + Path(url.split("?")[0]).suffix
                if not filtype_ok(navn):
                    continue
                ud.append(Fil(id=str(e.get("ElementId")), navn=rent_navn(navn), updated_at=e.get("LastUpdatedUtc"),
                              stoerrelse=None, mappe=str(mappe), data={"url": url}))

        gaa(self._sider(f"/restapi/personal/courses/{kursus_id}/resources/v1"), Path("Ressourcer"))
        return ud

    def deadlines(self, fra, til, kursus_ids):
        ud = []
        for t in self._sider("/restapi/personal/tasks/v1"):
            tid = _dato(t.get("Deadline"))
            if not tid or not (fra <= tid <= til):
                continue
            ud.append(Deadline(titel=t.get("Title", "?"), tid=tid,
                               kursus_id=str(t.get("CourseId")) if t.get("CourseId") else None,
                               type=t.get("ElementType", "opgave"),
                               afleveret=str(t.get("Status", "")).lower() in ("submitted", "completed", "afleveret")))
        return ud
