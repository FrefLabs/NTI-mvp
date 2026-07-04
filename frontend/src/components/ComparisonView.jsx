import { fetchChart, fetchFundamentals, fetchQuote } from "../api.js";
import useApiData from "../hooks/useApiData.js";
import PriceCard from "./PriceCard.jsx";
import FundamentalsSection from "./FundamentalsSection.jsx";
import TickerSearch from "./TickerSearch.jsx";

function ComparisonCard({ ticker, range, onClose }) {
  const quote = useApiData(() => fetchQuote(ticker), [ticker]);
  const chart = useApiData(() => fetchChart(ticker, range), [ticker, range]);
  const fundamentals = useApiData(() => fetchFundamentals(ticker), [ticker]);

  return (
    <>
      <PriceCard
        ticker={ticker}
        quote={quote}
        chart={chart}
        fundamentals={fundamentals}
        onClose={onClose}
      />
      <FundamentalsSection ticker={ticker} fundamentals={fundamentals} />
    </>
  );
}

export default function ComparisonView({ ticker, range, onSelect, onClose }) {
  if (!ticker) {
    return (
      <div className="card compare-empty">
        <div className="card-head">
          <p className="card-label">Comparar con…</p>
          <button className="close-btn" onClick={onClose} title="Cerrar comparación">
            ×
          </button>
        </div>
        <TickerSearch ticker={null} onSelect={onSelect} autoFocus />
      </div>
    );
  }

  return <ComparisonCard ticker={ticker} range={range} onClose={onClose} />;
}
