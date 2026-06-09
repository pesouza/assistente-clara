#!/usr/bin/env python3
"""
CLARA - Compaheiro digital

MVP entrypoint. Integra face + TTS opcional e espera eventos.
Versao inicial: interface grafica com animacoes.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="CLARA")
    ap.add_argument("--bg", default="10,40,120", help="Fundo RGB")
    ap.add_argument("--fps", type=int, default=30)
    ns = ap.parse_args()

    try:
        from clara.face.face import Face, FaceConfig
    except Exception as e:
        print(f"Falha ao importar face: {e}", file=sys.stderr)
        return 2

    r, g, b = map(int, ns.bg.split(","))
    cfg = FaceConfig(bg=(r, g, b))
    face = Face(cfg)
    face.start()
    return 0




