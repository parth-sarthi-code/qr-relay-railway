"""FastAPI application — HTTP routes and WebSocket endpoint."""

import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse

from app.ws_manager import manager

app = FastAPI(title="QR Image Relay")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


# --------------------------------------------------------------------------
# HTTP Routes (Supports both GET and HEAD for cloud healthcheckers)
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


@app.api_route("/status", methods=["GET", "HEAD"])
async def status():
    return await manager.get_stats()


# --------------------------------------------------------------------------
# WebSocket Endpoint (Handles binary images, roles, and keepalive pings)
# --------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    accepted = await manager.connect(websocket)
    if not accepted:
        return  # rejected (at capacity)

    try:
        while True:
            message = await websocket.receive()

            # Text payload: roles or keep-alive pings
            if "text" in message:
                text = message["text"]
                if not text:
                    continue
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        msg_type = data.get("type")
                        if msg_type == "role":
                            role = data.get("role")
                            if role in ("sender", "viewer"):
                                await manager.set_role(websocket, role)
                        elif msg_type == "ping":
                            await websocket.send_text('{"type":"pong"}')
                        elif msg_type in ("ring", "ready"):
                            action = data.get("action", "start")
                            await manager.broadcast_to_viewers(
                                json.dumps({
                                    "type": "ring",
                                    "action": action,
                                })
                            )
                except (json.JSONDecodeError, TypeError):
                    pass

            # Binary payload: QR crops from senders
            elif "bytes" in message:
                binary = message["bytes"]
                if binary:
                    await manager.broadcast_binary(binary)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
