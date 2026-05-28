# Фемида

<!--
Формат файла:
- `# Название` — заголовок мифа (используется для имени папки в content/)
- `## Сцена N (sent_NNN — шот M)` — порядковый номер визуального шота для
  imagefx_runner. Картинки сохранятся в images/review_images/scene_NN/vN.jpg.
- `**Текст:**` — закадровый текст (на русском).
- `**Промпт:**` — промпт для ImageFX / Nano Banana (одна строка, англ.).
  Первые 3-4 слова каждого промпта = уникальный subject-маркер сцены.

Всего 23 предложения → 18 визуальных шотов на ~1:00–1:10 видео (после
объединения 5 пар сцен 2026-05-22: 8+9, 14+15, 16+17, 19+20, 22+23 —
каждая пара сжимается до одного кадра, видео-промпт под пару пишется
один общий, аудио-предложения остаются 23 шт. без сдвига).
- sent_001 (хук) + sent_002 (титул) → scene_01 (один кадр-постер + караоке-титул поверх в pyCapCut)
- остальные сцены — 1 шот; некоторые сцены покрывают пару предложений

Маппинг sentence ↔ scene_NN (для последующего video.md и pyCapCut):
  sent_001 + sent_002 → scene_01            (1 шот)  кадр-крючок «почему закрыла глаза» + караоке-титул поверх
  sent_003           → scene_02             (1 шот)  Фемида зрячая, на троне с весами, гордится
  sent_004           → scene_03             (1 шот)  один взгляд видит вора, лжеца, отравителя (триптих)
  sent_005           → scene_04             (1 шот)  Эллада приходит к ней с подношениями
  sent_006           → scene_05             (1 шот)  таверна — мошенники придумывают уловку
  sent_007           → scene_06             (1 шот)  мошенники наряжаются в богатые тоги
  sent_008           → scene_07             (1 шот)  бедняков переодевают в лохмотья
  sent_009 + sent_010 → scene_08            (1 шот)  крупный план тоги в луче света + Фемида верит наряду (объединено: вместо двух кадров — один метафорический; первоначальный «не заметила подмены» поглощён)
  sent_011           → scene_09             (1 шот)  нищий в рваном плаще перед троном
  sent_012           → scene_10             (1 шот)  свидетели в золоте дают ложную клятву
  sent_013           → scene_11             (1 шот)  богиня выносит «виновен», нищий уходит в пыль
  sent_014           → scene_12             (1 шот)  вечер, пустой тронный зал — Фемида получает страшное известие
  sent_015 + sent_016 → scene_13            (1 шот)  жрец крадёт золото с алтаря (объединено: крупный план гладкой тоги поглощён, остаётся flashback с воровством)
  sent_017 + sent_018 → scene_14            (1 шот)  Фемида окаменела на троне (объединено: крупный план её глаз со слезой поглощён, остаётся стоп-кадр шока)
  sent_019           → scene_15             (1 шот)  Фемида срывает с пояса плотную синюю ленту
  sent_020           → scene_16             (1 шот)  рука с лентой у лица (объединено: финальный «уже завязаны» шот поглощён, остаётся только момент завязывания)
  sent_021           → scene_17             (1 шот)  крупный план её слов «больше никогда — по виду»
  sent_022 + sent_023 → scene_18            (1 шот)  финальный иконический кадр — слепая богиня правосудия в закатном свете (объединено: «слушает и взвешивает» поглощено в финальный sunset-статую)

Стилевой каркас (одинаковый во всех сценах):
highly detailed pixel art, 9:16 vertical composition, ancient Greek setting,
anthropomorphic bipedal cat characters (NOT real four-legged cats),
humanoid body proportions, standing/walking/gesturing like humans,
NO humans, NO people, NO real four-legged cats,
modern detailed pixel art style, warm cinematic lighting,
no text, no letters, no camera movement

КАРТОЧКИ ПЕРСОНАЖЕЙ (копировать в промпт каждой сцены дословно):

Themis-seeing = "Themis the dignified goddess of justice in her seeing form, a
noble graceful pale-marble-white-and-silver anthropomorphic cat character with
deep piercing steel-blue eyes wide open serene and all-knowing, two perked
silver-white cat ears, a small pale-cream cat muzzle, a long fluffy silver-
white cat tail, bipedal standing or seated upright on two legs with humanoid
body proportions body upright not on four legs, wearing a flowing pure-white
floor-length Greek peplos with rich gold embroidery of olive branches and
balance-scales along the hem and along the diagonal shoulder-fold, a wide
deep-blue and bronze waist-sash with a heavy polished bronze clasp shaped
like a tiny balance-scale, leather sandals laced up her humanoid calves,
long flowing platinum-silver hair cascading down her back held by a tall
ornate bronze laurel-leaf crown polished and gleaming, holding a large
bronze balance-scale with two empty bronze pans hanging from a central
bronze beam in her humanoid LEFT hand and a tall straight bronze ceremonial
sword pointed downward in her humanoid RIGHT hand" (для сцен 2, 3, 4, 8, 9, 10, 11, 12, 14 — она зрячая, до кульминации)

Themis-blindfolded = "Themis the dignified goddess of justice in her blinded
form, the same noble pale-marble-white-and-silver anthropomorphic cat
character with two perked silver-white cat ears, a small pale-cream cat
muzzle, a long fluffy silver-white cat tail, bipedal standing or seated
upright on two legs with humanoid body proportions body upright not on four
legs, wearing the same flowing pure-white floor-length Greek peplos with
rich gold embroidery of olive branches and balance-scales along the hem,
her wide deep-blue waist-sash now MISSING (the sash-band was torn off and
tied across her eyes — only the bronze clasp remains on her waist), leather
sandals laced up her humanoid calves, long flowing platinum-silver hair
cascading down her back held by the same tall ornate bronze laurel-leaf
crown, A WIDE THICK DEEP-BLUE-AND-GOLD-EMBROIDERED CLOTH BLINDFOLD (clearly
made from the same deep-blue and gold material as her former waist-sash)
tied firmly around her eyes covering them completely with a neat knot
behind her head, her small pale-cream muzzle calm and serene her head
slightly raised as if listening attentively, holding the same large
bronze balance-scale in her humanoid LEFT hand and the same tall bronze
ceremonial sword pointed downward in her humanoid RIGHT hand" (для сцен 1, 17, 18 — она с завязанными глазами)

Themis-blindfolding = "Themis the dignified goddess of justice in the very
act of binding her own eyes, the same noble pale-marble-white-and-silver
anthropomorphic cat character with deep piercing steel-blue eyes — ONE
eye still uncovered and visible with a single tear sliding down her cheek,
the OTHER eye already covered by the descending deep-blue-and-gold cloth —
two perked silver-white cat ears, a small pale-cream cat muzzle resolute
and grim, a long fluffy silver-white cat tail, bipedal standing upright
on two legs with humanoid body proportions, wearing her flowing pure-white
Greek peplos with gold olive-and-scale embroidery, her wide deep-blue
waist-sash CLEARLY TORN OFF (a frayed empty space at her waist where the
sash used to be — only the bronze clasp remaining), the tall ornate bronze
laurel-leaf crown on her head, holding the large bronze balance-scale
loosely tilting in her humanoid LEFT hand the bronze ceremonial sword
resting against her shoulder, her humanoid RIGHT hand raised to her face
gripping the deep-blue-and-gold cloth strip pulling it across her eyes"
(специально для сцены 16 — момент завязывания)

ConArtists = "Two scheming con-artist anthropomorphic cat characters:
ConArtistA — a sleek dark-tabby anthropomorphic cat with cunning amber
eyes a thin sly grin two perked dark-tabby cat ears a dark-tabby cat muzzle
a long lean tabby cat tail, bipedal humanoid body proportions, his short
slicked-back dark fur freshly groomed;
ConArtistB — a wiry ginger-and-white anthropomorphic cat with darting
green eyes a smug smirk two perked ginger cat ears a small ginger cat
muzzle a long ginger cat tail, bipedal humanoid body proportions, his
ginger fur slicked back.
In their disguised form both are dressed in luxurious deep-crimson-and-gold
or deep-blue-and-gold Greek togas with elaborate gold-thread embroidery
heavy gold chain necklaces gold rings on their humanoid fingers golden
sandals.
In their natural form (tavern scene) they wear plain dirty dark-brown
woollen Greek tunics rough rope belts unkempt fur." (для сцен 5, 6, 8, 10)

Beggar = "the honest beggar a thin tired dark-grey anthropomorphic cat
character with downcast soft brown eyes filled with quiet dignity two
perked grey cat ears a small grey cat muzzle a long thin grey cat tail,
bipedal standing or walking upright on two legs with humanoid body
proportions stoop-shouldered, wearing a tattered torn dirty grey-brown
Greek tunic with frayed edges dust stains and visible patches a knotted
rope belt at his waist worn-out leather sandals or bare humanoid feet,
his short dishevelled grey fur unkempt his face quiet resigned and
honest NOT angry NOT pleading — the visual image of a wronged poor
soul" (для сцен 7, 9, 11)

HonestRichVictim = "an honest middle-class merchant anthropomorphic cat
character who is being stripped of his fine clothes — a kind plump
honey-orange-and-white tabby with worried hazel eyes two perked tabby
cat ears a small honey-cream cat muzzle a long honey-orange tabby cat
tail, bipedal humanoid body proportions, originally dressed in a clean
respectable saffron-yellow Greek tunic with simple gold trim being
yanked off him by the con-artists who replace it with the beggar's
rags" (для сцены 7 — жертва обмана наряда)

Priest = "Themis's treacherous chief priest the real thief — a smug
well-fed silver-grey anthropomorphic cat character with cold pale-yellow
eyes and a sly thin smile two perked silver-grey cat ears a small silver
cat muzzle a long sleek silver-grey cat tail, bipedal standing upright on
two legs with humanoid body proportions, wearing a flowing pristine
deep-purple-and-gold Greek priestly robe with elaborate gold embroidery
of olive branches and balance-scales matching Themis's regalia a wide
gold belt with a polished bronze scale-clasp gold-trimmed sandals, his
short groomed silver-grey fur immaculate a thin gold circlet on his
head" (для сцены 13 — настоящий вор, флешбэк ограбления алтаря)

GoldWitnesses = "two well-dressed false-oath gold-laden anthropomorphic
cat witnesses: WitnessA — a stout brown-tabby anthropomorphic cat with
sly hazel eyes a small smirk two perked tabby cat ears a brown-tabby cat
muzzle a long tabby cat tail; WitnessB — a tall cream-and-white
anthropomorphic cat with shifty pale-green eyes a deadpan expression
two perked cream cat ears a small cream cat muzzle a long cream cat
tail; both bipedal humanoid body proportions, both dressed in luxurious
bright-saffron-yellow-and-gold Greek togas with heavy gold chains thick
gold rings golden sandals freshly groomed fur, their humanoid right
hands raised in oath" (для сцены 10)

PetitionerCrowd = "a humble crowd of three to five ancient-Greek-citizen
anthropomorphic cat characters in plain undyed-cream Greek tunics with
simple woven belts and leather sandals, varied fur colours (one brown-
tabby, one black-and-white, one ginger, one grey, one calico), bipedal
humanoid body proportions, each carrying a humble offering — a small
clay amphora, a wreath of olive leaves, a basket of figs, a single
scroll — their faces respectful and reverent looking up toward the
throne of Themis" (для сцены 4 — толпа просителей)

ОКРУЖЕНИЕ И КЛЮЧЕВЫЕ ЛОКАЦИИ:

Tribunal-court = "the open-air marble tribunal of Themis in classical
ancient Athens — a grand white-marble Greek temple courtroom with tall
fluted white-marble Doric columns rising into a clear blue sky, the
marble floor inlaid with a large bronze balance-scale motif at the
centre, a tall three-stepped white-marble dais leading up to a throne
carved from polished white marble with bronze lion-paw feet and a
backrest shaped like a balance-scale with two suspended bronze pans,
two tall bronze braziers burning warm olive-oil flames flanking the
throne, a sacred olive tree growing behind the throne with silver-
green leaves, sweeping panoramic view of sunny Athens visible between
the colonnade with white-marble city below and bright Mediterranean
sky"

Tavern-night = "a dim Greek tavern at night with low rough wooden
tables clay amphorae of wine flickering oil lamps low whitewashed
arches and a few wooden stools, conspiratorial atmosphere, warm
amber lamplight"

Backalley-day = "a narrow Athens backstreet between two whitewashed
mud-brick walls dusty cobblestones a small olive tree in a clay pot
laundry hanging on lines bright Greek sunlight"

Temple-altar-night = "Themis's marble altar shrine inside her temple
at night, a polished marble altar dressed with offerings — gold coins
in a bronze dish, olive wreaths, scrolls — flickering oil lamps, tall
shadows of olive branches on the wall, a tall bronze balance-scale
statue behind the altar"

Outside-gates = "the broad marble steps leading down from the
tribunal into the dusty road out of Athens, sweeping view of dusty
plains and distant olive groves under late afternoon sun"

ЛЕЙТМОТИВЫ (повторяющиеся визуальные символы):

- Bronze balance-scale — главный символ Фемиды, держит во всех сценах
  кроме flashback (sent_015/scene_13 — жрец у алтаря) и поясная сцена 15
  (срывает ленту). В кульминации scale слегка наклонены — символ
  покачнувшегося правосудия.
- Bronze ceremonial sword — в её правой руке, опущен вниз. Не оружие, символ.
- Deep-blue-and-gold waist-sash → blindfold — ОДИН И ТОТ ЖЕ МАТЕРИАЛ. В сцене
  15 она его срывает с пояса, в сцене 16 повязывает на глаза. В сценах
  1, 17, 18 эта ткань — на глазах. Зритель должен опознать материал.
- Olive branches & laurel — на её короне, в embroidery одежды, в храме.
- White marble + bronze палитра двора правосудия.
- Зрячие глаза = ярко-стальной синий цвет, открытые, проницательные.
  Завязанные глаза = повязка скрывает их полностью, но мордочка спокойная.

ПЛАТФОРМЕННЫЕ ОГРАНИЧЕНИЯ (TikTok / YouTube Shorts):

- Изгнание нищего (сцена 11) — БЕЗ цепей, БЕЗ удара, БЕЗ слёз ужаса. Просто
  его удаляющийся силуэт со спины, спускается по ступеням храма в пыль.
  Подача через печаль, не насилие.
- Кража жреца (сцена 13) — БЕЗ драки, БЕЗ оружия. Только тайный жест: его
  лапа берёт золотую монету с алтаря. Сцена тихая, разоблачительная.
- Сцена 16 (Фемида завязывает глаза) — БЕЗ боли, БЕЗ крови. Это ритуал-
  жест отказа от зрения, не самоослепление. Лента касается век, не более.
- Шок Фемиды (сцена 14) — окаменелое выражение, не агония. Без слёз ярости,
  без сжатых лап, без крика.

КОШАЧЬИ ДЕКОРАТИВНЫЕ МОТИВЫ:

В мраморном тронном зале Фемиды уместны кошачьи фрески (богиня с весами +
коты-просители у её ног) на стенах, кошачьи статуэтки на полках, кошачьи
лапы как ножки трона. НЕ в таверне, НЕ в переулке, НЕ снаружи на ступенях —
там обычный греческий антураж без принудительных кошачьих деталей.

ДИНАМИЧНЫЕ СЦЕНЫ (критическая зона "превращения в четвероногую кошку"):

- Сцена 15 (срывает пояс) — резкое движение рукой, обязательно
  «humanoid arms outstretched», «body upright not on four legs».
- Сцена 16 (поднимает руку с лентой) — поза стоя на двух ногах,
  лапа-рука у лица.

УНИКАЛЬНЫЙ ПРЕФИКС-МАРКЕР (первые 3-4 английских слова в каждом промпте):

1.  lowangle themis hero binding
2.  themis open-eyed bronze throne
3.  triptych thief liar poisoner
4.  hellas crowd worship throne
5.  tavern conspirators plotting disguise
6.  con-artists dressing rich togas
7.  honest merchant given rags
8.  spotlit toga deceives themis
9.  ragged beggar before throne
10. gold witnesses false oath
11. beggar exiled fading dust
12. evening empty tribunal hush
13. priest stealing temple gold
14. themis frozen marble shock
15. themis tearing belt sash
16. themis raising bandage hand
17. blindfolded themis vow oath
18. blindfolded themis sunset statue

Все 18 префиксов уникальны — проверено.
-->

## Сцена 1 (sent_001 + sent_002 — хук + титул караоке поверх)

**Текст:** Почему богиня правосудия закрыла глаза? Не потому что слепа — а потому что увидела слишком много. *(поверх — караоке-титул «Феми́да. Миф за минуту.»)*

**Промпт:** lowangle themis hero binding, highly detailed pixel art, 9:16 vertical composition, dramatic low-angle cinematic movie-poster hero shot looking up from the foot of the marble tribunal steps toward Themis standing tall on the highest step of her open-air court, monumental retention-hook frame designed to STOP a thumb mid-scroll through golden-hour grandeur and heroic silhouette not through cartoon shock, deliberate empty headroom at the top of the frame for the karaoke title overlay and visual weight along the bottom edge, Themis the dignified goddess of justice in the very act of binding her own eyes the same noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes — ONE eye still uncovered and visible glistening with a single tear catching a sharp golden ray of sunset light as it slides down her cheek, the OTHER eye already covered by the descending deep-blue-and-gold cloth — two perked silver-white cat ears, a small pale-cream cat muzzle resolute and grim her chin slightly raised, a long fluffy silver-white cat tail held still behind her, bipedal standing tall upright on two legs with humanoid body proportions body upright not on four legs in a heroic statue-like pose, wearing a flowing pure-white floor-length Greek peplos with rich gold embroidery of olive branches and balance-scales along the hem and along the diagonal shoulder-fold the embroidery catching the bronze-crimson sunset light, her wide deep-blue waist-sash CLEARLY TORN OFF (a frayed empty space at her waist where the sash used to be — only the polished bronze scale-shaped clasp remaining loose at her belt-line), leather sandals laced up her humanoid calves, long flowing platinum-silver hair cascading down her back and lifting slightly in the warm sunset breeze held by a tall ornate bronze laurel-leaf crown polished and gleaming forming a silhouette halo against the burning sky, in her humanoid LEFT hand she holds the large bronze balance-scale extended out to the side with ONE BRONZE PAN HANGING OVER THE EDGE OF THE TOP MARBLE STEP as if over a cliff the central beam tilting and the pans visibly uneven, the tall straight bronze ceremonial sword resting point-down leaning against the side of her humanoid hip its hilt level with her waist its tip planted firmly on the marble step, her humanoid RIGHT hand raised to her face gripping a wide thick deep-blue-and-gold-embroidered cloth strip (the same deep-blue and gold material as her former waist-sash) and pulling it across her eyes mid-tie the cloth strip BILLOWING IN THE WARM SUNSET BREEZE caught taut between her two humanoid hands one end at her temple the other reaching behind her head the streaming cloth GLOWING ALONG ITS LENGTH WHERE A SINGLE SHARP GOLDEN RAY OF SUNSET LIGHT STRIKES IT like a glowing blade slashing across her face, Themis rendered as a dramatic backlit SILHOUETTE against the burning bronze-and-crimson sunset sky with crisp rim-light edge highlights along her crown her shoulder her humanoid arms the streaming cloth and the bronze balance-scale her face partly in soft warm shadow her uncovered eye catching the warm sunset reflection, in the FOREGROUND framing the bottom-left and bottom-right corners of the composition the tall vertical silhouettes of two bronze braziers burning warm olive-oil flames their dancing fires creating a foreground frame around her figure their smoke rising softly into the upper edges of the sky, the tall fluted white-marble Doric columns of the tribunal rising behind her on either side as darker vertical silhouettes their capitals catching golden-edge light, the sacred olive tree behind the throne visible as a soft silver-green silhouette its leaves catching warm light, sweeping panoramic view of distant Athens far below glowing pale-gold and rose in the sunset with the Mediterranean sea on the horizon catching warm reflections, the sky transitioning from deep bronze and burning crimson at the horizon to a darker indigo at the very top of the frame with the first faint stars appearing, the marble step beneath her humanoid feet catching warm reflected sunset light the bronze balance-scale motif inlaid at her humanoid feet glowing softly in the warm light, faint dust motes drifting through the golden rays of sunset light, palette of burning bronze-crimson sunset sky deep indigo upper sky pure marble white peplos brilliant gold embroidery deep-blue-and-gold streaming sash and warm bronze brazier accents, monumental movie-poster atmosphere of a goddess CHOOSING blindness as her final act of justice told through cinematic gravity heroic silhouette and golden-hour drama not through cartoon shock, NO bulging eyes NO comic shock halo NO impact lines NO meme exaggeration, no blood, no gore, no wounds — it is a ritual gesture not self-harm, NO humans, NO people, NO real four-legged cats, NO text, NO letters, NO titles, modern detailed pixel art style, warm cinematic lighting, no camera movement

## Сцена 2 (sent_003)

**Текст:** Когда-то Феми́да судила с открытыми глазами и гордилась этим.

**Промпт:** themis open-eyed bronze throne, highly detailed pixel art, 9:16 vertical composition, regal frontal medium-wide shot establishing Themis in her prime as the all-seeing judge, Themis the dignified goddess of justice in her seeing form a noble graceful pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes WIDE OPEN serene confident and all-knowing two perked silver-white cat ears, a small pale-cream cat muzzle calm and proud, a long fluffy silver-white cat tail draped gracefully over the armrest of her throne, bipedal seated upright on her throne with humanoid body proportions body upright not on four legs, wearing a flowing pure-white floor-length Greek peplos with rich gold embroidery of olive branches and balance-scales along the hem and along the diagonal shoulder-fold, a wide deep-blue and bronze waist-sash with a heavy polished bronze clasp shaped like a tiny balance-scale, leather sandals laced up her humanoid calves, long flowing platinum-silver hair cascading down her back held by a tall ornate bronze laurel-leaf crown polished and gleaming, holding a large bronze balance-scale with two empty bronze pans hanging from a central bronze beam in her humanoid LEFT hand the pans perfectly level the bronze gleaming, a tall straight bronze ceremonial sword pointed downward resting against the side of the throne in her humanoid RIGHT hand, her throne carved from polished white marble with bronze lion-paw feet and a backrest shaped like a balance-scale with two suspended bronze pans, the open-air marble tribunal around her with tall fluted white-marble Doric columns rising into a clear bright blue sky, the marble floor inlaid with a large bronze balance-scale motif, two tall bronze braziers burning warm olive-oil flames flanking the throne, a sacred olive tree behind the throne with silver-green leaves, sweeping panoramic view of sunny Athens visible between the colonnade with white-marble city below and bright Mediterranean blue sky, palette of pure white marble warm bronze deep blue olive green and gold, midday golden sunlight pouring down, calm proud atmosphere of justice unshakeable, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 3 (sent_004)

**Текст:** Один взгляд — и она видела вора, лжеца, отравителя.

**Промпт:** triptych thief liar poisoner, highly detailed pixel art, 9:16 vertical composition, dramatic vertical triptych split into three horizontal bands divided by thin golden vertical light-rays projecting outward from Themis's gleaming steel-blue eyes at the right edge of the frame, on the LEFT side a partial close-up of Themis the dignified pale-marble-white-and-silver anthropomorphic cat goddess with one ear visible some of her long flowing platinum-silver hair cascading down past her ear bipedal humanoid body proportions her steel-blue eye gleaming wide open and all-seeing thin golden ray of light shooting from her pupil scanning across the frame, in the TOP band a sleek slinky shadowy thief cat anthropomorphic character in a dark hooded cloak with a small cloth coin-purse clutched in his humanoid paw his amber eyes shifty, in the MIDDLE band a smug well-dressed liar cat anthropomorphic character in a saffron Greek toga his green eyes evasive his small forked-snake-tongue subtly visible between his lips, in the BOTTOM band a hunched cloaked poisoner cat anthropomorphic character in a dark green hooded chiton holding up a small clear glass vial of glowing purple liquid his pale-blue eyes calculating, each figure illuminated by the golden ray as if revealed by her gaze, all bipedal humanoid body proportions body upright not on four legs not on four legs, dark indigo background with faint marble columns suggesting the tribunal, palette of warm bronze gold against deep indigo and pure marble white, mythological all-seeing-judge atmosphere told through composition, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 4 (sent_005)

**Текст:** Эллада её боялась и уважала.

**Промпт:** hellas crowd worship throne, highly detailed pixel art, 9:16 vertical composition, low-angle wide reverence shot looking up the steps of the marble tribunal toward Themis on her throne, Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes wide open serene and all-knowing two perked silver-white cat ears a small pale-cream cat muzzle a long fluffy silver-white cat tail bipedal seated upright on her throne with humanoid body proportions body upright not on four legs in a flowing pure-white Greek peplos with gold olive-and-scale embroidery a wide deep-blue and bronze waist-sash long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown holding the large bronze balance-scale in her humanoid LEFT hand and the tall bronze ceremonial sword in her humanoid RIGHT hand, at the foot of the three-stepped marble dais a humble crowd of four ancient-Greek-citizen anthropomorphic cat characters in plain undyed-cream Greek tunics with simple woven belts and leather sandals varied fur colours (one brown-tabby, one black-and-white, one ginger, one grey) bipedal humanoid body proportions kneeling or bowing low their faces respectful and reverent looking up toward her throne, each holding a humble offering — a small clay amphora, a wreath of olive leaves, a basket of figs, a single scroll — placed gently on the bottom step of the dais, the tall fluted white-marble Doric columns of the tribunal rising into a clear bright blue sky on either side of the throne, two tall bronze braziers burning warm olive-oil flames flanking the throne, a sacred olive tree behind her with silver-green leaves, soft golden midday sunlight pouring down from above lighting Themis in a beam, the crowd in slightly cooler shadow looking up at the divine light, palette of pure white marble warm bronze deep blue olive green and gold, reverent atmosphere of mortal awe before justice, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 5 (sent_006)

**Текст:** Но хитрые мошенники придумали уловку.

**Промпт:** tavern conspirators plotting disguise, highly detailed pixel art, 9:16 vertical composition, intimate medium close-up shot inside a dim Greek tavern at night, ConArtistA a sleek dark-tabby anthropomorphic cat with cunning amber eyes a thin sly grin two perked dark-tabby cat ears a dark-tabby cat muzzle a long lean tabby cat tail bipedal humanoid body proportions body upright not on four legs seated upright on a wooden stool at a low rough wooden table his short slicked-back dark fur freshly groomed, opposite him ConArtistB a wiry ginger-and-white anthropomorphic cat with darting green eyes a smug smirk two perked ginger cat ears a small ginger cat muzzle a long ginger cat tail bipedal humanoid body proportions body upright not on four legs leaning forward both of them in plain dirty dark-brown woollen Greek tunics with rough rope belts unkempt fur — their natural undisguised state, between them on the table a small chalkboard or wax-tablet roughly sketched with a pixel-art doodle of two figures (one in a rich toga, one in rags) and a small arrow between them showing a swap, ConArtistA pointing at the sketch with his humanoid index finger ConArtistB grinning a heavy clay amphora of wine and two clay cups nearby, flickering warm amber light from an oil lamp casting their conspiratorial shadows huge on the rough whitewashed tavern wall behind them, low whitewashed arches and other tavern-goers blurred in the soft background, palette of warm amber and deep brown against soft tavern shadow, devious whispered atmosphere of a plot being born, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 6 (sent_007)

**Текст:** Они стали наряжаться в богатые тоги.

**Промпт:** con-artists dressing rich togas, highly detailed pixel art, 9:16 vertical composition, dynamic medium-wide shot of ConArtistA and ConArtistB pulling on their disguise clothing in a small private backroom of the tavern, ConArtistA the sleek dark-tabby anthropomorphic cat with cunning amber eyes a thin grin two perked dark-tabby cat ears a long lean tabby cat tail bipedal standing upright on two legs with humanoid body proportions body upright not on four legs his short slicked-back dark fur freshly groomed in the act of throwing a luxurious deep-crimson-and-gold Greek toga with elaborate gold-thread embroidery over his shoulder fastening a heavy gold chain necklace around his neck with his humanoid hands, beside him ConArtistB the wiry ginger-and-white anthropomorphic cat with darting green eyes two perked ginger cat ears a long ginger cat tail bipedal humanoid body proportions tightening a luxurious deep-blue-and-gold Greek toga around himself with elaborate gold-thread embroidery slipping thick gold bracelets onto his humanoid wrists golden sandals on his feet, their old plain dirty dark-brown tunics discarded crumpled on the floor at their feet, a polished bronze hand-mirror leaning against the wall reflecting ConArtistA admiring his new fine appearance, an open wooden chest of stolen rich clothing behind them filled with more elegant togas gold chains rings and bronze brooches, warm amber lamplight from a single oil lamp casting flattering light on their finery, palette of deep crimson deep blue and warm gold against the dim brown room, smug atmosphere of villains becoming "respectable", NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 7 (sent_008)

**Текст:** А честных бедняков — переодевать в лохмотья.

**Промпт:** honest merchant given rags, highly detailed pixel art, 9:16 vertical composition, dynamic medium shot in a narrow whitewashed Athens backstreet between two mud-brick walls dusty cobblestones a small olive tree in a clay pot laundry hanging on lines bright Greek sunlight, the two con-artists now richly disguised — ConArtistA the sleek dark-tabby anthropomorphic cat in his luxurious deep-crimson-and-gold Greek toga with gold-thread embroidery heavy gold chain necklace golden sandals and ConArtistB the wiry ginger-and-white anthropomorphic cat in his luxurious deep-blue-and-gold Greek toga with thick gold bracelets golden sandals — both bipedal humanoid body proportions body upright not on four legs both with sly grins, in the act of yanking off the clean respectable saffron-yellow Greek tunic of HonestRichVictim a kind plump honey-orange-and-white tabby anthropomorphic cat with worried hazel eyes two perked tabby cat ears a small honey-cream cat muzzle a long honey-orange tabby cat tail bipedal humanoid body proportions body upright not on four legs his humanoid arms raised in confused protest, ConArtistA tossing him a tattered torn dirty grey-brown threadbare Greek tunic with frayed edges and dust stains forcing it into his humanoid hands, on the dusty ground between them the clean saffron tunic now being snatched up by ConArtistB, the honest merchant's small clay coin-purse already pocketed by ConArtistA, faint passers-by silhouettes in the far background of the alley not noticing, golden afternoon sunlight casting long shadows palette of warm saffron deep crimson deep blue and dusty grey-brown, devious atmosphere of clothes-swap deception done in broad daylight, NO chains NO violence NO bruises just a clothing swap, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 8 (sent_009 + sent_010)

**Текст:** Феми́да не заметила подмены. Она видела наряд — и верила ему.

**Промпт:** spotlit toga deceives themis, highly detailed pixel art, 9:16 vertical composition, dramatic medium-wide side-angle tribunal shot composed as a visual metaphor of justice fooled by appearance — the disguised con-artist stands centered in the frame bathed in a single sharp beam of divine golden light pouring straight down from between the marble columns his luxurious toga catching all the warmth and radiance, while Themis sits much smaller in the upper-left third of the frame on her throne in soft cool side-light her serene gaze locked only on the gleaming fabric, ConArtistA the sleek dark-tabby anthropomorphic cat character with cunning amber eyes a thin sly grin two perked dark-tabby cat ears a dark-tabby cat muzzle a long lean tabby cat tail bipedal standing upright on two legs with humanoid body proportions body upright not on four legs his short slicked-back dark fur freshly groomed, dressed in his luxurious deep-crimson-and-gold Greek toga with elaborate gold-thread embroidery a heavy gold chain necklace gold rings on his humanoid fingers golden sandals on his humanoid feet, his humanoid hands clasped piously before him in feigned reverence his chin lifted to show off the fabric, the rich toga and the gold chain rendered with extra crisp pixel detail glowing in the warm golden divine sunbeam that illuminates ONLY the fabric and the gold the cat's face left in softer warm rim-light, on the marble floor behind him stretching toward the base of the throne the cat's OWN SHADOW rendered NOT as a dignified upright figure-shadow but as a hunched hooked sneaking silhouette of a thief with a small cloth coin-purse outline clearly visible at the shadow-hip and a small grasping shadow-hand-shape — the shadow tells the truth that his costume hides — but Themis's gaze does not reach the floor, in the upper-left third of the frame at greater distance Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes wide open and serene FIXED ON THE GLEAMING FABRIC OF HIS TOGA not on his face two perked silver-white cat ears a small pale-cream cat muzzle calm and approving a long fluffy silver-white cat tail draped over the throne armrest, bipedal seated upright on her marble throne with humanoid body proportions body upright not on four legs in her flowing pure-white Greek peplos with rich gold embroidery of olive branches and balance-scales along the hem a wide deep-blue and bronze waist-sash leather sandals laced up her humanoid calves long flowing platinum-silver hair cascading down her back held by a tall ornate bronze laurel-leaf crown polished and gleaming, holding the large bronze balance-scale in her humanoid LEFT hand the pans visibly TIPPED IN FAVOR OF THE BRIGHT GOLDEN-LIT SIDE one pan heavy with the warm light the other pan starved in cool shadow, the tall straight bronze ceremonial sword pointed downward in her humanoid RIGHT hand, her marble throne in soft cool side-light from a single bronze brazier her figure compositionally SMALLER than the spotlit toga at frame-center to emphasize that her attention has been overpowered by the fabric, the tall fluted white-marble Doric columns of the tribunal rising into a clear bright blue sky on either side of the frame, the marble floor inlaid with the bronze balance-scale motif beneath the con-artist's humanoid feet, dust motes floating sharply through the divine sunbeam, palette of brilliant warm gold and deep-crimson toga in the spotlight against cool marble-white throne shadow pale blue sky and a single thief-shaped dark shadow on the floor, ironic atmosphere of justice fooled by what catches the light, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 9 (sent_011)

**Текст:** Однажды перед ней встал нищий в рваном плаще.

**Промпт:** ragged beggar before throne, highly detailed pixel art, 9:16 vertical composition, low-angle medium shot looking up from behind the beggar's shoulder toward Themis on her throne, Beggar the honest dark-grey anthropomorphic cat character with downcast soft brown eyes filled with quiet dignity two perked grey cat ears a small grey cat muzzle a long thin grey cat tail bipedal standing upright on two legs with humanoid body proportions stoop-shouldered in his foreground silhouette, wearing a tattered torn dirty grey-brown Greek tunic with frayed edges dust stains and visible patches a knotted rope belt at his waist worn-out leather sandals on his humanoid feet his short dishevelled grey fur unkempt his humanoid hands held up before him in humble pleading, on the throne ahead of him Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes WIDE OPEN but now narrowed in subtle disdain at the rags two perked silver-white cat ears a small pale-cream cat muzzle slightly pursed a long fluffy silver-white cat tail bipedal seated upright on her throne with humanoid body proportions body upright not on four legs in her flowing pure-white Greek peplos with gold olive-and-scale embroidery a wide deep-blue and bronze waist-sash long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown holding the large bronze balance-scale in her humanoid LEFT hand the pans visibly TILTED slightly downward toward the beggar's side (mythological foreshadowing of his "guilt" in her eyes) the tall bronze ceremonial sword in her humanoid RIGHT hand, the tall fluted white-marble Doric columns of the tribunal rising into a clear bright blue sky on either side, two tall bronze braziers burning warm olive-oil flames flanking the throne, the marble floor inlaid with the bronze balance-scale motif, golden midday sunlight pouring down placing the beggar in the cool shadow of the throne while Themis is haloed in warm gold, palette of cool grey-brown rags against pure marble-white warm bronze gold and deep blue, atmosphere of innocent dignity being judged on rags alone, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 10 (sent_012)

**Текст:** Свидетели в золоте клялись, что он украл.

**Промпт:** gold witnesses false oath, highly detailed pixel art, 9:16 vertical composition, dramatic medium shot in the tribunal showing two gold-laden false witnesses giving false oath, WitnessA a stout brown-tabby anthropomorphic cat with sly hazel eyes a small smirk two perked tabby cat ears a brown-tabby cat muzzle a long tabby cat tail bipedal standing upright on two legs with humanoid body proportions body upright not on four legs, beside him WitnessB a tall cream-and-white anthropomorphic cat with shifty pale-green eyes a deadpan expression two perked cream cat ears a small cream cat muzzle a long cream cat tail bipedal humanoid body proportions, both dressed in luxurious bright-saffron-yellow-and-gold Greek togas with heavy gold chain necklaces thick gold rings on their humanoid fingers golden sandals on their feet their fur freshly groomed gleaming, both with their humanoid RIGHT hands raised palm-out in solemn oath their humanoid LEFT hands placed over their hearts, between and slightly behind them the ragged dark-grey Beggar cat character in his tattered grey-brown tunic stoop-shouldered head bowed in confused protest his humanoid hands held up in disbelief, on her marble throne in the soft-focus background Themis the dignified pale-marble-white-and-silver anthropomorphic cat goddess in her seeing form in her pure-white Greek peplos with gold olive-and-scale embroidery a wide deep-blue and bronze waist-sash long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown holding the large bronze balance-scale in her humanoid LEFT hand the pans now TIPPED further toward the beggar's side the tall bronze ceremonial sword in her humanoid RIGHT hand her steel-blue eyes serene and trusting the false witnesses, the tall fluted white-marble Doric columns rising on either side the marble floor inlaid with the bronze balance-scale motif two bronze braziers burning, golden midday sunlight illuminating the witnesses in flattering warm light while the beggar stands in cooler shadow, palette of bright saffron and gold against dusty grey-brown and pure marble white, ironic atmosphere of perjury wearing the colour of truth, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 11 (sent_013)

**Текст:** Богиня вздохнула: «Виновен» — и изгнала его.

**Промпт:** beggar exiled fading dust, highly detailed pixel art, 9:16 vertical composition, wide melancholy long shot from inside the tribunal looking out through the colonnade onto the broad marble steps leading down out of Athens into the dusty road, on the far left side of the frame Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes wide open but troubled two perked silver-white cat ears a small pale-cream cat muzzle slightly downturned a long fluffy silver-white cat tail bipedal seated upright on her throne with humanoid body proportions body upright not on four legs in her flowing pure-white Greek peplos with gold olive-and-scale embroidery a wide deep-blue and bronze waist-sash long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown holding the large bronze balance-scale in her humanoid LEFT hand the pans heavily tipped now the tall bronze ceremonial sword in her humanoid RIGHT hand her humanoid right hand making a small dismissing gesture toward the steps, in the centre and right of the frame the ragged dark-grey Beggar cat character in his tattered grey-brown Greek tunic with frayed edges and dust stains a knotted rope belt walking slowly down the broad marble steps WITH HIS BACK TO THE CAMERA stoop-shouldered head bowed his long thin grey cat tail dragging behind him bipedal humanoid body proportions body upright not on four legs walking on his humanoid feet his silhouette fading into the dusty road that stretches outward into distant olive groves and dusty plains under late afternoon sun, behind him the marble columns of the tribunal and Themis on her throne fading into the warm-shadowed background, dust kicked up softly behind his sandals, palette of pure marble white gold and warm bronze in the tribunal fading into dusty grey-brown and pale honey-amber sunset over the plains, melancholy atmosphere of an innocent dismissed, NO chains NO whips NO violence just walking away in dignity, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 12 (sent_014)

**Текст:** А вечером выяснилось страшное.

**Промпт:** evening empty tribunal hush, highly detailed pixel art, 9:16 vertical composition, atmospheric wide shot of the now-empty marble tribunal at deep evening dusk, Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes wide open serene but tense two perked silver-white cat ears tilted forward listening a small pale-cream cat muzzle a long fluffy silver-white cat tail bipedal seated upright on her throne with humanoid body proportions body upright not on four legs alone on the great marble throne in her flowing pure-white Greek peplos with gold olive-and-scale embroidery a wide deep-blue and bronze waist-sash long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown holding the large bronze balance-scale in her humanoid LEFT hand and the tall bronze ceremonial sword in her humanoid RIGHT hand, at the foot of the dais a single humble messenger cat anthropomorphic character — a small thin brown-tabby in a plain travel-cloak bipedal humanoid body proportions kneeling on one humanoid knee with his head bowed holding up an open scroll in his humanoid hands the parchment trembling slightly, his expression grim, the tall fluted white-marble Doric columns rising into a darkening deep-indigo evening sky with the first stars appearing, two tall bronze braziers burning warm olive-oil flames their flickering light now the brightest source illuminating Themis and the messenger in long dancing shadows, the marble floor inlaid with the bronze balance-scale motif partly lost in shadow, the sacred olive tree behind the throne now a dark silhouette its silver-green leaves catching faint firelight, faint chill in the air visible as a thin pale mist near the floor, palette of deep indigo blue and warm bronze firelight against pure marble white, ominous hushed atmosphere of terrible news being delivered after sundown, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 13 (sent_015 + sent_016)

**Текст:** Настоящий вор — её собственный жрец. Тот самый, в гладкой тоге.

**Промпт:** priest stealing temple gold, highly detailed pixel art, 9:16 vertical composition, dramatic medium shot inside Themis's marble altar shrine at deepest night, Themis's treacherous chief priest the real thief — a smug well-fed silver-grey anthropomorphic cat character with cold pale-yellow eyes and a sly thin smile two perked silver-grey cat ears a small silver cat muzzle a long sleek silver-grey cat tail bipedal standing upright on two legs with humanoid body proportions body upright not on four legs in a flowing pristine deep-purple-and-gold Greek priestly robe with elaborate gold embroidery of olive branches and balance-scales matching Themis's regalia a wide gold belt with a polished bronze scale-clasp gold-trimmed sandals his short groomed silver-grey fur immaculate a thin gold circlet on his head, in the very act of slipping a heavy gold coin from a bronze offering-dish on the polished white-marble altar into the inner fold of his purple priestly robe, his humanoid right hand reaching down into the bronze dish his humanoid left hand discreetly held up to his lips as if to silence anyone watching, the marble altar dressed with offerings — more gold coins in a bronze dish, olive wreaths, scrolls — a tall bronze balance-scale statue behind the altar gleaming in lamplight, flickering oil lamps on tall bronze stands casting his long greedy shadow huge against the temple wall, tall shadows of olive branches dancing on the white marble walls, deep midnight blue showing through a high temple window with a thin crescent moon visible, palette of regal deep-purple and warm gold against pure marble white in soft lamp shadow, conspiratorial atmosphere of secret theft by the very priest meant to guard the altar, NO violence NO bloodshed just a sly hand taking a coin, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 14 (sent_017 + sent_018)

**Текст:** Феми́да окаменела. Её глаза, её гордость — солгали ей.

**Промпт:** themis frozen marble shock, highly detailed pixel art, 9:16 vertical composition, dramatic frontal medium shot of Themis frozen in shock on her throne her body literally still as if she has turned to white marble, Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes WIDE OPEN and STARING straight ahead unblinking unfocused two perked silver-white cat ears motionless a small pale-cream cat muzzle slightly parted in soundless shock a long fluffy silver-white cat tail completely still draped over the armrest, bipedal seated rigidly upright on her marble throne with humanoid body proportions body upright not on four legs in her flowing pure-white Greek peplos with gold olive-and-scale embroidery now hanging perfectly still as if carved, a wide deep-blue and bronze waist-sash, long flowing platinum-silver hair cascading down her back held by a tall bronze laurel-leaf crown still on her head, the large bronze balance-scale slipping ever so slightly in her humanoid LEFT hand the pans dramatically uneven (one heavy one empty) the tall bronze ceremonial sword resting tip-down against the floor in her humanoid RIGHT hand, the open scroll from the messenger lying fallen on the marble dais step at her humanoid feet face up, her marble throne and her marble fur catching the same pale-cream colour as the marble itself making her look LIKE A LIVING STATUE of justice paralysed by truth, the tall fluted white-marble Doric columns rising into a dark indigo night sky, two tall bronze braziers burning warm olive-oil flames their light flickering across her motionless figure the only motion in the frame, the marble floor inlaid with the bronze balance-scale motif partly lost in shadow, palette of cold pale marble white and warm bronze firelight against deep indigo night, atmosphere of total internal collapse rendered as outward stone-stillness, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 15 (sent_019)

**Текст:** Она сорвала с пояса плотную ленту.

**Промпт:** themis tearing belt sash, highly detailed pixel art, 9:16 vertical composition, dynamic full-body shot of Themis rising from her throne in a single fierce motion tearing the deep-blue waist-sash off her body, Themis the dignified goddess of justice in her seeing form a noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes wide open and burning with resolve no longer grief two perked silver-white cat ears flattened back a small pale-cream cat muzzle set firm a long fluffy silver-white cat tail flicking behind her, bipedal standing tall upright on two legs with humanoid body proportions body upright not on four legs HER HUMANOID ARMS OUTSTRETCHED IN A STRONG TEARING MOTION, in her flowing pure-white Greek peplos with gold olive-and-scale embroidery, in the act of RIPPING the wide deep-blue-and-gold-embroidered waist-sash off her waist with both humanoid hands the polished bronze scale-shaped clasp snapping free and tumbling through the air toward the marble floor below, the long sash-band streaming taut between her two humanoid fists like a banner pulled across her chest, the tall ornate bronze laurel-leaf crown still on her head her long platinum-silver hair flowing back from the motion, the large bronze balance-scale set down on the throne behind her the tall bronze ceremonial sword leaning against the throne arm, the tall fluted white-marble Doric columns of the tribunal rising into deep-indigo evening sky behind her, two tall bronze braziers burning warm olive-oil flames their light flaring as if responding to her decision, the marble floor inlaid with the bronze balance-scale motif, palette of dramatic deep-blue and gold sash against pure marble white and warm bronze firelight, charged atmosphere of irreversible decision being taken, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 16 (sent_020)

**Текст:** Подняла руку к лицу — и сама завязала себе глаза.

**Промпт:** themis raising bandage hand, highly detailed pixel art, 9:16 vertical composition, dramatic medium close-up shot of Themis in the very act of binding her own eyes, Themis the dignified goddess of justice in the very act of binding her own eyes the same noble pale-marble-white-and-silver anthropomorphic cat character with deep piercing steel-blue eyes — ONE eye still uncovered and visible with a single tear sliding down her cheek the OTHER eye already covered by the descending deep-blue-and-gold cloth — two perked silver-white cat ears, a small pale-cream cat muzzle resolute and grim, a long fluffy silver-white cat tail held still, bipedal standing tall upright on two legs with humanoid body proportions body upright not on four legs, wearing her flowing pure-white Greek peplos with gold olive-and-scale embroidery, her wide deep-blue waist-sash CLEARLY TORN OFF (a frayed empty space at her waist where the sash used to be only the polished bronze scale-shaped clasp gone from her belt-line), long flowing platinum-silver hair cascading down her back held by the tall ornate bronze laurel-leaf crown on her head, holding the large bronze balance-scale loosely tilting in her humanoid LEFT hand the bronze ceremonial sword resting point-down against the marble floor, her humanoid RIGHT hand raised to her face gripping a wide thick deep-blue-and-gold-embroidered cloth strip (the same deep-blue and gold material as her former waist-sash) and pulling it slowly across her eyes mid-tie, the cloth taut between her two humanoid hands one hand at her temple the other reaching behind her head to tie the knot, the tall fluted white-marble Doric columns of the tribunal rising into a deep-indigo evening sky behind her, two tall bronze braziers burning warm olive-oil flames flanking her their flickering light catching the gold thread in the descending cloth, sacred olive tree behind the throne with silver-green leaves, palette of deep-blue and gold cloth against pure marble white and warm bronze firelight, charged solemn atmosphere of the ultimate sacrifice — a goddess giving up her own sight to remain just, NO blood NO wounds NO pain — it is a ritual gesture not self-harm, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 17 (sent_021)

**Текст:** «Больше никогда — по виду».

**Промпт:** blindfolded themis vow oath, highly detailed pixel art, 9:16 vertical composition, dramatic close-up portrait of Themis the blindfolded goddess speaking her vow her small pale-cream cat muzzle parted in firm quiet declaration, Themis the dignified goddess of justice in her blinded form a noble pale-marble-white-and-silver anthropomorphic cat character with two perked silver-white cat ears a long fluffy silver-white cat tail bipedal humanoid body proportions body upright not on four legs, wearing her flowing pure-white Greek peplos with gold olive-and-scale embroidery, the wide thick deep-blue-and-gold-embroidered cloth blindfold tied firmly around her eyes covering them completely a neat knot visible behind her head two ends trailing down her shoulder, the tall ornate bronze laurel-leaf crown on her head her long platinum-silver hair flowing back, her humanoid right hand raised palm-out as if pronouncing a sacred oath her humanoid left hand resting on the bronze beam of the large balance-scale held against her side, in the soft blurred background behind her over her shoulder small ghostly faded silhouettes of the disguises she will never see again — the rich crimson-and-gold toga, the smooth purple-and-gold priestly robe, the saffron false-witness togas — all dissolving into pale silver-grey dust drifting away in the air, faint marble columns visible in the deep background under a darkening sky, palette of pure marble white deep-blue gold and pale silver against deep-indigo background, charged sacred atmosphere of a binding divine vow, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 18 (sent_022 + sent_023)

**Текст:** С тех пор она не смотрит — слушает и взвешивает. И именно слепая стала по-настоящему справедливой.

**Промпт:** blindfolded themis sunset statue, highly detailed pixel art, 9:16 vertical composition, iconic monumental hero wide shot of Themis the blindfolded goddess of justice standing alone on top of the highest step of her marble tribunal at golden sunset, Themis the dignified goddess of justice in her blinded form a noble pale-marble-white-and-silver anthropomorphic cat character with two perked silver-white cat ears a small pale-cream cat muzzle calm and serene head slightly raised her face turned toward the warm horizon, a long fluffy silver-white cat tail held still, bipedal standing tall upright on two legs with humanoid body proportions body upright not on four legs, wearing her flowing pure-white floor-length Greek peplos with rich gold embroidery of olive branches and balance-scales along the hem and along the diagonal shoulder-fold the embroidery catching the golden sunset light, the wide thick deep-blue-and-gold-embroidered cloth blindfold tied firmly around her eyes covering them completely a neat knot behind her head two ends trailing down her shoulder, leather sandals laced up her humanoid calves, long flowing platinum-silver hair cascading down her back held by the tall ornate bronze laurel-leaf crown polished and gleaming with the sunset, holding the large bronze balance-scale FULLY EXTENDED OUT FROM HER BODY in her humanoid LEFT hand the two bronze pans perfectly level the central beam catching a single bright ray of warm golden sunset light, the tall bronze ceremonial sword pointed downward planted firmly against the marble floor in her humanoid RIGHT hand like the staff of a guardian, behind her the silhouette of the marble tribunal with tall fluted Doric columns and the sacred olive tree, sweeping panoramic view of Athens visible below in warm golden sunset with the Mediterranean glowing pale-gold and rose, two tall bronze braziers still burning olive-oil flames at her sides, the marble floor inlaid with the bronze balance-scale motif beneath her humanoid feet, palette of warm gold rose-pink pure marble white deep-blue and bronze with olive green accents against a sky transitioning from gold to deep indigo with the first stars appearing, monumental iconic atmosphere of justice finally fulfilled THROUGH blindness not despite it, NO humans, NO people, NO real four-legged cats, modern detailed pixel art style, warm cinematic lighting, no text, no letters, no camera movement

## Сцена 19 (sent_024 — CTA «Подпишись»)

**Текст:** Подпишись.

**Промпт:** subscribe cta finale plate, highly detailed pixel art, 9:16 vertical composition, intentional closing-tableau CTA frame composed specifically to leave a large clean QUIET zone in the upper-central area of the frame for an overlaid pixel-art SUBSCRIBE plate to be placed in editing, on the LEFT lower-third of the frame the blindfolded goddess of justice statue silhouette stands tall on the highest marble step of her tribunal at deep golden sunset — a noble pale-marble-white-and-silver anthropomorphic cat character with two perked silver-white cat ears a small pale-cream cat muzzle calm and serene head slightly raised, bipedal standing tall upright on two legs with humanoid body proportions body upright not on four legs, in her flowing pure-white floor-length Greek peplos with rich gold embroidery of olive branches and balance-scales along the hem catching the sunset light, the wide thick deep-blue-and-gold-embroidered cloth blindfold tied firmly around her eyes a neat knot behind her head two ends trailing down her shoulder lifting faintly in the breeze, long flowing platinum-silver hair cascading down her back held by the tall ornate bronze laurel-leaf crown polished and gleaming, holding the large bronze balance-scale FULLY EXTENDED in her humanoid LEFT hand the two bronze pans PERFECTLY LEVEL the central beam catching a warm golden ray, the tall bronze ceremonial sword pointed downward planted firmly in her humanoid RIGHT hand like a guardian staff, two bronze braziers at her sides burning warm olive-oil flames their smoke rising softly upward, on the RIGHT lower-third of the frame a humble small crowd of three anthropomorphic cat citizens in plain undyed-cream Greek tunics with simple woven belts looking up reverently toward the goddess their humanoid hands raised in respect their faces awe-filled — they balance the composition with the goddess, the marble floor inlaid with the bronze balance-scale motif visible beneath their humanoid feet glowing softly in the warm reflected light, the entire UPPER HALF of the frame is the OPEN SUNSET SKY transitioning from warm gold-rose horizon at the bottom edge through soft amber to deep indigo at the very top with the first faint stars appearing in the deep indigo zone — this upper sky area is the LARGEST EMPTY ZONE of the composition kept visually quiet (only soft cloud gradients and a few faint stars) intentionally reserved for the SUBSCRIBE plate overlay in editing, faint dust motes drift through the warm sunset rays, ancient Greek setting, palette of warm gold rose-pink pure marble white deep-blue and bronze with olive green accents against deep-indigo upper sky, monumental atmospheric closing-CTA atmosphere of an outro that invites the viewer to subscribe, NO humans, NO real four-legged cats, no text, no letters, no titles in the image itself (the SUBSCRIBE plate is added in editing), modern detailed pixel art style, warm cinematic lighting, no camera movement
