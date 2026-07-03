export const money = (value) => (value == null ? "—" : `$${value.toFixed(2)}`);

export const ratio = (value) => (value == null ? "—" : value.toFixed(2));

export const percent = (value) =>
  value == null ? "—" : `${value.toFixed(2)}%`;

export function formatBig(value, prefix = "") {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${prefix}${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${prefix}${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${prefix}${(value / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${prefix}${(value / 1e3).toFixed(1)}K`;
  return `${prefix}${value}`;
}

export function formatNewsDate(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
