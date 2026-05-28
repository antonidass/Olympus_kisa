"""
Структура сцен мифа «Каллисто и Аркас».

Один источник правды для pyCapCut-сборки. 23 предложения озвучки
разложены на 24 видеошота в 23 «озвучковых» сценах. Сцена 001
содержит ДВА аудио (хук sent_001 + интро sent_002, один кадр-крючок
с накапливающимся караоке-титулом поверх). Сцены 006 и 020 покрывают
по два шота — это совпадает с маппингом в prompts/video.md.

Маппинг sentence ↔ scene_NN (источник: prompts/video.md):
  sent_001 + sent_002 → scene_01                  (1 шот) хук-кадр + караоке-титул
  sent_003            → scene_02                  (1 шот) Каллисто-нимфа ведёт охоту
  sent_004            → scene_03                  (1 шот) клятва под луной
  sent_005            → scene_04                  (1 шот) Зевс с Олимпа замечает
  sent_006            → scene_05                  (1 шот) Зевс блокирован клятвой
  sent_007            → scene_06 + scene_07       (2 шота) превращение Зевса + подход «подруги»
  sent_008            → scene_08                  (1 шот) Каллисто понимает обман
  sent_009            → scene_09                  (1 шот) нимфы купаются в ручье
  sent_010            → scene_10                  (1 шот) Артемида изгоняет
  sent_011            → scene_11                  (1 шот) Каллисто рожает Аркаса
  sent_012            → scene_12                  (1 шот) Гера превращает в медведицу
  sent_013            → scene_13                  (1 шот) медведица с янтарными глазами
  sent_014            → scene_14                  (1 шот) Аркас растёт у пастухов
  sent_015            → scene_15                  (1 шот) Аркас 15 лет — лучший охотник
  sent_016            → scene_16                  (1 шот) встреча с медведицей
  sent_017            → scene_17                  (1 шот) медведица бежит к сыну
  sent_018            → scene_18                  (1 шот) Аркас POV — несётся зверь
  sent_019            → scene_19                  (1 шот) копьё поднято
  sent_020            → scene_20 + scene_21       (2 шота) рука Зевса + звёздные потоки
  sent_021            → scene_22                  (1 шот) Большая и Малая Медведицы
  sent_022            → scene_23                  (1 шот) кружение вокруг Полярной
  sent_023            → scene_24                  (1 шот) моряк сверяет курс
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VideoShot:
    file: str
    start_from: float = 0.0
    muted: bool = True


@dataclass
class Scene:
    sid: str
    audios: List[str]
    videos: List[VideoShot]
    text: str = ""
    transition_after: Optional[str] = None
    trailing_pad: float = 0.0


SCENE_TEXTS = {
    "001": "",  # хук + интро-карточка (рендерятся karaoke_*.py поверх scene_01)
    "002": "Каллисто́ — нимфа из свиты Артеми́ды,\nлучшая охотница Аркадии.",
    "003": "Она поклялась богине: никаких женихов,\nтолько лук и луна.",
    "004": "Но Зевс увидел её\nи захотел заполучить.",
    "005": "А открыто не подойти —\nмешает клятва.",
    "006": "Он принял облик Артеми́ды\nи подошёл к Каллисто́ как «подруга».",
    "007": "Та расслабилась — и слишком поздно\nпоняла, кто перед ней.",
    "008": "Через пару месяцев\nнимфы купаются в ручье.",
    "009": "Артеми́да замечает живот Каллисто́\nи в ярости изгоняет её.",
    "010": "В лесу одна, она рожает\nсына — Арка́са.",
    "011": "На сцену выходит Ге́ра —\nи превращает Каллисто́ в медведицу.",
    "012": "Шерсть, когти, рык —\nмать осталась внутри, снаружи зверь.",
    "013": "Арка́с растёт у пастухов\nи ничего не знает о матери.",
    "014": "Пятнадцать лет спустя\nон уже лучший охотник в округе.",
    "015": "И вот однажды в лесу\nон встречает огромную медведицу.",
    "016": "Каллисто́ узнаёт сына\nи бежит к нему — обнять.",
    "017": "Арка́с видит только зверя,\nкоторый несётся прямо на него.",
    "018": "Он поднимает копьё.",
    "019": "Зевс хватает обоих в последний миг\nи забрасывает на небо.",
    "020": "Так появились Большая и Малая Медведицы —\nмать и сын.",
    "021": "С тех пор эти звёзды\nникогда не заходят за горизонт.",
    "022": "И по ним до сих пор\nсверяют север.",
}


def _shots(*files) -> List[VideoShot]:
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


SCENES: List[Scene] = [
    Scene("001", ["sentence_001_v14.mp3", "sentence_002_v13.mp3"],
                                            _shots("scene_01_v2.mp4"),                       transition_after="плавный"),
    Scene("002", ["sentence_003_v13.mp3"],  _shots("scene_02_v1.mp4"),                       transition_after="плавный"),
    Scene("003", ["sentence_004_v1.mp3"],   _shots("scene_03_v2.mp4"),                       transition_after="плавный"),
    Scene("004", ["sentence_005_v13.mp3"],  _shots("scene_04_v1.mp4"),                       transition_after="плавный"),
    Scene("005", ["sentence_006_v12.mp3"],  _shots("scene_05_v1.mp4"),                       transition_after="плавный"),
    Scene("006", ["sentence_007_v4.mp3"],   _shots("scene_06_v2.mp4", "scene_07_v1.mp4"),    transition_after="плавный"),
    Scene("007", ["sentence_008_v11.mp3"],  _shots("scene_08_v2.mp4"),                       transition_after="плавный"),
    Scene("008", ["sentence_009_v12.mp3"],  _shots("scene_09_v1.mp4"),                       transition_after="плавный"),
    Scene("009", ["sentence_010_v1.mp3"],   _shots("scene_10_v2.mp4"),                       transition_after="плавный"),
    Scene("010", ["sentence_011_v10.mp3"],  _shots("scene_11_v1.mp4"),                       transition_after="плавный"),
    Scene("011", ["sentence_012_v1.mp3"],   _shots("scene_12_v1.mp4"),                       transition_after="плавный"),
    Scene("012", ["sentence_013_v10.mp3"],  _shots("scene_13_v1.mp4"),                       transition_after="плавный"),
    Scene("013", ["sentence_014_v13.mp3"],  _shots("scene_14_v1.mp4"),                       transition_after="плавный"),
    Scene("014", ["sentence_015_v10.mp3"],  _shots("scene_15_v2.mp4"),                       transition_after="плавный"),
    Scene("015", ["sentence_016_v1.mp3"],   _shots("scene_16_v1.mp4"),                       transition_after="плавный"),
    Scene("016", ["sentence_017_v1.mp3"],   _shots("scene_17_v1.mp4"),                       transition_after="плавный"),
    Scene("017", ["sentence_018_v13.mp3"],  _shots("scene_18_v1.mp4"),                       transition_after="плавный"),
    Scene("018", ["sentence_019_v10.mp3"],  _shots("scene_19_v1.mp4"),                       transition_after="плавный"),
    Scene("019", ["sentence_020_v10.mp3"],  _shots("scene_20_v1.mp4", "scene_21_v1.mp4"),    transition_after="плавный"),
    Scene("020", ["sentence_021_v4.mp3"],   _shots("scene_22_v2.mp4"),                       transition_after="плавный"),
    Scene("021", ["sentence_022_v1.mp3"],   _shots("scene_23_v1.mp4"),                       transition_after="плавный", trailing_pad=0.2),
    Scene("022", ["sentence_023_v1.mp3"],   _shots("scene_24_v1.mp4"),                       trailing_pad=1.5),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
