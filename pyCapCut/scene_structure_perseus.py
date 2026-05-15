"""
Структура сцен мифа «Персей и Медуза».

Один источник правды для pyCapCut-сборки. 23 предложения озвучки
разложены на 24 видеошота. Сцена 002 содержит два аудио (хук + интро),
а сцены 014 и 018 покрывают по два шота —
это совпадает с маппингом в prompts/video.md.

Маппинг sentence ↔ scene_NN:
  sent_001 → scene_01
  sent_002 + sent_003 → scene_02
  sent_004 → scene_03
  sent_005 → scene_04
  sent_006 → scene_05
  sent_007 → scene_06
  sent_008 → scene_07
  sent_009 → scene_08
  sent_010 → scene_09
  sent_011 → scene_10
  sent_012 → scene_11
  sent_013 → scene_12
  sent_014 → scene_13
  sent_015 → scene_14 + scene_15
  sent_016 → scene_16
  sent_017 → scene_17
  sent_018 → scene_18
  sent_019 → scene_19 + scene_20
  sent_020 → scene_21
  sent_021 → scene_22
  sent_022 → scene_23
  sent_023 → scene_24
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
    "001": "Один взгляд Горгоны —\nи ты камень навсегда.",
    "002": "",  # scene_02 содержит hook-continuation + intro; титр рендерится karaoke_perseus.py
    "003": "Царь хотел жениться\nна матери Персея.",
    "004": "На пиру он попросил\nдары для свадьбы.",
    "005": "Персей поклялся принести\nхоть голову Медузы.",
    "006": "Полидект тут же\nпоймал его на слове.",
    "007": "К Персею\nявились боги.",
    "008": "Афина дала\nзеркальный щит.",
    "009": "Гермес — сандалии\nи серп.",
    "010": "Нимфы — шлем-невидимку\nи волшебный мешок.",
    "011": "Сначала он нашёл Грай —\nтрёх старух с одним глазом.",
    "012": "Он украл глаз\nи выпытал путь к горгонам.",
    "013": "В пещере спали\nтри сестры.",
    "014": "Персей крался спиной вперёд,\nглядя только в отражение.",
    "015": "Один взмах серпа —\nи голова в мешке.",
    "016": "Сёстры проснулись,\nно героя не нашли.",
    "017": "Дома царь всё ещё\nпреследовал его мать.",
    "018": "Персей ворвался:\n«Вот мой свадебный подарок!»",
    "019": "Полидект со свитой\nзастыли камнем.",
    "020": "Мать была\nсвободна.",
    "021": "Голова Медузы стала\nзнаком на щите Афины.",
    "022": "Глупая клятва сделала\nиз юноши героя.",
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
    Scene("001", ["sentence_001_v8.mp3"],  _shots(("scene_01_v2.mp4", 1.0)),               transition_after="плавный"),
    Scene("002", ["sentence_002_v10.mp3", "sentence_003_v1.mp3"], _shots("scene_02_v2.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_004_v8.mp3"],  _shots("scene_03_v1.mp4"),                      transition_after="плавный"),
    Scene("004", ["sentence_005_v2.mp3"],  _shots("scene_04_v1.mp4"),                      transition_after="плавный"),
    Scene("005", ["sentence_006_v6.mp3"],  _shots("scene_05_v1.mp4"),                      transition_after="плавный"),
    Scene("006", ["sentence_007_v3.mp3"],  _shots("scene_06_v1.mp4"),                      transition_after="плавный"),
    Scene("007", ["sentence_008_v3.mp3"],  _shots("scene_07_v1.mp4"),                      transition_after="плавный"),
    Scene("008", ["sentence_009_v10.mp3"], _shots("scene_08_v1.mp4"),                      transition_after="плавный"),
    Scene("009", ["sentence_010_v2.mp3"],  _shots("scene_09_v1.mp4"),                      transition_after="плавный"),
    Scene("010", ["sentence_011_v9.mp3"],  _shots("scene_10_v1.mp4"),                      transition_after="плавный"),
    Scene("011", ["sentence_012_v5.mp3"],  _shots("scene_11_v1.mp4"),                      transition_after="плавный"),
    Scene("012", ["sentence_013_v10.mp3"], _shots("scene_12_v2.mp4"),                      transition_after="плавный"),
    Scene("013", ["sentence_014_v1.mp3"],  _shots("scene_13_v2.mp4"),                      transition_after="плавный"),
    Scene("014", ["sentence_015_v9.mp3"],  _shots("scene_14_v1.mp4", "scene_15_v2.mp4"),   transition_after="плавный"),
    Scene("015", ["sentence_016_v10.mp3"], _shots("scene_16_v2.mp4"),                      transition_after="плавный"),
    Scene("016", ["sentence_017_v8.mp3"],  _shots("scene_17_v2.mp4"),                      transition_after="плавный"),
    Scene("017", ["sentence_018_v5.mp3"],  _shots("scene_18_v1.mp4"),                      transition_after="плавный"),
    Scene("018", ["sentence_019_v5.mp3"],  _shots("scene_19_v1.mp4", "scene_20_v1.mp4"),   transition_after="плавный"),
    Scene("019", ["sentence_020_v7.mp3"],  _shots("scene_21_v1.mp4"),                      transition_after="плавный"),
    Scene("020", ["sentence_021_v1.mp3"],  _shots("scene_22_v1.mp4"),                      transition_after="плавный"),
    Scene("021", ["sentence_022_v8.mp3"],  _shots("scene_23_v1.mp4"),                      transition_after="плавный"),
    Scene("022", ["sentence_023_v8.mp3"],  _shots("scene_24_v1.mp4")),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
