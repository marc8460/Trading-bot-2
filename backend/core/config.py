"""
PropOS — Configuration Management

Three-tier configuration system:
1. .env                    → Secrets (MT5 passwords, API keys)
2. config/settings.yaml    → Global system settings
3. config/accounts.yaml    → Account definitions
4. config/firms/*.yaml     → Per-firm compliance profiles

Environment variables override YAML values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from enum import Enum


# ──────────────────────────────────────────────
# Path resolution
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
FIRMS_DIR = CONFIG_DIR / "firms"
DATA_DIR = PROJECT_ROOT / "data"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


# ──────────────────────────────────────────────
# Sub-models for settings.yaml
# ──────────────────────────────────────────────


class SymbolConfig(BaseModel):
    symbol: str
    enabled: bool = True
    timeframe: str = "M15"
    role: str = "core"  # core | booster | optional


class StrategySettings(BaseModel):
    active_strategy: str = "trend_pullback"
    symbols: list[SymbolConfig] = Field(default_factory=list)
    tick_interval_seconds: int = 15


class SymbolRiskProfile(BaseModel):
    max_spread_points: int = 20
    max_lot_size: float = 10.0
    min_lot_size: float = 0.01


class RiskSettings(BaseModel):
    default_risk_per_trade_pct: float = 1.0
    max_risk_per_trade_pct: float = 2.0
    max_daily_trades: int = 5
    max_open_positions: int = 3
    correlation_pairs: list[list[str]] = Field(default_factory=list)
    symbol_profiles: dict[str, SymbolRiskProfile] = Field(default_factory=dict)


class SessionWindow(BaseModel):
    name: str
    start: str
    end: str
    timezone: str = "UTC"


class SpreadFilterSettings(BaseModel):
    enabled: bool = True


class SessionFilterSettings(BaseModel):
    enabled: bool = True
    allowed_sessions: list[SessionWindow] = Field(default_factory=list)


class NewsFilterSettings(BaseModel):
    enabled: bool = True
    minutes_before: int = 15
    minutes_after: int = 15
    min_impact: str = "high"


class VolatilityFilterSettings(BaseModel):
    enabled: bool = True
    atr_period: int = 14
    min_atr_multiplier: float = 0.5
    max_atr_multiplier: float = 3.0


class FilterSettings(BaseModel):
    spread: SpreadFilterSettings = Field(default_factory=SpreadFilterSettings)
    session: SessionFilterSettings = Field(default_factory=SessionFilterSettings)
    news: NewsFilterSettings = Field(default_factory=NewsFilterSettings)
    volatility: VolatilityFilterSettings = Field(default_factory=VolatilityFilterSettings)


class ProtectionSettings(BaseModel):
    kill_switch_enabled: bool = True
    connection_check_interval_seconds: int = 30
    max_reconnect_attempts: int = 5
    abnormal_spread_multiplier: float = 5.0


class ExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    PAPER = "paper"
    LIVE = "live"


class ExecutionSettings(BaseModel):
    mode: ExecutionMode = ExecutionMode.DRY_RUN
    confirm_live: bool = True
    max_lot_cap: float = Field(0.50, description="Hard ceiling on any single order volume")
    allowed_symbols: list[str] = Field(
        default_factory=lambda: ["EURUSD"],
        description="Whitelist of symbols allowed for PAPER/LIVE execution",
    )


class TelegramNotificationSettings(BaseModel):
    trade_opened: bool = True
    trade_closed: bool = True
    warnings: bool = True
    kill_switch: bool = True
    daily_summary: bool = True
    bot_status: bool = True


class TelegramSettings(BaseModel):
    enabled: bool = True
    notifications: TelegramNotificationSettings = Field(
        default_factory=TelegramNotificationSettings
    )


class ApiSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class DatabaseSettings(BaseModel):
    url: str = "sqlite+aiosqlite:///./data/propos.db"
    echo: bool = False


class MonitoringSettings(BaseModel):
    trade_log_enabled: bool = True
    performance_tracking: bool = True
    health_check_interval_seconds: int = 60


# ──────────────────────────────────────────────
# Environment-based secrets
# ──────────────────────────────────────────────


class EnvSecrets(BaseSettings):
    """Loaded from .env file automatically."""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    api_secret_key: str = "change-this"
    database_url: str = ""
    env: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "extra": "ignore"}


# ──────────────────────────────────────────────
# Master Settings
# ──────────────────────────────────────────────


class Settings(BaseModel):
    """Master settings object combining YAML config + env secrets."""

    strategy: StrategySettings = Field(default_factory=StrategySettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    filters: FilterSettings = Field(default_factory=FilterSettings)
    protection: ProtectionSettings = Field(default_factory=ProtectionSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    secrets: EnvSecrets = Field(default_factory=EnvSecrets)


def load_settings() -> Settings:
    """Load settings from YAML + .env, returning a validated Settings object."""
    yaml_data = _load_yaml(CONFIG_DIR / "settings.yaml")
    secrets = EnvSecrets()

    # Merge DB URL from env if present
    if secrets.database_url:
        yaml_data.setdefault("database", {})["url"] = secrets.database_url

    settings = Settings(**yaml_data, secrets=secrets)
    return settings


def load_accounts_config() -> list[dict[str, Any]]:
    """Load account definitions from accounts.yaml."""
    data = _load_yaml(CONFIG_DIR / "accounts.yaml")
    return data.get("accounts", [])


def load_firm_profile(firm_slug: str) -> dict[str, Any]:
    """Load a single firm compliance profile YAML."""
    path = FIRMS_DIR / f"{firm_slug}.yaml"
    return _load_yaml(path)


def load_all_firm_profiles() -> dict[str, dict[str, Any]]:
    """Load all firm compliance profiles from config/firms/."""
    profiles: dict[str, dict[str, Any]] = {}
    if FIRMS_DIR.exists():
        for yaml_file in FIRMS_DIR.glob("*.yaml"):
            data = _load_yaml(yaml_file)
            slug = data.get("slug", yaml_file.stem)
            profiles[slug] = data
    return profiles
