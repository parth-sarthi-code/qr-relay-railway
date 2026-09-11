"""Application configuration and constants."""


class Settings:
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # WebSocket limits
    MAX_CONNECTIONS: int = 150          # headroom above 120 target
    SEND_TIMEOUT: float = 2.5          # seconds — drop unresponsive viewers (mobile-friendly)
    MAX_FRAME_SIZE: int = 1_000_000    # bytes — reject oversized blobs (~1 MB)


settings = Settings()
