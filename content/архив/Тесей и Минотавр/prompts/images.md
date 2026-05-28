# Тесей и Минотавр

<!--
Формат файла:
- `# Название` — заголовок мифа (используется для имени папки в content/)
- `## Сцена N (sent_NNN — шот M)` — порядковый номер визуального шота для
  imagefx_runner. Картинки сохранятся в images/review_images/scene_NN/vN.jpg.
- `**Текст:**` — закадровый текст (на русском).
- `**Промпт:**` — промпт для ImageFX / Nano Banana (одна строка, англ.).

Всего 16 предложений → 23 визуальных шота на ~1:00–1:10 видео.
7 длинных предложений разбиты на 2 шота для динамики, остальные — 1 шот.

Маппинг sentence ↔ scene_NN (для последующего video.md и pyCapCut):
  sent_001 → scene_01                    (1 шот)  интро
  sent_002 → scene_02 + scene_03         (2 шота) проигранная война + чёрный корабль
  sent_003 → scene_04                    (1 шот)  пустая гавань Афин
  sent_004 → scene_05                    (1 шот)  вход в Лабиринт
  sent_005 → scene_06 + scene_07         (2 шота) Минотавр + происхождение
  sent_006 → scene_08                    (1 шот)  следы погибших — кости и тени
  sent_007 → scene_09                    (1 шот)  Тесей вызывается во дворце
  sent_008 → scene_10 + scene_11         (2 шота) посадка + клятва отцу
  sent_009 → scene_12                    (1 шот)  встреча с Ариадной на Крите
  sent_010 → scene_13 + scene_14         (2 шота) Ариадна вручает нить + у входа
  sent_011 → scene_15 + scene_16         (2 шота) бой с Минотавром + силуэт зверя
  sent_012 → scene_17 + scene_18         (2 шота) выход по нити + отплытие
  sent_013 → scene_19                    (1 шот)  забытый белый парус на корабле
  sent_014 → scene_20 + scene_21         (2 шота) Эгей видит чёрный + пустая скала
  sent_015 → scene_22                    (1 шот)  Эгейское море широкий план
  sent_016 → scene_23                    (1 шот)  возмужавший Тесей задумчиво

Стилевой каркас (одинаковый во всех сценах):
highly detailed pixel art, 9:16 vertical composition, ancient Greek setting,
anthropomorphic bipedal cat characters (NOT real four-legged cats),
humanoid body proportions, standing/walking/gesturing like humans,
NO humans, NO people, NO real four-legged cats,
modern detailed pixel art style, warm cinematic lighting,
no text, no letters, no camera movement

КАРТОЧКИ ПЕРСОНАЖЕЙ (копировать в промпт каждой сцены дословно):

Theseus = "Theseus the young Athenian prince hero, a lean athletic
golden-tan-and-cream tabby anthropomorphic cat character with bright
determined emerald-green eyes and a youthful clean-shaven face, two perked
tabby cat ears on top of his head, a distinct cat muzzle, a long graceful
tabby cat tail, bipedal standing upright on two legs like a human with
humanoid body proportions, short tousled tan hair with a thin gold circlet,
wearing a short white-and-blue Greek warrior chiton draped over one
shoulder belted with a wide leather strap, leather sandals laced up his
calves, a polished bronze breastplate with embossed wave patterns, a
sheathed short bronze xiphos sword at his hip, and a long blue cloak
fastened with a circular bronze brooch"

Aegeus = "King Aegeus the elderly Athenian king, a gray-and-white silver
tabby anthropomorphic cat character with weary wise pale-blue eyes and a
long well-kept silver beard, two slightly drooping silver-gray cat ears,
a graying cat muzzle, a long silver cat tail, bipedal standing upright on
two legs with humanoid body proportions, wearing a long flowing royal-blue
Greek royal robe with silver embroidered laurel pattern at the hem, a wide
leather belt with silver clasps, an olive-leaf gold crown set on his
white-streaked head, a long ornate wooden staff in one humanoid hand"

Minos = "King Minos the stern Cretan king, a tall imposing solid-black
anthropomorphic cat character with cold piercing yellow eyes and a sharp
pointed black beard, two erect black cat ears, a fierce black cat muzzle,
a long black cat tail held stiffly, bipedal standing upright on two legs
with humanoid body proportions, wearing a heavy deep-crimson Cretan royal
robe with embroidered gold double-axe symbols, layered draped folds over
one shoulder, a wide gold belt with rubies, a tall pointed gold-and-jeweled
Cretan crown carved with bull horns at the top, gold rings on his humanoid
black-furred fingers"

Ariadne = "Princess Ariadne the gentle young daughter of King Minos, a
graceful slender snow-white-and-pale-cream calico anthropomorphic cat
character with large kind sapphire-blue eyes and delicate features, two
small perked white cat ears, a small pink-and-white cat muzzle, a long
fluffy white cat tail, bipedal standing upright on two legs with humanoid
body proportions, wearing a flowing pale-blue and white Greek chiton with
subtle gold embroidered wave patterns at the hem, a thin silver belt,
leather sandals, long wavy pale-cream hair flowing down her back held with
a small simple gold tiara"

Minotaur = "the Minotaur the dread feline beast of the Labyrinth, a
massive towering anthropomorphic cat character with shaggy dark-brown-and-
black fur, a huge muscular humanoid body bipedal standing upright on two
thick humanoid legs body upright not on four legs, two heavy curved
sweeping bull horns growing out from the sides of his head between his
cat ears, two erect dark cat ears with tufted tips, a fierce dark cat
muzzle with bared fangs, smoldering glowing crimson-red feline eyes with
vertical slit pupils, a brass ring through his cat nose, a long thick
dark cat tail, broad muscular shoulders with thick dark mane around his
neck like a lion's, wearing only a simple tattered dark loin-cloth and
heavy iron shackles around his wrists, no weapons just massive humanoid
cat-paw hands with sharp claws — STRICTLY a feline cat character with
bull horns and a brass nose-ring, NOT a real bull, NOT a bull-headed
creature, NOT a real four-legged cat, but a unique cat-Minotaur hybrid
keeping a clear cat muzzle and cat ears under the horns"

Pasiphae = "Queen Pasiphae of Crete, a regal cream-and-tan calico
anthropomorphic cat character with large sad violet eyes and a delicate
muzzle, two perked cream-cat ears, a long cream cat tail, bipedal standing
upright on two legs with humanoid body proportions, wearing a layered deep
sea-green Cretan court gown with gold embroidered wave and double-axe
patterns, a tall ornate gold Cretan tiara, long wavy cream hair flowing
down her shoulders" (только в Сцене 7)

Разнообразие окружения: пустая гавань Афин с пирсом и пришвартованным
чёрным кораблём, Афинский акрополь с белыми колоннами и оливковыми рощами,
дворец Эгея с тронным залом и фресками, открытое море с волнами и
дельфинами, скалистые берега острова Крит, кносский дворец с красными
колоннами и фресками быков, каменные коридоры Лабиринта освещённые
факелами с резьбой бычьих голов на стенах, вход в Лабиринт — массивные
бронзовые ворота, мыс Сунион — высокая отвесная скала над морем, ночной
звёздный небосвод над морем, рассветное небо в розовых и оранжевых тонах,
закатное небо над Эгейским морем, греческие триремы с чёрными и белыми
парусами, портовая площадь Афин с амфорами и торговцами, кипарисы и
оливковые деревья на холмах. Варьировать ракурсы (крупный план, средний,
общий, сверху, низкий ракурс, силуэт против неба) и освещение
(утро/полдень/закат/ночь/огонь факелов/лунный свет).

КРИТИЧНО для динамичных сцен (бой с Минотавром, бег по Лабиринту,
прыжок на корабль) — явно прописывать человеческую позу: "human-like
combat stance, body upright not on four legs", "humanoid arms gripping
sword", "humanoid legs running upright". В сценах 15, 16, 17, 20 герои в
активном движении — без явной позы они скатываются в обычных кошек на
четвереньках.

ОГРАНИЧЕНИЯ ПЛАТФОРМ (TikTok / YouTube Shorts):
- Бой с Минотавром (сцены 15-16) — БЕЗ КРОВИ, БЕЗ РАН. Сцена 15 —
  momentum и блеск меча. Сцена 16 — силуэт поверженного зверя в темноте,
  без добивания в кадре, растворение в тени и пыли. Negative: no blood,
  no gore, no wounds, no carcass.
- Гибель Эгея (сцены 20-21) — НЕ показывать прыжок и не показывать тело.
  Сцена 20 — Эгей одиноко на скале против горизонта с чёрным парусом.
  Сцена 21 — пустая скала, ветер треплет упавший плащ, волны внизу,
  без фигуры человека/кота. Подача через намёк, не через действие.

ВИЗУАЛЬНЫЕ МОТИВЫ:
- Чёрный парус — главный лейтмотив (сцены 3, 10, 19, 20)
- Нить Ариадны — ключевой объект (сцены 13, 14, 15, 17), тянется красным
  или золотым шёлком вдоль каменных стен
- Бычьи рога — у Минотавра, на колоннах кносского дворца, в декоре трона
- Лабиринт — каменные коридоры, факелы, тени, спирали и тупики
- Афины — голубой и золотой, маслины, сова Афины как камео
  (например, на знамени корабля или на гербе дворца Эгея)

Кошачьи декоративные мотивы (статуи котов, вазы с котами, фрески с
котами) — уместны во дворцах Афин и Кносса, но НЕ в Лабиринте, на
скалах и в открытом море. Лабиринт оформлен бычьими мотивами, скалы и
море — обычный греческий пейзаж без принудительных кошачьих деталей.
-->

## Сцена 1 (sent_001)

**Текст:** Тесе́й и Минота́вр. Миф за минуту.

**Промпт:** highly detailed pixel art, 9:16 vertical, epic cinematic title shot, dramatic standoff composition of two rivals locked in fierce eye contact across a stone Labyrinth chamber, in the foreground left Theseus the young Athenian prince hero a lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright determined emerald-green eyes glaring intensely across the chamber two perked tabby cat ears a distinct cat muzzle a long tabby cat tail tense and flicked back, bipedal standing upright on two legs with humanoid body proportions in a braced low combat-ready stance body upright not on four legs, short tousled tan hair with a thin gold circlet, wearing a short white-and-blue Greek warrior chiton with a polished bronze breastplate embossed with wave patterns and a long blue cloak rippling behind him, his humanoid right hand drawing his sheathed bronze xiphos sword the blade half-pulled out of the scabbard catching the torchlight, facing him directly across the chamber the Minotaur the dread feline beast of the Labyrinth a massive towering anthropomorphic cat character with shaggy dark-brown-and-black fur a huge muscular humanoid body bipedal standing upright on two thick humanoid legs body upright not on four legs two heavy curved sweeping bull horns growing out from the sides of his head between his erect dark cat ears with tufted tips a fierce dark cat muzzle with bared fangs smoldering glowing crimson-red feline eyes with vertical slit pupils locking onto Theseus a brass ring through his cat nose a long thick dark cat tail lashing slowly thick dark mane around his neck like a lion's wearing only a tattered dark loin-cloth and heavy iron shackles around his wrists his massive humanoid cat-paw hands flexed open showing sharp claws his horned head lowered slightly in silent challenge, between them on the cracked stone floor a single bright vivid red thread of Ariadne snaking from the foreground past their feet into the darkness behind the Minotaur, the setting a vast circular stone chamber of the Labyrinth with high vaulted ceilings walls carved with relief friezes of bull heads and double-axes the corridors beyond fading into deep cold purple-black darkness, a single bronze brazier of bright orange flame burning between them throwing two towering rim-lit shadows onto the curved walls behind both figures lit dramatically from below by the brazier flame and from above by a single distant torch, deep crimson and black color palette with hot orange firelight, charged tense pre-combat moment of two locked rivals about to clash, mythological standoff atmosphere, NO humans, NO people, NO real four-legged bulls, NO bull-headed creatures, NO real four-legged cats, only the feline cat-Minotaur with bull horns keeping a clear cat muzzle, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 2 (sent_002 — шот 1)

**Текст:** Афи́ны проиграли войну Кри́ту и платили жуткую дань: каждые девять лет царю Мино́су отправляли семерых юношей и семерых девушек.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic medium-wide shot of a desolate aftermath of a sea battle on the harbour of Athens at dusk, broken Athenian triremes with shattered hulls and torn sails partly sunk in the shallow water of the harbour, splintered oars and burning torches floating among the waves, a single defeated bipedal Athenian warrior cat character with humanoid body proportions in dented bronze armor and a torn blue cloak kneeling on the stone pier with humanoid knees and lowered head one humanoid hand on a fallen blue-and-gold standard with the silver owl of Athena, in the background another bipedal Cretan warrior cat character with humanoid body proportions in dark crimson armor and a tall horned helmet standing tall over the harbour holding a tall spear, smoke and orange embers drifting in the air, the Athenian acropolis silhouetted on a hill behind with white columns barely visible through smoke, mournful defeated atmosphere, deep blue and orange dusk color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 3 (sent_002 — шот 2)

**Текст:** Афи́ны проиграли войну Кри́ту и платили жуткую дань: каждые девять лет царю Мино́су отправляли семерых юношей и семерых девушек.

**Промпт:** highly detailed pixel art, 9:16 vertical, sweeping wide cinematic shot of a single tall Greek trireme ship with stark fully unfurled black sails leaving the harbour of Athens at grey dawn, the dark hull cutting through silver-blue calm water leaving a long white wake, on its deck fourteen young bipedal anthropomorphic cat characters of varied tabby and calico fur in plain undyed white short Greek tunics with humanoid body proportions standing in two solemn rows their heads lowered their cat tails drooping, a single bipedal helmsman cat in a darker tunic at the stern with a humanoid hand on the steering oar, the great mast and the black sail silhouetted against a low pinkish dawn sky, distant Athenian acropolis with white columns receding behind on a hill, a flock of seagulls in the air, the silver owl of Athena symbol on the prow, sombre tribute-payment atmosphere, mournful and inevitable, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 4 (sent_003)

**Текст:** Назад не возвращался никто.

**Промпт:** highly detailed pixel art, 9:16 vertical, hauntingly empty wide shot of the harbour of Athens at grey overcast morning, the long stone pier completely empty no ships docked at it just dark seawater lapping against barnacled stones, a single forgotten wreath of white flowers floating in the water near the pier, on the shore a small huddled group of bipedal anthropomorphic cat characters in mourning grey and dark blue tunics with humanoid body proportions standing far back from the pier with humanoid hands clasped — mothers and fathers waiting in vain, their cat tails drooping their cat ears flattened, the white columns of the Athenian acropolis cold and distant on the hill behind, a flock of black ravens circling silently in the pale grey sky, a single fallen olive branch on the pier stones, oppressive cold silent grief atmosphere, muted blue-grey and pale-yellow color palette, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 5 (sent_004)

**Текст:** А исчезали они в Лабири́нте.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic wide low-angle shot of the colossal entrance to the Labyrinth on Crete at dusk, two massive ornate bronze double-doors set into a towering stone archway carved with deep spirals and bull-horn motifs slowly creaking open inward into pitch-black darkness, just inside the threshold pale flickering torchlight reveals stone walls disappearing into a maze of corridors, a long single-file procession of fourteen young bipedal anthropomorphic cat characters with humanoid body proportions in plain white tunics walking solemnly through the doorway with humanoid hands at their sides their cat tails low their heads bowed, two stern bipedal Cretan guard cat characters in dark crimson armor humanoid body proportions with tall horned helmets and spears standing on either side of the doorway, fragments of older offerings — broken pottery, withered flower wreaths, scraps of fabric — strewn at the foot of the doors, deep cold purple-blue dusk sky behind the archway with a single bright evening star, ominous silent foreboding atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 6 (sent_005 — шот 1)

**Текст:** В сердце Лабири́нта жил Минота́вр — получеловек-полубык, сын царицы и быка из моря.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic medium-close shot of the Minotaur the dread feline beast of the Labyrinth a massive towering anthropomorphic cat character with shaggy dark-brown-and-black fur, a huge muscular humanoid body bipedal standing upright on two thick humanoid legs body upright not on four legs, two heavy curved sweeping bull horns growing out from the sides of his head between his erect dark cat ears with tufted tips, a fierce dark cat muzzle with bared fangs, smoldering glowing crimson-red feline eyes with vertical slit pupils, a brass ring through his cat nose, a long thick dark cat tail lashing slowly, broad muscular shoulders with a thick dark mane around his neck like a lion's, wearing only a simple tattered dark loin-cloth and heavy iron shackles around his wrists, standing in the heart of the stone Labyrinth in a circular chamber with high vaulted stone ceilings and walls carved with relief friezes of bull heads and double-axes, a single bronze brazier of orange flame burning in the center casting his colossal horned shadow against the curved wall behind, scattered piles of broken pottery old bronze armor and torn fabric on the stone floor at his feet, low growling steam rising from his cat muzzle, ominous foreboding atmosphere, deep crimson and black color palette with orange firelight, NO humans, NO people, NO real four-legged bulls, NO bull-headed creatures, NO real four-legged cats, only feline cat-Minotaur with bull horns keeping a clear cat muzzle, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 7 (sent_005 — шот 2)

**Текст:** В сердце Лабири́нта жил Минота́вр — получеловек-полубык, сын царицы и быка из моря.

**Промпт:** highly detailed pixel art, 9:16 vertical, dreamy mythological flashback shot in soft sepia and gold tones, on the left half Queen Pasiphae of Crete a regal cream-and-tan calico anthropomorphic cat character with large sad violet eyes and a delicate muzzle two perked cream cat ears a long cream cat tail bipedal standing upright on two legs with humanoid body proportions wearing a layered deep sea-green Cretan court gown with gold embroidered wave and double-axe patterns and a tall ornate gold Cretan tiara her long wavy cream hair flowing she stands on a sea-cliff her humanoid hand reaching out toward the waves below, on the right half rising out of the surf a massive snow-white sacred bull a huge muscular four-legged ox-bull with golden curving horns and pale glowing eyes, water cascading from his flanks, divine — strictly a real bull on four legs in this single flashback only as it is the divine bull from the sea — radiating soft gold divine aura, between them swirling sea-foam and golden divine sparkles forming the small silhouette of a feline cat-Minotaur child — clearly an anthropomorphic cat shape with a cat muzzle, two cat ears, and small curved bull horns growing between the ears, hinting at their offspring, distant cliffs of Crete in the background under a mythic dawn sky of pink and gold, dreamlike origin-story atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 8 (sent_006)

**Текст:** Зверь, от которого никто не уходил живым.

**Промпт:** highly detailed pixel art, 9:16 vertical, eerie wide shot of a long winding stone corridor of the Labyrinth lit by a few sparse flickering torches in iron sconces, the floor and walls scattered with grim evidence of past visitors — broken bronze swords, dented helmets, torn pieces of white tunic fabric, scratches of claws on the walls, a single forgotten wreath of olive leaves on a low stone ledge, the walls carved with bull-horn motifs and shallow spirals, deep shadows pooling in side passages disappearing into darkness, in the deepest shadow at the far end of the corridor two small smoldering crimson-red feline cat eyes with vertical slit pupils — the distant glowing eyes of the cat-Minotaur — barely visible suggesting his lurking presence without showing him directly, no figures in this shot only the aftermath, oppressive doom-laden silence atmosphere, deep cold purple shadows with warm orange torchlight, no blood no gore no wounds, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 9 (sent_007)

**Текст:** Молодой царевич Тесе́й, сын афинского царя Эге́я, не выдержал.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic medium shot of the throne room of King Aegeus's Athenian palace at golden hour, Theseus the young Athenian prince hero a lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright determined emerald-green eyes and a youthful clean-shaven face, two perked tabby cat ears, a distinct cat muzzle, a long tabby cat tail flicked with resolve, bipedal standing upright on two legs with humanoid body proportions short tousled tan hair with a thin gold circlet, wearing a short white-and-blue Greek warrior chiton draped over one shoulder a polished bronze breastplate with embossed wave patterns leather sandals and a long blue cloak with a bronze brooch, standing tall in the center of the throne hall his humanoid right hand pressed firmly against his own chest in a vow his humanoid left hand pointing forward with conviction, his cat ears erect his green eyes burning with purpose, on a tall marble dais behind him King Aegeus the elderly Athenian king a gray-and-white silver tabby anthropomorphic cat character with weary wise pale-blue eyes and a long well-kept silver beard, two slightly drooping silver-gray cat ears a graying cat muzzle a long silver cat tail bipedal humanoid body proportions in a long flowing royal-blue Greek robe with silver embroidered laurel pattern and an olive-leaf gold crown, sitting on a tall blue-and-gold marble throne with one humanoid hand on his ornate wooden staff his other humanoid hand raised in alarmed protest his face stricken with worry, white marble columns with blue-painted capitals, frescoes of the silver owl of Athena on the back wall, blue-and-gold banners hanging, late afternoon light streaming through arched windows, tense determined atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 10 (sent_008 — шот 1)

**Текст:** Он сам сел на корабль с чёрными парусами и пообещал отцу: «Если вернусь — сменю чёрный парус на белый».

**Промпт:** highly detailed pixel art, 9:16 vertical, dynamic medium-wide shot of the harbour of Athens at early dawn, Theseus the young Athenian prince hero the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright determined emerald-green eyes and a youthful clean-shaven face two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal in a confident stride upright on two legs with humanoid body proportions in a human-like striding pose body upright not on four legs, wearing a short white-and-blue Greek warrior chiton a polished bronze breastplate leather sandals and a long blue cloak streaming behind him in the sea-wind, his humanoid right hand resting on the hilt of his sheathed bronze xiphos sword his humanoid left hand carrying a small bundled olive-wood case, walking up the wooden gangplank onto a tall Greek trireme ship with stark fully unfurled black sails towering above him, behind him on the pier thirteen other young bipedal anthropomorphic cat characters in plain white tunics with humanoid body proportions following solemnly, the great black sail filling the upper half of the frame against a pale pink dawn sky, the stone pier wet with sea-spray, distant Athenian acropolis with white columns on the hill behind, brave determined atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 11 (sent_008 — шот 2)

**Текст:** Он сам сел на корабль с чёрными парусами и пообещал отцу: «Если вернусь — сменю чёрный парус на белый».

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate emotional medium close-up on the pier of Athens at dawn, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes determined yet softened with affection two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal humanoid body proportions in his short white-and-blue warrior chiton bronze breastplate and blue cloak, kneeling down on one humanoid knee in a respectful son's gesture both his humanoid hands clasping the elderly humanoid hands of his father King Aegeus the gray-and-white silver tabby anthropomorphic cat character with weary wise pale-blue eyes wet with tears and a long silver beard two slightly drooping silver cat ears a graying cat muzzle a long silver cat tail bipedal humanoid body proportions in a long royal-blue robe and olive-leaf gold crown, standing slightly bent over Theseus, a small folded square of plain white sailcloth tucked under Theseus's arm clearly visible, the towering black sail of the trireme rising above them in the background, in the upper-right corner a faint translucent dream-bubble image of the same ship returning with a white sail under blue sky, soft pink sunrise light wrapping their figures, sea birds calling overhead, sombre tender promise atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 12 (sent_009)

**Текст:** На Крите его встретила Ариа́дна — дочь царя Мино́са.

**Промпт:** highly detailed pixel art, 9:16 vertical, beautiful first-meeting medium shot in the courtyard of the Knossos palace on Crete at golden afternoon, Theseus the young Athenian prince hero the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal standing upright on two legs with humanoid body proportions in his short white-and-blue Greek warrior chiton bronze breastplate leather sandals and long blue cloak, just disembarked his hair slightly windblown his humanoid hand on his sword hilt his face surprised arrested by what he sees, opposite him Princess Ariadne the gentle young daughter of King Minos a graceful slender snow-white-and-pale-cream calico anthropomorphic cat character with large kind sapphire-blue eyes and delicate features two small perked white cat ears a small pink-and-white cat muzzle a long fluffy white cat tail bipedal standing upright on two legs with humanoid body proportions, wearing a flowing pale-blue and white Greek chiton with subtle gold embroidered wave patterns a thin silver belt and a small gold tiara her long wavy pale-cream hair flowing, holding a small bowl of fresh fruit in her humanoid hands a single rose-petal in her hair, her face softening with sudden compassion as their eyes meet, between them a charged moment of mutual recognition, behind them tall striking deep-crimson Minoan columns with black and white capitals the famous bull-fresco half-visible on a courtyard wall, lush palace gardens with pomegranate trees, in the far background King Minos the tall imposing solid-black anthropomorphic cat character with cold piercing yellow eyes a sharp pointed black beard two erect black cat ears bipedal humanoid body proportions in a deep-crimson Cretan robe and a tall horned crown standing partly turned away on a high balcony watching coldly, soft golden Mediterranean afternoon light, romantic-fateful first-glance atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 13 (sent_010 — шот 1)

**Текст:** Она влюбилась с первого взгляда и тайно сунула герою клубок нити: «Привяжи у входа. По ней найдёшь дорогу обратно».

**Промпт:** highly detailed pixel art, 9:16 vertical, intimate close-up scene at night in a torch-lit corridor of the Knossos palace on Crete, Princess Ariadne the gentle slender snow-white-and-pale-cream calico anthropomorphic cat character with large sapphire-blue eyes wide with urgent affection two small perked white cat ears a small pink-and-white cat muzzle a long fluffy white cat tail bipedal standing upright on two legs with humanoid body proportions in her flowing pale-blue and white chiton with gold wave embroidery, leaning closely toward Theseus her humanoid hand pressing a small ball of bright vivid red wool yarn — a thread spool the size of an apple — firmly into his humanoid right palm, her other humanoid hand raised to her own muzzle in a hush gesture asking for silence, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes wide with grateful surprise two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal humanoid body proportions in his white-and-blue chiton bronze breastplate and blue cloak, his humanoid left hand cupped around hers protectively, a single torch in a bronze sconce on the deep-red palace wall casting warm flickering light over them, deep red Cretan column behind them with bull-fresco motifs, soft shadows, charged tender secret atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 14 (sent_010 — шот 2)

**Текст:** Она влюбилась с первого взгляда и тайно сунула герою клубок нити: «Привяжи у входа. По ней найдёшь дорогу обратно».

**Промпт:** highly detailed pixel art, 9:16 vertical, instructive medium shot at the colossal bronze entrance doors of the Labyrinth at dusk, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal kneeling upright on one humanoid knee with humanoid body proportions body upright not on four legs in his white-and-blue chiton bronze breastplate and blue cloak, carefully tying the loose end of the bright vivid red yarn thread to a heavy iron ring set into the stone of the doorway with both his humanoid hands working the knot, the bright vivid red thread visibly extending from the ring across the threshold and disappearing into the dark stone corridor beyond like a single bright crimson line, just behind him in the doorway in the shadows Princess Ariadne the slender snow-white-and-pale-cream calico anthropomorphic cat character with large sapphire-blue eyes two perked white cat ears a long fluffy white cat tail bipedal humanoid body proportions in her pale-blue chiton standing with humanoid hands clasped to her chest watching anxiously, evening sky deep cobalt-blue with the first stars showing above the doorway arch, two flaming torches in iron sconces on either side of the doors casting warm orange light across the stone, careful tense determined atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 15 (sent_011 — шот 1)

**Текст:** В глубине Лабири́нта Тесе́й одолел Минота́вра.

**Промпт:** highly detailed pixel art, 9:16 vertical, intense action shot in the central stone chamber of the Labyrinth lit by a few flickering torches, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes blazing with focused courage two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal in a dynamic combat lunge upright on two legs with humanoid body proportions in a human-like combat stance body upright not on four legs humanoid arms gripping his bronze xiphos sword raised diagonally above his head in a mid-strike pose his blue cloak swept back behind him, charging the Minotaur the dread feline beast of the Labyrinth a massive towering anthropomorphic cat character with shaggy dark-brown-and-black fur a huge muscular humanoid body bipedal standing upright on two thick humanoid legs body upright not on four legs two heavy curved sweeping bull horns growing out from the sides of his head between his erect dark cat ears with tufted tips a fierce dark cat muzzle with bared fangs smoldering glowing crimson-red feline eyes with vertical slit pupils a brass nose-ring a thick dark mane around his neck like a lion's a long thick dark cat tail lashing broad shoulders wearing a tattered loin-cloth and broken iron shackles, who is rearing back with massive humanoid cat-paw arms swung wide claws extended in a defensive snarl his cat muzzle wide open in a roar steam rising from his nostrils, the bright vivid red thread of Ariadne extending from the dark corridor behind Theseus along the floor and around a stone column anchoring his retreat path, sparks and dust kicked up around their feet, the bronze brazier of orange flame in the chamber illuminating their silhouettes from below, deep crimson and black color palette, no blood no gore no wounds, dynamic mythic combat atmosphere, NO humans, NO people, NO real four-legged cats, NO real four-legged bulls, NO bull-headed creatures, only feline cat-Minotaur with bull horns keeping a clear cat muzzle, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 16 (sent_011 — шот 2)

**Текст:** В глубине Лабири́нта Тесе́й одолел Минота́вра.

**Промпт:** highly detailed pixel art, 9:16 vertical, dramatic aftermath silhouette shot in the same labyrinth chamber moments later, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal standing upright on two legs with humanoid body proportions in a human-like victorious upright stance body upright not on four legs in his white-and-blue chiton bronze breastplate and torn blue cloak his lowered bronze xiphos sword in his humanoid right hand his chest heaving from breath, in front of him on the chamber floor only the colossal silhouette shadow of the fallen cat-Minotaur cast against the stone wall — a vast feline shape with two curved bull horns above the cat ears and arms thrown wide already half-dissolving into wisps of dark smoke and drifting embers — the actual figure of the beast no longer visible only his dissipating horned cat-silhouette and a few scattered iron shackle pieces on the floor, the bright vivid red thread leading away from the chamber back toward the corridor still anchored, the bronze brazier flame dim and almost out, soft fall of gold dust and dark smoke particles, no blood no gore no wounds no body no carcass only shadow silhouette and dissipation, victorious yet sober atmosphere, deep purple and ember-orange color palette, NO humans, NO people, NO real four-legged cats, NO real four-legged bulls, NO bull-headed creatures, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 17 (sent_012 — шот 1)

**Текст:** По нити вышел наружу, забрал Ариа́дну и поплыл домой.

**Промпт:** highly detailed pixel art, 9:16 vertical, hopeful medium shot at the colossal bronze entrance doors of the Labyrinth at the moment of dawn, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes weary but triumphant two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal striding upright through the threshold on two legs with humanoid body proportions in a human-like walking pose body upright not on four legs in his white-and-blue chiton bronze breastplate leather sandals and torn blue cloak his sheathed bronze xiphos sword on his hip, gathering up the bright vivid red thread in his humanoid hands as he walks the thread spooling around his humanoid wrist, just outside the doorway Princess Ariadne the slender snow-white-and-pale-cream calico anthropomorphic cat character with large sapphire-blue eyes filled with relief and joy two perked white cat ears a small cat muzzle a long fluffy white cat tail bipedal standing upright on two legs with humanoid body proportions in her pale-blue chiton, running forward to meet him her humanoid arms outstretched her cat tail flowing behind her, behind them the heavy bronze doors slowly closing on the dark Labyrinth corridors, the first warm pink-and-gold rays of dawn breaking over the horizon, the cobalt-blue night sky still holding a few last stars above, a palace torch dying out, hopeful liberated atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 18 (sent_012 — шот 2)

**Текст:** По нити вышел наружу, забрал Ариа́дну и поплыл домой.

**Промпт:** highly detailed pixel art, 9:16 vertical, lyrical wide shot of a Greek trireme ship sailing across the open Aegean Sea in golden afternoon light, the same ship from earlier with stark fully unfurled black sails still raised cutting through deep teal-blue waves, on the deck Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal standing upright on two legs at the bow with humanoid body proportions in his white-and-blue chiton bronze breastplate and blue cloak rippling in the sea-wind one humanoid arm around the shoulders of Princess Ariadne the slender snow-white-and-pale-cream calico anthropomorphic cat character with large sapphire-blue eyes two perked white cat ears a long fluffy white cat tail bipedal humanoid body proportions in her pale-blue chiton with her humanoid hand resting on the wooden railing her cream hair flowing back in the wind, the thirteen rescued young bipedal anthropomorphic cat characters in plain white tunics with humanoid body proportions visible behind them on the deck looking joyful, a pod of leaping dolphins in the foreground waves, the towering black sail filling the upper frame against pink-and-gold sunset clouds, the silver owl of Athena symbol on the prow, the receding cliffs of Crete tiny on the horizon, distant gull cries, joyful homebound atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 19 (sent_013)

**Текст:** Но в радости герой забыл главное — поднять белый парус.

**Промпт:** highly detailed pixel art, 9:16 vertical, foreboding medium-wide shot on the deck of the same Greek trireme as it nears the coast of Attica at late afternoon, Theseus the lean athletic golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes lit with joyful relief two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal laughing upright on two legs with humanoid body proportions in his white-and-blue chiton bronze breastplate and blue cloak both his humanoid arms thrown wide open toward the approaching shore his face turned toward Ariadne with a joyful smile, beside him Princess Ariadne the slender snow-white-and-pale-cream calico anthropomorphic cat character bipedal humanoid body proportions in her pale-blue chiton laughing with him her cat tail held high, but in the upper third of the frame the towering black sail of the trireme is still fully raised dominating the sky against pink sunset clouds clearly NOT replaced — and in the foreground at the foot of the mast a small folded square of bright clean white sailcloth lies forgotten on the deck planks tied with a blue ribbon caught under a coiled rope half-hidden in shadow, the bright color contrast between the pristine white folded cloth and the towering black sail drawing the eye, gulls circling overhead, a faint dark cliff of Cape Sounion just visible on the horizon, ironic tragic foreshadowing atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 20 (sent_014 — шот 1)

**Текст:** Эге́й увидел с берега чёрный — и не пережил этой вести.

**Промпт:** highly detailed pixel art, 9:16 vertical, devastating wide medium shot atop the high white limestone cliff of Cape Sounion overlooking the Aegean Sea at sunset, King Aegeus the elderly Athenian king the gray-and-white silver tabby anthropomorphic cat character with weary wise pale-blue eyes now wide with shattering grief and a long well-kept silver beard two slightly drooping silver-gray cat ears a graying cat muzzle a long silver cat tail bipedal standing upright on two legs alone at the cliff's edge with humanoid body proportions in his long flowing royal-blue Greek robe with silver embroidery his olive-leaf gold crown still on his head his long ornate wooden staff fallen from his humanoid hand onto the rocks beside him, both his humanoid hands raised to his cat muzzle in a frozen gasp of horror, his royal-blue robe whipping in the strong sea-wind, far out on the deep teal sea below a tiny silhouette of the Greek trireme is approaching with its towering BLACK sail still fully raised against a vast burning red-orange sunset sky with long golden god rays piercing scattered clouds, white seabirds wheeling around the cliff, the white Greek temple ruins of Cape Sounion partly visible behind the king on the headland, devastating tragic atmosphere of unbearable grief, no blood no gore, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 21 (sent_014 — шот 2)

**Текст:** Эге́й увидел с берега чёрный — и не пережил этой вести.

**Промпт:** highly detailed pixel art, 9:16 vertical, mournful empty wide shot of the same high white limestone cliff of Cape Sounion at deep dusk just minutes later, the cliff edge now completely empty no figure of any kind only the king's long flowing royal-blue Greek robe with silver embroidery and his olive-leaf gold crown left lying together on the bare windswept rocks at the edge, the wooden staff lying nearby, the wind tugging at the empty robe and making the silver embroidery glint, far below the deep teal-and-charcoal sea crashing against the cliff base with white foam, a few white feathers from a passing seabird drifting down through the air, the towering black sail of the trireme still tiny on the dark horizon under the dimming sunset sky now fading to deep purple-blue, the white Greek temple ruins on the headland silhouetted against the last glow of sunset, a single silver evening star above the temple, no figure of any person or cat in this shot only the absence and the wind, profound sorrow, no body no carcass, mournful poignant elegiac atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 22 (sent_015)

**Текст:** С тех пор то море зовётся Эге́йским.

**Промпт:** highly detailed pixel art, 9:16 vertical, sweeping serene establishing wide aerial shot of the vast deep-blue Aegean Sea at golden dawn, gentle rolling waves stretching to a far misty horizon scattered with rocky Greek islands silhouetted in the morning haze, several distant white-sailed Greek ships spread across the water their tiny sails catching the early gold light, a pod of leaping dolphins arcing through the waves in the middle distance, a flock of white gulls wheeling against the pink-and-gold dawn sky, on the right side of the frame the cliff of Cape Sounion in the foreground with the white columns of the temple ruin, a single faint translucent ghostly image of King Aegeus's silver-tabby silhouette in his royal-blue robe — gentle and dignified — fading into the morning mist above the cliff like a memory watching over the sea, soft golden warm light wrapping the whole scene, peaceful mythological closing-of-a-chapter atmosphere, no figure of any person or cat in clear focus only the reflective vast sea, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 23 (sent_016)

**Текст:** А Тесе́й всю жизнь помнил: одна забытая мелочь стоит дороже победы.

**Промпт:** highly detailed pixel art, 9:16 vertical, reflective intimate medium shot of the throne room of King Aegeus's Athenian palace many years later at sunset, Theseus now a mature king the lean-but-broader golden-tan-and-cream tabby anthropomorphic cat character with bright emerald-green eyes thoughtful and weighted with experience and a thin neat tabby beard two perked tabby cat ears a distinct cat muzzle a long tabby cat tail bipedal seated upright on the same blue-and-gold marble throne with humanoid body proportions in a long blue royal robe with silver embroidered laurel pattern at the hem and his father's olive-leaf gold crown on his head, leaning slightly forward with one humanoid hand resting on his cat muzzle in deep thought the other humanoid hand draped over the armrest holding a small folded square of clean white sailcloth — the same white sail from the ship — looking down at it pensively, his cat tail curled at his feet, beside the throne his late father's long ornate wooden staff respectfully propped upright, white marble columns frescoes of the silver owl of Athena and a quiet small portrait fresco of King Aegeus on the back wall, late golden hour light pouring through arched windows casting long warm shadows, melancholy wise reflective atmosphere, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement
