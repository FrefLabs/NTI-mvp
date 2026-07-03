import { fetchNews } from "../api.js";
import useApiData from "../hooks/useApiData.js";
import { formatNewsDate } from "../format.js";

export default function TickerNews({ ticker }) {
  const news = useApiData(() => fetchNews(ticker), [ticker]);

  return (
    <div className="card">
      <div className="panel-title">
        <h2>Noticias — {ticker}</h2>
      </div>
      {news.loading && <div className="panel-state">Cargando noticias…</div>}
      {news.error && <div className="panel-state error">{news.error}</div>}
      {news.data && news.data.length === 0 && (
        <div className="panel-state">Sin noticias recientes</div>
      )}
      {news.data && news.data.length > 0 && (
        <div className="news-list">
          {news.data.map((item, i) => (
            <article key={item.url ?? i} className="news-item">
              {item.url ? (
                <a
                  className="news-title"
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {item.title} ↗
                </a>
              ) : (
                <span className="news-title">{item.title}</span>
              )}
              {item.description && (
                <p className="news-desc">{item.description}</p>
              )}
              <div className="news-meta">
                <span>{item.publisher ?? "—"}</span>
                <span>{formatNewsDate(item.published_at)}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
