# Орфей и Эвридика

<!--
Формат файла:
- `# Название` — заголовок мифа (используется для имени папки в content/)
- `## Сцена N (sent_NNN — шот M)` — порядковый номер визуального шота для
  imagefx_runner. Картинки сохранятся в images/review_images/scene_NN/vN.jpg.
- `**Текст:**` — закадровый текст (на русском).
- `**Промпт:**` — промпт для ImageFX / Nano Banana (одна строка, англ.).

Всего 27 предложений → 30 визуальных шотов на ~1:00–1:10 видео.
3 длинных предложения разбиты на 2 шота для динамики, остальные — 1 шот.

Маппинг sentence ↔ scene_NN (для последующего video.md и pyCapCut):
  sent_001 → scene_01                    (1 шот)  интро
  sent_002 → scene_02                    (1 шот)  Орфей играет на лире, замершие камни
  sent_003 → scene_03                    (1 шот)  звери приходят слушать
  sent_004 → scene_04                    (1 шот)  река останавливает течение
  sent_005 → scene_05                    (1 шот)  Эвридика слушает молча, улыбается
  sent_006 → scene_06                    (1 шот)  Орфей и Эвридика любят друг друга
  sent_007 → scene_07                    (1 шот)  свадьба, цветы, клятва
  sent_008 → scene_08 + scene_09         (2 шота) Эвридика в лугах + змея
  sent_009 → scene_10                    (1 шот)  Эвридика пала, не успев попрощаться
  sent_010 → scene_11                    (1 шот)  Орфей не смирился, решимость
  sent_011 → scene_12 + scene_13         (2 шота) спуск в пещеру + Стикс с Хароном
  sent_012 → scene_14                    (1 шот)  Цербер зарычал и замер от музыки
  sent_013 → scene_15                    (1 шот)  тени остановились
  sent_014 → scene_16                    (1 шот)  Аид опустил скипетр и слушает
  sent_015 → scene_17 + scene_18         (2 шота) Аид говорит «забирай» + условие про свет
  sent_016 → scene_19                    (1 шот)  Орфей идёт по тёмному коридору
  sent_017 → scene_20                    (1 шот)  тень/контур шагов сзади
  sent_018 → scene_21                    (1 шот)  он не слышит её голоса
  sent_019 → scene_22                    (1 шот)  не чувствует руки
  sent_020 → scene_23                    (1 шот)  свет впереди уже близко
  sent_021 → scene_24                    (1 шот)  он не выдержал — внутреннее напряжение
  sent_022 → scene_25                    (1 шот)  обернулся
  sent_023 → scene_26                    (1 шот)  Эвридика растворяется в тенях
  sent_024 → scene_27                    (1 шот)  пустой коридор — навсегда
  sent_025 → scene_28                    (1 шот)  Орфей на пороге света
  sent_026 → scene_29                    (1 шот)  с лирой
  sent_027 → scene_30                    (1 шот)  эхо последнего шёпота

Стилевой каркас (одинаковый во всех сценах):
highly detailed pixel art, 9:16 vertical composition, ancient Greek setting,
anthropomorphic bipedal cat characters (NOT real four-legged cats),
humanoid body proportions, standing/walking/gesturing like humans,
NO humans, NO people, NO real four-legged cats,
modern detailed pixel art style, warm cinematic lighting,
no text, no letters, no camera movement

КАРТОЧКИ ПЕРСОНАЖЕЙ (копировать в промпт каждой сцены дословно):

Orpheus = "Orpheus the gentle young Thracian musician hero, a slender lithe
slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful
melancholic deep-amber eyes and a youthful clean-shaven face, two perked
dark-gray cat ears tipped with white, a distinct gray-and-white cat muzzle,
a long graceful gray cat tail with a white tip, bipedal standing upright on
two legs like a human with humanoid body proportions, long wavy raven-black
hair held back by a thin gold-and-laurel circlet, wearing a flowing
pale-cream Greek chiton draped over one shoulder belted with a thin braided
gold cord, a soft sky-blue mantle with golden hem trim across his back,
leather sandals laced up his calves, carrying a polished golden lyre with
seven strings stretched across two curved tortoiseshell horns inlaid with
mother-of-pearl"

Eurydice = "Eurydice the gentle wood-nymph bride, a graceful slender
pale-rose-cream-and-white calico anthropomorphic cat character with large
warm honey-brown eyes and delicate features, two small perked white-and-
cream cat ears, a small pink-and-white cat muzzle, a long fluffy cream-and-
white cat tail, bipedal standing upright on two legs with humanoid body
proportions, long wavy strawberry-blonde hair flowing down her back
interwoven with small white wildflowers, wearing a flowing soft-white-and-
pale-blush Greek peplos with subtle gold-thread embroidery of olive leaves
at the hem, a thin gold belt at her waist, leather sandals, a delicate gold
pendant at her throat shaped like a small lyre"

Hades = "Hades the somber lord of the underworld, a tall imposing solid-
dark-charcoal-gray anthropomorphic cat character with cold piercing pale-
violet eyes that glow faintly and a sharp neatly trimmed dark beard, two
erect dark-gray cat ears, a stern dark-gray cat muzzle, a long dark cat
tail held still, bipedal standing upright on two legs with humanoid body
proportions, wearing a heavy deep-black-and-midnight-purple royal robe with
silver embroidered pomegranate and asphodel motifs, layered draped folds
over both shoulders, a wide black belt with onyx clasps, a tall ornate
dark-iron crown set with three deep-purple gemstones on his head, holding
a long ornate dark-iron scepter topped with a carved skull and pomegranate
motif, faint pale-blue-and-purple ghostly aura around his figure"

Cerberus = "Cerberus the three-headed feline guardian of the underworld,
a massive towering anthropomorphic cat-creature with shaggy charcoal-black-
and-deep-red fur, three identical cat heads on three thick muscular necks
growing from one set of broad shoulders each head with two erect black cat
ears a fierce black cat muzzle with bared fangs and smoldering glowing
crimson-red feline eyes with vertical slit pupils, a huge muscular humanoid
body bipedal standing upright on two thick humanoid legs body upright not on
four legs, broad muscular shoulders with a thick dark mane around his necks
like a lion's, a long thick dark cat tail tipped with dark serpent-scales,
wearing only heavy iron-and-bronze chains across his chest like a collar,
no weapons just massive humanoid cat-paw hands with sharp claws — STRICTLY
a feline cat character with three cat heads and bull-like muscular humanoid
build, NOT a real four-legged cat, NOT a real four-legged dog, but a unique
three-headed cat-Cerberus keeping clear cat muzzles and cat ears on all
three heads"

Charon = "Charon the silent ferryman of the dead, a gaunt tall cloaked
anthropomorphic cat character with sunken pale-glowing-yellow-green eyes
and a hollow gray cat muzzle, two erect tattered gray cat ears, a long
ragged gray cat tail, bipedal standing upright on two legs with humanoid
body proportions, hidden under a heavy ragged hooded dark-gray robe with
torn hem reaching to the deck of his boat, a long wooden punting pole in
his bony humanoid hands, a single small dim lantern hanging from the prow"

Snake = "a single slender real ancient-Greek garden serpent, a thin
silver-and-pale-green-scaled snake winding through the meadow grass —
strictly a real snake here as it is a wild-creature plot device — keeping
a small simple natural snake form" (только в Сцене 9)

Разнообразие окружения: Фракийские холмы с оливковыми рощами и кипарисами,
зелёные луга с белыми и розовыми полевыми цветами, мраморный греческий
свадебный павильон с белыми колоннами увитыми плющом, каменистые тропы
вдоль ручьёв с водопадами, зеркальные горные озёра, тёмная пещера-вход
в подземный мир с висящими корнями и кристаллами, мрачная река Стикс
с туманом и серыми водами, серые асфоделовые поля царства мёртвых
с одинокими белыми асфоделовыми цветами, базальтовый чёрный тронный
зал Аида с колоннами из обсидиана и фресками гранатов и асфоделей,
длинный изогнутый каменный коридор-туннель ведущий вверх к свету,
далёкое тёплое золотое сияние выхода в мир живых. Варьировать ракурсы
(крупный план, средний, общий, сверху, низкий ракурс, силуэт против неба
или света) и освещение (золотое утро/полдень с косыми лучами/закатное
тепло/ночь со звёздами/тусклый зеленовато-синий свет подземного мира/
факельный/свет от лиры/далёкий тёплый свет выхода).

КРИТИЧНО для сцен с движением (Орфей идёт по коридору, шаги Эвридики
сзади, Орфей оборачивается, Цербер замирает) — явно прописывать
человеческую позу: "human-like walking pose, body upright not on four legs",
"humanoid arms holding the lyre", "humanoid legs striding upright". В
сценах 19, 20, 21, 22, 25 герои в активном движении — без явной позы они
скатываются в обычных кошек на четвереньках.

ОГРАНИЧЕНИЯ ПЛАТФОРМ (TikTok / YouTube Shorts):
- Укус змеи (сцена 9) — БЕЗ КРОВИ, БЕЗ РАН. Змея только подбирается к
  лодыжке Эвридики или скользит мимо в траве, без момента укуса
  крупным планом. Negative: no blood, no gore, no wounds, no fangs in skin.
- Смерть Эвридики (сцена 10) — НЕ показывать тело лежащим на земле.
  Сцена — белые лепестки и пыльца разлетаются на ветру, упавшая корзинка
  с цветами, лёгкое нежное растворение её фигуры в полупрозрачный
  туман-силуэт уходящий вверх. Без агонии, без раны, без падения.
- Растворение Эвридики в тенях (сцена 26) — мягкое исчезновение в
  частицы лёгкого тумана, призрачные звёздочки и пыльца, удлинённая рука
  тянется к Орфею в последний раз, без ужаса в кадре. Negative: no horror,
  no gore, no scream-distorted face.

ВИЗУАЛЬНЫЕ МОТИВЫ:
- Золотая лира — главный лейтмотив (сцены 2, 3, 4, 11, 12, 13, 14, 19, 25, 29, 30),
  струны излучают мягкое золотое сияние когда Орфей играет
- Свет конца туннеля — ключевой мотив второй половины (сцены 17, 18, 23,
  25, 28, 30), тёплый золотой против холодного фиолетово-синего подземного мира
- Цветочные мотивы — в живом мире (свадьба, луга): белые ромашки,
  розовые анемоны, маки, оливковые ветви
- Асфоделевые цветы — в подземном мире (одинокие тонкие белые цветы
  на серых полях, символ царства мёртвых)
- Тонкая бледно-золотая нить света между Орфеем и Эвридикой — невидимая
  связь, едва намеченная как лёгкое свечение в сценах после их встречи
  и в сценах коридора (намекая на её присутствие за спиной)
- Гранат — личный символ Аида (на скипетре, на фресках тронного зала,
  падает с дерева в финальном кадре как метафора утраты)

Кошачьи декоративные мотивы (статуи котов, вазы с котами, фрески с котами)
— уместны в свадебном павильоне на земле и в живых сценах с цветами, но
НЕ в подземном мире. В царстве Аида декор оформлен гранатами, асфоделем,
скелетоподобными мотивами, обсидиановыми колоннами — без принудительных
кошачьих деталей. Главные герои — всегда коты, но окружение Аида
подчёркнуто чужое и холодное.
-->

## Сцена 1 (sent_001)

**Текст:** Орфе́й и Эвриди́ка. Миф за минуту.

**Промпт:** highly detailed pixel art, 9:16 vertical, epic cinematic title shot, lyrical reaching composition with two figures separated by a vast gulf of light and shadow, on the left half stepping out of warm pale-gold sunbeams Orpheus the gentle young Thracian musician hero a slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful melancholic deep-amber eyes two perked dark-gray cat ears tipped with white a distinct gray-and-white cat muzzle a long graceful gray cat tail bipedal standing upright on two legs with humanoid body proportions, long wavy raven-black hair held back by a thin gold-and-laurel circlet, wearing a flowing pale-cream Greek chiton with a soft sky-blue mantle, his polished golden lyre held high in his humanoid right hand its seven strings glowing with soft golden light, his other humanoid hand outstretched longingly across the gulf of darkness toward the right side, on the right half fading into deep cobalt-purple shadow Eurydice the gentle wood-nymph bride a graceful slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes and delicate features two small perked white-and-cream cat ears a small pink-and-white cat muzzle a long fluffy cream-and-white cat tail bipedal standing upright on two legs with humanoid body proportions, long wavy strawberry-blonde hair interwoven with small white wildflowers, wearing a flowing soft-white-and-pale-blush Greek peplos, her humanoid right hand reaching back toward Orpheus already half-translucent her body slowly dissolving from her feet upward into wisps of pale lavender mist and tiny white flower petals, between them a vertical seam of warm gold meeting cold violet shadow split by a single thin glowing pale-gold thread of light connecting their reaching hands, in the background distant Greek countryside with cypress trees and white columns dissolving into a starless underworld of asphodel fields, charged elegiac mythological atmosphere, contrasting warm gold and cold violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 2 (sent_002)

**Текст:** Орфе́й играл на лире так, что замирали даже камни.

**Промпт:** highly detailed pixel art, 9:16 vertical, lyrical wide medium shot of a sun-dappled Thracian hillside meadow at golden afternoon, Orpheus the gentle young Thracian musician hero a slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful melancholic deep-amber eyes two perked dark-gray cat ears tipped with white a distinct gray-and-white cat muzzle a long graceful gray cat tail bipedal sitting upright on a smooth gray boulder with humanoid body proportions in a human-like seated cross-legged pose body upright not on four legs, long wavy raven-black hair held back by a thin gold-and-laurel circlet, wearing a flowing pale-cream Greek chiton with a soft sky-blue mantle and leather sandals, cradling his polished golden lyre across his lap his humanoid left hand on the curved tortoiseshell horns his humanoid right hand mid-pluck of the seven strings, soft golden ripples of music visible as concentric pale-gold circles radiating outward from the lyre, around him scattered ancient Greek standing stones and large gray boulders are anthropomorphized only with tiny faint glowing eyes-of-light and gentle smile-curves of light barely traced on their surfaces — clearly inanimate stones listening — frozen in attentive stillness, soft tall meadow grass with white wildflowers swaying gently, distant cypress trees and olive groves on rolling hills behind, a few clouds in a tender blue sky, peaceful enchanted mythological atmosphere, warm gold and soft green color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 3 (sent_003)

**Текст:** Звери приходили слушать.

**Промпт:** highly detailed pixel art, 9:16 vertical, charming wide medium shot of the same sunlit Thracian meadow continuing from the previous scene at golden afternoon, Orpheus the slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal seated upright on his boulder with humanoid body proportions in a calm human-like seated pose body upright not on four legs in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, his humanoid hands gently strumming the polished golden lyre soft pale-gold concentric ripples of music radiating outward, gathered around the boulder a small assembly of real natural Greek-countryside wild animals — strictly real natural creatures here as they are forest animals drawn to his music — a curious natural red fox sitting on its haunches with ears perked, a real four-legged tawny young deer with delicate antlers standing motionless with wide attentive eyes, a real four-legged spotted wild hare crouched alert, a small real natural badger peeking from the meadow grass, a real natural owl perched on a low olive branch with eyes closed in bliss, a real natural small songbird on a stone watching intently, a real garden tortoise slow at his feet, all the animals real natural wildlife of Greek hills NOT anthropomorphic and NOT cats — only Orpheus is the anthropomorphic bipedal cat character, soft golden afternoon light filtering through olive leaves, peaceful enchanted nature-stilled atmosphere, warm gold and soft green color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 4 (sent_004)

**Текст:** Реки останавливали течение.

**Промпт:** highly detailed pixel art, 9:16 vertical, wonder-struck wide low-angle shot of a small clear Greek mountain river running through a moss-covered stone gorge at golden hour, Orpheus the slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal standing upright on a flat stone at the river's edge with humanoid body proportions in a calm human-like standing pose body upright not on four legs, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, his humanoid hands gently plucking his polished golden lyre raised before him, soft pale-gold concentric ripples of music spreading outward across the water surface, the river itself visibly frozen mid-flow its silver-blue water arrested in suspended ribbons and droplets the rapids and small waterfall in mid-cascade halted in shimmering glass-like stillness fish (real natural Greek river fish, not anthropomorphic) hanging motionless in the water column with tails mid-swish, water spray suspended as tiny crystal droplets in the air over moss-covered rocks, weeping willows and tall reeds at the river edge bending toward the sound, a single dragonfly hovering motionless mid-air, soft golden god rays piercing through the gorge canopy, magical wonder atmosphere of nature paused, warm gold and silver-blue color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 5 (sent_005)

**Текст:** И только Эвриди́ка слушала молча — улыбаясь.

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate tender medium shot in the same sunlit meadow at golden afternoon partly hidden among tall meadow grass and white wildflowers, Eurydice the gentle wood-nymph bride a graceful slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes softened with deep affection two small perked white-and-cream cat ears a small pink-and-white cat muzzle curved into a soft tender smile a long fluffy cream-and-white cat tail bipedal sitting upright on a low mossy log with humanoid body proportions in a human-like seated pose body upright not on four legs her humanoid hands clasped softly in her lap, long wavy strawberry-blonde hair interwoven with small white wildflowers flowing over her shoulder, wearing a flowing soft-white-and-pale-blush Greek peplos with subtle gold-thread olive-leaf embroidery, a thin gold belt and a small lyre-shaped gold pendant at her throat catching the light, her cat ears slightly tilted forward listening with rapt quiet attention, in the soft-focused background just visible through the wildflowers Orpheus the slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal humanoid seated on his boulder playing his golden lyre concentric pale-gold music ripples around him, faint pale-gold pollen and tiny dandelion seeds drifting in the warm slanted afternoon light between them, butterflies fluttering nearby, soft warm golden god rays through the meadow, romantic awe-struck quiet atmosphere, warm gold and soft pink-cream color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 6 (sent_006)

**Текст:** Они любили друг друга.

**Промпт:** highly detailed pixel art, 9:16 vertical, romantic warm medium shot at the edge of a Greek olive grove at golden sunset, Orpheus the slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal standing upright on two legs with humanoid body proportions in his pale-cream Greek chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet his polished golden lyre slung over his back on a leather strap, leaning forehead-to-forehead with Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes two small perked white-and-cream cat ears a small pink-and-white cat muzzle a long fluffy cream-and-white cat tail bipedal standing upright on two legs with humanoid body proportions in her flowing soft-white-and-pale-blush Greek peplos long wavy strawberry-blonde hair flowing down her back interwoven with small white wildflowers, his humanoid hands cupped tenderly around hers her humanoid hands resting lightly on his chest both of them with eyes closed and soft smiles, their cat tails curving gently together at their feet, around them silver-leafed olive trees with twisted trunks scattered white wildflowers and trailing wild jasmine, a small natural ancient Greek shrine of weathered stone draped with a wildflower garland in the background, low warm golden sunset light bathing them in a soft amber halo with long stretched shadows, a flock of swallows drifting through the rose-and-gold sky behind, gentle deep love atmosphere, warm gold and soft rose color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 7 (sent_007)

**Текст:** Свадьба, цветы, обещания на всю жизнь.

**Промпт:** highly detailed pixel art, 9:16 vertical, joyful celebratory wide medium shot of an outdoor Greek wedding ceremony in a marble pavilion of slender white columns wrapped in trailing ivy and pink-and-white wildflower garlands at golden afternoon, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes a gray-and-white cat muzzle bipedal standing upright on two legs with humanoid body proportions in a clean fresh white-and-gold ceremonial Greek chiton with a richer gold-trimmed sky-blue mantle a wreath of olive leaves and white flowers in his raven-black hair his polished golden lyre slung across his back, holding both humanoid hands of Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character bipedal humanoid body proportions in a flowing pure white-and-blush Greek bridal peplos with rich gold-thread embroidered hem a longer wedding-veil of sheer pale-gold fabric draped over her strawberry-blonde hair with a wreath of white roses and orange blossoms her face radiant with a wide gentle smile her cat tail held high with joy, between them a small ceremonial bronze altar with a low flame, a smiling priestess cat character with humanoid body proportions in cream robes raising a humanoid hand in blessing in the background, around the pavilion a small joyful crowd of bipedal anthropomorphic Greek wedding-guest cat characters of varied tabby and calico fur in colorful chitons humanoid body proportions throwing handfuls of white flower petals and rose petals into the air the petals filling the foreground, a small gold-cat-statue motif on a column capital, oil-lamp lights starting to flicker as the sun lowers, low warm golden sunset light streaming between the columns casting long warm rays, distant Greek hills with cypress trees, joyful sacred celebration atmosphere, warm gold and rose-pink-and-white color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 8 (sent_008 — шот 1)

**Текст:** Но в день торжества Эвриди́ка ушла в луга — и змея настигла её.

**Промпт:** highly detailed pixel art, 9:16 vertical, lyrical wide medium shot of a sunlit summer meadow on a Greek hillside at golden hour, Eurydice the gentle slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes two small perked white-and-cream cat ears a small pink-and-white cat muzzle a long fluffy cream-and-white cat tail bipedal walking upright on two legs through tall meadow grass with humanoid body proportions in a human-like walking pose body upright not on four legs, still in her white-and-pale-blush bridal peplos with the gold-thread olive-leaf hem her wedding wreath of white roses still in her strawberry-blonde hair a small woven wicker basket of fresh-picked white wildflowers and herbs in her humanoid right hand the basket overflowing with petals, her humanoid left hand brushing softly through the grass tips, her face turned upward toward the warm sun with a gentle peaceful smile, butterflies swirling around her, the meadow filled with white daisies pink anemones and red poppies stretching to distant hills, the marble wedding pavilion with its white columns and trailing flower garlands tiny in the far background partially hidden by olive groves, a flock of small white birds rising into the warm sky, the long warm slanted golden afternoon light wrapping her figure in a soft halo, peaceful unsuspecting atmosphere, warm gold and rose-cream color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 9 (sent_008 — шот 2)

**Текст:** Но в день торжества Эвриди́ка ушла в луга — и змея настигла её.

**Промпт:** highly detailed pixel art, 9:16 vertical, tense low-angle close-up shot in the meadow grass at golden hour, the camera angle low among tall green grass blades and white daisy flowers, Eurydice's leather-sandaled humanoid foot just visible at the upper edge of the frame stepping forward gently the hem of her white-and-pale-blush bridal peplos brushing the grass, in the foreground a single slender real natural ancient-Greek garden serpent a thin silver-and-pale-green-scaled snake — strictly a real natural snake here as it is a wild creature plot device — gliding through the grass between the daisies its forked tongue out its small head subtly raised toward her humanoid ankle, the snake clearly only emerging from the grass its body partly hidden in the green never touching her cream-and-white fur in this shot, dramatic late-afternoon golden light cutting low through the grass blades casting long thin shadows of grass across her humanoid foot, a single startled butterfly lifting away in alarm in the upper background, a faint coil of soft pale lavender mist already starting to curl out of the grass at the edges of the frame foreshadowing her fading, no blood no gore no wounds no fangs in skin, ominous quiet sudden-tragedy atmosphere, warm gold turning to subtle violet at the edges, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 10 (sent_009)

**Текст:** Она пала, не успев попрощаться.

**Промпт:** highly detailed pixel art, 9:16 vertical, mournful wide medium shot of the same sunlit meadow now in fading dusk light, in the foreground at the center of the bent-down grass an overturned woven wicker wedding-basket lies on its side, a scattering of white roses orange-blossom petals and white wildflowers spilling from the basket into the grass, a single small lyre-shaped gold pendant on a thin gold chain — Eurydice's pendant — lying delicately in the petals catching the last warm light, her wedding wreath of white roses fallen softly nearby, no body of any cat character is shown in the frame, instead rising softly from the spot above the basket a translucent pale-lavender-and-cream ghostly silhouette of Eurydice — barely visible only as a gentle feminine bipedal cat-shaped wisp of mist with a long fluffy tail and the suggestion of two small cat ears — slowly drifting upward and dispersing into pale flower petals and pollen carried on the wind, in the soft-focused mid-distance Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with humanoid body proportions in his white-and-gold ceremonial chiton kneeling on one humanoid knee in the grass with his back turned three-quarters away one humanoid hand pressed to his cat muzzle his shoulders sagging his polished golden lyre fallen beside him in the grass, the marble wedding pavilion empty in the deeper background, the sky a deep rose-and-violet sunset with the first stars appearing, a flock of birds rising silently, no blood no gore no wounds no body, profoundly mournful gentle atmosphere, soft rose-violet and gold color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 11 (sent_010)

**Текст:** Орфе́й не смирился.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic low-angle medium close-up shot at the rocky entrance to a vast dark cave in the side of a cliff at deep night, Orpheus the slender lithe slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes now blazing with raw determined grief two perked dark-gray cat ears flattened back a gray-and-white cat muzzle set in resolve a long gray cat tail held stiffly bipedal standing upright on two legs with humanoid body proportions in a human-like braced standing pose body upright not on four legs, still in his now travel-stained white-and-gold ceremonial chiton with sky-blue mantle long wavy raven-black hair beneath an olive-leaf wreath now slightly askew (the wedding wreath replacing his usual gold-and-laurel circlet for these grief-driven scenes), his polished golden lyre held tightly in both his humanoid hands across his chest the strings catching faint light, his face turned upward facing the dark gaping cave mouth above him, behind him on the rocks Eurydice's small lyre-shaped gold pendant clenched on a chain in his fingers along with the lyre, a deep cobalt-blue night sky behind with a sliver moon and distant stars over jagged Greek cliffs, the gaping cave entrance filled with deep purple-black shadow exhaling thin coils of pale lavender mist, a single small white asphodel flower growing from a crack in the rocks at his feet — first hint of the underworld near the surface, scattered fallen white wedding-petals around his sandaled feet, distant cypress trees silhouetted against the sky, fierce sorrowful resolve atmosphere, deep cobalt and pale-amber color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 12 (sent_011 — шот 1)

**Текст:** Он взял лиру и спустился туда, откуда не возвращаются — в царство Аи́да.

**Промпт:** highly detailed pixel art, 9:16 vertical, atmospheric wide low-angle shot of a long descending staircase of cracked black-basalt steps spiraling down into the mouth of the underworld cave, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal walking downward upright on two legs with humanoid body proportions in a human-like striding pose body upright not on four legs body upright his back to camera and three-quarters profile, in his travel-stained pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, polished golden lyre cradled across his chest in both his humanoid hands, his humanoid feet stepping carefully on the basalt steps, the rough stone walls of the cave passage closing in on either side carved with faint relief friezes of pomegranates and asphodels, hanging gnarled tree roots dripping pale lavender mist from the ceiling, scattered glowing pale-purple crystals embedded in the walls casting cool eerie light, a few small bone fragments and discarded coins on the steps, far below at the bottom of the staircase a faint pale-green ghostly glow hinting at the river beyond, the warm golden world above visible only as a tiny shrinking circle of light far above his head, ominous descending atmosphere, deep purple cold-violet and pale-green color palette with the small distant warm yellow circle above, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 13 (sent_011 — шот 2)

**Текст:** Он взял лиру и спустился туда, откуда не возвращаются — в царство Аи́да.

**Промпт:** highly detailed pixel art, 9:16 vertical, eerie atmospheric wide medium shot at the misty bank of the river Styx deep in the underworld, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal standing upright on two legs at the dark stone bank with humanoid body proportions in a human-like standing pose body upright not on four legs, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, holding his polished golden lyre raised in his humanoid left hand his humanoid right hand offering a small gold coin obol toward the boatman, before him on the slow oily black-and-pale-green water of the river Styx a long narrow flat-bottomed wooden funeral boat drifting toward him steered by Charon the silent ferryman of the dead a gaunt tall cloaked anthropomorphic cat character with sunken pale-glowing-yellow-green eyes and a hollow gray cat muzzle two erect tattered gray cat ears a long ragged gray cat tail bipedal standing upright at the stern of his boat with humanoid body proportions hidden under a heavy ragged hooded dark-gray robe a long wooden punting pole in his bony humanoid hands a single small dim lantern hanging from the prow casting weak greenish light, dim translucent silhouettes of other passing souls drift in the water around and beyond the boat as ghostly bipedal cat-shaped wisps, the far bank of the river fades into thick pale-violet fog hinting at the asphodel fields beyond, blackened gnarled cypress trees on the near bank, no warm light at all only cold pale-green-and-violet glow, ominous threshold-of-death atmosphere, deep teal-violet and pale-green color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 14 (sent_012)

**Текст:** Це́рбер зарычал — и замер от музыки.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic medium shot in a vast cavernous black-stone gateway hall of the underworld lit by cold pale-blue ghostly torches, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal standing upright on two legs with humanoid body proportions in a calm but tense human-like standing pose body upright not on four legs, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, his polished golden lyre raised before him both his humanoid hands plucking the seven strings, soft pale-gold concentric ripples of music radiating outward through the cold gloom illuminating the dust motes in warm honey-yellow light, before him crouching mid-lunge but utterly frozen Cerberus the three-headed feline guardian of the underworld a massive towering anthropomorphic cat-creature with shaggy charcoal-black-and-deep-red fur three identical cat heads on three thick muscular necks growing from one set of broad shoulders each head with two erect black cat ears a black cat muzzle and smoldering crimson-red feline eyes with vertical slit pupils a huge muscular humanoid body bipedal upright on two thick humanoid legs body upright not on four legs broad muscular shoulders thick dark mane around his necks like a lion's a long thick dark cat tail tipped with serpent-scales heavy iron-and-bronze chains across his chest like a collar massive humanoid cat-paw hands with sharp claws frozen mid-swing, all three of his cat muzzles open mid-roar but visibly transitioning — the leftmost head still snarling fangs bared the center head softening with confused calm eyes half-closing the rightmost head completely calmed cat ears perking forward in awe his crimson-red eyes mellowing to a warm orange — caught in the moment of being subdued by music, his massive feline silhouette fills the doorway behind him a vast bronze gate carved with pomegranate and asphodel reliefs, scattered bones on the cold stone floor, mythic awestruck moment atmosphere, cold pale-blue and pale-gold music-light contrasting color palette, NO humans, NO people, NO real four-legged dogs, NO real four-legged cats, only the unique three-headed cat-Cerberus keeping clear cat muzzles and cat ears, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 15 (sent_013)

**Текст:** Тени остановились.

**Промпт:** highly detailed pixel art, 9:16 vertical, eerie atmospheric wide shot of the asphodel fields of the underworld a vast plain of thin pale-white asphodel flowers swaying in cold wind under a starless deep-purple-black sky, scattered across the plain a multitude of translucent pale-blue-and-violet ghostly silhouettes of bipedal anthropomorphic cat-shaped wandering shades — varied shapes hinted gently as dim cat outlines with two cat ears a faint cat muzzle a long tail and humanoid body proportions — that have ALL come to a complete halt mid-step their cat ears tilted toward the source of the music their translucent humanoid hands raised softly to their muzzles in awe their long tails frozen in soft curves, in the foreground center Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal walking upright on two legs with humanoid body proportions in a human-like walking pose body upright not on four legs in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, his polished golden lyre held mid-pluck his humanoid hands on the seven strings soft pale-gold concentric ripples of music radiating outward across the plain illuminating the shades, the radiating golden ripples gently warming nearby asphodel flowers to a soft amber glow contrasting the cold violet of the rest, in the far misty distance a colossal black palace of obsidian columns silhouetted against the dark sky — Hades's hall, profound otherworldly stillness atmosphere, cold pale-violet and pale-blue color palette with warm golden music-light radiating from Orpheus, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 16 (sent_014)

**Текст:** Даже сам Аи́д опустил скипетр и слушал.

**Промпт:** highly detailed pixel art, 9:16 vertical, awe-inducing medium-wide low-angle shot of the colossal black throne hall of Hades — a vast cathedral-like chamber of towering obsidian-black columns inlaid with dark-silver pomegranate and asphodel reliefs lit by cold pale-blue-and-violet ghostly braziers, on a tall raised dais of dark-iron and onyx stairs at the far end Hades the somber lord of the underworld a tall imposing solid-dark-charcoal-gray anthropomorphic cat character with cold piercing pale-violet eyes that glow faintly and a sharp neatly trimmed dark beard two erect dark-gray cat ears a stern dark-gray cat muzzle a long dark cat tail held still bipedal seated upright on a colossal throne of carved dark-iron and obsidian topped with a stylized cat-skull motif at its peak with humanoid body proportions in a relaxed yet attentive seated pose body upright not on four legs, in his heavy deep-black-and-midnight-purple royal robe with silver embroidered pomegranate and asphodel motifs, his tall ornate dark-iron crown with three deep-purple gemstones tilted slightly forward, his long ornate dark-iron scepter — topped with a carved skull and pomegranate motif — visibly lowered from its formal upright position now resting tip-down on the floor of the dais beside the throne, both his humanoid hands now relaxed open in his lap his cat ears tilted forward in genuine listening his cold violet eyes softened almost wet with unexpected feeling, in the foreground far below the dais Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal humanoid body proportions in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet standing upright on two legs facing the throne his back partly to camera his polished golden lyre raised playing the seven strings soft pale-gold concentric ripples of music radiating up the dais toward the throne, beside Hades's throne a smaller paler throne empty — Persephone's place, the warm gold music-light pushing back the cold violet gloom of the hall, mythic awestruck reverent atmosphere, cold pale-violet and warm pale-gold color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 17 (sent_015 — шот 1)

**Текст:** «Забирай её, — сказал владыка тьмы. — Но одно условие: иди вперёд и не оборачивайся, пока не выйдешь к свету. Иначе потеряешь её навсегда».

**Промпт:** highly detailed pixel art, 9:16 vertical, solemn medium shot in the same colossal black throne hall of Hades from a slightly closer angle, Hades the somber lord of the underworld the tall imposing solid-dark-charcoal-gray anthropomorphic cat character with cold piercing pale-violet eyes a sharp neatly trimmed dark beard two erect dark-gray cat ears a stern dark-gray cat muzzle a long dark cat tail bipedal standing upright on two legs at the foot of his throne with humanoid body proportions in a formal commanding pose body upright not on four legs, in his heavy deep-black-and-midnight-purple royal robe with silver embroidered pomegranate motifs and his tall ornate dark-iron crown, holding his long ornate dark-iron scepter horizontally across his chest in both his humanoid hands as if formally pronouncing a verdict his cat muzzle parted in mid-speech his cold violet eyes serious, behind Hades on a step above slightly translucent and pale stands the gentle silhouette of Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character bipedal humanoid body proportions in her now pale-translucent white-and-blush peplos her two perked white-and-cream cat ears her small pink-and-white cat muzzle her long fluffy cream-and-white cat tail long wavy strawberry-blonde hair flowing down her back interwoven with small white wildflowers (now slightly translucent like the rest of her) her humanoid hands clasped softly at her chest her honey-brown eyes hopeful and tender — she is partly ghostly pale-violet but recognizable, in the foreground three-quarters back to camera Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal humanoid body proportions in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet kneeling on one humanoid knee in a respectful listener's pose body upright not on four legs his polished golden lyre at his side his humanoid hands clasped before him his cat ears tilted forward listening intently, faint pale-blue-and-purple ghostly aura around Hades, cold pale-violet and warm pale-gold light from Orpheus's lyre at his side, weighty moment-of-mercy atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 18 (sent_015 — шот 2)

**Текст:** «Забирай её, — сказал владыка тьмы. — Но одно условие: иди вперёд и не оборачивайся, пока не выйдешь к свету. Иначе потеряешь её навсегда».

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic illustrative medium shot still in the throne hall of Hades, Hades the tall imposing solid-dark-charcoal-gray anthropomorphic cat character with cold pale-violet eyes a sharp dark beard two erect dark-gray cat ears a stern dark-gray cat muzzle bipedal standing upright on two legs with humanoid body proportions in his deep-black-and-midnight-purple royal robe and tall dark-iron crown, his long ornate dark-iron scepter raised diagonally his humanoid right arm extended pointing emphatically toward a dark archway on the far wall of the hall — at the end of which a long curved stone tunnel can be seen disappearing into upward darkness with the faintest distant pinprick of warm golden light at its very far end, a translucent ghostly trail of pale-gold light from his pointing scepter visualizing the path, his cat muzzle stern and instructive his pale-violet eyes glowing brighter as he speaks the warning, on a step above behind him Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character bipedal humanoid body proportions in her translucent pale white-and-blush peplos two perked white-and-cream cat ears a small cat muzzle a long fluffy cream-and-white cat tail long wavy strawberry-blonde hair flowing down her back interwoven with small white wildflowers (translucent ghost-pale like the rest of her) her humanoid hands clasped softly at her chest watching with hopeful patience her honey-brown eyes shimmering, in the foreground Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal humanoid body proportions in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet now standing upright on two legs body upright not on four legs his cat ears erect his polished golden lyre held tightly in his humanoid hands his face turned three-quarters toward the archway following the gesture his deep-amber eyes wide with hopeful resolve, the small distant golden light at the end of the tunnel a critical visual focal point — clearly far away, cold pale-violet and warm pale-gold contrast color palette, weighty mythic-condition atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 19 (sent_016)

**Текст:** Орфе́й шёл.

**Промпт:** highly detailed pixel art, 9:16 vertical, atmospheric wide three-quarters back-view shot deep in a long curved upward-rising stone tunnel of the underworld lit only by sparse pale-blue-and-violet ghostly will-o-wisps in iron sconces, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes two perked dark-gray cat ears a gray-and-white cat muzzle a long gray cat tail bipedal walking upright on two legs forward away from camera with humanoid body proportions in a steady human-like walking pose body upright not on four legs humanoid legs striding upright humanoid arms holding the lyre carefully across his chest, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet visible from behind on the back of his head, his polished golden lyre cradled in both his humanoid hands radiating a small steady warm pale-gold halo of light around him pushing back the cold gloom only a meter ahead, the rough stone walls of the tunnel carved with faint relief friezes of pomegranates and asphodels closing in on either side, a few hanging gnarled tree roots and pale-violet glowing crystal veins along the walls, the tunnel curving slightly upward ahead, far far up the curve in the very upper distance a tiny pinprick of warm golden light marks the eventual exit, his bare cat tail held still and tense not wagging, his cat ears erect listening intently behind him, focused tense walking-with-trust atmosphere, cold pale-violet with warm pale-gold halo color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 20 (sent_017)

**Текст:** Сзади — лёгкие шаги.

**Промпт:** highly detailed pixel art, 9:16 vertical, atmospheric wide low-angle shot of the same tunnel from behind Orpheus, in the foreground center Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal walking upright on two legs forward into the upward tunnel with humanoid body proportions in a human-like walking pose body upright not on four legs in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet visible from behind on the back of his head his back to camera his polished golden lyre cradled in his humanoid hands radiating a soft warm pale-gold halo only around himself, on the cold stone floor BEHIND him stretching back toward camera ONLY a faint translucent pale-violet ghostly footprint trail and the gentle echo-shape of small bipedal sandaled cat-paws — an invisible Eurydice walking quietly behind him — visualized only as a faint glow on the floor and a slight visible coiling of pale-lavender mist at the height of where her chiton hem would be, NO visible figure of Eurydice in this shot — only the suggestion of footsteps in mist behind him, a single small pale-cream cat-shaped translucent silhouette barely traced in the trailing mist hint at her presence, the cold pale-blue-and-violet stone walls of the tunnel close on either side, the warm golden distant exit still a tiny pinprick high up the tunnel curve far ahead of Orpheus, his cat ears half-tilted backward listening intently for confirmation, charged faith-and-doubt atmosphere, cold pale-violet and warm pale-gold color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 21 (sent_018)

**Текст:** Он не слышал её голоса.

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate medium close-up profile shot of Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes now wide with growing painful uncertainty two perked dark-gray cat ears strained forward and tilted backward at the same time straining to catch any sound a gray-and-white cat muzzle slightly parted in shallow breathing a long gray cat tail held tense bipedal still walking upright on two legs with humanoid body proportions in a tense human-like walking pose body upright not on four legs in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet his polished golden lyre cradled tightly in his humanoid hands its soft warm pale-gold halo flickering, around his cat ears subtle small floating sound-wave-shaped pale-blue glyphs visualizing the silence behind him — the absence of voice — with no warm-gold tones of speech among them, the rough cold dark-stone walls of the tunnel close on either side carved with faint pomegranate reliefs blurred in the soft-focus background, the air around him stagnant cold and empty no visible breath-mist except his own, his face in three-quarter profile his deep-amber eyes shadowed with self-doubt, behind him deep cold violet shadow with no visible figure only emptiness, painful unconfirmed faith atmosphere, cold pale-violet and warm pale-gold color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 22 (sent_019)

**Текст:** Не чувствовал руки́.

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate close-up shot focused on Orpheus's empty humanoid right hand at his side, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal walking upright on two legs with humanoid body proportions in his pale-cream chiton with sky-blue mantle, only his hand and side-profile visible, his slate-gray humanoid right hand half-open at his side fingers slightly parted as if reaching back hoping to feel a touch, hovering just above his hand in pale-violet translucent ghostly outline the faint shape of a gentle cream-and-white feminine humanoid cat hand — Eurydice's hand — REACHING FORWARD toward his fingers but visibly NOT TOUCHING NOT MAKING CONTACT a thin gap of cold violet shadow between their fingertips a single tiny tear-drop-shaped pale-gold spark suspended in the gap, around them only the dark cold stone walls of the tunnel with cold pale-violet glowing crystal veins, his polished golden lyre cradled in his other humanoid hand against his side glowing softly, his cat tail just visible held stiff with tension, the contrast between the warm-gold lyre-glow and the cold pale-violet ghostly hand drawing the eye, a single curl of pale lavender mist around her translucent fingers, painful absence atmosphere, cold pale-violet and warm pale-gold color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 23 (sent_020)

**Текст:** Один шаг, два, десять… до света оставалось чуть-чуть.

**Промпт:** highly detailed pixel art, 9:16 vertical, atmospheric wide upward-tilted shot from behind Orpheus in the upper section of the long tunnel, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character bipedal walking upright on two legs forward and slightly upward away from camera with humanoid body proportions in a determined human-like walking pose body upright not on four legs in his pale-cream chiton with sky-blue mantle his polished golden lyre cradled in his humanoid hands, his back-three-quarters silhouette now backlit by a much closer brighter warm golden light spilling around him from ahead, the WARM GOLDEN LIGHT OF THE EXIT now a large bright shape of soft pale-yellow-and-gold filling the upper third of the frame just a few steps ahead the curve of the tunnel-wall framing it like a warm halo, his slate-gray fur and pale-cream chiton finally catching the warm golden tones for the first time since the underworld began, the dark cold stone walls of the tunnel still on either side but already brightening, a slight wisp of warm fresh air visible as a faint breeze ruffling his raven-black hair and the hem of his chiton, behind him the deep dark cold violet of the tunnel falls away into shadow, on the floor behind him faint pale-violet footprint glow still trailing close behind him, his cat ears tilted slightly back still listening, anticipation hope-just-within-reach atmosphere, dramatic warm pale-gold versus cold pale-violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 24 (sent_021)

**Текст:** И он не выдержал.

**Промпт:** highly detailed pixel art, 9:16 vertical, intense intimate close-up profile shot of Orpheus's face captured in the crucial pivotal instant of breaking, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes now squeezed almost shut in unbearable inner conflict two perked dark-gray cat ears strained backward a gray-and-white cat muzzle pressed tight in a pained held breath a long gray cat tail held rigid bipedal still upright on two legs with humanoid body proportions in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet a few raven strands lifted by the tunnel draft, his polished golden lyre clutched tightly in his humanoid hands the strings half-trembling, his face in side profile turned three-quarters away with his head beginning the very first tiny rotation backward — captured in the half-second of breaking will — a small faint sweat drop on his temple, on the right side of the frame a bright halo of warm golden exit-light flooding the side of his face, on the left side of the frame the cold dark pale-violet shadow of the tunnel still hanging, between the two halves on the back of his head curling tendrils of cold pale-lavender mist whispering around his cat ears tempting him to look, his lips slightly parted as if about to whisper her name, charged unbearable inner-temptation atmosphere, dramatic warm pale-gold versus cold pale-violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 25 (sent_022)

**Текст:** Обернулся.

**Промпт:** highly detailed pixel art, 9:16 vertical, devastating dramatic full-body medium shot capturing Orpheus mid-turn, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes wide with sudden alarmed regret two perked dark-gray cat ears flicked backward a gray-and-white cat muzzle parted in a silent sharp gasp a long gray cat tail mid-swish bipedal standing upright on two legs with humanoid body proportions in a human-like dynamic mid-turn pose body upright not on four legs his torso twisted backward toward camera his humanoid feet planted his shoulders rotating his polished golden lyre still clutched in his humanoid hands at his side, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet flying with the sudden turn, the warm golden exit-light now bright filling the entire upper-right corner of the frame just one stride away highlighting half his body in warm gold, on his left in the cold pale-violet tunnel-shadow he sees for the first time clearly Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes wide and shining with shocked sorrow and love two small perked white-and-cream cat ears a small pink-and-white cat muzzle parted in a tiny silent cry a long fluffy cream-and-white cat tail bipedal standing upright on two legs with humanoid body proportions in her translucent pale-white-and-blush Greek peplos long wavy strawberry-blonde hair flowing down her back interwoven with small white wildflowers a few steps behind him her humanoid right hand reaching out toward him already starting to lose form the very tips of her fingers and the hem of her peplos beginning to disperse into pale-lavender mist and tiny pale-cream flower petals — the moment of irrevocable mistake captured the instant their eyes truly meet for the last time, charged tragic instant of shattered love atmosphere, dramatic warm pale-gold versus cold pale-violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 26 (sent_023)

**Текст:** Эвриди́ка вскрикнула — и растворилась в тенях.

**Промпт:** highly detailed pixel art, 9:16 vertical, devastating elegiac medium shot in the cold pale-violet tunnel-shadow, Eurydice the slender pale-rose-cream-and-white calico anthropomorphic cat character with large warm honey-brown eyes wide with gentle quiet grief NOT distorted with horror two small perked white-and-cream cat ears a small pink-and-white cat muzzle parted softly in a silent farewell a long fluffy cream-and-white cat tail bipedal standing upright on two legs with humanoid body proportions in her flowing pale white-and-blush Greek peplos, her humanoid right hand extended toward camera reaching for Orpheus, her entire figure rapidly dissolving from her sandaled feet upward into translucent pale-lavender mist tiny pale-cream flower petals soft pale-gold sparkles and small white asphodel petals — fully half her body already become drifting wisps her arms extending into petals and mist her hair lifting upward into floating pale-cream pollen — only her face hands and chest still recognizable her cat tail dispersing into petals at the back, the gentle dispersion drifting backward away from camera back toward the deep underworld shadow behind her, faint pale-gold tear-drops in the air between her dissolving form and Orpheus's outstretched hand visible in the foreground edge of the frame, her honey-brown eyes locked on his with deep love-and-loss until the last moment, soft pale-violet shadow filling the tunnel behind her, no horror no gore no scream-distorted face, profoundly mournful gentle dissolving atmosphere, cold pale-violet and warm pale-pink-cream color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 27 (sent_024)

**Текст:** Навсегда.

**Промпт:** highly detailed pixel art, 9:16 vertical, mournful empty wide deep shot looking down into the cold pale-violet shadow of the tunnel where Eurydice was, the entire frame filled with empty dark-stone tunnel walls cold pale-blue-and-violet glowing crystal veins along the rocks, the floor and air completely empty of any figure only a few last drifting pale-lavender mist wisps and a slow gentle fall of tiny pale-cream-and-white flower petals scattered in the air settling onto the cold stone floor, on the floor in the foreground a single small lyre-shaped gold pendant on a thin gold chain — Eurydice's pendant — caught faintly between cold violet shadow and a single thin warm pale-gold ray of light spilling in from the exit far behind, the deep cold violet emptiness stretches into an unreachable distance, no figure of any cat or person, profound finality atmosphere of irrevocable absence, no body no carcass no horror, cold pale-violet with one thin warm pale-gold ray color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 28 (sent_025)

**Текст:** Орфе́й остался на пороге света.

**Промпт:** highly detailed pixel art, 9:16 vertical, devastating wide medium shot at the very mouth of the tunnel where the underworld meets the upper world at twilight, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes now hollow and tear-streaked two perked dark-gray cat ears flattened back a gray-and-white cat muzzle drawn down in silent sorrow a long gray cat tail dragging on the stone bipedal kneeling slowly upright on one humanoid knee at the threshold with humanoid body proportions in a human-like kneeling pose body upright not on four legs, in his pale-cream chiton with sky-blue mantle now disheveled long wavy raven-black hair held back by a thin gold-and-laurel circlet a few strands fallen across his forehead, his back to the cold pale-violet underworld behind him his front facing the warm pale-gold-and-rose dawn world ahead of him caught precisely on the line between the two — half his slate-gray-and-white fur lit by warm gold the other half by cold violet, his head bowed forward forehead touching the cold stone, his polished golden lyre fallen at his side no longer glowing, in front of him the pale stone of the upper world the first warm soft sunrise light spilling onto the rocks and a few real natural Greek wildflowers blooming at his knees, behind him the dark cold tunnel silent and empty, distant cypress trees and rolling Greek hills barely visible against a soft pink-and-pale-amber dawn sky a single morning star fading, profound exhausted mourning atmosphere, dramatic warm pale-gold versus cold pale-violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 29 (sent_026)

**Текст:** С лирой.

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate close-up still-life shot at the threshold between the underworld tunnel and the upper world at dawn, Orpheus's polished golden lyre lying on its side on the pale stone of the threshold the seven strings half-broken or slack one curving tortoiseshell horn slightly chipped a single faint thread of mother-of-pearl inlay still catching the warm dawn light, faint pale-gold dust resting on the strings, beside the lyre Orpheus's humanoid hand visible only at the wrist resting on the stone fingers half-curled gently around the lower curve of the instrument, beside the lyre on the stone a single small fresh white asphodel flower lying as if just dropped from above the threshold linking the underworld to the world of the living, beside the asphodel one perfect small fresh living olive leaf from the upper world, the warm gentle pale-gold-and-rose dawn light spilling onto the stone from the right side, the cold pale-violet shadow of the tunnel still touching the left edge of the frame, soft floating dust motes in the warm light, profound silent intimate elegiac atmosphere, warm pale-gold and cold pale-violet color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 30 (sent_027)

**Текст:** И с эхом её последнего шёпота.

**Промпт:** highly detailed pixel art, 9:16 vertical, lyrical mournful wide low-angle shot at the threshold of the tunnel at full pale-gold dawn, Orpheus the slender slate-gray-and-white tuxedo-marked anthropomorphic cat character with soulful deep-amber eyes red-rimmed and distant two perked dark-gray cat ears slightly drooped a gray-and-white cat muzzle softly closed a long gray cat tail curled at his feet bipedal sitting upright on a low pale-stone outcrop at the threshold with humanoid body proportions in a quiet human-like seated pose body upright not on four legs, in his pale-cream chiton with sky-blue mantle long wavy raven-black hair held back by a thin gold-and-laurel circlet, holding his polished golden lyre cradled across his lap one humanoid hand resting on the strings without playing the seven strings utterly still, around his head curling softly through the warm pale-gold sunrise air a faint translucent ghostly trail of pale-lavender-and-cream mist forming the shape of small soft sound-wave glyphs and the suggestion of a single feminine cat-shaped wisp drifting close to his cat ear — the visualized echo of Eurydice's last whisper — softly dispersing into the warm dawn breeze, a few delicate pale-cream flower petals and small white-feather wisps drifting through the air around him, behind him the dark mouth of the tunnel still visible but already small in the corner of the frame the cold violet retreating, in front of him the warm Greek countryside opens up — rolling hills with cypress and olive trees a far meadow of white wildflowers a soft pink-and-gold sunrise sky a flock of small white birds rising — the world of the living going on without her, on the stone beside him Eurydice's small lyre-shaped gold pendant on its thin gold chain placed carefully near him, a single tear glints in the corner of his deep-amber eye, profound elegiac quiet-mourning closing-of-the-myth atmosphere, warm pale-gold and pale-rose-cream color palette with a faint pale-violet whisper, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement
