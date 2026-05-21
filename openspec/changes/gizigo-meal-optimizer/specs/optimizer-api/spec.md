## ADDED Requirements

### Requirement: Optimize Endpoint
The system SHALL expose `POST /v1/optimize` accepting JSON `{ household: HouseholdProfile, budget_rupiah: int, region: string, restrictions: { halal?: bool, allergies?: string[] } }` and returning JSON `{ plans: [Plan, Plan, Plan] | null, infeasibility?: InfeasibilityReport, plan_hash: string, request_id: string, solver_ms: int }`.

#### Scenario: Successful optimize request
- **WHEN** a valid `POST /v1/optimize` is received
- **THEN** the system SHALL respond with HTTP 200 within 1 second p95
- **AND** the body SHALL contain three plans OR an infeasibility report (never both)
- **AND** the `plan_hash` SHALL be a deterministic SHA-256 of the canonicalized inputs and outputs

#### Scenario: Validation rejects malformed body
- **WHEN** `budget_rupiah` is missing or non-positive
- **THEN** the system SHALL respond HTTP 422 with `{ error_code: "INVALID_BUDGET", field: "budget_rupiah", message: <Bahasa Indonesia message>, request_id }`

#### Scenario: Plan cache hit
- **WHEN** an identical optimize request is submitted within the same deployment
- **THEN** the system SHALL return the persisted response with `cache: true` in metadata
- **AND** the response time SHALL be ≤ 50ms p95

### Requirement: Sensitivity Endpoint
The system SHALL expose `POST /v1/sensitivity` accepting `{ baseline_request: OptimizeRequestBody, price_shock?: { [ingredient_id: string]: float }, budget_delta_rupiah?: int }` and returning the same response shape as `/v1/optimize` plus `{ baseline_plan_hash: string }`.

#### Scenario: Apply price shock and re-solve
- **WHEN** a sensitivity request shocks `cabai_merah` by 1.5
- **THEN** the system SHALL solve with the mutated price and respond within 500ms p95
- **AND** the `baseline_plan_hash` SHALL match the hash of the baseline request

### Requirement: Humanize Endpoint
The system SHALL expose `POST /v1/humanize` accepting `{ plan: Plan, household: HouseholdProfile }` and returning `{ recipes: [Recipe], humanization_mode: "templated" | "llm", validation?: ValidationReport }`. The default `humanization_mode` SHALL be `templated` unless the LLM feature flag is enabled and validation passes.

#### Scenario: Successful humanization
- **WHEN** a valid plan is submitted
- **THEN** the response SHALL include one recipe per meal slot present in the plan
- **AND** `humanization_mode` SHALL be `templated` or `llm`

### Requirement: Health Endpoint
The system SHALL expose `GET /v1/health` returning `{ status: "ok", version: <semver>, data_versions: { tkpi: <hash>, akg: <hash>, prices: { <region>: <iso_date> } }, solver: "cbc", uptime_s: int }`.

#### Scenario: Health check reports data versions
- **WHEN** `/v1/health` is called
- **THEN** the response SHALL include checksums for the loaded TKPI catalog and AKG reference, plus a per-region price-snapshot date

### Requirement: CORS Configuration
The system SHALL allow CORS for the configured front-end origin via the `CORS_ALLOWED_ORIGIN` environment variable. Preflight `OPTIONS` requests SHALL be handled correctly for all `/v1/*` routes.

#### Scenario: CORS allows the configured front-end
- **WHEN** the configured origin sends a preflight `OPTIONS /v1/optimize`
- **THEN** the system SHALL respond with `Access-Control-Allow-Origin` matching the configured origin

### Requirement: Structured Error Envelope
All error responses (4xx, 5xx) SHALL share the schema `{ error_code: string, message: string, request_id: string, details?: object }`. Error codes SHALL be SCREAMING_SNAKE_CASE and stable across releases.

#### Scenario: 5xx surfaces request_id
- **WHEN** the solver crashes on an internal exception
- **THEN** the response SHALL be HTTP 500 with `error_code: "SOLVER_FAILURE"` and a `request_id` traceable in server logs

### Requirement: Persistence Of Plan Cache
The system SHALL persist every successful `/v1/optimize` response in Postgres table `plans(plan_hash PRIMARY KEY, request_json JSONB, response_json JSONB, created_at TIMESTAMPTZ DEFAULT now())`. Identical-input requests SHALL be served from the cache.

#### Scenario: Cache write on first solve
- **WHEN** an optimize request is solved for the first time
- **THEN** a row keyed on `plan_hash` SHALL be written to the `plans` table
- **AND** the `response_json` column SHALL store the canonical response body

### Requirement: OpenAPI Documentation
The system SHALL serve OpenAPI 3.1 schema at `/openapi.json` and a Swagger UI at `/docs`. Every endpoint, request body, and response body SHALL have a schema.

#### Scenario: OpenAPI is reachable
- **WHEN** a reviewer fetches `/openapi.json`
- **THEN** the document SHALL include `paths` for `/v1/optimize`, `/v1/sensitivity`, `/v1/humanize`, `/v1/health`
