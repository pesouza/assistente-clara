# CLARA — Amazon Echo Show 5 (Raspberry Pi 2B)

Variante leve do assistente digital CLARA para rodar no Raspberry Pi 2B
(1 GB RAM, ARMv7) com monitor integrado de 5" ou 7" HDMI/DSI,
imitando o visual do Amazon Echo Show 5.

Destaques:
- Interface kiosk em tela touch/monitor
- Olhos/boca animados em tempo real
- Voz em pt-BR (offline quando possível)
- Integração com Hermes Agent para funcionalidades
- Boot automático
- Baixo consumo de RAM (< 300 MB)

---

## Hardware necessário

| item | especificação |
|------|---------------|
| SBC | Raspberry Pi 2B (v1.2) — 1 GB RAM, ARMv7 |
| Fonte | 5 V / 2 A (micro-USB ou USB-C dependendo da revisão) |
| Cartão | MicroSD 16 GB Classe 10 (A1 melhor) |
| Display | 5" HDMI 800x480 ou 7" oficial Raspberry Pi DSI |
| Áudio | microfone USB (preferencial) ou ICM-20948/INMP441 I2S |
| Caixas | saída HDMI ou microfone + fone de ouvido |
| Alimentação | fonte estabilizada; evite hubs USB fracos |
| Case | impresso 3D estilo Echo Show (opcional) |
| Botão | botão físico GPIO para mudo/liga-desliga (opcional) |

---

## Software base

- Raspberry Pi OS Lite (Bookworm ou Bullseye) — sem desktop
- Xorg mínimo + Openbox (para kiosk)
- Navegador leve: Midori ou Firefox ESR
- ALSA puro (sem PulseAudio, para economizar RAM)
- Python 3.11 + venv
- Hermes Agent (profile `companheiro`)
- VOSK modelo pequeno pt-BR
- edge-tts (ou espeak-ng puro offline)

### Download do sistema

1. Baixar Raspberry Pi Imager: https://www.raspberrypi.com/software/
2. Escolher "Raspberry Pi OS Lite (32-bit) Bookworm"
3. Configurar antes de gravar:
   - Hostname: `clara-echo`
   - Usuário: `pi`
   - Senha: definir
   - SSH: desligado (a menos que use headless)
   - Wi-Fi: configurar SSID/senha
4. Gravar no cartão e bootar.

### Primeiro acesso

Conectar teclado + monitor ou usar `ssh pi@clara-echo.local` com Bonjour.

---

## Setup automático

```bash
# Atualizar sistema
sudo apt update && sudo apt full-upgrade -y
sudo reboot

# Instalar dependências
sudo apt install -y xserver-xorg x11-xserver-utils openbox midori \
  alsa-utils python3 python3-venv python3-pip git unzip \
  chromium-browser fonts-noto-color-emoji

# Desativar PulseAudio (economiza ~20 MB)
sudo systemctl disable --now pipewire wireplumber 2>/dev/null || true

# Clonar projeto
mkdir -p /home/pi/projetos
cd /home/pi/projetos
git clone https://github.com/pesouza/assistente-clara.git
cd assistente-clara

# Rodar bootstrap RPi
chmod +x scripts/setup-rpi.sh
./scripts/setup-rpi.sh
```

### Otimizações pós-setup

```bash
# Desativar serviços desnecessários
sudo systemctl disable --now bluetooth.service 2>/dev/null || true
sudo systemctl disable --now hciuart.service 2>/dev/null || true
sudo systemmask apt-daily-upgrade.timer 2>/dev/null || true

# Ajustar memória de vídeo (GPU) para 16 MB
sudo raspi-config nonint do_memory_split 16

# Swap moderado (200 MB evita OOM sem gastar SD)
sudo dphys-swapfile swapoff 2>/dev/null || true
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=200/' /etc/dphys-swapfile.conf 2>/dev/null || true
sudo dphys-swapfile setup 2>/dev/null || true
sudo dphys-swapfile swapon 2>/dev/null || true
```

---

## Configuração do display

### Display HDMI 5" 800x480

Criar `/etc/x11/rogue.conf` ou usar `/boot/config.txt`:

```ini
# /boot/config.txt
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
hdmi_pixel_encoding=RGB
```

Reiniciar: `sudo reboot`

### Monitor DSI oficial 7"

```bash
sudo raspi-config nonint do_display_override 1
```

---

## Interface estilo Echo Show 5

Duas opções:

### Opção A — Navegador kiosk (recomendado)

Vantagens:
- animações suaves com CSS/SVG
- fácil ajuste de layout
- reativo a toque se o display for touch

Configurar `~/.config/openbox/autostart`:

```bash
xset s off
xset -dpms
xset s noblank
unclutter -idle 0.1 -root &
midori -e Fullscreen -a http://127.0.0.1:8010/kiosk
# ou Chromium:
# chromium-browser --noerrdialogs --disable-infobars --kiosk http://127.0.0.1:8010/kiosk
```

### Opção B — Framebuffer puro (sem Xorg)

Mais leve, mas animações limitadas. Para projetos avançados,
use a Opção A.

---

## CLARA Face Web (kiosk)

Arquivo em `clara/server.py` incluirá rota `/kiosk` servindo HTML/CSS/JS
com:
- relógio grande centralizado (estilo Echo Show)
- olhos/boca da CLARA quando ociosa
- indicador de escuta (ondas sonoras)
- animação de "pensando"

Para o RPi 2B:
- usar SVG inline (GPU acelera SVG melhor que Canvas)
- evitar fontes customizadas
- limitar partículas/efeitos

---

## Serviço systemd

`/etc/systemd/system/clara-echo.service`:

```ini
[Unit]
Description=CLARA Echo Show (RPi 2B)
After=network.target sound.target graphical.target

[Service]
Type=simple
User=pi
WorkingDir=/home/pi/projetos/assistente-clara
ExecStart=/home/pi/projetos/assistente-clara/.venv/bin/python -m uvicorn clara.server:app --host 127.0.0.1 --port 8010
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

[Install]
WantedBy=graphical.target
```

Habilitar auto-start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now clara-echo.service
```

Verificar:

```bash
journalctl -u clara-echo -f
```

---

## Áudio

### Microfone USB

```bash
# Listar dispositivos
arecord -l
# Gravar teste
arecord -d 3 /tmp/teste.wav && aplay /tmp/teste.wav
```

Configuração ALSA em `/etc/asound.conf`:

```text
pcm.!default {
  type asym
  playback.pcm "plughw:0,0"
  capture.pcm "plughw:1,0"
}
ctl.!default {
  type hw
  card 0
}
```

Ajustar `plughw:0,0` e `plughw:1,0` conforme saída do `arecord -l`.

### Hotword local (opcional)

Para ativar a CLARA só quando chamada, use:

- `porcupine` (exige licença) — excelente no RPi 2B
- `snowboy` (descontinuado mas roda) — modelo pt-BR custom
- VOSK com gramática curta ("oi clara", "clara") detectado no stream

Minimalista: gramática VOSK fixa com palavras-chave.

---

## Integração com Hermes

No RPi 2B, rode o Hermes como serviço separado consumindo a internet:

```bash
# Perfil companheiro já vem no repo
hermes --profile companheiro
```

A CLARA usa o Hermes para:
- processar linguagem natural
- buscar clima, notícias, Wikipedia
- lembrar compromissos
- contar piadas e histórias

Respostas do Hermes são enviadas ao TTS e ao face server.

---

## Economia de energia / desligar tela

Se quiser desligar a tela por inatividade:

```bash
# Desligar após 5 min (DPMS)
xset +dpms && xset dpms 0 0 300
```

Botão físico (GPIO) para despertar:
- ligar botão entre GPIO17 e GND
- script Python escuta falling edge e envia comando para o X server acordar

---

## Próximos ajustes específicos do RPi

- [ ] Calibrar brilho e contraste via `vcgencmd`
- [ ] Medir temperatura (`/sys/class/thermal/thermal_zone*/temp`) e reduzir FPS se > 80°C
- [ ] Low-power mode: desativar HDMI após X minutos (`tvservice -o`)
- [ ] Criar imagem pronta (img) para gravação direta no cartão
- [ ] Testar RAM utilizada em idle: meta < 200 MB

---

## Troubleshooting RPi

| sintoma | causa provável | fix |
|---------|----------------|-----|
| Tela preta / sem X | HDMI não detectado | `hdmi_force_hotplug=1`, checar `tvservice -s` |
| Áudio chiando | ALSA incorreto | checar `aplay -l` e `/etc/asound.conf` |
| Travando no boot | SWAP alto / SD ruim | reduzir SWAP para 100 MB, usar cartão A1 |
| Hermes lento | modelo LLM muito grande | usar versão quantizada ou remota via API |
| Face lenta | framebuffer sem aceleração | habilitar `dtoverlay=vc4-fkms-v3d` no `config.txt` |
