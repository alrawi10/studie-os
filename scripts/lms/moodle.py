"""Moodle (fx AAU, RUC, ITU) – Moodles webservice-API med den studerendes mobilapp-token.

.env: MOODLE_URL=https://<moodle-site>   MOODLE_TOKEN=<token>
Token (vælg én):
  1. Moodle → Profil/Præferencer → "Sikkerhedsnøgler" (Security keys) → nøglen til "Moodle mobile web service".
  2. Uden SSO: https://<site>/login/token.php?username=…&password=…&service=moodle_mobile_app
     (åbn i browseren; kopiér "token"). Virker ikke ved WAYF/SSO-login – brug så nr. 1.
Kræver at universitetet har slået Moodle-appen til (det har langt de fleste).
"""
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .base import LMS, Deadline, Fil, Kursus, LMSFejl, filtype_ok, iso, rent_navn


class Moodle(LMS):
    navn = "Moodle"

    def __init__(self):
        super().__init__()
        self.url = os.environ.get("MOODLE_URL", "").rstrip("/")
        self.token = os.environ.get("MOODLE_TOKEN", "")
        if not self.url or not self.token:
            raise LMSFejl("MOODLE_URL/MOODLE_TOKEN mangler i .env")

    def _ws(self, funktion, **params):
        params.update(wstoken=self.token, wsfunction=funktion, moodlewsrestformat="json")
        r = self.session.post(f"{self.url}/webservice/rest/server.php", data=params, timeout=60)
        r.raise_for_status()
        d = r.json()
        if isinstance(d, dict) and d.get("exception"):
            if d.get("errorcode") in ("invalidtoken", "accessexception"):
                raise LMSFejl(f"Moodle afviste tokenet ({d.get('errorcode')}) – lav et nyt og indsæt i .env")
            raise LMSFejl(f"Moodle-fejl i {funktion}: {d.get('message')}")
        return d

    def kurser(self):
        uid = self._ws("core_webservice_get_site_info")["userid"]
        nu = time.time()
        ud = []
        for c in self._ws("core_enrol_get_users_courses", userid=uid):
            if c.get("hidden") or (c.get("enddate") and c["enddate"] < nu - 30 * 86400):
                continue  # skjulte og afsluttede kurser
            ud.append(Kursus(str(c["id"]), c.get("fullname", ""), c.get("shortname", "")))
        return ud

    def filer(self, kursus_id):
        ud = {}
        for i, sek in enumerate(self._ws("core_course_get_contents", courseid=int(kursus_id))):
            sek_mappe = f"{i:02d} {rent_navn(sek.get('name') or f'Sektion {i}', 60)}"
            for m in sek.get("modules", []):
                for c in m.get("contents") or []:
                    if c.get("type") != "file" or not filtype_ok(c.get("filename")):
                        continue
                    mappe = Path(sek_mappe)
                    if m.get("modname") == "folder":  # Moodle-mapper: behold undermappestrukturen
                        mappe = mappe / rent_navn(m.get("name"), 60)
                        mappe = mappe.joinpath(*[rent_navn(d, 60) for d in (c.get("filepath") or "/").split("/") if d])
                    fid = f"{m['id']}:{c.get('filepath') or '/'}{c['filename']}"
                    ud[fid] = Fil(id=fid, navn=c["filename"], updated_at=iso(c.get("timemodified")),
                                  stoerrelse=c.get("filesize"), mappe=str(mappe),
                                  laast=not m.get("uservisible", True), data={"url": c.get("fileurl")})
        return list(ud.values())

    def download(self, fil, maal):
        url = fil.data["url"]
        self._stream(url + ("&" if "?" in url else "?") + f"token={self.token}", maal)

    def deadlines(self, fra, til, kursus_ids):
        d = self._ws("core_calendar_get_action_events_by_timesort", timesortfrom=int(fra.timestamp()),
                     timesortto=int(til.timestamp()), limitnum=50)
        ud = []
        for e in d.get("events", []):
            kid = str((e.get("course") or {}).get("id", "")) or None
            if kursus_ids and kid and kid not in kursus_ids:
                continue
            ud.append(Deadline(titel=e.get("activityname") or e.get("name") or "?",
                               tid=datetime.fromtimestamp(e["timesort"], tz=timezone.utc),
                               kursus_id=kid, type=e.get("modulename", ""),
                               afleveret=not (e.get("action") or {}).get("actionable", True) if e.get("action") else None))
        return ud
