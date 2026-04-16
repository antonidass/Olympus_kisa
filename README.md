# Кисы Олимпа — пайплайн генерации

Автоматизация для канала «Кисы Олимпа»: от сценария мифа до набора картинок в Google ImageFX.

## Структура

```
BOGI AI/
├── CONTEXT.md              # Контекст проекта (правила сценариев, стиль)
├── scripts/                # Markdown-файлы со сценами и промптами
│   └── pandora.md
├── automation/
│   ├── imagefx_runner.py   # Playwright-раннер для Google ImageFX
│   ├── requirements.txt
│   └── .browser_profile/   # Сохранённая сессия браузера (создаётся автоматически)
└── output/                 # Сгенерированные картинки
    └── ящик_пандоры/
        ├── scene_01.png
        ├── scene_02.png
        └── ...
```

## Установка

```bash
cd "BOGI AI"
pip install -r automation/requirements.txt
python -m playwright install chromium
```

## Как это работает

1. **Сценарий**: Claude в рамках сессии пишет сценарий мифа и разбивает его на сцены в файле `scripts/<миф>.md`.
2. **Запуск раннера**:
   ```bash
   python automation/imagefx_runner.py scripts/pandora.md
   ```
3. **Первый запуск**: откроется окно Chromium с ImageFX — залогинься в Google. Сессия сохранится в `automation/.browser_profile`.
4. **Генерация**: раннер по очереди вставляет промпт каждой сцены, ждёт генерации и сохраняет скриншот страницы в `output/<миф>/scene_NN.png`.

## Формат markdown-файла со сценами

```markdown
# Название мифа

## Сцена 1

**Текст:** Закадровый текст на русском...

**Промпт:** pixel art, cute cat as..., 16-bit retro game style, no text, no camera movement

## Сцена 2
...
```

Промпты пишутся на английском — ImageFX лучше их понимает. Стилистические константы: `pixel art`, `cute cat characters`, `16-bit retro game style`, `no text`, `no camera movement` (по правилам из `CONTEXT.md`).

## Если что-то сломалось

ImageFX может менять разметку — если раннер не находит поле ввода или кнопку генерации, поправь селекторы в функциях `wait_for_prompt_input()` и `click_generate()` в `automation/imagefx_runner.py`.
