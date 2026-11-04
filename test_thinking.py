"""Диагностика thinkingLevel: сколько жрёт модель 'мозгов' на уровнях LOW/MEDIUM/HIGH.

Зачем: проверить гипотезу Этапа 4.5 — что на простых вопросах LOW
даёт огромную экономию токенов и латентности без потери качества.

Запуск:  .venv\\Scripts\\python test_thinking.py
"""
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["GEMINI_API_KEY"]

QUESTIONS = [
    ("simple", "Что такое квантовая запутанность? Ответь в 2-3 предложениях."),
    ("hard", "Объясни, как квантовая запутанность связана с неравенством Белла и почему "
             "оно исключает локальный скрытый параметризм. Дай выводы для философии науки."),
]
LEVELS = [None, "LOW", "MEDIUM", "HIGH"]


def run(model: str) -> None:
    print(f"\n=== {model} ===")
    for qname, q in QUESTIONS:
        for lvl in LEVELS:
            body = {"contents": [{"role": "user", "parts": [{"text": q}]}]}
            if lvl:
                body["generationConfig"] = {"thinkingConfig": {"thinkingLevel": lvl}}
            started = time.time()
            try:
                r = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": KEY}, json=body, timeout=90, trust_env=False)
                u = r.json().get("usageMetadata", {})
                print(f"{qname:6s} {str(lvl):7s} -> {r.status_code}"
                      f" | thought={u.get('thoughtsTokenCount', 0):5d}"
                      f" out={u.get('candidatesTokenCount', 0):5d}"
                      f" total={u.get('totalTokenCount', 0):5d}"
                      f" | {round(time.time() - started, 1)}s")
            except Exception as e:
                print(f"{qname:6s} {str(lvl):7s} -> ERR {type(e).__name__}"
                      f" | {round(time.time() - started, 1)}s")


if __name__ == "__main__":
    run("gemini-3.6-flash")
