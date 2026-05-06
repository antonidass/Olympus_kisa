// Service worker расширения BOGI Flow Promptr.
//
// Делает три вещи:
//   1) Открывает sidepanel при клике на иконку (через setPanelBehavior).
//   2) Слушает chrome.downloads и ловит скачивания из Google Flow —
//      когда такой файл докачивается, шлёт sidepanel сообщение flow_download_ready.
//   3) Принимает от sidepanel запрос import_download и идёт за webapp на
//      127.0.0.1:5000, чтобы тот импортировал файл в content/<scenario>/images|video.

const WEBAPP = "http://127.0.0.1:5000";
const FLOW_DOWNLOAD_ARM_MS = 120_000;
let expectFlowDownloadUntil = 0;
const FLOW_DOWNLOAD_ARM_KEY = "flowDownloadArmUntil";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((e) => console.warn("setPanelBehavior:", e));
});

// ─── Перехват скачиваний от Flow ──────────────────────────────────────────
// Проблема: chrome.downloads.onCreated отдаёт `filename` ещё пустым.
// Нормальный способ — сначала запомнить id, потом дождаться onChanged со
// state.complete и взять `filename` через chrome.downloads.search.

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

function armFlowDownload(ms = FLOW_DOWNLOAD_ARM_MS) {
  expectFlowDownloadUntil = Date.now() + ms;
  chrome.storage.local.set({ [FLOW_DOWNLOAD_ARM_KEY]: expectFlowDownloadUntil }).catch(() => {});
}

function isFlowDownloadArmed() {
  return Date.now() < expectFlowDownloadUntil;
}

async function getFlowDownloadArmUntil() {
  if (expectFlowDownloadUntil > Date.now()) return expectFlowDownloadUntil;
  try {
    const saved = await chrome.storage.local.get([FLOW_DOWNLOAD_ARM_KEY]);
    const until = Number(saved?.[FLOW_DOWNLOAD_ARM_KEY] || 0);
    if (until > Date.now()) {
      expectFlowDownloadUntil = until;
      return until;
    }
  } catch (_) {}
  return 0;
}

async function isFlowDownloadArmedPersistent() {
  return (await getFlowDownloadArmUntil()) > Date.now();
}

function clearFlowDownloadArm() {
  expectFlowDownloadUntil = 0;
  chrome.storage.local.remove(FLOW_DOWNLOAD_ARM_KEY).catch(() => {});
}

function looksLikeFlowDownload(item) {
  const url = (item.finalUrl || item.url || "").toLowerCase();
  const fname = (item.filename || "").toLowerCase();
  if (!hasKnownFlowExt(fname) && !hasKnownFlowExt(url)) return false;
  // Flow складывает архивы в storage.googleapis.com / aisandbox / labs.google.
  return (
    url.includes("labs.google") ||
    url.includes("aisandbox") ||
    url.includes("storage.googleapis.com") ||
    url.includes("flow")
  );
}

chrome.downloads.onCreated.addListener(async (item) => {
  if (looksLikeFlowDownload(item) || await isFlowDownloadArmedPersistent()) {
    watchedDownloads.add(item.id);
  }
});

chrome.downloads.onChanged.addListener(async (delta) => {
  const armed = await isFlowDownloadArmedPersistent();
  if (!watchedDownloads.has(delta.id) && !armed) return;
  if (!delta.state || delta.state.current !== "complete") return;
  watchedDownloads.delete(delta.id);

  const items = await chrome.downloads.search({ id: delta.id });
  const item = items && items[0];
  if (!item || !item.filename) return;
  if (!looksLikeFlowDownload(item) && !armed) return;
  const payload = {
    type: "flow_download_ready",
    path: item.filename,
    url: item.finalUrl || item.url,
    filename: item.filename.split(/[\\/]/).pop() || item.filename,
  };

  // Шлём sidepanel — он уже знает текущий выбранный сценарий и режим.
  chrome.runtime
    .sendMessage(payload)
    .catch(() => {
      // Sidepanel может быть закрыт. Сохраняем событие — панель подберёт его
      // при следующем открытии и сама решит, импортировать ли файл.
      chrome.storage.local.set({
        pendingFlowDownload: {
          ...payload,
          ts: Date.now(),
        },
      });
    });

  // Один ручной клик Download Project должен подхватить одно ближайшее скачивание.
  clearFlowDownloadArm();
});

// ─── Импорт скачанного файла через webapp ─────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "flow_download_clicked") {
    armFlowDownload();
    chrome.runtime.sendMessage({
      type: "flow_download_armed",
      label: msg.label || "download project",
    }).catch(() => {});
    sendResponse?.({ ok: true });
    return false;
  }

  if (msg && msg.type === "import_download") {
    fetch(`${WEBAPP}/api/extension/import-download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: msg.scenario,
        source_path: msg.path,
        target: msg.target,
      }),
    })
      .then((r) => r.json().then((j) => ({ status: r.status, body: j })))
      .then(({ status, body }) => sendResponse({ ok: status >= 200 && status < 300, body }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async response
  }
  return false;
});
