"""
CLARA face server - rota web + Socket.IO
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from clara.face.face import Face, FaceConfig

app = FastAPI(title="CLARA")
face = Face(FaceConfig())

@app.on_event("startup")
def _startup():
    import threading
    threading.Thread(target=face.start, daemon=True).start()

@app.on_event("shutdown")
def _shutdown():
    face.stop()

@app.get("/kiosk")
def kiosk():
    return HTMLResponse(Path(__file__).with_name("web") / "kiosk.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/face/gaze")
def face_gaze(payload: dict):
    face.set_gaze(float(payload.get("target", 0)))
    return {"ok": True}

@app.post("/face/mouth")
def face_mouth(payload: dict):
    state = payload.get("state", "close")
    if state == "open":
        face.set_talking(False)
        face.set_mouth_open(float(payload.get("openness", 0.5)))
    elif state == "talk":
        face.set_talking(True)
    else:
        face.set_talking(False)
        face.set_mouth_open(0.0)
    return {"ok": True}

@app.post("/face/blink")
def face_blink():
    face.blink()
    return {"ok": True}

@app.websocket("/ws/face")
async def ws_face(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            t = data.get("type")
            if t == "gaze":
                face.set_gaze(float(data.get("target", 0)))
            elif t == "blink":
                face.blink()
            elif t == "mouth_open":
                face.set_mouth_open(float(data.get("openness", 0.5)))
                face.set_talking(False)
            elif t == "mouth_close":
                face.set_talking(False)
                face.set_mouth_open(0.0)
            await ws.send_text(json.dumps({"ok": True}))
    except WebSocketDisconnect:
        pass
