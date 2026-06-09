# CLARA — Companheira de Lazer, Apoio, Recordações e Atenção

Projeto para transformar um PC antigo em um acompanhante digital: rosto simples
(olhos e boca estilizados em fundo azul) com voz, personalidade calma e
capacidade de pesquisar a internet, trazer clima, notícias, lembrar compromissos
e manter conversas em português.

## Stack

- Ubuntu minimal
- Hermes Agent (profile `companheiro`)
- Python 3.12 + venv
- Pygame (face)
- VOSK (stt offline)
- edge-tts ou TTS do sistema
- FastAPI + uvicorn (interface HTTP/WS)
- SQLite (memória curta)

## Estrutura

```text
clara/
  face/             # pygame: rosto + animações
  stt/              # engine de voz
  tts/              # síntese de voz
  memory/           # SQLite com memória
  main.py           # entrypoint
scripts/
  setup.sh
docker/
  Dockerfile
```

## Setup rápido

```bash
git clone https://github.com/<user>/companheiro-clara.git
cd companheiro-clara
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite .env com suas chaves
python clara/main.py
```

## Contato / contexto

Inspirado na persona do projeto C.L.A.R.A. (para idosos, com tom calmo,
empático e paciente).