# Промпты картинок: Часть 1 — Хаос и первобожества

Промпты картинок-входов для Google Flow / ImageFX. Одна картинка = один кадр сцены. Видео потом строится через image-to-video, см. [video.md](video.md) (после генерации картинок).

Маппинг **картинка ↔ предложение** идёт по [voiceover.md](voiceover.md) → «Разбивка на предложения». В этой части — **18 картинок на 17 сцен** (хук+титул = одна сцена с одной картинкой; цикл+гекатонхейры — одна сцена с одной картинкой для двух коротких предложений; клиффхэнгер sent_018 — длинный, на него два шота с двумя картинками).

Карточки персонажей **дословно из [../../characters.md](../../characters.md)** — см. HTML-комментарий ниже. При написании промпта новой сцены копировать английский блок целиком, не пересказывать.

См. также:

- [CONTEXT.md](../../../../CONTEXT.md) → «Персонажи» (антропоморфность, NO humans, NO real cats), «Стилевой каркас промптов», «Уникальный subject-маркер», «Визуальное разнообразие».
- [MYTH.md](../../../../MYTH.md) → шаг 7 (чек-лист промптов: волосы в каждой сцене, голые части тела `humanoid`).
- [GENEALOGY.md](../../../../GENEALOGY.md) → шаг 7 (сериал — обязательная сквозная консистентность).

---

<!-- ============================================================
     КАРТОЧКИ ПЕРСОНАЖЕЙ ЧАСТИ — копия из ../../characters.md
     При написании промпта брать ТОТ ЖЕ английский блок ДОСЛОВНО.
     Модель Flow не помнит карточку из шапки — её надо повторить В САМОМ ПРОМПТЕ.

     ВНИМАНИЕ: в этой части ДВА визуальных класса персонажей.
     - ПЕРВОБОЖЕСТВА (Хаос, Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран) =
       абстрактные сущности-стихии с глазами. NO humanoid figure, NO body, NO hands.
       Эмоции — через изменения самой стихии (трещины, тучи, тусклый свет, слёзы по холмам).
     - КОТЫ (Кронос, 12 титанов, циклопы, гекатонхейры) = антропоморфные бипедальные коты.
       humanoid body proportions, standing upright on two legs.
     ============================================================

     ХАОС:
     swirling primordial Chaos void, deep violet and charcoal nebula,
     faint warm-gold embers drifting inside, no face, no body, no figure,
     vast cosmic emptiness, soft glow at the edges

     ГЕЯ (живой пейзаж-сущность; ч. 1 — спокойная; sent_014 — потускневшая;
     sent_015 — решимость; sent_020a/021 — страдающая, золотые слёзы по холмам):
     Gaia the living primordial earth-landscape entity,
     a vast rolling terrain of dark-moss-green and earth-brown soil
     with oak roots, grape vines and small wildflowers growing across it,
     TWO LARGE GLOWING GOLDEN-GREEN EYES set into the earth itself
     (one on the central hillside, one on a nearby slope) gazing upward
     with primordial awareness, faint warm earth-glow pulsing beneath
     the surface like slow breathing,
     NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face

     ТАРТАР (живая бездна-сущность):
     Tartarus the living primordial abyss entity, a bottomless dark chasm
     of anthracite-black rock with glowing crimson lava-vein patterns
     cracking through the walls, TWO FAINT CRIMSON DOT-EYES glowing
     deep inside the darkness at the bottom of the pit, descending into
     endless darkness,
     NO humanoid figure, NO body, NO hands, NO face

     ЭРОС (живая сила-сфера с глазами):
     Eros the primordial attraction-force entity, a glowing radiant
     pink-and-gold cosmic light orb floating in space, TWO LARGE GLOWING
     AMBER ALMOND EYES at its center gazing outward calmly,
     soft pink-and-gold concentric attraction rings radiating outward,
     NO humanoid figure, NO body, NO hands, NO mouth, NO face

     ЭРЕБ (живой Мрак-облако с глазами):
     Erebus the primordial darkness entity, a swirling pool of
     ash-grey-and-soot dark mist forming a sentient cloud,
     TWO AMBER GLOWING EYES WITH DARK RINGS shining from within the dark
     mist, ink-black tendrils of shadow drifting outward like wisps of
     smoke,
     NO humanoid figure, NO body, NO hands, NO mouth, NO face

     НИКТА (живая Ночь-облако с глазами):
     Nyx the primordial night entity, a deep blue-black living night-sky
     cloud dusted with tiny white star points, TWO LARGE SILVER FULL-MOON
     EYES shining from within the night-mist, drifting silver lunar
     crescent shapes circling around the cloud like tiny moon phases,
     NO humanoid figure, NO body, NO hands, NO mouth, NO face

     ЭФИР (живой небесный Свет-облако с глазами):
     Aether the primordial heavenly-light entity, a bright glowing
     ivory-and-pale-gold light cloud floating in the air, TWO PALE-BLUE
     GLOWING EYES shining from within the light, soft gold rays radiating
     outward,
     NO humanoid figure, NO body, NO hands, NO mouth, NO face

     ГЕМЕРА (живой День-облако с глазами):
     Hemera the primordial day entity, a warm glowing peach-and-rose-gold
     dawn-light cloud floating in the air, TWO WARM AMBER GLOWING EYES
     shining from within the dawn-mist, gentle pastel sunrise-pink rays
     radiating outward,
     NO humanoid figure, NO body, NO hands, NO mouth, NO face

     УРАН (живое Небо-купол с глазами; ч. 1 рождение — спокойный звёздный
     купол; ч. 1 финал — гневное небо, тучи и молнии):
     Uranus the living primordial sky-canopy entity, a vast silvery-blue
     starry sky-dome stretched across the upper portion of the frame
     filled with star points and constellations, drifting silver clouds
     across the dome, TWO ICY PALE-BLUE GLOWING EYES formed by especially
     bright star clusters within the constellation pattern gazing downward
     at the earth, the dome edges curving downward toward the horizon
     like a canopy,
     NO humanoid figure, NO body, NO hands, NO arms, NO crown,
     NO mantle, NO face

     КРОНОС (ч. 1 — МОЛОДОЙ титан, БЕЗ бороды, БЕЗ седины, серпа ещё нет;
     дерзкий взгляд — маркер «вот этот будет важен в ч. 2»):
     young Cronus the anthropomorphic bipedal cat titan teenager,
     cold-steel-grey fur with subtle silver streaks, short shoulder-length
     dark-silver hair, CLEAN-SHAVEN no beard, sharp amber-yellow predator eyes,
     dressed in a simple dark-grey tunic with a wide leather belt (no cuirass
     yet, no skull medallions yet — those come in ч. 2), lean athletic frame,
     defiant brooding teenage face, humanoid body proportions, standing
     upright on two legs

     ПРОЧИЕ ТИТАНЫ (массовка, 12 штук):
     twelve anthropomorphic bipedal cat Titans gathered together,
     each in a distinctive metallic or elemental palette — bronze, copper,
     silver, steel, gold, deep-indigo, sea-green, ivory, olive, violet,
     pearl-white, ember-orange — varied robes of bronze and linen with
     elemental motifs (waves, stars, wheat, moonlight), humanoid body
     proportions, standing upright on two legs

     ЦИКЛОПЫ (Бронт, Стероп, Арг):
     three Cyclops anthropomorphic bipedal cat blacksmith brothers —
     Brontes Steropes Arges — massive muscular frames,
     short stone-slate-grey fur,
     ONE large round eye in the middle of each forehead (NO two eyes,
     ONE single round eye in the center of the forehead),
     Brontes has amber eye, Steropes has electric-white eye, Arges has gold eye,
     bare muscular torsos with leather blacksmith aprons, bronze arm bracers,
     holding hammers and tongs and anvils, humanoid body proportions,
     standing upright on two legs

     ГЕКАТОНХЕЙРЫ (Котт, Бриарей, Гиес) — «сторукие»:
     three Hecatoncheires anthropomorphic bipedal cat hundred-handed giants —
     Cottus Briareus Gyges — towering even larger than the titans,
     dark granite-stone fur with cracked rock vein patterns,
     shaved or stubble heads, glowing ember-orange eyes,
     EACH GIANT HAS MANY ARMS — six large primary arms
     (three on each side of the body) holding the main weapons,
     PLUS a dense radial fan of about ten additional smaller secondary arms
     sprouting from the shoulders and back creating an unmistakable
     hundred-handed silhouette, the additional fan-arms gesturing and
     flexing in different directions like a halo of hands,
     bare granite-grey torsos, primary arms holding different weapons —
     clubs boulders chains stone hammers stone spears,
     single head one face per giant (NOT many heads — one face only),
     humanoid body proportions, standing upright on two legs
     ============================================================ -->

<!-- ============================================================
     СТИЛЕВОЙ КАРКАС (см. CONTEXT.md → «Стилевой каркас промптов»):
     highly detailed pixel art, 9:16 vertical composition,
     modern detailed pixel art style, [LIGHTING], no text, no letters,
     no camera movement

     ОБЩИЕ НЕГАТИВЫ (всегда в конце промпта):
     NO humans, NO people, NO real four-legged cats,
     no blood, no gore, no wounds

     ДОПОЛНИТЕЛЬНЫЕ НЕГАТИВЫ ДЛЯ СЦЕН С ПЕРВОБОЖЕСТВАМИ
     (Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран):
     NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face,
     only the abstract entity-form with eyes

     В СМЕШАННЫХ СЦЕНАХ (титаны-коты на фоне Геи-земли под Ураном-небом):
     антропоморфность пишется только для котов-титанов/циклопов/гекатонхейров,
     а для первобожеств-фонов добавляется «NO humanoid figure for Gaia/Uranus,
     they are the landscape and sky themselves».
     ============================================================ -->

---

## Сцена 1 (sent_001 + sent_002 — хук «До начала времени был только Хаос» + титул караоке поверх)

**Краткое описание кадра.** Stop-scroll крючок: гигантское Око Хаоса проступает из клубящейся туманности в верхней половине кадра и смотрит прямо на зрителя. Око сделано из самого Хаоса — веко = изогнутая полоса фиолетово-угольной туманности, радужка = янтарно-золотой диск с микрокосмосом завихрений внутри (туманность В туманности), зрачок = глубокая чёрная воронка-бездна. Из уголка глаза в туманность ниже стекает одинокая золотистая «слеза»-искра. Нижняя половина кадра — обычная клубящаяся пустота Хаоса с золотыми искрами, в эту тихую зону в монтаже ложится накопительная караоке-плашка «ОТ ХАОСА → ДО ОЛИМПА → ЧАСТЬ 1». Психологический крючок: «нечто живое смотрит на меня». Дополнительно — это завязка под визуальную рифму всего сериала «стихия с глазами»: в Сцене 2 у Геи в холмах открываются такие же огромные светящиеся глаза, потом у каждого первобожества свой набор глаз.

**Промпт:** giant cosmic eye of chaos opening in the void as the opening cosmogony shot, a single enormous glowing amber-and-gold cosmic EYE formed from the primordial swirling void itself dominating the upper half of the frame, the eyelid is a curved band of dark violet and charcoal nebula clouds wrapping above and below the eye, the iris is a glowing amber-and-warm-gold disk with tiny swirling nebula-clouds drifting inside it like a microcosm of chaos within the eye, the pupil at the center is a deep black abyss-vortex with faint warm-gold sparks spiraling into it, the eye gazes directly at the viewer with primordial awareness, a single warm-gold ember-tear droplet hanging at the lower corner of the eye about to fall into the void below, the lower half of the frame filled with the deep violet and charcoal Chaos nebula clouds with faint warm-gold embers drifting slowly inside the swirling clouds, soft warm-gold halo radiating around the cosmic eye into the surrounding dark void, no horizon line, only the endless cosmic emptiness beneath the watching eye, the lower vertical area of the frame intentionally kept visually quiet to leave room for an overlaid karaoke title plate in editing, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face apart from the single cosmic eye — the eye IS the entity, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dark cinematic lighting with warm amber-gold focal glow from the eye and gentle violet-charcoal edges, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 2 (sent_003 — «И вдруг в этой тьме родилась Гея — Земля»)

**Краткое описание кадра.** Сразу после титула — поворотная точка ролика. Из отступающей вверх тёмной туманности Хаоса в нижней половине кадра проявляется живая земля-сущность: пологие моховые холмы и тёмная почва, на двух точках поверхности (центральный холм и ближний склон) открываются два огромных золотисто-зелёных глаза. Никакой фигуры — только сама земля с парой глаз. Это первая «светлая» картинка ролика после двух тёмных секунд хука+титула.

**Визуальная рифма со Сценой 1.** В Сцене 1 Око Хаоса смотрит из туманности сверху и в финале сцены закрывается. В Сцене 2 туманность Хаоса откатывается вверх, открывая новую землю, и **два** глаза Геи открываются в холмах внизу — как ответ оку Хаоса, как продолжение «жеста открытия глаз». Это первый штрих к визуальной концепции сериала «каждая стихия = существо с глазами».

**Промпт:** earth-landscape entity awakens from chaos as the living primordial ground takes shape, Gaia the living primordial earth-landscape entity emerging in the lower half of the frame, a vast rolling terrain of dark-moss-green and earth-brown soil with oak roots, grape vines and small wildflowers growing across it, TWO LARGE GLOWING GOLDEN-GREEN EYES set into the earth itself (one on the central hillside, one on a nearby slope) just opening for the first time and gazing upward with primordial awareness, faint warm earth-glow pulsing beneath the surface like slow breathing, the deep violet and charcoal Chaos nebula receding upward into the background behind the landscape, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with the two golden-green eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm cinematic lighting with green-gold under-glow, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 3 (sent_004 — «Широкая, твёрдая, надёжная опора всему, что будет»)

**Краткое описание кадра.** Земля-сущность раскинулась во всю ширину кадра. Низкий ракурс снизу-вверх подчёркивает «опору»: видны мощные обнажённые корни, поросшие мхом валуны, зелёные побеги пробиваются вверх. Два золотисто-зелёных глаза в холмах смотрят спокойно и уверенно. Тёплое свечение из недр.

**Промпт:** primordial earth foundation spreads wide and firm across the world, Gaia the living primordial earth-landscape entity occupying the entire lower frame, vast rolling hillsides of dark-moss-green and rich earth-brown soil extending to the horizon, massive exposed oak roots gripping mossy boulders, small bright green shoots pushing up everywhere across the surface, grape vines wrapped around the rocks, small wildflowers, TWO LARGE GLOWING GOLDEN-GREEN EYES set deep into the hillsides (one on the central rise, one on a nearby slope) gazing calmly and steadily, faint warm earth-glow pulsing strongly from beneath the surface emphasizing the foundation, low-angle shot from below looking up at the rising landscape, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face, only the living earth itself with the two eyes acting as a foundation for the world to come, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm cinematic lighting with golden-green under-glow, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 4 (sent_005 — «Следом — Тартар, тёмная бездна, что лежит глубже самой Земли»)

**Краткое описание кадра.** Stop-scroll кадр: гигантская горизонтально раскрытая «пасть»-расщелина занимает нижние две трети кадра — как челюсть спящего древнего существа. Сверху и снизу пасти — антрацитово-чёрные скальные «зубы»-сталактиты и сталагмиты, между ними в глубине пасти горят **два огромных багровых глаза Тартара**, смотрящих прямо на зрителя. По стенкам пасти расходятся тлеющие красные жилы лавы. В верхней четверти кадра — тонкая полоса мшисто-зелёных холмов Геи, лежащая на пасти как «крышка», с обнажёнными корнями, свисающими в расщелину. Камера сбоку (не сверху-вниз) — мы видим Тартар как огромную чудовищную пасть, прорезающую кадр поперёк. Никакого «обрушения», никакого падения вниз — статичная, угрожающая, фронтальная композиция.

**Промпт:** giant abyss-mouth gapes open beneath the earth, a colossal horizontally-opened chasm-mouth dominates the lower two-thirds of the frame like the jaws of a sleeping primordial beast, anthracite-black jagged rock teeth-stalactites hang down from the upper lip of the mouth and matching stalagmites jut up from the lower lip framing a wide horizontal opening, deep inside the mouth in the darkness TWO ENORMOUS GLOWING CRIMSON EYES of Tartarus the living primordial abyss entity gaze directly outward at the viewer with ancient menace, glowing crimson lava-vein patterns crack along the inner walls of the chasm-mouth radiating outward from around the two eyes like a halo of molten cracks, faint warm crimson under-glow from inside the mouth illuminating the rock teeth from below, no figure inside the chasm — the chasm-mouth itself is the entity, in the upper quarter of the frame a thin band of Gaia's moss-green-and-earth-brown hillsides rests on top of the abyss-mouth like a thin lid with bare oak roots dangling down into the crack and small wildflowers along the edges, view from the side at eye-level with the mouth (NOT looking down into a pit), the chasm cuts horizontally across the frame, NO humanoid figure, NO body, NO hands, NO arms, NO mouth-with-tongue, NO face — only the living abyss itself with the two crimson eyes and the rock-teeth jaws around them, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dark cinematic lighting with deep crimson focal glow from the two eyes and warm lava-vein highlights along the chasm walls, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 5 (sent_006 — «И Эрос — сила, которая притягивает одно к другому»)

**Краткое описание кадра.** В центре кадра — розово-золотая сфера-сущность с двумя крупными янтарными глазами внутри. От сферы расходятся концентрические кольца света. Со всех сторон к сфере по изогнутым траекториям тянутся мелкие космические объекты (звёзды, пылинки, камешки) — это и есть «сила влечения». Никакого тела, тоники, волос — только живой светящийся орб.

**Промпт:** radiant attraction-force orb pulls small cosmic objects toward itself, Eros the primordial attraction-force entity at the center of the frame as a glowing radiant pink-and-gold cosmic light orb floating in space, TWO LARGE GLOWING AMBER ALMOND EYES at its center gazing outward calmly, soft pink-and-gold concentric attraction rings radiating outward from the orb in pulses, small floating cosmic stars and dust particles and pebbles drifting in curved magnetic lines toward the orb from all sides as if pulled in, gentle visible attraction lines glowing soft pink-gold across space, deep violet Chaos nebula far in the background, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living force-orb itself with the two amber eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm cinematic lighting with pink-gold radiance, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 6 (sent_007 — «Без него мир остался бы россыпью отдельных вещей»)

**Краткое описание кадра.** Контр-визуал к предыдущему: те же космические объекты, но БЕЗ Эроса в кадре, разлетаются в разные стороны без связи. Холодное освещение. Это «если бы» — представление, не реальность.

**Промпт:** scattered cosmic objects drifting apart in isolation without bond, small floating stars and rocks and dust particles spread across a vast empty void scattering in different directions with no connection between them, no character in frame, no face, no body, no figure, no aura, the deep violet and charcoal Chaos nebula far in the background, cold lonely composition emphasizing separation, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, cool cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 7 (sent_008 — «Потом пришли Эреб — Мрак, и Никта — Ночь»)

**Краткое описание кадра.** Два соседних абстрактных облака-сущности: слева пепельно-серый дымный сгусток (Эреб) с двумя янтарными глазами, справа иссиня-чёрное звёздное облако (Никта) с двумя серебряными глазами-полнолуниями. Оба выплывают из отступающей фиолетовой туманности Хаоса.

**Промпт:** twin primordial dark entities emerge side by side from chaos, on the left Erebus the primordial darkness entity as a swirling pool of ash-grey-and-soot dark mist forming a sentient cloud, TWO AMBER GLOWING EYES WITH DARK RINGS shining from within the dark mist, ink-black tendrils of shadow drifting outward like wisps of smoke, on the right Nyx the primordial night entity as a deep blue-black living night-sky cloud dusted with tiny white star points, TWO LARGE SILVER FULL-MOON EYES shining from within the night-mist, drifting silver lunar crescent shapes circling around her cloud like tiny moon phases, both cloud-entities floating forward out of the receding deep violet Chaos nebula behind them, NO humanoid figures, NO bodies, NO hands, NO mouths, NO faces — only the two living cloud-entities with their eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dark cinematic lighting with cool silver-blue highlights, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 8 (sent_009 — «Брат и сестра»)

**Краткое описание кадра.** Близкий план двух облаков-сущностей бок о бок. Их края соприкасаются и слегка перетекают друг в друга — это и есть «брат и сестра», родственная близость без позы и жестов. Все четыре светящихся глаза (два янтарных и два серебряных) смотрят вперёд в одну сторону.

**Промпт:** sibling primordial dark clouds touching at their edges, close framing of two living cloud-entities side by side, on the left Erebus the swirling ash-grey-and-soot dark mist cloud with TWO AMBER GLOWING EYES with dark rings and ink-black shadow tendrils, on the right Nyx the deep blue-black night-sky cloud dusted with white star points with TWO LARGE SILVER FULL-MOON EYES and drifting silver lunar crescents around it, the two cloud-edges gently touching and merging where they meet creating a sense of sibling closeness without any romance, all four glowing eyes (amber on the left, silver on the right) all gazing calmly forward in the same direction, dark nocturnal background with faint stars far behind, NO humanoid figures, NO bodies, NO hands, NO arms, NO mouths, NO faces — only the two living cloud-entities with their eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, cool moonlit cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 9 (sent_010 — «От их союза родились Эфир — чистый небесный свет, и Гемера — День»)

**Краткое описание кадра.** Два светлых облака-сущности рождаются между Эребом и Никтой: слева Эфир (ярко-слоновое-кости + бледно-золото с двумя бледно-голубыми глазами), справа Гемера (тёплый персиково-розово-золотой с двумя янтарными глазами). Тёмные родительские облака Эреба и Никты остаются на заднем плане для контраста.

**Промпт:** light-and-day primordial clouds born from the embrace of darkness, in the foreground two new living light-cloud entities emerging side by side, on the left Aether the primordial heavenly-light entity as a bright glowing ivory-and-pale-gold light cloud with TWO PALE-BLUE GLOWING EYES shining from within the light and soft gold rays radiating outward, on the right Hemera the primordial day entity as a warm glowing peach-and-rose-gold dawn-light cloud with TWO WARM AMBER GLOWING EYES shining from within the dawn-mist and gentle pastel sunrise-pink rays radiating outward, both bright cloud-entities emerging from a warm pale-gold glow between their parents, behind them in soft focus the darker parent-clouds visible for contrast (Erebus the ash-grey-and-soot dark mist with amber eyes on the far left, Nyx the deep blue-black star-dusted night cloud with silver moon eyes on the far right), NO humanoid figures, NO bodies, NO hands, NO mouths, NO faces — only the four living cloud-entities with their eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm dawn cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 10 (sent_011 — «Мир обрёл первых жителей. Но он был пуст и тих»)

**Краткое описание кадра.** Общий план первобытного мира. Все семь первобожеств — каждый в своей части пространства, никто не взаимодействует. Гея занимает нижнюю половину как пейзаж, Тартар — провал на краю, Эрос — сфера в центре над землёй, Эреб + Никта — пара облаков справа сверху, Эфир + Гемера — пара светлых облаков слева сверху. Зеркальное озеро отражает все огни. Безветрие.

**Промпт:** seven primordial entities scattered across a vast quiet primordial world, wide establishing shot, Gaia the living moss-green earth-landscape filling the lower half with TWO GOLDEN-GREEN earth-eyes in the hillsides, Tartarus the living dark chasm with TWO CRIMSON DOT-EYES at the lower right edge of the earth, Eros the floating pink-and-gold cosmic light orb with TWO AMBER EYES at the center of the frame above the ground, Erebus the swirling ash-grey-and-soot dark mist cloud with TWO AMBER EYES and Nyx the deep blue-black star-dusted night cloud with TWO SILVER FULL-MOON EYES together at the upper right beside a starry patch, Aether the ivory-and-pale-gold light cloud with TWO PALE-BLUE EYES and Hemera the warm peach-and-rose-gold dawn cloud with TWO AMBER EYES together at the upper left in a warm glowing dawn cloud, all seven entities are abstract living stihiya-clouds and landscape with their eyes — NO humanoid figures, NO bodies, NO hands, NO mouths, NO faces anywhere in the frame, large empty spaces between every entity, a mirror-still lake at the lower center reflecting all the colored lights, mossy hills, no wind, complete silence, no other living creatures in the world yet, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, quiet cinematic lighting mixing all the auras softly, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 11 (sent_012 — «Земле было одиноко»)

**Краткое описание кадра.** Крупный план пейзажа-сущности Геи. Полевые цветы поникли, лозы безжизненно висят, мох потускнел, тёплое свечение из недр ослабло. Два золотисто-зелёных глаза в холмах прикрыты до полуприкрытого состояния и приглушённо мерцают. Лёгкий ветер ворошит листву. Никаких других сущностей в кадре.

**Промпт:** lonely melancholic earth-landscape entity closeup, Gaia the living primordial earth-landscape entity in a medium closeup of her central hillside and nearby slope, dark-moss-green-and-earth-brown soil now slightly dimmer and muted, small wildflowers visibly drooping and limp, grape vines hanging lifelessly across rocks, oak roots looking thirsty, faint warm earth-glow beneath the surface dimmed and slow like a tired heartbeat, TWO LARGE GOLDEN-GREEN EYES set into the hillsides half-lowered and gazing off into the empty distance with quiet primordial melancholy, gentle wind softly ruffling the small wildflower petals and vine leaves, no other entities anywhere in frame, soft blurred background of empty mossy hills and a still mirror-like lake, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living earth itself with the two melancholic eyes, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, soft warm but muted cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 12 (sent_013 — «И тогда Гея решила: если у неё нет мужа — она родит его себе сама»)

**Краткое описание кадра.** Земля-сущность просыпается с решимостью. Свечение из-под поверхности разгорается ярче, тёплый зелёно-золотой пульс ускоряется. Два золотисто-зелёных глаза распахнуты широко и сияют. Из самого центрального холма (между глазами) начинает подниматься столб серебристо-голубого света — это первые проявления будущего Урана, выходящего из недр Земли.

**Промпт:** resolute earth-landscape entity begins to create her own sky-husband, Gaia the living primordial earth-landscape entity in a three-quarter wide shot of the central hillside, dark-moss-green-and-earth-brown soil pulsing brighter, wildflowers and oak roots straightening up as the earth wakes, faint warm earth-glow beneath the surface now strong and quickening like a determined heartbeat, TWO LARGE GOLDEN-GREEN EYES set into the hillsides wide open and glowing brighter with primordial resolve, a tall bright column of silvery-blue starlight starting to rise upward out of the very crown of the central hillside between the two earth-eyes (the very first emergence of Uranus from inside Gaia), the moment just before creation, mossy hilltop with a still lake far below at the horizon, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with the two resolute eyes and the rising silver-blue column, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic warm-and-cool cinematic lighting (warm green-gold from the earth, cool silver-blue rising from the central crown), no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 13 (sent_014 — «Из её плоти поднялось Небо — Уран, накрывший Землю куполом до самого края мира»)

**Краткое описание кадра.** Уран раскрывается как звёздный купол над Землёй. Серебристо-голубой столб света, поднимавшийся из Геи в предыдущей сцене, теперь развернулся в обширное звёздное небо-купол, накрывающее всю верхнюю половину кадра. Внутри созвездий — два ледяно-голубых глаза-скопления спокойно смотрят вниз на Землю. Гея в нижней половине — спокойная, два золотисто-зелёных глаза в холмах смотрят вверх, на новое небо.

**Промпт:** primordial sky-dome unfurls above the earth as Uranus is born from Gaia, Uranus the living primordial sky-canopy entity unfurled across the upper portion of the frame as a vast silvery-blue starry sky-dome filled with star points and constellations, drifting silver clouds across the dome, TWO ICY PALE-BLUE GLOWING EYES formed by especially bright star clusters within the constellation pattern gazing calmly downward at the earth, the dome edges curving downward toward the horizon like a canopy covering the world from edge to edge, beneath the sky in the lower half Gaia the living primordial earth-landscape entity with her TWO GOLDEN-GREEN EYES in the hillsides gazing upward at the newly formed sky in serene wonder, warm earth-glow pulsing softly from beneath the moss-green soil, mossy hills and a still lake at the very bottom of the frame reflecting the new starry sky above, NO humanoid figures, NO bodies, NO hands, NO mouths, NO faces anywhere in the frame — only the two living entities (the starry sky-dome above with star-cluster eyes and the moss-green earth-landscape below with golden-green eyes), highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic starlit cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 14 (sent_015 — «От их союза родились двенадцать титанов. Среди них — младший и самый дерзкий, Кронос»)

**Краткое описание кадра.** Группа из 12 титанов-котов стоит на мшистой земле Геи под звёздным куполом Урана. На переднем плане молодой Кронос (без бороды, без серпа) с дерзким взглядом. Гея — пейзаж под ногами (с глазами в холмах за группой), Уран — звёздный купол над ними (с глазами-скоплениями выше). Двенадцать титанов — единственные «человекоподобные» в кадре, остальное — стихии.

**Промпт:** twelve cat titans born on the living earth under the living starry sky, twelve anthropomorphic bipedal cat Titans gathered together in a wide group shot, each in a distinctive metallic or elemental palette — bronze, copper, silver, steel, gold, deep-indigo, sea-green, ivory, olive, violet, pearl-white, ember-orange — varied robes of bronze and linen with elemental motifs (waves, stars, wheat, moonlight), humanoid body proportions, standing upright on two legs on the mossy ground, with young Cronus the anthropomorphic bipedal cat titan teenager stepping slightly forward at the front of the group as a focal accent, cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes with a defiant brooding teenage stare into the camera, dressed in a simple dark-grey tunic with a wide leather belt (no cuirass, no skull medallions, no sickle in his hands yet), lean athletic frame, humanoid body proportions, standing upright on two legs, behind the cat titans the living earth-landscape entity Gaia visible as the moss-green hillsides with TWO GOLDEN-GREEN EYES set into the slopes gazing toward the children, above them the living starry sky-canopy entity Uranus visible as a vast silvery-blue star-dome with TWO ICY PALE-BLUE STAR-CLUSTER EYES gazing down toward the children, the parents are NOT humanoid — they are the landscape and the sky themselves with eyes, only the twelve titan cats and young Cronus are humanoid bipedal cat figures in the frame, mossy ground beneath the titans' humanoid feet, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, epic warm cinematic lighting, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 15 (sent_016 + sent_017 — циклопы на переднем плане, многорукие гекатонхейры за ними)

**Краткое описание кадра.** Совмещённый кадр под два соседних коротких предложения («Следом — три одноглазых циклопа-кузнеца. И трое сторуких гекатонхейров.»). Одна картинка-вход на обе видеосцены (`scene_15_01.mp4` и `scene_15_02.mp4`) — кадр статичен, разные движения камеры/зума в Veo создают «два шота» в монтаже.

**Композиция.** Передний план — три циклопа-кота-кузнеца с молотами, тёплый кузнечный свет, искры. Задний план — три огромных гекатонхейра-кота возвышаются за ними. Дополнительно на самом фоне: моховые холмы Геи (с золотисто-зелёными глазами в холмах слева вдалеке) и звёздный купол Урана (с ледяно-голубыми глазами-скоплениями) — родители новорождённых. Циклопы и гекатонхейры остаются котами (humanoid), Гея и Уран — стихиями.

**Промпт:** three cyclops cats and hundred-handed giant cats together on the living earth under the living sky, foreground left-to-right shows three Cyclops anthropomorphic bipedal cat blacksmith brothers — Brontes Steropes Arges — massive muscular frames, short stone-slate-grey fur, ONE large round eye in the middle of each forehead (NO two eyes, ONE single round eye in the center of the forehead per cyclops, repeat: only one eye each cyclops), Brontes on the left with amber eye, Steropes in the center with electric-white eye, Arges on the right with gold eye, bare muscular torsos with leather blacksmith aprons, bronze arm bracers, each holding a different blacksmith tool — Brontes holding a heavy iron hammer, Steropes holding bronze tongs gripping a glowing ember, Arges holding a small dark anvil, humanoid body proportions, standing upright on two legs, warm forge sparks and a glowing anvil behind them, behind the cyclops towering twice their height stand three Hecatoncheires anthropomorphic bipedal cat hundred-handed giants — Cottus Briareus Gyges — dark granite-stone fur with cracked rock vein patterns, shaved or stubble heads, glowing ember-orange eyes, EACH GIANT HAS MANY ARMS — six large primary arms (three on each side of the body) holding the main weapons, PLUS a dense radial fan of about ten additional smaller secondary arms sprouting from their shoulders and back creating an unmistakable hundred-handed silhouette, the additional fan-arms gesturing and flexing in different directions like a halo of hands, bare granite-grey torsos, primary arms holding — Cottus on the left with clubs and boulders, Briareus in the center with iron chains and stone hammers, Gyges on the right with jagged boulders and stone spears, single head one face per giant (just one head per giant, not many heads), humanoid body proportions, standing upright on two legs, at the far background the living moss-green earth-landscape entity Gaia visible as distant hillsides with TWO GOLDEN-GREEN EYES set in the slopes far to the left, and the living starry sky-canopy entity Uranus visible as a silvery-blue starry sky-dome high above with TWO ICY PALE-BLUE STAR-CLUSTER EYES, the parents are NOT humanoid — only the cyclops and hecatoncheires cats are humanoid figures in the frame, dark stone-and-cold-mist atmosphere around the giants contrasting the warm forge glow of the cyclops in front of them, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, split cinematic lighting (warm forge-fire on the cyclops in front, cool moody dark-stone light on the giants behind) with crimson ember highlights from giant eyes, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 16 (sent_018 — клиффхэнгер: два шота под одно длинное предложение)

Длинный клиффхэнгер 9–11 сек, монтируется в два визуальных шота: первая половина под «Уран возненавидел собственных детей и не позволил им выходить на свет», вторая под «Но он не знал, что один из них уже точит на него серп».

### Сцена 16, шот 1 (sent_018a — Уран запирает чудовищных детей)

**Краткое описание кадра.** Гневное небо давит на страдающую землю. Звёздный купол Урана сверху темнеет, тучи сгущаются поперёк созвездий, проскакивают молнии, глаза-скопления сужены и пылают ярче. Край купола опускается вниз и давит на Землю. Силуэты циклопов и гекатонхейров-котов вдавлены в моховую поверхность Геи и наполовину поглощены землёй. Гея — пейзаж с трещинами тёплого света, корни сохнут, цветы вянут, золотые слёзы текут ручейками вниз по холмам из её глаз. Никаких рук, никаких поз — только живая стихия страдает через свои изменения.

**Промпт:** angry sky pressing down on suffering earth as monstrous children are buried inside, Uranus the living primordial sky-canopy entity in the upper third of the frame as a darkening silvery-blue starry sky-dome with thick black storm clouds gathering across the constellations, faint white lightning flashes crackling between the stars, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES narrowed and burning hostile within the constellation pattern, the dome edges curving downward and pressing low against the earth like a heavy lid, in the lower half Gaia the living primordial earth-landscape entity suffering, dark-moss-green-and-earth-brown soil now criss-crossed by thin glowing warm-orange CRACKS of light running across the hillsides like wounds in the ground, oak roots visibly drying out and darkening, grape vines withering, small wildflowers wilted, TWO LARGE GOLDEN-GREEN EYES in the hillsides half-closed and wet, GOLDEN TEAR-STREAMS of glowing molten gold running down from each eye in long ribbons across the moss-green slopes, between the sky and the earth visible the half-buried silhouettes of three one-eyed cyclops cat brothers and three many-armed granite hecatoncheires cat giants (each with multiple arms creating an unmistakable hundred-handed silhouette) sinking into the moss-green ground as the sky-dome above pushes them down, the buried cat-children glow faintly from within the earth as prisoners now held inside, the parents are NOT humanoid — they are the sky and the earth themselves with eyes, only the cyclops and hecatoncheires cats are humanoid figures in the frame, NO humanoid figure for Uranus, NO humanoid figure for Gaia, NO hands NO arms NO mouths NO faces on the sky or earth — they suffer through their own elements, no blood, no wounds, no gore, only emotional landscape and sky suffering, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dark moody cinematic lighting with cold lightning from above and warm cracked earth-glow from below, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

### Сцена 16, шот 2 (sent_018b — молодой Кронос в тенях точит серп)

**Краткое описание кадра.** Закадровый угол. Молодой Кронос-кот (без бороды, тот же из сцены 14) склонился в тени над камнем-точилом, точит изогнутый адамантовый серп. Искра отлетает в воздух. Глаза янтарно-жёлтые горят. Атмосфера секретности — звёздный купол Урана высоко в фоне, но его глаза-скопления отвёрнуты в сторону, он не смотрит сюда. Серп ещё «зарождается» — лезвие тёмное, едва видимое.

**Промпт:** young cat cronus sharpening an adamant sickle in shadow, young Cronus the anthropomorphic bipedal cat titan teenager crouched in deep shadow over a low whetstone, cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes glowing in the dark, dressed in a simple dark-grey tunic with a wide leather belt (no cuirass yet, no skull medallions yet), lean athletic frame, humanoid body proportions, standing crouched on two legs, both humanoid hands gripping a curved jagged dark adamant sickle being sharpened against a stone whetstone, a single bright orange spark flying off the sickle blade into the air, focused intent face concentrating on the sickle, the rest of the scene in deep secretive shadow, far above in the distant background the living starry sky-canopy entity Uranus visible as a faint silvery-blue starry sky-dome with TWO ICY PALE-BLUE STAR-CLUSTER EYES turned aside toward the opposite horizon (not looking down at Cronus, unaware of him), Uranus is NOT humanoid — just the distant sky-dome with eyes, no other figures in the foreground except Cronus, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, tense low-key cinematic lighting with a single warm spark as focal point, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 17 (sent_019 — «Подпишись, чтобы не пропустить следующую часть»)

**Краткое описание кадра.** Финальный сборный кадр части под караоке-плашку «ПОДПИШИСЬ → ЧАСТЬ 2 СКОРО». Сверху — тёмный звёздный купол Урана с холодно-надменными глазами-скоплениями. Внизу — пейзаж страдающей Геи с тёплыми трещинами и одиночным ручейком золотых слёз с центрального холма. Силуэты титанов-котов разбросаны по холмам в мягком фокусе. На переднем плане слева в тенях — точило с серпом и одной искрой (намёк на Кроноса). Центральная вертикальная зона — пустая под плашку.

**Промпт:** part one finale ominous foreshadow composite, a wide atmospheric closing tableau, in the upper third Uranus the living primordial sky-canopy entity as a vast silvery-blue starry sky-dome with dark storm clouds gathering across the constellations and TWO ICY PALE-BLUE STAR-CLUSTER EYES proud and cold gazing down from the constellation pattern, in the lower half Gaia the living primordial earth-landscape entity as moss-green and earth-brown hillsides with thin glowing warm-orange CRACKS of light running across the slopes like wounds, TWO LARGE GOLDEN-GREEN EYES in the central hillsides lowered and tired, a single thin GOLDEN TEAR-STREAM of glowing molten gold running down from the central earth-eye along the slope of the hill, faint cat silhouettes of twelve titan cats scattered around the hillsides in soft focus at varying depths, in the foreground left corner a dark whetstone with a curved jagged adamant sickle lying on it and a single bright orange spark hovering above as an unmistakable hint toward Cronus, central vertical area of the frame intentionally left visually quiet to leave room for an overlaid subscribe-call-to-action title plate in editing, the sky and earth are NOT humanoid — they are the dome and the landscape themselves with eyes, only the twelve distant titan cat silhouettes are humanoid figures, NO hands NO arms NO mouths NO faces on the sky or earth, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, atmospheric cool-and-warm cinematic lighting (cool starlight above, warm cracked earth-glow below, single warm spark on the foreground sickle), no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Чек-лист перед запуском генерации (сверять перед каждым прогоном Flow)

Берём из [MYTH.md](../../../../MYTH.md) → шаг 7 + [GENEALOGY.md](../../../../GENEALOGY.md) → шаг 7. **ВНИМАНИЕ:** в этой части два класса персонажей — **абстрактные сущности-стихии с глазами** (Хаос, Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран) и **антропоморфные коты** (Кронос, 12 титанов, циклопы, гекатонхейры). Чек-лист отдельный для каждого класса.

1. **Уникальный subject-маркер.** Первые 3–4 слова каждого `**Промпт:**` отличаются от соседних. Проверить:

   ```bash
   grep '^\*\*Промпт:\*\* ' content/От\ Хаоса\ до\ Олимпа/часть_01_Хаос/prompts/images.md \
     | sed -E 's/^\*\*Промпт:\*\* ([^,]+),.*/\1/' \
     | sort | uniq -c | sort -rn
   ```

   Все строки должны быть с числом `1`.

2. **Класс «абстрактные сущности» — НЕТ humanoid.** Для Геи, Тартара, Эроса, Эреба, Никты, Эфира, Гемеры, Урана в каждом промпте должно быть `NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face`. Никаких `humanoid body proportions` или `standing upright on two legs` для них.

3. **Класс «абстрактные сущности» — ЕСТЬ глаза.** Для каждого первобожества в кадре чётко прописано `TWO [color] GLOWING EYES` (Гея — golden-green, Тартар — crimson dot, Эрос — amber almond, Эреб — amber with dark rings, Никта — silver full-moon, Эфир — pale-blue, Гемера — warm amber, Уран — icy pale-blue star-cluster).

4. **Класс «антропоморфные коты» — ЕСТЬ humanoid.** Для Кроноса, 12 титанов, циклопов, гекатонхейров — `humanoid body proportions, standing upright on two legs`. Если в промпте есть `hand`, `foot`, `ankle` для котов — обязательно `humanoid hand` / `humanoid feet`.

5. **Класс «антропоморфные коты» — волосы упомянуты в каждой сцене.** Молодой Кронос — `short shoulder-length dark-silver hair`. Циклопы — `short stone-slate-grey fur`. Гекатонхейры — `shaved or stubble heads`. Прочие титаны — `varied robes with elemental motifs`.

6. **Циклопы — ОДИН глаз.** В сцене 15 и в сцене 16a (силуэты при запирании) — `ONE large round eye in the middle of each forehead, NO two eyes, ONE single round eye in the center of the forehead per cyclops` (повторить дважды).

7. **Гекатонхейры — МНОГО рук («сторукие»).** В сцене 15 и в сцене 16a (силуэты) — `EACH GIANT HAS MANY ARMS — six large primary arms (three on each side) holding weapons, PLUS a dense radial fan of about ten additional smaller secondary arms sprouting from the shoulders and back, hundred-handed silhouette`. Голова **одна** (`single head one face per giant`).

8. **Кронос в ч. 1 — БЕЗ бороды и серпа (кроме сцены 16b).** В сцене 14 — `CLEAN-SHAVEN no beard yet`, серпа нет. В сцене 16b — серп есть.

9. **Уран — две «эмоции» по сценам (через само небо).** В сценах 13, 14, 15 — спокойный звёздный купол, глаза-скопления светят ровно. В сцене 16a — гневное небо: тучи поперёк созвездий, молнии, глаза сужены и пылают. В сцене 16b — глаза-скопления отвёрнуты в сторону (не видит Кроноса). В сцене 17 — холодные надменные глаза.

10. **Гея — четыре «эмоции» по сценам (через сам ландшафт).** Сцены 2, 3, 13 — спокойная торжественная земля, свежий мох, цветы раскрываются, глаза тепло светят. Сцена 10 — спокойная в составе общего плана. Сцена 11 — потускневшая земля, цветы поникли, глаза опущены и приглушённо мерцают. Сцена 12 — решимость, свечение разгорается, из центрального холма поднимается столб серебристо-голубого света. Сцены 16a, 17 — страдающая земля: трещины тёплого света по холмам, золотые слёзы из глаз ручейками по склонам.

11. **Смешанные сцены (14, 15, 16a, 17) — границы класса.** Если в одном кадре стихия и коты — обязательно прописать «the parents/sky/earth are NOT humanoid», «only the [cat-titans/cyclops/...] are humanoid figures in the frame». Иначе модель может прирастить Гее «лицо в холме» или Урану «фигуру в облаках».

12. **Стилевой каркас + негативы в каждом промпте.** `highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, [LIGHTING], no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats`. Для сцен 16a, 16b, 17 добавляется ещё `no blood, no gore, no wounds`.

---

## Журнал

- **2026-05-16** — Файл создан. 21 промпт на 20 сцен (sent_001+002 = сцена 1, sent_020 = сцена 19 в двух шотах). Карточки персонажей дублированы в шапке HTML-комментарием. Subject-маркеры уникальны для всех 21 промпта. Чек-лист в конце файла.
- **2026-05-16** — **Совмещение сцен 17 и 18 в одну Сцену 17 (sent_018 + sent_019).** Одна картинка-вход покрывает оба коротких соседних предложения о циклопах и гекатонхейрах: на переднем плане циклопы с тёплым кузнечным светом, за ними возвышаются вдвое выше многорукие гекатонхейры с холодным каменным светом. На стороне видео это по-прежнему две сцены (`scene_18_01.mp4` и `scene_19_01.mp4`), но обе используют одну картинку с разными движениями камеры/зума в Veo. **Гекатонхейры переделаны под «сторуких»:** 6 крупных основных рук с оружием + радиальный веер из ~10 дополнительных мелких рук, торчащих из плеч и спины — pixel-art стилизация мифической «сотни рук». Карточка в [../../characters.md](../../characters.md) обновлена синхронно (для согласованности в ч. 4 «Титаномахия», где гекатонхейры освобождены и сражаются). Перенумерация: бывшая Сцена 19 (клиффхэнгер sent_020) → Сцена 18, бывшая Сцена 20 (CTA sent_021) → Сцена 19. Итого 20 промптов на 19 сцен.
- **Заметки на будущее.** Кронос в ч. 1 присутствует только как «дерзкий подросток в массе титанов» (сцена 16) и «силуэт в тени, точащий серп» (сцена 19b). Полноценная карточка взрослого Кроноса с бородой и серпом — для ч. 2 и далее. В ч. 1 серп показывается только в финальных кадрах (сцена 19b, 20) как «улика» — это не противоречит мифу (в ч. 2 серп даёт Гея, тут — кадрово-художественная подсказка).
- **2026-05-17** — **Первобожества переведены в класс «абстрактные сущности-стихии с глазами».** Гея, Тартар, Эрос, Эреб, Никта, Эфир, Гемера, Уран больше не антропоморфные коты, а сама стихия с парой светящихся глаз внутри: пейзаж, пропасть, светящийся орб, дымное облако, ночное облако, светлое облако, рассветное облако, звёздный купол. Эмоции читаются через изменения самой стихии — трещины в земле, тучи и молнии в небе, потускневшее свечение, золотые слёзы текут ручейками по холмам, никаких рук/тел/мимики. Переписан HTML-блок карточек в шапке, общие негативы (добавлен блок «ДОПОЛНИТЕЛЬНЫЕ НЕГАТИВЫ ДЛЯ СЦЕН С ПЕРВОБОЖЕСТВАМИ»), все сцены с первобожествами (4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 18a, 19) и смешанные сцены с титанами-котами на стихиях (16, 17, 18b). Кронос, 12 титанов, циклопы, гекатонхейры — **остаются котами**. Чек-лист переработан под два класса (отдельные пункты «нет humanoid + есть глаза» для абстрактных, «есть humanoid + волосы» для котов). Карточка в [../../characters.md](../../characters.md) обновлена синхронно (добавлены отдельные карточки Эфира и Гемеры, изменение глобальное для всех будущих частей с теми же первобожествами).
- **Заметки на будущее.** В ч. 2 (Гея + Уран → свержение) ожидаем те же два класса. Уран не «согнувшийся» — он распадающееся небо. Гея не «даёт серп Кроносу-коту физически» — серп поднимается из недр на каменной плите. Если решим вернуть какие-то из первобожеств в кошачью форму — править characters.md (источник правды), не локальный HTML-блок здесь.
- **2026-05-18** — **Сцена 4 (Тартар) переделана с «вид сверху в шахту» на «гигантская пасть-бездна».** Было: камера смотрит сверху-вниз в узкую антрацитовую шахту, две багровые точки-глаза еле видны на дне — композиция «земля проваливается», слабый stop-scroll. Стало: горизонтально открытая пасть-расщелина в нижних 2/3 кадра, чёрные скальные «зубы»-сталактиты/сталагмиты обрамляют отверстие, два огромных багровых глаза Тартара смотрят прямо на зрителя из глубины пасти, лавовые жилы расходятся как «нимб» вокруг глаз. Земля Геи лежит сверху тонкой полосой как «крышка». Камера сбоку, на уровне пасти — никакого падения вниз. Композиционно сильнее (большие глаза = stop-scroll), тематически точнее (Тартар = чудовищная пасть-бездна, готовая поглотить детей Урана в финале). Карточка персонажа Тартара в шапке файла остаётся как есть (источник правды); конкретная ракурсная композиция описана только в промпте сцены.
- **2026-05-18** — **Сцена 1 переделана с «пустой Хаос» на «Око Хаоса».** Было: чистая фиолетово-угольная туманность без персонажей и центральная зона под титул — слабый stop-scroll, первые 3 сек ролика не цепляли (визуально неотличимо от десятка других «космогонических» Shorts). Стало: гигантский янтарно-золотой глаз, сделанный из самого Хаоса (веко = туманность, радужка = микрокосм завихрений, зрачок = чёрная воронка), смотрит прямо в зрителя. Психологический stop-scroll крючок «нечто живое смотрит на меня» + визуальная завязка концепции сериала «каждая стихия = существо с глазами» (в Сцене 2 у Геи в холмах открываются её собственные глаза = рифма). Караоке-плашка теперь ложится не в центр, а в нижнюю «тихую» половину кадра под оком — глаз становится верхним фокусом, титул — нижним. Также обновлено краткое описание Сцены 2 (добавлен блок «Визуальная рифма со Сценой 1»).
- **2026-05-18** — **Удалены Сцены 2 и 3 (два тёмных кадра Хаоса).** До правки интро было: Сцена 1 (Хаос+титул) → Сцена 2 (Хаос «во все стороны») → Сцена 3 (Хаос с искрой) → только потом Сцена 4 (Гея рождается). Три тёмных кадра подряд гарантировали свайп зрителя на первых 12–15 сек ролика. После правки: Сцена 1 (Хаос+титул) → Сцена 2 (Гея просыпается) — переход из тёмного в светлое уже на 8–10 сек. Перенумерация (минус 2): бывшие Сцены 4–19 → Сцены 2–17. Соответственно: sent_005…sent_021 → sent_003…sent_019. Итого **18 картинок на 17 сцен** (было 20 на 19). Обновлены: заголовки всех сцен, краткое описание Сцены 2 (теперь «И вдруг в этой тьме родилась Гея»), ссылки на видеофайлы в Сцене 15 (раньше `scene_18_01.mp4` и `scene_19_01.mp4` → теперь `scene_15_01.mp4` и `scene_15_02.mp4`), ссылка «из сцены 16» в Сцене 16b → «из сцены 14», все номера сцен в чек-листе (пункты 6–12). Картинки в `images/approved_images/` тоже надо переименовать — `scene_04_v1.jpg` → `scene_02_v1.jpg` и т.д.; пока не сделано, ждёт отдельного шага.
