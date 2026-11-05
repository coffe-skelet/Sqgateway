"""
Squeeze Gateway SDK - Package exports
"""

from .squeeze_sdk import (
    SqueezeClient,
    CompressionMode,
    ThinkingLevel,
    OptimizationMetrics,
    ChatResponse,
    chat,
)

__all__ = [
    'SqueezeClient',
    'CompressionMode',
    'ThinkingLevel',
    'OptimizationMetrics',
    'ChatResponse',
    'chat',
]

__version__ = '0.3.0'
