const SIGNAL_LABELS = { buy: "Comprar", hold: "Mantener", sell: "Vender" };

function rsiZone(rsi) {
  if (rsi >= 70) return `${rsi.toFixed(1)} — sobrecompra`;
  if (rsi <= 30) return `${rsi.toFixed(1)} — sobreventa`;
  return `${rsi.toFixed(1)} — neutral`;
}

function NetDiagram() {
  return (
    <svg className="net-diagram" viewBox="0 0 300 70" width="100%" height="70">
      <g stroke="#2c3033" strokeWidth="1">
        <line x1="30" y1="15" x2="130" y2="12" />
        <line x1="30" y1="15" x2="130" y2="35" />
        <line x1="30" y1="15" x2="130" y2="58" />
        <line x1="30" y1="35" x2="130" y2="12" />
        <line x1="30" y1="35" x2="130" y2="35" />
        <line x1="30" y1="35" x2="130" y2="58" />
        <line x1="30" y1="55" x2="130" y2="12" />
        <line x1="30" y1="55" x2="130" y2="35" />
        <line x1="30" y1="55" x2="130" y2="58" />
        <line x1="130" y1="12" x2="230" y2="35" />
        <line x1="130" y1="35" x2="230" y2="35" />
        <line x1="130" y1="58" x2="230" y2="35" />
      </g>
      <g fill="#0e1012" stroke="#454850" strokeWidth="1">
        <circle cx="30" cy="15" r="5" />
        <circle cx="30" cy="35" r="5" />
        <circle cx="30" cy="55" r="5" />
        <circle cx="130" cy="12" r="5" />
        <circle cx="130" cy="35" r="5" />
        <circle cx="130" cy="58" r="5" />
      </g>
      <circle cx="230" cy="35" r="7" fill="#0e1012" stroke="#f0a628" strokeWidth="1.5" />
      <circle cx="230" cy="35" r="12" fill="none" stroke="#f0a62844" strokeWidth="1" />
    </svg>
  );
}

export default function PredictionPanel({ prediction }) {
  const data = prediction.data;
  const filled = data ? Math.round((data.confidence / 100) * 20) : 0;
  const smaBullish = data && data.indicators.sma_short >= data.indicators.sma_long;

  return (
    <div className="card">
      <div className="panel-title">
        <h2>Sugerencia del modelo</h2>
        <span className="ai-tag">IA</span>
      </div>

      <NetDiagram />

      {prediction.loading && <div className="panel-state">Calculando señal…</div>}
      {prediction.error && (
        <div className="panel-state error">{prediction.error}</div>
      )}

      {data && (
        <>
          <div className="signal-badge">
            <div>
              <div className="signal-label">{SIGNAL_LABELS[data.signal]}</div>
              <div className="signal-sub">Señal generada por el modelo</div>
            </div>
            <div className="signal-glyph">&#8942;</div>
          </div>

          <div className="confidence-block">
            <div className="confidence-head">
              <span className="label">Nivel de confianza</span>
              <span className="value">{data.confidence}%</span>
            </div>
            <div className="chunks">
              {Array.from({ length: 20 }, (_, i) => (
                <div key={i} className={i < filled ? "chunk filled" : "chunk"} />
              ))}
            </div>
          </div>

          <div className="divider-ascii">
            {"· ".repeat(60).trim()}
          </div>

          <div className="indicators">
            <div className="indicator-row">
              <span className="k">SMA 20 / 50</span>
              <span className={smaBullish ? "v up" : "v down"}>
                {smaBullish ? "Cruce alcista" : "Cruce bajista"}
              </span>
            </div>
            <div className="indicator-row">
              <span className="k">RSI (14)</span>
              <span className="v">{rsiZone(data.indicators.rsi)}</span>
            </div>
            <div className="indicator-row">
              <span className="k">Último cierre</span>
              <span className="v">${data.indicators.close.toFixed(2)}</span>
            </div>
            <div className="indicator-row">
              <span className="k">Modelo</span>
              <span className="v">Heurístico v0.1</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
