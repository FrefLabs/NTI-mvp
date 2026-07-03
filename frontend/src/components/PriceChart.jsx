import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  createChart,
  CrosshairMode,
  LineStyle,
} from "lightweight-charts";

const UP = "#34d399";
const DOWN = "#f2495c";

function toSeriesData(points) {
  const seen = new Set();
  const data = [];
  for (const p of points) {
    if (p.open == null || p.high == null || p.low == null || p.close == null) {
      continue;
    }
    const time = Math.floor(new Date(p.time).getTime() / 1000);
    if (seen.has(time)) continue;
    seen.add(time);
    data.push({ time, open: p.open, high: p.high, low: p.low, close: p.close });
  }
  return data.sort((a, b) => a.time - b.time);
}

function formatTooltipTime(unixSeconds, intraday) {
  const date = new Date(unixSeconds * 1000);
  if (intraday) {
    return date.toLocaleString("es-AR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return date.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function PriceChart({ chart }) {
  const containerRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  const points = chart.data?.points;
  const range = chart.data?.range;
  const intraday = range === "1d" || range === "5d";

  useEffect(() => {
    if (!containerRef.current || !points) return undefined;
    const data = toSeriesData(points);
    if (data.length < 2) return undefined;

    const chartApi = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { color: "transparent" },
        textColor: "#6c7075",
        fontFamily:
          'ui-monospace, "JetBrains Mono", "SF Mono", Consolas, monospace',
        fontSize: 10,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "#1b1e21" },
        horzLines: { color: "#1b1e21" },
      },
      crosshair: {
        mode: CrosshairMode.Magnet,
        vertLine: {
          color: "#454850",
          style: LineStyle.Dashed,
          labelBackgroundColor: "#1b1e21",
        },
        horzLine: {
          color: "#454850",
          style: LineStyle.Dashed,
          labelBackgroundColor: "#1b1e21",
        },
      },
      rightPriceScale: { borderColor: "#232629" },
      timeScale: {
        borderColor: "#232629",
        timeVisible: intraday,
        secondsVisible: false,
      },
      localization: { locale: "es-AR" },
    });

    const series = chartApi.addSeries(CandlestickSeries, {
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
      priceLineVisible: true,
      lastValueVisible: true,
    });
    series.setData(data);
    chartApi.timeScale().fitContent();

    chartApi.subscribeCrosshairMove((param) => {
      const bar = param.time != null ? param.seriesData.get(series) : null;
      setTooltip(bar ? { time: param.time, ...bar } : null);
    });

    return () => {
      setTooltip(null);
      chartApi.remove();
    };
  }, [points, intraday]);

  if (chart.loading) return <div className="chart-state">Cargando datos…</div>;
  if (chart.error) return <div className="chart-state error">{chart.error}</div>;
  if (!points || toSeriesData(points).length < 2) {
    return <div className="chart-state">Sin datos suficientes</div>;
  }

  return (
    <div className="chart-wrap">
      <div className="lw-chart" ref={containerRef} />
      {tooltip && (
        <div className="chart-tooltip">
          <span className="t">{formatTooltipTime(tooltip.time, intraday)}</span>
          <span>A ${tooltip.open.toFixed(2)}</span>
          <span>M ${tooltip.high.toFixed(2)}</span>
          <span>m ${tooltip.low.toFixed(2)}</span>
          <span className={tooltip.close >= tooltip.open ? "up" : "down"}>
            C ${tooltip.close.toFixed(2)}
          </span>
        </div>
      )}
    </div>
  );
}
