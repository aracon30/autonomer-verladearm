"""Transformation Sensorkoordinaten -> Koordinaten der Armbasis.

Die 4x4-Matrix wird bei der Hand-Auge-Kalibrierung ermittelt (z. B. Anfahren von Kalibrierpunkten
mit dem Arm und Vergleich mit der Sensormessung) und in der Konfiguration abgelegt.
"""

import numpy as np


class SensorToArm:
    def __init__(self, matrix):
        self.T = np.asarray(matrix, dtype=float)
        if self.T.shape != (4, 4):
            raise ValueError("Kalibriermatrix muss 4x4 sein")

    def point(self, p: np.ndarray) -> np.ndarray:
        return self.T[:3, :3] @ p + self.T[:3, 3]

    def direction(self, v: np.ndarray) -> np.ndarray:
        r = self.T[:3, :3] @ v
        return r / np.linalg.norm(r)
