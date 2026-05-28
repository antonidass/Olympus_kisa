"""
Структура сцен мифа «Аполлон и Кассандра».

16 предложений озвучки → 20 видеошотов в 15 таймлайн-сценах. Сцена 001
объединяет хук (sent_001) и интро-титул (sent_002) на ОДНОМ визуале
scene_01_v1.mp4 — двухстрочный титул «Аполло́н и Касса́ндра / Миф за минуту»
накладывается караоке-скриптом поверх второго аудио. CTA-аутро нет —
финальный кадр заканчивается по последней озвучке.

Маппинг sentence ↔ scene_NN (из content/Аполлон и Кассандра/prompts/images.md):
  sent_001 + sent_002 → scene_01            (1 шот)
  sent_003            → scene_02            (1 шот)
  sent_004            → scene_03            (1 шот)
  sent_005            → scene_04            (1 шот)
  sent_006            → scene_05            (1 шот)
  sent_007            → scene_06 + scene_07 (2 шота)
  sent_008            → scene_08            (1 шот)
  sent_009            → scene_09            (1 шот)
  sent_010            → scene_10 + scene_11 (2 шота)
  sent_011            → scene_12            (1 шот)
  sent_012            → scene_13 + scene_14 (2 шота)
  sent_013            → scene_15 + scene_16 (2 шота)
  sent_014            → scene_17            (1 шот)
  sent_015            → scene_18            (1 шот)
  sent_016            → scene_19 + scene_20 (2 шота)
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
    "001": "Аполло́н и Касса́ндра\nМиф за минуту",
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
    Scene("001", ["sentence_001_v2.mp3", "sentence_002_v4.mp3"], _shots("scene_01_v1.mp4")),
    Scene("002", ["sentence_003_v2.mp3"],  _shots("scene_02_v3.mp4")),
    Scene("003", ["sentence_004_v1.mp3"],  _shots("scene_03_v1.mp4")),
    Scene("004", ["sentence_005_v1.mp3"],  _shots("scene_04_v1.mp4")),
    Scene("005", ["sentence_006_v1.mp3"],  _shots("scene_05_v1.mp4")),
    Scene("006", ["sentence_007_v3.mp3"],  _shots("scene_06_v1.mp4", "scene_07_v1.mp4")),
    Scene("007", ["sentence_008_v4.mp3"],  _shots("scene_08_v1.mp4")),
    Scene("008", ["sentence_009_v10.mp3"], _shots("scene_09_v1.mp4")),
    Scene("009", ["sentence_010_v3.mp3"],  _shots("scene_10_v1.mp4", "scene_11_v1.mp4")),
    Scene("010", ["sentence_011_v5.mp3"],  _shots("scene_12_v2.mp4")),
    Scene("011", ["sentence_012_v9.mp3"],  _shots("scene_13_v1.mp4", "scene_14_v1.mp4")),
    Scene("012", ["sentence_013_v7.mp3"],  _shots("scene_15_v1.mp4", "scene_16_v1.mp4")),
    Scene("013", ["sentence_014_v1.mp3"],  _shots("scene_17_v1.mp4")),
    Scene("014", ["sentence_015_v7.mp3"],  _shots("scene_18_v1.mp4")),
    Scene("015", ["sentence_016_v7.mp3"],  _shots("scene_19_v1.mp4", ("scene_20_v1.mp4", 0.5))),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
