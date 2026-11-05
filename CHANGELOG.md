# Squeeze Gateway - Change Log

## [0.3.0] - 2026-11-04

### 🚀 Major Features

#### CLI & Terminal Agent
- **Interactive Terminal Agent** - полноценный CLI по типу Claude Code
- **Command `sqz`** - установка, настройка, управление шлюзом
- **Interactive Chat Mode** - терминальный чат с real-time метриками оптимизации
- **Session Statistics** - отслеживание экономии токенов в реальном времени
- **Configuration Management** - простое управление настройками через CLI

#### Python SDK
- **SqueezeClient** - удобный Python клиент для интеграции
- **Async Support** - асинхронные операции для высокой производительности
- **Type Hints** - полная типизация для лучшего DX
- **Context Managers** - поддержка `with` и `async with`

#### Web Interface
- **GitHub Pages Deployment** - демо-режим для онлайн-просмотра
- **Theme System** - переключение light/dark темы
- **Profile Page** - статистика пользователя и настройки
- **i18n Support** - поддержка русского и английского языков

### ✨ Improvements

- Добавлена автоматическая установка зависимостей (`install.sh`, `install.bat`)
- Улучшена обработка ошибок и информативность сообщений
- Добавлена документация по установке и использованию
- Создан `pyproject.toml` для современной установки через pip
- Добавлены примеры использования в `examples/`

### 📦 Package Structure

```
squeeze-gateway/
├── sqz_cli/              # CLI модуль
│   ├── main.py           # Entry point
│   ├── commands.py       # CLI команды
│   ├── chat.py           # Интерактивный чат
│   ├── utils.py          # Утилиты
│   └── sdk.py            # Python SDK
├── web/                  # Web интерфейс
├── docs/                 # Документация
├── examples/             # Примеры использования
└── pyproject.toml        # Конфигурация пакета
```

### 🛠️ CLI Commands

```bash
sqz install              # Установка и конфигурация
sqz start               # Запуск шлюза
sqz stop                # Остановка
sqz status              # Статус и метрики
sqz chat                # Интерактивный чат
sqz stats               # Статистика оптимизации
sqz config set/get/list # Управление конфигурацией
```

### 📚 Documentation

- **QUICKSTART.md** - быстрый старт и примеры
- **CLI_README.md** - полная документация CLI
- **README.md** - технические детали и бенчмарки

### 🐛 Bug Fixes

- Исправлено переключение темы на GitHub Pages
- Исправлена загрузка профиля в демо-режиме
- Исправлены проблемы с кодировкой в Windows
- Улучшена совместимость с разными версиями Python

---

## [0.2.0] - 2026-10-XX

### Features
- C++ heuristic compression module
- Thinking level controller
- LLM-based compression with cost threshold
- Metrics logging (JSONL format)
- Web dashboard

---

## [0.1.0] - 2026-09-XX

### Initial Release
- Basic gateway proxy
- Token counting
- Simple compression
