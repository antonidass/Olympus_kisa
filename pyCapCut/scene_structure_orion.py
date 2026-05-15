"""
Структура сцен мифа «Орион и Артемида».

25 предложений озвучки разложены на 23 видеосцены:
сцена 001 содержит хук + интро, сцена 023 содержит две финальные фразы.
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
    "001": "Она попала точно в цель,\nне зная, кого убивает.",
    "002": "Орион был охотником,\nчьи стрелы не знали промаха.",
    "003": "Сын Посейдона шагал\nпо морю, как по тропе.",
    "004": "От его выстрела\nне уходил ни один зверь.",
    "005": "Артемида держала сердце\nна замке.",
    "006": "И все же небо свело их\nв одном лесу.",
    "007": "Они охотились\nдо рассвета.",
    "008": "У костра Артемида\nвпервые не молчала.",
    "009": "Это заметил Аполлон,\nее брат-близнец.",
    "010": "Он не простил сестре\nсмертного.",
    "011": "И решил убрать Ориона\nее же руками.",
    "012": "Орион заплыл\nдалеко в море.",
    "013": "С берега осталась\nтолько темная точка.",
    "014": "Аполлон бросил вызов:\nтуда даже ты не попадешь.",
    "015": "Богиня охоты\nподняла лук.",
    "016": "Серебряная стрела\nполетела над волнами.",
    "017": "Точка исчезла.",
    "018": "Утром море вернуло\nОриона на берег.",
    "019": "Артемида поняла все\nслишком поздно.",
    "020": "Ни сила, ни лунный свет\nего уже не вернут.",
    "021": "Тогда она подняла Ориона\nк небу.",
    "022": "С тех пор он стоит\nсреди звезд.",
    "023": "Не рядом с ней,\nно в ее небе каждую ночь.",
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
    Scene("001", ["sentence_001_v10.mp3", "sentence_002_v1.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_003_v9.mp3"], _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_004_v1.mp3"], _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_005_v7.mp3"], _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_006_v5.mp3"], _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_007_v3.mp3"], _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_008_v1.mp3"], _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_009_v6.mp3"], _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_010_v9.mp3"], _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_011_v7.mp3"], _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_012_v10.mp3"], _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_013_v4.mp3"], _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_014_v2.mp3"], _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_015_v6.mp3"], _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_016_v3.mp3"], _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_017_v1.mp3"], _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("017", ["sentence_018_v1.mp3"], _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_019_v1.mp3"], _shots("scene_18_v1.mp4"), transition_after="плавный"),
    Scene("019", ["sentence_020_v1.mp3"], _shots("scene_19_v1.mp4"), transition_after="плавный"),
    Scene("020", ["sentence_021_v10.mp3"], _shots("scene_20_v1.mp4"), transition_after="плавный"),
    Scene("021", ["sentence_022_v5.mp3"], _shots("scene_21_v1.mp4"), transition_after="плавный"),
    Scene("022", ["sentence_023_v8.mp3"], _shots("scene_22_v1.mp4"), transition_after="плавный"),
    Scene("023", ["sentence_024_v1.mp3", "sentence_025_v7.mp3"], _shots("scene_23_v2.mp4")),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
