# От Хаоса до Олимпа — Ч.02 Власть Кроноса — стикеры

<!--
Мем-стикеры с прозрачным фоном для overlay в pyCapCut поверх сцен.
Эталон тональности — `content/Дионис и Ариадна/prompts/stickers.md` (UI-каркасы
тиндера, RPG-меню, ачивки, Spotify-плеера, parental-control alert и т.п.).
Правила в [../../../../MYTH.md](../../../../MYTH.md) → шаг 8 (обновлено 2026-05-16:
тональность обязана быть «весёлая / смешная / абсурдная / ироничная», эталон —
Дионис и Ариадна).

Особенность ч. 2: сюжет — самый тёмный в цикле (свержение отца, пожирание
детей). Стикеры обязательны как комедийный противовес, иначе ролик скатывается
в чернуху. UI-метафоры с абсурдным юмором (RPG-достижения, system dialogs,
weather widgets, Amazon orders) снимают давление, не отменяя трагизма.

Правила:
- Прозрачный фон (transparent background, isolated, no scene background)
- Один объект в кадре, читается за 0.5s
- Pixel-art стиль канала (highly detailed pixel art)
- Греческие/космогонические мотивы вплетены в современную UI-иконографию
  (адамантовый серп в иконке оружия, силуэты котов-богов, лавровые венки)
- Палитра отзеркаливает палитру сцены:
    • scene_04 (серп выкован): mossy-green + warm gold + dark adamant steel
    • scene_05 (Кронос соглашается): mossy-green + warm gold + warning amber +
      Cronus steel-grey accent
    • scene_09 (Афродита из пены): pearl-pink + cream-white + turquoise +
      dawn-rose
    • scene_10 (дождь = слёзы Урана): cool twilight blue-grey + faint warm
      gold + pale-blue star accent
    • scene_11 (Кронос на троне с Реей): dark throne stone + warm torch gold
      + cream Rhea + warning amber for "sister"
    • scene_12 (пророчество Геи): dark throne stone + glowing golden-green
      rune + warning crimson
    • scene_13 (поглощение детей): dark charcoal Cronus + five colored kitten
      glows + warning amber
    • scene_16 (Рея бежит в горы): cool moonlit grey-blue + warm hood-brown
      + sage-green map accents
    • scene_17 (беременна Зевсом): warm hearth orange + glowing belly gold +
      thunder-yellow accent
    • scene_18 (клиффхэнгер Зевс): warm belly gold + thunder-yellow sparks +
      dark cave background + bright gold star accent
- Английский текст КАПСОМ, короткий (1-3 слова или короткое число),
  явная позиция и цвет в промпте
- Уникальный subject-маркер в первых 3-4 английских словах

Маппинг scene_NN ↔ файл стикера (для enrich_oh_02.py):
  scene_04 → Achievement-popup «NEW WEAPON: ADAMANT SICKLE · LEGENDARY»
  scene_05 → Doodle Poll «OVERTHROW URANUS? · 11 NO · 1 YES»
  scene_09 → Apple TV / Netflix release «NEW DROP: APHRODITE · 5★ LEGENDARY»
  scene_10 → Weather widget «FORECAST: SKY DAD CRYING · RAIN ∞%»
  scene_11 → Facebook relationship change «MARRIED · ⚠ SISTER»
  scene_12 → System dialog «PROPHECY.EXE — RUN AS ADMIN? [YES] [NO]»
  scene_13 → RPG progress bar «KIDS ABSORBED: 5/6 ⚠»
  scene_16 → Google Maps «STEALTH MODE · GPS: HIDDEN · ETA: NEVER»
  scene_17 → Amazon delivery «ORDER #006 · INCOMING: ZEUS · ETA 9 MO»
  scene_18 → Steam achievement «BABY OF THE YEAR ✓ ZEUS · LEGENDARY»

Размещение в CapCut (см. [../../../../CAPCUT.md](../../../../CAPCUT.md)):
video-overlay-track 0.8–1.5s в начале сцены под пуант-фразу + короткий
мем-SFX в зависимости от типа стикера:
  - Achievement / collection unlock → `Image of sound of coin of 8bit game`
  - RPG quest / dialog popup → `Mouse click sound` + опц. `Sparkling`
  - iOS / system alert → системный «pop» SFX (CapCut: «Notification»)
  - Apple TV / Netflix drop → `Sparkling hilarious attack` (микро)
  - Weather widget → системный «pop» + опц. короткий «rain» loop из CapCut
  - Doodle poll / Facebook → `Mouse click sound`
  - Amazon delivery → системный «ding» (CapCut: «New mail»)

Если Flow рендерит латиницу криво — три пути ([../../../../MYTH.md](../../../../MYTH.md) → шаг 8):
  1. Перегенерить 3-4 раза в Flow, выбрать лучший вариант букв.
  2. Сгенерить стикер БЕЗ текста и наложить текст отдельным
     text-track в CapCut поверх стикера (Anticva-Regular / STRomeTrial-Bold).
  3. Откатить к чистой визуальной метафоре без слов (только иконка,
     прогресс-бар, орел и т.п.).
-->

## Сцена scene_04 (sent_005 — «Из адаманта она выковала тяжёлый, неубывающий серп»)

**Промпт:** adamant sickle legendary weapon unlock, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal weapon-unlock-popup banner styled exactly like an Xbox or Steam achievement-unlocked notification or Dark Souls "weapon acquired" panel, at the left side of the banner a large pixel-art square icon-frame with a thick bright-gold rim containing inside it a small stylized pixel-art rendering of a curved jagged dark-grey adamant sickle with a tapered black handle wrapped in dark leather (the exact weapon from the scene), the sickle icon surrounded by a soft mossy-green halo with tiny floating pixel-art oak-leaves and one bright-orange forge-spark drifting around it, to the right of the icon in the body of the banner in small bold pale-gold pixel-font text the upper line "NEW WEAPON ACQUIRED" spanning the upper portion, below the upper line in larger bold pale-cream pixel-font text the weapon name "ADAMANT SICKLE" prominently displayed in capitals with a tiny pixel-art crossed-sickles icon to its left, below the name a smaller pale-gold pixel-font subtitle line "★ LEGENDARY · UNBREAKABLE" with a small bright-gold five-pointed star icon directly before the word "LEGENDARY", below the subtitle three small pixel-art stat-rows in tiny pale-cream pixel-font — "DAMAGE: ∞ · DURABILITY: ∞ · CRAFTED BY: GAIA", the entire banner with a deep-mossy-green and dark-earth-brown background filled with subtle pixel-art moss-and-oak texture and a faint golden halo radiating around the icon, ornate pale-gold filigree borders trimming the top and bottom edges of the banner styled with grape-vine motifs, soft drop-shadow beneath the banner for sticker readability, palette of deep mossy-green and earth-brown background bright pale-gold filigree pale-cream main text warm gold star accents and dark adamant-steel sickle icon, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals and infinity symbols in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_05 (sent_006 — «Только младший её сын, Кронос, согласился его взять»)

**Промпт:** overthrow uranus poll results doodle, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical Doodle-poll-style results card with a clean pale-cream background and a thin warm-bronze rounded border styled exactly like a When2meet or Doodle group-decision survey result, at the top in bold all-capital warm-bronze pixel-font text the poll question heading "OVERTHROW URANUS?" spanning the width centered with small pixel-art lightning-bolt icons flanking each side, below the heading a subtitle line in smaller pale-bronze pixel-font "12 TITANS · 1 VOTE EACH" centered, below the subtitle two stacked response rows each on its own line — row 1 a left-aligned large bold all-capital pale-grey pixel-font label "NO" followed by a long horizontal progress-bar filled almost entirely (91%) in dim pale-grey with a tiny pixel-font count "11" at the far right end, row 2 a left-aligned large bold all-capital warm-amber pixel-font label "YES" followed by a much shorter horizontal progress-bar filled only at the far left (9%) in bright warm-amber with a tiny pixel-font count "1" at the far right end and a tiny pixel-art crowned cold-steel-grey cat-silhouette portrait-bubble (Cronus signature look) hovering immediately to the right of that "1" with a small bright-amber speech-arrow pointing from the silhouette to the "YES" bar (the visual joke that the one YES vote is clearly Cronus), at the bottom of the card a tiny pale-bronze pixel-font signature line "11 DECLINED · 1 ACCEPTED", soft drop-shadow beneath the card for sticker readability, palette of pale cream background warm bronze borders and labels dim pale grey NO bar and bright warm amber YES bar and accents and cold-steel-grey Cronus silhouette, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_09 (sent_010 — «Из морской пены... родилась Афродита — богиня красоты»)

**Промпт:** aphrodite legendary new drop netflix, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal Netflix-or-Apple-TV-style "new release" banner card with a deep-pearlescent-rose-and-cream gradient background and a thin pale-turquoise rounded border styled exactly like a streaming platform new-arrival banner, at the left side of the banner a large pixel-art rounded-square poster-frame with a thick pearl-white rim containing inside it a small stylized pixel-art portrait silhouette of a pearl-pink anthropomorphic cat with long flowing cream-white hair covering her body (Aphrodite's signature look) facing the viewer with turquoise eye points, the poster surrounded by soft floating pixel-art sea-foam-bubbles and a few tiny pink heart-icons drifting around it, to the right of the poster in the body of the banner in small bold pale-turquoise pixel-font text the upper line "NEW DROP" spanning the upper portion with a tiny pixel-art star-burst icon before and after the word, below the upper line in larger bold pale-cream pixel-font text the title "APHRODITE" prominently displayed in capitals, below the title a horizontal row of five large bold pearl-gold five-pointed stars all filled ★★★★★ centered with a tiny pale-cream pixel-font label "RATING:" to the immediate left of the stars, below the rating row a smaller pale-rose pixel-font tagline line "BORN FROM SEA FOAM · BEAUTY S1" with a small pixel-art seashell icon to the left, at the bottom-right corner of the banner a small pearl-pink rounded button with bold pale-cream pixel-font label "▶ PLAY" indicating the streaming action, ornate pale-turquoise filigree borders trimming the top and bottom edges of the banner styled with wave-and-foam motifs, soft drop-shadow beneath the banner for sticker readability, palette of pearlescent rose and cream background pale turquoise borders pearl-gold rating stars pale-cream main text and pearl-pink play button, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the play-arrow symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats, no nudity

## Сцена scene_10 (sent_011 — «А Уран теперь плачет с неба. И его слёзы падают на землю дождём»)

**Промпт:** weather forecast sky dad crying, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical weather-widget card styled exactly like an iOS or Apple Weather mini-tile with a cool twilight-blue gradient background fading from deep-navy at top to faint-pale-blue at bottom and a thin pale-silver rounded border, at the top in bold all-capital pale-silver pixel-font text the location heading "EARTH · FOREVER" spanning the width centered with a tiny pixel-art globe icon at each side, below the heading in the center of the widget a large pixel-art weather-status-icon of a single cloud with two small tear-drops falling out of its bottom and one tiny pale-blue starburst inside the cloud body (visual joke: it's a weeping-sky cloud, not a normal storm cloud), beside the cloud icon in very large bold pale-cream pixel-font text the temperature reading "∞°" prominently displayed with the infinity-symbol used in place of the digits, below the cloud icon in bold all-capital pale-silver pixel-font text the conditions label "SKY DAD CRYING" centered, below the conditions a smaller pale-silver pixel-font row "RAIN: 100% · WIND: 0 · MOOD: GRIEF" centered, below the row a horizontal small forecast-strip with five tiny day-tiles labeled MON TUE WED THU FRI each showing a tiny version of the same crying-cloud icon (every day forever it rains) and below each tile a tiny "∞°" temperature, at the very bottom in tiny pale-silver pixel-font the small disclaimer line "FORECAST SINCE: B.C. · STILL ACTIVE", soft drop-shadow beneath the widget for sticker readability, palette of twilight-navy-to-pale-blue gradient background pale silver borders and labels pale cream main text and small faint warm-gold tear-drop accents (the rain still has a tiny gold tint), modern detailed pixel art style, no scene, no setting, no landscape, all English text and the infinity and degree symbols in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_11 (sent_012 — «Кронос сел на трон отца и взял в жёны свою сестру Рею»)

**Промпт:** married status sister warning facebook, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal Facebook-style "relationship status changed" notification card with a dark stone-grey throne-themed background and a thin warm-torch-gold rounded border styled exactly like a social-network life-event card, at the top in small bold pale-cream pixel-font text the small label "RELATIONSHIP UPDATE" spanning the upper portion with a tiny pixel-art interlocking-rings icon at the right end, below the label in larger bold pale-cream pixel-font text the main event "IS NOW MARRIED" prominently displayed in capitals with a small pixel-art bright-gold crown-icon to the immediate left of the word "MARRIED", below the main event a horizontal row showing two small pixel-art portrait-bubbles linked by a tiny pale-gold heart-icon — the LEFT bubble showing a small pixel-art cold-steel-grey anthropomorphic cat silhouette with full beard and tall silver-and-sapphire crown (Cronus signature look), the heart in the middle in pale gold, the RIGHT bubble showing a small pixel-art cream-and-pale-gold anthropomorphic cat silhouette with long honey-gold braided hair and thin gold diadem (Rhea signature look), below both portrait-bubbles a small bright-amber pixel-art warning-banner spanning the width with bold all-capital warm-amber pixel-font text "⚠ NOTE: SISTER" with a small pixel-art warning-triangle icon at each side of the words, below the warning a smaller dim pale-cream pixel-font subtle line "STATUS: COMPLICATED · 47 LIKES · 12 CONCERNED" with a tiny pixel-art thumbs-up icon to the left, at the bottom of the card three tiny pixel-art horizontal action-buttons in dim pale-grey labeled "LIKE · COMMENT · SHARE", soft drop-shadow beneath the card for sticker readability, palette of dark stone-grey throne background warm torch-gold borders and crown pale-cream main text bright warm-amber warning accents and dim pale-grey action buttons, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the warning triangle symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_12 (sent_013 — «Но Гея сказала сыну: тебя свергнет твой собственный ребёнок»)

**Промпт:** prophecy exe run admin dialog, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical Windows-style UAC system-permission dialog box with a dark stone-grey throne-themed background and a thin pale-bronze rounded border styled exactly like a User Account Control elevation prompt or system permission dialog, at the very top of the dialog a thin dark-charcoal title-bar with bold pale-cream pixel-font small text on the left "SYSTEM PROMPT" and a tiny pixel-art X close-button icon on the far right (greyed out and inactive), below the title-bar in the upper-center a large pixel-art warning-shield-icon in bright glowing golden-green (the color of Gaia's prophecy runes) with a small ancient-rune-symbol inside it instead of the usual exclamation mark, below the shield icon in bold all-capital pale-cream pixel-font text the main heading "PROPHECY.EXE" prominently displayed centered, below the heading in smaller pale-cream pixel-font text the question line "RUN AS ADMIN?" centered with a tiny blinking-cursor pixel-art element after the question mark, below the question a smaller dim pale-grey pixel-font body-text-block in two short lines "PUBLISHER: GAIA · UNKNOWN PRIORITY" and "ACTION: SON WILL OVERTHROW YOU" both center-aligned with the second line tinted slightly warning-crimson, below the body text a small horizontal row of two action-buttons — on the left a bright crimson rounded rectangle with bold pale-cream pixel-font label "[YES]" indicating the inevitable accept, on the right a dim greyed-out rounded rectangle with dim pale-grey pixel-font label "[NO]" indicating the disabled refuse option (since no one can decline fate), at the bottom of the dialog a tiny pale-bronze pixel-font system-info line "VERIFIED PUBLISHER · CANNOT BE CANCELLED", soft drop-shadow beneath the entire dialog for sticker readability, palette of dark stone-grey background pale bronze borders glowing golden-green shield icon pale cream main text crimson warning accents on YES button and dim pale grey disabled NO button, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the brackets and X symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_13 (sent_014 — «И тогда Кронос начал глотать своих детей — Гестию, Деметру, Геру, Аида, Посейдона»)

**Промпт:** kids absorbed progress bar tracker, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal RPG-style boss-progress-tracker widget with a deep-charcoal-and-warm-amber background and a thin warning-amber rounded border styled like a dark game's father-figure-stat-tracker, at the top a small warning-amber pixel-font header-strip with the small bold all-capital pale-cream pixel-font heading "DAD STATS" centered with a tiny pixel-art crown-icon flanking each side, below the header-strip in larger bold all-capital pale-cream pixel-font text the metric label "KIDS ABSORBED" spanning the width centered, below the label a long horizontal pixel-art progress-bar with five of six segments fully filled left-to-right in increasing color intensity (segment 1 soft-beige Hestia tint, segment 2 wheat-gold Demeter tint, segment 3 cream-emerald Hera tint, segment 4 charcoal-silver Hades tint, segment 5 sea-blue Poseidon tint, segment 6 at the far right remaining EMPTY with a thin warning-amber border around it and a tiny pixel-art glowing gold question-mark "?" floating inside it indicating Zeus is missing), beside the progress bar a tiny large pixel-font count "5/6" in bold pale-cream digits, below the progress bar in smaller bold all-capital warning-amber pixel-font text the status line "ACHIEVEMENT FAILED: DAD OF THE YEAR ✕" centered with a small bright-crimson "X" icon to the right end (the visual joke: he wanted to absorb all six but failed at #6), below the status line a tiny pale-cream pixel-font flavor line "NEXT TARGET: ??? · LOCATION UNKNOWN" centered with a small pixel-art question-mark-target icon to the left, soft drop-shadow beneath the widget for sticker readability, palette of deep charcoal background warming-amber borders five colored kitten-tint segments (beige wheat cream charcoal sea-blue) pale-cream main text and bright crimson achievement-failed accent, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals and X and question-mark symbols in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats, no blood, no gore

## Сцена scene_16 (sent_017 — «Она бежала от мужа и спряталась далеко в горах»)

**Промпт:** stealth mode gps hidden google maps, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single vertical Google-Maps-style navigation widget styled exactly like a smartphone navigation app screen with a cool moonlit-blue-grey background and a thin sage-green rounded border, at the top a thin dark-slate header-bar with bold pale-cream pixel-font small label "NAVIGATION" on the left and a tiny pixel-art compass-rose icon on the right, below the header-bar in the upper-center a large pixel-art map-fragment showing curving sage-green mountain contour-lines on a moonlit-grey background with a small dashed-line route-path that ends mid-screen and dissolves into pixelated static (the route just stops, hidden from tracking), at the route start-point a tiny pixel-art warm-brown hooded-traveler icon (Rhea silhouette in her cloak) with a glowing green dot beside it, at the route end-point only pixel-art static-fog instead of a destination pin, below the map fragment in bold all-capital pale-cream pixel-font text the status line "STEALTH MODE: ON" prominently displayed centered with a small bright-green pixel-art glowing-dot icon to the immediate left of the word ON, below the status a smaller pale-cream pixel-font data row "GPS: HIDDEN · ETA: NEVER" with a small pixel-art eye-with-slash stealth-icon to the immediate left of the word GPS, below the data row a tiny dim pale-grey pixel-font subtle disclaimer line "BLOCKED FROM: KRONOS_2.EXE · ALL TRACKERS", at the very bottom a small horizontal pixel-art rounded action-button in muted sage-green with bold pale-cream pixel-font label "REROUTE TO CAVE", soft drop-shadow beneath the entire widget for sticker readability, palette of cool moonlit blue-grey background sage-green map contour-lines and borders pale-cream main text bright-green stealth-active dot and warm-brown traveler icon, modern detailed pixel art style, no scene, no setting, no landscape, all English text in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_17 (sent_018 — «Когда она снова забеременела, она знала: этот ребёнок будет особенным»)

**Промпт:** incoming order zeus amazon delivery, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal Amazon-style shipment-tracking notification card with a warm-hearth-orange-and-cream background and a thin warm-gold rounded border styled exactly like a delivery-tracking widget from a shopping app, at the top in small bold warm-gold pixel-font text the small label "DELIVERY UPDATE" spanning the upper portion with a tiny pixel-art lightning-bolt icon at the right end, below the label in larger bold all-capital pale-cream pixel-font text the main line "INCOMING: ZEUS" prominently displayed centered with a small pixel-art glowing-gold lightning-bolt icon to the immediate right of the name, below the main line a horizontal progress-bar styled as a delivery-status-stepper with four small icon-nodes connected by a dashed pale-gold line — first node a small filled-checkmark warm-gold "ORDERED" with a tiny pixel-font label below it, second node a small filled-checkmark warm-gold "PACKED" with a tiny pixel-font label below it, third node a small filled-glowing-warm-gold "IN TRANSIT" with a tiny pixel-art glowing-belly icon and a tiny pixel-font label below it (the current state), fourth node an unfilled dim pale-grey "DELIVERED" with a tiny pixel-font label below it (still pending), below the stepper in bold all-capital warm-gold pixel-font text the ETA line "ETA: 9 MO · ⚡ LEGENDARY" centered with a tiny pixel-art alarm-clock icon to the left of "ETA" and a small pixel-art lightning-bolt icon between "MO" and "LEGENDARY", below the ETA line a smaller dim pale-cream pixel-font tracking-number line "ORDER #006 · SHIPPED FROM: GAIA · HIDDEN ROUTE", at the very bottom a tiny warm-gold pixel-font flavor line "FREE SHIPPING · CANNOT BE INTERCEPTED", soft drop-shadow beneath the card for sticker readability, palette of warm hearth-orange and cream background warm gold borders and accents pale-cream main text glowing warm-gold delivery node and bright warm-gold lightning-bolt icon, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the numerals and lightning-bolt symbol in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

## Сцена scene_18 (sent_019 — клиффхэнгер: «Внутри неё рос тот, кому суждено сбросить отца с трона. Его имя — Зевс»)

**Промпт:** baby of the year zeus achievement, highly detailed pixel art sticker, isolated transparent background, no scene background, no environment, a single horizontal achievement-popup banner styled exactly like an Xbox or Steam achievement-unlocked notification or trophy-pop reveal, at the left side of the banner a large pixel-art circular icon-frame with a thick bright-gold rim containing inside it a small stylized pixel-art seated-kitten silhouette glowing warm gold with three tiny gold lightning-spark icons floating above its head (the exact unborn-Zeus signature from the cliffhanger scene), the icon surrounded by a bright golden halo with tiny scattered pixel-art lightning-bolt icons drifting around it, to the right of the icon in the body of the banner in small bold pale-gold pixel-font text the upper line "ACHIEVEMENT UNLOCKED" spanning the upper portion like a standard achievement notification, below the upper line in larger bold pale-cream pixel-font text the achievement name "BABY OF THE YEAR" prominently displayed in capitals with a small bright-cyan checkmark "✓" immediately after the word YEAR, below the name a smaller pale-gold pixel-font subtitle line "★ ZEUS · LEGENDARY · 1/1 SAVIORS" with a small bright-gold five-pointed star icon directly before the word "ZEUS", below the subtitle a tiny pale-cream pixel-font stat row "POWER: ⚡∞ · DESTINY: OVERTHROW DAD", the entire banner with a deep-cave-warm-orange and dark-stone-brown background filled with subtle pixel-art hearth-fire-flicker texture and a strong golden halo radiating around the icon, ornate pale-gold filigree borders trimming the top and bottom edges of the banner styled with lightning-bolt motifs, soft drop-shadow beneath the banner for sticker readability, palette of deep cave hearth-orange and dark stone-brown background bright pale-gold filigree pale-cream main text warm gold star and halo accents and bright cyan checkmark, modern detailed pixel art style, no scene, no setting, no landscape, all English text and the checkmark and infinity and lightning-bolt symbols in crisp clean bold pixel-font capital letters easily readable, NO humans, NO people, NO real four-legged cats

---

## Чек-лист перед запуском Flow

1. **Уникальный subject-маркер.** Проверить первые 3–4 слова каждого `**Промпт:**`:

   ```powershell
   Get-Content "content\От Хаоса до Олимпа\часть_02_Власть_Кроноса\prompts\stickers.md" -Encoding UTF8 |
     Where-Object { $_ -match '^\*\*Промпт:\*\* ' } |
     ForEach-Object { ($_ -replace '^\*\*Промпт:\*\* ([^,]+),.*', '$1') } |
     Group-Object | Sort-Object Count -Descending
   ```

   Все строки должны быть с числом `1`.

2. **Английский текст всегда КАПСОМ, короткий.** Не более 1–3 слов на блок, цифры/символы можно. Длинные предложения — переписать.

3. **Прозрачный фон.** В каждом промпте обязательны фразы `transparent background, isolated, no scene background, no environment` + в конце `no scene, no setting, no landscape`.

4. **Палитра под сцену.** Каждый стикер использует палитру своей сцены (см. маппинг в шапке файла), а не generic-meme-цвета.

5. **Тональность.** Каждый стикер — самостоятельная шутка через UI-метафору. Если читая описание не улыбаешься — переписать. Эталон — Дионис.

6. **Защита от платформенной модерации.**
   - scene_09 (Афродита из пены) — `no nudity` в негативах. Афродита изображается только как portrait silhouette с длинными волосами.
   - scene_13 (поглощение 5 детей) — `no blood, no gore` в негативах. Сам стикер показывает прогресс-бар, не процесс глотания. 5 котят упомянуты только как **цветовые сегменты** (beige Гестия, gold Деметра, etc.) и тинтованные иконки.

7. **Уникальные UI-каркасы (без повторов с ч.1).** В ч.1 уже использованы: achievement-popup Геи, TripAdvisor warning, Spotify mini-player, dashboard, RPG quest popup, achievement Урана, Pokédex, iOS parental control, RPG quest tracker «revenge». В ч.2 — новые: Steam weapon unlock (scene_04), Doodle poll (scene_05), Netflix new drop (scene_09), Weather widget (scene_10), Facebook relationship (scene_11), UAC system dialog (scene_12), RPG progress bar (scene_13), Google Maps stealth (scene_16), Amazon delivery (scene_17), Steam achievement Zeus (scene_18). **Achievement-popup появляется в ч.2 дважды** (scene_04 weapon + scene_18 baby), но это разные подвиды — weapon-unlock и baby-of-the-year — и они достаточно различимы.

---

## Размещение в CapCut (для `enrich_oh_02.py`)

| Файл стикера | Сцена pyCapCut | Время от старта сцены | Длительность | SFX |
|---|---|---|---|---|
| `scene_04_adamant_sickle_*.jpeg` | scene_04 | 0.5s | 1.6s | `Image of sound of coin of 8bit game` |
| `scene_05_overthrow_uranus_poll_*.jpeg` | scene_05 | 0.5s | 1.8s | `Mouse click sound` |
| `scene_09_aphrodite_netflix_*.jpeg` | scene_09 | 0.6s | 2.0s | `Sparkling hilarious attack` (микро) |
| `scene_10_weather_sky_dad_*.jpeg` | scene_10 | 0.5s | 1.8s | системный «notification pop» |
| `scene_11_married_sister_warning_*.jpeg` | scene_11 | 0.5s | 1.6s | `Mouse click sound` |
| `scene_12_prophecy_exe_admin_*.jpeg` | scene_12 | 0.4s | 1.8s | системный «notification alert» + `Sparkling` |
| `scene_13_kids_absorbed_tracker_*.jpeg` | scene_13 | 0.7s | 1.6s | `Image of sound of coin of 8bit game` (тёмный оттенок) |
| `scene_16_stealth_mode_gps_*.jpeg` | scene_16 | 0.5s | 1.5s | `Mouse click sound` |
| `scene_17_zeus_amazon_delivery_*.jpeg` | scene_17 | 0.5s | 1.8s | системный «ding» (CapCut: «New mail») |
| `scene_18_baby_year_zeus_*.jpeg` | scene_18 | 0.6s | 2.0s | `Image of sound of coin of 8bit game` (×2 для торжественности) |

**Общее правило для ч. 2.** Стикеры в сценах с тяжёлым сюжетом (scene_13 поглощение, scene_11 брак с сестрой) НЕ должны звучать триумфально — SFX в этих сценах либо короче, либо в более тёмном оттенке. UI-каркас сам по себе несёт юмор, SFX лишь подчёркивает; перебор → отталкивает зрителя.

---

## Журнал

- **2026-05-17** — Файл создан. 10 мем-стикеров на 19 сцен (плотность 0.53, как у ч.1). Тональность по эталону «Дионис и Ариадна» / ч.1: UI-метафоры с короткими английскими надписями. Все UI-каркасы **уникальны для ч.2** — не повторяют ч.1 (вместо achievement-Гея → achievement-weapon; вместо парadental-control → UAC-prompt; вместо RPG-quest → Google-Maps-stealth и т.п.).
- **2026-05-17** — Стикеры распределены по «комедийным крючкам» сюжета: серп как loot-drop (scene_04), голосование 11:1 (scene_05), новый сериал Афродита (scene_09), вечный дождь = погода (scene_10), Facebook MARRIED ⚠ SISTER (scene_11), UAC PROPHECY.EXE (scene_12), счёт пожранных 5/6 (scene_13), Google Maps STEALTH (scene_16), Amazon доставка Зевса (scene_17), achievement BABY OF THE YEAR (scene_18). Покрыты ВСЕ ключевые сюжетные узлы, кроме хука/титула (sent_001-002), сцен свержения и поднятия в небо (sent_007-008) и CTA (sent_020) — там стикеры мешали бы караоке-плашке или ломали бы трагический ритм свержения.
- **2026-05-17** — **Платформенная безопасность учтена в самих стикерах.** scene_13 (поглощение детей) — прогресс-бар «KIDS ABSORBED 5/6» сделан **визуальным гэгом**, а не описанием насилия: 5 цветовых сегментов соответствуют тинтам пятерых олимпийцев, шестой пустой с вопросом «?» — Зевс ускользнул. Подзаголовок «ACHIEVEMENT FAILED: DAD OF THE YEAR ✕» переводит сюжет в иронию (Кронос провалил роль отца), что снимает чернуху. scene_09 (Афродита) — `no nudity` в негативах, только portrait silhouette в длинных волосах.
- **2026-05-17** — **Тематические находки для будущих частей.** В ч.2 родилось 3 UI-приёма, которые можно использовать в ч.3+: (1) **прогресс-бар с цветовыми сегментами под персонажей** (scene_13) — можно повторить в ч.3 при освобождении котят из Кроноса как обратный процесс «KIDS RESCUED 6/6 ✓»; (2) **Google Maps с stealth-mode** (scene_16) — подойдёт для любых сцен побега или скрытия в будущих мифах; (3) **Amazon delivery с ETA** (scene_17) — подойдёт для любых «беременностей-пророчеств» в одиночных мифах (Лето с Аполлоном/Артемидой, Семела с Дионисом и т.п.).
