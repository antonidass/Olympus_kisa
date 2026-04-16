import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const subtitleOpacity = interpolate(frame, [30, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #1a0533 0%, #0d001a 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${titleScale})`,
          color: "#FFD700",
          fontSize: 72,
          fontWeight: "bold",
          fontFamily: "serif",
          textAlign: "center",
          textShadow: "0 0 30px rgba(255, 215, 0, 0.5)",
        }}
      >
        Кисы Олимпа
      </div>
      <div
        style={{
          opacity: subtitleOpacity,
          color: "#FFFFFF",
          fontSize: 36,
          marginTop: 20,
          fontFamily: "serif",
          textAlign: "center",
        }}
      >
        Миф за минуту
      </div>
    </AbsoluteFill>
  );
};
