#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "[CLARA-Echo] Otimizando sistema..."
sudo systemctl disable --now bluetooth.service hciuart.service 2>/dev/null || true

echo "[CLARA-Echo] Configurando video..."
sed -i '/^#\?hdmi_force_hotplug/d' /boot/config.txt 2>/dev/null || true
grep -q '^hdmi_force_hotplug=1' /boot/config.txt || echo 'hdmi_force_hotplug=1' | sudo tee -a /boot/config.txt >/dev/null

echo "[CLARA-Echo] Instalando dependencias..."
sudo apt update
sudo apt install -y xserver-xorg x11-xserver-utils openbox \
  alsa-utils python3 python3-venv python3-pip git unzip

echo "[CLARA-Echo] Configurando audio ALSA..."
sudo install -D -m 644 /dev/null /etc/asound.conf 2>/dev/null || true | cat
cat <<'EOF' | sudo tee /etc/asound.conf >/dev/null
pcm.!default { type asym; playback.pcm "plughw:0,0"; capture.pcm "plughw:1,0"; }
ctl.!default { type hw; card 0; }
EOF

echo "[CLARA-Echo] Clonando projeto (se necessario)..."
if [ ! -d "/home/pi/projetos/assistente-clara" ]; then
  sudo -u pi mkdir -p /home/pi/projetos
  sudo -u pi git clone https://github.com/pesouza/assistente-clara.git /home/pi/projetos/assistente-clara
fi

echo "[CLARA-Echo] Instalando venv..."
sudo -u pi bash -lc "cd /home/pi/projetos/assistente-clara && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt"

echo "[CLARA-Echo] Baixando modelo VOSK pequeno..."
sudo -u pi python3 -c "
import urllib.request, zipfile, io
url='https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip'
open('/tmp/vosk.zip','wb').write(urllib.request.urlopen(url, timeout=60).read())
zipfile.ZipFile('/tmp/vosk.zip').extractall('/home/pi/projetos/assistente-clara/clara/stt/model')
"
rm -f /tmp/vosk.zip

echo "[CLARA-Echo] Criando estrutura de diretorios..."
sudo -u pi mkdir -p /home/pi/projetos/assistente-clara/clara/home /home/pi/projetos/assistente-clara/logs

echo "[CLARA-Echo] Finalizado."
