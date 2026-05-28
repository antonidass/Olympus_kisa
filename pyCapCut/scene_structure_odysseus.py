"""
Структура сцен мифа «Одиссей и Пенелопа».

Один источник правды для pyCapCut-сборки. 25 предложений озвучки разложены
на 24 видеошота. Сцена 001 объединяет хук (sent_001) и интро-титул
(sent_002) на ОДНОМ визуале scene_01_v1.mp4 — двухстрочный титул «Одиссей
и Пенелопа / Миф за минуту» накладывается караоке-скриптом поверх второго
аудио (см. feedback_intro_single_unit и prompts/video.md). Дальше один к
одному: sent_NNN → scene_(NN-1)_v1.mp4.

Маппинг sentence ↔ scene_NN (источник: prompts/video.md):
  sent_001 + sent_002 → scene_01   (1 шот) хук + накапливающийся титул
  sent_003 → scene_02   (1 шот) Одиссей уходит на войну
  sent_004 → scene_03   (1 шот) война закончилась, он не вернулся
  sent_005 → scene_04   (1 шот) прошло 10/15/20 лет
  sent_006 → scene_05   (1 шот) 108 женихов
  sent_007 → scene_06   (1 шот) пируют, требуют выбора
  sent_008 → scene_07   (1 шот) Пенелопа не отказывает прямо
  sent_009 → scene_08   (1 шот) обещание соткать саван
  sent_010 → scene_09   (1 шот) днём ткёт полотно
  sent_011 → scene_10   (1 шот) ночью при свече распускает
  sent_012 → scene_11   (1 шот) три года обмана
  sent_013 → scene_12   (1 шот) служанка выдаёт тайну
  sent_014 → scene_13   (1 шот) Одиссей плывёт к Итаке
  sent_015 → scene_14   (1 шот) переоделся нищим
  sent_016 → scene_15   (1 шот) никто не узнал
  sent_017 → scene_16   (1 шот) состязание: 12 колец
  sent_018 → scene_17   (1 шот) старый лук Одиссея
  sent_019 → scene_18   (1 шот) 108 женихов отступают
  sent_020 → scene_19   (1 шот) нищий натягивает лук
  sent_021 → scene_20   (1 шот) стрела сквозь 12 колец
  sent_022 → scene_21   (1 шот) Пенелопа узнала, но проверяет
  sent_023 → scene_22   (1 шот) «вынесите кровать»
  sent_024 → scene_23   (1 шот) кровать из живой оливы
  sent_025 → scene_24   (1 шот) финал — объятие
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


# Placeholder тексты для драфта — реальные караоке-слова рендерит karaoke_odysseus.py.
SCENE_TEXTS = {
    "001": "",  # хук + интро-карточка (Одиссей и Пенелопа\nМиф за минуту) рендерится отдельно
    "002": "Одиссей ушёл на войну,\nоставив дома жену и сына.",
    "003": "Война закончилась,\nно он так и не вернулся.",
    "004": "Десять, пятнадцать,\nдвадцать лет.",
    "005": "В дом Пенелопы пришли\nсто восемь женихов.",
    "006": "Пили его вино —\nтребовали нового мужа.",
    "007": "Пенелопа\nне отказывала прямо.",
    "008": "Выберу, когда доткну\nсаван для свёкра.",
    "009": "Днём ткала\nтонкое полотно.",
    "010": "Ночью при свече\nраспускала всё.",
    "011": "Три года\nобмана.",
    "012": "Пока служанка\nне выдала тайну.",
    "013": "Одиссей уже плыл\nк родному берегу.",
    "014": "Сошёл на Итаку\nнищим стариком.",
    "015": "Никто не узнал —\nдаже жена.",
    "016": "Чей выстрел пройдёт\nчерез двенадцать колец.",
    "017": "Лук был старый —\nсамого Одиссея.",
    "018": "Сто восемь раз\nотступали.",
    "019": "Нищий поднял лук\nи натянул его легко.",
    "020": "Стрела прошла\nсквозь двенадцать колец.",
    "021": "Узнала мужа —\nно не бросилась.",
    "022": "«Вынесите его кровать\nво двор».",
    "023": "Нашу кровать нельзя сдвинуть —\nона из живой оливы.",
    "024": "Двадцать лет ожидания —\nв одном объятии.",
}


def _shots(*files) -> List[VideoShot]:
    out: List[VideoShot] = []
    for f in files:
        if isinstance(f, tuple):
            out.append(VideoShot(file=f[0], start_from=f[1]))
        else:
            out.append(VideoShot(file=f))
    return out


# Все переходы — placeholder «плавный». Реальный план переходов с эталонными
# effect_id (Зум с тряской, Резкий зум, Глитч-вспышка и т.д.) живёт в
# enrich_odysseus.py — он клонирует их из живого драфта Мидаса.
SCENES: List[Scene] = [
    Scene("001", ["sentence_001_v10.mp3", "sentence_002_v1.mp3"], _shots("scene_01_v1.mp4"), transition_after="плавный"),
    Scene("002", ["sentence_003_v1.mp3"],  _shots("scene_02_v1.mp4"),  transition_after="плавный"),
    Scene("003", ["sentence_004_v6.mp3"],  _shots("scene_03_v1.mp4"),  transition_after="плавный"),
    Scene("004", ["sentence_005_v5.mp3"],  _shots("scene_04_v1.mp4"),  transition_after="плавный"),
    Scene("005", ["sentence_006_v10.mp3"], _shots("scene_05_v1.mp4"),  transition_after="плавный"),
    Scene("006", ["sentence_007_v10.mp3"], _shots("scene_06_v1.mp4"),  transition_after="плавный"),
    Scene("007", ["sentence_008_v1.mp3"],  _shots("scene_07_v1.mp4"),  transition_after="плавный"),
    Scene("008", ["sentence_009_v10.mp3"], _shots("scene_08_v1.mp4"),  transition_after="плавный"),
    Scene("009", ["sentence_010_v3.mp3"],  _shots("scene_09_v1.mp4"),  transition_after="плавный"),
    Scene("010", ["sentence_011_v2.mp3"],  _shots("scene_10_v1.mp4"),  transition_after="плавный"),
    Scene("011", ["sentence_012_v10.mp3"], _shots("scene_11_v1.mp4"),  transition_after="плавный"),
    Scene("012", ["sentence_013_v5.mp3"],  _shots("scene_12_v1.mp4"),  transition_after="плавный"),
    Scene("013", ["sentence_014_v2.mp3"],  _shots("scene_13_v1.mp4"),  transition_after="плавный"),
    Scene("014", ["sentence_015_v10.mp3"], _shots("scene_14_v1.mp4"),  transition_after="плавный"),
    Scene("015", ["sentence_016_v9.mp3"],  _shots("scene_15_v1.mp4"),  transition_after="плавный"),
    Scene("016", ["sentence_017_v5.mp3"],  _shots("scene_16_v1.mp4"),  transition_after="плавный"),
    Scene("017", ["sentence_018_v10.mp3"], _shots("scene_17_v1.mp4"),  transition_after="плавный"),
    Scene("018", ["sentence_019_v3.mp3"],  _shots("scene_18_v1.mp4"),  transition_after="плавный"),
    Scene("019", ["sentence_020_v9.mp3"],  _shots("scene_19_v1.mp4"),  transition_after="плавный"),
    Scene("020", ["sentence_021_v1.mp3"],  _shots("scene_20_v1.mp4"),  transition_after="плавный"),
    Scene("021", ["sentence_022_v1.mp3"],  _shots("scene_21_v1.mp4"),  transition_after="плавный"),
    Scene("022", ["sentence_023_v1.mp3"],  _shots("scene_22_v1.mp4"),  transition_after="плавный"),
    Scene("023", ["sentence_024_v7.mp3"],  _shots("scene_23_v1.mp4"),  transition_after="плавный", trailing_pad=0.2),
    Scene("024", ["sentence_025_v2.mp3"],  _shots("scene_24_v1.mp4"),  trailing_pad=1.0),
]

for _s in SCENES:
    _s.text = SCENE_TEXTS.get(_s.sid, "")
