"""FastAPI application — HTTP routes and WebSocket endpoint."""

import json

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse

from app.ws_manager import manager

app = FastAPI(title="QR Image Relay")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


# --------------------------------------------------------------------------
# HTML page routes (served directly to avoid StaticFiles intercepting /ws)
# --------------------------------------------------------------------------

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return RedirectResponse(url="/viewer.html")


@app.api_route("/sender.html", methods=["GET", "HEAD"])
async def sender_page():
    return FileResponse(STATIC_DIR / "sender.html", media_type="text/html")


@app.api_route("/viewer.html", methods=["GET", "HEAD"])
async def viewer_page():
    return FileResponse(STATIC_DIR / "viewer.html", media_type="text/html")


# --------------------------------------------------------------------------
# Status API (used for healthchecks and monitor)
# --------------------------------------------------------------------------

@app.api_route("/status", methods=["GET", "HEAD"])
async def status():
    return await manager.get_stats()


# --------------------------------------------------------------------------
# WebSocket endpoint — handles text (role JSON) and binary (images)
# --------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    accepted = await manager.connect(websocket)
    if not accepted:
        return  # connection was rejected (at capacity)

    try:
        while True:
            message = await websocket.receive()

            # --- Text messages: JSON role announcements ---
            if "text" in message:
                text = message["text"]
                if not text:
                    continue
                try:
                    data = json.loads(text)
                    if isinstance(data, dict) and data.get("type") == "role":
                        role = data.get("role")
                        if role in ("sender", "viewer"):
                            await manager.set_role(websocket, role)
                except (json.JSONDecodeError, TypeError):
                    pass

            # --- Binary messages: QR image crops from senders ---
            elif "bytes" in message:
                binary = message["bytes"]
                if binary:
                    await manager.broadcast_binary(binary)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)

