"""
PropOS — Strategy Registry

Dynamic strategy registration and lookup.
Strategies register by name and can be swapped at runtime.
"""

from __future__ import annotations

from typing import Type

from backend.core.logging import get_logger
from backend.strategy.base import BaseStrategy

logger = get_logger(__name__)


class StrategyRegistry:
    """Registry for available trading strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, Type[BaseStrategy]] = {}

    def register(self, name: str, strategy_cls: Type[BaseStrategy]) -> None:
        """Register a strategy class by name."""
        self._strategies[name] = strategy_cls
        logger.info("Registered strategy", name=name, cls=strategy_cls.__name__)

    def get(self, name: str) -> Type[BaseStrategy] | None:
        """Get a strategy class by name."""
        return self._strategies.get(name)

    def create(self, name: str, **params: dict) -> BaseStrategy:
        """Create a strategy instance by name."""
        cls = self.get(name)
        if cls is None:
            raise ValueError(f"Unknown strategy: {name}")
        return cls(**params)

    def list_available(self) -> list[str]:
        """List all registered strategy names."""
        return list(self._strategies.keys())


def create_default_registry() -> StrategyRegistry:
    """Create a registry with all built-in strategies."""
    from backend.strategy.breakout import BreakoutStrategy
    from backend.strategy.trend_pullback import TrendPullbackStrategy

    registry = StrategyRegistry()
    registry.register("trend_pullback", TrendPullbackStrategy)
    registry.register("breakout", BreakoutStrategy)
    return registry
