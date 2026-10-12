# P1-M2-RATE-003 batch 2 — difficulty matrix, calibration, probe and decision

Work ID: `P1-M2-RATE-003`
Role: implementation
Scope: accepted revision 3 §3–§11 plus Amendment DR-B (BC-DRB-1..7) and
the batch-2 clarifications BC-B2-CQ1/CQ2
Batch 1 predecessor: reviewed candidate `57f2561` (round 2 `PASS`)

Rounds:

1. Candidate `6417dc3` — first batch-2 implementation. Acceptance
   (`3bea810`) accepted CQ-1/CQ-2 as BC-B2-CQ1/CQ2 but returned the stop
   point `NOT_CONFIRMED_REWORK_REQUIRED`: the two route-legality reports
   were missing, so the reproduced difficulty audit was still
   `ENVELOPE_OUT_OF_BOUNDS`, and the recorded audit command was not
   reproducible.
2. Candidate `dea5111` — reports generated and committed, audit
   `ENVELOPE_OK`, evidence commands corrected, Unity re-run in place.
   Acceptance confirmed the stop point (`a1257b3`) and independent review
   round 3 (`aa3dd21`) returned **`REWORK_REQUIRED`** on two blocking
   orchestration defects, having reproduced every other claim.
3. This round — both blocking findings fixed, the two name-only tests
   rewritten against production state, the contradicted evidence claims
   corrected. Returns to the same stop point.

Batch 2 is a mandatory review stop point. Nothing in this batch starts a
research-data session; the orchestrator refuses to authorise one until
every accepted gate is satisfied.

## What was implemented

| Accepted clause | Landing |
|---|---|
| §3 difficulty knob (`target.speed_mps` only) | `config/scenario.p1-scene-004-d2.json` and its 5 Hz variant; `check_scenario_configs()` proves the allowed difference set |
| §4 three deterministic phases + frozen 12-slot order | `Rate3ScoutingTool` (Unity), `freeze_scouting`, `FORMAL_SLOT_ORDER`, `authorize_session` order gate |
| §5 D2 probe, A0 before B1–B3 | `build_probe`, `measure_displacement` |
| §6 totally defined disposition function | `controller/rate3_decision.py` |
| §10 four-quantity completion gate at 150.0 s | `finalize_attempt` |
| §11 report-only measured lap period | `measure_lap_period`, evaluator truth stream |
| B1 unconditional fields + `CGEOM_DIVERGENCE_FLAG` | `rate3_decision.build_difficulty_cell` / `build_decision_body` |
| B2 must-pass / record-only audit partition | `tools/build_rate3_difficulty_audit.py` |
| B3 six calibration slots + pairing anchor | `CALIBRATION_SLOTS`, `calibration_preflight`, `pairing_findings` |
| BC-R3-1 / BC-R3-2 | `PLANNED_DURATION_S = 150.0`, `batch_invalid_attempt_count` pause at 4 |
| BC-DRB-1..7 | `theta_geom = 0.05`, typed D1 equality, road-audit field set, calibration option B, pair-fails-together, probe reads all three quantities, 0c run gate |

### Key files and protocols

- `controller/rate3_decision.py` (new, pure): type-7 quantiles, median of
  three, the ordered difficulty-level rules, the closed six-value
  `final_action` enum, every diagnostic flag, the BC-DRB-5 pairing check
  and the B1.3 claim/qualifier rules. No I/O, so a reviewer can recompute
  every number directly.
- `tools/run_rate3_study.py` (new): campaign freeze, run gates, scouting
  freeze, calibration preview/freeze, session preparation with the
  BC-DRB-4/5 startup preflight, launch/release, `finalize_attempt`, the
  probe, the D2 selection, and the immutable `p1-rate3-decision/v1`
  artifact plus its recompute-from-artifacts validator.
- `tools/build_rate3_difficulty_audit.py` (new): the B2 partition and the
  BC-DRB-2/BC-DRB-3 equality semantics.
- `tools/build_scene004_geometry.py`: `build_geometry()` gains a
  `scenario_path` parameter (B2.3). The default is unchanged and the
  archived D1 artifact regenerates **byte-identically**
  (`248ae0b3…fefe` before and after).
- `Assets/TetheredTracking/Scripts/Rate3ScoutingTool.cs` (new): the §4
  three-phase table, reusing RATE-002 §3's qualification predicate verbatim.
- `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs`: writes the
  evaluation-domain truth sidecar `runtime/evaluation_truth.jsonl` for an
  active RATE-003 session on released frames only.
- `Assets/TetheredTracking/Scripts/RateStudyProtocol.cs`: the six
  `rs3-d{1|2}-p{1|2|3}-calib` session identities (BC-DRB-4); the two
  revision-3 identities are gone.
- `Assets/TetheredTracking/Scripts/RateStudyExperimentController.cs`: the
  truth sidecar is a stale runtime slot and is cleared by
  `PrepareRuntimeSlots`.
- `Assets/TetheredTracking/Editor/P1Rate003DifficultyEvidenceGenerator.cs`
  (new): produces the D1 and D2 `p1-scene-road-audit/v1` reports BC-DRB-3
  compares.

### New schemas (all batch-2, none retro-fitted onto a shipped artifact)

`p1-rate3-campaign/v1`, `p1-rate3-run-gates/v1`, `p1-rate3-scouting/v1`,
`p1-rate3-scouting-freeze/v1`, `p1-rate3-calibration-preview/v1`,
`p1-rate3-calibration/v1`, `p1-rate3-attempt-status/v1`,
`p1-rate3-failed-attempt/v1`, `p1-rate3-displacement/v1`,
`p1-rate3-lap-period/v1`, `p1-rate3-probe/v1`,
`p1-rate3-d2-selection/v1`, `p1-rate3-decision/v1`,
`p1-rate3-evaluation-truth/v1`, `p1-rate3-difficulty-audit/v1`.

### Ground-truth boundary

§5 and §11 need the evaluation-domain projected truth centre and the
target world position on the released span, and no such stream existed.
It is produced **inside `CoverageEvaluator` only**, written to an offline
analysis sidecar, and read only by `tools/run_rate3_study.py`. Nothing in
`controller/` reads or copies it; the tracker process never opens it. The
existing truth-leak audit
(`tests/test_detector_scouting.py::test_truth_sidecar_is_not_referenced_by_controller_runtime`)
is unchanged and still passes.

## The two clarifications, and how acceptance ruled

Both were raised rather than resolved unilaterally. Acceptance
(2026-07-31, `3bea810`) ruled
**`ACCEPTED_WITH_BINDING_CLARIFICATIONS`** on both and
**`NOT_CONFIRMED_REWORK_REQUIRED`** on the stop point: neither
clarification changes the measurement matrix, the metrics, the frozen
numbers, the phase boundary or the research claim, so `DR-P1-M2-001` does
not re-open — but candidate `6417dc3` was missing the two route-legality
reports, so the reproduced audit was still `ENVELOPE_OUT_OF_BOUNDS` and
the candidate was not reviewable. This rework closes that gap; the
sections below are updated to the accepted form.

**CQ-1 → BC-B2-CQ1 (accepted).** The Inputs section declares exactly
one new config (`scenario.p1-scene-004-d2.json`, differing from D1 only in
`scenario_id` and `target.speed_mps`), but `rate3_protocol.expected_scenario`
(batch 1, reviewed) maps a run's `scenario_id` to its **difficulty only**,
so the 5/20 Hz condition cannot be carried by `scenario_id`. In this
project the capture rate lives in the scenario config
(`sensor.capture_hz`), so a 5 Hz run needs a config of its own.
**Assumption implemented:** four frozen configs, one per (difficulty,
rate). Within a difficulty the two files differ **only** in the fields the
accepted RATE protocol allows to be rate-scaled (design §3.6:
`sensor.capture_hz`, `sensor.retained_frame_count`,
`evaluation.maximum_pending_frame_count`), and across difficulties **only**
in `scenario_id` and `target.speed_mps`. `check_scenario_configs()` proves
both statements and fails closed otherwise, and the difficulty audit
compares D2/20 Hz against D1/20 Hz. `scenario_id` never encodes the rate.

Per BC-B2-CQ1 the four SHA-256 are bound into the campaign provenance and
re-proved at every startup: `prepare_campaign` writes the
`check_scenario_configs()` result into the create-once campaign manifest,
and `load_campaign` now re-runs the check and fails closed if any of the
four files has drifted since the freeze.

| Config | SHA-256 | `capture_hz` | `speed_mps` |
|---|---|---|---|
| `config/scenario.p1-scene-004.json` (unchanged) | `00c8802a…b514` | 20.0 | 2.0 |
| `config/scenario.p1-scene-004-r5.json` | `f0daebd6…5ef8` | 5.0 | 2.0 |
| `config/scenario.p1-scene-004-d2.json` | `90d45651…43fc` | 20.0 | 8.0 |
| `config/scenario.p1-scene-004-d2-r5.json` | `a800bd13…a405` | 5.0 | 8.0 |

**CQ-2 → BC-B2-CQ2 (accepted).** BC-DRB-3 compares the difficulty
`p1-scene-road-audit/v1` report against "the archived D1 report", but no
such report existed for the SCENE-004 circuit: the SCENE-002 generator is
hardwired to `scenario.default.json` and asserts a legacy-route defect,
and SCENE-004's own evidence is a corridor audit plus a Python
re-verification, not a `RoadSceneAuditReport`. Acceptance approved the new
same-`RoadSceneAuditor` Editor generator, in the fixed order D1 then D2,
with the D1 file becoming a read-only archived baseline once first
committed in a stable candidate.

**Both reports now exist and are `CLEAR`.** One Unity Editor evidence run
(no research-data session, no session file, no run directory) produced
them from the frozen scenario bytes:

```
/Applications/Unity/Hub/Editor/6000.4.10f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -nographics -projectPath ~/TetheredDroneTracking \
  -executeMethod TetheredTracking.Editor.P1Rate003DifficultyEvidenceGenerator.Generate \
  -quit -logFile runtime/test-results/p1-rate3-batch2-roadaudit.log
```

Exit code 0; `error CS` count in the log is 0 and the licensing handshake
resolved after one retry, so this was a licensed, clean-compile run. Log
lines 3165 and 3189:

| Report | SHA-256 | `status` | route samples | obstacles audited |
|---|---|---|---|---|
| `docs/evidence/P1-M2-RATE-003-d1-road-audit.json` | `9dddecaa578a83a793707b5ecbd91288a14f28d7abecc8648bb50a8245611775` | `CLEAR` | 126 | 782 |
| `docs/evidence/P1-M2-RATE-003-d2-road-audit.json` | `492d3d1f9701b38b0e701ff865c75c0256f80d84ba8c92f4df8df6cb3b798636` | `CLEAR` | 126 | 782 |

Every violation count is 0 and both violation arrays are empty in each
report; the two files are identical on all fourteen BC-DRB-3 fields and
differ only in `scenario_id`, which is the single exempt field.

## Review round 3 findings, and how they were fixed

Round 3 reproduced every automated and artifact claim and verified every
accepted clause in code, then returned the candidate on two blocking
orchestration defects. Both are fixed here; no committed artifact changed
and no C# changed.

**Finding 1 — the immutable probe artifact froze the first A0 forever.**
`build_probe` wrote the create-once `probe.json` on the A0 branch too, so
one A0 adjudication — or a call fired before any attempt existed — made
the §5 in-place rerun unadjudicable and permanently blocked all twelve
formal slots. The adjudication is now **per attempt**:

- an A0 verdict is written to `probe-attempts/attempt-N.json` (create-once
  per attempt) and leaves `probe.json` unwritten, so the accepted
  archive-and-rerun path stays open;
- only a terminal disposition freezes the campaign artifact — B1/B2/B3, or
  `BLOCKED_PROBE` when attempt `N == 3` is still A0, which is §5's own
  terminal code for an exhausted probe slot;
- the terminal artifact records `attempt_number`, `max_attempts`,
  `terminal` and the SHA-256 of every prior attempt artifact, so the whole
  probe history stays auditable;
- a call made before any adjudicable attempt exists now **refuses**
  (`Rate3StudyError`) instead of adjudicating, which is round 3's
  non-blocking note 3.

Regressions: `test_premature_probe_call_is_a_refusal_not_an_adjudication`,
`test_a0_does_not_freeze_the_campaign_probe_artifact`,
`test_an_a0_attempt_then_an_in_place_rerun_reaches_b2` (the one the review
asked for — A0, archive, rerun, B2, and the formal phase authorises
again), `test_exhausting_the_probe_slot_blocks_the_probe_terminally`.

**Finding 2 — failed calibration attempts could produce no receipt.**
Calibration is HOLD-only and never creates `runs/<slot>`, so the generic
archive branch raised `FileNotFoundError` and BC-DRB-4's per-slot cap and
BC-R3-2's batch counter silently undercounted — fail-open. The receipt
payload is now chosen per slot kind:

| Slot kind | Receipt payload |
|---|---|
| scouting | the scouting report |
| calibration | the installed session file (required), the preview JSON/overlay, and a copy of the referenced reference-frame pair |
| probe / formal | the run directory plus the evaluation-truth sidecar; **falls back to the session payload** when the §1.1(a) startup checks refused before the run directory existed |

The installed session file is exactly BC-R3-2's dividing line: it is
written by `prepare_session` only after `authorize_session` passed, so a
preflight refusal before it existed is still not a counted attempt, and
everything after it is countable. Two further fail-closed guards came out
of the same review: a slot that already produced its terminal artifact (a
frozen scouting table, a frozen calibration product, a terminal
`probe.json`) can no longer be archived as failed, and an already-frozen
calibration slot can no longer be re-authorised.

The two tests the review called out as asserting the claim in name only
(they fabricated `runs/<calib-slot>` by hand) are rewritten to drive the
real production path — authorise, `prepare_session`, archive — and
`test_calibration_receipt_payload_is_the_real_attempt_identity`,
`test_a_startup_refused_run_slot_still_produces_a_receipt`,
`test_an_admissible_run_cannot_be_archived_as_failed` and
`test_a_frozen_calibration_cannot_be_reattempted` were added.

Round 3's non-blocking notes 4 and 5 are carried forward unchanged: the
`metrics.final.json` release-identity binding is worth tightening whenever
a verify-style recheck is added, and the evaluator truth stream still
awaits a live Play session.

## Other implementation choices a reviewer should check explicitly

1. **Scouting has no RATE session.** Like RATE-002 §3 it is a stand-alone
   Unity tool run with the experiment controller inactive, so
   `rs3-scouting` is deliberately *not* a valid `p1-rate3-session/v1`
   identity. It is still a campaign slot: total attempts ≤ 3 and its
   invalid receipts feed `batch_invalid_attempt_count` (BC-DRB-4/BC-R3-2),
   with the scouting report as the receipt payload — see the payload table
   above for the other slot kinds.
2. **Calibration slot execution order** inside the frozen schedule is
   `d1-p1, d1-p2, d1-p3, d2-p1, d2-p2, d2-p3`; the amendment fixes the six
   slots but not their order, so a deterministic one is frozen in the
   campaign manifest.
3. **Calibration installs the difficulty's 20 Hz config.** The frozen
   product must be byte-shared by both rates of the pair (BC-DRB-4/5) and
   the target does not move in HOLD, so exactly one product exists per
   (difficulty, phase) and one config has to be named. The pairing hash is
   the calibration manifest SHA-256, which binds the frame bytes, the
   metadata bytes, the operator box and the overlay.
4. **`phase_collision` is a fail-closed addition.** If the forward search
   returns the same candidate for two phases the three matched design
   points would collapse; scouting reports `INVALID_SCOUTING` rather than
   proceeding. This only refuses, never admits.
5. **S1′–S3 are applied at both rates.** §10 makes them an admissibility
   condition for every run; RATE-002's implementation evaluated them only
   at 20 Hz. The threshold is rate-relative (`>= 0.95 × target rate`).
6. **The 0c gate is enforced in code.** `record_run_gates` refuses unless
   `docs/authorizations.md` contains the 0c entry and the operator asserts
   the qual-3 attribution, the DR round-3 pass and the clock-smoke pass;
   the create-once artifact hashes the ledger it was checked against.
   `docs/authorizations.md` stays read-only to this role.
7. **The decision-time pairing check is a backstop, not the primary
   guard.** The startup preflight refuses a mismatched product before the
   session file is written; if the decision-time check ever fires it is an
   implementation defect to be attributed, not merely a scrapped run
   (BC-DRB-5).

## Automated evidence

Commands run from the repository root.

| Check | Result |
|---|---|
| Command | Exit | Result |
|---|---|---|
| `.venv-track/bin/python -m unittest discover -s tests` | 0 | **287/287 passed** (200 batch-1 baseline + 87 new) |
| `.venv-yoloe/bin/python -m unittest discover -s tests` | 1 | 285/287; the two failures are the pinned-CSRT adapter and CLI tests, which need `opencv-contrib-python`. That venv ships plain `cv2 5.0.0` without `TrackerCSRT_create`, and both fail identically on an unmodified `HEAD` worktree — pre-existing, untouched by this batch |
| `.venv-track/bin/python -m unittest tests.test_rate3_decision` | 0 | 25/25 |
| `.venv-track/bin/python -m unittest tests.test_rate3_study` | 0 | 43/43 |
| `.venv-track/bin/python -m unittest tests.test_rate3_difficulty_audit` | 0 | 19/19 |
| `.venv-track/bin/python -m tools.build_scene004_geometry --output <scratch>/geo-d1.json` | 0 | byte-identical to the archived `docs/evidence/P1-SCENE-004-geometry.json` (`248ae0b3a19dc43eea4383a1e2d50ac15985193aec0f40a79c3d7bd706fffefe`) |
| `.venv-track/bin/python -m tools.build_rate3_difficulty_audit --scenario config/scenario.p1-scene-004-d2.json --difficulty-label D2 --road-audit docs/evidence/P1-M2-RATE-003-d2-road-audit.json --d1-road-audit docs/evidence/P1-M2-RATE-003-d1-road-audit.json --output docs/evidence/P1-M2-RATE-003-d2-difficulty-audit.json` | 0 | `status=ENVELOPE_OK difficulty=D2 speed=8.0 failures=0`; artifact SHA-256 `dd931be27a0c70a9e5127f0c87c03047eeef3afc6094d8452ed53e00400cacb2` |
| Unity Editor evidence run, `-executeMethod …P1Rate003DifficultyEvidenceGenerator.Generate` (command quoted above) | 0 | both route reports `CLEAR`, 0 `error CS` in the log |
| C# compile, Unity 6000.4.1f1 Roslyn with the project's own `.rsp` arguments | 0 | `TetheredTracking.Runtime`, `Assembly-CSharp-Editor`, `TetheredTracking.EditModeTests` all compile with **0 errors** (only pre-existing `FindObjectsSortMode` obsolescence warnings) |
| `…6000.4.10f1/…/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests -testResults runtime/test-results/p1-rate3-batch2-editmode.xml` | 0 | **162/162 passed, 0 failed** (150 batch-1 baseline + 12 new), run **in place** with no Editor holding the lock |
| same binary, `-testPlatform PlayMode -testResults runtime/test-results/p1-rate3-batch2-playmode.xml` | 0 | **3/3 passed**, in place |

Re-running the difficulty audit is byte-reproducible except for
`generated_unix_s`, which is provenance and is the only field that
changes; `test_committed_evidence_chain_reproduces_envelope_ok` pins that
by rebuilding the artifact from the committed reports and comparing every
other field. All paths recorded in the artifact are repository-relative,
so a reviewer's worktree reproduces the same values.

The type-7 quantile has the direct reference assertion §6 requires:
`test_type7_matches_the_numpy_reference_value_for_value` compares against
`numpy.quantile(..., method="linear")` and the implementation reproduces
NumPy's `_lerp` branch, so the two agree **bit for bit** (verified over
40,000 randomised comparisons during development; the committed test pins
a deterministic sample set).

Record-only triples produced for D2 = 8.0 m/s, exactly as B2.1 requires
them to be reported rather than gated:

| Record-only gate | D2 value | D1 baseline | delta |
|---|---|---|---|
| `loop_period_s` | 7.767766952966369 | 31.071067811865476 | −23.303300858899107 |
| `distractor_opportunities` | 12 | 49 | −37 |

## Not verified, and known limitations

- Unity version note: `ProjectVersion.txt` pins 6000.4.1f1, which still
  cannot run this repo headlessly (pre-existing, same as batch 1); all
  Unity evidence above used 6000.4.10f1. Opening the project in place with
  that editor rewrote `ProjectSettings/ProjectVersion.txt`,
  `Packages/manifest.json` (rider 3.0.39 → 3.0.40) and
  `Packages/packages-lock.json`. Those three files were **reverted** and
  are not part of this candidate — bumping the project's editor pin is a
  user decision, not an implementation change. A reviewer running Unity in
  place will see the same three files dirty and should revert them the
  same way.
- The candidate `6417dc3` evidence recorded the Unity suites from an APFS
  clone, because an Editor instance held the project lock. That caveat is
  now retired: the user closed the Editor and both suites were re-run **in
  place** with the results in the table above. Independent review still
  reproduces them in its own disposable worktree.
- The evaluator truth stream is new runtime behaviour that only a Play
  Mode session exercises end to end. Its record shape, the stale-slot
  handling and the offline analysis are covered by Edit Mode and Python
  tests, but the file is not yet proven to be written by a live session.
- No research-data session has been prepared, authorised or run. The
  scouting table, all six calibration products, the probe and the twelve
  formal runs are unmeasured. The Editor evidence run that produced the
  route reports creates no session file and no run directory.
- The 6.0 m/s downshift configs are deliberately **not** created: they
  belong to acceptance criterion 0b, which is only reachable if the probe
  takes branch B3.

## Review scope

1. `controller/rate3_decision.py` against §6 and B1.1–B1.4 clause by
   clause: rule order, the closed enum, every flag definition, the null
   semantics, and that no flag can change `final_action`.
2. `tools/run_rate3_study.py`: the frozen order gate, the per-slot and
   batch-wide attempt guards — check that **every** slot kind now has a
   reachable receipt payload, that the session file is the right BC-R3-2
   dividing line, and that a terminal artifact blocks a later failure
   receipt — the BC-DRB-4/5 preflight and backstop, the §10 four-quantity
   gate including the shared-host wall duration definition (last trusted
   frame capture minus `release_monotonic_s`, not the summary's
   frame-to-frame span), and the §5 A0-before-B1–B3 ordering with the new
   per-attempt / terminal split (an A0 must never write `probe.json`, and
   `BLOCKED_PROBE` must fire exactly at attempt 3).
3. `tools/build_rate3_difficulty_audit.py`: BC-DRB-2 typed equality
   (especially that integers get no float fallback and that non-finite or
   missing values fail closed) and the BC-DRB-3 field set against the real
   `RoadSceneAuditReport` schema.
4. The C# diff: the truth stream's gating condition (RATE-003 session,
   released frames only), the session-identity change, and the scouting
   forward-search/wrap/collision logic.
5. BC-B2-CQ1/CQ2 as executed: that `scenario_id` never encodes the rate,
   that `load_campaign` re-proves the four config hashes, that the D1
   route report is treated as a read-only baseline (the generator writes
   it, the audit only reads it), and that the committed difficulty
   artifact really recomputes to `ENVELOPE_OK`.

## Unity cases for the user (after the stop point passes)

1. Re-run the Edit Mode and Play Mode suites in place on the reviewed
   candidate to confirm 162/162 and 3/3. **Run below** — awaiting
   transcription and attribution by acceptance.
2. Do **not** start any scouting, calibration, probe or formal session:
   `P1-DETECT-001` qual-3 `PASS` plus acceptance attribution, and the
   run-gate record, are separate prerequisites.

## Batch-2 Unity suite gate run (2026-07-31, for transcription)

Raw implementer record of the case-1 run, on the user's instruction to
proceed. `docs/unity-test-log.md` is read-only to this role: acceptance
(or chore) must transcribe and attribute this entry, and the workflow
§4.5 pre-collection record below is supplied here rather than written to
the log by me.

**Pre-collection state (workflow §4.5 / AGENTS.md step 0)**

- `git rev-parse HEAD` → `24198e7d8510372244b3f5201af38010105acef7`
- `git status --porcelain` → empty (clean worktree)
- Commits after reviewed candidate `ab8ae73`: `53c5bb0` (review round-4
  record) and `24198e7` (acceptance closure attribution). Both are
  **docs-only**: `git diff --name-only ab8ae73..HEAD -- Assets config
  controller tools tests` is empty, so the tree is code-equivalent to the
  reviewed candidate.
- Runtime carries no RATE-003 research identity: no
  `rate_study_session.json`, no `runs/rs3-*`, no
  `rate-study/P1-M2-RATE-003-B1/`, no `evaluation_truth.jsonl`, no
  `rate3_scouting_qualification.json`.

**Commands and results** — Unity 6000.4.10f1 (`ProjectVersion.txt` pins
6000.4.1f1, which still cannot run this repo headlessly; pre-existing),
`-batchmode -nographics`, project path
`~/TetheredDroneTracking`, no Editor holding the lock:

| Platform | Command tail | Exit | Result |
|---|---|---|---|
| Edit Mode | `-runTests -testPlatform EditMode -testFilter TetheredTracking.Tests -testResults runtime/test-results/p1-rate3-batch2-gate-editmode.xml` | 0 | **162/162 passed**, 0 failed, 0 skipped, 5.06 s |
| Play Mode | `-runTests -testPlatform PlayMode -testResults runtime/test-results/p1-rate3-batch2-gate-playmode.xml` | 0 | **3/3 passed**, 0 failed, 0 skipped, 0.05 s |

`error CS` count is 0 in both logs; no Console error was reported. Both
match the expected counts, so the gate result is **PASS**.

Opening the project in place again rewrote
`ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json` and
`Packages/packages-lock.json`; all three were reverted and the worktree
is clean, exactly as in the previous rounds.

`.venv-track` full Python suite re-run alongside: **287/287 OK**.

**What this run does not unlock.** It closes case 1 only. No
research-data session is started or authorised: `P1-DETECT-001` qual-3
`PASS` with acceptance attribution, the `record-run-gates` artifact, 0c
and BC-R3-2 all remain separate prerequisites, and the orchestrator
refuses `authorize_session` until they hold.
