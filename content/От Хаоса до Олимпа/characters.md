# Карта персонажей: От Хаоса до Олимпа

> **Источник правды.** При написании промптов в `часть_NN/prompts/images.md` и `video.md` копировать английский блок ДОСЛОВНО (цвет меха, глаза, одежда, аксессуары, поза). Модель Flow/Veo не помнит, что было в прошлой сцене и тем более в прошлой части.
>
> **Канал = pixel-art коты, ДВА КЛАССА персонажей:**
>
> 1. **Антропоморфные коты** — все, кто в мифе сюжетно ведут себя как люди (титаны, циклопы, гекатонхейры, олимпийцы, герои). Английские карточки включают `anthropomorphic bipedal cat character, standing upright on two legs, humanoid body proportions`. Негативы `NO humans, NO real four-legged cats` добавляются в каждый промпт отдельно через стилевой каркас.
> 2. **Абстрактные сущности-стихии с глазами** — первобожества, которые по концепции НЕ человекоподобны (Земля, Небо, Ночь, Мрак, День, Свет, Бездна, Сила влечения). Они показываются как сам ландшафт/туманность/облако/свет — с двумя крупными светящимися глазами внутри. Без тела, без рук, без лица, без рта. Эмоции читаются через изменения самой стихии: трещины в земле, тучи в небе, потускневший свет, золотые слёзы текут по холмам. У этих карточек добавлены жёсткие негативы `NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face`. Это **отдельный визуальный класс** — он не сочетается с «кот-богом» в одной фигуре, но в одной сцене они могут соседствовать (например, титаны-коты на земле-сущности под небом-сущностью).
>
> **`video.md` ≠ `images.md`.** В `images.md` имена богов (`Zeus`, `Hades`, `Cronus` …) можно оставлять — фильтр Flow/ImageFX мягкий. В `video.md` имена ЗАПРЕЩЕНЫ из-за IP-фильтра Veo — использовать раздел «Descriptive (video.md)» каждой карточки. См. [CONTEXT.md](../../CONTEXT.md) → «IP-фильтр Veo».
>
> **Эволюция образа.** Если бог растёт по ходу цикла (Зевс: младенец → юноша → владыка), у него подразделы по возрастам. Это один персонаж, не три — меняются возраст, поза, аксессуары, но окрас/глаза/общая конституция те же.

---

## Сводная таблица: палитра и появления

| # | Персонаж | Поколение | Палитра / маркер | Появляется в частях |
|---|---|---|---|---|
| 1 | Хаос ⬜ | прим. бездна | тёмно-фиолетовая туманность, угольные искры, без формы | 1 |
| 2 | Гея ⬜ | прим. (Земля) | пейзаж: моховой зелёный + бурый + 2 золотисто-зелёных глаза в холмах | 1, 2 |
| 3 | Тартар ⬜ | прим. (Бездна) | пропасть: антрацит + красные лава-жилы + 2 багровых точки-глаза | 1, 3 (финал) |
| 4 | Эрос (космог.) ⬜ | прим. (Сила влечения) | сфера: розово-золотой свет + 2 янтарных глаза в центре | 1 |
| 5 | Эреб ⬜ | прим. (Мрак) | дымное облако: пепельно-серый + 2 янтарных глаза, чернильные нити | 1 |
| 6 | Никта ⬜ | прим. (Ночь) | ночное облако: иссиня-чёрное + 2 серебряных глаза-полнолуния | 1 |
| – | Эфир ⬜ | прим. (Свет) | облако: слоновая кость + 2 бледно-голубых глаза, золотые лучи | 1 |
| – | Гемера ⬜ | прим. (День) | облако: персиково-золотое + 2 янтарных глаза, рассветные лучи | 1 |
| 7 | Уран ⬜ | Небо (сын Геи) | звёздный купол: сине-серебристый + 2 ледяно-голубых глаза-скопления | 1 (финал), 2 |
| 8 | Кронос | титан, узурпатор | холодная сталь, седина, серп | 1 (упом.), 2 (молодой → узурпатор → параноик), 3 (свергнут) |
| 9 | Рея | титанида, мать | кремово-золотой, материнский, тёплый | 2 (жена → беглянка), 3 (подмена камнем) |
| 10 | Иапет | титан (отец Прометея) | бронзово-медный, могучий | 1 (массовка), 3 |
| 11 | Прочие титаны | массовка (4 ♂ + 5 ♀) | металлы и камни | 1 (массовка), 3 |
| 12 | Циклопы | (Бронт, Стероп, Арг) | мускулистые, 1 крупный глаз, кузнецы | 1 (рождение), 3 |
| 13 | Гекатонхейры | (Котт, Бриарей, Гиес) | многорукие, тёмно-каменные | 1 (рождение), 3 |
| 14 | Афродита | (рождена из пены) | перламутрово-розовый, пенно-белый | 2 (рождение), опц. 5 |
| 15 | Эринии | *(не в цикле; заглушка)* | угольные, светящиеся глаза | — (для будущих одиночных мифов) |
| 16 | Зевс | олимпиец, царь | золото-слоновая кость, синие глаза, молния | 2 (силуэт в утробе Реи), 3 (младенец → юноша → владыка), опц. 4, 5 |
| 17 | Гера | олимпийка, царица | кремово-белый, павлинья мантия | 2 (котёнок, поглощается Кроносом), 3, опц. 4, 5 |
| 18 | Посейдон | олимпиец, море | сине-зелёный, борода-волна, трезубец | 2 (котёнок, поглощается Кроносом), 3, опц. 4, 5 |
| 19 | Аид | олимпиец, подземье | угольно-чёрный, тёмный плащ | 2 (котёнок, поглощается Кроносом), 3, опц. 4 |
| 20 | Деметра | олимпийка, урожай | пшенично-золотой, колосья | 2 (котёнок, поглощается Кроносом), 3, опц. 5 |
| 21 | Гестия | олимпийка, очаг | мягко-бежевый, тёплый, скромный | 2 (котёнок, поглощается Кроносом), 3, опц. 5 |

Опциональная часть 5 («12 Олимпийцев») потребует ещё карточки для Афины, Аполлона, Артемиды, Гермеса, Ареса, Гефеста, Диониса — заглушки в конце файла.

---

# Поколение 0: Первобожества (ч. 1)

## Хаос

*(ч. 1 — рождение из ничего)*

**Визуальный образ:** не персонаж в привычном смысле. Клубящаяся первобытная пустота. Без формы, без лица, без тела. Тёмно-фиолетовые и угольные туманности, редкие искры тёплого золота вглубине. От Хаоса берёт начало всё остальное — в кадре он сначала заполняет весь экран, потом постепенно «отступает на фон», когда из него рождаются первобожества.

**Английская карточка (images.md):**

```
swirling primordial Chaos void, deep violet and charcoal nebula, faint warm-gold embers drifting inside, no face, no body, no figure, vast cosmic emptiness, soft glow at the edges, 9:16 vertical, highly detailed pixel art, modern detailed pixel art style, dark cinematic lighting
```

**Descriptive (video.md):** карточка и так descriptive, имени собственного нет — копируется без изменений.

**Эволюция:** в начале ч. 1 — заполняет весь кадр. По мере появления Геи / Тартара / Эроса — отступает на задний план, остаётся как тёмная клубящаяся атмосфера.

---

## Гея

*(ч. 1 — рождение из Хаоса, одиночество, рождает Урана и от союза с ним — 12 титанов + циклопов + гекатонхейров, начинает страдать от того, что Уран прячет детей внутри неё; ч. 2 — три эмоции в одном ролике: страдающая → мстительная (даёт серп Кроносу) → пророческая (предсказывает Кроносу, что его свергнет собственный ребёнок); в ч. 3 и далее не появляется)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Гея — не кошка-богиня, а **сама живая Земля**. Никакого тела, рук, ног, лица. Только пейзаж с двумя огромными светящимися глазами внутри.

**Визуальный образ:** обширный пейзаж — холмы из мха и тёмной плодородной почвы, корни дуба, лозы, мелкие полевые цветы. Это и есть сама Гея — единое тело-ландшафт. В двух точках поверхности (на центральном холме и на ближнем склоне) сияют **две огромных золотисто-зелёных глаза** — это её сознание. Глаза находятся внутри самой земли, как будто холм одновременно и склон, и веко. Из-под поверхности проступает тёплое золотисто-зелёное свечение, пульсирующее как дыхание. Тела, лица, рук — нет.

**Палитра:** dark moss green + warm earth brown + gold-green glowing eyes + small wildflowers accents.

**Английская карточка (images.md):**

```
Gaia the living primordial earth-landscape entity, a vast rolling terrain of dark-moss-green and earth-brown soil with oak roots, grape vines and small wildflowers growing across it, TWO LARGE GLOWING GOLDEN-GREEN EYES set into the earth itself (one on the central hillside, one on a nearby slope) gazing upward with primordial awareness, faint warm earth-glow pulsing beneath the surface like slow breathing, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with the two eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial earth-landscape entity, vast rolling moss-green and earth-brown terrain with roots vines and wildflowers, two large glowing golden-green eyes set into the earth surface, faint warm earth-glow pulsing beneath, no body no figure no hands
```

**Эволюция эмоций (через изменения ландшафта, не позы):**

- **Ч. 1 (рождение)** — спокойная торжественная земля. Свежий мох, нежные ростки, цветы раскрываются. Глаза полузакрыты и тепло сияют. Тёплое золотисто-зелёное свечение из-под поверхности.
- **Ч. 1 (одиночество, sent_014)** — потускневшая земля. Цветы поникли, лозы безжизненно висят, свечение ослабло. Глаза опущены и приглушённо мерцают.
- **Ч. 1 (решимость, sent_015)** — земля просыпается. Свечение под поверхностью разгорается ярче, глаза распахнуты широко и горят. Из центрального холма начинает подниматься столб серебристо-голубого света (будущий Уран).
- **Ч. 1 финал → ч. 2 (страдание, sent_003-004)** — трескающаяся земля. По холмам бегут тонкие трещины тёплого света, корни сохнут и темнеют, цветы вянут. Из глаз текут **золотые слёзы** — ручейки светящегося золота сбегают вниз по склонам. Глаза прикрыты, скорбные.
- **Ч. 2 (мстительная, sent_005-006)** — глаза горят холодным золотом. Из недр поднимается каменная плита с лежащим на ней изогнутым адамантовым серпом (Гея отдаёт серп Кроносу). По земле бегут чёрно-золотые жилы решимости.
- **Ч. 2 (пророческая, sent_013)** — глаза прикрыты как в трансе, на поверхности проступают древние светящиеся руны и символы пророчества «тебя свергнет твой собственный ребёнок». Туман над почвой. Это последнее появление Геи в цикле — после ч.2 она уходит в фон как лейтмотив «земля смотрит и знает».

---

## Тартар

*(ч. 1 — рождение; ч. 5 — туда низвергают побеждённых титанов)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Тартар — сама живая бездна, не фигура. Без тела, без рук.

**Визуальный образ:** бездонная пропасть в антрацитово-чёрной скале. Стенки рваные, по ним бегут тлеющие красные жилы лавы (как остывающая магма). Внутри, глубоко на дне темноты, мерцают **две багровые точки-глаза** — сознание бездны. Никакого силуэта, никакой фигуры — только сама пропасть с парой светящихся глаз в её глубине.

**Английская карточка (images.md):**

```
Tartarus the living primordial abyss entity, a bottomless dark chasm of anthracite-black rock with glowing crimson lava-vein patterns cracking through the walls, TWO FAINT CRIMSON DOT-EYES glowing deep inside the darkness at the bottom of the pit, descending into endless darkness, NO humanoid figure, NO body, NO hands, NO face — only the living abyss itself with the two crimson eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial abyss entity, bottomless anthracite-black chasm with crimson lava-vein walls, two faint crimson dot-eyes glowing deep inside the darkness at the bottom, no body no figure no hands
```

**В ч. 5 чаще показан как локация** (тёмная пропасть с прутьями-решёткой, куда падают побеждённые титаны), а не как сущность. Решётка и красное свечение снизу — узнаваемые маркеры локации.

---

## Эрос (космогонический)

*(ч. 1 — рождение из Хаоса)*

> ⚠️ **Не путать с поздним Эросом — сыном Афродиты** (тот другой персонаж, не входит в данный цикл). В греческой космогонии первородный Эрос — сила влечения, удерживающая мир. Без лука, без стрел, без крылышек херувима.
>
> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Эрос — сама сила влечения, не существо. Без тела, без рук, без лица.

**Визуальный образ:** яркая розово-золотая сфера-облако космического света, парящая в пространстве. В центре сферы — **два больших янтарных миндалевидных глаза**, спокойно смотрящих наружу. От сферы радиально расходятся мягкие розово-золотые концентрические кольца света — это и есть «сила влечения», которая стягивает первичные вещи к центру. Никакого тела, никаких волос, никакой туники — только живой светящийся орб с парой глаз.

**Английская карточка (images.md):**

```
Eros the primordial attraction-force entity, a glowing radiant pink-and-gold cosmic light orb floating in space, TWO LARGE GLOWING AMBER ALMOND EYES at its center gazing outward calmly, soft pink-and-gold concentric attraction rings radiating outward from the orb, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living radiant force-orb with the two amber eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial attraction-force entity, glowing pink-and-gold cosmic light orb, two large glowing amber almond eyes at its center, soft pink-gold attraction rings radiating outward, no body no figure no hands
```

---

## Эреб

*(ч. 1 — рождение из Хаоса)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Эреб — сам Мрак, не персонаж. Без тела.

**Визуальный образ:** клубящийся пепельно-серый дымный сгусток (как туман над остывшим углём). Внутри сгустка — **два янтарных светящихся глаза с тёмной обводкой**, спокойно смотрящих наружу. От сгустка во все стороны тянутся тонкие чернильно-чёрные нити-тени, как щупальца дыма. Никакой фигуры, никакого плаща — только живая тёмная дымка с парой глаз.

**Английская карточка (images.md):**

```
Erebus the primordial darkness entity, a swirling pool of ash-grey-and-soot dark mist forming a sentient cloud, TWO AMBER GLOWING EYES WITH DARK RINGS shining from within the dark mist, ink-black tendrils of shadow drifting outward like wisps of smoke, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living dark mist with the two amber eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial darkness entity, swirling ash-grey-and-soot dark mist cloud, two amber glowing eyes with dark rings shining inside the dark mist, ink-black shadow tendrils drifting outward, no body no figure no hands
```

**Часто в кадре рядом с Никтой** — они пара, в ч. 1 показаны вместе как два соседних облака-сущности на фоне Хаоса.

---

## Никта

*(ч. 1 — рождение из Хаоса, пара Эреба)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Никта — сама Ночь, не богиня. Без тела.

**Визуальный образ:** клубящееся иссиня-чёрное облако ночного неба, усыпанное крошечными белыми звёздами-точками. Внутри облака — **два серебристых глаза-полнолуния** (большие, светлые, спокойные), как настоящие луны посреди ночного неба. Вокруг облака медленно дрейфуют серебряные полумесяцы — будто маленькие фазы луны кружат рядом. Никакой фигуры, никакой короны, никакого платья — только живое ночное небо с парой лун-глаз.

**Английская карточка (images.md):**

```
Nyx the primordial night entity, a deep blue-black living night-sky cloud dusted with tiny white star points, TWO LARGE SILVER FULL-MOON EYES shining from within the night-mist, drifting silver lunar crescent shapes circling around the cloud like tiny moon phases, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living night-sky with the two silver moon-eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial night entity, deep blue-black night-sky cloud dusted with white star points, two large silver full-moon eyes shining inside the cloud, drifting silver lunar crescents around it, no body no figure no hands
```

---

## Эфир

*(ч. 1 — рождён от союза Эреба и Никты, парный Гемере)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Эфир — сам чистый небесный свет, не персонаж. Без тела.

**Визуальный образ:** яркое слоновой-кости-и-бледного-золота облако чистого небесного света, парящее в воздухе. Внутри облака — **два бледно-голубых светящихся глаза**, спокойно смотрящих наружу. От облака радиально расходятся мягкие золотые лучи. Контрастирует с тёмной парой родителей (Эреб + Никта).

**Английская карточка (images.md):**

```
Aether the primordial heavenly-light entity, a bright glowing ivory-and-pale-gold light cloud floating in the air, TWO PALE-BLUE GLOWING EYES shining from within the light, soft gold rays radiating outward, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living heavenly light with the two pale-blue eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial heavenly-light entity, bright ivory-and-pale-gold light cloud, two pale-blue glowing eyes shining inside the light, soft gold rays radiating outward, no body no figure no hands
```

---

## Гемера

*(ч. 1 — рождена от союза Эреба и Никты, парная Эфиру)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Гемера — сам День, не богиня. Без тела.

**Визуальный образ:** тёплое персиково-и-розово-золотое облако рассветного света, парящее в воздухе. Внутри облака — **два тёплых янтарных глаза**, спокойно смотрящих наружу. От облака радиально расходятся пастельные розово-восходные лучи. Контрастирует с тёмной парой родителей (Эреб + Никта), парная Эфиру.

**Английская карточка (images.md):**

```
Hemera the primordial day entity, a warm glowing peach-and-rose-gold dawn-light cloud floating in the air, TWO WARM AMBER GLOWING EYES shining from within the dawn-mist, gentle pastel sunrise-pink rays radiating outward, NO humanoid figure, NO body, NO hands, NO mouth, NO face — only the living dawn-light with the two amber eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial day entity, warm peach-and-rose-gold dawn-light cloud, two warm amber glowing eyes shining inside the dawn-mist, gentle pastel sunrise-pink rays radiating outward, no body no figure no hands
```

---

# Поколение 1: Дети Геи (ч. 1 финал, ч. 2)

## Уран

*(ч. 1 финал — рождён Геей, накрывает её как небо, появляются титаны/циклопы/гекатонхейры, начинает прятать чудовищных детей в Гею; ч. 2 — свергнут Кроносом, **не погибает** — навсегда поднимается в небо, его капли становятся пеной для рождения Афродиты, его слёзы становятся дождём)*

> ⚠️ **Класс: абстрактная сущность-стихия с глазами.** Уран — само живое Небо-купол, не царь-кот. Без тела, без рук, без короны и мантии в привычном смысле — всё это растворено в самой структуре звёздного неба.

**Визуальный образ:** обширный сине-серебристый звёздный купол ночного неба, натянутый над верхней третью кадра. Внутри купола — россыпь звёзд и созвездий, медленно дрейфующие серебристые облака. **Два ледяно-голубых светящихся глаза**, сформированных особенно яркими скоплениями звёзд, смотрят сверху вниз на Землю. Контур купола может слегка опускаться к краям кадра, как купол шатра. Само небо и есть Уран — тела, лица, рук, мантии нет.

**Английская карточка (images.md):**

```
Uranus the living primordial sky-canopy entity, a vast silvery-blue starry sky-dome stretched across the upper portion of the frame filled with star points and constellations, drifting silver clouds across the dome, TWO ICY PALE-BLUE GLOWING EYES formed by especially bright star clusters within the constellation pattern gazing downward at the earth, the dome edges curving downward toward the horizon like a canopy, NO humanoid figure, NO body, NO hands, NO arms, NO crown, NO mantle, NO face — only the living starry sky-dome with the two pale-blue star-cluster eyes, highly detailed pixel art
```

**Descriptive (video.md):**

```
the living primordial sky-canopy entity, vast silvery-blue starry sky-dome across the upper frame with star points and constellations, two icy pale-blue glowing eyes formed by bright star clusters gazing downward, drifting silver clouds, no body no figure no hands
```

**Эволюция эмоций (через изменения самого неба, не позы):**

- **Ч. 1 (рождение, союз с Геей)** — спокойный звёздный купол. Яркие чистые созвездия, серебряные облака медленно плывут, глаза-скопления светят ровно и холодно-надменно. Купол только что раскрылся над Землёй.
- **Ч. 1 финал (начинает прятать чудовищных детей)** — гневное небо. Тучи сгущаются и темнеют поперёк созвездий, проскакивают слабые молнии, глаза-скопления сужаются и пылают ярче и холоднее. Край купола опускается вниз и давит на Землю — будто небо пригнетает.
- **Ч. 2 (sent_007: нападение Кроноса)** — небо застигнуто врасплох. Созвездия начинают «трескаться» — между звёздами появляются тонкие линии-трещины серебряного света. Глаза-скопления расширены. Молния-вспышка серпа проходит поперёк купола. **Самого момента удара по фигуре нет** (Уран и так не фигура) — показывается только трескающееся небо.
- **Ч. 2 (sent_008: не погибает, поднимается в небо)** — звёздный купол **не распадается, а наоборот — отрывается от земли и навсегда поднимается выше**, становясь далёким космосом. Глаза-скопления тускнеют, но не гаснут: остаются как две далёкие холодные звезды на самом верху кадра, видимые только ночью. Это **ключевая образная замена** жестокости свержения — Уран не убит, он становится недосягаемым небом.
- **Ч. 2 (sent_010: капли → Афродита)** — с краёв уходящего купола падают серебристо-жемчужные капли (НЕ кровь, НЕ красные). Капли падают в море, **превращаются в морскую пену**, из которой поднимается Афродита.
- **Ч. 2 (sent_011: слёзы → дождь, лейтмотив части)** — из двух далёких глаз-звёзд Урана льются золотисто-серебряные капли, превращающиеся в дождь над землёй. Дождь идёт мягко, тёплыми каплями, на покинутые им холмы Геи и на детей, что наконец-то вышли на свет. **Этот образ можно возвращать в кадр на протяжении всей оставшейся части как лейтмотив отцовской скорби** — например, в сцене пожирания детей (sent_014-015) дождь идёт как фон, а в финале с беременной Реей (sent_018) — превращается в тёплый закатный свет, прорезающийся сквозь облака.

---

# Поколение 2: Титаны (ч. 1 финал, 2, 3)

## Кронос

*(ч. 1 финал — упомянут как младший и самый дерзкий из 12 титанов, появляется в массе; ч. 2 — главный антагонист цикла: подросток → молодой узурпатор (свергает Урана серпом) → надевший корону тиран (берёт в жёны сестру Рею) → параноик-отец (глотает первых пятерых детей одного за другим); ч. 3 — свергнут Зевсом, низвергнут в Тартар)*

**Визуальный образ:** мрачный могучий антропоморфный кот-титан. Холодно-стальной мех с серебристо-серыми вкраплениями. Длинные тёмно-серебряные волосы до плеч, седеющие на висках. Длинная густая борода (только у Кроноса в этом цикле — маркер старшего поколения). Глаза янтарно-жёлтые, хищные. Одет в тяжёлую бронзовую кирасу поверх тёмной туники, на поясе — широкий пояс с черепами-медальонами (намёк на пожирание детей). В правой руке — изогнутый серп из несокрушимого камня (адамант) с тёмно-серым лезвием.

**Английская карточка (images.md):**

```
Cronus the anthropomorphic bipedal cat titan, cold-steel-grey fur with silver streaks, long dark-silver shoulder-length hair greying at the temples, full thick beard, sharp amber-yellow predator eyes, dressed in heavy bronze cuirass over dark grey tunic, wide belt with skull-shaped medallions, holding a curved jagged adamant sickle in his right paw, towering muscular frame, stern brooding face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the brooding bearded titan cat king, cold-steel-grey fur with silver streaks, long dark-silver shoulder hair, full beard, amber-yellow eyes, bronze cuirass over dark tunic, skull-medallion belt, holding a curved jagged adamant sickle, standing upright on two legs
```

**Эволюция:**

- **Ч. 1 финал** — самый младший в массе из 12 новорождённых титанов. Подросток, без бороды, без седины. Выделяется только взглядом — «дерзкий, в отличие от других». Серпа ещё нет. Это просто намёк-маркер «вот этот будет важен в ч. 2».
- **Ч. 2 (sent_006–007: согласие + удар)** — молодой титан-узурпатор. Борода короткая, без седины, серп получает от Геи и тут же наносит удар. Кадр свержения — силуэт согнувшегося Урана, вспышка серпа (см. карточку Урана → «Эволюция»). Сам удар НЕ в кадре.
- **Ч. 2 (sent_012: воцарение)** — надевает корону отца на свою голову. Длинная борода, седина на висках, надменный взгляд. Сидит на троне рядом с Реей.
- **Ч. 2 (sent_013–015: пророчество + пожирание)** — параноидальный отец. Сначала слушает пророчество Геи (тень от рун на лице), потом каждый раз, когда Рея рожает, **поглощает** новорождённого котёнка. Поглощение показано стилизованно: котёнок в свивальнике превращается в свет/звёзды и втягивается в Кроноса. **Никакого рта, никакого глотка в кадре. Никакой крови.** Глаза тёмные, в кругах.
- **Ч. 3** — свергнут. Закован в цепи у входа в Тартар, борода спутана, корона разбита. **Не показывать раны.**

---

## Рея

*(ч. 2 — три состояния в одной части: молодая жена Кроноса → измученная мать пятерых поглощённых детей → беглянка, скрывающаяся в горах беременной Зевсом; ч. 3 — подменяет Зевса камнем в свивальнике, прячет младенца в пещере на Крите; в опц. ч. 4-5 — короткое появление, благословляет Зевса)*

**Визуальный образ:** взрослая антропоморфная кошка-титанида. Кремово-золотой мех с тёплыми персиковыми переливами. Длинные медово-золотые волосы, заплетённые в косу через плечо. Глаза тёплые карие. Одета в струящееся платье цвета слоновой кости с золотой вышивкой колосьев и львов. На голове тонкая золотая диадема. В ч. 4 — пеленает камень в свивальник вместо Зевса (центральная сцена).

**Английская карточка (images.md):**

```
Rhea the anthropomorphic bipedal cat titaness mother, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair braided over her shoulder, warm brown eyes, dressed in a flowing ivory gown with gold embroidery of wheat sheaves and lions, thin gold diadem on her head, gentle protective expression, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the gentle titaness mother cat character, cream-and-pale-gold fur with peach undertones, long honey-gold hair braided over her shoulder, warm brown eyes, flowing ivory gown with gold wheat-and-lion embroidery, thin gold diadem, standing upright on two legs
```

**Эволюция:**

- **Ч. 2 (sent_012: молодая жена)** — спокойная титанида рядом с воцарившимся Кроносом. Светлое платье, тонкая диадема, тёплая улыбка. Это её самое мирное состояние в цикле.
- **Ч. 2 (sent_014–015: пожирание детей)** — измученная мать. С каждым проглоченным ребёнком — глаза всё темнее, поза всё ниже. На пятом (Посейдоне) — стоит на коленях, протянув руки за уносимым в свет силуэтом котёнка. **Без крика, без агонии** — тихая безмолвная скорбь.
- **Ч. 2 финал (sent_016–019: беглянка)** — прячется в горной пещере. Тёплый плащ-накидка поверх платья. Глаза твёрдые, решительные. На животе — мягкое золотистое свечение (Зевс растёт внутри). Спокойствие после побега.
- **Ч. 3** — пеленает камень в свивальник, протягивает его Кроносу. Глаза полны слёз и решимости. Сразу после — прячет настоящего младенца Зевса в пещере на Крите.
- **Опц. ч. 4-5** — короткое появление, благословляет Зевса перед битвой / делёжом мира.

---

## Иапет

*(ч. 1 финал — один из 12 новорождённых титанов, особое появление; ч. 3 — сражается на стороне Кроноса в Титаномахии)*

**Визуальный образ:** могучий антропоморфный кот-титан. Бронзово-медный мех. Короткие тёмно-медные волосы, короткая борода. Зелёно-золотые глаза. Одет в кожаную бронированную тунику с медными заклёпками. В руке — копьё с медным наконечником. Высокий, мускулистый, воинственный.

**Английская карточка (images.md):**

```
Iapetus the anthropomorphic bipedal cat titan warrior, bronze-and-copper fur, short dark-copper hair, short trimmed beard, green-gold eyes, dressed in a leather-and-bronze armored tunic with copper rivets, holding a bronze-tipped spear, towering muscular frame, fierce battle-ready face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the bronze-furred warrior titan cat character, bronze-and-copper fur, short dark-copper hair and trimmed beard, green-gold eyes, leather-and-bronze armored tunic with copper rivets, bronze-tipped spear, standing upright on two legs
```

**Примечание:** в ч. 1 финал Иапет выделяется среди массы новорождённых титанов как «дядя Прометея» (мост к одиночному мифу про Прометея). В ч. 3 — главный воин-титан в битве (после Кроноса).

---

## Прочие титаны (массовка)

*(ч. 1 финал — рождаются у Геи и Урана; ч. 3 — массовка в Титаномахии)*

12 титанов изначально, из них в индивидуальных карточках выше — **Кронос, Рея, Иапет**. Остальные 9 показываются как **массовка**: толпа фигур разных металлов и камней.

**Маркеры различимости в кадре** (если в сцене 2-3 титана одновременно — придерживаться этих палитр; если массовка из 6+ — просто разноцветные титаны без чётких имён):

| Титан | Палитра в массовке |
|---|---|
| Океан (титан моря) | сине-зелёный с серебром, борода-волна |
| Гиперион (титан света) | золотисто-белый, сияние |
| Кой (титан разума) | тёмно-индиго, серебряные глаза |
| Криос (титан созвездий) | пурпурный с серебром |
| Тейя (титанида сияния) | золотисто-белая, лучистая |
| Фемида (титанида правосудия) | оливково-зелёная, повязка на глазах (см. content/Фемида/ — для будущего мифа) |
| Мнемосина (память) | тёмно-серо-голубая, со свитком |
| Феба (титанида сияния луны) | серебристо-белая, лунные узоры |
| Тефида (титанида моря) | бирюзовая, ракушки в волосах |

**Английская карточка для массовки (images.md):**

```
twelve anthropomorphic bipedal cat Titans gathered in a stone hall, each in a distinctive metallic or elemental palette — bronze, copper, silver, steel, gold, deep-indigo, sea-green, ivory, olive, violet — varied robes of bronze and linen with elemental motifs (waves, stars, wheat, moonlight), humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):** карточка и так descriptive, копировать без изменений.

---

## Циклопы

*(ч. 1 финал — рождаются у Геи и Урана, на последнем кадре Уран начинает запирать их обратно в Гею; ч. 2 — выходят на свет после свержения Урана как фоновая массовка освобождённых детей Геи; ч. 3 — освобождены Зевсом из Тартара / земли, куют молнии Зевсу, трезубец Посейдону, шлем-невидимку Аиду)*

Три циклопа: **Бронт** (Гром), **Стероп** (Молния), **Арг** (Сияние). Не путать с одноглазым великаном-людоедом Полифемом из мифа об Одиссее — там другой циклоп.

**Визуальный образ:** мощные мускулистые антропоморфные коты-кузнецы. Тёмно-серый каменно-шиферный мех, очень короткий. **Один большой круглый глаз посреди лба** (цвет глаза разный у каждого — у Бронта оранжевый-янтарь, у Стеропа электрически-белый, у Арга золотой). Голые торсы, кожаные кузнечные фартуки, бронзовые наручи. В руках — молоты, клещи, наковальни.

**Английская карточка (images.md):**

```
three Cyclops anthropomorphic bipedal cat blacksmith brothers — Brontes Steropes Arges — massive muscular frames, short stone-slate-grey fur, ONE large round eye in the middle of each forehead (NO two eyes), Brontes has amber eye, Steropes has electric-white eye, Arges has gold eye, bare muscular torsos with leather blacksmith aprons, bronze arm bracers, holding hammers and tongs and anvils, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
three muscular one-eyed blacksmith cat brothers, stone-slate-grey fur, ONE single round glowing eye each in the middle of the forehead, bare torsos with leather aprons and bronze bracers, hammers and tongs, standing upright on two legs
```

**Критично:** ОДИН глаз. Модель Flow по умолчанию рисует двух глаз; в каждом промпте сцены с циклопами **дважды повторить** `ONE single round eye in the middle of the forehead, NO two eyes`.

---

## Гекатонхейры

*(ч. 1 финал — рождение, на последнем кадре Уран начинает запирать их обратно в Гею; ч. 2 — выходят на свет после свержения Урана как фоновая массовка освобождённых детей Геи; ч. 3 — освобождены Зевсом из Тартара, побеждают титанов и остаются охранять их в Тартаре)*

Три гекатонхейра: **Котт** (Гневный), **Бриарей** (Сильный), **Гиес** (Большерукий). В мифе у каждого 50 голов и 100 рук. Прямо «100 рук и 50 голов» в pixel-art-формате нереализуемо (получится клубок), поэтому **стилизуем как «сторуких котов»**: одна голова + **6 крупных основных рук с оружием** (по 3 с каждой стороны) + **радиальный веер из ~10 дополнительных мелких “вторичных” рук**, торчащих из плеч и спины. Большие руки читаются как «вот с чем он бьётся», веер из мелких — передаёт мифическую «сторукость» как визуальный маркер.

**Визуальный образ:** огромные антропоморфные коты — даже выше титанов. Тёмно-каменный мех с гранитными прожилками. Бритые головы или короткая щётка. Глаза тлеющие оранжевые. Полуобнажённые торсы. **6 основных рук** (по 3 с каждой стороны) держат разное оружие — дубины, валуны, цепи. **~10 дополнительных мелких рук** торчат веером сзади и из плеч, как нимб из ладоней — они жестикулируют в разные стороны (статично в кадре, без явного движения).

**Английская карточка (images.md):**

```
three Hecatoncheires anthropomorphic bipedal cat hundred-handed giants — Cottus Briareus Gyges — towering even larger than the titans, dark granite-stone fur with cracked rock vein patterns, shaved or stubble heads, glowing ember-orange eyes, EACH GIANT HAS MANY ARMS — six large primary arms (three on each side of the body) holding the main weapons, PLUS a dense radial fan of about ten additional smaller secondary arms sprouting from the shoulders and back creating an unmistakable hundred-handed silhouette, the additional fan-arms gesturing and flexing in different directions like a halo of hands, bare granite-grey torsos, primary arms holding different weapons — clubs boulders chains stone hammers stone spears, single head one face per giant (NOT many heads — one face only), humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
three towering granite-stone hundred-handed cat giant brothers, dark granite-stone fur with cracked rock veins, shaved heads, glowing ember-orange eyes, each with six large primary arms (three per side) plus a radial fan of about ten extra smaller arms behind, one head and one face per giant, primary hands holding clubs boulders chains, standing upright on two legs
```

**Критично для модели Flow:**

1. **Голова одна.** Модель по умолчанию пытается рисовать многоголовых — повторить `single head one face per giant, NOT many heads`.
2. **Руки — много, но осмысленно.** Не «50 рук» (модель не справится) и не «2 руки» (теряется мифический образ). Прописывать дословно: «6 large primary arms holding weapons + ~10 smaller secondary arms in a radial fan». Это даёт стабильный читаемый pixel-art силуэт.
3. **На вход image-to-video в Veo (см. video.md)** — descriptive выше, имя `Hecatoncheires` сохраняем (это не игровой IP-триггер в отличие от `Zeus`/`Hades`/`Persephone`).

---

# Поколение 3: Олимпийцы — рождение и Титаномахия (ч. 2, 3, опц. 4, 5)

## Афродита

*(ч. 2, sent_010 — рождается из морской пены, куда упали капли свергнутого Урана; в данном цикле дальше не появляется. Полноценно — в опц. ч. 5 «12 Олимпийцев» и в будущих одиночных мифах)*

**Визуальный образ:** молодая антропоморфная кошка-богиня красоты. Перламутрово-розовый мех с молочно-белым подшёрстком. Длинные кремово-белые волосы до пояса, словно покрытые морской пеной. Глаза цвета морской волны (бирюзово-зелёные). В ч. 2 появляется обнажённой из морской пены, прикрытой только волосами и пеной (без откровенного обнажения — модель Flow аккуратно скроет область пеной и волосами).

**Английская карточка (images.md):**

```
Aphrodite the anthropomorphic bipedal cat goddess of beauty rising from sea foam, pearl-pink fur with milky-white undershade, long cream-white hair flowing down her back covering her body, turquoise-green sea-wave eyes, modestly covered by curling sea foam and her own long hair, soft inner glow, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the beauty cat goddess rising from sea foam, pearl-pink fur, long cream-white hair flowing over her body, turquoise sea-wave eyes, covered by sea foam and hair, soft inner glow, standing upright on two legs
```

**Платформенная безопасность:** ни в коем случае не рисовать явное обнажение — модель Flow часто скатывается. В промпт обязательно: `modestly covered by sea foam and her long hair, no nudity, no explicit body`.

---

## Эринии (Алекто, Тисифона, Мегера)

*(в данном цикле «От Хаоса до Олимпа» **не появляются**; карточка остаётся как заглушка для будущих одиночных мифов — напр. Орест)*

> ⚠️ **Удалены из текущего нарратива ч. 2.** Изначально эринии должны были рождаться из крови свергнутого Урана (мифологический канон). В ч. 2 «Власть Кроноса» этот эпизод заменён на поэтический образ слёз Урана как дождя (см. карточку Урана → «Эволюция → Ч. 2 sent_011»). Эринии не нужны в нарративе ч. 2 и могут отвлечь визуально (фурии с пылающими глазами + кровь = лишний негативный слой для платформ).

Три сестры-мстительницы. Полноценно живут в одиночных мифах (напр. Орест).

**Визуальный образ:** три антропоморфные кошки-фурии. Тёмно-угольный мех. Длинные растрёпанные волосы, в которых живут змеи (по 1-2 змеи в волосах, не клубок). Глаза — кроваво-красные, светящиеся. Босые. Простые тёмные туники. В руках — кнуты или горящие факелы. Худые, остроносые, агрессивные.

**Английская карточка (images.md):**

```
three Furies anthropomorphic bipedal cat sisters — Alecto Tisiphone Megaera — dark charcoal-black fur, long wild matted black hair with one or two small green snakes coiled inside, blood-red glowing eyes, barefoot, wearing simple dark torn tunics, each holding a burning torch or a leather whip, gaunt sharp-featured fierce faces, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
three fury-sister cat characters, dark charcoal-black fur, long wild matted black hair with small green snakes inside, blood-red glowing eyes, barefoot, dark torn tunics, torches or whips, standing upright on two legs
```

---

## Зевс

*(ч. 2 финал — силуэт-эмбрион внутри беременной Реи (sent_018–019), первое появление имени в озвучке; ч. 3 — рождение, спасение от Кроноса через подмену камнем, взросление в пещере на Крите, возвращение, освобождение братьев, Титаномахия; опц. ч. 4 — делит мир; опц. ч. 5 — царь Олимпа)*

**Главный персонаж цикла.** Эволюция образа — **четыре** стадии, один и тот же кот: эмбрион → младенец → юноша → владыка.

**Базовая палитра (одна на все возрасты):** золотисто-белый мех (слоновая кость + золотые подпалины), синие электрические глаза, золотой отблеск шерсти. Это то, что НЕ меняется между возрастами.

### Зевс-эмбрион (ч. 2 финал, sent_018–019)

**Визуальный образ:** в кадре **не Зевс сам**, а Рея-беглянка в горной пещере. Над её животом — мягкое **золотистое внутреннее свечение** в форме сидящего силуэта-эмбриона котёнка с зачаточными золотыми искрами над «головой» (намёк на будущую молнию). Силуэт читается через ткань платья как светящееся пятно, не как полноценный персонаж. Лица нет. Это **первое появление Зевса в цикле** — он ещё не родился, но имя уже звучит.

**Английская карточка (images.md):**

```
Rhea pregnant titaness cat in a hidden mountain cave, her belly glowing with a soft warm golden inner light shaped like a tiny seated kitten silhouette — the unborn Zeus — faint tiny gold lightning sparks above the kitten silhouette inside her belly visible through her gown, no face on the embryo only a glowing pose-silhouette, Rhea protective hand resting on her belly, soft warm hearth-fire glow on her face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the pregnant titaness mother cat with belly glowing warm gold in the shape of a tiny seated kitten silhouette, faint gold sparks above the inner silhouette, no embryo face only a glowing pose, hand on her belly, hidden in a mountain cave
```

### Зевс-младенец (ч. 3)

**Визуальный образ:** новорождённый антропоморфный котёнок. Маленький, слоновая кость + золотые подпалины. Большие синие глаза. Завёрнут в льняную пелёнку. Над головой едва заметные искры — будущий символ молнии. Безмятежный.

**Английская карточка (images.md):**

```
baby Zeus newborn anthropomorphic bipedal cat kitten, ivory-and-pale-gold fur with golden tabby patches, large bright sky-blue eyes, wrapped in white linen swaddling cloth, faint tiny gold lightning sparks above his head, peaceful sleeping or wide-eyed face, tiny humanoid body proportions in baby form, highly detailed pixel art
```

**Descriptive (video.md):**

```
the newborn ivory-and-gold kitten character, large bright sky-blue eyes, wrapped in white linen swaddling, faint gold sparks above his head, peaceful baby
```

### Зевс-юноша (ч. 3, середина; вырастает в пещере на Крите)

**Визуальный образ:** молодой кот-воин, подросток-юноша. Тот же золотисто-белый мех. Короткая лохматая золотистая грива (волосы средней длины, не до плеч). Без бороды. Синие электрические глаза. Простая льняная туника с золотым поясом. В руке — копьё или **уже молния** (после того как циклопы её выковали в середине ч. 3).

**Английская карточка (images.md):**

```
young Zeus anthropomorphic bipedal cat youth warrior, ivory-and-pale-gold fur with golden tabby patches, short tousled golden hair, no beard, bright electric blue eyes, dressed in a simple white linen tunic with a gold belt, holding a spear OR a glowing gold lightning bolt, lean athletic frame, determined fierce face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the young thunder-cat youth warrior, ivory-and-pale-gold fur with golden tabby patches, short tousled golden hair, electric-blue eyes, white linen tunic with gold belt, holding a spear or a glowing gold lightning bolt, standing upright on two legs
```

### Зевс-владыка (ч. 3 финал, опц. ч. 4, опц. ч. 5)

**Визуальный образ:** взрослый царь Олимпа. Тот же золотисто-белый мех. **Длинная густая золотая грива** до плеч. **Короткая золотая борода** (отличается от длинной бороды Кроноса!). Синие электрические глаза. Тяжёлая царская мантия — белая с золотом, золотые наплечники в форме облаков. На голове — тонкий лавровый венец из золота. В правой руке — золотая молния, в левой — скипетр или орёл на запястье.

**Английская карточка (images.md):**

```
Zeus the anthropomorphic bipedal cat king of Olympus, ivory-and-pale-gold fur with golden tabby patches, long thick golden mane hair to his shoulders, short trimmed golden beard, bright electric blue eyes, wearing a heavy white-and-gold royal mantle with cloud-shaped gold pauldrons, thin gold laurel wreath on his head, holding a glowing gold lightning bolt in his right paw and a tall scepter or a perched golden eagle on his left wrist, towering regal frame, commanding stern face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):** (важно — это descriptive уже используется в Персефоне, единый стиль с одиночными мифами)

```
the throned thunder cat king, ivory-and-pale-gold fur with golden tabby patches, long golden mane hair to his shoulders, short trimmed golden beard, electric-blue eyes, heavy white-and-gold royal mantle with cloud-shaped pauldrons, gold laurel wreath, glowing gold lightning bolt in his right paw, scepter or perched golden eagle in his left, standing upright on two legs
```

---

## Гера

*(ч. 2, sent_014 — поглощена Кроносом как новорождённый котёнок; ч. 3 — освобождена из чрева Кроноса, сражается в Титаномахии; опц. ч. 4 — становится царицей рядом с Зевсом; опц. ч. 5)*

**Визуальный образ:** царственная антропоморфная кошка-богиня. Кремово-белый мех с золотыми подпалинами на ушах и кончике хвоста. Длинные кремово-золотые волосы, уложенные в высокую косу или хитон-причёску. Большие тёмно-зелёные глаза. Одета в струящееся павлинье-сине-зелёное платье с золотой вышивкой павлиньих перьев. На голове — высокая золотая диадема с павлиньим пером. На запястьях — золотые браслеты. Часто в кадре рядом — павлин.

**Английская карточка (images.md):**

```
Hera the anthropomorphic bipedal cat queen goddess, cream-white fur with golden tabby tips on ears and tail, long cream-and-gold hair in a high braided crown updo, large dark emerald-green eyes, dressed in a flowing peacock-blue-and-green gown with gold peacock-feather embroidery, tall gold diadem set with a single peacock feather, gold wrist bracelets, regal proud face, sometimes a peacock at her feet, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the regal peacock-feathered cat queen goddess, cream-white fur with golden tabby tips, long cream-and-gold hair in a high braided crown updo, dark emerald-green eyes, flowing peacock-blue-and-green gown with gold peacock-feather embroidery, tall gold diadem with peacock feather, gold bracelets, sometimes a peacock at her feet, standing upright on two legs
```

**Эволюция:**

- **Ч. 2 (sent_014)** — показана как новорождённый котёнок-олимпийка, поглощается Кроносом. Стилизованно: котёнок-Гера в свивальнике с павлиньим перышком превращается в свет/звёзды и втягивается в Кроноса. **Никакого рта, никакого глотка в кадре, без жестокости.**
- **Ч. 3** — освобождена из чрева Кроноса, появляется как уже взрослая богиня (мифологическая условность — все вышли уже взрослыми). Сражается в битве.
- **Опц. ч. 4, 5** — царица, у трона Зевса.

---

## Посейдон

*(ч. 2, sent_014 — поглощён Кроносом как новорождённый котёнок; ч. 3 — освобождён, сражается; опц. ч. 4 — получает в удел море; опц. ч. 5)*

**Визуальный образ:** мощный антропоморфный кот-морской царь. Сине-зелёный мех с серебристым отливом (как поверхность моря). Длинные тёмно-синие волосы и густая борода, словно мокрые морские волны. Глаза глубокого моря — тёмно-сине-зелёные. Голый мощный торс (или лёгкая туника морского-синего цвета), на плечах — плащ из водорослей и ракушек. **Трезубец** в правой руке — главный атрибут. Скорее босой или в сандалиях.

**Английская карточка (images.md):**

```
Poseidon the anthropomorphic bipedal cat sea king god, sea-blue-and-green fur with silvery sheen like water surface, long deep-navy wavy hair and thick wavy beard like ocean waves, deep sea-green eyes, bare muscular torso OR light sea-blue tunic, cloak of seaweed and seashells on his shoulders, holding a massive gold trident in his right paw, barefoot or sandals, powerful stern face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the sea-blue trident-wielding cat king god, sea-blue-and-green fur with silvery sheen, long deep-navy wavy hair and thick wavy beard like ocean waves, deep sea-green eyes, muscular torso, cloak of seaweed and seashells, holding a massive gold trident, standing upright on two legs
```

---

## Аид

*(ч. 2, sent_014 — поглощён Кроносом как новорождённый котёнок; ч. 3 — освобождён, сражается; опц. ч. 4 — получает в удел подземный мир)*

> **Важно:** descriptive Аида **уже задана эталонной формулировкой Персефоны** — это критическая преемственность с одиночным мифом «Персефона и Аид» (см. [CONTEXT.md](../../CONTEXT.md) → «IP-фильтр Veo»). Зритель, посмотревший «От Хаоса до Олимпа» и потом «Персефону», должен УЗНАТЬ Аида. Поэтому английская карточка тут спроектирована так, чтобы согласовываться с тем, что уже сделано в Персефоне.

**Визуальный образ:** мрачный могучий антропоморфный кот, владыка подземного мира. Угольно-чёрный мех с тёмно-серыми подпалинами. Длинные тёмно-серые волосы до плеч, короткая аккуратная серебристая борода. Глаза — холодные платиновые (бесцветно-серебряные), иногда с тёмно-фиолетовым отсветом. Одет в чёрный с золотой оторочкой плащ-мантию, на плечах — застёжки в форме гранатов. На голове — тёмный венец из чёрного железа с зубцами. В руке — церемониальный посох (НЕ скипетр — Veo не любит «scepter»), на запястье часто — Цербер-щенок (в ч. 2-3 ещё не взрослый).

**Английская карточка (images.md):**

```
Hades the anthropomorphic bipedal cat king god of the underworld, somber dark-charcoal-gray fur with deeper grey patches, long dark-grey shoulder-length hair, short trimmed silver beard, cold platinum-silver eyes with faint violet glints, dressed in a long black mantle trimmed in gold with pomegranate-shaped shoulder clasps, dark iron jagged crown on his head, holding a tall ornate ceremonial staff, sometimes a small Cerberus-puppy at his side, regal brooding face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):** **(использовать ровно эту формулировку, она уже работает в роликах Персефоны)**

```
the somber dark-charcoal-gray regal cat king, long dark-grey shoulder-length hair, short trimmed silver beard, cold platinum-silver eyes with faint violet glints, long black mantle trimmed in gold with pomegranate-shaped shoulder clasps, dark iron jagged crown, holding a tall ornate ceremonial staff, standing upright on two legs
```

**Эволюция:**

- **Ч. 2 (sent_014)** — котёнок-Аид (тёмно-угольный пушок, серебряные глаза-точки) поглощается Кроносом стилизованно: котёнок в свивальнике превращается в свет/звёзды и втягивается. **Никакого рта, никакого глотка в кадре.**
- **Ч. 3** — освобождён, сражается в Титаномахии. Уже взрослый, но без короны и плаща (юноша-воин, потом получит регалии).
- **Опц. ч. 4** — получает в удел подземный мир. Появляется в полной царственной форме (см. карточку выше) у входа в подземный мир.

---

## Деметра

*(ч. 2, sent_014 — поглощена Кроносом как новорождённый котёнок; ч. 3 — освобождена; опц. ч. 5 — олимпийка; мост к будущему мифу «Персефона и Аид», где она — мать Персефоны)*

**Визуальный образ:** взрослая антропоморфная кошка-богиня урожая. Пшенично-золотой мех с тёплыми медовыми оттенками. Длинные медово-золотые волосы, заплетённые в косу через плечо или украшенные колосьями. Большие тёплые карие глаза. Одета в платье цвета спелой пшеницы с зелёной вышивкой колосьев и маков. На голове — венок из колосьев. В руке — серп (золотой, не угрожающий — для урожая) или сноп пшеницы.

**Английская карточка (images.md):**

```
Demeter the anthropomorphic bipedal cat goddess of harvest, wheat-and-honey-gold fur with warm amber tabby tips, long honey-gold hair braided over her shoulder or adorned with wheat stalks, large warm brown eyes, dressed in a wheat-gold gown embroidered with green wheat stalks and red poppies, wheat-stalk wreath on her head, holding a golden harvest sickle or a bound sheaf of wheat, gentle maternal face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the wheat-gold harvest cat goddess, wheat-and-honey-gold fur with warm amber tips, long honey-gold hair with wheat stalks, warm brown eyes, wheat-gold gown with green wheat and poppy embroidery, wheat wreath, holding a golden harvest sickle or sheaf of wheat, standing upright on two legs
```

---

## Гестия

*(ч. 2, sent_014 — поглощена Кроносом **первой** как новорождённый котёнок; ч. 3 — освобождена; опц. ч. 5 — упоминание; самая скромная из олимпийцев)*

**Визуальный образ:** мягкая, скромная антропоморфная кошка-богиня очага. Мягко-бежевый, пшенично-кремовый мех с тёплыми ушками-подпалинами. Длинные распущенные кремовые волосы. Тёплые золотисто-карие глаза. Одета в простое домашнее платье цвета охры с белой каймой, на плечи накинут лёгкий бежевый плащ. В руке — горящий факел или маленькая глиняная масляная лампа. Возле ног — тёплое сияние очага.

**Английская карточка (images.md):**

```
Hestia the anthropomorphic bipedal cat goddess of the hearth, soft-beige cream fur with warm tabby ears, long loose cream hair, warm gold-brown eyes, dressed in a simple ochre home gown with white trim, light beige shawl over her shoulders, holding a burning torch or a small clay oil lamp, soft hearth-fire glow around her feet, gentle modest face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the gentle hearth-fire cat goddess, soft-beige cream fur with warm tabby ears, long loose cream hair, gold-brown eyes, simple ochre gown with white trim, light beige shawl, holding a burning torch or clay oil lamp, hearth-fire glow at her feet, standing upright on two legs
```

---

# Опциональная часть 5: остальные Олимпийцы

*(если решим делать опц. ч. 5 «12 Олимпийцев» — здесь нужны полные карточки. Сейчас — заглушки с базовыми descriptive из CONTEXT.md → таблица замен. Полные карточки прорабатываются перед опц. ч. 5.)*

## Афина

*(рождается из головы Зевса)*

**Базовый descriptive (из CONTEXT.md → IP-фильтр Veo):** `the silver-grey-and-white wisdom cat goddess`

**TODO** заполнить полную карточку перед опц. ч. 5: серебристо-серый + белый мех, серые глаза, золотой шлем, копьё, эгида, сова на запястье.

## Аполлон

**Базовый descriptive (из CONTEXT.md):** `the golden sun cat archer`

**TODO** заполнить: золотистый мех, лук и колчан, лира, лавровый венец, золотисто-зелёные глаза.

## Артемида

**TODO** заполнить: серебристо-белый мех, лунный венец, охотничий лук, короткая туника, серебряные сандалии. Сестра-близнец Аполлона.

## Гермес

**TODO** заполнить: серо-бежевый мех, крылатые сандалии, петас (шляпа с крыльями), кадуцей.

## Арес

**TODO** заполнить: красно-бурый мех, бронзовый доспех, копьё и щит, шрам через щёку.

## Гефест

**TODO** заполнить: тёмно-серый мех, кожаный кузнечный фартук, молот, искры. Хромой — одна нога короче.

## Дионис

**TODO** заполнить: винно-пурпурный мех, виноградные лозы в волосах, тирс (жезл с шишкой).

---

# Чек-лист консистентности (при работе с новым частью)

Перед написанием промптов очередного `часть_NN/prompts/images.md`:

1. ✅ **Перечислить персонажей сцены.** Кто появляется?
2. ✅ **Найти карточку каждого здесь.** Если новый бог — добавить карточку в этот файл ДО написания промптов.
3. ✅ **Скопировать английский блок дословно** в начало `images.md` части как HTML-комментарий с карточкой персонажа (по аналогии с одиночными мифами).
4. ✅ **Подставить нужный возрастной/эмоциональный вариант** для Зевса (эмбрион в утробе Реи / младенец / юноша / владыка), Кроноса (подросток в массе титанов / молодой узурпатор / надевший корону тиран / параноик-отец / закованный), Геи (спокойная / одинокая / страдающая / мстительная / пророческая), Реи (молодая жена / измученная мать / беглянка с Зевсом / подмена камнем).
5. ✅ **В каждой сцене где видна голова персонажа** — упомянуть волосы явно (см. правило про «лысую голову под короной» в [MYTH.md](../../MYTH.md) → шаг 7).
6. ✅ **Антропоморфность** — каждое появление: `bipedal humanoid body proportions standing upright on two legs`.
7. ✅ **Для `video.md`** — заменить имена на descriptive из «Descriptive (video.md)» каждой карточки.
8. ✅ **Уникальный subject-маркер** в первых 3-4 словах каждого `**Промпт:**` (см. [CONTEXT.md](../../CONTEXT.md) → «Уникальный subject-маркер»).

---

# Журнал изменений

- **2026-05-14** — Файл создан. Заполнены полные карточки первобожеств, Урана, главных титанов (Кронос, Рея, Иапет), массовки титанов, циклопов, гекатонхейров, Афродиты, эриний, всех 6 первородных олимпийцев (Зевс, Гера, Посейдон, Аид, Деметра, Гестия). Карточка Аида согласована с descriptive из живых роликов Персефоны. Заглушки для опциональных карточек ч. 7 (Афина, Аполлон, Артемида, Гермес, Арес, Гефест, Дионис).
- **2026-05-17** — **Первобожества переведены в отдельный визуальный класс «абстрактные сущности-стихии с глазами».** Гея, Тартар, Эрос, Эреб, Никта, Уран — больше не антропоморфные коты, а сами стихии (земля-пейзаж, бездна-пропасть, орб-свечение, дымное облако, ночное облако, звёздный купол) с парой светящихся глаз внутри. Эмоции читаются через изменения самой стихии (трещины, тучи, потускневший свет, золотые слёзы по холмам), не через позы и мимику тела. Добавлены отдельные карточки Эфира и Гемеры (раньше были только в HTML-блоке images.md ч. 1). Сводная таблица помечена символом ⬜ для абстрактных сущностей. Эволюция Геи и Урана переписана через «изменения ландшафта/неба», не «согнулась/застигнут врасплох». Кронос, прочие титаны, циклопы, гекатонхейры — **остаются котами**, как и было. Изменение глобальное: применяется и к ч. 1, и к будущим частям 2–4 (где появляются те же первобожества).
- **2026-05-17** — **Перенумерация под новую структуру цикла (4 базовых ч. → 3 базовых ч., см. [series.md](series.md) → журнал).** Бывшая ч. 2 «Свержение Урана» + бывшая ч. 3 «Кронос пожирает детей» склеены в новую **ч. 2 «Власть Кроноса»**. Бывшая ч. 4 «Титаномахия» → новая ч. 3. Опц. ч. 5-6 (Делёж + Олимпийцы) → опц. ч. 4-5. Все эволюционные блоки персонажей пересмотрены под новые номера: **Гея** (страдающая→мстительная→пророческая теперь в одной ч. 2; после ч. 2 в цикле не появляется), **Уран** (ч. 2 не погибает, а навсегда поднимается в небо; добавлены образы «капли → Афродита» и «слёзы → дождь как лейтмотив части»), **Кронос** (4 состояния все теперь в ч. 2: подросток в массе титанов → молодой узурпатор → надевший корону тиран → параноик-отец, глотающий детей; ч. 3 — свергнут), **Рея** (3 состояния в ч. 2: молодая жена → измученная мать пятерых поглощённых детей → беглянка в горах беременной Зевсом; ч. 3 — подмена камнем), **Зевс** (добавлена 4-я стадия «эмбрион в утробе Реи» для финала ч. 2; младенец/юноша/владыка перенумерованы в ч. 3 и опц. 4-5), **Афродита** (рождение перенесено из ч. 3 в ч. 2 sent_010), **первенцы Кроноса** (Гестия/Деметра/Гера/Аид/Посейдон — поглощаются в ч. 2 sent_014 стилизованно как свет/звёзды, освобождаются в ч. 3). Раздел «Опциональная часть 7» переименован в «Опциональная часть 5». **Эринии удалены из цикла** — карточка сохранена как заглушка для будущих одиночных мифов; в самой ч. 2 их место занимает поэтический образ слёз Урана как дождя.
