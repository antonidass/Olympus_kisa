# Промпты картинок: Часть 2 — Власть Кроноса

Промпты картинок-входов для Google Flow / ImageFX. Одна картинка = один кадр сцены. Видео потом строится через image-to-video, см. [video.md](video.md) (после генерации картинок).

Маппинг **картинка ↔ предложение** идёт по [voiceover.md](voiceover.md) → «Разбивка на предложения». В этой части — **19 картинок на 19 сцен** (хук+титул = одна сцена с одной картинкой; sent_003..sent_020 — каждое в своей сцене).

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
     - ПЕРВОБОЖЕСТВА (Гея, Уран) =
       абстрактные сущности-стихии с глазами. NO humanoid figure, NO body, NO hands.
       Эмоции — через изменения самой стихии (трещины, тучи, тусклый свет, слёзы по холмам).
     - КОТЫ (Кронос, Рея, 12 титанов, Афродита, котята-олимпийцы,
       Зевс-эмбрион в утробе) = антропоморфные бипедальные коты.
       humanoid body proportions, standing upright on two legs.
     ============================================================

     ГЕЯ (живой пейзаж-сущность; ч. 2 — три эмоции по сценам:
     страдающая sent_003-004 → мстительная sent_005-006 → пророческая sent_013):
     Gaia the living primordial earth-landscape entity,
     a vast rolling terrain of dark-moss-green and earth-brown soil
     with oak roots, grape vines and small wildflowers growing across it,
     TWO LARGE GLOWING GOLDEN-GREEN EYES set into the earth itself
     (one on the central hillside, one on a nearby slope) gazing upward
     with primordial awareness, faint warm earth-glow pulsing beneath
     the surface like slow breathing,
     NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face

     УРАН (живое Небо-купол с глазами; ч. 2 — четыре состояния:
     гневный sent_003 → разрезанный серпом sent_007 → отрывается и
     поднимается выше sent_008 → две далёкие холодные звезды,
     плачущий дождём sent_010-011):
     Uranus the living primordial sky-canopy entity,
     a vast silvery-blue starry sky-dome stretched across the upper portion
     of the frame filled with star points and constellations,
     drifting silver clouds across the dome,
     TWO ICY PALE-BLUE GLOWING EYES formed by especially bright star clusters
     within the constellation pattern gazing downward at the earth,
     the dome edges curving downward toward the horizon like a canopy,
     NO humanoid figure, NO body, NO hands, NO arms, NO crown,
     NO mantle, NO face

     КРОНОС (ч. 2 — ЧЕТЫРЕ возраста, прогресс по части:
     sent_006 — молодой подросток без бороды, только что взял серп;
     sent_007 — молодой узурпатор-кот в момент свержения, серп в руке;
     sent_012 — надевший корону отца, борода короткая, седина на висках;
     sent_013-015 — параноик-отец на троне, глаза тёмные в кругах):
     Cronus the anthropomorphic bipedal cat titan, cold-steel-grey fur
     with silver streaks, long dark-silver shoulder-length hair greying
     at the temples, full thick beard (only in later sentences sent_012+,
     in sent_006-007 still CLEAN-SHAVEN no beard), sharp amber-yellow predator eyes,
     dressed in heavy bronze cuirass over dark grey tunic (sent_012+) OR
     simple dark-grey tunic (sent_006-007), wide belt with skull-shaped
     medallions (only sent_012+, dark uses them as paranoia symbol),
     holding a curved jagged adamant sickle in his right paw (sent_006+,
     not before), towering muscular frame, stern brooding face,
     humanoid body proportions, standing upright on two legs

     РЕЯ (ч. 2 — ТРИ состояния по сценам:
     sent_012 — молодая жена рядом с Кроносом, спокойная улыбка;
     sent_014-016 — измученная мать, глаза всё темнее, на коленях;
     sent_017-019 — беглянка в горной пещере, рука на животе,
     внутреннее золотистое свечение от эмбриона Зевса):
     Rhea the anthropomorphic bipedal cat titaness mother,
     cream-and-pale-gold fur with warm peach undertones,
     long honey-gold hair braided over her shoulder, warm brown eyes,
     dressed in a flowing ivory gown with gold embroidery of wheat sheaves
     and lions, thin gold diadem on her head, gentle protective expression,
     humanoid body proportions, standing upright on two legs

     ПРОЧИЕ ТИТАНЫ (массовка, 11 штук в сцене 5 — отказались брать серп):
     eleven anthropomorphic bipedal cat Titans gathered together
     in a half-circle, each in a distinctive metallic or elemental palette
     — bronze, copper, silver, steel, gold, deep-indigo, sea-green, ivory,
     olive, violet, pearl-white — varied robes of bronze and linen with
     elemental motifs (waves, stars, wheat, moonlight), humanoid body
     proportions, standing upright on two legs, all averting their gaze
     downward (refusing to take the sickle)

     АФРОДИТА (ч. 2 sent_010 — новорождённая богиня красоты,
     поднимается из морской пены, прикрыта только волосами и пеной):
     Aphrodite the anthropomorphic bipedal cat goddess of beauty rising
     from sea foam, pearl-pink fur with milky-white undershade,
     long cream-white hair flowing down her back covering her body,
     turquoise-green sea-wave eyes, modestly covered by curling sea foam
     and her own long hair, soft inner glow, humanoid body proportions,
     standing upright on two legs, NO nudity, NO explicit body —
     fully covered by sea foam and hair

     ПЯТЬ КОТЯТ-ОЛИМПИЙЦЕВ (sent_014-015 — поглощаются Кроносом,
     стилизованно: котёнок превращается в свет/звёзды и втягивается):
     five tiny newborn cat-kitten Olympians wrapped in white linen
     swaddling cloths, each with a hint of their adult palette —
     Hestia soft-beige cream kitten, Demeter wheat-and-honey-gold kitten,
     Hera cream-white with golden tabby tips kitten, Hades dark-charcoal-gray
     kitten with silver eye-points, Poseidon sea-blue-and-green kitten —
     each kitten dissolving into golden particles and starlight
     as they are absorbed, NO open mouths, NO screams, NO blood,
     NO swallowing motion — the kittens turn into LIGHT and STARS
     and stream into Cronus's silhouette like an absorbed soul

     ЗЕВС-ЭМБРИОН (ч. 2 sent_018-019 — силуэт-эмбрион внутри Реи,
     первое появление главного героя цикла; в кадре Рея, а не Зевс):
     unborn baby Zeus visible only as a tiny seated kitten silhouette
     glowing warm gold inside Rhea's belly through her gown,
     faint tiny gold lightning sparks above the kitten silhouette inside
     her belly, no embryo face, only a glowing pose-silhouette,
     Rhea's protective hand resting on her belly

     ============================================================ -->

<!-- ============================================================
     СТИЛЕВОЙ КАРКАС (см. CONTEXT.md → «Стилевой каркас промптов»):
     highly detailed pixel art, 9:16 vertical composition,
     modern detailed pixel art style, [LIGHTING], no text, no letters,
     no camera movement

     ОБЩИЕ НЕГАТИВЫ (всегда в конце промпта):
     NO humans, NO people, NO real four-legged cats,
     no blood, no gore, no wounds

     ДОПОЛНИТЕЛЬНЫЕ НЕГАТИВЫ ДЛЯ СЦЕН С ПЕРВОБОЖЕСТВАМИ (Гея, Уран):
     NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face,
     only the abstract entity-form with eyes

     В СМЕШАННЫХ СЦЕНАХ (Кронос/Рея на фоне Геи-земли под Ураном-небом):
     антропоморфность пишется только для котов,
     а для первобожеств-фонов добавляется «NO humanoid figure for Gaia/Uranus,
     they are the landscape and sky themselves».

     ДЛЯ СЦЕН СО СВЕРЖЕНИЕМ И ПОГЛОЩЕНИЕМ ДЕТЕЙ (платформенная безопасность):
     no blood, no gore, no wounds, no open mouths, no swallowing motion,
     no screams, no agony — death and absorption shown only as
     transformations into light, stars, particles, or distant rising.
     ============================================================ -->

---

## Сцена 1 (sent_001 + sent_002 — хук «Сын сверг отца...» + титул караоке поверх)

**Краткое описание кадра.** Якорный визуал части. Силуэт молодого Кроноса-кота в полупрофиль на фоне разрезанного звёздного неба Урана: одна серебряная трещина-молния идёт поперёк ночного купола (намёк на свержение), под куполом тёмные холмы Геи. В правой лапе Кроноса — изогнутый адамантовый серп. Глаза янтарно-жёлтые горят. Композиция должна оставить центральное «пустое» поле под накопительную караоке-плашку «ОТ ХАОСА → ДО ОЛИМПА → ЧАСТЬ 2».

**Промпт:** cronus titan silhouette under cracked starry sky as part two anchor shot, young Cronus the anthropomorphic bipedal cat titan teenager in three-quarter back silhouette standing on a mossy hilltop, cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard, sharp amber-yellow predator eyes glowing in profile, dressed in a simple dark-grey tunic with a wide leather belt, lean athletic teen frame, humanoid body proportions, standing upright on two legs, holding a curved jagged dark adamant sickle low in his right humanoid paw, above him the living primordial sky-canopy entity Uranus as a vast silvery-blue starry sky-dome filled with constellations with a single dramatic silver lightning crack running diagonally across the dome from horizon to horizon, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES of Uranus visible far in the upper background gazing aside, beneath the silhouette the moss-green hillsides of Gaia far below, the sky and the earth are NOT humanoid — they are the dome and the landscape themselves with eyes, only Cronus is a humanoid figure in the frame, central vertical area of the frame kept visually quiet to leave room for an overlaid karaoke title plate in editing, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, ominous cinematic lighting with cool starlight above and warm golden eye glow on Cronus, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 2 (sent_003 — «Уран прятал собственных детей обратно в чреве Геи»)

**Краткое описание кадра.** Угнетающий кадр перед действием Геи. Звёздный купол Урана сверху давит вниз, тучи сгущаются поперёк созвездий, край купола опускается низко и придавливает Землю. Холмы Геи прогнулись от давления, на их поверхности проступают слабые силуэты циклопов и гекатонхейров — наполовину вдавлены в моховую почву. Гея — пейзаж с двумя золотисто-зелёными глазами на холмах, глаза прикрыты от боли.

**Промпт:** suffocating sky entombs the children inside the suffering earth, the living primordial sky-canopy entity Uranus filling the upper two thirds of the frame as a darkening silvery-blue starry sky-dome with thick storm clouds gathering across the constellations, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES of Uranus narrowed and burning hostile within the constellation pattern, the dome edges curving downward and pressing visibly low against the earth like a heavy lid almost touching the horizon, in the lower third the living primordial earth-landscape entity Gaia with sagging dark-moss-green-and-earth-brown hillsides pushed down by the weight of the sky, faint thin glowing warm-orange CRACKS of light starting to form across her slopes, oak roots straining under pressure, TWO LARGE GOLDEN-GREEN EYES set into the hillsides half-closed in pain, half-buried faint cat silhouettes visible inside the moss-green ground — three one-eyed cyclops cat brothers and three many-armed granite hecatoncheires cat giants sinking back into the earth (each giant with multiple arms creating a hundred-handed silhouette), the buried cat-children glow faintly from within the earth as prisoners held inside, the sky and the earth are NOT humanoid — they are the dome and the landscape themselves with eyes, only the half-buried cyclops and hecatoncheires cats are humanoid figures in the frame, NO humanoid figure for Uranus or Gaia, NO hands NO arms NO mouths NO faces on the sky or earth, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, oppressive dark cinematic lighting with cold sky above and warm cracked earth-glow below, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 3 (sent_004 — «Гея больше не могла терпеть»)

**Краткое описание кадра.** Поворотная точка части. Крупный план одного из глаз Геи в центральном холме. Глаз медленно открывается, золотисто-зелёное свечение в нём горит ярче и теплее, по контуру глаза стекает одинокая золотая слеза-ручеёк по моховому склону вниз. Решимость, не отчаяние. Никаких других элементов в кадре — только земля, глаз и слеза.

**Промпт:** earth-eye awakens with resolve as one single golden tear falls, intimate medium closeup of one of Gaia's two earth-eyes set into the central mossy hillside, the living primordial earth-landscape entity Gaia in tight crop of the hillside, dark-moss-green and earth-brown soil texture filling most of the frame, ONE LARGE GLOWING GOLDEN-GREEN EYE opening slowly and burning brighter with primordial determination, faint warm earth-glow pulsing strongly beneath the surface around the eye, ONE single thin GOLDEN TEAR-STREAM of glowing molten gold running down from the corner of the eye along the moss-green slope, oak roots and small wildflowers visible around the eye now perking up slightly with returning life, no other entities in the frame, soft blurred mossy hillsides far behind, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face — only the living earth itself with the one resolute eye and one golden tear, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm intimate cinematic lighting with strong green-gold under-glow, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 4 (sent_005 — «Из адаманта она выковала тяжёлый, неубывающий серп»)

**Краткое описание кадра.** Из недр Геи поднимается плоский каменный алтарь-плита, на котором лежит только что выкованный серп: тёмно-серое адамантовое лезвие, изогнутое, тяжёлое. Вокруг плиты — серебристые искры и редкие тонкие линии расплавленного золота под поверхностью почвы (память о ковке). Глаза Геи в холмах за плитой смотрят на серп торжественно и холодно. Никаких рук — серп выковала сама земля.

**Промпт:** adamant sickle emerges from earth on a stone altar slab, a flat circular stone altar-slab pushed up from beneath the moss-green ground of the living primordial earth-landscape entity Gaia at the center of the frame, on top of the slab lies a single newly forged curved jagged dark-grey adamant sickle with a tapered black handle wrapped in dark leather, the sickle blade still faintly glowing warm orange from forging, small silver sparks drifting in the air around the slab, thin glowing rivulets of molten gold running beneath the surrounding moss-green soil like fading forge-veins, behind the altar slab the moss-green hillsides of Gaia with TWO LARGE GLOWING GOLDEN-GREEN EYES set into the slopes gazing solemnly at the sickle, the earth is NOT humanoid — it is the landscape itself with the eyes that forged the sickle from inside itself, NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face, NO blacksmith, NO forge tools in the frame — the sickle was forged by the earth itself, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic warm cinematic lighting with a single bright key light on the sickle blade and golden-green under-glow from the surrounding earth, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 5 (sent_006 — «Только младший её сын, Кронос, согласился его взять»)

**Краткое описание кадра.** На той же мшистой поляне вокруг каменного алтаря — полукруг из одиннадцати молодых титанов-котов, все опускают глаза или отвернулись от серпа на плите. Перед плитой шагает вперёд один — молодой Кронос-подросток (тот же, что в сцене 1), правой лапой берёт серп с алтаря. Глаза горят. Гея-пейзаж вокруг с двумя глазами в холмах наблюдает.

**Промпт:** youngest titan accepts the sickle while eleven siblings look away, on a wide mossy clearing around the central stone altar-slab from the previous scene with the curved jagged dark adamant sickle still resting on it, eleven anthropomorphic bipedal cat Titans gathered in a half-circle behind the slab, each in a distinctive metallic or elemental palette — bronze, copper, silver, steel, gold, deep-indigo, sea-green, ivory, olive, violet, pearl-white — varied robes of bronze and linen with elemental motifs (waves, stars, wheat, moonlight), humanoid body proportions, standing upright on two legs, all averting their gaze downward and stepping back from the sickle, in the front center stepping forward toward the altar young Cronus the anthropomorphic bipedal cat titan teenager, cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes locked on the sickle with defiant determination, dressed in a simple dark-grey tunic with a wide leather belt (no cuirass yet, no skull medallions yet), lean athletic teen frame, humanoid body proportions, standing upright on two legs, his right humanoid paw just reaching out and closing around the leather-wrapped handle of the curved adamant sickle, behind the half-circle of titans the moss-green hillsides of the living primordial earth-landscape entity Gaia with TWO LARGE GLOWING GOLDEN-GREEN EYES set into the slopes watching the choice with grim approval, Gaia is NOT humanoid — only the cat titans are humanoid figures in the frame, NO humanoid figure for Gaia, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic warm cinematic lighting with a single golden key light on Cronus and the sickle, the rest in cool shaded tones to emphasize the eleven refusing siblings, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 6 (sent_007 — «Той ночью он сверг отца одним ударом»)

**Краткое описание кадра.** Ночь. Звёздное небо Урана прямо над землёй, его край опущен очень низко (как в сцене 2). На переднем плане молодой Кронос (теперь уже после ритуала, серп в обеих лапах) замахивается серпом снизу вверх. В момент удара лезвие серпа разрезает звёздный купол серебряной диагональной трещиной-молнией. Самого момента удара по фигуре нет — небо не фигура, а купол. Глаза Урана-звёзды в кадре в шоке расширены. Силуэт Кроноса в нижней трети, лезвие на пике взмаха.

**Промпт:** night strike a single silver crack splits the starry sky-dome, dramatic night scene, young Cronus the anthropomorphic bipedal cat titan teenager in mid-strike pose in the lower third of the frame, cold-steel-grey fur with subtle silver streaks, short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard yet, sharp amber-yellow predator eyes blazing with focused intent, dressed in a simple dark-grey tunic with a wide leather belt, lean athletic teen frame, humanoid body proportions, standing upright on two legs on a moonlit mossy hilltop, both humanoid paws gripping the curved jagged dark adamant sickle raised high above his head at the peak of an upward swing, the sickle blade striking diagonally across the very bottom edge of the sky-canopy entity above, above him the living primordial sky-canopy entity Uranus pressed low against the earth as a silvery-blue starry sky-dome filled with constellations, ONE bright silver lightning crack tearing diagonally across the dome from where the sickle blade meets it spreading outward across the constellations, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES of Uranus visible within the constellation pattern wide and shocked, no figure to strike — the sky itself is being torn, no blood, no wound, no body, only the silver crack across the dome, the sky is NOT humanoid — it is the starry dome being cracked, only Cronus is a humanoid figure in the frame, NO humanoid figure for Uranus, beneath the strike the moss-green hillsides of Gaia visible in the very bottom of the frame, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, intense night cinematic lighting with the silver lightning crack as the brightest focal light and Cronus's eyes glowing amber from below, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 7 (sent_008 — «Уран не погиб — он навсегда поднялся в небо»)

**Краткое описание кадра.** Ключевая образная сцена части — мягкая, не трагическая. Звёздный купол Урана **отрывается от Земли и поднимается выше**, превращаясь в далёкие холодные звёзды. Раньше близкие глаза-скопления теперь становятся двумя крошечными холодными точками на самом верху кадра. На земле — Гея-пейзаж с глазами в холмах смотрит вверх в спокойном изумлении. Без боли, без скорби — это переход формы, не смерть.

**Промпт:** sky rises forever upward and becomes distant cosmos, the living primordial sky-canopy entity Uranus visibly detaching from the horizon and lifting upward through the frame, the silvery-blue starry sky-dome now floating high above and shrinking with distance into a smaller deeper field of stars, the constellation pattern stretching and thinning as it rises away, TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES of Uranus now shrunk to TWO TINY DISTANT COLD STAR-POINTS far at the very top of the frame still glowing faintly, soft silver star-particles drifting upward from the rising dome edges like a slow ascension, beneath the rising sky in the lower half the living primordial earth-landscape entity Gaia visible as moss-green and earth-brown hillsides now free of pressure, TWO LARGE GOLDEN-GREEN EYES set into the central hillsides gazing upward in serene primordial wonder watching the sky leave, faint warm earth-glow pulsing softly beneath the surface, the warm-orange cracks of suffering from earlier scenes now closing and healing, no other figures in the frame, the sky and the earth are NOT humanoid — they are the dome and the landscape themselves with eyes, NO humanoid figure for Uranus or Gaia, NO hands NO arms NO mouths NO faces on the sky or earth, this is a transformation, NOT a death — no falling body, no blood, no gore, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, atmospheric cinematic lighting with soft cool starlight rising upward and warm green-gold under-glow below, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 8 (sent_009 — «А дети его наконец-то вышли на свет»)

**Краткое описание кадра.** Светлая сцена. Тёплый утренний свет (или предрассветный) разливается по моховым холмам Геи. Из земли поднимаются на свет три циклопа-кота (одноглазых) и три гекатонхейра-кота (многоруких) — освобождённые. Их фигуры наполовину вышли из почвы, мхом ещё облеплены спины и плечи. Глаза горят тёплыми оттенками. Гея-пейзаж приветствует их.

**Промпт:** earth-children emerge into morning light after long imprisonment, warm dawn lighting across rolling moss-green hillsides of the living primordial earth-landscape entity Gaia, six freed children rising up out of the moss-green ground as the earth releases them, in the foreground three Cyclops anthropomorphic bipedal cat blacksmith brothers — Brontes Steropes Arges — half-emerged from the soil up to their waists, massive muscular frames, short stone-slate-grey fur, ONE large round eye in the middle of each forehead (NO two eyes, ONE single round eye in the center of the forehead per cyclops, repeat: only one eye each cyclops), Brontes with amber eye, Steropes with electric-white eye, Arges with gold eye, bare muscular torsos with leather blacksmith aprons, bronze arm bracers, hands reaching upward toward the light, humanoid body proportions, standing upright on two legs, behind them three Hecatoncheires anthropomorphic bipedal cat hundred-handed giants — Cottus Briareus Gyges — towering taller than the cyclops, half-emerged from the hillsides up to their knees, dark granite-stone fur with cracked rock vein patterns, shaved or stubble heads, glowing ember-orange eyes, EACH GIANT HAS MANY ARMS — six large primary arms (three on each side of the body) PLUS a dense radial fan of about ten additional smaller secondary arms sprouting from the shoulders and back creating an unmistakable hundred-handed silhouette, the additional fan-arms gesturing outward as if stretching after long imprisonment, single head one face per giant (NOT many heads — one face only), humanoid body proportions, standing upright on two legs, on the hillsides around them the moss-green soil splitting open gently to release them with soft warm earth-glow streaming out of the cracks, TWO LARGE GOLDEN-GREEN EYES of Gaia in the distant background hillsides gazing toward the freed children with tired primordial joy, the earth is NOT humanoid — only the cyclops and hecatoncheires cats are humanoid figures in the frame, NO humanoid figure for Gaia, no remnant of the sky-dome — the sky above is empty pale-gold dawn, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm dawn cinematic lighting with golden sun rays and green-gold under-glow from the freed earth, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds

---

## Сцена 9 (sent_010 — «Из морской пены, куда упали капли свергнутого бога, родилась Афродита — богиня красоты»)

**Краткое описание кадра.** Море на рассвете. У скалистого берега бьются мягкие волны. Из густой клубящейся морской пены поднимается Афродита-кошка: перламутрово-розовый мех, длинные кремово-белые волосы спадают на тело и сливаются с пеной, бирюзовые глаза. Полностью прикрыта пеной и волосами — никакой обнажённости. Сверху, очень высоко в розово-золотом утреннем небе, видны две далёкие холодные звёзды Урана и тонкий след падающих серебристо-жемчужных капель к морской пене.

**Промпт:** beauty goddess rises from sea foam where sky droplets fell, dawn coastal seascape, gentle waves crashing softly against rocky shoreline in the lower half, thick swirling pearl-white sea foam piled along the wave-line, in the very center of the foam rising upward Aphrodite the anthropomorphic bipedal cat goddess of beauty, pearl-pink fur with milky-white undershade, long flowing cream-white hair flowing down her back and front covering her body completely, turquoise-green sea-wave eyes gazing upward in calm wonder, modestly covered by curling sea foam wrapping around her body and her own long hair, soft inner pearlescent glow around her, humanoid body proportions, standing upright on two legs partially still submerged in the foam, NO nudity NO explicit body — fully and modestly covered by sea foam and long hair, high above in the rose-and-gold dawn sky two tiny distant cold star-points of the receded Uranus still visible as faint pale-blue twinkles, a single thin trail of silvery-pearl droplets falling from the distant star-points down through the dawn sky and landing in the sea foam where Aphrodite rises, the droplets clearly silvery-pearl NOT red NOT blood, the sky is NOT humanoid — only Uranus's two distant star-eyes mark his presence, only Aphrodite is a humanoid figure in the frame, soft sunrise pastels — pearl-pink rose-gold pale-blue — across the entire palette, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, soft warm dawn cinematic lighting with pearlescent inner glow on Aphrodite, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds, no nudity

---

## Сцена 10 (sent_011 — «А Уран теперь плачет с неба. И его слёзы падают на землю дождём»)

**Краткое описание кадра.** **Самый поэтичный кадр части. Лейтмотив.** Вид снизу-вверх на ночное небо (или сумеречное). Высоко-высоко — две далёкие холодные звезды-глаза Урана, и из каждого медленно льются золотисто-серебряные слёзы-капли. Эти капли превращаются в мягкий тёплый дождь, падающий на моховые холмы Геи внизу. На холмах — лужицы и ручейки, отражающие далёкие звёзды. Без персонажей. Тихо. Композиция вертикальная, акцент на потоке капель сверху вниз.

**Промпт:** sky-tears become the eternal rain across the world, vertical low-angle view looking upward at a twilight sky from the moss-green hillsides of the living primordial earth-landscape entity Gaia, high at the very top of the frame far in the distance TWO TINY COLD GLOWING STAR-POINTS of the receded Uranus still gazing down sadly, soft golden-silver tear-droplets visibly streaming downward from each distant star-eye in continuous slow trails, the falling tear-trails gradually transforming into warm gentle rain partway down the frame, soft warm rain falling across the entire scene, raindrops glowing faint gold as they fall through the twilight air, in the lower third the moss-green and earth-brown hillsides of Gaia catching the rain in small mirror-like puddles and tiny rivulets, TWO LARGE GLOWING GOLDEN-GREEN EYES of Gaia set into the distant hillsides lifted upward gazing back at the distant star-points with quiet sorrow, no figures in the frame, no other characters, the sky and the earth are NOT humanoid — only the two pairs of eyes (the two tiny pale-blue star-points high above and the two large golden-green earth-eyes below) mark the two grieving primordial entities, NO humanoid figure for Uranus or Gaia, NO hands NO arms NO mouths NO faces on the sky or earth — they grieve through the falling rain and through the upward gaze, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, soft melancholic cinematic lighting with cool moonlit twilight palette and warm gold raindrop highlights, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 11 (sent_012 — «Кронос сел на трон отца и взял в жёны свою сестру Рею»)

**Краткое описание кадра.** Тронный зал в горной пещере (намёк на «трон отца» — небо, но физический трон стоит на земле). Каменный массивный трон в центре. На троне — Кронос, уже подросший: длинная густая борода, седина на висках, на голове — серебряная корона Урана (с сапфирами, как звёзды), тяжёлая бронзовая кираса, серп лежит у трона на каменной плите. Рядом на меньшем троне — Рея, молодая, спокойная, в светлом платье. Между ними — лёгкое расстояние, без объятий, торжественная статика. Над троном высоко в потолке пещеры — пара далёких холодных звёзд Урана, едва видимых.

**Промпт:** crowned usurper takes his father's throne with his wife at his side, wide formal interior shot of a massive stone throne hall carved into a mountain cave with high vaulted rocky ceiling, in the center of the frame a large dark-stone throne with star-pattern engravings, on the throne sits Cronus the anthropomorphic bipedal cat titan in his usurper form, cold-steel-grey fur with silver streaks, long dark-silver shoulder-length hair greying at the temples, full thick beard now grown in, sharp amber-yellow predator eyes proud and stern, dressed in heavy bronze cuirass over dark grey tunic, wide belt with skull-shaped medallions, a tall silver crown with sapphires shaped like constellations on his head (the recovered crown of Uranus), the curved jagged adamant sickle resting on a low stone slab beside the throne, towering muscular frame, humanoid body proportions, sitting upright on the throne, beside him to the right on a smaller secondary throne sits Rhea the anthropomorphic bipedal cat titaness mother, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair braided over her shoulder, warm brown eyes calm and gentle, dressed in a flowing ivory gown with gold embroidery of wheat sheaves and lions, thin gold diadem on her head, gentle protective expression, humanoid body proportions, sitting upright on her throne with hands folded in her lap, slight respectful distance between the two thrones without embracing, two stone torch sconces flank the thrones with warm golden flames, high above in the cathedral-like cave ceiling a small opening reveals the night sky outside with TWO TINY DISTANT COLD STAR-POINTS of the receded Uranus visible as faint pale-blue twinkles watching the new ruler from afar, the sky is NOT humanoid — only the two star-points mark Uranus, only Cronus and Rhea are humanoid figures in the frame, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic warm cinematic lighting with torch glow on the two thrones and cool starlight from the ceiling opening, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 12 (sent_013 — «Но Гея сказала сыну: тебя свергнет твой собственный ребёнок»)

**Краткое описание кадра.** Сюжетный поворот. Кронос на троне (тот же, что в сцене 11) — крупнее, в полупрофиль. На полу перед троном проступают древние светящиеся руны и символы прямо в каменных плитах — это голос Геи, выходящий из земли. Лицо Кроноса в тени, только янтарные глаза горят и расширяются от страха. На потолке — пары далёких звёзд Урана едва видны. Рея за троном в тени, смотрит на руны с тревогой.

**Промпт:** prophecy runes glow on the throne room floor warning the usurper, medium close shot of Cronus the anthropomorphic bipedal cat titan in his usurper form sitting on the stone throne in three-quarter view, cold-steel-grey fur with silver streaks, long dark-silver shoulder-length hair greying at the temples, full thick beard, sharp amber-yellow predator eyes wide and frightened catching the rune-light from below, dressed in heavy bronze cuirass over dark grey tunic, wide belt with skull-shaped medallions, tall silver crown with sapphires shaped like constellations, humanoid body proportions, sitting upright on the throne leaning forward to look down at the floor, on the stone floor directly in front of the throne ancient glowing golden-green primordial runes and prophecy symbols have appeared etched into the stone slabs glowing brightly from beneath — the voice of the living earth itself speaking through the ground, faint warm earth-glow pulsing upward through the cracks of the floor around the runes, in the background behind the throne Rhea visible as a soft shadowed silhouette of the cream-and-pale-gold titaness mother cat watching the runes with quiet alarm, high in the cathedral-like ceiling opening TWO TINY DISTANT COLD STAR-POINTS of the receded Uranus visible faintly observing the prophecy moment, only Cronus and Rhea are humanoid figures in the frame, the earth-runes are the voice of Gaia herself — Gaia is NOT humanoid here, NO humanoid figure for Gaia, NO body NO hands NO mouth — she speaks through the runes glowing in the stone floor, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, tense low-key cinematic lighting with strong warm golden-green rune-glow from below on Cronus's face and cool starlight from above, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 13 (sent_014 — «И тогда Кронос начал глотать своих детей — Гестию, Деметру, Геру, Аида, Посейдона»)

**Краткое описание кадра.** Кронос на троне в полупрофиль, теперь в более тёмном свете, глаза в кругах. Перед троном висят в воздухе по полукругу пять светящихся силуэтов котят-олимпийцев в свивальниках — каждый своего цвета (бежевый, золотой, кремовый, угольный, морской). Они **превращаются в свет и звёзды** и тянутся длинными струйками к Кроносу — поглощение, не глотание. Никакого рта Кроноса в кадре — он сидит спокойно, и котята растворяются в его силуэте как впитываемые души. Без агонии, без криков, без крови.

**Промпт:** five newborn kittens dissolve into starlight and are absorbed into the throned father, medium-wide shot of Cronus the anthropomorphic bipedal cat titan in his paranoid father form sitting on the stone throne in three-quarter view, cold-steel-grey fur with silver streaks, long dark-silver shoulder-length hair greying at the temples, full thick beard, sharp amber-yellow predator eyes dark and ringed in shadow, dressed in heavy bronze cuirass over dark grey tunic, wide belt with skull-shaped medallions, tall silver crown with sapphires shaped like constellations, humanoid body proportions, sitting upright on the throne with mouth CLOSED (mouth not open, no swallowing motion visible), arranged in a soft half-circle floating in the air in front of the throne five tiny newborn cat-kitten Olympians each wrapped in white linen swaddling cloths, each with a hint of their adult palette — leftmost Hestia a soft-beige cream kitten with warm gold-brown eye-points, then Demeter a wheat-and-honey-gold kitten with warm amber eye-points, then Hera a cream-white kitten with golden tabby tips and emerald eye-points, then Hades a dark-charcoal-gray kitten with silver eye-points, rightmost Poseidon a sea-blue-and-green kitten with sea-green eye-points, EACH KITTEN DISSOLVING into long streams of golden particles and silver starlight stretching from the kitten silhouettes toward Cronus's chest where the streams enter his body like absorbed souls, NO open mouths on the kittens (no screams), NO open mouth on Cronus (no swallowing), NO blood, NO swallowing motion — the kittens TURN INTO LIGHT AND STARS and stream into Cronus's silhouette like absorbed souls, behind the throne soft dark stone walls of the throne hall, only Cronus and the five kittens are humanoid figures in the frame, the dissolving particles are abstract light NOT physical, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, ominous low-key cinematic lighting with deep shadows on Cronus and soft pale-gold particle glow from the five dissolving kittens, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds, no open mouths, no screams

---

## Сцена 14 (sent_015 — «Одного за другим»)

**Краткое описание кадра.** Тихий, тяжёлый кадр-точка. Крупный план: за тёмным силуэтом Кроноса на троне — Рея на коленях в углу зала, протянутая ладонь, тёмный профиль, глаза полны слёз. Перед ней последний из пятерых — крошечный силуэт Посейдона-котёнка (сине-зелёный пушок) растворяется в свету и тянется длинной струйкой звёзд к Кроносу. Без агонии, тихая скорбь.

**Промпт:** one by one each kitten leaves the mother's outstretched paw as light, intimate medium shot inside the dark throne hall, in the foreground left Rhea the anthropomorphic bipedal cat titaness mother kneeling on the stone floor in profile, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair braided over her shoulder now disheveled and falling forward, warm brown eyes wet with quiet silent tears, dressed in a flowing ivory gown with gold embroidery of wheat sheaves and lions now slightly torn at the hem, thin gold diadem on her head askew, gentle protective hand outstretched palm-up reaching toward the air in front of her, humanoid body proportions, kneeling on two legs on the cold stone floor, hovering just above her open palm one final newborn cat-kitten Olympian wrapped in white linen swaddling — Poseidon a tiny sea-blue-and-green kitten with sea-green eye-points — DISSOLVING into a long stream of golden particles and silver starlight stretching away from Rhea's palm toward the throne in the background, NO open mouth on the kitten (no screams), the kitten is turning into LIGHT and STARS, in the soft-focused background the dark silhouette of Cronus on the stone throne with his crown and beard visible only as outlines, his back partly turned, the trail of light entering his silhouette, mouth NOT visible (no swallowing), the absorption is shown only as light streaming into his shadow, ONE long warm-orange glow stretching from Rhea's palm to Cronus's silhouette, only Rhea, Cronus and Poseidon-kitten are humanoid figures in the frame, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, intimate sorrow cinematic lighting with single key light on Rhea's profile and the dissolving kitten and deep shadows everywhere else, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds, no open mouths, no screams

---

## Сцена 15 (sent_016 — «Рея больше не могла смотреть на это»)

**Краткое описание кадра.** Поворот в линии Реи. Тронный зал в фокусе на Рее: она стоит у дальней стены спиной к трону, тёмный профиль, лоб упёрт в холодную каменную стену, плечи опущены. Через щель в стене виден внешний пейзаж — горные склоны, ночное небо с далёкими звёздами Урана. На полу у её ног лежит крошечный белый свивальник (пустой). Без слёз, без крика — оцепенение и решение.

**Промпт:** silent mother turns her back on the throne against a cold stone wall, intimate vertical interior shot inside the dark stone throne hall, in the foreground Rhea the anthropomorphic bipedal cat titaness mother standing with her back to the camera facing a cold rough stone wall, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair braided over her shoulder loose and disheveled falling down her back, warm brown eyes (visible only in slight profile reflection) dry and frozen, dressed in a flowing ivory gown with gold embroidery of wheat sheaves and lions slightly torn, thin gold diadem on her head, both humanoid hands resting flat against the stone wall in front of her, her forehead pressed to the cold stone, shoulders slumped in silent decision, humanoid body proportions, standing upright on two legs, in front of her face a thin vertical crack in the wall shows a glimpse of the outside — distant mountain slopes and a night sky with TWO TINY COLD STAR-POINTS of the receded Uranus visible in the gap, at her feet on the stone floor one tiny empty white linen swaddling cloth lying flat (empty, the kitten gone), softly blurred in the deep background behind her the dark silhouette of the stone throne with the seated outline of Cronus barely visible, only Rhea and the throne silhouette are humanoid figures in the frame, NO humanoid figure for Uranus — only the two distant star-points mark him through the wall crack, no agony no screams no tears — frozen silent resolution, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, intimate cool cinematic lighting with deep shadow on the throne side and a thin cool moonlight beam from the wall crack across Rhea's profile, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 16 (sent_017 — «Она бежала от мужа и спряталась далеко в горах»)

**Краткое описание кадра.** Ночь. Узкая горная тропа на склоне. Рея бежит в тёплом плаще-накидке поверх платья, капюшон надвинут. Луна освещает тропу. Под ногами — серые валуны и кустарники. Вдалеке справа на горизонте — тёмный силуэт пика, в котором едва угадывается тронный зал (свет факелов из щели). Над всем — холодное ночное небо с далёкими звёздами Урана, что светят теплее обычного — будто провожают её.

**Промпт:** mother flees alone across a moonlit mountain path away from the throne, wide dynamic night scene, narrow rocky mountain footpath winding diagonally across the frame across a steep slope, Rhea the anthropomorphic bipedal cat titaness mother running along the path in mid-stride toward the far distance, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair tucked under a hood, warm brown eyes determined and forward-looking, dressed in a flowing ivory gown with gold embroidery beneath a warm dark-brown traveler's cloak with a deep hood pulled up over her head, thin gold diadem hidden under the hood, both humanoid hands gripping the front of her cloak tight, humanoid body proportions, running upright on two legs along the path, around her grey moonlit boulders and low scrubby mountain bushes, in the far background to the right a distant dark mountain peak with a faint warm orange glow from a small crack — the throne hall left behind, above her a cold night sky with TWO TINY DISTANT STAR-POINTS of the receded Uranus glowing slightly warmer than before as if quietly accompanying her flight, soft scattered raindrops falling from above as the eternal sky-tears continue, no other figures in the frame, only Rhea is a humanoid figure in the frame, NO humanoid figure for Uranus — only the two distant star-points, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dynamic night cinematic lighting with cool moonlight on the path and warm sky-tear raindrops, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 17 (sent_018 — «Когда она снова забеременела, она знала: этот ребёнок будет особенным»)

**Краткое описание кадра.** Тёплая, надёжная сцена. Внутри горной пещеры (далеко от тронного зала). Маленький костёр горит на каменном очаге. Рея сидит на пеньке у костра, плащ свалился на плечи, обе ладони на животе. Через ткань платья её живот мягко светится тёплым золотом — внутри уже растёт особенный ребёнок. Лицо Реи спокойное, лёгкая улыбка предвкушения. На стене пещеры — мерцающие тени от костра.

**Промпт:** sheltered pregnant mother glows warm with her unborn child at the hearth, intimate interior of a small mountain cave with rough natural stone walls and a low rocky ceiling, a small warm campfire burning on a flat stone hearth in the center foreground, Rhea the anthropomorphic bipedal cat titaness mother sitting on a low log seat beside the fire in three-quarter view, cream-and-pale-gold fur with warm peach undertones, long honey-gold hair braided over her shoulder now neat and softly lit by the firelight, warm brown eyes calm and serene with quiet anticipation, dressed in a flowing ivory gown with gold embroidery of wheat sheaves and lions, traveler's dark-brown cloak now fallen back from her shoulders, thin gold diadem on her head, both humanoid hands resting gently on her round pregnant belly, her belly glowing softly with a warm WARM GOLDEN INNER LIGHT visible through the fabric of her gown like a small heartbeat of the unborn — the first hint of baby Zeus inside her, gentle protective expression with a faint smile, humanoid body proportions, sitting upright on the log on two legs, soft flickering firelight casting warm orange shadows on the cave walls behind her, only Rhea is a humanoid figure in the frame, peaceful sanctuary atmosphere, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, warm intimate cinematic lighting with strong firelight key on Rhea and gold inner glow from her belly, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 18 (sent_019 — клиффхэнгер: «Внутри неё рос тот, кому суждено сбросить отца с трона. Его имя — Зевс»)

**Краткое описание кадра.** **Клиффхэнгер.** Очень крупный план: живот Реи в мягком фокусе занимает левую часть кадра, рука Реи на животе. **Через ткань платья отчётливо просвечивает золотистый силуэт-эмбрион сидящего котёнка** — это Зевс. Над «головой» силуэта — крошечные тонкие золотые искры (будущая молния). Силуэт не имеет лица, только поза. На правой стороне кадра — мягкое размытие пещерной стены с тенями от костра.

**Промпт:** unborn thunder-kitten silhouette glows inside the mother's belly as part two cliffhanger, ultra-tight intimate vertical composition, in the left half of the frame closeup of Rhea's pregnant cat-titaness belly visible through her flowing ivory gown with gold embroidery, the cream-and-pale-gold fur of her hand visible resting protectively on the belly, INSIDE the belly through the gown fabric a clear and unmistakable WARM GOLDEN GLOW shaped exactly like a TINY SEATED KITTEN SILHOUETTE — the unborn baby Zeus, the silhouette shows only the curled-up seated pose of a kitten without any face features (no eyes no mouth no whiskers — only the glowing pose-outline), small triangular ears at the top of the silhouette, ABOVE the kitten silhouette's head several faint tiny gold lightning sparks floating inside the belly glow — the foreshadowing of the future thunder bolt, the inner glow brighter and warmer than in the previous scene as if the unborn child is fully alive and aware, in the soft-blurred right half of the frame the warm flickering firelight of the cave hearth casting orange shadows on the rough stone wall, only Rhea is a humanoid figure in the frame, the unborn Zeus is NOT a fully drawn character — only a glowing seated pose-silhouette inside the belly, no embryo face, this is the first appearance of Zeus in the cycle and his identity is shown only through the silhouette and the sparks, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, ultra-intimate cinematic lighting with warm gold inner-belly glow dominating the frame and soft firelight on the right, no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats

---

## Сцена 19 (sent_020 — CTA: «Подпишись, чтобы узнать, как Зевс вернётся за братьями и сёстрами»)

**Краткое описание кадра.** **Финал-клиффхэнгер части — циклопы куют первую молнию Зевса.** Прямой визуальный «трейлер» ч.3: оружие, которым Зевс свергнет отца, кузнецы готовят прямо сейчас. Сцена замыкает символическое кольцо части: в сцене 4 Гея сама выковала из адаманта серп для Кроноса (против Урана), теперь её сыновья-циклопы куют из того же адаманта молнию для Зевса (против Кроноса) — **тот же металл, новое поколение, тот же исход**. Композиция — горная кузница в скальной пещере на рассвете, в кадре все три циклопа из сцены 8 (Бронт, Стероп, Арг) одновременно: **Бронт слева** замахивается тяжёлым железным молотом над наковальней, **Стероп в центре** удерживает на наковальне бронзовыми клещами свежевыкованную **адамантовую молнию-копьё** (тот же тёмно-серый металл, что у серпа Геи в сцене 4, но изогнутый зигзагом-молнией, лезвие раскалено оранжево-золотым), **Арг справа** на боковом верстаке шлифует второй зубец молнии, искры разлетаются. Один большой круглый глаз у каждого циклопа (Бронт — янтарный, Стероп — электрический белый, Арг — золотой) горит ярче от жара кузни. Над их головами в дальнем углу пещеры через скальное окно виден ночной мир — на скальном уступе вдалеке маленький силуэт юного Зевса-подростка молча наблюдает (короткие золотые волосы, белая туника, диадема), над ним высоко в звёздном небе **две далёкие тёплые звезды-глаза Урана** одобрительно мерцают. У основания каменной наковальни на полу проступают **золотисто-зелёные руны Геи** (мать-земля благословляет ковку, как когда-то благословила серп). Тёплый кузнечный оранжево-золотой свет заливает циклопов и наковальню, синие тени в углах пещеры. Центральный вертикальный коридор между молотом сверху и рунами снизу намеренно держится в спокойной тёплой темноте под караоке-плашку «ПОДПИШИСЬ → ЧАСТЬ 3 СКОРО».

**Промпт:** three cyclops cat brothers forging adamant thunder bolt in mountain cave smithy, dramatic vertical interior composition closing part two as a visual trailer for part three, inside a deep rocky mountain cave-forge at dawn warm orange-and-gold forge-light filling the lower two thirds of the frame from a glowing forge-pit on the right, in the centre foreground a large flat dark stone anvil with a half-forged curved jagged dark-grey adamant lightning-bolt spear resting on top of it — the same metal as the sickle from scene 4 forged by Gaia herself, now shaped into a zigzag thunder-bolt blade, the blade still glowing bright orange-red hot along its edges with cooler dark-grey adamant in the centre, on the LEFT of the anvil Brontes the Cyclops anthropomorphic bipedal cat blacksmith brother in mid-pose raising a heavy iron hammer high above his head ready to strike down on the glowing blade — massive muscular humanoid frame, short stone-slate-grey fur with soot streaks across the chest, bare muscular torso wrapped in a leather blacksmith apron tied with thick leather straps, bronze arm bracers on both forearms, ONE LARGE ROUND AMBER EYE in the middle of his forehead glowing bright with forge-light reflection (NO two eyes, ONE single round eye in the centre of the forehead — repeat: only one eye), humanoid body proportions, standing upright on two legs, cat muzzle firmly closed in focused concentration, hammer head catching the warm forge-light glint at the top of the swing, in the CENTRE just behind the anvil Steropes the Cyclops anthropomorphic bipedal cat blacksmith brother holding long bronze tongs firmly gripping the glowing adamant lightning-bolt blade steady on the anvil — same massive muscular humanoid frame, short stone-slate-grey fur with deeper soot streaks, leather blacksmith apron, bronze arm bracers, ONE LARGE ROUND ELECTRIC-WHITE EYE in the middle of his forehead burning bright with focused intensity (only one eye), humanoid body proportions, standing upright on two legs facing slightly forward, cat muzzle firmly closed, both his humanoid paws gripping the bronze tongs holding the lightning-bolt blade steady, on the RIGHT of the anvil at a slightly lower side workbench Arges the Cyclops anthropomorphic bipedal cat blacksmith brother shaping a second smaller zigzag fragment of the lightning-bolt with a smaller chisel and stone-hammer — same massive muscular humanoid frame, short stone-slate-grey fur, leather apron, bronze arm bracers, ONE LARGE ROUND GOLD EYE in the middle of his forehead glowing warm gold (only one eye), humanoid body proportions, standing upright on two legs in three-quarter back-view bent slightly over his workbench, cat muzzle firmly closed, small bright orange forge-sparks flying off his chisel-work and drifting upward, warm forge-sparks drift continuously upward across the entire frame from the anvil and from Arges's workbench like a slow ascending shower of orange embers, in the BACKGROUND right side a deep forge-pit with bright orange-red coals and a stone-and-leather bellows half-visible, in the BACKGROUND left side high up in the cave wall a small rocky window-opening reveals a deep blue twilight sky outside, on a distant rocky outcrop visible through that window a small silhouette of young Zeus the anthropomorphic bipedal cat youth-warrior in three-quarter back-view watching the forging from afar (ivory-and-pale-gold silhouette, short tousled golden hair, simple white linen short tunic with gold belt, thin twisted-gold diadem on his brow with a tiny lightning-bolt charm catching one warm spark of light, his future weapon being made for him as he watches — Zeus is rendered very small in scale visible only as a backlit silhouette at the cave-window NOT a foreground figure), high above the distant figure in the dark sky outside the cave-window TWO TINY DISTANT WARM STAR-POINTS of the receded Uranus visible glowing distinctly warmer than in any previous scene — the sky-grandfather watches the forging and silently blesses, on the rocky cave floor at the BASE of the stone anvil and along the cave-floor plates the faintly glowing golden-green primordial prophecy runes of Gaia from scene 12 visible etched into the rock now glowing brightly with the heat of the forging — the earth-mother is blessing the new weapon just as she once blessed the adamant sickle for Cronus in scene 4 (the visual rhyme is intentional — same metal, same maker, new wielder), Brontes and Steropes and Arges are all humanoid bipedal cat figures (the three cat brothers of the forge), young Zeus is a small distant humanoid silhouette at the cave-window, Gaia is NOT humanoid — only the floor-runes mark her, Uranus is NOT humanoid — only the two warm star-points mark him, ONE single round eye per cyclops (repeat: ONE eye each, NO two eyes on any cyclops), the central vertical column of the frame between Brontes's raised hammer above and the bright runes on the cave floor below intentionally kept visually quiet in warm forge-shadow to reserve a clean zone for an overlaid karaoke subscribe-call-to-action title plate in editing, no other figures, no monsters, no weapons besides the lightning-bolt being forged, highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, dramatic forge-workshop cinematic lighting (brilliant warm orange-and-gold forge-light dominating the centre of the frame from the glowing adamant blade on the anvil and from the forge-pit, deep cool blue shadow in the cave corners and along the cave-walls, cold pale-blue twilight light from the high cave-window backlighting Zeus's silhouette, warm gold pulse from the prophecy runes on the cave floor), no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats, no blood, no gore, no wounds, no open mouths, no screams

---

## Чек-лист перед запуском генерации (сверять перед каждым прогоном Flow)

Берём из [MYTH.md](../../../../MYTH.md) → шаг 7 + [GENEALOGY.md](../../../../GENEALOGY.md) → шаг 7. **ВНИМАНИЕ:** в этой части два класса персонажей — **абстрактные сущности-стихии с глазами** (Гея, Уран) и **антропоморфные коты** (Кронос, Рея, 11 титанов, циклопы, гекатонхейры, Афродита, 5 котят-олимпийцев). Чек-лист отдельный для каждого класса.

1. **Уникальный subject-маркер.** Первые 3–4 слова каждого `**Промпт:**` отличаются от соседних. Проверить:

   ```bash
   grep '^\*\*Промпт:\*\* ' "content/От Хаоса до Олимпа/часть_02_Власть_Кроноса/prompts/images.md" \
     | sed -E 's/^\*\*Промпт:\*\* ([^,]+),.*/\1/' \
     | sort | uniq -c | sort -rn
   ```

   Все строки должны быть с числом `1`.

2. **Класс «абстрактные сущности» — НЕТ humanoid.** Для Геи и Урана в каждом промпте должно быть `NO humanoid figure, NO body, NO hands, NO arms, NO mouth, NO face`. Никаких `humanoid body proportions` или `standing upright on two legs` для них.

3. **Класс «абстрактные сущности» — ЕСТЬ глаза.** Гея — `TWO LARGE GLOWING GOLDEN-GREEN EYES`. Уран — `TWO ICY PALE-BLUE GLOWING STAR-CLUSTER EYES` (после sent_007 → `TWO TINY DISTANT COLD STAR-POINTS`, потому что небо ушло выше).

4. **Класс «антропоморфные коты» — ЕСТЬ humanoid.** Для Кроноса, Реи, 11 титанов, Афродиты, 5 котят-олимпийцев — `humanoid body proportions, standing upright on two legs`. Если в промпте есть `hand`, `foot`, `paw` для котов — обязательно `humanoid hand` / `humanoid paw`.

5. **Класс «антропоморфные коты» — волосы упомянуты в каждой сцене.** Молодой Кронос (sent_001, 005, 006, 007) — `short shoulder-length dark-silver hair, CLEAN-SHAVEN no beard`. Кронос-узурпатор (sent_011-014) — `long dark-silver shoulder-length hair greying at the temples, full thick beard`. Рея — `long honey-gold hair braided over her shoulder`. Афродита — `long flowing cream-white hair covering her body`.

6. **Кронос — ВОЗРАСТ по сценам:**
   - Сцены 1, 5, 6 — **молодой подросток**: `CLEAN-SHAVEN no beard, simple dark-grey tunic, no cuirass, no skull medallions`.
   - Сцены 11-14 — **узурпатор-параноик**: `full thick beard, heavy bronze cuirass, skull-medallion belt, tall silver crown with sapphires`.

7. **Афродита — НЕТ обнажения.** В сцене 9 — `modestly covered by curling sea foam and long hair, NO nudity, NO explicit body — fully and modestly covered`. Капли в кадре — `silvery-pearl droplets, NOT red NOT blood`.

8. **Пять котят-олимпийцев — НЕТ глотания и НЕТ криков.** В сценах 13-14 — `kittens DISSOLVING into golden particles and silver starlight, NO open mouths on the kittens (no screams), NO open mouth on Cronus (no swallowing), NO blood, NO swallowing motion — the kittens TURN INTO LIGHT AND STARS`. Цвета котят: Гестия soft-beige cream, Деметра wheat-honey-gold, Гера cream-white + emerald, Аид dark-charcoal + silver, Посейдон sea-blue-green.

9. **Зевс-эмбрион — НЕТ лица.** В сценах 17-18 — `unborn baby Zeus visible only as a TINY SEATED KITTEN SILHOUETTE glowing warm gold inside Rhea's belly, no embryo face, only a glowing pose-silhouette, faint tiny gold lightning sparks above the silhouette`. Это не персонаж в кадре — это **внутреннее свечение** Реи.

10. **Уран — состояния по сценам:**
    - Сцены 1 (фон), 2 — **гневное** небо: тучи поперёк созвездий, низкий купол, глаза-скопления `narrowed and burning hostile`.
    - Сцена 6 — **разрезанное** небо: серебряная диагональная трещина-молния от серпа Кроноса, глаза `wide and shocked`.
    - Сцена 7 — **отрывается** и поднимается выше: глаза сжимаются до `TWO TINY DISTANT COLD STAR-POINTS far at the very top of the frame`.
    - Сцены 9-19 — **далёкие звёзды-глаза** на самом верху кадра, иногда `glowing slightly warmer` как сочувствие.

11. **Гея — состояния по сценам:**
    - Сцена 2 — **страдающая**: трещины тёплого света по холмам, циклопы и гекатонхейры наполовину вдавлены в почву, глаза `half-closed in pain`.
    - Сцена 3 — **решимость**: одинокая золотая слеза-ручеёк, глаз `burning brighter with primordial determination`.
    - Сцена 4 — **ковка**: серебристые искры, серп на каменной плите, глаза `gazing solemnly at the sickle`.
    - Сцена 5 — **наблюдает** выбор Кроноса: глаза в дальнем фоне `watching with grim approval`.
    - Сцена 7 — **облегчение**: трещины закрываются, глаза `gazing upward in serene primordial wonder`.
    - Сцена 8 — **тихая радость**: глаза `gazing toward the freed children with tired primordial joy`.
    - Сцены 10, 11 — **в фоне** скорбящая.
    - Сцена 12 — **пророческие руны**: глаз нет в кадре, голос Геи звучит через `ancient glowing golden-green primordial runes and prophecy symbols etched into the stone floor`.

12. **Стилевой каркас + негативы в каждом промпте.** `highly detailed pixel art, 9:16 vertical composition, modern detailed pixel art style, [LIGHTING], no text, no letters, no camera movement, NO humans, NO people, NO real four-legged cats`. Для сцен 6, 7, 13, 14, 19 добавляется ещё `no blood, no gore, no wounds, no open mouths, no screams` (где есть момент удара или поглощения). Для сцены 9 — `no nudity`.

13. **Смешанные сцены — границы класса.** В смешанных кадрах (2, 5, 6, 7, 8, 10-19) обязательно прописать «the sky and the earth are NOT humanoid», «only the [Cronus/Rhea/kittens/...] are humanoid figures in the frame». Иначе модель может прирастить Гее «лицо в холме» или Урану «фигуру в облаках». Особое внимание сценам 1 (Кронос под небом-Ураном) и 12 (Кронос на троне + руны Геи).

---

## Журнал

- **2026-05-17** — Файл создан. 19 промптов на 19 сцен (sent_001+002 = сцена 1, остальные sentence-в-сцену). Карточки персонажей дублированы в шапке HTML-комментарием. Subject-маркеры уникальны для всех 19 промптов. Чек-лист отдельный по двум классам персонажей.
- **2026-05-17** — **Поглощение детей Кроносом стилизовано через свет/звёзды** (сцены 13-14), без рта / без глотательного движения / без криков. Котёнок-олимпиец в свивальнике превращается в стрим золотых частиц и серебряного звёздного света, который втягивается в силуэт Кроноса как поглощаемая душа. Это решает платформенный риск (TikTok-бот ловит «глотать ребёнка» в визуале), и одновременно создаёт более мифический образ — Кронос не пожиратель в буквальном смысле, а узурпатор, поглощающий судьбы детей. В ч. 3 «Титаномахия» эти пятеро освобождаются обратным процессом — выходят из его силуэта как свет.
- **2026-05-17** — **Уран в этой части — четыре состояния стихии** (гневное → разрезанное → отрывающееся → далёкие звёзды плачут дождём). Свержение показано **не как смерть**, а как переход формы: купол отрывается от земли и поднимается выше, превращаясь в далёкие холодные звёзды. Этот образ работает как платформенно-безопасная замена «оскопления» из канонического мифа и одновременно поддерживает поэтический лейтмотив «дождь = слёзы Урана».
- **2026-05-17** — **Афродита (сцена 9) — обязательная защита от обнажения.** В промпте трижды повторено: `modestly covered by curling sea foam and her own long hair`, `NO nudity NO explicit body`, `fully and modestly covered by sea foam and long hair`. Капли от свергнутого Урана — `silvery-pearl droplets, NOT red NOT blood`, чтобы исключить интерпретацию модели как «кровь из неба».
- **2026-05-17** — **Зевс-эмбрион (сцены 17-18) — не персонаж, а свечение внутри Реи.** Без лица, без черт — только силуэт сидящей позы и крошечные золотые искры (будущая молния) над «головой». Это первое появление Зевса в цикле, но он ещё не родился — модель Flow не должна нарисовать котёнка как отдельную фигуру в кадре, только как glow inside the belly. В сцене 19 (CTA) Зевс уже появляется как backlit silhouette в полный рост — но в виде юноши на горизонте ч.3, не как родившийся младенец ч.2.
- **2026-05-19** — **Сцена 19 (CTA) переписана со «спокойного обещания» на зрелищный клиффхэнгер «секунда до удара»**. Молния-доминанта во весь кадр сверху вниз, Зевс шагает сквозь разорванное штормовое небо в позе удара (не приходит, а уже бьёт). Кронос на троне — глаза расширены в ужасе, корона Урана сползает, **по кирасе и трону ползёт та же зигзагообразная серебряная трещина**, которой он сам когда-то рассёк небо Урана (закрывает символическое кольцо «свергнувший отца будет свергнут сыном»). Три из пяти проглоченных котят-душ изнутри прижали ладошки к стенке его тела — вот-вот вырвутся. На полу снова светятся руны Геи из сцены 12 (земля подтверждает момент). Звёзды-глаза Урана впервые в части теплеют ярче — дед молча одобряет внука. Центральный вертикальный коридор затемнён под караоке-плашку «ПОДПИШИСЬ → ЧАСТЬ 3 СКОРО». Subject-маркер `thunder son arrives one` — уникален, не совпадает с другими 18 промптами части.
