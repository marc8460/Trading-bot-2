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

    is_dev = settings.secrets.env == "development"

    uvicorn.run(
        "backend.app:create_app" if is_dev else create_app(),
        host=settings.api.host,
        port=settings.api.port,
        log_level=settings.secrets.log_level.lower(),
        reload=is_dev,
        factory=is_dev,
    )


if __name__ == "__main__":
    main()
