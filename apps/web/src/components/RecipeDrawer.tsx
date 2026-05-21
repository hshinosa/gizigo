import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { COPY } from "../copy/id";
import type { Plan } from "../lib/types";
import { fmtIDR } from "../lib/format";

interface Props {
  plan: Plan | null;
  meals: { meal_slot: string; title: string; description_id: string }[];
  onClose: () => void;
}

export function RecipeDrawer({ plan, meals, onClose }: Props) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!plan) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    drawerRef.current?.focus();
    return () => window.removeEventListener("keydown", onKey);
  }, [plan, onClose]);

  if (!plan) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Resep rencana makan"
      className="fixed inset-0 z-50 flex"
    >
      <div className="absolute inset-0 bg-slate-900/40" onClick={onClose} />
      <aside
        ref={drawerRef}
        tabIndex={-1}
        className="relative ml-auto h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
          aria-label={COPY.drawer.closeLabel}
        >
          <X className="h-5 w-5" />
        </button>
        <h2 className="text-xl font-semibold text-slate-900">
          {COPY.drawer.titlePrefix} {plan.plan_label_id}
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          {fmtIDR(plan.total_cost_idr)} · {plan.food_group_count} kelompok pangan · {plan.ingredients.length} bahan
        </p>

        <section className="mt-6 space-y-4">
          {meals.map((m) => (
            <div key={m.meal_slot} className="rounded-xl border border-slate-200 p-4">
              <div className="text-sm font-semibold text-slate-800">{m.title}</div>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{m.description_id}</p>
            </div>
          ))}
        </section>
      </aside>
    </div>
  );
}
