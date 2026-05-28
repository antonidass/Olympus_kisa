// Service worker расширения TTS EL.
//
// Делает две вещи:
//   1) Открывает sidepanel при клике на иконку.
//   2) Слушает chrome.downloads и ловит mp3-скачивания с elevenlabs.* —
//      когда такой файл докачивается, шлёт sidepanel сообщение
//      el_download_ready. Sidepanel импортирует mp3 в
//      content/<миф>/voiceover/audio/approved_sentences/<base>_v1.mp3
//      через webapp (см. /api/extension/import-voiceover).
//
// ВАЖНО: на страницу ElevenLabs расширение НЕ внедряется. Никакого content
// script, никаких click/keydown-листенеров. Скачивания определяются
// исключительно по URL/host в chrome.downloads.

const WEBAPP = "http://127.0.0.1:5000";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((e) => console.warn("setPanelBehavior:", e));
});

// ─── Перехват скачиваний от ElevenLabs ────────────────────────────────────
// chrome.downloads.onCreated отдаёт filename ещё пустым. Запоминаем id,
// дожидаемся onChanged со state.complete и берём filename через search.

const watchedDownloads = new Set();

function isMp3(value) {
  return String(value || "").toLowerCase().endsWith(".mp3");
}

function looksLikeElDownload(item) {
  const url = (item.finalUrl || item.url || "").toLowerCase();
  const fname = (item.filename || "").toLowerCase();
  if (!isMp3(fname) && !isMp3(url)) return false;
  // ElevenLabs ходит через elevenlabs.io / api.us.elevenlabs.io /
  // eleven-public-prod.s3.amazonaws.com — везде есть подстрока "elevenlabs".
  return url.includes("elevenlabs");
}

chrome.downloads.onCreated.addListener((item) => {
  if (looksLikeElDownload(item)) {
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
  if (!looksLikeElDownload(item)) return;
  const payload = {
    type: "el_download_ready",
    downloadId: item.id,
    path: item.filename,
    url: item.finalUrl || item.url,
    filename: item.filename.split(/[\\/]/).pop() || item.filename,
  };

  chrome.runtime.sendMessage(payload).catch(() => {
    // Sidepanel может быть закрыт. Сохраняем — панель подберёт при
    // следующем открытии и сама решит, импортировать ли файл.
    chrome.storage.local.set({
      pendingElDownload: {
        ...payload,
        ts: Date.now(),
      },
    });
  });
});

// ─── Импорт скачанного mp3 через webapp ───────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "import_voiceover") {
    fetch(`${WEBAPP}/api/extension/import-voiceover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: msg.scenario,
        source_path: msg.path,
        base: msg.base,
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
