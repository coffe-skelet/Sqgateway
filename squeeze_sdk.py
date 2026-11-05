"""
Squeeze Gateway Python SDK
Easy integration for Python applications
"""

from typing import Optional, Dict, List, Any, Union
import httpx
from dataclasses import dataclass
from enum import Enum


class CompressionMode(Enum):
    """Compression modes"""
    AUTO = "auto"
    CPP = "cpp"
    LLM = "llm"
    OFF = "off"


class ThinkingLevel(Enum):
    """Thinking levels"""
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "-"


@dataclass
class OptimizationMetrics:
    """Optimization metrics from gateway"""
    mode: str
    input_tokens: int
    baseline_tokens: int
    saved_tokens: int
    aux_tokens: int
    net_saved: int
    thinking_tokens: int
    thinking_level: str
    latency_ms: float


@dataclass
class ChatResponse:
    """Response from chat completion"""
    text: str
    metrics: Optional[OptimizationMetrics] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict] = None


class SqueezeClient:
    """
    Squeeze Gateway Python Client

    Examples:
        >>> client = SqueezeClient(api_key="YOUR_KEY")
        >>> response = client.chat("Explain quantum physics")
        >>> print(response.text)
        >>> print(f"Tokens saved: {response.metrics.net_saved}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gateway_url: str = "http://localhost:8082",
        mode: Union[str, CompressionMode] = CompressionMode.AUTO,
        thinking: Union[str, ThinkingLevel] = ThinkingLevel.AUTO,
        model: str = "gemini-3.6-flash",
        timeout: float = 60.0
    ):
        """
        Initialize Squeeze Gateway client

        Args:
            api_key: Gemini API key (if not configured in gateway)
            gateway_url: Gateway base URL
            mode: Default compression mode
            thinking: Default thinking level
            model: Default model to use
            timeout: Request timeout in seconds
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.api_key = api_key
        self.mode = mode.value if isinstance(mode, CompressionMode) else mode
        self.thinking = thinking.value if isinstance(thinking, ThinkingLevel) else thinking
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._sync_client = httpx.Client(timeout=timeout)

    def chat(
        self,
        message: str,
        history: Optional[List[Dict]] = None,
        mode: Optional[Union[str, CompressionMode]] = None,
        thinking: Optional[Union[str, ThinkingLevel]] = None,
        model: Optional[str] = None
    ) -> ChatResponse:
        """
        Send a chat message (synchronous)

        Args:
            message: User message
            history: Conversation history
            mode: Override compression mode
            thinking: Override thinking level
            model: Override model

        Returns:
            ChatResponse with text and metrics
        """
        # Build request
        mode = mode or self.mode
        thinking = thinking or self.thinking
        model = model or self.model

        if isinstance(mode, CompressionMode):
            mode = mode.value
        if isinstance(thinking, ThinkingLevel):
            thinking = thinking.value

        # Build conversation
        contents = history or []
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        # Build query params
        params = {"squeeze": mode}
        if thinking != "-":
            params["thinking"] = thinking

        # Make request
        response = self._sync_client.post(
            f"{self.gateway_url}/v1beta/models/{model}:generateContent",
            params=params,
            json={"contents": contents}
        )

        response.raise_for_status()
        data = response.json()
        headers = response.headers

        # Extract response text
        answer = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

        # Extract metrics
        usage = data.get('usageMetadata', {})

        metrics = OptimizationMetrics(
            mode=self._parse_mode_label(headers.get('x-squeeze-mode', 'passthrough')),
            input_tokens=int(headers.get('x-squeeze-input', usage.get('promptTokenCount', 0))),
            baseline_tokens=int(headers.get('x-squeeze-baseline', 0)),
            saved_tokens=int(headers.get('x-squeeze-saved', 0)),
            aux_tokens=int(headers.get('x-squeeze-aux', 0)),
            net_saved=int(headers.get('x-squeeze-saved', 0)) - int(headers.get('x-squeeze-aux', 0)),
            thinking_tokens=usage.get('thoughtsTokenCount', 0),
            thinking_level=headers.get('x-squeeze-thinking', 'client'),
            latency_ms=float(headers.get('x-squeeze-latency', 0))
        )

        return ChatResponse(
            text=answer,
            metrics=metrics,
            usage=usage,
            raw_response=data
        )

    async def chat_async(
        self,
        message: str,
        history: Optional[List[Dict]] = None,
        mode: Optional[Union[str, CompressionMode]] = None,
        thinking: Optional[Union[str, ThinkingLevel]] = None,
        model: Optional[str] = None
    ) -> ChatResponse:
        """Async version of chat()"""
        mode = mode or self.mode
        thinking = thinking or self.thinking
        model = model or self.model

        if isinstance(mode, CompressionMode):
            mode = mode.value
        if isinstance(thinking, ThinkingLevel):
            thinking = thinking.value

        contents = history or []
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        params = {"squeeze": mode}
        if thinking != "-":
            params["thinking"] = thinking

        response = await self._client.post(
            f"{self.gateway_url}/v1beta/models/{model}:generateContent",
            params=params,
            json={"contents": contents}
        )

        response.raise_for_status()
        data = response.json()
        headers = response.headers

        answer = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        usage = data.get('usageMetadata', {})

        metrics = OptimizationMetrics(
            mode=self._parse_mode_label(headers.get('x-squeeze-mode', 'passthrough')),
            input_tokens=int(headers.get('x-squeeze-input', usage.get('promptTokenCount', 0))),
            baseline_tokens=int(headers.get('x-squeeze-baseline', 0)),
            saved_tokens=int(headers.get('x-squeeze-saved', 0)),
            aux_tokens=int(headers.get('x-squeeze-aux', 0)),
            net_saved=int(headers.get('x-squeeze-saved', 0)) - int(headers.get('x-squeeze-aux', 0)),
            thinking_tokens=usage.get('thoughtsTokenCount', 0),
            thinking_level=headers.get('x-squeeze-thinking', 'client'),
            latency_ms=float(headers.get('x-squeeze-latency', 0))
        )

        return ChatResponse(
            text=answer,
            metrics=metrics,
            usage=usage,
            raw_response=data
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics (synchronous)"""
        response = self._sync_client.get(f"{self.gateway_url}/api/summary")
        response.raise_for_status()
        return response.json()

    async def get_stats_async(self) -> Dict[str, Any]:
        """Get gateway statistics (async)"""
        response = await self._client.get(f"{self.gateway_url}/api/summary")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check gateway health (synchronous)"""
        response = self._sync_client.get(f"{self.gateway_url}/health")
        response.raise_for_status()
        return response.json()

    async def health_check_async(self) -> Dict[str, Any]:
        """Check gateway health (async)"""
        response = await self._client.get(f"{self.gateway_url}/health")
        response.raise_for_status()
        return response.json()

    def _parse_mode_label(self, mode: str) -> str:
        """Parse mode label from header"""
        if mode == 'squeeze_cpp':
            return 'cpp'
        elif mode == 'squeeze_llm':
            return 'llm'
        else:
            return 'passthrough'

    def close(self):
        """Close sync client"""
        self._sync_client.close()

    async def aclose(self):
        """Close async client"""
        await self._client.aclose()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()


# Convenience function
def chat(
    message: str,
    api_key: Optional[str] = None,
    gateway_url: str = "http://localhost:8082",
    mode: Union[str, CompressionMode] = CompressionMode.AUTO,
    thinking: Union[str, ThinkingLevel] = ThinkingLevel.AUTO,
    model: str = "gemini-3.6-flash"
) -> str:
    """
    Quick one-shot chat function

    Example:
        >>> response = squeeze.chat("What is quantum entanglement?")
        >>> print(response)
    """
    with SqueezeClient(api_key, gateway_url, mode, thinking, model) as client:
        response = client.chat(message)
        return response.text
