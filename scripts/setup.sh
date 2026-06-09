#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "[CLARA] Criando venv..."
python3 -m venv .venv

echo "[CLARA] Ativando venv..."
source .venv/bin/activate

echo "[CLARA] Instalando dependências..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[CLARA] Garantindo symlink do modelo VOSK..."
mkdir -p "$REPO_DIR/clara/stt/model"
if [ ! -d "$REPO_DIR/clara/stt/model" ] || [ "$(ls -A "$REPO_DIR/clara/stt/model" 2>/dev/null)" = "" ]; then
  echo "[CLARA] Modelo VOSK não encontrado. Baixe manualmente um modelo pequeno em:"
  echo "https://alphacephei.com/vosk/models"
  echo "Ex.: vosk-model-small-pt-0.3"
  echo "Depois descompacte em: $REPO_DIR/clara/stt/model/"
else
  echo "[CLARA] Modelo já presente."
fi

echo "[CLARA] Criando diretórios necessários..."
mkdir -p "$REPO_DIR/logs"
mkdir -p "$REPO_DIR/clara/home"
mkdir -p "$REPO_DIR/clara/sessions"

echo "[CLARA] Finalizado."