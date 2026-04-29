"""
Структура сцен мифа «Тесей и Минотавр».

Один источник правды для pyCapCut-сборки. 16 предложений озвучки,
разложенные на 23 видеошота (некоторые предложения покрывают
2 шота — см. images.md / video.md).

Маппинг sentence ↔ scene_NN:
  sent_001 → scene_01                    (1 шот)  интро
  sent_002 → scene_02 + scene_03         (2 шота) проигранная война + чёрный корабль
  sent_003 → scene_04                    (1 шот)  пустая гавань Афин
  sent_004 → scene_05                    (1 шот)  вход в Лабиринт
  sent_005 → scene_06 + scene_07         (2 шота) Минотавр + происхождение
  sent_006 → scene_08                    (1 шот)  следы погибших
  sent_007 → scene_09                    (1 шот)  Тесей вызывается во дворце
  sent_008 → scene_10 + scene_11         (2 шота) посадка + клятва отцу
  sent_009 → scene_12                    (1 шот)  встреча с Ариадной на Крите
  sent_010 → scene_13 + scene_14         (2 шота) нить вручается + у входа
  sent_011 → scene_15 + scene_16         (2 шота) бой + растворение зверя
  sent_012 → scene_17 + scene_18         (2 шота) выход + отплытие
  sent_013 → scene_19                    (1 шот)  забытый белый парус на корабле
  sent_014 → scene_20 + scene_21         (2 шота) Эгей видит чёрный + пустая скала
  sent_015 → scene_22                    (1 шот)  Эгейское море
  sent_016 → scene_23                    (1 шот)  возмужавший Тесей
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
# спецкейс в build_theseus. Остальные — обычные субтитры внизу кадра.
# ─────────────────────────────────────────────────────────────────────

SCENE_TEXTS = {
    "01": "",  # интро ("Тесей и Минотавр\nМиф за минуту") рендерится отдельно в build_theseus
    "02": "Афины проиграли войну Криту\nи платили жуткую дань.",
    "03": "Назад не возвращался никто.",
    "04": "А исчезали они\nв Лабиринте.",
    "05": "В сердце Лабиринта жил Минотавр —\nполучеловек-полубык.",
    "06": "Зверь, от которого\nникто не уходил живым.",
    "07": "Молодой царевич Тесей\nне выдержал.",
    "08": "Сел на корабль с чёрными парусами:\n«Вернусь — сменю на белый».",
    "09": "На Крите его встретила Ариадна —\nдочь царя Миноса.",
    "10": "Влюбилась с первого взгляда\nи сунула клубок нити.",
    "11": "В глубине Лабиринта\nТесей одолел Минотавра.",
    "12": "По нити вышел наружу,\nзабрал Ариадну и поплыл домой.",
    "13": "Но в радости герой забыл главное —\nподнять белый парус.",
    "14": "Эгей увидел чёрный —\nи не пережил этой вести.",
    "15": "С тех пор то море\nзовётся Эгейским.",
    "16": "Одна забытая мелочь\nстоит дороже победы.",
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
# из content/Тесей и Минотавр/video/.
#
# Переходы — базовый «плавный» для всех. В CapCut легко поменять
# мышкой, если захочется другого.
#
# trailing_pad на драматических паузах:
#   - sid="13" (забытый белый парус) — пауза перед трагедией
#   - sid="14" (Эгей не пережил вести) — пауза после трагедии
#   - sid="16" (мораль и финал) — большой хвост на затухание музыки
# ─────────────────────────────────────────────────────────────────────

SCENES: List[Scene] = [
    Scene("01", ["sentence_001_v6.mp3"],   _shots("scene_01_v1.mp4"),                       transition_after="плавный"),
    Scene("02", ["sentence_002_v3.mp3"],   _shots("scene_02_v1.mp4", "scene_03_v1.mp4"),    transition_after="плавный"),
    Scene("03", ["sentence_003_v1.mp3"],   _shots("scene_04_v1.mp4"),                       transition_after="плавный"),
    Scene("04", ["sentence_004_v10.mp3"],  _shots("scene_05_v1.mp4"),                       transition_after="плавный"),
    Scene("05", ["sentence_005_v6.mp3"],   _shots("scene_06_v1.mp4", "scene_07_v1.mp4"),    transition_after="плавный"),
    Scene("06", ["sentence_006_v7.mp3"],   _shots("scene_08_v1.mp4"),                       transition_after="плавный"),
    Scene("07", ["sentence_007_v7.mp3"],   _shots("scene_09_v1.mp4"),                       transition_after="плавный"),
    Scene("08", ["sentence_008_v8.mp3"],   _shots("scene_10_v1.mp4", "scene_11_v1.mp4"),    transition_after="плавный"),
    Scene("09", ["sentence_009_v2.mp3"],   _shots("scene_12_v1.mp4"),                       transition_after="плавный"),
    Scene("10", ["sentence_010_v9.mp3"],   _shots("scene_13_v1.mp4", "scene_14_v1.mp4"),    transition_after="плавный"),
    Scene("11", ["sentence_011_v4.mp3"],   _shots("scene_15_v1.mp4", "scene_16_v1.mp4"),    transition_after="плавный"),
    Scene("12", ["sentence_012_v1.mp3"],   _shots("scene_17_v1.mp4", "scene_18_v1.mp4"),    transition_after="плавный"),
    Scene("13", ["sentence_013_v1.mp3"],   _shots("scene_19_v1.mp4"),                       transition_after="плавный", trailing_pad=0.3),
    Scene("14", ["sentence_014_v7.mp3"],   _shots("scene_20_v1.mp4", "scene_21_v1.mp4"),    transition_after="плавный", trailing_pad=0.3),
    Scene("15", ["sentence_015_v8.mp3"],   _shots("scene_22_v1.mp4"),                       transition_after="плавный"),
    Scene("16", ["sentence_016_v8.mp3"],   _shots("scene_23_v1.mp4"),                       trailing_pad=2.0),
]

# Заполняем поле text из SCENE_TEXTS
for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
