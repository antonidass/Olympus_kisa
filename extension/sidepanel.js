// Sidebar расширения. Показывает список промптов выбранного сценария,
// позволяет скопировать любой по кнопке Copy и автоматически кладёт
// следующий в буфер, когда пользователь нажимает Generate в Flow.
//
// Также принимает от background сообщение zip_ready, когда Flow скачивает
// архив, и POST'ит на webapp /api/extension/distribute.

const WEBAPP = "http://127.0.0.1:5000";
const $ = (id) => document.getElementById(id);

const state = {
  scenario: "",
  kind: "images",
  prompts: [],
  currentIdx: -1,
  doneIdx: new Set(),
  autocopy: true,
};

// ─── Лог ───────────────────────────────────────────────────────────────────

function log(msg, cls = "") {
  const line = document.createElement("div");
  line.className = "log-line " + cls;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  const root = $("log");
  root.prepend(line);
  while (root.children.length > 60) root.lastChild.remove();
}

// ─── Загрузка списков ──────────────────────────────────────────────────────

async function loadScenarios() {
  let data;
  try {
    const r = await fetch(`${WEBAPP}/api/extension/scenarios`);
    data = await r.json();
  } catch (e) {
    log(`webapp недоступен (${e.message}). Запусти webapp/run.bat`, "err");
    return;
  }
  const sel = $("scenario-select");
  sel.innerHTML = '<option value="">— выбери сценарий —</option>';
  for (const s of data.scenarios) {
    const opt = document.createElement("option");
    opt.value = s.name;
    const cnt = state.kind === "images" ? s.image_count : s.video_count;
    opt.textContent = `${s.name}${cnt ? ` (${cnt})` : ""}`;
    sel.appendChild(opt);
  }

  // Восстановим прошлый выбор из storage.local
  chrome.storage.local.get(["scenario", "kind", "autocopy"], (saved) => {
    if (saved.kind) {
      $("kind-select").value = saved.kind;
      state.kind = saved.kind;
    }
    if (saved.autocopy === false) {
      $("autocopy").checked = false;
      state.autocopy = false;
    }
    if (saved.scenario) {
      sel.value = saved.scenario;
      state.scenario = saved.scenario;
      loadPrompts();
    }
  });
}

async function loadPrompts() {
  if (!state.scenario) {
    state.prompts = [];
    state.currentIdx = -1;
    state.doneIdx = new Set();
    renderPrompts();
    return;
  }
  let data;
  try {
    const r = await fetch(
      `${WEBAPP}/api/extension/prompts/${encodeURIComponent(state.scenario)}/${state.kind}`
    );
    if (!r.ok) {
      log(`нет ${state.kind}.md для ${state.scenario}`, "err");
      state.prompts = [];
      state.currentIdx = -1;
      state.doneIdx = new Set();
      renderPrompts();
      return;
    }
    data = await r.json();
  } catch (e) {
    log(`ошибка загрузки промптов: ${e.message}`, "err");
    return;
  }
  state.prompts = data.prompts || [];
  state.currentIdx = state.prompts.length > 0 ? 0 : -1;
  state.doneIdx = new Set();
  renderPrompts();
  log(`загружено ${state.prompts.length} промптов из ${state.kind}.md`, "ok");
  if (state.autocopy && state.prompts.length > 0) {
    copyToClipboard(state.prompts[0].prompt, 0, /*silent*/ true);
  }
}

// ─── Рендер ────────────────────────────────────────────────────────────────

function renderPrompts() {
  const root = $("prompts");
  root.innerHTML = "";

  if (!state.scenario) {
    root.innerHTML = '<div style="padding:14px;color:#666">Выбери сценарий выше.</div>';
    updateProgress();
    return;
  }
  if (state.prompts.length === 0) {
    root.innerHTML = '<div style="padding:14px;color:#666">Промптов нет.</div>';
    updateProgress();
    return;
  }

  state.prompts.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "prompt-card";
    if (idx === state.currentIdx) card.classList.add("current");
    if (state.doneIdx.has(idx)) card.classList.add("done");

    const head = document.createElement("div");
    head.className = "prompt-head";
    head.innerHTML = `
      <span class="scene-num">Сцена ${p.scene}</span>
      <span class="marker" title="${escapeAttr(p.marker || "")}">${escapeHtml(p.marker || "")}</span>
      <button class="copy-btn" data-idx="${idx}">Copy</button>
    `;
    card.appendChild(head);

    if (p.text) {
      const txt = document.createElement("div");
      txt.className = "text";
      txt.textContent = p.text;
      card.appendChild(txt);
    }

    const pt = document.createElement("div");
    pt.className = "prompt-text";
    pt.textContent = p.prompt;
    card.appendChild(pt);

    const exp = document.createElement("span");
    exp.className = "expand";
    exp.textContent = "развернуть промпт";
    exp.onclick = () => {
      card.classList.toggle("expanded");
      exp.textContent = card.classList.contains("expanded") ? "свернуть" : "развернуть промпт";
    };
    card.appendChild(exp);

    root.appendChild(card);
  });

  root.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = parseInt(btn.dataset.idx, 10);
      copyToClipboard(state.prompts[idx].prompt, idx);
      btn.classList.add("copied");
      setTimeout(() => btn.classList.remove("copied"), 700);
    });
  });

  updateProgress();
  scrollToCurrent();
}

function scrollToCurrent() {
  const cur = $("prompts").querySelector(".prompt-card.current");
  if (cur) cur.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function updateProgress() {
  const total = state.prompts.length;
  if (!total) {
    $("progress").textContent = "—";
    return;
  }
  const done = state.doneIdx.size;
  const cur = state.currentIdx >= 0 ? state.currentIdx + 1 : "—";
  $("progress").textContent = `${done}/${total} (текущая: ${cur})`;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
function escapeAttr(s) {
  return escapeHtml(s).replaceAll('"', "&quot;");
}

// ─── Буфер обмена и навигация ─────────────────────────────────────────────

async function copyToClipboard(text, idx, silent = false) {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    if (typeof idx === "number") state.currentIdx = idx;
    if (!silent) {
      const sceneNum = state.prompts[state.currentIdx]?.scene;
      log(`в буфер: сцена ${sceneNum} (${text.length} симв.)`, "ok");
    }
    renderPrompts();
  } catch (e) {
    log(`не удалось скопировать: ${e.message}`, "err");
  }
}

function advance() {
  if (state.prompts.length === 0) return;
  if (state.currentIdx >= 0) state.doneIdx.add(state.currentIdx);
  if (state.currentIdx + 1 < state.prompts.length) {
    state.currentIdx += 1;
    renderPrompts();
    if (state.autocopy) {
      copyToClipboard(state.prompts[state.currentIdx].prompt, state.currentIdx);
    } else {
      log(`следующая сцена ${state.prompts[state.currentIdx].scene}`, "ok");
    }
  } else {
    state.currentIdx = -1;
    renderPrompts();
    log("Все промпты прошли — можно жать Download Project в Flow.", "ok");
  }
}

// ─── Сообщения от background и content ───────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return;

  if (msg.type === "generate_clicked") {
    log("клик Generate в Flow → следующий промпт", "ok");
    advance();
    return;
  }

  if (msg.type === "zip_ready") {
    if (!state.scenario) {
      log(`zip скачан (${msg.path}), но сценарий не выбран — distribute не запущен`, "warn");
      return;
    }
    log(`zip скачан → distribute для «${state.scenario}»…`, "ok");
    chrome.runtime.sendMessage(
      { type: "distribute", scenario: state.scenario, path: msg.path },
      (resp) => {
        if (chrome.runtime.lastError) {
          log(`distribute: ${chrome.runtime.lastError.message}`, "err");
          return;
        }
        if (!resp || !resp.ok) {
          log(`distribute не дошёл до webapp: ${resp?.error || "?"}`, "err");
          return;
        }
        const r = resp.body || {};
        if (r.ok) {
          log(`distribute OK (rc=${r.returncode})`, "ok");
          if (r.stdout) log(r.stdout.trim().split("\n").slice(-3).join(" | "), "ok");
        } else {
          log(`distribute упал rc=${r.returncode}: ${(r.stderr || "").slice(0, 220)}`, "err");
        }
      }
    );
  }
});

// Если sidepanel был закрыт когда zip скачался — подберём из storage.
chrome.storage.local.get(["pendingZip"], (saved) => {
  const pz = saved.pendingZip;
  if (!pz || !pz.path) return;
  // Считаем «свежим» если меньше 2 минут назад.
  if (Date.now() - (pz.ts || 0) > 120_000) return;
  log(`найден pending zip: ${pz.path} (открой sidepanel сразу после скачивания, чтобы distribute стартовал автоматически)`, "warn");
  chrome.storage.local.remove("pendingZip");
});

// ─── UI события ────────────────────────────────────────────────────────────

$("scenario-select").addEventListener("change", (e) => {
  state.scenario = e.target.value;
  chrome.storage.local.set({ scenario: state.scenario });
  loadPrompts();
});

$("kind-select").addEventListener("change", (e) => {
  state.kind = e.target.value;
  chrome.storage.local.set({ kind: state.kind });
  loadScenarios();
  loadPrompts();
});

$("autocopy").addEventListener("change", (e) => {
  state.autocopy = e.target.checked;
  chrome.storage.local.set({ autocopy: state.autocopy });
});

$("reload-btn").addEventListener("click", () => {
  loadScenarios();
  if (state.scenario) loadPrompts();
});

$("clear-log").addEventListener("click", () => {
  $("log").innerHTML = "";
});

loadScenarios();
