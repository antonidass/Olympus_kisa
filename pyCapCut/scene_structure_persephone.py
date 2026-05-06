"""
Структура сцен мифа «Персефона и Аид».

Один источник правды для pyCapCut-сборки. 24 предложения озвучки
разложены на 28 видеошотов. Сцены 004, 006, 013 и 020 покрывают
по два шота — это совпадает с маппингом в prompts/video.md.

Маппинг sentence ↔ scene_NN (источник: prompts/video.md):
  sent_001 → scene_01                    (1 шот)
  sent_002 → scene_02                    (1 шот) интро-карточка
  sent_003 → scene_03                    (1 шот)
  sent_004 → scene_04 + scene_05         (2 шота) трещина + колесница
  sent_005 → scene_06                    (1 шот)
  sent_006 → scene_07 + scene_08         (2 шота) Аид схватил + унеслись
  sent_007 → scene_09                    (1 шот)
  sent_008 → scene_10                    (1 шот)
  sent_009 → scene_11                    (1 шот)
  sent_010 → scene_12                    (1 шот)
  sent_011 → scene_13                    (1 шот)
  sent_012 → scene_14                    (1 шот)
  sent_013 → scene_15 + scene_16         (2 шота) увядшие поля + лёд
  sent_014 → scene_17                    (1 шот)
  sent_015 → scene_18                    (1 шот)
  sent_016 → scene_19                    (1 шот)
  sent_017 → scene_20                    (1 шот)
  sent_018 → scene_21                    (1 шот)
  sent_019 → scene_22                    (1 шот)
  sent_020 → scene_23 + scene_24         (2 шота) под землёй + наверху
  sent_021 → scene_25                    (1 шот)
  sent_022 → scene_26                    (1 шот)
  sent_023 → scene_27                    (1 шот)
  sent_024 → scene_28                    (1 шот) финал
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
    "001": "Её украл владыка мёртвых —\nи мир впервые увидел зиму.",
    "002": "",  # интро-карточка («Персефона и Аид\nМиф за минуту») рендерится отдельно
    "003": "Дочь Деметры собирала цветы\nна весеннем лугу.",
    "004": "Земля треснула —\nвылетела чёрная колесница.",
    "005": "На ней — сам Аид,\nвладыка царства мёртвых.",
    "006": "Он схватил её и умчал\nпод землю.",
    "007": "Ни сватов, ни записок —\nпросто увёз и сделал женой.",
    "008": "Деметра кинулась\nискать дочь.",
    "009": "Девять дней с факелом\nобошла всю землю.",
    "010": "Гелиос шепнул правду:\n«Это Аид».",
    "011": "«И, кстати, Зевс\nбыл в курсе».",
    "012": "Деметра впала в горе\nи бросила работу.",
    "013": "Поля высохли,\nреки замёрзли.",
    "014": "Люди голодают,\nжертв богам нет.",
    "015": "Зевс в панике:\nпора возвращать девочку.",
    "016": "Гермес летит\nв подземное царство.",
    "017": "А Персефона уже не плачет —\nсидит на троне, царица.",
    "018": "И успела съесть\nзёрнышко граната.",
    "019": "А кто поел в царстве мёртвых —\nсвязан с ним навсегда.",
    "020": "Треть года под землёй,\nостальное — наверху.",
    "021": "Дочь возвращается —\nприходит весна.",
    "022": "Дочь уходит —\nнаступает зима.",
    "023": "С тех пор зима —\nэто не погода.",
    "024": "Это разлука\nматери с дочерью.",
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
    Scene("001", ["sentence_001_v9.mp3"],  _shots("scene_01_v1.mp4"),                      transition_after="плавный"),
    Scene("002", ["sentence_002_v3.mp3"],  _shots("scene_02_v1.mp4"),                      transition_after="плавный"),
    Scene("003", ["sentence_003_v3.mp3"],  _shots("scene_03_v1.mp4"),                      transition_after="плавный"),
    Scene("004", ["sentence_004_v3.mp3"],  _shots("scene_04_v1.mp4", "scene_05_v1.mp4"),   transition_after="плавный"),
    Scene("005", ["sentence_005_v6.mp3"],  _shots("scene_06_v1.mp4"),                      transition_after="плавный"),
    Scene("006", ["sentence_006_v4.mp3"],  _shots("scene_07_v1.mp4", "scene_08_v1.mp4"),   transition_after="плавный"),
    Scene("007", ["sentence_007_v4.mp3"],  _shots("scene_09_v2.mp4"),                      transition_after="плавный"),
    Scene("008", ["sentence_008_v10.mp3"], _shots("scene_10_v1.mp4"),                      transition_after="плавный"),
    Scene("009", ["sentence_009_v5.mp3"],  _shots("scene_11_v1.mp4"),                      transition_after="плавный"),
    Scene("010", ["sentence_010_v4.mp3"],  _shots("scene_12_v1.mp4"),                      transition_after="плавный"),
    Scene("011", ["sentence_011_v10.mp3"], _shots("scene_13_v1.mp4"),                      transition_after="плавный"),
    Scene("012", ["sentence_012_v7.mp3"],  _shots("scene_14_v1.mp4"),                      transition_after="плавный"),
    Scene("013", ["sentence_013_v5.mp3"],  _shots("scene_15_v1.mp4", "scene_16_v1.mp4"),   transition_after="плавный"),
    Scene("014", ["sentence_014_v6.mp3"],  _shots("scene_17_v2.mp4"),                      transition_after="плавный"),
    Scene("015", ["sentence_015_v7.mp3"],  _shots("scene_18_v1.mp4"),                      transition_after="плавный"),
    Scene("016", ["sentence_016_v1.mp3"],  _shots("scene_19_v1.mp4"),                      transition_after="плавный"),
    Scene("017", ["sentence_017_v8.mp3"],  _shots("scene_20_v2.mp4"),                      transition_after="плавный"),
    Scene("018", ["sentence_018_v10.mp3"], _shots("scene_21_v2.mp4"),                      transition_after="плавный"),
    Scene("019", ["sentence_019_v1.mp3"],  _shots("scene_22_v1.mp4"),                      transition_after="плавный"),
    Scene("020", ["sentence_020_v9.mp3"],  _shots("scene_23_v2.mp4", "scene_24_v1.mp4"),   transition_after="плавный"),
    Scene("021", ["sentence_021_v3.mp3"],  _shots("scene_25_v1.mp4"),                      transition_after="плавный"),
    Scene("022", ["sentence_022_v6.mp3"],  _shots("scene_26_v2.mp4"),                      transition_after="плавный"),
    Scene("023", ["sentence_023_v10.mp3"], _shots("scene_27_v2.mp4"),                      transition_after="плавный", trailing_pad=0.2),
    Scene("024", ["sentence_024_v4.mp3"],  _shots("scene_28_v1.mp4"),                      trailing_pad=1.5),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
