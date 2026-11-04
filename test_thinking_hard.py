"""Hard-вопрос при разных thinkingLevel с ретраями (503 — шум перегрузки).

Запуск:  .venv\\Scripts\\python test_thinking_hard.py
"""
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["GEMINI_API_KEY"]

HARD_Q = ("Объясни, как квантовая запутанность связана с неравенством Белла "
          "и почему оно исключает локальный скрытый параметризм.")


def main() -> None:
    for lvl in ("LOW", "MEDIUM", "HIGH"):
        body = {
            "contents": [{"role": "user", "parts": [{"text": HARD_Q}]}],
            "generationConfig": {"thinkingConfig": {"thinkingLevel": lvl}},
        }
        for attempt in range(5):
            started = time.time()
            try:
                r = httpx.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
                    headers={"x-goog-api-key": KEY}, json=body, timeout=90, trust_env=False)
                if r.status_code != 503:
                    u = r.json().get("usageMetadata", {})
                    print(f"{lvl:7s} -> {r.status_code}"
                          f" | thought={u.get('thoughtsTokenCount', 0):5d}"
                          f" out={u.get('candidatesTokenCount', 0):5d}"
                          f" total={u.get('totalTokenCount', 0):5d}"
                          f" | {round(time.time() - started, 1)}s (attempt {attempt + 1})")
                    break
            except Exception as e:
                print(f"{lvl:7s} attempt {attempt + 1}: ERR {type(e).__name__}")
            time.sleep(2 ** attempt)


if __name__ == "__main__":
    main()
