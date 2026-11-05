# Squeeze Gateway — Web Interface

Современный веб-интерфейс для Squeeze Gateway с поддержкой светлой и тёмной тем, мультиязычностью и live-метриками.

## Функции

### ✅ Реализовано

- **Переключение тем** — Светлая и тёмная темы с плавными переходами
- **Мультиязычность** — Поддержка английского и русского языков
- **Dashboard** — Live-метрики, статистика запросов, terminal feed
- **Playground** — Интерактивная песочница для тестирования gateway
- **Documentation** — Полная документация API и модулей
- **Profile** — Страница профиля пользователя с настройками
- **About** — Информация о проекте и команде
- **Login** — Страница входа (демо-режим)

### 🎨 Дизайн-система

**Шрифты:**
- Display: Syne (заголовки)
- Body: Space Grotesk (основной текст)
- Mono: JetBrains Mono (код и метрики)

**Цветовая схема:**
- Использует CSS-переменные для динамического переключения
- Material Design 3 inspired палитра
- Поддержка светлой и тёмной тем

### 🚀 Запуск

#### Вариант 1: Python HTTP Server (для разработки)
```bash
python -m http.server 8080 --directory web
```

#### Вариант 2: С бэкендом Gateway
```bash
# Запустить gateway на порту 8082
uvicorn server:app --port 8082

# Открыть web/index.html в браузере
# или запустить отдельный веб-сервер
```

#### Вариант 3: Live Server (VS Code)
Откройте `web/index.html` через Live Server расширение

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

### 🔧 API Integration

Web-интерфейс работает с Squeeze Gateway API:

**Endpoints:**
- `GET /health` — Проверка состояния gateway
- `GET /api/summary` — Сводная статистика
- `GET /metrics?limit=N` — Последние N запросов
- `POST /v1beta/models/{model}:generateContent` — Gemini-совместимый API

**Настройка gateway URL:**
По умолчанию использует `http://localhost:8082`. Для GitHub Pages можно настроить через:
```javascript
localStorage.setItem('sqg_api', 'https://your-gateway-url.com');
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

## Разработка

### Добавление новой страницы

1. Создайте `new-page.html` по шаблону существующих
2. Добавьте подключение `assets/theme.css`
3. Укажите `data-page="new-page"` в `<body>`
4. Добавьте переводы в `assets/i18n.js`
5. При необходимости добавьте логику в `assets/app.js`

### Добавление нового перевода

Отредактируйте `assets/i18n.js`:
```javascript
const translations = {
  en: {
    your_key: "English text",
  },
  ru: {
    your_key: "Русский текст",
  }
};
```

Используйте в HTML:
```html
<span data-i18n="your_key">Fallback text</span>
```

### Изменение цветовой схемы

Отредактируйте CSS-переменные в `assets/theme.css`:
```css
:root { /* dark theme */ }
.light { /* light theme */ }
```

---

**Автор:** @kirill_skoch  
**Лицензия:** MIT  
**Версия:** 0.3
