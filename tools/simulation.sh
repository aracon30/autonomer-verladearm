#!/usr/bin/env bash
# Komplette Simulation auf einem Linux-Rechner ohne Hardware:
#   SPS-Simulator (OPC UA) + Vision-Dienst (simulierter Sensor) + Live-Ansicht (Browser)
#
#   tools/simulation.sh                 Live-Ansicht nur lokal (Zugriff per SSH-Tunnel)
#   tools/simulation.sh --netz          Live-Ansicht im Netzwerk erreichbar (0.0.0.0)
#   tools/simulation.sh --anlage NAME   Anlagendatei vision/config/anlagen/NAME.yaml simulieren
#                                       (z. B. im Konfigurator angelegt; Standard: heta_prototyp)
#   PORT=8080 tools/simulation.sh       anderer Port für die Live-Ansicht
#   ZEITRAFFER=1 tools/simulation.sh    Achsen in Echtzeit (Standard 0.25 = vierfach schneller)
#
# Der HETA-Prototyp fährt mit den Geschwindigkeiten und Rampen seiner Antriebe
# (vision/config/anlagen/heta_prototyp.yaml, Abschnitt drives).
#
# Vom eigenen PC per SSH-Tunnel:  ssh -L 8000:127.0.0.1:8000 <benutzer>@<server>
# dann im Browser http://127.0.0.1:8000 öffnen. Beenden mit Strg+C (stoppt alle drei).
set -euo pipefail
cd "$(dirname "$0")/.."
ARGS=("$@")

CONFIG=vision/config/anlagen/simulation.yaml
PORT="${PORT:-8000}"
ZEITRAFFER="${ZEITRAFFER:-0.25}"
HOST=127.0.0.1
ANLAGE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --netz) HOST=0.0.0.0 ;;
    --anlage) ANLAGE="${2:?Name der Anlagendatei fehlt}"; shift ;;
    *) echo "Unbekannte Option: $1"; exit 1 ;;
  esac
  shift
done
if [[ -n "$ANLAGE" ]]; then
  [[ -f "vision/config/anlagen/$ANLAGE.yaml" ]] || { echo "Nicht gefunden: vision/config/anlagen/$ANLAGE.yaml"; exit 1; }
  mkdir -p data
  CONFIG="data/simulation_$ANLAGE.yaml"  # Anlage + simulierter Sensor + SPS-Simulator
  cat > "$CONFIG" <<YAML
# erzeugt von tools/simulation.sh – Simulation der Anlage $ANLAGE
extends: ../vision/config/anlagen/$ANLAGE.yaml
source:
  type: sim
  joint_error_deg: [0.3, -0.25, 0.2]
plc:
  url: opc.tcp://127.0.0.1:4840/
YAML
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Erstinstallation: virtuelle Umgebung .venv anlegen ..."
  python3 -m venv .venv
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -e ".[dev]"
fi
PY=.venv/bin/python
mkdir -p data/logs

port_busy() { $PY -c "import socket,sys; s=socket.socket(); sys.exit(s.connect_ex(('127.0.0.1', $1)) != 0)"; }
if port_busy "$PORT"; then
  echo "Port $PORT ist schon belegt (anderes Programm). Anderen Port wählen, z. B.:"
  echo "  PORT=8080 $0 ${ARGS[*]:-}"
  exit 1
fi
if port_busy 4840; then
  echo "Port 4840 (OPC UA) ist belegt – läuft schon eine Simulation oder ein OPC-UA-Server?"
  exit 1
fi

pids=()
cleanup() { echo; echo "Stoppe Simulation ..."; kill "${pids[@]}" 2>/dev/null || true; wait; }
trap cleanup EXIT INT TERM

$PY tools/plc_simulator.py --config "$CONFIG" --zeitraffer "$ZEITRAFFER" \
  > data/logs/sps.log 2>&1 & pids+=($!)
sleep 2
$PY -m verladearm_vision.service.main --config "$CONFIG" > data/logs/vision.log 2>&1 & pids+=($!)
$PY -m verladearm_vision.viewer --opcua --config "$CONFIG" --host "$HOST" --port "$PORT" \
  > data/logs/viewer.log 2>&1 & pids+=($!)

sleep 3
for i in 0 1 2; do
  if ! kill -0 "${pids[$i]}" 2>/dev/null; then
    log=(sps vision viewer); echo "Start fehlgeschlagen, siehe data/logs/${log[$i]}.log:"
    tail -n 5 "data/logs/${log[$i]}.log"; exit 1
  fi
done
echo "Simulation läuft: SPS-Simulator, Vision-Dienst, Live-Ansicht  (Anlage: ${ANLAGE:-heta_prototyp})"
if [[ "$HOST" == 0.0.0.0 ]]; then
  for ip in $(hostname -I 2>/dev/null); do
    [[ "$ip" == 172.1[78].* || "$ip" == *:* ]] && continue   # Docker-Netze, IPv6
    echo "  Live-Ansicht: http://${ip}:${PORT}  (im Browser eines PCs im selben Netz)"
  done
else
  echo "  Live-Ansicht: http://127.0.0.1:${PORT}  (vom eigenen PC: ssh -L ${PORT}:127.0.0.1:${PORT} <benutzer>@<server>)"
fi
echo "  Logs:         data/logs/{sps,vision,viewer}.log"
echo "  Beenden:      Strg+C"
tail -n +1 -F data/logs/vision.log
