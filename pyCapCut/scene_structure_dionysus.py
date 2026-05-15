"""
Структура сцен мифа «Дионис и Ариадна».

25 предложений озвучки разложены на 24 видеосцены:
сцена 001 содержит хук + интро, дальше одно предложение = одна сцена.
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
    "001": "Её бросили спящей\nна пустом острове.",
    "002": "Ариадна была дочерью\nцаря Крита.",
    "003": "Она дала Тесею\nклубок ниток.",
    "004": "Тесей одолел чудовище\nи поклялся жениться.",
    "005": "Корабль причалил\nк острову Наксос.",
    "006": "Ариадна уснула\nна тёплом песке.",
    "007": "Тесей поднял паруса\nи уплыл без неё.",
    "008": "Утром Ариадна\nпроснулась одна.",
    "009": "Море, ветер,\nпустой берег.",
    "010": "Она кричала\nи звала Тесея.",
    "011": "Но горизонт\nмолчал.",
    "012": "И тут с моря\nдонеслась музыка.",
    "013": "К острову плыл корабль,\nувитый виноградной лозой.",
    "014": "На носу стоял Дионис —\nбог вина и веселья.",
    "015": "Вокруг него плясали\nсатиры и нимфы.",
    "016": "Он увидел Ариадну\nи замер.",
    "017": "«Тот, кто бросил тебя —\nглупец. Будь моей женой.»",
    "018": "Свадьбу играли\nвсем Олимпом.",
    "019": "Дионис подарил Ариадне\nкорону со звёздами.",
    "020": "Прошли годы\nсчастья.",
    "021": "Когда Ариадны не стало,\nДионис держал её корону.",
    "022": "Он подбросил её\nв небо.",
    "023": "С тех пор горит\nсозвездие Северной Короны.",
    "024": "Кто бросает тебя —\nосвобождает место для бога.",
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
    Scene("001", ["sentence_001_v3.mp3", "sentence_002_v7.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_003_v9.mp3"], _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_004_v3.mp3"], _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_005_v3.mp3"], _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_006_v5.mp3"], _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_007_v8.mp3"], _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_008_v5.mp3"], _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_009_v1.mp3"], _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_010_v6.mp3"], _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_011_v6.mp3"], _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_012_v4.mp3"], _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_013_v1.mp3"], _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_014_v1.mp3"], _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_015_v10.mp3"], _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_016_v1.mp3"], _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_017_v8.mp3"], _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("017", ["sentence_018_v2.mp3"], _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_019_v4.mp3"], _shots("scene_18_v1.mp4"), transition_after="плавный"),
    Scene("019", ["sentence_020_v3.mp3"], _shots("scene_19_v1.mp4"), transition_after="плавный"),
    Scene("020", ["sentence_021_v3.mp3"], _shots("scene_20_v1.mp4"), transition_after="плавный"),
    Scene("021", ["sentence_022_v5.mp3"], _shots("scene_21_v1.mp4"), transition_after="плавный"),
    Scene("022", ["sentence_023_v10.mp3"], _shots("scene_22_v1.mp4"), transition_after="плавный"),
    Scene("023", ["sentence_024_v4.mp3"], _shots("scene_23_v1.mp4"), transition_after="плавный"),
    Scene("024", ["sentence_025_v7.mp3"], _shots("scene_24_v1.mp4")),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
