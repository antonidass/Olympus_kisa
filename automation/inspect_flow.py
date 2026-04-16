"""
Инспектор страницы Flow — собирает все интерактивные элементы
(textarea, input, contenteditable, button) с их атрибутами.

Запуск:
    python automation/inspect_flow.py

После запуска:
    1. В открывшемся окне залогинься в Google и дождись полной загрузки Flow-проекта.
    2. Если надо — наведи мышь на поле ввода промпта, кликни в него.
    3. Нажми Enter в консоли — скрипт соберёт и распечатает элементы.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

FLOW_URL = "https://labs.google/fx/ru/tools/flow/project/7bd82873-3936-4fc2-8687-f4284b363c1f"
PROFILE_DIR = Path(__file__).parent / ".browser_profile"

INSPECT_JS = r"""
() => {
    const result = { textareas: [], inputs: [], editables: [], buttons: [], images: [] };

    const describe = (el) => {
        const rect = el.getBoundingClientRect();
        return {
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            name: el.getAttribute('name') || null,
            placeholder: el.getAttribute('placeholder') || null,
            aria_label: el.getAttribute('aria-label') || null,
            data_testid: el.getAttribute('data-testid') || null,
            role: el.getAttribute('role') || null,
            type: el.getAttribute('type') || null,
            class: (el.className && typeof el.className === 'string') ? el.className.slice(0, 120) : null,
            text: (el.innerText || '').trim().slice(0, 80),
            visible: rect.width > 0 && rect.height > 0,
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            w: Math.round(rect.width),
            h: Math.round(rect.height),
        };
    };

    document.querySelectorAll('textarea').forEach(e => result.textareas.push(describe(e)));
    document.querySelectorAll('input').forEach(e => result.inputs.push(describe(e)));
    document.querySelectorAll('[contenteditable="true"]').forEach(e => result.editables.push(describe(e)));
    document.querySelectorAll('button').forEach(e => result.buttons.push(describe(e)));
    document.querySelectorAll('img').forEach(e => {
        const rect = e.getBoundingClientRect();
        if (rect.width > 50 && rect.height > 50) {
            result.images.push({
                src: (e.src || '').slice(0, 120),
                alt: e.alt || null,
                w: Math.round(rect.width),
                h: Math.round(rect.height),
            });
        }
    });
    return result;
}
"""


def dump(title, items, keys):
    print(f"\n=== {title} ({len(items)}) ===")
    for i, it in enumerate(items):
        if not it.get("visible", True):
            continue
        parts = [f"{k}={it.get(k)!r}" for k in keys if it.get(k)]
        print(f"  [{i}] {' | '.join(parts)}")


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        print(f"🌐 Открываю {FLOW_URL}")
        page.goto(FLOW_URL, wait_until="domcontentloaded", timeout=60_000)

        print("\n⏸  Залогинься (если нужно) и дождись загрузки Flow-проекта.")
        print("   Переключись в режим создания ВИДЕО.")
        print("   Когда видишь слоты для кадров — нажми Enter.")
        input("   Нажми Enter для ПЕРВОГО сбора элементов... ")

        data = page.evaluate(INSPECT_JS)
        dump("TEXTAREA", data["textareas"],
             ["placeholder", "aria_label", "data_testid", "name", "id", "class", "w", "h"])
        dump("INPUT", data["inputs"],
             ["type", "placeholder", "aria_label", "data_testid", "name", "id", "class", "w", "h"])
        dump("CONTENTEDITABLE", data["editables"],
             ["aria_label", "data_testid", "role", "id", "class", "text", "w", "h"])
        dump("BUTTON (видимые)", data["buttons"],
             ["text", "aria_label", "data_testid", "id", "class", "w", "h"])
        print(f"\n=== IMG (>50px, {len(data['images'])}) ===")
        for img in data["images"][:30]:
            print(f"  src={img['src'][:80]}  {img['w']}x{img['h']}  alt={img['alt']!r}")

        # ── ПРОХОД 2: Целевая инспекция видео-панели ──
        print("\n" + "="*60)
        print("ПРОХОД 2: ВИДЕО-ПАНЕЛЬ")
        print("  1. Переключись на вкладку «Видео» (не «Изображение»)")
        print("  2. Убедись что видишь секцию «Кадры»")
        print("  3. НЕ кликай пока на слот кадра")
        input("   Нажми Enter... ")

        video_panel = page.evaluate(r"""
        () => {
            const result = {
                near_kadry: [],
                bottom_clickable: [],
                small_elements: [],
                all_text_labels: [],
            };

            const describe = (el) => {
                const rect = el.getBoundingClientRect();
                const cs = window.getComputedStyle(el);
                return {
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    role: el.getAttribute('role') || null,
                    aria_label: el.getAttribute('aria-label') || null,
                    tabindex: el.getAttribute('tabindex'),
                    class: (el.className && typeof el.className === 'string') ? el.className.slice(0, 100) : null,
                    text: (el.innerText || '').trim().slice(0, 60),
                    title: el.getAttribute('title') || null,
                    cursor: cs.cursor,
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height),
                    children: el.children.length,
                    hasImg: el.querySelector('img') ? true : false,
                    hasSvg: el.querySelector('svg') ? true : false,
                };
            };

            // 1. Найти элемент с текстом "Кадры" и собрать всё рядом
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const txt = walker.currentNode.textContent.trim();
                if (txt === 'Кадры' || txt === 'Кадры ') {
                    let ancestor = walker.currentNode.parentElement;
                    // Поднимаемся на 3 уровня
                    for (let i = 0; i < 3 && ancestor && ancestor !== document.body; i++) {
                        ancestor = ancestor.parentElement;
                    }
                    if (ancestor) {
                        // Собираем ВСЕ потомки этого предка
                        ancestor.querySelectorAll('*').forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                result.near_kadry.push(describe(el));
                            }
                        });
                    }
                    break;
                }
            }

            // 2. Все кликабельные элементы в нижней части экрана (y > 500)
            const clickable = document.querySelectorAll(
                'button, [role="button"], [tabindex="0"], [tabindex="-1"]'
            );
            clickable.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.y > 500 && rect.width > 0 && rect.height > 0) {
                    result.bottom_clickable.push(describe(el));
                }
            });

            // 3. Все элементы 30-200px (потенциальные слоты кадров)
            document.querySelectorAll('div, button, span, a, [role]').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width >= 30 && rect.width <= 200
                    && rect.height >= 30 && rect.height <= 200
                    && rect.y > 500) {
                    const cs = window.getComputedStyle(el);
                    if (cs.cursor === 'pointer' || el.getAttribute('tabindex') !== null
                        || el.tagName === 'BUTTON' || el.getAttribute('role')) {
                        result.small_elements.push(describe(el));
                    }
                }
            });

            // 4. Все текстовые лейблы в нижней панели
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.y > 500 && el.children.length === 0) {
                    const txt = (el.innerText || el.textContent || '').trim();
                    if (txt && txt.length < 40 && txt.length > 0) {
                        result.all_text_labels.push({
                            text: txt,
                            tag: el.tagName.toLowerCase(),
                            x: Math.round(rect.x), y: Math.round(rect.y),
                            w: Math.round(rect.width), h: Math.round(rect.height),
                        });
                    }
                }
            });

            return result;
        }
        """)

        print(f"\n=== ОКОЛО «Кадры» ({len(video_panel['near_kadry'])} элементов) ===")
        for i, el in enumerate(video_panel['near_kadry'][:50]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'aria_label', 'tabindex', 'cursor', 'title', 'text']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            if el.get('hasImg'):
                parts.append("HAS_IMG")
            if el.get('hasSvg'):
                parts.append("HAS_SVG")
            parts.append(f"children={el['children']}")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== КЛИКАБЕЛЬНЫЕ ВНИЗУ ({len(video_panel['bottom_clickable'])}) ===")
        for i, el in enumerate(video_panel['bottom_clickable'][:30]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'aria_label', 'tabindex', 'cursor', 'title', 'text']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            if el.get('hasImg'):
                parts.append("HAS_IMG")
            if el.get('hasSvg'):
                parts.append("HAS_SVG")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== МАЛЕНЬКИЕ ЭЛЕМЕНТЫ 30-200px ВНИЗУ ({len(video_panel['small_elements'])}) ===")
        for i, el in enumerate(video_panel['small_elements'][:20]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'aria_label', 'tabindex', 'cursor', 'text', 'class']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== ТЕКСТОВЫЕ ЛЕЙБЛЫ ВНИЗУ ({len(video_panel['all_text_labels'])}) ===")
        for i, lbl in enumerate(video_panel['all_text_labels'][:40]):
            print(f"  [{i}] '{lbl['text']}' <{lbl['tag']}> {lbl['w']}x{lbl['h']} @({lbl['x']},{lbl['y']})")

        # ── ПРОХОД 3: После клика на «Первый кадр» — инспекция пикера ──
        print("\n" + "="*60)
        print("ПРОХОД 3: ПИКЕР ПЕРВОГО КАДРА")
        print("  1. Кликни на «Первый кадр» (квадрат ~50x50)")
        print("  2. Должен открыться список/пикер с названиями изображений")
        print("  3. НЕ выбирай ничего из списка")
        input("   Нажми Enter когда пикер открыт... ")

        picker_data = page.evaluate(r"""
        () => {
            const result = { list_items: [], all_clickable: [], menus: [], popups: [] };

            const describe = (el) => {
                const rect = el.getBoundingClientRect();
                const cs = window.getComputedStyle(el);
                return {
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || null,
                    aria_label: el.getAttribute('aria-label') || null,
                    data_testid: el.getAttribute('data-testid') || null,
                    tabindex: el.getAttribute('tabindex'),
                    class: (el.className && typeof el.className === 'string') ? el.className.slice(0, 120) : null,
                    text: (el.innerText || '').trim().slice(0, 80),
                    cursor: cs.cursor,
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height),
                    children: el.children.length,
                    hasImg: el.querySelector('img') ? true : false,
                };
            };

            // 1. Все li, [role=option], [role=menuitem], [role=listitem]
            document.querySelectorAll(
                'li, [role="option"], [role="menuitem"], [role="listitem"], [role="row"]'
            ).forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    result.list_items.push(describe(el));
                }
            });

            // 2. Все кликабельные элементы с текстом (потенциальные пункты списка)
            document.querySelectorAll('div, span, a, button, li').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width < 10 || rect.height < 10) return;
                const cs = window.getComputedStyle(el);
                const text = (el.innerText || '').trim();
                if (text && text.length > 3 && text.length < 100
                    && (cs.cursor === 'pointer' || el.getAttribute('tabindex') !== null
                        || el.tagName === 'A' || el.tagName === 'BUTTON')) {
                    // Только элементы, которые выглядят как пункт списка
                    if (rect.height < 60 && rect.height > 15) {
                        result.all_clickable.push(describe(el));
                    }
                }
            });

            // 3. Меню/попапы/дропдауны
            document.querySelectorAll(
                '[role="menu"], [role="listbox"], [role="dialog"], [role="popover"], ' +
                '[data-radix-popper-content-wrapper], [data-state="open"]'
            ).forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0) {
                    result.menus.push(describe(el));
                }
            });

            // 4. Оверлеи/попапы (элементы с высоким z-index)
            document.querySelectorAll('div').forEach(el => {
                const cs = window.getComputedStyle(el);
                const z = parseInt(cs.zIndex);
                if (z > 100) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 100 && rect.height > 100) {
                        result.popups.push({
                            ...describe(el),
                            zIndex: z,
                        });
                    }
                }
            });

            return result;
        }
        """)

        print(f"\n=== ПУНКТЫ СПИСКА: li/option/menuitem ({len(picker_data['list_items'])}) ===")
        for i, el in enumerate(picker_data['list_items'][:30]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'aria_label', 'data_testid', 'tabindex', 'cursor', 'text', 'class']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            if el.get('hasImg'):
                parts.append("HAS_IMG")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== КЛИКАБЕЛЬНЫЕ С ТЕКСТОМ ({len(picker_data['all_clickable'])}) ===")
        for i, el in enumerate(picker_data['all_clickable'][:40]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'tabindex', 'cursor', 'text', 'class']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            if el.get('hasImg'):
                parts.append("HAS_IMG")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== МЕНЮ/ЛИСТБОКСЫ ({len(picker_data['menus'])}) ===")
        for i, el in enumerate(picker_data['menus'][:10]):
            parts = [f"tag={el['tag']}"]
            for k in ['role', 'aria_label', 'data_testid', 'text', 'class']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            print(f"  [{i}] {' | '.join(parts)}")

        print(f"\n=== ПОПАПЫ (z-index > 100) ({len(picker_data['popups'])}) ===")
        for i, el in enumerate(picker_data['popups'][:10]):
            z = el.get('zIndex', '?')
            parts = [f"tag={el['tag']}", f"z={z}"]
            for k in ['role', 'text', 'class']:
                if el.get(k):
                    parts.append(f"{k}={el[k]!r}")
            parts.append(f"{el['w']}x{el['h']} @({el['x']},{el['y']})")
            print(f"  [{i}] {' | '.join(parts)}")

        print("\n✅ Скопируй ВЕСЬ вывод (все 3 прохода) и пришли мне.")
        input("Enter для закрытия... ")
        context.close()


if __name__ == "__main__":
    main()
