"""
Тестовый чат-клиент Squeeze Gateway (Этап 1).

Говорит со шлюзом так же, как обычное приложение говорило бы с Gemini:
просто направляет запросы на localhost:8080 вместо Google.

Запуск:  python client.py
Выход:   команда /exit или Ctrl+C
"""

import os
import sys

import httpx
from dotenv import load_dotenv

GATEWAY = f"http://localhost:{os.environ.get('GATEWAY_PORT', '8082')}"
MODEL = "gemini-3.6-flash"   # 3.8 сейчас перегружена (503); вернёмся, когда отпустит


def call_gateway(history: list, squeeze: bool) -> (str, dict):
    """Шлёт всю историю диалога через шлюз, возвращает текст ответа и метрики."""
    query = "?squeeze=1" if squeeze else ""
    resp = httpx.post(
        f"{GATEWAY}/v1beta/models/{MODEL}:generateContent{query}",
        json={"contents": history},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text, data.get("usageMetadata", {})


def main() -> None:
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Нет GEMINI_API_KEY. Скопируй .env.example в .env и вставь ключ.")

    history = []
    squeeze = os.environ.get("SQUEEZE", "1") == "1"   # SQUEEZE=0 → выключить сжатие
    print(f"Чат через шлюз ({GATEWAY}). Модель: {MODEL}. Сжатие: {'ВКЛ' if squeeze else 'выкл'}. Для выхода — /exit\n")
    while True:
        try:
            user = input("Ты: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not user:
            continue
        if user.lower() in ("/exit", "/quit"):
            break
        if user.lower() == "/squeeze":
            squeeze = not squeeze
            print(f"Сжатие {'ВКЛ' if squeeze else 'выкл'}\n")
            continue

        history.append({"role": "user", "parts": [{"text": user}]})
        try:
            answer, usage = call_gateway(history, squeeze)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print("Квота Google на сегодня исчерпана (429). Бесплатный тариф ~20 запросов/день. Подожди сброса или включи тариф с оплатой.\n")
            else:
                print(f"Ошибка API {e.response.status_code}: {e.response.text[:300]}\n")
            history.pop()
            continue
        except httpx.RequestError as e:
            print(f"Шлюз недоступен: {e}\n")
            history.pop()
            continue

        history.append({"role": "model", "parts": [{"text": answer}]})
        tokens = usage.get("totalTokenCount", "?")
        print(f"Модель ({tokens} токенов): {answer}\n")

    print("Пока! Статистика шлюза: http://localhost:8080/stats")


if __name__ == "__main__":
    main()
