"""D2L Brightspace (fx AU, DTU Learn) – Valence REST-API.

.env: BRIGHTSPACE_URL=https://<brightspace-site>
      BRIGHTSPACE_TOKEN=<OAuth2 access token>   (officielt – kun hvis universitetet udsteder det)
  ELLER BRIGHTSPACE_COOKIE=<Cookie-header fra en indlogget browser>  (uofficielt, udløber når du logger ud)
Cookie: log ind i Brightspace i Chrome → Udviklerværktøjer (⌥⌘I) → Network → klik en anmodning til
Brightspace → Request Headers → kopiér hele værdien af "Cookie".
"""
import os
from datetime import datetime, timezone
from pathlib import Path

from .base import LMS, Deadline, Fil, Kursus, LMSFejl, filtype_ok, rent_navn


class Brightspace(LMS):
    navn = "Brightspace"

    def __init__(self):
        super().__init__()
        self.url = os.environ.get("BRIGHTSPACE_URL", "").rstrip("/")
        token, cookie = os.environ.get("BRIGHTSPACE_TOKEN", ""), os.environ.get("BRIGHTSPACE_COOKIE", "")
        if not self.url or not (token or cookie):
            raise LMSFejl("BRIGHTSPACE_URL og BRIGHTSPACE_TOKEN eller BRIGHTSPACE_COOKIE mangler i .env")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.session.headers["Cookie"] = cookie
            self.officiel = False
        self._versioner = None

    def _get(self, sti, **params):
        r = self.session.get(f"{self.url}{sti}", params=params, timeout=60)
        if r.status_code in (401, 403) or "text/html" in r.headers.get("Content-Type", ""):
            raise LMSFejl("Brightspace afviste adgangen (token/cookie udløbet?) – forny i .env")
        r.raise_for_status()
        return r.json()

    def _v(self, produkt):
        if self._versioner is None:
            self._versioner = {p["ProductCode"]: p["LatestVersion"] for p in self._get("/d2l/api/versions/")}
        return self._versioner.get(produkt, {"lp": "1.30", "le": "1.60"}[produkt])

    def kurser(self):
        ud, bookmark = [], None
        while True:
            params = {"orgUnitTypeId": 3}  # 3 = kursusudbud
            if bookmark:
                params["bookmark"] = bookmark
            d = self._get(f"/d2l/api/lp/{self._v('lp')}/enrollments/myenrollments/", **params)
            for item in d.get("Items", []):
                ou, adgang = item.get("OrgUnit", {}), item.get("Access", {})
                if adgang.get("IsActive", True) and adgang.get("CanAccess", True):
                    ud.append(Kursus(str(ou.get("Id")), ou.get("Name", ""), ou.get("Code") or ""))
            side = d.get("PagingInfo") or {}
            if not side.get("HasMoreItems"):
                return ud
            bookmark = side.get("Bookmark")

    def filer(self, kursus_id):
        toc = self._get(f"/d2l/api/le/{self._v('le')}/{kursus_id}/content/toc")
        ud = []

        def gaa(moduler, sti):
            for i, m in enumerate(moduler, 1):
                mappe = sti / f"{i:02d} {rent_navn(m.get('Title'), 60)}" if sti == Path() else sti / rent_navn(m.get("Title"), 60)
                for t in m.get("Topics", []):
                    url = t.get("Url") or ""
                    endelse = Path(url.split("?")[0]).suffix
                    navn = t.get("Title") or Path(url).name
                    if not filtype_ok(navn):
                        navn += endelse
                    if str(t.get("TypeIdentifier", "")).lower() != "file" or not filtype_ok(navn):
                        continue
                    ud.append(Fil(id=str(t["TopicId"]), navn=rent_navn(navn), updated_at=t.get("LastModifiedDate"),
                                  stoerrelse=None, mappe=str(mappe),
                                  laast=bool(t.get("IsLocked")) or bool(t.get("IsHidden")),
                                  data={"ou": kursus_id, "topic": t["TopicId"]}))
                gaa(m.get("Modules", []), mappe)

        gaa(toc.get("Modules", []), Path())
        return ud

    def download(self, fil, maal):
        self._stream(f"{self.url}/d2l/api/le/{self._v('le')}/{fil.data['ou']}/content/topics/{fil.data['topic']}/file", maal)

    def deadlines(self, fra, til, kursus_ids):
        fmt = lambda t: t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        params = {"startDateTime": fmt(fra), "endDateTime": fmt(til)}
        if kursus_ids:
            params["orgUnitIdsCSV"] = ",".join(kursus_ids)
        ud, url = [], f"/d2l/api/le/{self._v('le')}/calendar/events/myEvents/"
        while url:
            d = self._get(url, **params)
            for e in d.get("Objects", []):
                tid = e.get("EndDateTime") or e.get("StartDateTime")
                if tid:
                    ud.append(Deadline(titel=e.get("Title", "?"), tid=datetime.fromisoformat(tid.replace("Z", "+00:00")),
                                       kursus_id=str(e.get("OrgUnitId")) if e.get("OrgUnitId") else None,
                                       type=str((e.get("AssociatedEntity") or {}).get("AssociatedEntityType", ""))))
            nxt = d.get("Next")
            url, params = (nxt.replace(self.url, "") if nxt else None), {}
        return ud
