## ADDED Requirements

### Requirement: Single-Page Vite + React Plan Builder
The system SHALL provide a single-page Vite + React + Tailwind interface where the user enters a household profile, selects a region, sets a budget, declares restrictions, and receives three Pareto plans without a page reload. The interface SHALL be usable on a 360px-wide mobile viewport and a 1440px desktop viewport.

#### Scenario: Build a plan end-to-end without reload
- **WHEN** the user fills the household form, picks a region, sets budget, and clicks "Buatkan Rencana"
- **THEN** the three plan cards SHALL appear in the same view within 1.5 seconds p95
- **AND** the URL SHALL NOT navigate

#### Scenario: Mobile viewport renders plan cards stacked
- **WHEN** the viewport is 360px wide
- **THEN** plan cards SHALL stack vertically with full-width controls

### Requirement: Three-Plan Pareto Card Layout
The system SHALL render the three returned plans (`Termurah`, `Paling Seimbang`, `Paling Beragam`) as adjacent cards on desktop and stacked cards on mobile. Each card SHALL display total cost in Rupiah, an AKG-adequacy bar chart for the eight tracked nutrients, and a meal-slot accordion listing ingredients with grams.

#### Scenario: Card displays AKG adequacy at a glance
- **WHEN** plan cards render
- **THEN** every card SHALL show eight horizontal bars, one per tracked nutrient, normalized so 100% = AKG met
- **AND** values >100% SHALL be visually distinct from values <100% without relying on color alone

#### Scenario: Accordion reveals ingredients
- **WHEN** the user expands the `Sarapan` accordion on a card
- **THEN** the listing SHALL show each ingredient name in Bahasa Indonesia, grams, and a per-member portion suggestion

### Requirement: Live Sensitivity Slider And Two Preset Shocks
The system SHALL provide a budget slider and two preset price-shock chips (`Cabai +50%`, `Telur −10%`). Slider drag SHALL re-issue a `/v1/sensitivity` request with debounce ≤ 200ms. Plan cards SHALL update within 500ms p95 of the network response.

#### Scenario: Drag budget slider triggers re-solve
- **WHEN** the user drags the budget slider from Rp 80,000 to Rp 50,000
- **THEN** within 200ms of release the front-end SHALL issue `/v1/sensitivity`
- **AND** within 500ms of receiving the response the cards SHALL update

#### Scenario: Toggle "cabai +50%" updates plans
- **WHEN** the user toggles the `cabai +50%` chip
- **THEN** the system SHALL re-solve with that price shock applied
- **AND** any plan that substitutes cabai SHALL visually indicate the substitution with a small badge on the affected ingredient row

### Requirement: Infeasibility Transparency Panel With Action
When the API returns an infeasibility report, the system SHALL render a dedicated panel listing each failing nutrient, the achieved-vs-required gap, and the minimum budget delta required. The panel SHALL include a one-click button "Naikkan budget ke Rp X" that auto-applies the suggested delta and triggers a fresh optimize request.

#### Scenario: Infeasibility shown with action
- **WHEN** the API returns an infeasibility report
- **THEN** the panel SHALL list every failing nutrient with progress bars
- **AND** the "Naikkan budget" button SHALL set the slider to the suggested amount and trigger a new optimize call

#### Scenario: Plan cards hidden during infeasibility
- **WHEN** the API returns an infeasibility report
- **THEN** no plan card SHALL be rendered alongside the panel

### Requirement: Two Demo Personas
The system SHALL ship two pre-configured demo personas accessible from a "Coba Persona" menu: `Keluarga Bu Sari (4 anggota, Rp 60k/hari, DKI Jakarta)` (intentionally feasible) and `Anggaran Ekstrem (5 anggota, Rp 25k/hari, national-baseline)` (intentionally infeasible). Selecting a persona SHALL fully populate the form and trigger the live optimizer.

#### Scenario: Persona populates the form
- **WHEN** the user selects "Keluarga Bu Sari"
- **THEN** the household form SHALL fill with 4 members at the specified ages
- **AND** the optimizer SHALL run and display three plans within 2 seconds

#### Scenario: Extreme-budget persona surfaces infeasibility
- **WHEN** the user selects "Anggaran Ekstrem"
- **THEN** the system SHALL render the infeasibility panel with the failing-nutrients list

### Requirement: Recipe Drawer
Clicking a meal-slot ingredient SHALL open a side drawer rendering the humanized recipe for that meal slot, including per-member portions, cooking steps in Bahasa Indonesia, and a substitute-suggestion list.

#### Scenario: Open recipe drawer
- **WHEN** the user clicks the `Sarapan` ingredient row
- **THEN** the drawer SHALL slide in showing the humanized recipe text and substitution chips
- **AND** the drawer SHALL be dismissible by ESC, backdrop click, and a close button

### Requirement: Bahasa Indonesia Copy And Basic Accessibility
All visible UI strings SHALL be in Bahasa Indonesia. Body-text contrast SHALL meet WCAG 2.1 AA (≥ 4.5:1). Interactive controls SHALL be operable by keyboard alone. Form fields SHALL have associated labels.

#### Scenario: Keyboard-only flow
- **WHEN** a user navigates the page using only Tab, Shift+Tab, Enter, and arrow keys
- **THEN** they SHALL be able to fill the household form, set budget, run optimize, and open the recipe drawer
- **AND** focus indicators SHALL be visible on every focusable element

#### Scenario: All copy is Bahasa Indonesia
- **WHEN** any view renders
- **THEN** every visible string SHALL be in Bahasa Indonesia
- **AND** date/number formatting SHALL use `id-ID` locale
