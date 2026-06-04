from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def setup_cors(app) -> None:
    """Mount CORS middleware.

    IMPORTANT: allow_origins=['*'] is incompatible with allow_credentials=True per CORS spec.
    In dev, we use a broad explicit list. In production, set CORS_ORIGINS in .env explicitly.
    """
    origins = settings.CORS_ORIGINS

    # If wildcard is in the list, replace with explicit broad dev origins
    # (wildcard + credentials is rejected by browsers/mobile HTTP clients)
    if "*" in origins:
        origins = [
            "http://localhost:8000",
            "http://localhost:3000",
            "http://localhost:5173",   # Vite admin web
            "http://localhost:5174",   # Vite admin web (fallback port)
            "http://localhost:19006",   # Expo web
            "http://10.196.131.225:8000",
            "http://10.196.131.225:8001",
            "http://192.168.100.211:8000",
            "http://192.168.100.211:19006",
            "exp://192.168.100.211:8081",
            "http://192.168.1.160:8000",
            "http://192.168.1.160:19006",
            "exp://192.168.1.160:8081",
            # Add more as needed in .env: CORS_ORIGINS=["http://your-ip:port"]
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
