"""
Структура сцен мифа «Цирцея и Одиссей».

20 предложений озвучки → 19 видеошотов в 19 таймлайн-сценах. Сцена 001
объединяет хук (sent_001) и интро-титул (sent_002) на ОДНОМ визуале
scene_01_v2.mp4 — двухстрочный титул «Цирце́я и Одиссе́й / Миф за минуту»
накладывается караоке-скриптом поверх второго аудио. CTA-аутро нет —
финальный кадр заканчивается по последней озвучке.

Маппинг sentence ↔ scene_NN:
  sent_001 + sent_002 → scene_01   (хук + интро-карточка)
  sent_003 → scene_02 ... sent_020 → scene_19
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
    "001": "Цирце́я и Одиссе́й\nМиф за минуту",
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
    Scene("001", ["sentence_001_v4.mp3", "sentence_002_v6.mp3"], _shots("scene_01_v2.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_003_v3.mp3"],  _shots("scene_02_v1.mp4"),  transition_after="плавный"),
    Scene("003", ["sentence_004_v6.mp3"],  _shots("scene_03_v1.mp4"),  transition_after="плавный"),
    Scene("004", ["sentence_005_v3.mp3"],  _shots("scene_04_v1.mp4"),  transition_after="плавный"),
    Scene("005", ["sentence_006_v10.mp3"], _shots("scene_05_v1.mp4"),  transition_after="плавный"),
    Scene("006", ["sentence_007_v5.mp3"],  _shots("scene_06_v1.mp4"),  transition_after="плавный"),
    Scene("007", ["sentence_008_v1.mp3"],  _shots("scene_07_v1.mp4"),  transition_after="плавный"),
    Scene("008", ["sentence_009_v1.mp3"],  _shots("scene_08_v1.mp4"),  transition_after="плавный"),
    Scene("009", ["sentence_010_v2.mp3"],  _shots("scene_09_v2.mp4"),  transition_after="плавный"),
    Scene("010", ["sentence_011_v5.mp3"],  _shots("scene_10_v1.mp4"),  transition_after="плавный"),
    Scene("011", ["sentence_012_v3.mp3"],  _shots("scene_11_v1.mp4"),  transition_after="плавный"),
    Scene("012", ["sentence_013_v6.mp3"],  _shots("scene_12_v1.mp4"),  transition_after="плавный"),
    Scene("013", ["sentence_014_v6.mp3"],  _shots("scene_13_v1.mp4"),  transition_after="плавный"),
    Scene("014", ["sentence_015_v10.mp3"], _shots("scene_14_v1.mp4"),  transition_after="плавный"),
    Scene("015", ["sentence_016_v8.mp3"],  _shots("scene_15_v2.mp4"),  transition_after="плавный"),
    Scene("016", ["sentence_017_v10.mp3"], _shots("scene_16_v1.mp4"),  transition_after="плавный"),
    Scene("017", ["sentence_018_v3.mp3"],  _shots("scene_17_v1.mp4"),  transition_after="плавный"),
    Scene("018", ["sentence_019_v9.mp3"],  _shots("scene_18_v1.mp4"),  transition_after="плавный"),
    Scene("019", ["sentence_020_v9.mp3"],  _shots("scene_19_v1.mp4")),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
