import { useEffect, useState } from "react";

function formatClock(date) {
  return (
    date.toLocaleTimeString("es-AR", {
      hour12: false,
      timeZone: "America/Argentina/Buenos_Aires",
    }) + " ART"
  );
}

export default function TopBar({ live }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="topbar">
      <div className="brand">
        <div className="brand-mark">
          NTI<span className="dim">.mvp</span>
        </div>
        <div className="brand-sub">Neuronal Trading Intelligence</div>
      </div>
      <div className="status-cluster">
        <span className="pill">R2 · Análisis de activos</span>
        <div className="status-live">
          <span className={live ? "status-dot" : "status-dot offline"}></span>
          {live ? "Live" : "Offline"}
        </div>
        <div className="clock">{formatClock(now)}</div>
      </div>
    </div>
  );
}
