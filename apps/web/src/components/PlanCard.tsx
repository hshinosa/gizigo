import { useState } from "react";
import { ChevronDown, ChevronUp, Soup, AlertTriangle } from "lucide-react";
import type { Plan } from "../lib/types";
import { COPY } from "../copy/id";
import { fmtIDR, fmtNutrient, fmtPct, cn } from "../lib/format";

interface Props {
  plan: Plan;
  onOpenDrawer?: (plan: Plan) => void;
}

const ACCENT: Record<Plan["plan_type"], string> = {
  cheapest: "border-brand-200 bg-brand-50",
  balanced: "border-sky-200 bg-sky-50",
  diverse: "border-fuchsia-200 bg-fuchsia-50",
};

const ACCENT_TEXT: Record<Plan["plan_type"], string> = {
  cheapest: "text-brand-800",
  balanced: "text-sky-800",
  diverse: "text-fuchsia-800",
};

const BAR_COLOR = (pct: number): string => {
  if (pct < 80) return "bg-amber-400";
  if (pct < 100) return "bg-amber-500";
  if (pct <= 120) return "bg-brand-500";
  if (pct <= 200) return "bg-brand-600";
  return "bg-sky-500";
};

export function PlanCard({ plan, onOpenDrawer }: Props) {
  const [expanded, setExpanded] = useState(true);

  const grouped = plan.ingredients.reduce<Record<string, typeof plan.ingredients>>((acc, u) => {
    (acc[u.meal_slot] ??= []).push(u);
    return acc;
  }, {});

  return (
    <article
      className={cn(
        "rounded-2xl border bg-white shadow-sm overflow-hidden",
        ACCENT[plan.plan_type],
      )}
    >
      <header className="px-5 py-4 flex items-start justify-between gap-3">
        <div>
          <h3 className={cn("text-lg font-semibold", ACCENT_TEXT[plan.plan_type])}>
            {plan.plan_label_id}
          </h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-600">
            <span>{COPY.plans.foodGroupCount(plan.food_group_count)}</span>
            <span>•</span>
            <span className="font-semibold tabular-nums">{fmtIDR(plan.total_cost_idr)}</span>
          </div>
          {plan.diverse_constraint_relaxed && (
            <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
              <AlertTriangle className="h-3 w-3" />
              {COPY.plans.relaxedBadge}
              {plan.relaxation_reason ? ` (${COPY.plans.relaxationReason[plan.relaxation_reason] ?? plan.relaxation_reason})` : ""}
            </div>
          )}
        </div>
        {onOpenDrawer && (
          <button
            type="button"
            onClick={() => onOpenDrawer(plan)}
            className="shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm border border-slate-200 hover:border-brand-300 whitespace-nowrap"
          >
            <Soup className="h-3.5 w-3.5" /> Resep
          </button>
        )}
      </header>

      <div className="px-5 pb-3 space-y-2">
        {plan.achievement.map((a) => {
          const pct = Math.max(0, Math.min(220, a.pct));
          return (
            <div key={a.nutrient} className="text-xs">
              <div className="flex items-center justify-between text-slate-700">
                <span className="font-medium">{COPY.akg.nutrient[a.nutrient] ?? a.nutrient}</span>
                <span className="tabular-nums text-slate-500">
                  {fmtNutrient(a.achieved, a.unit)} / {fmtNutrient(a.required, a.unit)} <span className={cn("ml-1 font-semibold", a.pct < 100 ? "text-amber-600" : "text-brand-700")}>{fmtPct(a.pct)}</span>
                </span>
              </div>
              <div className="mt-1 h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all", BAR_COLOR(a.pct))}
                  style={{ width: `${(pct / 220) * 100}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full px-5 py-2 flex items-center justify-between border-t border-slate-100 text-xs text-slate-600 hover:bg-slate-50"
      >
        <span>{plan.ingredients.length} bahan</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {expanded && (
        <div className="px-5 pb-4 pt-1 space-y-3 bg-white">
          {(["sarapan", "makan_siang", "makan_malam", "kudapan"] as const).map((slot) => {
            const items = grouped[slot];
            if (!items || items.length === 0) return null;
            return (
              <div key={slot}>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  {COPY.meals[slot]}
                </div>
                <ul className="space-y-1">
                  {items.map((u) => (
                    <li key={u.ingredient_id} className="flex items-center justify-between text-xs">
                      <span className="truncate text-slate-700">{u.display_name}</span>
                      <span className="ml-2 shrink-0 tabular-nums text-slate-500">
                        {Math.round(u.grams)} g · {fmtIDR(u.cost_idr)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
