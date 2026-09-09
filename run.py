#!/usr/bin/env python3
"""Unified, zero-configuration runner for QR Image Relay.

Auto-detects environment (Cloud vs Local):
- Cloud (Railway, Render, Fly, Container): Binds to $PORT over HTTP behind proxy with forwarded headers.
- Local: Auto-provisions self-signed SSL (for mobile camera support) and discovers LAN IP.
"""

import os
import socket
import subprocess
import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / "certs"
KEY_FILE = CERT_DIR / "server.key"
CERT_FILE = CERT_DIR / "server.crt"


def get_lan_ip() -> str:
    """Discover the local LAN IP address."""
    # Method 1: Query routing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # Method 2: ip route command fallback
    try:
        out = subprocess.check_output(
            ["ip", "-4", "route", "get", "8.8.8.8"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        tokens = out.split()
        if "src" in tokens:
            return tokens[tokens.index("src") + 1]
    except Exception:
        pass

    return "127.0.0.1"


def ensure_local_certs() -> bool:
    """Generate self-signed certificates locally if openssl is available."""
    if KEY_FILE.exists() and CERT_FILE.exists():
        return True

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048",
                "-days", "365",
                "-keyout", str(KEY_FILE),
                "-out", str(CERT_FILE),
                "-subj", "/CN=qr-relay.local/O=QR Relay/C=US"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


def is_cloud_env() -> bool:
    """Check if running in a containerized cloud environment."""
    cloud_indicators = (
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PROJECT_ID",
        "RENDER",
        "FLY_APP_NAME",
        "K_SERVICE",
        "HEROKU_APP_NAME",
        "CONTAINER",
        "DOCKER_CONTAINER"
    )
    if any(os.environ.get(var) for var in cloud_indicators):
        return True

    # If PORT is explicitly set and not in an interactive tty
    if "PORT" in os.environ and not sys.stdout.isatty():
        return True

    return False


def main():
    # Read port dynamically from environment or default to 8000
    port_env = os.environ.get("PORT", "8000")
    try:
        port = int(port_env)
    except ValueError:
        port = 8000

    cloud = is_cloud_env() or "--cloud" in sys.argv
    force_local = "--local" in sys.argv

    if cloud and not force_local:
        # --------------------------------------------------------------
        # CLOUD MODE (Railway, Render, Containers)
        # --------------------------------------------------------------
        print("==========================================")
        print("  QR Image Relay Server [Cloud Mode]")
        print(f"  Listening internally on 0.0.0.0:{port}")
        print("  TLS / SSL handled by Cloud Reverse Proxy")
        print("==========================================")
        sys.stdout.flush()

        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            proxy_headers=True,
            forwarded_allow_ips="*",
            log_level="info"
        )
    else:
        # --------------------------------------------------------------
        # LOCAL DEVELOPMENT MODE
        # --------------------------------------------------------------
        has_certs = ensure_local_certs()
        lan_ip = get_lan_ip()

        ssl_kwargs = {}
        protocol = "http"
        if has_certs:
            ssl_kwargs = {
                "ssl_keyfile": str(KEY_FILE),
                "ssl_certfile": str(CERT_FILE)
            }
            protocol = "https"

        print("")
        print("==========================================")
        print(f"  QR Image Relay Server [Local Mode]")
        print("==========================================")
        print(f"  Local:    {protocol}://localhost:{port}")
        if lan_ip and lan_ip != "127.0.0.1":
            print(f"  Network:  {protocol}://{lan_ip}:{port}")
        print("==========================================")
        print("  Sender:   /sender.html")
        print("  Viewer:   /viewer.html  (or /)")
        print("  Status:   /status")
        print("==========================================")
        print("")
        sys.stdout.flush()

        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            **ssl_kwargs
        )


if __name__ == "__main__":
    main()
