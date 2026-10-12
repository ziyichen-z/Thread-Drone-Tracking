# P1-SCENE-006 independent review

Status: ROUND_2_PASS_WITH_NOTES (batch 1b `77595c8`); round 1 batch 1 `345b3ea` PASS_WITH_NOTES

Reviewer: review 角色 (independent review, strongest pool; fresh context)

Implementation author: implementation 角色 (Cursor)

## Candidate and requirements

- Accepted design: `docs/proposals/P1-SCENE-006-difficulty-scene-rebuild.md`
  revision 4, Acceptance round 5 `ACCEPTED_WITH_BINDING_CLARIFICATIONS`
  (BC-SC6-1–6); formal design `docs/phase1-single-drone-design.md` v0.3.12.
- Candidate: `345b3ea` (local, not pushed per user decision). Prior passed
  candidate / diff base: `ab8ae73`. `0c4a012` and `960d7aa` are
  status/stop-point docs commits outside the code candidate.
- Stop point: proposal §15 (`STOP_POINT_CONFIRMED_AWAITING_INDEPENDENT_REVIEW`,
  2026-08-02) with the 14-path full-base attribution.
- Implementer evidence: `docs/evidence/P1-SCENE-006-batch1.md` plus the three
  committed artifacts (`P1-SCENE-006-baseline.json`,
  `P1-SCENE-006-anchor-preflight.json`, `P1-SCENE-006-probe-60deg.json`) and
  the untracked `runtime/p1-scene-006/` capture (trace + 106-tick probe).

## Diff coverage

Reviewed the full `ab8ae73..345b3ea` diff (55 files), split by provenance:

1. **Implementation batch `48eb6a2..345b3ea` (36 paths)** — read every file:
   the new `Assets/TetheredTracking/Editor/Scene006/` assembly (11 .cs +
   asmdef + metas), `Scene006EditModeTests.cs` (25 tests), the one-line
   `TetheredTracking.EditModeTests.asmdef` reference, `tools/run_scene006_probe.py`,
   `tests/test_scene006_probe.py`, the three evidence JSONs, the evidence
   file, the status board, and one mechanical `rotate_docs` archive move.
   Exactly the BC-SC6-1 write scope; zero `config/`, zero `Scripts/`, zero
   Play/scenario/session/run-ID. Reran
   `python3 tools/check_role_writes.py --role implementation --base 48eb6a2`
   in the candidate worktree myself: **36 paths PASS**, reproducing §15's
   narrow audit. (Run from `960d7aa` it additionally flags the proposal file —
   that is Acceptance's own §15 stop-point commit, correctly attributed.)
2. **Intervening `ab8ae73..48eb6a2` (20 paths, docs/infra only)** — no code,
   no config. Reproduced the full-base audit
   (`--role implementation --base ab8ae73`): the **same 14 prohibited paths**
   as §15, and verified all 19 attribution commits exist with role-consistent
   subjects (coordination `902a72c` under COORD-003/004 ledger entries;
   DR-P1-M2-001 rounds `f91cb8f`/`cffae36`; acceptance batches; ideation
   proposals; review round `53c5bb0`; qual-3 transcriptions). Ledger entries
   for COORD-003/004 and the three 2026-08-01 SCENE-006 authorizations are
   present in `docs/authorizations.md`. Content of these files is owned by
   their own gates (DR rounds, M2 closure, acceptance records); none of them
   affects the Scene006 code paths.

## What I reran and reproduced myself

**Python tests.** `tests.test_scene006_probe`: **11/11** in `.venv-track`
and **11/11** in `.venv-yoloe` (`PYTHONPATH=.` direct run), reproducing the
implementer/Acceptance counts. Note: run inside the bare review worktree the
suite reports 7F/3E — all traced to step-1 `FAIL_WEIGHT_HASH` because the
pinned model weights are untracked and absent there; the chain fails closed
exactly as designed. This is a worktree environment artifact, not a defect.

**Full Python suite.** `.venv-track` `unittest discover -s tests`:
**297/298, 1 failure** — see finding F3 (pre-existing base breakage in
`test_check_docs`, not this batch).

**Baseline artifact, recomputed from raw samples.** From
`P1-SCENE-006-baseline.json`'s 541 per-sample records I recomputed every gate
value independently (type-7 quantiles via `controller/rate3_decision.py`):
`C_frustum = 540/540 = 1.0` → `L_point = 0.0000` → T2 FAIL;
`C_geom = 506/540 = 0.937037`, `L_occ = total = 0.062963` → T3 FAIL (L_occ
inside [0.05, 0.40] but total < 0.15); occlusion is exactly **34 contiguous
ticks k = 209–242**; T1 domain 540/540, p05 **18.881 px**, median 24.126,
min 17.915, max 85.020 → FAIL; T6 k\* = 0, prompt 35.453 ≥ median → PASS
(descriptive only; the baseline trace uses `s_init = 0`, not the §3.6
argmin). All stored values match my recomputation to float32 precision.

**T4, recounted.** 1040 stations ((h, x, z)-sorted — order verified),
726 certificates passed, rejections 122 body / 307 tether / 0 path
(recounted per record), best station index 754 = `(148, 20.2, 105)` with
`C_station = 1.0` (first-in-order at the max, tie-break verified),
`G = 1.0 − 0.937037 = 0.062963 ≥ 0.05` → PASS. The `p_hover` degenerate
certificate (1 sample, §4.2 of the evidence) passes and its `C_station`
equals `C_hold`, consistent with the §5.2.7 merge semantics.

**T5 preflight, recounted.** Candidate mode: 1257/1257 candidates, support
**all PASS** on measured grass `support_surface_y_m = 1.3e-06` (the §3.4
support-y rederivation demonstrably removes SCENE-003's
`SUPPORT_HEIGHT_MISMATCH`), then **all 1257 rejected
`CLEARANCE_INTERSECTION` with `Building_Stadium` as the only blocker**;
route sub-gate 0 rejections (distances 17.5–27.5 m); status
`BLOCKED_ANCHOR_PLACEMENT_V2`. Current-anchor mode: 305 legal, 356 support
rejections (286 NOT_FOUND + 70 HEIGHT_MISMATCH), 379 clearance, 222 route
(217 as primary reason + 5 shadowed by scene003 reasons) — all counts
internally consistent. BC-SC6-2 is followed: no batch-2 GO request appears
anywhere in the candidate, evidence, or status board.

**T1′ probe, recounted.** Tool state `FAIL` / `RECALL_BELOW_FAIL_MAX` at
step 5 of the frozen chain; weights verified (9 identity hashes); 99 target
samples (V=1 ticks) and 820 distractor samples, both ≥ 40; zero
incompleteness, zero fidelity contradictions; strict recall **16/99 =
0.161616** recounted from per-sample hits; hit ticks are exactly the
near-anchor arcs k = 25–90 and k = 530–540, matching the evidence narrative
and SCENE-003's far-side structural blindness. Embedding is report-only:
medians 0.4149 / 0.4797 / −0.0498 and dual-gate (0.5/0.1) fraction
18/99 = 0.1818 recounted. `gate_state` is null with owner `acceptance`;
the tool has no PASS branch (verified in code and tests).

**Cross-artifact binding.** `trace_sha256` `682dfad0…cca8` is echoed
identically by the trace artifact, the baseline JSON and the probe
manifest/result; `scenario_sha256 f9c92052…` matches the frozen bytes
(hash-asserted in the EditMode tests as well). The untracked
`runtime/p1-scene-006/` capture (541-state trace, 107 frames + 107 truth
sidecars, manifest) is present and consistent with the committed artifacts.

**Unity Edit Mode.** The implementer XML
(`runtime/test-results/p1-scene-006-editmode.xml`) reads **187/187 passed,
0 failed** (Unity 6000.4.1f1, filter `TetheredTracking.Tests`, 2026-08-02
16:11Z, 7.06 s), and I enumerated all **25** `Scene006*` test cases in it
by name against the source file — they match one-for-one. Acceptance's own
rerun was blocked by the sandbox (`listen EPERM /tmp/Unity-Upm-*.sock`,
corroborated in `p1-scene-006-acceptance-editmode.log`). My first
independent batchmode rerun aborted before test execution with
`error CS1069` (IMGUI module resolution) in the pre-existing
`Scripts/SimulationTimerHud.cs` — an editor package-state artifact, not a
candidate defect (the same code compiled in the implementer's same-day run;
UPM connected normally in mine). A second attempt is recorded below.

**Unity rerun (second attempt): environment-blocked, honestly recorded.**
The retry aborted identically — `Scripts have compiler errors`, and the
only errors are the same `CS1069` IMGUI-module lines in
`SimulationTimerHud.cs` (added `cc17844`, predates the `ab8ae73` base;
zero errors in any Scene006 or candidate file). UPM connected normally in
both of my attempts, so this is a batchmode built-in-module resolution
state on this machine, not a sandbox socket issue and not a candidate
defect — the identical code compiled and passed 187/187 in the
implementer's same-day batch run. My independent Unity verification is
therefore **blocked by editor package state**; the Unity gate rests on the
implementer XML (deeply validated above: root counts, engine version, all
25 Scene006 case names cross-checked one-for-one against the source),
Acceptance's XML root check, and my full code read. Failed-run logs:
review session scratchpad `review-editmode{,2}.log`.

## Semantic fidelity to the frozen contracts (code review)

Checked line-by-line against the runtime originals and §5.2–§5.6:

- `Scene006RouteGeometry` reproduces `RateStudyScouting`
  perimeter/sampling operation-for-operation (EditMode test asserts
  0-tolerance equality against the internals).
- `Scene006Trace.Generate` reproduces `Configure` + `PlaceAtRouteDistance`
  + `Step` float32 semantics including the `< 0.5f` pause-and-advance and
  `delta.y = 0`; the trace-vs-real-component test drives an actual
  `LoopTargetVehicle` for 541 states at `s_init` 0 and 123.4 with zero
  position/rotation drift. First lap 538 ≤ 540 confirmed.
- `Scene006GimbalReplay` transcribes `TetheredGimbal.LateUpdate` literally
  (45° clamp, `max(0.1, −Δy)`, 0.001 yaw-hold, 24°/step quaternion
  geodesic, frozen `Euler(90,0,0)` init matching the bootstrap; `s_0`
  evaluated without update). Target point is the vehicle root position,
  matching the truth-directed convention in `P1DetectScouting`
  (`LookAtWorld(target.position)`).
- `Scene006Visibility` matches `CoverageEvaluator.EvaluateVisibility`
  point-for-point (15-sample construction asserted equal via
  InternalsVisibleTo; denominator constant 15; `≥ 0.2`;
  `RaycastAll(…, −0.05, ~0, Ignore)` skip-target-subtree; `ProjectBounds`
  identical and tested against `ProjectRenderers`). The rays-off frustum
  boolean is the §5.2.8 domain predicate; membership and renderer size
  measurement are separated; an unprojectable member routes to
  `PROBE_FIDELITY_CONTRADICTION`, never silent exclusion.
- Coverage denominators are exactly `s_1..s_540`; `s_0` excluded; every
  interval gate closed; per-station `C_station` replays independently from
  the frozen gimbal init (no state inheritance).
- `Scene006StationSet` implements the 4 m lattice × 7 heights with
  `r(h) = sqrt(35² − h²)`, `p_hover` merge and (h, x, z) order; the
  approximate `Vector3 ==` in the merge is safe at these parameters
  (4 m spacing / ≥ 1 m height gaps).
- `Scene006PathCertificate` implements §5.4: convexity endpoint checks for
  ball and [8, 32] band; `N = ceil(len/0.25)` inclusive sampling; 1.625 m
  body and 0.375 m tether inflations; closed-set tangency; per-class
  rejection counts (no silent culling); exact segment–prism distance by
  golden section on a convex objective (I verified the convexity argument);
  a conservative AABB broadphase that cannot reject a true violation.
- `Scene006AnchorPreflight` reuses the SCENE-003 auditor with the §5.5
  parameter contract (contract values test-asserted): strict-interior
  support, measured per-candidate support y (requested 0.0 is only the
  ±0.05 contract input; see evidence §4.3), zero-hit and height-conflict
  fail-closed, fail-closed TRS, anchor column/vertical corridor/hover
  sphere as SCENE-003's frozen effective closed sets (I checked the
  SCENE-003 proposal §2: the "participation band [support, hover + 1.5]" is
  a coverage statement over the three volumes, which the auditor
  implements), the new ≥ 1.5 m route sub-gate, and the frozen V2
  disposition for the all-reject case.
- `Scene006ProbeRenderer` renders the 106 pre-registered ticks plus the
  `s_{k*}` prompt (V=1 required, k\* ≤ 10, constructively disjoint), keeps
  gimbal continuity over the full trace, fails loudly on any missing tick
  or missing prompt, and binds trace/scenario/road hashes, optics, pairing
  rule and weights-config paths into the manifest with per-file SHA-256 for
  the prompt.
- `tools/run_scene006_probe.py` implements the seven-step chain in frozen
  order with no PASS branch; recall uses the frozen scouting constants
  (conf ≥ 0.25, IoU ≥ 0.30); the missing-sidecar case is treated as
  `PROBE_INCOMPLETE` (evidence §4.4) — a conservative superset of §5.6
  which I endorse; embedding/margin is report-only; models are constructed
  lazily only at step 5; the probe root is read-only with a path-traversal
  guard.
- Truth-boundary discipline: the Scene006 assembly is Editor-only,
  referenced only by the EditMode test assembly; no runtime assembly, no
  controller and no sensor metadata consumes any truth-derived output.
  All truth-derived values land in evaluation artifacts only.

## BC-SC6 compliance

- **BC-SC6-1** (batch-1 write scope): held — verified by diff enumeration
  and my own narrow write audit (36 paths PASS).
- **BC-SC6-2** (T5 preflight precedes any batch-2 request): held — V2
  recorded; no GO request exists; the handoff returns the anchor direction
  to Acceptance/Ideation. Review PASS does **not** unlock batch 2.
- **BC-SC6-3** (fidelity failures produce no gate value): held — T1 and T1′
  both fail closed on contradiction/incompleteness with NaN/no-recall
  outputs (code + tests + my synthetic checks).
- **BC-SC6-4** (T1′ final gate only returns to Acceptance): held —
  `gate_state: null`, `gate_state_owner: "acceptance"`, no tool PASS state
  exists; the 60° self-check stops at tool state `FAIL`.
- **BC-SC6-5** (T6 must not impersonate runtime initialization): held —
  `s_init` appears only in the proposal and evaluation artifacts; no
  scenario schema field, no Bootstrap change, no runtime placement code.
- **BC-SC6-6** (batch stop points): held — batch 1 stopped at the
  candidate; no batch-2 work exists in the tree.

## T4 unexpected PASS — concurrence

I verified §15's attribution arithmetic end-to-end from the artifact
(`C_hold = 506/540`, the single 34-tick occlusion arc, station
`(148, 20.2, 105)` with `C_station = 1.0`, `G = 34/540 = 0.062963`) and
checked the tools contain no tunable knobs beyond the frozen thresholds.
The PASS is a legitimate consequence of the frozen metric on this scene —
one small avoidable occlusion arc — and carries no body-motion-necessity or
BC-M34-4(b) claim. Concur with §15's framing and limits.

## UNITY_NA position

No `UNITY_NA` is claimed for batch 1 (round 5 explicitly records none), and
none is needed: the batch is Editor-offline tooling plus current-scene
negative baselines, its only Unity-facing obligation is the Edit Mode
suite, and no user Unity case exists to run. I concur with the gate-board
Unity cell ("No Play/capture/session; headless Edit Mode reproduction").
Closure semantics stay with Acceptance.

## Findings

None of these blocks the batch-1 verdict; F1 and F2 carry obligations that
bind **before batch 2**, F3 routes outside this work ID.

1. **F1 — `trace_sha256` is not externally recomputable from the serialized
   trace artifact (fix before any batch-2 reliance).** Applying the
   documented canonical layout (`Scene006Trace.HashStates`: int32-LE `k`,
   then float32-LE bit patterns of position x/y/z and quaternion x/y/z/w)
   to the 541 serialized states of `runtime/p1-scene-006/trace-sinit0.json`
   yields `69c9fd01…`, not the recorded `682dfad0…cca8`. I tested the
   documented layout plus four alternatives and twelve sign-of-zero
   variants; none matches. Every serialized value is float32-exact, and
   `qx`/`qz` are `0.0` in all 541 states, so the most plausible mechanism
   is float32 bit information (e.g. `−0.0` signs from quaternion math) that
   exists in the hashed in-memory states but is normalized by JsonUtility
   on write. Batch-1 impact: none material — the hash is deterministic
   C#-side (`TraceHashIsDeterministicAndSensitive`), all three artifacts
   echo one in-process value, and the states themselves are test-pinned to
   the real vehicle. But the §5.2.2 "SHA-256 绑定" is currently a
   self-attested token: a third party cannot re-derive it from the
   published states. Before batch-2 candidate evidence leans on this
   binding, implementation should make it externally verifiable (serialize
   the exact bit patterns, e.g. hex of `SingleToInt32Bits` per component,
   or define the hash over the serialized bytes).
2. **F2 — §5.4.4 head-trim realized structurally; needs Acceptance
   ratification before batch-2 certificates.** The frozen text says the
   tether head segment `[0, 1.70 m]` "queries all colliders, ignoring only
   the measured support instance", with the remainder ignoring nothing. The
   implementation instead evaluates certificates against the §5.5 obstacle
   set, which excludes **all** road-surface and support-allowlist instances
   along the **whole** path (disclosed in evidence §4.1; the
   `d_trim = 1.70 m` bound `1.70 × sin(13.212980°) = 0.388571 ≥ 0.375` is
   recorded in the T4 artifact). For the batch-1 baseline this is provably
   immaterial (flat scene, 0 path rejections, the bound discharges the
   support-plane case). It is a real semantic difference for future
   grass-anchor candidates adjacent to +0.2 m road surfaces: within roughly
   `d < 2.6 m` of the anchor the literal algorithm would fail a tether
   capsule overlapping a road surface that the structural version never
   sees. The interpretation is defensible from §5.5's exclusion-set
   language ("二者单列判定，不作为障碍参与净空"), but Acceptance should
   either ratify it as the frozen reading or require the literal head-trim
   before batch-2 certificates are consumed.
3. **F3 — full Python suite broken at the base by the coordination batch
   (outside this work ID).** `unittest discover -s tests` fails 1/298:
   `test_check_docs.test_compliant_minimal_status_passes`. Coordination
   batch `902a72c` (COORD-003/004, user-authorized) extended
   `tools/check_docs.py` with the Current-state/Active-handoffs section
   checks without updating `tests/test_check_docs.py` (last touched
   `02d90b5`). The failure reproduces identically at the candidate and at
   its base — not introduced by, and not attributable to, the SCENE-006
   batch, whose claim was 11/11 on its own suite (true). The repo's
   canonical test command currently fails on a clean checkout; fix belongs
   to a user-authorized coordination batch (align the stale test with the
   new checker semantics).
4. **F4 — JsonUtility null-string flattening in the preflight artifact
   (cosmetic).** C# `null` strings serialize as `""`, so legal candidates
   carry `"rejection_reason": ""` (and empty `blocking_object`); a consumer
   testing `is None` counts 0 legal candidates. The numeric `*_count`
   fields are computed pre-serialization and are correct (I recounted with
   the `""` convention and they reconcile exactly). Worth normalizing or
   documenting if any downstream tool consumes the per-candidate records.
5. **F5 — minor observations, no action required.**
   (a) `Scene006Evaluation.Run` folds a fidelity contradiction at `s_0`
   into the global T1 disposition although `s_0` is outside the T1 domain —
   strictly conservative (fail-closed) relative to §5.2.8.
   (b) The route sub-gate accepts `distance ≥ 1.5 − 1e-5` — a 10 µm-scale
   liberal epsilon at a safety boundary, inconsistent in spirit with the
   tangency-is-violation convention; physically immaterial here.
   (c) The baseline artifact's `t6.gate = "PASS"` carries no "descriptive"
   qualifier in the JSON itself; the evidence file and §7.1 make the
   non-gate status clear, but the field could be misread standalone.
   (d) Gimbal-replay fidelity rests on formula transcription plus
   hand-computed cases (Unity only invokes `LateUpdate` in Play); the
   trace, visibility and projection replicas do have direct
   real-component equivalence tests.
   (e) `ArgminOffAxisPhase` evaluates the XZ-projected foot per segment —
   exact for level routes (all current routes are level); a sloped route
   could shift the true argmin. Candidate-side only; the baseline pins
   `s_init = 0`.

## Verdict

**`PASS_WITH_NOTES`** for the batch-1 stable candidate `345b3ea`.

The candidate implements the accepted §5.1–§5.6 contract faithfully within
the BC-SC6-1 write scope; every headline number in the stop-point record —
T1 p05 18.881 FAIL, T2 `L_point` 0.0000 FAIL, T3 total 0.0630 FAIL, T4
G = 0.062963 PASS (attributed), T5 candidate preflight 0/1257
`BLOCKED_ANCHOR_PLACEMENT_V2` with the support-y fix verified, T1′ 60°
self-check FAIL 16/99 — reproduces independently from the committed
artifacts and my own test reruns. This verdict validates the batch-1 tools
and the negative results only: per BC-SC6-2 and the V2 disposition, **no
batch-2 GO request may follow from it**; the anchor direction returns to
Acceptance/Ideation, and the F1/F2 obligations bind before batch-2 evidence
is consumed.

---

# Round 2 — amendment 1 batch 1b (2026-08-03)

Reviewer: review 角色 (independent review, strongest pool; fresh context).
Only legal action exercised: this file plus the status-board sync; zero
implementation files touched. Disposable worktree
`.claude/worktrees/review-P1-SCENE-006-b1b` at the candidate, removed at
close-out.

## Candidate and requirements

- Accepted basis: amendment 1 revision 5 (`ACCEPTED`, Acceptance round 6,
  BC-AM1-1–6), user verbatim authorization §8 a+b+c+d+f with e = A+B
  (ledger entry verified in `docs/authorizations.md`); formal design
  v0.3.13 (`1dbe15f` sync verified as Acceptance-owned).
- Candidate: **`C_1b = 77595c8`**, tool commit **`C_tool = fe37ad2`**
  (B1B-R1 rework chain `3ac640a → 6e9fc64 → d11cae5 → [f6a41e3 REWORK] →
  fe37ad2 → 77595c8`). Diff base = last passed candidate **`345b3ea`**;
  I read the full `345b3ea..77595c8` diff (46 files).
- Stop point: proposal §24 `STOP_CONFIRMED / HANDED_TO_REVIEW` after the
  §23 B1B-R1 rework round.

## Commit topology and write audit (§5.6, reproduced myself)

- `fe37ad2` self-diff touches exactly 5 paths, all inside the frozen tool
  path set; no artifacts. `77595c8` self-diff re-emits the 13 artifacts,
  the evidence file and the status board only; `fe37ad2..77595c8` has
  **zero diff on the frozen tool path set**; `345b3ea..77595c8` has
  **zero diff on `config/` and runtime `Scripts/`**. First-round tool
  commits `3ac640a`/`6e9fc64`/`d11cae5` self-diffs also stay inside the
  tool set (plus the status board, which is not an artifact).
- Reran `python3 tools/check_role_writes.py --role implementation
  --base 345b3ea` in the worktree: the **same 5 non-implementation paths**
  as §23/§24. Per-path `git log` provenance confirms every touching commit
  is the attributed non-implementation batch (ideation revisions 0–5,
  acceptance `1dbe15f`/`960d7aa`/`6bea781`/`daf00d0`, review `c0e8dd1`).
  Attribution reproduced; no unattributed path.
- B1B-R1 topology note: `fe37ad2` sits on the actual capture history above
  the rejected `f6a41e3`, so its tree contains the old artifacts while its
  own diff touches none — exactly the R16 diff-level definition; the
  reworked capture then re-emitted all 13 artifacts in `77595c8`.

## What I reran and reproduced myself

- **Focused Python**: `tests.test_scene006_candidate_check` +
  `tests.test_scene006_trace_hash` = **17/17** in the worktree.
- **Checker, module entry**: `python3 -m tools.scene006_candidate_check
  check` over all 13 artifacts = **13/13 OK**, reproducing route audit
  `CLEAR`, P1 A/B `P1_OK` (10/30 legal pairs), P2 A
  `BLOCKED_GEOMETRY_INFEASIBLE` 0/50, P2 B `P2_OK` 3/150. The
  direct-script invocation `python3 tools/scene006_candidate_check.py`
  fails with `ModuleNotFoundError: No module named 'tools'` — see F8.
- **Trace hashes (F1)**: all 8 v2 trace artifacts recomputed
  cross-process from the published `*_bits` fields alone — 8/8 match.
  The four B z=30 anchors share one `s_init` hence one hash, as declared.
- **Full Python suite**: bare worktree = 315 run, 7F/3E all in
  `test_scene006_probe` (untracked pinned weights absent in a fresh
  worktree → step-1 `FAIL_WEIGHT_HASH` fail-closed; same round-1
  environment artifact; module unchanged in this diff) plus the known F3.
  Main tree at `342f496` (docs-only delta from the candidate, verified):
  **315 run, 1 failure = F3 `test_check_docs` only**, reproducing the
  implementer/Acceptance 314/315 claim; tree stayed clean.
- **Unity Edit Mode, independent rerun — PASS.** I ran the full EditMode
  suite myself on the fresh review worktree
  (`-batchmode -nographics -runTests`, Unity 6000.4.1f1): **206/206
  passed, 0 failed**, including all 44 `Scene006*` cases. (The fresh
  import first logged 2 `CS0246 GUID` errors in the
  `com.unity.shadergraph` package cache and a Tundra failure — zero
  errors in any candidate file — then Unity's automatic rebuild
  recovered and the run completed.) Round 1's environment block did not
  recur; the Unity gate no longer rests on the implementer XML alone.
  I also validated the implementer XML (206/206, engine/date sane) and
  enumerated its 19 new `Scene006Candidate*` cases one-for-one against
  the test source.
- **Independent artifact recomputation** (own script, no checker reuse):
  - identity **values**: all 13 artifacts carry
    `capture_commit = tool_commit = fe37ad2…` (full hash), empty
    porcelain, `scene_saved=false`, scene-file SHA-256 stable, and bind
    the frozen `scenario.default.json` bytes (`f9c92052…` recomputed);
  - scene-state hash equality: route-audit = P1-B = P2-B (one frozen
    §3.3.3 temp scene), P1-A = P2-A, and A ≠ B (relocations applied);
  - P1↔P2 consistency: per-anchor legal-altitude sets match; P2 anchors
    = P1-legal grid anchors (this cross-check is NOT exercised on real
    artifacts by the CLI/tests — see F8 — so I ran it out-of-band);
  - `s_init`: replicated the argmin-off-axis scan from the frozen route
    bytes (+ B translation): 8/8 match the tool
    (A 22.5/24.5; B 176.2279/184.2279×4/186.2279), altitude-independent;
  - trace binding: `states[0]` = `PlaceAtRouteDistance(s_init)` for all
    8 traces; 541 states / horizon 540 / dt float32 0.2;
  - **first-lap replay**: re-implemented the `FirstLapSteps` semantics
    over the serialized states: **538 for all 8 anchors**, matching the
    tool and confirming §23's attribution of the proposal's offline
    472–497 undercount (both sides inside the 540 horizon; no gate
    effect);
  - **P2 gates**: recomputed T1 p05/median/min/max (type-7) from the
    published per-cell domains, the loss decomposition, T2/T3 interval
    gates and the in-band conjunction for **all 200 cells**; the in-band
    set is exactly the 3 evidence cells with exactly the evidence values
    — B `(195,30)` h20 vfov40 (37.061 / 0.3389 / 0.0574 / 0.3963),
    B `(197,30)` h16 vfov35 (30.290 / 0.5000 / 0.0537 / 0.5537),
    B `(197,30)` h16 vfov40 (35.143 / 0.4407 / 0.0648 / 0.5056);
    family A `L_occ ∈ [0.0000, 0.0278]` as claimed (0/50 in band), with
    honest unexpected T1/T2 passes recorded (e.g. h20 vfov30
    `l_point 0.4759` T2 PASS, T3 FAIL);
  - **P1 counts**: 1257 candidates, legal 86 (A) / 158 (B) at **each** of
    the five altitudes, rejection decompositions internally consistent,
    and **no legal candidate with any failing sub-gate**; every legal
    candidate and all 8 screening anchors are grass-supported at
    `support_y ≈ 1.311342e-06`;
  - **§3.3.2 relocations**: the five authorized rows appear verbatim
    (prefab, original xz, segment 6/4/5/2/0, all `left`,
    4.6/4.6/0.8/4.2/4.3, landing positions), `recompute_match` 5/5,
    landing road-coverage and static clearance all true; I additionally
    hand-verified the left-normal arithmetic of all five landings from
    the translated route (including row 3's diagonal 0.8/√2 split) and
    the lexicographic application order;
  - **route legality**: translated-route SCENE-002 audit `CLEAR` with
    road 0 / swept-obstacle 0 (779 audited) / vehicle-corridor 0 (101
    audited); 764 thick obstacle instances as recorded.

## Code review (semantic fidelity)

Read every changed code file line-by-line against the amendment:

- `Scene006CandidateContract`: centres `(150,108)`/`(195,30)`, §5.3 grid
  (2+6 anchors), altitude/vfov axes, `(+60,−60)` pure translation
  (y untouched), and the five authorized rows are frozen constants; an
  EditMode test pins the translated route to the §3.3 listing verbatim
  and the row order to the lexicographic rule.
- `Scene006RelocationSolver`: unique binding (name + xz ≤ 0.1, ≠1 match
  throws); nearest segment with strict-improvement scan ⇒ lowest-index
  tie at ≤ 1e-6; left normal `(-dir.z, dir.x)`; 0.1 m stepping without
  accumulation drift to 30.0 m; constraint (a) 0.25 m-sampled
  footprint-to-route ≥ 2.0 m, (b) 0.25 m-grid full road-surface
  coverage (strict interior), (c) obstacle overlap with only the subject
  excluded (the "763 = 764 − self" accounting), (d) already-placed
  landings in application order; smaller displacement, tie → left;
  landing = **root**-shifted rigid-body position (the `d11cae5` fix);
  closed-set tangency counts as overlap. The 5e-4 compare tolerance is
  the 3-decimal publication rounding level and can only produce a
  fail-closed mismatch, never a silent override
  (`RELOCATION_RECOMPUTE_MISMATCH` / `NO_LEGAL_LANDING` /
  `LANDING_ILLEGAL` all return to Acceptance with artifacts written).
- `Scene006CandidateGenerator`: family-B legality strictly precedes its
  geometry (§3.3.1); landing audits re-verify (b)/(c)/(d) on the applied
  scene with the parked vehicle as audit object (§2.2a/§2.2b); the
  SCENE-002 auditors run on the same applied state; P1 runs the full
  1257-candidate T5 per altitude with the altitude as
  `hover_offset_y_m` (the inherited SCENE-003 contract volumes therefore
  scale per pair); the P1 status ladder implements §5.2's three
  terminals literally; P2 runs only on P1-legal pairs, recomputes
  `s_init` per legal altitude and fails closed on drift; per-anchor v2
  trace artifacts are written before cells; `HORIZON_SHORT` cells carry
  no gate values; capture identity is recorded pre-run on a clean HEAD
  and every artifact write re-hashes the scene file (zero-write proof);
  `EditorSceneManager` never saves (no `SaveScene` anywhere in the
  assembly; `Cleanup` destroys owned objects).
- `Scene006CandidateEvaluation.RunCell`: replicates the reviewed
  baseline per-sample loop (frozen gimbal init + replay, 15-sample
  `≥ 0.2` predicate, denominators `s_1..s_540`, type-7 quantiles,
  `ProjectBounds`); T4/T6 are **not** computed (P3-authoritative, §5.3);
  fidelity contradictions terminal the cell with no gate values
  (BC-SC6-3; the `s_0` fold-in stays conservative as in round 1 F5(a)).
- `Scene006Visibility.OccludingRoots`: the predicate refactor is
  byte-equivalent (`HasClearLineOfSight` delegates to
  `OccludingRoots(...).Length == 0`; same trim, layers, trigger mode,
  target-subtree skip); attribution reports sorted distinct top-level
  root names; an EditMode test pins predicate equivalence.
- **F1** (`Scene006TraceArtifact` + `tools/scene006_trace_hash.py`):
  v2 publishes per-component float32 bit patterns; the hash layout is
  unchanged; C# and Python rebuild the canonical bytes independently and
  a Python-constructed fixture (with a pinned negative-zero `80000000`)
  nails both to one byte sequence; `Write` self-checks recomputability.
  Round-1 F1 is discharged for v2 artifacts (batch-1 v1 stays frozen).
- **F2** (`Scene006PathCertificate` + `Scene006SceneRig`
  `BuildAllInstancePrisms`): literal §5.4.4 — only the bound measured
  support instance is exempt, and only over the head `[0, 1.70 m]` of
  the tether; the remainder and every other instance (road surfaces as
  0.2 m slabs from road_data, support-allowlist instances included) are
  queried in full; naming an absent binding throws. Tests cover the
  three-state semantics and the head-trim distance. The batch-1
  baseline path (null binding + T5 set) reproduces the historic
  structural form; batch-1 T4 numbers are not re-run. F2 is discharged
  as an implementation; its consumption is P3/batch-1c.
- **F4** (`Scene006AnchorPreflight`): per-candidate `legal` boolean
  computed pre-serialization is authoritative; `""` documented as the
  no-value convention; schema v2; batch-1 v1 artifact untouched; the
  checker reconciles `legal == (rejection_reason == "")` per candidate.
  Round-1 F4 is discharged.
- **B1B-R1**: `Scene006TraceArtifact.Write` fails closed on any missing
  identity field, dirty porcelain, scene-hash mismatch or
  `scene_saved`; the cross-process checker enforces the same on the
  trace schema; negative tests exist on both the C# and Python sides
  (missing capture, dirty porcelain, before/after mismatch, dual-commit
  divergence). §23's rework conditions are all met: schema + checker
  + tests changed in a new tool commit whose own diff touches only
  frozen tool paths, and the complete batch was re-captured on clean
  `fe37ad2` (no hand-patched JSON; values match the round-1 claims).

## BC-AM1 compliance

- **BC-AM1-1**: only §8 a+b+c+d+f, e=A+B executed; exact centres, pure
  translation, five frozen rows; no approximate/recomputed coordinate
  ever replaces an authorized one (mismatch is fail-closed) — held.
- **BC-AM1-2**: both families ran P1+P2 completely; no priority, no
  early stop; P3/`F` untouched (batch 1c) — held.
- **BC-AM1-3**: batch 1b stopped at `C_1b`; Acceptance ran the base
  write audit (reproduced); no batch-1c work exists in the tree — held.
- **BC-AM1-4**: the three relocation terminals are implemented
  fail-closed with artifacts, and none was reached in the accepted run
  (the two earlier tool defects — dropped serialization rows and the
  centroid/root confusion — were implementer self-test failures fixed in
  `6e9fc64`/`d11cae5` before the clean capture; the final tool changed
  no authorized content, 5/5 verbatim) — held.
- **BC-AM1-5**: dual identity on **all 13** artifacts with equal commits
  (no zero-diff proof owed), frozen tool path set declared in the
  evidence, topology per R16 — held.
- **BC-AM1-6**: zero `config/`/scene writes (diff-verified), zero
  Play/capture, zero scenario/session/run IDs (the only new identity
  string is the audit report label
  `…-scene006-familyb-candidate`, which creates no bytes or session);
  batch 2 remains `BLOCKED_USER_GO` — held. **No batch-2 GO follows
  from this verdict.**

## UNITY_NA position

No `UNITY_NA` is claimed for batch 1b and none is needed: the batch is
Edit-Mode/offline with zero Play and zero capture; its Unity-facing
surface is the Edit Mode suite, which I independently reran (206/206).
I concur with the gate-board treatment.

## Findings (round 2; F1–F5 numbering continues from round 1)

None of these blocks the batch-1b verdict or batch 1c. F6/F7 carry
Acceptance obligations; F8 is cleanup.

1. **F6 — frozen support semantics admit ground-level road_data
   surfaces as anchor support; surfaced by family B, zero effect here;
   needs Acceptance disposition.** `P1Scene003AnchorAuditor.SupportAt`
   (frozen `Scripts/` code, unchanged by this batch, PASS-reviewed in
   SCENE-003/004 and batch 1) treats **every** `road_data.json` surface
   patch strictly containing the candidate as a support match; the
   support allowlist filters only scene-root instances. The ±0.05 m
   height gate rejected such candidates so far because road surfaces
   sit at 0.2000004 (batch-1's 70 `SUPPORT_HEIGHT_MISMATCH`). But
   road_data contains **5 ground-level paved patches (y ≈ 0)**, and
   family B's lattice overlaps one (`Road Tile@210,30`, x∈[200,220],
   z∈[10,50]): **230 candidates are `support_status=PASS` with
   `support_ids=['Road Tile@210,30']`, support y 4.37e-07** — pavement,
   not allowlist grass. Verified consequences: all 230 are
   clearance-rejected by `Building_Factory` at every altitude, so the
   legal sets (86/158), every screening anchor, P2 and the 3 in-band
   cells are unaffected (I checked every legal candidate is
   grass-supported); batch-1c finalists are grass anchors, so 1c is not
   gated. But this contradicts the §5.5 design-text reading that
   support comes from the two-grass allowlist, and it is the actual
   cause of the artifact's B support/clearance decomposition
   **300/799** diverging from the proposal's §3.3 diagnostic
   **530/569** — a §10 geometric-prescreen-class divergence that the
   evidence did not disclose and nobody attributed. Obligation:
   Acceptance should record the attribution and either ratify
   "ground-level road_data surfaces within height tolerance count as
   support" as the frozen reading or require an allowlist-only support
   fix **before any future lattice overlapping a ground-level paved
   patch is consumed**; no change is required for this batch's
   conclusions.
2. **F7 — family A route-rejection diagnostic: tool 52 vs proposal
   §3.2's 0; tool is right; attribution missing.** The A lattice centre
   `(150,108)` is 9.5 m from the frozen route's north edge (z = 117.5),
   so candidates at z ∈ {116.5, 117, 117.5, 118} fail the ≥ 1.5 m route
   sub-gate: 21+17+13+1 = **52 at every altitude** (my geometric recount
   matches the artifact exactly; z = 116.0 passes via the pre-existing
   `−1e-5` epsilon, round-1 F5(b)). The proposal's §3.2 table row
   "路线子门拒绝 0" is wrong; all 52 are support-shadowed (off the grass
   tile), so legal counts are unaffected. Same §10 obligation as F6:
   tool value stands; Acceptance should attribute the divergence. The
   evidence's "与提案 §3.2/§3.3 的离线诊断（86 / 158、五高度不变）逐项
   一致" is literally true for its parenthetical scope but incomplete as
   a diagnostic-consistency statement — F6+F7 are the two columns where
   the tables and the tool disagree.
3. **F8 — checker wrapper and cross-check gaps (non-blocking cleanup
   before 1c relies on the CLI).** (a) The direct-script invocation
   `python3 tools/scene006_candidate_check.py …` fails
   (`ModuleNotFoundError: No module named 'tools'`); only the module
   entry works. The shebang and `__main__` block imply direct
   invocation, and evidence §7's own command line is written in the
   broken form (§24 already corrects it to the module entry). Assessed
   **non-blocking**: the canonical module entry, the tests and my
   independent recomputation all verify the artifacts. Actionable
   cleanup: absolute-import wrapper or documented module-entry-only.
   (b) `check_p2`'s P1-cross-checks (scene-state equality, legal-pair
   consistency) run only when `p1_path` is passed, which neither the
   CLI dispatcher nor the real-artifact test does — the capability
   exists but is not exercised on real artifacts; I ran both checks
   out-of-band and they pass. (c) `check_p1` reconciles support/route
   counts but not `clearance_rejection_count` (I reconciled it
   independently). Suggested: wire `p1_path` into the real-artifact
   test and add the clearance reconciliation.
4. **F9 — minor observations, no action required.**
   (a) `Scene006AnchorPreflight`'s class doc-comment still describes
   the batch-1 fixed `hover_offset_y_m = 20.0` while `RunMode` is now
   altitude-parameterized; stale comment only.
   (b) `Scene006TraceArtifact.Build` labels `first_lap_status`
   "MEASURED" for any positive count; `FirstLapSteps` can only return
   −1 or ≤ 540, so the branch cannot disagree with the generator's
   `HORIZON_SHORT` check — by construction, not by assertion.
   (c) The worktree full-suite probe failures (7F/3E) are the round-1
   documented missing-untracked-weights artifact, not a regression;
   the module is unchanged in this diff.

## Verdict

**`PASS_WITH_NOTES`** for the batch-1b stable candidate
`C_1b = 77595c8` (tool commit `fe37ad2`).

The reworked batch 1b implements the accepted amendment faithfully
inside the authorized write scope; B1B-R1 is closed with per-artifact
§5.6 identity enforced fail-closed on both sides; F1/F2/F4 are
discharged; every headline number — route audit CLEAR with 5/5 verbatim
relocations, P1 `P1_OK` 86/158 × five altitudes, P2 A 0/50
`BLOCKED_GEOMETRY_INFEASIBLE`, P2 B 3/150 `P2_OK`, first lap 538 × 8,
all 13 identities on clean `fe37ad2` — reproduces independently from
the committed artifacts, my own recomputations, and my own Unity
206/206 rerun. This verdict is the §5.6 ③ gate: **batch 1c (P3) may
start** on the frozen terms (tool unchanged ⇒ zero-diff proof against
the declared path set; any tool change ⇒ `C_tool′` re-review; review
endpoints `C_1b..C_1c`). It does **not** unlock batch 2, config/scene
bytes, Play/capture or any scenario/session/run ID (BC-AM1-6), and the
F6/F7 attributions belong to Acceptance before or alongside the 1c
acceptance round.

---

# Round 3 — batch 1c tool stage `C_tool′` (2026-08-03)

Reviewer: review 角色 (independent review, strongest pool; fresh context).
Only legal action exercised: this file plus the status-board sync; zero
implementation files touched. Disposable worktree
`.claude/worktrees/review-P1-SCENE-006-b1c` (created at `7a103ff`, later
detached to `06bbf86` for the probe run), removed at close-out.

## Candidate and requirements

- Accepted basis: proposal §25 (`REVIEW_NOTES_DISPOSED /
  BATCH1C_AUTHORIZED`, BC-B1C-1–5) and §26 stop audit
  (`TOOL_STOP_CONFIRMED / HANDED_TO_REVIEW`); design v0.3.13 unchanged.
- Tool candidate: **`C_tool′ = 06bbf86`**; evidence/stop commit
  `7a103ff`. Diff base = last passed candidate **`77595c8`**; I read the
  full `77595c8..7a103ff` diff (14 files).
- Handoff constraint honoured: **no authoritative P3 artifact was run or
  committed**. The one `RunBatch1c` execution below was a
  worktree-internal probe on the disposable copy (explicitly allowed by
  the handoff and evidence §5), its output was never copied out, and it
  is **not** P3 evidence; the worktree including that output is deleted.

## Commit topology and write audit (reproduced myself)

- `06bbf86` self-diff touches exactly **8 paths**, all inside the frozen
  tool path set declared at the batch-1b stop (2 Editor classes + 2
  `.meta`, 1 EditMode test + `.meta`, checker + its Python test); zero
  artifacts, `config/`, scenes, runtime `Scripts/`. `7a103ff` self-diff
  is the evidence file, status board and one mechanical archive move.
- The three intervening commits are all attributed non-implementation
  batches: `342f496` (§24, Acceptance), `1b7a9dd` (review round 2, this
  file), `0d5e5f0` (§25, Acceptance). Only `06bbf86` touches the frozen
  tool path set anywhere in the range (`git log` per-path verified).
- Reran `python3 tools/check_role_writes.py --role implementation
  --base 77595c8` in the worktree at `7a103ff`: the **same 2
  non-implementation paths** as §26 (proposal file, this review file),
  both fully attributed; no unattributed path. Full-range diff shows
  zero `config/`, zero `Scripts/`, zero `.json` artifact changes, and no
  P3 artifact exists on disk in the main tree or the range.

## What I reran and reproduced myself

- **Unity Edit Mode, independent rerun — PASS**: full suite on the fresh
  worktree at `7a103ff` (Unity 6000.4.1f1, `-batchmode -nographics
  -runTests`): **214/214 passed**, and the 8 `Scene006Finalist*` cases
  match the test source one-for-one. The implementer XML
  (`runtime/test-results/p1-scene-006-editmode-b1c.xml`) also reads
  214/214 with the same 8 cases.
- **Focused Python**: `tests.test_scene006_candidate_check` = **18/18**
  in the worktree (system python), including the 6 new P3 tests.
- **Full Python suite**: main tree at `5976edf` (clean), `.venv-track`:
  **321 ran, 1 failure = known F3** (`test_check_docs`, coordination
  base breakage `902a72c`) — reproducing the §26 claim. Bare worktree
  with the same venv: 321 ran, 8F/3E = F3 + the documented
  missing-untracked-weights `test_scene006_probe` environment artifact
  (module unchanged in this diff; same decomposition as round 2).
- **Checker, module entry**: 13/13 OK over all batch-1b artifacts,
  reproducing route `CLEAR`, P1 A/B `P1_OK` (10/30 pairs), P2 A
  `BLOCKED_GEOMETRY_INFEASIBLE` 0/50, P2 B `P2_OK` 3/150, 8/8 trace
  cross-process hashes.
- **Independent §5.4 recomputation** (own script, no checker reuse):
  from the real P2 family-B artifact the in-band set is exactly the 3
  reviewed cells; binary64 margins/scores recompute to
  `(197,30) h16 vfov40 = 0.08465603419712611` >
  `(195,30) h20 vfov40 = 0.04232822145734513` >
  `(197,30) h16 vfov35 = 0.0` (m_T2 at the 0.50 edge), finalist
  `(197,30) h16 vfov40` — matching the tool, the EditMode expectations
  and evidence §5. The EditMode test's hard-coded inputs match the
  artifact values **bit-for-bit** (verified all 12 numbers). My own
  lattice re-implementation reproduces `AnchorRank`: 1257 points,
  (dist², x, z) order identical to the frozen `CandidatePositions`
  LINQ ordering (round-trip float arithmetic exact at these values;
  boundary ε differences inert below the 0.25 granularity).
- **BC-B1C-2 preconditions on the real artifacts**: all three in-band
  cells (finalist included) are `legal=true` with exactly one support id
  `Natures_Grass Tile Small`, canonical name in the two-grass allowlist,
  altitudes consistent with `grid_anchors`, support y ≈ 1.311e-06; the
  finalist cell's `trace_sha256` equals the
  `P1-SCENE-006-trace-B-197.0-30.0.json` artifact hash and `s_init`
  matches exactly.

## Code review (semantic fidelity)

- `Scene006FinalistSelection`: the four margin formulas and constants
  are §5.4 verbatim; input finiteness precedes all margin arithmetic
  (`SCORE_INPUT_NOT_FINITE` returns before any formula; a +Inf p05
  cannot launder through `min(…, 1.0)`); margin/score finiteness fails
  closed (`SCORE_NOT_FINITE`); score equality is binary64 `==` via the
  `!=`-then-`>` comparator, so `+0.0 == −0.0` falls through to the next
  tie-break field (the comment correctly rejects `CompareTo`); terminal
  cells exit `F` before ranking, so NaN never reaches the comparator;
  tie-break chain is score desc → vfov asc → altitude asc → family
  ordinal (`CompareOrdinal`, A < B) → §5.5 lattice rank asc; empty `F`
  is `BLOCKED_GEOMETRY_INFEASIBLE`. Total order ⇒ unique finalist.
- `Scene006FinalistGenerator`: inputs are only the two reviewed
  family-B P1/P2 artifacts, hash-bound (`Bind`) and schema/state-gated
  (`P1_OK`/`P2_OK`); selection precedes BC-B1C-2, which runs before any
  scene/gate work and fails closed to `SUPPORT_SEMANTICS_MISMATCH`
  (the five mismatch classes match BC-B1C-2 literally; road_data ids
  like `Road Tile@210,30` cannot pass the ordinal grass-allowlist check
  — F6 non-ratification is enforced in the tool); trace is regenerated
  and compared to the P2 cell binding (`TRACE_BINDING_MISMATCH`); the
  T5 re-audit reuses the frozen `RunMode` candidate contract at the
  finalist altitude; T4 takes `C_hold` from the P2 cell `c_geom`
  (`c_hold_source = "p2_cell_c_geom"`, never recomputed) with
  certificates from the F2-literal path (`BuildAllInstancePrisms` full
  instance set + bound-instance-only head-trim; absent binding throws);
  T6 takes the size-gate median from the P2 cell, scans k = 0..10 with
  the frozen gimbal bootstrap (no update at k = 0), and routes a
  visible-but-unprojectable prompt to `PROBE_FIDELITY_CONTRADICTION`;
  station replay denominators are exactly `s_1..s_540` per station with
  independent gimbal replays; certificate failures never enter the max.
  Support-id naming is consistent end-to-end (auditor `SupportAt`
  records grass `root.name` / road `surface.id`; prisms carry the same
  ids; `CanonicalPrefabName` strips only ` (N)` clone suffixes, ordinal
  compare — the two grass names cannot alias). Capture identity requires
  clean porcelain pre-run, records `capture_commit = tool_commit = HEAD`
  (§5.6 ④ by construction), and asserts scene-file SHA-256 before ==
  after with `scene_saved = false`; the artifact write is atomic;
  no scenario/session/run ID is created (`source_scenario_id` reads the
  frozen config identity as in batch 1b).
- `ModeReportsEqual` compares all 15 serialized `CandidateRecord` fields
  plus report-level counts/status — full-field as claimed — **but see
  F10: its float comparisons use IEEE `!=`, so NaN-valued fields make
  identical reports compare unequal.** Report-level
  `anchor_contract_sha256` is not compared in C#, but the checker
  requires the recorded P1/recheck contract hashes to equal the P1
  artifact's value, which covers parameter divergence.
- `tools/scene006_candidate_check.py check_p3`: binds the P3 artifact to
  the exact P1/P2 file hashes; **re-derives** the §5.4 ordering in
  binary64 (the 1e-9 absolute tolerance applies only to reconciling the
  stored margin/score copies, never to the ordering, so serialization
  noise cannot smuggle a different finalist); recomputes the BC-B1C-2
  expected-ok per cell from the P1 artifact with equivalent canonical
  semantics; enforces the terminal-status state machine (mismatch
  status ⇔ a failing record, trace status ⇔ hash inequality, T5 status
  ⇔ `equal: false`), T4 count/gain/gate arithmetic and the T6 window,
  k\*, prompt and gate recomputation, and the final
  `P3_OK`/`BLOCKED_FINALIST_AUDIT_FAILED` conjunction. Dispatch without
  `--p1-path/--p2-path` fails closed (tested). F8(b) is discharged (the
  real-artifact test now passes `p1_path` for both P2 files and the
  cross-checks run); F8(c) is discharged (`check_p1` reconciles
  `clearance_rejection_count` with the fixture corrected to the real
  auditor semantics); F8(a) remains open per BC-B1C-4 (non-mandatory).
- New `.meta` files are minimal with unique GUIDs; both new classes live
  in the existing Editor-only `TetheredTracking.Scene006.Editor`
  assembly; zero runtime-assembly surface (truth boundary unchanged).

## Worktree probe (not P3 evidence)

To exercise the real-scene path the synthetic tests cannot reach, I ran
`RunBatch1c` once **inside the disposable worktree**, detached to
`capture_commit = tool_commit = 06bbf86` exactly as §26 prescribes
(clean porcelain, `Library/` imported fresh). The §26 identity
discipline is therefore **executable as written**. The probe artifact
stayed in the worktree and is deleted with it; per the handoff it is
not P3 evidence and pre-judges no gate value. Probe observations:

- Selection, BC-B1C-2 and trace binding behaved exactly as reviewed:
  `f_count = 3`, finalist `(197,30) h16 vfov40` score
  `0.08465603419712611`, all three support records ok, trace hash
  match, identity fields correct, scene file hash unchanged, and the
  probe's `scene_state_sha256` **equals the batch-1b P1 capture's**
  (`75b84083da0f…`) — the §26 scene-reconstruction chain reproduces the
  reviewed scene state.
- The run then terminated **`T5_RECHECK_DIVERGENCE`** at
  `candidate[305] (190, 30)` with **identical** P1/recheck contract
  hashes — which exposed F10 below. `check_p3` validated the artifact
  as a consistent `T5_RECHECK_DIVERGENCE` state (the terminal state
  machine works end-to-end).
- The probe reached only the T5-recheck stage; real-scene T4/T6
  execution remains unexercised (synthetic-only coverage), which is
  acceptable for this stop but means the next tool round's probe should
  re-run the chain past T5.

## Findings (round 3; numbering continues)

1. **F10 — BLOCKING (the rework): `ModeReportsEqual` treats NaN fields
   as unequal, so the T5 re-audit diverges on every real family-B P1
   report and P3 can never reach T4/T6.** `SupportAt` legitimately
   records `support_surface_y_m = NaN` for `SUPPORT_NOT_FOUND`
   candidates; the family-B P1 artifact has **288 such candidates at
   every altitude, first at rank 305 = (190, 30)**. The comparator's
   `left.support_surface_y_m != right.support_surface_y_m` is IEEE
   `NaN != NaN = true`, so **`ModeReportsEqual(x, x) = false`** for
   every real report — I proved this from the artifact alone by
   applying the comparator semantics to the P1 report against a deep
   copy of itself (first divergence at index 305, exactly where the
   probe diverged; all five altitudes share first-NaN index 305). The
   §5.3 contract "重跑必须与 P1 结果逐项相同" is about value identity;
   a re-run that byte-identically reproduces P1 must compare equal.
   Fail-closed direction is preserved (no wrong gate value can pass),
   but the accepted P3 procedure is structurally unexecutable at
   `06bbf86`. The synthetic comparator test missed it because its
   fixture uses a finite support height. **Rework**: NaN-aware equality
   for the float fields (both-NaN — or bit-level equality — counts as
   same; real divergence detection must not weaken), plus a regression
   test whose fixture contains a NaN-bearing candidate; any fix is a
   frozen-tool-path change and must stop at a new `C_tool′` commit for
   write audit and re-review per BC-B1C-3 before any P3.
2. **F11 — checker cannot validate the two pre-scene P3 terminals;
   evidence §4.5's claimed exemption is not implemented.**
   `_check_capture` unconditionally requires a non-empty
   `scene_state_sha256`, but the generator by design writes it empty
   for `BLOCKED_GEOMETRY_INFEASIBLE` and `SUPPORT_SEMANTICS_MISMATCH`
   (produced before the scene opens). Such artifacts would fail
   `check_p3` with a misleading "scene hash missing" error, and the
   scene-stage conditional inside `check_p3` is dead code. Unreachable
   for the real bound inputs (F = 3 non-empty; all support records
   verified ok), and fail-closed in direction — but the checker's
   declared semantics and the code disagree. Fix alongside the F10
   tool round (checker is a frozen tool path).
3. **F12 — terminal-scored cells are dropped from the ranking table
   instead of being recorded with their terminal label.** §5.4 requires
   the ranking table "含每格的终态标签"; `Select` excludes
   `SCORE_INPUT_NOT_FINITE`/`SCORE_NOT_FINITE` cells from `Ordered`, so
   they would be absent from the artifact, and the checker's
   `f_count == len(in-band cells)` / non-finite `_require` would reject
   such an artifact rather than validate it. Unreachable from any
   authentic `P2_OK` artifact (in-band implies finite gate inputs);
   fail-closed preserved. Note-level; fold into the next tool round if
   convenient.
4. **F13 — checker's T6 gate model omits `PROBE_FIDELITY_CONTRADICTION`.**
   The C# T6 writes that gate for a visible-but-unprojectable prompt;
   `check_p3` only models PASS/FAIL and would report a generic
   "t6 gate" failure on such an artifact. Fail-closed, unreachable in
   the expected path, note-level.
5. **F14 — minor observations, no action required.**
   (a) The T5 divergence record stores only the pointer
   (`candidate[305] (190, 30) differs`), not the two differing values;
   diagnosis required my probe — worth enriching when F10 is fixed.
   (b) The checker verifies `best_c_station`/`g_station` by value but
   not that `best_station_index` is the first-in-order argmax (C#
   strict-`>` semantics); value-level equivalence is what the gate
   consumes.
   (c) `P3Report.batch = 12` follows the batch-1b `batch = 11` internal
   encoding (1b→11, 1c→12); consistent, slightly opaque.
   (d) A committed `C_1c` capture from detached HEAD `06bbf86` will
   fork history from the three later docs commits; Acceptance should
   plan the reconciliation (merge or re-parent of docs commits) while
   keeping the §26 requirement `capture HEAD = tool commit` intact —
   process note, not a tool defect.

## BC-B1C compliance

- **BC-B1C-1**: held in code and probe — inputs are only the reviewed
  hash-bound artifacts; the in-band set derives from the P2 flags (= the
  3 reviewed cells); no new grid/threshold/route/scene content anywhere.
- **BC-B1C-2**: held — implemented fail-closed before any gate value
  with the five mismatch classes; real-artifact preconditions verified.
- **BC-B1C-3**: held — the zero-diff question was answered honestly
  (P3 components absent from the frozen set), `C_tool′` self-diff stays
  inside the frozen tool paths, and **no P3 artifact was run or written
  by the implementation** (my worktree probe is review action under the
  handoff's explicit allowance, non-evidence, deleted).
- **BC-B1C-4**: moot (tool changed); the canonical module entry works
  and F8(a) remains correctly non-mandatory.
- **BC-B1C-5**: not yet reached (no `C_1c`); nothing in the range or on
  disk violates it — zero config/scene bytes, zero Play/capture, zero
  scenario/session/run IDs; batch 2 stays `BLOCKED_USER_GO`.

## UNITY_NA position

No `UNITY_NA` is claimed for the batch-1c tool stage and none is
needed: it is Edit-Mode/offline tooling with zero Play and zero
capture; its Unity-facing surface is the Edit Mode suite, which I
independently reran (214/214). I concur with the gate-board treatment.

## Verdict

**`REWORK_REQUIRED`** for the batch-1c tool candidate
`C_tool′ = 06bbf86` (diff `77595c8..7a103ff`), returning to the same
tool stop per §26.

Everything else at this stop verifies: the §5.4 selection is faithful
to the letter (margins, binary64 `==`, complete tie-break, finiteness
fail-closed) and reproduces independently from the real artifacts; the
BC-B1C-2 guard, trace binding, T4/T6 P2-source discipline, capture
identity and checker state machine are correct; the write audit,
topology and test counts (Unity 214/214, focused 18/18, full 321 with
only known failures) all reproduce. But F10 makes the accepted P3
procedure unexecutable: the T5 re-audit comparator spuriously diverges
on every real family-B report (proved from the artifact alone and
demonstrated end-to-end by the worktree probe at exactly the §26
capture identity). The fix is a frozen-tool-path change: per BC-B1C-3
it must land as a new tool commit with implementer tests (including a
NaN-bearing comparator fixture), F11 fixed in the same round, then stop
for Acceptance write audit and independent re-review **before any P3
artifact is run or written**. F12/F13 are non-blocking cleanups;
F14(d) is a process note for Acceptance. Batch 2 remains locked.

---

# Round 4 — batch 1c reworked tool `C_tool′` (2026-08-03)

Reviewer: review 角色 (independent review, strongest pool; same fresh
session as round 3, re-invoked on the reworked candidate). Only legal
action exercised: this file plus the status-board sync; zero
implementation files touched. Disposable worktree
`.claude/worktrees/review-P1-SCENE-006-b1c2` (created at `9245601`,
detached to `e7213e5` for the probe), removed at close-out.

## Candidate and requirements

- Accepted basis: proposal §27 (`REWORKED_TOOL_STOP_CONFIRMED /
  HANDED_TO_REREVIEW`) on top of §25 BC-B1C-1–5 and §26; design
  v0.3.13 unchanged.
- Reworked tool candidate: **`C_tool′ = e7213e5`**; evidence/stop
  commit `9245601`. Frozen endpoints **`77595c8..9245601`** (9
  commits); I verified every commit: only `06bbf86` and `e7213e5`
  touch the frozen tool path set, the rest are the attributed
  docs/status batches (including my own `d7ba972` round-3 record);
  full-range diff has zero `config/`, `Scripts/`, artifact-JSON or
  scene changes, and no P3 artifact exists on disk or in the range.
- `e7213e5` self-diff touches exactly the 5 declared frozen tool/test
  paths (both finalist Editor classes, the finalist EditMode test, the
  Python checker and its tests); `9245601` is evidence/status/archive
  only. Reran the implementation write audit at base `77595c8`: the
  same **2 non-implementation paths** as §27, per-path commit
  provenance exactly matching §27's attribution table (proposal ←
  Acceptance `342f496`/`0d5e5f0`/`5976edf`; review file ← Review
  `1b7a9dd`/`d7ba972`); no unattributed path.

## F10–F13 closure verification

- **F10 closed.** `ModeReportsEqual` now routes all six float fields
  and the report-level `hover_offset_y_m` through
  `SameFloat(l, r) = l == r || (IsNaN(l) && IsNaN(r))`; field coverage
  is unchanged (rank, 6 floats, 6 strings, `legal`, `support_ids`
  length + per-id), and divergence messages now carry the field name
  and both values (round-3 F14(a) enrichment). My artifact-only proof
  re-run under the new semantics: the P1 family-B report vs a deep
  copy of itself now has **zero divergences at all five altitudes**
  (previously first divergence at rank 305), while NaN-vs-finite on
  `support_surface_y_m` is still detected and named. The new
  `T5RecheckComparatorTreatsBothNaNAsSame` regression pins both
  directions with a NaN fixture.
- **F11 closed.** `_check_capture` gained `require_scene_state`;
  `check_p3` passes `status in scene_stages`, so the two pre-scene
  terminals must carry an **empty** scene-state hash and the four
  scene-stage statuses a non-empty one — both wrong combinations are
  rejected (stricter than round 3 asked, correctly so). The round-3
  dead conditional is gone. `test_pre_scene_terminal_allows_empty_
  scene_hash` covers all three combinations with a consistent
  underlying mismatch record; other artifact types keep the default
  strict behaviour.
- **F12 closed.** `SelectionResult.Table` = ranked cells (rank 0..n−1)
  followed by terminal-labeled cells (rank −1); the P3 artifact
  serializes the Table; `f_count` still counts only scored cells;
  terminal cells still never enter `F` or the finalist. The checker
  now requires the ranking to cover **every** in-band cell, verifies
  ranked rows carry no terminal, and matches each terminal row's
  membership, recomputed label and rank −1, failing on omissions.
  `SelectionTableKeepsTerminalLabels` and
  `test_ranking_keeps_terminal_labels` cover both sides.
- **F13 closed.** For a recomputed non-finite prompt min-side with
  k\* ≥ 0, the checker now requires the recorded value to be
  non-finite and the T6 gate to be `PROBE_FIDELITY_CONTRADICTION`,
  which forces overall `BLOCKED_FINALIST_AUDIT_FAILED` through the
  final conjunction — matching the C# state machine.
  `test_t6_fidelity_contradiction_gate` covers it.

## What I reran and reproduced myself

- **Unity Edit Mode**: full suite on the fresh worktree at `9245601` —
  **216/216 passed** (214 + the 2 new finalist cases, enumerated
  one-for-one); the implementer XML
  (`runtime/test-results/p1-scene-006-editmode-b1c2.xml`) also reads
  216/216 with the same case set.
- **Focused Python**: `tests.test_scene006_candidate_check` =
  **21/21** (18 + 3 new).
- **Full Python**: main tree at `1f5b9f2` — **324 ran, 1 failure =
  known F3 only**, reproducing §27's 323/324. Bare worktree: 324 ran,
  8F/3E = F3 + the documented missing-untracked-weights
  `test_scene006_probe` set (module untouched; same decomposition as
  rounds 2–3).
- **Checker regression**: module entry over all 13 batch-1b artifacts
  = **13/13 OK** (no regression from the checker rework).
- **Selection semantics unchanged**: the §5.4 scoring path has no
  diff except the Table addition; the probe reproduces the round-3
  finalist and score exactly.

## Worktree probe (required by §27; not P3 evidence)

Per the handoff I ran one disposable `RunBatch1c` at clean HEAD
**exactly `e7213e5`** in the worktree (porcelain empty pre-run). The
output stayed in the worktree, was validated, then deleted; it is
review evidence only and **not** a P3 artifact; formal P3 must still
be captured by Implementation from clean HEAD `e7213e5`.

- The chain **passed the prior blockage**: T5 recheck `equal = true`
  with both contract hashes equal to the P1 value — rank 305 no
  longer diverges — and proceeded through T4 and T6 to a scene-stage
  terminal, exercising every stage of the state machine.
- Identity and zero-write discipline held: `capture_commit =
  tool_commit = e7213e5`, empty porcelain recorded, scene-file
  SHA-256 before == after, `scene_saved = false`, and the probe's
  `scene_state_sha256` equals the batch-1b P1 capture's
  (`75b84083…`) — the §26/§27 identity procedure is executable as
  written on the reworked tool.
- Selection/support/trace stages matched round 3 bit-for-bit:
  `f_count = 3`, no terminal rows, finalist `(197,30) h16 vfov40`
  score `0.08465603419712611`, all three support records ok, trace
  hash bound.
- T4/T6 consumed the P2 values verbatim: `c_hold =
  0.49444442987442017` equals the finalist cell's `c_geom` and the T6
  size-gate median `63.25716018676758` equals the cell's
  `t1_min_side_median_px` (both checked against the real P2 artifact
  by my own read as well as by the checker).
- The probe completed with a coherent scene-stage status
  (**`P3_OK`**: T4 gate PASS — 1039 stations, 183 certificates
  passed, 478 body / 842 tether / 0 path rejections, best station
  index 847 with `C_station = 1.0`, `G = 0.5055555701255798 ≥ 0.05`;
  T6 gate PASS — `k* = 2`, prompt min-side `143.2294464111328 ≥`
  median), and the canonical checker validated the artifact
  (`check_p3` → OK). **These numbers are probe observations for
  review purposes only** — the authoritative P3 gate values are
  whatever Implementation's formal capture produces; if the formal
  run diverges from this probe, that divergence itself needs
  attribution before consumption.
- After validation I deleted the probe artifact; the worktree returned
  to clean before removal.

## Findings (round 4; numbering continues)

1. **F15 — minor observations, no action required.**
   (a) The checker's `_score_cell_margins` returns `None` for both
   non-finite inputs and non-finite margins, and `expected_terminals`
   labels every such cell `SCORE_INPUT_NOT_FINITE`; a hypothetical C#
   `SCORE_NOT_FINITE` row (finite inputs, overflowed margins) would
   fail the label recompute. Unreachable for in-band cells (gate
   values are band-bounded, p05 is image-bounded), and any mismatch
   fails closed — asymmetry noted for completeness.
   (b) Round-3 F14(d) still stands as a process note: a formal `C_1c`
   captured from detached `e7213e5` will fork history from the later
   docs commits (`9245601`, `1f5b9f2`, this round's record);
   Acceptance should plan the reconciliation while keeping
   `capture HEAD = tool commit` intact.
   (c) The probe demonstrates the T4 station replay cost (~0.5 M
   visibility evaluations) is tractable headless — no runtime-budget
   concern for the formal P3.

## BC-B1C compliance

- **BC-B1C-1/2**: unchanged semantics re-verified on the reworked
  code; the probe consumed only the two hash-bound reviewed artifacts
  and produced the identical finalist.
- **BC-B1C-3**: held — the rework stopped at `C_tool′ = e7213e5`
  (self-diff strictly inside the frozen tool path set), Acceptance
  ran the write audit, and **no authoritative P3 artifact was run or
  written by Implementation**; my probe was the §27-mandated
  disposable review probe, deleted after validation.
- **BC-B1C-4**: moot (tool changed); module entry remains canonical;
  F8(a) stays correctly non-mandatory.
- **BC-B1C-5**: next stop — formal P3 from clean HEAD exactly
  `e7213e5`, then `C_1c` awaits Acceptance audit and independent
  review. Batch 2 stays `BLOCKED_USER_GO`; the probe's `P3_OK` is not
  a batch-2 GO and must not be cited as one.

## UNITY_NA position

No `UNITY_NA` is claimed for the reworked tool stage and none is
needed: Edit-Mode/offline only, zero Play, zero capture; the
Unity-facing surface is the Edit Mode suite, which I independently
reran (216/216). I concur with the gate-board treatment.

## Verdict

**`PASS_WITH_NOTES`** for the reworked batch-1c tool candidate
`C_tool′ = e7213e5` (endpoints `77595c8..9245601`).

All four round-3 findings are closed with regression coverage on both
the C# and Python sides; the write audit, topology, and every test
count reproduce independently (Unity 216/216 twice, focused 21/21,
full 324 with only known failures, checker 13/13); my artifact-only
NaN proof now shows zero self-comparison divergences; and the
§27-mandated probe at exactly `e7213e5` executed the entire real-scene
chain — T5 recheck equal, T4/T6 reached, P2-source discipline
bit-exact, checker-validated terminal state — with correct §5.6 ④
identity throughout. Implementation may now run the **formal P3**
capture from clean HEAD exactly `e7213e5` and stop at `C_1c` per
BC-B1C-5; my probe's numbers are not that evidence. F15 notes are
non-blocking; batch 2 remains locked.

---

# Round 5 — batch 1c formal P3 `C_1c` (2026-08-03)

Reviewer: review 角色 (independent review, strongest pool; same session
re-invoked on the formal P3 stop). Only legal action exercised: this
file plus the status-board sync; zero implementation files touched;
the candidate branch was not merged, rebased or rewritten. Disposable
worktree `.claude/worktrees/review-P1-SCENE-006-c1c` checked out
directly at `3d6f0dc` per §28, removed at close-out.

## Candidate and requirements

- Accepted basis: §28 (`C_1C_STOP_CONFIRMED / HANDED_TO_REVIEW`) on top
  of §25 BC-B1C-1–5, §26/§27 and review round 4 `PASS_WITH_NOTES` on
  `C_tool′ = e7213e5`.
- Candidate: **`C_1c = 3d6f0dc`** on branch `p1-scene-006-c1c`, parent
  verified to be exactly `e7213e5`; frozen endpoints
  **`77595c8..3d6f0dc`** (`a69c0b4` on `main` correctly excluded). The
  range contains precisely the eight commits already line-reviewed in
  rounds 3–4 plus `3d6f0dc`, whose self-diff is **only** the two new
  evidence files (`P1-SCENE-006-batch1c.md`,
  `P1-SCENE-006-p3-finalist.json`, 21,120 insertions). Zero diff on
  the frozen tool path set, `config/`, scenes, runtime `Scripts/`, and
  zero changes to any of the 13 reviewed batch-1b artifacts.
- Write audit reproduced at the `C_1c` worktree
  (`--role implementation --base 77595c8`): the same **2
  non-implementation paths** with the same per-commit attributions as
  §28; no unattributed path.

## What I recomputed myself (own script, no checker reuse)

All of the following pass against the committed artifact:

- **Capture identity**: `capture_commit = tool_commit = e7213e5`,
  empty porcelain, scene-file SHA-256 before == after,
  `scene_saved = false`, and `scene_state_sha256` equal to the
  batch-1b P1 capture's (`75b84083…`).
- **Input bindings**: the recorded P1/P2 SHA-256 equal my recomputed
  file hashes; `source_scenario_sha256` equals the SHA-256 I
  recomputed from the frozen `config/scenario.default.json` bytes
  (`f9c92052…`, also matching the trace artifact);
  `road_data_sha256` matches P1; `source_scenario_id` is the frozen
  config id — no new scenario/session/run identity anywhere.
- **§5.4 selection**: margins/scores recomputed in binary64 for the 3
  in-band cells; stored rows match within the 1e-9 reconciliation
  bound, ordering and ranks 0–2 match my independent sort, no
  terminal rows, `f_count = 3`, finalist `(197,30) h16 vfov40` at
  rank 0 with score **bit-equal** to my round-4 probe
  (`0.08465603419712611`).
- **BC-B1C-2**: all three support records re-derived from the P1
  artifact — legal, single support `Natures_Grass Tile Small`,
  P1/P2 altitude binding consistent; `ok = true` 3/3.
- **T5 recheck**: `equal = true`, empty divergence, both contract
  hashes equal to the P1 altitude-16 report's
  `anchor_contract_sha256`.
- **Trace chain**: `finalist_trace_sha256` == the P2 cell binding ==
  the published `trace-B-197.0-30.0.json` artifact hash
  (`46036a6c…`), `s_init` identical across all three records.
- **T4, fully recounted**: I re-implemented the §5.2.7 station set
  from the frozen text (4 m world lattice × heights {8..32},
  `r(h) = sqrt(35² − h²)` with the double-precision membership rule,
  `p_hover` merge, (h, x, z) order) — **all 1039 stations match the
  artifact bit-for-bit in position, height, order and the single
  hover flag** (the h = 16 lattice origin absorbs `p_hover`).
  Rejection counts recounted: 183 certified / 478 body / 842 tether /
  0 path; per-station coherence holds (passed ⇔ no rejection flags ∧
  `c_station ∈ [0,1]`; failed ⇔ NaN `c_station`; path-rejected would
  exclude body/tether — none present). For **every** station I also
  recomputed the trapezoid `duration_s` and the 0.25 m
  `sample_count` from its geometry — all reconcile. Best station:
  first-at-max index **847** with `C_station = 1.0`; `c_hold` is
  **bit-equal** to the P2 cell `c_geom` (`0.49444442987442017`);
  `G = 0.5055555701255798 ≥ 0.05` → PASS. (`gate_threshold`
  serializes as `0.05000000074505806` — the exact float32 widening of
  the frozen `0.05f`; my first probe assertion compared against the
  binary64 literal and was corrected — probe error, not a defect.)
- **T6, per sample**: 11 samples k = 0..10; k = 0, 1 not
  geometrically visible; `k* = 2` is the first visible tick; prompt
  min-side equals `samples[2]` (`143.2294464111328 px`), the size
  gate median equals the P2 cell's `t1_min_side_median_px`
  (`63.25716018676758 px`), geometric-visible ⇒ frustum-visible holds
  on every sample; gate PASS.
- **Status**: `P3_OK` equals the T4 ∧ T6 conjunction.
- **Canonical checker**: `python3 -m tools.scene006_candidate_check
  check <p3> --p1-path … --p2-path …` → **OK / `P3_OK`** rerun by me
  in the worktree; focused `tests.test_scene006_candidate_check` =
  **21/21**.
- **Probe agreement**: every value the formal artifact shares with my
  round-4 independent probe execution (finalist identity and score,
  `c_hold`, `G`, best index, station/certificate counts, `k*`, prompt
  and median) agrees **bit-for-bit** — two independent executions of
  the reviewed tool at the same commit produced identical results.
  The formal artifact stands on its own; the agreement is
  corroboration, not the evidence.

## Unity position

`e7213e5..3d6f0dc` has zero diff on any Unity-facing path, so the
round-4 independent Edit Mode rerun (216/216, plus the implementer's
216/216 XML) applies verbatim to this candidate's tool tree; the P3
batch adds no code and no Unity case. No `UNITY_NA` is claimed and
none is needed (Edit-Mode offline capture, zero Play, zero session);
I concur with the gate-board treatment.

## Findings (round 5)

None blocking; no new obligations. Informational only: the
`gate_threshold` field carries the float32 constant widened to
binary64 (`0.05000000074505806`) — consistent with the frozen `0.05f`
comparison actually used; consumers should not compare it against the
binary64 literal `0.05`. Round-4 F15 notes (checker
`SCORE_NOT_FINITE` label asymmetry; history-fork reconciliation) are
unchanged; the branch topology in §28 ④ (non-squash merge by
Acceptance) resolves F15(b) cleanly — keep `p1-scene-006-c1c`
untouched until that merge.

## Verdict

**`PASS`** for the batch-1c formal P3 candidate `C_1c = 3d6f0dc`
(endpoints `77595c8..3d6f0dc`).

The formal P3 artifact is fully faithful to §25 BC-B1C-1–5 and
§5.4/§5.6 ④: inputs are the reviewed hash-bound artifacts, the unique
finalist `(197,30) h=16 vfov=40` follows from the frozen scoring, the
support guard and T5 re-audit hold, the T4 certificate audit and T6
acquisition window recompute exactly (station lattice, counts,
durations, best station, gates), the capture identity is exactly
`capture = tool = e7213e5` with the zero-write proof intact, and the
canonical checker plus my full independent recomputation agree with
zero discrepancies. Per §28: Acceptance may now merge `3d6f0dc` into
`main` **non-squash, non-rebase** and dispose these notes; **`P3_OK`
is not a batch-2 GO** — batch 2 stays `BLOCKED_USER_GO`, and no
M3′ implementation may start on the strength of this result.

---

# Round 6 — batch 2 tool stage `C_b2tool` (2026-08-04)

Reviewer: review 角色 (independent review, strongest pool; fresh
context). Only legal action exercised: this file plus the status-board
sync; zero implementation files touched. Disposable worktree
`.claude/worktrees/review-P1-SCENE-006-b2tool` at exactly `c0091d1`,
removed at close-out.

## Candidate and requirements

- Accepted basis: proposal §30 (`BATCH2_GO_RECORDED /
  TOOL_STAGE_AUTHORIZED`, BC-B2-1–8; user "授权batch2" ledgered in
  `docs/authorizations.md`) and §31 stop audit (`C_B2TOOL_STOP_CONFIRMED
  / HANDED_TO_REVIEW`); design v0.3.14.
- Tool candidate: **`C_b2tool = c0091d1`**
  (`c0091d19c859748696cf1bc0769df64a027e0d4f`), parent exactly
  `4d116ce`; frozen endpoints **`d21aafc..c0091d1`** (2 commits). I read
  the full 15-path range diff file by file.
- Handoff constraints honoured by the range and by me: no
  `config/scenario.p1-scene-006.json` anywhere (worktree and main tree
  checked), no candidate probe directory (`runtime/p1-scene-006/` holds
  only the reviewed baseline `probe-baseline-vfov60` + trace),
  `RunCandidateProbe` never executed, zero Play/session/run IDs.

## Commit topology and write audit (reproduced myself)

- Ancestry verified: `3d6f0dc` ⊆ `d21aafc` ⊆ `c0091d1`
  (`git merge-base --is-ancestor` both hops).
- `c0091d1` self-diff touches exactly the **11 declared paths**: 2 new
  Editor/EditMode sources + their 2 `.meta` (fresh GUIDs, unique in the
  repo, minimal format), 2 modified Editor sources, the Python consumer
  + its test module, the evidence file, the status board and one
  mechanical archive move. `4d116ce` self-diff is 6 Acceptance doc paths
  (authorizations ledger with the verbatim GO, v0.3.14 design sync, §30
  BCs, implementation-status GO note, status board, archive).
- Full-range diff has **zero** `config/`, tracked `runtime/`, runtime
  `Scripts/`, scene, or artifact-JSON changes; no path outside the
  BC-B2-2 tool set plus evidence/status/archive.
- Reran `python3 tools/check_role_writes.py --role implementation
  --base d21aafc` in the worktree: the **same 3 non-implementation
  paths** as §31 (authorizations, design, proposal), each touched only
  by `4d116ce` (per-path `git log` verified) — fully attributed. Same
  check at `--base 4d116ce` **passes** with 11 paths; no unattributed
  path.

## What I reran and reproduced myself

- **Unity Edit Mode, independent rerun — PASS**: full suite on the
  fresh worktree at `c0091d1` (Unity 6000.4.1f1, `-batchmode
  -nographics -runTests`): **219/219 passed**, including the 3 new
  `Scene006CandidateProbeEditModeTests` cases, name-for-name identical
  to the implementer XML
  (`runtime/test-results/p1-scene-006-editmode-b2tool.xml`, also
  219/219).
- **Focused Python**: `tests.test_scene006_probe` = **13/13** in the
  main tree (`.venv-track`; main HEAD `7372be0` verified zero-diff from
  `c0091d1` on every code path — the two later commits are docs only).
- **Full Python, main tree**: **326 ran, 1 failure = known F3**
  (`test_check_docs`, coordination base breakage `902a72c`) —
  reproducing the §31 claim 325/326.
- **Full Python, bare worktree**: 326 ran, 9F/3E/3S = F3 + the
  documented missing-untracked-weights `test_scene006_probe`
  environment set (7F + 3E, same decomposition as rounds 2–4) **plus
  the new `test_v2_happy_path_reaches_embedding_review`**, which needs
  the same untracked weights; the v2 violations test passes even bare.
  Consistent with the environment decomposition, not a code regression.
- **Frozen-value recomputation**: the family-B route expected by
  `LoadAndBind` (`FamilyRoute` = default route + `(+60, −60)`,
  y preserved) equals the §3.3 eight-point literal vertex-for-vertex,
  float32-exact; `FamilyBRelocations` equals the §3.3.2 table value for
  value on all five rows (prefab, original xz, segment, direction,
  displacement, landing), `match_tolerance_m = 0.1`,
  `expected_distractor_count = 0`. The committed P3 artifact re-read:
  `P3_OK`, schema `p1-scene-006-p3/v1`, finalist B `(197,30) h16
  vfov40`, `s_init = 184.22793579101562`, trace `46036a6c…` (the
  round-5 reviewed values), `k* = 2` — the loader's double-sided
  finalist check binds against exactly these.

## Code review (semantic fidelity)

- **`Scene006CandidateProbe.LoadAndBind`** (new): P3 gate first
  (`P3_OK` + schema + selection/finalist/t6 present, else throw);
  `scenario_id` pinned; anchor x/z exact `==`; anchor y within `1e-9`
  of the frozen literal; altitude/vfov must equal the P3 finalist *and*
  the finalist itself must be the BC-B2-3 point (double-sided, defends
  against a swapped P3 file); route compared vertex-by-vertex against
  the frozen translation; the five relocation rows matched by
  prefab+xz — exactly-5 plus all-5-matched forces a bijection (the two
  same-prefab trucks are 58 m apart, so the 1e-4 match bands cannot
  alias) — with `mark_as_distractor`/`remove_from_scene` forced false
  and count 0 (BC-B2-4); then a not-in-BC-B2-3 freeze sweep over
  random_seed, road_data_sha256, 5 drone fields, 2 gimbal fields, 5
  sensor fields, 2 target fields, 3 evaluation fields and 7
  route-corridor floats — **but see F17: `schema_version` and the two
  corridor bools are not swept**. Any failure throws; the loader writes
  nothing.
- `ScenarioConfig.FromJsonStrict`/`Normalize` interaction: laundered
  values (missing/blank/non-finite fields fall back or clamp) can only
  land on values that the exact comparisons then reject, because the
  default config passes through the same `Normalize` — fail-closed
  direction preserved end-to-end.
- The P3 file is read from the fixed committed path; with the
  `RunCandidateProbe` empty-porcelain precondition, its content is
  pinned to the committed (round-5 reviewed) artifact by construction —
  local tampering cannot survive the porcelain gate.
- **`RunCandidateProbe`** (new entry, never run — tool capability
  only): precondition order is bind (read-only) → `rev-parse HEAD` →
  porcelain must be empty → scene-file hash before → open/adjust scene
  → regenerate trace from the bound config and compare to the P3
  `finalist_trace_sha256` (throws before any directory work) →
  `PrepareProbeDirectory` (probe-id guard refuses foreign directories;
  candidate id/dir constants are disjoint from the baseline's) → render
  → scene-file hash after (zero-write check; **see F18 for its position
  relative to the manifest write**). Trace-hash binding also closes the
  route-equality band left by `Vector3 ==` (F19a): `HashStates` covers
  every state's position/rotation float32 bits, so any parsed route
  difference diverges the hash and fails closed.
- **`Scene006ProbeRenderer`**: `Manifest` unsealed (serialization
  unchanged), `Render`/truth records parameterized on `probeId` with
  both baseline call sites passing the original constants — v1 byte
  semantics preserved (my 219/219 rerun with the unchanged 216 prior
  cases is the regression evidence); `CandidateExtras != null` branch
  enforces discovered `k*` == P3-bound `ExpectedKStar` **before** the
  manifest write and emits the v2 manifest (v1 fields + 8 BC-B2-5
  bindings; `created_by` correctly `RunCandidateProbe`).
- **v2 manifest vs BC-B2-5**: candidate config SHA over raw file bytes
  ✓; old default SHA from `LoadFrozenScenario`'s raw bytes ✓; k\*
  provenance = P3 path + SHA ✓; `capture_commit`/`tool_commit` recorded
  ✓ **but see F16 for the tool_commit source**; empty porcelain
  required by the consumer ✓; model manifest and weights SHA-256 live
  in the v1 result layer (`detector_weights_sha256`/
  `appearance_weights_sha256` + `manifest_sha256` binding), unchanged ✓.
- **`tools/run_scene006_probe.py`**: v1 semantics untouched (the v2
  block is gated on the v2 schema string); v1 checks still enforce the
  pre-registered 106-tick set, `k* ∈ [0,10]` outside the ticks and the
  disjoint prompt (BC-B2-6); v2 adds per-field checks including
  bool-rejecting `expected_k_star == k_star` and empty-porcelain. The
  11 violation subtests fail closed for the right reason in the main
  tree (weights present ⇒ the ValueError comes from manifest
  validation).
- Both new classes live in the Editor-only assembly; zero
  runtime-assembly surface; truth boundary unchanged.

## Findings (round 6; numbering continues)

1. **F16 — BLOCKING (the rework): `RunCandidateProbe` records
   `tool_commit = capture HEAD` unconditionally, which is wrong by
   construction on every legal formal-T1′ execution path.** §5.6
   defines `tool_commit` as the last commit *introducing changes in the
   frozen tool path set* along the capture history, with a zero-diff
   proof whenever `capture_commit ≠ tool_commit`; BC-B2-5 requires the
   formal T1′ to run at `C_b2config` (only the new config) *or a
   tool-path-zero-diff successor*. At any such HEAD the config exists,
   so HEAD is strictly after the last tool-path-changing commit
   (`c0091d1` or its rework successor) — the code would stamp the
   config-stage HEAD as `tool_commit`, mis-stating the identity,
   vacating the zero-diff-proof obligation (the recorded
   `tool_commit..capture_commit` range becomes empty), and severing the
   manifest's link to the reviewed tool commit. §5.6's own clause
   («`tool_commit` 与记录不符 … 一律 fail closed 重跑») then mandates
   re-rendering at the `C_b2` audit — after frames were produced. The
   identical stamp in `Scene006FinalistGenerator` was correct only
   because §5.6 ④ made P3 capture happen *at* the tool commit; that
   precondition is provably false here. The Python validator cannot
   catch it (40-char check only). **Rework** (a frozen-tool-path
   change, so per BC-B2-2 it must stop at a new `C_b2tool` for write
   audit and re-review): derive the true last tool-path-changing
   commit (e.g. `git log -1` over the frozen path set) or bind a
   declared tool commit verified in-process by a
   `tool_commit..HEAD` zero-diff check on the frozen paths; record it,
   and add a test pinning the semantics.
2. **F17 — the not-in-BC-B2-3 freeze sweep misses three fields
   (fail-open direction, narrow).** `LoadAndBind` never checks
   `schema_version` (`Normalize` only logs a warning for an unknown
   schema string) or `route_corridor.enable_dynamic_intersection_audit`
   / `enable_jump_diagnostic` (both `false` in the frozen default), so
   a candidate config diverging on any of the three passes the loader,
   and evidence §2.1's "corridor 逐项等于" claim does not hold for the
   two bools. None of the three affects the rendered T1′ frames, and
   the `C_b2config` byte audit against the default is a real
   second net — but the loader's stated purpose is to make the audit
   not the last line. Fix in the same tool round (three `Require`s plus
   violation cases).
3. **F18 — zero-write ordering deviates from the reviewed pattern: the
   v2 manifest is written before the scene-hash after-check.** The
   reviewed `StampAndWrite` (batch-1c) compares the scene-file hash
   *before* writing the P3 artifact, so a zero-write violation leaves
   no consumable output. `RunCandidateProbe` checks the hash only
   after `Render` returns — i.e. after the complete v2 manifest is on
   disk — so a violated run exits 1 but leaves a fully-formed,
   Python-consumable probe directory behind (the v2 manifest records
   no scene-file hashes that a consumer could re-check). Unlikely to
   trigger (no code path saves the scene; batch-1c ran hash-stable),
   and a rerun's `PrepareProbeDirectory` would delete the leftovers —
   but
   the fail-closed hygiene of the reviewed pattern is lost. Fix in the
   same round: perform the scene-hash comparison (and record
   before/after) prior to the manifest write, mirroring
   `StampAndWrite`.
4. **F19 — minor observations, no action forced.**
   (a) Route vertices compare via Unity `Vector3 ==` (~3.16e-5 m
   band) and relocation rows via 1e-4/1e-6 bands, while the evidence
   says "逐顶点等于" — for the route the trace-hash binding closes the
   band bit-exactly at probe time, and the bands are geometrically
   inert; exact comparisons would still be cheaper to reason about.
   (b) `capture_commit`/`tool_commit` validation is length-40 only
   while the error message says "40-hex" — declared by the implementer;
   tighten opportunistically.
   (c) `P3ArtifactSha256` hashes `ReadAllText`→UTF-8 re-encoded text
   (BOM-stripped) rather than raw file bytes; identical for the
   committed artifact, but `ReadAllBytes` (as used for the config SHA)
   would be robust by construction.
   (d) The v2 manifest omits the P3 precedent's scene-file/scene-state
   hash fields; scene bytes remain pinned via `capture_commit` + the
   empty-porcelain precondition, so identity is derivable — folding
   the hashes into the F18 fix would restore parity.
   (e) Probe outputs are untracked, so a completed run dirties the
   porcelain for any *subsequent* run until committed/cleaned —
   operational note for the config stage, matching batch-1c practice.

## BC-B2 compliance

- **BC-B2-1**: held — audit base `d21aafc` (non-squash ancestry of the
  reviewed `3d6f0dc` verified); the zero-diff question was answered
  honestly and correctly: I verified each of the four claimed
  obstacles in the `d21aafc` code (hard-bound frozen scenario/id/dir in
  `RenderProbeFrames`; no binding component; v1 manifest lacks the
  BC-B2-5 identity fields; `_validate_manifest` accepted v1 only). No
  config or T1′ work preceded the tool stop.
- **BC-B2-2**: held — the candidate self-diff stays inside the frozen
  tool path set plus evidence/status/archive; implementation stopped
  at `C_b2tool` for audit and this review; no config bytes, no formal
  frames, no T1′ values anywhere in the range or on disk.
- **BC-B2-3/4**: enforced by `LoadAndBind` for every listed field and
  almost all unlisted ones (F17's three-field gap; F19a bands); the
  five-row set, flags `false/false` and count 0 are forced; nothing
  was written to `config/`.
- **BC-B2-5**: the v2 manifest binds old-default SHA, candidate config
  path+SHA, P3 provenance and porcelain, and the result layer keeps
  the model/weights SHAs — but the `tool_commit` source is wrong
  (F16), so the identity chain is not yet deliverable as specified.
  The reader-listing obligation belongs to the config stage and is
  untouched.
- **BC-B2-6**: the consumer still enforces the frozen chain (106
  pre-registered ticks, `k*` window, disjoint prompt, fail-closed
  states, tool never writes `PASS` — the v2 happy path caps at
  `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`).
- **BC-B2-7**: not reached; nothing in the range pre-empts the later
  `C_b2` stop.
- **BC-B2-8**: held — zero Play, zero capture, zero
  scenario/session/run IDs, zero runtime `Scripts/` diff;
  `RunCandidateProbe` never executed (no candidate directory exists in
  the worktree, the main tree, or the range).

## UNITY_NA position

No `UNITY_NA` is claimed for the batch-2 tool stage and none is
needed: it is Edit-Mode/offline tooling with zero Play and zero
capture; its Unity-facing surface is the Edit Mode suite, which I
independently reran (219/219). I concur with the gate-board treatment,
including the standing note that the eventual new config still needs
the user's non-Play Unity visual inspection after review.

## Verdict

**`REWORK_REQUIRED`** for the batch-2 tool candidate
`C_b2tool = c0091d1` (endpoints `d21aafc..c0091d1`), returning to the
same BC-B2-2 tool stop.

Nearly everything at this stop verifies: the topology, write audit and
attributions reproduce exactly; my independent Unity (219/219), focused
(13/13) and full-suite (326/only-F3 in the main tree) runs match the
implementer's counts; the zero-diff verdict's four obstacles are real;
`LoadAndBind` binds the BC-B2-3/4 literals and the reviewed P3 identity
fail-closed (route and relocation values recomputed against the frozen
§3.3/§3.3.2 numbers); v1 byte semantics are preserved; and the declared
anchor-y `1e-9` tolerance is a validation-only band that does **not**
relax the BC-B2-3 config-literal obligation — I concur with §31 item 4
on that point. But F16 is structural: on the only execution paths
BC-B2-5 permits for the formal T1′, the tool stamps a
§5.6-nonconformant `tool_commit` into every manifest it can ever
produce, silently — the exact class of defect this stop exists to catch
before frames are rendered. The fix is a frozen-tool-path change: per
BC-B2-2 it must land as a new `C_b2tool` commit with tests, take an
Acceptance write audit at base `d21aafc`, and return here for
re-review; F17 and F18 must be fixed in the same round, F19 is
optional. `config/scenario.p1-scene-006.json`, formal frames and T1′
values remain locked until that re-review passes and Acceptance
explicitly opens the config stage.

---

# Round 7 — batch 2 reworked tool `C_b2tool′` (2026-08-04)

Reviewer: review 角色 (independent review, strongest pool; same session
re-invoked on the reworked candidate). Only legal action exercised:
this file plus the status-board sync; zero implementation files
touched. Disposable worktree
`.claude/worktrees/review-P1-SCENE-006-b2tool2` at exactly `b85f461`,
removed at close-out. Environment note, recorded honestly: my first
worktree for this round was deleted out from under me mid-session by
something outside this review (its directory vanished while the git
registration survived; the sibling harness-managed worktrees suggest an
external cleanup sweep). Nothing from that copy is cited as evidence —
I pruned the stale registration, re-created the worktree at the same
commit and re-ran everything below from the fresh copy, with the result
XML kept outside the worktree.

## Candidate and requirements

- Accepted basis: proposal §32 (`C_B2TOOL_REWORK_STOP_CONFIRMED /
  HANDED_BACK_TO_REVIEW`) on top of §30 BC-B2-1–8 and round-6
  `REWORK_REQUIRED`; design v0.3.14 unchanged.
- Reworked tool candidate: **`C_b2tool′ = b85f461`**
  (`b85f4615b7321de3a6a09a5deec11109514ba86d`), parent exactly the
  round-6 record `dae3dec`; frozen endpoints **`d21aafc..b85f461`**
  (6 commits). I re-read the full range file by file; the delta since
  round 6 is `dae3dec..b85f461` plus three attributed docs-only
  commits (`3151a0a` candidate-pointer backfill, `7372be0` §31 stop
  audit, `dae3dec` my round-6 record — self-diffs verified docs-only).
- `b85f461` self-diff touches exactly the **9 declared paths**: 3
  Editor sources + the EditMode test file + the Python consumer + its
  test module (all inside the frozen tool path set, which itself is
  unchanged — no additions or deletions), the evidence file, the
  status board and one mechanical archive move. No new `.meta` files
  (no new source files).
- Handoff constraints honoured: still no config bytes, no formal
  frames, no T1′ values, no Play/session/run ID anywhere in the range
  or on disk; `RunCandidateProbe` still never executed.

## Commit topology and write audit (reproduced myself)

- Ancestry `3d6f0dc ⊆ d21aafc ⊆ dae3dec ⊆ b85f461` verified.
- Reran `check_role_writes --role implementation --base d21aafc`: the
  same **4 non-implementation paths** as §32, per-path provenance
  matching its attribution table exactly (authorizations, design ←
  `4d116ce`; proposal ← `4d116ce` + `7372be0`; review file ← my
  `dae3dec`); no unattributed path. Same check at `--base dae3dec`
  (the candidate alone) **passes** with 9 paths.
- Full-range diff has zero `config/`, tracked `runtime/`, runtime
  `Scripts/`, scene, or artifact changes.

## F16–F18 closure verification

- **F16 closed.** `ResolveToolCommit` derives the §5.6 `tool_commit`
  by `git log -1 --format=%H <capture> -- <frozen paths>` along the
  actual capture history, validates both commits as 40-hex, and when
  `tool ≠ capture` proves `git diff --name-only tool..capture --
  <frozen paths>` empty in-process — a mis-derivation fails closed
  before any manifest exists. `RunCandidateProbe` uses the binding
  (production overload through real git) instead of stamping HEAD; the
  v2 manifest gains `frozen_tool_paths` +
  `tool_path_zero_diff_verified`, and the renderer refuses to write a
  manifest when the proof flag is not true. `FrozenToolPaths` equals
  the batch-1b stop record §1 set **entry for entry** (nine entries; I
  checked the record text myself — the `dir/**` rows and the bare-dir
  git pathspec have identical coverage), and an EditMode test pins the
  constant against that set. **My own plumbing reproduces the
  semantics on the real history**: at capture `dae3dec` the derivation
  yields `c0091d1` with a zero frozen-path diff (exactly the §9.1
  forensic case — the shape F16 said would be mis-stamped), and at
  capture `35c6ec2` (current `main`) it yields `b85f461` with a zero
  diff — the live formal-capture shape now produces the correct §5.6
  identity. The stub tests pin "not the capture HEAD", the
  one-call-only equality case, drift rejection, and five degenerate
  git outputs plus a non-commit capture id; the real-repository test
  additionally re-checks the §5.6 definition through different
  plumbing (`show --name-only` non-empty at the derived commit,
  `log tool..head -- paths` empty) and locks the pathspec-splitting
  end of the contract. The nine paths contain no spaces, so the
  single-argument-string join cannot mis-split.
- **F17 closed.** The freeze sweep now covers `schema_version` and
  both `route_corridor` bools; the violation matrix grew 10 → 13 and
  reports **all** accepted violations at once instead of stopping at
  the first (the implementer's mutation evidence names each of the
  three new comparisons as load-bearing; the accumulate-then-assert
  structure makes such a regression enumerate every unfrozen field).
- **F18 closed.** The scene-file hash comparison now runs inside
  `Render`'s v2 branch, immediately **before** the manifest is
  constructed or written — the reviewed `StampAndWrite` order — and
  both hashes are recorded in the manifest
  (`scene_file_sha256_before/after`); the post-`Render` comparison in
  `RunCandidateProbe` was removed, not duplicated. Two further
  pre-write preconditions were added (missing scene-hash probe;
  unverified zero-diff flag). The Python consumer requires both hashes
  64-hex and equal (`_sha256_field` returns the validated text, so the
  drift comparison is live — checked). A zero-write violation can no
  longer leave a consumable manifest behind.

## F19 dispositions (handoff asked me to adjudicate a/d)

- **(b) done**: commit fields are 40-hex on both sides
  (`IsCommitHash` in C#, `COMMIT_PATTERN.fullmatch` in Python; the
  round-6 message/code mismatch is gone).
- **(c) done**: `P3ArtifactSha256` now hashes the raw file bytes,
  same discipline as the config SHA.
- **(d) partial — I concur.** The scene-file before/after hashes are
  folded into the manifest per F18; `scene_state_sha256` is not added.
  The stated rationale holds: at this stage there is no reviewed
  reference value to compare a state hash against, and the applied
  scene identity is already pinned by `capture_commit` + empty
  porcelain + the candidate config SHA (git pins the scene file and
  the tools; the config pins the adjustments). No parity obligation
  from me; if the config-stage review finds it wants the field, that
  is a new tool round by construction anyway.
- **(a) not done — I concur.** The route stays on Unity `Vector3 ==`
  (~3.16e-5 m band) at the loader; the trace-hash binding closes the
  band to float32 bit level at probe time (`HashStates` covers every
  state's position/rotation bits), and forcing exact decimal
  round-trip at the loader would add a failure surface to the
  not-yet-open config stage without buying additional protection the
  `C_b2config` byte audit does not already provide.
- (e) stands as an operational note for the config stage.

## What I reran and reproduced myself

- **Unity Edit Mode, independent rerun — PASS**: full suite on the
  fresh worktree at `b85f461`: **225/225 passed** (219 + the 6 new
  cases, enumerated name-for-name, including the real-repository
  derivation test running green inside the disposable worktree); the
  implementer XML
  (`runtime/test-results/p1-scene-006-editmode-b2tool-r2.xml`) also
  reads 225/225.
- **Focused Python**: `tests.test_scene006_probe` = **13/13** in the
  main tree (HEAD `35c6ec2` verified zero-diff from `b85f461` on all
  code paths — both later commits are docs-only).
- **Full Python, main tree**: **326 ran, 1 failure = known F3 only**,
  reproducing §32's 325/326.
- **Full Python, bare worktree**: 326 ran, 9F/3E/3S — bit-identical
  decomposition to round 6 (F3 + the documented missing-untracked-
  weights probe environment set including the v2 happy path); no new
  failure mode.
- **Real-history derivation** (described under F16): both capture
  shapes recomputed with my own git invocations, independent of the
  implementation's code path.

## BC-B2 compliance

- **BC-B2-1/2**: held — rework stayed inside the frozen tool set
  (which is unchanged as a set), stopped at `C_b2tool′` for the §32
  audit and this re-review; the round-6 defects were fixed at the
  same stop as required.
- **BC-B2-3/4**: unchanged semantics re-verified; the F17 fix closes
  the sweep gap; the five-row/flag/count enforcement is untouched.
- **BC-B2-5**: the v2 manifest now carries a §5.6-conformant
  `tool_commit` with its frozen-path set and discharged zero-diff
  proof alongside the round-6-verified bindings — the identity chain
  is deliverable as specified.
- **BC-B2-6**: consumer chain unchanged where it was correct
  (pre-registered ticks, `k*` window, disjoint prompt, fail-closed
  states) and stricter where v2 is concerned.
- **BC-B2-7**: not reached; nothing pre-empts the later `C_b2` stop.
- **BC-B2-8**: held — zero Play/capture/IDs, zero runtime `Scripts/`
  diff, no config, `RunCandidateProbe` never executed.

## UNITY_NA position

No `UNITY_NA` is claimed and none is needed: Edit-Mode/offline
tooling, zero Play, zero capture; the Unity-facing surface is the Edit
Mode suite, which I independently reran (225/225). I concur with the
gate-board treatment, including the standing requirement that the
eventual new config get the user's non-Play Unity visual inspection.

## Findings (round 7)

None blocking; no new obligations. Informational only: (i) the
`RunCandidateProbe` end-to-end path (real git derivation + v2 manifest
write + scene-hash gate joint behaviour inside one Unity process)
remains unexercised **by BC-B2-2/8 design** until the config stage —
its components are covered separately (EditMode incl. the
real-repository plumbing case; Python manifest contract), and the
first formal T1′ run plus the `C_b2` review are the natural place the
joint path gets exercised; (ii) the consumer requires
`frozen_tool_paths` to be a non-empty list of non-empty strings but
does not pin the nine entries — the pinning lives in the EditMode
constant test, which is acceptable layering; (iii) the worktree
deletion recorded in the header is an environment anomaly external to
the candidate, with no bearing on the verdict.

## Verdict

**`PASS`** for the batch-2 reworked tool candidate
`C_b2tool′ = b85f461` (endpoints `d21aafc..b85f461`).

All three round-6 findings are closed with regression coverage on both
the C# and Python sides, and the closures verify independently: my own
git plumbing reproduces the §5.6 derivation and zero-diff proof on the
real history (including the exact capture shape round 6 proved would
be mis-stamped), the frozen path set matches the batch-1b record entry
for entry, the manifest write is now behind the scene-hash gate, and
every test count reproduces (Unity 225/225 twice, focused 13/13, full
326 with only known failures, worktree decomposition unchanged). The
F19(a)/(d) non-implementations are reasoned trade-offs I concur with.
Per §32: this verdict returns to **Acceptance**, which must dispose it
and may only then **explicitly open the BC-B2-3/5 config stage**;
until that disposition, `config/scenario.p1-scene-006.json`, formal
frames and T1′ gate values remain locked, and `PASS` here is **not**
a config-stage GO.

---

# Round 8 — batch 2 config + formal T1′ stop `C_b2` (2026-08-04)

Reviewer: review 角色 (independent code review, strongest pool; fresh
context session). Only legal action exercised: this file plus the
status-board sync; **zero implementation files touched**. Disposable
worktree `.claude/worktrees/review-P1-SCENE-006` at exactly `d2db9f3`,
removed at close-out. Inside that copy (and only there) I materialised
the gitignored `runtime/models` + `runtime/yoloe` weight trees by copy,
because `_resolve_project_path` rejects symlinks that resolve outside
`PROJECT_ROOT`; the main tree was never written to, and the analyzer's
only output went to a scratch path outside the repository.

## Candidate and requirements

- Accepted basis: proposal §34 (`C_B2_STOP_CONFIRMED /
  T1PRIME_FAIL_RECALL_BELOW_FAIL_MAX / HANDED_TO_REVIEW`) on top of
  §30 BC-B2-1–8, §33 config-stage handoff, and the round-7 `PASS`;
  design v0.3.14; frozen T1′ protocol = base proposal §5.6, frozen
  identity semantics = amendment §5.6.
- Candidate: **`C_b2 = d2db9f3`**
  (`d2db9f3031a40e673f4e97e04217667a097c303a`); frozen endpoints
  **`d21aafc..d2db9f3`** (10 commits). I re-read the full range file by
  file. The delta since the last passed candidate (`b85f461`, round 7)
  is `ed8ea4a` (Acceptance authorisation), `e00d88b` (reader
  inventory), `0e6407b` (`C_b2config`) and `d2db9f3` (T1′ artifact +
  evidence + status), i.e. **exactly one new code/config byte-change:
  `config/scenario.p1-scene-006.json`**.
- Verified mechanically, not accepted as a claim: `git diff
  --name-only b85f461..0e6407b` and `b85f461..d2db9f3` over the nine
  frozen tool paths are both **empty**, so every Editor/EditMode/Python
  tool path in this candidate is byte-identical to the code I passed in
  round 7. `git diff --stat d21aafc d2db9f3 -- Assets/.../Scripts` is
  empty (BC-B2-8).

## Commit topology, identity chain and write audit (reproduced myself)

- Main-tree reflog is linear over the whole stage — no amend, no reset,
  no discarded commit: `ed8ea4a` 16:57 → `e00d88b` 17:21:11 →
  `0e6407b` 17:21:19 → capture 17:22:07 → `d2db9f3` 17:29:15. There is
  exactly **one** config commit and **one** probe log
  (`runtime/test-results/p1-scene-006-probe-candidate.log`, 17:22); all
  107 frames and the manifest share a single mtime second.
- **§5.6 identity re-derived with my own git plumbing**, not the
  tool's: `git log -1 --format=%H 0e6407b -- <9 frozen paths>` =
  `b85f4615b7321de3a6a09a5deec11109514ba86d` = the manifest's
  `tool_commit` = the round-7 `PASS`ed candidate; `git diff --name-only
  b85f461..0e6407b -- <paths>` is empty, so the zero-diff obligation is
  really discharged. `capture_commit = 0e6407b` = `C_b2config`, and
  `capture ≠ tool` is the legal F16-fixed shape.
- The manifest survives on disk and **hash-binds to the committed gate
  artifact**: `sha256(runtime/…/manifest.json) = ac7b1885…9cecd` =
  `probe.manifest_sha256`. From it I re-checked `git_status_porcelain =
  ""`, `tool_path_zero_diff_verified = true`,
  `scene_file_sha256_before == after == dec58698…c9bf`,
  `frozen_tool_paths` = the nine batch-1b entries, and
  `baseline_scenario_sha256 = f9c92052…2ce3`.
- Hashes recomputed by me: candidate config `ec4154d1…c831` (=
  manifest `scenario_sha256`, so the capture provably consumed the
  committed bytes), default config `f9c92052…2ce3`, P3 artifact
  `87b24e7e…0578` (= `k_star_binding_artifact_sha256`). The manifest's
  `trace_sha256 = 46036a6c…326c`, `s_init = 184.22793579101562` and
  `k_star = 2` are **bit-identical** to the reviewed P3
  (`finalist_trace_sha256`, `selection.finalist.s_init`, `t6.k_star`,
  `status = P3_OK`).
- Write audit rerun by me at the candidate HEAD (`--root` the
  worktree): `--role implementation --base d21aafc` lists the **same 4
  non-implementation paths** as §34, and per-path `git log` provenance
  matches its table exactly (`docs/authorizations.md` ← `4d116ce`;
  design ← `4d116ce`, `ed8ea4a`; proposal ← `4d116ce`, `7372be0`,
  `35c6ec2`, `ed8ea4a`; review file ← `dae3dec`, `6cbce16`). Same check
  at `--base ed8ea4a` **passes** with 5 paths, reproducing §34 item 5.
- The user authorisation is in the ledger verbatim ("授权batch2",
  2026-08-04) and its recorded scope already covers "新增而不覆盖的
  scenario 配置字节" plus the offline T1′ artifacts, so §33 opening the
  config stage needed no new authorisation. I concur.

## Config bytes vs BC-B2-3/4 (recomputed, not read off the evidence)

- Leaf-by-leaf diff of `scenario.p1-scene-006.json` against
  `scenario.default.json`: 61 changed leaves, **zero of them outside**
  the BC-B2-3/4 allow-list (`scenario_id`, `anchor_world_m`,
  `drone.initial_altitude_m`, `sensor.vertical_fov_deg`,
  `target.route_world_m`, `scene_adjustments.vehicle_relocations`,
  `expected_distractor_count`); 50 leaves byte-identical, including
  `schema_version`, `random_seed`, `road_data_sha256`, the other five
  drone fields, both gimbal fields, the other five sensor fields,
  `target.track_id/speed_mps`, all three evaluation fields and all nine
  corridor fields.
- `scenario_id = p1-scene-006-difficult-v1`; anchor x/z exactly
  197.0/30.0; anchor y parses to float32 `1.3113417e-06`, within 1e-9
  of the frozen constant; altitude 16.0 and vfov 40.0 equal the
  reviewed P3 finalist.
- Route: all eight vertices are **bit-exact** `default + (+60, −60)` in
  float32 with `y` unchanged, and match the §3.3 literal list.
- Relocations: exactly the five §3.3.2 rows (prefab + original xz +
  landing), `match_tolerance_m = 0.1`, `mark_as_distractor = false` and
  `remove_from_scene = false` on all five, `expected_distractor_count =
  0` — BC-B2-4 to the letter. The in-code
  `Scene006CandidateContract.FamilyBRelocations` I checked against the
  §3.3.2 table row for row.
- BC-B2-5 reader inventory independently reproduced: `git grep` finds
  **exactly** the eight direct default-config readers the evidence
  lists (plus their four `LoadFrozenScenario` call sites, none of which
  passes `fileName`), all bound by source literals or the constant
  default parameter; `ScenarioConfig.Load()` chooses between the
  runtime override slot and the literal project default. The only
  references to the new file anywhere in `Assets/tools/tests/config`
  are `Scene006CandidateProbe`'s constant/doc-comment and one Python
  fixture string. Nothing pre-existing can reach the new file, and the
  default's bytes were not touched.

## T1′ chain — recomputed end to end

- **Full independent re-run of the analyzer** from the worktree code
  against the on-disk capture: `tool_state=FAIL recall=0.076923
  (4/52)`. My result JSON is **field-for-field identical** to the
  committed artifact — `completeness`, `sample_counts`,
  `fidelity_contradictions`, `frozen_protocol`, `probe` echo, `recall`,
  the report-only `embedding` block **and every one of the 52
  per-sample records** (each `maximum_target_iou`, `recall_hit`,
  `target_cosine`, per-distractor cosine and `margin`). The only two
  differing fields are `model_identity.reanchor_config_path` /
  `nanotrack_config_path`, which are absolute paths and therefore
  worktree-dependent; all nine hash fields match.
- **Independently from the raw truth sidecars** (my own script, no tool
  reuse): ticks are exactly `[15, 20, …, 540]` = 106; 106/106 images
  and truth present, zero missing; `k* = 2` is in `[0,10]` and disjoint
  from the tick set; prompt image/truth hashes match the manifest and
  the prompt frame is `V=1` with `target_box_status = OK`; **V=1 ticks
  = 52**, all with `OK` status and non-null boxes (so zero fidelity
  contradictions is correct, not an artefact of the tool skipping a
  case); **distractor samples = 112**. Both floors (≥40) are met, so
  step 4 legitimately does not fire and the chain legitimately reaches
  recall.
- Disposition order in `run_probe` matches §5.6's frozen chain
  1→7 exactly (weights → completeness → fidelity → floors → recall
  bands), `gate_state` is hard-`null` with `gate_state_owner =
  "acceptance"`, and no code path can emit `PASS`. The frozen constants
  in the artifact (`0.25/0.30/0.5/0.1`, floors 40/40, `0.85/0.90`, 106)
  are the DETECT-frozen pair plus §5.6's literals.
- `4/52 = 0.076923 < 0.85` ⇒ `FAIL` / `RECALL_BELOW_FAIL_MAX` is the
  correct frozen branch. Hits are ticks 390/395/510/520 with IoU
  0.951/0.936/0.862/0.878; 47 samples have exactly 0.000 IoU and one
  more sits at 0.012.
- Renderer-side gates that actually fired in this run: `k*` is compared
  to the P3-bound `expected_k_star` **before** anything is written, the
  scene-file hash is re-probed and compared **before** the v2 manifest
  is constructed (round-6 F18's requirement), and the zero-diff flag is
  a pre-write precondition. The trace regenerated from the candidate
  route hashes bit-equal to the reviewed P3 trace before rendering — a
  wrong route byte could not have reached the frames.

## Anti-tuning / anti-retry (the handoff's explicit ask)

The "no repair" claim is not merely asserted, it is structurally
enforced and I checked each escape route: a config tweak would need a
second config commit (clean-porcelain gate + `capture_commit`) — the
reflog has none; a threshold/frame-set/model change would break the
frozen-path zero-diff proof — verified empty; the pipeline is
deterministic (my re-run is bit-identical), so re-running cannot
"select" a better number. §3.4's failure characterisation uses only the
already-produced artifact and truth sidecars, and I reproduced its
substantive numbers: min-side min `25.09` / median `74.47` / max
`107.79` px, slant `21.41–36.62 m`, `visible_sample_fraction` median
`1.000`, 52/52 `OK` box status, 47/52 zero IoU, and the batch-1 60°
control `FAIL 16/99 = 0.161616` under the identical frozen protocol.

## What I reran and reproduced myself

- **Unity Edit Mode, independent rerun — PASS**: full suite in the
  fresh worktree at `d2db9f3`: **225/225 passed**, 0 failed/skipped;
  the test-name set is identical to the implementer's XML
  (`p1-scene-006-editmode-b2config.xml`, also 225/225), so the
  new config on disk disturbs nothing — including the case that pins
  the **default** config's SHA-256.
- **Focused Python**: `tests.test_scene006_probe` = **13/13**.
- **Full Python**: **326 ran, 1 failure = the known F3
  `test_check_docs.test_compliant_minimal_status_passes`**, 1 skipped —
  reproducing the claimed 326/only-F3.
- **Analyzer end-to-end** and **§5.6 git derivation**: described above.

## BC-B2 compliance

- **BC-B2-1/2**: held — the config stage ran only after the round-7
  `PASS` and §33's explicit opening; the frozen tool set is unchanged
  and byte-identical.
- **BC-B2-3/4**: held to the letter (leaf-diff, bit-exact route, five
  rows, flags false, count 0).
- **BC-B2-5**: held — inventory before the first config byte,
  self-diff-only `C_b2config`, capture on a clean HEAD whose frozen
  tool paths are zero-diff from the tool commit, and the identity
  fields recorded (manifest) + hash-bound into the committed artifact.
  See finding F20 for the durability caveat.
- **BC-B2-6**: held — pre-registered 106 ticks, disjoint prompt,
  uncontracted denominator, floors, frozen bands, never `PASS`, and the
  full per-frame cosine/margin/gate-fraction distributions delivered as
  report-only.
- **BC-B2-7**: held — Implementation stopped at `C_b2` with
  `gate_state = null`, did not adjudicate the gate, and returned the
  fail-closed terminal state unmodified.
- **BC-B2-8**: held — zero Play, zero formal capture, zero
  scenario/session/run ID (no new `runtime/runs/` entry since Jul 31),
  zero runtime `Scripts/` diff, no M3′ / criterion 4 / BC-M34-7 /
  metric change.

## Unity position

No `UNITY_NA` is claimed for this candidate and none would be correct:
the Unity-facing surface is the Edit Mode suite, which I independently
reran (225/225), and BC-B2-8's user non-Play visual inspection of the
five landings remains an open, unwaived obligation before terminal
closure. I concur with the gate-board treatment, and I explicitly
**oppose** treating the T1′ `FAIL` as grounds to skip that inspection:
whether it is still worth running is Acceptance's call, but it cannot
be dropped by review-level reasoning.

## Findings (round 8; numbering continues)

None blocking. Three notes, none of which changes the verdict:

- **F20 (durability of the identity chain, recommendation).** The
  committed gate artifact carries `probe.manifest_sha256` but not
  `capture_commit`, `tool_commit`, `git_status_porcelain`,
  `frozen_tool_paths`, `tool_path_zero_diff_verified`,
  `scene_file_sha256_before/after` or `baseline_scenario_sha256`; those
  live only in `runtime/…/manifest.json`, which is gitignored. Today
  the manifest exists and hash-matches, so BC-B2-5 is satisfied and I
  verified every field. But if that directory is lost, a future reader
  of the repository alone can no longer check the identity of a
  negative result that is meant to enter the research record — only the
  hash of a missing file. The analyzer already echoes many manifest
  fields into `probe`; echoing the v2 identity block as well would be a
  small, targeted change. **Not required by any accepted clause**, so
  it is a recommendation for whoever next opens the tool set, not a
  rework item.
- **F21 (no regression pin on the committed config, informational).**
  No EditMode case binds the real `config/scenario.p1-scene-006.json`
  through `LoadAndBind`; the nine candidate-probe cases use synthesised
  configs (correctly so — BC-B2-2 froze them before the file existed).
  A later edit to the committed config would therefore fail no suite;
  only a re-run's `scenario_sha256` would expose it. If this config
  becomes a persistent asset, a single test that binds the real file is
  the cheap insurance.
- **F22 (`p05` convention in the evidence prose, documentation).**
  §3.4 and the status board report `target_min_side_px` p05 =
  `44.07 px`. That is the third-smallest of 52 samples, i.e. the
  nearest-rank/"lower" convention; the project's frozen type-7
  quantile (`quantile_type7`, used by the artifact's own embedding
  summaries) gives `48.67 px`. min `25.09`, median `74.47` and max
  `107.79` reproduce exactly. Purely descriptive text, no gate depends
  on it, and the point it supports ("the target is not small") holds
  under either convention — but the two conventions should not share a
  label in the same work item.

### Boundary observation outside the reviewed range

`35b2ac6` (Acceptance, immediately after the candidate) edits
`docs/evidence/P1-SCENE-006-batch2-config.md`, which is outside the
acceptance write whitelist — `python3 tools/check_role_writes.py --role
acceptance --base d2db9f3` fails on exactly that path. The content is
only the backfill of self-referential commit pointers (`C_b2config
0e6407b`, `C_b2 d2db9f3`, the review endpoints), which by construction
cannot exist inside the commits they name, so nothing substantive was
altered and the reviewed candidate is unaffected. I record it because
the whitelist exists precisely to keep evidence files single-owner;
attributing or preventing it is Acceptance's call, not mine.

## Verdict

**`PASS`** for the batch-2 config + formal T1′ stop `C_b2 = d2db9f3`
(endpoints `d21aafc..d2db9f3`).

Per §34 this `PASS` certifies that **a negative result was honestly
implemented, correctly measured and faithfully reported** — it does
**not** turn T1′ into a success and does not qualify the candidate
scene. The config obeys BC-B2-3/4 leaf by leaf and vertex by vertex,
the §5.6 identity chain re-derives from real git history with my own
plumbing, the capture is complete with both floors met and zero
fidelity contradictions, and the `4/52 = 0.076923 ⇒ FAIL` branch is the
frozen one — my independent re-run of the analyzer reproduces the
committed artifact bit for bit, including every per-sample IoU and
cosine. Every retry/tuning escape route is structurally closed and the
reflog shows a single linear stage with one config commit and one probe
run. Test counts all reproduce (Unity 225/225 independently, focused
13/13, full 326 with only the known F3). F20–F22 are recommendations
and documentation notes carrying no rework obligation.

This verdict returns to **Acceptance**. `P1-SCENE-006` is not `DONE`,
and M1, M3′ and DETECT criterion 4 stay open; BC-B2-8's user non-Play
Unity visual inspection remains a live prerequisite for terminal
closure, and any change to frames, floors, thresholds, FOV, anchor,
route, vehicles or model to "repair" this result still requires a new
ideation/acceptance round and fresh user scope authorization.

## Round 8 addendum — F23 (recorded after the verdict, 2026-08-04)

Recorded honestly: I found this **after** committing the round-8 `PASS`
(`bf8797d`), while answering a follow-up question about what the
failure means. I did not have it when I issued the verdict. Per the
role rules I only append; nothing above is deleted or rewritten.

- **F23 — the probe's target appearance is not the runtime's; the
  recall is therefore not a valid detectability statement about the
  scene. Blocking for interpretation and closure, NOT for code
  conformance.**

  `Scene006SceneRig.CreateTargetReplica` builds the probe target from
  two primitive cubes (`2×1×4` body, `1.7×0.7×2` roof) and **assigns no
  material**, so every T1′ frame renders the target in Unity's default
  **grey** — on grey asphalt. I confirmed this in the rendered frames
  themselves (`frames/frame_000015.jpg`, `frame_000520.jpg`): the
  target is a featureless grey slab, while the surrounding scene
  vehicles are fully modelled. `TetheredScenarioBootstrap.AddCarVisual`
  builds the **runtime/Play** target from the *same two cubes with the
  same dimensions* but paints them **red** (`0.9, 0.12, 0.1`) and dark
  red (`0.65, 0.08, 0.07`). Geometry is identical; appearance is not.

  Consequence: T1′ measures a **grey** target, whereas
  `P1-DETECT-001`'s scout-4 (`172/187 = 0.919786`) and qual-3 measured
  the **red** runtime target through Play-mode sessions
  (`run_detector_scouting._load_session` consumes a runtime session
  directory). The three recall numbers are therefore **not on a common
  scale**, and `4/52` cannot by itself support "this candidate scene is
  undetectable for the system under test". The internal
  candidate-vs-baseline comparison (`4/52` vs `16/99`) stays valid —
  both used the same grey replica.

  Supporting read-only evidence that the failure is **not** explained
  by scene difficulty: across the 52 samples, hits and misses are
  geometrically indistinguishable — off-nadir is pinned at the `45.0°`
  gimbal limit for both, median `min(w,h)` is `70.4 px` (hits) vs
  `74.5 px` (misses), median slant `29.9 m` vs `31.7 m`, median target
  cosine `0.605` vs `0.582`. `k=15` (center `(0.501, 0.469)`, box
  `0.217×0.219`, `visible_sample_fraction 1.000`) scores IoU `0.000`,
  while `k=520` (center `(0.500, 0.451)`, box `0.214×0.224`) scores
  `0.878`. A near-identical pair landing on opposite sides of the gate
  is an appearance/prompt-domain signature, not a geometry one.

  Second parity gap in the same direction: the T6 prompt frame
  (`k* = 2`) has `min(w,h) = 143.2 px` at `23.1°` off-nadir and its
  truth box starts at `x = 0.000` — i.e. the visual prompt is a
  **border-clipped** crop at roughly double the scale and half the
  obliquity of every probe frame (`~70 px`, `45°`). §5.6 requires
  `V(s_{k*}) = 1` and a non-null `OK` box; it does not require the
  prompt to be un-truncated or scale-comparable.

  **Attribution — this is a specification gap, not an implementer
  deviation.** §5.6 pins the frame set, pairing, floors, thresholds and
  disposition chain, but never pins the rendered target's appearance or
  prompt-frame parity; the rig helper predates T1′ and is entirely
  adequate for the *geometric* gates (T1/T2/T3/T4), which is where it
  came from. The implementer executed the accepted text literally, as
  BC-B2-2/6 require. Nothing here contradicts the round-8 `PASS` on
  code conformance, reproducibility or honesty of reporting — every
  number still reproduces bit for bit.

  **What it does block.** Until Acceptance disposes this, the T1′
  `FAIL` must not be used to (i) conclude that the candidate scene, the
  40°/16 m optics, or the frozen detector stack is undetectable;
  (ii) close `P1-SCENE-006` as a negative result; or (iii) feed the
  "no separable scene exists" argument toward M3′/M4′ or the
  submission narrative. It remains a valid, honestly measured statement
  about *the probe as specified*.

  **What I am not doing.** I am not proposing the fix and I have
  changed no code. Repainting the replica or re-selecting the prompt
  would change what T1′ renders, which BC-B2-7 forbids at this stop and
  which §5.5's anti-tuning discipline requires be decided **before**
  seeing new numbers. The route is a new ideation/acceptance round with
  a pre-registered parity definition — and, because the outcome could
  change a research claim, user scope authorization.
