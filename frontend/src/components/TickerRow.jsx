const TIMEFRAMES = [
  { key: "1d", label: "1D" },
  { key: "1mo", label: "1M" },
  { key: "6mo", label: "6M" },
  { key: "1y", label: "1Y" },
  { key: "5y", label: "5Y" },
];

export default function TickerRow({ tickers, ticker, onTicker, range, onRange }) {
  return (
    <div className="ticker-row">
      <div className="ticker-toggle">
        {tickers.map((t) => (
          <button
            key={t.ticker}
            className={t.ticker === ticker ? "ticker-opt active" : "ticker-opt"}
            onClick={() => onTicker(t.ticker)}
          >
            {t.ticker}
            <span className="name">{t.name}</span>
          </button>
        ))}
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
