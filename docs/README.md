# Squeeze Gateway — GitHub Pages Deployment

🌐 **Live Demo:** `https://YOUR_USERNAME.github.io/squeeze-gateway/`

Современный веб-интерфейс для Squeeze Gateway с поддержкой светлой и тёмной тем, мультиязычностью и live-метриками. Работает как самостоятельно (demo mode), так и с подключением к реальному gateway.

## Функции

## 🎯 Режимы работы

### Demo Mode (GitHub Pages)
Автоматически активируется при доступе через GitHub Pages:
- ✅ Все страницы работают без backend
- ✅ Демонстрационные метрики и статистика
- ✅ Интерактивные элементы UI функциональны
- ✅ Четкие индикаторы демо-режима

### Full Mode (с Gateway)
При подключении к работающему gateway:
- 🔥 Live метрики в реальном времени
- 🔥 Интерактивный playground
- 🔥 Реальная статистика оптимизации
- 🔥 Профиль с вашими данными

### ✅ Реализованные страницы

- **Dashboard** (`index.html`) — Live-метрики, статистика запросов, terminal feed
- **Playground** (`playground.html`) — Интерактивная песочница для тестирования
- **Documentation** (`docs.html`) — Полная документация API и модулей
- **Profile** (`profile.html`) — Страница профиля пользователя с настройками
- **About** (`about.html`) — Информация о проекте и команде
- **Login** (`login.html`) — OAuth авторизация (опционально)
- **Project** (`project.html`) — Информация о проекте и настройках

### ✅ Работающие функции

- ✅ **Переключение тем** — Dark/Light mode с сохранением в localStorage
- ✅ **Мультиязычность** — EN/RU переключение
- ✅ **Demo Mode Detection** — Автоматическое определение GitHub Pages
- ✅ **Gateway Status** — Индикатор состояния подключения
- ✅ **Responsive Design** — Адаптивная верстка для всех устройств

### 🎨 Дизайн-система

**Шрифты:**
- Display: Syne (заголовки)
- Body: Space Grotesk (основной текст)
- Mono: JetBrains Mono (код и метрики)

**Цветовая схема:**
- Использует CSS-переменные для динамического переключения
- Material Design 3 inspired палитра
- Поддержка светлой и тёмной тем

## 🚀 Подключение к Gateway

### Вариант 1: Локальный Gateway

```bash
# Установить CLI
pip install squeeze-gateway

# Настроить и запустить
sqz install
sqz config set api_key YOUR_GEMINI_API_KEY
sqz start

# Открыть в браузере
open http://localhost:8082
```

### Вариант 2: Подключить GitHub Pages к Gateway

Если у вас gateway запущен локально или на сервере:

**Через localStorage (консоль браузера):**
```javascript
// Установить URL вашего gateway
localStorage.setItem('sqg_api', 'http://localhost:8082');
// или для удаленного сервера
localStorage.setItem('sqg_api', 'https://your-gateway.com');

// Перезагрузить страницу
location.reload();
```

**⚠️ Важно:** Убедитесь, что gateway разрешает CORS для GitHub Pages домена.

### Вариант 3: Развернуть полностью локально

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/squeeze-gateway.git
cd squeeze-gateway

# Запустить gateway (включает web UI)
sqz start

# Или использовать uvicorn напрямую
uvicorn server:app --port 8082
```

### 📂 Структура

```
web/
├── index.html          # Dashboard / Главная страница
├── playground.html     # Интерактивная песочница
├── docs.html          # Документация
├── about.html         # О проекте
├── profile.html       # Профиль пользователя
├── login.html         # Страница входа
├── project.html       # Страница проекта
└── assets/
    ├── app.js         # Основная логика приложения
    ├── i18n.js        # Система переводов
    ├── theme.css      # CSS-переменные для тем
    ├── style.css      # Дополнительные стили
    └── favicon.svg    # Иконка сайта
```

## 🔧 Настройка GitHub Pages

### Включить GitHub Pages

1. Перейдите в **Settings** вашего репозитория
2. Откройте секцию **Pages**
3. Установите:
   - **Source:** Deploy from a branch
   - **Branch:** main
   - **Folder:** /docs
4. Сохраните настройки
5. Подождите 1-2 минуты для деплоя
6. Откройте `https://YOUR_USERNAME.github.io/squeeze-gateway/`

### Файл .nojekyll

Файл `.nojekyll` уже включен в `docs/` и отключает Jekyll обработку. Это важно для корректной работы всех ассетов.

### Обновление GitHub Pages

Любые изменения в `docs/` автоматически деплоятся после push в `main`:

```bash
# Синхронизировать web → docs
cp -r web/* docs/

# Закоммитить и запушить
git add docs/
git commit -m "Update GitHub Pages"
git push origin main
```

### 🌐 Локализация

Смена языка через кнопку в header или программно:
```javascript
window.i18n.setLanguage('ru'); // или 'en'
```

### 🎨 Темы

Переключение через кнопку в header или программно:
```javascript
localStorage.setItem('sqg_theme', 'light'); // или 'dark'
location.reload();
```

Темы реализованы через CSS-переменные в `assets/theme.css` и автоматически применяются ко всем страницам.

### 📱 Адаптивность

Все страницы полностью адаптивны и работают на:
- Desktop (1920px+)
- Laptop (1280-1920px)
- Tablet (768-1280px)
- Mobile (320-768px)

### 🔒 Безопасность

- Все внешние ссылки открываются в новой вкладке
- XSS защита через экранирование пользовательского ввода
- CORS настроен для работы с gateway

### 📊 Live Metrics

Dashboard отображает метрики в реальном времени:
- Total Requests — общее количество запросов
- Avg Latency — средняя задержка
- Tokens Saved — процент сохранённых токенов
- Live Terminal Feed — поток событий gateway

### 🧪 Playground

Интерактивная песочница позволяет:
- Отправлять запросы через gateway
- Выбирать режим сжатия (passthrough, cpp, llm)
- Управлять уровнем thinking (low, medium, high)
- Видеть детальную телеметрию для каждого запроса

### 📖 Документация

Встроенная документация включает:
- Quick Start Guide
- API Reference
- Модули оптимизации
- FAQ
- Примеры кода на Python, JavaScript, cURL

---

## 🐛 Troubleshooting

### Проблема: Темы не переключаются
**Решение:**
1. Откройте консоль браузера (F12)
2. Очистите localStorage: `localStorage.clear()`
3. Hard refresh: Ctrl+Shift+R (⌘+Shift+R на Mac)
4. Проверьте что `theme.css` загружается

### Проблема: Язык не меняется
**Решение:**
1. Проверьте что `i18n.js` загружен
2. Откройте консоль и проверьте `window.i18n`
3. Попробуйте: `window.i18n.setLanguage('ru')`

### Проблема: Gateway не подключается
**Решение:**
1. Проверьте CORS headers на gateway
2. Убедитесь что gateway запущен и доступен
3. Проверьте URL в localStorage: `localStorage.getItem('sqg_api')`
4. Попробуйте открыть gateway URL напрямую в браузере

### Проблема: GitHub Pages показывает 404
**Решение:**
1. Проверьте что `.nojekyll` файл существует в `docs/`
2. Убедитесь что Settings → Pages настроены на `/docs`
3. Подождите 2-3 минуты после push
4. Проверьте что файлы существуют в `docs/` директории

### Проблема: Стили не применяются
**Решение:**
1. Проверьте что все CSS файлы загружаются (Network tab в DevTools)
2. Убедитесь что пути к ассетам относительные
3. Hard refresh страницы
4. Проверьте консоль на ошибки

---

## 📖 Дополнительная документация

- [Main README](../README.md) — Обзор проекта и технические детали
- [QUICKSTART](../QUICKSTART.md) — Быстрый старт для всех сценариев
- [CLI README](../CLI_README.md) — Документация CLI команд
- [CONTRIBUTING](../CONTRIBUTING.md) — Гайд для контрибьюторов

## 🤝 Contributing

Нашли баг или хотите улучшить веб-интерфейс?

1. **Issues:** [GitHub Issues](https://github.com/kirill-skoch/squeeze-gateway/issues)
2. **Pull Requests:** См. [Contributing Guide](../CONTRIBUTING.md)
3. **Telegram:** [@kirill_skoch](https://t.me/kirill_skoch)

## 📄 License

MIT License — см. [LICENSE](../LICENSE) файл

---

**Сделано с ❤️ by [@kirill_skoch](https://t.me/kirill_skoch)**  
**Версия:** 0.4.0  
**Последнее обновление:** 2026-11-05
