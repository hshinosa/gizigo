import { useEffect, useState } from "react";

type Health = {
  ok: boolean;
  catalog_hash: string;
  ingredients_count: number;
  db_ok: boolean;
};

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  (typeof window !== "undefined" ? `${window.location.origin}` : "");

export function Footer() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    fetch(`${API_BASE}/v1/health`)
      .then((r) => r.json())
      .then((j: Health) => { if (alive) setHealth(j); })
      .catch(() => { if (alive) setError(true); });
    return () => { alive = false; };
  }, []);

  return (
    <footer className="mt-10 border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-6xl px-5 py-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-600">
        <div>
          <div className="font-semibold text-slate-800 mb-1">Data sources</div>
          <ul className="space-y-1">
            <li>
              Nutrient catalog:{" "}
              <a href="https://www.panganku.org/id-ID/semua_nutrisi" target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
                TKPI 2020 (Kemenkes RI)
              </a>
            </li>
            <li>
              RDA standard:{" "}
              <span className="font-medium">Permenkes 28/2019</span>
            </li>
            <li>
              Solver: <span className="font-medium">PuLP + COIN-OR CBC</span>
            </li>
          </ul>
        </div>
        <div>
          <div className="font-semibold text-slate-800 mb-1">Live status</div>
          <div className="flex items-center gap-2">
            <span
              aria-hidden
              className={
                "inline-block h-2 w-2 rounded-full " +
                (health?.ok ? "bg-emerald-500 animate-pulse" : error ? "bg-rose-500" : "bg-slate-300")
              }
            />
            <span>
              {health?.ok
                ? `${health.ingredients_count.toLocaleString("en-US")} ingredients · catalog ${health.catalog_hash.slice(0, 8)}${health.db_ok ? " · DB ok" : ""}`
                : error
                  ? "Cannot reach API"
                  : "Checking..."}
            </span>
          </div>
          <div className="mt-1 text-slate-500">
            <span>TLS via Let's Encrypt · </span>
            <span>Python 3.10 + FastAPI 0.136</span>
          </div>
        </div>
        <div>
          <div className="font-semibold text-slate-800 mb-1">Project</div>
          <ul className="space-y-1">
            <li>Submitted to ALGOfest Hackathon 2026</li>
            <li>Solo build · MIT License</li>
            <li>
              <a href="/v1/health" className="text-brand-600 hover:underline">
                /v1/health
              </a>
              {" · "}
              <a href="https://github.com/" target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
                Source code
              </a>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
