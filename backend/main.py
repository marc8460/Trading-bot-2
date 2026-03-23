"""
PropOS — Application Entry Point

Starts the FastAPI server with uvicorn.
Usage: python -m backend.main
"""

from __future__ import annotations

import uvicorn

from backend.app import create_app
from backend.core.config import load_settings


def main() -> None:
    """Start the PropOS backend server."""
    settings = load_settings()

    app = create_app()

    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.secrets.log_level.lower(),
        reload=settings.secrets.env == "development",
    )


if __name__ == "__main__":
    main()
