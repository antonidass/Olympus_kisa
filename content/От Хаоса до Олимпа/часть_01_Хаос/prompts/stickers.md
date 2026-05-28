# От Хаоса до Олимпа — Ч.01 Хаос — стикеры

<!--
Мем-стикеры с прозрачным фоном для overlay в pyCapCut поверх сцен.
Эталон тональности — `content/Дионис и Ариадна/prompts/stickers.md` (UI-каркасы
тиндера, RPG-меню, ачивки, Spotify-плеера, parental-control alert и т.п.).
Правила в [../../../../MYTH.md](../../../../MYTH.md) → шаг 8 (обновлено 2026-05-16:
тональность обязана быть «весёлая / смешная / абсурдная / ироничная», эталон —
Дионис и Ариадна).

Правила:
- Прозрачный фон (transparent background, isolated, no scene background)
- Один объект в кадре, читается за 0.5s
- Pixel-art стиль канала (highly detailed pixel art)
- Греческие/космогонические мотивы вплетены в современную UI-иконографию
  (ветви оливы, лавровые венки, силуэты котов-богов, серп Кроноса в иконках)
- Палитра отзеркаливает палитру сцены (после перенумерации −2 от 2026-05-18):
    • scene_03 (Гея рождается, sent_003): mossy-green + warm gold + earth-brown
    • scene_05 (Тартар, sent_005): deep anthracite + crimson red + grey
    • scene_06 (Эрос, sent_006): pink-gold gradient + amber + dark accent
    • scene_11 (мир пуст, sent_011): cool pale-grey + cool blue + soft yellow warning
    • scene_12 (Гея одинока, sent_012): pale moss-green + dusty rose + warm wood-brown
    • scene_13 (Гея решает, sent_013): deep moss + warm gold + bright magenta accent
    • scene_14 (Уран рождается, sent_014): silvery-blue + starlight gold + pale cream
    • scene_15 (12 титанов, sent_015): warm bronze + multi-color tiles + pale gold
    • scene_18 (Уран запирает, sent_018a): dark slate + locked-red + warning amber
    • scene_18 (Кронос точит, sent_018b): dark charcoal + ember orange + cold steel
- Английский текст КАПСОМ, короткий (1-3 слова или короткое число),
  явная позиция и цвет в промпте
- Уникальный subject-маркер в первых 3-4 английских словах

Маппинг scene_NN ↔ файл стикера (для enrich_oh_01.py). ВНИМАНИЕ: scene_NN
в имени файла стикера = ИНДЕКС ПРЕДЛОЖЕНИЯ (sent_NNN с убранным leading-нулём),
а не порядковый номер сцены из images.md. После перенумерации от 2026-05-18:

  scene_03 → Achievement-popup «UNLOCKED: GAIA · LEGENDARY · 1/12 PRIMORDIALS»
              (sent_003 «И вдруг в этой тьме родилась Гея — Земля»)
  scene_05 → TripAdvisor-warning «TARTARUS · ★☆☆☆☆ · DO NOT VISIT»
              (sent_005 «Следом — Тартар, тёмная бездна»)
  scene_06 → Spotify mini-player «NOW PLAYING: GRAVITY.MP3 · ♥ EROS · ∞:∞»
              (sent_006 «И Эрос — сила, которая притягивает одно к другому»)
  scene_11 → Dashboard «POPULATION: 7 · ACTIVITY: 0% · VIBE: AWKWARD»
              (sent_011 «Мир обрёл первых жителей. Но он был пуст и тих»)
  scene_12 → Health-bar «LONELINESS: 100/100 · MAX»
              (sent_012 «Земле было одиноко»)
  scene_13 → RPG quest popup «NEW QUEST: BIRTH YOUR OWN HUSBAND»
              (sent_013 «И тогда Гея решила…»)
  scene_14 → Achievement «GOT HUSBAND ✓ · BUILT IN 1 DAY · NO RETURNS»
              (sent_014 «Из её плоти поднялось Небо — Уран…»)
  scene_15 → Collection unlock «12 NEW TITANS · LEGENDARY EDITION · CRONUS ⚠ MARKED»
              (sent_015 «От их союза родились двенадцать титанов…»)
  scene_18 (шот 1, sent_018 первая половина «Уран возненавидел...») →
    iOS-alert «PARENTAL CONTROL: ON · CHILDREN HIDDEN»
  scene_18 (шот 2, sent_018 вторая половина «...один из них уже точит серп») →
    RPG quest tracker «QUEST: REVENGE · 1% · SHARPENING SICKLE...»

  ВАЖНО: на scene_18 ДВА стикера в одной сцене (один за другим, разные тайминги
  внутри длинного 9-11 сек клиффхэнгера). В `distribute_stickers.py` файлы
  будут лежать как `scene_18_a_parental_control_*.jpeg` и
  `scene_18_b_revenge_quest_*.jpeg`. `enrich_oh_01.py` подхватывает оба и кладёт
  на overlay-трек с разным временем старта (a — на 0.5–2.5s, b — на 5.5–8.5s
  от начала scene_18, под пуант-фразы соответствующих половин предложения).

Размещение в CapCut (см. [../../../../CAPCUT.md](../../../../CAPCUT.md)):
video-overlay-track 0.8–1.5s в начале сцены под пуант-фразу + короткий
мем-SFX в зависимости от типа стикера:
  - Achievement / collection unlock → `Image of sound of coin of 8bit game`
  - RPG quest / dialog popup → `Mouse click sound` + опц. `Sparkling`
  - iOS / system alert → системный «pop» SFX (CapCut: «Notification»)
  - Spotify-плеер → «Cat barks meow» как иронический звук
  - TripAdvisor warning → `Woman screams` (короткий) или системный error-beep

Если Flow рендерит латиницу криво — три пути ([../../../../MYTH.md](../../../../MYTH.md) → шаг 8):
  1. Перегенерить 3-4 раза в Flow, выбрать лучший вариант букв.
  2. Сгенерить стикер БЕЗ текста и наложить текст отдельным
     text-track в CapCut поверх стикера (Anticva-Regular / STRomeTrial-Bold).
  3. Откатить к чистой визуальной метафоре без слов (только иконка,
     прогресс-бар, орел и т.п.).
-->

## Сцена scene_03 (sent_003 — «И вдруг в этой тьме родилась Гея — Земля»)

**Промпт:** gaia legendary primordial achievement unlocked, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal achievement-popup banner styled exactly like an Xbox or Steam achievement-unlocked notification, at the left side of the banner a large pixel-art circular icon-frame with a thick bright-gold rim containing inside it a small stylized pixel-art portrait silhouette of a moss-green anthropomorphic cat with long hair of oak leaves and grape vines and small wildflowers (Gaia's signature look) facing the viewer, the icon surrounded by a soft golden halo glow with tiny floating pixel-art oak leaves and seedlings drifting around it, to the right of the icon in the body of the banner in small bold pale-gold pixel-font text the upper line "ACHIEVEMENT UNLOCKED" spanning the upper portion like a standard achievement notification, below the upper line in larger bold pale-cream pixel-font text the achievement name "GAIA" prominently displayed in capitals, below the name a smaller pale-gold pixel-font subtitle line "LEGENDARY · 1/12 PRIMORDIALS" with a small bright-gold five-pointed star icon directly before the word "LEGENDARY", the entire banner with a deep-forest-green-and-earth-brown background filled with subtle pixel-art moss texture and a faint golden halo radiating around the icon, ornate pale-gold filigree borders trimming the top and bottom edges of the banner styled with oak-leaf motifs, soft drop-shadow beneath the banner for sticker readability, palette of deep forest green and warm earth brown background bright pale-gold filigree pale-cream main text and warm moss-green silhouette, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numeral "1/12" in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_05 (sent_005 — «Следом — Тартар, тёмная бездна»)

**Промпт:** tartarus one star review warning, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single rounded-rectangle TripAdvisor-style review summary card with a deep-anthracite-grey background and a thin crimson rounded border styled like a one-star traveler review widget, at the top in bold all-capital crimson pixel-font text the heading "TARTARUS" spanning the width centered with a tiny pixel-art warning-triangle "⚠" icon flanking each side of the heading in bright warning yellow, below the heading a horizontal row of five large bold pixel-art five-pointed stars — the FIRST star on the left fully filled in dirty crimson-orange with tiny lava-vein details inside it and the remaining FOUR stars completely greyed out empty outlines (the universal one-star-out-of-five symbol), below the stars in slightly smaller italicized bold crimson pixel-font text the user-review quote "WORST PIT EVER · 0/10" with quotation marks clearly drawn at start and end, below the quote a smaller pale-grey pixel-font byline "— ANCIENT TRAVELER · 1 REVIEW", a small pixel-art cracked-stone icon in the top-right corner of the card and a tiny pixel-art crimson lava-vein motif at the bottom-left corner, soft drop-shadow beneath the card for sticker readability, palette of deep anthracite grey crimson red dirty crimson-orange star and bright warning yellow accents pale grey byline, modern detailed pixel art style, no scene, no setting, no landscape, all English text and numerals and stars in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_06 (sent_006 — «И Эрос — сила, которая притягивает одно к другому»)

**Промпт:** gravity now playing eros spotify, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single small rounded-rectangle music-player widget styled exactly like a Spotify mini-player, the entire widget background in deep almost-black charcoal with soft pink-and-gold accent highlights instead of the usual Spotify green to match the Eros palette, at the top in small bold soft-pink pixel-font text the small label "NOW PLAYING" clearly readable, in the center of the widget in larger bold pale-cream pixel-font text the track title "GRAVITY.MP3" prominently displayed with a small bright-pink pixel-art heart "♥" icon to its left replacing the usual musical-note icon, below the title a small horizontal progress-bar fully filled left-to-right in a soft pink-to-gold gradient indicating the track has been playing forever, beside the progress bar a tiny pixel-font timestamp "∞:∞" in pale-pink digits on the left and "∞:∞" in pale-gold digits on the right (the infinity symbol used as both elapsed and total time, the joke being it plays forever), below the progress bar in smaller pale-gold pixel-font the artist line "♥ EROS · COSMOGONY HITS" centered, at the bottom three small pixel-art circular playback buttons in pale-grey (previous track skip-back, a central currently-active play-arrow ▶ in bright pink, next track skip-forward), a small decorative pixel-art golden-rose-and-amber sparkle icon in one corner of the widget, soft drop-shadow beneath the widget for sticker readability, palette of charcoal-black background bright pink-and-gold accents pale cream track title and pale gold subtitle, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the infinity-symbol timestamps in crisp clean bold pixel-font letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_11 (sent_011 — «Мир обрёл первых жителей. Но он был пуст и тих»)

**Промпт:** population seven activity zero dashboard, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical system-monitor dashboard widget with a cool pale-grey-and-pale-blue background and a thin dark-slate rounded border styled like an old-school task-manager status panel, at the top in bold all-capital dark-slate pixel-font text the heading "WORLD STATUS" centered with a tiny pixel-art globe icon at each side, below the heading three stacked metric rows each on its own line — row 1 a left-aligned small pixel-font label "POPULATION:" in dark-slate followed by a large bold cyan digit "7" in bright cyan pixel-font with a tiny silhouette-of-seven-cat-figures icon to its right, row 2 a left-aligned small pixel-font label "ACTIVITY:" followed by a small horizontal progress-bar with a long pale-grey empty track and only the very leftmost 0% sliver visible with a tiny pixel-font number "0%" labeled inside the bar, row 3 a left-aligned small pixel-font label "VIBE:" followed by a bold all-capital warning-yellow pixel-font word "AWKWARD" with a tiny pixel-art warning-triangle "⚠" icon flanking the word, at the bottom of the dashboard a small horizontal status-bar in dim grey with a tiny pixel-art cricket-insect icon and three dots "..." next to it (a callback to the "crickets" silence meme), soft drop-shadow beneath the widget for sticker readability, palette of cool pale grey background pale blue accents bright cyan digits warning yellow vibe-text and dark-slate labels, modern detailed pixel art style, no scene, no setting, no landscape, all English text and numerals and the percent sign in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_12 (sent_012 — «Земле было одиноко»)

**Промпт:** loneliness gauge maxed out, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal status-bar widget styled like an RPG character health-bar but labeled as a sadness meter, with a pale-mossy-cream parchment background and a thin pale-bronze rounded border, at the top in bold all-capital pale-bronze pixel-font text the label heading "LONELINESS" spanning the width left-aligned with a small pixel-art bandaged-heart icon "❤️‍🩹" (cute pixel-art broken-heart with a tiny bandage drawn over it) to the immediate left of the word, below the label a long horizontal pixel-art progress-bar with a thick deep-rose-pink fill completely filling the entire track from left to right showing the meter is fully maxed out, the pink fill with tiny pixel-art shimmer-highlights along its top edge, below the bar in slightly smaller bold pale-bronze pixel-font text the numeric readout "100/100" left-aligned and the bold all-capital crimson pixel-font label "MAX" right-aligned with a tiny pixel-art alarm-bell-icon beside the MAX label, at the bottom of the widget a small decorative pixel-art lone wildflower drooping to one side (a tiny callback to Gaia's leaf-and-flower hair), soft drop-shadow beneath the widget for sticker readability, palette of pale mossy cream background pale bronze borders and labels deep rose-pink progress fill and crimson MAX label, modern detailed pixel art style, no scene, no setting, no landscape, all English text and numerals in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_13 (sent_013 — «И тогда Гея решила: если у неё нет мужа — она родит его себе сама»)

**Промпт:** birth own husband rpg quest popup, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single classic RPG-style quest popup dialog widget with a deep moss-green background and a thick bright-gold pixel-art double-line border styled exactly like a Final Fantasy or Zelda quest-update menu box, at the top a small bright-gold pixel-font header-strip flanked by a tiny pixel-art oak-leaf icon on the left and a tiny pixel-art exclamation mark "!" icon on the right with the small bold all-capital pale-cream pixel-font heading "NEW QUEST" centered on the strip, below the header-strip in large bold pale-cream pixel-font text the main quest title "BIRTH YOUR OWN HUSBAND" spanning the width centered in two lines if necessary (line 1 "BIRTH YOUR OWN", line 2 "HUSBAND"), below the title a small horizontal row of FIVE pixel-art five-pointed difficulty-rating stars all completely filled in bright gold ★★★★★ left-aligned with a tiny pale-cream pixel-font label "DIFFICULTY:" before the stars, below the difficulty line another row in smaller pale-gold pixel-font text the line "REWARD: COMPANIONSHIP" with a small pixel-art treasure-chest icon to the left, at the bottom of the dialog a tiny pale-gold pixel-font instruction line "PRESS A TO ACCEPT" in smaller text, decorative pixel-art tiny floating oak-leaves and grape-vines in the corners of the dialog box tying it visually to Gaia, soft drop-shadow beneath the dialog box for sticker readability, palette of deep moss-green dialog background bright pale-gold double-line borders pale-cream main text bright gold difficulty stars and warm tiny grape-vine accents, modern detailed pixel art style, no scene, no setting, no landscape, all English text in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_14 (sent_014 — «Из её плоти поднялось Небо — Уран, накрывший Землю куполом»)

**Промпт:** husband built one day achievement, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal achievement-popup banner styled exactly like an Xbox or Steam achievement-unlocked notification, at the left side of the banner a large pixel-art circular icon-frame with a thick silver rim containing inside it a small stylized pixel-art portrait silhouette of a silvery-blue anthropomorphic cat with long silver-white hair and a tall silver crown set with sapphire constellations (Uranus's signature look) facing the viewer, the icon surrounded by a soft silver-blue starlit halo with tiny scattered pixel-art star points around it, to the right of the icon in the body of the banner in small bold pale-gold pixel-font text the upper line "ACHIEVEMENT UNLOCKED" spanning the upper portion like a standard achievement notification, below the upper line in larger bold pale-cream pixel-font text the achievement name "GOT HUSBAND" with a small bright-cyan checkmark "✓" immediately after the word HUSBAND, below the name a smaller pale-gold pixel-font subtitle line "BUILT IN 1 DAY · NO RETURNS" with a small pixel-art alarm-clock icon directly before the words "1 DAY", the entire banner with a deep-silver-and-night-blue starlit background filled with subtle scattered pixel-art star points and a faint silver halo radiating around the icon, ornate pale-gold filigree borders trimming the top and bottom edges of the banner styled with constellation-line motifs, soft drop-shadow beneath the banner for sticker readability, palette of deep silver and night-blue starlit background bright pale-gold filigree pale-cream main text bright cyan checkmark and silvery-blue silhouette, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the checkmark symbol and the numeral "1" in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_15 (sent_015 — «От их союза родились двенадцать титанов. Среди них — младший и самый дерзкий, Кронос»)

**Промпт:** twelve titans legendary edition collection, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical pixel-art Pokédex-style collection-screen panel with a warm bronze-and-pale-cream background and a thick gold-and-bronze rounded border styled like a "collection completed" reveal screen, at the top of the panel in bold all-capital pale-gold pixel-font text the heading "12 NEW TITANS" spanning the width centered with small pixel-art laurel-wreath flourishes flanking each side, below the heading a smaller pale-gold pixel-font subtitle line "LEGENDARY EDITION · COMPLETE" centered with three small filled gold star icons "★★★" to the right end, below the subtitle a 4-by-3 grid of twelve small square portrait-tile slots each tile with a thin bronze pixel-art border and inside each tile a tiny stylized pixel-art silhouette of an anthropomorphic cat in a distinctive metallic palette (top row left-to-right bronze, copper, silver, gold; middle row deep-indigo, sea-green, ivory, olive; bottom row violet, pearl-white, ember-orange, and the LAST tile in the bottom-right specifically showing a cold-steel-grey cat silhouette with a thick bright-crimson warning-triangle "⚠" badge overlaid in the upper-right corner of that one tile and a tiny pixel-font label "CRONUS" in bold crimson pixel-font printed directly below that one tile only — drawing attention to it as the "marked" one), the eleven other tiles unlabeled, at the bottom of the panel a tiny pale-gold pixel-font legend line "★ MARKED: FUTURE THREAT" centered with a small warning-triangle icon, soft drop-shadow beneath the panel for sticker readability, palette of warm bronze and pale-cream background gold filigree pale-cream heading multi-color tile silhouettes (each tile in its own metallic palette) and bright crimson warning accent on the Cronus tile only, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals and warning symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_18 (шот 1, sent_018 первая половина — Уран запирает чудовищных детей)

**Промпт:** parental control children hidden alert, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical rounded-rectangle iOS-style system-modal alert dialog with a deep-slate-grey background and a thin pale-bronze rounded border styled exactly like a smartphone notification or system permission dialog, at the top of the dialog a large pixel-art locked-padlock icon "🔒" in crimson-red centered, below the padlock icon in bold all-capital pale-cream pixel-font text the main heading "PARENTAL CONTROL" spanning the width centered, below the heading a small bold all-capital bright-amber pixel-font status line "STATUS: ON" centered with a tiny pixel-art glowing dot in bright green to the immediate left of the word ON, below the status line in smaller pale-grey pixel-font body text the descriptive subtitle "CHILDREN HIDDEN" centered with a small pixel-art ghost-eye-icon flanking each side of the word CHILDREN to imply something has been concealed, below the body text two small pixel-art horizontal pale-grey-rounded buttons stacked vertically — top button a dimmer rounded pale-grey rectangle with bold dark-grey pixel-font label "OVERRIDE ✕" indicating it is disabled, bottom button a brighter rounded crimson rectangle with bold pale-cream pixel-font label "OK · LOCKED IN" indicating the dominant locked-state action, at the very bottom of the dialog in tiny pale-grey pixel-font the small disclaimer line "FATHER KNOWS BEST", soft drop-shadow beneath the entire dialog for sticker readability, palette of deep slate-grey background pale-bronze border crimson padlock and confirm button bright amber status pale cream main text and pale grey disabled button, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the lock and X symbols in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_18 (шот 2, sent_018 вторая половина — молодой Кронос точит серп)

**Промпт:** revenge quest sharpening sickle tracker, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal RPG-style quest-tracker widget with a deep-charcoal-black background and a thin warm-ember-orange rounded border styled like a quest-update HUD panel from a stealth-action game, at the top a small bright-ember-orange pixel-font header-strip with the small bold all-capital pale-cream pixel-font heading "QUEST UPDATE" centered with a tiny pixel-art crossed-sickles icon flanking each side, below the header-strip in larger bold all-capital pale-cream pixel-font text the quest title "REVENGE" spanning the width centered with a small ember-orange glow under the word, below the title a long horizontal pixel-art progress-bar with a mostly-empty deep-grey track and only the very leftmost 1% sliver filled in bright ember-orange showing the quest just begun, beside the progress bar a tiny pixel-font label "PROGRESS: 1%" in pale-ember pixel-font digits, below the progress bar in slightly smaller italicized bold pale-cream pixel-font text the current-action status line "SHARPENING SICKLE..." with the trailing three-dot ellipsis clearly drawn, beside the action line a tiny pixel-art bright-orange spark-particle floating off as if from the act of sharpening, at the bottom of the widget a tiny dim pale-grey pixel-font disclaimer line "TARGET: DAD · STEALTH: ACTIVE" with a small pixel-art eye-with-slash icon (the stealth-active symbol) to the left of the word STEALTH, soft drop-shadow beneath the widget for sticker readability, palette of deep charcoal-black background warm ember-orange borders progress fill and accents pale cream main text and dim pale-grey disclaimer line, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals and percent symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

---

## Чек-лист перед запуском Flow

1. **Уникальный subject-маркер.** Проверить первые 3–4 слова каждого `**Промпт:**`:

   ```bash
   grep '^\*\*Промпт:\*\* ' content/От\ Хаоса\ до\ Олимпа/часть_01_Хаос/prompts/stickers.md \
     | sed -E 's/^\*\*Промпт:\*\* ([^,]+),.*/\1/' \
     | sort | uniq -c | sort -rn
   ```

   Все строки должны быть с числом `1`.

2. **Английский текст всегда КАПСОМ, короткий.** Не более 1–3 слов на блок, цифры/символы можно. Длинные предложения — переписать.

3. **Прозрачный фон.** В каждом промпте обязательны фразы `transparent background, isolated, no scene background, no environment` + в конце `no scene, no setting, no landscape`.

4. **Палитра под сцену.** Каждый стикер использует палитру своей сцены (см. маппинг в шапке файла), а не generic-meme-цвета. Например, scene_05 стикер Геи — moss-green + gold, scene_15 стикер Урана — silver-blue + starlight.

5. **Тональность.** Каждый стикер — самостоятельная шутка через UI-метафору. Если читая описание не улыбаешься — переписать. Эталон — Дионис.

---

## Размещение в CapCut (для `enrich_oh_01.py`)

| Файл стикера | Сцена pyCapCut | Время от старта сцены | Длительность | SFX |
|---|---|---|---|---|
| `scene_03_gaia_legendary_*.jpeg` | scene_03 | 0.5s | 1.5s | `Image of sound of coin of 8bit game` |
| `scene_05_tartarus_one_star_*.jpeg` | scene_05 | 0.5s | 1.5s | `Woman screams` (short) или системный error-beep |
| `scene_06_gravity_now_playing_*.jpeg` | scene_06 | 0.4s | 1.6s | `Cat barks meow` (иронический) |
| `scene_11_population_seven_*.jpeg` | scene_11 | 0.5s | 1.4s | `Mouse click sound` |
| `scene_12_loneliness_gauge_*.jpeg` | scene_12 | 0.3s | 1.3s | `Sparkling hilarious attack` (микро) |
| `scene_13_birth_own_husband_*.jpeg` | scene_13 | 0.5s | 1.8s | `Mouse click sound` + `Sparkling` |
| `scene_14_husband_built_one_day_*.jpeg` | scene_14 | 0.6s | 1.8s | `Image of sound of coin of 8bit game` |
| `scene_15_twelve_titans_legendary_*.jpeg` | scene_15 | 0.6s | 2.0s | `Image of sound of coin of 8bit game` (×2) |
| `scene_18_a_parental_control_*.jpeg` | scene_18 (шот 1) | 1.0s | 2.0s | системный «notification pop» |
| `scene_18_b_revenge_quest_*.jpeg` | scene_18 (шот 2) | 5.5s | 2.5s | `Mouse click sound` + `Sparkling hilarious attack` |

**Важно про scene_18:** два разных стикера в одной сцене (длинный 9–11 сек клиффхэнгер из двух шотов). `distribute_stickers.py` положит их как `scene_18_a_*` и `scene_18_b_*` — `enrich_oh_01.py` должен подхватить ОБОИХ и разместить с разным временем старта (см. таблицу выше).

---

## Журнал

- **2026-05-16** — Файл создан. 10 мем-стикеров на 19 сцен (плотность 0.53, как у Диониса 13/24). Тональность по эталону «Дионис и Ариадна»: UI-метафоры с короткими английскими надписями. Подбор — таблица A/B в чате, юзер выбрал 4-A / 6-A / 7-A / 12-B / 13-A / 14-A / 15-B / 16-A / 18a-A / 18b-A. На scene_20 (клиффхэнгер sent_020) — два стикера в одной сцене с разными таймингами (a — parental control под первую половину предложения, b — revenge quest tracker под вторую). Это новый для проекта паттерн «два стикера в одной сцене», `enrich_oh_01.py` должен будет поддержать.
- **2026-05-18** — **Сдвиг имён сцен на −2 после переделки интро в voiceover.md.** Удалены sent_003 «Он простирался…» и sent_004 «что-то шевельнулось» (два темных Хаос-кадра, гарантировавшие свайп). Все sent-номера сдвинуты вниз на 2 → имена стикеров (= индекс предложения с убранным leading-нулём) тоже сдвинуты: `scene_05` (Гея) → `scene_03`, `scene_07` (Тартар) → `scene_05`, `scene_08` (Эрос) → `scene_06`, `scene_13` (мир пуст) → `scene_11`, `scene_14` (Гея одинока) → `scene_12`, `scene_15` (Гея решает) → `scene_13`, `scene_16` (Уран рождается) → `scene_14`, `scene_17` (12 титанов) → `scene_15`, `scene_20` (клиффхэнгер a+b) → `scene_18` (a+b). Содержание стикеров не менялось — только индексы в шапке, в заголовках секций и в таблице CapCut-размещения. Файлы в `images/stickers/` тоже надо переименовать (шаг `distribute_stickers.py` или вручную) — пока ждёт.
