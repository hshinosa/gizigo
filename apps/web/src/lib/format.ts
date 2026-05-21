export const fmtIDR = (value: number): string =>
  `Rp ${Math.round(value).toLocaleString("id-ID")}`;

export const fmtNutrient = (value: number, unit: string): string => {
  const v = unit.startsWith("µg") || unit === "kcal" || unit === "mg"
    ? Math.round(value)
    : Math.round(value * 10) / 10;
  return `${v.toLocaleString("id-ID")} ${unit}`;
};

export const fmtPct = (pct: number): string => `${Math.round(pct)}%`;

export const cn = (...c: (string | undefined | false | null)[]): string =>
  c.filter(Boolean).join(" ");
