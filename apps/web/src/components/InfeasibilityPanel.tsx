import { AlertTriangle, ArrowUp } from "lucide-react";
import { COPY } from "../copy/id";
import type { InfeasibilityHint } from "../lib/types";
import { fmtIDR } from "../lib/format";

interface Props {
  hint: InfeasibilityHint;
  onRaiseBudget?: (newBudget: number) => void;
}

export function InfeasibilityPanel({ hint, onRaiseBudget }: Props) {
  if (hint.error_code === "INFEASIBLE_BUDGET_TOO_LOW") {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-center gap-2 text-amber-900 font-semibold">
          <AlertTriangle className="h-5 w-5" /> {COPY.infeasibility.title}
        </div>
        <p className="mt-2 text-sm text-amber-800">{hint.message}</p>
        {hint.minimum_feasible_budget_idr && (
          <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-white px-3 py-2">
            <div>
              <div className="text-xs text-amber-700">{COPY.infeasibility.minimumLabel}</div>
              <div className="text-base font-semibold tabular-nums text-amber-900">
                {fmtIDR(hint.minimum_feasible_budget_idr)}
              </div>
            </div>
            {onRaiseBudget && (
              <button
                type="button"
                onClick={() => onRaiseBudget(hint.minimum_feasible_budget_idr!)}
                className="inline-flex items-center gap-1 rounded-lg bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-700"
              >
                <ArrowUp className="h-4 w-4" /> {COPY.infeasibility.raiseBudget}
              </button>
            )}
          </div>
        )}
        {hint.deficit_nutrients.length > 0 && (
          <div className="mt-3 text-xs text-amber-800">
            <div className="font-medium">{COPY.infeasibility.deficitLabel}:</div>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {hint.deficit_nutrients.map((n) => (
                <span
                  key={n}
                  className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-900"
                >
                  {COPY.akg.nutrient[n] ?? n}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
      <div className="flex items-center gap-2 text-amber-900 font-semibold">
        <AlertTriangle className="h-5 w-5" /> {COPY.infeasibility.restrictionsTitle}
      </div>
      <p className="mt-2 text-sm text-amber-800">{hint.message}</p>
      <p className="mt-2 text-xs text-amber-700">{COPY.infeasibility.restrictionsHint}</p>
    </div>
  );
}
