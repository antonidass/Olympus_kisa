import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/Rubik";

const { fontFamily } = loadFont("normal", {
  weights: ["700"],
  subsets: ["cyrillic"],
});

const WORD_FADE_FRAMES = 4;

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

const WordReveal: React.FC<{
  text: string;
  durationInFrames: number;
  fontSize: number;
  color?: string;
  stroke?: string;
}> = ({ text, durationInFrames, fontSize, color, stroke }) => {
  const frame = useCurrentFrame();
  const lines = text.split("\n");
  const allWords: { word: string; lineIdx: number }[] = [];
  lines.forEach((line, lineIdx) => {
    line.split(/\s+/).filter(Boolean).forEach((word) => {
      allWords.push({ word, lineIdx });
    });
  });

  const wordCount = allWords.length;
  if (wordCount === 0) return null;

  const revealWindow = durationInFrames * 0.8;
  const interval = wordCount > 1 ? revealWindow / (wordCount - 1) : 0;

  const lineGroups: { word: string; opacity: number }[][] = lines.map(() => []);
  allWords.forEach((item, i) => {
    const appearAt = i * interval;
    const opacity = interpolate(
      frame,
      [appearAt, appearAt + WORD_FADE_FRAMES],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );
    lineGroups[item.lineIdx].push({ word: item.word, opacity });
  });

  return (
    <>
      {lineGroups.map((words, lineIdx) => (
        <div key={lineIdx} style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 0.3em" }}>
          {words.map((w, wIdx) => (
            <span
              key={wIdx}
              style={{
                ...baseStyle,
                fontSize,
                opacity: w.opacity,
                ...(color ? { color } : {}),
                ...(stroke ? { WebkitTextStroke: stroke } : {}),
              }}
            >
              {w.word}
            </span>
          ))}
        </div>
      ))}
    </>
  );
};

// ─── Intro (по центру экрана, крупный текст, word-by-word) ───

export const IntroTextOverlay: React.FC<{
  title: string;
  subtitle: string;
  durationInFrames: number;
}> = ({ title, subtitle, durationInFrames }) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <WordReveal text={title} durationInFrames={durationInFrames * 0.5} fontSize={120} />
      </div>
      <WordReveal
        text={subtitle}
        durationInFrames={durationInFrames * 0.5}
        fontSize={120}
        color="#E63946"
        stroke="1px rgba(0,0,0,0.4)"
      />
    </AbsoluteFill>
  );
};

// ─── Субтитры для обычных сцен (верхняя часть экрана, word-by-word) ───

export const SceneTextOverlay: React.FC<{
  text: string;
  durationInFrames: number;
}> = ({ text, durationInFrames }) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-start",
        alignItems: "center",
        paddingTop: 80,
        pointerEvents: "none",
      }}
    >
      <div style={{ maxWidth: "85%" }}>
        <WordReveal text={text} durationInFrames={durationInFrames} fontSize={40} />
      </div>
    </AbsoluteFill>
  );
};
