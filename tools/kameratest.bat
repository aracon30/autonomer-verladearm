@echo off
rem Kameratest mit der echten SICK-Kamera unter Windows (ohne Arm, ohne SPS). Anleitung: docs\kameratest.md
rem   tools\kameratest.bat            Live-Ansicht der Kamera im Browser (http://127.0.0.1:8000)
rem   tools\kameratest.bat aufnahme   Punktwolken speichern (Enter = Aufnahme, q = Ende)
setlocal
cd /d "%~dp0\.."
set CONFIG=vision\config\anlagen\kameratest.yaml
if not exist .venv\Scripts\python.exe (
  echo Erst einmal tools\simulation.bat starten (legt .venv an^).
  pause
  exit /b 1
)
.venv\Scripts\python -c "import python_base" 2>nul || (
  echo SICK-Bibliothek installieren ...
  .venv\Scripts\python -m pip install -q -e ".[dev,sick]"
)
if /i "%1"=="aufnahme" (
  .venv\Scripts\python -u tools\aufnahme.py --config %CONFIG%
  exit /b 0
)
start "Kamera Live-Ansicht" cmd /k ""%CD%\.venv\Scripts\python.exe" -m verladearm_vision.viewer --config %CONFIG% --port 8000"
timeout /t 8 /nobreak >nul
start "" http://127.0.0.1:8000
echo Live-Ansicht: http://127.0.0.1:8000  (Beenden: Fenster "Kamera Live-Ansicht" schliessen)
