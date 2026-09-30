"""Deadlines fra et kalender-feed (iCal/ICS) – virker med næsten alle LMS'er og skemaer.

.env: ICAL_URL=https://…/feed.ics   (flere adskilles med mellemrum)
Canvas: Kalender → "Kalenderfeed". Brightspace: Kalender → Abonnér. Moodle: Kalender → Eksportér kalender.
itslearning: Kalender → Abonnér/Eksportér. Bruges automatisk af deadlines.py, hvis ICAL_URL er sat.
"""
import os
from datetime import date, datetime, time, timezone

import requests

from .base import Deadline


def deadlines(fra, til):
    urls = os.environ.get("ICAL_URL", "").split()
    if not urls:
        return []
    from icalendar import Calendar

    ud = []
    for url in urls:
        cal = Calendar.from_ical(requests.get(url.replace("webcal://", "https://"), timeout=60).content)
        for ev in cal.walk("VEVENT"):
            t = (ev.get("DTEND") or ev.get("DTSTART")).dt
            if isinstance(t, date) and not isinstance(t, datetime):
                t = datetime.combine(t, time(23, 59), timezone.utc)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if fra <= t <= til:
                ud.append(Deadline(titel=str(ev.get("SUMMARY", "?")), tid=t, type="kalender",
                                   kursus_id=str(ev.get("CATEGORIES").cats[0]) if ev.get("CATEGORIES") else None))
    return ud
