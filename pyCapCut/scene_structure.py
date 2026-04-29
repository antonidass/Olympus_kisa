"""
Структура сцен мифа «Сизифов труд».

Один источник правды для pyCapCut-сборки. Все величины в секундах.
"""

from dataclasses import dataclass
from typing import List, Optional


# Одна сцена = одно предложение озвучки.
# Внутри сцены может быть несколько видеошотов для динамики.

@dataclass
class VideoShot:
    file: str                     # имя файла в content/Сизифов Труд/video/
    start_from: float = 0.0       # с какой секунды исходника брать (по умолчанию — с начала)
    muted: bool = True            # заглушить исходную дорожку mp4 (остаётся только озвучка)


@dataclass
class Scene:
    sid: str                                # идентификатор сцены: "01", "04-05" и т.п.
    audios: List[str]                       # один или несколько mp3 на сцену (склеиваются последовательно)
    videos: List[VideoShot]                 # один или несколько шотов, делят время сцены поровну
    text: str = ""                          # субтитры (\n = перенос строки)
    transition_after: Optional[str] = None  # переход к следующей сцене — русское имя из transitions.py
    trailing_pad: float = 0.0               # «тишина» в конце сцены для драматичного послевкусия


# ─────────────────────────────────────────────────────────────────────
# Субтитры — только текст, без ударений (ударения живут в mp3).
# Ключи совпадают со Scene.sid.
# ─────────────────────────────────────────────────────────────────────

SCENE_TEXTS = {
    "01": "",
    "02": "Сизиф — царь Коринфа,\nглавный хитрец древнего мира.\nЕго фишка — обманывать тех,\nкого обмануть невозможно.",
    "03": "Первая жертва — Зевс.",
    "04-05": "Громовержец увёл нимфу,\nа Сизиф настучал её отцу.\nПросто так?",
    "06": "Нет — за это он выбил для\nКоринфа вечный источник воды.",
    "07": "Зевс в ответ прислал Смерть.",
    "08-09": "Танат явился за душой Сизифа —\nа ушёл в цепях.",
    "10": "Пока Смерть сидела в плену,\nна земле никто не уходил.",
    "11": "Воины вставали после сражений.",
    "12": "Старики не могли уйти.",
    "13": "Полный бардак.",
    "14-15": "Арес разрулил ситуацию —\nосвободил Таната,\nи Сизифа утащили\nв подземный мир.",
    "16": "Но даже в Аиде\nСизиф не растерялся.",
    "17": "Он заранее попросил жену\nне проводить обряд.",
    "18-19": "А потом разыграл\nобиженного мужа\nперед Персефоной:\n«Меня даже не проводили!",
    "20": "Отпусти —\nя только разобраться».",
    "21": "Отпустили.",
    "22": "Назад он, понятное дело,\nне пришёл.",
    "23": "Третий шанс боги\nему не дали.",
    "24": "Наказание — простое и жестокое:\nкатить камень в гору.",
    "25": "У вершины камень падает.",
    "26": "Заново.\nНавсегда.",
    "27": "Смерть можно обхитрить.\nВечность — нельзя.",
}


def _shots(*files) -> List[VideoShot]:
    """Сахар: строка или (файл, start_from) → List[VideoShot]."""
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


# ─────────────────────────────────────────────────────────────────────
# Сами сцены. Переходы указываем на русском — список поддерживаемых
# имён живёт в transitions.py (RU_TO_CN).
# ─────────────────────────────────────────────────────────────────────

SCENES: List[Scene] = [
    Scene("01",    ["scene_01.mp3"],    _shots("scene_01.mp4"),                                transition_after="тряское увеличение"),
    Scene("02",    ["scene_02.mp3"],    _shots("scene_02_01.mp4", "scene_02_02.mp4"),          transition_after="тряское уменьшение"),
    Scene("03",    ["scene_03.mp3"],    _shots("scene_03.mp4"),                                transition_after="смена ударной волной"),
    Scene("04-05", ["scene_04_05.mp3"], _shots("scene_04.mp4", "scene_05.mp4"),                transition_after="музыкальный плеер"),
    Scene("06",    ["scene_06.mp3"],    _shots(("scene_06.mp4", 1.3)),                         transition_after="плавная метка"),
    Scene("07",    ["scene_07.mp3"],    _shots("scene_07.mp4"),                                transition_after="зернистое размытие"),
    Scene("08-09", ["scene_08_09.mp3"], _shots("scene_08.mp4", "scene_09.mp4"),                transition_after="опрокидывающая деформация"),
    Scene("10",    ["scene_10.mp3"],    _shots(("scene_10.mp4", 2.0)),                         transition_after="ветряная мельница"),
    Scene("11",    ["scene_11.mp3"],    _shots("scene_11.mp4"),                                transition_after="снегопад"),
    Scene("12",    ["scene_12.mp3"],    _shots("scene_12.mp4"),                                transition_after="мозаика"),
    Scene("13",    ["scene_13.mp3"],    _shots("scene_13.mp4"),                                transition_after="мозаика 2"),
    Scene("14-15", ["scene_14_15.mp3"], _shots("scene_14.mp4", "scene_15.mp4"),                transition_after="смена капчи"),
    Scene("16",    ["scene_16.mp3"],    _shots("scene_16.mp4"),                                transition_after="клик по капче"),
    Scene("17",    ["scene_17.mp3"],    _shots("scene_17.mp4"),                                transition_after="высокоскоростное скольжение"),
    Scene("18-19", ["scene_18_19.mp3"], _shots("scene_18.mp4", "scene_19.mp4"),                transition_after="призрачный изгиб"),
    Scene("20",    ["scene_20.mp3"],    _shots("scene_20.mp4"),                                transition_after="осколки кубика рубика"),
    Scene("21",    ["scene_21.mp3"],    _shots("scene_21.mp4"),                                transition_after="магическое сердце", trailing_pad=0.5),
    Scene("22",    ["scene_22.mp3"],    _shots("scene_22.mp4"),                                transition_after="рыбий глаз"),
    Scene("23",    ["scene_23.mp3"],    _shots("scene_23.mp4"),                                transition_after="рыбий глаз 2"),
    Scene("24",    ["scene_24.mp3"],    _shots("scene_24.mp4"),                                transition_after="рыбий глаз 3"),
    Scene("25",    ["scene_25.mp3"],    _shots("scene_25.mp4"),                                transition_after="рыбий глаз снимок"),
    Scene("26",    ["scene_26.mp3"],    _shots("scene_26.mp4"),                                transition_after="рыбий глаз искажение"),
    Scene("27",    ["scene_27.mp3"],    _shots("scene_27.mp4"),                                trailing_pad=3.0),
]

# Наполняем поле text из SCENE_TEXTS по id, чтобы не дублировать текст в SCENES.
for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
