#!/usr/bin/env bash
# Installation auf dem Edge-PC (Ubuntu 22.04/24.04), als root ausführen:
#   sudo deploy/install.sh vision/config/anlagen/<anlage>.yaml
# Legt Benutzer, virtuelle Umgebung, Konfiguration und Systemdienste an. Mehrfach ausführbar
# (Update: Repo aktualisieren und erneut ausführen).
set -euo pipefail

ANLAGE="${1:?Anlagendatei angeben, z. B. vision/config/anlagen/beispiel.yaml}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX=/opt/verladearm
DATA=/var/lib/verladearm
CONF=/etc/verladearm

id verladearm >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin verladearm
mkdir -p "$PREFIX" "$DATA/data" "$CONF"

# Programm in eigene virtuelle Umgebung (SICK-Bibliothek inklusive)
python3 -m venv "$PREFIX/venv"
"$PREFIX/venv/bin/pip" install --upgrade pip >/dev/null
"$PREFIX/venv/bin/pip" install "$REPO[sick]"

# Konfiguration: default.yaml + Anlagendatei; extends auf die installierte default.yaml umbiegen
install -m 0644 "$REPO/vision/config/default.yaml" "$CONF/default.yaml"
sed 's#^extends:.*#extends: default.yaml#' "$ANLAGE" > "$CONF/anlage.yaml"
chmod 0640 "$CONF/anlage.yaml"
chown -R verladearm:verladearm "$DATA"
chgrp verladearm "$CONF/anlage.yaml"

install -m 0644 "$REPO/deploy/verladearm-vision.service" /etc/systemd/system/
install -m 0644 "$REPO/deploy/verladearm-viewer.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now verladearm-vision.service verladearm-viewer.service
systemctl --no-pager status verladearm-vision.service | head -5
echo "Fertig. Protokoll: journalctl -u verladearm-vision -f   Ansicht: http://<PC>:8000"
