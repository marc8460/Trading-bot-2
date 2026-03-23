"""
PropOS — FastAPI Application Factory

Creates and configures the FastAPI application with all routes,
middleware, and WebSocket endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import controls, dashboard, health
from backend.api.websocket import websocket_endpoint
from backend.core.config import load_settings
from backend.core.logging import get_logger, setup_logging
from backend.core.state import SystemStatus, get_state
from backend.protection.kill_switch import KillSwitch

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup and shutdown."""
    settings = load_settings()

    # Setup logging
    setup_logging(
        log_level=settings.secrets.log_level,
        json_output=settings.secrets.env == "production",
    )

    # Initialize state
    state = get_state()
    await state.update(status=SystemStatus.STARTING)

    # Initialize kill switch
    kill_switch = KillSwitch()
    controls.set_kill_switch(kill_switch)

    logger.info("PropOS starting", version="1.0.0", env=settings.secrets.env)
    await state.update(status=SystemStatus.RUNNING)

    yield

    # Shutdown
    await state.update(status=SystemStatus.STOPPED)
    logger.info("PropOS stopped")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = load_settings()

    app = FastAPI(
        title="PropOS — Multi-Account Prop Trading OS",
        description="Real-time trading platform API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routes
    app.include_router(dashboard.router)
    app.include_router(controls.router)
    app.include_router(health.router)

    # WebSocket
    app.websocket("/ws")(websocket_endpoint)

    return app
