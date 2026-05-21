# Data Sources

GiziGo is grounded in two public Indonesian government sources plus a small, hand-curated retail price layer. Every dataset is committed to the repository so the build is reproducible without re-hitting any upstream service.

## 1. Nutrient catalogue (TKPI 2020)

- **Upstream**: *Tabel Komposisi Pangan Indonesia 2020* — Direktorat Gizi Masyarakat, Kementerian Kesehatan RI. ISBN 978-623-301-0368. The authoritative national food-composition table.
- **Retrieval channel**: https://www.panganku.org/id-ID/semua_nutrisi (catalog, GET) + https://www.panganku.org/id-ID/view (detail, POST `haha=<food_code>`). panganku.org is the Kemenkes-affiliated portal that re-publishes TKPI for end users.
- **Method**: One-shot scrape via `services/api/scripts/scrape_panganku.py`. Polite 0.3 s delay between requests, identifying User-Agent. The full ~1146 detail pages plus the catalog HTML are committed under [`data/raw/panganku/`](../data/raw/panganku/). Re-running the scraper is idempotent: existing files are not re-fetched.
- **Normalization**: `services/api/scripts/normalize_panganku.py` parses the eight tracked nutrients per 100 g of edible portion. When a nutrient row is absent in the upstream HTML, we treat it as 0 (this is consistent with how TKPI itself omits zero-value nutrients on many entries — e.g. white rice has no listed vitamin A).
- **Output**: [`data/normalized/ingredients.json`](../data/normalized/ingredients.json), 1146 ingredients, `catalog_hash = 2c14daf9cda57500`.
- **Quarantine policy**: A row is rejected only when (a) energy or protein cannot be parsed, or (b) any value is negative. The validation report at [`data/validation-report.json`](../data/validation-report.json) currently shows zero quarantined rows.

## 2. AKG (Angka Kecukupan Gizi)

- **Upstream**: *Peraturan Menteri Kesehatan RI No. 28 Tahun 2019* — the Permenkes that lists daily AKG values per age/sex/condition.
- **Coverage**: We extract a 7-category subset that covers both demo personas:
  - `toddler_1_3` — Balita 1-3 tahun
  - `child_4_6` — Anak 4-6 tahun
  - `teen_male_13_15` and `teen_female_13_15`
  - `adult_male_19_49` and `adult_female_19_49`
  - `lactating_mother_0_6m` — adult-female baseline plus the 0-6 month lactation supplement
- **Output**: [`data/akg/permenkes-28-2019.json`](../data/akg/permenkes-28-2019.json).

## 3. Retail prices

The optimizer needs a price-per-100 g vector that matches the nutrient basis. We sample 40 staple ingredients in two regions:

- **DKI Jakarta** ([`data/prices/dki_jakarta.yaml`](../data/prices/dki_jakarta.yaml)) — sources: https://infopangan.jakarta.go.id (DKI Jakarta Info Pangan, official portal), https://www.bi.go.id/hargapangan (PIHPS Bank Indonesia), and a small manual sample at Pasar Tebet and Pasar Senen in May 2026.
- **National baseline** ([`data/prices/national_baseline.yaml`](../data/prices/national_baseline.yaml)) — sources: PIHPS Nasional median across 34 provinces, plus Bappenas Stranas Stunting commodity bands. This is intentionally tuned to put the "Anggaran Ekstrem" persona into infeasibility so the demo exercises the budget-bisection branch.

Each YAML row carries `name` and `price_per_100g_idr` for traceability. Prices update by replacing the YAML and restarting the API — no rebuild required.

## 4. Substitution graph

[`data/substitutes.yaml`](../data/substitutes.yaml) — 32 hand-curated swap pairs grouped by nutritional similarity (tempe ↔ tofu, spinach ↔ water spinach, orange sweet potato ↔ carrot for vitamin A, etc.). Used by the *Most Varied* heuristic to pick acceptors when reallocating spend.

## 5. Cooking-method mapping

[`data/cooking-method.yaml`](../data/cooking-method.yaml) — per-ingredient cooking-verb overrides plus a food-group fallback. Each ingredient is mapped to one of `{tumis, rebus, kukus, goreng, sangrai, mentah}`. This is **hand-curated, not learned** — the templated humanizer reads this file directly to render meal narrations.

## Reproducibility checks

```bash
make data       # scrape + normalize, idempotent
```

The current build snapshots:

| File | Count | Hash / Notes |
|---|---|---|
| `data/raw/panganku/` | 1146 detail pages + index + meta | scrape took 8 min, 0 errors |
| `data/normalized/ingredients.json` | 1146 ingredients | `catalog_hash = 2c14daf9cda57500` |
| `data/normalized/food_groups.json` | 13 distinct food groups | |
| `data/akg/permenkes-28-2019.json` | 7 AKG categories × 8 nutrients | Permenkes 28/2019 subset |
| `data/prices/dki_jakarta.yaml` | 105 priced ingredients | |
| `data/prices/national_baseline.yaml` | 105 priced ingredients | |
| `data/substitutes.yaml` | 32 entries, 40 unique IDs | |
| `data/cooking-method.yaml` | 41 overrides + 13 group defaults | |
| `data/validation-report.json` | 0 quarantined | |
