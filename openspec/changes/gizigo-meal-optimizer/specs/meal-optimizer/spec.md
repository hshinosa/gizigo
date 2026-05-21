## ADDED Requirements

### Requirement: Three-Plan Generation
The system SHALL generate three daily meal plans from a single user request: a `Termurah` plan minimizing total cost subject to AKG nutrient lower bounds and the user budget; a `Paling Seimbang` plan minimizing a weighted sum of total cost plus a nutrient-deficit penalty subject to the user budget; and a `Paling Beragam` plan derived by iterative ingredient substitution on top of `Termurah` that swaps the least-impactful ingredient (by nutrient density per rupiah) with one from a previously-unused TKPI food group, repeating until at least `count_groups(Termurah) + 2` distinct food groups are present, the budget is exhausted, or AKG bounds break.

#### Scenario: Three plans returned for a feasible request
- **WHEN** the user submits a household profile of 4 members (1 lactating mother, 1 toddler 2-5y, 2 adults), a daily budget of Rp 80,000, region `dki-jakarta`, and no allergies
- **THEN** the API SHALL return exactly three plans labelled `cheapest`, `balanced`, `diverse`
- **AND** each plan SHALL include a list of `(ingredient_id, grams, meal_slot)` tuples covering at least three meal slots (`sarapan`, `makan_siang`, `makan_malam`)
- **AND** each plan SHALL include a `total_cost_rupiah` value not exceeding the budget
- **AND** each plan SHALL include an `akg_adequacy` map with one ratio (`achieved/required`) per tracked nutrient, where every ratio is ≥ 1.0

#### Scenario: Diverse plan uses more food groups than cheapest when feasible
- **WHEN** three plans are generated for a feasible request
- **THEN** the count of distinct TKPI food groups in `diverse` SHALL be ≥ the count in `cheapest` plus two, OR the system SHALL emit a metadata flag `diverse_constraint_relaxed: true` with a `reason` of `budget_exhausted` or `akg_bound_violated` if no such expansion is possible while keeping AKG and budget feasible

### Requirement: Hard Constraint Enforcement
The system SHALL treat halal, allergy, and regional-availability constraints as hard constraints that cannot be violated by any returned plan. The solver SHALL never include an ingredient that violates a declared restriction, even if doing so would improve the objective.

#### Scenario: Halal constraint excludes pork
- **WHEN** the user marks `dietary_law: halal`
- **THEN** no returned plan SHALL contain any ingredient whose TKPI category includes pork or pork derivatives
- **AND** the response SHALL include `applied_constraints: ["halal"]`

#### Scenario: Allergy constraint excludes peanut
- **WHEN** the user lists `peanut` in allergies
- **THEN** no returned plan SHALL contain peanut, peanut oil, or peanut-derived sauces
- **AND** if removing peanut renders the request infeasible, the system SHALL return an infeasibility report rather than silently substituting

### Requirement: AKG Nutrient Bound Compliance
The system SHALL enforce nutrient lower bounds aggregated across the daily plan that match Permenkes 28/2019 AKG values, segmented per household member by the supported member categories (`toddler_1_3`, `child_4_6`, `teen_male_13_15`, `teen_female_13_15`, `adult_male_19_49`, `adult_female_19_49`, `lactating_mother_0_6m`), then summed for the household. Tracked nutrients SHALL include energy (kcal), protein (g), fat (g), carbohydrate (g), iron (mg), zinc (mg), vitamin A (µg RAE), and calcium (mg).

#### Scenario: AKG segmentation for lactating mother
- **WHEN** the household includes a `lactating_mother_0_6m` member
- **THEN** the iron requirement contributed by that member SHALL be the AKG iron value for lactating women 0-6 months from Permenkes 28/2019
- **AND** the energy requirement contributed by that member SHALL include the lactation supplement (+330 kcal for 0-6 months)

#### Scenario: AKG met across all eight nutrients
- **WHEN** the `Paling Seimbang` plan is returned with feasibility
- **THEN** for each of the eight tracked nutrients, the plan total SHALL be ≥ the household-summed AKG requirement

### Requirement: Sub-500ms Sensitivity Re-Solve
The system SHALL accept a sensitivity request consisting of an existing plan request plus a price-shock vector (ingredient → multiplier) and a budget delta. The system SHALL re-solve the three single-objective ILPs with the mutated inputs and return the new plans within 500ms p95 on the project VPS.

#### Scenario: Cabai price shock re-solve
- **WHEN** the user submits a sensitivity request with `price_shock: {cabai_merah: 1.5}` against a previously feasible plan
- **THEN** the system SHALL return three updated plans within 500ms p95
- **AND** the plans MAY substitute cabai with a lower-priced equivalent
- **AND** the response SHALL include a `baseline_plan_hash` matching the hash of the baseline request

### Requirement: Infeasibility Transparency Report
When no plan satisfies the AKG constraints under the given budget, allergies, and dietary law, the system SHALL return a structured infeasibility report identifying which nutrients fail, by what margin, and the minimum budget delta required to restore feasibility holding all other constraints fixed.

#### Scenario: Insufficient budget for iron
- **WHEN** a household requires 50mg iron/day total but the budget caps iron-rich food intake at 38mg
- **THEN** the response SHALL be `{ "feasible": false, "failing_nutrients": [{"name": "iron", "achieved": 38, "required": 50, "gap": 12}], "minimum_budget_delta_rupiah": <integer ≥ 0> }`
- **AND** no partial plan SHALL be returned that fails AKG

#### Scenario: Multi-nutrient failure ranked by gap
- **WHEN** both iron and vitamin A are infeasible under budget
- **THEN** the `failing_nutrients` array SHALL list both, sorted by `gap / required` ratio descending

### Requirement: Deterministic Reproducibility
Given identical inputs (household profile, budget, region, restrictions, price snapshot version, AKG version), the system SHALL return byte-identical plan outputs across runs.

#### Scenario: Same inputs yield same plans
- **WHEN** the same `/v1/optimize` request is submitted twice within the same deployment
- **THEN** the response bodies SHALL be byte-identical
- **AND** the `plan_hash` field in the response SHALL match across both runs
