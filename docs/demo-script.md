# Demo Script (3-minute video)

Live URL: **https://gizigo.jmola.my.id**
Code: **(repo URL)** — public on submission.

The video must run **between 2:00 and 3:00 minutes** to fit Devpost's 2-5 minute window comfortably while staying engaging. Aspect ratio: 1920×1080 H.264, ≤ 200 MB.

---

## Shot 1 — Hero hook (0:00 → 0:15)

**On-screen**: Title card

> "GiziGo
> Operations-research meal planning against Indonesian childhood stunting.
> 21.6 % of children under five — RPJMN target 14 %."

**Voiceover**:

> "21.6 % of Indonesian children under five are stunted. Most of those families don't lack knowledge — they lack a way to turn whatever budget they have today into the most nutritious plate they can buy. That is what GiziGo solves."

## Shot 2 — Persona 1 (Bu Sari, feasible) (0:15 → 1:00)

**Action**:
1. Open https://gizigo.jmola.my.id
2. Click the **"Keluarga Bu Sari (4 anggota, Rp 60k)"** persona chip.
3. Pause one beat — pan over the form to show the four members and budget.
4. Click **"Hitung Rencana"**.
5. Three plan cards appear within 1 second.

**Voiceover**:

> "Bu Sari's family — her husband, herself nursing a baby, a 5-year-old, and a toddler — has 60 thousand Rupiah a day. We pick the persona, hit *Hitung*, and within a second the optimizer returns three plans: cheapest, balanced, and most varied. The cheapest covers all eight tracked AKG nutrients within Rp 56,731 — under budget, with seven different food groups."

**On-screen highlight**: The 8 AKG bars on each PlanCard, each ≥ 100 %.

## Shot 3 — Sensitivity slider (1:00 → 1:30)

**Action**:
1. Click **"Cabai +50%"** preset chip.
2. The badge updates with `Δ Biaya: +Rp ...`.
3. Slide the global percentage slider from 0 to +50 %, then back to -10 %.
4. Pause on the new total.

**Voiceover**:

> "What happens when chili prices jump 50 %? GiziGo re-solves the entire LP under the new prices. The new total appears in real time — not a linear extrapolation, an *actual re-optimisation*. Slide back, prices return, plans return."

## Shot 4 — Persona 2 (Anggaran Ekstrem, infeasible) (1:30 → 2:15)

**Action**:
1. Click the **"Anggaran Ekstrem (5 anggota, Rp 25k)"** chip.
2. Click **Hitung Rencana**.
3. The InfeasibilityPanel renders, showing:
   - Anggaran minimum perkiraan: Rp 63,000
   - Deficit nutrients: energi, protein, vitamin A, kalsium
4. Click **"Naikkan ke anggaran minimum"**.
5. Three plans render at the new budget.

**Voiceover**:

> "Now the harder case. Five-person family, Rp 25,000 a day. The optimizer runs a budget bisection and returns the truth: this budget cannot meet AKG. The minimum required is Rp 63,000, the deficit is concentrated in energy, protein, vitamin A, and calcium. One tap raises the budget — and the plans appear. That is the difference between an LLM that 'tries its best' and a linear program that *cannot lie*."

## Shot 5 — Recipe drawer + close (2:15 → 2:45)

**Action**:
1. Click **"Lihat Resep"** on the *Paling Seimbang* card.
2. The drawer slides in showing meal-by-meal narration.
3. Press ESC to close.

**Voiceover**:

> "Each plan opens into a meal-by-meal recipe — sarapan, makan siang, makan malam, kudapan — generated from a hand-curated cooking-method map. That keeps the demo deterministic and the gram counts honest. An LLM path exists behind a feature flag, with a post-render validator that rejects any narration that drifts from the optimizer's gram amounts."

## Shot 6 — Architecture and close (2:45 → 3:00)

**On-screen**: A clean architecture diagram (web → FastAPI → Postgres + ILP).

**Voiceover**:

> "Built solo over a 36-hour hackathon. FastAPI plus PuLP plus CBC behind a Vite React app, all live at gizigo.jmola.my.id. Code on GitHub, README maps directly to the rubric. Thank you."

---

## Recording checklist

- [ ] OBS scene at 1920×1080, 30 fps, H.264, AAC audio at 192 kbps
- [ ] Browser zoomed to 110 % so AKG numbers are readable
- [ ] Hide bookmarks bar, switch to a clean profile
- [ ] DevTools closed
- [ ] Cursor visible, click highlight enabled
- [ ] Voiceover recorded separately, mixed in post (Audacity)
- [ ] Background noise gate at -30 dB

## Render and upload

```bash
ffmpeg -i raw.mkv -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 192k \
       -movflags +faststart gizigo-demo.mp4
```

Target file size: **40-80 MB** (well under the Devpost 200 MB cap). Upload to YouTube as **Unlisted**, paste the URL into the Devpost submission. Keep the source `.mkv` archived locally in case we re-cut.
