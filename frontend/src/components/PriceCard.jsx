import PriceChart from "./PriceChart.jsx";

function formatVolume(volume) {
  if (volume == null) return "—";
  if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`;
  if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`;
  if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`;
  return String(volume);
}

const money = (value) => (value == null ? "—" : `$${value.toFixed(2)}`);

export default function PriceCard({ ticker, quote, chart }) {
  const data = quote.data;
  const [units, cents] = data
    ? data.price.toFixed(2).split(".")
    : ["—", "--"];
  const up = data ? data.change >= 0 : true;

  return (
    <div className="card">
      <p className="card-label">Precio actual — {ticker}</p>
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
          <div className="v">{formatVolume(data?.volume)}</div>
        </div>
        <div className="meta-item">
          <div className="k">Cierre ant.</div>
          <div className="v">{money(data?.previous_close)}</div>
        </div>
      </div>
    </div>
  );
}
