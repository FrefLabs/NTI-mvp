import { useCallback, useEffect, useState } from "react";
import { fetchChart, fetchPrediction, fetchQuote } from "./api.js";
import TopBar from "./components/TopBar.jsx";
import TickerRow from "./components/TickerRow.jsx";
import PriceCard from "./components/PriceCard.jsx";
import PredictionPanel from "./components/PredictionPanel.jsx";

const TICKERS = [
  { ticker: "KO", name: "Coca-Cola Co." },
  { ticker: "NVDA", name: "NVIDIA Corp." },
];

const DEFAULT_RANGE = "6mo";

function useApiData(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const load = useCallback(loader, deps);

  useEffect(() => {
    let cancelled = false;
    setState({ data: null, error: null, loading: true });
    load()
      .then((data) => !cancelled && setState({ data, error: null, loading: false }))
      .catch(
        (error) =>
          !cancelled && setState({ data: null, error: error.message, loading: false })
      );
    return () => {
      cancelled = true;
    };
  }, [load]);

  return state;
}

export default function App() {
  const [ticker, setTicker] = useState("KO");
  const [range, setRange] = useState(DEFAULT_RANGE);

  const quote = useApiData(() => fetchQuote(ticker), [ticker]);
  const chart = useApiData(() => fetchChart(ticker, range), [ticker, range]);
  const prediction = useApiData(() => fetchPrediction(ticker), [ticker]);

  const live = !quote.loading && !quote.error;

  return (
    <div className="app">
      <TopBar live={live} />
      <TickerRow
        tickers={TICKERS}
        ticker={ticker}
        onTicker={setTicker}
        range={range}
        onRange={setRange}
      />
      <div className="grid">
        <PriceCard ticker={ticker} quote={quote} chart={chart} />
        <PredictionPanel prediction={prediction} />
      </div>
      <div className="disclaimer">
        <span className="glyph">&#9888;</span>
        <p>
          <strong>
            NTI no ejecuta operaciones ni brinda asesoramiento financiero
            profesional.
          </strong>{" "}
          Las sugerencias mostradas son orientativas, se basan en datos
          históricos y no garantizan resultados futuros. Toda decisión de
          inversión es exclusiva responsabilidad del usuario.
        </p>
      </div>
      <div className="footnote">
        Fuente de datos: Yahoo Finance (yfinance) — KO · NVDA únicamente
      </div>
    </div>
  );
}
