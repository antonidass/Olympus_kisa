"""
Структура сцен мифа «Орфей и Эвридика».

Один источник правды для pyCapCut-сборки. 28 предложений озвучки
разложены на 31 видеошот + CTA-аутро без озвучки (scene_32).
Предложения 009, 012 и 016 покрывают по два шота — это совпадает
с маппингом в prompts/video.md.
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
    "001": "Он спустился в Аид ради неё —\nно всё испортил за одну секунду.",
    "002": "",  # интро ("Орфей и Эвридика\nМиф за минуту") рендерится отдельно
    "003": "Орфей играл так,\nчто камни слушали.",
    "004": "Звери подходили ближе\nи забывали дышать.",
    "005": "Даже река могла остановиться,\nчтобы дослушать.",
    "006": "А потом он встретил Эвридику.",
    "007": "И вот тут миф решил:\nслишком много счастья.",
    "008": "Свадьба, цветы, клятвы —\nвсё как надо.",
    "009": "Но в траве скользнула змея,\nи праздник оборвался.",
    "010": "Эвридика ушла,\nне успев попрощаться.",
    "011": "Орфей не смирился.",
    "012": "Он спустился туда,\nкуда живые не ходят.",
    "013": "Страж замер,\nуслышав его лиру.",
    "014": "Тени остановились.",
    "015": "Даже тёмный царь опустил взгляд.",
    "016": "Ему разрешили забрать Эвридику —\nно с одним условием.",
    "017": "Идти вперёд.",
    "018": "Не оборачиваться.",
    "019": "Не проверять.",
    "020": "Не искать её руку.",
    "021": "Свет был уже близко.",
    "022": "Но Орфей не выдержал.",
    "023": "Он обернулся.",
    "024": "И Эвридика исчезла второй раз.",
    "025": "Коридор снова стал пустым.",
    "026": "Орфей вышел к свету один.",
    "027": "С лирой, которая больше не спасала.",
    "028": "И с эхом её последнего шёпота.",
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
    Scene("001", ["sentence_001_v3.mp3"],  _shots("scene_01_v1.mp4"),                      transition_after="плавный"),
    Scene("002", ["sentence_002_v4.mp3"],  _shots("scene_02_v2.mp4"),                      transition_after="плавный"),
    Scene("003", ["sentence_003_v6.mp3"],  _shots("scene_03_v1.mp4"),                      transition_after="плавный"),
    Scene("004", ["sentence_004_v8.mp3"],  _shots("scene_04_v1.mp4"),                      transition_after="плавный"),
    Scene("005", ["sentence_005_v6.mp3"],  _shots("scene_05_v1.mp4"),                      transition_after="плавный"),
    Scene("006", ["sentence_006_v3.mp3"],  _shots("scene_06_v1.mp4"),                      transition_after="плавный"),
    Scene("007", ["sentence_007_v10.mp3"], _shots("scene_07_v1.mp4"),                      transition_after="плавный"),
    Scene("008", ["sentence_008_v10.mp3"], _shots("scene_08_v1.mp4"),                      transition_after="плавный"),
    Scene("009", ["sentence_009_v4.mp3"],  _shots("scene_09_v1.mp4", "scene_10_v1.mp4"),   transition_after="плавный"),
    Scene("010", ["sentence_010_v1.mp3"],  _shots("scene_11_v1.mp4"),                      transition_after="плавный"),
    Scene("011", ["sentence_011_v3.mp3"],  _shots("scene_12_v1.mp4"),                      transition_after="плавный"),
    Scene("012", ["sentence_012_v1.mp3"],  _shots("scene_13_v1.mp4", "scene_14_v1.mp4"),   transition_after="плавный"),
    Scene("013", ["sentence_013_v9.mp3"],  _shots("scene_15_v1.mp4"),                      transition_after="плавный"),
    Scene("014", ["sentence_014_v10.mp3"], _shots("scene_16_v1.mp4"),                      transition_after="плавный"),
    Scene("015", ["sentence_015_v5.mp3"],  _shots("scene_17_v1.mp4"),                      transition_after="плавный"),
    Scene("016", ["sentence_016_v3.mp3"],  _shots("scene_18_v1.mp4", "scene_19_v1.mp4"),   transition_after="плавный"),
    Scene("017", ["sentence_017_v3.mp3"],  _shots("scene_20_v1.mp4"),                      transition_after="плавный"),
    Scene("018", ["sentence_018_v5.mp3"],  _shots("scene_21_v1.mp4"),                      transition_after="плавный"),
    Scene("019", ["sentence_019_v10.mp3"], _shots("scene_22_v1.mp4"),                      transition_after="плавный"),
    Scene("020", ["sentence_020_v4.mp3"],  _shots("scene_23_v1.mp4"),                      transition_after="плавный"),
    Scene("021", ["sentence_021_v2.mp3"],  _shots("scene_24_v1.mp4"),                      transition_after="плавный"),
    Scene("022", ["sentence_022_v3.mp3"],  _shots("scene_25_v1.mp4"),                      transition_after="плавный"),
    Scene("023", ["sentence_023_v2.mp3"],  _shots("scene_26_v1.mp4"),                      transition_after="плавный", trailing_pad=0.2),
    Scene("024", ["sentence_024_v3.mp3"],  _shots("scene_27_v1.mp4"),                      transition_after="плавный", trailing_pad=0.2),
    Scene("025", ["sentence_025_v4.mp3"],  _shots("scene_28_v1.mp4"),                      transition_after="плавный"),
    Scene("026", ["sentence_026_v3.mp3"],  _shots("scene_29_v1.mp4"),                      transition_after="плавный"),
    Scene("027", ["sentence_027_v8.mp3"],  _shots("scene_30_v1.mp4"),                      transition_after="плавный"),
    Scene("028", ["sentence_028_v3.mp3"],  _shots("scene_31_v1.mp4"),                      trailing_pad=1.8),
    Scene("032", [],                        _shots("scene_32_v1.mp4"),                      trailing_pad=8.0),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
