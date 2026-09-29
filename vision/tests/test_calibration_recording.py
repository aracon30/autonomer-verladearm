from pathlib import Path

import numpy as np

from verladearm_vision.acquisition import FileSource
from verladearm_vision.acquisition.simulation import SimulatedScene
from verladearm_vision.calibration import SensorToArm
from verladearm_vision.calibration.handeye import (
    HandEyeCalibration,
    apply,
    solve_rigid,
    suggest_poses,
)
from verladearm_vision.config import load_config
from verladearm_vision.kinematics import ArmGeometry
from verladearm_vision.plc import MeasureResult, Request
from verladearm_vision.recording import Recorder

BEISPIEL = Path(__file__).parents[1] / "config" / "anlagen" / "beispiel.yaml"


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def test_starre_transformation():
    rng = np.random.default_rng(0)
    t = np.eye(4)
    t[:3, :3] = rot_z(0.3) @ np.diag([1, -1, -1])
    t[:3, 3] = [3, 0.1, 2]
    ps = rng.uniform(-1, 1, (8, 3))
    assert np.allclose(solve_rigid(ps, apply(t, ps)), t)


def test_kalibrierung_findet_versetzten_sensor():
    cfg = load_config(BEISPIEL)
    geom = ArmGeometry(**cfg["arm"])
    guess = np.asarray(cfg["calibration"]["matrix"], float)
    true_t = guess.copy()
    true_t[:3, :3] = guess[:3, :3] @ rot_z(np.radians(2))
    true_t[:3, 3] += [0.05, -0.04, 0.03]
    scene = SimulatedScene(geom, SensorToArm(guess), empty=True, sensor_matrix=true_t, seed=3)
    cal = HandEyeCalibration(geom, guess)
    ws = cfg["commissioning"]
    for pose in suggest_poses(geom, ws["workspace_min"], ws["workspace_max"]):
        scene.prepare(2, pose)
        cal.add(scene.grab(), pose)
    result = cal.solve()
    assert result["used"] == result["total"] >= 8
    assert np.abs(result["matrix"][:3, 3] - true_t[:3, 3]).max() < 0.004
    assert np.abs(result["matrix"][:3, :3] - true_t[:3, :3]).max() < 0.002
    assert result["residuals_m"].mean() < 0.005 and not result["warnings"]


def test_aufzeichnung_und_wiedergabe(tmp_path):
    rec = Recorder(tmp_path, station="Test")
    pts = np.random.default_rng(0).uniform(-1, 1, (500, 3))
    folder = rec.save(Request(job=1, product_id=2), MeasureResult(ok=True, waypoints=[(1, 2, 3)]),
                      pts, {"gesamt_ms": 12.5})
    assert (folder / "punkte.npz").exists() and (folder / "ergebnis.json").exists()
    back = FileSource(tmp_path, "**/punkte.npz").grab()
    assert np.allclose(back, pts, atol=1e-6)


def test_alte_aufzeichnungen_werden_geloescht(tmp_path):
    (tmp_path / "2020-01-01").mkdir()
    (tmp_path / "keine-datumsangabe").mkdir()
    Recorder(tmp_path, keep_days=30).save(Request(), MeasureResult(ok=True), None)
    assert not (tmp_path / "2020-01-01").exists()
    assert (tmp_path / "keine-datumsangabe").exists()
