"""
Структура сцен мифа «Фемида».

23 предложения озвучки → 18 видеосцен после объединения пар:
  scene_001 = sent_001 + sent_002  (хук + интро-титул)
  scene_002…007 = по одному предложению (sent_003…008)
  scene_008 = sent_009 + sent_010   (мерж — "не заметила подмены" / "верила наряду")
  scene_009…012 = по одному предложению (sent_011…014)
  scene_013 = sent_015 + sent_016   (мерж — настоящий вор + гладкая тога)
  scene_014 = sent_017 + sent_018   (мерж — окаменела + глаза солгали)
  scene_015 = sent_019              (срывает пояс)
  scene_016 = sent_020              (завязывает глаза)
  scene_017 = sent_021              ("больше никогда — по виду")
  scene_018 = sent_022 + sent_023   (мерж — финальная sunset-статуя)

CTA-аутро нет — финальный кадр заканчивается по последней озвучке.
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
    "001": "Феми́да\nМиф за минуту",
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
    Scene("001", ["sentence_001_v1.mp3", "sentence_002_v10.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_003_v1.mp3"], _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_004_v4.mp3"], _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_005_v1.mp3"], _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_006_v4.mp3"], _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_007_v10.mp3"], _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_008_v1.mp3"], _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_009_v1.mp3", "sentence_010_v9.mp3"], _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_011_v5.mp3"], _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_012_v1.mp3"], _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_013_v2.mp3"], _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_014_v10.mp3"], _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_015_v1.mp3", "sentence_016_v1.mp3"], _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_017_v1.mp3", "sentence_018_v1.mp3"], _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_019_v1.mp3"], _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_020_v7.mp3"], _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("017", ["sentence_021_v10.mp3"], _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_022_v2.mp3", "sentence_023_v3.mp3"], _shots("scene_18_v1.mp4")),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
