"""LMS-adaptere. Vælg platform med "lms" i config/fag.json."""
from .base import LMS, Deadline, Fil, Kursus, LMSFejl

PLATFORME = {
    "canvas": ("canvas", "Canvas"),
    "moodle": ("moodle", "Moodle"),
    "brightspace": ("brightspace", "Brightspace"),
    "itslearning": ("itslearning", "Itslearning"),
}


def hent_adapter(navn: str) -> LMS | None:
    """Returnerer adapteren for platformen, eller None for "manuel" (kun manuelle filer + iCal)."""
    navn = (navn or "canvas").lower()
    if navn == "manuel":
        return None
    if navn not in PLATFORME:
        raise LMSFejl(f"Ukendt LMS '{navn}' – vælg en af: {', '.join(PLATFORME)}, manuel")
    modul, klasse = PLATFORME[navn]
    from importlib import import_module
    return getattr(import_module(f".{modul}", __name__), klasse)()
