import { useState } from "react";
import { TrendingUp } from "lucide-react";
import { COPY } from "../copy/id";
import { fmtIDR } from "../lib/format";

export interface Perturbation {
  ingredient_id: string;
  delta_pct: number;
}

interface Props {
  costDelta: number;
  perturbations: Perturbation[];
  onChange: (next: Perturbation[]) => void;
  onPreset: (presetId: "cabai_50" | "telur_minus10" | "beras_15" | "cabai_rawit_natal" | "telur_lebaran") => void;
}

export function SensitivityBar({ costDelta, perturbations, onChange, onPreset }: Props) {
  const [globalShift, setGlobalShift] = useState(0);

  const applyGlobal = (pct: number) => {
    setGlobalShift(pct);
    onChange([]);
    if (pct === 0) {
      onChange([]);
      return;
    }
    onChange([{ ingredient_id: "tkpi_AR001", delta_pct: pct }]);
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-slate-800">
            <TrendingUp className="h-4 w-4 text-brand-500" /> {COPY.sensitivity.title}
          </h3>
          <p className="text-xs text-slate-500 mt-1">{COPY.sensitivity.subtitle}</p>
        </div>
        <div
          className={
            costDelta === 0
              ? "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 tabular-nums"
              : costDelta > 0
                ? "rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 tabular-nums"
                : "rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-800 tabular-nums"
          }
          aria-live="polite"
        >
          {COPY.sensitivity.deltaCost(costDelta)}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="range"
          min={-50}
          max={100}
          step={5}
          value={globalShift}
          onChange={(e) => applyGlobal(Number(e.target.value))}
          className="flex-1 accent-brand-500"
          aria-label="Global price shift"
        />
        <span className="w-14 text-right text-sm font-medium tabular-nums text-slate-700">
          {globalShift > 0 ? "+" : ""}
          {globalShift}%
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onPreset("cabai_50")}
          className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-800 hover:bg-amber-100"
        >
          {COPY.sensitivity.presets.cabai_50}
        </button>
        <button
          type="button"
          onClick={() => onPreset("telur_minus10")}
          className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs text-sky-800 hover:bg-sky-100"
        >
          {COPY.sensitivity.presets.telur_minus10}
        </button>
        <button
          type="button"
          onClick={() => onPreset("beras_15")}
          className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs text-orange-800 hover:bg-orange-100"
        >
          {COPY.sensitivity.presets.beras_15}
        </button>
        <button
          type="button"
          onClick={() => onPreset("cabai_rawit_natal")}
          className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs text-red-800 hover:bg-red-100"
        >
          {COPY.sensitivity.presets.cabai_rawit_natal}
        </button>
        <button
          type="button"
          onClick={() => onPreset("telur_lebaran")}
          className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs text-violet-800 hover:bg-violet-100"
        >
          {COPY.sensitivity.presets.telur_lebaran}
        </button>
      </div>

      {perturbations.length > 0 && (
        <div className="mt-3 text-xs text-slate-500">
          {perturbations.length} ingredient{perturbations.length === 1 ? "" : "s"} modified · cost delta {fmtIDR(Math.abs(costDelta))}
        </div>
      )}
    </section>
  );
}
