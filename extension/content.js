// Content script. Внедряется на labs.google/*.
//
// Единственная задача: поймать клик пользователя по кнопке «Generate» в
// Flow и сообщить sidepanel-у, чтобы тот переключился на следующий промпт
// и автоматически положил его в буфер.
//
// Никаких click()/dispatchEvent на страницу — мы только слушаем настоящие
// клики пользователя, чтобы Flow ничего не заподозрил.

const TRIGGERS = ["generate", "create", "сгенерировать", "создать", "go"];

function looksLikeGenerate(el) {
  if (!el || !el.tagName) return false;
  const tag = el.tagName.toLowerCase();
  if (tag !== "button" && el.getAttribute("role") !== "button") return false;
  const text = (el.innerText || el.textContent || "").trim().toLowerCase();
  const aria = (el.getAttribute("aria-label") || "").toLowerCase();
  const title = (el.getAttribute("title") || "").toLowerCase();
  for (const t of TRIGGERS) {
    if (text === t || text.startsWith(t + " ") || aria === t || aria.includes(t) || title.includes(t)) {
      return true;
    }
  }
  return false;
}

document.addEventListener(
  "click",
  (e) => {
    let el = e.target;
    for (let i = 0; i < 6 && el; i += 1) {
      if (looksLikeGenerate(el)) {
        try {
          chrome.runtime.sendMessage({ type: "generate_clicked" });
        } catch (_) {}
        return;
      }
      el = el.parentElement;
    }
  },
  true
);
