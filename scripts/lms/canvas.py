"""Canvas LMS (KU Absalon, CBS m.fl.) – officielt REST-API med personligt adgangstoken.

.env: CANVAS_API_URL=https://<canvas>/api/v1   CANVAS_API_TOKEN=<token>
Token: Konto → Indstillinger → "+ Nyt adgangstoken".
"""
import os
import re
from datetime import datetime
from pathlib import Path

from .base import LMS, Deadline, Fil, Kursus, LMSFejl, filtype_ok, rent_navn


class Canvas(LMS):
    navn = "Canvas"

    def __init__(self):
        super().__init__()
        self.api = os.environ.get("CANVAS_API_URL", "").rstrip("/")
        token = os.environ.get("CANVAS_API_TOKEN", "")
        if not self.api or not token:
            raise LMSFejl("CANVAS_API_URL/CANVAS_API_TOKEN mangler i .env")
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _alle(self, url, **params):
        """GET med Canvas-paginering. None ved 401/403/404 (fx skjult Files-fane)."""
        params.setdefault("per_page", 100)
        ud = []
        while url:
            r = self.session.get(url, params=params, timeout=60)
            if r.status_code == 401:
                raise LMSFejl("Canvas afviste tokenet (udløbet?) – lav et nyt og indsæt i .env")
            if r.status_code in (403, 404):
                return None
            r.raise_for_status()
            ud += r.json()
            url, params = r.links.get("next", {}).get("url"), None
        return ud

    def kurser(self):
        cs = self._alle(f"{self.api}/courses", enrollment_state="active", **{"include[]": "term"}) or []
        return [Kursus(str(c["id"]), c.get("name", ""), c.get("course_code", ""), (c.get("term") or {}).get("name", ""))
                for c in cs if "name" in c]

    def filer(self, kursus_id):
        ud = {}
        moduler = self._alle(f"{self.api}/courses/{kursus_id}/modules", **{"include[]": "items"}) or []
        for i, modul in enumerate(sorted(moduler, key=lambda m: m.get("position", 0)), 1):
            mappe = f"{i:02d} {rent_navn(modul.get('name', 'Modul'), 60)}"
            items = modul.get("items")
            if items is None:  # store moduler returnerer ikke items inline
                items = self._alle(f"{self.api}/courses/{kursus_id}/modules/{modul['id']}/items") or []
            for item in items:
                if item.get("type") != "File" or str(item.get("content_id")) in ud:
                    continue
                r = self.session.get(f"{self.api}/courses/{kursus_id}/files/{item['content_id']}", timeout=60)
                if r.ok and filtype_ok(r.json().get("display_name")):
                    ud[str(item["content_id"])] = self._fil(r.json(), mappe)

        mapper = {m["id"]: m.get("full_name", "") for m in (self._alle(f"{self.api}/courses/{kursus_id}/folders") or [])}
        for f in self._alle(f"{self.api}/courses/{kursus_id}/files") or []:
            if str(f["id"]) in ud or not filtype_ok(f.get("display_name")):
                continue
            sti = re.sub(r"^course files/?", "", mapper.get(f.get("folder_id"), ""))
            ud[str(f["id"])] = self._fil(f, str(Path("Filer", *[rent_navn(d, 60) for d in sti.split("/") if d])))
        return list(ud.values())

    @staticmethod
    def _fil(f, mappe):
        return Fil(id=str(f["id"]), navn=f.get("display_name") or f.get("filename"), updated_at=f.get("updated_at"),
                   stoerrelse=f.get("size"), mappe=mappe, laast=bool(f.get("locked_for_user")) or not f.get("url"),
                   data={"url": f.get("url")})

    def deadlines(self, fra: datetime, til: datetime, kursus_ids):
        params = {"start_date": fra.isoformat(), "end_date": til.isoformat(),
                  "context_codes[]": [f"course_{k}" for k in kursus_ids]}
        ud = []
        for p in self._alle(f"{self.api}/planner/items", **params) or []:
            plan = p.get("plannable") or {}
            sub = p.get("submissions") if isinstance(p.get("submissions"), dict) else {}
            ud.append(Deadline(titel=plan.get("title") or plan.get("name") or "?",
                               tid=datetime.fromisoformat(p["plannable_date"].replace("Z", "+00:00")),
                               kursus_id=str(p.get("course_id")) if p.get("course_id") else None,
                               type=p.get("plannable_type", ""), afleveret=sub.get("submitted")))
        return ud
