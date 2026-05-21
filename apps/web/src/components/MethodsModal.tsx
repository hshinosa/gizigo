import { useEffect, useRef } from "react";
import { X, Calculator, BookOpen, Database, Shield } from "lucide-react";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function MethodsModal({ open, onClose }: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div role="dialog" aria-modal="true" aria-label="Methods and data sources" className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/50 p-4 sm:p-8">
      <div
        ref={dialogRef}
        tabIndex={-1}
        className="relative w-full max-w-2xl rounded-2xl bg-white shadow-2xl outline-none"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-4 right-4 rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6 sm:p-8 space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">How GiziGo works</h2>
            <p className="mt-1 text-sm text-slate-600">
              An Operations-Research-grade meal planner. Every result is the global optimum of a linear program — not a chatbot guess.
            </p>
          </div>

          <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-800 font-semibold mb-2">
                <Calculator className="h-4 w-4 text-brand-600" /> Three plans, one solver
              </div>
              <ul className="text-sm text-slate-600 space-y-1.5">
                <li><span className="font-medium text-slate-700">Cheapest:</span> pure cost LP — minimizes Σ(price·grams) subject to RDA floors and a budget cap.</li>
                <li><span className="font-medium text-slate-700">Most Balanced:</span> cost + 50·Σ(slack) so RDAs are met as evenly as possible.</li>
                <li><span className="font-medium text-slate-700">Most Varied:</span> deterministic iterative substitution on top of Cheapest, capped at +2 food groups.</li>
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-800 font-semibold mb-2">
                <Database className="h-4 w-4 text-brand-600" /> Data sources
              </div>
              <ul className="text-sm text-slate-600 space-y-1.5">
                <li>
                  Nutrient catalog: <a className="text-brand-600 hover:underline" href="https://www.panganku.org/id-ID/semua_nutrisi" target="_blank" rel="noreferrer">TKPI 2020</a> via panganku.org (Kemenkes RI). 1,146 ingredients × 8 tracked nutrients per 100 g.
                </li>
                <li>
                  RDA: <span className="font-medium">Permenkes 28/2019</span>, 7 demographic categories (toddler → lactating mother).
                </li>
                <li>
                  Prices: 40-ingredient retail samples from <a className="text-brand-600 hover:underline" href="https://infopangan.jakarta.go.id" target="_blank" rel="noreferrer">infopangan.jakarta.go.id</a> and <a className="text-brand-600 hover:underline" href="https://www.bi.go.id/hargapangan" target="_blank" rel="noreferrer">PIHPS Bank Indonesia</a>.
                </li>
              </ul>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-800 font-semibold mb-2">
                <BookOpen className="h-4 w-4 text-brand-600" /> Sensitivity and infeasibility
              </div>
              <p className="text-sm text-slate-600">
                The price-perturbation slider triggers a <em>full LP re-solve</em> under the new prices, not a linear extrapolation of dual variables. When the budget can't meet RDA, a budget bisection finds the minimum feasible amount and surfaces the deficit nutrients.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-800 font-semibold mb-2">
                <Shield className="h-4 w-4 text-brand-600" /> Determinism &amp; license
              </div>
              <ul className="text-sm text-slate-600 space-y-1.5">
                <li>CBC: <code>threads=1, randomS=1, presolve=on, cuts=off</code>; <code>PYTHONHASHSEED=0</code>.</li>
                <li>Plan caching is content-addressed by SHA-256 of the canonical request.</li>
                <li>License: MIT. Solver: COIN-OR CBC (EPL).</li>
              </ul>
            </div>
          </section>

          <p className="text-xs text-slate-500">
            Full mathematical formulation:{" "}
            <code className="text-slate-700">docs/ilp-formulation.md</code>{" "}
            in the repository.
          </p>
        </div>
      </div>
    </div>
  );
}
