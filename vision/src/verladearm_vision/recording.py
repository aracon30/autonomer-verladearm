"""Aufzeichnung jedes Auftrags: Punktwolke, Auftrag, Ergebnis und Zusatzinfos.

Ablage: <dir>/<JJJJ-MM-TT>/<HHMMSS_mmm>_job<N>/
    punkte.npz     Punktwolke (N x 3, float32, Sensorkoordinaten, Meter)
    ergebnis.json  Zeit, Anlage, Auftrag der SPS, Ergebnis an die SPS, Zusatzinfos

Zweck: Nachweis der Positioniergenauigkeit (N-01), Fehlersuche, Wiedergabe mit
`source: {type: file, path: <dir>, pattern: "**/punkte.npz"}`, Auswertung mit
`tools/auswertung.py`. Fehler beim Speichern werden nur protokolliert und stören nie die Messung.
"""

import dataclasses
import json
import logging
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)


def _jsonable(obj):
    if dataclasses.is_dataclass(obj):
        return {k: _jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


class Recorder:
    def __init__(self, dir: str | Path = "data/aufzeichnung", keep_days: int = 60,
                 enabled: bool = True, station: str = ""):
        self.dir = Path(dir)
        self.keep_days = keep_days
        self.enabled = enabled
        self.station = station
        self._cleaned_on = None

    def save(self, request, result, points: np.ndarray | None, info: dict | None = None):
        """Speichert einen Auftrag; liefert den Ordner oder None."""
        if not self.enabled:
            return None
        now = datetime.now()
        folder = self.dir / f"{now:%Y-%m-%d}" / f"{now:%H%M%S}_{now.microsecond // 1000:03d}"
        folder = folder.with_name(folder.name + f"_job{getattr(request, 'job', 0)}")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if points is not None:
                np.savez_compressed(folder / "punkte.npz", points=points.astype(np.float32))
            record = {
                "zeit": now.isoformat(timespec="milliseconds"),
                "anlage": self.station,
                "auftrag": _jsonable(request),
                "ergebnis": _jsonable(result),
                "info": _jsonable(info or {}),
            }
            (folder / "ergebnis.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError as e:
            log.warning("Aufzeichnung nicht gespeichert: %s", e)
            return None
        self._cleanup(now.date())
        return folder

    def _cleanup(self, today: date):
        """Tagesordner älter als keep_days löschen (einmal pro Tag)."""
        if self._cleaned_on == today or not self.keep_days:
            return
        self._cleaned_on = today
        limit = today - timedelta(days=self.keep_days)
        for day in self.dir.iterdir():
            try:
                if day.is_dir() and datetime.strptime(day.name, "%Y-%m-%d").date() < limit:
                    shutil.rmtree(day)
                    log.info("Alte Aufzeichnung gelöscht: %s", day)
            except (ValueError, OSError):
                continue
