# GiziGo Data Manifest

This directory bundles every data input that powers the optimizer. All files are derived from public, government, or hand-curated sources and are committed to the repo so the build is fully reproducible.

## Layout

```
data/
├── raw/panganku/         # Raw HTML pages scraped from panganku.org (Kemenkes TKPI 2020)
│   ├── _index.html       # Catalog of all 1146 ingredients
│   ├── _meta.json        # Scrape metadata (started, finished, errors)
│   └── <food_code>.html  # Per-ingredient detail page (~1146 files)
│
├── normalized/
│   ├── ingredients.json  # Normalized 8-nutrient catalogue (canonical)
│   └── food_groups.json  # Distinct food groups present in the catalogue
│
├── akg/
│   └── permenkes-28-2019.json  # AKG per AKG category (subset, 7 categories)
│
├── prices/
│   ├── dki_jakarta.yaml         # Retail prices Jakarta region
│   └── national_baseline.yaml   # Median national prices (used by Anggaran Ekstrem persona)
│
├── substitutes.yaml      # Hand-curated ingredient swap list (≥30 entries)
├── cooking-method.yaml   # Per-ingredient/per-group cooking verb mapping
└── validation-report.json # Quarantined rows from normalization
```

## Sources

### Nutrient catalogue

- **Upstream**: Tabel Komposisi Pangan Indonesia 2020, Direktorat Gizi Masyarakat, Kementerian Kesehatan RI. ISBN 978-623-301-0368.
- **Retrieval channel**: https://www.panganku.org/id-ID/semua_nutrisi (catalog) + POST `/id-ID/view` `haha=<food_code>` (detail).
- **Method**: One-shot scrape via `services/api/scripts/scrape_panganku.py`, polite 0.3 s delay between requests, User-Agent identifies the project. Raw HTML is committed under `data/raw/panganku/` so the build is reproducible without re-hitting the upstream.
- **Normalization**: `services/api/scripts/normalize_panganku.py` parses the eight tracked nutrients per 100 g of edible portion (energy kcal, protein g, fat g, carbohydrate g, iron mg, zinc mg, vitamin A µg RAE, calcium mg).
- **Validation rule**: A row is accepted iff every tracked nutrient is parseable and ≥ 0. Quarantined rows are listed in `validation-report.json` along with the reason.

### AKG (Angka Kecukupan Gizi)

- **Source**: Permenkes RI No. 28 Tahun 2019.
- **Coverage**: A 7-category subset (`toddler_1_3`, `child_4_6`, `teen_male_13_15`, `teen_female_13_15`, `adult_male_19_49`, `adult_female_19_49`, `lactating_mother_0_6m`) covering both demo personas. Lactating-mother values include the 0-6 month supplement applied to `adult_female_19_49`.

### Prices

- **DKI Jakarta**: Retail prices sourced from https://infopangan.jakarta.go.id and PIHPS Bank Indonesia, sampled May 2026 from Pasar Tebet and Pasar Senen.
- **National baseline**: Median of 34 provinces from PIHPS BI, plus Bappenas Stranas Stunting commodity bands.
- Prices are stored per 100 g of edible portion (matching nutrient basis) so the optimizer has a single common unit.

### Substitutes

`substitutes.yaml` defines 30+ swap pairs grouped by nutritional similarity (e.g. tempe ↔ tahu, bayam ↔ kangkung, ubi jalar oranye ↔ wortel for vitamin A). Used by `derive_diverse` to enrich variety, and by the UI to surface alternative ingredients in plan cards.

### Cooking method

`cooking-method.yaml` maps each ingredient (or food-group fallback) to one preferred cooking verb from `{tumis, rebus, kukus, goreng, sangrai, mentah}`. This drives the templated humanizer — there is no learning involved.

## Reproducibility

```
make data            # scrape + normalize + validate
```

The scrape is idempotent — existing detail HTMLs are reused without re-hitting panganku.org. Delete a specific HTML to force a re-fetch.
