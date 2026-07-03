import PriceChart from "./PriceChart.jsx";
import { formatBig, money, ratio } from "../format.js";

export default function PriceCard({ ticker, quote, chart, fundamentals, onClose }) {
  const data = quote.data;
  const funda = fundamentals?.data;
  const [units, cents] = data ? data.price.toFixed(2).split(".") : ["—", "--"];
  const up = data ? data.change >= 0 : true;

  const fromLow =
    data && funda?.fifty_two_week_low
      ? ((data.price - funda.fifty_two_week_low) / funda.fifty_two_week_low) * 100
      : null;
  const relVolume =
    data?.volume && funda?.average_volume
      ? data.volume / funda.average_volume
      : null;

  return (
    <div className="card">
      <div className="card-head">
        <p className="card-label">Precio actual — {ticker}</p>
        {onClose && (
          <button className="close-btn" onClick={onClose} title="Cerrar comparación">
            ×
          </button>
        )}
      </div>
      {quote.error ? (
        <div className="chart-state error">{quote.error}</div>
      ) : (
        <div className="price-block">
          <div className="price-figure">
            ${units}
            <span className="cents">.{cents}</span>
          </div>
          {data && (
            <div className={up ? "change-badge" : "change-badge down"}>
              {up ? "↗" : "↘"} {up ? "+" : ""}
              {data.change_percent.toFixed(2)}%
            </div>
          )}
        </div>
      )}

      <PriceChart chart={chart} />

      <div className="meta-row">
        <div className="meta-item">
          <div className="k">Máximo día</div>
          <div className="v">{money(data?.day_high)}</div>
        </div>
        <div className="meta-item">
          <div className="k">Mínimo día</div>
          <div className="v">{money(data?.day_low)}</div>
        </div>
        <div className="meta-item">
          <div className="k">Volumen</div>
          <div className="v">{formatBig(data?.volume)}</div>
        </div>
        <div className="meta-item">
          <div className="k">Cierre ant.</div>
          <div className="v">{money(data?.previous_close)}</div>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi">
          <div className="k">Market Cap</div>
          <div className="v">{formatBig(funda?.market_cap, "$")}</div>
        </div>
        <div className="kpi">
          <div className="k">Beta</div>
          <div className="v">{ratio(funda?.beta)}</div>
        </div>
        <div className="kpi">
          <div className="k">P/E (trailing)</div>
          <div className="v">{ratio(funda?.trailing_pe)}</div>
        </div>
        <div className="kpi">
          <div className="k">Rango 52 sem.</div>
          <div className="v">
            {funda?.fifty_two_week_low != null && funda?.fifty_two_week_high != null
              ? `${money(funda.fifty_two_week_low)} – ${money(funda.fifty_two_week_high)}`
              : "—"}
          </div>
        </div>
        <div className="kpi">
          <div className="k">Desde mín. 52s</div>
          <div className={fromLow != null && fromLow >= 0 ? "v up" : "v down"}>
            {fromLow != null ? `${fromLow >= 0 ? "+" : ""}${fromLow.toFixed(1)}%` : "—"}
          </div>
        </div>
        <div className="kpi">
          <div className="k">Vol. relativo</div>
          <div className="v">{relVolume != null ? `${relVolume.toFixed(2)}×` : "—"}</div>
        </div>
      </div>
    </div>
  );
}
