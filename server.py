"""
Squeeze Gateway — прокси к Gemini API с оптимизацией расхода токенов.

Что делает шлюз:
  1) принимает запрос в формате Gemini API (полная совместимость:
     можно подключить любой клиент, заменив host),
  2) считает baseline через countTokens (сколько стоил бы исходный промпт),
  3) по ?squeeze= сжимает вход C++-эвристикой или мини-моделью,
  4) по ?thinking= управляет глубиной рассуждений (LOW/MEDIUM/HIGH),
  5) пересылает запрос в Gemini и возвращает ответ без изменений,
  6) пишет в logs/metrics.jsonl только цифры: токены, режим, латентность.

Запуск:  uvicorn server:app --port 8082
Проверка клиентом:  python client.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# C++ ядро (Этап 3)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "build"))
import squeeze_core as core  # noqa: E402

load_dotenv()

VERSION = "0.3.0"
ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"

API_KEY = os.environ.get("GEMINI_API_KEY", "")
UPSTREAM = os.environ.get("GEMINI_UPSTREAM", "https://generativelanguage.googleapis.com/v1beta")

METRICS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "metrics.jsonl")

COMPRESSOR_MODEL = os.environ.get("COMPRESSOR_MODEL", "gemini-3.1-flash-lite")

SQUEEZE_PROMPT = (
    "Сократи следующий промпт для языковой модели. Правила жёсткие:\n"
    "1) Сохрани ВСЕ факты, числа, имена, названия, требования и ограничения.\n"
    "2) Сохрани исходный язык и тон задачи (technical task — технический).\n"
    "3) Убери вежливость, повторы, отступления и вводные фразы.\n"
    "4) Не отвечай на промпт! Верни ТОЛЬКО сжатый текст промпта без пояснений.\n\n"
    "ПРОМПТ:\n"
)

# LLM-сжатие стоит ~300+ aux-токенов (вызов компрессора). На коротких промптах
# оно убыточно, поэтому включаем его только для длинных текстов.
LLM_SQUEEZE_MIN_CHARS = 2000

app = FastAPI(
    title="Squeeze Gateway",
    version=VERSION,
    docs_url="/api/docs",      # встроенный Swagger не должен занимать /docs
    redoc_url=None,
    openapi_url="/openapi.json",
)
# CORS: статическая витрина может жить на GitHub Pages и обращаться к шлюзу.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # браузер на GitHub Pages должен видеть телеметрию шлюза
)
# один httpx-клиент на все запросы — так быстрее (переиспользуются соединения)
http = httpx.AsyncClient(timeout=120)

# Ретраи при перегрузке модели (503): Gemini сам советует "try later".
# Ступенчатая задержка, чтобы не долбить сервер зря.
RETRYABLE_STATUSES = {503}
RETRIES = 3

# 429 (квота исчерпана) ретраить "один раз с большой паузой": если лимит
# дневной — не имеет смысла долбить, это ломает счётчик попыток на клиенте.
QUOTA_STATUSES = {429}


# ---------- Этап 4.5: контроллер глубины мышления -----------------------------
# Маркеры "тяжёлых" задач: доказательства выкладки, анализ нескольких
# альтернатив, код. На таких понижать уровень нельзя (теряется качество).
HEAVY_MARKERS = [
    "объясни", "объясните", "распишите", "подробно", "детально", "глубоко",
    "проанализируй", "докажи", "докажите", "доказательство", "выведи формулу",
    "уравнение", "сравни стратегии", "оптимизируй", "рефактор", "задача:",
    "вычисли", "реши", "почему", "откуда", "напиши код", "составь план",
    "анализ", "следствия", "выводы", "в чем разница", "какова причина",
    "analyze", "prove", "derive", "optimize", "why", "debug", "implement",
    "refactor", "solve", "algorithm", "explain",
]
# Маркеры "лёгких" задач: определения, переводы, форматирование, краткость.
LIGHT_MARKERS = [
    "что такое", "кто такой", "переведи", "перевод", "кратко", "в нескольких",
    "в двух", "в трёх", "одним предложением", "одним предложении", "определение",
    "перечисли", "назови", "синоним", "аноним", "формат", "переформулируй",
    "what is", "who is", "define", "define:", "translate", "summarize",
    "list", "briefly", "in short", "one sentence",
]


def classify_thinking(body: dict) -> str:
    """Выбирает thinkingLevel по характеру запроса.

    Правило должно быть консервативным: сомневаешься — не понижай.
    Возвращает 'LOW' или 'MEDIUM' (HIGH не назначаем: модель сама способна
    поднять, а наш принцип 'не навредить' важнее последней капли экономии).
    """
    texts = []
    total_chars = 0
    for turn in body.get("contents", []):
        for part in turn.get("parts", []):
            if isinstance(part.get("text"), str):
                texts.append(part["text"])
                total_chars += len(part["text"])

    joined = " \n".join(texts).lower()
    heavy = sum(1 for m in HEAVY_MARKERS if m in joined)
    light = sum(1 for m in LIGHT_MARKERS if m in joined)
    last_turn = texts[-1].lower() if texts else ""

    # Явные просьбы о краткости в последнем сообщении — самый надёжный сигнал.
    if any(m in last_turn for m in LIGHT_MARKERS[:8]) and heavy == 0:
        return "LOW"
    # Любая тяжёлая задача — не понижаем глубину.
    if heavy > 0:
        return "MEDIUM"
    # Короткий безобидный вопрос без маркеров сложности.
    if total_chars < 400 and light > 0:
        return "LOW"
    return "MEDIUM"


def apply_thinking(body: dict, level: str) -> dict:
    """Прописывает generationConfig.thinkingConfig.thinkingLevel в тело запроса.

    Если клиент сам указал thinkingLevel — уважаем его (шлюз не лезет
    поверх явного выбора вызывающего).
    """
    gc = body.setdefault("generationConfig", {})
    existing = gc.get("thinkingConfig", {}).get("thinkingLevel")
    if existing:
        return body, str(existing)
    gc["thinkingConfig"] = {**gc.get("thinkingConfig", {}), "thinkingLevel": level}
    return body, level


def log_metrics(record: dict) -> None:
    """Дописываем одну строку JSON с метриками запроса в metrics.jsonl."""
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    with open(METRICS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_usage(payload: dict) -> dict:
    """Достаём из ответа Gemini потраченные токены (если модель их вернула)."""
    usage = payload.get("usageMetadata", {})
    return {
        "input_tokens": usage.get("promptTokenCount", 0),
        "thought_tokens": usage.get("thoughtsTokenCount", 0),
        "output_tokens": usage.get("candidatesTokenCount", 0),
        "total_tokens": usage.get("totalTokenCount", 0),
    }


def count_tokens_body(body: dict) -> dict:
    """Оставляет только те поля, которые countTokens действительно принимает.

    generationConfig (maxOutputTokens, thinkingConfig и т.п.) не влияет на
    количество входных токенов, но endpoint его отвергает с 400. Из-за этого
    baseline молча превращался в 0 и вся экономия обнулялась.
    """
    allowed = ("contents", "systemInstruction", "tools", "toolConfig", "cachedContent")
    return {k: body[k] for k in allowed if k in body}


async def count_tokens_upstream(model: str, body: dict) -> int:
    """Сколько токенов потратил бы запрос в исходном (несжатом) виде.

    Спрашиваем у самого Gemini через /countTokens — это наш 'базовый сценарий':
    то, что было бы потрачено без оптимизаций шлюза. Когда появится сжатие,
    фактический расход станет меньше, а baseline останется честным.
    """
    try:
        url = f"{UPSTREAM}/models/{model}:countTokens?key={API_KEY}"
        payload = count_tokens_body(body)
        for attempt in range(2):
            resp = await http.post(url, json=payload)
            if resp.status_code == 200:
                return int(resp.json().get("totalTokens", 0))
            # 429 — дневная квота: повторять бессмысленно и вредно
            if resp.status_code == 429:
                break
            if attempt == 0:
                await asyncio.sleep(0.4)
    except Exception as exc:
        print(f"countTokens failed: {exc}", file=sys.stderr)
    return 0


async def llm_squeeze(text: str) -> (str, int):
    """Сжатие промпта мини-моделью (Этап 4). Дорогое, но качественное.
    Возвращает (сжатый текст, сколько токенов сам сжиматель потратил)."""
    resp = await http.post(
        f"{UPSTREAM}/models/{COMPRESSOR_MODEL}:generateContent?key={API_KEY}",
        json={
            "contents": [{"role": "user", "parts": [{"text": SQUEEZE_PROMPT + text}]}],
            "generationConfig": {"thinkingConfig": {"thinkingLevel": "LOW"},
                                 "maxOutputTokens": 4096},
        },
    )
    if resp.status_code != 200:
        return text, 0  # не смогли сжать — шлём как есть, качество не рискуем
    try:
        payload = resp.json()
        squeezed = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        u = payload.get("usageMetadata", {})
        cost = u.get("totalTokenCount", 0)  # служебная цена нашего сжатия
        # страховка: пустой/сломанный сжиматель → откат на эвристику
        if not squeezed or len(squeezed) >= len(text):
            return core.compress(text), cost
        return squeezed, cost
    except (KeyError, IndexError, ValueError):
        return core.compress(text), 0


async def compress_body(body: dict, mode: str) -> (dict, bool, int):
    """Сжимает текстовые части запроса.

    mode='cpp' — эвристика на C++ (мгновенно, бесплатно, консервативно)
    mode='llm' — мини-модель (качественнее; только свежий user-turn, историю не трогаем)
    Возвращает (сжатое тело, менялось ли что-то, служебный расход aux_tokens).
    """
    copy = json.loads(json.dumps(body))  # глубокая копия без внешних зависимостей
    changed = False
    aux = 0  # сколько токенов потратил сам шлюз на оптимизацию
    for turn in copy.get("contents", []):
        for part in turn.get("parts", []):
            if isinstance(part.get("text"), str):
                if mode == "cpp":
                    squeezed = core.compress(part["text"])
                elif turn.get("role") == "user" and len(part["text"]) >= LLM_SQUEEZE_MIN_CHARS:
                    # LLM-сжатие окупается только на длинных промптах
                    squeezed, cost = await llm_squeeze(part["text"])
                    aux += cost
                else:
                    # короткий промпт или модель-история: эвристика или без изменений
                    squeezed = core.compress(part["text"]) if mode in ("cpp", "llm") else part["text"]
                if squeezed:  # не даём сжать запрос в пустоту
                    changed |= squeezed != part["text"]
                    part["text"] = squeezed
    return copy, changed, aux


@app.post("/v1beta/models/{model}:generateContent")
async def generate_content(model: str, request: Request):
    """Прокси с оптимизацией: ?squeeze=1 включает сжатие C++ ядром."""
    body = await request.json()
    started = time.perf_counter()

    # baseline: сколько токенов потратил бы оригинальный запрос без шлюза
    baseline_tokens = await count_tokens_upstream(model, body)

    # режим сжатия: 0 — выкл (honest baseline), 1 — C++ эвристика, 2 — LLM-сжатие
    squeeze_param = request.query_params.get("squeeze", "0")
    squeeze_on = squeeze_param in ("1", "2")
    squeeze_mode = "llm" if squeeze_param == "2" else "cpp"
    sent_body = body
    aux_tokens = 0
    if squeeze_on:
        squeezed, changed, aux_tokens = compress_result = await compress_body(body, squeeze_mode)
        if changed:
            sent_body = squeezed
        else:
            sent_body = squeezed  # unchanged copy, но aux всё равно посчитан

    # Этап 4.5: ?thinking=auto|low|medium|high управляет глубиной мышления.
    # По умолчанию не вмешиваемся (honest baseline для бенчмарка).
    thinking_param = request.query_params.get("thinking")
    chosen_level = None
    if thinking_param:
        sent_body = json.loads(json.dumps(sent_body))  # не мутируем чужое тело
        if thinking_param == "auto":
            level = classify_thinking(sent_body)
        else:
            level = thinking_param.upper()
        if level in ("LOW", "MEDIUM", "HIGH"):
            sent_body, chosen_level = apply_thinking(sent_body, level)

    upstream_url = f"{UPSTREAM}/models/{model}:generateContent?key={API_KEY}"
    for attempt in range(RETRIES):
        resp = await http.post(upstream_url, json=sent_body)
        if resp.status_code in QUOTA_STATUSES:
            # квота исчерпана на сегодня — сразу отдаём клиенту понятную ошибку
            break
        if resp.status_code not in RETRYABLE_STATUSES:
            break
        # перегрузка: ждём 1с, 2с, 4с и пробуем снова
        time.sleep(2 ** attempt)
    elapsed_ms = round((time.perf_counter() - started) * 1000)

    try:
        payload = resp.json()
    except Exception:
        payload = {}

    usage = extract_usage(payload)
    mode = ("squeeze_llm" if squeeze_mode == "llm" else "squeeze_cpp") if squeeze_on else "passthrough"
    log_metrics({
        "mode": mode,
        "model": model,
        "status": resp.status_code,
        "attempts": attempt + 1,          # >1 значит модель была перегружена
        "latency_ms": elapsed_ms,
        "baseline_tokens": baseline_tokens,   # было бы входных токенов без шлюза
        "aux_tokens": aux_tokens,             # служебный расход самого шлюза (сжиматель)
        "net_bypass_tokens": max(0, baseline_tokens - usage["input_tokens"]) - aux_tokens,  # сжатие входа за вычетом цены
        "thinking": thinking_param or "",     # режим управления глубиной
        "thinking_level_applied": chosen_level or "client",  # что в итоге ушло в модель
        **usage,
    })

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
        headers={
            # телеметрия для интерфейса: те же цифры, что попали в журнал
            "X-Squeeze-Mode": mode,
            "X-Squeeze-Baseline": str(baseline_tokens),
            "X-Squeeze-Input": str(usage["input_tokens"]),
            "X-Squeeze-Aux": str(aux_tokens),
            "X-Squeeze-Saved": str(max(0, baseline_tokens - usage["input_tokens"] - aux_tokens)),
            "X-Squeeze-Thinking": chosen_level or "client",
            "X-Squeeze-Elapsed-Ms": str(elapsed_ms),
        },
    )


@app.get("/health")
async def health():
    """Живая проверка: шлюз работает и ключ настроен."""
    return {"status": "ok", "key_configured": bool(API_KEY)}


@app.get("/stats")
async def stats():
    """Суммарная статистика по всем запросам из журнала метрик."""
    if not os.path.exists(METRICS_FILE):
        return {"requests": 0}
    total = {"requests": 0, "baseline_tokens": 0, "input": 0, "aux": 0, "thought": 0, "output": 0, "latency_ms": 0}
    with open(METRICS_FILE, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("status") != 200:
                continue  # ошибки не считаем в экономии
            total["requests"] += 1
            total["baseline_tokens"] += r.get("baseline_tokens", 0)
            total["input"] += r.get("input_tokens", 0)
            total["aux"] += r.get("aux_tokens", 0)
            total["thought"] += r.get("thought_tokens", 0)
            total["output"] += r.get("output_tokens", 0)
            total["latency_ms"] += r.get("latency_ms", 0)
    if total["requests"]:
        total["avg_latency_ms"] = round(total.pop("latency_ms") / total["requests"])
        baseline = total.pop("baseline_tokens")
        # нетто-экономия: базовый сценарий минус фактический ввод минус служебный расход
        total["net_tokens_saved"] = max(0, baseline - total["input"] - total["aux"])
        total["savings_pct"] = (
            round(100 * total["net_tokens_saved"] / baseline, 1) if baseline else 0
        )
    return total


@app.get("/metrics")
async def metrics(limit: int = 12):
    """Последние записи журнала в виде, удобном интерфейсу."""
    if not os.path.exists(METRICS_FILE):
        return []
    rows = []
    with open(METRICS_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            mode = r.get("mode", "passthrough")
            rows.append({
                "mode": mode,
                "mode_label": {"passthrough": "passthrough",
                               "squeeze_cpp": "cpp",
                               "squeeze_llm": "llm"}.get(mode, mode),
                "mode_class": {"passthrough": "pass", "squeeze_cpp": "cpp",
                               "squeeze_llm": "llm"}.get(mode, "pass"),
                "model": r.get("model", ""),
                "status": r.get("status", 0),
                "input": r.get("input_tokens", 0),
                "baseline": r.get("baseline_tokens", 0),
                "aux": r.get("aux_tokens", 0),
                "saved": max(0, r.get("baseline_tokens", 0)
                             - r.get("input_tokens", 0)
                             - r.get("aux_tokens", 0)),
                "thought": r.get("thought_tokens", 0),
                "output": r.get("output_tokens", 0),
                "thinking_level": r.get("thinking_level_applied", ""),
                "latency_ms": r.get("latency_ms", 0),
            })
    return rows[-limit:][::-1]  # свежие сверху


@app.get("/api/summary")
async def api_summary():
    """Единая сводка для дашборда: статус, метрики, разбивка по режимам."""
    s = await stats()
    per_mode: dict[str, int] = {}
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("status") == 200:
                    per_mode[r.get("mode", "passthrough")] = per_mode.get(r.get("mode", "passthrough"), 0) + 1
    return {
        "version": VERSION,
        "key_configured": bool(API_KEY),
        "upstream": UPSTREAM,
        "default_model": "gemini-3.6-flash",
        "stats": s,
        "requests_per_mode": per_mode,
    }


# ---------- статический сайт (Этап 7) ----------------------------------------
if WEB.exists():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(WEB / "index.html")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        # современные браузеры понимают SVG и по старому адресу
        return FileResponse(WEB / "assets" / "favicon.svg", media_type="image/svg+xml")

    for _page in ("playground", "docs", "project", "about", "login", "profile"):
        def _make(page: str):
            async def _handler():
                return FileResponse(WEB / f"{page}.html")
            return _handler
        app.get(f"/{_page}", include_in_schema=False)(_make(_page))

    # Плоские .html-адреса нужны статической копии на GitHub Pages:
    # относительные ссылки работают и локально, и в подкаталоге репозитория.
    for _page in ("index", "playground", "docs", "project", "about", "login", "profile"):
        def _make_html(page: str):
            async def _handler():
                return FileResponse(WEB / f"{page}.html")
            return _handler
        app.get(f"/{_page}.html", include_in_schema=False)(_make_html(_page))
