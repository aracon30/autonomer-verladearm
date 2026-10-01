import numpy as np
import pytest

from verladearm_vision.acquisition.sick_visionary import (
    CameraParams,
    SickVisionarySource,
    depth_to_points,
)
from verladearm_vision.detection import detect_opening

# Visionary-T Mini: 512 x 424 Pixel, ca. 70° x 60° Blickfeld
CAM = CameraParams(width=512, height=424, fx=256 / np.tan(np.radians(35)),
                   fy=212 / np.tan(np.radians(30)), cx=255.5, cy=211.5)


def render_roof(cam, depth, hole_xy=(0.2, -0.1), hole_d=0.5, inside=1.2):
    """Radiale Distanzen [mm]: ebenes Dach in `depth` m mit offenem Dom, ohne Verzeichnung."""
    xp, yp = np.meshgrid((cam.cx - np.arange(cam.width)) / cam.fx,
                         (cam.cy - np.arange(cam.height)) / cam.fy)
    s0 = np.sqrt(xp**2 + yp**2 + 1)
    x, y = xp * depth, yp * depth
    z = np.where(np.hypot(x - hole_xy[0], y - hole_xy[1]) < hole_d / 2, depth + inside, depth)
    return z * s0 * 1000.0


def test_ebene_in_bekannter_tiefe():
    pts = depth_to_points(render_roof(CAM, 3.5, hole_d=0), CAM)
    assert pts.shape == (CAM.width * CAM.height, 3)
    assert np.allclose(pts[:, 2], 3.5, atol=1e-9)


def test_ungueltige_pixel_entfallen():
    d = render_roof(CAM, 3.5)
    d[:10] = np.nan
    assert len(depth_to_points(d, CAM)) == CAM.width * (CAM.height - 10)


def test_erkennung_auf_simuliertem_tof_bild():
    rng = np.random.default_rng(0)
    d = render_roof(CAM, 3.5) + rng.normal(0, 5, (CAM.height, CAM.width))  # 5 mm Rauschen
    op = detect_opening(depth_to_points(d, CAM))
    assert np.hypot(op.center[0] - 0.2, op.center[1] + 0.1) < 0.02
    assert abs(op.center[2] - 3.5) < 0.02
    assert abs(op.diameter - 0.5) < 0.04


def test_gleiche_formel_wie_sick_bibliothek():
    pc = pytest.importorskip("python_base.PointCloud.PointCloud")
    from python_base.Streaming.ParserHelper import CameraParameters

    small = CameraParams(width=24, height=18, fx=20.0, fy=21.0, cx=11.7, cy=8.4,
                         k1=0.05, k2=-0.01, f2rc=3.0)
    sick_params = CameraParameters(width=24, height=18, fx=20.0, fy=21.0, cx=11.7, cy=8.4,
                                   k1=0.05, k2=-0.01, f2rc=3.0)
    rng = np.random.default_rng(1)
    dist = rng.uniform(2000, 4000, (18, 24))
    ref, _ = pc.convertToPointCloud(dist.ravel(), np.ones(dist.size), np.zeros(dist.size),
                                    sick_params, False)
    ref = np.array(ref)[:, :3] / 1000.0
    assert np.allclose(depth_to_points(dist, small), ref, atol=1e-9)


class FakeSource(SickVisionarySource):
    def __init__(self, frames):
        super().__init__(frames=len(frames), connect=False)
        self._frames = iter(frames)

    def _snapshot(self):
        return next(self._frames), CAM


def test_median_ueber_mehrere_bilder():
    base = render_roof(CAM, 3.5, hole_d=0)
    a, b, c = base.copy(), base.copy(), base.copy()
    b[0, 0] = 9999.0  # Ausreißer
    c[0, 1] = np.nan  # ein Bild ohne Wert
    pts = FakeSource([a, b, c]).grab()
    assert len(pts) == CAM.width * CAM.height
    assert np.allclose(pts[:, 2], 3.5, atol=1e-6)


class LateCamera(SickVisionarySource):
    """Kamera, die erst nach zwei Verbindungsversuchen antwortet (startet noch)."""

    def __init__(self):
        self.attempts = 0
        super().__init__(retry_s=0.02)

    def _connect(self):
        self.attempts += 1
        if self.attempts < 3:
            raise OSError("Verbindung abgelehnt")
        self._control, self._stream = object(), object()


def test_dienst_startet_ohne_kamera_und_verbindet_spaeter():
    import time

    cam = LateCamera()
    deadline = time.time() + 2.0
    while not cam.ready and time.time() < deadline:
        time.sleep(0.01)
    assert cam.ready and cam.attempts == 3
    cam._stop.set()


def test_ohne_kamera_nicht_bereit_und_klarer_fehler():
    cam = SickVisionarySource(ip="192.0.2.1", retry_s=0.05)  # Testadresse, nie erreichbar
    try:
        assert not cam.ready
        with pytest.raises(RuntimeError, match="nicht verbunden"):
            cam.grab()
    finally:
        cam.close()
