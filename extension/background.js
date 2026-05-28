// Service worker расширения BOGI Promptr.
//
// Делает две вещи:
//   1) Открывает sidepanel при клике на иконку.
//   2) Слушает chrome.downloads и ловит скачивания из Google Flow —
//      когда такой файл докачивается, шлёт sidepanel сообщение
//      flow_download_ready. Sidepanel импортирует файл в content/<миф>/
//      через webapp.
//
// ВАЖНО: на страницу Flow расширение НЕ внедряется. Никакого content
// script, никаких click/keydown-листенеров на странице Flow. Скачивания
// определяются исключительно по URL/host в chrome.downloads — Flow
// считает читание DOM автоматизацией и за это наказывает, поэтому не
// трогаем его страницу вообще.

const WEBAPP = "http://127.0.0.1:5000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((e) => console.warn("setPanelBehavior:", e));
});

// ─── Перехват скачиваний от Flow ──────────────────────────────────────────
// chrome.downloads.onCreated отдаёт filename ещё пустым. Запоминаем id,
// дожидаемся onChanged со state.complete и берём filename через search.

const watchedDownloads = new Set();
const FLOW_MEDIA_EXTS = [
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

function hasKnownFlowExt(value) {
  const low = String(value || "").toLowerCase();
  return FLOW_MEDIA_EXTS.some((ext) => low.endsWith(ext) || low.includes(ext));
}

function looksLikeFlowDownload(item) {
  const url = (item.finalUrl || item.url || "").toLowerCase();
  const fname = (item.filename || "").toLowerCase();
  if (!hasKnownFlowExt(fname) && !hasKnownFlowExt(url)) return false;
  // Flow складывает архивы в storage.googleapis.com / aisandbox / labs.google.
  // Grok отдаёт файлы через grok.com / x.ai.
  return (
    url.includes("labs.google") ||
    url.includes("aisandbox") ||
    url.includes("storage.googleapis.com") ||
    url.includes("flow") ||
    url.includes("grok.com") ||
    url.includes("x.ai")
  );
}

chrome.downloads.onCreated.addListener((item) => {
  if (looksLikeFlowDownload(item)) {
    watchedDownloads.add(item.id);
  }
});

chrome.downloads.onChanged.addListener(async (delta) => {
  if (!watchedDownloads.has(delta.id)) return;
  if (!delta.state || delta.state.current !== "complete") return;
  watchedDownloads.delete(delta.id);

  const items = await chrome.downloads.search({ id: delta.id });
  const item = items && items[0];
  if (!item || !item.filename) return;
  if (!looksLikeFlowDownload(item)) return;
  const payload = {
    type: "flow_download_ready",
    downloadId: item.id,
    path: item.filename,
    url: item.finalUrl || item.url,
    filename: item.filename.split(/[\\/]/).pop() || item.filename,
  };

  // Шлём sidepanel — он уже знает текущий выбранный сценарий и режим.
  chrome.runtime.sendMessage(payload).catch(() => {
    // Sidepanel может быть закрыт. Сохраняем событие — панель подберёт его
    // при следующем открытии и сама решит, импортировать ли файл.
    chrome.storage.local.set({
      pendingFlowDownload: {
        ...payload,
        ts: Date.now(),
      },
    });
  });
});

// ─── Импорт скачанного файла через webapp ─────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "import_download") {
    fetch(`${WEBAPP}/api/extension/import-download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: msg.scenario,
        source_path: msg.path,
        target: msg.target,
        // auto_distribute=true заставляет webapp после распаковки запустить
        // соответствующий distribute_*.py (images / stickers / videos) и
        // вернуть его результат в поле `distribute`.
        auto_distribute: msg.autoDistribute !== false, // default true
      }),
    })
      .then((r) => r.json().then((j) => ({ status: r.status, body: j })))
      .then(({ status, body }) =>
        sendResponse({ ok: status >= 200 && status < 300, body })
      )
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async response
  }
  return false;
});
