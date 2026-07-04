import { useState } from "react";
import { formatBig, money, percent, ratio } from "../format.js";

const SIGNAL_LABELS = { buy: "Comprar", hold: "Mantener", sell: "Vender" };

function rsiZone(rsi) {
  if (rsi >= 70) return `${rsi.toFixed(1)} — sobrecompra`;
  if (rsi <= 30) return `${rsi.toFixed(1)} — sobreventa`;
  return `${rsi.toFixed(1)} — neutral`;
}

function Row({ k, children }) {
  return (
    <div className="indicator-row">
      <span className="k">{k}</span>
      <span className="v">{children}</span>
    </div>
  );
}

export default function PredictionPanel({ prediction, fundamentals }) {
  const [expanded, setExpanded] = useState(false);
  const data = prediction.data;
  const funda = fundamentals?.data;
  const smaBullish = data && data.indicators.sma_short >= data.indicators.sma_long;

  return (
    <div className="card">
      <div className="panel-title">
        <h2>Sugerencia del modelo</h2>
        <span className="ai-tag">IA</span>
      </div>

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
            <div className="confidence-track">
              <div
                className="confidence-fill"
                style={{ width: `${data.confidence}%` }}
              />
            </div>
            <div className="confidence-marks">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>

          <div className="divider-ascii">{"· ".repeat(60).trim()}</div>

          <div className="indicators">
            <div className="indicator-row">
              <span className="k">SMA 20 / 50</span>
              <span className={smaBullish ? "v up" : "v down"}>
                {smaBullish ? "Cruce alcista" : "Cruce bajista"}
              </span>
            </div>
            <Row k="RSI (14)">{rsiZone(data.indicators.rsi)}</Row>
            <Row k="Último cierre">${data.indicators.close.toFixed(2)}</Row>
            <Row k="Modelo">Heurístico v0.1</Row>
          </div>
        </>
      )}

      <div className="divider-ascii">{"· ".repeat(60).trim()}</div>

      <div className="panel-subtitle">Fundamentals</div>
      {fundamentals?.loading && (
        <div className="panel-state">Cargando fundamentals…</div>
      )}
      {fundamentals?.error && (
        <div className="panel-state error">{fundamentals.error}</div>
      )}
      {funda && (
        <>
          <div className="indicators">
            <Row k="Sector">{funda.sector ?? "—"}</Row>
            <Row k="Industria">{funda.industry ?? "—"}</Row>
            <Row k="Market Cap">{formatBig(funda.market_cap, "$")}</Row>
            <Row k="P/E (trailing)">{ratio(funda.trailing_pe)}</Row>
            {expanded && (
              <>
                <Row k="P/E (forward)">{ratio(funda.forward_pe)}</Row>
                <Row k="Dividend yield">{percent(funda.dividend_yield)}</Row>
                <Row k="Beta">{ratio(funda.beta)}</Row>
                <Row k="Rango 52 sem.">
                  {funda.fifty_two_week_low != null &&
                  funda.fifty_two_week_high != null
                    ? `${money(funda.fifty_two_week_low)} – ${money(funda.fifty_two_week_high)}`
                    : "—"}
                </Row>
                <Row k="Vol. promedio">{formatBig(funda.average_volume)}</Row>
              </>
            )}
          </div>
          <button className="see-more" onClick={() => setExpanded((v) => !v)}>
            {expanded ? "Ver menos ▴" : "Ver más ▾"}
          </button>
        </>
      )}
    </div>
  );
}
