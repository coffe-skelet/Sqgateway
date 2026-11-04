"""Диагностика: почему generateContent зависает, а countTokens — нет.

Сценарии (короткий таймаут 20с):
  1. Напрямую (без прокси)
  2. Через локальный VPN-прокси (127.0.0.1:10809)
  3. Через прокси + thinkingLevel=LOW

Запуск:  .venv\\Scripts\\python diag.py
"""
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["GEMINI_API_KEY"]
PROXY = os.environ.get("HTTP_PROXY", "http://127.0.0.1:10809")
BASE = "https://generativelanguage.googleapis.com/v1beta"
HEADERS = {"x-goog-api-key": KEY}

b1 = {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}
b2 = {"contents": [{"role": "user", "parts": [{"text": "hi"}]}],
      "generationConfig": {"thinkingConfig": {"thinkingLevel": "LOW"}}}
b3 = {"contents": [{"parts": [{"text": "hi"}]}]}  # для countTokens


def call(name: str, client: httpx.Client, path: str, body: dict) -> None:
    started = time.time()
    try:
        r = client.post(f"{BASE}/models/{path}", json=body, headers=HEADERS, timeout=20)
        taken = round(time.time() - started, 1)
        print(f"{name} -> {r.status_code} ({taken}s) {r.text[:180]}".replace("\n", " "),
              flush=True)
    except Exception as e:
        print(f"{name} -> ERR {type(e).__name__} ({round(time.time() - started, 1)}s)",
              flush=True)


with httpx.Client(trust_env=False) as direct:
    call("direct/generate", direct, "gemini-3.8-flash:generateContent", b1)
    call("direct/countTokens", direct, "gemini-3.8-flash:countTokens", b3)

with httpx.Client(proxy=PROXY, trust_env=False) as via:
    call(f"proxy/generate", via, "gemini-3.8-flash:generateContent", b1)
    call("proxy/countTokens", via, "gemini-3.8-flash:countTokens", b3)
    call("proxy/generate+thinkingLOW", via, "gemini-3.8-flash:generateContent", b2)
