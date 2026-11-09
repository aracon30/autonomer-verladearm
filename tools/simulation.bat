@echo off
rem Simulation unter Windows (Laptop, spaeter Beckhoff-IPC): SPS-Simulator, Vision-Dienst und
rem Live-Ansicht in je einem eigenen Fenster.
rem
rem   tools\simulation.bat              Dauertest (Verladung auf Verladung)
rem   tools\simulation.bat bedienen     selbst bedienen im Fenster "SPS-Simulator" (? = Hilfe)
rem   tools\simulation.bat echtzeit     alles in echter Zeit (Befuellung je Kammer ca. 25 min)
rem   tools\simulation.bat bedienen echtzeit   beides
rem
rem Voraussetzung: Python ab 3.10 von python.org (beim Installieren "Add python.exe to PATH").
rem Beim ersten Start wird .venv angelegt und alles installiert (Internet noetig, ca. 2 min).
rem Beenden: die drei Fenster schliessen.
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."
set CONFIG=vision\config\anlagen\simulation.yaml
set PORT=8000

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
set PY=%CD%\.venv\Scripts\python.exe
if not exist data\logs mkdir data\logs

set SPS_ARGS=tools\plc_simulator.py --config %CONFIG% --zeitraffer 0.25
set BEDIENEN=
for %%A in (%*) do (
  if /i "%%A"=="bedienen" set BEDIENEN=1& set SPS_ARGS=!SPS_ARGS! --bedienen
  if /i "%%A"=="echtzeit" set SPS_ARGS=!SPS_ARGS! --echtzeit
)

start "SPS-Simulator" cmd /k ""%PY%" -u %SPS_ARGS%"
timeout /t 3 /nobreak >nul
start "Vision-Dienst" cmd /k ""%PY%" -m verladearm_vision.service.main --config %CONFIG%"
start "Live-Ansicht" cmd /k ""%PY%" -m verladearm_vision.viewer --opcua --config %CONFIG% --port %PORT%"
timeout /t 6 /nobreak >nul
start "" http://127.0.0.1:%PORT%

echo.
echo Simulation laeuft in drei Fenstern: SPS-Simulator, Vision-Dienst, Live-Ansicht.
echo Live-Ansicht: http://127.0.0.1:%PORT%  (oeffnet sich im Browser)
if defined BEDIENEN echo Bedienung: Befehle im Fenster "SPS-Simulator" eingeben (? = Hilfe).
echo Beenden: die drei Fenster schliessen.
