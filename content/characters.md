# Карта персонажей канала «Кисы Олимпа»

> **Источник правды для ВСЕХ мифов канала.** Перед написанием `prompts/images.md` нового сценария — **сначала** заглянуть сюда. Если персонаж уже есть в файле (Артемида, Зевс, Гера и т.д.) — взять его карточку оттуда **дословно**. Если персонажа ещё нет (новый герой, новая нимфа, новое чудовище) — придумать его, добавить карточку сюда **и только потом** копировать её в `images.md` нового мифа.
>
> Так зритель, посмотревший «Орион и Артемиду» и затем «Каллисто и Аркаса», УЗНАЁТ ту же богиню. Канал держит мифологическую вселенную с консистентной кастингом — не «новая Артемида в каждом ролике».

---

## Как пользоваться файлом

### Перед написанием нового `images.md`

1. **Открыть этот файл.** Найти всех персонажей сценария в сводной таблице ниже.
2. **Существующих** — взять английскую карточку из соответствующего раздела ДОСЛОВНО и вклеить в шапку `images.md` в блок «КАРТОЧКИ ПЕРСОНАЖЕЙ». Их descriptive-версии — в шапку `video.md` в блок «descriptive ↔ имя».
3. **Новых** — придумать карточку по канону канала (см. ниже), добавить новый раздел в этот файл, обновить сводную таблицу, и только потом копировать в `images.md`.
4. **Меняющих внешность по сюжету** (новая форма, проклятье, взросление) — добавить **подраздел** в существующий раздел персонажа, как сделано для Каллисто (нимфа → изгнанница → медведица) или для Аркаса (младенец → мальчик → охотник).

### Канон канала для новых карточек

- **Класс A — антропоморфные коты.** Все герои, боги, нимфы, смертные, чудовища-с-головой = бипедальные коты с гуманоидным телосложением. Английская карточка обязательно содержит `anthropomorphic bipedal cat character, standing upright on two legs, humanoid body proportions`. Негативы `NO humans, NO real four-legged cats` каждый промпт добавляет через стилевой каркас, не через карточку.
- **Класс B — абстрактные сущности-стихии с глазами.** Первобожества (Хаос, Гея, Уран, Эреб, Никта…), которые по концепции НЕ человекоподобны — показываются как сам ландшафт/туманность/облако с двумя огромными светящимися глазами внутри. См. эталон в `content/От Хаоса до Олимпа/characters.md` (тот файл закреплён за сериалом «От Хаоса до Олимпа» и содержит первобожеств; в общеканальный `content/characters.md` они не дублируются).
- **Класс C — заколдованные звери.** Когда героя проклинают в животное (Каллисто-медведица, Ио-корова, Ликаон-волк) — это **настоящее четвероногое животное**, не кот, не гуманоид. От бывшего героя остаётся ОДИН маркер (обычно цвет глаз) — это и есть «душа внутри зверя». Негатив `NO real four-legged cats` сохраняется, поскольку животное НЕ кот.

### Структура карточки

Каждая карточка персонажа содержит:

- **Появляется в:** список мифов (с галочкой ✅ для уже сделанных и 🔜 для запланированных)
- **Визуальный образ** на русском (1 абзац)
- **Английская карточка (images.md)** — длинный английский блок для Flow/ImageFX, можно с именем
- **Descriptive (video.md)** — короткий descriptive без имени, для Veo (имена греческих богов = IP-фильтр)
- **Атрибуты-маркеры** — чеклист ✅/❌, без чего персонаж сломается
- **Эволюция / эмоциональные состояния** — если есть

### Правило про имена в `video.md`

В `images.md` имена (Callisto, Artemis, Hera, Arcas, Zeus, Apollo …) можно оставлять — фильтр Flow/ImageFX мягкий. **В `video.md` имена ЗАПРЕЩЕНЫ** из-за IP-фильтра Veo — использовать только раздел «Descriptive (video.md)» каждой карточки. См. CONTEXT.md → «IP-фильтр Veo».

---

## Сводная таблица персонажей

> Помечено ✅ = карточка уже использована в опубликованном/сделанном мифе.
> 🔜 = запланировано на будущий сценарий.
>
> **Возрастные/проклятые формы — отдельной строкой.** Если персонаж проходит через несколько возрастов или форм (Каллисто: нимфа → изгнанница → медведица; Аркас: младенец → мальчик → охотник), КАЖДАЯ форма — отдельная строка таблицы со своим маркером. Подразделы внутри одного раздела персонажа в теле файла. Брать в `images.md` ту форму, которая нужна по сюжету конкретной сцены.

### Боги и богини

| # | Персонаж | Форма / возраст | Класс | Палитра / маркер | Мифы |
|---|---|---|---|---|---|
| 1 | [Артемида](#артемида) | взрослая | A — богиня | silver-grey-and-white **tabby**, pale-silver-blue eyes, длинные серебристо-голубые волосы + диадема-полумесяц, silver longbow | ✅ Орион и Артемида, ✅ Каллисто и Аркас |
| 2 | [Зевс](#зевс-старший) | старший (зрелый царь) | A — царь | old white fur, **длинная** white beard, electric-blue eyes, white-and-gold toga, lightning bolt | ✅ Каллисто и Аркас |
| 2a | [Зевс](#зевс-старший) | молодой / владыка | A — царь | ivory-and-pale-gold tabby, золотая грива, **короткая** золотая борода | ведётся в `От Хаоса до Олимпа/characters.md` |
| 3 | [Зевс в облике Артемиды](#зевс-в-облике-артемиды-zeus-as-artemis) | маскировка | A — маскировка | визуально = Артемида, но electric-gold glint в глазах + warm-gold aura вместо cool-silver | ✅ Каллисто и Аркас |
| 4 | [Гера](#гера) | зрелая мстительная | A — царица | deep-royal-blue + peacock fur, emerald-green slit-pupil eyes, peacock-feather crown | ✅ Каллисто и Аркас |
| 4a | [Гера](#гера) | молодая (только-что освобождена из Кроноса) | A — царица | cream-white fur с золотыми пятнами | ведётся в `От Хаоса до Олимпа/characters.md` |
| 5 | [Аполлон](#аполлон) | молодой бог-близнец Артемиды | A — бог | gold-and-cream **tabby**, bright **golden-amber** eyes, **короткие вьющиеся honey-gold волосы** под лавровым венцом из полированного золота, **golden longbow** + gold quiver, warm golden divine glow | ✅ Орион и Артемида, ✅ Аполлон и Кассандра |
| 6 | [Гермес](#гермес) | юный бог-вестник | A — бог | **silver-and-charcoal tabby** (контрастный, темнее Артемиды), **quicksilver/bright-mercury** глаза, короткие волнистые **платиново-серебряные** волосы, крылатый **petasos** + крылатые сандалии (**talaria**), золотой **кадуцей** с двумя серебряными змеями | ✅ Цирцея и Одиссей |
| 7 | [Цирцея](#цирцея) | волшебница-дочь Гелиоса | A — богиня-волшебница | **emerald-and-bronze tortoiseshell** (мшистые + медные пятна), **warm sun-gold slit-pupil** глаза (наследие Гелиоса), длинные медно-рыжие волосы с травами + амулетами, **dark-moss-green** хитон с золотыми солнечными дисками по подолу, оливковый жезл со змеёй, pale-violet + emerald magic mist | ✅ Цирцея и Одиссей |
| 8 | [Афина](#афина) | взрослая богиня мудрости и войны | A — богиня | silver-grey-and-snow-white **tabby**, **storm-grey** глаза, бронзово-золотой коринфский шлем с белым гребнем, бронзовое копьё, круглый щит-эгида, сова на плече | ✅ Персей и Медуза, ✅ Медуза Горгона |
| 9 | [Посейдон](#посейдон) | владыка морей | A — бог-царь | deep-teal-and-storm-blue-grey, **turquoise-aqua** глаза, борода-грива из морской пены, коралловая корона с жемчугом, золотой трезубец | ✅ Медуза Горгона |

### Смертные / нимфы / заколдованные

| # | Персонаж | Форма / возраст | Класс | Палитра / маркер | Мифы |
|---|---|---|---|---|---|
| 5 | [Каллисто-нимфа](#каллисто-нимфа-maiden) | юная охотница (свита Артемиды) | A — нимфа | pale-cream + honey calico, honey-amber eyes, **dusty-rose** хитон, **silver crescent brooch**, длинная коса | ✅ Каллисто и Аркас (сц. 02, 03, 07, 08, 09, 10) |
| 6 | [Каллисто-изгнанница](#каллисто-изгнанница-pregnant-exiled) | изгнанная, беременная | A — нимфа (без атрибутов Артемиды) | та же, **БЕЗ броши, БЕЗ лука**, рваный хитон, свободные спутанные волосы, **округлый живот** | ✅ Каллисто и Аркас (сц. 11, 12) |
| 7 | [Каллисто-медведица](#каллисто-медведица-mother-bear--класс-c) | проклята Герой в медведицу | C — заколдованный зверь (4 лапы) | shaggy brown she-bear, **honey-amber eyes (preserved!)**, серебряная метка-полумесяц на лбу, pale-violet curse-mist | ✅ Каллисто и Аркас (сц. 13, 16, 17, 18) |
| 8 | [Аркас-младенец](#аркас-младенец-baby) | новорождённый | A — котёнок-смертный | tiny pale-cream-and-honey calico kitten, **honey-amber глаза (полузакрытые)**, swaddled in cream linen | ✅ Каллисто и Аркас (сц. 11) |
| 9 | [Аркас-мальчик](#аркас-мальчик-child-4-5-лет) | ~4-5 лет, у пастухов | A — котёнок-смертный | small pale-cream-and-honey calico, **honey-amber глаза (наивные)**, shepherd's tunic, wooden crook | ✅ Каллисто и Аркас (сц. 14) |
| 10 | [Аркас-охотник](#аркас-охотник-hunter-15-лет) | 15 лет, лучший охотник округи | A — смертный | athletic pale-cream-and-honey calico, **honey-amber глаза (жёсткий взгляд)**, olive-green chiton, **короткие волосы** (НЕ как коса матери), spear + bow | ✅ Каллисто и Аркас (сц. 01, 15, 16, 18, 19) |
| 11 | [Пастух (приёмный отец Аркаса)](#пастух-приёмный-отец-аркаса) | пожилой | A — смертный | elderly grey-and-brown tabby, shepherd's cloak, gnarled crook | ✅ Каллисто и Аркас (сц. 14) |
| 12 | [Одиссей](#одиссей) | царь Итаки, воин в расцвете сил | A — смертный (царь-воин) | lean broad-shouldered **russet-and-bronze tabby**, sharp clever **grey-green** глаза, густая каштаново-коричневая **короткая борода**, шрам через бровь, надсечка на одном ухе от старой битвы, бронзовый нагрудник + crimson cloak, **xiphos** sword | ✅ Одиссей и Пенелопа, ✅ Цирцея и Одиссей |
| 14 | [Медуза-дева](#медуза-дева-maiden) | прекрасная жрица Афины (до проклятия) | A — смертная жрица | soft **pale-gold-and-cream**, **jade-green** глаза, длинные золотые волосы до земли, белый жреческий пеплос с совами Афины | ✅ Медуза Горгона |
| 15 | [Медуза-горгона](#медуза-горгона-gorgon) | проклята Афиной в горгону | A — чудовище-с-головой (бипедальный кот) | **greenish-grey-and-bronze scaled**, **jade-green** петрифицирующие глаза, стилизованные змейки вместо волос, рваный bronze-and-green пеплос | ✅ Персей и Медуза, ✅ Медуза Горгона |
| 16 | [Персей](#персей) | юный герой-победитель горгоны | A — смертный герой | **sandy-gold-and-cream tabby**, **emerald-green** глаза, зеркальный бронзовый щит, серп-харпе, крылатые сандалии, шлем-невидимка | ✅ Персей и Медуза, ✅ Медуза Горгона (камео в финале) |

### Славянский пантеон (эксперимент за пределами Олимпа)

> С 2026-05-22 канал пробует тематические эксперименты за пределами греческой мифологии. Канон класса A (антропоморфные коты) сохраняется — славянские персонажи тоже коты, но с другим костюмом, другим окрасом, другими атрибутами. Если эксперимент приживётся, эта секция станет полноценной.

| # | Персонаж | Форма / возраст | Класс | Палитра / маркер | Мифы |
|---|---|---|---|---|---|
| 13 | [Баба-Яга](#баба-яга) | древняя пограничная ведьма | A — ведьма-кошка | hunched **smoke-grey-and-white tabby** с проседью, **luminous yellow-green slit-pupil** глаза, **одна костяная гуманоидная нога** (главный маркер!), single yellow fang, dark Slavic sarafan moss-green + iron-rust с red embroidery of suns/roosters, burlap shawl, headscarf, klyuka + mortar pestle, pale-violet + sickly-green curse mist | ✅ Баба-Яга |

**Связи поколений:** одинаковые **honey-amber глаза** — наследственный маркер Каллисто (все 3 формы) → Аркас (все 3 формы). Это единственное, что зритель видит сквозь все превращения и взросление.

---

# Артемида

*(богиня охоты и луны, дочь Зевса и Лето, сестра-близнец Аполлона)*

**Появляется в:**
- ✅ Орион и Артемида (`content/архив/Орион и Артемида/prompts/images.md` — **источник эталона**)
- ✅ Каллисто и Аркас (сцены 03 — благословение клятвы, 10 — изгнание; в сценах 06-07 присутствует подделка-Зевс, см. отдельную карточку)
- 🔜 будущие мифы про охоту, луну, нимф

**Визуальный образ:** грациозная стройная серебристо-серо-белая **табби** кошка-богиня. Светящиеся большие бледно-серебристо-голубые глаза, отражающие лунный свет, спокойное холодно-сосредоточенное выражение. Длинные волнистые **серебристо-голубые волосы**, спадающие по спине. Тонкая серебряная диадема с полумесяцем на лбу. Короткий до колен струящийся бледно-серебряно-белый хитон с вышивкой полумесяцев и лавра. Серебряный пояс с пряжкой-полумесяцем. Серебряно-серые кожаные охотничьи сандалии со шнуровкой до голеней. Высокий орнаментированный серебряный длинный лук с гравированными полумесяцами. Тонкий серебряный колчан со серебряными стрелами. Холодное серебряно-голубое божественное свечение. Шерсть мерцает звёздным светом.

**Английская карточка (images.md):**

```
Artemis the goddess of the hunt and moon, a graceful slender silver-grey-and-white tabby anthropomorphic cat character with luminous large pale-silver-blue eyes that reflect moonlight and a calm composed cool expression, two erect silver-grey tabby cat ears, a small silver cat muzzle, a long fluffy silver-grey tabby cat tail, bipedal standing upright on two legs with humanoid body proportions body upright not on four legs, wearing a short knee-length flowing pale-silver-and-white Greek hunting chiton with delicate silver embroidery of crescent moons and laurel leaves a wide silver belt with a small crescent moon clasp silver-grey leather hunting sandals laced up her shins, her long wavy silver-and-pale-blue hair flowing down her back held back by a thin silver crescent moon diadem resting on her forehead, carrying a tall ornate silver longbow with engraved crescent moons and a slim silver quiver of silver arrows slung over her back, faint cool silver-blue divine glow surrounding her body, her silver-grey-and-white fur shimmering with starlight
```

**Descriptive (video.md):**

```
the silver-grey-and-white tabby goddess of the hunt and moon
```

Короче (в плотных промптах): `"the silver moon huntress cat"`.

**Атрибуты-маркеры:**
- ✅ Silver-grey-and-white **tabby** мех (не просто плоский silver-grey-and-white)
- ✅ Pale silver-blue глаза, отражающие лунный свет (НЕ янтарные, НЕ электрические)
- ✅ **Длинные волнистые серебристо-голубые волосы** до спины (НЕ короткие, ни в одной сцене не лысая под диадемой)
- ✅ Тонкая серебряная диадема с полумесяцем на лбу (НЕ корона)
- ✅ Высокий орнаментированный серебряный длинный лук с гравированными полумесяцами
- ✅ Серебряно-серые **сандалии** со шнуровкой (НЕ белые сапоги)
- ✅ Cool silver-blue divine glow + шерсть мерцает звёздным светом

**Эмоциональные состояния:**
- **Каллисто и Аркас, сцена 03 (клятва):** торжественная, благосклонная — рука над Каллисто в жесте благословения, лук в свободной руке
- **Каллисто и Аркас, сцена 10 (изгнание):** холодная ярость — pale silver-blue eyes blazing with cold fury, рука указывает прочь от свиты, лук держит диагонально через корпус
- **Орион и Артемида (полная палитра эмоций):** см. `content/архив/Орион и Артемида/prompts/images.md` — там есть варианты горя, гнева на брата, статуарной скорби, дарования бессмертия через звёзды

---

# Зевс (старший)

*(царь богов в зрелой/старой форме — с длинной белой бородой)*

**Появляется в:**
- ✅ Каллисто и Аркас (сцены 04 — наблюдает с Олимпа, 05 — блокирован клятвой-барьером, 20 — рука с неба, превращающая мать и сына в созвездия)
- 🔜 будущие мифы поздней эпохи правления

> **Возрастная форма.** Это Зевс уже после многих лет правления Олимпом. Для сериала «От Хаоса до Олимпа» (где Зевс молод: младенец → юноша → новый владыка после Титаномахии) используется ОТДЕЛЬНАЯ карточка в `content/От Хаоса до Олимпа/characters.md` → раздел «Зевс». Разница: молодой Зевс — ivory-and-pale-gold tabby, золотая грива, короткая золотая борода. Старший Зевс — белый мех, длинная белая борода. Один персонаж, две возрастные формы.

**Визуальный образ:** высокий пожилой белошёрстный кот. Длинная густая белая борода. Пронзительные электрически-синие глаза. Белый с золотом царский тогой с вышивкой золотых орлов. Тонкий лавровый венец из золота на голове. Длинный тёмно-пурпурный плащ. В руке — потрескивающая золотая молния. Бледно-золотое свечение вокруг.

**Английская карточка (images.md):**

```
Zeus the mighty king of the gods, a tall old white-furred anthropomorphic cat character with a long thick white beard and piercing electric-blue eyes, two perked silver-white cat ears, a thick white cat muzzle, a long white cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a flowing white-and-gold Greek royal toga with golden eagle embroidery and a wide gold belt, a small olive-leaf gold crown on his white head, a long deep-purple cloak draped from his shoulders, holding a crackling golden lightning bolt in his humanoid hand, faint pale-gold glow surrounding him
```

**Descriptive (video.md):**

```
the old white-furred thunder cat king with a long thick white beard and electric-blue eyes
```

**Атрибуты-маркеры:**
- ✅ Electric-blue глаза
- ✅ Длинная густая белая борода (отличие от молодого Зевса в «От Хаоса до Олимпа», у которого короткая золотая)
- ✅ Золотая молния
- ✅ Белый с золотом тога + тёмно-пурпурный плащ
- ✅ Лавровый венец из золота

---

# Зевс в облике Артемиды (Zeus-as-Artemis)

*(маскировка Зевса для подхода к Каллисто, поклявшейся не знать мужчин)*

**Появляется в:**
- ✅ Каллисто и Аркас (сцены 06 — превращение Зевса в Артемиду, 07 — фейк-Артемида подходит к Каллисто как «подруга»)

> ⚠️ **Визуально идентичен Артемиде.** Единственное отличие, видное зрителю (но НЕ Каллисто): едва заметный electric-gold glint в pale-silver-blue глазах + warm-gold tint ауры вместо cool silver.

**Английская карточка (images.md):**

```
Zeus disguised as Artemis — visually IDENTICAL to Artemis: a graceful slender silver-grey-and-white tabby anthropomorphic cat character with luminous large pale-silver-blue eyes and a calm composed cool expression two erect silver-grey tabby cat ears a small silver cat muzzle a long fluffy silver-grey tabby cat tail bipedal standing upright on two legs with humanoid body proportions wearing the same short knee-length flowing pale-silver-and-white Greek hunting chiton with delicate silver embroidery of crescent moons and laurel leaves a wide silver belt with a small crescent moon clasp silver-grey leather hunting sandals laced up the shins long wavy silver-and-pale-blue hair flowing down the back held by a thin silver crescent moon diadem a tall ornate silver longbow with engraved crescent moons and a slim silver quiver of silver arrows — НО с одной едва заметной нотой: в её pale-silver-blue eyes мерцает едва уловимая искра ELECTRIC-GOLD (тонкий золотой блик в глазах — единственный намёк, что это не Артемида), the faint cool silver-blue divine glow around her body slightly TINTED warm gold rather than cool silver, her silver-grey-and-white tabby fur shimmering with starlight that has a subtle gold cast
```

**Descriptive (video.md):**

```
the silver-grey-and-white tabby huntress-disguise cat character — visually identical to the moon goddess but with a faint electric-gold glint in the pale-silver-blue eyes and a warm gold-tinted aura instead of cool silver
```

**Главное в промпте:**
- В сцене превращения — диагональный переход Zeus→Artemis с golden-and-silver mist
- В сцене подхода — держать обе характеристики: визуально Артемида + electric-gold spark в глазах

---

# Гера

*(царица богов, жена Зевса — мстительная богиня брака)*

**Появляется в:**
- ✅ Каллисто и Аркас (сцена 12 — превращает Каллисто в медведицу из ревности)
- 🔜 «От Хаоса до Олимпа» ч. 3+ (см. отдельную карточку в `content/От Хаоса до Олимпа/characters.md` — там Гера-новорождённая, поглощённая Кроносом, и Гера-освобождённая царица; визуально это БОЛЕЕ МОЛОДАЯ форма, cream-white fur)
- 🔜 будущие одиночные мифы (Ио, Геракл, Семела)

> **Возрастная/палитровая консистентность.** В «Каллисто и Аркас» Гера показана **в зрелой мстительной форме** (deep-royal-blue + peacock-iridescent мех, эталон описан ниже). В «От Хаоса до Олимпа» она ещё **молода и более светлая** (cream-white fur с золотыми пятнами — палитра только что освобождённой из Кроноса олимпийки). Это сюжетно один персонаж — но **визуально разные формы по возрасту/злобе**. Для каждого нового мифа решать, в какой форме брать Геру: молодую невинную (сразу после Титаномахии) или зрелую мстительную (после длительного брака с Зевсом). Каллисто и Аркас — точно зрелая.

**Визуальный образ (зрелая мстительная форма):** царственная кошка-богиня с глубоким сине-павлиньим мехом (богатый navy-мех с переливающимися зелёно-фиолетовыми бликами вдоль спины и хвоста). Пронзительные ревнивые изумрудно-зелёные глаза с острым кошачьим вертикальным зрачком. Длинные тёмно-синие волосы каскадом по спине. Высокая золотая корона в форме развёрнутого веера павлиньих перьев. Сине-золотое царское платье с золотой вышивкой павлинов и гранатов. Золотой посох с павлиньим веером. Хвост украшен узором «глаз павлиньего пера». Вокруг ног — peacock-feather mist.

**Английская карточка (images.md):**

```
Hera the queen of the gods, a regal majestic anthropomorphic cat goddess with deep-royal-blue and iridescent peacock-coloured fur (rich navy fur with shimmering green-purple highlights along her back and tail), piercing jealous emerald-green eyes with sharp cat slit pupils, two tall perked dark-blue cat ears, a small dark-blue cat muzzle, a long graceful navy-blue cat tail tipped with peacock-feather eye-patterns, bipedal standing upright on two legs with humanoid body proportions, wearing a flowing deep-royal-blue and gold Greek royal robe with elaborate gold embroidery of peacocks and pomegranates along the hem and sleeves, a wide gold belt with a peacock-eye-gem clasp, golden sandals, a tall ornate gold crown shaped like peacock feathers fanning above her head, long flowing dark-blue hair cascading down her back, holding a long golden staff topped with a peacock-feather fan in her humanoid hand, a swirl of peacock-feather mist around her feet
```

**Descriptive (video.md):**

```
the deep-royal-blue and peacock-feathered cat queen goddess with emerald-green slit-pupil eyes and a tall peacock-feather gold crown
```

**Атрибуты-маркеры:**
- ✅ Emerald-green slit-pupil глаза (ревнивые, холодные)
- ✅ Navy-blue + peacock-iridescent мех
- ✅ Хвост с узором «глаз павлиньего пера»
- ✅ Золотой посох с павлиньим веером
- ✅ Peacock-feather mist вокруг ног

---

# Аполлон

*(бог солнца, музыки, пророчества и стрельбы из лука, сын Зевса и Лето, брат-близнец Артемиды)*

**Появляется в:**
- ✅ Орион и Артемида (`content/архив/Орион и Артемида/prompts/images.md` — **источник эталона**; сцены 09 — наблюдает с террасы храма, 10 — в ярости на сестру, 12 — провоцирует выстрел, 15 — у моря, 23 — финал среди звёзд)
- ✅ Аполлон и Кассандра (сцены 03 — спускается с солнечной колесницы, влюблён, 04 — дарит дар пророчества, 08 — получает отказ, 09 — понимает что дар не отозвать, 10 — насылает проклятие на Кассандру)
- 🔜 будущие мифы про музыку, пророчество, Дафну, Гиацинта, Асклепия, эпидемии

**Визуальный образ:** грациозный молодой золотисто-кремовый **табби** кот-бог. Яркие золотисто-янтарные глаза, рафинированные красивые черты лица. Короткие вьющиеся медово-золотые волосы, удерживаемые тонким лавровым венцом из полированного золота. Струящийся бело-золотой греческий тунику с богатой золотой вышивкой солнечных лучей и лавровых листьев. Широкий золотой пояс с пряжкой-солнечным диском. Золотые кожаные сандалии со шнуровкой до голеней. Высокий орнаментированный золотой длинный лук с гравированными солнечными лучами и золотой колчан с золотыми стрелами за спиной. Мягкое тёплое золотое божественное свечение вокруг тела. Шерсть мерцает солнечным светом.

**Английская карточка (images.md):**

```
Apollo the sun god twin brother of Artemis, a graceful young gold-and-cream tabby anthropomorphic cat character with bright golden-amber eyes and refined handsome features, two perked gold tabby cat ears, a small golden cat muzzle, a long fluffy gold-and-cream cat tail, bipedal standing upright on two legs with humanoid body proportions body upright not on four legs, wearing a flowing white-and-gold Greek tunic with rich gold embroidery of sunbursts and laurel leaves a wide gold belt with a sun-disc clasp golden leather sandals laced up his shins, his short curling honey-gold hair held back by a thin laurel crown of polished gold leaves, carrying a tall ornate golden longbow with engraved sunbursts and a gold quiver of golden arrows slung over his back, faint warm golden divine glow surrounding him, his gold-and-cream fur shimmering with sunlight
```

**Descriptive (video.md):**

```
the gold-and-cream tabby sun god twin brother
```

Короче (в плотных промптах): `"the gold sun cat archer"`.

**Атрибуты-маркеры:**
- ✅ Gold-and-cream **tabby** мех (не просто плоский pale-gold-and-cream — именно tabby с полосами)
- ✅ Bright **golden-amber** глаза (НЕ sun-gold светящиеся изнутри, НЕ зелёные — тёплый янтарь с золотом)
- ✅ **Короткие вьющиеся honey-gold волосы** под лавровым венцом (НЕ короткие прямые tousled gold-blond, НЕ длинные)
- ✅ Тонкий лавровый венец из полированного золота на лбу (НЕ корона, НЕ диадема)
- ✅ Бело-золотая греческая туника с золотой вышивкой солнечных лучей и лавровых листьев
- ✅ Высокий золотой длинный лук с гравированными солнечными лучами + золотой колчан с золотыми стрелами
- ✅ Golden leather sandals со шнуровкой до **голеней** (не до икр)
- ✅ Warm golden divine glow + шерсть мерцает солнечным светом
- ❌ **НЕ лира.** Аполлон — бог музыки тоже, но в эталоне канала лиры нет, чтобы не ломать узнавание силуэта. Если по сюжету будущего мифа понадобится лира — добавить в этом же разделе подсекцию «Аполлон-музыкант» с лирой, не менять основную карточку.

**Эмоциональные состояния:**
- **Орион и Артемида, сцены 09-15:** subtly cold and calculating — холодный наблюдающий брат, ревнующий сестру к смертному. Лук перекинут через плечо, статуарная стойка часового. Финальная сцена (23) — спокойный силуэт уходящий на закате, тёмное золото в ауре.
- **Аполлон и Кассандра, сцены 03-04:** влюблённый бог — глаза смотрят с reverent stillness, NOT predatory, тёплое золото в ауре, sun-sparks дрейфуют в воздухе вокруг.
- **Аполлон и Кассандра, сцены 09-10 (Apollo-wronged):** лицо HARDENED INTO A COLD GOD'S WRATH — глаза narrowed, glowing с darker amber edge, brow furrowed, muzzle pressed into a thin line. Soft pale-gold halo визуально TINGED WITH BRONZE-AMBER fading toward a darker tone (no longer warm but bitter), faint amber sparks crackling along его humanoid fingers. То же тело, но визуально отравленное гневом.

**Связь с Артемидой:** близнецы по сюжету, но визуально РАЗНЫЕ — Артемида cool silver-blue, Аполлон warm gold-and-cream. Лейтмотив пары: серебро+луна vs золото+солнце. При совместном кадре композиция явно цветоразделена (Орион и Артемида сцены 09, 12, 23).

---

# Каллисто

*(нимфа из свиты Артемиды → изгнанница, мать Аркаса → медведица по проклятью Геры)*

**Появляется в:**
- ✅ Каллисто и Аркас (три формы — см. подразделы)

**Связывающий маркер:** large warm **honey-amber eyes** — единственное, что сохраняется во всех трёх формах. В медведице это узнаваемо человеческие глаза на медвежьей морде. Этот же цвет наследует её сын Аркас.

---

## Каллисто-нимфа (maiden)

*Каллисто и Аркас, сцены 02, 03, 07, 08, 09, 10*

**Визуальный образ:** юная охотница. Стройная, бледно-кремово-медовая калико-кошка. Большие тёплые янтарные глаза. Охотничий хитон пыльно-розового цвета с кремовыми вставками, зелёная оливковая вышивка по подолу. Маленькая серебряная брошь в форме полумесяца — знак принадлежности к свите Артемиды. Коса из медово-кремовых волос. Короткий лук за спиной, колчан.

**Английская карточка (images.md):**

```
Callisto the young huntress nymph in her maiden form, a graceful slender pale-cream-and-honey calico anthropomorphic cat character with large warm honey-amber eyes and gentle but determined hunter features, two small perked pale-cream cat ears, a small pink-and-cream cat muzzle, a long fluffy pale-cream cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a short hunter's chiton in dusty-rose and cream with green olive-leaf embroidery at the hem, a dark-brown leather strap belt, a small leather pauldron over one shoulder, soft brown leather sandals laced up her calves, a small silver crescent-moon brooch pinned at her shoulder (the mark of Artemis's followers), long wavy honey-cream hair tied back in a thick braid with small silver clasps, a slim short hunting bow strapped across her back beside a quiver of arrows with pale-cream fletching
```

**Descriptive (video.md):**

```
the young pale-cream-and-honey calico huntress-maiden cat character with warm honey-amber eyes
```

**Атрибуты-маркеры:**
- ✅ Серебряная брошь-полумесяц на плече
- ✅ Короткий охотничий лук + колчан
- ✅ Медово-кремовая коса с серебряными заколками
- ✅ Пыльно-розовый хитон с оливковой вышивкой

---

## Каллисто-изгнанница (pregnant-exiled)

*Каллисто и Аркас, сцены 11, 12*

**Визуальный образ:** та же кошка, но измученная изгнанием. Беременный живот. Хитон истрёпан и порван, вышивка поблёкла. Броши НЕТ (Артемида забрала при изгнании). Лука и колчана НЕТ. Волосы распущены и спутаны. Босые ноги.

**Английская карточка (images.md):**

```
Callisto in her exiled pregnant form, the same pale-cream-and-honey calico anthropomorphic cat character with large warm honey-amber eyes now full of quiet weariness and lonely resolve, two perked pale-cream cat ears, a small pink-and-cream cat muzzle, a long pale-cream cat tail, bipedal standing or kneeling upright on two legs with humanoid body proportions, her belly noticeably round with child, wearing the same dusty-rose-and-cream hunter's chiton (now travel-worn and torn at the hem, the green olive-leaf embroidery faded, the leather pauldron removed), her hunting bow and silver crescent-moon brooch GONE (Artemis took them when banishing her), her honey-cream hair loose and tangled around her shoulders without the braid, bare feet, faint dust on her fur
```

**Descriptive (video.md):**

```
the exiled pale-cream-and-honey calico pregnant cat character with warm honey-amber eyes
```

**Ключевые отличия от maiden-формы:**
- ❌ Броши НЕТ
- ❌ Лука и колчана НЕТ
- ❌ Косы НЕТ (волосы свободные, спутанные)
- ✅ Живот округлён
- ✅ Хитон рваный, поблёкший

---

## Каллисто-медведица (mother-bear) — класс C

*Каллисто и Аркас, сцены 13, 16, 17, 18*

> ⚠️ **Класс C — заколдованный зверь.** После проклятья Геры Каллисто — настоящая четырёхногая медведица, НЕ антропоморфная кошка. Ходит на четырёх лапах. Но это НЕ реальный дикий медведь — это заколдованная нимфа внутри медвежьего тела. Её душа читается через глаза.

**Визуальный образ:** огромная бурая медведица с более тёмными полосами вдоль спины. На морде — те самые **большие тёплые янтарные глаза** из её нимфской формы, полные человеческой скорби и материнского узнавания (НЕ звериной ярости). На лбу едва заметная метка серебряного полумесяца — угасающий след прежней жизни. Бледно-фиолетовый туман проклятья вокруг шерсти.

**Английская карточка (images.md):**

```
Callisto transformed by Hera's curse into a great brown she-bear — a massive shaggy brown bear with darker brown stripes along her back, the same LARGE WARM HONEY-AMBER EYES from her maiden form preserved as the ONLY sign of her humanoid soul (these eyes are full of human grief and motherly recognition, NOT animalistic rage), four powerful bear paws with sharp claws, a short shaggy bear tail, walking on all fours or rearing up on her hind legs with bear-like proportions (she has LOST her bipedal humanoid form to the curse, but is NOT a real wild bear and NOT a humanoid bear — she is a divine transformation), a tiny faint silver crescent-moon mark still visible on her shaggy forehead as a fading remnant of her former bond to Artemis, faint pale-violet mist whispering around her fur from the curse
```

**Descriptive (video.md):**

```
the great shaggy brown she-bear with preserved warm honey-amber eyes and a faint silver crescent-moon mark on her forehead
```

**Критично:**
- ✅ Янтарные honey-amber глаза — человеческие по выражению, полные скорби
- ✅ Серебряная метка полумесяца на лбу (едва видна)
- ✅ Бледно-фиолетовый туман проклятья
- ❌ НЕ кот на четвереньках (негатив `NO real four-legged cats` остаётся — она медведь)
- ❌ НЕ гуманоид-медведь (она потеряла бипедальную форму)

---

# Аркас

*(сын Каллисто и Зевса — смертный охотник, в финале становится созвездием Малой Медведицы)*

**Появляется в:**
- ✅ Каллисто и Аркас (три формы — см. подразделы)

**Связывающий маркер:** те же **honey-amber глаза** что у матери — генетический маркер. В сцене 01 это визуально объединяет охотника и медведицу через глаза.

---

## Аркас-младенец (baby)

*Каллисто и Аркас, сцена 11 (рождение)*

**Английская карточка (images.md):**

```
Arcas as a newborn baby — a tiny pale-cream-and-honey calico anthropomorphic kitten with the same warm honey-amber eyes as his mother Callisto (eyes closed or half-open in a baby's sleepy gaze), two small perked pale-cream cat ears, a tiny pink-and-cream cat muzzle, a small fluffy pale-cream cat tail, swaddled in a simple white-and-cream linen wrap with green olive-leaf embroidery (Callisto's torn chiton repurposed as the only blanket she had), tiny humanoid baby hands peeking out from the wrap
```

**Descriptive (video.md):**

```
the tiny pale-cream-and-honey calico newborn kitten swaddled in cream linen
```

---

## Аркас-мальчик (child ~4-5 лет)

*Каллисто и Аркас, сцена 14 (растёт у пастухов)*

**Английская карточка (images.md):**

```
young Arcas as a small kitten boy around 4-5 years old, a small pale-cream-and-honey calico anthropomorphic cat character with warm honey-amber eyes (like his mother) full of innocent unknowing curiosity, two perked pale-cream cat ears, a small pink-and-cream cat muzzle, a small pale-cream cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a simple short brown-and-tan shepherd's tunic with a rope belt and bare humanoid feet, short tousled honey-cream hair, holding a small wooden shepherd's crook
```

**Descriptive (video.md):**

```
the small pale-cream-and-honey calico kitten boy in a shepherd's tunic
```

---

## Аркас-охотник (hunter, 15 лет)

*Каллисто и Аркас, сцены 01, 15, 16, 18, 19*

**Визуальный образ:** подросший сын. Спортивный, стройный. Тот же pale-cream-and-honey калико-кот, те же янтарные глаза — но взгляд охотника, жёсткий и целеустремлённый. Заметно крупнее и мужественнее матери-нимфы. Оливково-зелёный охотничий хитон, копьё + лук.

> ⚠️ Волосы у Аркаса КОРОТКИЕ (стрижка для охоты) — в отличие от материнской длинной косы. Это важный маркер отличия в кадре при одновременном присутствии.

**Английская карточка (images.md):**

```
Arcas now grown into a young hunter at fifteen years old, an athletic lean pale-cream-and-honey calico anthropomorphic cat character with the same warm honey-amber eyes as his mother Callisto but with a hard determined hunter's gaze (NOT yet aware that his mother is the bear he hunts), two perked pale-cream cat ears, a small pink-and-cream cat muzzle, a long fluffy pale-cream cat tail, bipedal standing upright on two legs with humanoid body proportions visibly stronger taller and more masculine than his mother's nymph form, wearing a short hunter's chiton in earthy olive-green and tan with brown leather straps across the chest, a wide dark-brown leather belt with a small hunting knife, sturdy brown leather hunter's boots laced high up his calves, a heavy olive-green hunter's cloak with a hood pulled back, short tousled honey-cream hair cropped short for hunting (visibly different from his mother's long braid), carrying a tall wooden hunting spear with a bronze leaf-shaped head and a short hunting bow with a quiver of arrows strapped across his back
```

**Descriptive (video.md):**

```
the young athletic pale-cream-and-honey calico hunter cat character with warm honey-amber eyes
```

**Ключевые отличия от Каллисто-нимфы при совместных сценах:**
- Аркас — olive-green хитон vs Каллисто — dusty-rose хитон
- Аркас — short tousled hair vs Каллисто — long honey-cream braid
- Аркас — tall wooden hunting spear vs Каллисто — slim short bow
- Аркас — visibly stronger and more masculine

---

# Пастух (приёмный отец Аркаса)

*Каллисто и Аркас, сцена 14*

**Английская карточка (images.md):**

```
an elderly weathered grey-and-brown tabby anthropomorphic cat shepherd, two perked grey cat ears, a soft grey muzzle, a long grey cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a worn olive-brown shepherd's cloak over a faded tan tunic, a wide leather belt, rough leather sandals, short grey hair and a short grey beard, carrying a tall gnarled wooden shepherd's crook in his humanoid hand, a small woven satchel slung across his shoulder
```

**Descriptive (video.md):**

```
an elderly weathered grey-and-brown tabby cat shepherd with a short grey beard and a wooden crook
```

> **Заглушка для повторного использования:** если в будущем мифе появится «пастух / старик-крестьянин / приёмный отец / пасущий стада смертный», можно взять эту карточку как стартовую и подкрутить детали (цвет меха, выражение лица). Это общеканальный «крестьянин-архетип».

---

# Гермес

*(юный бог-вестник, проводник душ в Аид, покровитель путников, торговцев и хитрецов)*

**Появляется в:**
- ✅ Цирцея и Одиссей (сцена 10 — перехватывает Одиссея в лесу и даёт траву моли)
- 🔜 будущие мифы: «Гермес и младенец Дионис», «Геракл в Аиде», любые сцены «боги отправляют посланника», проводник Психеи, проводник Орфея на земле

**Визуальный образ:** юный стройный быстрый кот-вестник. Серебристо-угольный табби (тёмные графитовые полосы по серебристо-серому меху, контрастнее чем у Артемиды). Большие живые **ртутно-серебряные глаза** — двигаются как капля жидкой ртути, никогда не статичны. Короткие волнистые платиново-серебряные волосы торчком, словно от ветра. Маленький крылатый дорожный шлем-петас (petasos) — низкая серая фетровая шапка с парой белых перьевых крыльев по бокам. Короткий белоснежный греческий хитон, чуть мятый «на ходу», с одной открытой плечом. Тёмно-серый шерстяной дорожный плащ (chlamys) через одно плечо, скреплённый маленькой серебряной фибулой. Крылатые сандалии (talaria) с парой белых перьевых крылышек на лодыжках. В правой humanoid-руке держит золотой **кадуцей** — жезл с двумя обвившимися серебряными змеями и парой золотых крыльев на верхушке. Хитрая полуулыбка в уголке морды. Поза всегда динамичная — будто только что приземлился или вот-вот сорвётся.

**Английская карточка (images.md):**

```
Hermes the youthful god of messengers and travelers, a lean swift silver-and-charcoal tabby anthropomorphic cat character with luminous large quicksilver-bright-mercury eyes always alive with motion and a sly half-smile at the corner of his cat muzzle, two perked silver-and-charcoal tabby cat ears, a small silver cat muzzle, a long fluffy silver-and-charcoal tabby cat tail held with playful tension, bipedal standing upright on two legs with humanoid body proportions body upright not on four legs in a dynamic mid-stride or just-landed messenger pose, wearing a short crisp white Greek chiton draped over one shoulder with a thin bronze belt, a dark-grey wool traveler's chlamys cloak draped over his other shoulder fastened with a small silver fibula, short windswept platinum-silver curls held under a low silver-grey winged petasos hat with a pair of small white feathered wings sprouting from its sides, winged talaria sandals with pairs of small white feathered wings at his ankles, holding a tall golden caduceus staff topped with two intertwined silver serpents and a pair of small golden wings in his humanoid hand, faint cool quicksilver-silver divine glow surrounding him, his silver-and-charcoal tabby fur catching small wind-blown specks of stardust
```

**Descriptive (video.md):**

```
the silver-and-charcoal tabby messenger cat god with quicksilver eyes and a winged petasos hat
```

Короче (в плотных промптах): `"the silver winged-hat messenger cat"`.

**Атрибуты-маркеры:**
- ✅ Silver-and-charcoal **tabby** (более тёмный/контрастный, чем у Артемиды; полосы графитовые)
- ✅ **Quicksilver/bright-mercury** глаза (НЕ pale-silver-blue как у Артемиды — у Гермеса они «живые», цвета жидкого металла)
- ✅ Короткие платиново-серебряные волосы (НЕ длинные — он подросток-вестник, всегда «на ходу»)
- ✅ Крылатый petasos — низкая серая шапка с белыми перьевыми крылышками по бокам (НЕ высокий шлем, НЕ диадема)
- ✅ Крылатые сандалии talaria с белыми перьями на лодыжках
- ✅ Золотой кадуцей с двумя серебряными змеями и парой золотых крыльев на верхушке (узнаваемый артефакт — НЕ путать с жезлом Цирцеи или посохом Геры)
- ✅ Хитрая полуулыбка, динамичная поза (НЕ статичен, в каждом кадре в движении или его остатке)

**Различение с Артемидой при совместном кадре (теоретически могут встретиться):**
- Артемида: silver-grey-and-white tabby (более светлая) + pale-silver-blue eyes + длинные волосы + диадема-полумесяц + серебряный лук + cool silver-blue glow
- Гермес: silver-and-charcoal tabby (более тёмный) + quicksilver-mercury eyes + короткие волосы + winged petasos + золотой кадуцей + cool quicksilver-silver glow

---

# Цирцея

*(дочь титана Гелиоса и океаниды Персеиды, сослана богами на остров Ээя, могущественная волшебница, мастерица трав и превращений; сестра Пасифаи и Ээта)*

**Появляется в:**
- ✅ Цирцея и Одиссей (все сцены — главный персонаж)
- 🔜 будущие мифы: «Главк и Скилла» (Цирцея ревнует и превращает Скиллу в чудовище), «Медея у Цирцеи» (племянница приплыла за очищением), возможно эпизодически в «Аргонавтах»

**Связывающий маркер:** **warm sun-gold slit-pupil cat eyes** — это её ДНК-маркер от отца **Гелиоса**. Тот же тон золота, что у Аполлона на ауре и шерсти, но именно в глазах. Это мостик к будущим мифам про её сестёр-волшебниц (**Пасифая** — мать Минотавра, **Медея** — племянница) и её брата (**Ээт** — хранитель золотого руна). У всех потомков Гелиоса по канону канала должна быть нота **sun-gold** в глазах или мехе.

**Визуальный образ:** царственная стройная кошка-волшебница в расцвете сил, дочь Солнца, сосланная на дикий остров. Глубокий черепаховый окрас — мшисто-изумрудные пятна перетекают в бронзово-медные по корпусу и хвосту (редкий «ведьмин» окрас, отличающий её от любого другого кота канала). Большие **тёплые sun-gold глаза с вертикальными кошачьими зрачками** — единственный наследный знак отца-Гелиоса, который она не может скрыть. Спокойная высокомерная мимика с лёгкой ленцой — она знает, что в её доме всё под её контролем. Длинные густые медно-рыжие волосы каскадом по спине, заплетённые с маленькими сухими веточками трав, крошечными костяными амулетами и **одним маленьким золотым диском-солнцем** (родовой знак Гелиоса, который она прячет среди ведьминских талисманов). Длинный струящийся греческий хитон цвета тёмного мха с золотой вышивкой солнечных дисков по подолу (родовая вышивка, выдаёт её происхождение). Широкий бронзовый пояс с подвешенными маленькими стеклянными пузырьками-флаконами зелий, которые тихо позвякивают при движении. Бронзовые сандалии. В правой humanoid-руке держит оливковый деревянный жезл, верхушка которого вырезана в виде свернувшейся змеи (он же — палочка для зелий и для превращений). Вокруг рук и ног — pale-violet и emerald magic mist; в этом тумане иногда плавают полупрозрачные силуэты животных, в которых она превращает гостей (свинья, олень, лев, волк) — её фирменный визуальный шлейф.

**Английская карточка (images.md):**

```
Circe the witch-goddess daughter of the sun titan Helios, a regal slender enchantress anthropomorphic cat character with deep emerald-green-and-bronze tortoiseshell fur (mossy emerald patches melting into bronze-copper patches along her body and tail in a rare witch-cat coat), luminous large warm sun-gold eyes with sharp cat slit pupils (the only visible inheritance of her sun-titan father), composed haughty serene features with a faint knowing half-smile at the corner of her cat muzzle, two perked emerald-and-bronze tortoiseshell cat ears, a small dark-pink cat muzzle, a long graceful emerald-and-bronze tortoiseshell cat tail tipped with bronze, bipedal standing upright on two legs with humanoid body proportions body upright not on four legs, wearing a long flowing dark-moss-green Greek chiton with rich gold embroidery of sun-discs and laurel along the hem and sleeves (the hidden sun-disc heraldry of her father Helios), a wide polished bronze belt hung with small clinking glass potion vials of emerald and violet liquid, bronze sandals laced up her calves, her long thick copper-red hair flowing down her back braided with small dried sprigs of herbs and tiny carved bone amulets and one small woven gold sun-disc charm half-hidden among the talismans, holding a tall olivewood witch's wand topped with a small carved coiled serpent in her humanoid hand, soft pale-violet and emerald magic mist swirling around her hands and feet with faint translucent silhouettes of swine and stags drifting in the mist (the trace of her transformative magic), faint warm gold-and-emerald divine glow surrounding her, her emerald-and-bronze tortoiseshell fur shimmering with a hint of inherited sunlight
```

**Descriptive (video.md):**

```
the emerald-and-bronze tortoiseshell witch-cat sun-daughter sorceress with sun-gold slit-pupil eyes
```

Короче (в плотных промптах): `"the emerald witch-cat sorceress"`.

**Атрибуты-маркеры:**
- ✅ Deep emerald-green-and-bronze **tortoiseshell** мех (мшистый изумруд + бронзовая медь — редкий «ведьмин» окрас, ни у кого больше на канале)
- ✅ Warm **sun-gold** глаза с **вертикальными кошачьими зрачками** (slit-pupil — отличает от Аполлона у которого тоже золото, но без вертикали; это её родовая черта от Гелиоса)
- ✅ Длинные густые **медно-рыжие** волосы, заплетённые с веточками трав + костяными амулетами + одним золотым диском-солнцем
- ✅ Dark-moss-green хитон с **золотой вышивкой солнечных дисков** по подолу (родовая вышивка Гелиоса — она не может полностью отречься)
- ✅ Широкий бронзовый пояс с **позвякивающими стеклянными пузырьками зелий** (визуальный аудио-маркер ведьмы)
- ✅ **Оливковый деревянный жезл с вырезанной змеёй** на верхушке (НЕ короткая палочка, НЕ скипетр — длинный witch's wand)
- ✅ **Pale-violet + emerald magic mist** вокруг рук и ног (фирменный шлейф) с **силуэтами свиньи/оленя/льва/волка** в тумане
- ✅ Slit-pupil + spokойное «всё под контролем» выражение (НЕ зловещая злодейка с оскалом — она просто знает, что вы ей не противник)

**Эмоциональные состояния:**
- **Цирцея и Одиссей, сцены 1, 7, 11:** smug satisfaction — лёгкая ухмылка, лениво держит жезл, sun-gold глаза прищурены
- **Цирцея и Одиссей, сцена 12 (зелье не сработало):** shocked widening — глаза распахиваются, жезл опускается, ухмылка исчезает
- **Цирцея и Одиссей, сцена 14 (на коленях):** soft pleading — sun-gold глаза смягчаются, копперные волосы падают вперёд, жезл выронен
- **Цирцея и Одиссей, сцены 16-17 (романтическая фаза):** warm affectionate calm — взгляд тёплый, magic mist спокойный, жезл отложен в сторону
- **Цирцея и Одиссей, сцена 19-20 (отпускает):** composed dignity — sun-gold глаза сухие, не плачет, осанка царственная, копперные волосы поднимает ветер

**Различение с Аполлоном (оба «золотые потомки Гелиоса по канону»):**
- Аполлон: gold-and-cream **tabby**, **round-pupil** golden-amber eyes, short curly honey-gold hair, laurel crown, golden longbow, warm gold glow, **бог Солнца молодой и яркий**
- Цирцея: emerald-and-bronze **tortoiseshell** (НЕ tabby), **slit-pupil** sun-gold eyes, long copper-red hair with herbs, olivewood wand, emerald+violet magic mist, **ведьма-сосланная скрытая дочь Солнца**
- Общий ДНК: тон золота в глазах. Зритель, увидевший Аполлона и Цирцею, должен почувствовать «у них одинаковое золото — родня».

---

# Одиссей

*(царь Итаки, хитроумный воин-герой, муж Пенелопы, отец Телемаха; персонаж Гомеровой Илиады и Одиссеи)*

**Появляется в:**
- ✅ Одиссей и Пенелопа (`content/архив/Одиссей и Пенелопа/prompts/images.md` — **источник эталона**; формы: воин-в-расцвете, нищий-под-маской)
- ✅ Цирцея и Одиссей (форма: воин-в-расцвете; сцены 8-20)
- 🔜 будущие мифы: «Полифем и Одиссей», «Сирены», «Сцилла и Харибда», «Одиссей в Аиде»

> **Эталон карточки — в `content/архив/Одиссей и Пенелопа/prompts/images.md`** (раздел «Odysseus warrior» и «Odysseus beggar»). Все будущие мифы про Одиссея берут оттуда дословно. Здесь дублируется только сводка-памятка и descriptive-версия.

**Визуальный образ (воин-в-расцвете):** стройный широкоплечий атлетический кот-воин в зрелой силе. Окрас russet-and-bronze tabby (медно-бронзовый табби с тёмными полосами вдоль спины). Острые умные **серо-зелёные** глаза цвета моря в шторм — узнаваемый маркер моряка-итакийца. Короткая густая каштаново-коричневая борода. Маленький **шрам через одну бровь** (старый, от вепря). Одно ухо с маленькой надсечкой от давней битвы. Короткие растрёпанные каштановые волосы. Короткий бронзово-кожаный греческий хитон через одно плечо. Полированный бронзовый нагрудник с тиснёным узором волны-и-оливы. Кожаные сандалии со шнуровкой до икр. Широкий кожаный пояс с бронзовой пряжкой. На бедре — ножны с бронзовым мечом-**xiphos**. Длинный тёмно-красный плащ, скреплённый бронзовой фибулой в форме оливкового листа. Поза всегда чуть с прищуром, ухмылкой в уголке морды — «хитрец, а не богатырь».

**Английская карточка (images.md) — копировать дословно из `content/архив/Одиссей и Пенелопа/prompts/images.md`:**

```
King Odysseus of Ithaca the cunning warrior hero in his prime, a lean broad-shouldered athletic russet-and-bronze tabby anthropomorphic cat character with sharp clever grey-green eyes and a thick well-groomed chestnut-brown beard and a small scar across one eyebrow, two perked tabby cat ears (one slightly notched from old battle), a strong tabby cat muzzle, a long graceful russet tabby cat tail, bipedal standing upright on two legs like a human with humanoid body proportions, short tousled chestnut hair, wearing a short bronze-and-leather Greek warrior chiton draped over one shoulder, a polished bronze breastplate with embossed wave-and-olive patterns, leather sandals laced up his calves, a wide leather belt with a bronze buckle, a sheathed bronze xiphos sword at his hip, a long crimson cloak fastened with a bronze brooch shaped like an olive leaf
```

**Descriptive (video.md):**

```
the russet-and-bronze tabby warrior king cat
```

Короче (в плотных промптах): `"the russet-bronze warrior king cat"`.

**Атрибуты-маркеры:**
- ✅ Russet-and-bronze **tabby** мех (медно-бронзовый с полосами)
- ✅ Sharp clever **grey-green** глаза цвета моря в шторм (НЕ янтарные, НЕ синие; маркер моряка-итакийца)
- ✅ Густая каштаново-коричневая **короткая борода** (отличие от безбородого молодого Аполлона и от длиннобородого старшего Зевса)
- ✅ **Шрам через бровь** (от вепря — мифологически важно, появится в будущих мифах)
- ✅ Одно ухо со **слегка надсеченной верхушкой** от старой битвы
- ✅ Короткие растрёпанные каштановые волосы (НЕ под шлемом обязательно — шлем опционален)
- ✅ Бронзовый нагрудник с тиснением волны-и-оливы + crimson cloak с фибулой-оливковым-листом
- ✅ **Xiphos sword** (короткий бронзовый прямой меч — НЕ длинный, НЕ кривой)

**Эмоциональные состояния (по мифам):**
- **Одиссей и Пенелопа:** воин-в-расцвете (прощание с Пенелопой) → нищий-под-маской (возвращение на Итаку) → воин-разоблачение (натягивает лук)
- **Цирцея и Одиссей:** определившийся-капитан (идёт спасать команду) → меч-у-горла (ведьма падает на колени) → задумчивый-любовник (год пира) → разбуженный-герой (вспоминает Итаку) → благодарный-уходящий (берёт карту в Аид)

---

# Баба-Яга

*(древняя ведьма-страж границы между миром живых и миром мёртвых; первый славянский персонаж канала)*

**Появляется в:**
- ✅ Баба-Яга (формат «Миф за минуту», портрет-Вариант C)
- 🔜 будущие славянские сценарии (Василиса Прекрасная, Гуси-лебеди, Финист Ясный Сокол), если эксперимент с темой приживётся

> **Эксперимент за пределами Олимпа.** Канал «Кисы Олимпа» с 2026-05-22 пробует не только греческие сюжеты. Канон класса A (антропоморфный бипедальный кот) сохраняется — Баба-Яга это кошка-ведьма, не реальная женщина и не реальная кошка. Но эстетика — славянская: сарафан вместо хитона, лапти вместо сандалий, изба на курьих ножках вместо греческого храма, deep moss-green + iron-rust + bone-white + sickly-green витчмист вместо средиземноморского cool-silver / warm-gold / royal-blue.

**Визуальный образ:** очень древняя сгорбленная кошка-ведьма. Облезлый дымчато-серый табби с белыми проплешинами по плечам и груди — мех потерял лоск, кое-где видны узлы и колтуны. Большие пронзительные жёлто-зелёные глаза с вертикальным кошачьим зрачком, светящиеся изнутри ведьминским светом. Длинная кривая морда с одним длинным жёлтым клыком, торчащим из угла рта. Рваные клочковатые серые уши торчат из-под платка. Глубокий горб — плечи подняты выше шеи. **Одна задняя нога — голая белая кость от колена и ниже, без меха, гладкая, как высохшая кость** (та самая «костяная нога», главный маркер). Другая нога — обычная гуманоидная кошачья в плетёном лапте. Длинные спутанные серебристо-седые волосы выбиваются из-под тёмного платка, заплетены с сухими листьями, крошечными косточками, паутиной. Многослойный тёмный сарафан в цветах глубокого мха и ржавого железа, с поблёкшей красной вышивкой солнц и петухов по подолу. Поверх — рваная шаль из мешковины. На поясе — кожаная сумка с травами. В левой руке — высокий узловатый посох-клюка из чёрного тёрна. В правой — тяжёлый деревянный пест от ступы. Вокруг костяной ноги клубится бледно-фиолетовый и болезненно-зелёный туман проклятья. По всему меху мерцает слабый ведьмин свет.

**Английская карточка (images.md):**

```
Baba Yaga the ancient witch crone of the Slavic forest guarding the border between the living world and the world of the dead, a hunched gaunt very old smoke-grey-and-white tabby anthropomorphic cat crone character with patchy graying fur and threadbare worn spots and small mats along her shoulders and chest, luminous large piercing yellow-green eyes with sharp cat slit pupils glowing from within with witchlight, a long crooked cat muzzle with a single long yellowed fang jutting from one corner of her mouth, two ragged tufted grey cat ears poking out from under her dark headscarf, a long thin sooty-grey cat tail, bipedal standing upright on two legs with humanoid body proportions body upright not on four legs but with a deeply hunched stooped back her shoulders raised higher than her neck, ONE LEG OF BARE WHITE BONE — a smooth fleshless humanoid bone leg from the knee down with no fur at all (the iconic костяная нога bone-leg marker — half her body already in the world of the dead) while her OTHER LEG is a normal furred humanoid cat leg wearing a worn woven leather bast shoe (lapot) tied with rope, wearing a layered dark Slavic sarafan dress in deep moss-green and iron-rust with faded red embroidery of suns and roosters along the hem and sleeves over an undershirt of coarse off-white linen, a tattered burlap shawl draped around her hunched shoulders, a dark forest-green headscarf knotted at the back with messy wisps of long tangled silver-grey hair braided with small dried leaves and tiny bird bones and cobwebs spilling out from underneath, a worn leather satchel of dried herbs at her belt, her left humanoid hand clutching a tall gnarled twisted blackthorn walking staff (klyuka) taller than herself, her right humanoid hand holding a heavy carved wooden mortar pestle, faint pale-violet and sickly-green curse mist swirling around her bone leg, her smoke-grey-and-white tabby fur shimmering with faint witchlight
```

**Descriptive (video.md):**

```
the hunched smoke-grey-and-white tabby witch crone cat with one bare white bone leg, glowing yellow-green slit-pupil eyes, a single long fang, and a tattered dark moss-green Slavic sarafan with red embroidery
```

Короче (в плотных промптах): `"the bone-legged forest witch cat crone"`.

**Атрибуты-маркеры:**
- ✅ **Smoke-grey-and-white tabby** мех с проплешинами и колтунами (старый, облезлый — НЕ ухоженный)
- ✅ **Luminous yellow-green slit-pupil** глаза, светящиеся изнутри (отличие от emerald-green Геры и sun-gold Цирцеи)
- ✅ **ОДНА КОСТЯНАЯ ГУМАНОИДНАЯ НОГА** — голая белая кость от колена и ниже, без меха, гладкая (КРИТИЧНО — главный визуальный маркер, без него Баба-Яга не Баба-Яга)
- ✅ Другая нога — обычная меховая в **лапте** (плетёная обувь из лыка, привязанная верёвками)
- ✅ Одиночный длинный жёлтый клык в углу рта
- ✅ Глубокий горб — плечи выше шеи
- ✅ Длинные спутанные серебристо-седые волосы, заплетённые с сухими листьями, костями, паутиной — выбиваются из-под платка
- ✅ Тёмный платок завязан назад (закрывает макушку, уши торчат)
- ✅ Сарафан **deep moss-green + iron-rust** с **поблёкшей красной вышивкой солнц и петухов** (русский фольклорный, НЕ греческий хитон)
- ✅ Burlap shawl поверх плеч
- ✅ Klyuka — высокий узловатый посох из чёрного тёрна
- ✅ Wooden mortar pestle — деревянный пест от ступы (отдельный артефакт, не путать с клюкой)
- ✅ Pale-violet + sickly-green curse mist вокруг костяной ноги
- ❌ **НЕ хихикающая мультяшная Хэллоуин-ведьма** в остроконечной шляпе — у неё платок, не шляпа
- ❌ **НЕ просто старушка** — обязательно костяная нога видна в каждом кадре где видны ноги
- ❌ **НЕ зловещая злодейка с оскалом** — она древняя пограничная сила, не просто злая; выражение скорее «всё знаю заранее» с тяжёлым взглядом

**Эмоциональные состояния:**
- **сцены описания (внутри избы, у печи, у забора, у ступы):** spooky but composed — стоит/сидит, smug knowing presence, ведьмин свет в глазах ровный
- **сцены «кто пришёл за огнём» / «кто пришёл с дурным умыслом»:** двойственность одним кадром невозможна → две отдельные сцены, в одной протягивает череп с огнём гостю (calm benediction), в другой — заталкивает фигуру в печь лопатой (cold judgement, безэмоционально)
- **сцены «три вопроса / три задачи»:** вглядывается с прищуром, slit-pupil сужены, klyuka вертикально перед собой
- **сцены «летает в ступе по ночам»:** stooped silhouette в ступе с метлой против луны, мех развевается на ветру, witchlight шлейф позади

**Атрибуты-объекты, появляющиеся отдельно от персонажа** (визуальные иконы мифа):

- **Изба на курьих ножках** — деревянная славянская изба с резными ставнями и петушком на коньке крыши, **стоит на двух гигантских жёлтых куриных ногах** (бипедальные птичьи лапы с чешуёй и когтями), забор из костей вокруг участка, чёрный лес позади, бледно-фиолетовая луна. В action-сценах изба ПОВОРАЧИВАЕТСЯ — куриные ноги шагают, изба разворачивается дверью к камере. Внутри — печь с открытой пастью, лавки, сундуки, пучки сушёных трав на потолке.
- **Ступа с метлой и пестом** — высокая деревянная ступа (как большой стакан из бревна, с пояском железных колец), внутри стоит Баба-Яга, в одной руке метла из берёзовых прутьев, в другой пест. В полёте оставляет след curse-mist.
- **Череп с горящими глазами** — реальный череп (может быть лошадиный с длинной мордой, может звериный) насаженный на деревянный кол. В пустых глазницах — два **ярко-оранжевых живых пламени** (НЕ свечи, не уголья, а самостоятельный огонь, похожий на жизнь). Передаваемый из лап в лапы артефакт.
- **Забор из костей** — частокол вокруг избы из вертикально вкопанных длинных белых костей (берцовые/бедренные), на верхушках насажены пустые черепа разных зверей, в которых тлеют те же оранжевые огни (но более слабые, чем в главном черепе). Ночью весь забор светится как ряд тыкв на Хэллоуин, но мрачнее и без триумфа.

> **Заглушка для будущих славянских мифов:** атрибуты-объекты выше (изба, ступа, череп, забор) переиспользуются в любом мифе, где появляется Яга. Если в будущем мифе изба/ступа меняется по сюжету (например, в Василисе изба заворачивается ИМЕННО когда сказана формула — это уже сюжетная сцена, не статичная икона), описание можно расширить локально в `images.md`, но базовая внешность остаётся.

---

# Афина

*(богиня мудрости, справедливой войны и ремёсел, дочь Зевса; покровительница храма, где служила Медуза)*

**Появляется в:**
- ✅ Персей и Медуза (`content/архив/Персей и Медуза/prompts/images.md` — **источник эталона**; сцены 08 — даёт зеркальный щит, 23 — принимает голову на эгиду)
- ✅ Медуза Горгона (сцены 04 — алтарь храма, клятва жрицы; 07 — возвращается и видит осквернение; 08 — ярость; 09 — бессильна против Посейдона; 10 — обрушивает гнев; 11 — превращение)
- 🔜 будущие мифы про мудрость, войну, ремёсла, Арахну, Геракла

> **Различение с Артемидой (обе серо-серебристые tabby-богини).** Артемида — silver-grey-and-white tabby, **pale-silver-blue** глаза, диадема-полумесяц, серебряный лук, cool silver-blue glow, охотничий хитон. Афина — silver-grey-and-snow-white tabby, **storm-grey** глаза (грозовые, не голубые), **бронзовый коринфский боевой шлем с белым гребнем**, **копьё + круглый щит-эгида**, **сова на плече**, silver-and-gold glow. Главные различители: шлем+копьё+сова у Афины vs диадема+лук у Артемиды.

**Визуальный образ:** высокая величественная серебристо-серо-снежно-белая табби-кошка-богиня с грозовыми серо-стальными глазами и благородными резкими чертами. Высокий бронзово-золотой коринфский боевой шлем с развевающимся белым конским гребнем, сдвинут на затылок. Длинные волнистые серебристо-кремовые волосы по спине. Снежно-бело-серебряный греческий пеплос с золотой вышивкой оливковых ветвей и сов по подолу. Широкий золотой пояс с пряжкой-совой. В правой руке — длинное бронзовое копьё, в левой — высокий круглый бронзовый щит (эгида). На плече — маленькая бело-серая сова. Серебряно-золотая божественная аура.

**Английская карточка (images.md) — копировать дословно из `content/архив/Персей и Медуза/prompts/images.md`:**

```
Athena the silver-grey-and-white wisdom cat goddess, a tall majestic silver-grey-and-snow-white tabby anthropomorphic cat character with piercing intelligent storm-grey eyes and noble sharp features two perked silver cat ears a small white-and-grey cat muzzle a long silver-grey tabby cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a flowing snow-white-and-silver Greek peplos with intricate gold embroidery of olive branches and small owl motifs along the hem, a wide gold belt with a small golden owl clasp, golden sandals, a tall ornate bronze-and-gold Corinthian war helm with a flowing white horsehair crest pushed back on her head, her long wavy silver-and-cream hair flowing down her back held by the helm, a long bronze spear in her humanoid right hand, a tall round bronze shield (her aegis) in her humanoid left hand, a small white-and-grey owl perched on her shoulder, a faint silver-and-gold divine aura surrounding her
```

**Descriptive (video.md):**

```
the silver-grey-and-white tabby wisdom cat goddess with a bronze Corinthian war helm with a white crest a bronze spear and a round bronze shield
```

Короче (в плотных промптах): `"the helmeted wisdom cat goddess with spear and shield"`.

**Атрибуты-маркеры:**
- ✅ Silver-grey-and-snow-white **tabby** мех
- ✅ **Storm-grey** грозовые глаза (НЕ pale-silver-blue как у Артемиды)
- ✅ Бронзово-золотой **коринфский шлем с белым конским гребнем**, сдвинут на затылок
- ✅ Длинные волнистые серебристо-кремовые волосы (видны из-под шлема)
- ✅ Бронзовое **копьё** + круглый бронзовый **щит-эгида**
- ✅ Маленькая бело-серая **сова** на плече
- ✅ Пеплос с золотой вышивкой олив и сов
- ✅ Silver-and-gold divine aura (НЕ cool silver-blue)
- 🔱 В «Персей и Медуза» сцена 23 — на эгиде появляется горгонеон (рельеф головы Медузы); в «Медуза Горгона» эгида ещё чистая, БЕЗ горгонеона (это предыстория)

**Эмоциональные состояния (Медуза Горгона):**
- **сцена 04 (клятва жрицы):** торжественная благосклонность — принимает клятву девы у алтаря, копьё опущено
- **сцена 07 (осквернённый храм):** шок и нарастающий гнев — глаза распахнуты, гребень будто встал дыбом
- **сцены 08–10 (ярость → бессилие → кара):** storm-grey eyes blazing с холодной яростью; в сцене 09 смотрит вслед уходящему в волны богу морей со сжатым бессильным жестом; в сцене 10 разворачивается к Медузе, рука вытянута, аура вспыхивает гневным светом

---

# Посейдон

*(бог морей, землетрясений и коней, брат Зевса и Аида; в мифе о Медузе — виновник, осквернивший храм Афины)*

**Появляется в:**
- ✅ Медуза Горгона (сцены 05 — замечает деву из моря, 06 — настигает её в храме)
- 🔜 будущие мифы: «Одиссей и Полифем» (гнев Посейдона), «Тесей» (отец-покровитель), «спор за Афины с Афиной», «Андромеда / морское чудовище»

**Визуальный образ:** огромный могучий кот-владыка морей. Глубокий сине-зелёный (teal) и грозово-сине-серый мех, широкое мускулистое сложение. Пронзительные бирюзово-аквамариновые глаза цвета мелководья. Длинная струящаяся сине-зелёная борода и грива, похожие на катящуюся морскую пену и волны. Сине-зелёный с тёмно-синим греческий хитон/гиматий с золотой вышивкой волн, дельфинов и раковин. Широкий золотой пояс с пряжкой-перламутром. Высокая корона из золота и розовых коралловых ветвей с жемчугом. В руке — массивный золотой трезубец. Мех влажно поблёскивает каплями морской воды. Вокруг ног — пена и брызги, сине-зелёное водяное божественное свечение.

**Английская карточка (images.md):**

```
Poseidon the mighty god of the sea, a large powerful imposing deep-teal-and-storm-blue-grey anthropomorphic cat character with a broad muscular build and piercing turquoise-aqua eyes the colour of shallow seawater, two perked teal-blue cat ears, a thick blue-grey cat muzzle, a long flowing teal cat tail tipped with small fin-like fronds, bipedal standing upright on two legs with humanoid body proportions, a long flowing blue-green beard and mane like rolling sea-foam and ocean waves, wearing a flowing sea-green-and-deep-blue Greek robe with rich gold embroidery of waves dolphins and seashells along the hem, a wide gold belt with a mother-of-pearl clasp, bronze-and-coral sandals, a tall ornate crown of gold and pink coral branches set with pearls upon his head, holding a massive golden three-pronged trident in his humanoid hand, his teal-and-blue fur glistening as if wet with droplets of seawater, a faint blue-green watery divine glow and a swirl of foam and spray around his feet
```

**Descriptive (video.md):**

```
the large teal-and-storm-blue sea cat king with a sea-foam beard a gold-and-coral crown and a massive golden trident
```

Короче (в плотных промптах): `"the teal sea cat king with golden trident"`.

**Атрибуты-маркеры:**
- ✅ Deep-teal-and-storm-blue-grey мех, крупное мускулистое сложение
- ✅ **Turquoise-aqua** глаза (цвет морской воды)
- ✅ Длинная **сине-зелёная борода-грива «из морской пены»** (главный силуэтный маркер — отличие от белобородого Зевса)
- ✅ Корона из **золота и розового коралла с жемчугом**
- ✅ Массивный золотой **трезубец** (узнаваемый артефакт)
- ✅ Хитон с золотой вышивкой волн/дельфинов/раковин
- ✅ Влажно-блестящий мех + пена и брызги у ног + сине-зелёное водяное свечение
- ❌ **НЕ путать с Зевсом:** Зевс — белый мех, белая борода, молния; Посейдон — teal мех, сине-зелёная борода, трезубец
- ❌ NO horns, NO demonic features — он величественный, не злодейский внешне (драма в действии, не в облике)

---

# Медуза

*(жрица Афины, обращённая богиней в горгону за то, что её осквернил Посейдон в храме; две формы — дева до проклятия и горгона после)*

**Появляется в:**
- ✅ Медуза Горгона (обе формы — см. подразделы)
- ✅ Персей и Медуза (только форма горгоны — `content/архив/Персей и Медуза/prompts/images.md`)

**Связывающий маркер:** large **jade-green eyes** — единственное, что сохраняется при превращении. У девы это сияющие нежные глаза, в которые влюблялись; у горгоны те же jade-green глаза становятся холодными, светящимися и **обращают в камень**. Зритель должен понять «это те же глаза» — что и есть трагедия мифа.

---

## Медуза-дева (maiden)

*Медуза Горгона, сцены 02, 03, 04, 15 (а также флешбэк-узнавание в сцене-хуке 01)*

**Визуальный образ:** прекраснейшая юная жрица всей Эллады. Стройная мягко-золотисто-кремовая кошка с большими сияющими нефритово-зелёными глазами и безмятежными красивыми чертами. Её главная гордость — длинные струящиеся сияющие золотые волосы, спадающие мягкими волнами до самой земли. Тонкий золотой лавровый венчик на лбу. Снежно-белый жреческий пеплос с золотой вышивкой оливковых ветвей и маленьких сов (знак храма Афины) по подолу и плечам. Тонкий золотой пояс, золотые сандалии, тонкие золотые браслеты. Мягкое тёплое свечение. БЕЗ змей, БЕЗ чешуи — в этой форме она полностью прекрасна.

**Английская карточка (images.md):**

```
Medusa in her maiden form before the curse, the most beautiful young priestess of all Hellas, a graceful slender soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes and serene gentle beautiful features, two delicate pale-gold cat ears, a small pink-and-cream cat muzzle, a long elegant pale-gold cat tail, bipedal standing upright on two legs with humanoid body proportions, her crowning glory long flowing radiant golden hair cascading in soft waves all the way down to the ground (her most famous feature), a thin gold laurel circlet resting on her brow, wearing a flowing snow-white Greek priestess peplos with delicate gold embroidery of olive branches and small owls (the mark of Athena's temple) along the hem and shoulders, a thin gold belt, gold sandals, slender gold bracelets on her humanoid wrists, a faint soft warm glow around her, NO snakes NO scales — fully beautiful and graceful in this maiden form
```

**Descriptive (video.md):**

```
the beautiful pale-gold-and-cream maiden priestess cat with long flowing golden hair down to the ground and luminous jade-green eyes
```

Короче (в плотных промптах): `"the golden-haired maiden priestess cat"`.

**Атрибуты-маркеры:**
- ✅ Soft **pale-gold-and-cream** мех
- ✅ Большие сияющие **jade-green** глаза (связывающий маркер с формой горгоны)
- ✅ **Длинные золотые волосы до самой земли** — её главная черта, упоминать в каждой сцене где видна голова
- ✅ Тонкий золотой лавровый венчик
- ✅ Снежно-белый жреческий пеплос с золотой вышивкой **олив и сов** (знак храма Афины)
- ✅ Золотые пояс/сандалии/браслеты, мягкое тёплое свечение
- ❌ NO snakes, NO scales в этой форме

---

## Медуза-горгона (gorgon)

*Медуза Горгона, сцены 11, 12, 13, 14, 16, 17 (превращение и после); вся форма мифа «Персей и Медуза»*

> **Класс A — чудовище-с-головой = бипедальный кот.** Не реальная змея, не четвероногая. Стилизованные мультяшные пиксельные змейки вместо волос, БЕЗ хоррора.

**Визуальный образ:** высокая зеленовато-серо-бронзовая чешуйчатая кошка с резкими угловатыми чертами. Те же **jade-green глаза**, что были у девы — теперь холодные, светящиеся, обращающие в камень. Вместо волос — множество живых стилизованных змеек тёмно-зелёного и бронзового цвета с крошечными ruby-glint глазками. Маленькие клыки. Рваный тёмно-бронзовый с глубоко-зелёным греческий пеплос с вышивкой змеиной чешуи, бронзовый пояс с пряжкой-змеёй. Бледно-зелёное мифологическое свечение. БЕЗ крови, БЕЗ ран — атмосфера проклятого чудовища через композицию, не через ужас.

**Английская карточка (images.md) — копировать дословно из `content/архив/Персей и Медуза/prompts/images.md`** (с добавлением jade-green глаз как мостика к форме девы):

```
Medusa the cursed Gorgon, a tall menacing greenish-grey-and-bronze scaled anthropomorphic cat character with sharp angular features and cold luminous jade-green eyes (the same jade-green eyes she had as a maiden, now glowing and petrifying) and small ivory fangs visible under her cat muzzle, two perked dark-bronze cat ears with small brass rings, a slim greenish-grey cat muzzle, a long dark-bronze cat tail with small bronze scale-patterns, bipedal standing or seated upright with humanoid body proportions, wearing a tattered dark-bronze and deep-green Greek peplos with intricate snake-scale embroidery, a wide bronze belt with a serpent-shaped clasp, dark sandals, instead of hair her head is crowned with WRITHING STYLIZED SNAKE STRANDS — many living serpentine locks of dark-green and bronze scaled snakes coiling and twisting where her hair would be each with tiny ruby-glint eyes (small cartoonish stylized snakes NOT realistic horror snakes NOT graphic), faint pale-green mythological glow around her, NO blood NO gore NO wounds — only mythological cursed-monster atmosphere through composition not through horror
```

**Descriptive (video.md):**

```
the tall greenish-grey-and-bronze scaled gorgon cat character with cold glowing jade-green eyes and a crown of stylized dark-green-and-bronze snakes instead of hair
```

Короче (в плотных промптах): `"the green-and-bronze snake-haired gorgon cat"`.

**Атрибуты-маркеры:**
- ✅ **Greenish-grey-and-bronze scaled** мех/чешуя
- ✅ **Jade-green глаза** — те же, что у девы, теперь холодные/светящиеся/петрифицирующие (связывающий маркер!)
- ✅ Стилизованные мультяшные **змейки вместо волос** (тёмно-зелёные + бронзовые, ruby-glint глазки) — НЕ хоррор-змеи
- ✅ Рваный bronze-and-green пеплос с вышивкой чешуи, бронзовый пояс с пряжкой-змеёй
- ✅ Маленькие клычки, pale-green мифологическое свечение
- ❌ **NO blood, NO gore, NO wounds, NO realistic horror snakes** — только мифическая атмосфера через композицию

**Связь форм:** в сценах превращения (11–13) показывать переход: золотые волосы → шипящие змеи, нежная кожа → зелёная чешуя, но **jade-green глаза остаются неизменными** — это сюжетный замок трагедии.

---

# Персей

*(юный герой, сын Зевса и Данаи; победитель горгоны Медузы — в мифе «Медуза Горгона» появляется только камео в финале как «грядущий герой»)*

**Появляется в:**
- ✅ Персей и Медуза (`content/архив/Персей и Медуза/prompts/images.md` — **источник эталона**, главный герой)
- ✅ Медуза Горгона (камео — сцены 17, 18: силуэт грядущего героя с зеркальным щитом у входа в пещеру, связка с отдельным роликом)
- 🔜 будущие мифы: «Персей и Андромеда», «Персей и Атлас»

**Визуальный образ:** храбрый красивый юный песочно-золотисто-кремовый короткошёрстный табби-кот с яркими решительными изумрудно-зелёными глазами. Короткая белая с бронзой греческая туника (хитонискос) с бронзовой застёжкой-листом на плече, широкий кожаный пояс, сандалии, короткий красный дорожный плащ через плечо, маленький бронзовый лавровый ободок на коротких растрёпанных песочно-золотых волосах. По сцене экипируется: высокий круглый полированный бронзовый зеркальный щит, изогнутый бронзовый серп (харпе), золотые крылатые сандалии, серый шлем-невидимка (когда надет — верх тела превращается в серебристое мерцание), тёмный кожаный мешок (кибисис) на поясе.

**Английская карточка (images.md) — копировать дословно из `content/архив/Персей и Медуза/prompts/images.md`:**

```
Perseus the young Greek hero, a brave handsome young sandy-gold-and-cream short-haired tabby anthropomorphic cat character with bright determined emerald-green eyes and youthful confident features, two perked sandy-gold cat ears, a small cream-and-pink cat muzzle, a long sandy-gold cat tail, bipedal standing upright on two legs with humanoid body proportions, wearing a short white-and-bronze Greek tunic (chitoniskos) with a bronze leaf-pattern shoulder clasp, a wide brown leather belt with a bronze buckle, leather sandals, a short red travel cloak draped over one shoulder, his short tousled sandy-gold hair with a single small bronze laurel circlet — and depending on scene equipped with: a tall round polished bronze MIRROR SHIELD (highly reflective like a mirror) on his humanoid left arm, a curved bronze sickle-sword (harpe) in his humanoid right hand, golden winged sandals (talaria) on his ankles with small white feathered wings, a pale-grey winged invisibility helm (kunee) — when noted in the scene as worn, his head and upper body fade into a faint silver-grey shimmer of magical transparency — and a dark leather drawstring bag (kibisis) at his belt
```

**Descriptive (video.md):**

```
the young sandy-gold-and-cream tabby hero cat with emerald-green eyes a tall round polished bronze mirror shield and a curved bronze sickle-sword
```

Короче (в плотных промптах): `"the young hero cat with the mirror shield"`.

**Атрибуты-маркеры:**
- ✅ **Sandy-gold-and-cream** короткошёрстный tabby
- ✅ Bright **emerald-green** глаза
- ✅ Короткие растрёпанные песочно-золотые волосы + бронзовый лавровый ободок
- ✅ Высокий круглый **зеркальный бронзовый щит** (главный лейтмотив) + изогнутый **серп-харпе**
- ✅ Золотые крылатые сандалии, шлем-невидимка (верх тела → серебристое мерцание), кожаный мешок-кибисис
- ✅ Бело-бронзовая туника + короткий красный плащ
- 🎬 В «Медуза Горгона» — только силуэт/со спины у входа в пещеру, зеркальный щит ловит отражение; полноценная история героя — в отдельном ролике

---

# Глобальные правила консистентности

## Один персонаж — одна карточка

Если персонаж появляется в новом мифе — **не сочиняй новую внешность**, открой этот файл и возьми существующую. Артемида в «Орионе» и в «Каллисто» — одна и та же богиня. Зрителю канала это важно. Если хочешь чтобы было «иначе» — это **уже другой персонаж** (другая богиня, другая нимфа), и она должна иметь своё имя и свою карточку.

## Возрастные формы — один раздел, разные подразделы

Если один персонаж проходит через возрасты или формы (Каллисто: нимфа → изгнанница → медведица; Аркас: младенец → мальчик → охотник; Зевс: молодой → старший), всё это идёт в **один раздел** с подразделами. Связывающий маркер (цвет глаз) держим во всех формах.

## ДНК-маркер семьи

Связь поколений показывается через ОДИН наследственный маркер — обычно цвет глаз:
- **Каллисто → Аркас:** honey-amber глаза
- **Зевс → Зевс-в-облике-Артемиды:** electric-gold spark в pale-silver-blue глазах (выдаёт маскировку)
- (для будущих мифов: Леда → Елена, Деметра → Персефона, Аполлон → Асклепий)

## Антропоморфные позы в активных сценах

В сценах с активным движением (бег, прыжок, бросок, падение, рождение, превращение) явно прописывать в промпте:

```
"human-like pose, body upright not on four legs",
"humanoid arms outstretched",
"humanoid legs running upright"
```

Без этих оборотов модель Flow в action-кадрах скатывается в обычную четвероногую кошку. **Исключение** — персонажи класса C (заколдованные звери), которые СЮЖЕТНО на четырёх лапах.

## Голые части тела требуют `humanoid` рядом

Никогда не оставлять `her ankle`, `her hand`, `her arm`, `his foot` без `humanoid` рядом. Модель отрисует человеческую ногу/руку/ступню, а не кошачью. Правильно: `humanoid hand`, `humanoid paw`, `humanoid leg`. См. memory `feedback_prompt_audit_pitfalls`.

## Волосы в КАЖДОЙ сцене где видна голова

Если в карточке у персонажа есть волосы (грива, коса, гладкая укладка), описание волос обязано быть в КАЖДОМ промпте сцены, где видна голова. Карточка в шапке `images.md` не подхватывается моделью. Без описания волос Flow рисует лысую голову под короной/венком. См. memory `feedback_prompt_audit_pitfalls`.
