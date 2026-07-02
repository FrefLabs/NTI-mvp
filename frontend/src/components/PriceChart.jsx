import { useMemo, useState } from "react";

const WIDTH = 640;
const HEIGHT = 220;
const PAD_TOP = 16;
const PAD_BOTTOM = 16;

function formatTime(iso, range) {
  const date = new Date(iso);
  if (range === "1d") {
    return date.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
    year: range === "5y" || range === "1y" ? "2-digit" : undefined,
  });
}

export default function PriceChart({ chart }) {
  const [hover, setHover] = useState(null);

  const geometry = useMemo(() => {
    if (!chart.data) return null;
    const points = chart.data.points.filter((p) => p.close != null);
    if (points.length < 2) return null;

    const closes = points.map((p) => p.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const span = max - min || 1;
    const usable = HEIGHT - PAD_TOP - PAD_BOTTOM;

    const coords = points.map((p, i) => ({
      x: (i / (points.length - 1)) * WIDTH,
      y: PAD_TOP + (1 - (p.close - min) / span) * usable,
      point: p,
    }));
    const up = closes[closes.length - 1] >= closes[0];
    const line = coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" L");
    return {
      coords,
      up,
      linePath: `M${line}`,
      areaPath: `M0,${HEIGHT} L${line} L${WIDTH},${HEIGHT} Z`,
      last: coords[coords.length - 1],
    };
  }, [chart.data]);

  if (chart.loading) return <div className="chart-state">Cargando datos…</div>;
  if (chart.error) return <div className="chart-state error">{chart.error}</div>;
  if (!geometry) return <div className="chart-state">Sin datos suficientes</div>;

  const color = geometry.up ? "var(--up-500)" : "var(--down-500)";
  const gradientId = geometry.up ? "fillUp" : "fillDown";
  const range = chart.data.range;

  const onMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * WIDTH;
    const index = Math.round((x / WIDTH) * (geometry.coords.length - 1));
    setHover(geometry.coords[Math.max(0, Math.min(index, geometry.coords.length - 1))]);
  };

  const axisLabels = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const point = chart.data.points[Math.round(f * (chart.data.points.length - 1))];
    return formatTime(point.time, range);
  });

  return (
    <div className="chart-wrap">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id="fillUp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#34d399" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="fillDown" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f2495c" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#f2495c" stopOpacity="0" />
          </linearGradient>
        </defs>
        <g stroke="#1e2124" strokeWidth="1">
          <line x1="0" y1="36" x2={WIDTH} y2="36" />
          <line x1="0" y1="92" x2={WIDTH} y2="92" />
          <line x1="0" y1="148" x2={WIDTH} y2="148" />
          <line x1="0" y1="204" x2={WIDTH} y2="204" />
        </g>
        <path d={geometry.areaPath} fill={`url(#${gradientId})`} />
        <path d={geometry.linePath} fill="none" stroke={color} strokeWidth="2" />
        {hover ? (
          <g>
            <line
              x1={hover.x}
              y1="0"
              x2={hover.x}
              y2={HEIGHT}
              stroke="#454850"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
            <circle cx={hover.x} cy={hover.y} r="4" fill={color} />
          </g>
        ) : (
          <g>
            <circle cx={geometry.last.x} cy={geometry.last.y} r="4" fill={color} />
            <circle
              cx={geometry.last.x}
              cy={geometry.last.y}
              r="8"
              fill={color}
              opacity="0.2"
            />
          </g>
        )}
      </svg>
      {hover && (
        <div className="chart-tooltip">
          {formatTime(hover.point.time, range)} · ${hover.point.close.toFixed(2)}
        </div>
      )}
      <div className="chart-axis-labels">
        {axisLabels.map((label, i) => (
          <span key={i}>{label}</span>
        ))}
      </div>
    </div>
  );
}
