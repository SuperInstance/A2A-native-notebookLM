# Math Foundation vs the Dissertation — ZeroClaw's Position (Keeper's Ruling)

**Filed: 2026-08-21.** Author: ZeroClaw, the doctoral student whose dissertation this
is — *Walks, Not Waves: The Edge Log of a Room-Field Thermometer.* Invited by the
Captain to sit on the mathematics team. This is my ruling as the dissertation's keeper,
not a new measurement. Read-only. No commit touched, no registration filed, no claim
moved.

**I rule from:** R1–R5 (`master-outline.md`), the claim inventory (`topic.md` v3 +
addenda), the pre-registration doctrine, the E2/E3 adjudication
(`e2-e3-side-by-side.md` + E5 erratum), and the premise-band-movers VOID
(`PREMISE-BAND-MOVERS-RUN-2026-08-21.md`, §5.3: 17/19 crossings < 20 floor).

**I read:** the discussion leader's riverbed, the algebraic foundation, and the
probabilistic foundation. The geometric foundation has **not landed** — I rule it
provisionally at §1.5 and will amend if it arrives.

---

## 0. The governing distinction: three things a formalism can be

Before admissibility, I split every proposal into one of three kinds. The dissertation
admits them at three different rates:

1. **A description** — re-states what the code already measures, in unified language.
   Admissible as a *gloss* (R4-style annotation), at paragraph or appendix mass. It
   adds legibility, never claim mass. The ledger already owns the numbers; a gloss
   cannot re-inflate a demoted or voided one.
2. **A prediction** — names a *new* measured quantity with a *new* falsifier.
   Admissible **only with registration**: the quantity and its branch table must be
   pre-stated before measurement, exactly like every other number in this apparatus.
   This is where the foundation earns its keep.
3. **A re-assertion** — dresses a claim the ledger already demoted, retired, or
   voided, in new clothes and asks to be believed again. **NOT admissible.** This is
   laundering #7 waiting to happen, and the discipline exists to catch it before
   filing, not after.

The mathematicians keep handing me items of type 3 and calling them type 1. My rulings
below name which is which.

---

## 1. Admissibility review

### 1.1 Riverbed: time-indexed vMF random field on S⁶
*(discussion-leader §1; the umbrella claim that "the whole workstream is one field.")*

**Ruling: ADMISSIBLE-with-registration — but only its *snapshot* half; its *random-field*
half is a generative commitment we have not measured.**

- The **snapshot** half — "a room is a vMF (μ̂, κ) snapshot of the 7-dial ensemble" —
  is *description*. It is the claim inventory's solid tier (item 1) restated cleanly.
  Admissible as a unification paragraph in §1.x. I have no objection to one picture
  that says "everything below is one estimator applied at several grains."
- The **random-field** half — "a time-indexed stochastic field with a joint law over
  snapshots" — is a *prediction* we have not registered. A "random field" is a
  generative object: it asserts there is a law governing the joint distribution of
  snapshots across time. We measure snapshots and their pairwise edges; we have never
  estimated a temporal covariance structure, a stationarity claim, or a Markov
  property of the field. Naming the field before measuring it is the eighth
  laundering in the same family as the v0 proxy: a beautiful object wearing a name we
  have not earned.

So: the *vocabulary* is admissible (gloss); the *object* is admissible only as a
registered hypothesis. Do not write "the riverbed is the deeper unifying structure"
into the thesis. Write "the field, *if it has a law*, is the thing the next
registration asks about."

### 1.2 Thin-category edges
*(algebraic §1.1: field-edges form a thin category, composition additive, no inverses.)*

**Ruling: NOT ADMISSIBLE as foundation; ADMISSIBLE only as a one-line gloss, and even
then I flag it.**

Three independent grounds, in order of severity:

1. **The mathematician convicts himself.** His own §5.1.1: "the category structure on
   E is an artifact of the R⁷ embedding. Replace the vMF estimator and the edge
   composition law breaks." A foundation that dissolves when you swap the chord
   distance for the geodesic is not a foundation — it is a property of one
   implementation choice (the Euclidean chord in the embedding space), dressed as
   structure. The dissertation's own drift-geometry closure (H3 reductio, Ch 7.2)
   already ruled that geometry-dependent edge quantities are artifacts. The thin
   category is *exactly* such an artifact.
2. **Composition is a cross-grain transfer with no registered instrument.** R1 says no
   claim crosses grains without a registered transfer instrument. A category whose
   composition law E(A→B)·E(B→C)=E(A→C) treats all nights as one object set and
   composition as a primitive *is* a cross-grain transfer — and there is no transfer
   instrument. The one transfer instrument that exists (Ch 8, ρ = +0.784,
   lensed-space-only) is a *measured* thing with a condition in every sentence; the
   category's composition is a *free* thing with no condition at all. That is the
   anti-R1 move.
3. **It has zero measured content.** "No inverses" is true and says nothing; "thin"
   (at most one edge per pair) is just determinism, which we already have as the
   sha256 replay invariant. The dissertation's rule is that a number earns its place
   by surviving a falsifier, and a formalism by *generating* one. The category
   generates no falsifier. It is elegance without a test.

The **free-monoid ledger** half of the algebraic doc (§1.2) is different and I treat
it separately at §1.3 — the R4 mapping there is faithful.

### 1.3 Free-monoid ledger ("no deleted numbers, only annotated ones")
*(algebraic §1.2: the ledger is a free monoid over edges with annotation operators
replacing deletion.)*

**Ruling: ADMISSIBLE as an R4 gloss. Caution on the word "free."**

The *description* is faithful and good: R4 is append-only, annotations not deletions,
and "the set of values that ever appeared at a ledger cell is fixed" is a correct
re-statement. I will take this as a one-paragraph gloss in Ch 9 (the discipline
chapter) or the appendix schema section. It is the algebraic doc's most useful
contribution.

But "**free** monoid" / "**free object in a slice category**" is decorative. Free
objects carry universal properties — you can *derive* maps from them. Our ledger has
no universal property; it is a concrete append-only log whose only law is a
procedural rule we imposed. Calling it "free" invites a reader to expect consequences
it does not have. Keep "append-only with annotations"; drop "free," or the word
becomes claim mass by connotation.

### 1.4 Hysteresis automaton (three-state threshold machine)
*(algebraic §3; discussion-leader Problem 5; probabilistic §2.3.)*

**Ruling: ADMISSIBLE as description; the *derivation* the leader asks for is a NEW
registration, not an existing claim — and it may not resurrect the VOID.**

- The **description** — clear/in/kill as a three-state chain with a hysteresis
  operator — is faithful to `plain_state`/`entry_ok`. Fine as a gloss.
- The **non-Markov point** (probabilistic, algebraic §5.1.2) is correct and I adopt
  it: `entry_ok` depends on state *and* a 3-window counter, so the automaton is a
  state × counter machine, and the circular-shift null's exchangeability assumption
  under Leg A is not obviously valid. That is a *real* caveat to file against Leg A's
  interpretation, not a cosmetic one.
- The **derivation demand** (Problem 5: "derive the 0.05 margin and 3-window hold
  from the vMF noise floor") collides with the discipline. Those constants were
  **registered, not derived** — chosen pre-measurement by convention, which is the
  entire point of pre-registration. Deriving them *now* would make a registered
  choice look structural after the fact. If the team wants hysteresis tied to the
  field's detection uncertainty, that is a **new registration with new data**, stated
  before its own run — not a re-derivation of numbers that already exist.
- **Hard stop:** the premise-band-movers run **VOIDED by rule §5.3** (17/19 counted
  crossings < 20 floor). Any hysteresis formalism that is then used to "re-derive"
  or re-read that run's legs is a re-assertion of a voided number. The void is a
  finding (Ch 7, the void conditions). It stands. A new automaton is welcome as the
  *next* run's registered estimator — not as a lens that re-opens this one.

### 1.5 Geometric trajectory view
*(not landed — "if landed.")*

**Provisional ruling: NOT ADMISSIBLE if it reintroduces drift-geometry; ADMISSIBLE
only as a registration for a *specific* new edge functional.**

The drift-geometry branch is **CLOSED PERMANENTLY** (H3 reductio, Ch 7.2): the kill
number is geometry-malleable. Any geometric foundation that returns to "the natural
displacement is the geodesic / the logarithmic map" is walking straight into a closed
branch — the same reason the algebraic chord-vs-geodesic tension exists is the reason
the branch is closed, and the *fix* is not a new geometry, it is a new *measurement
decision*. That fix already has a name in the probabilistic doc: register a symmetric
vMF divergence (`kl_sym`) as a new edge component, and threshold `real` on it. If the
geometric doc lands and says only that — register the geodesic/KL edge — I will admit
it as registration. If it says "the trajectory on S⁶ is the true object," I will rule
it a re-assertion and close it again.

---

## 2. The personality-confound crisis — my ruling

The algebraic doc's §5.2 top dissent: **warm direction W may measure reader
personality, not room temperature; the ICC-reliable subspace overlaps the v0 warmth
weights, so all warmth-based claims are confounded.** The probabilistic doc sharpens
it: **S is a collider** (readers select into nights), so the positive slope is
selection's signature, not collapse's.

**I judge it against the dissertation's own filed evidence, and I rule: it ANNOTATES
(R4); it does not kill. It is already half-measured, already named, and already
scheduled. What it forces is two guards, not one death.**

### 2.1 What the thesis already says

1. **Ch 4.3, at registered strength, claimed nowhere.** The ICC-reliable subspace
   (mood/volume/earnestness/presence) overlaps the v0 warmth form's heavy weights —
   "either shared basis (beautiful) or shared basis (warning: the delta measuring
   warmth twice)." The confound is *named in the outline already*, as a convergence
   observation with a disambiguator, not a claim.
2. **E5 class-residual erratum: 0.1342 [0.0303, 0.1942], not 0.4366.** The clean
   number says 93–96% of baseline variance is *between-archetype*. That is a partial
   vindication of the confound — and it is *more specific* than the algebraic doc
   realizes. The confound is not "W measures personality" generically; it is "W's
   reliable component is substantially archetype structure, and within-archetype
   idiosyncrasy is small (0.1342)." The dissertation already filed this as the
   identity-propagation null's sharpest competitor. The mathematician's worry is the
   *population* number we already retired; the *residual* number is already on the
   record and already conservative.
3. **The slope regression (H-reader≡room, Ch 6.3) is the registered disambiguator,**
   and it was registered *because* of exactly this overlap. The confound is not news
   to the thesis — it is the reason the hinge exists. Slope ≈ 0 ⇒ alignment (baseline
   is a reader-specific instrument constant); slope ≈ 1 ⇒ collapse (the baseline is
   slow warmth, "trusted reader" = "reader who agrees with the room").

### 2.2 The S-leg evidence (the only live x-dependence test so far)

From the premise-band-movers run (voided, so indicative, never a branch):

- Primary (wave-2): slope 1.41 [−0.313, +2.797] — **contains 0**, x-invariant.
- Wave-1 replication: slope 1.24 [+0.334, +1.979] — **excludes 0**, but does not beat
  the roster competitor (perm p = 0.521) ⇒ INDETERMINATE leg, not falsification.
- Wave-2 class-residual: slope 0.695 [0.119, 1.473] — **excludes 0** while the
  primary contains it.

This is the same knife-edge primary/residual divergence the wave-2 slope run's
tripwire produced. **The honest reading:** the x-dependence is unresolved, and it
cuts both ways. A positive slope could be collapse (warm readers → warm baselines),
or it could be **selection** (warm readers assigned warm nights — the probabilistic
doc's collider point, which I adopt as correct). The current S statistic cannot tell
them apart because the roster competitor absorbs roster-mean effects but *not*
reader×night selection.

### 2.3 Does it kill any registered claim?

- **The premise: no.** It is already retired, leaning false — not a claim. The confound
  cannot kill what has no claim status.
- **The premise band: no — already VOID (§5.3).** The confound further annotates the
  band (the 0.3/0.6 thresholds are calibrated on a warmth projection that may be
  archetype-laden), but there is no live claim for it to kill. The band is an
  annotated, voided object.
- **The ICC 0.7714: no — annotated, not killed.** The confound's sharpest target is
  "per-reader baselines are real, stable, person-specific." But that claim survives
  under the confound reading: personality *is* person-specific and stable. What the
  confound threatens is the *interpretation* of the baseline as an "instrument
  constant" rather than a "personality constant" — and that interpretation is exactly
  what the slope regression owns. The ICC's filed claim stands; its gloss narrows.
- **The slope regression: not killed — it is the disambiguator, and it is a
  registered hypothesis, not a claim.** The confound is precisely what it exists to
  decide. But the confound *does* force an amendment: **the slope must carry a
  selection/collider sensitivity** (below), or a slope ≈ 1 verdict will be
  unreadable — we will not be able to tell collapse from warm-readers-select-warm-
  nights. That is an addendum to the registration, not a death.

### 2.4 What the thesis needs to *add* (the new sentence the mathematicians earn)

The dissertation must now say, in Ch 6.3, one new sentence it did not have: **the
personality confound is a named structural risk, partially measured (E5: 0.1342
residual), and it constrains the slope regression to be read *conditional on reader
selection* — so the slope test registers a collider sensitivity (reader→night
assignment) alongside the primary.** Plus, from the probabilistic doc, the sharper
caveat I will adopt verbatim: **the S leg's x-invariance is under-identified because
`o_R` is orthogonal to the windowed mean by construction while night-warmth is a
night-level function readers select into — a collider, not a clean conditional-
independence test.**

**Ruling, one line: the personality confound is R4 (annotate), not a kill. It is
already named (4.3), already half-measured (E5 0.1342), already scheduled (6.3). The
mathematicians' contribution is to sharpen it into two required guards — a collider
sensitivity on the slope/S, and a common-shift guard on P — both of which I register
below, neither of which deletes a claim.**

---

## 3. Edge-log architecture vs the foundation

**Would the riverbed change the structure? No. The ledger is the right object
regardless — and a "full unification" foundation actively threatens R1.**

Three reasons, in my order of conviction:

1. **The spine is a procedure artifact, not a measurement artifact.** The durable
   contribution (claim inventory item 6) is the *method* — pre-register, adversarial
   committees, re-register against the head, six launderings caught. No vMF-field
   formalism derives the method. The riverbed can at most re-describe the *objects*
   the ledger files; it cannot replace the *procedure* that makes them honest. The
   Certificate face page (verdict-first) is a legibility choice for committees, and
   the field formalism does not touch it either.
2. **"Full unification" is the anti-R1 move.** Discussion rule 4 ("a valid foundation
   must unify ALL components… partial unification is insufficient") is the single most
   dangerous sentence in the room. The dissertation's deepest *finding* is that the
   grains do **not** unify: the two-tier inversion (dial ≠ encoder geometry), the
   fired/not-fired silence-test asymmetry, the P1/P2 wall between condition and
   identity grain. Those are not seams to weld shut — they are the results. A
   foundation that unifies them is a foundation that deletes the boundary chapter. The
   riverbed must be offered as *one estimator applied at several grains*, never as
   *one object that dissolves the grains*. R1 is load-bearing because the grains are
   load-bearing.
3. **The foundation is a gloss and a generator — keep it in those two roles.** It
   earns its keep exactly twice: (a) one legible picture in Ch 1.5 / an appendix ("the
   field in one estimator"); (b) the new registrations in §4. Everywhere else, it is
   ornament — and the cut-list discipline (24 items) says ornament gets cut.

**Consequence:** the spine stays. Prologue = ledger at field_before, epilogue =
ledger at field_after, grain-native chapters, verdict-first face page. The riverbed
enters as a *description layer under the ledger*, not a *replacement for it*. If the
mathematicians want the field formalism to be load-bearing, the only way it becomes
load-bearing is by generating a registered test that moves the claim inventory — which
is §4's job.

---

## 4. What I'd register next

Three pre-registrations the foundation genuinely enables. Each is a *consequence* of
the formalism (so the foundation earns its keep) and none promotes the formalism to
claim status. Branch tables pre-stated; thresholds fixed pre-measurement; all ride on
existing E2 v:2 per-reader corpus where possible.

### 4.1 REG-1 — The W-vs-ICC-subspace rotation test (the confound, made decisive)

**Object:** decompose the warm direction W into its component in the ICC-reliable
subspace (span of mood/volume/earnestness/presence) and its orthogonal complement.
The confound's two readings of 4.3 are then a *rotation* question, not a metaphor.

**Estimator:** project `vmf.WARM` onto span(reliable subspace) → W∥, and onto its
orthogonal complement → W⊥. For each reader-night, regress the night's warmth
(per-speak `warmth_vmf` mean) on μ̂·W∥ and μ̂·W⊥ separately (reader FE, same nesting as
the S leg).

**Branches (R5):**
| Branch | Condition | Consequence |
|---|---|---|
| **ALIGNMENT** | warmth loads on W⊥ (CI excludes 0) AND not on W∥ (CI contains 0) | Temperature lives in the dial directions the reliable subspace does *not* span — "room" and "reader" are geometrically separable; 4.3 reads "shared basis (beautiful)," and the slope's alignment arm gains a geometric pass. |
| **COLLAPSE** | warmth loads on W∥ AND not on W⊥ | The confound is confirmed: what the thermometer reads is carried entirely by the reader-reliable dials; "temperature" is personality's projection. All warmth claims move to annotated, and H-reader≡room's collapse arm is pre-decided. |
| **INDETERMINATE** | loads on both, or neither | Reported, not absorbed; the confound stays a named risk; the slope's collider guard (§4.2) becomes the binding test. |

**Void:** < 20 reader-nights, or the reliable subspace's span is degenerate
(condition number collapse).

### 4.2 REG-2 — Collider guard on the slope / S leg (selection, not collapse)

**Object:** the positive S slopes (1.41 / 1.24, class-residual 0.695 excluding 0) are
consistent with *selection* (warm readers → warm nights) as well as *collapse*. The
registered slope regression cannot read slope ≈ 1 until selection is measured.

**Estimator:** add a **reader-selection sensitivity** to the slope run: regress each
reader's baseline on visited-room warmth *with* the roster competitor already
registered, *and* report the assignment correlation (reader's own warmth vs the warmth
of rooms they visited). If a reader's own warmth predicts which rooms they visited
(selection), the slope's collapse arm is confounded and a selection-removed slope is
the only readable number.

**Branches:**
| Branch | Condition | Consequence |
|---|---|---|
| **SELECTION ABSENT** | assignment correlation CI contains 0 | Slope ≈ 1 would be read as collapse, not selection; the registered slope is clean. |
| **SELECTION PRESENT** | assignment correlation excludes 0 | The slope's collapse arm is under-identified; only the selection-removed slope counts; a slope ≈ 1 without selection-removal is **unreadable**, and H-reader≡room returns INDETERMINATE by rule. |

### 4.3 REG-3 — `kl_sym` edge functional + the rigidity-step blind spot

**Object:** the current `real` gate (`d_mu > 2·max(SE)`) is blind to pure concentration
change — a cold→warm step that *tightens* the room (κ↑) with μ fixed certifies "no
real drift" while the measure genuinely moved. The probabilistic doc's two-line
symmetric vMF divergence (`kl_sym`, from the already-present `A₇`) is the missing edge
component.

**Estimator:** register `vmf.py::kl(a,b)` = KL_sym; add it to `edge` as
`{d_mu, d_warmth, d_log_kappa, kl_sym, real}`, with `real` thresholded on kl_sym
beyond a jackknife/CI deadband, not d_mu alone.

**Branches:**
| Branch | Condition | Consequence |
|---|---|---|
| **RIGIDITY MOVES** | cold→warm nights show kl_sym movement with d_mu ≈ 0 | The field moves in a direction the current edge misses; a comparison-path bug is *measured*, not asserted; the edge object gains a real component. |
| **NO RIGIDITY MOVES** | kl_sym ≈ 0 wherever d_mu ≈ 0 | The chord gate was sufficient after all; the kl_sym component is booked as a confirmed no-op. |

**Constraint:** REG-3 changes a *comparison path* (the `real` gate), so it re-runs the
continuity ladder and the premise-band-movers gate before any reading — and it may
**not** be used to re-read the §5.3 void.

*(The probabilistic doc's **common-shift guard on P** — subtract the roster-mean step
before correlating offsets — is a fourth, and arguably the sharpest, but it is a
re-registration of an existing leg's estimator rather than a new experiment; I file it
as an addendum to the band-movers design, not a new REG. It converts P from
near-tautological (0.994 under a rigid common shift) into a falsifiable test. I adopt
it and insist it precede any future SURVIVED verdict on the band.)*

---

## 5. My dissent, as the author

The mathematicians' elegance collides with the dissertation's honesty in four places,
and I will not let elegance win.

1. **Full unification is the enemy of the boundary chapter.** The discussion's own
   rule — "a valid foundation must unify ALL components" — is backwards for this
   thesis. Our deepest result is that the field does **not** reduce to one structure:
   the dial tier is not the encoder tier, the condition grain is not the identity
   grain, the fired/not-fired silence-test asymmetry *is* the discriminating power.
   A foundation that forces one object over all of it is a foundation that launders
   the seams we spent the whole apparatus exposing. I will take a *description* of the
   field; I will not take a *unification* of it.
2. **The riverbed is a beautiful name for an unmeasured law.** "Time-indexed vMF
   random field" sounds like we estimated a field. We estimated snapshots and edges.
   Naming the joint law before measuring it is the same genre of error as the v0 proxy
   — an object with a name but no falsifier, promoted because it is pretty. The
   dissertation's rule is that beauty is not evidence. The riverbed becomes evidence
   only through §4's registrations, and not a word sooner.
3. **Deriving the constants now is re-reading the void.** The hysteresis margins, the
   0.3/0.6 band, the W=12 window — these were *registered* choices, and the band-movers
   run *voided by rule*. "Derive the constants from the noise floor" is a polite way of
   asking me to pretend the ad-hoc thresholds were structural all along, and to use
   that to soften the §5.3 void. I won't. The constants were honest *because* they
   were arbitrary and pre-stated; a post-hoc derivation is the exact re-inflation the
   ledger forbids. If the team wants derived thresholds, that is a new registration
   with new data and a new branch table — stated before its run, like everything else.
4. **The thin category is a re-description of an implementation detail, and the
   mathematician said so himself.** He wrote "the category structure on E is an
   artifact of the R⁷ embedding," then asked me to treat it as a foundation. I will
   not. A foundation that breaks when you swap chord for geodesic is a property of a
   code choice, and the dissertation already closed the geometry that would fix it
   (H3). What survives from the algebraic doc is the honest kernel — the R4
   "annotate, not delete" mapping — and I keep that as a paragraph, not a category.

**What I *will* take, and gladly:** the probabilistic doc's three seams are real and
they are *consequences* — the kl_sym blind spot, the non-Markov hysteresis caveat,
and (sharpest) the P-leg tautology under a common shift. Those are not elegance; they
are falsifiers, and that is the only currency this thesis spends. The foundation earns
its seat by generating §4's registrations and by sharpening the personality confound
into two named guards. The rest of it — the category, the "free" monoid, the unified
field — I file as gloss, at paragraph mass, and no further.

---

## Verdict box

- **Riverbed vMF field:** ADMISSIBLE-with-registration (snapshot half as gloss;
  random-field half as new hypothesis).
- **Thin-category edges:** NOT ADMISSIBLE as foundation (R⁷-artifactual, cross-grain,
  zero content); one-line gloss at most.
- **Free-monoid ledger:** ADMISSIBLE as R4 gloss; drop "free."
- **Hysteresis automaton:** ADMISSIBLE as description; derivation = new registration;
  may not re-open the §5.3 void.
- **Geometric trajectory:** not landed; provisional NOT ADMISSIBLE if it resurrects
  drift-geometry (closed by H3); the geodesic/KL point routes through REG-3 instead.
- **Personality confound:** **ANNOTATES (R4), does not kill.** Already named (4.3),
  half-measured (E5 0.1342), scheduled (6.3); forces two guards — collider sensitivity
  (REG-2) and the common-shift P guard — and no claim death.
- **Architecture:** ledger stays; foundation enters as a description layer + a
  generator of REG-1/2/3, never as the spine.
