"""
Voz da CLARA - STT (VOSK) e TTS (edge-tts).
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import queue
import threading
from pathlib import Path
from typing import Optional

import sounddevice as sd
from vosk import Model, KaldiRecognizer


AUDIO_QUEUE: "queue.Queue[str]" = queue.Queue()


class STT:
    def __init__(self, model_path: Optional[str] = None, samplerate: int = 16000) -> None:
        self.samplerate = samplerate
        model_path = model_path or os.getenv("STT_MODEL", "clara/stt/model")
        self.model = Model(str(model_path))
        self.rec = KaldiRecognizer(self.model, samplerate)
        self._stream: Optional[sd.InputStream] = None

    def start(self) -> None:
        q: queue.Queue[bytes] = queue.Queue()

        def callback(indata, frames, time, status):  # type: ignore[no-untyped-def]
            if status:
                pass
            q.put(bytes(indata))

        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        )
        self._stream.start()

        def worker() -> None:
            while True:
                data = q.get()
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                else:
                    res = json.loads(self.rec.PartialResult())
                text = res.get("text", "") or res.get("partial", "")
                if text:
                    AUDIO_QUEUE.put(text)

        threading.Thread(target=worker, daemon=True).start()

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
