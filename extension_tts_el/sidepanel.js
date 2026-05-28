// Sidebar расширения TTS EL. Показывает список предложений выбранного
// сценария. Клик по Copy кладёт ТЕКСТ предложения в буфер обмена (чтобы
// вставить в ElevenLabs) и сдвигает выделение на следующее предложение.
// Скачивания mp3 с elevenlabs.* ловит через chrome.downloads и импортирует
// в content/<миф>/voiceover/audio/approved_sentences/<base>_v1.mp3 через
// webapp (см. /api/extension/import-voiceover).
//
// Привязка скачанного mp3 к предложению — по «последнему скопированному»:
// state.lastCopiedIdx запоминается на каждом Copy и НЕ сбрасывается при
// сдвиге currentIdx. Это значит: скопировал sentence_001 → сгенерировал
// в EL → скачал mp3 → он улетел в sentence_001 (даже если currentIdx
// уже на sentence_002).
//
// ВАЖНО: расширение НЕ внедряется на страницу ElevenLabs.

const WEBAPP = "http://127.0.0.1:5000";
const $ = (id) => document.getElementById(id);

const state = {
  scenario: "",
  sentences: [],
  currentIdx: -1,
  doneIdx: new Set(),
  lastCopiedIdx: -1, // привязка скачанного mp3 → этот индекс
  downloadAudio: true,
  seenDownloadIds: new Set(),
  seenDownloadKeys: new Set(),
  importedDownloadKeys: new Set(),
};

const EL_HOST_MARKER = "elevenlabs";

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
    // Показываем только сценарии у которых есть voiceover/texts/. Сценарии
    // вроде только-картинок (has_voiceover=false) для TTS EL бесполезны.
    if (!s.has_voiceover) continue;
    const opt = document.createElement("option");
    opt.value = s.name;
    const cnt = s.sentence_count || 0;
    opt.textContent = `${s.name}${cnt ? ` (${cnt})` : ""}`;
    sel.appendChild(opt);
  }

  // Восстановим прошлый выбор из storage.local.
  chrome.storage.local.get(["scenario", "downloadAudio"], (saved) => {
    if (saved.downloadAudio === false) {
      $("download-audio").checked = false;
      state.downloadAudio = false;
    }
    if (saved.scenario) {
      sel.value = saved.scenario;
      state.scenario = saved.scenario;
      loadSentences();
    }
  });
}

async function loadSentences() {
  if (!state.scenario) {
    state.sentences = [];
    state.currentIdx = -1;
    state.doneIdx = new Set();
    state.lastCopiedIdx = -1;
    renderPrompts();
    return;
  }
  let data;
  try {
    const r = await fetch(
      `${WEBAPP}/api/extension/sentences/${encodeURIComponent(state.scenario)}`
    );
    if (!r.ok) {
      log(`нет voiceover/texts/ для ${state.scenario}`, "err");
      state.sentences = [];
      state.currentIdx = -1;
      state.doneIdx = new Set();
      state.lastCopiedIdx = -1;
      renderPrompts();
      return;
    }
    data = await r.json();
  } catch (e) {
    log(`ошибка загрузки предложений: ${e.message}`, "err");
    return;
  }
  state.sentences = data.sentences || [];
  state.currentIdx = state.sentences.length > 0 ? 0 : -1;
  state.doneIdx = new Set();
  state.lastCopiedIdx = -1;
  renderPrompts();
  log(`загружено ${state.sentences.length} предложений`, "ok");
}

// ─── Импорт скачанного mp3 ─────────────────────────────────────────────────

function basename(path) {
  return String(path || "").split(/[\\/]/).pop() || String(path || "");
}

function getExt(path) {
  const low = basename(path).toLowerCase();
  const idx = low.lastIndexOf(".");
  return idx >= 0 ? low.slice(idx) : "";
}

function looksLikeElDownloadItem(item) {
  const url = String(item?.finalUrl || item?.url || "").toLowerCase();
  const name = basename(item?.filename || "").toLowerCase();
  if (getExt(name) !== ".mp3") return false;
  return url.includes(EL_HOST_MARKER);
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

function targetSentenceForDownload() {
  // Привязка скачанного mp3 к предложению:
  // 1) lastCopiedIdx — последний Copy. Это самый частый случай: «скопировал
  //    sentence_NN → сгенерировал в EL → скачал», даже если currentIdx уже
  //    уехал дальше.
  // 2) Если ни разу не копировали, но currentIdx валидный — берём currentIdx
  //    (например, юзер вручную скачал озвучку первого предложения, не нажав
  //    Copy — редкий, но возможный случай).
  if (state.lastCopiedIdx >= 0 && state.lastCopiedIdx < state.sentences.length) {
    return state.lastCopiedIdx;
  }
  if (state.currentIdx >= 0 && state.currentIdx < state.sentences.length) {
    return state.currentIdx;
  }
  return -1;
}

function downloadImportKey(path) {
  return [
    state.scenario || "",
    String(path || "").toLowerCase(),
  ].join("|");
}

function handleElDownload(msg, fromPending = false) {
  const fileLabel = basename(msg.path || msg.filename || "");

  if (!state.scenario) {
    log(`${fileLabel}: сценарий не выбран — импорт пропущен`, "warn");
    return;
  }
  if (!state.downloadAudio) {
    log(`${fileLabel}: галка «скачать аудио» выключена — импорт пропущен`, "warn");
    return;
  }

  const targetIdx = targetSentenceForDownload();
  if (targetIdx < 0) {
    log(
      `${fileLabel}: непонятно к какому предложению привязать — сначала нажми Copy`,
      "warn"
    );
    return;
  }
  const sentence = state.sentences[targetIdx];
  const base = sentence.base;

  const importKey = downloadImportKey(msg.path || msg.filename || "");
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
    `${fromPending ? "pending" : "EL"} mp3 → ${base}_v1.mp3 для «${state.scenario}»…`,
    "ok"
  );
  chrome.runtime.sendMessage(
    {
      type: "import_voiceover",
      scenario: state.scenario,
      path: msg.path,
      base,
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
      log(`import OK → approved_sentences/${base}_v1.mp3`, "ok");
      if (Array.isArray(r.stuck) && r.stuck.length) {
        log(`не удалось удалить старые: ${r.stuck.join(", ")}`, "warn");
      }
      // Подсветим карточку как approved.
      sentence.approved = "v1";
      renderPrompts();
    }
  );
}

function importObservedDownload(item, source = "downloads") {
  if (!item || !item.filename) return;
  if (alreadySawDownload(item)) return;
  if (!state.downloadAudio) return;
  if (!looksLikeElDownloadItem(item)) return;

  markDownloadSeen(item);
  handleElDownload(
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
    if (!looksLikeElDownloadItem(item)) return;
    log(`downloads: замечен файл ${basename(item.filename)}`, "ok");
  });

  chrome.downloads.onChanged.addListener((delta) => {
    if (!delta || delta.id == null) return;
    if (!delta.state || delta.state.current !== "complete") return;
    chrome.downloads.search({ id: delta.id }, (items) => {
      const item = items && items[0];
      if (!item || !item.filename) return;
      if (!looksLikeElDownloadItem(item)) return;
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
  if (state.sentences.length === 0) {
    root.innerHTML = '<div style="padding:14px;color:#666">Предложений нет (нет voiceover/texts/).</div>';
    updateProgress();
    return;
  }

  state.sentences.forEach((s, idx) => {
    const card = document.createElement("div");
    card.className = "prompt-card";
    if (idx === state.currentIdx) card.classList.add("current");
    if (state.doneIdx.has(idx)) card.classList.add("done");
    if (s.approved) card.classList.add("approved");

    const head = document.createElement("div");
    head.className = "prompt-head";
    const approvedHtml = s.approved
      ? `<span class="approved-flag" title="approved_sentences/${escapeAttr(s.base)}_${escapeAttr(s.approved)}.mp3">★ ${escapeHtml(s.approved)}</span>`
      : `<span class="approved-flag" title="${escapeAttr(s.base)}">${escapeHtml(s.base)}</span>`;
    head.innerHTML = `
      <span class="scene-num">#${s.scene || idx + 1}</span>
      ${approvedHtml}
      <button class="copy-btn" data-idx="${idx}">Copy</button>
    `;
    card.appendChild(head);

    if (s.text) {
      const txt = document.createElement("div");
      txt.className = "text";
      txt.textContent = s.text;
      card.appendChild(txt);
    }

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
  const total = state.sentences.length;
  if (!total) {
    $("progress").textContent = "—";
    return;
  }
  const done = state.doneIdx.size;
  const cur = state.currentIdx >= 0 ? state.currentIdx + 1 : "—";
  const approved = state.sentences.filter((s) => s.approved).length;
  $("progress").textContent = `${done}/${total} (текущая: ${cur}) · approved ${approved}`;
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

// Копирует текст предложения idx в буфер, помечает его как done, фиксирует
// lastCopiedIdx (привязка будущего mp3) и сдвигает выделение на следующее
// предложение.
async function copyAndAdvance(idx) {
  if (idx < 0 || idx >= state.sentences.length) return;
  const text = state.sentences[idx].text;
  if (!text) {
    log(`sentence_${idx + 1}: пустой текст — копировать нечего`, "warn");
    return;
  }

  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    log(`не удалось скопировать: ${e?.message || e}`, "err");
    return;
  }

  state.doneIdx.add(idx);
  state.lastCopiedIdx = idx;
  state.currentIdx = idx + 1 < state.sentences.length ? idx + 1 : -1;

  const base = state.sentences[idx].base;
  if (state.currentIdx === -1) {
    log(
      `в буфер: ${base} — последнее (${text.length} симв.). Все предложения прошли.`,
      "ok"
    );
  } else {
    const nextBase = state.sentences[state.currentIdx].base;
    log(
      `в буфер: ${base} (${text.length} симв.) → след. ${nextBase}`,
      "ok"
    );
  }
  renderPrompts();
}

// Ручной откат на предыдущее предложение. Если все прошли (currentIdx === -1)
// — возвращает на последнее.
function goBack() {
  if (state.sentences.length === 0) return;
  let targetIdx;
  if (state.currentIdx === -1) {
    targetIdx = state.sentences.length - 1;
  } else if (state.currentIdx === 0) {
    log("уже на первом предложении, откатить некуда", "warn");
    return;
  } else {
    targetIdx = state.currentIdx - 1;
  }
  state.currentIdx = targetIdx;
  state.doneIdx.delete(targetIdx);
  state.lastCopiedIdx = targetIdx - 1; // привязку тоже откатываем
  renderPrompts();
  const base = state.sentences[targetIdx].base;
  log(`откат на ${base}`, "ok");
}

// ─── Сообщения от background ──────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return;
  if (msg.type === "el_download_ready") {
    handleElDownload(msg, false);
  }
});

// Если sidepanel был закрыт когда EL скачал mp3 — подберём из storage.
chrome.storage.local.get(["pendingElDownload"], (saved) => {
  const pz = saved.pendingElDownload;
  if (!pz || !pz.path) return;
  // Считаем «свежим» если меньше 2 минут назад.
  if (Date.now() - (pz.ts || 0) > 120_000) return;
  log(`найден pending download: ${basename(pz.path)}`, "warn");
  chrome.storage.local.remove("pendingElDownload");
  handleElDownload(pz, true);
});

// ─── UI события ────────────────────────────────────────────────────────────

$("scenario-select").addEventListener("change", (e) => {
  state.scenario = e.target.value;
  chrome.storage.local.set({ scenario: state.scenario });
  loadSentences();
});

$("download-audio").addEventListener("change", (e) => {
  state.downloadAudio = e.target.checked;
  chrome.storage.local.set({ downloadAudio: state.downloadAudio });
});

$("reload-btn").addEventListener("click", () => {
  loadScenarios();
  if (state.scenario) loadSentences();
});

$("back-btn").addEventListener("click", () => {
  goBack();
});

$("clear-log").addEventListener("click", () => {
  $("log").innerHTML = "";
});

attachDownloadsWatch();
loadScenarios();
