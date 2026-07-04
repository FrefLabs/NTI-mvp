import { useState } from "react";
import { formatBig, money, percent, ratio } from "../format.js";

export default function FundamentalsSection({ ticker, fundamentals }) {
  const [open, setOpen] = useState(true);
  const funda = fundamentals.data;

  return (
    <div className="card">
      <button className="fund-toggle" onClick={() => setOpen((v) => !v)}>
        <span className="panel-subtitle">Datos fundamentales — {ticker}</span>
        <span className="fund-arrow">{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <>
          {fundamentals.loading && (
            <div className="panel-state">Cargando fundamentals…</div>
          )}
          {fundamentals.error && (
            <div className="panel-state error">{fundamentals.error}</div>
          )}
          {funda && (
            <>
              <div className="fund-grid">
                <div className="kpi">
                  <div className="k">Nombre</div>
                  <div className="v">{funda.name ?? "—"}</div>
                </div>
                <div className="kpi">
                  <div className="k">Sector</div>
                  <div className="v">{funda.sector ?? "—"}</div>
                </div>
                <div className="kpi">
                  <div className="k">Industria</div>
                  <div className="v">{funda.industry ?? "—"}</div>
                </div>
                <div className="kpi">
                  <div className="k">Market Cap</div>
                  <div className="v">{formatBig(funda.market_cap, "$")}</div>
                </div>
                <div className="kpi">
                  <div className="k">P/E (trailing)</div>
                  <div className="v">{ratio(funda.trailing_pe)}</div>
                </div>
                <div className="kpi">
                  <div className="k">P/E (forward)</div>
                  <div className="v">{ratio(funda.forward_pe)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Dividend yield</div>
                  <div className="v">{percent(funda.dividend_yield)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Beta</div>
                  <div className="v">{ratio(funda.beta)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Máx. 52 sem.</div>
                  <div className="v">{money(funda.fifty_two_week_high)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Mín. 52 sem.</div>
                  <div className="v">{money(funda.fifty_two_week_low)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Vol. promedio</div>
                  <div className="v">{formatBig(funda.average_volume)}</div>
                </div>
                <div className="kpi">
                  <div className="k">Sitio web</div>
                  <div className="v">
                    {funda.website ? (
                      <a
                        href={funda.website}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {funda.website.replace(/^https?:\/\/(www\.)?/, "")}
                      </a>
                    ) : (
                      "—"
                    )}
                  </div>
                </div>
              </div>
              {funda.long_business_summary && (
                <p className="fund-summary">{funda.long_business_summary}</p>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
