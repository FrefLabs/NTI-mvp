const BASE = "/api";

async function request(path, options) {
  const response = await fetch(`${BASE}${path}`, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return response.json();
}

const getJson = (path) => request(path);

export const fetchQuote = (ticker) => getJson(`/tickers/${ticker}/quote`);
export const fetchChart = (ticker, range) =>
  getJson(`/tickers/${ticker}/chart?range=${range}`);
export const fetchPrediction = (ticker) =>
  getJson(`/tickers/${ticker}/prediction`);
export const fetchSearch = (query) =>
  getJson(`/search?q=${encodeURIComponent(query)}`);
export const fetchNews = (ticker) => getJson(`/tickers/${ticker}/news`);
export const fetchFundamentals = (ticker) =>
  getJson(`/tickers/${ticker}/fundamentals`);
export const exportCsvUrl = (ticker, range) =>
  `${BASE}/tickers/${ticker}/chart/export?range=${encodeURIComponent(range)}`;
export const postBacktest = (ticker, params) =>
  request(`/tickers/${ticker}/backtest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
