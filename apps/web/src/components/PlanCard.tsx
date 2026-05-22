import { useState } from "react";
import { ChevronDown, ChevronUp, Soup, AlertTriangle, Printer, Download } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
} from "recharts";
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

function downloadCSV(plan: Plan) {
  const rows = [
    ["ingredient_id", "name", "food_group", "meal_slot", "grams", "cost_idr"],
    ...plan.ingredients.map((i) => [
      i.ingredient_id,
      `"${i.display_name.replace(/"/g, '""')}"`,
      i.food_group,
      i.meal_slot,
      Math.round(i.grams).toString(),
      Math.round(i.cost_idr).toString(),
    ]),
  ];
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `gizigo-${plan.plan_type}-procurement.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

const ACCENT_BORDER: Record<Plan["plan_type"], string> = {
  cheapest: "border-l-brand-500",
  balanced: "border-l-sky-500",
  diverse: "border-l-fuchsia-500",
};

export function PlanCard({ plan, onOpenDrawer }: Props) {
  const [expanded, setExpanded] = useState(true);

  const grouped = plan.ingredients.reduce<Record<string, typeof plan.ingredients>>((acc, u) => {
    (acc[u.meal_slot] ??= []).push(u);
    return acc;
  }, {});

  return (
    <article
      data-print-card
      data-plan-type={plan.plan_type}
      className={cn(
        "rounded-2xl border border-slate-200 border-l-4 bg-white shadow-sm overflow-hidden",
        ACCENT_BORDER[plan.plan_type],
      )}
    >
      <header className="px-5 py-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className={cn("text-[11px] font-semibold uppercase tracking-wider", ACCENT_TEXT[plan.plan_type])}>
            {plan.plan_label}
          </p>
          <p className="text-2xl font-black tabular-nums text-slate-900 mt-0.5 leading-none">
            {fmtIDR(plan.total_cost_idr)}
          </p>
          <div className="mt-1.5 flex items-center gap-2 text-xs text-slate-500">
            <span>{COPY.plans.foodGroupCount(plan.food_group_count)}</span>
            <span>·</span>
            <span>{plan.ingredients.length} ingredients</span>
          </div>
          {plan.diverse_constraint_relaxed && (
            <div className="mt-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
              <AlertTriangle className="h-3 w-3" />
              {COPY.plans.relaxedBadge}
              {plan.relaxation_reason ? ` (${COPY.plans.relaxationReason[plan.relaxation_reason] ?? plan.relaxation_reason})` : ""}
            </div>
          )}
        </div>
        <div className="shrink-0 flex items-center gap-1.5 print:hidden">
          <button
            type="button"
            onClick={() => downloadCSV(plan)}
            aria-label={`Download ${plan.plan_label} as CSV`}
            title="Download procurement list as CSV"
            className="inline-flex items-center gap-1 rounded-lg bg-white px-2 py-1.5 text-xs font-medium text-slate-700 shadow-sm border border-slate-200 hover:border-brand-300 whitespace-nowrap"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => {
              if (typeof document === "undefined") return;
              document.body.dataset.printPlan = plan.plan_type;
              window.print();
              setTimeout(() => { delete document.body.dataset.printPlan; }, 500);
            }}
            aria-label={`Print ${plan.plan_label} as PDF`}
            title="Print this plan to PDF"
            className="inline-flex items-center gap-1 rounded-lg bg-white px-2 py-1.5 text-xs font-medium text-slate-700 shadow-sm border border-slate-200 hover:border-brand-300 whitespace-nowrap"
          >
            <Printer className="h-3.5 w-3.5" />
          </button>
          {onOpenDrawer && (
            <button
              type="button"
              onClick={() => onOpenDrawer(plan)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm border border-slate-200 hover:border-brand-300 whitespace-nowrap"
            >
              <Soup className="h-3.5 w-3.5" /> Recipe
            </button>
          )}
        </div>
      </header>

      <div className="px-5 pb-2">
        <ResponsiveContainer width="100%" height={220}>
          <RadarChart
            data={plan.achievement.map((a) => ({
              nutrient: COPY.akg.nutrient[a.nutrient] ?? a.nutrient,
              pct: Math.min(200, Math.round(a.pct)),
              fullMark: 200,
            }))}
            margin={{ top: 4, right: 20, bottom: 4, left: 20 }}
          >
            <PolarGrid stroke="#e2e8f0" />
            <PolarAngleAxis
              dataKey="nutrient"
              tick={{ fontSize: 10, fill: "#475569" }}
            />
            <Radar
              name="Achievement %"
              dataKey="pct"
              stroke={plan.plan_type === "cheapest" ? "#1d623b" : plan.plan_type === "balanced" ? "#0284c7" : "#a21caf"}
              fill={plan.plan_type === "cheapest" ? "#1d623b" : plan.plan_type === "balanced" ? "#0284c7" : "#a21caf"}
              fillOpacity={0.35}
              strokeWidth={2.5}
            />
            <Tooltip
              formatter={(v: unknown) => [`${Number(v)}%`, "Achievement"]}
              contentStyle={{ fontSize: 11, borderRadius: 8 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="px-5 pb-3 space-y-1.5">
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
              <div className="mt-0.5 h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
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
        <span>{plan.ingredients.length} ingredients</span>
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
