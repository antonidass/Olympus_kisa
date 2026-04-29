"""
Структура сцен мифа «Арахна».

Один источник правды для pyCapCut-сборки. 16 предложений озвучки,
разложенные на 21 видеошот (4 предложения покрывают по 2-3 шота —
см. images.md / video.md).

Маппинг sentence ↔ scene_NN:
  sent_001 → scene_01                       (1 шот)  титульный standoff
  sent_002 → scene_02 + scene_03            (2 шота) мастерская + нимфы у гобелена
  sent_003 → scene_04                       (1 шот)  портрет Арахны у станка
  sent_004 → scene_05                       (1 шот)  дерзкая фраза перед толпой
  sent_005 → scene_06                       (1 шот)  Олимп, Афина слышит
  sent_006 → scene_07                       (1 шот)  старуха-Афина с предупреждением
  sent_007 → scene_08                       (1 шот)  Арахна смеётся
  sent_008 → scene_09 + scene_10            (2 шота) сброс маски + два станка готовы
  sent_009 → scene_11                       (1 шот)  две ткачихи параллельно
  sent_010 → scene_12                       (1 шот)  гобелен Афины — торжество богов
  sent_011 → scene_13 + scene_14            (2 шота) Арахна за работой + её гобелен
  sent_012 → scene_15                       (1 шот)  Афина в ужасе видит идеал
  sent_013 → scene_16                       (1 шот)  гнев богини, рука поднимается
  sent_014 → scene_17 + scene_18 + scene_19 (3 шота) касание + появление паучка + плетение в углу
  sent_015 → scene_20                       (1 шот)  широкий план паутины на рассвете
  sent_016 → scene_21                       (1 шот)  макро паутины, в капле росы — силуэт ткачихи
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
# Субтитры. Сцена "01" — интро, её текст крупный шрифт через спецкейс
# в build_arahna. Остальные — обычные субтитры внизу кадра. Все они
# на финальной сборке скрываются karaoke_arahna.py — там вместо них
# идёт пословное караоке. Здесь нужны лишь как плейсхолдер на случай
# отдельной сборки без караоке.
# ─────────────────────────────────────────────────────────────────────

SCENE_TEXTS = {
    "01": "",  # интро ("Арахна\nМиф за минуту") рендерится отдельно в build_arahna
    "02": "В Лидии жила ткачиха,\nчьи гобелены завораживали даже нимф.",
    "03": "Арахна умела всё.\nИ знала это.",
    "04": "«Сама Афина не соткёт лучше меня», —\nбросила она однажды.",
    "05": "Дерзость дошла до Олимпа.",
    "06": "Богиня спустилась в облике старухи:\n«Возьми слова обратно».",
    "07": "Арахна лишь рассмеялась.",
    "08": "Тогда Афина сбросила маску.\nВызов принят.",
    "09": "Два станка. Две ткачихи.",
    "10": "Афина соткала торжество богов —\nсияющее золотом и величием.",
    "11": "Арахна — гобелен о тёмных делах олимпийцев:\nих обманах, ссорах, насмешках над смертными.",
    "12": "И, к ужасу Афины,\nработа Арахны была безупречна.",
    "13": "Богиня не вынесла правды.",
    "14": "Одним касанием она превратила соперницу\nв крошечное существо, что будет ткать вечно.",
    "15": "Так появились пауки.",
    "16": "И каждый раз, видя паутину, помни:\nкогда-то её соткала ткачиха,\nчто осмелилась спорить с богиней.",
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
# из content/Арахна/video/.
#
# Переходы — базовый «плавный» (заменяется на конкретные effect_id
# в enrich_arahna.py, который тянет шаблоны из живого Мидас-драфта).
#
# trailing_pad на драматических паузах:
#   - sid="13" (богиня не вынесла правды) — короткая пауза перед магией
#   - sid="16" (финал, мораль) — большой хвост на затухание музыки
# ─────────────────────────────────────────────────────────────────────

SCENES: List[Scene] = [
    Scene("01", ["sentence_001_v10.mp3"], _shots("scene_01_v1.mp4"),                                          transition_after="плавный"),
    Scene("02", ["sentence_002_v1.mp3"],  _shots("scene_02_v1.mp4", "scene_03_v1.mp4"),                       transition_after="плавный"),
    Scene("03", ["sentence_003_v1.mp3"],  _shots("scene_04_v1.mp4"),                                          transition_after="плавный"),
    Scene("04", ["sentence_004_v6.mp3"],  _shots("scene_05_v1.mp4"),                                          transition_after="плавный"),
    Scene("05", ["sentence_005_v1.mp3"],  _shots("scene_06_v1.mp4"),                                          transition_after="плавный"),
    Scene("06", ["sentence_006_v10.mp3"], _shots("scene_07_v1.mp4"),                                          transition_after="плавный"),
    Scene("07", ["sentence_007_v9.mp3"],  _shots("scene_08_v1.mp4"),                                          transition_after="плавный"),
    Scene("08", ["sentence_008_v10.mp3"], _shots("scene_09_v1.mp4", "scene_10_v1.mp4"),                       transition_after="плавный"),
    Scene("09", ["sentence_009_v2.mp3"],  _shots("scene_11_v1.mp4"),                                          transition_after="плавный"),
    Scene("10", ["sentence_010_v5.mp3"],  _shots("scene_12_v1.mp4"),                                          transition_after="плавный"),
    Scene("11", ["sentence_011_v8.mp3"],  _shots("scene_13_v1.mp4", "scene_14_v1.mp4"),                       transition_after="плавный"),
    Scene("12", ["sentence_012_v3.mp3"],  _shots("scene_15_v1.mp4"),                                          transition_after="плавный"),
    Scene("13", ["sentence_013_v2.mp3"],  _shots("scene_16_v1.mp4"),                                          transition_after="плавный", trailing_pad=0.3),
    Scene("14", ["sentence_014_v6.mp3"],  _shots("scene_17_v1.mp4", "scene_18_v1.mp4", "scene_19_v1.mp4"),    transition_after="плавный"),
    Scene("15", ["sentence_015_v1.mp3"],  _shots("scene_20_v1.mp4"),                                          transition_after="плавный"),
    Scene("16", ["sentence_016_v4.mp3"],  _shots("scene_21_v1.mp4"),                                          trailing_pad=2.0),
]

# Заполняем поле text из SCENE_TEXTS
for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
