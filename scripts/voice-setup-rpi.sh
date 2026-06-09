#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "[CLARA-Echo] Baixando modelo VOSK pequeno..."
sudo -u pi python3 -c "
import urllib.request, zipfile, io
url='https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip'
open('/tmp/vosk.zip','wb').write(urllib.request.urlopen(url, timeout=60).read())
zipfile.ZipFile('/tmp/vosk.zip').extractall('${REPO_DIR}/clara/stt/model')
"
rm -f /tmp/vosk.zip

echo "[CLARA-Echo] Instalando venv e dependencias..."
sudo -u pi bash -lc "cd '${REPO_DIR}' && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt"

echo "[CLARA-Echo] Ajustando alsamixer..."
sudo -u pi bash -lc "amixer set Capture 80% 2>/dev/null || true"

echo "[CLARA-Echo] Finalizado."
