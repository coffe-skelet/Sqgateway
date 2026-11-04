/* Squeeze Gateway — общий клиентский слой.
   Работает и на локальном шлюзе (same-origin), и на GitHub Pages
   (тогда адрес шлюза задаётся в настройках и хранится в localStorage). */

(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fmt = new Intl.NumberFormat("ru-RU");
  const n = (v) => fmt.format(Number(v || 0));

  const DEFAULT_API = "http://localhost:8082";

  function apiBase() {
    const saved = localStorage.getItem("sqg_api");
    if (saved) return saved.replace(/\/$/, "");
    if (location.protocol.startsWith("http") && /^(localhost|127\.0\.0\.1)/.test(location.hostname)) {
      return ""; // локально: шлюз и сайт на одном origin
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

  /* ---------- навигация ---------- */
  function markNav() {
    const page = document.body.dataset.page;
    $$(".nav a").forEach((a) => {
      if (a.dataset.page === page) a.classList.add("active");
    });
  }

  /* ---------- статус шлюза в шапке ---------- */
  async function paintStatus() {
    const pill = $("#gw-status");
    if (!pill) return;
    try {
      const h = await api("/health");
      pill.classList.remove("bad");
      pill.innerHTML = `<span class="beacon pulse"></span>${h.key_configured ? "gateway online" : "online · no key"}`;
      localStorage.setItem("sqg_reachable", "1");
    } catch {
      pill.classList.add("bad");
      pill.innerHTML = `<span class="beacon"></span>gateway offline`;
      localStorage.setItem("sqg_reachable", "0");
    }
  }

  /* ---------- dashboard ---------- */
  async function initDashboard() {
    const offline = $("#offline-note");
    try {
      const s = await api("/api/summary");
      if (offline) offline.classList.add("hidden");

      $("#m-net").textContent = n(s.stats.net_tokens_saved);
      const pct = Number(s.stats.savings_pct || 0);
      const savedChip = $("#chip-saved");
      if (savedChip) savedChip.textContent = `−${pct.toFixed(1)}% к baseline`;
      $("#m-saved-pct").textContent = `${pct.toFixed(1)}%`;
      $("#m-req").textContent = n(s.stats.requests);
      $("#m-lat").textContent = s.stats.avg_latency_ms ? (s.stats.avg_latency_ms / 1000).toFixed(1) : "–";
      $("#m-thought").textContent = n(s.stats.thought);
      $("#m-out").textContent = n(s.stats.output);
      $("#m-aux").textContent = n(s.stats.aux);
      $("#m-in").textContent = n(s.stats.input);
      $("#k-upstream").textContent = s.upstream.replace("https://", "");
      $("#k-model").textContent = s.default_model;
      $("#k-version").textContent = "v" + s.version;
      $("#k-key").textContent = s.key_configured ? "настроен" : "не настроен";
    } catch (e) {
      if (offline) offline.classList.remove("hidden");
    }
    await loadMetrics();
  }

  async function loadMetrics() {
    const tbody = $("#rows");
    if (!tbody) return;
    try {
      const rows = await api("/metrics?limit=12");
      if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty">Пока нет запросов. Откройте <a href="playground.html" style="color:var(--lilac)">Playground</a> и задайте первый вопрос.</td></tr>`;
        return;
      }
      tbody.innerHTML = rows.map((r) => `
        <tr>
          <td><span class="chip ${r.mode_class}">${r.mode_label}</span></td>
          <td class="num">${n(r.input)}</td>
          <td class="num">${n(r.baseline)}</td>
          <td class="num">${n(r.aux)}</td>
          <td class="num" style="color:${r.saved > 0 ? "var(--green-soft)" : "var(--text-faint)"}">${n(r.saved)}</td>
          <td class="num">${n(r.thought)}</td>
          <td class="num">${(r.latency_ms / 1000).toFixed(1)}</td>
          <td class="num ${r.status === 200 ? "" : "faint"}">${r.status}</td>
        </tr>`).join("");
    } catch {
      tbody.innerHTML = `<tr><td colspan="8" class="empty">Шлюз недоступен. Запустите <span class="mono">uvicorn server:app --port 8082</span></td></tr>`;
    }
  }

  /* ---------- playground ---------- */
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
      typing.textContent = "шлюз оптимизирует и отправляет запрос…";
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
        const answer = data.candidates?.[0]?.content?.parts?.[0]?.text || "(пустой ответ)";

        // телеметрия шлюза: baseline, фактический ввод, aux, сохранённые токены
        const h = res.headers;
        const baseline = Number(h.get("x-squeeze-baseline") || 0);
        const inputTok = Number(h.get("x-squeeze-input") || u.promptTokenCount || 0);
        const aux = Number(h.get("x-squeeze-aux") || 0);
        const saved = Number(h.get("x-squeeze-saved") || 0);
        const level = h.get("x-squeeze-thinking") || "client";
        const modeName = h.get("x-squeeze-mode") || "passthrough";
        const modeLabel = modeName === "squeeze_cpp" ? "cpp"
          : modeName === "squeeze_llm" ? "llm" : "pass";
        const modeClass = modeName === "squeeze_cpp" ? "cpp"
          : modeName === "squeeze_llm" ? "llm" : "pass";

        addMsg("bot", answer, `
          <span class="chip ${modeClass}">${modeLabel}</span>
          <span class="chip cyan">${n(inputTok)} / ${n(baseline)} ввод</span>
          <span class="chip ${saved > 0 ? "green" : "dim"}">${saved > 0 ? "−" : ""}${n(saved)} saved</span>
          <span class="chip dim">aux ${n(aux)}</span>
          <span class="chip amber">${level}</span>
          <span class="chip dim">${n(u.thoughtsTokenCount)} мысли</span>
          <span class="chip">${sec} с</span>`);
        history.push({ role: "model", parts: [{ text: answer }] });
      } catch (err) {
        typing.remove();
        addMsg("bot", "Ошибка: " + err.message +
          "\n\nПроверьте, что шлюз запущен и ключ Gemini настроен в .env.");
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
      log.innerHTML = "";
    });
  }

  /* ---------- docs: табы кода и копирование ---------- */
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
        btn.textContent = "скопировано";
        setTimeout(() => (btn.textContent = old), 1400);
      } catch { /* clipboard может быть запрещён */ }
    });
  }

  /* ---------- настройка адреса шлюза (для GitHub Pages) ---------- */
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

  /* ---------- запуск ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    markNav();
    paintStatus();
    initGatewayForm();
    switch (document.body.dataset.page) {
      case "dashboard": initDashboard(); break;
      case "playground": initPlayground(); break;
      case "docs": initDocs(); break;
      case "project": initDocs(); break;
    }
  });
})();
