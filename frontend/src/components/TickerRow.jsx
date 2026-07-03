import { exportCsvUrl } from "../api.js";
import TickerSearch from "./TickerSearch.jsx";

const TIMEFRAMES = [
  { key: "1d", label: "1D" },
  { key: "1mo", label: "1M" },
  { key: "6mo", label: "6M" },
  { key: "1y", label: "1Y" },
  { key: "5y", label: "5Y" },
];

export default function TickerRow({
  ticker,
  onTicker,
  range,
  onRange,
  comparing,
  onToggleCompare,
}) {
  const downloadCsv = () => {
    const link = document.createElement("a");
    link.href = exportCsvUrl(ticker, range);
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="ticker-row">
      <div className="ticker-controls">
        <TickerSearch ticker={ticker} onSelect={onTicker} />
        <button
          className={comparing ? "action-btn active" : "action-btn"}
          onClick={onToggleCompare}
        >
          {comparing ? "× Comparación" : "+ Comparar"}
        </button>
        <button className="action-btn" onClick={downloadCsv}>
          ↓ Exportar CSV
        </button>
      </div>
      <div className="timeframes">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf.key}
            className={tf.key === range ? "tf active" : "tf"}
            onClick={() => onRange(tf.key)}
          >
            {tf.label}
          </button>
        ))}
      </div>
    </div>
  );
}
