## ADDED Requirements

### Requirement: TKPI Ingredient Catalog
The system SHALL load and serve a derivative of the Tabel Komposisi Pangan Indonesia (TKPI) dataset published by Kemenkes via the official web portal `panganku.org` (Data Komposisi Pangan Indonesia, 2017 edition with 2020 revision). Each ingredient SHALL be exposed with a stable `ingredient_id` derived from its `panganku` food code (e.g. `tkpi_AM002`), an Indonesian display name, a food-group code, and per-100g nutrient values for the eight tracked nutrients (energy, protein, fat, carbohydrate, iron, zinc, vitamin A, calcium). Raw scraped artifacts SHALL live under `data/raw/panganku/` and parsed normalized records under `data/normalized/ingredients.json`.

#### Scenario: Ingredient lookup by id
- **WHEN** a caller requests ingredient `tkpi_AM002`
- **THEN** the system SHALL return its name, food group, per-100g nutrient vector, and source URL (`panganku.org/id-ID/<slug>`)
- **AND** all eight tracked nutrients SHALL be present as numeric values (zero is allowed; null is not)

#### Scenario: Catalog covers minimum breadth
- **WHEN** the catalog is loaded
- **THEN** it SHALL contain at least 150 distinct ingredients
- **AND** at least 7 distinct food groups (e.g., serealia, kacang-kacangan, sayur, buah, daging, ikan, telur)

### Requirement: Unit and Validity Enforcement
The system SHALL validate every nutrient value at load time and quarantine rows with inconsistent units, negative values, or missing tracked nutrients. The validation report SHALL be persisted under `data/validation-report.json`.

#### Scenario: Negative nutrient quarantines a row
- **WHEN** a TKPI row has `protein_g: -1.2`
- **THEN** the row SHALL be quarantined with reason `negative_value`
- **AND** the validation report SHALL list the row id and reason

### Requirement: Permenkes 28/2019 AKG Reference (Demo Subset)
The system SHALL ship a versioned AKG reference at `data/akg/permenkes-28-2019.json` covering the seven supported member categories required for the demo personas: `toddler_1_3`, `child_4_6`, `teen_male_13_15`, `teen_female_13_15`, `adult_male_19_49`, `adult_female_19_49`, `lactating_mother_0_6m`. Each entry SHALL specify the eight tracked nutrients and a stable schema version.

#### Scenario: Lookup AKG for adult woman 19-49
- **WHEN** the optimizer queries AKG for `adult_female_19_49`
- **THEN** the response SHALL contain numeric values for all eight tracked nutrients
- **AND** the schema_version SHALL be `permenkes-28-2019.subset.v1`

#### Scenario: Lactating supplement applied
- **WHEN** the optimizer queries AKG for `lactating_mother_0_6m`
- **THEN** the returned values SHALL include the lactation 0-6m supplement deltas defined in Permenkes 28/2019 (notably +330 kcal energy, +0.4mg iron over base adult female)

### Requirement: Regional Price Snapshots
The system SHALL ship at least two price snapshots — `dki-jakarta` and `national-baseline` — at `data/prices/<region>.yaml`. Each entry SHALL include `ingredient_id`, `unit_price_rupiah_per_kg`, `last_updated_iso_date`, and `source_url`. Snapshots SHALL cover at least 70% of the catalog by ingredient count.

#### Scenario: Region price lookup
- **WHEN** the optimizer requests prices for `dki-jakarta`
- **THEN** the system SHALL return the Jakarta snapshot with at least 70% coverage of catalog ingredients
- **AND** every entry SHALL include a `last_updated_iso_date`

#### Scenario: Missing region falls back to national baseline
- **WHEN** the optimizer requests prices for an unknown region
- **THEN** the system SHALL return the `national-baseline` snapshot
- **AND** the response SHALL set `fallback: true`

### Requirement: Hand-Curated Substitution Table
The system SHALL ship a curated substitution table at `data/substitutes.yaml` mapping at least 30 common Indonesian ingredients (`cabai_merah_keriting`, `telur_ayam`, `tempe`, `tahu`, `bayam`, `kangkung`, `wortel`, etc.) to one or more substitute `ingredient_id`s with a brief reason field. The table SHALL be human-readable YAML.

#### Scenario: Substitute lookup
- **WHEN** the humanizer queries substitutes for `cabai_merah_keriting`
- **THEN** the response SHALL return at least one substitute id with a reason field
- **AND** the substitute SHALL be a valid `ingredient_id` present in the catalog

### Requirement: Data Provenance Manifest
The system SHALL ship a manifest at `data/MANIFEST.md` listing every dataset's source URL, license, version, retrieval date, and the script that produced the normalized form. Reviewers SHALL be able to reproduce the data pipeline from this manifest alone.

#### Scenario: Manifest names every dataset
- **WHEN** a reviewer reads `data/MANIFEST.md`
- **THEN** every file under `data/normalized/`, `data/akg/`, `data/prices/`, and `data/substitutes.yaml` SHALL be named in the manifest with its source and license
