"""Einheitliche Schnittstelle für alle Sensoren, damit Sensortypen austauschbar bleiben."""

from typing import Protocol

import numpy as np


class PointSource(Protocol):
    def grab(self) -> np.ndarray:
        """Liefert eine Punktwolke als Array (N, 3) in Metern, Sensorkoordinaten."""
        ...
