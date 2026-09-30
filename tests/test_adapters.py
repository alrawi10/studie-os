"""Tests af LMS-adapterne med simulerede API-svar (formet efter platformenes dokumentation).
Tester vores parsing og mappestruktur – ikke at de rigtige API'er svarer sådan.

Kør:  uv run --with pytest --with requests --with python-dotenv --with icalendar pytest tests -q
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lms import hent_adapter  # noqa: E402


class Svar:
    def __init__(self, data, status=200, ctype="application/json"):
        self._data, self.status_code, self.ok = data, status, status < 400
        self.headers, self.links = {"Content-Type": ctype}, {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.status_code)


NU = datetime(2026, 10, 1, tzinfo=timezone.utc)


def test_moodle(monkeypatch):
    monkeypatch.setenv("MOODLE_URL", "https://moodle.test")
    monkeypatch.setenv("MOODLE_TOKEN", "t")
    svar = {
        "core_webservice_get_site_info": {"userid": 7},
        "core_enrol_get_users_courses": [
            {"id": 11, "fullname": "Anatomi", "shortname": "ANA", "enddate": 0},
            {"id": 12, "fullname": "Gammelt", "shortname": "OLD", "enddate": 1000},
        ],
        "core_course_get_contents": [
            {"name": "Uge 1", "modules": [
                {"id": 5, "modname": "resource", "uservisible": True, "contents": [
                    {"type": "file", "filename": "F1.pdf", "filepath": "/", "fileurl": "https://moodle.test/f1",
                     "timemodified": 1700000000, "filesize": 10}]},
                {"id": 6, "modname": "folder", "name": "Slides", "contents": [
                    {"type": "file", "filename": "s.pptx", "filepath": "/uge1/", "fileurl": "u", "timemodified": 1},
                    {"type": "file", "filename": "video.mp4", "filepath": "/", "fileurl": "u"}]},
                {"id": 7, "modname": "url", "contents": [{"type": "url", "fileurl": "https://x"}]}]}],
        "core_calendar_get_action_events_by_timesort": {"events": [
            {"activityname": "Opgave 1", "timesort": int(NU.timestamp()) + 3600, "course": {"id": 11},
             "modulename": "assign", "action": {"actionable": True}}]},
    }
    lms = hent_adapter("moodle")
    monkeypatch.setattr(lms.session, "post", lambda url, data, timeout: Svar(svar[data["wsfunction"]]))
    assert [k.id for k in lms.kurser()] == ["11"]  # afsluttet kursus filtreret fra
    filer = {f.navn: f for f in lms.filer("11")}
    assert set(filer) == {"F1.pdf", "s.pptx"}
    assert filer["s.pptx"].mappe == "00 Uge 1/Slides/uge1"
    d = lms.deadlines(NU, NU + timedelta(days=7), ["11"])
    assert d[0].titel == "Opgave 1" and d[0].afleveret is False


def test_brightspace(monkeypatch):
    monkeypatch.setenv("BRIGHTSPACE_URL", "https://bs.test")
    monkeypatch.setenv("BRIGHTSPACE_COOKIE", "d2lSessionVal=x")
    monkeypatch.delenv("BRIGHTSPACE_TOKEN", raising=False)
    svar = {
        "/d2l/api/versions/": [{"ProductCode": "lp", "LatestVersion": "1.40"}, {"ProductCode": "le", "LatestVersion": "1.70"}],
        "/d2l/api/lp/1.40/enrollments/myenrollments/": {
            "Items": [{"OrgUnit": {"Id": 99, "Name": "Farmakologi", "Code": "FA"}, "Access": {"IsActive": True, "CanAccess": True}}],
            "PagingInfo": {"HasMoreItems": False}},
        "/d2l/api/le/1.70/99/content/toc": {"Modules": [{"Title": "Forelæsninger", "Topics": [
            {"TopicId": 1, "Title": "F1 Intro", "Url": "/content/enforced/99/F1.pdf", "TypeIdentifier": "File",
             "LastModifiedDate": "2026-09-01T10:00:00.000Z"},
            {"TopicId": 2, "Title": "Link", "Url": "https://x", "TypeIdentifier": "Link"}],
            "Modules": [{"Title": "Uge 2", "Topics": [{"TopicId": 3, "Title": "Noter.docx", "Url": "/n.docx",
                                                       "TypeIdentifier": "File", "IsHidden": True}], "Modules": []}]}]},
        "/d2l/api/le/1.70/calendar/events/myEvents/": {"Objects": [
            {"Title": "Aflevering", "EndDateTime": "2026-10-02T21:59:00.000Z", "OrgUnitId": 99}], "Next": None},
    }
    lms = hent_adapter("brightspace")
    assert lms.officiel is False
    monkeypatch.setattr(lms.session, "get", lambda url, params=None, timeout=None: Svar(svar[url.replace("https://bs.test", "")]))
    assert lms.kurser()[0].navn == "Farmakologi"
    filer = {f.navn: f for f in lms.filer("99")}
    assert set(filer) == {"F1 Intro.pdf", "Noter.docx"}
    assert filer["F1 Intro.pdf"].mappe == "01 Forelæsninger" and filer["Noter.docx"].laast
    assert filer["Noter.docx"].mappe == "01 Forelæsninger/Uge 2"
    assert lms.deadlines(NU, NU + timedelta(days=7), ["99"])[0].kursus_id == "99"


def test_itslearning(monkeypatch):
    monkeypatch.setenv("ITSLEARNING_URL", "https://sdu.test")
    monkeypatch.setenv("ITSLEARNING_ACCESS_TOKEN", "a")
    monkeypatch.delenv("ITSLEARNING_REFRESH_TOKEN", raising=False)
    svar = {
        "/restapi/personal/courses/v2": {"EntityArray": [{"CourseId": 3, "Title": "Jura 1"}], "Total": 1},
        "/restapi/personal/courses/3/resources/v1": {"Resources": {"EntityArray": [
            {"ElementId": 10, "Title": "Uge 1", "ElementType": "Folder"},
            {"ElementId": 11, "Title": "Pensumliste.pdf", "ElementType": "File", "ContentUrl": "https://sdu.test/f11"}]},
            "Total": 2},
        "/restapi/personal/courses/3/folders/10/resources/v1": {"EntityArray": [
            {"ElementId": 12, "Title": "Slides", "ElementType": "LearningToolElement", "ContentUrl": "https://sdu.test/s.pptx"}],
            "Total": 1},
        "/restapi/personal/tasks/v1": {"EntityArray": [
            {"Title": "Opgave", "Deadline": "2026-10-03T10:00:00Z", "CourseId": 3, "Status": "NotSubmitted"},
            {"Title": "Gammel", "Deadline": "2025-01-01T10:00:00Z"}], "Total": 2},
    }
    lms = hent_adapter("itslearning")
    monkeypatch.setattr(lms.session, "get", lambda url, params=None, timeout=None: Svar(svar[url.replace("https://sdu.test", "")]))
    assert lms.kurser()[0].id == "3"
    filer = {f.navn: f for f in lms.filer("3")}
    assert set(filer) == {"Pensumliste.pdf", "Slides.pptx"}
    assert filer["Slides.pptx"].mappe == "Ressourcer/Uge 1"
    d = lms.deadlines(NU, NU + timedelta(days=7), [])
    assert [x.titel for x in d] == ["Opgave"] and d[0].afleveret is False


def test_ukendt_og_manuel():
    assert hent_adapter("manuel") is None
    with pytest.raises(Exception):
        hent_adapter("blackboard")
