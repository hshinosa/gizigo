import { useState } from "react";
import { Plus, Trash2, Users, DollarSign, MapPin, Ban, Sparkles } from "lucide-react";
import { COPY } from "../copy/id";
import { PERSONAS, type PersonaId } from "../data/personas";
import type { OptimizeRequest, AkgCategory, Region, RestrictionType } from "../lib/types";
import { fmtIDR, cn } from "../lib/format";

interface Props {
  value: OptimizeRequest;
  onChange: (next: OptimizeRequest) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const AKG_OPTIONS: { value: AkgCategory; label: string }[] = (
  Object.keys(COPY.akgCategoryLabel) as AkgCategory[]
).map((k) => ({ value: k, label: COPY.akgCategoryLabel[k] }));

export function HouseholdForm({ value, onChange, onSubmit, isLoading }: Props) {
  const [newRestriction, setNewRestriction] = useState({ type: "dislike" as RestrictionType, target: "" });

  const updateMember = (idx: number, patch: Partial<OptimizeRequest["members"][0]>) => {
    const members = value.members.map((m, i) => (i === idx ? { ...m, ...patch } : m));
    onChange({ ...value, members });
  };

  const addMember = () => {
    const n = value.members.length + 1;
    onChange({
      ...value,
      members: [
        ...value.members,
        { member_id: `m${Date.now()}`, label: `Anggota ${n}`, akg_category: "adult_male_19_49" },
      ],
    });
  };

  const removeMember = (idx: number) => {
    if (value.members.length <= 1) return;
    onChange({ ...value, members: value.members.filter((_, i) => i !== idx) });
  };

  const setBudget = (amount: number) =>
    onChange({ ...value, daily_budget_idr: Math.max(0, Math.min(2_000_000, Math.round(amount))) });

  const applyPersona = (id: PersonaId) => onChange({ ...PERSONAS[id] });

  const addRestriction = () => {
    if (!newRestriction.target.trim()) return;
    onChange({
      ...value,
      restrictions: [
        ...value.restrictions,
        { type: newRestriction.type, target: newRestriction.target.trim() },
      ],
    });
    setNewRestriction({ ...newRestriction, target: "" });
  };

  const removeRestriction = (idx: number) =>
    onChange({ ...value, restrictions: value.restrictions.filter((_, i) => i !== idx) });

  return (
    <form
      className="space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
          <Sparkles className="h-4 w-4 text-brand-500" />
          {COPY.persona.label}
        </div>
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => applyPersona("bu_sari")}
            className="rounded-xl border border-brand-100 bg-brand-50 px-4 py-3 text-left text-sm font-medium text-brand-800 hover:border-brand-300"
          >
            {COPY.persona.options.bu_sari}
          </button>
          <button
            type="button"
            onClick={() => applyPersona("anggaran_ekstrem")}
            className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-left text-sm font-medium text-amber-800 hover:border-amber-300"
          >
            {COPY.persona.options.anggaran_ekstrem}
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-semibold text-slate-800">
            <Users className="h-4 w-4 text-brand-500" /> {COPY.household.sectionTitle}
          </h3>
          <button
            type="button"
            onClick={addMember}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:border-brand-300 hover:text-brand-700"
          >
            <Plus className="h-3 w-3" /> {COPY.household.addMember}
          </button>
        </div>
        <div className="space-y-2">
          {value.members.map((m, idx) => (
            <div key={m.member_id} className="grid grid-cols-12 gap-2 items-center">
              <input
                value={m.label}
                onChange={(e) => updateMember(idx, { label: e.target.value })}
                className="col-span-5 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-400"
                placeholder={COPY.household.memberLabel}
                aria-label={COPY.household.memberLabel}
              />
              <select
                value={m.akg_category}
                onChange={(e) => updateMember(idx, { akg_category: e.target.value as AkgCategory })}
                className="col-span-6 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-400"
                aria-label={COPY.household.memberCategory}
              >
                {AKG_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => removeMember(idx)}
                disabled={value.members.length <= 1}
                className="col-span-1 rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-30"
                aria-label={COPY.household.removeMember}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <DollarSign className="h-4 w-4 text-brand-500" /> {COPY.budget.sectionTitle}
        </h3>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={5000}
            max={300000}
            step={1000}
            value={value.daily_budget_idr}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 accent-brand-500"
            aria-label={COPY.budget.label}
          />
          <input
            type="number"
            value={value.daily_budget_idr}
            onChange={(e) => setBudget(Number(e.target.value))}
            min={0}
            step={1000}
            className="w-32 rounded-lg border border-slate-200 px-3 py-2 text-sm text-right tabular-nums focus:border-brand-400"
            aria-label={COPY.budget.label}
          />
        </div>
        <div className="text-xs text-slate-500">{fmtIDR(value.daily_budget_idr)} per hari</div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <MapPin className="h-4 w-4 text-brand-500" /> {COPY.region.sectionTitle}
        </h3>
        <div className="flex gap-2">
          {(Object.keys(COPY.region.options) as Region[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => onChange({ ...value, region: r })}
              className={cn(
                "rounded-lg px-3 py-2 text-sm border",
                value.region === r
                  ? "border-brand-400 bg-brand-50 text-brand-800"
                  : "border-slate-200 text-slate-600 hover:border-brand-200",
              )}
            >
              {COPY.region.options[r]}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <Ban className="h-4 w-4 text-brand-500" /> {COPY.restrictions.sectionTitle}
        </h3>
        <div className="flex gap-2">
          <select
            value={newRestriction.type}
            onChange={(e) => setNewRestriction({ ...newRestriction, type: e.target.value as RestrictionType })}
            className="rounded-lg border border-slate-200 px-2 py-2 text-sm"
          >
            <option value="dislike">{COPY.restrictions.typeDislike}</option>
            <option value="allergy">{COPY.restrictions.typeAllergy}</option>
            <option value="religious">{COPY.restrictions.typeReligious}</option>
          </select>
          <input
            value={newRestriction.target}
            onChange={(e) => setNewRestriction({ ...newRestriction, target: e.target.value })}
            placeholder={COPY.restrictions.placeholder}
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-400"
          />
          <button
            type="button"
            onClick={addRestriction}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:border-brand-300"
          >
            +
          </button>
        </div>
        {value.restrictions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {value.restrictions.map((r, idx) => (
              <span
                key={`${r.type}-${r.target}-${idx}`}
                className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
              >
                <span className="font-medium uppercase tracking-wide text-[10px]">{r.type}</span>
                <span>{r.target}</span>
                <button
                  type="button"
                  onClick={() => removeRestriction(idx)}
                  className="text-slate-400 hover:text-red-600"
                  aria-label="Hapus pembatasan"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className={cn(
          "w-full rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-sm transition",
          isLoading
            ? "bg-brand-300 cursor-not-allowed"
            : "bg-brand-600 hover:bg-brand-700",
        )}
      >
        {isLoading ? COPY.cta.optimizing : COPY.cta.optimize}
      </button>
    </form>
  );
}
