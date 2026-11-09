@echo off
rem Simulation unter Windows (Laptop, spaeter Beckhoff-IPC): SPS-Simulator, Vision-Dienst und
rem Live-Ansicht in je einem eigenen Fenster. Optionen beliebig kombinierbar:
rem
rem   tools\simulation.bat                    Dauertest (Verladung auf Verladung)
rem   tools\simulation.bat bedienen           selbst bedienen im Fenster "SPS-Simulator" (? = Hilfe)
rem   tools\simulation.bat echtzeit           alles in echter Zeit (Befuellung je Kammer ca. 25 min)
rem   tools\simulation.bat anlage NAME        Anlagendatei vision\config\anlagen\NAME.yaml simulieren
rem                                           (z. B. im Konfigurator angelegt)
rem   tools\simulation.bat kammern 3          jedes Fahrzeug mit genau 3 Kammern (1-3)
rem   tools\simulation.bat port 8080          anderer Port fuer die Live-Ansicht (Standard 8000)
rem   tools\simulation.bat netz               Live-Ansicht auch von anderen Rechnern im Netz
rem   Beispiel: tools\simulation.bat bedienen anlage BASF_Verladearm port 8080
rem
rem Voraussetzung: Python ab 3.10 von python.org (beim Installieren "Add python.exe to PATH").
rem Beim ersten Start wird .venv angelegt und alles installiert (Internet noetig, ca. 2 min).
rem Beenden: die drei Fenster schliessen.
setlocal
cd /d "%~dp0\.."
set CONFIG=vision\config\anlagen\simulation.yaml
set PORT=8000
set HOST=127.0.0.1
set BEDIENEN=
set ECHTZEIT=
set ANLAGE=
set KAMMERN=

:args
if "%~1"=="" goto args_ende
set OPT=%~1
if "%OPT:~0,2%"=="--" set OPT=%OPT:~2%
if /i "%OPT%"=="bedienen" (set BEDIENEN=1& shift & goto args)
if /i "%OPT%"=="echtzeit" (set ECHTZEIT=1& shift & goto args)
if /i "%OPT%"=="netz" (set HOST=0.0.0.0& shift & goto args)
if /i "%OPT%"=="anlage" (set ANLAGE=%~2& shift & shift & goto args)
if /i "%OPT%"=="kammern" (set KAMMERN=%~2& shift & shift & goto args)
if /i "%OPT%"=="port" (set PORT=%~2& shift & shift & goto args)
echo Unbekannte Option: %~1
echo Moeglich: bedienen, echtzeit, netz, anlage NAME, kammern 1-3, port NUMMER
pause
exit /b 1
:args_ende

if not exist data\logs mkdir data\logs
if defined ANLAGE (
  if not exist "vision\config\anlagen\%ANLAGE%.yaml" (
    echo Nicht gefunden: vision\config\anlagen\%ANLAGE%.yaml
    pause
    exit /b 1
  )
  set CONFIG=data\simulation_%ANLAGE%.yaml
  > "data\simulation_%ANLAGE%.yaml" (
    echo # erzeugt von tools\simulation.bat - Simulation der Anlage %ANLAGE%
    echo extends: ../vision/config/anlagen/%ANLAGE%.yaml
    echo source:
    echo   type: sim
    echo   joint_error_deg: [0.3, -0.25, 0.2]
    echo   vehicles: [lkw]
    echo   domes: [offen]
    echo   openings: [1, 2, 3]
    echo   dome_pitch: 2.5
    echo detection:
    echo   roi_min: [-2.0, -3.3, 0.5]
    echo   roi_max: [2.0, 3.3, 8.0]
    echo plc:
    echo   url: opc.tcp://127.0.0.1:4840/
  )
)
if defined KAMMERN (
  if not "%KAMMERN%"=="1" if not "%KAMMERN%"=="2" if not "%KAMMERN%"=="3" (
    echo kammern: 1, 2 oder 3
    pause
    exit /b 1
  )
  > data\simulation_kammern.yaml (
    echo # erzeugt von tools\simulation.bat - jedes Fahrzeug mit %KAMMERN% Kammer^(n^)
    if defined ANLAGE (echo extends: simulation_%ANLAGE%.yaml) else (echo extends: ../vision/config/anlagen/simulation.yaml)
    echo source:
    echo   openings: [%KAMMERN%]
  )
  set CONFIG=data\simulation_kammern.yaml
)

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

set SPS_ARGS=tools\plc_simulator.py --config %CONFIG% --zeitraffer 0.25
if defined BEDIENEN set SPS_ARGS=%SPS_ARGS% --bedienen
if defined ECHTZEIT set SPS_ARGS=%SPS_ARGS% --echtzeit

start "SPS-Simulator" cmd /k ""%PY%" -u %SPS_ARGS%"
timeout /t 3 /nobreak >nul
start "Vision-Dienst" cmd /k ""%PY%" -m verladearm_vision.service.main --config %CONFIG%"
start "Live-Ansicht" cmd /k ""%PY%" -m verladearm_vision.viewer --opcua --config %CONFIG% --host %HOST% --port %PORT%"
timeout /t 6 /nobreak >nul
start "" http://127.0.0.1:%PORT%

echo.
echo Simulation laeuft in drei Fenstern: SPS-Simulator, Vision-Dienst, Live-Ansicht.
echo Anlagendatei: %CONFIG%
echo Live-Ansicht: http://127.0.0.1:%PORT%  (oeffnet sich im Browser)
if "%HOST%"=="0.0.0.0" echo Von anderen Rechnern: http://^<IP dieses Laptops^>:%PORT%  (ipconfig zeigt die IP; Windows-Firewall zulassen)
if defined BEDIENEN echo Bedienung: Befehle im Fenster "SPS-Simulator" eingeben (? = Hilfe).
echo Beenden: die drei Fenster schliessen.
