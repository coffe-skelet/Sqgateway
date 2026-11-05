"""Squeeze Gateway Python SDK."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx


class CompressionMode(Enum):
    AUTO = "auto"
    CPP = "cpp"
    LLM = "llm"
    OFF = "off"


class ThinkingLevel(Enum):
    AUTO = "auto"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "-"


@dataclass
class OptimizationMetrics:
    mode: str
    input_tokens: int
    baseline_tokens: int
    aux_tokens: int
    net_saved: int
    thinking_tokens: int
    thinking_level: str
    latency_ms: float

    @property
    def saved_tokens(self) -> int:
        return self.net_saved


@dataclass
class ChatResponse:
    text: str
    metrics: Optional[OptimizationMetrics] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict] = None


class SqueezeClient:
    """Client for the Gemini-compatible Squeeze Gateway HTTP API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        gateway_url: str = "http://127.0.0.1:8082",
        mode: Union[str, CompressionMode] = CompressionMode.AUTO,
        thinking: Union[str, ThinkingLevel] = ThinkingLevel.AUTO,
        model: str = "gemini-2.5-flash",
        timeout: float = 60.0,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.api_key = api_key
        self.mode = mode.value if isinstance(mode, CompressionMode) else mode
        self.thinking = thinking.value if isinstance(thinking, ThinkingLevel) else thinking
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    def _sync(self) -> httpx.Client:
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self.timeout)
        return self._sync_client

    def _async(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    @staticmethod
    def _params(mode, thinking) -> Dict[str, str]:
        mode = mode.value if isinstance(mode, CompressionMode) else mode
        thinking = thinking.value if isinstance(thinking, ThinkingLevel) else thinking
        params = {"squeeze": mode}
        if thinking != "-":
            params["thinking"] = thinking
        return params

    def _build_response(self, response: httpx.Response) -> ChatResponse:
        response.raise_for_status()
        data = response.json()
        usage = data.get("usageMetadata", {})
        headers = response.headers
        candidates = data.get("candidates") or [{}]
        answer = ""
        if candidates:
            answer = (candidates[0].get("content") or {}).get("parts", [{}])[0].get("text", "")
        baseline = int(headers.get("x-squeeze-baseline", 0) or 0)
        aux = int(headers.get("x-squeeze-aux", 0) or 0)
        net = max(0, baseline - int(usage.get("promptTokenCount", 0) or 0) - aux)
        metrics = OptimizationMetrics(
            mode=self._parse_mode(headers.get("x-squeeze-mode", "passthrough")),
            input_tokens=int(headers.get("x-squeeze-input", usage.get("promptTokenCount", 0))),
            baseline_tokens=baseline,
            aux_tokens=aux,
            net_saved=net,
            thinking_tokens=int(usage.get("thoughtsTokenCount", 0) or 0),
            thinking_level=headers.get("x-squeeze-thinking", "client"),
            latency_ms=float(headers.get("x-squeeze-elapsed-ms", 0)),
        )
        return ChatResponse(answer, metrics, usage, data)

    def chat(self, message, history=None, mode=None, thinking=None, model=None):
        contents = list(history or [])
        contents.append({"role": "user", "parts": [{"text": message}]})
        response = self._sync().post(
            f"{self.gateway_url}/v1beta/models/{model or self.model}:generateContent",
            params=self._params(mode or self.mode, thinking or self.thinking),
            json={"contents": contents},
        )
        return self._build_response(response)

    async def chat_async(self, message, history=None, mode=None, thinking=None, model=None):
        contents = list(history or [])
        contents.append({"role": "user", "parts": [{"text": message}]})
        response = await self._async().post(
            f"{self.gateway_url}/v1beta/models/{model or self.model}:generateContent",
            params=self._params(mode or self.mode, thinking or self.thinking),
            json={"contents": contents},
        )
        return self._build_response(response)

    def get_stats(self) -> Dict[str, Any]:
        response = self._sync().get(f"{self.gateway_url}/api/summary")
        response.raise_for_status()
        return response.json()

    async def get_stats_async(self) -> Dict[str, Any]:
        response = await self._async().get(f"{self.gateway_url}/api/summary")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        response = self._sync().get(f"{self.gateway_url}/health")
        response.raise_for_status()
        return response.json()

    async def health_check_async(self) -> Dict[str, Any]:
        response = await self._async().get(f"{self.gateway_url}/health")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _parse_mode(mode: str) -> str:
        return {"squeeze_cpp": "cpp", "squeeze_llm": "llm"}.get(mode, "passthrough")

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
        self._sync_client = None

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
        self._client = None
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()


def chat(
    message: str,
    api_key: Optional[str] = None,
    gateway_url: str = "http://127.0.0.1:8082",
    mode: Union[str, CompressionMode] = CompressionMode.AUTO,
    thinking: Union[str, ThinkingLevel] = ThinkingLevel.AUTO,
    model: str = "gemini-2.5-flash",
) -> str:
    with SqueezeClient(api_key, gateway_url, mode, thinking, model) as client:
        return client.chat(message).text