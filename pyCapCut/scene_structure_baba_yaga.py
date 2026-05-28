"""
Структура сцен мифа «Баба-Яга».

23 предложения озвучки разложены на 23 видеошота (по одному на сцену).
ИСКЛЮЧЕНИЕ этого мифа: титульная строка «Ба́ба-Яга́. Миф за минуту.»
убрана из озвучки целиком, поэтому отдельного sentence_002 (титула) нет —
sentence_001 это сам хук, а sentence_002 это уже первое сюжетное
предложение «Её хозяйка — старуха с одной костяной ногой». Нумерация
sentence_NN = scene_NN без сдвига.

Маппинг sentence ↔ scene_NN (источник: content/Баба-Яга/prompts/video.md):
  sent_001 → scene_01   (хук: изба на куриных ногах в ночном лесу)
  sent_002 → scene_02   (Яга в дверях, костяная нога)
  sent_003 → scene_03   (порог двух миров)
  sent_004 → scene_04   (Яга у древнего дуба)
  sent_005 → scene_05   (путник шепчет формулу)
  sent_006 → scene_06   (изба поворачивается на куриных ногах)
  sent_007 → scene_07   (дверь скрипит и открывается)
  sent_008 → scene_08   (устье русской печи)
  sent_009 → scene_09   (ступа с метлой и пестом у входа)
  sent_010 → scene_10   (Яга летит в ступе через небо)
  sent_011 → scene_11   (забор из костей с черепами)
  sent_012 → scene_12   (крупный план: череп на колу)
  sent_013 → scene_13   (Яга отдаёт путнику череп-фонарь)
  sent_014 → scene_14   (Яга сажает в печь непрошеного гостя)
  sent_015 → scene_15   (портрет Яги — взгляд в камеру)
  sent_016 → scene_16   (силуэт против луны, клюка вертикально)
  sent_017 → scene_17   (сплит: печь vs клубок)
  sent_018 → scene_18   (три рунических знака вопроса)
  sent_019 → scene_19   (три задачи: мак, зерно, дырявое ведро)
  sent_020 → scene_20   (котёл с зелёным варом и призраком)
  sent_021 → scene_21   (три магических дара: клубок, конь, меч-кладене́ц)
  sent_022 → scene_22   (POV: гигантская куриная лапа)
  sent_023 → scene_23   (POV: лапоть делает шаг)
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


# Короткие плейсхолдер-подписи. Karaoke их потом удалит — нужны только
# для того, чтобы в драфте оказался хоть один text-сегмент (karaoke
# берёт его как шаблон стиля). См. memory feedback_no_placeholder_subtitles.
SCENE_TEXTS = {
    "001": "На границе живого и\nмёртвого мира стоит изба",
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
    Scene("001", ["sentence_001_v1.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_002_v3.mp3"], _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_003_v3.mp3"], _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_004_v1.mp3"], _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_005_v1.mp3"], _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_006_v3.mp3"], _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_007_v1.mp3"], _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_008_v1.mp3"], _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_009_v1.mp3"], _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_010_v3.mp3"], _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_011_v3.mp3"], _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_012_v3.mp3"], _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_013_v3.mp3"], _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_014_v1.mp3"], _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_015_v2.mp3"], _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_016_v2.mp3"], _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("017", ["sentence_017_v1.mp3"], _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_018_v1.mp3"], _shots("scene_18_v1.mp4"), transition_after="плавный"),
    Scene("019", ["sentence_019_v1.mp3"], _shots("scene_19_v1.mp4"), transition_after="плавный"),
    Scene("020", ["sentence_020_v2.mp3"], _shots("scene_20_v1.mp4"), transition_after="плавный"),
    Scene("021", ["sentence_021_v2.mp3"], _shots("scene_21_v1.mp4"), transition_after="плавный"),
    Scene("022", ["sentence_022_v1.mp3"], _shots("scene_22_v1.mp4"), transition_after="плавный"),
    Scene("023", ["sentence_023_v2.mp3"], _shots("scene_23_v1.mp4"), trailing_pad=1.5),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
