export const fmtIDR = (value: number): string => {
  const rounded = Math.round(value);
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(rounded);
};

export const fmtNutrient = (value: number, unit: string): string => {
  const v = unit.startsWith("µg") || unit === "kcal" || unit === "mg"
    ? Math.round(value)
    : Math.round(value * 10) / 10;
  return `${v.toLocaleString("id-ID")} ${unit}`;
};

export const fmtPct = (pct: number): string => `${Math.round(pct)}%`;

export const cn = (...c: (string | undefined | false | null)[]): string =>
  c.filter(Boolean).join(" ");
