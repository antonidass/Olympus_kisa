import {
  AbsoluteFill,
  Audio as MusicAudio,
  Sequence,
  staticFile,
  CalculateMetadataFunction,
  interpolate,
} from "remotion";
import { OffthreadVideo } from "remotion";
import { Audio } from "@remotion/media";
import { TransitionSeries, linearTiming, TransitionPresentation } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";
import { lightLeak, zoomIn, zoomOut } from "./transitions";
import { IntroTextOverlay, SceneTextOverlay } from "./TextOverlay";

// ─── Константы ───

const FPS = 30;
const TRANSITION_FRAMES = 8; // 0.27 сек длительность перехода между сценами
const GAP_FRAMES = 2; // ~66 мс пауза в озвучке между соседними аудио-чанками
const MUSIC_FILE = "Dorian_Concept_-_Hide_CS01_Version_(SkySound.cc).mp3";
const MUSIC_PLAYBACK_RATE = 0.9;
const MUSIC_VOLUME = 0.2;
const WHOOSH_FILE = "WHOOSH.mp3";
const WHOOSH_DURATION_FRAMES = 20; // ~0.67 сек — достаточно для воспроизведения whoosh-звука

// ─── Видео-клип с тримом ───
// Позволяет выбрать конкретный отрезок исходного видео.
// Если указан только startFrom — видео играет с этой точки на всю длину сцены.
// endAt хранится как метаданные выбранного фрагмента.

interface VideoClip {
  file: string;
  /** Начало фрагмента исходного видео (секунды) */
  startFrom?: number;
  /** Конец фрагмента исходного видео (секунды) */
  endAt?: number;
}

type VideoEntry = string | VideoClip;

function normalizeVideo(v: VideoEntry): VideoClip {
  return typeof v === "string" ? { file: v } : v;
}

// ─── Структура сцен ───
// Каждая сцена: 1+ аудио и 1+ видео.
// Длительность сцены = сумма длительностей её аудио.
// Видео внутри сцены делят это время поровну.
// transitionAfter — тип перехода к следующей сцене (slideLeft/slideRight
// ставятся на границах абзацев сценария, остальные — внутри абзацев).
// scene_00_intro намеренно исключён — оставлен для превью.

type TransitionKind =
  | "fade"
  | "lightLeak"
  | "slideLeft"
  | "slideRight"
  | "zoomIn"
  | "zoomOut";

interface SceneSpec {
  id: string;
  audios: string[];
  videos: VideoEntry[];
  transitionAfter?: TransitionKind;
}

// ─── Тексты субтитров (без ударений — они только для озвучки) ───

const SCENE_TEXTS: Record<string, string> = {
  intro: "", // обрабатывается отдельно через IntroTextOverlay
  "01": "Дедал — гениальный изобретатель.",
  "02": "Он построил Лабиринт\nдля царя Миноса на Крите,",
  "03": "чтобы запереть внутри\nчудовище — Минотавра.",
  "04": "Лабиринт получился\nнастолько хорош,\nчто выбраться из него\nбыло невозможно.",
  "05": "Но Минос не оценил.",
  "06": "Вместо награды он запер\nсамого Дедала и его сына\nИкара на острове.",
  "07": "Уплыть нельзя —\nкорабли под контролем царя.\nУбежать по суше некуда —\nкругом море.",
  "08": "Тогда Дедал придумал\nбезумный план.",
  "09": "Он собрал птичьи перья,\nскрепил их воском",
  "10": "и смастерил\nдве пары крыльев.",
  "11": "Перед полётом отец\nпредупредил Икара:",
  "12": "«Не поднимайся\nслишком высоко —\nсолнце растопит воск.",
  "13": "И не спускайся\nслишком низко —\nморе намочит перья.\nЛети за мной».",
  "14": "Они взлетели. Свобода!",
  "15": "Ветер в лицо,\nКрит остаётся позади.",
  "16": "Но Икар забыл обо всём.",
  "17": "Восторг полёта ударил\nв голову, и он рванул\nвверх — к самому солнцу.",
  "18": "Воск начал таять.\nПерья посыпались одно за другим.\nИкар забил руками\nпо воздуху,\nно крыльев больше не было.\nОн упал в море.",
  "19": "Дедал обернулся —\nа сына уже нет.",
  "20": "Море, в котором погиб Икар,\nназвали Икарийским.",
  "21": "А история стала вечным\nнапоминанием:\nсвобода без головы — это падение.",
};

const SCENE_STRUCTURE: SceneSpec[] = [
  { id: "intro", audios: ["intro.mp3"], videos: ["intro.mp4"], transitionAfter: "slideLeft" },
  { id: "01", audios: ["scene_01.mp3"], videos: ["scene_01_v1.mp4"] },
  { id: "02", audios: ["scene_02.mp3"], videos: ["scene_02_01_v1.mp4", "scene_02_02_v1.mp4"], transitionAfter: "zoomOut" },
  { id: "03", audios: ["scene_03.mp3"], videos: ["scene_03_01_v1.mp4", "scene_03_02_v1.mp4"], transitionAfter: "zoomOut" },
  { id: "04", audios: ["scene_04.mp3"], videos: ["scene_04_v1.mp4"], transitionAfter: "slideRight" },
  { id: "05", audios: ["scene_05.mp3"], videos: [{ file: "scene_05_v1.mp4", startFrom: 1, endAt: 2.5 }], transitionAfter: "zoomIn" },
  { id: "06", audios: ["scene_06.mp3"], videos: ["scene_06_v1.mp4"] },
  { id: "07", audios: ["scene_07.mp3"], videos: ["scene_07_v1.mp4"], transitionAfter: "slideLeft" },
  { id: "08", audios: ["scene_08.mp3"], videos: ["scene_08_01_v1.mp4", "scene_08_02_v1.mp4"] },
  { id: "09", audios: ["scene_09.mp3"], videos: ["scene_09_01_v1.mp4", "scene_09_02_v1.mp4", "scene_09_03_v1.mp4"], transitionAfter: "lightLeak" },
  { id: "10", audios: ["scene_10.mp3"], videos: ["scene_10_v1.mp4"], transitionAfter: "slideLeft" },
  { id: "11", audios: ["scene_11.mp3"], videos: ["scene_11_v1.mp4"] },
  { id: "12", audios: ["scene_12.mp3"], videos: ["scene_12_v1.mp4"] },
  { id: "13", audios: ["scene_13.mp3"], videos: ["scene_13_v1.mp4"], transitionAfter: "slideLeft" },
  { id: "14", audios: ["scene_14.mp3"], videos: ["scene_14_v1.mp4"] },
  { id: "15", audios: ["scene_15.mp3"], videos: ["scene_15_v1.mp4"] },
  { id: "16", audios: ["scene_16.mp3"], videos: ["scene_16_v1.mp4"] },
  { id: "17", audios: ["scene_17.mp3"], videos: ["scene_17_v1.mp4"], transitionAfter: "slideRight" },
  {
    id: "18",
    audios: ["scene_18_01.mp3", "scene_18_02.mp3", "scene_18_03.mp3", "scene_18_04.mp3"],
    videos: ["scene_18_v1.mp4"],
    transitionAfter: "zoomOut",
  },
  { id: "19", audios: ["scene_19.mp3"], videos: ["scene_19_v1.mp4"], transitionAfter: "slideLeft" },
  { id: "20", audios: ["scene_20.mp3"], videos: ["scene_20_v1.mp4"], transitionAfter: "lightLeak" },
  { id: "21", audios: ["scene_21.mp3"], videos: ["scene_21_v1.mp4"] },
];

// ─── Вспомогательные функции ───

async function getAudioDuration(src: string): Promise<number> {
  const input = new Input({
    formats: ALL_FORMATS,
    source: new UrlSource(src, { getRetryDelay: () => null }),
  });
  return await input.computeDuration();
}

// ─── Props и calculateMetadata ───

interface ResolvedScene {
  id: string;
  audios: string[];
  videos: VideoClip[];
  audioFrames: number[];
  sceneTotalFrames: number;
  transitionAfter: TransitionKind;
  text: string;
}

type IcarusProps = {
  scenes: ResolvedScene[];
  [key: string]: unknown;
};

export const calculateIcarusMetadata: CalculateMetadataFunction<IcarusProps> = async () => {
  const resolved: ResolvedScene[] = [];
  let totalCursor = 0;

  for (let i = 0; i < SCENE_STRUCTURE.length; i++) {
    const spec = SCENE_STRUCTURE[i];

    const durationsSec = await Promise.all(
      spec.audios.map((a) => getAudioDuration(staticFile(`audio/${a}`)))
    );
    const audioFrames = durationsSec.map((d) => Math.ceil(d * FPS));
    const isLast = i === SCENE_STRUCTURE.length - 1;

    // Видео сцены растягивается, чтобы включить gap-паузы:
    // internalGaps — между аудио одной сцены, outboundGap — перед следующей сценой.
    const sumAudios = audioFrames.reduce((a, b) => a + b, 0);
    const internalGaps = (audioFrames.length - 1) * GAP_FRAMES;
    const outboundGap = isLast ? 0 : GAP_FRAMES;
    const sceneTotalFrames = sumAudios + internalGaps + outboundGap;

    resolved.push({
      id: spec.id,
      audios: spec.audios,
      videos: spec.videos.map(normalizeVideo),
      audioFrames,
      sceneTotalFrames,
      transitionAfter: spec.transitionAfter ?? "fade",
      text: SCENE_TEXTS[spec.id] ?? "",
    });

    totalCursor += sceneTotalFrames - (isLast ? 0 : TRANSITION_FRAMES);
  }

  return {
    durationInFrames: totalCursor,
    props: { scenes: resolved },
  };
};

// ─── Главная композиция ───

export const IcarusVideo: React.FC<IcarusProps> = ({ scenes }) => {
  type VideoSegment = {
    key: string;
    sceneId: string;
    clip: VideoClip;
    durationInFrames: number;
    transitionAfter: TransitionKind | null; // null = нет перехода после сегмента
  };

  // Плоский список видео-сегментов с распределением длительности внутри сцены
  const videoSegments: VideoSegment[] = [];
  scenes.forEach((scene, sIdx) => {
    const isLastScene = sIdx === scenes.length - 1;
    const videoCount = scene.videos.length;
    const baseFrames = Math.floor(scene.sceneTotalFrames / videoCount);
    const remainder = scene.sceneTotalFrames - baseFrames * videoCount;

    scene.videos.forEach((clip, vIdx) => {
      const isLastInScene = vIdx === videoCount - 1;
      const dur = isLastInScene ? baseFrames + remainder : baseFrames;
      videoSegments.push({
        key: `v-${scene.id}-${vIdx}`,
        sceneId: scene.id,
        clip,
        durationInFrames: dur,
        transitionAfter: isLastInScene && !isLastScene ? scene.transitionAfter : null,
      });
    });
  });

  // Вычисляем абсолютные позиции сцен (для текста и WHOOSH)
  const scenePositions: { id: string; from: number; duration: number; text: string }[] = [];
  let sceneCursor = 0;
  scenes.forEach((scene, sIdx) => {
    const isLast = sIdx === scenes.length - 1;
    scenePositions.push({
      id: scene.id,
      from: sceneCursor,
      duration: scene.sceneTotalFrames,
      text: scene.text,
    });
    sceneCursor += scene.sceneTotalFrames - (isLast ? 0 : TRANSITION_FRAMES);
  });

  // Вычисляем абсолютные позиции WHOOSH-звуков для slide-переходов
  let cursor = 0;
  const whooshPositions: number[] = [];
  videoSegments.forEach((seg) => {
    const segEnd = cursor + seg.durationInFrames;
    if (seg.transitionAfter === "slideLeft" || seg.transitionAfter === "slideRight") {
      whooshPositions.push(segEnd - TRANSITION_FRAMES);
    }
    cursor = segEnd - (seg.transitionAfter ? TRANSITION_FRAMES : 0);
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* ── Видео-дорожка ── */}
      <TransitionSeries>
        {videoSegments.flatMap((seg) => {
          const startFromFrames = seg.clip.startFrom != null
            ? Math.round(seg.clip.startFrom * FPS)
            : undefined;

          const nodes = [
            <TransitionSeries.Sequence
              key={seg.key}
              durationInFrames={seg.durationInFrames}
            >
              <AbsoluteFill>
                <OffthreadVideo
                  src={staticFile(`scenes/${seg.clip.file}`)}
                  startFrom={startFromFrames}
                  style={{ width: "100%", height: "105%", objectFit: "cover", objectPosition: "center 40%" }}
                  volume={0.5}
                />
              </AbsoluteFill>
            </TransitionSeries.Sequence>,
          ];
          if (seg.transitionAfter) {
            const presentation = (() => {
              switch (seg.transitionAfter) {
                case "lightLeak":
                  return lightLeak();
                case "slideLeft":
                  return slide({ direction: "from-right" });
                case "slideRight":
                  return slide({ direction: "from-left" });
                case "zoomIn":
                  return zoomIn();
                case "zoomOut":
                  return zoomOut();
                case "fade":
                default:
                  return fade();
              }
            })() as TransitionPresentation<Record<string, unknown>>;
            nodes.push(
              <TransitionSeries.Transition
                key={`t-${seg.sceneId}`}
                presentation={presentation}
                timing={linearTiming({ durationInFrames: TRANSITION_FRAMES })}
              />
            );
          }
          return nodes;
        })}
      </TransitionSeries>

      {/* ── Аудио + текст (абсолютные Sequence, привязаны к scenePositions) ── */}
      {scenePositions.map((sp) => {
        const scene = scenes.find((s) => s.id === sp.id)!;
        return (
          <Sequence key={`at-${sp.id}`} from={sp.from} durationInFrames={sp.duration}>
            {/* Аудио-чанки */}
            {(() => {
              let localCursor = 0;
              return scene.audios.map((file, aIdx) => {
                const from = localCursor;
                const dur = scene.audioFrames[aIdx];
                localCursor += dur + GAP_FRAMES;
                return (
                  <Sequence key={`aud-${sp.id}-${aIdx}`} from={from} durationInFrames={dur}>
                    <Audio src={staticFile(`audio/${file}`)} />
                  </Sequence>
                );
              });
            })()}
            {/* Текст */}
            {sp.id === "intro" ? (
              <IntroTextOverlay title="Икар и Дедал" subtitle="Миф за минуту" durationInFrames={sp.duration} />
            ) : scene.text ? (
              <SceneTextOverlay text={scene.text} durationInFrames={sp.duration} />
            ) : null}
          </Sequence>
        );
      })}

      {/* ── Звуки переходов (WHOOSH на slide-переходах между абзацами) ── */}
      {whooshPositions.map((frame, i) => (
        <Sequence key={`whoosh-${i}`} from={frame} durationInFrames={WHOOSH_DURATION_FRAMES}>
          <Audio src={staticFile(`audio/${WHOOSH_FILE}`)} volume={0.7} />
        </Sequence>
      ))}

      {/* ── Фоновая музыка (играет на всю длину, fade-out в последней сцене) ── */}
      <MusicAudio
        src={staticFile(`music/${MUSIC_FILE}`)}
        playbackRate={MUSIC_PLAYBACK_RATE}
        volume={(f) => {
          const lastScene = scenePositions[scenePositions.length - 1];
          const fadeStart = lastScene.from;
          const fadeEnd = lastScene.from + lastScene.duration;
          return interpolate(f, [fadeStart, fadeEnd], [MUSIC_VOLUME, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
        }}
      />
    </AbsoluteFill>
  );
};

// Дефолтные пропсы для Studio (до загрузки calculateMetadata)
export const icarusDefaultProps: IcarusProps = {
  scenes: [],
};
