"""Squeeze Gateway package and SDK exports."""

from .sdk import (
    ChatResponse,
    CompressionMode,
    OptimizationMetrics,
    SqueezeClient,
    ThinkingLevel,
    chat,
)

__all__ = [
    "SqueezeClient",
    "CompressionMode",
    "ThinkingLevel",
    "OptimizationMetrics",
    "ChatResponse",
    "chat",
]
__version__ = "0.4.0"