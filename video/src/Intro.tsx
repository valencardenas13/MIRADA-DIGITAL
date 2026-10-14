import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const AZUL_NOCHE = "#0D1B2A";
const ELECTRICO = "#00D4FF";

export const Intro: React.FC<{ titulo: string; bajada: string }> = ({
  titulo,
  bajada,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const escala = spring({ frame, fps, config: { damping: 200 } });
  const opacidadBajada = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const anchoLinea = interpolate(frame, [15, 45], [0, 320], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: AZUL_NOCHE,
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Inter, system-ui, sans-serif",
        padding: 80,
        textAlign: "center",
      }}
    >
      <h1
        style={{
          color: "white",
          fontSize: 120,
          margin: 0,
          transform: `scale(${escala})`,
        }}
      >
        {titulo}
      </h1>
      <div
        style={{
          height: 8,
          width: anchoLinea,
          backgroundColor: ELECTRICO,
          borderRadius: 4,
          margin: "40px 0",
        }}
      />
      <p style={{ color: ELECTRICO, fontSize: 56, opacity: opacidadBajada }}>
        {bajada}
      </p>
    </AbsoluteFill>
  );
};
