"""
PropOS — FastAPI Application Factory

Creates and configures the FastAPI application with all routes,
middleware, and WebSocket endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import controls, dashboard, health
from backend.api.websocket import websocket_endpoint
from backend.core.config import load_settings
from backend.core.logging import get_logger, setup_logging
from backend.core.scheduler import Scheduler
from backend.core.state import SystemStatus, get_state
from backend.monitoring.telegram import TelegramNotifier
from backend.orchestrator import TradingOrchestrator
from backend.protection.kill_switch import KillSwitch
from backend.storage.database import close_database, init_database

logger = get_logger(__name__)

# Global instances for lifespan
orchestrator: TradingOrchestrator | None = None
scheduler: Scheduler | None = None
telegram: TelegramNotifier | None = None

async def daily_reset_job() -> None:
    """Reset daily trading stats at midnight UTC."""
    state = get_state()
    from backend.storage.repository import TradeRepository
    repo = TradeRepository()
    
    logger.info("Running daily stats reset")
    async with state._lock:
        state.signals_generated_today = 0
        state.total_trades_today = 0
        
        for account in state.accounts.values():
            # Save end of day performance
            await repo.save_daily_performance(
                account_id=account.account_id, 
                date_str=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                pnl=account.daily_pnl, 
                trades=account.trades_today
            )
            account.daily_pnl = 0.0
            account.trades_today = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup and shutdown."""
    settings = load_settings()

    # Setup logging
    setup_logging(
        log_level=settings.secrets.log_level,
        json_output=settings.secrets.env == "production",
    )

    # Init Database
    await init_database()

    # Initialize state
    state = get_state()
    await state.update(status=SystemStatus.STARTING)

    # Initialize kill switch
    kill_switch = KillSwitch()
    controls.set_kill_switch(kill_switch)

    # Init Telegram
    global telegram
    telegram = TelegramNotifier(
        bot_token=settings.secrets.telegram_bot_token,
        chat_id=settings.secrets.telegram_chat_id,
        enabled=settings.telegram.enabled
    )
    await telegram.initialize()
    telegram.subscribe_to_events()
    
    # Init Orchestrator
    global orchestrator
    orchestrator = TradingOrchestrator()
    await orchestrator.initialize()

    # Init Scheduler
    global scheduler
    scheduler = Scheduler()
    scheduler.add_interval_job(
        orchestrator.tick, 
        seconds=settings.strategy.tick_interval_seconds, 
        job_id="orchestrator_tick"
    )
    scheduler.add_cron_job(
        daily_reset_job,
        cron_expression="0 0 * * *", # Midnight UTC
        job_id="daily_reset"
    )
    scheduler.start()

    logger.info("PropOS starting", version="1.0.0", env=settings.secrets.env)
    await state.update(status=SystemStatus.RUNNING)
    await telegram.notify_system_status("running")

    yield

    # Shutdown
    await state.update(status=SystemStatus.STOPPING)
    await telegram.notify_system_status("stopping")
    
    if scheduler:
        scheduler.shutdown()
    if orchestrator:
        await orchestrator.shutdown()
        
    await close_database()
    
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

    # API Auth Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    class APIAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Skip auth for health, websockets, docs, options
            path = request.url.path
            if (path.startswith("/api/health") or 
                path.startswith("/ws") or 
                path.startswith("/docs") or 
                path.startswith("/openapi.json") or
                request.method == "OPTIONS"):
                return await call_next(request)

            # Check header
            api_key = request.headers.get("x-api-key")
            if not api_key or api_key != settings.secrets.api_secret_key:
                # To allow testing dashboard right away, if "change-this" is still set, we can implicitly allow localhost devs
                if api_key != settings.secrets.api_secret_key and not (settings.secrets.env == "development" and settings.secrets.api_secret_key == "change-this"):
                    return JSONResponse(status_code=401, content={"detail": "Unauthorized. Invalid or missing X-API-Key."})

            return await call_next(request)
            
    app.add_middleware(APIAuthMiddleware)

    # REST routes
    app.include_router(dashboard.router)
    app.include_router(controls.router)
    app.include_router(health.router)

    # WebSocket
    app.websocket("/ws")(websocket_endpoint)

    return app
