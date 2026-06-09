"""
TTS da CLARA usando edge-tts (vozes da Microsoft, gratuitas).
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

import edge_tts


class TTS:
    def __init__(self, voice: Optional[str] = None) -> None:
        self.voice = voice or os.getenv("TTS_VOICE", "pt-BR-FranciscaNeural")

    async def synthesize(self, text: str, out_path: str) -> str:
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(out_path)
        return out_path

    def speak(self, text: str, out_path: str = "/tmp/clara_tts.mp3") -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.synthesize(text, out_path))
        else:
            fut = asyncio.run_coroutine_threadsafe(
                self.synthesize(text, out_path), loop
            )
            return fut.result()
