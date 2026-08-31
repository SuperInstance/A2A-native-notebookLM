# Discussion Leader Round 1 — 2026-08-21

## 1. The Riverbed Vision
The deeper unifying mathematical structure is a **time-indexed von Mises–Fisher (vMF) random field on the 7-dimensional sphere of standardized dial readings** (S⁶). This structure fully unifies all components of the elephant/JEPA workstream:
- Room fields are single-time vMF snapshots of the collective dial readings.
- Field edges are the temporal gradient of the field's sufficient statistics (mean direction μ̂, concentration κ, local drift Δμ̂).
- Premise bands are hysteretic thresholds on the ratio of idiosyncratic reader offset (μ̂ - b̄) to local drift (Δμ̂).
- Hysteresis is a state machine over these thresholds, enforcing stasis within statistical deadbands.
- The ledger/persistence tracks the state of this dynamical system over time.

The codebase is a discretized, windowed inference pipeline for this field, with registered statistical tests for structured signal detection.

## 2. The Seams
The current code shows its patched-together nature in six key places:
1. **Window-referent ambiguity**: The code uses a window-center speak-position referent for crossing timing statistics, but the design doc notes that a window-start referent produces arithmetically different results, with the start-referent value only labeled as a sensitivity test — no formal framework exists for choosing between them.
2. **Static-ratio-as-artifact seam**: The 0.3/0.6 premise score kill band is a hard-coded global threshold, but the design doc proves this is actually a phase-averaged value: clear in stable strata (idiosyncrasy ≫ drift) and kill at room steps (drift spikes). The code treats this as a universal threshold rather than a dynamical function of field phase.
3. **Dual warming seam**: The code uses two inconsistent warmth metrics: `RoomField.warmth()` (direct linear projection of raw dial readings) and `warmth_vmf` (projection of the vMF mean direction onto the fixed warm vector) — these are not formally linked, leading to conflicting temperature readings.
4. **Reader-seam ambiguity**: The nurse JEPA doctrine requires modeling two levels of JEPA (room field + reader baseline deviations), but the current code either treats readers as part of a global population mean or isolated idiosyncrasies, with no unified hierarchical framework for reader-specific drifts.
5. **Hard-coded hysteresis seam**: The hysteresis margin (0.05) and hold count (3 windows) are hard-coded ad-hoc constants, not derived from the field's detection theory or statistical uncertainty.
6. **Temporal/static disconnection**: The code computes both static premise scores per night and temporal trajectories per window, but no formal unifying link exists between them — the continuity ladder is an afterthought rather than part of the core structure.

## 3. The Agenda
Five sharply-posed mathematical problems for the team:

### Problem 1: Formalize vMF Field Temporal Gradients as Edge Detection
**Statement**: Derive a formal definition of field edges as the temporal gradient of the vMF field's sufficient statistics (μ̂, κ, Δμ̂), with detection thresholds tied directly to the field's noise floor (from vmf.py's jackknife SE(μ̂) and bootstrap CI for κ).
**Why it matters**: Current edge detection is a patched-over heuristic with no formal link to the underlying vMF field — this unification would make edges a principled part of the field's dynamical system.
**Solution outcome**: A paper deriving the gradient of vMF sufficient statistics, with detection thresholds replaced hard-coded hysteresis constants. The solution would align edge detection with the field's statistical uncertainty.

### Problem 2: Unify Static Premise Ratio and Temporal Trajectory
**Statement**: Prove that the static premise score (RMS_R o_R / mean_R d_R) is the time-average of the temporal premise trajectory R(t) over a stable stratum, with phase-dependent corrections for window size and stride.
**Why it matters**: The current code treats static and temporal scoring as separate ad-hoc computations, but the design doc shows the static ratio is a phase-average of the temporal trajectory — this unification would make premise scoring a direct part of the field's inference pipeline.
**Solution outcome**: A mathematical proof linking static and temporal scoring, replacing the continuity ladder with a formal, core part of the foundation rather than an afterthought check.

### Problem 3: Model Hierarchical Reader Baselines as a JEPA of a JEPA
**Statement**: Formalize the reader-seam as a two-level vMF field: the first level is the collective room field, the second level is a vMF field over each reader's deviation from their own baseline drift. Derive inference pipelines for this two-level field.
**Why it matters**: The nurse JEPA doctrine requires modeling two levels of JEPA, but the current code lacks a formal framework for this — this would unify reader-specific deltas with the collective room field.
**Solution outcome**: A mathematical definition of the two-level vMF field, with inference pipelines for estimating both the collective room field and each reader's baseline deviation. The solution would replace ad-hoc reader handling with a formal hierarchical model.

### Problem 4: Resolve Window-Referent Ambiguity
**Statement**: Derive a principled choice of speak-position referent for crossing timing statistics, tied directly to the field's causal structure (the time at which a room transition is actually detectable).
**Why it matters**: The current code uses an ad-hoc window-center referent, with no formal basis for choosing between it and the window-start referent noted in the design doc.
**Solution outcome**: A formal analysis of causal timing relative to windowed measurements, deriving the optimal referent for crossing statistics. The solution would replace the ad-hoc choice with a principled one tied to the field's causal structure.

### Problem 5: Formalize Hysteresis as a Dynamical State Machine Over Detection Uncertainty
**Statement**: Derive hysteretic band-state machines as a dynamical system over the field's detection uncertainty (probability a crossing is real signal vs noise), with transition probabilities tied to the field's signal-to-noise ratio.
**Why it matters**: Current hysteresis constants are hard-coded ad-hoc values, with no formal link to the field's statistical uncertainty — this would make hysteresis a principled part of the field's dynamical system.
**Solution outcome**: A mathematical definition of hysteresis tied to the field's noise floor, replacing hard-coded margins/hold counts with thresholds derived from the field's statistical properties.

## 4. Discussion Rules
All disagreements and evaluations must follow these principles:
1. **Generative over descriptive**: A good foundation is one from which the *entire codebase can be derived*, not just explained. For example, premise band scoring must follow directly from the vMF field's temporal dynamics, not be a patched-over add-on.
2. **Formal disagreement tied to structure**: Disagreements must be rooted in gaps in the mathematical foundation, not personal preference. For example, arguing about window referents is only valid if tied to causal structure or detection theory.
3. **Ad-hoc constants must be derived**: All hard-coded values (hysteresis margins, window sizes, score thresholds) must be derivable from the foundation's parameters, not arbitrary choices.
4. **Full unification requirement**: A valid foundation must unify *all* components of the workstream (vMF fields, edges, deltas, hysteresis, premise bands, ledger) — partial unification is insufficient.
5. **Principled testing over thresholds**: All statistical tests and thresholds must be derived from the foundation's mathematical structure, not hard-coded ad-hoc values.

## Summary of Riverbed Vision
1. The riverbed is a time-indexed von Mises–Fisher random field over the 7-dimensional sphere of standardized dial readings.
2. Room fields are single-time vMF snapshots; edges are temporal gradients of their sufficient statistics.
3. Premise bands are hysteretic thresholds on idiosyncrasy/drift ratios; the ledger tracks state over these thresholds.
4. The entire codebase is a discretized inference pipeline for this field, with registered tests for structured signal detection.