"""
PropOS — Database ORM Models

SQLAlchemy models for persistent storage of trades, performance, and logs.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TradeRecord(Base):
    """Persistent record of all executed trades."""
    __tablename__ = "trades"

    id = Column(String, primary_key=True)
    signal_id = Column(String, index=True)
    account_id = Column(String, index=True)
    symbol = Column(String, index=True)
    direction = Column(String)
    volume = Column(Float)
    open_price = Column(Float)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    mt5_ticket = Column(Integer, nullable=True)
    status = Column(String)
    realized_pnl = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    close_reason = Column(String, default="")
    strategy = Column(String, default="")
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)


class DailyPerformance(Base):
    """Daily performance snapshot per account."""
    __tablename__ = "daily_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, index=True)
    date = Column(String, index=True)
    starting_balance = Column(Float)
    ending_balance = Column(Float)
    pnl = Column(Float)
    trades_count = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    max_drawdown_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemLog(Base):
    """System event log for debugging and auditing."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String)
    source = Column(String)
    message = Column(Text)
    data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
