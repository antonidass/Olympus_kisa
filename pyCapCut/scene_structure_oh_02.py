"""
Структура сцен части 02 «Власть Кроноса» сериала «От Хаоса до Олимпа».

Один источник правды для pyCapCut-сборки. 20 предложений озвучки
ложатся на 19 видеошотов. Сцена 001 совмещает хук+титул на одной картинке
(одна сцена с двумя TTS-файлами), остальные предложения sent_003..sent_020
лежат 1:1 на сценах images.md/video.md scene_02..scene_19.

Маппинг sentence ↔ scene_NN (источник: prompts/video.md):
  sent_001 + sent_002 → scene_01_v1.mp4   (хук «Сын сверг отца...» + титул «От Хаоса до Олимпа. Часть 2»)
  sent_003           → scene_02_v1.mp4   (Уран прятал детей в чреве Геи — небо давит вниз)
  sent_004           → scene_03_v1.mp4   (Гея больше не могла терпеть — глаз открывается, золотая слеза)
  sent_005           → scene_04_v1.mp4   (адамантовый серп поднимается из земли)
  sent_006           → scene_05_v1.mp4   (Кронос берёт серп, 11 титанов отступают)
  sent_007           → scene_06_v1.mp4   (свержение — серебряная трещина по куполу неба)
  sent_008           → scene_07_v1.mp4   (Уран поднимается в небо, далёкие звёзды)
  sent_009           → scene_08_v1.mp4   (циклопы и гекатонхейры выходят на свет)
  sent_010           → scene_09_v1.mp4   (Афродита поднимается из пены)
  sent_011           → scene_10_v1.mp4   (Уран плачет с неба, дождь — лейтмотив)
  sent_012           → scene_11_v1.mp4   (Кронос на троне с Реей)
  sent_013           → scene_12_v1.mp4   (Гея говорит сыну через руны на полу)
  sent_014           → scene_13_v1.mp4   (Кронос поглощает пятерых котят-олимпийцев)
  sent_015           → scene_14_v1.mp4   («одного за другим» — Рея, последний котёнок-Посейдон)
  sent_016           → scene_15_v1.mp4   (Рея больше не могла — спиной к трону, лоб в стене)
  sent_017           → scene_16_v1.mp4   (бегство Реи в горы, две далёкие звёзды теплеют)
  sent_018           → scene_17_v1.mp4   (беременная Рея у костра в пещере, золотое свечение живота)
  sent_019           → scene_18_v1.mp4   (клиффхэнгер: силуэт Зевса-эмбриона + молнии-искры)
  sent_020           → scene_19_v1.mp4   (CTA: финал-клиффхэнгер с молнией и юным Зевсом)

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


# Тексты для шаблона subtitles. karaoke_oh_02.py их перетрёт пословным
# караоке + интро-карточкой; здесь только опорные строки для проверки
# таймингов в CapCut.
SCENE_TEXTS = {
    "001": "От Хаоса до Олимпа\nЧасть 2",        # титул караоке поверх силуэта молодого Кроноса
    "003": "Уран прятал детей\nв чреве Геи.",
    "004": "Гея больше\nне могла терпеть.",
    "005": "Из адаманта —\nнеубывающий серп.",
    "006": "Только младший —\nКронос — взял его.",
    "007": "Той ночью\nсверг отца одним ударом.",
    "008": "Уран не погиб —\nнавсегда поднялся в небо.",
    "009": "Дети наконец\nвышли на свет.",
    "010": "Из пены родилась\nАфродита — богиня красоты.",
    "011": "А Уран плачет с неба.\nЕго слёзы — дождь.",
    "012": "Кронос сел на трон\nи взял в жёны Рею.",
    "013": "Тебя свергнет\nтвой собственный ребёнок.",
    "014": "Кронос начал глотать детей —\nГестию, Деметру, Геру, Аида, Посейдона.",
    "015": "Одного за другим.",
    "016": "Рея больше\nне могла смотреть.",
    "017": "Она бежала\nи спряталась в горах.",
    "018": "Этот ребёнок\nбудет особенным.",
    "019": "Его имя —\nЗевс.",
    "020": "Подпишись —\nне пропусти ч. 3.",
}


def _shots(*files) -> List[VideoShot]:
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


# 19 сцен: 18 «одиночных» + 1 «совмещённая» (001 = хук+титул на одном кадре).
# Финальная сцена 020 (CTA-клиффхэнгер) держит trailing_pad=1.5 — хвостовой
# воздух после слов «Зевс вернётся за братьями и сёстрами».
SCENES: List[Scene] = [
    Scene("001", ["sentence_001_v4.mp3", "sentence_002_v1.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("003", ["sentence_003_v2.mp3"],                         _shots("scene_02_v1.mp4"), transition_after="плавный"),
    Scene("004", ["sentence_004_v4.mp3"],                         _shots("scene_03_v1.mp4"), transition_after="плавный"),
    Scene("005", ["sentence_005_v1.mp3"],                         _shots("scene_04_v1.mp4"), transition_after="плавный"),
    Scene("006", ["sentence_006_v1.mp3"],                         _shots("scene_05_v1.mp4"), transition_after="плавный"),
    Scene("007", ["sentence_007_v4.mp3"],                         _shots("scene_06_v1.mp4"), transition_after="плавный"),
    Scene("008", ["sentence_008_v1.mp3"],                         _shots("scene_07_v1.mp4"), transition_after="плавный"),
    Scene("009", ["sentence_009_v5.mp3"],                         _shots("scene_08_v1.mp4"), transition_after="плавный"),
    Scene("010", ["sentence_010_v3.mp3"],                         _shots("scene_09_v1.mp4"), transition_after="плавный"),
    Scene("011", ["sentence_011_v4.mp3"],                         _shots("scene_10_v1.mp4"), transition_after="плавный"),
    Scene("012", ["sentence_012_v1.mp3"],                         _shots("scene_11_v1.mp4"), transition_after="плавный"),
    Scene("013", ["sentence_013_v1.mp3"],                         _shots("scene_12_v1.mp4"), transition_after="плавный"),
    Scene("014", ["sentence_014_v9.mp3"],                         _shots("scene_13_v1.mp4"), transition_after="плавный"),
    Scene("015", ["sentence_015_v4.mp3"],                         _shots("scene_14_v1.mp4"), transition_after="плавный"),
    Scene("016", ["sentence_016_v2.mp3"],                         _shots("scene_15_v1.mp4"), transition_after="плавный"),
    Scene("017", ["sentence_017_v2.mp3"],                         _shots("scene_16_v2.mp4"), transition_after="плавный"),
    Scene("018", ["sentence_018_v5.mp3"],                         _shots("scene_17_v1.mp4"), transition_after="плавный"),
    Scene("019", ["sentence_019_v1.mp3"],                         _shots("scene_18_v1.mp4"), transition_after="плавный"),
    Scene("020", ["sentence_020_v10.mp3"],                        _shots("scene_19_v2.mp4"), trailing_pad=1.5),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
