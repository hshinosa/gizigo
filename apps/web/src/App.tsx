import { useState, useCallback, useMemo } from "react";
import { Toaster, toast } from "sonner";
import { Loader2, Sparkles } from "lucide-react";
import { HouseholdForm } from "./components/HouseholdForm";
import { PlanCard } from "./components/PlanCard";
import { InfeasibilityPanel } from "./components/InfeasibilityPanel";
import { SensitivityBar, type Perturbation } from "./components/SensitivityBar";
import { RecipeDrawer } from "./components/RecipeDrawer";
import { PERSONAS } from "./data/personas";
import { COPY } from "./copy/id";
import { optimize, sensitivity, humanize, ApiClientError } from "./lib/api";
import type { OptimizeRequest, OptimizeResponse, Plan } from "./lib/types";
import { fmtIDR } from "./lib/format";

type Status = "idle" | "loading" | "success" | "error" | "infeasible";

const PRESET_PERTURBATIONS: Record<string, Perturbation[]> = {
  cabai_50: [
    { ingredient_id: "tkpi_NR014", delta_pct: 50 },
    { ingredient_id: "tkpi_NR015", delta_pct: 50 },
  ],
  telur_minus10: [
    { ingredient_id: "tkpi_HR001", delta_pct: -10 },
    { ingredient_id: "tkpi_HR011", delta_pct: -10 },
    { ingredient_id: "tkpi_HR005", delta_pct: -10 },
  ],
};

export default function App() {
  const [request, setRequest] = useState<OptimizeRequest>(PERSONAS.bu_sari);
  const [status, setStatus] = useState<Status>("idle");
  const [response, setResponse] = useState<OptimizeResponse | null>(null);
  const [perturbations, setPerturbations] = useState<Perturbation[]>([]);
  const [costDelta, setCostDelta] = useState(0);
  const [drawerPlan, setDrawerPlan] = useState<Plan | null>(null);
  const [drawerMeals, setDrawerMeals] = useState<{ meal_slot: string; title: string; description_id: string }[]>([]);

  const runOptimize = useCallback(async () => {
    setStatus("loading");
    try {
      const result = await optimize(request);
      setResponse(result);
      if (result.infeasibility && result.plans.length === 0) {
        setStatus("infeasible");
        toast.warning("Anggaran belum mencukupi.", {
          description: result.infeasibility.message,
        });
      } else if (result.infeasibility) {
        setStatus("success");
        toast.warning("Plan tersedia tapi sebagian AKG belum tercapai.", {
          description: result.infeasibility.message,
        });
      } else if (result.plans.length > 0) {
        setStatus("success");
        toast.success(`Rencana siap · ${result.elapsed_ms} ms`, {
          description: `${result.plans.length} plan · catalog ${result.catalog_hash.slice(0, 8)}`,
        });
      } else {
        setStatus("success");
      }
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiClientError) {
        toast.error(err.message, { description: `Kode: ${err.errorCode}` });
      } else {
        toast.error(COPY.errors.generic);
      }
    }
  }, [request]);

  const runSensitivity = useCallback(async (next: Perturbation[]) => {
    if (!response || next.length === 0) {
      setCostDelta(0);
      return;
    }
    try {
      const result = await sensitivity(request, next);
      setCostDelta(result.cost_delta_idr);
    } catch {
    }
  }, [request, response]);

  const onSensitivityChange = useCallback((next: Perturbation[]) => {
    setPerturbations(next);
    runSensitivity(next);
  }, [runSensitivity]);

  const onPreset = useCallback((id: "cabai_50" | "telur_minus10") => {
    const next = PRESET_PERTURBATIONS[id];
    setPerturbations(next);
    runSensitivity(next);
  }, [runSensitivity]);

  const onOpenDrawer = useCallback(async (plan: Plan) => {
    setDrawerPlan(plan);
    try {
      const result = await humanize(plan, false);
      setDrawerMeals(result.meals);
    } catch {
      setDrawerMeals([]);
    }
  }, []);

  const orderedPlans = useMemo(() => {
    if (!response) return [];
    const order: Record<string, number> = { cheapest: 0, balanced: 1, diverse: 2 };
    return [...response.plans].sort((a, b) => (order[a.plan_type] ?? 99) - (order[b.plan_type] ?? 99));
  }, [response]);

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-5 py-5 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-500 text-white shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{COPY.app.title}</h1>
            <p className="text-xs text-slate-600">{COPY.app.tagline}</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-5">
          <HouseholdForm
            value={request}
            onChange={(next) => {
              setRequest(next);
              setResponse(null);
              setStatus("idle");
              setPerturbations([]);
              setCostDelta(0);
            }}
            onSubmit={runOptimize}
            isLoading={status === "loading"}
          />
        </section>

        <section className="lg:col-span-7 space-y-5">
          {status === "idle" && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <Sparkles className="mx-auto h-8 w-8 text-brand-500" />
              <p className="mt-3 text-slate-600">{COPY.empty.hero}</p>
              <p className="mt-1 text-xs text-slate-400">{COPY.app.subtitle}</p>
            </div>
          )}

          {status === "loading" && (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="animate-pulse rounded-2xl border border-slate-200 bg-white p-5">
                  <div className="h-5 w-32 rounded bg-slate-200" />
                  <div className="mt-3 h-3 w-48 rounded bg-slate-100" />
                  <div className="mt-4 space-y-2">
                    {[0, 1, 2, 3, 4, 5, 6, 7].map((j) => (
                      <div key={j} className="h-2 rounded bg-slate-100" />
                    ))}
                  </div>
                </div>
              ))}
              <div className="text-center text-xs text-slate-500 flex items-center justify-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" /> Menjalankan ILP solver...
              </div>
            </div>
          )}

          {status === "infeasible" && response?.infeasibility && (
            <InfeasibilityPanel
              hint={response.infeasibility}
              onRaiseBudget={(newBudget) => {
                setRequest((r) => ({ ...r, daily_budget_idr: newBudget }));
                setStatus("idle");
                setResponse(null);
              }}
            />
          )}

          {status === "success" && response && (
            <>
              {response.infeasibility && (
                <InfeasibilityPanel
                  hint={response.infeasibility}
                  onRaiseBudget={(newBudget) => {
                    setRequest((r) => ({ ...r, daily_budget_idr: newBudget }));
                    setStatus("idle");
                    setResponse(null);
                  }}
                />
              )}
              <SensitivityBar
                costDelta={costDelta}
                perturbations={perturbations}
                onChange={onSensitivityChange}
                onPreset={onPreset}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {orderedPlans.map((p) => (
                  <PlanCard key={p.plan_type} plan={p} onOpenDrawer={onOpenDrawer} />
                ))}
              </div>
              <div className="text-xs text-slate-400 text-right">
                request {response.request_id} · catalog {response.catalog_hash.slice(0, 8)} · solved in {response.elapsed_ms} ms · {fmtIDR(orderedPlans[0]?.total_cost_idr ?? 0)} terendah
              </div>
            </>
          )}

          {status === "error" && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
              {COPY.errors.generic}
            </div>
          )}
        </section>
      </main>

      <RecipeDrawer plan={drawerPlan} meals={drawerMeals} onClose={() => setDrawerPlan(null)} />
      <Toaster richColors position="top-right" closeButton />
    </div>
  );
}
