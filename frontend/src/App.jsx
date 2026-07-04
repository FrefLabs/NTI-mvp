import { useEffect, useRef, useState } from "react";
import {
  fetchChart,
  fetchFundamentals,
  fetchPrediction,
  fetchQuote,
} from "./api.js";
import useApiData from "./hooks/useApiData.js";
import TopBar from "./components/TopBar.jsx";
import TickerRow from "./components/TickerRow.jsx";
import PriceCard from "./components/PriceCard.jsx";
import PredictionPanel from "./components/PredictionPanel.jsx";
import FundamentalsSection from "./components/FundamentalsSection.jsx";
import TickerNews from "./components/TickerNews.jsx";
import ComparisonView from "./components/ComparisonView.jsx";

const DEFAULT_RANGE = "6mo";

export default function App() {
  const [ticker, setTicker] = useState("KO");
  const [range, setRange] = useState(DEFAULT_RANGE);
  const [comparing, setComparing] = useState(false);
  const [compareTicker, setCompareTicker] = useState(null);
  const mainColRef = useRef(null);
  const compareColRef = useRef(null);
  const [mainColHeight, setMainColHeight] = useState(null);
  const [compareColHeight, setCompareColHeight] = useState(null);

  useEffect(() => {
    const el = mainColRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setMainColHeight(entry.contentRect.height);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const el = compareColRef.current;
    if (!el) {
      setCompareColHeight(null);
      return;
    }
    const ro = new ResizeObserver(([entry]) => {
      setCompareColHeight(entry.contentRect.height);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [comparing]);

  const sideColHeight = compareColHeight
    ? Math.max(mainColHeight ?? 0, compareColHeight)
    : mainColHeight;

  const quote = useApiData(() => fetchQuote(ticker), [ticker]);
  const chart = useApiData(() => fetchChart(ticker, range), [ticker, range]);
  const prediction = useApiData(() => fetchPrediction(ticker), [ticker]);
  const fundamentals = useApiData(() => fetchFundamentals(ticker), [ticker]);

  const live = !quote.loading && !quote.error;

  const changeTicker = (next) => {
    setTicker(next);
    setComparing(false);
    setCompareTicker(null);
  };

  const toggleCompare = () => {
    setComparing((v) => !v);
    setCompareTicker(null);
  };

  return (
    <div className="app">
      <TopBar live={live} />
      <TickerRow
        ticker={ticker}
        onTicker={changeTicker}
        range={range}
        onRange={setRange}
        comparing={comparing}
        onToggleCompare={toggleCompare}
      />
      <div className={comparing ? "grid grid-compare" : "grid"}>
        <div className="main-col" ref={mainColRef}>
          <PriceCard
            ticker={ticker}
            quote={quote}
            chart={chart}
            fundamentals={fundamentals}
          />
          <FundamentalsSection ticker={ticker} fundamentals={fundamentals} />
        </div>
        {comparing && (
          <div className="main-col" ref={compareColRef}>
            <ComparisonView
              ticker={compareTicker}
              range={range}
              onSelect={setCompareTicker}
              onClose={toggleCompare}
            />
          </div>
        )}
        <div
          className="side-col"
          style={sideColHeight ? { height: sideColHeight } : undefined}
        >
          <PredictionPanel prediction={prediction} fundamentals={fundamentals} />
          <TickerNews ticker={ticker} />
        </div>
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
        Fuente de datos: Yahoo Finance (yfinance)
      </div>
    </div>
  );
}
