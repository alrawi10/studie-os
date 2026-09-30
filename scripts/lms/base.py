"""Fælles datatyper og hjælpefunktioner for LMS-adaptere (Canvas, Moodle, Brightspace, itslearning)."""
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

TILLADTE = {".pdf", ".pptx", ".docx"}


@dataclass
class Kursus:
    id: str
    navn: str
    kode: str = ""
    termin: str = ""


@dataclass
class Fil:
    id: str                 # stabilt id i LMS'et (bruges som nøgle i manifestet)
    navn: str               # filnavn inkl. endelse
    updated_at: str | None  # ISO 8601 – ændres når læreren uploader en ny version
    stoerrelse: int | None
    mappe: str              # relativ mappe under kilder/ (fx "03 Uge 38" eller "Filer/Slides")
    laast: bool = False
    data: dict = field(default_factory=dict)  # adapter-specifikt (download-url m.m.)


@dataclass
class Deadline:
    titel: str
    tid: datetime           # tidszone-bevidst
    kursus_id: str | None = None
    type: str = ""
    afleveret: bool | None = None


class LMSFejl(RuntimeError):
    """Forståelig fejl til brugeren (fx udløbet token)."""


class LMS:
    navn = "?"
    officiel = True          # False = uofficielt API (kan gå i stykker uden varsel)
    understoetter_filer = True
    understoetter_deadlines = True

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "full-uni-package (studiesynk)"

    def kurser(self) -> list[Kursus]:
        raise NotImplementedError

    def filer(self, kursus_id: str) -> list[Fil]:
        raise NotImplementedError

    def deadlines(self, fra: datetime, til: datetime, kursus_ids: list[str]) -> list[Deadline]:
        raise NotImplementedError

    def download(self, fil: Fil, maal: Path):
        """Standard: hent fil.data["url"] med adapterens session."""
        self._stream(fil.data["url"], maal)

    def _stream(self, url, maal: Path, **kw):
        maal.parent.mkdir(parents=True, exist_ok=True)
        tmp = maal.with_suffix(maal.suffix + ".part")
        with self.session.get(url, stream=True, timeout=300, **kw) as r:
            r.raise_for_status()
            if "text/html" in r.headers.get("Content-Type", ""):
                raise LMSFejl("serveren returnerede en webside i stedet for filen (login udløbet eller ingen direkte download)")
            with open(tmp, "wb") as f:
                for bid in r.iter_content(1 << 16):
                    f.write(bid)
        tmp.replace(maal)


def rent_navn(navn, maks=90):
    navn = re.sub(r'[/\\:*?"<>|\x00-\x1f]', "-", navn or "").strip().strip(".")
    navn = re.sub(r"\s+", " ", navn)
    endelse = Path(navn).suffix if Path(navn).suffix.lower() in TILLADTE else ""
    stamme = navn[: len(navn) - len(endelse)] if endelse else navn
    return (stamme[: maks - len(endelse)].rstrip() or "uden-navn") + endelse


def filtype_ok(navn):
    return Path(navn or "").suffix.lower() in TILLADTE


def iso(ts):
    """Unix-tid → ISO 8601 (UTC)."""
    from datetime import timezone
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else None
