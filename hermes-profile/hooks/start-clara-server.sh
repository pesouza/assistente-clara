#!/usr/bin/env bash
set -euo pipefail

CLARA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "${CLARA_DIR}" ]; then
  echo "clara: diretorio do projeto nao encontrado: ${CLARA_DIR}" >&2
  exit 1
fi

python3 -m uvicorn clara.server:app --host 127.0.0.1 --port 8010
