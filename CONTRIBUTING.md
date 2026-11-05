# Squeeze Gateway - Contributing Guide

Спасибо за интерес к проекту! Буду рад любому вкладу.

## 🚀 Быстрый старт для разработчиков

```bash
# 1. Fork и clone репозиторий
git clone https://github.com/YOUR_USERNAME/squeeze-gateway.git
cd squeeze-gateway

# 2. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Установить зависимости для разработки
pip install -e ".[dev]"

# 4. (Опционально) Собрать C++ модуль
cd core && mkdir build && cd build
cmake .. && make

# 5. Запустить тесты
pytest tests/
python test_cli.py
```

## 📝 Как внести вклад

### Reporting Bugs

Если вы нашли баг:

1. Проверьте, что баг еще не был зарепорчен в [Issues](https://github.com/kirill-skoch/squeeze-gateway/issues)
2. Создайте новый Issue с описанием:
   - Что ожидалось
   - Что произошло на самом деле
   - Шаги для воспроизведения
   - Версия Python, ОС
   - Логи (если есть)

### Suggesting Features

Есть идея для улучшения? Отлично!

1. Создайте Issue с тегом `enhancement`
2. Опишите:
   - Какую проблему это решит
   - Как вы видите реализацию
   - Примеры использования

### Pull Requests

1. **Fork** репозиторий
2. Создайте **feature branch**: `git checkout -b feature/amazing-feature`
3. **Сделайте изменения** и commit: `git commit -m 'Add amazing feature'`
4. **Push** в branch: `git push origin feature/amazing-feature`
5. Откройте **Pull Request**

#### Pull Request Guidelines

- Одна фича = один PR
- Добавьте тесты для новой функциональности
- Обновите документацию, если нужно
- Следуйте существующему стилю кода
- Опишите что и зачем в PR description

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest tests/ -v

# Тесты CLI
python test_cli.py

# Тесты с покрытием
pytest tests/ --cov=sqz_cli --cov-report=html
```

## 📐 Code Style

Проект использует:
- **Black** для форматирования Python кода
- **mypy** для проверки типов

```bash
# Форматирование
black sqz_cli/

# Проверка типов
mypy sqz_cli/
```

## 🏗️ Архитектура

### Структура проекта

```
squeeze-gateway/
├── sqz_cli/              # CLI модуль
│   ├── main.py           # Entry point, argument parsing
│   ├── commands.py       # Реализация команд
│   ├── chat.py           # Интерактивный чат
│   ├── utils.py          # Утилиты и helpers
│   └── sdk.py            # Python SDK для интеграции
├── core/                 # C++ модуль компрессии
│   ├── squeeze.cpp       # Эвристическое сжатие
│   └── CMakeLists.txt
├── server.py             # FastAPI сервер шлюза
├── web/                  # Web интерфейс
├── tests/                # Тесты
└── examples/             # Примеры использования
```

### Ключевые компоненты

1. **CLI (`sqz_cli/`)** - терминальный агент
2. **Gateway (`server.py`)** - FastAPI прокси
3. **Compression (`core/`)** - C++ модуль сжатия
4. **Web UI (`web/`)** - веб-интерфейс и dashboard

## 🔧 Полезные команды разработки

```bash
# Локальная установка в dev режиме
pip install -e .

# Запуск gateway в dev режиме
uvicorn server:app --reload --port 8082

# Запуск CLI из исходников
python -m sqz_cli.main --help

# Сборка пакета
python -m build

# Проверка пакета
twine check dist/*
```

## 📚 Области для вклада

### 🔥 High Priority

- [ ] OpenAI API compatibility layer
- [ ] Кэширование промптов (prefix cache)
- [ ] Поддержка других LLM провайдеров (Claude, GPT)
- [ ] Rate limiting и quota management

### 💡 Nice to Have

- [ ] Web UI улучшения (charts, better stats)
- [ ] Docker image
- [ ] Benchmark suite
- [ ] CI/CD pipeline
- [ ] Больше примеров интеграции

### 🧪 Testing & Quality

- [ ] Увеличить покрытие тестами
- [ ] E2E тесты
- [ ] Performance benchmarks
- [ ] Load testing

### 📖 Documentation

- [ ] API reference (auto-generated)
- [ ] Видео туториалы
- [ ] Blog posts / case studies
- [ ] Перевод документации

## ❓ Вопросы?

- Telegram: [@kirill_skoch](https://t.me/kirill_skoch)
- GitHub Issues: [создать вопрос](https://github.com/kirill-skoch/squeeze-gateway/issues/new)

## 📜 License

MIT License - можете свободно использовать и модифицировать код.

---

**Спасибо за вклад в Squeeze Gateway! 🙏**
