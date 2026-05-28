# Медуза Горгона

<!--
Формат файла:
- `## Сцена N (sent_NNN)` — порядковый номер визуального шота для Flow / ImageFX.
  Картинки сохранятся в images/review_images/scene_NN/vN.jpg.
- `**Текст:**` — закадровый текст сцены (на русском).
- `**Промпт:**` — промпт для ImageFX / Nano Banana (одна строка, англ.).
  Первые 3-4 слова каждого промпта = УНИКАЛЬНЫЙ subject-маркер сцены
  (Flow берёт их в имя файла → тривиальная раскладка distribute_images.py).

Всего 19 предложений → 18 визуальных сцен на ~1:00-1:10 видео.
sent_001 (хук) + sent_002 (титул) монтируются как ОДНА сцена scene_01:
картинка-крючок + караоке-титул «Меду́за Горго́на. Миф за минуту.» поверх.

Маппинг sentence ↔ scene_NN (для video.md и pyCapCut):
  sent_001 + sent_002 → scene_01  (1 шот, 2 аудио)  хук-кадр + титул караоке
  sent_003 → scene_02   красавица Эллады (дева во славе)
  sent_004 → scene_03   гордость — золотые волосы до земли
  sent_005 → scene_04   жрица в храме Афины, клятва чистоты
  sent_006 → scene_05   Посейдон замечает деву из моря
  sent_007 → scene_06   Посейдон настигает её в храме (смягчённо)
  sent_008 → scene_07   Афина возвращается, видит осквернение
  sent_009 → scene_08   Афина в ярости ищет виновного
  sent_010 → scene_09   но против бога морей она бессильна
  sent_011 → scene_10   и весь гнев обрушился на Медузу
  sent_012 → scene_11   волосы → шипящие змеи
  sent_013 → scene_12   кожа → зелёная чешуя
  sent_014 → scene_13   взгляд обращает в камень
  sent_015 → scene_14   горгона одна в пещере на краю мира
  sent_016 → scene_15   прежде красотой любовались издалека (флешбэк-контраст)
  sent_017 → scene_16   теперь взгляд = камень навсегда (сад статуй)
  sent_018 → scene_17   спустя годы придёт Персей (камео-силуэт)
  sent_019 → scene_18   «другая история» — связка с роликом про Персея

Стилевой каркас (одинаковый во всех сценах):
highly detailed pixel art, 9:16 vertical composition, ancient Greek setting,
anthropomorphic bipedal cat characters (NOT real four-legged cats),
humanoid body proportions, standing/sitting/gesturing like humans,
NO humans, NO people, NO real four-legged cats,
modern detailed pixel art style, warm cinematic lighting,
no text, no letters, no camera movement

КАРТОЧКИ ПЕРСОНАЖЕЙ (источник правды — content/characters.md; копировать в промпт каждой сцены дословно):

Medusa-maiden = "Medusa in her maiden form before the curse, the most beautiful young
priestess of all Hellas, a graceful slender soft pale-gold-and-cream anthropomorphic cat
character with luminous large jade-green eyes and serene gentle beautiful features, two
delicate pale-gold cat ears, a small pink-and-cream cat muzzle, a long elegant pale-gold
cat tail, bipedal standing upright on two legs with humanoid body proportions, her
crowning glory long flowing radiant golden hair cascading in soft waves all the way down
to the ground (her most famous feature), a thin gold laurel circlet resting on her brow,
wearing a flowing snow-white Greek priestess peplos with delicate gold embroidery of olive
branches and small owls (the mark of Athena's temple) along the hem and shoulders, a thin
gold belt, gold sandals, slender gold bracelets on her humanoid wrists, a faint soft warm
glow around her, NO snakes NO scales — fully beautiful and graceful in this maiden form"

Medusa-gorgon = "Medusa the cursed Gorgon, a tall greenish-grey-and-bronze scaled
anthropomorphic cat character with sharp angular features and cold luminous jade-green eyes
(the same jade-green eyes she had as a maiden, now glowing and petrifying) and small ivory
fangs visible under her cat muzzle, two perked dark-bronze cat ears with small brass rings,
a slim greenish-grey cat muzzle, a long dark-bronze cat tail with small bronze scale-patterns,
bipedal standing or seated upright with humanoid body proportions, wearing a tattered
dark-bronze and deep-green Greek peplos with intricate snake-scale embroidery, a wide bronze
belt with a serpent-shaped clasp, dark sandals, instead of hair her head is crowned with
WRITHING STYLIZED SNAKE STRANDS — many living serpentine locks of dark-green and bronze
scaled snakes coiling and twisting where her hair would be each with tiny ruby-glint eyes
(small cartoonish stylized snakes NOT realistic horror snakes NOT graphic), faint pale-green
mythological glow around her, NO blood NO gore NO wounds — only mythological cursed-monster
atmosphere through composition not through horror"

Athena = "Athena the silver-grey-and-white wisdom cat goddess, a tall majestic
silver-grey-and-snow-white tabby anthropomorphic cat character with piercing intelligent
storm-grey eyes and noble sharp features two perked silver cat ears a small white-and-grey
cat muzzle a long silver-grey tabby cat tail, bipedal standing upright on two legs with
humanoid body proportions, wearing a flowing snow-white-and-silver Greek peplos with
intricate gold embroidery of olive branches and small owl motifs along the hem, a wide gold
belt with a small golden owl clasp, golden sandals, a tall ornate bronze-and-gold Corinthian
war helm with a flowing white horsehair crest pushed back on her head, her long wavy
silver-and-cream hair flowing down her back held by the helm, a long bronze spear in her
humanoid right hand, a tall round bronze shield (her aegis, here still CLEAN without any
gorgon-head relief — this is the prequel) in her humanoid left hand, a small white-and-grey
owl perched on her shoulder, a faint silver-and-gold divine aura surrounding her"

Poseidon = "Poseidon the mighty god of the sea, a large powerful imposing
deep-teal-and-storm-blue-grey anthropomorphic cat character with a broad muscular build and
piercing turquoise-aqua eyes the colour of shallow seawater, two perked teal-blue cat ears,
a thick blue-grey cat muzzle, a long flowing teal cat tail tipped with small fin-like fronds,
bipedal standing upright on two legs with humanoid body proportions, a long flowing blue-green
beard and mane like rolling sea-foam and ocean waves, wearing a flowing sea-green-and-deep-blue
Greek robe with rich gold embroidery of waves dolphins and seashells along the hem, a wide
gold belt with a mother-of-pearl clasp, bronze-and-coral sandals, a tall ornate crown of gold
and pink coral branches set with pearls upon his head, holding a massive golden three-pronged
trident in his humanoid hand, his teal-and-blue fur glistening as if wet with droplets of
seawater, a faint blue-green watery divine glow and a swirl of foam and spray around his feet"

Perseus = "Perseus the young Greek hero, a brave handsome young sandy-gold-and-cream
short-haired tabby anthropomorphic cat character with bright determined emerald-green eyes and
youthful confident features, two perked sandy-gold cat ears, a small cream-and-pink cat muzzle,
a long sandy-gold cat tail, bipedal standing upright on two legs with humanoid body proportions,
wearing a short white-and-bronze Greek tunic (chitoniskos) with a bronze leaf-pattern shoulder
clasp, a wide brown leather belt with a bronze buckle, leather sandals, a short red travel cloak
draped over one shoulder, his short tousled sandy-gold hair with a single small bronze laurel
circlet, carrying a tall round polished bronze MIRROR SHIELD (highly reflective like a mirror)
on his humanoid left arm and a curved bronze sickle-sword (harpe) in his humanoid right hand"

Разнообразие окружения: залитый солнцем мраморный храм Афины (дорические колонны, оливковые
ветви, мозаики с совами, алтарь с курильницами), цветущая греческая роща и берег у храма,
открытое штормовое и спокойное Эгейское море, мраморные ступени храма, мрачная пещера на
скалистом краю мира с обсидиановыми стенами и pale-green мхом, серые каменные статуи у входа,
закатное и лунное небо. Варьировать ракурсы (крупный, средний, общий, низкий, силуэт против
неба) и освещение (золотое утро / полдень / закат / буря / лунный потусторонний свет).

Кошачьи декоративные мотивы (статуи котов, мозаики с совами-котами, вазы с котами) — уместны
в мраморном храме Афины, но НЕ в пещере горгоны, не на голых скалах, не на берегу. Пещера и
природа — обычный греческий пейзаж без принудительных кошачьих деталей.

КРИТИЧНО для динамичных сцен (превращение, настигает, обрушивает гнев) — явно прописывать
человеческую позу: "human-like pose, body upright not on four legs", "humanoid arms
outstretched". Без этого Flow скатывается в обычных четвероногих кошек.

ОГРАНИЧЕНИЯ ПЛАТФОРМ (TikTok / YouTube Shorts):
- Тема Посейдона (sent_006-007) подаётся СМЯГЧЁННО: бог входит/настигает в храме, дева
  отшатывается — БЕЗ сцен насилия, БЕЗ контакта, только драматическое вторжение и испуг.
  «Осквернение» показано как опрокинутые курильницы / погасшие огни / нарушенный покой храма.
- Превращение в камень (sent_014) — жертва НЕ человек и НЕ кот: маленькая птица / оливковое
  деревце / бабочка сереет и каменеет через мифический пиксельный эффект «трещины и серый
  цвет», без ужаса, без агонии.
- Превращение Медузы (sent_012-013) — мягкий мифический переход (золото→зелень, волосы→змейки),
  стилизованные мультяшные змейки с ruby-glint глазками, БЕЗ хоррора.
- Каменные статуи (sent_017) — целые героические фигуры в позах ужаса/защиты, НЕ разломанные,
  без костей. Negative: no blood, no gore, no wounds, no realistic horror snakes, no skulls.

ВИЗУАЛЬНЫЕ МОТИВЫ:
- jade-green глаза — мостик между девой и горгоной (sent_001, 011-014); держать цвет постоянным.
- Золотые волосы до земли — гордость девы (sent_003, 002, 004, 016); в превращении становятся змеями.
- Сова Афины — символ храма и богини (sent_004, 007, 008); вышита на пеплосе девы и Афины.
- Трезубец и морская пена — маркер Посейдона (sent_006, 007).
- Зеркальный щит Персея — финальный лейтмотив-связка (sent_018, 019) с роликом «Персей и Медуза».
-->

## Сцена 1 (sent_001 + sent_002 — хук + титул караоке поверх)

**Текст:** Её прокляли не за злодеяние — а за чужое преступление. Меду́за Горго́на. Миф за минуту.

**Промпт:** medusa cursed sorrow ghost of beauty, highly detailed pixel art, 9:16 vertical composition, dramatic dignified retention-hook title-card frame designed to STOP a thumb mid-scroll through cinematic sorrow and tragedy NOT through cartoon shock, intimate dramatic medium shot deep inside a dim cavern on the rocky edge of the world lit by a cold sickly pale-green mythological glow, seated alone on a low broken stone ledge in the center Medusa the cursed Gorgon a tall greenish-grey-and-bronze scaled anthropomorphic cat character with sharp angular features and cold luminous jade-green eyes (lowered and full of quiet grief NOT rage) small ivory fangs two perked dark-bronze cat ears with small brass rings a slim greenish-grey cat muzzle a long dark-bronze cat tail, bipedal seated hunched upright with humanoid body proportions her humanoid hands resting limply in her lap, in a tattered dark-bronze and deep-green Greek peplos with snake-scale embroidery a wide bronze belt with a serpent-shaped clasp, instead of hair her head crowned with WRITHING STYLIZED SNAKE STRANDS of dark-green and bronze scaled stylized cartoon snakes with tiny ruby-glint eyes (drooping quietly downward in sorrow not flaring), rising softly behind her like a haunting memory a large faint translucent golden ghost-silhouette of her former maiden self — a beautiful pale-gold-and-cream cat maiden with long flowing radiant golden hair cascading to the ground and the SAME luminous jade-green eyes and a serene gentle face — overlapping her cursed form so the viewer instantly understands these are ONE being, between them a single golden olive leaf drifting down, the obsidian-black cave walls streaked with pale-green moss behind, palette deep cool obsidian shadows pierced by sickly pale-green Gorgon glow contrasted with the warm faint gold of the ghost-memory, tragic atmosphere of an innocent punished for a crime that was not hers told through CINEMATIC GRAVITY and CLASSICAL DIGNITY not cartoon exaggeration, NO bulging eyes NO comic shock NO impact lines, no blood no gore no wounds no skulls no realistic horror snakes, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 2 (sent_003)

**Текст:** Когда-то Меду́за была не чудовищем, а первой красавицей Элла́ды.

**Промпт:** medusa radiant maiden beauty, highly detailed pixel art, 9:16 vertical composition, luminous idyllic medium-wide shot on the sunlit marble steps of a Greek temple at golden morning, Medusa in her maiden form before the curse the most beautiful young priestess of all Hellas a graceful slender soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes and a serene gentle beautiful smiling face two delicate pale-gold cat ears a small pink-and-cream cat muzzle a long elegant pale-gold cat tail, bipedal standing upright on two legs with humanoid body proportions in a graceful relaxed pose, her crowning glory long flowing radiant golden hair cascading in soft waves all the way down to the ground catching the morning sun, a thin gold laurel circlet on her brow, in a flowing snow-white Greek priestess peplos with delicate gold embroidery of olive branches and small owls along the hem and shoulders a thin gold belt gold sandals slender gold bracelets on her humanoid wrists, a faint soft warm golden glow around her, behind her tall white marble Doric columns wreathed in green olive branches and small pink flowers a clear cyan Aegean sea sparkling in the distance, soft sun-rays and floating golden pollen motes in the warm air, palette radiant warm gold-and-cream with soft cyan sky, idyllic atmosphere of breathtaking innocent beauty before tragedy, NO snakes NO scales, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 3 (sent_004)

**Текст:** Особенно гордились её золотыми волосами струящимися до земли.

**Промпт:** golden hair cascading pride, highly detailed pixel art, 9:16 vertical composition, intimate elegant close-medium shot focusing on the legendary hair of Medusa in her maiden form a graceful soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes and serene gentle beautiful features two delicate pale-gold cat ears a small pink-and-cream cat muzzle, bipedal seated gracefully upright on a marble bench with humanoid body proportions turned three-quarter as she gently runs a carved ivory comb through her hair with her humanoid hand, her crowning glory LONG FLOWING RADIANT GOLDEN HAIR cascading in luxurious soft glossy waves all the way down past the bench to pool on the sunlit marble floor — the visual focus of the frame catching brilliant golden highlights, a thin gold laurel circlet on her brow, in a flowing snow-white Greek priestess peplos with gold owl-and-olive embroidery a thin gold belt slender gold bracelets, a soft warm glow around her, behind her a polished bronze hand-mirror on a marble stand reflecting her beauty tall white marble columns and a window opening onto cyan sea, scattered pink rose petals and a small bowl of scented oil on the bench, palette luminous warm gold with soft white marble and cyan accents, atmosphere of serene vanity and admired beauty, NO snakes NO scales, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 4 (sent_005)

**Текст:** Она служила жрицей в храме Афи́ны и поклялась богине в чистоте.

**Промпт:** maiden priestess vow altar, highly detailed pixel art, 9:16 vertical composition, reverent dramatic medium shot inside the grand marble temple of Athena at soft sacred daylight, Medusa in her maiden form a graceful soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes and a devout serene expression two delicate pale-gold cat ears a small pink-and-cream cat muzzle a long pale-gold cat tail, bipedal kneeling gracefully upright on one knee with humanoid body proportions before a great altar her humanoid hands pressed together in solemn prayer and vow, her long flowing radiant golden hair cascading down her back to the temple floor a thin gold laurel circlet on her brow, in a flowing snow-white Greek priestess peplos with gold embroidery of olive branches and small owls a thin gold belt gold sandals, before her a tall white marble statue of Athena the wisdom goddess (a regal armoured cat-goddess figure with a Corinthian war helm a spear a round shield and an owl carved at her feet) looming benevolently with a small bronze brazier of sacred incense smoke curling upward at its base, tall marble Doric columns mosaics of owls on the floor hanging bronze oil lamps soft shafts of holy light from high windows, a live small white-and-grey owl perched on a column watching, palette serene cool white marble with warm gold incense-light, sacred devout atmosphere of a vow of purity, NO snakes NO scales, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 5 (sent_006)

**Текст:** Но красоту девы заметил сам Посейдо́н, владыка морей.

**Промпт:** poseidon emerging sea gaze, highly detailed pixel art, 9:16 vertical composition, dramatic low-angle wide shot of the open Aegean sea at stormy golden-grey afternoon, rising powerfully from a towering crest of foaming waves Poseidon the mighty god of the sea a large powerful imposing deep-teal-and-storm-blue-grey anthropomorphic cat character with a broad muscular build and piercing turquoise-aqua eyes two perked teal-blue cat ears a thick blue-grey cat muzzle a long flowing teal cat tail tipped with fin-like fronds, bipedal standing upright on two legs atop the wave with humanoid body proportions, a long flowing blue-green beard and mane like rolling sea-foam streaming in the salt wind, in a flowing sea-green-and-deep-blue Greek robe with gold embroidery of waves dolphins and seashells a wide gold belt bronze-and-coral sandals, a tall ornate crown of gold and pink coral branches set with pearls upon his head, holding a massive golden three-pronged trident raised in his humanoid hand, his teal fur glistening wet with seawater droplets a blue-green watery glow and foam swirling around him, his turquoise eyes turned and locked intently toward the distant sunlit marble temple of Athena on the cliff (small in the upper background) where a tiny faint golden glow marks the maiden — his expression one of captivated dangerous desire, leaping dolphins and gulls around him a dramatic stormy sky, palette deep teal-and-storm-blue ocean tones with gold trident highlights and a distant warm-gold temple glow, dramatic atmosphere of a powerful god fixated on a mortal beauty, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 6 (sent_007)

**Текст:** Очарованный, он настиг её прямо в священном храме Афи́ны.

**Промпт:** poseidon intrudes sacred temple, highly detailed pixel art, 9:16 vertical composition, dramatic tense medium-wide shot inside the marble temple of Athena now invaded, on the right Poseidon the mighty sea god a large imposing deep-teal-and-storm-blue-grey anthropomorphic cat character with turquoise-aqua eyes a long flowing blue-green sea-foam beard and mane two perked teal-blue cat ears, bipedal striding forward upright on two legs with humanoid body proportions human-like pose body upright not on four legs his humanoid hand reaching forward, in his sea-green-and-deep-blue Greek robe with gold wave-and-dolphin embroidery a coral-and-pearl crown his golden trident in his other humanoid hand, trailing wet footprints and a wash of seawater and foam across the sacred marble floor, on the left Medusa in her maiden form a graceful soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes now WIDE with fear and alarm two delicate pale-gold cat ears flattened back a small pink-and-cream cat muzzle, bipedal recoiling and shrinking back upright on two legs with humanoid body proportions her humanoid arms raised defensively her long flowing radiant golden hair swept as she turns away, in her snow-white priestess peplos with gold owl-and-olive embroidery a thin gold circlet, around them the desecrated sanctuary — a tall bronze incense brazier knocked over its sacred flame guttering out, scattered olive branches, the marble statue of Athena in the background seeming to watch in stern shadow its carved owl eyes catching cold light, tall marble columns hanging lamps swinging, palette tense clash of cold teal-and-seawater intrusion against warm sacred gold-and-white temple light now disturbed, dramatic atmosphere of a sacred space violated and a maiden in peril told with TENSION and DIGNITY NOT graphic content, no contact no violence shown only intrusion and recoil, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 7 (sent_008)

**Текст:** Богиня вернулась — и увидела, что её святилище осквернено.

**Промпт:** athena returns desecrated sanctuary, highly detailed pixel art, 9:16 vertical composition, dramatic medium shot at the grand marble doorway of the temple of Athena, framed in the bright archway Athena the silver-grey-and-white wisdom cat goddess a tall majestic silver-grey-and-snow-white tabby anthropomorphic cat character with piercing intelligent storm-grey eyes now WIDENING in shock and dawning anger noble sharp features two perked silver cat ears a small white-and-grey cat muzzle a long silver-grey tabby cat tail, bipedal standing upright frozen mid-step on two legs with humanoid body proportions just arrived at the threshold, in a flowing snow-white-and-silver Greek peplos with gold owl-and-olive embroidery a gold owl-clasp belt golden sandals, a tall bronze-and-gold Corinthian war helm with a flowing white horsehair crest pushed back her long wavy silver-and-cream hair flowing down her back held by the helm, a long bronze spear in her humanoid right hand its tip dipping as she stops a tall round CLEAN bronze shield-aegis (no gorgon relief yet) on her humanoid left arm, a small white-and-grey owl on her shoulder its feathers ruffled in alarm, before her the violated sanctuary — the toppled bronze incense brazier its sacred flame extinguished and smoking, puddles of seawater and wet footprints across the holy marble floor scattered olive branches an overturned offering bowl, the cold daylight from high windows revealing the disorder, the great marble statue of Athena looming in the background, palette cold disturbed white-and-silver marble with the dead-grey smoke of the snuffed sacred flame and a rising glint of storm-grey divine anger, dramatic atmosphere of sacred outrage discovered, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 8 (sent_009)

**Текст:** В ярости Афи́на искала виновного.

**Промпт:** athena blazing wrath search, highly detailed pixel art, 9:16 vertical composition, dramatic dynamic close-medium shot of Athena the silver-grey-and-white wisdom cat goddess a tall majestic silver-grey-and-snow-white tabby anthropomorphic cat character with piercing intelligent storm-grey eyes now BLAZING with cold divine fury her brow furrowed her noble features hardened two perked silver cat ears pinned back a small white-and-grey cat muzzle set in anger a long silver-grey tabby cat tail lashing, bipedal standing upright on two legs with humanoid body proportions human-like pose turning sharply scanning the temple her body coiled with rage, in a flowing snow-white-and-silver Greek peplos with gold owl-and-olive embroidery a gold owl-clasp belt golden sandals, a tall bronze-and-gold Corinthian war helm with a white horsehair crest pushed back her long wavy silver-and-cream hair flowing down her back, gripping her long bronze spear tightly upright in her humanoid right hand her CLEAN bronze shield-aegis on her humanoid left arm, the small white-and-grey owl on her shoulder also turning its head sharply searching, a fierce silver-and-gold divine aura flaring brighter around her crackling at her fingertips, behind her the dim disturbed temple interior with the snuffed brazier and tall shadowed columns the marble Athena statue in deep shadow, palette dramatic cold silver-grey-and-white with a hot flaring silver-gold divine glow of wrath against deep marble shadow, intense atmosphere of a goddess hunting for who defiled her shrine, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 9 (sent_010)

**Текст:** Но покарать всесильного бога морей она не могла.

**Промпт:** athena powerless against sea, highly detailed pixel art, 9:16 vertical composition, dramatic wide shot from behind and beside Athena standing at the cliff-edge marble terrace of her temple looking out over the sea, Athena the silver-grey-and-white wisdom cat goddess a tall majestic silver-grey-and-snow-white tabby anthropomorphic cat character with storm-grey eyes (now narrowed in bitter frustration) noble sharp features two perked silver cat ears a small white-and-grey cat muzzle a long silver-grey tabby cat tail, bipedal standing upright on two legs with humanoid body proportions seen three-quarter from behind one humanoid hand clenched into a frustrated fist at her side the other gripping her lowered bronze spear, in her snow-white-and-silver peplos with gold owl-and-olive embroidery a Corinthian war helm with white crest pushed back her long wavy silver-and-cream hair flowing down her back her CLEAN bronze aegis on her arm a small owl on her shoulder, in the far distance out over the churning grey-teal sea the small retreating figure of Poseidon the teal-and-storm-blue sea god sinking back beneath a towering wave his coral crown and golden trident glinting his sea-foam beard merging with the spray — utterly beyond her reach, a band of stormy clouds and a cold wind sweeping spray toward the terrace, Athena's silver-gold aura dimming with helpless anger, palette cold grey-teal sea and stormy sky against the white marble terrace, dramatic atmosphere of a goddess whose fury cannot touch an equal god, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 10 (sent_011)

**Текст:** И весь гнев обрушился на Меду́зу.

**Промпт:** athena wrath descends medusa, highly detailed pixel art, 9:16 vertical composition, dramatic dynamic medium shot inside the temple, on the right Athena the silver-grey-and-white wisdom cat goddess a tall majestic silver-grey-and-snow-white tabby anthropomorphic cat character with storm-grey eyes blazing with redirected cold fury two perked silver cat ears pinned a long silver-grey tabby cat tail, bipedal standing upright on two legs with humanoid body proportions human-like pose her humanoid arm thrust forward and down pointing accusingly at Medusa a fierce blast of silver-and-gold divine light pouring from her outstretched humanoid hand, in her snow-white-and-silver peplos with gold owl-and-olive embroidery a Corinthian war helm with white crest her long wavy silver-and-cream hair flowing back her CLEAN bronze aegis on her other arm, on the left and lower Medusa in her maiden form a graceful soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes now wide with terror and tearful confusion two delicate pale-gold cat ears flattened a small pink-and-cream cat muzzle, bipedal sinking and cowering down on her knees upright with humanoid body proportions her humanoid arms raised to shield herself her long flowing radiant golden hair swirling around her as the wave of silver-gold divine wrath-light engulfs her, in her snow-white priestess peplos with gold owl-and-olive embroidery a thin gold circlet, the air between them filled with swirling silver-gold curse-light just beginning to tint sickly green where it touches Medusa, tall marble columns and the stern marble Athena statue behind, palette overpowering silver-gold divine light flooding from the right onto the helpless gold maiden on the left with the first sickly-green tint of the curse appearing, tragic dramatic atmosphere of misplaced divine wrath striking the innocent, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 11 (sent_012)

**Текст:** Прекрасные волосы обратились в шипящих змей.

**Промпт:** golden hair becoming snakes, highly detailed pixel art, 9:16 vertical composition, dramatic emotional close-up of Medusa mid-transformation, a cat character caught between her maiden and cursed forms — still soft pale-gold-and-cream fur but with the FIRST patches of greenish-grey scale appearing at her temples, her luminous large jade-green eyes wide with anguish and tears (the SAME jade-green eyes she keeps through the curse) a small pink-and-cream cat muzzle parted in a silent gasp two pale-gold cat ears, bipedal upright with humanoid body proportions her humanoid hands flying up to clutch at her own head in horror, her once-glorious LONG FLOWING GOLDEN HAIR now visibly TRANSFORMING strand by strand into WRITHING STYLIZED SNAKE STRANDS — the upper locks already become living dark-green-and-bronze scaled stylized cartoon snakes with tiny ruby-glint eyes hissing and rising upward in alarm while the lower lengths are still half golden hair caught mid-change shimmering between gold and green-bronze scales, swirling sickly pale-green-and-silver-gold curse mist spiralling around her head, her thin gold laurel circlet slipping the snow-white priestess peplos still on her shoulders, behind her the blurred marble columns of the temple, palette anguished blend of fading warm gold dissolving into rising sickly green-and-bronze with curse mist, tragic mythological transformation atmosphere told softly NOT as horror stylized cartoon snakes not realistic, no blood no gore no wounds no realistic horror snakes, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 12 (sent_013)

**Текст:** Нежная кожа стала зелёной чешуёй.

**Промпт:** soft fur turning scales, highly detailed pixel art, 9:16 vertical composition, dramatic medium shot continuing the transformation, Medusa now further changed a cat character whose once soft pale-gold-and-cream fur is rapidly turning across her arms shoulders and face into GREENISH-GREY-AND-BRONZE SCALES spreading in fine creeping patterns like advancing frost, her luminous large jade-green eyes still wide and grieving (unchanged), a small greenish-grey-forming cat muzzle with the first tiny ivory fangs appearing two darkening bronze cat ears with small brass rings beginning to form, bipedal upright with humanoid body proportions her humanoid hands held out before her face staring in despair as the scales climb up her humanoid arms and wrists (humanoid not animal), her crown now fully a writhing mass of dark-green-and-bronze stylized cartoon snakes with ruby-glint eyes, her snow-white priestess peplos darkening and tattering into the dark-bronze-and-deep-green cursed peplos with snake-scale embroidery a serpent-clasp bronze belt forming at her waist, swirling pale-green curse mist around her, behind her the temple dissolving into shadow, palette the last warm cream tones being overtaken by cold green-and-bronze scale tones amid pale-green mist, tragic transformation atmosphere of beauty lost told with dignity NOT horror, no blood no gore no wounds, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 13 (sent_014)

**Текст:** А взгляд, что когда-то сводил с ума, теперь обращал любого в холодный камень.

**Промпт:** petrifying gaze turns stone, highly detailed pixel art, 9:16 vertical composition, dramatic medium shot now showing Medusa the cursed Gorgon fully transformed a tall greenish-grey-and-bronze scaled anthropomorphic cat character with sharp angular features and COLD LUMINOUS JADE-GREEN EYES now glowing and radiating concentric pale-green petrification light rings forward small ivory fangs two perked dark-bronze cat ears with brass rings a slim greenish-grey cat muzzle a long bronze-scaled cat tail, bipedal standing upright on two legs with humanoid body proportions one humanoid hand half-raised as she realises her own terrible new power, in her tattered dark-bronze-and-deep-green peplos with snake-scale embroidery a serpent-clasp belt, her crown of writhing dark-green-and-bronze stylized cartoon snakes with ruby-glint eyes, the pale-green beams of her gaze striking a small fluttering bird and a slender young olive sapling in front of her — the bird and the little tree CAUGHT MID-MOTION already turning pale-grey stone fine cracking grey veins spreading across the bird's wings and the olive leaves freezing into solid grey marble (the victim is NOT a person NOT a cat — only a bird and a plant), the petrification shown through the mythological pixel effect of grey colour and fine cracks NOT through gore or agony, behind her the temple now empty and shadowed, palette cold sickly pale-green glow of the gaze and the dead-grey of fresh petrified stone against deep shadow, tragic dramatic atmosphere of a gift of beauty turned into a curse of death told with dignity, no blood no gore no wounds no skulls, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 14 (sent_015)

**Текст:** Так невинная жрица стала Горго́ной — одинокой, всеми проклятой, обречённой жить в пещере на краю мира.

**Промпт:** gorgon alone edge world cave, highly detailed pixel art, 9:16 vertical composition, lonely atmospheric wide shot of Medusa the cursed Gorgon a tall greenish-grey-and-bronze scaled anthropomorphic cat character with cold luminous jade-green eyes (lowered in lonely sorrow) small ivory fangs two perked dark-bronze cat ears with brass rings a slim greenish-grey cat muzzle a long bronze-scaled cat tail, bipedal seated alone hunched upright on a stone ledge with humanoid body proportions her humanoid arms wrapped around her own knees, in her tattered dark-bronze-and-deep-green peplos with snake-scale embroidery a serpent-clasp belt, her crown of writhing dark-green-and-bronze stylized cartoon snakes with ruby-glint eyes coiling quietly and drowsily around her shoulders, inside a vast dim cavern carved into a barren rocky island at the very edge of the world, the mouth of the cave opening onto a desolate twilight sea and a cold pale-violet horizon far beyond, the obsidian-black cave walls streaked with pale-green moss tall jagged columns of dark rock a few cracks of dim cold light from above, scattered dust and a single dead grey-stone olive sapling near her, her faint pale-green mythological glow the only warmth, palette desolate cold obsidian-and-green cave tones with a distant lonely pale-violet twilight sea, profoundly lonely tragic atmosphere of an outcast cursed to solitude at the world's end, no blood no gore no skulls, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 15 (sent_016)

**Текст:** Прежде её красотой любовались издалека.

**Промпт:** maiden beauty admired afar flashback, highly detailed pixel art, 9:16 vertical composition, warm nostalgic flashback medium-wide shot rendered with a soft golden dreamlike haze to read clearly as a MEMORY of the past, Medusa in her maiden form a graceful soft pale-gold-and-cream anthropomorphic cat character with luminous large jade-green eyes and a serene gentle smile two delicate pale-gold cat ears a small pink-and-cream cat muzzle a long pale-gold cat tail, bipedal standing gracefully upright on two legs with humanoid body proportions on the sunlit marble temple steps her long flowing radiant golden hair cascading to the ground a thin gold laurel circlet in a snow-white priestess peplos with gold owl-and-olive embroidery, at a respectful DISTANCE in the lower foreground two or three young anthropomorphic cat admirers (suitor cats in fine Greek chitons of blue and red with humanoid body proportions standing upright) gazing up at her with awe and longing one offering a bouquet of white flowers one with a humanoid hand pressed to his chest — all kept far back at the base of the steps admiring from afar never close, sunlit white marble columns olive trees and cyan sea behind, floating golden pollen motes and soft sun-rays, a gentle golden vignette around the edges marking the dream-memory, palette warm radiant nostalgic gold-and-cream with soft cyan, bittersweet atmosphere of beauty that was once adored from a distance, NO snakes NO scales on Medusa here, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 16 (sent_017)

**Текст:** Теперь взглянуть на неё значило застыть камнем навсегда.

**Промпт:** gorgon garden of statues, highly detailed pixel art, 9:16 vertical composition, sombre dramatic wide shot inside the gloomy cavern of Medusa the cursed Gorgon, in the midground Medusa a tall greenish-grey-and-bronze scaled anthropomorphic cat character with cold luminous jade-green eyes glowing faintly small ivory fangs two perked dark-bronze cat ears with brass rings a slim greenish-grey cat muzzle a long bronze-scaled cat tail, bipedal standing upright on two legs with humanoid body proportions turned partly away her head bowed she does not want to look, in her tattered dark-bronze-and-deep-green peplos with snake-scale embroidery a serpent-clasp belt her crown of writhing dark-green-and-bronze stylized cartoon snakes with ruby-glint eyes, all around her across the cave floor a SILENT GARDEN OF GREY STONE STATUES — several solid intact weathered grey-marble figures of anthropomorphic cat travellers and would-be heroes frozen forever in poses of awe defence or terror (one shielding his eyes one reaching out one stepping back) each a complete unbroken statue cracked faintly with pale moss NOT broken NOT decapitated no bones, the statues lit by the cold pale-green glow radiating from Medusa, the obsidian cave walls and a faint shaft of grey daylight from the cave mouth, palette desolate grey stone and cold pale-green glow in deep obsidian shadow, tragic atmosphere of a curse that turns every visitor to lifeless stone told with mournful dignity NOT horror, no blood no gore no wounds no skulls no skeletons no broken statues, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 17 (sent_018)

**Текст:** Спустя годы за её головой придёт юный Персе́й.

**Промпт:** perseus approaching cave silhouette, highly detailed pixel art, 9:16 vertical composition, dramatic atmospheric medium shot at the mouth of the gorgon cave at cold dusk, in the foreground seen from behind and in three-quarter silhouette Perseus the young Greek hero a brave young sandy-gold-and-cream short-haired tabby anthropomorphic cat character with bright determined emerald-green eyes two perked sandy-gold cat ears a small cream-and-pink cat muzzle a long sandy-gold cat tail, bipedal standing upright on two legs with humanoid body proportions in a cautious advancing stance, in his short white-and-bronze Greek tunic with a bronze shoulder clasp a wide brown leather belt leather sandals a short red travel cloak streaming behind his short tousled sandy-gold hair with a small bronze laurel circlet, raising his tall round polished bronze MIRROR SHIELD before him angled so its mirror surface faintly catches a small reflected glint of pale-green glow from deep in the cave a curved bronze sickle-sword (harpe) in his other humanoid hand golden winged sandals at his ankles, deep inside the dark cave behind him the faint distant silhouette and pale-green eye-glow of Medusa the gorgon waiting among her grey statues — small and shadowed in the background, the rocky cave entrance jagged stone the cold dusk sky and a sliver of moon behind Perseus, palette cold dusk-blue and obsidian with the warm bronze glint of the mirror shield and a distant sickly pale-green glow, tense atmosphere of a hero arriving to confront the monster — the bridge to a different tale, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 18 (sent_019)

**Текст:** Но это уже совсем другая история.

**Промпт:** mirror shield reflection closing, highly detailed pixel art, 9:16 vertical composition, evocative cinematic closing close-up of the tall round polished bronze MIRROR SHIELD of Perseus held up in the foreground filling much of the frame its highly reflective polished bronze surface engraved with a small owl of Athena, in the mirror's reflection appears the small framed image of Medusa the cursed Gorgon a greenish-grey-and-bronze scaled anthropomorphic cat character with cold luminous jade-green eyes (the same jade-green that were once a maiden's) and a crown of stylized dark-green-and-bronze cartoon snakes with ruby-glint eyes — but caught in the bronze reflection her glowing eyes look strangely sorrowful rather than fierce, a sliver of the young hero's sandy-gold humanoid hand and emerald-green eye visible at the edge of the frame holding the shield, the dim obsidian cave and a faint pale-green glow around the reflected gorgon, the bronze mirror catching one warm glint of dusk light from the cave mouth, palette deep obsidian-and-green with warm reflective bronze and a melancholy pale-green glow, open-ended «to be continued» atmosphere bridging to the tale of Perseus told with quiet melancholy, no blood no gore, NO humans NO people NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement
