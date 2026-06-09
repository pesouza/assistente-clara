"""
CLARA face server - HTTP + WebSocket para controlar o rosto.

Endpoints:
- POST /face/gaze {"target": -1..1}
- POST /face/mouth {"state": "open"|"close"|"talk", "openness": 0..1}
- POST /face/blink
- WebSocket /ws/face recebe {type, payload}
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except Exception as e:
    raise SystemExit(f"fastapi/pydantic required: {e}")

from clara.face.face import Face, FaceConfig, EyeState, MouthState

app = FastAPI(title="CLARA Face")

face: Optional[Face] = None


class GazeModel(BaseModel):
    target: float


class MouthModel(BaseModel):
    state: str = "close"
    openness: float = 0.5


@app.on_event("startup")
def startup() -> None:
    global face
    cfg = FaceConfig(
        bg=tuple(map(int, os.getenv("FACE_BG", "10,40,120").split(","))),
    )
    face = Face(cfg)
    # Roda o loop do pygame em thread separada para não bloquear FastAPI
    import threading
    threading.Thread(target=face.start, daemon=True).start()


@app.on_event("shutdown")
def shutdown() -> None:
    if face:
        face.stop()


@app.post("/face/gaze")
def set_gaze(m: GazeModel) -> JSONResponse:
    if not face:
        return JSONResponse({"error": "face not initialized"}, status_code=503)
    face.set_gaze(m.target)
    return JSONResponse({"ok": True})


@app.post("/face/mouth")
def set_mouth(m: MouthModel) -> JSONResponse:
    if not face:
        return JSONResponse({"error": "face not initialized"}, status_code=503)
    if m.state == "open":
        face.set_mouth_open(float(m.openness))
        face.set_talking(False)
    elif m.state == "talk":
        face.set_talking(True)
    else:
        face.set_talking(False)
        face.set_mouth_open(0.0)
    return JSONResponse({"ok": True})


@app.post("/face/blink")
def blink() -> JSONResponse:
    if not face:
        return JSONResponse({"error": "face not initialized"}, status_code=503)
    face.blink()
    return JSONResponse({"ok": True})


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "face": face is not None})


@app.websocket("/ws/face")
async def ws_face(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "invalid json"}))
                continue

            if not face:
                await ws.send_text(json.dumps({"error": "face not initialized"}))
                continue

            t = data.get("type")
            if t == "gaze":
                face.set_gaze(float(data.get("target", 0)))
            elif t == "mouth":
                face.set_talking(bool(data.get("talk", False)))
                if "openness" in data:
                    face.set_mouth_open(float(data["openness"]))
            elif t == "blink":
                face.blink()
            else:
                await ws.send_text(json.dumps({"error": "unknown type"}))
                continue

            await ws.send_text(json.dumps({"ok": True}))
    except WebSocketDisconnect:
        pass
