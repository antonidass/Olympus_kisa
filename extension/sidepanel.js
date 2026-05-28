// Sidebar расширения. Показывает список промптов выбранного сценария.
// Клик по Copy кладёт промпт в буфер обмена и сдвигает выделение на
// следующую сцену. Скачивания из Flow ловит через chrome.downloads и
// импортирует в content/<миф>/ через webapp.
//
// ВАЖНО: расширение НЕ внедряется на страницу Flow и НЕ слушает её
// события. Никакой автоматизации DOM Flow, никакого перехвата Enter
// или клика по «Generate» / «Download Project» — только буфер обмена
// и chrome.downloads. Flow считает чтение DOM роботом и за это наказывает,
// поэтому не лезем на его страницу вообще.

const WEBAPP = "http://127.0.0.1:5000";
const $ = (id) => document.getElementById(id);

const state = {
  scenario: "",
  kind: "images",
  generator: "flow",
  prompts: [],
  currentIdx: -1,
  lastCopiedIdx: -1,   // последняя сцена, на которую нажали Copy — фоллбэк для Grok
  tabSceneMap: {},     // tabId → { sceneNum, idx } — для параллельных Grok-вкладок
  doneIdx: new Set(),
  downloadImages: true,
  downloadStickers: true,
  downloadVideos: true,
  autoDistribute: true,
  seenDownloadIds: new Set(),
  seenDownloadKeys: new Set(),
  importedDownloadKeys: new Set(),
};

const FLOW_HOST_MARKERS = [
  "labs.google",
  "aisandbox",
  "storage.googleapis.com",
  "flow",
];

const GROK_HOST_MARKERS = ["grok.com", "x.ai"];

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

  // Восстановим прошлый выбор из storage.local.
  chrome.storage.local.get(
    [
      "scenario",
      "kind",
      "generator",
      "downloadImages",
      "downloadStickers",
      "downloadVideos",
      "autoDistribute",
    ],
    (saved) => {
      if (saved.generator) {
        $("generator-select").value = saved.generator;
        state.generator = saved.generator;
        updateTogglesForGenerator();
      }
      if (saved.kind) {
        $("kind-select").value = saved.kind;
        state.kind = saved.kind;
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
      if (saved.autoDistribute === false) {
        $("auto-distribute").checked = false;
        state.autoDistribute = false;
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
  state.lastCopiedIdx = -1;
  state.tabSceneMap = {};
  state.doneIdx = new Set();
  renderPrompts();
  log(`загружено ${state.prompts.length} промптов из ${state.kind}.md`, "ok");
}

// ─── Импорт скачанного файла ────────────────────────────────────────────────

function basename(path) {
  return String(path || "").split(/[\\/]/).pop() || String(path || "");
}

function currentDownloadTarget() {
  if (state.kind === "video") return state.downloadVideos ? "video" : "";
  if (state.kind === "images") return state.downloadImages ? "images" : "";
  if (state.kind === "stickers") return state.downloadStickers ? "stickers" : "";
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

function looksLikeGrokDownloadItem(item) {
  const name = basename(item?.filename || "").toLowerCase();
  const ext = getExt(name);
  // В Grok-режиме принимаем любой медиафайл с нужным расширением —
  // URL Grok непредсказуем (CDN), фильтровать по хосту ненадёжно.
  return [".mp4", ".mov", ".webm", ".m4v", ".jpg", ".jpeg", ".png", ".webp"].includes(ext);
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

function downloadImportKey(path, target) {
  return [
    state.scenario || "",
    target || "",
    String(path || "").toLowerCase(),
  ].join("|");
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
      `Скачан ${fileLabel}, но сценарий не выбран — импорт пропущен`,
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

  const importKey = downloadImportKey(msg.path || msg.filename || "", target);
  if (state.importedDownloadKeys.has(importKey)) {
    log(`${fileLabel}: duplicate download event skipped`, "warn");
    return;
  }
  state.importedDownloadKeys.add(importKey);
  markDownloadSeen({
    id: msg.downloadId ?? msg.id,
    filename: msg.path || msg.filename,
  });

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
      autoDistribute: state.autoDistribute,
    },
    (resp) => {
      if (chrome.runtime.lastError) {
        state.importedDownloadKeys.delete(importKey);
        log(`import: ${chrome.runtime.lastError.message}`, "err");
        return;
      }
      if (!resp || !resp.ok) {
        state.importedDownloadKeys.delete(importKey);
        log(`import не дошёл до webapp: ${resp?.error || "?"}`, "err");
        return;
      }
      const r = resp.body || {};
      if (!r.ok) {
        state.importedDownloadKeys.delete(importKey);
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

      // Результат distribute_*.py (если webapp его запускал).
      const dist = r.distribute;
      if (dist) {
        const scriptLabel = dist.script || "distribute";
        if (dist.ok) {
          // Достаём из stdout последние 1-2 строки — обычно там итоговая
          // статистика «N matched / M unmatched». Если stdout пустой —
          // просто сообщаем returncode=0.
          const tail = (dist.stdout || "")
            .trim()
            .split(/\r?\n/)
            .slice(-3)
            .join(" · ");
          log(
            `distribute OK (${scriptLabel}): ${tail || "returncode=0"}`,
            "ok"
          );
        } else {
          const errTail =
            (dist.stderr || "").trim().split(/\r?\n/).pop() ||
            dist.error ||
            `returncode=${dist.returncode}`;
          log(
            `distribute упал (${scriptLabel}): ${errTail}`,
            "err"
          );
          // Также покажем stdout-хвост: distribute_images.py пишет конфликты
          // сопоставления в stdout (не stderr).
          if (dist.stdout) {
            const stdoutTail = dist.stdout
              .trim()
              .split(/\r?\n/)
              .slice(-3)
              .join(" · ");
            if (stdoutTail) log(`distribute stdout: ${stdoutTail}`, "warn");
          }
        }
      }
    }
  );
}

function updateTogglesForGenerator() {
  const isGrok = state.generator === "grok";
  // Авто-разложить не нужен в Grok — там раскладка по текущей сцене автоматическая
  const autoDistLabel = $("auto-distribute").closest("label");
  if (autoDistLabel) autoDistLabel.style.display = isGrok ? "none" : "";
}

async function handleGrokDownload(msg) {
  const fileLabel = basename(msg.path || msg.filename || "");
  if (!state.scenario) {
    log(`Скачан ${fileLabel}, но сценарий не выбран — импорт пропущен`, "warn");
    return;
  }

  const target = currentDownloadTarget();
  if (!target) {
    let label = "скачать изображения";
    if (state.kind === "video") label = "скачать видео";
    else if (state.kind === "stickers") label = "скачать стикеры";
    log(`${fileLabel}: галка «${label}» выключена — импорт пропущен`, "warn");
    return;
  }

  // Ищем сцену: сначала по tabId (для параллельных вкладок), потом lastCopiedIdx.
  const tabId = msg.tabId;
  let curIdx = -1;
  let sceneNum = -1;

  if (tabId != null && tabId >= 0 && state.tabSceneMap[tabId] != null) {
    ({ sceneNum, idx: curIdx } = state.tabSceneMap[tabId]);
    delete state.tabSceneMap[tabId];
  } else if (state.lastCopiedIdx >= 0 && state.lastCopiedIdx < state.prompts.length) {
    curIdx = state.lastCopiedIdx;
    sceneNum = state.prompts[curIdx].scene;
  }

  if (sceneNum < 0) {
    log(`${fileLabel}: сначала нажми Copy на нужной сцене — куда класть файл неизвестно`, "warn");
    return;
  }
  const importKey = downloadImportKey(msg.path || msg.filename || "", target);
  if (state.importedDownloadKeys.has(importKey)) {
    log(`${fileLabel}: duplicate event skipped`, "warn");
    return;
  }
  state.importedDownloadKeys.add(importKey);
  markDownloadSeen({ id: msg.downloadId ?? msg.id, filename: msg.path || msg.filename });

  const tabLabel = tabId != null && tabId >= 0 ? ` [tab ${tabId}]` : "";
  log(`Grok${tabLabel} → сцена ${sceneNum} (${targetLabel(target)}) «${state.scenario}»…`, "ok");

  try {
    const resp = await fetch(`${WEBAPP}/api/extension/import-grok`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: state.scenario,
        source_path: msg.path,
        target,
        scene_number: sceneNum,
      }),
    });
    const r = await resp.json();
    if (!r.ok) {
      state.importedDownloadKeys.delete(importKey);
      log(`Grok import упал: ${r.error || "?"}`, "err");
      return;
    }
    log(`Grok → сцена ${sceneNum} ✓ ${r.file}`, "ok");
    // currentIdx уже двинулся при Copy — не двигаем повторно.
    // Сбрасываем lastCopiedIdx, чтобы следующий случайный download
    // не лёг в ту же сцену.
    state.lastCopiedIdx = -1;
    renderPrompts();
  } catch (e) {
    state.importedDownloadKeys.delete(importKey);
    log(`Grok import: ошибка — ${e.message}`, "err");
  }
}

function importObservedDownload(item, source = "downloads") {
  if (!item || !item.filename) return;
  if (alreadySawDownload(item)) return;

  const target = currentDownloadTarget();
  if (!target) return;

  if (state.generator === "grok") {
    if (!looksLikeGrokDownloadItem(item)) return;
    if (!targetAcceptsItem(target, item)) return;
    markDownloadSeen(item);
    handleGrokDownload({
      path: item.filename,
      filename: basename(item.filename),
      url: item.finalUrl || item.url || "",
      tabId: item.tabId,
    });
  } else {
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
}

function looksLikeRelevantDownload(item) {
  return state.generator === "grok"
    ? looksLikeGrokDownloadItem(item)
    : looksLikeFlowDownloadItem(item);
}

function attachDownloadsWatch() {
  if (!chrome.downloads?.onChanged) return;

  chrome.downloads.onCreated.addListener((item) => {
    if (!item || !item.filename) return;
    if (!looksLikeRelevantDownload(item)) return;
    log(`downloads: замечен файл ${basename(item.filename)}`, "ok");
  });

  chrome.downloads.onChanged.addListener((delta) => {
    if (!delta || delta.id == null) return;
    if (!delta.state || delta.state.current !== "complete") return;
    chrome.downloads.search({ id: delta.id }, (items) => {
      const item = items && items[0];
      if (!item || !item.filename) return;
      if (!looksLikeRelevantDownload(item)) return;
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
      copyAndAdvance(idx);
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

// Копирует промпт сцены idx в буфер, помечает её как done и сдвигает
// выделение на следующую сцену (или сбрасывает в -1, если это была
// последняя). Без авто-копирования следующего промпта — пользователь
// сам жмёт Copy на следующей карточке.
//
// Клик по Copy — это пользовательский жест в фокусе side panel, поэтому
// navigator.clipboard.writeText работает напрямую. Прокси через content
// script (как было раньше) не нужен.
async function copyAndAdvance(idx) {
  if (idx < 0 || idx >= state.prompts.length) return;
  const text = state.prompts[idx].prompt;
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    log(`не удалось скопировать: ${e?.message || e}`, "err");
    return;
  }

  state.doneIdx.add(idx);
  state.lastCopiedIdx = idx;
  state.currentIdx = idx + 1 < state.prompts.length ? idx + 1 : -1;

  // В Grok-режиме запоминаем активную вкладку → эта вкладка генерирует сцену idx.
  // Позволяет вести несколько Grok-вкладок параллельно — каждая скачивает в свою сцену.
  if (state.generator === "grok") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs?.[0]?.id;
      if (tabId != null && tabId >= 0) {
        state.tabSceneMap[tabId] = { sceneNum: state.prompts[idx].scene, idx };
      }
    });
  }

  const sceneNum = state.prompts[idx].scene;
  if (state.currentIdx === -1) {
    log(
      `в буфер: сцена ${sceneNum} — последняя (${text.length} симв.). Все промпты прошли.`,
      "ok"
    );
  } else {
    const nextScene = state.prompts[state.currentIdx].scene;
    log(
      `в буфер: сцена ${sceneNum} (${text.length} симв.) → след. ${nextScene}`,
      "ok"
    );
  }
  renderPrompts();
}

// Ручной откат на предыдущую сцену. Используется если по ошибке нажал
// Copy и хочешь вернуться к незавершённой сцене. Если все промпты прошли
// (currentIdx === -1) — возвращает на последнюю сцену.
function goBack() {
  if (state.prompts.length === 0) return;
  let targetIdx;
  if (state.currentIdx === -1) {
    targetIdx = state.prompts.length - 1;
  } else if (state.currentIdx === 0) {
    log("уже на первой сцене, откатить некуда", "warn");
    return;
  } else {
    targetIdx = state.currentIdx - 1;
  }
  state.currentIdx = targetIdx;
  state.doneIdx.delete(targetIdx);
  renderPrompts();
  const sceneNum = state.prompts[targetIdx].scene;
  log(`откат на сцену ${sceneNum}`, "ok");
}

// ─── Сообщения от background ──────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return;
  if (msg.type === "flow_download_ready") {
    if (state.generator === "grok") {
      handleGrokDownload(msg);
    } else {
      handleFlowDownload(msg, false);
    }
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

$("generator-select").addEventListener("change", (e) => {
  state.generator = e.target.value;
  chrome.storage.local.set({ generator: state.generator });
  updateTogglesForGenerator();
});

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

$("auto-distribute").addEventListener("change", (e) => {
  state.autoDistribute = e.target.checked;
  chrome.storage.local.set({ autoDistribute: state.autoDistribute });
});

$("reload-btn").addEventListener("click", () => {
  loadScenarios();
  if (state.scenario) loadPrompts();
});

$("back-btn").addEventListener("click", () => {
  goBack();
});

$("clear-log").addEventListener("click", () => {
  $("log").innerHTML = "";
});

attachDownloadsWatch();
loadScenarios();
