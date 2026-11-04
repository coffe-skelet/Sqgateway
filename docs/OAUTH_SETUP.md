# OAuth Authentication Setup Guide

Squeeze Gateway поддерживает OAuth авторизацию через Google и GitHub.

## 🔐 Настройка Google OAuth

### 1. Создание OAuth Client ID

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Создайте новый проект или выберите существующий
3. Перейдите в раздел **APIs & Services → Credentials**
4. Нажмите **Create Credentials → OAuth client ID**
5. Выберите тип приложения: **Web application**
6. Укажите имя (например, "Squeeze Gateway")
7. Добавьте **Authorized redirect URIs**:
   - Для локальной разработки: `http://localhost:8082/auth/google/callback`
   - Для production: `https://your-domain.com/auth/google/callback`
8. Нажмите **Create**
9. Скопируйте **Client ID** и **Client Secret**

### 2. Настройка экрана согласия (OAuth Consent Screen)

1. Перейдите в **OAuth consent screen**
2. Выберите **External** (если не используете Google Workspace)
3. Заполните обязательные поля:
   - App name: `Squeeze Gateway`
   - User support email: ваш email
   - Developer contact information: ваш email
4. Сохраните и продолжите
5. Добавьте scopes: `openid`, `email`, `profile`
6. Сохраните изменения

### 3. Добавление credentials в .env

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
BASE_URL=http://localhost:8082
```

## 🐙 Настройка GitHub OAuth

### 1. Создание OAuth App

1. Перейдите в [GitHub Settings → Developer settings](https://github.com/settings/developers)
2. Нажмите **New OAuth App**
3. Заполните форму:
   - **Application name**: `Squeeze Gateway`
   - **Homepage URL**: `http://localhost:8082` (или ваш домен)
   - **Authorization callback URL**: `http://localhost:8082/auth/github/callback`
4. Нажмите **Register application**
5. Скопируйте **Client ID**
6. Нажмите **Generate a new client secret**
7. Скопируйте **Client Secret** (показывается только один раз!)

### 2. Добавление credentials в .env

```bash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
BASE_URL=http://localhost:8082
```

## 🔑 Генерация Session Secret

Для безопасности сессий нужен случайный секретный ключ:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Добавьте результат в `.env`:

```bash
SESSION_SECRET=your_generated_secret_here
```

## 📝 Полный .env файл

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# OAuth Settings
BASE_URL=http://localhost:8082
SESSION_SECRET=your_generated_secret
```

## 🚀 Запуск

После настройки `.env` файла, запустите сервер:

```bash
uvicorn server:app --port 8082 --reload
```

Проверьте статус OAuth:
```bash
curl http://localhost:8082/auth/status
```

Ответ:
```json
{
  "authenticated": false,
  "user": null,
  "google_enabled": true,
  "github_enabled": true
}
```

## 🌐 Production Deploy

### Обновите BASE_URL

В `.env` для production:
```bash
BASE_URL=https://your-domain.com
```

### Обновите redirect URIs

В настройках Google и GitHub замените:
- `http://localhost:8082/auth/google/callback` → `https://your-domain.com/auth/google/callback`
- `http://localhost:8082/auth/github/callback` → `https://your-domain.com/auth/github/callback`

### Включите HTTPS

В `auth.py` измените:
```python
response.set_cookie(
    key='sqg_session',
    value=session_token,
    httponly=True,
    secure=True,  # ← включите для HTTPS
    samesite='lax',
    max_age=7 * 24 * 60 * 60,
)
```

## 🔍 Отладка

### Проверка OAuth endpoints

```bash
# Статус аутентификации
curl http://localhost:8082/auth/status

# Текущий пользователь
curl -b cookies.txt http://localhost:8082/auth/me

# Logout
curl -b cookies.txt http://localhost:8082/auth/logout
```

### Логи сервера

При проблемах с OAuth проверьте логи uvicorn:
```
INFO:     Google OAuth error: <error details>
INFO:     GitHub OAuth error: <error details>
```

### Проверка redirect URIs

Убедитесь, что redirect URIs в Google/GitHub **точно совпадают** с `BASE_URL/auth/{provider}/callback`

## ✅ Тестирование

1. Откройте http://localhost:8082/login.html
2. Нажмите "Google" или "GitHub"
3. Авторизуйтесь в выбранном сервисе
4. Вы будете перенаправлены на `/profile.html`
5. Проверьте данные профиля

## 📚 API Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /auth/google` | Начало OAuth flow с Google |
| `GET /auth/google/callback` | Callback после авторизации Google |
| `GET /auth/github` | Начало OAuth flow с GitHub |
| `GET /auth/github/callback` | Callback после авторизации GitHub |
| `GET /auth/logout` | Выход из системы |
| `GET /auth/me` | Получить данные текущего пользователя |
| `GET /auth/status` | Проверить статус OAuth конфигурации |

## 🔒 Безопасность

- ✅ HttpOnly cookies предотвращают XSS атаки
- ✅ SameSite=lax защищает от CSRF
- ✅ Session tokens криптографически случайны
- ✅ Сессии имеют срок действия (7 дней по умолчанию)
- ⚠️ В production используйте HTTPS и `secure=True` для cookies

## 🎯 Demo Mode

Если OAuth не настроен, доступен demo режим:
- Любой email/пароль работает для тестирования
- Данные хранятся только в localStorage браузера
- При перезагрузке страницы сессия сохраняется

---

**Автор:** @kirill_skoch  
**Документация:** https://github.com/kirill-skoch/squeeze-gateway
