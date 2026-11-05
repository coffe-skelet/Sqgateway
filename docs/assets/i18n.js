/* Multi-language support for Squeeze Gateway */

const translations = {
  en: {
    // Navigation
    nav_dashboard: "Dashboard",
    nav_playground: "Playground",
    nav_docs: "Docs",
    nav_about: "About",
    nav_project: "Project",
    nav_profile: "Profile",
    nav_login: "Login",
    nav_logout: "Logout",

    // Theme
    theme_light: "Light",
    theme_dark: "Dark",

    // Dashboard
    dash_title: "SQUEEZE GATEWAY",
    dash_subtitle: "// LLM Token Optimizer & Intelligent Gateway",
    dash_description: "Transparent proxy between your application and LLM providers that reduces token consumption by 30–60% without quality loss. Intelligent compression, thinking controller, and semantic optimization.",
    dash_try_playground: "Try Playground",
    dash_documentation: "Documentation",
    dash_total_requests: "// Total Requests",
    dash_avg_latency: "// Avg Latency",
    dash_tokens_saved: "// Tokens Saved",
    dash_live_feed: "Live Metrics Feed",
    dash_gateway_status: "// Gateway Status",
    dash_checking: "Checking connection...",

    // Playground
    play_title: "Playground",
    play_subtitle: "Real gateway with compression, thinking control, and honest telemetry.",
    play_clear_chat: "Clear Chat",
    play_compression: "Compression",
    play_thinking: "Thinking Level",
    play_model: "Model",
    play_send: "Send",
    play_placeholder: "Ask something...",

    // Login
    login_title: "Login",
    login_subtitle: "Access your Squeeze Gateway dashboard",
    login_email: "Email / Username",
    login_password: "Password",
    login_remember: "Remember me",
    login_forgot: "Forgot password?",
    login_signin: "Login",
    login_signup: "Sign up",
    login_no_account: "Don't have an account?",
    login_or_continue: "Or continue with",
    login_demo: "Demo Mode: Any credentials will work for testing",

    // Profile
    profile_title: "User Profile",
    profile_member_since: "Member since 2026",
    profile_active: "Active",
    profile_stats: "Your Statistics",
    profile_api_config: "API Configuration",
    profile_preferences: "Preferences",
    profile_danger_zone: "Danger Zone",
    profile_save_changes: "Save Changes",
    profile_test_connection: "Test Connection",

    // About
    about_title: "Making AI More Efficient",
    about_subtitle: "Squeeze Gateway is an open-source project focused on reducing LLM token consumption without sacrificing quality.",
    about_mission: "Our Mission",
    about_story: "The Story",
    about_team: "The Team",
    about_values: "Core Values",
    about_contact: "Get In Touch",

    // Footer
    footer_copyright: "Squeeze Gateway © 2026 • MIT License",
    footer_home: "Home",
  },

  ru: {
    // Навигация
    nav_dashboard: "Панель",
    nav_playground: "Песочница",
    nav_docs: "Документация",
    nav_about: "О нас",
    nav_project: "Проект",
    nav_profile: "Профиль",
    nav_login: "Вход",
    nav_logout: "Выход",

    // Тема
    theme_light: "Светлая",
    theme_dark: "Тёмная",

    // Панель управления
    dash_title: "SQUEEZE GATEWAY",
    dash_subtitle: "// Оптимизатор токенов LLM и интеллектуальный шлюз",
    dash_description: "Прозрачный прокси между вашим приложением и провайдерами LLM, который снижает потребление токенов на 30-60% без потери качества. Интеллектуальное сжатие, контроллер мышления и семантическая оптимизация.",
    dash_try_playground: "Попробовать песочницу",
    dash_documentation: "Документация",
    dash_total_requests: "// Всего запросов",
    dash_avg_latency: "// Средняя задержка",
    dash_tokens_saved: "// Сохранено токенов",
    dash_live_feed: "Живая лента метрик",
    dash_gateway_status: "// Статус шлюза",
    dash_checking: "Проверка соединения...",

    // Песочница
    play_title: "Песочница",
    play_subtitle: "Реальный шлюз со сжатием, контролем мышления и честной телеметрией.",
    play_clear_chat: "Очистить чат",
    play_compression: "Сжатие",
    play_thinking: "Уровень мышления",
    play_model: "Модель",
    play_send: "Отправить",
    play_placeholder: "Задайте вопрос...",

    // Вход
    login_title: "Вход",
    login_subtitle: "Доступ к панели управления Squeeze Gateway",
    login_email: "Email / Имя пользователя",
    login_password: "Пароль",
    login_remember: "Запомнить меня",
    login_forgot: "Забыли пароль?",
    login_signin: "Войти",
    login_signup: "Регистрация",
    login_no_account: "Нет аккаунта?",
    login_or_continue: "Или продолжить с",
    login_demo: "Демо режим: Любые учётные данные работают для тестирования",

    // Профиль
    profile_title: "Профиль пользователя",
    profile_member_since: "Участник с 2026",
    profile_active: "Активен",
    profile_stats: "Ваша статистика",
    profile_api_config: "Настройки API",
    profile_preferences: "Предпочтения",
    profile_danger_zone: "Опасная зона",
    profile_save_changes: "Сохранить изменения",
    profile_test_connection: "Проверить соединение",

    // О нас
    about_title: "Делаем ИИ более эффективным",
    about_subtitle: "Squeeze Gateway — это проект с открытым исходным кодом, направленный на снижение потребления токенов LLM без потери качества.",
    about_mission: "Наша миссия",
    about_story: "История",
    about_team: "Команда",
    about_values: "Основные ценности",
    about_contact: "Связаться с нами",

    // Подвал
    footer_copyright: "Squeeze Gateway © 2026 • Лицензия MIT",
    footer_home: "Главная",
  }
};

class I18n {
  constructor() {
    this.currentLang = localStorage.getItem('sqg_lang') || 'en';
    this.translations = translations;
  }

  t(key) {
    return this.translations[this.currentLang][key] || this.translations['en'][key] || key;
  }

  setLanguage(lang) {
    if (this.translations[lang]) {
      this.currentLang = lang;
      localStorage.setItem('sqg_lang', lang);
      this.updatePage();
    }
  }

  updatePage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = this.t(key);

      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translation;
      } else {
        el.textContent = translation;
      }
    });
  }

  getCurrentLanguage() {
    return this.currentLang;
  }
}

// Global instance
window.i18n = new I18n();
