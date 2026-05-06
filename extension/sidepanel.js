// Sidebar расширения. Показывает список промптов выбранного сценария,
// позволяет скопировать любой по кнопке Copy и автоматически кладёт
// следующий в буфер, когда пользователь нажимает Generate в Flow.
//
// Также принимает от background сообщение flow_download_ready, когда Flow
// вручную скачивает проект, и импортирует файл в images/ или video/.

const WEBAPP = "http://127.0.0.1:5000";
const $ = (id) => document.getElementById(id);

const state = {
  scenario: "",
  kind: "images",
  prompts: [],
  currentIdx: -1,
  doneIdx: new Set(),
  autocopy: true,
  downloadImages: true,
  downloadStickers: true,
  downloadVideos: true,
  seenDownloadIds: new Set(),
  seenDownloadKeys: new Set(),
};

const FLOW_HOST_MARKERS = [
  "labs.google",
  "aisandbox",
  "storage.googleapis.com",
  "flow",
];

const FLOW_DOWNLOAD_EXTS = [
  ".zip",
  ".mp4",
  ".mov",
  ".webm",
  ".m4v",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
];

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
    let cnt = 0;
    if (state.kind === "images") cnt = s.image_count || 0;
    else if (state.kind === "stickers") cnt = s.sticker_count || 0;
    else if (state.kind === "video") cnt = s.video_count || 0;
    opt.textContent = `${s.name}${cnt ? ` (${cnt})` : ""}`;
    sel.appendChild(opt);
  }

  // Восстановим прошлый выбор из storage.local
  chrome.storage.local.get(
    [
      "scenario",
      "kind",
      "autocopy",
      "downloadImages",
      "downloadStickers",
      "downloadVideos",
    ],
    (saved) => {
      if (saved.kind) {
        $("kind-select").value = saved.kind;
        state.kind = saved.kind;
      }
      if (saved.autocopy === false) {
        $("autocopy").checked = false;
        state.autocopy = false;
      }
      if (saved.downloadImages === false) {
        $("download-images").checked = false;
        state.downloadImages = false;
      }
      if (saved.downloadStickers === false) {
        $("download-stickers").checked = false;
        state.downloadStickers = false;
      }
      if (saved.downloadVideos === false) {
        $("download-videos").checked = false;
        state.downloadVideos = false;
      }
      if (saved.scenario) {
        sel.value = saved.scenario;
        state.scenario = saved.scenario;
        loadPrompts();
      }
    }
  );
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

function basename(path) {
  return String(path || "").split(/[\\/]/).pop() || String(path || "");
}

function currentDownloadTarget() {
  if (state.kind === "video") {
    return state.downloadVideos ? "video" : "";
  }
  if (state.kind === "images") {
    return state.downloadImages ? "images" : "";
  }
  if (state.kind === "stickers") {
    return state.downloadStickers ? "stickers" : "";
  }
  return "";
}

function targetLabel(target) {
  if (target === "video") return "video/";
  if (target === "stickers") return "images/stickers/";
  return "images/";
}

function getExt(path) {
  const low = basename(path).toLowerCase();
  const idx = low.lastIndexOf(".");
  return idx >= 0 ? low.slice(idx) : "";
}

function looksLikeFlowDownloadItem(item) {
  const url = String(item?.finalUrl || item?.url || "").toLowerCase();
  const name = basename(item?.filename || "").toLowerCase();
  const ext = getExt(name);
  if (!FLOW_DOWNLOAD_EXTS.includes(ext)) return false;
  if (FLOW_HOST_MARKERS.some((marker) => url.includes(marker))) return true;
  return /^download(?: \(\d+\))?\.(zip|mp4|mov|webm|m4v|jpg|jpeg|png|webp)$/.test(name);
}

function targetAcceptsItem(target, item) {
  const ext = getExt(item?.filename || "");
  if (ext === ".zip") return true;
  if (target === "video") {
    return [".mp4", ".mov", ".webm", ".m4v"].includes(ext);
  }
  if (target === "images" || target === "stickers") {
    return [".jpg", ".jpeg", ".png", ".webp"].includes(ext);
  }
  return false;
}

function markDownloadSeen(item) {
  if (item?.id != null) state.seenDownloadIds.add(item.id);
  if (item?.filename) state.seenDownloadKeys.add(item.filename);
}

function alreadySawDownload(item) {
  return (
    (item?.id != null && state.seenDownloadIds.has(item.id)) ||
    (!!item?.filename && state.seenDownloadKeys.has(item.filename))
  );
}

function handleFlowDownload(msg, fromPending = false) {
  const fileLabel = basename(msg.path || msg.filename || "");
  if (!state.scenario) {
    log(
      `Flow скачал ${fileLabel}, но сценарий не выбран — импорт пропущен`,
      "warn"
    );
    return;
  }

  const target = currentDownloadTarget();
  if (!target) {
    let label = "скачать изображения";
    if (state.kind === "video") label = "скачать видео";
    else if (state.kind === "stickers") label = "скачать стикеры";
    log(
      `${fileLabel}: режим ${state.kind}, но галка «${label}» выключена — импорт пропущен`,
      "warn"
    );
    return;
  }

  log(
    `${fromPending ? "pending" : "Flow"} download → импорт в ${targetLabel(target)} для «${state.scenario}»…`,
    "ok"
  );
  chrome.runtime.sendMessage(
    {
      type: "import_download",
      scenario: state.scenario,
      path: msg.path,
      target,
    },
    (resp) => {
      if (chrome.runtime.lastError) {
        log(`import: ${chrome.runtime.lastError.message}`, "err");
        return;
      }
      if (!resp || !resp.ok) {
        log(`import не дошёл до webapp: ${resp?.error || "?"}`, "err");
        return;
      }
      const r = resp.body || {};
      if (!r.ok) {
        log(`import упал: ${r.error || "неизвестная ошибка"}`, "err");
        return;
      }
      const imported = r.imported_count ?? 0;
      const skipped = r.skipped_count ?? 0;
      log(
        `import OK → ${targetLabel(target)} ${imported} файл(ов)` +
          (skipped ? `, пропущено ${skipped}` : ""),
        "ok"
      );
      if (Array.isArray(r.files) && r.files.length) {
        log(r.files.slice(0, 4).join(" | "), "ok");
      }
    }
  );
}

function importObservedDownload(item, source = "downloads") {
  if (!item || !item.filename) return;
  if (alreadySawDownload(item)) return;

  const target = currentDownloadTarget();
  if (!target) return;
  if (!looksLikeFlowDownloadItem(item)) return;
  if (!targetAcceptsItem(target, item)) return;

  markDownloadSeen(item);
  handleFlowDownload(
    {
      path: item.filename,
      filename: basename(item.filename),
      url: item.finalUrl || item.url || "",
    },
    source === "pending"
  );
}

function attachDownloadsWatch() {
  if (!chrome.downloads?.onChanged) return;

  chrome.downloads.onCreated.addListener((item) => {
    if (!item || !item.filename) return;
    if (!looksLikeFlowDownloadItem(item)) return;
    log(`downloads: замечен файл ${basename(item.filename)}`, "ok");
  });

  chrome.downloads.onChanged.addListener((delta) => {
    if (!delta || delta.id == null) return;
    if (!delta.state || delta.state.current !== "complete") return;
    chrome.downloads.search({ id: delta.id }, (items) => {
      const item = items && items[0];
      if (!item || !item.filename) return;
      if (!looksLikeFlowDownloadItem(item)) return;
      log(`downloads: завершён ${basename(item.filename)}`, "ok");
      importObservedDownload(item, "downloads");
    });
  });
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

  // Side panel НЕ имеет document focus, когда пользователь работает в Flow,
  // поэтому navigator.clipboard.writeText прямо отсюда обычно падает с
  // NotAllowedError ("Document is not focused"). Fix: попросить content script
  // на активной Flow-вкладке записать буфер — у неё фокус есть. Fallback на
  // navigator.clipboard остаётся для случаев, когда side panel сам сфокусирован
  // (ручной клик по Copy в карточке) или Flow-вкладки нет вовсе.
  let success = false;
  let lastError = null;
  let route = null;

  // ── Strategy 1: запись через content script сфокусированной Flow-вкладки.
  try {
    const activeTabs = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    const flowTab = (activeTabs || []).find((t) =>
      /^https:\/\/labs\.google/.test(t?.url || "")
    );
    if (flowTab && flowTab.id != null) {
      const resp = await chrome.tabs
        .sendMessage(flowTab.id, { type: "clipboard_write", text })
        .catch((e) => ({ ok: false, error: e?.message || String(e) }));
      if (resp && resp.ok) {
        success = true;
        route = "content";
      } else {
        lastError = resp?.error || "no response from Flow tab content script";
      }
    } else {
      lastError = "active tab is not labs.google";
    }
  } catch (e) {
    lastError = e?.message || String(e);
  }

  // ── Strategy 2: fallback в navigator.clipboard самого side panel.
  // Работает только если side panel сейчас сфокусирован (ручной Copy).
  if (!success) {
    try {
      await navigator.clipboard.writeText(text);
      success = true;
      route = "sidepanel";
    } catch (e) {
      lastError = e?.message || String(e);
    }
  }

  if (!success) {
    log(`не удалось скопировать: ${lastError}`, "err");
    return;
  }

  if (typeof idx === "number") state.currentIdx = idx;
  if (!silent) {
    const sceneNum = state.prompts[state.currentIdx]?.scene;
    log(
      `в буфер (${route}): сцена ${sceneNum} (${text.length} симв.)`,
      "ok"
    );
  }
  renderPrompts();
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

  if (msg.type === "flow_download_armed") {
    log(`поймал клик «${msg.label || "Download Project"}» → жду ближайшее скачивание`, "ok");
    return;
  }

  if (msg.type === "flow_download_ready") {
    handleFlowDownload(msg, false);
  }
});

// Если sidepanel был закрыт когда Flow скачал файл — подберём из storage.
chrome.storage.local.get(["pendingFlowDownload"], (saved) => {
  const pz = saved.pendingFlowDownload;
  if (!pz || !pz.path) return;
  // Считаем «свежим» если меньше 2 минут назад.
  if (Date.now() - (pz.ts || 0) > 120_000) return;
  log(`найден pending download: ${basename(pz.path)}`, "warn");
  chrome.storage.local.remove("pendingFlowDownload");
  handleFlowDownload(pz, true);
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

$("download-images").addEventListener("change", (e) => {
  state.downloadImages = e.target.checked;
  chrome.storage.local.set({ downloadImages: state.downloadImages });
});

$("download-stickers").addEventListener("change", (e) => {
  state.downloadStickers = e.target.checked;
  chrome.storage.local.set({ downloadStickers: state.downloadStickers });
});

$("download-videos").addEventListener("change", (e) => {
  state.downloadVideos = e.target.checked;
  chrome.storage.local.set({ downloadVideos: state.downloadVideos });
});

$("reload-btn").addEventListener("click", () => {
  loadScenarios();
  if (state.scenario) loadPrompts();
});

$("clear-log").addEventListener("click", () => {
  $("log").innerHTML = "";
});

attachDownloadsWatch();
loadScenarios();
