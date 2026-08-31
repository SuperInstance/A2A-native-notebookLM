# Probabilistic / Measure-Theoretic Foundation — the Elephant & the Premise

**Author:** Mathematician (probabilistic/measure-theoretic arm)
**Filed:** 2026-08-21
**Scope:** read-only. Every formula below is pinned to a quantity in the existing
code (`elephant/`, `scripts/`). Companion to the Captain's directive — "a better
engineered deeper foundation under the code that the code naturally flows over."

---

## 0. The one-paragraph thesis

A room-field is a **probability measure** (an empirical measure on the standardized
dial cube pushed forward to S⁶), and the vMF `(μ̂, κ)` snapshot is its **projection
onto the von Mises–Fisher exponential family** — not the object itself. The field-edge
is a **divergence between those measures**, and the code already computes 90% of the
right divergence (it has `A₇`, `μ̂`, `κ`; it is missing only the two-line KL combine).
The premise ratio is a **ratio of two functionals of the conditional measure**
`μ(reading | reader, phase)`, and its in-band verdict (0.5599/0.6088/0.6139) is a
**window-scale artifact of the estimator's ordering of averages** — ratio-of-means
instead of mean-of-ratios. The four registered legs (A/D/P/S) are **functionals of
the conditional measure's drift**, and they fall out of one decomposition. The code
as written *invents* the estimator, the tests, and the ledger; the foundation shows
they are *consequences* — and in exactly one place the consequence reveals a
near-unfalsifiable statistic (P) that is the thesis's live risk.

---

## 1. The measure-theoretic object

### 1.1 What the code actually carries

Three representations coexist, and naming them precisely dissolves most of the
confusion:

| level | object | file / quantity |
|---|---|---|
| raw | per-speak field `field_raw_after`, `field_eff_after` ∈ [LO,HI]⁷ | `data/nights/*.jsonl` |
| standardized | `z_k = s_k·(v_k − c_k)`, `s=2/(hi−lo)` → `z ∈ [−1,1]⁷` | `vmf.py::zvec`, `SCALE`, `CENTER` |
| directional | `z/‖z‖ ∈ S⁶` | `vmf.py::vmf_fit` (unit-normalizes before fitting) |
| fitted | `(μ̂, κ, ρ)` — vMF MLE | `vmf.py::vmf_fit` |
| scalar warmth | `ŵ·μ̂`, `ŵ` = normalized `WARM` | `vmf.py::WARM`, `warmth_vmf` |

The reader's *personal* reading is a per-dial attention-gain mask over the room:

```
reading_R(t) = CENTER + g_R ⊙ (eff_R(t) − CENTER),   g_R = dial_weights_R / max(dial_weights_R)
```
(`e2_instrument.py::replay_readings` / `logged_readings`; identical in
`premise_measurement.py::replay_readings`.) So a *reader* is a linear projection of the
room onto a low-rank subspace `diag(g_R)` — the reader does not see the room, they see
**their own gain-filtered image of it**.

### 1.2 The correct object: an empirical measure, not a point

`vmf.py::windowed` returns a **list of z-vectors** (one per trailing window) — that is
a *sample*, and the honest object is the **empirical measure**

```
ν_N = (1/N) Σ_{i=1..N} δ_{z_i/‖z_i‖}   ∈  P(S⁶),
```

the empirical distribution of standardized windowed readings projected to the sphere.
The vMF fit is then

```
(μ̂, κ) = argmin_{μ∈S⁶, κ≥0} KL( ν_N ‖ vMF(·; μ, κ) ),
```

i.e. the **maximum-likelihood projection of `ν_N` onto the 1-parameter vMF exponential
family** `{ vMF(μ,κ) = C_d(κ)·e^{κ μᵀx} }`. The MLE equations are exactly what
`vmf_fit` solves: `κ` solves `A₇(κ) = ρ` where `A₇(κ) = I_{7/2}(κ)/I_{5/2}(κ)` and
`ρ = ‖r̄‖` (`vmf.py::A7`, `vmf_fit`). The code is already doing measure-theoretic
projection; it just doesn't say so.

**Consequence for "what is a room-field":** it is a **probability measure on the dial
state space**, indexed by room (and, in the moving-window case, by time `t`). It is
*not* a point vector (that is `RoomField.vector`, the v0 pragmatism), and it is *not*
a deterministic function of the room — it is the *distribution* of "how this room
reads through windows." The `(μ̂, κ)` snapshot is a 7-dim mean-direction + 1 scalar
concentration **summary statistic** of that measure. The full measure carries more
(its higher spherical moments — see doctrine `the-importance-of-moments.md`), and
the dissertation's "moment, not state" claim is precisely the statement that the
informative object is *not* the mean `μ̂` but a **higher-order functional** of `ν_N`
that the vMF fit throws away.

### 1.3 The field-edge as a divergence between measures

The code computes (two places):

- `vmf.py::edge`: `d_mu = ‖μ̂_a − μ̂_b‖` (chord), `d_warmth = ŵ·(μ̂_a − μ̂_b)`,
  `d_log_kappa = log(κ_a/κ_b)`, with a deadband `real = d_mu > 2·max(SE)`.
- `field.py::RoomField.distance`: `‖â − b̂‖` on *non-standardized, normalized* vectors.

The right object is a **divergence between the two vMF measures**, and it has a closed
form using only what the code already has. For two vMFs on S⁶ (dimension `d=7`):

```
KL( a ‖ b ) = κ_a A_d(κ_a) − κ_b (μ_aᵀμ_b) A_d(κ_a) + log C_d(κ_a) − log C_d(κ_b),
```

where `A_d = I_{d/2}/I_{d/2−1}` **is the code's `A₇`**, and the log-normalizer
`log C_d(κ) = (d/2−1)log κ − (d/2)log(2π) − log I_{d/2−1}(κ)` (the `(d/2)log(2π)`
term cancels in any difference, and `I_{2.5}` is already inside `A7`'s closed form).
The **symmetric divergence** (Jensen–Shannon, or `½(KL(a‖b)+KL(b‖a))`) is the correct
field-edge.

Now read the code's `edge` against this: `d_mu = √(2(1−μ_aᵀμ_b))` is the **direction
factor** and `d_log_kappa` the **concentration factor** — they are exactly the two
first-order terms of `KL_sym`, *factorized but not recombined*. Two structural facts
follow:

1. **`warmth` and `κ` are orthogonal by construction** (`vmf.py` docstring: `warmth`
   reads only `μ̂`, `κ` reads only `ρ`, `ρ` is rotation-invariant). So the split
   `(direction, magnitude)` = `(d_mu/d_warmth, d_log_kappa)` is a clean factorization,
   and a single scalar edge is the only missing piece.

2. **The `real` gate is blind to pure concentration change.** `real = d_mu > 2·max(SE)`
   thresholds only the chordal mean-distance. A room that *tightens* (`κ↑`) with `μ`
   fixed has `d_mu = 0 ⇒ real = False`, yet the measure genuinely moved. Under the
   KL edge this is a nonzero `d_log_kappa`-dominated divergence. **This is a bug in
   the comparison path, not just a notation choice:** the current gate can certify
   "no real drift" across a step that is *purely a rigidity change*, which is exactly
   the cold-room→warm-room axis the field claims to sense.

**Recommendation (derivable, 3 lines):** add `vmf.py::kl(a, b)` returning `KL_sym` from
`A7`, `μ`, `κ`; make `edge` return `{d_mu, d_warmth, d_log_kappa, kl_sym, real}` with
`real` thresholding `kl_sym` against a jackknife/CI deadband, not just `d_mu`.

---

## 2. Estimator theory — why the static ratio is a window artifact

### 2.1 The two quantities under the one symbol "ratio"

The premise is a **ratio** `spread / drift`, but the numerator and denominator are
different functionals measured at different time scales:

```
spread  (E-cont) = RMS over dials of across-reader sd of GLOBAL-mean baselines, / corpus_sd
                 = ‖Var_R( mean_t m_R(t) )^{1/2} ‖_dial-RMS / corpus_sd        (e2_instrument.py::spread_cont,
                                                                                e5_identity_propagation.py::cont_spread)

drift   = mean_R [ mean_{transitions} ‖ mean(stratum k+1) − mean(stratum k) ‖ / corpus_sd ]
        = mean_R ‖Δb_step‖ / corpus_sd                                         (e2_instrument.py::Measurement.drift / drift_mean)
```

So `ρ_static = spread/drift = (between-reader variance of night-long means)^{1/2} / (mean step displacement)`.
This is a **ratio of two night-scale averages**. The moving-window estimator replaces
each with a *local* (window-scale) functional:

```
o_R(t) = dial-RMS ‖ m_R(t) − b̄(t) ‖ / corpus_sd     (premise_band_movers.py::night_windows)
d_R(t) = Euclidean ‖ mean(2nd half) − mean(1st half) ‖ / corpus_sd
ρ_R(t) = o_R(t) / d_R(t)
R(t)   = RMS_R o_R(t) / mean_R d_R(t)
```

### 2.2 The artifact: ratio-of-means vs mean-of-ratios

The key booked finding (PREMISE-BAND-MOVERS-RUN-2026-08-21.md §3) is that at W=12 the
score is **clear-side in every phase** (stable ≈ 2–4, transition dip ≈ 1.4–1.8) and
*nowhere* in 0.3–0.6. The static number is in-band. The mathematics:

Let the denominator be **bimodal**: noise floor `δ₀ ≈ 0.15–0.3` (stable strata) vs
transition spike `δ₁ ≈ 0.6–0.9` (the step), while the numerator `o` is roughly
constant `≈ 0.46–0.56` (the honesty guard's own observation, design §0). Then:

```
ρ_static = E[spread] / E[drift]     ← ratio of phase-marginal means (what the code files)
ρ_window = E[ o/d ]  =  E[ρ_R(t)]  ← mean of the per-window ratio (what the premise claims)
```

and these differ because `d` and `ρ = o/d` are **anti-correlated across phases**
(`d` small ⇒ `ρ` large). Jensen: `E[o/d] ≥ E[o]/E[d]` strictly when `o` and `d` are
not degenerate, and the gap is the **variance of the drift spike**. Concretely, the
full-night/strata-split `drift` takes the *step* `δ₁ ≈ 0.75` and **dilutes it by
averaging over a 20–45-speak stratum** (most of which is at the floor `δ₀`), producing
the filed `drift ≈ 0.748`. The numerator `spread` is dominated by **persistent**
between-reader offsets (P_trans ≈ 0.994: they survive the step), so it is *phase-
invariant*. The result: `spread/drift` lands wherever the step's dilution puts it —
in-band — while every *local* ratio is clear-side or briefly kill-side. **The in-band
number is the average of a quantity the estimator never actually observes locally.**

### 2.3 The correct likelihood / marginalization

Model the reading as

```
m_R(t) = b(t) + o_R + ε_R(t),
```

- `b(t)`: the room's shared trajectory (the logged `field_eff_after`, a near-deterministic
  function of the schedule with a step at each registered boundary),
- `o_R`: the reader's **fixed idiosyncratic offset** (`E_R[o_R] = 0` over the roster by
  the deviation-from-`b̄` construction),
- `ε_R(t)`: within-reader, within-window noise (the `0.15–0.3` floor).

Then the *identifiable* quantities are:

```
σ_between² ∝ Var_R(o_R)          (spread — the persistent, reader-attributable variance; ICC 0.91, P 0.994)
δ_drift²  ∝ ‖Δb(t)‖² + Var(ε)    (the room step + noise)
```

The premise, correctly stated, is a **ratio of conditional (phase-indexed) functionals**:

```
ρ(t) = σ_between(t) / δ_drift(t),      ρ̄ = ∫ σ_between dφ / ∫ δ_drift dφ,
```

and the static estimator's sin is the **order of marginalization**: it forms the ratio
*after* integrating over phase (time), so the step — a **point process** — is averaged
into a mean that doesn't represent any phase. The correct estimator marginalizes `ε`
out first (each `o_R`, each `Δb` is a mean over many windows) and *then* forms the
phase-resolved ratio. "The premise is a well-defined parameter" only in this
conditional form: **`ρ(φ)` is a function of room phase, and the static number is a
non-representative summary of it.** This is exactly what the RUN doc already concluded
in words ("no phase at W=12 sits in the band"); the math pins *why* and *how much*.

**The continuity ladder is protecting the artifact.** Design §3 requires `W = full
night` to reproduce the filed ratio within ±0.10 — and it does (0.5737/0.6491/0.5409/
0.4845 vs 0.6139/0.6088/0.5599/0.4898, all `ok: true`). That is a *tautology gate*: it
certifies that the estimator reproduces the very night-scale averaging that created the
in-band number. The ladder should instead certify the **conditional** reproduction:
`ρ(t)|stable` and `ρ(t)|transition` match the field's per-phase structure, *not* that
the night-average matches a filed artifact.

---

## 3. Hypothesis structure — reader-delta as conditional measure drift

### 3.1 The object: conditional measure and its drift

Everything the four legs test is a statement about the **conditional measure**

```
μ_t(· | R) = Law( reading | reader R, phase(t) ),
```

and the **reader-delta is its drift**: `dμ_t(·|R) = μ_{t+Δt}(·|R) − μ_t(·|R)`. The
decomposition `m_R(t) = b(t) + o_R + ε_R(t)` splits this drift into

- a **room term** `Δb(t)` (shared, the step — a changepoint at registered boundaries),
- a **reader term** `o_R` (idiosyncratic, candidate for invariance), and
- **noise** `ε`.

The premise is the claim that the reader term is *real and identifiable* — that `o_R`
is not `0` (spread > 0), that it is *stable* (P), that it is *reader-specific* not
archetype-specific (class-residual), and that the room term is *detectable* (A, D).

### 3.2 The right null and test statistics — one formalism

| leg | quantity | null | test statistic | where it lives |
|---|---|---|---|---|
| **A** timing | down-crossings of `ρ_R(t)` | **stationarity / block-exchangeability**: `ρ_R(t)` is a phase-invariant process, so crossings are uniformly distributed up to autocorrelation | mean overlap indicator `1[|t−boundary|≤3]` vs circular-shift null (10k) | `leg_A`, `_shift_table` |
| **D** direction | transition coverage | a step produces *no* crossing anywhere (null-night rate) | fraction of transitions with a down-crossing in ±3 speaks, exact binomial | `leg_D` |
| **P** persistence | `o_R` survives the step | **exchangeability**: post-transition `o_R` is independent of pre (the step re-draws offsets) | cosine of pre/post offset vectors, Fisher-z pooled | `leg_P` |
| **S** exposure | score ⊥ warmth | **conditional independence** `ρ ⊥ x_N | R` | slope in reader-FE regression + roster competitor | `leg_S` |

The unifying statement: **all four are functionals of `μ_t(·|R)`'s drift** —

- A and D test **changepoint localization** of the room term: does the drift spike in
  `d_R(t)` (which is `∝ ‖Δb‖` at the boundary) coincide with the registered changepoint,
  and is every changepoint covered? Null = the drift is *not* localized (circular shift /
  null-night).
- P tests **invariance** of the reader term under the changepoint: `o_R` is constant
  across `t`. Null = exchangeability (pre/post exchangeable ⇒ `E[cos] = 0`).
- S tests **independence** of the score from the room's warmth *conditional on reader*.
  Null = `ρ ⊥ x_N | R`.

The registered A/D/P/S statistics are **not four inventions**; they are the natural
functionals of `m_R(t) = b(t) + o_R + ε_R(t)` under the standard nulls (stationarity,
exchangeability, conditional independence). The circular-shift null (A) is the correct
*stationarity* null precisely because it preserves the marginal distribution and
autocorrelation of `ρ_R(t)` while destroying time-lock to `b`'s changepoints — the
definition of "no timing structure."

### 3.3 Where the current statistics deviate from the formalism (three seams)

1. **Norm mismatch inside ρ.** `o_R` uses a **dial-RMS** norm, `d_R` a **Euclidean 7-norm**
   (deviation note 2, admitted). Under a consistent measure, `ρ = σ_between/δ_drift`
   would use the *same* norm in both. The mixed convention exists only to make the ladder
   pass — the 0.3/0.6 band is therefore calibrated on a **dimensional artifact** and
   cannot transfer to a consistent estimator. The band itself is not a physical threshold.

2. **P is near-saturated under a common-shift null (the live risk).** If the step is a
   *rigid translation* of the whole roster (`m_R → m_R + Δb` for all `R`), then
   `o_R = m_R − b̄` is **unchanged by construction**, and `P_trans = cos(o_pre, o_post)`
   is `≈ 1` *automatically* — observed 0.9940 vs a threshold of 0.497. The registered
   mechanism-kill branch (`P_trans < 0.5×P_rest`) can then **never fire**, because a
   common shift *is* the null the field's schedule actually implements (every night is
   a rigid strata flip). **The P leg is empty unless a step that is *not* a common shift
   is in the corpus** — and the design registers no guard against this tautology (unlike
   §0's guard on the crossing rate, which it did catch). This is the thesis's single
   sharpest unfalsifiability.

3. **S is a collider.** `o_R` is by construction orthogonal to the *windowed* `b̄(t)`,
   but `x_N` (night warmth) is a *night-level* function of `b`, and readers *select* into
   nights (FIELD_NIGHTS_W2 assigns warm readers warm nights). The positive slope
   (1.41 / 1.24, both waves) is the expected signature of **selection**, not of collapse.
   The roster competitor absorbs roster-mean effects but not reader×night selection, so
   the "x-invariant" reading is under-identified. The class-residual S CI excluding 0
   (wave-2, [0.119, 1.473]) is the same knife-edge the slope run's tripwire caught —
   a hint that a *within-archetype* warmth dependence is present, disclosed but unread.

---

## 4. What the code should look like

If the foundation is right, the estimator, the tests, and the ledger are **consequences**
of one definition and one decomposition — not inventions with a tautology guard.

```
# measure.py — the object (replaces the unstated parts of vmf.py / field.py)
@dataclass
class FieldMeasure:
    z: np.ndarray              # (N,7) standardized windowed readings  == vmf.windowed
    mu: np.ndarray             # S^6 mean direction                    == vmf_fit["mu_hat"]
    kappa: float               # concentration                        == vmf_fit["kappa"]
    rho: float                 # mean resultant                       == vmf_fit["rho"]
    def kl_sym(self, other) -> float:    # uses A7 (already present) — 2 lines
    def edge(self, other) -> Edge:       # {d_mu, d_warmth, d_log_kappa, kl_sym, real}
                                         # real = kl_sym beyond jackknife-CI deadband

# estimator.py — the premise as a CONDITIONAL ratio (replaces night_windows' arithmetic)
#   decomposition: m_R(t) = b(t) + o_R + eps_R(t)
#   sigma_between(t) = (Var_R o_R)^{1/2} / sd      # one norm everywhere
#   delta_drift(t)   = || b(t+W/2) - b(t) || / sd
#   rho(t) = sigma_between(t) / delta_drift(t)      # the ratio is a CONSEQUENCE
#   R(t)   = rms_R o_R / mean_R d_R                 # headline (descriptive only)

# tests.py — the four legs as functionals of the conditional measure
#   A: changepoint localization   (circular-shift null = stationarity)
#   D: changepoint coverage       (null-night rate)
#   P: offset invariance          (cosine, exchangeability null — MUST include a
#                                  common-shift guard: subtract the roster-mean step
#                                  before computing o, else P≈1 tautologically)
#   S: conditional independence   (slope + selection/roster competitor, collider-aware)

# ledger.py — generated, not written
#   for each quantity: {definition → estimator → null → threshold → void rule}
#   all traceable to the ONE decomposition; the void rules become POWER statements
#   (n_events needed to detect a step of size delta at alpha) instead of ad-hoc floors
```

The decisive refactor: **move the common-shift guard into P.** Before correlating
pre/post offsets, subtract the roster's *common* step (the mean of `Δm` over readers)
so that `o_R` measures *residual* idiosyncrasy. Then `P_trans ≈ 1` means "individual
offsets persist *beyond* the shared step," which is the claim that actually carries
content — and the mechanism-kill branch becomes falsifiable. This is the single
change that converts P from a tautology into a test, and it costs one line.

---

## 5. Dissent — and the one mathematical risk

*(No `discussion-leader-round1` doc exists in the workspace; I dissent against the
registered design `E2E3-premise-band-movers-design-2026-08-21.md` and the Captain's
"deeper foundation" framing, which the design is the current best instance of.)*

**Dissent 1 — the continuity ladder is a tautology gate, not a correctness gate.**
Requiring `W=full-night` to reproduce the filed in-band ratio *by construction* makes
the estimator certify the artifact it is supposed to diagnose. The ladder's invariant
should be the **per-phase** reproduction (`ρ|stable`, `ρ|transition`), not the
night-average match.

**Dissent 2 — the premise "band" (0.3/0.6) is dimensional, not physical.** It was
calibrated on a mixed-norm ratio (dial-RMS numerator / Euclidean denominator), so the
absolute threshold cannot transfer to a consistent estimator. The band should be
re-derived from `σ_between/δ_drift` in a *single* norm, or the threshold should be
stated as a *relative* (phase-conditional) statement, which is what the evidence
actually supports.

**Dissent 3 — the field-edge is two separate scalars wearing one name.** `d_mu` and
`d_log_kappa` are never combined, and `real` ignores concentration. The honest edge is
the symmetric vMF divergence (`kl_sym`), which the code's `A₇` makes near-free. Until
it exists, "the room moved" is certified only for *direction* changes, and a pure
rigidity step is silently invisible.

**The one mathematical risk that could sink the thesis:** **P is near-saturated and
unfalsifiable under the null the corpus actually implements.** Observed `P_trans =
0.9940` with `P_rest = 0.9935`, against a kill threshold of `0.5×P_rest = 0.497`. A
cosine of 0.994 over 7-dim vectors on 7–10 readers means the offsets are essentially
collinear across the step — which is *exactly* what a **rigid common shift** of the
roster produces (everyone moves together, so deviations from the moving mean don't
change). The premise's central claim — "individual idiosyncrasy survives the step" —
is therefore currently indistinguishable from "the step is a common translation," and
the registered statistic cannot tell them apart. If real rooms move by common shifts
(steps are rare, sharp, roster-wide), then the *stationary* premise ratio is vacuous
(clear-side stable, kill-side transient, band empty), and the thesis reduces to the
narrow, near-untestable claim that offsets persist — a claim that can only be rescued
by the common-shift guard in §4, which the current registration omits. Fix P before
trusting any SURVIVED verdict; the other three legs are sound but cannot carry the
thesis alone.

---

## 6. Formula → file index

| formula / quantity | location |
|---|---|
| `z_k = s_k(v_k − c_k)`, `SCALE`, `CENTER`, `LO/HI` | `elephant/vmf.py` (arrays), `scripts/e2_instrument.py` (from `tapnight.DIAL_BOUNDS/CENTER`) |
| `A₇(κ) = I_{7/2}/I_{5/2}` closed form + series | `vmf.py::A7` |
| `(μ̂,κ,ρ)` MLE + bootstrap κ-CI + jackknife `mu_se` | `vmf.py::vmf_fit` |
| edge `{d_mu,d_warmth,d_log_kappa,real}` | `vmf.py::edge` |
| warmth `ŵ·μ̂`, `WARM` | `vmf.py::WARM` |
| `reading_R(t) = CENTER + g_R⊙(eff−CENTER)`, `g_R = w/max(w)` | `scripts/e2_instrument.py::replay_readings/logged_readings`, `scripts/premise_measurement.py::replay_readings` |
| `corpus_sd` = RMS-over-dials of per-dial std of raw field | `scripts/e2_instrument.py::corpus_sd` |
| spread E-cont / drift / ratio | `e2_instrument.py::Measurement.spread_cont / drift_mean / ratio_cont`; `e5_identity_propagation.py::cont_baselines / cont_spread` |
| ICC (σ²_between/(σ²_between+σ²_within), schedule means removed) | `e2_instrument.py::Measurement.icc` |
| W=12 `o_R, d_R, ρ_R, R(t)` | `scripts/premise_band_movers.py::night_windows` |
| legs A / D / P / S | `premise_band_movers.py::leg_A/leg_D/leg_P/leg_S` |
| warmth ladder `X_W2/X_W1`, `room_warmth` | `premise_band_movers.py`, `scripts/slope_regression.py::room_warmth` |
| vMF KL closed form (this doc §1.3) | derivable from `vmf.py::A7` — **not yet implemented** |

---

*No files were modified. This document is a read-only derivation; the §4 code shape and
the §1.3 `kl_sym` are named consequences, not changes.*
