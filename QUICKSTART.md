# Squeeze Gateway — Quick Start Guide

## 🎯 3 способа использования

### 1️⃣ CLI (Терминальный агент) — рекомендуется

```bash
# Установка
pip install squeeze-gateway

# Настройка за 30 секунд
sqz install
sqz config set api_key YOUR_GEMINI_KEY
sqz start

# Интерактивный чат
sqz chat
```

**Возможности CLI:**
- ✅ Терминальный агент как Claude Code
- ✅ Автоматический запуск и управление шлюзом
- ✅ Интерактивный чат с real-time метриками
- ✅ Статистика и мониторинг
- ✅ Простая конфигурация

### 2️⃣ Python SDK

```python
from sqz_cli.sdk import SqueezeClient, CompressionMode

# Быстрый старт
client = SqueezeClient()
response = client.chat("Explain quantum computing")
print(response.text)
print(f"Saved: {response.metrics.net_saved} tokens")

# Или одной строкой
from sqz_cli.sdk import chat
answer = chat("What is machine learning?")
```

### 3️⃣ HTTP API (прозрачный прокси)

```bash
# Запуск сервера
sqz start

# Или вручную
uvicorn server:app --port 8082
```

```python
import requests

response = requests.post(
    "http://localhost:8082/v1beta/models/gemini-3.6-flash:generateContent?squeeze=auto",
    json={"contents": [{"role": "user", "parts": [{"text": "Hello!"}]}]}
)
```

---

## 📦 Установка и настройка

### Требования

- Python 3.10+
- Gemini API key (получить на [ai.google.dev](https://ai.google.dev/aistudio))

### Полная установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/kirill-skoch/squeeze-gateway.git
cd squeeze-gateway

# 2. Установить пакет
pip install -e .

# 3. (Опционально) Собрать C++ модуль для максимальной производительности
cd core && mkdir build && cd build
cmake .. && make
cd ../..

# 4. Инициализация
sqz install

# 5. Настройка API ключа
sqz config set api_key YOUR_GEMINI_API_KEY

# 6. Запуск
sqz start

# 7. Проверка
sqz status
```

### Быстрая установка (без C++ модуля)

```bash
pip install squeeze-gateway
sqz install
sqz config set api_key YOUR_KEY
sqz start
```

> **Примечание:** C++ модуль дает максимальную производительность сжатия (<1ms overhead), но необязателен. Без него шлюз использует Python fallback.

---

## 🎮 Использование CLI

### Команды управления

```bash
sqz install              # Первичная настройка
sqz start               # Запустить шлюз (foreground)
sqz start --daemon      # Запустить в фоне
sqz stop                # Остановить шлюз
sqz status              # Проверить статус и метрики
```

### Интерактивный чат

```bash
sqz chat                                    # Базовый режим
sqz chat --mode cpp --thinking low          # С параметрами
sqz chat --model gemini-3.6-flash          # Выбор модели
```

**Команды в чате:**

- `/exit`, `/quit` — выход
- `/clear` — очистить историю разговора
- `/stats` — показать статистику сессии
- `/mode <auto|cpp|llm|off>` — сменить режим сжатия
- `/thinking <auto|low|medium|high|->` — сменить уровень мышления

**Пример сессии:**

```
You > Explain quantum entanglement in simple terms

⏳ Gateway optimizing and processing...

┌─ Assistant [15:42:31]
│ Quantum entanglement is a phenomenon where two particles become
│ connected in such a way that the state of one instantly affects
│ the other, regardless of distance...
│
│ ─────────────────────────────────────────────────────────────────
│ 📈 Optimization Metrics:
│   🟢 Mode: CPP     │ Input: 127      / 182      baseline
│   💰 Saved: 55      │ Aux: 0         │ Net: 55
│   🧠 Thinking: low  │ Tokens: 342    │ Time: 4.2s
└──────────────────────────────────────────────────────────────────
```

### Просмотр статистики

```bash
sqz stats                    # Общая статистика
sqz stats --limit 20         # Последние 20 запросов
sqz stats --export stats.json # Экспорт в файл
```

**Вывод:**

```
📊 Squeeze Gateway Statistics

============================================================
OVERALL STATISTICS
============================================================
Total Requests:       1,247
Tokens Saved:         52,890
Savings Rate:         42.3%
Average Latency:      156ms

============================================================
RECENT REQUESTS (last 10)
============================================================
Mode     Input    Baseline Saved    Think    Time
------------------------------------------------------------
cpp      182      255      73       0        1.2s
llm      3245     5670     2425     234      3.4s
cpp      127      189      62       0        0.9s
```

### Конфигурация

```bash
sqz config list                         # Показать всю конфигурацию
sqz config get api_key                 # Получить значение
sqz config set api_key YOUR_NEW_KEY    # Установить значение
sqz config set default_mode auto       # Изменить режим по умолчанию
```

**Файл конфигурации:** `~/.sqz/config.toml`

```toml
[gateway]
host = "127.0.0.1"
port = 8082

[optimization]
default_mode = "auto"           # auto, cpp, llm, off
default_thinking = "auto"       # auto, low, medium, high, -
llm_compression_threshold = 2000

[api]
gemini_api_key = "YOUR_KEY"

[models]
default = "gemini-3.6-flash"
```

---

## 🔧 Режимы оптимизации

### Режимы сжатия (--mode)

| Режим | Описание | Экономия | Overhead |
|-------|----------|----------|----------|
| `auto` | Автоматический выбор оптимального метода (рекомендуется) | 30-60% | <1ms |
| `cpp` | Быстрая эвристическая компрессия (C++) | 5-36% | <1ms |
| `llm` | LLM-компрессия для длинных промптов (>2000 chars) | до 60% | ~2s |
| `off` | Без сжатия, только контроль мышления | 0-46% | 0ms |

### Уровни мышления (--thinking)

| Уровень | Использование | Экономия |
|---------|---------------|----------|
| `auto` | Автоматическая классификация сложности (рекомендуется) | 10-46% |
| `low` | Простые вопросы, определения, переводы | до 46% |
| `medium` | Сбалансированное рассуждение | 10-20% |
| `high` | Сложные задачи, доказательства, анализ | 0-10% |
| `-` | Не вмешиваться в уровень мышления | 0% |

---

## 💻 Python SDK

### Синхронное использование

```python
from sqz_cli.sdk import SqueezeClient, CompressionMode, ThinkingLevel

# Создать клиента
client = SqueezeClient(
    gateway_url="http://localhost:8082",
    mode=CompressionMode.AUTO,
    thinking=ThinkingLevel.AUTO
)

# Простой запрос
response = client.chat("What is Python?")
print(response.text)
print(f"Tokens saved: {response.metrics.net_saved}")

# Multi-turn разговор
history = []
r1 = client.chat("What is AI?", history=history)
history.append({"role": "user", "parts": [{"text": "What is AI?"}]})
history.append({"role": "model", "parts": [{"text": r1.text}]})

r2 = client.chat("How does it work?", history=history)
print(r2.text)

# Закрыть клиента
client.close()
```

### Асинхронное использование

```python
import asyncio
from sqz_cli.sdk import SqueezeClient

async def main():
    async with SqueezeClient() as client:
        # Параллельные запросы
        tasks = [
            client.chat_async("What is ML?"),
            client.chat_async("What is DL?"),
            client.chat_async("What is AI?")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        for r in responses:
            print(f"Response: {r.text[:50]}...")
            print(f"Saved: {r.metrics.net_saved} tokens")

asyncio.run(main())
```

### Context Manager

```python
with SqueezeClient() as client:
    response = client.chat("Hello!")
    print(response.text)
# Автоматически закрывается
```

### Быстрая функция

```python
from sqz_cli.sdk import chat

# Один вызов без создания клиента
answer = chat("Explain quantum physics")
print(answer)
```

---

## 🌐 HTTP API

### Совместимость с Gemini API

Шлюз полностью совместим с Gemini API. Просто измените base URL:

```python
# До
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

# После
url = "http://localhost:8082/v1beta/models/gemini-3.6-flash:generateContent?squeeze=auto"
```

### Query параметры

| Параметр | Значения | Описание |
|----------|----------|----------|
| `squeeze` | `auto`, `cpp`, `llm`, `0-2` | Режим сжатия |
| `thinking` | `auto`, `low`, `medium`, `high`, `-` | Контроль мышления |

### Response Headers

Шлюз добавляет заголовки с метриками:

- `x-squeeze-mode` — использованный режим сжатия
- `x-squeeze-input` — фактические входные токены
- `x-squeeze-baseline` — baseline (без оптимизации)
- `x-squeeze-saved` — сэкономлено токенов
- `x-squeeze-aux` — служебные токены шлюза
- `x-squeeze-thinking` — уровень мышления
- `x-squeeze-latency` — задержка (мс)

### Endpoints

```
GET  /health              # Проверка здоровья
GET  /stats               # Сводная статистика
GET  /metrics?limit=N     # Последние N запросов
GET  /api/summary         # Детальная статистика

POST /v1beta/models/{model}:generateContent
     Gemini API совместимый endpoint
```

---

## 📊 Метрики и мониторинг

### Real-time метрики в чате

При использовании `sqz chat` каждый ответ показывает:
- 🟢 Режим оптимизации (cpp/llm/pass)
- 💰 Сэкономленные токены (saved - aux = net)
- 🧠 Уровень мышления и потраченные токены
- ⏱️ Время обработки

### Статистика сессии

Команда `/stats` в чате показывает:
- Количество сообщений
- Всего сэкономлено токенов
- Общее время
- Среднее время на сообщение

### Логи

Все запросы логируются в `logs/metrics.jsonl` в формате:

```json
{
  "timestamp": "2026-11-04T15:42:31.123Z",
  "mode": "squeeze_cpp",
  "input_tokens": 127,
  "baseline_tokens": 182,
  "saved_tokens": 55,
  "aux_tokens": 0,
  "thinking_level": "low",
  "thinking_tokens": 342,
  "latency_ms": 4234,
  "status": 200
}
```

---

## 🔍 Примеры использования

Смотрите полные примеры в директории `examples/`:

- `sdk_usage.py` — использование Python SDK
- `api_usage.py` — прямое использование HTTP API
- `integration_*.py` — интеграция с популярными фреймворками

---

## 🐛 Troubleshooting

### Gateway не запускается

```bash
# Проверить порт
lsof -i :8082           # macOS/Linux
netstat -ano | findstr :8082  # Windows

# Запустить на другом порту
sqz start --port 8083
```

### API ключ не работает

```bash
sqz config get api_key   # Проверить текущий ключ
sqz config set api_key NEW_KEY
sqz status               # Проверить подключение
```

### Чат не подключается

```bash
sqz status               # Проверить что gateway запущен
sqz stop && sqz start    # Перезапустить gateway
```

### C++ модуль не собирается

```bash
# Проверить зависимости
pip install pybind11
cmake --version  # Должен быть >= 3.24

# Переустановить без C++ (будет использован Python fallback)
pip install squeeze-gateway --no-binary :all:
```

---

## 📚 Документация

- **[CLI_README.md](./CLI_README.md)** — полная документация CLI
- **[README.md](./README.md)** — техническое описание и бенчмарки
- **[examples/](./examples/)** — примеры интеграции

---

## 🎯 Что дальше?

1. **Попробуйте интерактивный чат:**
   ```bash
   sqz chat
   ```

2. **Интегрируйте в свое приложение:**
   ```python
   from sqz_cli.sdk import chat
   answer = chat("Your question here")
   ```

3. **Мониторьте экономию:**
   ```bash
   sqz stats
   ```

4. **Настройте под себя:**
   ```bash
   sqz config set default_mode cpp
   sqz config set default_thinking low
   ```

---

**Автор:** Kirill Skoch (@kirill_skoch)  
**License:** MIT  
**GitHub:** https://github.com/kirill-skoch/squeeze-gateway
