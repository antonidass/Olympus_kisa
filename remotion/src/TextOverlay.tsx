import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/Rubik";

const { fontFamily } = loadFont("normal", {
  weights: ["700"],
  subsets: ["cyrillic"],
});

const WORD_FADE_FRAMES = 4;

// ─── Имена собственные (подсвечиваются красным в субтитрах сцен) ───
// Ловим любые падежные формы по корню слова.

const PROPER_NOUN_REGEX = /^(Дедал|Икар|Минос|Минотавр|Лабиринт|Крит|Икарийск)/;

// ─── Стили текста ───

const textShadow = [
  "0 2px 8px rgba(0,0,0,0.9)",
  "0 0 20px rgba(0,0,0,0.7)",
  "0 0 4px rgba(0,0,0,1)",
].join(", ");

const baseStyle: React.CSSProperties = {
  fontFamily,
  fontWeight: 700,
  color: "#fff",
  textShadow,
  textAlign: "center",
  lineHeight: 1.25,
  WebkitTextStroke: "1px rgba(0,0,0,0.3)",
};

// ─── Word-by-word reveal ───
// startFrame — смещение (относительное) для отложенного появления.
// singleLine — запрещает перенос слов на новую строку.

const WordReveal: React.FC<{
  text: string;
  durationInFrames: number;
  fontSize: number;
  color?: string;
  stroke?: string;
  startFrame?: number;
  singleLine?: boolean;
  revealFraction?: number;
  highlightRegex?: RegExp;
  highlightColor?: string;
}> = ({ text, durationInFrames, fontSize, color, stroke, startFrame = 0, singleLine = false, revealFraction = 0.8, highlightRegex, highlightColor }) => {
  const frame = useCurrentFrame() - startFrame;
  const lines = text.split("\n");
  const allWords: { word: string; lineIdx: number }[] = [];
  lines.forEach((line, lineIdx) => {
    line.split(/\s+/).filter(Boolean).forEach((word) => {
      allWords.push({ word, lineIdx });
    });
  });

  const wordCount = allWords.length;
  if (wordCount === 0) return null;

  const revealWindow = durationInFrames * revealFraction;
  const interval = wordCount > 1 ? revealWindow / (wordCount - 1) : 0;

  const lineGroups: { word: string; opacity: number; highlight: boolean }[][] = lines.map(() => []);
  allWords.forEach((item, i) => {
    const appearAt = i * interval;
    const opacity = interpolate(
      frame,
      [appearAt, appearAt + WORD_FADE_FRAMES],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );
    const highlight = !!(highlightRegex && highlightRegex.test(item.word));
    lineGroups[item.lineIdx].push({ word: item.word, opacity, highlight });
  });

  return (
    <>
      {lineGroups.map((words, lineIdx) => (
        <div
          key={lineIdx}
          style={{
            display: "flex",
            flexWrap: singleLine ? "nowrap" : "wrap",
            whiteSpace: singleLine ? "nowrap" : "normal",
            justifyContent: "center",
            gap: "0 0.3em",
          }}
        >
          {words.map((w, wIdx) => {
            const wordColor = w.highlight && highlightColor ? highlightColor : color;
            return (
              <span
                key={wIdx}
                style={{
                  ...baseStyle,
                  fontSize,
                  opacity: w.opacity,
                  ...(wordColor ? { color: wordColor } : {}),
                  ...(stroke ? { WebkitTextStroke: stroke } : {}),
                }}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      ))}
    </>
  );
};

// ─── Intro (по центру экрана, крупный текст, word-by-word) ───
// Сначала полностью появляется заголовок, затем — субтитр.

export const IntroTextOverlay: React.FC<{
  title: string;
  subtitle: string;
  durationInFrames: number;
}> = ({ title, subtitle, durationInFrames }) => {
  const titleDur = Math.floor(durationInFrames * 0.5);
  const subtitleDur = durationInFrames - titleDur;
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <WordReveal text={title} durationInFrames={titleDur} fontSize={120} revealFraction={0.35} />
      </div>
      <WordReveal
        text={subtitle}
        durationInFrames={subtitleDur}
        fontSize={120}
        color="#f20000"
        stroke="1px rgba(0,0,0,0.4)"
        startFrame={titleDur}
        revealFraction={0.35}
      />
    </AbsoluteFill>
  );
};

// ─── Финальный эффект «Конец» (круговое затемнение / iris-out) ───
// Радиальная виньетка мягко сжимается к центру кадра, затем всё уходит в чёрное.
// Компонент предполагается помещённым в Sequence длительностью durationInFrames.

export const EndingIris: React.FC<{
  durationInFrames: number;
  cx?: number;
  cy?: number;
}> = ({ durationInFrames, cx = 50, cy = 50 }) => {
  const frame = useCurrentFrame();

  // Радиус «прозрачной дырки» в процентах от диагонали кадра.
  // 130% на старте (ничего не закрыто) → 0% к концу основной анимации (всё чёрное).
  const mainPhase = durationInFrames * 0.9;
  const radius = interpolate(frame, [0, mainPhase], [130, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Мягкий край (feather): внутренняя граница на (radius - FEATHER), внешняя на radius.
  const FEATHER = 18;
  const innerStop = Math.max(0, radius - FEATHER);
  const outerStop = Math.max(0.01, radius);

  // Страховочный сплошной чёрный в самом конце — чтобы точка уходила в полный black.
  const blackOpacity = interpolate(
    frame,
    [durationInFrames * 0.85, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <>
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(circle farthest-corner at ${cx}% ${cy}%, rgba(0,0,0,0) ${innerStop}%, rgba(0,0,0,1) ${outerStop}%)`,
          pointerEvents: "none",
        }}
      />
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: blackOpacity,
          pointerEvents: "none",
        }}
      />
    </>
  );
};

// ─── Субтитры для обычных сцен (верхняя часть экрана, word-by-word) ───
// Каждая строка (разделитель \n в SCENE_TEXTS) показывается последовательно
// в одну строку: старый чанк исчезает, появляется новый.

export const SceneTextOverlay: React.FC<{
  text: string;
  durationInFrames: number;
}> = ({ text, durationInFrames }) => {
  const chunks = text
    .split("\n")
    .map((c) => c.trim())
    .filter(Boolean);
  if (chunks.length === 0) return null;

  const totalWords = chunks.reduce(
    (sum, c) => sum + c.split(/\s+/).filter(Boolean).length,
    0,
  );

  let cursor = 0;
  const schedule = chunks.map((chunk, i) => {
    const words = chunk.split(/\s+/).filter(Boolean).length;
    const isLast = i === chunks.length - 1;
    const dur = isLast
      ? Math.max(1, durationInFrames - cursor)
      : Math.max(1, Math.round((words / totalWords) * durationInFrames));
    const from = cursor;
    cursor += dur;
    return { chunk, from, dur };
  });

  return (
    <>
      {schedule.map((s, i) => (
        <Sequence key={i} from={s.from} durationInFrames={s.dur}>
          <AbsoluteFill
            style={{
              justifyContent: "flex-start",
              alignItems: "center",
              paddingTop: 140,
              pointerEvents: "none",
            }}
          >
            <div style={{ maxWidth: "95%" }}>
              <WordReveal
                text={s.chunk}
                durationInFrames={s.dur}
                fontSize={50}
                singleLine
                highlightRegex={PROPER_NOUN_REGEX}
                highlightColor="#f20000"
              />
            </div>
          </AbsoluteFill>
        </Sequence>
      ))}
    </>
  );
};
