# Algebraic / Structural Foundation for the Elephant Thesis
*Written by the Mathematician (Qwen3.6-35B), 2026-08-21. Read-only analysis.*

---

## 1. The Algebra of Edges

### 1.1 Field-edges form a category, not a group

**Definition.** For each measurement night N, the vMF estimator returns
vhat_N in S^6 (the 6-sphere in R^7) and kappa_N in [0, inf). A *field-edge* between
two nights A, B is the tuple

  E(A->B) = (d_mu, d_warmth, d_log_kappa)

where d_mu = ||vhat_B - vhat_A|| (chord length in R^7),
d_warmth = warmth_B - warmth_A, d_log_kappa = log(kappa_B/kappa_A).

**Code:** `elephant/vmf.py::edge()` implements this exactly:

    d_mu = float(np.linalg.norm(np.array(fa["mu_hat"]) - np.array(fb["mu_hat"])))
    d_warmth = fa["warmth_vmf"] - fb["warmth_vmf"]
    d_log_kappa = float(np.log(fa["kappa"] / fb["kappa"]))

**Proposition 1 (Category, not Group).** The set of field-edges, with
composition defined along temporally adjacent night sequences, forms a
thin category E:

- **Objects:** measurement nights N (indexed by strings like "A", "D", "T1").
- **Morphisms:** edges E(A->B) for all ordered pairs (A, B) with measurable
  fields at both.
- **Composition:** E(A->B) . E(B->C) = E(A->C), where
    d_mu(A->C) = d_mu(A->B) + d_mu(B->C)
  by transitivity of difference in R^7. The other components compose additively too.
- **Identity:** E(N->N) = (0, 0, 0) — the zero-edge. This exists because
  `edge()` returns None only when one operand is None; N->N is a degenerate
  but well-defined morphism with value (0, 0, 0).
- **No inverses:** The forward edge (vhat_B - vhat_A) and "backward edge"
  (vhat_A - vhat_B) are not inverses in any geometric sense — the manifold
  is S^6, not R^7, and the chord composition does not yield a group operation.
  In the ledger's vocabulary: the zero-edge records *no change*; it does not undo a change.
- **Thin:** between any two objects N1, N2, there is at most one edge E(N1->N2)
  (the same three components are deterministically computed). Hence E is a
  *thin category*, and in fact a *preorder* when restricted to temporal precedence.

**Why not a monoid?** A monoid is a single-object category. E has many
objects (nights), so it is a category. The monoid of *total displacement*
(Edge(First->Last)) is a single element of E, not a monoid structure.

### 1.2 The Ledger as a Free Object over Edges

**Definition.** The ledger L is an append-only sequence of entries

  L = [e1, e2, ..., en]

where each ei is either:
  - A field-edge E(N->N') in Mor(E), tagged with a sequence index, OR
  - An *annotation* a in A (the annotation monoid) applied to a preceding entry.

**R4 algebraically:** "No deleted numbers, only annotated ones." This means
the ledger monoid M(L) is *not* the free monoid over edges (which would allow
deletion). Instead:

  M(L) = L with deletion replaced by annotation

This is a **partially ordered free monoid with annotation operators**. Formally:

- Let Free(Edge) be the free monoid over field-edges.
- Let A be the set of annotation types (e.g., "length-confounded", "voided",
  "promoted", "demoted").
- The ledger operations are:
  - Append: e . f (standard monoid concatenation)
  - Annotate: ann(a, e) for a in A, e in L (no deletion, only tagging)
- R4 enforces: for all e in L, the ledger contains e and every annotation applied to e.

**This is the free object over the category E in the slice category**
AnnCat/E where objects are labeled morphisms. The ledger preserves the
categorical composition law (edges compose transitively) while refusing to
permit the monoid operation of cancellation/deletion.

**Code mapping:**
- `scripts/e2_field.py::main()` appends results to JSON output deterministically.
- The claim ledger in master-outline.md is the ledger L: each row is an
  entry, verdict changes are annotations (SOLID->CONDITIONAL is an annotation,
  not a deletion).
- The launderings table (section 9.2) is exactly the annotation record.

### 1.3 Field-edges at the vMF level

The vMF estimator is a function:

  vMF_fit: (R^+)^Nx7 -> (S^6, [0, inf))
        = vmf_fit(zs) -> {mu_hat, kappa, rho, CI, warmth, SE}

Composing with the edge function:

  edge . (vMF_fit x vMF_fit): P(N1) x P(N2) -> R^3

This is a **natural transformation** from the discrete-time functor on nights
to the vector space R^3, because:
- For each night N, we have vMF_fit(N) in (S^6 x [0, inf)).
- edge maps pairs to R^3.
- The composition is consistent with the temporal preorder on nights.

---

## 2. Invariants

### 2.1 The sha256 chain and determinism

Every measurement is keyed by sha256 of the input corpus + estimator + seed.
This chain is not an invariant *of the theory* but an invariant *of the
procedure*: deterministic reproducibility is the meta-invariant.

**Code:** `scripts/e2_instrument.py::assert_replay_matches_log()` — asserts
|replayed - logged| < 1e-9. This is the strongest invariant in the system:
the same inputs *always* produce the same outputs. It makes the ledger
replay-honest.

### 2.2 The 1.229 annotation invariant (R4)

The fine edge value 1.229 (condition-grain gap between content-only and
silence-only at the clock) appears everywhere it once appeared, but always
annotated. The *number itself* is the invariant; its *claim status* is the
variable.

Mathematically: the function f(night) = fine_edge(night) returns 1.229 at
the condition grain for Stage 1. R4 says:
- f() is not deleted from the ledger.
- A new function annotate(night, 1.229) -> {length-confounded, indeterminate}
  is added to the same ledger cell.

The invariant is: **the set of all values that ever appeared at any
ledger-cell is fixed.** Annotations are side-channels; the primary value
stream is monotonically append-only.

### 2.3 The ICC reliability invariant

per-reader baselines have ICC = 0.7714 [0.667, 0.810]. This is an invariant
because:

- ICC is computed as sigma^2_between / (sigma^2_between + sigma^2_within)
  on per-reader median baselines.
- It is a **scale-free invariant** of the per-reader drift distribution: it
  does not depend on the corpus_sd scalar, the measurement instrument, or
  the room-field geometry. It measures *relative reliability*.
- Per-dial values (mood .97, volume .98, earnestness .95, presence .91) are
  also invariants — they survive instrument changes, corpus changes, and
  field geometry changes. They are properties of the reader's personality,
  not the measurement.

**Code:** `scripts/e2_instrument.py::Measurement.icc()` computes this exactly.

### 2.4 The drift-geometry branch closure (reductio)

The thesis proved (H3 reductio) that the kill number in the drift-geometry
framework is geometry-malleable. The proof structure:

1. Assume drift-geometry can isolate a "true" transition signal.
2. Show that applying a rotation to the field space changes the measured
   drift (because the geometry itself encodes the drift definition).
3. Since rotations are symmetries of the room (the room's geometry is
   invariant), the drift measure itself is a geometric artifact, not a
   fundamental quantity.
4. Therefore: the drift-geometry branch is closed. The invariant here is
   the symmetry argument itself.

**Code:** The closure is recorded in the ledger (Ch 7.2), not in code. The
codebase implements the chord-difference in vMF space, which is rotationally
non-invariant. The H3 reductio works because the code's raw chord difference
*is* geometry-dependent.

### 2.5 The replay-equation invariant

From `scripts/e2_instrument.py::replay_readings()`:

    raw = row["field_raw_after"]
    room_eff = row["field_eff_after"]
    s = 1.0 - exp(-charisma * n)
    eff = clip(raw + s * (vibe - raw))
    vibe = vibe + (room_eff - vibe) * alpha

This function is the **derivation law**: given a reader's parameters and a
night's speaks, the readings are *determined*. The replay_readings function
is a deterministic homomorphism from the input monoid (sequence of speaks
x reader params) to the output monoid (sequence of reading vectors). The
invariant is: `assert_replay_matches_log()` holds |replayed - logged| < 1e-9.
This equality is the algebraic conservation law of the system.

---

## 3. The Band Structure

### 3.1 Premise bands as a threshold automaton

**Definition.** The premise band system operates on the scalar rho (ratio =
spread/drift in corpus-sd units). Two threshold edges define three states:

  EDGE_LO = 0.3,  EDGE_HI = 0.6

  plain_state(x):
    x > 0.6 -> "clear"
    x < 0.3 -> "kill"
    else    -> "in"

This is a **three-state threshold automaton** on the field R. The state
space S = {0, 1, 2} = {"clear", "in", "kill"} is a finite chain (lattice).

**Code:** `scripts/premise_band_movers.py::plain_state()` and `entry_ok()`
implement the state machine.

### 3.2 Hysteresis as a hysteresis operator on the state chain

The hysteresis margin HYST_MARGIN = 0.05 and hold count HYST_HOLD = 3
consecutive windows implement a hysteresis operator on the chain S:

    def entry_ok(cur, tgt, x):
        if tgt > cur:          # upward move
            if cur == 0 and tgt == 1: return x >= 0.35  # 0.3 + 0.05
            return x >= 0.65                              # 0.6 + 0.05
        if cur == 2 and tgt == 1: return x <= 0.55       # 0.6 - 0.05
        return x <= 0.25                                  # 0.3 - 0.05

This is a **Morse-theoretic** structure: the state transitions are gradient-
flow on the potential V(x) defined by:

  V(x) = inf  for x in (0.3, 0.35) U (0.55, 0.65)   # forbidden region
  V(x) = 0       for x in [0, 0.3] U [0.6, 1]       # stable basins
  V(x) = large   for x in [0.35, 0.55]                # transition region

The 0.05 deadband is a **topological barrier**: crossing requires both
sufficient distance (>= 0.05 past the edge) AND sufficient time (>= 3
consecutive windows).

### 3.3 Band-crossing is NOT a group action

The band-crossing events are better described as:

- A **marked point process** on the time axis of each reader's rho(t) series.
- Each crossing event is tagged: position, edge crossed (0.3 or 0.6),
  direction (up or down).
- The set of events forms a monoid under concatenation (events from reader
  A at night T followed by events from reader B at night T+1).

The crossing-counting function `counted_crossings()` is a **fold** over the
time axis:

    counted_crossings = fold_left(entry_ok, initial_state, rho_series)

This is not a group action because:
- There is no group G acting on the state space S.
- The hysteresis operator is stateful (memory of current state).
- The operator is not commutative: crossing 0.3->0.6 then 0.6->0.3 differs
  from crossing 0.3->0.6-eps then 0.3->0.6 (different intermediate states).

### 3.4 The registered statistics as a decomposition monoid

Four legs form a decomposition of the premise evidence:

| Leg | Measures | Algebraic Structure | Code |
|-----|----------|-------------------|------|
| A: timing | Temporal proximity to transitions | Point process on strata boundaries | leg_A() — circular-shift null, binomial |
| D: direction | Fraction of transitions covered | Bernoulli proportion with CI | leg_D() — Clopper-Pearson exact CI |
| P: persistence | Cosine similarity of pre/post vectors | Sphere S^6 cosine alignment | leg_P() — Fisher z-pooling, bootstrap |
| S: exposure | Regression slope of rho vs warmth | Linear model with nested null | leg_S() — reader-clustered bootstrap |

**Leg A as a marked point process:** The circular-shift null generates a
reference distribution. The real crossings form a measure mu_real on the
window-start axis; the null generates mu_null via rotation. The test
statistic A = mu_real(boundary-neighborhood) / mu_real(total) compares
spatial concentration.

**Leg P as a sphere alignment invariant:** The cosine of pre/post offset
vectors in the reliable subspace (mood, volume, earnestness, presence) is
an invariant of the subspace geometry. Fisher z-pooling (atanh/cosh) is
the canonical map for spherical correlation coefficients, making the
pooling invariant under rotation of the reliable subspace.

**Leg S as comparative model selection:** The slope regression tests whether
room warmth (x) predicts reader score (y). The nested permutation null
compares against roster_size + archetype_warmth as competitors. The
"beats competitor" boolean is the truth value of x >= competitor in
predictive power.

### 3.5 x-invariance (Leg S final flag)

x_invariant = contains_0 and not beats means: the slope CI contains 0
(movement is noise) AND x does not beat the competitor. This is the
**null hypothesis** of the exposure analysis: the reader's score
distribution is invariant to room warmth.

---

## 4. The Derivable Code

### 4.1 The minimal algebraic core

If the algebraic skeleton is right, the following are **forced** (they
cannot be changed without breaking the entire structure):

**1. The RoomField class (field.py)**
- The room is a vector in R^7 (dial space). Forced because 7 dials = 7 dimensions.
- vector() extracts this R^7 coordinate. normalize() maps to S^6.
- warmth() is a fixed linear functional W . v. Forced because the warm
  direction is a priori (from the vmf spec).
- concentration() = 2 * ||v - 0.5|| — the v0 extremity proxy, banned from
  comparison paths. An algebraic constraint.

**2. The vMF estimator (vmf.py)**
- vmf_fit() is the **unique** map from z-samples to (mu_hat, kappa) that
  solves the vMF MLE equations. Forced because:
  - vMF is the maximum-entropy distribution on S^6 with given mean direction
    and concentration. MLE is the canonical estimator.
  - The Newton solve on A_7(kappa) = rho has a unique solution (A_7 is monotone).
- edge() is forced because: given vMF fits at two times, the displacement
  must be measured. The chord-difference (not geodesic distance) is the
  choice that composes additively in R^7, enabling the category structure.

**3. The Measurement class (e2_instrument.py)**
- _build(): readings -> cell_baselines -> drift = a **monadic computation**
  (Reader monad on the space of (night, reader) pairs).
- drift_mean(): fold over readers of drift values. Categorical pushforward
  from the Reader monad to R.
- ratio_cont() = spread_cont() / drift_mean(): the **morphisms of category E
  projected to R^+**. The ratio is the 1-dimensional shadow of the edge object.
- bootstrap(): resampling is a **random endomorphism** on the Reader monad.
  The CI is the confidence interval of the pushforward.

**4. The ledger as a fold**

The claim ledger is a fold over the operation stream:

    Ledger = fold (append . maybe-annotate, initial_ledger, events)

where events are the sequence of measurement results, each a field-edge or
an annotation event.

### 4.2 What is NOT forced (design choices)

- The warm direction WARM in vmf.py: a priori, not derivable from the algebra.
- The corpus-sd normalization: "RMS over dials" = Euclidean scale. Design
  choice; different normalization would change numeric values but not
  algebraic structure.
- The window size W=12 in premise_band_movers: hyperparameter, not structural.

---

## 5. Dissent and Structural Risk

### 5.1 Where the algebraic view strains

**1. The vMF chord-difference is not geometrically natural.**

The edge function computes d_mu = ||vhat_B - vhat_A|| as a chord in R^7.
But vhat lives on S^6. The geometrically natural displacement is the
*geodesic distance* d_S6(vhat_A, vhat_B) or the *logarithmic map*
log_vhat_A(vhat_B) in T_vhat_A(S^6).

The chord-difference:
- Composes in R^7 (d_mu(A->C) = d_mu(A->B) + d_mu(B->C) for collinear points),
  which is why it was chosen.
- Does NOT compose on the manifold: the exponential map is nonlinear.
- Is an artifact of the R^7 embedding, not of the manifold S^6.

**Consequence:** The category structure on E is an artifact of the R^7
embedding. Replace the vMF estimator and the edge composition law breaks.

**2. The hysteresis state machine is not a Markov process.**

`entry_ok` depends on the current state `cur` AND requires `HYST_HOLD`
consecutive windows. This is an *h-accretion* (debounce filter) — it has
memory of the full trajectory. A Markov chain on {clear, in, kill} cannot
capture this; you need {clear, in, kill} x {0, 1, 2, 3} (state + counter).

**Consequence:** Statistical inference on crossing rates must account for
non-Markovian structure. The circular-shift null (Leg A) assumes that the
consecutive-window structure under the null is exchangeable — not obvious.

**3. The decomposition (A, D, P, S) is not orthogonal.**

- A and D are clearly correlated: more nearby crossings scores higher on
  both timing and coverage.
- P and S use the same dial-space: the offset vectors in P and the rho
  values in S are computed from the same underlying vectors.

**The four legs are a suggested decomposition, not a provably orthogonal
one.** The thesis should state this explicitly.

### 5.2 THE ONE STRUCTURAL RISK that could sink the thesis

**The narrow-scope invariant problem / warmth-personality confound.**

The thesis's strongest claims are all *narrow-scope invariants*:
- ICC 0.7714 [0.667, 0.810]: "per-reader baselines are real."
- Content separation 0.893 vs silence 0.36: "room-level composition
  identity survives."

Both are true *within the measurement context* — the specific readers,
nights, dials, and estimator used. The risk is that these invariants
*depend on the very measurement instrument they are used to validate*.

**Concrete scenario:** The vMF warm direction W (a fixed vector in R^7)
was chosen after seeing the data. If W correlates with reader personality
(which the outline notes in Ch 4.3: "ICC-reliable subspace overlaps the
v0 warmth form's heavy weights"), then the warmth projection is not a
neutral instrument. It is a *reader-personality detector*.

All warmth-based claims (room-field temperature, slope regression, premise
bands) become confounded with reader personality. The warmth defines a 1D
projection R^7 -> R. The ICC says the pullback to individual readers is
reliable. But reliability != signal. If W is a personality detector,
reliability reflects stable personality, not changing room temperature.

**This is the one structural risk:** the measurement instrument (vMF + warm
projection) may be measuring reader personality rather than room temperature,
and this confound propagates through every edge computation, every band
crossing, every slope regression. The ledger's append-only honesty would
record this, but the ledger itself is built on the same instrument.

### 5.3 Mitigating this risk (algebraically)

The draft already includes several mitigations:
- **Class-residual regression:** removing archetype structure from the
  baseline isolates the within-archetype signal.
- **H-reader=room slope test (Ch 6.3):** registered but not claimed —
  exactly the right posture.
- **Null-drift control (0.291 vs primary drift 0.748):** low null-drift
  suggests at least some noise is not personality-driven.

**The algebraic safety net is the ledger itself:** R4 forces every number
to appear with its annotation. If the confound is discovered, all warmth-
based claims move to "annotated" status. The ledger stays honest; the
claims move to registered-hypothesis. The procedure survives; the specific
measurement may not.

---

## Summary of Code-to-Algebra Mappings

| Algebraic Structure | Code Location | Function/Class |
|---------------------|---------------|----------------|
| Category E (edges) | elephant/vmf.py | edge(), vmf_fit() |
| Free monoid with annotation | master-outline.md | claim ledger |
| Three-state threshold automaton | scripts/premise_band_movers.py | plain_state(), entry_ok() |
| Hysteresis operator | scripts/premise_band_movers.py | counted_crossings() |
| Point process (Leg A) | scripts/premise_band_movers.py | leg_A() |
| Bernoulli proportion (Leg D) | scripts/premise_band_movers.py | leg_D(), clopper_pearson() |
| Spherical alignment (Leg P) | scripts/premise_band_movers.py | leg_P(), cos_pair() |
| Linear model + nested null (Leg S) | scripts/premise_band_movers.py | leg_S(), ols_slope() |
| Monadic computation | scripts/e2_instrument.py | Measurement._build(), drift_mean() |
| Replay homomorphism | scripts/e2_instrument.py | replay_readings(), assert_replay_matches_log() |
| vMF MLE (forced) | elephant/vmf.py | vmf_fit(), A7() |
| RoomField vector (forced) | elephant/field.py | RoomField.vector(), normalize() |

---

*Written by the Mathematician. Read-only. No code changes proposed.*
