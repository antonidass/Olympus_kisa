"""
Дамп всех медиа-элементов на странице Flow ПОСЛЕ генерации.

Запуск:
    python automation/dump_media.py

Что делать:
    1. Залогинься, открой проект.
    2. Сгенерируй любую картинку во Flow вручную.
    3. Когда картинки появятся на экране — нажми Enter в консоли.
    4. Скрипт распечатает все <img>, <video>, <canvas>, <source>, а также
       все background-image на странице. Пришли вывод.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

FLOW_URL = "https://labs.google/fx/ru/tools/flow/project/7bd82873-3936-4fc2-8687-f4284b363c1f"
PROFILE_DIR = Path(__file__).parent / ".browser_profile"

DUMP_JS = r"""
() => {
    const result = { imgs: [], videos: [], sources: [], canvases: [], bg_images: [] };

    document.querySelectorAll('img').forEach(el => {
        const r = el.getBoundingClientRect();
        result.imgs.push({
            src: el.src || null,
            currentSrc: el.currentSrc || null,
            srcset: el.srcset || null,
            alt: el.alt || null,
            w: Math.round(r.width),
            h: Math.round(r.height),
            visible: r.width > 0 && r.height > 0,
        });
    });

    document.querySelectorAll('video').forEach(el => {
        const r = el.getBoundingClientRect();
        result.videos.push({
            src: el.src || null,
            currentSrc: el.currentSrc || null,
            poster: el.poster || null,
            w: Math.round(r.width),
            h: Math.round(r.height),
        });
    });

    document.querySelectorAll('source').forEach(el => {
        result.sources.push({
            src: el.src || null,
            srcset: el.srcset || null,
            type: el.type || null,
        });
    });

    document.querySelectorAll('canvas').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width > 100 && r.height > 100) {
            result.canvases.push({ w: Math.round(r.width), h: Math.round(r.height) });
        }
    });

    // Элементы с background-image
    const all = document.querySelectorAll('*');
    const seen = new Set();
    for (const el of all) {
        const bg = getComputedStyle(el).backgroundImage;
        if (bg && bg !== 'none' && bg.includes('url(')) {
            const r = el.getBoundingClientRect();
            if (r.width > 100 && r.height > 100 && !seen.has(bg)) {
                seen.add(bg);
                result.bg_images.push({
                    bg: bg.slice(0, 200),
                    tag: el.tagName.toLowerCase(),
                    class: (typeof el.className === 'string' ? el.className : '').slice(0, 80),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                });
            }
        }
    }

    return result;
}
"""


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

        # Слушаем сетевые ответы с картинками
        media_responses = []

        def on_response(resp):
            ct = (resp.headers or {}).get("content-type", "")
            if ct.startswith("image/") or ct.startswith("video/"):
                media_responses.append((resp.status, ct, resp.url))

        page.on("response", on_response)

        print("\n⏸  Открой проект, СГЕНЕРИРУЙ КАРТИНКУ ВРУЧНУЮ во Flow.")
        print("   Когда картинки появятся на экране — нажми Enter.")
        input("   Enter для дампа... ")

        data = page.evaluate(DUMP_JS)

        print(f"\n=== <img> ({len(data['imgs'])}) ===")
        for i, im in enumerate(data["imgs"]):
            if not im["visible"]:
                continue
            src = (im["src"] or "")[:150]
            cur = (im["currentSrc"] or "")[:150]
            print(f"  [{i}] {im['w']}x{im['h']}  src={src}")
            if cur and cur != src:
                print(f"       currentSrc={cur}")
            if im["srcset"]:
                print(f"       srcset={im['srcset'][:200]}")

        print(f"\n=== <video> ({len(data['videos'])}) ===")
        for i, v in enumerate(data["videos"]):
            print(f"  [{i}] {v['w']}x{v['h']}")
            print(f"       src={(v['src'] or '')[:150]}")
            print(f"       currentSrc={(v['currentSrc'] or '')[:150]}")
            print(f"       poster={(v['poster'] or '')[:150]}")

        print(f"\n=== <source> ({len(data['sources'])}) ===")
        for i, s in enumerate(data["sources"]):
            print(f"  [{i}] type={s['type']} src={(s['src'] or '')[:150]}")

        print(f"\n=== <canvas> ({len(data['canvases'])}) ===")
        for i, c in enumerate(data["canvases"]):
            print(f"  [{i}] {c['w']}x{c['h']}")

        print(f"\n=== background-image ({len(data['bg_images'])}) ===")
        for i, b in enumerate(data["bg_images"]):
            print(f"  [{i}] {b['tag']}.{b['class'][:40]}  {b['w']}x{b['h']}")
            print(f"       {b['bg']}")

        print(f"\n=== Network: image/video responses ({len(media_responses)}) ===")
        for status, ct, url in media_responses[-30:]:
            print(f"  [{status}] {ct}  {url[:160]}")

        print("\n✅ Пришли весь вывод целиком.")
        input("Enter для закрытия... ")
        context.close()


if __name__ == "__main__":
    main()
