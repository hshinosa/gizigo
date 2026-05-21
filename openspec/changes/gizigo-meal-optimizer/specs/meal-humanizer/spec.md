## ADDED Requirements

### Requirement: Templated Bahasa Indonesia Rendering As Default
The system SHALL render every plan using a deterministic templated Bahasa Indonesia recipe per meal slot. The templated path is the required and default behavior. It SHALL produce one recipe block per meal slot, list each ingredient with grams, and include a per-member portioning hint computed from AKG-weighted shares.

#### Scenario: Plan converted to recipes per meal slot
- **WHEN** the humanizer receives a plan with three meal slots and 9 ingredients total
- **THEN** the response SHALL contain three `recipe` blocks keyed by meal slot
- **AND** every `ingredient_id` from the input SHALL appear in exactly one recipe block
- **AND** the cumulative `grams` per ingredient across recipes SHALL equal the input grams exactly

#### Scenario: Templated output is byte-stable
- **WHEN** the same humanize request is submitted twice in templated mode
- **THEN** the responses SHALL be byte-identical
- **AND** the response metadata SHALL include `humanization_mode: "templated"`

### Requirement: Optional LLM Enrichment Via Configured Gateway
The system SHALL optionally call a configured OpenAI-compatible HTTP endpoint (`OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`) to produce a more natural-sounding rendering. The LLM call SHALL use temperature 0.2 and a 6-second timeout. The LLM upgrade is gated behind a feature flag and SHALL be skipped if the gateway is unreachable or returns a non-2xx response.

#### Scenario: LLM upgrade applied when gateway is healthy
- **WHEN** the feature flag `humanizer.llm_enabled` is true and the gateway responds 200 within timeout
- **THEN** the system SHALL return the LLM-rendered text
- **AND** the response metadata SHALL include `humanization_mode: "llm"` if validation passes

#### Scenario: Gateway failure falls back to templated
- **WHEN** the gateway returns a non-2xx response or times out after 6s
- **THEN** the system SHALL emit the templated rendering
- **AND** metadata SHALL include `humanization_mode: "templated"` and `humanization_failure_reason`

### Requirement: Quantitative Validation Of LLM Output
The system SHALL post-validate every LLM-rendered response by re-parsing recovered ingredient quantities from the rendered text and comparing them against the source plan. If any ingredient's recovered grams differ from source by >5% or any source ingredient is missing from the rendered text, the system SHALL discard the LLM output and emit the templated rendering.

#### Scenario: LLM hallucination triggers fallback
- **WHEN** the LLM omits an ingredient that appears in the source plan
- **THEN** the post-validator SHALL detect the missing ingredient
- **AND** the system SHALL emit the templated rendering instead
- **AND** the response metadata SHALL include `humanization_mode: "templated"` and the validation diff

#### Scenario: Drift within tolerance accepted
- **WHEN** every ingredient in the LLM output is within ±5% of source grams
- **THEN** the system SHALL return the LLM output
- **AND** metadata SHALL include `humanization_mode: "llm"`

### Requirement: Indonesian Localization
All user-facing humanized text SHALL be in Bahasa Indonesia. Cooking verbs SHALL be drawn from a fixed vocabulary (`tumis`, `rebus`, `kukus`, `goreng`, `sangrai`). Meal-slot labels SHALL be `sarapan`, `makan siang`, `makan malam`, `cemilan`. Numeric quantities SHALL be rendered in metric (g, ml).

#### Scenario: Bahasa Indonesia output
- **WHEN** any humanizer response is rendered
- **THEN** every recipe step and label SHALL be in Bahasa Indonesia
- **AND** every cooking verb used SHALL appear in the fixed vocabulary

### Requirement: Hand-Curated Substitution Hints
The system SHALL load a hand-curated `data/substitutes.yaml` mapping each of at least 30 common Indonesian ingredients to one or more substitute `ingredient_id`s with a substitution reason. When the user marks an ingredient as locally unavailable, the humanizer SHALL surface up to three substitutes from this table.

#### Scenario: Cabai unavailable, substitutes returned
- **WHEN** the user marks `cabai_merah_keriting` as unavailable
- **THEN** the recipe drawer SHALL display up to three substitutes from `data/substitutes.yaml`
- **AND** each substitute SHALL include its display name and the substitution reason
