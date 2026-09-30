"""Antriebe der Achsen J1–J3: Motor, Übersetzung, Geschwindigkeit, Rampen, Getriebespiel.

Aus der Anlagendatei (Abschnitt `drives`, Werte am Gelenk, siehe hardware/antriebe.md). Genutzt
von SPS-Simulator (Fahrzeiten, synchrones Fahren), simuliertem Sensor (Getriebespiel) und
Inbetriebnahmeprüfung (Übersicht, Fahrzeiten). Die echte Achsregelung liegt in SPS/Umrichter;
diese Werte sind dort als Grenzen der Technologieobjekte einzustellen.
"""

from dataclasses import dataclass, field

import numpy as np

from verladearm_vision.kinematics import JOINTS


@dataclass
class Drive:
    motor: str = ""  # Typbezeichnung (nur Anzeige)
    gear: str = ""  # Getriebe/Übersetzungsstufen (nur Anzeige)
    motor_speed: float = 0.0  # Motordrehzahl bei Höchstgeschwindigkeit [1/min]
    ratio: float = 1.0  # Gesamtübersetzung Motor -> Gelenk
    speed_limit: float | None = None  # zulässige Gelenkgeschwindigkeit [°/s] (Getriebe, Anwendung)
    accel_time: float = 1.0  # Rampe 0 -> Höchstgeschwindigkeit [s]
    backlash: float = 0.0  # Spiel am Gelenk [°]
    gravity_preload: bool = False  # Last drückt immer in eine Richtung (Hubachse)
    torque: float | None = None  # Dauermoment am Gelenk [Nm] (nur Anzeige)
    torque_peak: float | None = None  # Spitzenmoment am Gelenk [Nm] (nur Anzeige)
    brake: bool = False
    encoder: str = ""

    @property
    def speed_max(self) -> float:
        """Höchstgeschwindigkeit am Gelenk [°/s]: Motor und Übersetzung, ggf. begrenzt."""
        v = self.motor_speed / self.ratio * 6.0 if self.motor_speed else float("inf")
        return min(v, self.speed_limit or float("inf"))

    @property
    def accel(self) -> float:
        """Beschleunigung am Gelenk [°/s²]."""
        return self.speed_max / max(self.accel_time, 1e-3)

    def move_time(self, delta_deg: float, speed_factor: float = 1.0) -> float:
        """Fahrzeit für einen Winkel [s] mit Trapezprofil (Rampe hoch, konstant, Rampe runter)."""
        d = abs(delta_deg)
        v, a = self.speed_max * speed_factor, self.accel
        if d == 0:
            return 0.0
        if d <= v * v / a:  # Höchstgeschwindigkeit wird nicht erreicht
            return 2.0 * np.sqrt(d / a)
        return d / v + v / a


@dataclass
class Drives:
    axes: dict = field(default_factory=dict)  # "q1" … "q3" -> Drive

    @classmethod
    def from_config(cls, cfg: dict | None):
        cfg = cfg or {}
        return cls({k: Drive(**cfg[k]) if isinstance(cfg.get(k), dict) else Drive()
                    for k in JOINTS})

    @property
    def configured(self) -> bool:
        return any(d.motor_speed or d.speed_limit for d in self.axes.values())

    def sync_time(self, start_deg, target_deg, speed_factor: float = 1.0) -> float:
        """Gemeinsame Fahrzeit: die langsamste Achse bestimmt, die anderen werden angepasst,
        damit alle gleichzeitig ankommen (so fährt die SPS die Stützpunkte)."""
        delta = np.asarray(target_deg, float) - np.asarray(start_deg, float)
        return max(self.axes[k].move_time(d, speed_factor) for k, d in zip(JOINTS, delta,
                                                                          strict=True))

    def backlash(self) -> np.ndarray:
        return np.array([self.axes[k].backlash for k in JOINTS])

    def preload(self) -> np.ndarray:
        return np.array([self.axes[k].gravity_preload for k in JOINTS])


def profile(u: float) -> float:
    """Normierter Weg 0…1 über normierter Zeit 0…1, weiches Anfahren und Bremsen."""
    return u * u * (3 - 2 * u)


class Backlash:
    """Getriebespiel im Modell: Die Abtriebsseite bleibt je nach letzter Bewegungsrichtung um die
    halbe Spielweite hinter dem Antrieb zurück. Bei Hubachsen (gravity_preload) liegt das Spiel
    immer auf der Lastseite: Der Ausleger hängt um die halbe Spielweite tiefer."""

    def __init__(self, backlash_deg, preload, servo_direction=(1, 1, 1)):
        self.half = np.asarray(backlash_deg, float) / 2
        self.preload = np.asarray(preload, bool)
        self.sign = np.asarray(servo_direction, float)  # Servo-Grad -> Modellrichtung
        self.last = None
        self.moving = np.zeros(len(self.half))  # letzte Bewegungsrichtung im Modell

    def __call__(self, servo_deg) -> np.ndarray:
        """Abweichung Gelenk − Antrieb in Modell-Grad nach Fahrt auf servo_deg."""
        q = np.asarray(servo_deg, float) * self.sign
        if self.last is not None:
            moved = q - self.last
            self.moving = np.where(np.abs(moved) > 1e-6, np.sign(moved), self.moving)
        self.last = q
        return np.where(self.preload, -self.half, -self.moving * self.half)
