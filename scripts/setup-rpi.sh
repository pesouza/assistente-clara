#!/usr/bin/env bash
set -euo pipefail

LOGFILE="/var/log/clara-setup.log"
REPO_URL="https://github.com/pesouza/assistente-clara.git"
REPO_DEFAULT="/home/pi/projetos/assistente-clara"
VOSK_URL="https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"

run() {
  echo "[CLARA-Echo] $*" | tee -a "$LOGFILE"
}

check_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Execute com sudo." | tee -a "$LOGFILE"
    exit 1
  fi
}

check_disk() {
  local avail
  avail=$(df --output=avail / | tail -1 | tr -d ' ')
  if [ "$avail" -lt 150000 ]; then
    echo "Espaco insuficiente (menos de 150 MB). Libere antes de continuar." | tee -a "$LOGFILE"
    exit 1
  fi
}

ask_params() {
  if [ -z "${TARGET_USER:-}" ]; then
    read -p "Usuario alvo [pi]: " TARGET_USER
    TARGET_USER="${TARGET_USER:-pi}"
  fi

  if [ -z "${REPO_DIR:-}" ]; then
    if [ -d "$REPO_DEFAULT" ]; then
      REPO_DIR="$REPO_DEFAULT"
    else
      read -p "Diretorio do projeto [${REPO_DEFAULT}]: " REPO_DIR
      REPO_DIR="${REPO_DIR:-$REPO_DEFAULT}"
    fi
  fi

  if ! id -u "$TARGET_USER" >/dev/null 2>&1; then
    echo "Usuario $TARGET_USER nao existe. Crie antes." | tee -a "$LOGFILE"
    exit 1
  fi

  TARGET_HOME=$(eval echo "~$TARGET_USER")
}

install_pkgs() {
  run "Atualizando pacotes..."
  apt-get update | tee -a "$LOGFILE"
  run "Instalando dependencias..."
  apt-get install -y --no-install-recommends \
    xserver-xorg x11-xserver-utils openbox \
    alsa-utils python3 python3-venv python3-pip git unzip \
    | tee -a "$LOGFILE"
}

clone_repo() {
  if [ ! -d "$REPO_DIR/.git" ]; then
    run "Clonando projeto..."
    mkdir -p "$(dirname "$REPO_DIR")"
    git clone "$REPO_URL" "$REPO_DIR" | tee -a "$LOGFILE"
  else
    run "Repo ja existe em $REPO_DIR"
  fi
}

setup_venv() {
  run "Criando venv..."
  su - "$TARGET_USER" -c "cd '$REPO_DIR' && python3 -m venv .venv" | tee -a "$LOGFILE"
  run "Instalando dependencias Python..."
  su - "$TARGET_USER" -c "cd '$REPO_DIR' && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt" | tee -a "$LOGFILE"
}

setup_alsa() {
  local alsa_conf="/etc/asound.conf"
  if [ -f "$alsa_conf" ] && grep -q "pcm.!default" "$alsa_conf"; then
    run "ALSA ja configurado."
    return
  fi

  run "Configurando ALSA basico..."
  cat <<EOF > "$alsa_conf"
pcm.!default {
  type asym
  playback.pcm "plughw:0,0"
  capture.pcm "plughw:1,0"
}
ctl.!default {
  type hw
  card 0
}
EOF
}

download_vosk() {
  local model_dir="$REPO_DIR/clara/stt/model"
  run "Verificando modelo VOSK..."
  if [ -d "$model_dir/vosk-model-small-pt-0.3" ] && [ "$(ls -A "$model_dir/vosk-model-small-pt-0.3" 2>/dev/null)" ]; then
    run "Modelo ja presente."
    return
  fi

  run "Baixando modelo..."
  local zip_tmp
  zip_tmp=$(mktemp /tmp/vosk.XXXXXX.zip)
  if ! curl -L --fail --output "$zip_tmp" "$VOSK_URL" --max-time 120; then
    echo "Falha no download do VOSK. Veja $LOGFILE." | tee -a "$LOGFILE"
    rm -f "$zip_tmp"
    exit 1
  fi

  run "Descompactando modelo..."
  mkdir -p "$model_dir"
  unzip -q "$zip_tmp" -d "$model_dir"
  rm -f "$zip_tmp"
  chown -R "$TARGET_USER:$TARGET_USER" "$model_dir"
}

fix_perms() {
  run "Ajustando permissoes..."
  chown -R "$TARGET_USER:$TARGET_USER" "$REPO_DIR"
}

main() {
  check_root
  check_disk
  ask_params
  install_pkgs
  clone_repo
  setup_alsa
  setup_venv
  download_vosk
  fix_perms

  run "Concluido."
  echo "Projeto em: $REPO_DIR"
  echo "Usuario: $TARGET_USER"
  echo "Log: $LOGFILE"
}

main "$@"
