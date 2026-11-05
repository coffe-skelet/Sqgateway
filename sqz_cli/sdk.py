"""Backward-compatible SDK imports."""

from .sdk_impl import (
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
