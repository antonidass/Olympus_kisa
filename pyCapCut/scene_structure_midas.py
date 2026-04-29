"""
Структура сцен мифа «Мидас и золотое прикосновение».

Один источник правды для pyCapCut-сборки. 25 визуальных сцен,
в них заложены 35 sentence-mp3 (некоторые сцены склеивают
несколько коротких предложений — см. скобки в sid).
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


# ─────────────────────────────────────────────────────────────────────
# Субтитры. Сцена "01" — интро, её текст большим шрифтом через
# спецкейс в build_midas. Остальные — обычные субтитры внизу кадра.
# ─────────────────────────────────────────────────────────────────────

SCENE_TEXTS = {
    "01": "",  # интро ("Царь Мидас\nМиф за минуту") рендерится отдельно в build_midas
    "02": "Всё, чего касаетесь,\nстановится золотом.",
    "03": "Царь Мидас думал — это мечта.\nОказалось — ловушка.",
    "04": "Началось всё с жадности.\nМидас был богатейшим царём —\nзолото, слуги, пиры.",
    "05": "Глаза горели,\nруки тянулись к чужим сундукам.",
    "06": "Однажды в саду нашли\nпьяного старика — Силена,\nспутника самого Диониса.",
    "07": "Мидас не выдал гостя страже,\nа приютил.",
    "08": "Семь дней вина, песен\nи звёздных ночей.",
    "09": "Когда царь вернул Силена богу,\nДионис был в восторге.",
    "10": "«Проси, чего хочешь!\nЛюбое желание!»",
    "11": "«Пусть всё, чего коснусь,\nстановится золотом!»",
    "12": "Дионис вздохнул,\nно слово дал.",
    "13": "И началось.\nВетка — золото. Камень — золото.\nПесок под сандалиями — золото!",
    "14": "Царь танцевал в сияющем дворце,\nцеловал колонны,\nхохотал как ребёнок.",
    "15": "Потом сел ужинать.",
    "16": "Взял хлеб — холодный слиток.\nПоднёс кубок — золото вместо вина.",
    "17": "Улыбка сползла с лица.\nВ животе заурчало.",
    "18": "И тут вбежала маленькая дочь —\nобнять папу.\nМидас отпрянул, но поздно.",
    "19": "Девочка застыла\nзолотой статуей посреди зала.",
    "20": "Царь упал на колени.",
    "21": "«Дионис, забери дар!\nУмоляю!»",
    "22": "«Омойся в реке Пактол —\nи всё исчезнет».",
    "23": "Мидас помчался к реке,\nокунулся с головой.",
    "24": "Проклятое золото\nутекло в речные пески.",
    "25": "С тех пор в Пактоле\nнет-нет да и блеснёт золотая крупица —\nнапоминание о царской жадности.",
}


def _shots(*files) -> List[VideoShot]:
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


# ─────────────────────────────────────────────────────────────────────
# Сами сцены. Имена mp3 — те, что лежат в approved_sentences/
# (с суффиксом _vN — конкретный одобренный вариант). Видео — scene_NN_v1.mp4
# из content/Мидас и золотое прикосновение/video/.
#
# Переходы — базовый «плавный» для всех, кроме нескольких «драматичных»
# моментов. В CapCut легко поменять мышкой, если захочется другого.
# ─────────────────────────────────────────────────────────────────────

SCENES: List[Scene] = [
    Scene("01", ["sentence_001_v3.mp3"],                                              _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("02", ["sentence_002_v9.mp3"],                                              _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("03", ["sentence_003_v5.mp3", "sentence_004_v5.mp3"],                       _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("04", ["sentence_005_v1.mp3", "sentence_006_v4.mp3"],                       _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("05", ["sentence_007_v1.mp3"],                                              _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("06", ["sentence_008_v10.mp3"],                                             _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("07", ["sentence_009_v3.mp3"],                                              _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("08", ["sentence_010_v1.mp3"],                                              _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("09", ["sentence_011_v5.mp3"],                                              _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("10", ["sentence_012_v4.mp3", "sentence_013_v1.mp3"],                       _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("11", ["sentence_014_v8.mp3"],                                              _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("12", ["sentence_015_v7.mp3"],                                              _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("13", ["sentence_016_v2.mp3", "sentence_017_v2.mp3",
                 "sentence_018_v9.mp3", "sentence_019_v10.mp3"],                      _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("14", ["sentence_020_v1.mp3"],                                              _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("15", ["sentence_021_v8.mp3"],                                              _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("16", ["sentence_022_v1.mp3", "sentence_023_v9.mp3"],                       _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("17", ["sentence_024_v4.mp3", "sentence_025_v3.mp3"],                       _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("18", ["sentence_026_v3.mp3", "sentence_027_v8.mp3"],                       _shots("scene_18_v1.mp4"), transition_after="плавный"),
    Scene("19", ["sentence_028_v3.mp3"],                                              _shots("scene_19_v1.mp4"), transition_after="плавный", trailing_pad=0.3),
    Scene("20", ["sentence_029_v5.mp3"],                                              _shots("scene_20_v1.mp4"), transition_after="плавный"),
    Scene("21", ["sentence_030_v2.mp3", "sentence_031_v8.mp3"],                       _shots("scene_21_v1.mp4"), transition_after="плавный"),
    Scene("22", ["sentence_032_v3.mp3"],                                              _shots("scene_22_v1.mp4"), transition_after="плавный"),
    Scene("23", ["sentence_033_v8.mp3"],                                              _shots("scene_23_v1.mp4"), transition_after="плавный"),
    Scene("24", ["sentence_034_v8.mp3"],                                              _shots("scene_24_v1.mp4"), transition_after="плавный"),
    Scene("25", ["sentence_035_v3.mp3"],                                              _shots("scene_25_v1.mp4"), trailing_pad=2.0),
]

# Заполняем поле text из SCENE_TEXTS
for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
