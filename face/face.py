"""
Face minimalista da CLARA

- Fundo azul.
- Olhos e boca brancos estilizados.
- Animações: olhar para os lados, piscar, boca abrir/fechar ao falar.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    import pygame
except Exception as e:  # pragma: no cover - sem pygame em headless
    raise SystemExit(f"pygame necessario: {e}")


class EyeState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    BLINK = "blink"


class MouthState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    TALK = "talk"


@dataclass(frozen=True)
class FaceConfig:
    width: int = 640
    height: int = 480
    bg: tuple[int, int, int] = (10, 40, 120)
    fg: tuple[int, int, int] = (235, 235, 235)
    eye_color: tuple[int, int, int] = (235, 235, 235)
    mouth_color: tuple[int, int, int] = (235, 235, 235)

    @property
    def center_x(self) -> int:
        return self.width // 2

    @property
    def center_y(self) -> int:
        return self.height // 2


class Face:
    def __init__(self, cfg: Optional[FaceConfig] = None) -> None:
        self.cfg = cfg or FaceConfig()
        self._lock = threading.RLock()
        self._running = False
        self._blink_timer = 0.0
        self._eye_state: EyeState = EyeState.OPEN
        self._mouth_state: MouthState = MouthState.CLOSED
        self._mouth_openness = 0.0  # 0..1
        self._gaze = 0.0  # -1..1
        self._target_gaze = 0.0
        self._talk_speed = 12.0

        pygame.init()
        pygame.display.set_caption("CLARA")
        self.screen = pygame.display.set_mode(
            (self.cfg.width, self.cfg.height), pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def start(self) -> Face:
        self._running = True
        self._loop()
        return self

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def set_gaze(self, target: float) -> None:
        self._target_gaze = max(-1.0, min(1.0, float(target)))

    def blink(self) -> None:
        with self._lock:
            self._eye_state = EyeState.BLINK
            self._blink_timer = 0.14

    def set_talking(self, speaking: bool) -> None:
        with self._lock:
            self._mouth_state = MouthState.OPEN if speaking else MouthState.CLOSED

    def set_mouth_open(self, openness: float) -> None:
        with self._lock:
            self._mouth_openness = max(0.0, min(1.0, float(openness)))

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------
    def _loop(self) -> None:
        last = pygame.time.get_ticks() / 1000.0
        while self._running:
            now = pygame.time.get_ticks() / 1000.0
            dt = max(0.0001, now - last)
            last = now

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self._running = False
                    break
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self._running = False

            self._update(dt)
            self._draw()
            pygame.display.flip()
            self.clock.tick(int(self.cfg.width and 30 or 30))

        pygame.quit()

    def _update(self, dt: float) -> None:
        with self._lock:
            # Olhos
            if self._eye_state == EyeState.BLINK:
                self._blink_timer -= dt
                if self._blink_timer <= 0:
                    self._eye_state = EyeState.OPEN

            # Olhar (suavizado)
            blend = 1.0 - math.exp(-6.0 * dt)
            self._gaze += (self._target_gaze - self._gaze) * blend

            # Boca
            target = (
                1.0 if self._mouth_state == MouthState.TALK
                else (
                    0.5 if self._mouth_state == MouthState.OPEN
                    else 0.0
                )
            )
            self._mouth_openness += (target - self._mouth_openness) * blend

    def _draw(self) -> None:
        w, h = self.screen.get_size()
        self.screen.fill(self.cfg.bg)

        cx = w // 2
        cy = h // 2

        eye_radius = int(min(w, h) * 0.13)
        eye_gap = int(min(w, h) * 0.32)
        eye_y = int(h * 0.42)

        # Base dos olhos
        max_eye_h = int(eye_radius * 2)
        eye_h = max_eye_h if self._eye_state != EyeState.CLOSED else int(max_eye_h * 0.15)

        offset = int(self._gaze * eye_radius * 0.4)

        for ex in (-1, 1):
            ex_pos = cx + ex * eye_gap + offset
            rect = pygame.Rect(0, 0, int(eye_radius * 2), max(eye_h, int(eye_radius * 0.15)))
            rect.center = (ex_pos, eye_y)
            pygame.draw.ellipse(self.screen, self.cfg.eye_color, rect)

        # Boca
        mouth_w = int(min(w, h) * 0.45)
        mouth_y = int(h * 0.72)
        mouth_h = int(min(w, h) * 0.18)
        mouth_open = int(mouth_h * self._mouth_openness)

        rect = pygame.Rect(0, 0, mouth_w, mouth_h)
        rect.center = (cx, mouth_y)
        pygame.draw.ellipse(self.screen, self.cfg.mouth_color, rect)

        if mouth_open > 0:
            aabb = rect.inflate(-int(mouth_w * 0.35), 0)
            aabb.height = max(mouth_open, 2)
            aabb.centery = rect.centery
            aabb.width = max(aabb.width - int(mouth_open * 0.3), 6)
            pygame.draw.ellipse(self.screen, self.cfg.bg, aabb)
