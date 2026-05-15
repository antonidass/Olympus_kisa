# Карта персонажей: Древо богов

> **Источник правды.** При написании промптов в `часть_NN/prompts/images.md` и `video.md` копировать английский блок ДОСЛОВНО (цвет меха, глаза, одежда, аксессуары, поза). Модель Flow/Veo не помнит, что было в прошлой сцене и тем более в прошлой части.
>
> **Канал = pixel-art коты.** Каждый бог — антропоморфный бипедальный кот (см. [CONTEXT.md](../../CONTEXT.md) → «Персонажи»). Английские карточки уже включают `anthropomorphic bipedal cat character, standing upright on two legs, humanoid body proportions`. Негативы `NO humans, NO real four-legged cats` добавляются в каждый промпт отдельно через стилевой каркас.
>
> **`video.md` ≠ `images.md`.** В `images.md` имена богов (`Zeus`, `Hades`, `Cronus` …) можно оставлять — фильтр Flow/ImageFX мягкий. В `video.md` имена ЗАПРЕЩЕНЫ из-за IP-фильтра Veo — использовать раздел «Descriptive (video.md)» каждой карточки. См. [CONTEXT.md](../../CONTEXT.md) → «IP-фильтр Veo».
>
> **Эволюция образа.** Если бог растёт по ходу цикла (Зевс: младенец → юноша → владыка), у него подразделы по возрастам. Это один персонаж, не три — меняются возраст, поза, аксессуары, но окрас/глаза/общая конституция те же.

---

## Сводная таблица: палитра и появления

| # | Персонаж | Поколение | Палитра / маркер | Появляется в частях |
|---|---|---|---|---|
| 1 | Хаос | прим. бездна | тёмно-фиолетовая туманность, угольные искры | 1 |
| 2 | Гея | прим. (Земля) | моховой зелёный + бурый, венок из листвы | 1, 2, 3, 4 |
| 3 | Тартар | прим. (Бездна) | антрацит + красные прожилки, без лица | 1, 5 |
| 4 | Эрос (космог.) | прим. (Сила влечения) | золото-розовый, лучистый, юный | 1 |
| 5 | Эреб | прим. (Мрак) | тёмно-серый, пепельный, плащ-тень | 1 |
| 6 | Никта | прим. (Ночь) | иссиня-чёрный мех, звёзды в шерсти | 1 |
| 7 | Уран | Небо (сын Геи) | сине-серебристый, звёздная мантия | 2, 3 |
| 8 | Кронос | титан, узурпатор | холодная сталь, седина, серп | 2, 3, 4, 5 |
| 9 | Рея | титанида, мать | кремово-золотой, материнский, тёплый | 2, 4, 5 |
| 10 | Иапет | титан (отец Прометея) | бронзово-медный, могучий | 2, 5 |
| 11 | Прочие титаны | массовка (4 ♂ + 5 ♀) | металлы и камни | 2, 5 |
| 12 | Циклопы | (Бронт, Стероп, Арг) | мускулистые, 1 крупный глаз, кузнецы | 2, 5 |
| 13 | Гекатонхейры | (Котт, Бриарей, Гиес) | многорукие, тёмно-каменные | 2, 5 |
| 14 | Афродита | (рождена из пены) | перламутрово-розовый, пенно-белый | 3, (опц. 7) |
| 15 | Эринии | массовка (3 фурии) | угольные, окровавленные глаза | 3 |
| 16 | Зевс | олимпиец, царь | золото-слоновая кость, синие глаза, молния | 4, 5, 6, 7 |
| 17 | Гера | олимпийка, царица | кремово-белый, павлинья мантия | 4, 5, 6, 7 |
| 18 | Посейдон | олимпиец, море | сине-зелёный, борода-волна, трезубец | 4, 5, 6, 7 |
| 19 | Аид | олимпиец, подземье | угольно-чёрный, тёмный плащ | 4, 5, 6 |
| 20 | Деметра | олимпийка, урожай | пшенично-золотой, колосья | 4, 5, 7 |
| 21 | Гестия | олимпийка, очаг | мягко-бежевый, тёплый, скромный | 4, 5, 7 |

Опциональная часть 7 («12 Олимпийцев») потребует ещё карточки для Афины, Аполлона, Артемиды, Гермеса, Ареса, Гефеста, Диониса — заглушки в конце файла.

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

*(ч. 1 — рождение из Хаоса; ч. 2 — рождает Урана и титанов; ч. 3 — даёт серп Кроносу; ч. 4 — упоминается в пророчестве)*

**Визуальный образ:** антропоморфная кошка — мать-земля. Зрелая, мудрая, спокойная. Тёмно-зелёный с моховыми и бурыми вкраплениями мех. Волосы длинные, до пояса, переплетены с лозами, дубовыми листьями и мелкими цветами. Одета в платье из коры и мха, на голове венок из листвы. Глаза тёплые золотисто-зелёные. Высокая, статная.

**Палитра:** dark moss green + warm earth brown + gold-green eyes + cream petals accents.

**Английская карточка (images.md):**

```
Gaia the anthropomorphic bipedal cat earth mother, dark-moss-green-and-earth-brown fur, long hair flowing down her back intertwined with oak leaves and grape vines and small wildflowers, dressed in a robe of bark and moss with cream embroidered petals, golden-green eyes, mature serene face, standing upright on two legs, humanoid body proportions, highly detailed pixel art
```

**Descriptive (video.md):**

```
the mature earth-mother cat goddess in a moss-and-bark robe, dark-moss-green-and-earth-brown fur, long hair with oak leaves and vines flowing down her back, golden-green eyes, standing upright on two legs
```

**Эволюция эмоций (внешность та же, поза меняется):**

- **Ч. 1** — спокойная, торжественная. Только что родилась из Хаоса, оглядывает мир.
- **Ч. 2** — страдающая, согнувшаяся. Уран запирает её детей внутри неё, поза боли.
- **Ч. 3** — мстительная, прямая. Протягивает серп Кроносу. Хмурый взгляд.
- **Ч. 4** — пророческая. Шепчет пророчество Кроносу. Тень от свечи на лице.

---

## Тартар

*(ч. 1 — рождение; ч. 5 — туда низвергают побеждённых титанов)*

**Визуальный образ:** не персонаж, а место-сущность. Бездонная пропасть. Если показывать персонификацию — тёмная антропоморфная фигура без чётких черт, антрацитово-чёрный мех с тлеющими красными прожилками, как остывающая лава. Без лица — там, где должно быть лицо, тёмный провал с двумя багровыми точками-глазами.

**Английская карточка (images.md):**

```
Tartarus the primordial abyss anthropomorphic shadow cat figure, anthracite-black fur with glowing crimson lava-vein patterns, no defined face only two faint crimson dot-eyes in a dark void, towering silhouette, surrounded by descending darkness, bipedal humanoid body proportions, standing upright, highly detailed pixel art
```

**Descriptive (video.md):**

```
the primordial abyss-shadow cat figure, anthracite-black fur with crimson lava-vein glows, no defined face only faint crimson eye-glows, towering silhouette standing upright on two legs
```

**В ч. 5 чаще показан как локация** (тёмная пропасть с прутьями-решёткой, куда падают побеждённые титаны), а не как персонаж. Решётка и красное свечение снизу — узнаваемые маркеры локации.

---

## Эрос (космогонический)

*(ч. 1 — рождение из Хаоса)*

> ⚠️ **Не путать с поздним Эросом — сыном Афродиты** (тот другой персонаж, не входит в данный цикл). В греческой космогонии первородный Эрос — сила влечения, удерживающая мир. Без лука, без стрел, без крылышек херувима.

**Визуальный образ:** юный антропоморфный кот-подросток. Золотисто-розовый мех, как заря. Волосы короткие, золотистые. Большие миндалевидные глаза тёплого янтарного цвета. Одет в простую льняную тунику цвета слоновой кости. От него исходит мягкое розово-золотое свечение — это сила влечения, которая теперь связывает первобожества.

**Английская карточка (images.md):**

```
Eros the primordial anthropomorphic bipedal cat youth, golden-rose fur with soft pink undertones, short tousled gold hair, large amber almond eyes, dressed in a simple ivory linen tunic, soft pink-and-gold radiant aura around him, calm warm smile, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the youthful primordial cat character of attraction, golden-rose fur, short gold hair, amber eyes, ivory linen tunic, soft pink-gold aura, standing upright on two legs
```

---

## Эреб

*(ч. 1 — рождение из Хаоса)*

**Визуальный образ:** взрослый антропоморфный кот, олицетворение мрака. Тёмно-серый, пепельный мех, как остывший уголь. Длинные распущенные волосы цвета сажи. Янтарные глаза с тёмной обводкой. Одет в длинный струящийся плащ-тень цвета чернил. Тихий, молчаливый, статичный.

**Английская карточка (images.md):**

```
Erebus the primordial anthropomorphic bipedal cat of darkness, ash-grey-and-soot fur, long loose soot-black hair flowing down his back, amber eyes with dark rings, dressed in a long flowing ink-black shadow cloak, silent stoic face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the primordial darkness cat character, ash-grey-and-soot fur, long soot-black hair flowing down his back, amber eyes, long flowing ink-black cloak, standing upright on two legs
```

**Часто в кадре рядом с Никтой** — они пара, в ч. 1 показаны вместе как двойной силуэт на фоне Хаоса.

---

## Никта

*(ч. 1 — рождение из Хаоса, пара Эреба)*

**Визуальный образ:** антропоморфная кошка-богиня ночи. Иссиня-чёрный мех с россыпью крошечных белых звёзд-точек по всей шкуре (как у настоящего ночного неба). Длинные распущенные тёмно-синие волосы до пояса. Серебристые глаза, как полная луна. На голове корона из лунных полумесяцев. Платье — тёмно-синее с серебряной звёздной вышивкой.

**Английская карточка (images.md):**

```
Nyx the primordial anthropomorphic bipedal cat goddess of night, deep blue-black fur dusted with tiny white star points across her shoulders and back, long midnight-blue hair flowing down her back, silver full-moon eyes, wearing a crown of silver lunar crescents, dressed in a deep navy gown with silver star embroidery, regal calm face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the primordial night cat goddess, deep blue-black fur dusted with tiny white star points, long midnight-blue hair flowing down her back, silver moon eyes, crown of silver lunar crescents, navy gown with silver star embroidery, standing upright on two legs
```

---

# Поколение 1: Дети Геи (ч. 2–3)

## Уран

*(ч. 2 — рождён Геей, накрывает её как небо, плодит титанов; ч. 3 — свергнут Кроносом, гибель)*

**Визуальный образ:** царственный антропоморфный кот, олицетворение неба. Сине-серебристый мех с прохладным холодным блеском, как ночное небо. Длинные серебристо-белые волосы до пояса, в них рассыпаны крошечные звёзды-точки. Холодные ледяно-голубые глаза. На голове высокая корона из серебра и сапфиров, как звёздный венец. Длинная сине-серебряная мантия со звёздной вышивкой, на плечах — облачные эполеты. Высокий, статный, надменный.

**Английская карточка (images.md):**

```
Uranus the anthropomorphic bipedal cat sky father, silvery-blue fur with cool starlight sheen, long silver-white hair flowing down his back dusted with tiny star points, icy pale-blue eyes, wearing a tall silver crown set with sapphires shaped like constellations, dressed in a long silver-and-deep-blue mantle embroidered with stars and constellations, cloud-shaped pauldrons on his shoulders, tall regal stern proud face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the regal sky-father cat character, silvery-blue fur with starlight sheen, long silver-white hair flowing down his back with star points, icy pale-blue eyes, tall silver crown with sapphire constellations, long silver-and-deep-blue starry mantle with cloud pauldrons, standing upright on two legs
```

**Эволюция:**

- **Ч. 2 (рождение, союз с Геей)** — статный, надменный, отстранённый. Стоит над лежащей Геей как небосвод.
- **Ч. 2 (запирает детей)** — гневный, тёмные тени на лице. Заталкивает циклопов и гекатонхейров обратно в Гею.
- **Ч. 3 (нападение Кроноса)** — застигнут врасплох, согнувшийся. Серп бьёт в кадре как вспышка, **самого момента удара НЕ показываем** (см. CONTEXT.md → «Ограничения платформ»). Только силуэт согнувшейся фигуры и оседающие облака.
- **Ч. 3 (после)** — растворяется в сине-серебряных частицах, уходит в небо. Из его крови (показано как тёмно-красные звёзды-капли) рождаются эринии, из пены морской — Афродита.

---

# Поколение 2: Титаны (ч. 2, 3, 4, 5)

## Кронос

*(ч. 2 — младший из титанов; ч. 3 — свергает Урана, узурпатор; ч. 4 — пожирает детей; ч. 5 — свергнут Зевсом, низвергнут в Тартар)*

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

- **Ч. 2** — молодой титан, без седины, борода короче. Стоит в массе титанов, ещё не лидер.
- **Ч. 3** — узурпатор. Длинная борода, седина на висках, серп в руке, надменный взгляд. Воцаряется.
- **Ч. 4** — параноидальный отец. Сидит на каменном троне с кубком (внутри — проглоченные дети показаны намёком, силуэт ребёнка тает в кубке). Глаза тёмные, в кругах.
- **Ч. 5** — свергнут. Закован в цепи у входа в Тартар, борода спутана, корона разбита. **Не показывать раны.**

---

## Рея

*(ч. 2 — титанида, жена Кроноса; ч. 4 — мать олимпийцев, прячет Зевса; ч. 5 — упоминается)*

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

- **Ч. 2** — молодая титанида рядом с Кроносом. Спокойная.
- **Ч. 4** — измученная мать. Под одеждой видно, что только что родила. Пеленает камень. Глаза полны слёз и решимости.
- **Ч. 5** — короткое появление, благословляет Зевса перед битвой.

---

## Иапет

*(ч. 2 — один из 12 титанов, особое появление; ч. 5 — сражается на стороне Кроноса в Титаномахии)*

**Визуальный образ:** могучий антропоморфный кот-титан. Бронзово-медный мех. Короткие тёмно-медные волосы, короткая борода. Зелёно-золотые глаза. Одет в кожаную бронированную тунику с медными заклёпками. В руке — копьё с медным наконечником. Высокий, мускулистый, воинственный.

**Английская карточка (images.md):**

```
Iapetus the anthropomorphic bipedal cat titan warrior, bronze-and-copper fur, short dark-copper hair, short trimmed beard, green-gold eyes, dressed in a leather-and-bronze armored tunic with copper rivets, holding a bronze-tipped spear, towering muscular frame, fierce battle-ready face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the bronze-furred warrior titan cat character, bronze-and-copper fur, short dark-copper hair and trimmed beard, green-gold eyes, leather-and-bronze armored tunic with copper rivets, bronze-tipped spear, standing upright on two legs
```

**Примечание:** в ч. 2 Иапет выделяется среди массы титанов как «дядя Прометея» (мост к одиночному мифу про Прометея). В ч. 5 — главный воин-титан в битве (после Кроноса).

---

## Прочие титаны (массовка)

*(ч. 2 — рождаются у Геи и Урана; ч. 5 — массовка в Титаномахии)*

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

*(ч. 2 — рождаются у Геи и Урана; ч. 2 — заперты в Гее Ураном; ч. 5 — освобождены Зевсом, куют молнии)*

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

*(ч. 2 — рождение, запирание Ураном; ч. 5 — освобождены Зевсом, побеждают титанов)*

Три гекатонхейра: **Котт** (Гневный), **Бриарей** (Сильный), **Гиес** (Большерукий). В мифе у каждого 50 голов и 100 рук — в pixel-art-формате это нереализуемо, поэтому **антропоморфизируем как «многоруких котов»**: одна голова, **6 рук** (по 3 с каждой стороны), могучие.

**Визуальный образ:** огромные антропоморфные коты — даже выше титанов. Тёмно-каменный мех с гранитными прожилками. Бритые головы или короткая щётка. Глаза тлеющие оранжевые. **6 рук** (по 3 с каждой стороны). Полуобнажённые торсы. Каждая рука держит оружие — дубины, валуны, цепи. Узнаются как «горы с глазами».

**Английская карточка (images.md):**

```
three Hecatoncheires anthropomorphic bipedal cat giants — Cottus Briareus Gyges — towering even larger than the titans, dark granite-stone fur with cracked rock vein patterns, shaved or stubble heads, glowing ember-orange eyes, SIX arms each (three on each side of the body), bare granite-grey torsos, each pair of hands holding a different weapon — clubs boulders chains, single head one face per giant, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
three towering granite-stone cat giant brothers, dark granite-stone fur with cracked rock veins, shaved heads, glowing ember-orange eyes, SIX arms each (three on each side), one head and one face per giant, hands holding clubs boulders chains, standing upright on two legs
```

**Критично:** 6 рук, не 2. Модель Flow по умолчанию рисует 2 руки; в каждом промпте — **дважды повторить** `SIX arms each, THREE on each side of the body`.

---

# Поколение 3: Олимпийцы — рождение и Титаномахия (ч. 4, 5, 6, 7)

## Афродита

*(ч. 3 — рождается из пены морской из крови Урана; в данном цикле дальше не появляется. Полноценно — в части 7 «12 Олимпийцев» и в будущих одиночных мифах)*

**Визуальный образ:** молодая антропоморфная кошка-богиня красоты. Перламутрово-розовый мех с молочно-белым подшёрстком. Длинные кремово-белые волосы до пояса, словно покрытые морской пеной. Глаза цвета морской волны (бирюзово-зелёные). В ч. 3 появляется обнажённой из морской пены, прикрытой только волосами и пеной (без откровенного обнажения — модель Flow аккуратно скроет область пеной и волосами).

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

*(ч. 3 — рождение из крови Урана)*

Три сестры-мстительницы. Появляются в ч. 3 как массовка-вспышка (момент рождения), потом уходят. Полноценно живут в одиночных мифах (напр. Орест).

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

*(ч. 4 — рождение и спасение от Кроноса; ч. 5 — освобождает братьев, ведёт олимпийцев в Титаномахии; ч. 6 — делит мир; ч. 7 — царь Олимпа)*

**Главный персонаж цикла.** Эволюция образа — три возраста, один и тот же кот.

**Базовая палитра (одна на все возрасты):** золотисто-белый мех (слоновая кость + золотые подпалины), синие электрические глаза, золотой отблеск шерсти. Это то, что НЕ меняется между возрастами.

### Зевс-младенец (ч. 4)

**Визуальный образ:** новорождённый антропоморфный котёнок. Маленький, слоновая кость + золотые подпалины. Большие синие глаза. Завёрнут в льняную пелёнку. Над головой едва заметные искры — будущий символ молнии. Безмятежный.

**Английская карточка (images.md):**

```
baby Zeus newborn anthropomorphic bipedal cat kitten, ivory-and-pale-gold fur with golden tabby patches, large bright sky-blue eyes, wrapped in white linen swaddling cloth, faint tiny gold lightning sparks above his head, peaceful sleeping or wide-eyed face, tiny humanoid body proportions in baby form, highly detailed pixel art
```

**Descriptive (video.md):**

```
the newborn ivory-and-gold kitten character, large bright sky-blue eyes, wrapped in white linen swaddling, faint gold sparks above his head, peaceful baby
```

### Зевс-юноша (ч. 5, начало; вырастает в пещере на Крите)

**Визуальный образ:** молодой кот-воин, подросток-юноша. Тот же золотисто-белый мех. Короткая лохматая золотистая грива (волосы средней длины, не до плеч). Без бороды. Синие электрические глаза. Простая льняная туника с золотым поясом. В руке — копьё или **уже молния** (после того как циклопы её выковали в середине ч. 5).

**Английская карточка (images.md):**

```
young Zeus anthropomorphic bipedal cat youth warrior, ivory-and-pale-gold fur with golden tabby patches, short tousled golden hair, no beard, bright electric blue eyes, dressed in a simple white linen tunic with a gold belt, holding a spear OR a glowing gold lightning bolt, lean athletic frame, determined fierce face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):**

```
the young thunder-cat youth warrior, ivory-and-pale-gold fur with golden tabby patches, short tousled golden hair, electric-blue eyes, white linen tunic with gold belt, holding a spear or a glowing gold lightning bolt, standing upright on two legs
```

### Зевс-владыка (ч. 5 финал, ч. 6, ч. 7)

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

*(ч. 4 — проглочена Кроносом; ч. 5 — освобождена, сражается в Титаномахии; ч. 6 — становится царицей рядом с Зевсом; ч. 7)*

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

- **Ч. 4** — показана как ребёнок-котёнок, проглатываемая Кроносом (силуэт в кубке, без жестокости).
- **Ч. 5** — освобождена из чрева Кроноса, появляется как уже взрослая богиня (мифологическая условность — все вышли уже взрослыми). Сражается в битве.
- **Ч. 6, 7** — царица, у трона Зевса.

---

## Посейдон

*(ч. 4 — проглочен; ч. 5 — освобождён, сражается; ч. 6 — получает в удел море; ч. 7)*

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

*(ч. 4 — проглочен; ч. 5 — освобождён, сражается; ч. 6 — получает в удел подземный мир)*

> **Важно:** descriptive Аида **уже задана эталонной формулировкой Персефоны** — это критическая преемственность с одиночным мифом «Персефона и Аид» (см. [CONTEXT.md](../../CONTEXT.md) → «IP-фильтр Veo»). Зритель, посмотревший «Древо богов» и потом «Персефону», должен УЗНАТЬ Аида. Поэтому английская карточка тут спроектирована так, чтобы согласовываться с тем, что уже сделано в Персефоне.

**Визуальный образ:** мрачный могучий антропоморфный кот, владыка подземного мира. Угольно-чёрный мех с тёмно-серыми подпалинами. Длинные тёмно-серые волосы до плеч, короткая аккуратная серебристая борода. Глаза — холодные платиновые (бесцветно-серебряные), иногда с тёмно-фиолетовым отсветом. Одет в чёрный с золотой оторочкой плащ-мантию, на плечах — застёжки в форме гранатов. На голове — тёмный венец из чёрного железа с зубцами. В руке — церемониальный посох (НЕ скипетр — Veo не любит «scepter»), на запястье часто — Цербер-щенок (в ч. 4-5 ещё не взрослый).

**Английская карточка (images.md):**

```
Hades the anthropomorphic bipedal cat king god of the underworld, somber dark-charcoal-gray fur with deeper grey patches, long dark-grey shoulder-length hair, short trimmed silver beard, cold platinum-silver eyes with faint violet glints, dressed in a long black mantle trimmed in gold with pomegranate-shaped shoulder clasps, dark iron jagged crown on his head, holding a tall ornate ceremonial staff, sometimes a small Cerberus-puppy at his side, regal brooding face, humanoid body proportions, standing upright on two legs, highly detailed pixel art
```

**Descriptive (video.md):** **(использовать ровно эту формулировку, она уже работает в роликах Персефоны)**

```
the somber dark-charcoal-gray regal cat king, long dark-grey shoulder-length hair, short trimmed silver beard, cold platinum-silver eyes with faint violet glints, long black mantle trimmed in gold with pomegranate-shaped shoulder clasps, dark iron jagged crown, holding a tall ornate ceremonial staff, standing upright on two legs
```

**Эволюция:**

- **Ч. 4** — котёнок, проглатываемый Кроносом.
- **Ч. 5** — освобождён, сражается в Титаномахии. Уже взрослый, но без короны и плаща (юноша-воин, потом получит регалии).
- **Ч. 6** — получает в удел подземный мир. Появляется в полной царственной форме (см. карточку выше) у входа в подземный мир.

---

## Деметра

*(ч. 4 — проглочена; ч. 5 — освобождена; ч. 7 — олимпийка; мост к будущему мифу «Персефона и Аид», где она — мать Персефоны)*

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

*(ч. 4 — проглочена первой; ч. 5 — освобождена; ч. 7 — упоминание; самая скромная из олимпийцев)*

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

# Опциональная часть 7: остальные Олимпийцы

*(если решим делать ч. 7 «12 Олимпийцев» — здесь нужны полные карточки. Сейчас — заглушки с базовыми descriptive из CONTEXT.md → таблица замен. Полные карточки прорабатываются перед ч. 7.)*

## Афина

*(рождается из головы Зевса)*

**Базовый descriptive (из CONTEXT.md → IP-фильтр Veo):** `the silver-grey-and-white wisdom cat goddess`

**TODO** заполнить полную карточку перед ч. 7: серебристо-серый + белый мех, серые глаза, золотой шлем, копьё, эгида, сова на запястье.

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
4. ✅ **Подставить нужный возрастной вариант** для Зевса (младенец/юноша/владыка), Кроноса (молодой/узурпатор/параноик/закованный), Геи (спокойная/страдающая/мстительная).
5. ✅ **В каждой сцене где видна голова персонажа** — упомянуть волосы явно (см. правило про «лысую голову под короной» в [MYTH.md](../../MYTH.md) → шаг 7).
6. ✅ **Антропоморфность** — каждое появление: `bipedal humanoid body proportions standing upright on two legs`.
7. ✅ **Для `video.md`** — заменить имена на descriptive из «Descriptive (video.md)» каждой карточки.
8. ✅ **Уникальный subject-маркер** в первых 3-4 словах каждого `**Промпт:**` (см. [CONTEXT.md](../../CONTEXT.md) → «Уникальный subject-маркер»).

---

# Журнал изменений

- **2026-05-14** — Файл создан. Заполнены полные карточки первобожеств, Урана, главных титанов (Кронос, Рея, Иапет), массовки титанов, циклопов, гекатонхейров, Афродиты, эриний, всех 6 первородных олимпийцев (Зевс, Гера, Посейдон, Аид, Деметра, Гестия). Карточка Аида согласована с descriptive из живых роликов Персефоны. Заглушки для опциональных карточек ч. 7 (Афина, Аполлон, Артемида, Гермес, Арес, Гефест, Дионис).
