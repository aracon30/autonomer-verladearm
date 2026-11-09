@echo off
rem Konfigurator (Anlagendatei eines Verladearms im Browser bearbeiten) unter Windows.
rem   tools\konfigurator.bat     -> http://127.0.0.1:8090
rem Beim ersten Start wird .venv angelegt (wie tools\simulation.bat). Beenden: Fenster schliessen.
setlocal
cd /d "%~dp0\.."
if not exist .venv\Scripts\python.exe (
  echo Erstinstallation: virtuelle Umgebung .venv anlegen ...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if not exist .venv\Scripts\python.exe (
    echo Python nicht gefunden. Bitte Python ab 3.10 von python.org installieren.
    pause
    exit /b 1
  )
  .venv\Scripts\python -m pip install -q --upgrade pip
  .venv\Scripts\python -m pip install -q -e ".[dev]"
)
start "Konfigurator" cmd /k ""%CD%\.venv\Scripts\python.exe" -m verladearm_vision.konfigurator --port 8090"
timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:8090
echo Konfigurator: http://127.0.0.1:8090  (Beenden: Fenster "Konfigurator" schliessen)
