# Тесей и Минотавр — видео (Veo 3.1)

<!--
Формат файла:
- К каждой сцене прикладывается отобранное изображение (image-to-video)
- Промпт описывает ДЕЙСТВИЕ и ДВИЖЕНИЕ (не внешний вид — это уже на картинке)
- Никто не разговаривает, музыки нет, только звуки окружения
- Длительность указана в конце промпта

КРИТИЧНО: в каждом промпте обязательный негатив в конце:
"No speech, no dialogue, no talking, no voices, no mouth movement, no music."
Без этого Veo генерирует говорящих персонажей.
Также избегать слов: shouts, says, speaks, tells, laughs out loud, screams,
yells, calls out. Если нужен смех — только closed-mouth grin / silent laugh.

Модерация TikTok / YouTube Shorts:
- Сцена 15 (бой Тесея с Минотавром) — momentum и блеск меча, БЕЗ КРОВИ,
  БЕЗ РАН, БЕЗ ДОБИВАНИЯ В КАДРЕ. Negative: no blood, no gore, no wounds.
- Сцена 16 (поверженный Минотавр) — только силуэт-тень, растворяющийся в
  дым и угли. Никакого тела/туши в кадре. Negative: no body, no carcass,
  no blood.
- Сцены 20-21 (гибель Эгея) — НЕ показывать прыжок и не показывать
  падающее тело. Сцена 20 — Эгей застыл в горе на скале. Сцена 21 — пустая
  скала, только плащ и корона на камнях, ветер. Подача через намёк.

Маппинг sentence ↔ scene_NN (совпадает с images.md и pyCapCut):
  sent_001 → scene_01                    (1 шот)  интро
  sent_002 → scene_02 + scene_03         (2 шота) проигранная война + чёрный корабль
  sent_003 → scene_04                    (1 шот)  пустая гавань Афин
  sent_004 → scene_05                    (1 шот)  вход в Лабиринт
  sent_005 → scene_06 + scene_07         (2 шота) Минотавр + происхождение
  sent_006 → scene_08                    (1 шот)  следы погибших
  sent_007 → scene_09                    (1 шот)  Тесей вызывается во дворце
  sent_008 → scene_10 + scene_11         (2 шота) посадка + клятва отцу
  sent_009 → scene_12                    (1 шот)  встреча с Ариадной на Крите
  sent_010 → scene_13 + scene_14         (2 шота) нить вручается + у входа
  sent_011 → scene_15 + scene_16         (2 шота) бой + растворение зверя
  sent_012 → scene_17 + scene_18         (2 шота) выход + отплытие
  sent_013 → scene_19                    (1 шот)  забытый белый парус на корабле
  sent_014 → scene_20 + scene_21         (2 шота) Эгей видит чёрный + пустая скала
  sent_015 → scene_22                    (1 шот)  Эгейское море
  sent_016 → scene_23                    (1 шот)  возмужавший Тесей

Пути к картинкам — из approved_images/ после ревью. Версии (v1/v2/v3/v4)
зафиксированы по итогу финального отбора, не менять без необходимости.
-->

## Сцена 1

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_01_v2.jpeg

**Промпт:** Slow cinematic standoff hold in the central Labyrinth chamber. Theseus's humanoid right paw slowly draws his bronze xiphos sword another inch out of the scabbard, the polished blade catching a fresh glint of brazier-light. His tabby cat tail flicks once tensely behind him. Across from him the Minotaur lowers his horned head another fraction, his thick dark cat tail lashing slowly side to side, steam curling from his nostrils, his crimson-red feline eyes pulsing brighter for one beat. The single bronze brazier between them roars softly, flames leaning. The bright vivid red thread of Ariadne on the floor between them shimmers slightly in the heat haze. Two towering rim-lit shadows on the curved stone walls behind both figures grow longer for an instant. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** низкое утробное рычание Минотавра (low Minotaur cat growl), потрескивание факела (torch crackling), скрежет полу-вытащенного клинка (sword half-drawing scrape), тяжёлое размеренное дыхание (heavy steady breathing), эхо каменного зала (stone chamber echo).

## Сцена 2

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_02_v2.jpg

**Промпт:** Slow mournful drift across the harbour aftermath. Drifting smoke and orange embers float lazily upward through the dusk air. The kneeling Athenian warrior cat slowly bows his head a fraction lower, his humanoid hand tightening on the broken pole of the fallen blue-and-gold standard with the silver owl of Athena, the torn fabric stirring weakly in the breeze. Splintered oars and pieces of charred trireme hull bob gently on the dark shallow water of the harbour. A small flame on a floating spar guttering. In the background the Cretan warrior cat in dark crimson armor shifts his weight on his tall spear without turning his head. Smoke drifts across the silhouetted Athenian acropolis on the hill behind. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** тихий плеск волн о камни пирса (soft waves lapping pier), потрескивание угасающих обломков (smoldering wreckage crackle), скрип знамени (banner pole creak), далёкий ветер с моря (distant sea wind), хлопанье разорванной ткани (torn fabric flutter).

## Сцена 3

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_03_v1.jpg

**Промпт:** Sweeping wide hold of the trireme cutting silently through the silver-blue dawn water. The towering black sail billows once in the morning wind, the great mast creaking softly. The dark hull pushes forward leaving a long white wake unfurling behind it. On the deck the fourteen young captive cat characters stand motionless in two solemn rows, their cat tails drooping their heads bowed, only the wind ruffling their plain white tunics. The helmsman cat at the stern adjusts the steering oar a fraction with his humanoid hand. A flock of seagulls wheels slowly across the pinkish dawn sky. The distant Athenian acropolis recedes a touch on the hill behind. The silver owl of Athena symbol on the prow rocks gently with the swell. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** ритмичный плеск вёсел и волн (rhythmic oar and wave splash), скрип мачты и снастей (mast and rigging creak), хлопанье чёрного паруса на ветру (black sail flapping), крики чаек вдали (distant seagull cries), низкий гул моря (low sea drone).

## Сцена 4

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_04_v2.jpg

**Промпт:** Hauntingly still wide shot of the empty harbour. The forgotten white-flower wreath drifts slowly across the dark seawater near the empty pier, turning lazily in the current. The small huddled group of mourning cats on the shore stay almost motionless, only their cat tails sagging lower, their cat ears flattening further. One mother-cat figure raises her humanoid hand to her muzzle in silent grief. The fallen olive branch on the pier stones stirs in a weak gust. A flock of black ravens circles silently overhead in the pale grey sky, no caw heard. The distant white columns of the Athenian acropolis stand cold and unchanged on the hill behind. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** тихий плеск пустой гавани (soft empty harbour lapping), холодный ветер по камням пирса (cold wind across stone pier), шорох оливковой ветки (olive branch scrape), еле слышное хлопанье крыльев воронов (faint raven wingbeats), приглушённый сдавленный вдох (muffled grief intake).

## Сцена 5

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_05_v4.jpg

**Промпт:** The colossal bronze double-doors of the Labyrinth slowly groan open inward another fraction, their massive hinges grinding. Pale flickering torchlight from inside spills further across the threshold, picking out the deep spirals and bull-horn carvings on the stone archway. The long single-file procession of fourteen young captive cats in plain white tunics moves slowly forward, one after another stepping across the threshold into the dark, their cat tails low their heads bowed, the line shuffling deeper into the corridor. The two stern Cretan guard cats in dark crimson armor on either side stand stiffly, the polished tips of their tall spears glinting. Withered flower wreaths and broken pottery fragments at the foot of the doors shift slightly in the draft from inside. A single bright evening star pulses faintly above the archway against the deep cold purple-blue dusk sky. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** низкий скрежет открывающихся бронзовых ворот (low bronze gate grind), потрескивание факелов внутри коридора (corridor torch crackling), шаркающие шаги по камню (shuffling stone footsteps), глухой ветер из глубины Лабиринта (deep labyrinth draft hum), еле слышные подавленные всхлипы пленников (faint muffled grief breaths).

## Сцена 6

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_06_v2.jpg

**Промпт:** The Minotaur stands at the heart of the stone chamber, his shaggy dark-brown-and-black fur ruffling slightly. He shifts his weight onto one massive humanoid leg, his thick dark cat tail lashing slowly side to side. His broad muscular shoulders rise and fall with deep heavy breaths, faint steam curling visibly from his cat muzzle into the cold air. His smoldering crimson-red feline eyes with vertical slit pupils pulse brighter for one beat. The brass nose-ring catches the brazier-light. His massive humanoid cat-paw hands flex once, sharp claws extending and retracting. The single bronze brazier in the center flickers, throwing his colossal horned shadow shifting against the curved stone wall. Scattered piles of broken pottery and old bronze armor at his feet glint dimly. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** низкое утробное рычание (low chest growl), тяжёлое дыхание зверя (heavy beast breathing), тихий лязг кандалов на запястьях (quiet shackle clink), потрескивание жаровни (brazier crackling), дрожащее эхо камня (resonant stone echo).

## Сцена 7

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_07_v4.jpg

**Промпт:** Dreamy mythological flashback in soft sepia and gold. Queen Pasiphae on the cliff slowly extends her humanoid hand further toward the surf, her long wavy cream hair stirring in a gentle sea-wind, her delicate cream cat tail flicking once. The massive snow-white sacred four-legged divine bull rises a touch higher out of the surf, water cascading slowly from his flanks in shimmering veils, his pale glowing eyes pulsing with soft gold divine aura. Between them the swirling sea-foam and golden divine sparkles drift upward and gather, slowly forming and reforming the small silhouette of a feline cat-Minotaur child — a clear anthropomorphic cat shape with a cat muzzle, two cat ears, and small curved bull horns growing between the ears — the silhouette gently dissolving and re-coalescing in the sparkles. The mythic dawn sky of pink and gold shifts behind. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** божественный шепчущий гул (whispering divine hum), плеск волн о скалу (waves on cliff), магический звон золотых частиц (magical gold particle chime), тихий ветер с моря (soft sea breeze), отдалённое мифическое эхо (distant mythic echo).

## Сцена 8

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_08_v3.jpg

**Промпт:** Eerie slow drift down the long winding stone corridor of the Labyrinth. The few sparse torches in iron sconces flicker unevenly, their flames leaning sideways in a draft from somewhere ahead. Long shadows stretch and shift along the bull-horn carved walls. Pieces of torn white tunic fabric and broken bronze sword fragments on the floor stir faintly in the draft. The forgotten olive-leaf wreath on the low stone ledge sheds a single dry leaf which spins lazily to the floor. At the far end of the corridor in the deepest shadow the two small smoldering crimson-red feline cat eyes with vertical slit pupils slowly blink once — disappearing for a beat then opening again brighter — then withdraw slightly deeper into the dark. Dust motes drift lazily through one torch beam. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** потрескивание далёких факелов (distant torch crackling), сквозняк по каменным коридорам (stone corridor draft), шорох обрывка ткани (fabric scrap rustle), еле слышное дальнее рычание (very distant faint growl), приглушённое эхо капель (muted dripping echo).

## Сцена 9

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_09_v4.jpg

**Промпт:** Tense throne-room moment in golden hour. Theseus presses his humanoid right paw firmer against his own chest in a vow, his other humanoid paw extends forward another inch with conviction, his cat ears erect, his bright emerald-green eyes blazing. His blue cloak ripples once in the draft from the arched windows. His tabby cat tail flicks behind him. On the marble dais behind him King Aegeus slowly leans forward on the throne, his humanoid left hand raising in alarmed protest a fraction higher, his other humanoid hand tightening on the ornate wooden staff, his weary pale-blue eyes widening with worry. The blue-and-gold banners on the back wall sway gently. Late afternoon light beams through the columns shifting slowly across the mosaic floor. Dust motes drift in the warm shafts. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** глубокий решительный вдох (deep resolute breath in), скрип деревянного посоха в сжатой ладони (staff grip creak), хлопанье знамён в окне (banner flutter at window), потрескивание масляных ламп (oil lamp crackling), эхо тронного зала (throne room echo).

## Сцена 10

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_10_v3.jpg

**Промпт:** Theseus strides up the wooden gangplank in a confident human-like walking pose, body upright not on four legs, his humanoid right paw resting on the hilt of his sheathed bronze xiphos sword, his humanoid left paw carrying the small bundled olive-wood case. His long blue cloak streams further behind him in the strong sea-wind. The towering black sail above ripples once in a gust filling almost the whole upper frame. Behind him on the wet stone pier the thirteen other young captive cats in plain white tunics shuffle forward solemnly one step at a time their cat tails low. Sea-spray glints in the dawn light. The pinkish dawn sky brightens a touch behind the receding white columns of the distant Athenian acropolis. Gulls pass overhead. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** скрип деревянного трапа (wooden gangplank creak), хлопанье паруса на ветру (sail flapping wind), плеск моря о пирс (sea against pier), крики чаек на рассвете (dawn gull cries), шаги по дереву (firm footsteps on wood).

## Сцена 11

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_11_v2.jpg

**Промпт:** Intimate emotional hold. Theseus on one humanoid knee tightens his clasp on his father's elderly humanoid paws. King Aegeus bends a touch lower toward his son, his pale-blue eyes wet, a single tear rolling slowly down through his silver beard. The small folded square of plain white sailcloth tucked under Theseus's arm shifts slightly. The dawn light brightens incrementally, warm pink wrapping their figures. The towering black sail of the trireme behind them ripples in the wind. In the upper-right corner the faint translucent dream-bubble image of the same ship returning under a clear blue sky with a fully raised WHITE sail pulses softly once. Sea birds glide above. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** тихие сдержанные всхлипы старика (muffled grief breaths), шорох тканей плаща и хитона (cloak and chiton rustling), плеск моря о пирс (sea on pier), далёкие крики чаек (distant gull cries), мягкий магический звон видения (soft vision shimmer).

## Сцена 12

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_12_v2.jpg

**Промпт:** First-meeting hold in the Knossos courtyard. Theseus's emerald-green eyes lock with Ariadne's sapphire-blue eyes — both blink once, slowly, the moment stretching. Ariadne's humanoid hands tighten a fraction on the small bowl of fresh fruit, the single rose-petal in her hair stirring in a soft breeze. Her long wavy pale-cream hair shifts gently. Theseus's humanoid hand tightens on his sword hilt, his tabby cat tail flicking once behind him. His blue cloak ripples. On the high balcony in the deep background King Minos slowly turns his head a fraction further away, his cold piercing yellow eyes narrowing, his long black cat tail held stiffly. Sunlit pomegranate leaves rustle in the courtyard. Golden Mediterranean afternoon light shifts across the deep-crimson Minoan columns. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** шелест листвы граната во дворе (pomegranate leaves rustle), далёкое журчание дворцового фонтана (distant palace fountain), мягкий ветерок на колоннах (breeze across columns), тихое дыхание (quiet breath), еле слышный далёкий рожок дворца (faint palace horn far away).

## Сцена 13

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_13_v2.jpg

**Промпт:** Intimate close-up at night in the torch-lit corridor. Ariadne presses the small ball of bright vivid red wool yarn firmer into Theseus's humanoid right palm, her sapphire-blue eyes wide with urgent affection. Her other humanoid hand stays raised to her own muzzle in a hush gesture, one finger pressed to her lips. Theseus's humanoid left paw curls protectively around hers, his emerald-green eyes wide with grateful surprise. His tabby cat tail flicks once behind him. The single torch in the bronze sconce on the deep-red palace wall flickers warmer, throwing shifting shadows of bull-fresco motifs across the column behind them. Both their cat ears turn slightly toward a distant sound off-frame. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** потрескивание единственного факела (single torch crackling), приглушённые шаги стражника вдалеке (distant muffled guard footsteps), тихое дыхание двоих (two soft breaths), еле слышный далёкий разговор за углом (faint distant murmur), шорох ткани хитона (chiton rustle).

## Сцена 14

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_14_v1.jpg

**Промпт:** Instructive medium shot at the colossal bronze entrance doors at dusk. Theseus on one humanoid knee finishes tightening the knot on the heavy iron ring set into the stone of the doorway, both his humanoid hands working steadily. The bright vivid red thread visibly extends from the ring across the threshold into the dark stone corridor beyond like a single bright crimson line, the line stretching taut for an instant. Just behind him in the doorway in the shadows Ariadne presses her humanoid hands tighter to her own chest, her sapphire-blue eyes wide with anxious affection, her long fluffy white cat tail held still. The two flaming torches in iron sconces on either side of the doors flicker, warm orange light dancing across the carved spirals. The first stars above the doorway arch pulse faintly in the deep cobalt-blue evening sky. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** натяжение шёлковой нити (taut yarn thread tension), потрескивание двух факелов у входа (two doorway torches crackling), глухой сквозняк из Лабиринта (deep labyrinth draft), скрип кожаных сандалий по камню (sandal creak on stone), тревожный вдох Ариадны (Ariadne's anxious breath).

## Сцена 15

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_15_v1.jpg

**Промпт:** Intense action hold in the central Labyrinth chamber. Theseus mid-lunge in a dynamic combat pose body upright not on four legs, his humanoid arms gripping the bronze xiphos sword raised diagonally above his head in a frozen mid-strike, his blue cloak swept back behind him, his tabby cat tail straight out for balance. The Minotaur rears back further, his massive humanoid cat-paw arms swung wide claws extended in a defensive snarl, his cat muzzle wide open in a roar with bared fangs, steam pouring from his nostrils, his crimson-red feline eyes blazing. The bright vivid red thread of Ariadne anchors taut along the floor from the dark corridor behind Theseus around a stone column. Sparks and dust kick up around their feet. The bronze brazier flame surges, throwing dramatic shifting silhouettes against the curved walls. No blood, no gore, no wounds, no actual strike contact in this shot — only the charged frozen instant before impact. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** мощный рык Минотавра (powerful Minotaur roar), свист рассекающего воздух меча (sword swing whoosh), хруст камня под ногами (stone crunching underfoot), вспышка жаровни (brazier flare), боевой выдох героя (hero's combat exhale).

## Сцена 16

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_16_v2.jpg

**Промпт:** Slow dramatic aftermath hold in the same chamber. Theseus stands upright on two legs in a human-like victorious stance body upright not on four legs, his lowered bronze xiphos sword in his humanoid right hand, his chest rising and falling with heavy breaths, his torn blue cloak swaying. The colossal silhouette shadow of the fallen cat-Minotaur on the curved stone wall behind him slowly dissolves further — the vast feline shape with two curved bull horns and arms thrown wide breaking apart into wisps of dark smoke and drifting embers, the silhouette half-gone fading at the edges. A few scattered iron shackle pieces lie still on the floor at the edge of frame. The bright vivid red thread leads away from the chamber back toward the dark corridor still anchored. The bronze brazier flame burns dim and low, almost out, casting long purple shadows. Soft fall of gold dust and dark smoke particles drifts down through the air. Only shadow and dissipation — no body, no carcass, no blood. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** тяжёлое усталое дыхание Тесея (Theseus's heavy weary breathing), тихий звон оседающих кандалов (settling shackle clink), угасающее потрескивание жаровни (dying brazier crackle), шорох рассеивающегося дыма (dissipating smoke whisper), глубокая каменная тишина зала (deep stone chamber silence).

## Сцена 17

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_17_v2.jpg

**Промпт:** Hopeful medium shot at the colossal bronze entrance doors at dawn. Theseus strides upright through the threshold in a human-like walking pose body upright not on four legs, gathering up the bright vivid red thread in his humanoid hands, the yarn spooling rapidly around his humanoid wrist as he walks, his torn blue cloak swaying. Just outside the doorway Ariadne runs forward another step to meet him, her humanoid arms outstretched, her long fluffy white cat tail flowing behind her, her sapphire-blue eyes filled with relief. Behind them the heavy bronze double-doors slowly grind a fraction closer to closing on the dark Labyrinth corridors within. The first warm pink-and-gold rays of dawn break a touch higher over the horizon, lighting their figures. The cobalt-blue night sky still holds a few last fading stars above. The last palace torch on the wall sputters and dies in a thin curl of smoke. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 3 seconds.
**Звуки:** наматывание шёлковой нити на запястье (yarn spooling on wrist), низкий скрежет закрывающихся бронзовых ворот (closing gate grind), быстрые шаги по камню (quick stone footsteps), радостный вдох Ариадны (Ariadne's joyful breath in), угасание факела с шипением (torch dying hiss).

## Сцена 18

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_18_v1.jpg

**Промпт:** Lyrical sweeping hold of the trireme sailing across the open Aegean in golden afternoon light. The towering black sail billows once in a strong following wind, the great mast creaking. The dark hull cuts through deep teal-blue waves leaving a long bright wake. At the bow Theseus's humanoid arm tightens around Ariadne's shoulders, his blue cloak streaming. Ariadne's humanoid hand on the wooden railing steadies her, her cream hair flowing back, her white cat tail lifting in the wind. The thirteen rescued young captive cats in white tunics on the deck behind them shift weight, two of them pressing their humanoid hands to the railing. A pod of leaping dolphins arcs through the foreground waves, splashing back into the sea. The pink-and-gold sunset clouds shift slowly behind the great black sail. The receding cliffs of Crete on the horizon dim a touch. The silver owl of Athena symbol on the prow rocks gently. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** крики дельфинов и плеск (dolphin clicks and splashes), мощное хлопанье паруса (powerful sail flapping), скрип мачты и снастей (mast and rigging creak), крики чаек на закате (sunset gull cries), глубокий гул открытого моря (deep open-sea drone).

## Сцена 19

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_19_v4.jpg

**Промпт:** Foreboding medium-wide hold on the deck as the trireme nears the Attica coast. Theseus throws his humanoid arms wider toward the approaching shore in joyful relief, a closed-mouth grin of pure happiness on his cat muzzle, his blue cloak streaming, his tabby cat tail held high. Beside him Ariadne smiles warmly her white cat tail also lifted, her humanoid hand resting on his arm. The towering BLACK sail of the trireme above them billows once in the wind dominating the upper third of the frame against the pink sunset clouds — clearly NOT replaced. In the foreground at the foot of the mast the small folded square of bright clean white sailcloth tied with a blue ribbon lies forgotten on the deck planks, half-hidden under a coiled rope, only the corner of the white cloth catching one stray ray of sunset light, completely unnoticed. A single gull lands briefly on the railing nearby. Distant dark cliffs of Cape Sounion on the horizon slowly grow closer. Tragic ironic atmosphere. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** хлопанье чёрного паруса (black sail flapping), радостный закрытый выдох (joyful closed-mouth exhale), плеск волн о борт (waves against hull), крики чаек у берега (coastal gull cries), скрип палубных досок (deck plank creak).

## Сцена 20

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_20_v4.jpg

**Промпт:** Devastating slow hold atop Cape Sounion at sunset. King Aegeus's pale-blue eyes widen further with shattering grief, both his humanoid hands slowly raising to his cat muzzle in a frozen gasp of horror. His long ornate wooden staff slips from his humanoid hand and falls clattering onto the rocks beside him. His royal-blue robe with silver embroidery whips violently in the strong sea-wind, his silver beard streaming sideways. His silver-gray cat ears flatten back against his head. Far out on the deep teal sea below the tiny silhouette of the Greek trireme approaches with its towering BLACK sail still fully raised against the vast burning red-orange sunset sky, long golden god rays piercing scattered clouds. White seabirds wheel around the cliff. The white Greek temple ruins of Cape Sounion behind him stand cold against the headland. He does NOT move from the cliff in this shot — only his silent frozen horror. No fall in frame. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** оглушительный ветер на скале (roaring cliff wind), стук падающего посоха о камни (staff clattering on rocks), удары волн далеко внизу (waves crashing far below), приглушённый сдавленный вдох ужаса (muffled horrified breath intake), крики чаек на ветру (gulls in the wind).

## Сцена 21

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_21_v4.jpg

**Промпт:** Mournful empty wide hold of the same Cape Sounion cliff at deep dusk minutes later. The cliff edge stays completely empty — no figure of any kind. The king's long flowing royal-blue Greek robe with silver embroidery and his olive-leaf gold crown lie together on the bare windswept rocks at the edge, the strong sea-wind tugging at the empty robe and making the silver embroidery glint with each gust. The fallen wooden staff lies a foot away. Far below the deep teal-and-charcoal sea crashes slowly against the cliff base sending up white foam plumes. A few white feathers from a passing seabird drift slowly down through the air. The towering black sail of the trireme stays tiny on the dark horizon under the dimming sunset sky now fading to deep purple-blue. The white Greek temple ruins on the headland silhouette against the last glow of sunset. A single silver evening star pulses gently above the temple. No figure, no body, no carcass — only absence and wind. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** оглушительный ветер на пустой скале (howling empty cliff wind), мерные удары волн о подножие скалы (slow surf crashing below), хлопанье оставленного плаща (abandoned robe flapping), скрип каменных осыпей (loose stone scrape), еле слышный одинокий крик чайки (lone distant gull cry).

## Сцена 22

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_22_v2.jpg

**Промпт:** Sweeping serene aerial hold over the vast Aegean Sea at golden dawn. Gentle rolling waves stretch to a far misty horizon. Several distant white-sailed Greek ships drift slowly across the water, their tiny sails catching the early gold light. A pod of leaping dolphins arcs through the waves in the middle distance, splashing softly back. A flock of white gulls wheels slowly across the pink-and-gold dawn sky. On the right side of the frame the cliff of Cape Sounion with the white temple columns stands quiet. Above the cliff the faint translucent ghostly silhouette of King Aegeus in his royal-blue robe — gentle and dignified, his pale-blue eyes calm — fades slowly in and out of the morning mist like a memory watching over the sea. Soft golden warm light pulses slowly across the whole scene. No figure of any cat in clear focus — only the reflective vast sea. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** широкое дыхание моря (vast sea breathing), далёкий плеск дельфинов (distant dolphin splashes), крики чаек высоко в небе (high circling gulls), тихий ветер над храмом (soft wind over temple ruins), мягкое мифическое мерцание (soft mythic shimmer).

## Сцена 23

**Изображение:** content/Тесей и Минотавр/images/approved_images/scene_23_v2.jpg

**Промпт:** Reflective intimate hold in the throne room of the Athenian palace many years later at sunset. Theseus now a mature king sits leaned slightly forward on the blue-and-gold marble throne, his humanoid hand resting against his cat muzzle in deep thought, his other humanoid hand draped over the armrest holding the small folded square of clean white sailcloth — the same forgotten white sail from the ship — looking down at it pensively. He turns the folded cloth a fraction in his humanoid fingers, the ribbon catching the light. His tabby cat tail curls slowly at his feet. His thoughtful emerald-green eyes soften with weight. Beside the throne his late father's long ornate wooden staff stands respectfully propped upright, untouched, still bearing the same olive-leaf gold crown's reflection on the floor below it. Late golden hour light pours through the arched windows casting long warm shadows across the mosaic floor. Dust motes drift slowly through the beams. Melancholy wise atmosphere. No speech, no dialogue, no talking, no voices, no mouth movement, no music. 4 seconds.
**Звуки:** шорох сложенного паруса в ладони (folded sailcloth rustle), потрескивание далёких факелов в зале (distant hall torches crackling), тихий ветер в арочных окнах (soft window draft), глубокий задумчивый вдох (deep contemplative breath), еле слышное эхо тронного зала (faint throne room echo).
