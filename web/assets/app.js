/* Squeeze Gateway — Client Application
   Works locally (same-origin) and on GitHub Pages (custom gateway URL in localStorage) */

(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fmt = new Intl.NumberFormat("en-US");
  const n = (v) => fmt.format(Number(v || 0));

  const DEFAULT_API = "http://localhost:8082";

  function apiBase() {
    const saved = localStorage.getItem("sqg_api");
    if (saved) return saved.replace(/\/$/, "");
    if (location.protocol.startsWith("http") && /^(localhost|127\.0\.0\.1)/.test(location.hostname)) {
      return ""; // local: gateway and site on same origin
    }
    return DEFAULT_API;
  }

  async function apiFetch(path, opts) {
    const url = apiBase() + path;
    const res = await fetch(url, opts);
    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try {
        const d = await res.json();
        if (d?.error?.message) msg = d.error.message;
      } catch { /* ignore */ }
      throw new Error(msg);
    }
    return res;
  }

  async function api(path, opts) {
    const res = await apiFetch(path, opts);
    return res.json();
  }

  /* ---------- Theme Toggle ---------- */
  function initTheme() {
    const btn = $("#theme-toggle");
    const icon = $("#theme-icon");
    const label = $("#theme-label");
    const html = document.documentElement;

    function updateTheme(theme) {
      if (theme === 'light') {
        html.classList.remove('dark');
        html.classList.add('light');
        if (icon) icon.textContent = 'dark_mode';
        if (label) {
          label.textContent = window.i18n ? window.i18n.t('theme_dark') : 'Dark';
        }
      } else {
        html.classList.remove('light');
        html.classList.add('dark');
        if (icon) icon.textContent = 'light_mode';
        if (label) {
          label.textContent = window.i18n ? window.i18n.t('theme_light') : 'Light';
        }
      }
    }

    const savedTheme = localStorage.getItem('sqg_theme') || 'dark';
    updateTheme(savedTheme);

    if (btn) {
      btn.addEventListener('click', function() {
        const isLight = html.classList.contains('light');
        const nextTheme = isLight ? 'dark' : 'light';
        localStorage.setItem('sqg_theme', nextTheme);
        updateTheme(nextTheme);
      });
    }
  }

  /* ---------- Language Toggle ---------- */
  function initLanguage() {
    const langBtn = $("#lang-toggle");
    if (!langBtn) return;

    const currentLang = localStorage.getItem('sqg_lang') || 'en';
    langBtn.textContent = currentLang === 'en' ? 'RU' : 'EN';

    langBtn.addEventListener('click', function() {
      const newLang = localStorage.getItem('sqg_lang') === 'en' ? 'ru' : 'en';
      localStorage.setItem('sqg_lang', newLang);
      langBtn.textContent = newLang === 'en' ? 'RU' : 'EN';

      if (window.i18n) {
        window.i18n.setLanguage(newLang);
      } else {
        location.reload();
      }
    });
  }

  /* ---------- Gateway Status in Header ---------- */
  async function checkStatus() {
    const statusText = $("#status-text");
    if (!statusText) return;

    // Check if running on GitHub Pages
    const isGitHubPages = location.hostname.includes('github.io');

    if (isGitHubPages) {
      statusText.textContent = "DEMO MODE";
      localStorage.setItem("sqg_reachable", "0");
      return;
    }

    try {
      const h = await api("/health");
      statusText.textContent = h.key_configured ? "OPERATIONAL" : "NO API KEY";
      localStorage.setItem("sqg_reachable", "1");
    } catch {
      statusText.textContent = "OFFLINE";
      localStorage.setItem("sqg_reachable", "0");
    }
  }

  /* ---------- Dashboard ---------- */
  async function initDashboard() {
    // Check if running on GitHub Pages
    const isGitHubPages = location.hostname.includes('github.io');

    if (isGitHubPages) {
      // Demo mode for GitHub Pages
      $("#live-requests").textContent = "1,247";
      $("#live-latency").textContent = "156";
      $("#live-saved").textContent = "42.3";
      const bar = $("#saved-bar");
      if (bar) bar.style.width = "42.3%";
      $("#gateway-status").textContent = "Demo Mode - Deploy gateway to see live metrics";

      const feed = $("#terminal-feed");
      if (feed) {
        const demoLogs = [
          `[${timestamp()}] <span class="text-primary font-bold">DEMO</span> GitHub Pages deployment`,
          `[${timestamp()}] <span class="text-secondary font-bold">INFO</span> Deploy backend to enable live metrics`,
          `[${timestamp()}] <span class="text-outline font-bold">GUIDE</span> See README for deployment instructions`,
        ];
        feed.innerHTML = demoLogs.map(log => `<div class="text-outline-variant">${log}</div>`).join('');
      }

      await loadDemoRequestsTable();
      return;
    }

    try {
      const s = await api("/api/summary");

      // Update metrics
      $("#live-requests").textContent = n(s.stats.requests || 0);
      $("#live-latency").textContent = s.stats.avg_latency_ms || "-";

      const pct = Number(s.stats.savings_pct || 0);
      $("#live-saved").textContent = pct.toFixed(1);
      const bar = $("#saved-bar");
      if (bar) bar.style.width = `${Math.min(100, pct)}%`;

      // Gateway status
      $("#gateway-status").textContent = s.key_configured ?
        "Connected • API Key Configured" : "Connected • No API Key";

      // Update terminal with summary
      updateTerminal(s);
    } catch (e) {
      $("#gateway-status").textContent = "Gateway Offline";
      $("#live-requests").textContent = "-";
      $("#live-latency").textContent = "-";
      $("#live-saved").textContent = "-";
    }

    await loadRequestsTable();
  }

  async function loadDemoRequestsTable() {
    const tbody = $("#requests-table");
    if (!tbody) return;

    const demoData = [
      { mode_label: "cpp", mode_class: "cpp", input: 3245, baseline: 4120, saved: 875, thought: 0, latency_ms: 1200, status: 200 },
      { mode_label: "llm", mode_class: "llm", input: 1890, baseline: 3456, saved: 1566, thought: 234, latency_ms: 2340, status: 200 },
      { mode_label: "cpp", mode_class: "cpp", input: 567, baseline: 789, saved: 222, thought: 0, latency_ms: 890, status: 200 },
    ];

    tbody.innerHTML = demoData.map((r) => {
      const modeClass = r.mode_class === 'cpp' ? 'text-green-400' :
                       r.mode_class === 'llm' ? 'text-purple-400' :
                       'text-gray-400';
      const savedColor = r.saved > 0 ? 'text-green-400' : 'text-gray-500';

      return `
      <tr class="hover:bg-surface-container-high/60 transition-colors">
        <td class="p-3 ${modeClass}">${r.mode_label}</td>
        <td class="p-3 text-right">${n(r.input)}</td>
        <td class="p-3 text-right">${n(r.baseline)}</td>
        <td class="p-3 text-right ${savedColor}">${n(r.saved)}</td>
        <td class="p-3 text-right text-amber-400">${n(r.thought)}</td>
        <td class="p-3 text-right">${(r.latency_ms / 1000).toFixed(1)}s</td>
        <td class="p-3 text-right">${r.status}</td>
      </tr>`;
    }).join("");
  }

  function updateTerminal(summary) {
    const feed = $("#terminal-feed");
    if (!feed) return;

    const logs = [
      `[${timestamp()}] <span class="text-primary font-bold">SYSTEM</span> Gateway v${summary.version} operational`,
      `[${timestamp()}] <span class="text-secondary font-bold">STATS</span> Total requests: ${n(summary.stats.requests || 0)} • Avg latency: ${summary.stats.avg_latency_ms || 0}ms`,
      `[${timestamp()}] <span class="text-primary font-bold">SAVINGS</span> Net tokens saved: ${n(summary.stats.net_tokens_saved || 0)} (${(summary.stats.savings_pct || 0).toFixed(1)}%)`,
      `[${timestamp()}] <span class="text-outline font-bold">CONFIG</span> Upstream: ${summary.upstream.replace('https://', '')}`,
      `[${timestamp()}] <span class="text-outline font-bold">CONFIG</span> Default model: ${summary.default_model}`,
    ];

    feed.innerHTML = logs.map(log => `<div class="text-outline-variant">${log}</div>`).join('');
  }

  function timestamp() {
    const now = new Date();
    return now.toTimeString().substring(0, 8);
  }

  async function loadRequestsTable() {
    const tbody = $("#requests-table");
    if (!tbody) return;

    try {
      const rows = await api("/metrics?limit=12");
      if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-on-surface-variant">No requests yet. Try the <a href="playground.html" class="text-primary hover:underline">Playground</a>.</td></tr>`;
        return;
      }

      tbody.innerHTML = rows.map((r) => {
        const modeClass = r.mode_class === 'cpp' ? 'text-green-400' :
                         r.mode_class === 'llm' ? 'text-purple-400' :
                         'text-gray-400';
        const savedColor = r.saved > 0 ? 'text-green-400' : 'text-gray-500';

        return `
        <tr class="hover:bg-surface-container-high/60 transition-colors">
          <td class="p-3 ${modeClass}">${r.mode_label}</td>
          <td class="p-3 text-right">${n(r.input)}</td>
          <td class="p-3 text-right">${n(r.baseline)}</td>
          <td class="p-3 text-right ${savedColor}">${n(r.saved)}</td>
          <td class="p-3 text-right text-amber-400">${n(r.thought)}</td>
          <td class="p-3 text-right">${(r.latency_ms / 1000).toFixed(1)}s</td>
          <td class="p-3 text-right ${r.status === 200 ? '' : 'text-red-400'}">${r.status}</td>
        </tr>`;
      }).join("");
    } catch {
      tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-on-surface-variant">Gateway offline. Start with <code>uvicorn server:app --port 8082</code></td></tr>`;
    }
  }

  /* ---------- Playground ---------- */
  function initPlayground() {
    const form = $("#composer");
    const log = $("#chat-log");
    if (!form || !log) return;

    let busy = false;
    const history = [];

    const addMsg = (role, text, meta) => {
      const el = document.createElement("div");
      el.className = "msg " + role;
      el.textContent = text;
      if (meta) {
        const m = document.createElement("div");
        m.className = "meta";
        m.innerHTML = meta;
        el.append(m);
      }
      log.append(el);
      log.scrollTop = log.scrollHeight;
      return el;
    };

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (busy) return;

      const input = $("#chat-input");
      const text = input.value.trim();
      if (!text) return;

      busy = true;
      $("#send").disabled = true;
      input.value = "";
      addMsg("user", text);
      history.push({ role: "user", parts: [{ text }] });

      const typing = document.createElement("div");
      typing.className = "thinking";
      typing.textContent = "Gateway optimizing and sending request...";
      log.append(typing);
      log.scrollTop = log.scrollHeight;

      const mode = $("#squeeze-mode").value;
      const thinking = $("#thinking-mode").value;
      const model = $("#model-select").value;
      const qs = `?squeeze=${mode}` + (thinking === "-" ? "" : `&thinking=${thinking}`);
      const t0 = performance.now();

      try {
        const res = await apiFetch(`/v1beta/models/${model}:generateContent${qs}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: history }),
        });
        const data = await res.json();
        typing.remove();

        const sec = ((performance.now() - t0) / 1000).toFixed(1);
        const u = data.usageMetadata || {};
        const answer = data.candidates?.[0]?.content?.parts?.[0]?.text || "(empty response)";

        // Gateway telemetry
        const h = res.headers;
        const baseline = Number(h.get("x-squeeze-baseline") || 0);
        const inputTok = Number(h.get("x-squeeze-input") || u.promptTokenCount || 0);
        const aux = Number(h.get("x-squeeze-aux") || 0);
        const saved = Number(h.get("x-squeeze-saved") || 0);
        const level = h.get("x-squeeze-thinking") || "client";
        const modeName = h.get("x-squeeze-mode") || "passthrough";

        const modeLabel = modeName === "squeeze_cpp" ? "cpp" :
                         modeName === "squeeze_llm" ? "llm" : "pass";
        const modeClass = modeName === "squeeze_cpp" ? "cpp" :
                         modeName === "squeeze_llm" ? "llm" : "pass";

        addMsg("bot", answer, `
          <span class="chip ${modeClass}">${modeLabel}</span>
          <span class="chip cyan">${n(inputTok)} / ${n(baseline)} input</span>
          <span class="chip ${saved > 0 ? 'green' : 'dim'}">${saved > 0 ? '−' : ''}${n(saved)} saved</span>
          <span class="chip dim">aux ${n(aux)}</span>
          <span class="chip amber">${level}</span>
          <span class="chip dim">${n(u.thoughtsTokenCount)} thinking</span>
          <span class="chip">${sec}s</span>`);

        history.push({ role: "model", parts: [{ text: answer }] });
      } catch (err) {
        typing.remove();
        addMsg("bot", "Error: " + err.message +
          "\n\nCheck that gateway is running and Gemini API key is configured in .env");
      } finally {
        busy = false;
        $("#send").disabled = false;
        $("#chat-input").focus();
      }
    });

    $("#chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit();
      }
    });

    $("#reset-chat")?.addEventListener("click", () => {
      history.length = 0;
      log.innerHTML = '<div class="msg bot">Chat cleared. Send a new message.</div>';
    });
  }

  /* ---------- Docs: Code Tabs & Copy ---------- */
  function initDocs() {
    $$("[data-tabs]").forEach((group) => {
      const buttons = $$("[data-lang]", group.parentElement);
      const panes = $$("[data-pane]", group.parentElement);
      buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
          buttons.forEach((b) => b.classList.toggle("active", b === btn));
          panes.forEach((p) => p.classList.toggle("hidden", p.dataset.pane !== btn.dataset.lang));
        });
      });
    });

    document.addEventListener("click", async (e) => {
      const btn = e.target.closest(".copy-btn");
      if (!btn) return;
      const code = btn.parentElement.querySelector("code, pre")?.innerText || "";
      try {
        await navigator.clipboard.writeText(code);
        const old = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = old), 1400);
      } catch { /* clipboard may be denied */ }
    });
  }

  /* ---------- Gateway URL Config (for GitHub Pages) ---------- */
  function initGatewayForm() {
    const input = $("#gateway-url");
    if (!input) return;
    input.value = localStorage.getItem("sqg_api") || "";
    $("#gateway-save")?.addEventListener("click", () => {
      const v = input.value.trim().replace(/\/$/, "");
      if (v) localStorage.setItem("sqg_api", v);
      else localStorage.removeItem("sqg_api");
      location.reload();
    });
  }

  /* ---------- Initialize ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initLanguage();
    checkStatus();
    initGatewayForm();

    // Initialize i18n if available
    if (window.i18n) {
      window.i18n.updatePage();
    }

    const page = document.body.dataset.page;
    switch (page) {
      case "dashboard": initDashboard(); break;
      case "playground": initPlayground(); break;
      case "docs": initDocs(); break;
    }
  });
})();
