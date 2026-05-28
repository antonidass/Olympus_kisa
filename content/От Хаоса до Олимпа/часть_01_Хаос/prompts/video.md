# Промпты видео (Veo 3.1): Часть 1 — Хаос и первобожества

Промпты **image-to-video** для Google Flow / Veo. Картинки уже сгенерированы и одобрены — см. [images.md](images.md) и `../images/approved_images/`. Промпт ниже описывает только **ДВИЖЕНИЕ и АТМОСФЕРУ** — внешность персонажей берётся из картинки.

См. также:

- [CONTEXT.md](../../../../CONTEXT.md) → «IP-фильтр Veo» (запрет имён греческих богов), «Правила промптов для анимации» (без зумов, без речи), «Связка озвучки и видео».
- [GENEALOGY.md](../../../../GENEALOGY.md) → шаг 10 (descriptive-замены для серии, усиленный IP-фильтр).
- [MYTH.md](../../../../MYTH.md) → шаг 10 (правило уникального subject-маркера).

---

<!-- ============================================================
     IP-FILTER VEO: descriptive-замены для имён первобожеств и титанов.
     В этой части НИ ОДНО греческое имя бога не должно появиться в **Промпт:**.
     В images.md имена разрешены, в video.md — НЕТ (Veo блокирует генерацию).

       Хаос        → "primordial swirling void entity" / "void nebula"
       Гея         → "living moss-green earth-landscape entity" / "earth-landscape with two golden-green earth-eyes"
       Тартар      → "living dark-abyss entity" / "deep dark chasm entity"
       Эрос        → "radiant pink-and-gold attraction-orb entity"
       Эреб        → "living ash-grey darkness-cloud entity"
       Никта       → "living blue-black night-cloud entity"
       Эфир        → "living ivory-and-pale-gold heavenly-light cloud entity"
       Гемера      → "living peach-and-rose-gold dawn-cloud entity"
       Уран        → "living silvery-blue starry sky-canopy entity" / "starry sky-dome with two pale-blue star-cluster eyes"
       Кронос      → "young dark-silver cat titan teenager"
       титаны      → "twelve anthropomorphic bipedal cat titans"
       циклопы     → "three one-eyed cat blacksmith brothers"
       гекатонхейры → "three many-armed cat granite giants" / "hundred-handed cat giants"

     Также превентивно избегать:
       - "Olympus" / "Greek gods" / "deities" в текст-промпте
       - любые "-style" отсылки к франшизам (Disney/Marvel/Hades-game/God-of-War)
       - физика-описания эффектов вместо названий вселенных
     ============================================================ -->

<!-- ============================================================
     ОБЯЗАТЕЛЬНЫЕ НЕГАТИВЫ В КАЖДОМ ПРОМПТЕ:
       No speech, no dialogue, no talking, no voices, no mouth movement, no music,
       no on-screen text, no letters, no titles,
       NO humans, NO people, NO real four-legged cats

     ДОПОЛНИТЕЛЬНО ДЛЯ АБСТРАКТНЫХ СУЩНОСТЕЙ
     (Хаос, Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран):
       entities are the landscape/clouds/dome/orb themselves with eyes,
       NO humanoid figure for the entity, NO body, NO hands, NO arms,
       NO mouth, NO face — only the abstract entity-form with its eyes,
       emotion shown only through changes in the element itself
       (eye glow, mist swirl, surface cracks, golden tear-streams)

     ДОПОЛНИТЕЛЬНО ДЛЯ СЦЕН С СТРАДАНИЕМ И УГРОЗОЙ (18, шот 1; 18, шот 2; 19):
       no blood, no gore, no wounds, no death imagery, no aggression

     ВЕТО ПО АНИМАЦИИ (общие правила канала):
       - камера статична: NO camera pan, NO camera zoom, NO camera shake
         (если в промпте не сказано иное явно)
       - персонажи НЕ разговаривают: cat muzzles stay firmly closed,
         no mouth movement, никаких "shouts/speaks/says/laughs/screams"
       - никакого нарушения класса персонажа: абстрактные сущности
         НЕ обзаводятся руками-ногами, антропоморфные коты НЕ съезжают
         в четвероногих
     ============================================================ -->

---

## Маппинг sentence ↔ scene_NN_M.mp4

Один TTS-файл `sentence_NNN.mp3` ↔ один или несколько mp4-шотов с префиксом `scene_NN_`. Нумерация сцен 1:1 совпадает с [images.md](images.md). У `sent_001` и `sent_002` — общая картинка и **один видео-шот** (хук + титул караоке поверх одного и того же кадра, см. memory `feedback_intro_single_unit`). У `sent_016` и `sent_017` — общая картинка, **два видео-шота** под одну сцену (фокус на циклопы → фокус на гекатонхейров). У `sent_018` (клиффхэнгер, 9–11 сек) — **два шота** с двумя разными картинками (Уран запирает детей, Кронос точит серп).

| sent | scene file(s) | картинка-вход | заметка |
| --- | --- | --- | --- |
| 001 + 002 | `scene_01_01.mp4` | `scene_01_v1.jpg` | хук + титул — один шот, караоке-плашка ложится в монтаже поверх медленно «дышащей» пустоты |
| 003 | `scene_02_01.mp4` | `scene_02_v1.jpg` | Гея открывает глаза, первый светлый кадр после двух тёмных секунд интро |
| 004 | `scene_03_01.mp4` | `scene_03_v1.jpg` | Гея — твёрдая опора, пульс тёплого света |
| 005 | `scene_04_01.mp4` | `scene_04_v1.jpg` | Тартар — провал, мерцание лавы |
| 006 | `scene_05_01.mp4` | `scene_05_v1.jpg` | Эрос — кольца притяжения |
| 007 | `scene_06_01.mp4` | `scene_06_v1.jpg` | контр-кадр: разрозненные объекты |
| 008 | `scene_07_01.mp4` | `scene_07_v1.jpg` | Эреб + Никта, два облака выплывают |
| 009 | `scene_08_01.mp4` | `scene_08_v1.jpg` | «Брат и сестра» — края облаков соприкасаются |
| 010 | `scene_09_01.mp4` | `scene_09_v1.jpg` | Эфир + Гемера рождаются между Эребом и Никтой |
| 011 | `scene_10_01.mp4` | `scene_10_v1.jpg` | общий план — семь сущностей в покое |
| 012 | `scene_11_01.mp4` | `scene_11_v1.jpg` | одинокая Гея, цветы поникли |
| 013 | `scene_12_01.mp4` | `scene_12_v1.jpg` | Гея решилась — столб серебристого света поднимается |
| 014 | `scene_13_01.mp4` | `scene_13_v1.jpg` | купол Урана раскрывается над Геей |
| 015 | `scene_14_01.mp4` | `scene_14_v1.jpg` | 12 титанов под куполом, молодой Кронос вперёд |
| 016 | `scene_15_01.mp4` | `scene_15_v1.jpg` | циклопы — кузнечные искры, foreground motion |
| 017 | `scene_15_02.mp4` | `scene_15_v1.jpg` (та же) | гекатонхейры — веер рук, background motion |
| 018 | `scene_16_01.mp4` | `scene_16a_v1.jpg` | Уран запирает: тучи, молнии, золотые слёзы Геи |
| 018 | `scene_16_02.mp4` | `scene_16b_v1.jpg` | Кронос в тенях точит адамантовый серп, искра отлетает |
| 019 | `scene_17_01.mp4` | `scene_17_v1.jpg` | финал-CTA: купол, поникшие холмы, серп на точиле |

Итого: **18 видео-шотов** на 17 сцен (нумерация сцен совпадает с images.md). Картинок-входов — 18 (две картинки общие для соседних шотов: `scene_01_v1.jpg` под sent_001+002, `scene_15_v1.jpg` под sent_016+017).

---

## Сцена 01 (sent_001 + sent_002 — хук «До начала времени был только Хаос. Вечная, бескрайняя, клубящаяся тьма» + титул «От Хаоса до Олимпа. Часть первая»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_01_v1.jpg

**Заметка к монтажу.** Один видео-шот покрывает сразу два TTS-предложения. На хуке (sent_001, 5–6 сек) огромное Око Хаоса в верхней половине кадра медленно открывается из тумана, моргает раз и фиксирует взгляд прямо на зрителя — психологический stop-scroll крючок «нечто живое смотрит на меня» в первые 2 секунды. К концу хука с уголка ока в туманность ниже стекает одинокая золотая искра-слеза. Во второй половине шота (под sent_002, титул 3–4 сек) око держит спокойный взгляд, туманность вокруг успокаивается, нижняя половина кадра становится визуально стабильной — туда в pyCapCut ляжет накопительная караоке-плашка «ОТ ХАОСА → ДО ОЛИМПА → ЧАСТЬ 1». Никакого отдельного «титул-кадра» — титул живёт ПОВЕРХ хук-кадра, под оком. Это завязка визуальной рифмы «стихия с глазами» — в Сцене 02 ей ответит открытие двух глаз Геи в холмах.

**Промпт:** chaos eye opening hook and title settle shot, in the upper half of the frame a single enormous glowing amber-and-gold cosmic EYE built from the primordial swirling void itself slowly opens for the first time, the eyelid (a curved band of dark violet and charcoal nebula clouds wrapping above and below the eye) parts and curls back smoothly during the first two seconds of the shot, the amber-and-warm-gold iris with tiny swirling nebula-clouds drifting inside it brightens gradually and the deep black abyss-vortex pupil at the center steadies its gaze directly at the viewer, the eye blinks once gently then holds the gaze open with primordial awareness, a single warm-gold ember-tear droplet hanging at the lower corner of the eye slowly detaches and drifts downward into the void below leaving a faint glowing trail, in the lower half of the frame the deep violet and charcoal Chaos nebula clouds drift very slowly inward and outward in long concentric breath-pulses during the first half of the shot, faint warm-gold embers drift extremely slowly in long lazy spirals deep inside the dark clouds, during the second half of the shot the cosmic eye's gaze steadies and the surrounding nebula calms into a slower cadence the lower central area of the frame becomes intentionally quiet and stable to support an overlaid karaoke title plate appearing in editing over the same hook frame, soft warm-gold halo around the eye glows softly throughout, the void feels eternal and timeless, no horizon, no other figures, the lower central area of the frame remains visually quiet throughout to leave room for the overlaid title plate, camera completely static, no camera pan, no camera zoom, slow contemplative dreamlike pace, dark cinematic lighting with warm amber-gold focal glow from the eye and gentle violet-charcoal edges, no on-screen text, no letters, no titles in the video itself, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the chaos entity, NO body, NO hands, NO arms, NO mouth, NO face apart from the single cosmic eye — the eye IS the entity, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 7 seconds.
**Звуки:** глубокий низкий первобытный гул вечной пустоты (deep primordial low void hum), мягкий шёлковый звон открывающегося ока (soft silken eye-opening chime in the first two seconds), тёплый золотой пульс на радужке (warm gold iris pulse), очень медленное «дыхание» тьмы вокруг (very slow dark breathing pulse around the eye), отдалённый намёк на пробуждающееся сознание Хаоса (distant hint of awakening chaos awareness), переход к торжественному отдалённому эху во второй половине (transition into distant solemn reverb in the second half), еле слышный отдалённый звон космического покоя под спокойным взглядом ока (faint distant cosmic stillness chime).

---

## Сцена 02 (sent_003 — «И вдруг в этой тьме родилась Гея — Земля»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_02_v1.jpg

**Заметка к монтажу.** Это первая «светлая» картинка ролика — после двух тёмных секунд хука+титула резкий визуальный поворот: из отступающей вверх тёмной туманности выплывает живая земля-сущность с двумя огромными золотисто-зелёными глазами в холмах. Контраст по палитре (тёмно-фиолетовый → мшисто-зелёный + тёплое золото) и по форме (бесформенная пустота → конкретный пейзаж) удерживает зрителя на стыке хука и основного нарратива.

**Промпт:** earth landscape eyes opening, in the lower half of the frame the living moss-green earth-landscape entity slowly emerges and settles into existence from the receding primordial swirling void above, the vast rolling terrain of dark-moss-green and earth-brown soil with oak roots and grape vines settles into place small bright green wildflowers gently sway, TWO LARGE GOLDEN-GREEN EYES set into the central hillside and a nearby slope slowly open for the very first time blinking once then steadying their gaze upward with quiet primordial awareness their golden-green glow strengthening gradually, faint warm earth-glow pulses softly under the surface of the moss-green soil like a slow first heartbeat, the deep violet and charcoal void above slowly recedes upward into the background behind the landscape, no figure on the landscape, the earth itself is the living entity, camera completely static, no camera pan, no camera zoom, slow tender pace of a new being awakening, warm cinematic lighting with green-gold under-glow rising softly, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the earth, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth with its two golden-green eyes opening, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** глубокий низкий гул просыпающейся земли (deep low awakening-earth rumble), мягкий звон первого дыхания почвы (soft first-soil breath chime), тихое биение жизни под холмами (quiet life-pulse under hills), еле слышный шелест распускающейся травы (faint opening-grass rustle).

---

## Сцена 03 (sent_004 — «Широкая, твёрдая, надёжная опора всему, что будет»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_03_v1.jpg

**Промпт:** earth foundation glowing pulse, the living moss-green earth-landscape entity stretches wide and firm across the entire lower frame as a vast rolling terrain of dark-moss-green and earth-brown soil with massive exposed oak roots gripping mossy boulders and small bright green shoots pushing upward, the small green shoots visibly straighten and grow a fraction taller in slow motion as the earth wakes into its role as the foundation of the world, the grape vines around the rocks twitch and tighten their grip the small wildflowers slowly turn their petals upward, TWO LARGE GOLDEN-GREEN EYES set deep into the central rise and a nearby slope blink once and gaze calmly and steadily upward their glow strengthens in a slow confident pulse, faint warm earth-glow under the surface throbs in a strong steady rhythm emphasizing the foundation, low-angle composition stays steady, camera completely static, no camera pan, no camera zoom, slow grounded pace of an unshakable foundation, warm cinematic lighting with golden-green under-glow strengthening once, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the earth, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth with its two golden-green eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** глубокое биение опоры мира (deep world-foundation heartbeat), мягкий хруст распрямляющихся побегов (soft straightening-shoot crackle), низкий гул укрепляющейся земли (low strengthening-earth hum), отдалённый звон золотого света изнутри (distant golden inner-light chime).

---

## Сцена 04 (sent_005 — «Следом — Тартар, тёмная бездна, что лежит глубже самой Земли»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_04_v1.jpg

**Промпт:** abyss-mouth eyes opening crimson glow, the living dark-abyss entity revealed as a colossal horizontally-opened chasm-mouth dominating the lower two-thirds of the frame like the jaws of a sleeping primordial beast, anthracite-black jagged rock teeth-stalactites hang down from the upper lip and matching stalagmites jut up from the lower lip framing the wide horizontal opening, deep inside the mouth TWO ENORMOUS GLOWING CRIMSON EYES of the abyss entity slowly open and steady their gaze directly outward at the viewer with ancient menace then pulse once together with primordial awareness, glowing crimson lava-vein patterns along the inner walls of the chasm-mouth slowly pulse brighter and dimmer in a slow ominous heartbeat radiating outward from around the two eyes like a halo of molten cracks, faint warm crimson under-glow inside the mouth illuminating the rock teeth from below, in the upper quarter of the frame a thin band of the moss-green-and-earth-brown earth-landscape rests on top of the chasm-mouth like a thin lid with bare oak roots dangling slightly and small wildflowers along the edges staying still, view from the side at eye-level with the mouth — the chasm cuts horizontally across the frame, NOT looking down into a pit, camera completely static, no camera pan, no camera zoom, slow ominous awakening pace, dark cinematic lighting with deep crimson focal glow from the two eyes and warm lava-vein highlights along the chasm walls, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the abyss, NO body, NO hands, NO arms, NO mouth-with-tongue, NO face — only the living abyss with its two crimson eyes and rock-teeth jaws, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** глубокий грозный гул просыпающейся бездны (deep ominous awakening-abyss rumble), потрескивание тлеющих лавовых жил вокруг глаз (smoldering lava-vein crackle around the eyes), низкое каменное скрипение раскрывающейся пасти (low stone-grinding chasm-mouth creak), еле слышный пульс двух багровых глаз (faint twin crimson-eye pulse).

---

## Сцена 05 (sent_006 — «И Эрос — сила, которая притягивает одно к другому»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_05_v1.jpg

**Промпт:** attraction orb pulling cosmic objects, the radiant pink-and-gold attraction-orb entity at the centre of the frame as a glowing radiant pink-and-gold cosmic light orb floats serenely in space, soft pink-and-gold concentric attraction rings continuously radiate outward from the orb in slow rhythmic pulses, TWO LARGE GLOWING AMBER ALMOND EYES at the centre of the orb stay open gazing outward calmly with a single slow blink, around the orb small floating cosmic stars dust particles and pebbles drift in curved magnetic lines toward the orb from all sides as if gently pulled in some of the small objects orbit briefly before settling closer, gentle visible attraction lines glow soft pink-gold across space, the deep violet primordial void recedes far in the background, camera completely static, no camera pan, no camera zoom, gentle hypnotic attraction-pulse pace, warm cinematic lighting with pink-gold radiance pulsing softly, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the orb-entity, NO body, NO hands, NO mouth, NO face — only the living force-orb itself with its two amber eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** мягкий звон притяжения (soft attraction-chime), нежное гудение тёплого света (gentle warm-light hum), отдалённый шорох сходящихся к орбу пылинок (distant dust-pulled-inward rustle), еле слышный пульс розово-золотых колец (faint pink-gold ring pulse).

---

## Сцена 06 (sent_007 — «Без него мир остался бы россыпью отдельных вещей»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_06_v1.jpg

**Промпт:** scattered cosmic objects drifting apart, small floating stars rocks and dust particles spread across a vast empty void scatter slowly outward in different directions with no connection between them, each object continues its lonely trajectory in slow drift no curving back no orbit no attraction, the previously seen attraction-rings are absent the radiant pink-gold orb is absent from the frame, no figure of any kind, the deep violet and charcoal primordial swirling void recedes far in the background, the composition emphasises separation and silence, camera completely static, no camera pan, no camera zoom, cold lonely slow drift pace, cool cinematic lighting with faint blue rim-glow on isolated objects, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure, NO body, NO hands, NO face, no character anywhere, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** холодная пустая тишина без эха (cold silent emptiness with no reverb), еле слышный одинокий звон далёкой звезды (faint lone distant-star chime), очень тихое мерцание разрозненных частиц (very faint scattered-particle shimmer).

---

## Сцена 07 (sent_008 — «Потом пришли Эреб — Мрак, и Никта — Ночь»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_07_v1.jpg

**Промпт:** twin dark entities emerging side by side, on the left the living ash-grey darkness-cloud entity slowly drifts forward as a swirling pool of ash-grey-and-soot dark mist forming a sentient cloud its ink-black tendrils of shadow drift outward like slow wisps of smoke, TWO AMBER GLOWING EYES WITH DARK RINGS shine from within the dark mist blinking once and steadying, on the right the living blue-black night-cloud entity slowly drifts forward as a deep blue-black night-sky cloud dusted with tiny white star points its silver lunar crescent shapes circle slowly around the cloud like tiny moon phases, TWO LARGE SILVER FULL-MOON EYES shine from within the night-mist blinking once and steadying, both cloud-entities float forward together out of the receding deep violet primordial void behind them, the two clouds stay separate not touching yet, camera completely static, no camera pan, no camera zoom, slow ceremonial emergence pace, dark cinematic lighting with cool silver-blue highlights, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figures for the cloud-entities, NO bodies, NO hands, NO mouths, NO faces — only the two living cloud-entities with their eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** низкий шорох выплывающего дымного облака (low drifting smoke-mist rustle), нежный звон серебристых лунных полумесяцев (gentle silver-crescent chime), тихий шёпот двух теней рядом (quiet whisper of two shadows close), еле слышный пульс четырёх светящихся глаз (faint four-eyes pulse).

---

## Сцена 08 (sent_009 — «Брат и сестра»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_08_v1.jpg

**Промпт:** sibling clouds edges touching close, close framing of two living dark cloud-entities side by side, the edges of the ash-grey-and-soot dark mist cloud on the left and the deep blue-black star-dusted night cloud on the right slowly drift closer together and gently touch their soft cloud-borders subtly merging where they meet creating a quiet sense of sibling closeness without any romance, the ink-black shadow tendrils of the left cloud and the silver lunar crescents of the right cloud weave through one another at the touchpoint in slow motion, all four glowing eyes (TWO AMBER on the left, TWO SILVER FULL-MOON on the right) gaze calmly forward in the same direction in unison, the dark nocturnal background stays steady with faint stars far behind, camera completely static, no camera pan, no camera zoom, slow tender sibling pace, cool moonlit cinematic lighting, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figures for the cloud-entities, NO bodies, NO hands, NO mouths, NO faces — only the two living cloud-entities with their eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 2 seconds.
**Звуки:** мягкий шорох соприкасающихся облаков (soft touching-clouds rustle), нежный звон родственной связи (gentle kinship-chime), очень тихое биение в унисон (very quiet unison heartbeat).

---

## Сцена 09 (sent_010 — «От их союза родились Эфир — чистый небесный свет, и Гемера — День»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_09_v1.jpg

**Промпт:** light clouds dawn birth between darkness, in the foreground two new living light-cloud entities slowly emerge side by side from a warm pale-gold glow between their darker parent-clouds in the background, on the left the living ivory-and-pale-gold heavenly-light cloud entity brightens softly its soft gold rays radiate gently outward and TWO PALE-BLUE GLOWING EYES open slowly within the light gazing forward with newborn awareness, on the right the living peach-and-rose-gold dawn-cloud entity warms into existence its gentle pastel sunrise-pink rays radiate outward and TWO WARM AMBER GLOWING EYES open within the dawn-mist gazing forward, behind them in soft focus the darker parent-clouds remain visible for contrast (the ash-grey-and-soot dark mist with its amber eyes on the far left, the deep blue-black star-dusted night cloud with its silver moon eyes on the far right) their light dimming a fraction as the new children take the foreground glow, camera completely static, no camera pan, no camera zoom, slow tender birth pace, warm dawn cinematic lighting building gradually, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figures for any cloud-entity, NO bodies, NO hands, NO mouths, NO faces — only the four living cloud-entities with their eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 5 seconds.
**Звуки:** нежный звон рассвета (gentle dawn-chime), мягкое мерцание распускающегося света (soft opening-light shimmer), тихий вздох первых лучей (quiet first-rays sigh), отдалённый отзвук материнской и отцовской тьмы позади (distant fading parent-darkness echo).

---

## Сцена 10 (sent_011 — «Мир обрёл первых жителей. Но он был пуст и тих»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_10_v1.jpg

**Промпт:** seven primordials quiet world tableau, a vast establishing wide shot of the primordial world holds completely still each of the seven living abstract entities pulses softly in their own place but no one interacts with anyone else, the living moss-green earth-landscape with its TWO GOLDEN-GREEN earth-eyes in the lower half pulses warmly once, the living dark-abyss entity at the lower right rim glows faintly with its TWO CRIMSON DOT-EYES once, the radiant pink-and-gold attraction-orb at the centre of the frame above the earth pulses softly with its TWO AMBER almond eyes its rings barely visible, the living ash-grey darkness-cloud and the living blue-black night-cloud beside the starry patch at the upper right shimmer faintly with their four amber and silver eyes, the living ivory-and-pale-gold heavenly-light cloud and the living peach-and-rose-gold dawn-cloud at the upper left glow softly with their four pale-blue and warm amber eyes, a mirror-still lake at the lower centre reflects all the colored lights faintly the water surface barely moves, large empty spaces between every entity emphasize the quiet world, no other living creatures yet, no wind, complete cosmic silence, camera completely static, no camera pan, no camera zoom, slow quiet pace of waiting, quiet cinematic lighting mixing all the auras softly, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figures for any entity, NO bodies, NO hands, NO mouths, NO faces anywhere in the frame, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** глубокая первобытная тишина мира (deep primordial world silence), едва слышное дыхание разнесённых сущностей (barely audible scattered-entities breathing), тихий пульс отражения в зеркальной воде (quiet mirror-water reflection pulse), отдалённый отголосок далёкого звона пустоты (distant void-chime echo).

---

## Сцена 11 (sent_012 — «Земле было одиноко»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_11_v1.jpg

**Промпт:** lonely earth dimming flowers wilt, medium closeup of the living moss-green earth-landscape entity in melancholy state, the small wildflowers visibly droop a fraction lower in slow motion their petals losing their bright colour, the grape vines hang lifelessly across the rocks the oak roots look thirsty and dim, the faint warm earth-glow beneath the surface fades slightly slowing into a tired heartbeat the green-gold under-glow dimming a notch, TWO LARGE GOLDEN-GREEN EYES set into the hillsides are half-lowered gazing off into the empty distance with quiet primordial melancholy the eyes blink slowly once their glow muted, gentle wind softly ruffles the small wildflower petals and vine leaves in a slow forlorn drift, the soft blurred background of empty mossy hills and a still mirror-like lake stays unchanged, no other entities anywhere in the frame, camera completely static, no camera pan, no camera zoom, slow melancholy pace of solitude, soft warm but muted cinematic lighting, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the earth-entity, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with its two melancholic eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** одинокий шелест увядающей травы (lonely withering-grass rustle), тихий вздох ветра по пустым холмам (quiet empty-hills wind sigh), медленное угасание тёплого пульса (slow fading warm-pulse), еле слышное капание единственной росинки (faint single dewdrop drop).

---

## Сцена 12 (sent_013 — «И тогда Гея решила: если у неё нет мужа — она родит его себе сама»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_12_v1.jpg

**Промпт:** earth resolute silver column rising, the living moss-green earth-landscape entity in a three-quarter wide shot of the central hillside awakens with new resolve, the dark-moss-green-and-earth-brown soil pulses noticeably brighter in a quickening determined heartbeat, the wildflowers and oak roots straighten themselves upward the small petals reopen and grow brighter as the earth wakes, the faint warm earth-glow beneath the surface strengthens into a strong determined pulse, TWO LARGE GOLDEN-GREEN EYES set into the hillsides slowly open wide and glow brighter with primordial resolve gazing upward steadily, from the very crown of the central hillside between the two earth-eyes a tall bright column of silvery-blue starlight starts to rise slowly upward growing taller and brighter as the very first emergence of a sky-husband from inside the earth-mother, glimmering star-points appear faintly inside the rising silver column, the moment just before creation is held in suspense, the mossy hilltop and the still distant lake far below stay steady, camera completely static, no camera pan, no camera zoom, dramatic rising creation pace, dramatic warm-and-cool cinematic lighting (warm green-gold from the earth, cool silver-blue rising from the central crown), no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the earth-entity, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with its two resolute eyes and the rising silver-blue column, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 5 seconds.
**Звуки:** низкий нарастающий гул решимости земли (low rising earth-resolve rumble), хрустальный звон поднимающегося серебристого света (crystalline rising silver-light chime), мягкое разгорание тёплой пульсации (soft warming pulse swell), отдалённый намёк на новое начало (distant hint of new beginning).

---

## Сцена 13 (sent_014 — «Из её плоти поднялось Небо — Уран, накрывший Землю куполом до самого края мира»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_13_v1.jpg

**Промпт:** sky dome unfurling stars over earth, the silvery-blue column of starlight rising from the central hillside of the living moss-green earth-landscape entity unfurls slowly across the upper portion of the frame and becomes the living silvery-blue starry sky-canopy entity, the vast star-dome stretches outward across the upper half filled with star points and constellations the silver clouds drift slowly across the dome, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES form gradually within the brightest constellation clusters and steady their gaze calmly downward at the earth below, the dome edges curve downward toward the horizon like a canopy covering the world from edge to edge, in the lower half the earth-landscape entity with its TWO GOLDEN-GREEN EYES in the hillsides gazes upward at the newly formed sky in serene wonder its warm earth-glow pulses softly under the moss-green soil, the still lake at the very bottom of the frame slowly mirrors the new starry sky above its surface only barely rippling, camera completely static, no camera pan, no camera zoom, dramatic celestial unveiling pace, dramatic starlit cinematic lighting with cool silver-blue from the dome and warm green-gold from the earth, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figures for either entity, NO bodies, NO hands, NO mouths, NO faces anywhere in the frame — only the starry sky-dome with its star-cluster eyes and the earth-landscape with its golden-green eyes, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 5 seconds.
**Звуки:** торжественный звон раскрывающегося звёздного купола (solemn unfurling-star-dome chime), мягкое мерцание созвездий (soft constellation shimmer), глубокий благоговейный отзвук земли смотрящей вверх (deep awe-struck earth-looking-up reverb), едва слышное эхо первого вечного союза (faint first-eternal-union echo).

---

## Сцена 14 (sent_015 — «От их союза родились двенадцать титанов. Среди них — младший и самый дерзкий, Кронос»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_14_v1.jpg

**Промпт:** twelve cat titans gathering under starry dome, twelve anthropomorphic bipedal cat titans gathered in a wide group on the mossy ground beneath the living silvery-blue starry sky-canopy with TWO ICY PALE-BLUE STAR-CLUSTER EYES gazing down from the constellations, the twelve cat titans stand upright on two legs in human-like body posture in their distinctive metallic and elemental robes (bronze, copper, silver, steel, gold, deep-indigo, sea-green, ivory, olive, violet, pearl-white, ember-orange) some of them gently shift their humanoid stance some adjust their humanoid hands at their sides, at the front of the group young dark-silver cat titan teenager (cold-steel-grey fur, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes, simple dark-grey tunic with a wide leather belt, NO sickle in his humanoid hands yet, NO cuirass, NO skull medallions yet) takes a single slow step forward bringing himself slightly ahead of the line his amber-yellow eyes glow brighter once with defiant brooding teenage focus and lock straight onto the camera, behind the cat titans the living moss-green earth-landscape with TWO GOLDEN-GREEN EYES set into the slopes gazes toward the children warmly the earth-glow pulses softly, the parents (the sky-dome above and the earth-landscape below) are NOT humanoid — only the twelve cat titans are humanoid bipedal cat figures in the frame, all cat muzzles stay firmly closed in silent ceremony, camera completely static, no camera pan, no camera zoom, slow epic ceremonial pace, epic warm cinematic lighting with starlit accents from above, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, no shouts, no speech, all cats humanoid bipedal upright on two legs, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 6 seconds.
**Звуки:** торжественный низкий хорал рождения титанов (solemn low titan-birth chorale), тихий шорох двенадцати ног по мху (quiet twelve-feet-on-moss rustle), мягкое биение материнской земли (soft mother-earth heartbeat), едва слышный звон амбиций молодого титана (faint young-titan ambition chime).

---

## Сцена 15 (sent_016 + sent_017 — циклопы на переднем плане, многорукие гекатонхейры за ними)

Одна картинка-вход покрывает оба коротких соседних предложения («Следом — три одноглазых циклопа-кузнеца. И трое сторуких гекатонхейров.»). Кадр статичен, разные движения в Veo создают «два шота» в монтаже — `scene_15_01.mp4` (фокус на циклопов) и `scene_15_02.mp4` (фокус на гекатонхейров).

### Сцена 15, шот 1 (sent_016 — «Следом — три одноглазых циклопа-кузнеца»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_15_v1.jpg

**Промпт:** three cyclops forge sparks foreground, three anthropomorphic bipedal cat blacksmith brothers stand in a row at the foreground of the frame each with ONE LARGE ROUND EYE in the middle of his forehead (one cyclops with an amber eye on the left, one with an electric-white eye in the centre, one with a gold eye on the right) their single eyes blink once in unison and steady their gaze forward, the cyclops cats slowly raise and lower their humanoid hands holding their tools — the left brother raises his heavy iron hammer once in a slow firm motion the central brother slowly turns the bronze tongs holding a glowing ember the right brother taps a small dark anvil once gently with his humanoid hand, warm forge sparks flick upward from the glowing ember and the anvil in a slow upward drift the warm forge glow flickers across the cyclops faces, leather blacksmith aprons and bronze arm bracers stir slightly with the movement, in the background out of focus the three many-armed cat granite giants tower silently behind them their many small fan-arms barely visible flexing in the soft blur, in the far background the living moss-green earth with its two golden-green eyes and the living silvery-blue starry sky-dome with its two icy pale-blue star-cluster eyes stay steady — the parents are NOT humanoid, only the cyclops and giant cats are humanoid figures, all cat muzzles stay firmly closed, camera completely static, no camera pan, no camera zoom, slow forge-work pace, split cinematic lighting (warm forge-fire on the cyclops in front, cool moody dark-stone light on the giants behind), no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, all cats humanoid bipedal upright on two legs, NO two eyes on any cyclops only ONE single round eye per cyclops, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** ритмичный звон молота по наковальне (rhythmic hammer-on-anvil ring), потрескивание раскалённого угля в клещах (crackling hot-coal in tongs), тёплый шёпот кузнечного огня (warm forge-fire whisper), мягкий хруст кожаного фартука (soft leather-apron creak).

### Сцена 15, шот 2 (sent_017 — «И трое сторуких гекатонхейров»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_15_v1.jpg *(та же, что у шота 1)*

**Промпт:** hecatoncheires fan arms flexing background, three towering anthropomorphic bipedal cat granite giants step slightly forward from the background of the frame becoming the new focal point while the three one-eyed cat blacksmith brothers in the immediate foreground hold still in a slight soft blur, the granite-grey giants tower twice the height of the cyclops their dark granite-stone fur with cracked rock vein patterns visibly cracks pulse faintly with inner ember-orange glow, EACH GIANT HAS MANY ARMS — six large primary arms (three on each side of the body) raise and lower their main weapons in slow alternating gestures (the left giant raises clubs and boulders, the central giant swings iron chains and stone hammers, the right giant brandishes jagged boulders and stone spears) PLUS a dense radial fan of about ten additional smaller secondary arms sprouting from the shoulders and back of each giant flex and gesture in different directions like a halo of hands the fan-arms rippling like a wave of motion, glowing ember-orange eyes (one face per giant — single head one face only, NOT many heads) blink once and steady their gaze forward, the single-head silhouette of each giant remains unmistakable, in the far background the living moss-green earth and the living silvery-blue starry sky-dome with their respective eye-clusters stay steady — the parents are NOT humanoid, only the giant cats and the cyclops cats are humanoid figures, all cat muzzles stay firmly closed, camera completely static, no camera pan, no camera zoom, slow looming power-display pace, dark stone-and-cold-mist atmospheric lighting with crimson ember highlights from the giants' eyes and from the cracked rock veins, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, all cats humanoid bipedal upright on two legs, EACH GIANT HAS MANY ARMS forming a hundred-handed silhouette, single head one face per giant, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** низкий каменный шорох движения гигантов (low giant-stone-movement rustle), мягкий лязг цепей и шум камней в руках (soft chain-clink and stone rumble), глубокий каменный гул просыпающейся силы (deep awakening-stone-power hum), едва слышное гудение веера сотен рук (faint hundred-arms fan hum).

---

## Сцена 16 (sent_018 — клиффхэнгер: два шота под одно длинное предложение)

Длинный клиффхэнгер 9–11 сек, монтируется в два визуальных шота: первая половина под «Уран возненавидел собственных детей и не позволил им выходить на свет», вторая под «Но он не знал, что один из них уже точит на него серп».

### Сцена 16, шот 1 (sent_018a — Уран запирает чудовищных детей)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_16a_v1.jpg

**Промпт:** angry sky pressing earth burying children, the living silvery-blue starry sky-canopy entity in the upper third of the frame visibly darkens as thick black storm clouds gather slowly across the constellations covering more and more of the star-points, faint white lightning flashes crackle once and then again between the stars in slow dramatic strikes, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES narrow into hostile slits within the constellation pattern their glow burns brighter once with cold hatred, the dome edges curve downward and press low against the earth like a heavy lid the pressure visible in the bowed canopy line, in the lower half the living moss-green earth-landscape entity visibly suffers as thin glowing warm-orange CRACKS of light slowly creep across the hillsides like wounds opening in the ground in slow motion, the oak roots dry out and darken the grape vines wither the small wildflowers wilt, TWO LARGE GOLDEN-GREEN EYES in the hillsides slowly half-close becoming wet and tired GOLDEN TEAR-STREAMS of glowing molten gold begin to run down from each earth-eye in long ribbons across the moss-green slopes flowing slowly downhill, between the sky and the earth visible the half-buried silhouettes of three one-eyed cat blacksmith brothers and three many-armed cat granite giants (each giant with a fan of many arms creating an unmistakable hundred-handed silhouette) sink slowly into the moss-green ground as the sky-dome above pushes them down their buried cat-silhouettes glow faintly from within the earth as prisoners held inside, the parents (sky-dome above and earth-landscape below) are NOT humanoid — they suffer through their own elements only the cyclops and giant cats are humanoid figures, no blood no wounds no gore on any figure only emotional landscape and sky suffering, camera completely static, no camera pan, no camera zoom, slow tragic oppressive pace, dark moody cinematic lighting with cold lightning from above and warm cracked earth-glow from below, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the sky or the earth, NO body, NO hands, NO arms, NO mouth, NO face on either parent-entity, EACH GIANT HAS MANY ARMS forming hundred-handed silhouette, ONE single round eye per cyclops, no blood, no gore, no wounds, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 5 seconds.
**Звуки:** глубокий гневный гул надвигающейся бури (deep wrathful storm-gathering rumble), резкий треск далёкой молнии (sharp distant lightning crack), низкое стонущее эхо страдающей земли (low groaning suffering-earth reverb), мягкое сочение золотых ручейков по холмам (soft golden-tear-stream trickle), приглушённый стон котов-детей уходящих под землю (muffled buried-children moan).

### Сцена 16, шот 2 (sent_018b — молодой Кронос в тенях точит серп)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_16b_v1.jpg

**Промпт:** young cat sharpening adamant sickle in shadow, young dark-silver cat titan teenager crouches in deep secretive shadow over a low whetstone in the foreground his humanoid hands grip a curved jagged dark adamant sickle and slowly draw the blade across the stone whetstone in a long careful stroke (cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes glowing in the dark, simple dark-grey tunic with a wide leather belt, lean athletic frame, humanoid body proportions, crouched on two legs), a single bright orange spark flies off the sickle blade slowly into the air rising upward then fading, the amber-yellow eyes glow brighter once with focused intent the cat muzzle stays firmly closed in concentrated silence, the rest of the foreground stays in deep low-key shadow with only the sickle-spark as a focal point of warm light, far above in the distant background the living silvery-blue starry sky-canopy entity is visible as a faint star-dome with TWO ICY PALE-BLUE STAR-CLUSTER EYES turned aside toward the opposite horizon NOT looking down at the young titan cat unaware of him, the sky-dome is NOT humanoid — just the distant dome with eyes turned away, no other figures in the foreground except the young dark-silver cat titan teenager, his cat muzzle stays firmly closed throughout, all four limbs in humanoid posture, camera completely static, no camera pan, no camera zoom, slow tense secretive pace, tense low-key cinematic lighting with a single warm spark as focal point against deep shadow, no on-screen text, no letters, no titles, NO humans, NO people, NO real four-legged cats, the young titan cat is humanoid bipedal crouched on two legs his hands are humanoid hands holding the sickle and whetstone, no blood, no gore, no wounds, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 5 seconds.
**Звуки:** медленное металлическое скольжение лезвия по точильному камню (slow metallic blade-on-whetstone scrape), сухой треск отлетающей искры (dry flying-spark crack), приглушённое сосредоточенное дыхание молодого титана (muffled focused titan-breath), отдалённый гул отвёрнутого ничего не подозревающего неба (distant unaware sky-dome hum), едва слышный звон рождающейся мести (faint nascent-vengeance chime).

---

## Сцена 17 (sent_019 — «Подпишись, чтобы не пропустить следующую часть»)

**Изображение:** content/От Хаоса до Олимпа/часть_01_Хаос/images/approved_images/scene_17_v1.jpg

**Промпт:** finale subscribe foreshadow tableau, a wide atmospheric closing tableau holds completely still with subtle continuous element-motion to keep the viewer's thumb still while the call-to-action title plate appears in editing, in the upper third of the frame the living silvery-blue starry sky-canopy entity holds as a vast star-dome with dark storm clouds drifting slowly across the constellations TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES proud and cold gaze down from the constellation pattern blinking once slowly, in the lower half of the frame the living moss-green earth-landscape entity holds as moss-green and earth-brown hillsides with thin glowing warm-orange CRACKS of light running across the slopes like wounds the cracks pulse faintly once, TWO LARGE GOLDEN-GREEN EYES in the central hillsides stay lowered and tired their glow muted a single thin GOLDEN TEAR-STREAM of glowing molten gold runs slowly down from the central earth-eye along the slope of the hill, faint silhouettes of twelve anthropomorphic bipedal cat titans scattered across the hillsides in soft focus at varying depths stand still as silent witnesses, in the foreground left corner a dark whetstone with a curved jagged dark adamant sickle lying on it and a single bright orange spark hovering slowly above and fading — an unmistakable hint toward the young titan cat to come, the central vertical area of the frame is intentionally left visually quiet to leave room for an overlaid subscribe-call-to-action title plate in editing, camera completely static, no camera pan, no camera zoom, slow atmospheric closing pace, atmospheric cool-and-warm cinematic lighting (cool starlight above, warm cracked earth-glow below, single warm spark on the foreground sickle), no on-screen text, no letters, no titles in the video itself, NO humans, NO people, NO real four-legged cats, NO humanoid figure for the sky-dome, NO body, NO hands, NO mouth, NO face on the sky or the earth, only the twelve distant titan cat silhouettes are humanoid bipedal figures in the frame, no blood, no gore, no wounds, No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** торжественный отзвук завершения первой части (solemn part-one-closing reverb), глубокое биение земли вдалеке (deep distant earth-heartbeat), холодный звон далёких звёзд (cold distant-star chime), едва слышный треск тлеющей искры на серпе (faint smoldering-sickle-spark crackle), отдалённый намёк на грядущую месть (distant hint of coming vengeance).

---

## Чек-лист перед запуском Veo (сверять перед каждой генерацией)

Берём из [CONTEXT.md](../../../../CONTEXT.md) → «IP-фильтр Veo» + [GENEALOGY.md](../../../../GENEALOGY.md) → шаг 10 + [CONTEXT.md](../../../../CONTEXT.md) → «Правила промптов для анимации». В этой части два класса персонажей — **абстрактные сущности-стихии с глазами** (Хаос, Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран) и **антропоморфные коты** (молодой Кронос, 12 титанов, циклопы, гекатонхейры). Проверки разные для двух классов.

1. **Никаких греческих имён в `**Промпт:**`.** Veo блокирует `Chaos / Gaia / Tartarus / Eros / Erebus / Nyx / Aether / Hemera / Uranus / Cronus / Olympus`. Везде вместо них — descriptive из IP-фильтра в шапке файла. Проверить:

   ```bash
   grep -nE 'Chaos|Gaia|Tartarus|Eros|Erebus|Nyx|Aether|Hemera|Uranus|Cronus|Olympus' \
     "content/От Хаоса до Олимпа/часть_01_Хаос/prompts/video.md" \
     | grep -v '<!--'
   ```

   Должно быть пусто. Имена допустимы только в комментариях `<!-- ... -->` и заголовках на русском.

2. **Уникальный subject-маркер.** Первые 3–4 слова каждого `**Промпт:**` отличаются от соседних. Проверить:

   ```bash
   grep '^\*\*Промпт:\*\* ' "content/От Хаоса до Олимпа/часть_01_Хаос/prompts/video.md" \
     | sed -E 's/^\*\*Промпт:\*\* ([^,]+),.*/\1/' \
     | sort | uniq -c | sort -rn
   ```

   Все строки должны быть с числом `1`.

3. **Обязательный негатив в каждом промпте.** `No speech, no dialogue, no talking, no voices, no mouth movement, no music`. Также избегать слов-триггеров: `shouts, says, speaks, tells, laughs, screams, yells, calls out, sings, cries out`.

4. **Класс «абстрактные сущности» — НЕТ humanoid в анимации.** Для Геи, Тартара, Эроса, Эреба, Никты, Эфира, Гемеры, Урана в промпте обязательно `NO humanoid figure for the entity, NO body, NO hands, NO arms, NO mouth, NO face — only the abstract entity itself with its eyes`. Никаких `humanoid body proportions` или `standing upright on two legs` для них. Эмоция читается только через изменение стихии (трещины, тучи, слёзы по холмам, потускневшее свечение, золотистая пульсация).

5. **Класс «антропоморфные коты» — ЕСТЬ humanoid.** Для молодого Кроноса, 12 титанов, циклопов, гекатонхейров — `humanoid body proportions, standing upright on two legs` или `crouched on two legs`. Если в промпте есть `hand`, `arm`, `foot`, `knee` для котов — обязательно `humanoid hand` / `humanoid arm` / `humanoid feet`.

6. **Циклопы — ОДИН глаз.** Сцена 15, шот 1, и Сцена 16, шот 1 (силуэты) — `ONE large round eye in the middle of each forehead`, обязательно повторено отрицание `NO two eyes only ONE single round eye per cyclops`.

7. **Гекатонхейры — МНОГО рук, одна голова.** Сцена 15, шот 2, и Сцена 16, шот 1 (силуэты) — `EACH GIANT HAS MANY ARMS — six large primary arms PLUS a fan of about ten additional smaller secondary arms, hundred-handed silhouette`. Голова **одна**: `single head one face per giant, NOT many heads`.

8. **Кронос в ч. 1 — БЕЗ бороды.** Сцены 14 (в массе титанов) и 16, шот 2 (точит серп) — `CLEAN-SHAVEN no beard yet`. Серп есть только в Сцене 16, шот 2 (и как «улика» на точиле в Сцене 17).

9. **Без камеры-движения.** Камера статична во ВСЕХ сценах. `camera completely static, no camera pan, no camera zoom`. Это правило канала (см. CONTEXT.md → «Правила промптов для анимации»). Veo сам добавит парallax/breath к стихиям — этого достаточно.

10. **Без речи.** Все коты — `cat muzzles stay firmly closed`. Никаких `shouts`, `says`, `speaks`, `tells`, `laughs`, `screams`, `yells`, `calls out`. Эмоция через позу, жест, направление взгляда. Абстрактные сущности без рта по определению.

11. **Без зумов в стихиях.** Сущности «дышат» сами по себе (концентрические пульсы, мерцание глаз, ленивый дрейф искр). НЕ просить Veo сделать `slow zoom in/out` — снэп к кадру и таймстретч в CapCut (см. memory feedback_capcut_frame_snap_robovoice).

12. **Модерация TikTok/Shorts.** Сцены 16, шот 1; 16, шот 2; 17 — добавлено `no blood, no gore, no wounds`. В Сцене 16, шот 1 силуэты заперты под землю — никаких ран, тел, костей; только свечение из земли. В Сцене 16, шот 2 — серп на точиле, без размахивания и без угрозы конкретной мишени в кадре.

13. **`-style` отсылки запрещены.** Veo блокирует `Hades-style`, `God of War style`, `Marvel-style`. Описывать эффекты через физику: «slow concentric pulses», «curved magnetic lines», «hundred-handed silhouette», а не через названия франшиз. См. memory feedback_veo_no_pop_culture_ip.

14. **Длительность каждого шота кратна 1 секунде** и **≤7 сек** для надёжной генерации Veo. Объединённый хук+титул (sent_001+002, ≈9–11 сек аудио) укладывается в один Veo-шот 7 сек — остаток покрывается монтажным freeze-frame или удлинением последнего кадра в pyCapCut. Sent_015 (≈6–7 сек) укладывается в один шот по 6–7 сек.

15. **Маппинг сцен 1:1 с images.md.** Нумерация сцен в video.md совпадает с images.md (17 сцен). Если в images.md одна сцена покрывает два предложения с общей картинкой (sent_001+002 → Сцена 01, sent_016+017 → Сцена 15), то в video.md это **одна сцена** с одним или несколькими шотами под общим заголовком `## Сцена NN`, а не два соседних `## Сцена NN` / `## Сцена NN+1`. См. memory `feedback_intro_single_unit` и `feedback_scene_audio_pipeline`.

---

## Журнал

- **2026-05-17** — Файл создан. 22 видео-шота на 21 предложение (sent_001+sent_002 = два шота с общей картинкой, sent_018+sent_019 = два шота с общей картинкой, sent_020 = два шота с двумя картинками). IP-фильтр Veo прописан в шапке (имена первобожеств → descriptive). Subject-маркеры уникальны для всех 22 промптов. Чек-лист в конце файла под два класса персонажей (абстрактные сущности vs антропоморфные коты).
- **2026-05-17** — **Выравнивание нумерации сцен под images.md (19 сцен, 20 шотов).** Объединены пары соседних `## Сцена NN` / `## Сцена NN+1`, которые делили одну картинку в images.md:
  - Бывшие `## Сцена 01 (sent_001)` + `## Сцена 02 (sent_002)` → одна `## Сцена 01 (sent_001 + sent_002 — хук + титул караоке поверх)` с **одним** видео-шотом (7 сек). Промпт описывает медленное «дыхание» void с переходом во вторую половину к более стабильному ритму, чтобы караоке-плашка ложилась в монтаже поверх того же кадра. Аудио sent_001+002 (≈11–13 сек) покрывается одним 7-сек Veo-шотом плюс монтажный freeze-frame в pyCapCut. См. memory `feedback_intro_single_unit`.
  - Бывшие `## Сцена 18 (sent_018)` + `## Сцена 19 (sent_019)` → одна `## Сцена 17 (sent_018 + sent_019)` с двумя подзаголовками `### Сцена 17, шот 1` и `### Сцена 17, шот 2`. Картинка та же (`scene_17_v1.jpg`), разные движения камеры/фокуса в Veo. Этот же стиль уже использовался для клиффхэнгера sent_020.
  - Перенумерация: бывшая Сцена 03 → Сцена 02, бывшая 04 → 03, …, бывшая 17 → 16. Бывшие `## Сцена 20, шот 1` / `## Сцена 20, шот 2` → `## Сцена 18 (sent_020 — клиффхэнгер)` с подзаголовками `### Сцена 18, шот 1` / `### Сцена 18, шот 2`. Бывшая Сцена 21 → Сцена 19.
  - Видео-файлы переименованы по новой нумерации: `scene_01_01.mp4` (один шот вместо двух), `scene_17_01.mp4` + `scene_17_02.mp4` (вместо `scene_18_01.mp4` + `scene_19_01.mp4`), `scene_18_01.mp4` + `scene_18_02.mp4` (клиффхэнгер, вместо `scene_20_01.mp4` + `scene_20_02.mp4`), `scene_19_01.mp4` (финал, вместо `scene_21_01.mp4`). Картинки-входы в `images/approved_images/` уже были названы по нумерации images.md и не требуют переименования.
  - Чек-лист дополнен пунктом 15 (маппинг 1:1 с images.md). Пункт 14 переписан под объединённый хук+титул-шот. Итого: 20 видео-шотов на 19 сцен.
- **2026-05-18** — **Сцена 01 переделана: «пустая дышащая туманность» → «Око Хаоса открывается».** Прежний промпт описывал плавные концентрические пульсы тёмной пустоты — это работало как фон, но не как stop-scroll. Новый промпт: в первые 2 секунды веко-туманность раскрывается и в верхней половине кадра появляется гигантский янтарно-золотой глаз с радужкой-микрокосмосом и зрачком-воронкой, моргает раз и держит взгляд прямо на камеру; на «Хаос» в озвучке золотая ember-tear отделяется от уголка глаза и стекает в туманность ниже; вторая половина шота — спокойный взгляд + успокоение туманности под караоке-плашку. Звуки тоже доработаны (добавлен «шёлковый звон открывающегося ока» в первые 2 сек). Картинка-вход (scene_01_v1.jpg) тоже переделана — синхронно правится images.md, Сцена 1. Это даёт двойной крючок «нечто живое смотрит» + «движение в кадре в первые 2 сек», не нарушая правило канала «камера статична» (двигается само око, не камера).
- **2026-05-18** — **Удалены Сцены 02 и 03 (два тёмных Хаос-кадра) — переделка интро.** До правки между хуком+титулом и первой Геей-сценой стояли два полностью тёмных Хаос-кадра (sent_003 «boundless cosmic void radial drift» + sent_004 «first stir spark»). Три тёмных сцены подряд (Сцены 01, 02, 03) гарантировали высокий churn на первых 12–15 секундах ролика. Теперь после титула (~9–11 сек хук+титул) сразу Сцена 02 = Гея открывает глаза — контраст «тёмно-фиолетовый → мшисто-зелёный с золотыми глазами» удерживает зрителя. Перенумерация: бывшие Сцены 04–17 → 02–15, бывшая Сцена 18 (клиффхэнгер sent_020) → Сцена 16 (sent_018), бывшая Сцена 19 (CTA sent_021) → Сцена 17 (sent_019). Все sent-номера сдвинуты на −2. Все пути в `**Изображение:**` обновлены под новые `scene_NN_v1.jpg`. Картинки клиффхэнгера переименованы: `scene_18a_v1.jpg` → `scene_16a_v1.jpg`, `scene_18b_v1.jpg` → `scene_16b_v1.jpg` (само переименование файлов в `images/approved_images/` — отдельный шаг, ждёт). Обновлены маппинг-таблица, пункты 6–8, 12, 14, 15 чек-листа. Итого: **18 видео-шотов на 17 сцен** (было 20 на 19).
