// Service worker расширения BOGI Flow Promptr.
//
// Делает три вещи:
//   1) Открывает sidepanel при клике на иконку (через setPanelBehavior).
//   2) Слушает chrome.downloads и ловит zip-архивы из Google Flow —
//      когда такой скачивается, шлёт sidepanel сообщение zip_ready.
//   3) Принимает от sidepanel запрос distribute и идёт за webapp на
//      127.0.0.1:5000, чтобы тот запустил automation/distribute_images.py.

const WEBAPP = "http://127.0.0.1:5000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((e) => console.warn("setPanelBehavior:", e));
});

// ─── Перехват zip-архивов от Flow ─────────────────────────────────────────
// Проблема: chrome.downloads.onCreated отдаёт `filename` ещё пустым.
// Нормальный способ — сначала запомнить id, потом дождаться onChanged со
// state.complete и взять `filename` через chrome.downloads.search.

const watchedDownloads = new Set();

function looksLikeFlowZip(item) {
  const url = (item.finalUrl || item.url || "").toLowerCase();
  const fname = (item.filename || "").toLowerCase();
  const isZip = fname.endsWith(".zip") || url.includes(".zip");
  if (!isZip) return false;
  // Flow складывает архивы в storage.googleapis.com / aisandbox / labs.google.
  return (
    url.includes("labs.google") ||
    url.includes("aisandbox") ||
    url.includes("storage.googleapis.com") ||
    url.includes("flow")
  );
}

chrome.downloads.onCreated.addListener((item) => {
  if (looksLikeFlowZip(item)) {
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

  // Шлём sidepanel — он уже знает текущий выбранный сценарий.
  chrome.runtime
    .sendMessage({ type: "zip_ready", path: item.filename, url: item.finalUrl || item.url })
    .catch(() => {
      // Sidepanel может быть закрыт. Ничего страшного — пользователь
      // его откроет, увидит, что zip скачался, и нажмёт «Распределить».
      chrome.storage.local.set({ pendingZip: { path: item.filename, ts: Date.now() } });
    });
});

// ─── Запуск distribute_images.py через webapp ─────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "distribute") {
    fetch(`${WEBAPP}/api/extension/distribute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: msg.scenario, archive_path: msg.path }),
    })
      .then((r) => r.json().then((j) => ({ status: r.status, body: j })))
      .then(({ status, body }) => sendResponse({ ok: status >= 200 && status < 300, body }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true; // async response
  }
  return false;
});
