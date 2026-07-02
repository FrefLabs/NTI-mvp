const BASE = "/api";

async function getJson(path) {
  const response = await fetch(`${BASE}${path}`);
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

export const fetchQuote = (ticker) => getJson(`/tickers/${ticker}/quote`);
export const fetchChart = (ticker, range) =>
  getJson(`/tickers/${ticker}/chart?range=${range}`);
export const fetchPrediction = (ticker) =>
  getJson(`/tickers/${ticker}/prediction`);
