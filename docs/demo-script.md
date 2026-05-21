# Demo Script (≤ 3-minute video, captions-only)

Live URL: **https://gizigo.jmola.my.id**
Code: **(repo URL — pasted into Devpost when public)**

Target: 1920×1080 H.264, ≤ 200 MB, captions-only (no voiceover), runs muted on Devpost preview.

---

## Recording plan

Six shots, each with a caption that appears as on-screen text. Caption font: any clean sans (Plus Jakarta Sans, Inter, or system-ui). Caption position: lower-third, semi-transparent dark backdrop.

### Shot 1 — Hero hook (0:00 → 0:15)

**Caption (visible 4 s, then fade)**

> Indonesia: 21.6 % of children under five are stunted (SSGI 2024).
> RPJMN target by 2029: 14 %.
> Most families don't lack knowledge — they lack a way to turn today's budget into the most nutritious plate.

**On-screen**: blank green background → fade to live app.

### Shot 2 — Persona 1 / Bu Sari (0:15 → 1:00)

**Action sequence**:

1. Open https://gizigo.jmola.my.id
2. Click the **"Bu Sari's Family (4 members, Rp 60k/day)"** persona chip.
3. Slow pan over the four-member form so the AKG categories are readable.
4. Click **"Calculate Plan"**.
5. Three plan cards render in under a second.

**Captions** (one at a time, each on screen ~5 s):

> Bu Sari, husband, lactating mother, child 5 yrs, toddler. Rp 60,000 a day.

> ILP solver: PuLP + CBC. Three optimal plans. Less than a second.

> All eight tracked AKG nutrients hit at Rp 56,731. Under budget, seven food groups.

### Shot 3 — Sensitivity slider (1:00 → 1:30)

**Action**:
1. Click the **"Chili +50%"** preset chip.
2. The cost-delta pill updates.
3. Drag the global slider from 0 % → +50 % → -10 %.
4. Pause on the new total.

**Captions**:

> What if chili prices jump 50 %? Full LP re-solve, not extrapolation.

> Cost delta is the actual new optimum.

### Shot 4 — Persona 2 / Extreme Budget (1:30 → 2:15)

**Action**:
1. Click the **"Extreme Budget (5 members, Rp 25k/day)"** chip.
2. Click **Calculate Plan**.
3. The InfeasibilityPanel renders:
   - Estimated minimum budget: **Rp 57,000-63,000** (depending on persona shape)
   - Deficits: energy, protein, vitamin A, calcium
4. Click **"Raise to minimum budget"**.
5. Plans appear at the new budget.

**Captions**:

> Five-person family, Rp 25,000. Optimizer runs a budget bisection.

> Honest answer: this budget cannot meet AKG. Minimum is the value shown.

> One tap raises to the minimum. The LP cannot lie about feasibility.

### Shot 5 — Recipe drawer (2:15 → 2:45)

**Action**:
1. Click **"Recipe"** on the *Most Balanced* card.
2. Drawer slides in showing meal-by-meal narration (Breakfast / Lunch / Dinner / Snack).
3. Press ESC to close.

**Captions**:

> Each plan opens into recipes. Cooking methods come from a hand-curated YAML.

> Optional LLM path exists, gated by a validator that re-extracts grams. Default off, deterministic.

### Shot 6 — Architecture and close (2:45 → 3:00)

**On-screen**: cut to `docs/architecture.svg`.

**Caption**:

> FastAPI + PuLP + CBC, Vite + React 18 + Tailwind. Live at gizigo.jmola.my.id.

> Built solo over a 36-hour hackathon. Code on GitHub. Thank you.

---

## OBS configuration (recommended)

**Scene Setup**

- Source 1: **Window Capture** → your browser window.
- Source 2: **Image Source** → `docs/architecture.svg` (only enabled for shot 6).
- Source 3: **Text (FreeType 2)** for the captions, parented to a 50 % opacity black `#000000A0` rectangle behind it (lower-third, height ~100 px).

**Output Settings**
- Output mode: **Advanced**
- Encoder: **x264** (or **Apple VT H.264** on macOS for hardware accel).
- Rate control: **CRF 22**.
- Keyframe interval: 2.
- Profile: **high**, tune: **none**.
- Format: **MKV** (recover from crashes), then convert.

**Video Settings**
- Base & Output Resolution: **1920×1080**.
- FPS: **30**.

**Recording flow**
1. Start a fresh browser profile (no extensions, no toolbars).
2. Zoom to **110 %** so the AKG bars are readable.
3. Hide bookmarks bar (Cmd+Shift+B).
4. Run a warm-up `curl https://gizigo.jmola.my.id/v1/health` so the catalog is in cache.
5. Start the OBS recording, perform the six shots in order, stop when shot 6 finishes.
6. Caption text gets toggled on/off via the Source visibility hotkey between shots.

## Render and upload

Convert MKV → MP4 with libx264 (faststart for streaming previews):

```bash
ffmpeg -i raw.mkv \
       -c:v libx264 -preset slow -crf 22 \
       -an \
       -movflags +faststart \
       gizigo-demo.mp4
```

Target file size: **30-60 MB** (well under the Devpost 200 MB cap). `-an` strips any silent audio track.

**Upload**: YouTube as **Unlisted**. Paste the URL into the Devpost submission body. Keep `raw.mkv` archived locally for re-cuts.

## Pre-flight checklist

- [ ] Browser at 110 % zoom, 1920×1080 viewport
- [ ] DevTools closed
- [ ] No notifications visible
- [ ] `/v1/health` warmed (catalog loaded)
- [ ] OBS scene tested with one short take
- [ ] Captions tested for readability over green and amber backgrounds
- [ ] All six shots rehearsed at least once

## Last-resort fallback

If recording goes sideways, the code-side ship is still complete: live URL, README with screenshots, all docs, and the OpenSpec change. A static submission with no video will still hit *Innovation & Creativity*; the video boosts *Presentation and Documentation*.
