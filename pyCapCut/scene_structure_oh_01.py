"""
Структура сцен части 01 «Хаос» сериала «От Хаоса до Олимпа».

Один источник правды для pyCapCut-сборки. 19 предложений озвучки
ложатся на 17 видеошотов. Сцены 001 и 016 объединяют по два соседних
TTS-предложения на один видеокадр — это совпадает с маппингом в
prompts/video.md (Сцена 01 = хук+титул на оке Хаоса, Сцена 15 =
циклопы+гекатонхейры на одном кадре).

Маппинг sentence ↔ scene_NN (источник: prompts/video.md):
  sent_001 + sent_002 → scene_01_v1.mp4   (хук «До начала времени был только Хаос» + титул «От Хаоса до Олимпа. Часть 1»)
  sent_003           → scene_02_v1.mp4   (Гея пробуждается)
  sent_004           → scene_03_v1.mp4   (Гея — твёрдая опора)
  sent_005           → scene_04_v1.mp4   (Тартар)
  sent_006           → scene_05_v1.mp4   (Эрос)
  sent_007           → scene_06_v1.mp4   (контр-кадр: разрозненные объекты без Эроса)
  sent_008           → scene_07_v1.mp4   (Эреб + Никта)
  sent_009           → scene_08_v1.mp4   («Брат и сестра»)
  sent_010           → scene_09_v1.mp4   (Эфир + Гемера)
  sent_011           → scene_10_v1.mp4   (общий план: мир пуст)
  sent_012           → scene_11_v1.mp4   (Гея одинока)
  sent_013           → scene_12_v1.mp4   (Гея решилась)
  sent_014           → scene_13_v1.mp4   (Уран рождается)
  sent_015           → scene_14_v1.mp4   (12 титанов, молодой Кронос)
  sent_016 + sent_017 → scene_15_v1.mp4   (циклопы + гекатонхейры — два коротких предложения на одном кадре)
  sent_018           → scene_16_v1.mp4   (клиффхэнгер: Уран запирает / Кронос точит серп)
  sent_019           → scene_17_v1.mp4   (CTA «Подпишись»)

Имена approved-mp3 указаны буквально по содержимому
`voiceover/audio/approved_sentences/` на момент создания. Если webapp
изменит approved (другая selection-версия), правь это здесь и пересобирай.
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


# Тексты для шаблона subtitles. karaoke_oh_01.py их перетрёт пословным
# караоке + интро-карточкой; здесь только опорные строки для проверки
# таймингов в CapCut.
SCENE_TEXTS = {
    "001": "От Хаоса до Олимпа\nЧасть 1",          # титул караоке поверх ока Хаоса
    "003": "Родилась Гея —\nЗемля.",
    "004": "Твёрдая опора\nвсему, что будет.",
    "005": "Тартар —\nтёмная бездна.",
    "006": "Эрос —\nсила влечения.",
    "007": "Иначе мир —\nроссыпь вещей.",
    "008": "Эреб — Мрак,\nНикта — Ночь.",
    "009": "Брат и сестра.",
    "010": "Эфир — небесный свет,\nГемера — День.",
    "011": "Но мир был\nпуст и тих.",
    "012": "Земле было\nодиноко.",
    "013": "Гея решила:\nрожу мужа сама.",
    "014": "Из плоти Земли\nподнялось Небо — Уран.",
    "015": "Двенадцать титанов.\nСреди них — Кронос.",
    "016": "Три циклопа-кузнеца.\nТрое сторуких гекатонхейров.",
    "018": "Уран не дал детям\nвыйти на свет.\nНо один уже точит серп.",
    "019": "Подпишись —\nне пропусти ч. 2.",
}


def _shots(*files) -> List[VideoShot]:
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


# 17 сцен: 15 «одиночных» + 2 «совмещённых» (001 = хук+титул, 016 = циклопы+гекатонхейры).
# Финальная сцена 019 (CTA) держит trailing_pad=1.5 — под эффект «Финальный круг» в enrich.
SCENES: List[Scene] = [
    Scene("001", ["sentence_001_v8.mp3", "sentence_002_v1.mp3"],  _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_003_v6.mp3"],                          _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_004_v6.mp3"],                          _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_005_v1.mp3"],                          _shots("scene_04_v2.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_006_v5.mp3"],                          _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_007_v1.mp3"],                          _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_008_v13.mp3"],                         _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_009_v10.mp3"],                         _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_010_v10.mp3"],                         _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_011_v12.mp3"],                         _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_012_v2.mp3"],                          _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_013_v1.mp3"],                          _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_014_v10.mp3"],                         _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_015_v1.mp3"],                          _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_016_v10.mp3", "sentence_017_v4.mp3"], _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_018_v5.mp3"],                          _shots("scene_16_v1.mp4"), transition_after="плавный"),
    Scene("019", ["sentence_019_v1.mp3"],                          _shots("scene_17_v1.mp4"), trailing_pad=1.5),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
