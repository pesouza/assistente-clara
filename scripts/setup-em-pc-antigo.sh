#!/usr/bin/env bash
# setup-em-pc-antigo.sh
# Usar este script num PC com Ubuntu Server já instalado.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "[CLARA] Primeiro acesso detectado."
read -p "Usuario para instalar (ex: paulo): " USER
if [ -z "${USER}" ]; then
  echo "Informe um usuario valido."
  exit 1
fi

USER_HOME="/home/${USER}"
if [ ! -d "${USER_HOME}" ]; then
  echo "Pasta home ${USER_HOME} nao encontrada."
  exit 1
fi

CLARA_DIR="${USER_HOME}/assistente-clara"
if [ ! -d "${CLARA_DIR}" ]; then
  echo "Repo assistente-clara nao encontrado em ${CLARA_DIR}."
  exit 1
fi

echo "[CLARA] Aplicando permissoes..."
sudo chown -R "${USER}:${USER}" "${CLARA_DIR}"

echo "[CLARA] Criando venv e instalando dependencias..."
sudo -u "${USER}" bash -lc "cd '${CLARA_DIR}' && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt"

echo "[CLARA] Preparando diretorios auxiliares..."
sudo -u "${USER}" mkdir -p "${CLARA_DIR}/clara/home" "${CLARA_DIR}/clara/sessions" "${CLARA_DIR}/logs"

echo "[CLARA] Linkando profile companheiro para o Hermes..."
sudo -u "${USER}" mkdir -p "${USER_HOME}/.hermes/profiles/companheiro"

sudo -u "${USER}" ln -sfn "${CLARA_DIR}/clara/home" "${USER_HOME}/.hermes/profiles/companheiro/home"
sudo -u "${USER}" ln -sfn "${CLARA_DIR}/hermes-profile/hooks" "${USER_HOME}/.hermes/profiles/companheiro/hooks" 2>/dev/null || true
sudo -u "${USER}" ln -sfn "${CLARA_DIR}/hermes-profile/scripts" "${USER_HOME}/.hermes/profiles/companheiro/scripts" 2>/dev/null || true
sudo -u "${USER}" ln -sfn "${CLARA_DIR}/hermes-profile/skills" "${USER_HOME}/.hermes/profiles/companheiro/skills" 2>/dev/null || true

if [ -f "${CLARA_DIR}/hermes-profile/.env.example" ] && [ ! -f "${USER_HOME}/.hermes/profiles/companheiro/.env" ]; then
  echo "[CLARA] Criando .env inicial a partir do template..."
  sudo -u "${USER}" cp "${CLARA_DIR}/hermes-profile/.env.example" "${USER_HOME}/.hermes/profiles/companheiro/.env"
fi

echo "[CLARA] Finalizado."
echo "Proximo passo: editar ${USER_HOME}/.hermes/profiles/companheiro/.env"
echo "Depois rodar o Hermes com o profile: hermes --profile companheiro"
