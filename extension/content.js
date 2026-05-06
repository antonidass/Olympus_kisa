// Content script. Внедряется на labs.google/*.
//
// Задачи:
//   1) Поймать клик пользователя по кнопке «Generate» в Flow и сообщить
//      sidepanel-у, чтобы тот переключился на следующий промпт и
//      автоматически положил его в буфер.
//   2) Поймать ручной клик по «Download Project», чтобы background заранее
//      вооружился и подхватил следующее скачивание как flow-download.
//   3) Также детектим клавиатурный сабмит (Enter / Ctrl+Enter в prompt-инпуте) —
//      Flow позволяет отправлять промпт с клавиатуры, не нажимая кнопку.
//
// Никаких click()/dispatchEvent на страницу — мы только слушаем настоящие
// клики пользователя, чтобы Flow ничего не заподозрил.

const TRIGGERS = [
  "generate",
  "create",
  "сгенерировать",
  "создать",
  "go",
  "submit",
  "send",
  "run",
  "отправить",
  "produce",
];
const DOWNLOAD_TRIGGERS = [
  "download project",
  "download",
  "скачать проект",
  "скачать",
];

function notifyGenerateClicked() {
  try {
    chrome.runtime.sendMessage({ type: "generate_clicked" });
  } catch (_) {}
}

// Защита от двойного срабатывания, когда клавиатурный сабмит (Enter)
// дополнительно дёргает click() на submit-кнопке внутри формы.
let lastNotifyTs = 0;
function notifyGenerateClickedDeduped() {
  const now = Date.now();
  if (now - lastNotifyTs < 600) return;
  lastNotifyTs = now;
  notifyGenerateClicked();
}

function isPromptInputArea(el) {
  // «Внутри prompt-инпута» = у элемента есть предок, в поддереве которого
  // лежит textarea / contenteditable / role=textbox. Используется для:
  //   (а) icon-only submit-кнопок без текста (стрелка ↑/→ во Flow),
  //   (б) детекции Enter-сабмита в самом инпуте.
  let p = el;
  for (let i = 0; i < 8 && p; i += 1) {
    if (p.querySelector && p.querySelector("textarea, [contenteditable='true'], [role='textbox']")) {
      return true;
    }
    p = p.parentElement;
  }
  return false;
}

function looksLikeGenerate(el) {
  if (!el || !el.tagName) return false;
  const tag = el.tagName.toLowerCase();
  const role = (el.getAttribute("role") || "").toLowerCase();
  if (tag !== "button" && role !== "button") return false;

  const text = (el.innerText || el.textContent || "").trim().toLowerCase();
  const aria = (el.getAttribute("aria-label") || "").toLowerCase();
  const title = (el.getAttribute("title") || "").toLowerCase();
  const testid = (el.getAttribute("data-testid") || "").toLowerCase();

  const fields = [text, aria, title, testid];
  for (const t of TRIGGERS) {
    for (const f of fields) {
      if (!f) continue;
      if (f === t || f.startsWith(t + " ") || f.includes(t)) return true;
    }
  }

  // Icon-only submit-кнопка: ни text, ни aria, ни testid не содержат триггера,
  // но это явная «send prompt» кнопка во Flow (стрелка ↑/→ справа от инпута).
  // Признаки: пустой видимый текст + есть SVG внутри + рядом prompt-инпут
  // (textarea / contenteditable) в общем контейнере. Дополнительный bonus —
  // type="submit" или ancestor=form, но не обязательно (некоторые UI-библиотеки
  // не ставят type на иконочные кнопки).
  if (tag === "button" && !text) {
    const hasSvg = !!el.querySelector("svg");
    if (hasSvg && isPromptInputArea(el)) return true;
  }

  return false;
}

function pathElements(e) {
  const path = typeof e.composedPath === "function" ? e.composedPath() : [];
  const out = [];
  for (const node of path) {
    if (node && node.nodeType === Node.ELEMENT_NODE) out.push(node);
  }
  if (out.length) return out;

  const fallback = [];
  let el = e.target;
  for (let i = 0; i < 12 && el; i += 1) {
    fallback.push(el);
    el = el.parentElement;
  }
  return fallback;
}

function elementWords(el) {
  return {
    text: (el.innerText || el.textContent || "").trim().toLowerCase(),
    aria: (el.getAttribute("aria-label") || "").toLowerCase(),
    title: (el.getAttribute("title") || "").toLowerCase(),
  };
}

function looksLikeDownloadProject(el) {
  if (!el || !el.tagName) return false;
  const tag = el.tagName.toLowerCase();
  const role = (el.getAttribute("role") || "").toLowerCase();
  const clickable =
    tag === "button" ||
    tag === "a" ||
    role === "button" ||
    role === "menuitem" ||
    role === "option";
  if (!clickable) return false;

  const { text, aria, title } = elementWords(el);
  const hay = `${text}\n${aria}\n${title}`;
  return DOWNLOAD_TRIGGERS.some((t) => hay.includes(t));
}

// Запись в буфер по запросу из sidepanel. Side panel сам не может надёжно
// дёрнуть navigator.clipboard.writeText — у него нет document focus, когда
// пользователь работает на странице Flow, и Chrome возвращает NotAllowedError.
// Content script же бежит на сфокусированной вкладке Flow, поэтому write идёт
// без проблем — это и есть штатный способ доставлять промпт в clipboard
// после клика Generate. Отвечаем sendResponse-ом, чтобы sidepanel мог
// упасть на fallback (навигатор-клипборд) если что-то пошло не так.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.type !== "clipboard_write") return;
  const text = String(msg.text || "");
  if (!text) {
    sendResponse({ ok: false, error: "empty text" });
    return;
  }
  navigator.clipboard.writeText(text).then(
    () => sendResponse({ ok: true, length: text.length }),
    (err) =>
      sendResponse({
        ok: false,
        error: String((err && err.message) || err || "clipboard write failed"),
      })
  );
  return true; // оставляем канал открытым для async sendResponse
});

document.addEventListener(
  "click",
  (e) => {
    for (const el of pathElements(e)) {
      if (looksLikeGenerate(el)) {
        notifyGenerateClickedDeduped();
        return;
      }
      if (looksLikeDownloadProject(el)) {
        try {
          chrome.runtime.sendMessage({
            type: "flow_download_clicked",
            label: elementWords(el).text || elementWords(el).aria || "download project",
            href: location.href,
          });
        } catch (_) {}
        return;
      }
    }
  },
  true
);

// Клавиатурный сабмит: Enter (без Shift) или Ctrl/Cmd+Enter внутри
// prompt-инпута Flow считается отправкой промпта. Слушаем keydown в
// capture-фазе чтобы успеть до того, как Flow обработает ввод.
//
// Shift+Enter — это перенос строки, не сабмит, его пропускаем.
// Дедуп с click через общий lastNotifyTs защищает от двойного уведомления,
// если Flow сам дёргает .click() на кнопке после клавиатурного Enter.
document.addEventListener(
  "keydown",
  (e) => {
    if (e.key !== "Enter" || e.shiftKey) return;

    const target = e.target;
    if (!target || !target.tagName) return;
    const tag = target.tagName.toLowerCase();
    const role = (target.getAttribute && target.getAttribute("role")) || "";
    const isPromptInput =
      tag === "textarea" ||
      target.isContentEditable === true ||
      role.toLowerCase() === "textbox";
    if (!isPromptInput) return;

    // Подтверждаем, что инпут действительно сидит в области с prompt-кнопкой
    // (а не, скажем, в поле поиска / комментарии). isPromptInputArea для самого
    // инпута тривиально true (он сам — textarea), поэтому проверяем родителя.
    if (!isPromptInputArea(target.parentElement || target)) return;

    notifyGenerateClickedDeduped();
  },
  true
);
