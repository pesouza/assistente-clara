# CLARA — Companheira Digital para PC Antigo

Transforma um PC antigo em um acompanhante digital com rosto animado, voz
empática e acesso a informações (clima, notícias, web, agenda).

Stack:
- Ubuntu Server 22.04/24.04 minimal
- Hermes Agent (profile `companheiro`)
- Python 3.12 + venv
- Pygame (face)
- VOSK (STT offline)
- edge-tts (TTS em pt-BR)
- SQLite (memória curta)

## Hardware recomendado

| peça       | mínimo                  | ideal           |
|------------|-------------------------|-----------------|
| CPU        | Dual-core 64-bit        | Quad-core       |
| RAM        | 2 GB                    | 4 GB            |
| disco      | 16 GB                   | 32 GB SSD       |
| rede       | Wi-Fi / Ethernet        | Ethernet        |
| entrada    | microfone USB/3.5mm     | microfone USB   |
| saída      | caixas / fone           | caixas ativas   |

PCs como Raspberry Pi 3/4, NUCs antigos, notebooks aposentados ou desktops
Core 2 Duo com 2 GB+ funcionam.

---

## Passo 1 — Instalar o Ubuntu Server

1. Baixar imagem:
   - Ubuntu 22.04 LTS ou 24.04 LTS:
     https://ubuntu.com/download/server

2. Gravar no pendrive:
   - Linux: `dd bs=4M if=ubuntu-xx.xx-live-server-amd64.iso of=/dev/sdX status=progress && sync`
   - Windows/macOS: Rufus / BalenaEtcher

3. Instalar no PC antigo:
   - Iniciar pelo pendrive.
   - Idioma: English (menos chance de bug com teclado).
   - Keyboard: Portuguese (ABNT2).
   - Rede: configurar Wi-Fi ou Ethernet com DHCP.
   - Proxy/ mirrors: deixar padrão (ou usar mirror brasileiro).
   - Storage: disco inteiro ( Guided — use entire disk ).
   - Profile:
     - Name: `clara`
     - Hostname: `clara-pc`
     - Username: `paulo` (ou outro)
     - Password: senha forte
   - **NÃO instalar snaps adicionais** (economiza espaço/disco).
   - **NÃO instalar SSH** por enquanto (se quiser acesso remoto depois).
   - Aguardar instalação e reboot.

4. Após reboot:
   ```bash
   ssh paulo@IP_DO_PC  # se instalou SSH
   # ou usar teclado/monitor localmente
   ```

---

## Passo 2 — Primeira configuração do sistema

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Ferramentas básicas
sudo apt install -y git curl build-essential python3 python3-venv python3-pip \
  alsa-utils pulseaudio ffmpeg unzip

# Usuário para o Hermes (opcional, pode usar seu usuário normal)
sudo useradd -m -s /bin/bash hermes || true

# Ajustar horário
sudo timedatectl set-timezone America/Sao_Paulo
```

### Som (ALSA mínimo)

Testar microfone:
```bash
arecord -d 5 /tmp/teste.wav && aplay /tmp/teste.wav
```

Se gravar e reproduzir, som está OK. Se não, verificar `alsamixer`
e garantir que o microfone não está mudo (MM = mudo, `M` para desmutar).

---

## Passo 3 — Clonar o projeto da CLARA

```bash
git clone https://github.com/pesouza/assistente-clara.git
cd assistente-clara
```

---

## Passo 4 — Subir o Hermes com profile `companheiro`

Essa etapa faz a CLARA funcionar como um agente Hermes separado.

### 4.1 Instalar Hermes (no próprio PC antigo)

Siga o guia oficial:
- Repositório e instalação: https://github.com/NousResearch/hermes-agent

Resumo rápido (pode mudar dependendo do release):
```bash
# exemplo genérico; use o método oficial do repo
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### 4.2 Criar profile `companheiro`

```bash
hermes profiles create companheiro
```

Edite `~/.hermes/profiles/companheiro/.env`:
```bash
HERMES_HOME=/home/paulo/.hermes/profiles/companheiro
OPENAI_BASE_URL=http://127.0.0.1:8000
OPENAI_API_KEY=local-clara
LANG=pt-BR
```

Edite `~/.hermes/profiles/companheiro/config.yaml` para usar:
- Modelo: o mesmo que você já usa no Hermes principal
- Prompt base: carregue `clara/SOUL.md` como system prompt
- Skills: habilite busca web, clima, notícias, agenda

### 4.3 Rodar o Hermes nesse profile

```bash
hermes --profile companheiro
```

---

## Passo 5 — Preparar o projeto CLARA

```bash
cd assistente-clara
./scripts/setup.sh
```

Isso:
- Cria venv em `.venv`
- Instala dependências
- Cria pastas `logs/`, `clara/home/`, `clara/sessions/`

### Baixar modelo VOSK (STT)

```bash
python3 -c "
import urllib.request, pathlib, zipfile, io
url='https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip'
print('Baixando modelo VOSK pequeno em pt-BR...')
data=urllib.request.urlopen(url, timeout=60).read()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    z.extractall('clara/stt/model')
print('Pronto.')
"
```

### Configurar `.env`

```bash
cp .env.example .env
nano .env
```

Ajuste pelo menos:
- `OPENAI_BASE_URL` e `OPENAI_API_KEY`
- `TTS_VOICE=pt-BR-FranciscaNeural` (ou outra voz Edge TTS)
- `FACE_FPS=30`

---

## Passo 6 — Rodar a CLARA

### 6.1 Só a interface (rosto)

```bash
source .venv/bin/activate
python clara/main.py
```

Você verá uma janela com:
- fundo azul
- dois olhos que piscam e olham
- boca que abre/fecha ao falar

Fechar com `ESC` ou fechando a janela.

### 6.2 Com voz (STT + TTS)

A integração completa de voz será feita pelo Hermes como um agente
separado. O fluxo previsto:

```text
[Usuário fala] -> VOSK STT -> Hermes (profile companheiro) -> LLM
    -> resposta -> Edge TTS -> áudio -> face.set_talking(True)
```

Essa parte será encaixada via skill do Hermes, mantendo o rosto
independente para reduzir acoplamento.

---

## Passo 7 — Deixar a CLARA ligada no boot

### Opção A — systemd (recomendado)

Crie `/etc/systemd/system/clara.service`:

```ini
[Unit]
Description=CLARA Companheira
After=network.target sound.target

[Service]
Type=simple
User=paulo
WorkingDir=/home/paulo/assistente-clara
ExecStart=/home/paulo/assistente-clara/.venv/bin/python clara/main.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/paulo/.Xauthority

[Install]
WantedBy=graphical.target
```

Se o PC antigo não tiver interface gráfica ligada ao boot:
- Instalar `lightdm` + `openbox`/`xfce4`
- Ou rodar o face como windowless com `SDL_VIDEODRIVER=fbcon` / framebuffer

### Opção B — iniciar manualmente

No desktop (LXDE/Xfce/MATE), adicionar ao "Autostart":
`/home/paulo/assistente-clara/.venv/bin/python clara/main.py`

---

## Passo 8 — Usar

- **Voz**: fale com a CLARA; ela responde em pt-BR.
- **Teclado/atalho**: futuramente, tecla de atalho para ativar escuta.
- **Comandos úteis**:
  - "Que horas são?"
  - "Como está o clima?"
  - "Me diga uma notícia."
  - "Me lembre de X às Y."
  - "Que dia é hoje?"

---

## Estrutura do repositório

```text
assistente-clara/
├── README.md
├── .env.example
├── requirements.txt
├── scripts/
│   └── setup.sh
├── clara/
│   ├── SOUL.md
│   ├── main.py
│   ├── memory.py
│   └── home/          # SQLite local
├── face/
│   └── face.py        # pygame: olhos + boca
├── stt/
│   └── model/         # modelo VOSK (não versionado, baixar separado)
├── tts/
└── logs/
```

---

## Personalização

- Cores: altere `FaceConfig.bg` e `FaceConfig.fg` em `face/face.py`.
- Personalidade: edite `clara/SOUL.md` — é o "cérebro" da CLARA.
- Voz: troque `TTS_VOICE` no `.env` por outra voz Edge TTS pt-BR.

---

## Troubleshooting rápido

| sintoma                                    | causa provável                          | fix                                  |
|-------------------------------------------|-----------------------------------------|--------------------------------------|
| `pygame` não abre janela                  | falta de display / drivers              | `sudo apt install xserver-xorg-core`  |
| microfone não grava                        | microfone mudo / dispositivo errado     | `alsamixer` e `arecord -l`            |
| VOSK não carrega modelo                   | modelo ausente ou path errado           | verificar `clara/stt/model/`          |
| Hermes não conecta                        | profile não criado / .env errado        | revisar `~/.hermes/profiles/companheiro` |
| face trava no boot                        | service roda antes do X                 | ajustar `After=graphical.target`      |

---

## Próximos passos

- [x] SOUL.md
- [x] Rosto com pygame
- [x] Memória SQLite
- [ ] Skill Hermes para voz (STT + TTS)
- [ ] Integração face ↔ Hermes (boca abre ao falar)
- [ ] Ativação por hotword
- [ ] Habilidades: clima, notícias, agenda, Spotify

---

## Licença

MIT