import { useEffect, useRef, useState } from "react";
import { fetchSearch } from "../api.js";

export default function TickerSearch({ ticker, onSelect, autoFocus = false }) {
  const [editing, setEditing] = useState(!ticker);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("idle");
  const [highlight, setHighlight] = useState(-1);
  const boxRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!editing) return undefined;
    const q = query.trim();
    if (!q) {
      setResults([]);
      setStatus("idle");
      setHighlight(-1);
      return undefined;
    }
    let cancelled = false;
    setStatus("loading");
    const id = setTimeout(() => {
      fetchSearch(q)
        .then((items) => {
          if (cancelled) return;
          setResults(items);
          setStatus("done");
          setHighlight(items.length ? 0 : -1);
        })
        .catch(() => {
          if (cancelled) return;
          setResults([]);
          setStatus("error");
        });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(id);
    };
  }, [query, editing]);

  useEffect(() => {
    if (!editing) return undefined;
    inputRef.current?.focus();
    const onOutside = (event) => {
      if (boxRef.current && !boxRef.current.contains(event.target)) {
        close();
      }
    };
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [editing]);

  const close = () => {
    setQuery("");
    setResults([]);
    setStatus("idle");
    setHighlight(-1);
    if (ticker) setEditing(false);
  };

  const select = (item) => {
    onSelect(item.ticker);
    setEditing(false);
    setQuery("");
    setResults([]);
    setStatus("idle");
    setHighlight(-1);
  };

  const onKeyDown = (event) => {
    if (event.key === "Escape") {
      close();
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlight((h) => (results.length ? (h + 1) % results.length : -1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlight((h) =>
        results.length ? (h - 1 + results.length) % results.length : -1
      );
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (highlight >= 0 && results[highlight]) {
        select(results[highlight]);
      } else if (query.trim()) {
        select({ ticker: query.trim().toUpperCase() });
      }
    }
  };

  if (!editing) {
    return (
      <button className="ticker-active" onClick={() => setEditing(true)}>
        <span className="sym">{ticker}</span>
        <span className="hint">cambiar ▾</span>
      </button>
    );
  }

  return (
    <div className="ticker-search" ref={boxRef}>
      <input
        ref={inputRef}
        className="ticker-input"
        type="text"
        value={query}
        placeholder="Buscar ticker (ej. AAPL, MSFT, KO)..."
        autoFocus={autoFocus}
        spellCheck={false}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={onKeyDown}
      />
      {status !== "idle" && (
        <div className="search-dropdown">
          {status === "loading" && (
            <div className="search-state">Buscando…</div>
          )}
          {status === "error" && (
            <div className="search-state error">Error al buscar</div>
          )}
          {status === "done" && results.length === 0 && (
            <div className="search-state">Sin resultados</div>
          )}
          {status === "done" &&
            results.map((item, i) => (
              <button
                key={`${item.ticker}-${item.exchange}`}
                className={i === highlight ? "search-item active" : "search-item"}
                onMouseEnter={() => setHighlight(i)}
                onClick={() => select(item)}
              >
                <span className="sym">{item.ticker}</span>
                <span className="name">{item.name ?? "—"}</span>
                <span className="exch">{item.exchange ?? ""}</span>
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
