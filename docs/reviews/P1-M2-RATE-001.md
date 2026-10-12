# P1-M2-RATE-001 — independent verification

Reviewer/role: Claude Sonnet / independent verification

Round: 1

Date: 2026-07-24

Implementation snapshot: candidate `0642290` (review range `86ffc47..0642290`
as requested; implementation code commit `d29bc13` inside that range).

Verdict: **PASS_WITH_NOTES**

**Latest round: see "Round 4" at the end of this file for the current
verdict (`PASS`) on candidate `fad91da`. This header and the sections below
it are the unmodified Round 1 record.**

## Scope

Per the active handoff, runtime/code scope is `config/scenario.rate-study-*.json`,
`tools/run_rate_study.py`, `tools/run_track_experiment.py`,
`controller/run_log.py`, `controller/track_loop.py`, `tests/`,
`Assets/TetheredTracking/Scripts/CoverageEvaluator.cs`,
`Assets/TetheredTracking/Tests/`; docs are requirements/evidence context.
`git diff 86ffc47..0642290 --stat`: 17 files, 2298 insertions / 39 deletions.
No implementation code was modified during this review.

This is the largest candidate reviewed in this series (`tools/run_rate_study.py`
alone is 984 new lines). I read every changed line rather than sampling, and
prioritized the two areas with the highest blast radius: anything touching
`CoverageEvaluator.cs` (the frozen-metric-semantics file) and the frozen
scenario configs (the study's core invariant).

## Accepted requirements checked

From the accepted proposal (`docs/proposals/P1-M2-RATE-001-frozen-rate-study.md`,
Round 2) and its five binding implementation clarifications:

1. Two configs differing **only** in `scenario_id`, `capture_hz`,
   `retained_frame_count`, `maximum_pending_frame_count`, with retention/pending
   *durations* held equal across rates (25.6 s / 102.4 s).
2. Deterministic per-rate calibration: first frame in `simulation_time_s ∈ [3,4)`,
   frozen reference image + operator-drawn box, shared by all 6 runs of that
   rate; visual-check failure invalidates and restarts, never silently relabels.
3. Fixed N=3 per cell, median as the sole predeclared decision statistic, full
   per-run reporting plus median/range.
4. 20 Hz non-substitutable; S1 (wall-clock capture rate ≥19 Hz) / S2 (compute
   p95 <50 ms) / S3 (backlog p95 ≤1, no `ERROR_REINIT_REQUIRED`) gate every
   20 Hz run; any failure → `RATE_UNSUSTAINABLE`, not silently replaced.
5. R1 (`C_track_given_geom` median <25%) OR R2 (`time_to_first_LOST` median <
   one route-loop duration) triggers `P1-TRACK-002`; threshold sensitivity at
   {15,25,35}%; interaction framed as diagnostic, not causal.
6. Evaluator aggregation/state-machine admissibility precondition: duration
   weighting + `1/capture_hz` fallback, matched/incorrect/duplicate/unmatched,
   pending-pruning attribution preserved at time-equivalent 5/20 Hz windows,
   numeric tolerances (ratios ≤1e-5, durations ≤1e-4 s).
7. Truth-isolation boundary preserved; no runtime C# behavior change beyond the
   accepted test seams; no metric-semantic change folded in silently.

## Files read in full

- `config/scenario.rate-study-5hz.json`, `scenario.rate-study-20hz.json`
- `tools/run_rate_study.py` (984 lines, every function)
- `tools/run_track_experiment.py` (diff), `controller/run_log.py` (diff),
  `controller/track_loop.py` (diff)
- `Assets/TetheredTracking/Scripts/CoverageEvaluator.cs` (diff, cross-checked
  against my `P1-M0-001`/`P1-TEST-001` reviews of this same file)
- `Assets/TetheredTracking/Tests/EditMode/TetheredTrackingEditModeTests.cs`
  (new `CoverageEvaluatorAggregationTests` fixture, full diff)
- `tests/test_rate_study.py` (339 lines, new), and the diffs to
  `test_run_log.py`, `test_track_experiment.py`, `test_track_loop.py`
- `docs/evidence/P1-M2-RATE-001-implementation.md`,
  `docs/unity-test-log.md`'s new `UT-P1-M2-RATE-001-001` section (prepared,
  correctly `PENDING_AFTER_SONNET`, no sessions run yet),
  `runtime/README.md`'s new entries

## Independent verification performed

**Configs.** `diff` on the two checked-in JSON files directly (not just trusting
the validator) confirms they differ in exactly `scenario_id`, `capture_hz`
(5→20), `retained_frame_count` (128→512, both give 25.6 s), and
`maximum_pending_frame_count` (512→2048, both give 102.4 s); everything else —
anchor, drone limits, gimbal, sensor resolution/FOV/JPEG quality, target
route/speed, evaluation thresholds — is byte-identical. `validate_rate_configs()`
([run_rate_study.py:118-166](../../tools/run_rate_study.py)) proves this same
fact programmatically (deep-copy-neutralize the 4 varying fields, then compare
the rest for equality), so the invariant is enforced by code, not just by my
one-time diff.

**Automated tests, rerun myself rather than trusted from the report:**

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 34 tests in 0.234s — OK
```

All 34 names match the evidence document, including the new
`test_rate_study.RateStudyTests` (5 tests) and the extended
`test_run_log`/`test_track_experiment`/`test_track_loop` cases.

**Raw Unity artifacts, read directly rather than trusting the summary:**

```
$ python3 -c "... parse runtime/test-results/p1-m2-rate-001-editmode.xml ..."
root: testcasecount=15 result=Passed total=15 passed=15 failed=0
  ... CoverageEvaluatorAggregationTests.Aggregation_UsesFrameDurationsAndCaptureRateFallback -> Passed
  ... CoverageEvaluatorAggregationTests.ObservationStateMachine_HandlesMatchedIncorrectDuplicateAndUnmatched -> Passed
  ... CoverageEvaluatorAggregationTests.PendingPruning_PreservesAcceptedAttributionAcrossEquivalentWindows(5.0f,512) -> Passed
  ... CoverageEvaluatorAggregationTests.PendingPruning_PreservesAcceptedAttributionAcrossEquivalentWindows(20.0f,2048) -> Passed
  ... (the 11 pre-existing P1-TEST-001 tests, unchanged, all Passed)
```

Confirmed the Unity log ends with `Test run completed. Exiting with code 0 (Ok).`
Also reran `pip check` (clean), `py_compile` on all `controller/`/`tools/`/`tests/`
files (clean), `python3 -m json.tool` on both new configs (valid), and
`git diff --check` (clean).

## `CoverageEvaluator.cs` diff review (frozen-metric-semantics boundary)

This file is the one place a silent regression would be hardest to notice and
most consequential (it produces `C_geom`/`C_track`/`C_track_given_geom`, the
paper's primary outcome). I read every changed line against the version I
already reviewed twice before:

- `OnFramePublished`/`OnObservationReceived` are now one-line wrappers calling
  new `RecordFrame`/`RecordObservation` methods. The diff shows the entire
  body of both (weight computation, duration accumulation, matched/incorrect/
  unmatched counting, `IntersectionOverUnion` call, `ObservationProcessed`
  duplicate-guard) as unchanged **context lines**, not additions — i.e., git
  itself proves this is a pure relocation, not a rewrite I have to trust by
  description.
- `RecordObservation` now takes `expectedTrackId` as an explicit parameter
  instead of reading `TetheredScenarioBootstrap.Instance.Target.trackId`
  inline; `OnObservationReceived` passes that exact same value through, so the
  real runtime call path is unchanged. This only exists so tests can supply an
  expected track ID without needing a full scene bootstrap.
- Five new `internal ...ForTests` methods
  ([CoverageEvaluator.cs:281-341](../../Assets/TetheredTracking/Scripts/CoverageEvaluator.cs))
  are purely additive — nothing in `Start()`/`Update()`/the production
  callbacks calls any of them, confirmed by scanning the whole file.
  `ConfigureAggregationForTests` reuses the real `ScenarioConfig.CreateDefault()`
  + `Normalize()` pipeline rather than a fake config object, so the tests
  exercise the real normalization path too.
- One thing worth naming precisely: the new `AggregationSnapshot` struct
  computes `CGeom`/`CTrack`/`CTrackGivenGeom` with its own copy of the same
  division formulas `WriteMetrics()` already uses inline
  (`geometricDuration/Mathf.Max(totalDuration, Epsilon)`, etc.). I confirmed
  both copies are currently identical, but this is now a second place in the
  codebase computing the same ratios — see Non-blocking note 3.

## New C# test verification (hand-checked, not just "it passed")

I recomputed the expected numbers by hand for all three new test methods
(one of them parametrized twice) rather than trusting the assertions:

- **`Aggregation_UsesFrameDurationsAndCaptureRateFallback`** (20 Hz config): a
  4-frame sequence mixing a normal-weight frame, a `deltaSimulationSeconds=0`
  frame (forcing the `1/capture_hz=0.05` fallback), a not-geometrically-visible
  frame, and an unobserved frame. I traced `totalDuration=0.5`,
  `geometricDuration=0.4`, `trackingDuration=0.2` (only the correctly-identified,
  visible, in-threshold observation counts), `CGeom=0.8`, `CTrack=0.4`,
  `CTrackGivenGeom=0.5`, `matched=3`, `incorrect=2` — every one matches the
  test's assertions exactly.
- **`ObservationStateMachine_HandlesMatchedIncorrectDuplicateAndUnmatched`**: a
  second observation for an already-processed `frame_id` is silently ignored
  (the `duplicate` case — I confirmed it increments none of
  matched/incorrect/unmatched, per `record.ObservationProcessed` guarding
  before any counter touches), a correct-identity-but-low-IoU observation
  counts as `incorrect`, and an observation for a `frame_id` with no pending
  record counts as `unmatched`. My hand-traced counts (`matched=2, incorrect=1,
  unmatched=1, trackingDuration=0.2`) match exactly.
- **`PendingPruning_PreservesAcceptedAttributionAcrossEquivalentWindows`**,
  run at both `(5, 512)` and `(20, 2048)`: inserts one observed frame, then
  exactly `maximumPendingFrames` more frames, which evicts the first frame from
  the pending dictionary (I confirmed the eviction arithmetic: `N+1` inserts
  against a cap of `N` triggers exactly one dequeue). The already-counted
  `trackingDuration` from the evicted frame survives pruning untouched, and a
  **late** duplicate observation arriving for the now-evicted `frame_id`
  correctly falls through to `unmatched` (there's no record left to check
  `ObservationProcessed` against) rather than corrupting `trackingDuration`.
  Both parametrizations match my hand-derivation exactly, and both ran as
  independent Unity test cases per the raw XML.

The tolerances used (`.Within(1e-5f)` on ratios, `.Within(1e-4f)` on
duration sums) match the proposal's stated numeric tolerances exactly.

## Python orchestration review (`tools/run_rate_study.py` and friends)

- **`run_track_experiment.py`**: `two_loop_duration_s` is now a thin wrapper
  over new `route_timing_s`, whose body is the same perimeter/speed
  computation as before (confirmed the formula is algebraically identical);
  `tracker_command()`'s new `rate_study` parameter defaults to `None` and only
  appends `--rate-study-*` flags when provided, so a non-rate-study caller
  (i.e. `P1-TRACK-001`, already closed) produces an unchanged command list —
  I confirmed the existing truth-isolation audit test still passes with this
  parameter present but unused.
- **`track_loop.py`**: ten new optional CLI flags, all validated together
  (all-or-nothing) if any is present, with `rate_study_rate_hz` restricted to
  `{5,20}` and SHA-256 fields checked against `[0-9a-f]{64}` — a normal
  (non-rate-study) invocation is completely unaffected since every new field
  defaults to `None`.
- **`run_log.py`**: new `_cadence()` helper computes `(N-1)/elapsed` exactly as
  the binding clarification specifies for wall-clock capture cadence, applied
  to both `capture_unix_s` (wall) and `simulation_time_s` (sim) series. New
  `time_to_first_lost_s`/`time_to_first_lost_right_censored` correctly
  implement right-censoring (defaults to `actual_duration_s` with
  `right_censored=True` when no `LOST` record exists) — I hand-verified this
  against a constructed 3-record sequence in the test and it matches exactly,
  including the percentile-interpolated `backlog_count.p95=1.9` from
  `[0,2,1]`.
- **`tools/run_rate_study.py`**: this is the largest new file in the project.
  I traced every function against the accepted protocol (§8's A/B steps) and
  found a precise, verifiable match: the `[3,4)` half-open window, "first
  frame by simulation time" ordering (verified by a test with an
  out-of-chronological-order candidate), the frozen-box-shared-across-both-
  conditions design (verified: `stage_run` always selects a **fresh** init
  frame per run but always reuses the **calibration's** box), the mandatory
  `--confirmed` gate before `launch`, the `invalidate-stage`/`invalidate-run`
  pair that never deletes evidence and lets a canonical replicate ID be
  reclaimed only after its predecessor is renamed away, and the S1/S2/S3
  formulas, R1/R2 decision, and {15,25,35}% sensitivity table all matching the
  proposal's numbers exactly (19.0 Hz = 95% of 20 Hz nominal; 0.25 for R1;
  the loop-duration comparison for R2). `summarize_attempt()` reads
  `C_track`/`C_geom`/`C_track_given_geom` straight out of the real
  `metrics.final.json` produced by Unity — it never recomputes them, which is
  the correct way to respect the "metric semantics stay frozen" clarification.

## Findings

### Blocking

None found.

### Non-blocking

1. **No automated check that a "COMPLETE" attempt actually ran to (or near)
   its planned duration, for either rate.** `launch_staged_run`
   ([run_rate_study.py:573-590](../../tools/run_rate_study.py)) classifies an
   attempt `COMPLETE`/admissible based on artifact presence and
   `returncode ∈ {0, 2}`; it does not compare `summary.json`'s
   `actual_duration_s` against the planned duration. `time_to_first_lost_s` is
   right-censored at `actual_duration_s` when no `LOST` occurs
   ([run_log.py](../../controller/run_log.py)), so a run that ends early for
   an unrelated reason (an unusual `GAP`, or a session stopped before the
   terminal completed) with no `LOST` yet observed would report an
   artificially small `time_to_first_lost_s` — which feeds directly into the
   pre-registered R2 continuity trigger. The accepted protocol's step B6 asks
   the human operator to confirm the run reached `planned_duration_s` before
   archiving, so this is mitigated by process today, but the tooling itself
   doesn't cross-check it. Given R2 is one of only two triggers for
   `P1-TRACK-002`, I'd suggest either an automated
   `actual_duration_s`-vs-`planned_duration_s` tolerance check before
   `summarize`, or at minimum surfacing `actual_duration_s` next to
   `time_to_first_lost_s` in `summarize_attempt`'s output so a reviewer can
   catch this by inspection before trusting the decision. Worth resolving
   before the 12 measured sessions begin, since a bad session is cheaper to
   invalidate before analysis than after.
2. **No explicit recalibration path.** `capture_calibration`
   ([run_rate_study.py:294-325](../../tools/run_rate_study.py)) creates
   `runs/rate{X}-calib/` with `mkdir(..., exist_ok=False)`; if the operator's
   first calibration box for a rate turns out to be wrong, there is no
   `invalidate`-style helper to redo it — only manual filesystem intervention
   outside the tool. Every other stage (staging, completed runs) has an
   explicit invalidate/retry path; calibration does not. Not a violation of
   the accepted scope (the proposal doesn't ask for this), just an asymmetry
   worth knowing about before the first calibration session.
3. **`AggregationSnapshot`'s ratio formulas duplicate `WriteMetrics()`'s
   inline computation.** See "CoverageEvaluator.cs diff review" above —
   currently identical, but a future fix to one without the other would
   silently make the tests pass while `metrics.json` reports something
   different (or vice versa). Low urgency; worth a comment or a shared helper
   if either is touched again.
4. **`summarize_runs`'s `duplicates` detection appears unreachable through
   normal tool usage** given the `FileExistsError` guards elsewhere prevent
   two admissible runs from ever sharing a canonical `replicate_id` in
   practice. Not a defect — it's a defensive safety net — but it is also not
   exercised by any test, so I can't rule out it silently breaking in a future
   refactor. No action needed now.

## Missing or weak tests

None beyond what's noted above. The precondition tests (proposal §6) precisely
match the load-bearing state transitions I would have asked for, the
config-invariant validator is enforced by both code and my own diff, and the
orchestration tool's tests exercise real staging/calibration/invalidate logic
end-to-end (mocking only the actual tracker subprocess, which is the correct
boundary — the real CSRT/subprocess path is separately covered by
`test_track_loop.py`'s existing real-dependency test).

## Requirement-to-evidence mapping

| Requirement | Evidence | Verdict |
|---|---|---|
| Configs differ only in the 4 accepted fields, time-equivalent windows | Direct `diff`; `validate_rate_configs()` (rerun) | Met |
| Deterministic per-rate calibration, shared frozen box, invalidate-not-relabel | `capture_calibration`/`stage_run`/`invalidate_stage`; `test_prepare_calibrate_stage_and_invalidate_preserve_evidence` (rerun, traced) | Met |
| Fixed N=3, median-only decision statistic | `_cell_summary`/`summarize_runs`; `test_summary_uses_fixed_cell_medians_and_both_sot_gates` (rerun, hand-verified) | Met |
| 20 Hz non-substitutable, S1–S3 gates | `summarize_attempt`'s sustainability block; `test_summary_blocks_decision_when_20hz_is_unsustainable` (rerun, hand-verified) | Met |
| R1/R2 decision, threshold sensitivity | `summarize_runs`'s decision block; hand-verified against the same test | Met |
| Evaluator aggregation precondition (matched/incorrect/duplicate/unmatched, duration weighting, pending pruning, tolerances) | `CoverageEvaluatorAggregationTests` (4 Unity cases, rerun via raw XML, hand-verified) | Met |
| Truth-isolation boundary preserved; no runtime behavior change beyond test seams | Full diff read of `CoverageEvaluator.cs`, `TetheredDronePlant.cs` (untouched this round), `EvaluationOcclusionGeometry.cs` (untouched this round); confirmed extraction-only | Met |
| Dual-clock reporting | `run_log.py`'s `_cadence()`; hand-verified against a constructed record sequence | Met |
| No metric-semantic change folded in silently | Diff shows zero change to `C_geom`/`C_track`/`C_track_given_geom` formulas anywhere they're computed | Met |

## Requested Codex action

None blocking. Recommend addressing or explicitly accepting non-blocking note
1 (duration-completion cross-check) before the 12 measured Unity sessions
begin, since it protects the integrity of the R2 trigger. Notes 2–4 can wait.

Codex may proceed to schedule `UT-P1-M2-RATE-001-001`'s two calibration and
twelve measured Unity sessions; this code/tooling review does not block that,
though I'd weigh note 1 given how directly it touches the pre-registered
decision rule.

## Re-review result

Superseded by Round 2 below.

## Round 2 — focused verification of the four review notes

Reviewer/role: Claude Sonnet / independent verification

Round: 2

Date: 2026-07-24

Implementation snapshot: candidate `cbff720` (focused review range
`0642290..cbff720`, as requested); docs handoff `6bfbc5b` on top is
docs-only (confirmed below).

Verdict: **PASS**

### Scope discipline

`git diff 0642290..cbff720 --stat`: 7 files, 657 insertions / 34 deletions —
`docs/current-status.md`, `docs/evidence/P1-M2-RATE-001-implementation.md`,
`docs/implementation-status.md`, `docs/reviews/P1-M2-RATE-001.md` (docs), plus
`runtime/README.md`, `tests/test_rate_study.py`, and
`tools/run_rate_study.py` (code). I independently confirmed via
`git diff 0642290..6bfbc5b --stat -- config/ Assets/` that this range touches
**zero** files under `config/` or `Assets/` — the claim "C#/Unity/config 未改变"
is not just asserted, it's absent from the diff entirely. `git diff cbff720..6bfbc5b --stat`
shows only docs changed after the code candidate, confirming `cbff720` is the
code snapshot this round evaluates. No implementation code was modified
during this review.

### Verification performed

I read every changed line in `tools/run_rate_study.py` and
`tests/test_rate_study.py` rather than trusting the implementer's
characterization, and reran the automated evidence myself:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 37 tests in 0.242s — OK
$ .venv-track/bin/python -m pip check
No broken requirements found.
$ python3 -m py_compile controller/*.py tools/*.py tests/*.py
(clean)
$ git diff --check
(clean)
```

All 37 test names match the evidence document, including the 3 new cases
(`test_launch_marks_short_attempt_invalid`,
`test_summary_rejects_short_attempt_even_if_status_claims_complete`,
`test_summary_rejects_duplicate_admissible_replicates`) and the extended
`test_prepare_calibrate_stage_and_invalidate_preserve_evidence`.

I also found that Codex re-ran the real Unity Edit Mode suite for this round
even though no `Assets/` file changed (`runtime/test-results/p1-m2-rate-001-editmode.xml`
now shows a fresh `start-time`/`end-time` of `2026-07-24 15:27:45Z`, still
`15/15 Passed`, and the log still ends `Test run completed. Exiting with code
0 (Ok).`) — extra, appreciated corroboration rather than something I had to
take on faith.

### Per-note verification

**Note 1 — no automated duration-completion check.** Resolved, and more
thoroughly than I asked for. New `duration_completion(summary,
planned_duration_s)` ([run_rate_study.py:530-547](../../tools/run_rate_study.py))
computes `shortfall = max(0, planned - actual)` and requires
`shortfall <= 1e-6` (`PLANNED_DURATION_TOLERANCE_S`) to call a run complete —
essentially requiring the actual duration to reach (not just approximate) the
planned one. This is enforced at **two independent points**, exactly matching
the "surface it so a reviewer can catch it" plus "automate the check"
alternatives I offered, done as both:
1. `launch_staged_run` ([run_rate_study.py:601-644](../../tools/run_rate_study.py)):
   after confirming `summary.json` exists and parses, computes
   `duration_completion` against the staged `planned_duration_s` and appends
   `"planned_duration_not_reached"` to `artifact_errors` if it fails — which
   forces `classification="INVALID"` — and merges the completion fields
   (`actual_duration_s`, `planned_duration_s`, `duration_tolerance_s`,
   `duration_shortfall_s`, `duration_complete`) into `rate-study-status.json`
   so the reason is visible, not just the verdict. A malformed/unparseable
   summary is caught by a `try/except (TypeError, ValueError)` and also marked
   invalid, rather than crashing the launch.
2. `summarize_attempt` ([run_rate_study.py:696-703](../../tools/run_rate_study.py)):
   independently recomputes `duration_completion` from the run's own manifest
   and **raises** `ValueError` if it fails, even for an attempt whose
   `status.json` already claims `COMPLETE`/`admissible=True`. I verified this
   defense-in-depth is real, not decorative: `test_summary_rejects_short_attempt_even_if_status_claims_complete`
   constructs exactly that adversarial case (a hand-written status file
   claiming completion, contradicted by the summary's `actual_duration_s`) and
   the real `summarize_runs()` call does raise. I traced the arithmetic by
   hand for `test_launch_marks_short_attempt_invalid` (`actual=10.0` vs.
   `planned≈268.97`, shortfall≫1e-6) and it matches the asserted
   `duration_complete=False`/`"planned_duration_not_reached"` exactly.
   `render_markdown` also gained an `actual/planned (s)` column, so a human
   scanning the generated table sees this directly. **Resolved.**

**Note 2 — no calibration-redo path.** Resolved. New
`invalidate_calibration(runtime, rate_hz, suffix, reason)`
([run_rate_study.py:350-380](../../tools/run_rate_study.py)) mirrors
`invalidate_stage`'s shape exactly: validates the `invalid-*` suffix format
and non-empty reason, calls `load_calibration()` first (which itself
re-validates the calibration's hash/schema integrity before allowing the
operation), writes a `calibration-status.json` recording the invalidation,
then `shutil.move()`s the whole `runs/rate{X}-calib/` directory to
`runs/rate{X}-calib-{suffix}/` — freeing the canonical path for
`capture_calibration()` to succeed again (its `mkdir(..., exist_ok=False)`
would otherwise refuse a second calibration for the same rate). I traced the
downstream safety net that already existed from Round 1 and confirmed it
still applies here: `launch_staged_run` reloads `load_calibration()` fresh and
rejects a stage whose recorded `reference_image_sha256` doesn't match the
*current* calibration, so a stage created against a since-invalidated
calibration cannot be silently launched — the new recalibration path composes
correctly with the pre-existing protection rather than needing its own
special case. The extended
`test_prepare_calibrate_stage_and_invalidate_preserve_evidence` exercises this
exact sequence end-to-end with the real functions (invalidate the first
`(0.1,0.2,0.3,0.4)` calibration, capture a revised `(0.11,0.2,0.3,0.4)` one,
confirm the *later* `stage_run` picks up the revised box) and I confirmed it
passes. Evidence is preserved, not deleted, matching every other
invalidate path in this tool. **Resolved.**

**Note 3 — duplicated ratio formula between `AggregationSnapshot` and
`WriteMetrics()`.** Explicitly deferred, and I agree with the reasoning:
resolving it would mean touching `CoverageEvaluator.cs` (the frozen,
twice-reviewed metric-semantics file) for a maintainability improvement with
no behavior change, which is exactly the kind of avoidable risk the binding
clarification about not folding metric-adjacent changes into this rate study
was meant to prevent. Confirmed no `Assets/` file changed in this round, so
the deferral is real, not just claimed. **Appropriately deferred, not a
condition of this gate.**

**Note 4 — `duplicates` detection path untested.** Resolved via a direct test
rather than new production code (none was needed — the detection logic
already existed). New `test_summary_rejects_duplicate_admissible_replicates`
constructs a full valid 12-run set via the `write_attempt` helper, then adds a
13th admissible run for `rate20-follow-r1` under a `-retry-a` suffix whose
manifest still reports the canonical `replicate_id="rate20-follow-r1"` — i.e.,
two admissible runs claiming the same logical replicate. I traced
`summarize_runs`'s existing dictionary-keying loop by hand and confirmed this
input necessarily populates `duplicates` and triggers the `strict` `ValueError`
path; the test's `assertRaisesRegex(ValueError, "duplicates=")` against the
real function confirms it. **Resolved.**

### Regression check on the existing 34 tests

The shared `write_attempt()` test helper now writes `planned_duration_s` into
every generated manifest and defaults `actual_duration_s=269.0` (which exceeds
the ~268.97 s default planned duration, so `duration_complete=True` by
default). I confirmed this default is why the three pre-existing tests that
call `write_attempt()` without overriding `actual_duration_s`
(`test_summary_uses_fixed_cell_medians_and_both_sot_gates`,
`test_summary_blocks_decision_when_20hz_is_unsustainable`, and the shared
setup in the new duplicate test) continue to pass unaffected by the new
duration gate — this isn't an accident I have to take on faith, I checked the
default value against the known planned duration by hand.

### Findings (Round 2)

**Blocking**: none.

**Non-blocking**: none new. All four Round 1 notes are accounted for: three
resolved in code with matching tests I independently traced and reran: note 3
is deferred with sound, explicitly-stated reasoning that I agree with given
its low urgency and the desire to avoid touching the frozen C# metric path
without a behavior-changing reason to do so.

### Verdict

**PASS.** Round 1's `PASS_WITH_NOTES` stands with no blocking defects; all
four notes are now closed (three fixed and verified, one soundly deferred).
Candidate `cbff720` is ready for the two calibration and twelve measured
Unity sessions (`UT-P1-M2-RATE-001-001`); this focused review does not
identify anything that should delay them. Formal M2 closure still requires
the separate `DR-P1-M2-001` fresh-context design audit after the measured
sessions complete.

Handing back to Codex.

## Round 3 — initialization-window amendment (`[3,4)` → `[7,8)` + box-overlay confirmation)

Reviewer/role: Claude Sonnet / independent verification

Round: 3

Date: 2026-07-24

Implementation snapshot: candidate `34dd40a` (focused review range
`d70a7cf..34dd40a`, as requested); docs handoff `94fae8f` on top is
docs-only (confirmed below).

Verdict: **PASS**

### Why this round exists

The first real 5 Hz Unity calibration attempt (`UT-P1-M2-RATE-001-001`) found
the red target visually overlapping a yellow distractor throughout the
entire accepted `[3.0,4.0)` window, and the user separately rejected an
initial response that offered only numeric box coordinates with no visual
overlay to confirm against. No `rate5-calib` directory had been created, so
the rejected attempt contaminated no evidence. The user approved replacing
the window with `[7.0,8.0)` (both rates, same half-open window) plus a
mandatory rectangle-overlay confirmation step before this candidate was
built. This is exactly the kind of change the workflow's mandatory-stop list
names explicitly ("改变...坐标或时间语义...的 work item"), so it correctly
re-entered a focused Sonnet gate rather than shipping directly.

### Scope discipline

`git diff d70a7cf..34dd40a --stat`: 7 files, 312 insertions/38 deletions —
`docs/current-status.md`, `docs/phase1-single-drone-design.md`,
`docs/proposals/P1-M2-RATE-001-frozen-rate-study.md`, `docs/unity-test-log.md`
(docs/design/proposal, read as context per the accepted amendment), plus
`runtime/README.md`, `tests/test_rate_study.py`, and `tools/run_rate_study.py`
(code). `git diff d70a7cf..34dd40a --stat -- config/ Assets/` is empty —
independently confirmed zero files under those paths changed. `git diff
34dd40a..94fae8f --stat -- config/ Assets/ tools/ tests/` is also empty, so
`34dd40a` is the correct code snapshot and `94fae8f` is docs-only. No
implementation code was modified during this review.

### Verification performed

Reran the automated evidence myself rather than trusting the report:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 37 tests in 0.281s — OK
$ .venv-track/bin/python -m pip check
No broken requirements found.
$ python3 -m py_compile controller/*.py tools/*.py tests/*.py
(clean)
$ git diff --check
(clean)
```

Same test count as Round 2 (37) — this amendment extends existing test
methods with new assertions rather than adding new ones, which matches what
I found reading the diff.

I also found the actual retained-frame smoke evidence Codex cited still on
disk and checked it directly rather than taking the claim on faith:

```
$ shasum -a 256 runtime/frames/frame_0000000035.jpg
00a86024b75a917f5c3d33489ee4ebfe9eecc29f4bb81ecbf1711844d2c83def
$ python3 -m json.tool runtime/frames/frame_0000000035.json | grep -E "simulation_time_s|frame_id|scenario_id"
"scenario_id": "rate-study-5hz"
"frame_id": 35
"simulation_time_s": 7.180588722229004
```

Both the hash and the timestamp match exactly. I then viewed the actual
frame image — the red target and the yellow/black distractor car are
**visibly separated** by a clear gap at this frame, unlike the described
overlap earlier in `[3,4)`. This is first-hand visual confirmation of the
amendment's stated motivation, not just a re-statement of Codex's narrative.

### Per-focus-area verification

**`[7,8)` frame selection.** `INIT_WINDOW_S = (7.0, 8.0)`
([run_rate_study.py:32](../../tools/run_rate_study.py)) is the single
constant `_frame_candidates`/`select_init_frame` default against, used
identically for both rates (it is not rate-parameterized, so there is no way
for 5 Hz and 20 Hz to silently drift apart). The extended
`test_prepare_calibrate_stage_and_invalidate_preserve_evidence` writes a
frame at `simulation_time_s=3.1` (deliberately outside the new window) plus
two frames inside `[7,8)` at `7.4` and `7.1`; I confirmed `preview_init_frame`
correctly excludes the `3.1` frame entirely and selects the earlier
in-window one (`7.1`, frame 11) — a direct, real exclusion test, not just a
constant-value assertion. `validate_rate_configs()` now also reports
`init_window_simulation_s`, and the test asserts it equals `[7.0, 8.0]`.

**Green box overlay.** `_render_box_overlay()`
([run_rate_study.py:287-320](../../tools/run_rate_study.py)) draws with
`color = (0, 255, 0)` — OpenCV's channel order is BGR, so this is pure green,
not a coincidental RGB value. I hand-verified the normalized-to-pixel box
math against the test's synthetic 64×48 image: box `(0.1,0.2,0.3,0.4)` →
`left=floor(0.1·64)=6`, `top=floor(0.2·48)=9`,
`right=ceil(0.4·64)-1=25`, `bottom=ceil(0.6·48)-1=28`, giving
`{x:6,y:9,width:20,height:20}` — exactly the value the test asserts, and
exactly what `cv2.rectangle`'s inclusive-corner convention requires.

**Original image not modified.** I read every call site of
`_render_box_overlay` and confirmed `source` and `destination` are always
different paths — `preview_calibration_box` reads the already-separate
`preview_init_frame` copy and writes to a new `...-init-box.jpg`;
`stage_run` reads the staging copy of the frame (itself already a `copy2` of
the retained sensor image, never the original) and writes to a new
`init-box-preview.jpg`. `cv2.imread` never keeps a live handle back to disk,
so nothing in this diff can mutate the file it read from. This isn't just my
read of the code: the test captures `raw_preview_bytes` **before** calling
`preview_calibration_box`, then asserts the raw preview file's bytes are
still exactly equal afterward, and separately asserts the overlay file's
bytes are **not** equal to the raw bytes (proving a rectangle was actually
drawn, not that the function silently no-oped). A real byte-identity check,
not an assumption.

**Hash binding and confirmation gate.** This is layered more thoroughly than
the minimum I'd have asked for:
1. `capture_calibration` now takes a required `confirmed: bool` and raises
   `ValueError` naming "confirmation" if `False`
   ([run_rate_study.py:383-384](../../tools/run_rate_study.py)) — directly
   closing the exact gap the user's rejection identified (numeric coordinates
   alone are not an acceptable confirmation artifact).
2. Before accepting a calibration, it re-reads the box-preview manifest and
   requires `schema_version`, `rate_hz`, `frame_id`, `image_sha256`,
   `metadata_sha256`, and `box_xywh_norm` to all match the **freshly**
   re-selected init frame and the box being submitted — not the frame/box
   the preview was originally generated against, if those have since drifted
   (e.g. a new Play session changed which frame is "first in window"). It
   further re-verifies the overlay file's own path and a freshly-recomputed
   SHA-256 against what the manifest claims. I confirmed via the test that
   submitting a *different* box than what was last previewed raises
   `"box_xywh_norm mismatch"` rather than silently accepting it.
3. The archived calibration directory gains `reference-box-preview.jpg`/
   `.json` and a `reference_box_preview_sha256` field that `load_calibration`
   now also verifies on every subsequent load — so tampering with the
   archived overlay after the fact is caught the same way tampering with
   `reference.jpg` already was.
4. `stage_run` renders a **fresh** overlay of the frozen calibration box onto
   *this run's* freshly-selected init frame (which can legitimately differ
   image-to-image across Play sessions), and `_verify_staged_frame` extends
   its existing hash re-check to include this new overlay before `launch`
   will proceed — reusing the pre-existing `--confirmed` gate on `launch`
   itself rather than adding a second, redundant confirmation flag at the
   staging step. `launch_staged_run` archives the staged overlay into the
   final run directory alongside the other durable artifacts. I confirmed
   the extended `test_launch_requires_confirmation_and_archives_authoritative_artifacts`
   asserts `init-frame-box-preview.jpg` exists in the archived run directory.

### Findings

**Blocking**: none.

**Non-blocking**: none requiring action. One minor observation, already
self-mitigated by the design: `rate-study/previews/` (where transient preview
overlays live) isn't cleared by `prepare_session`/`clean_runtime_slots`, so a
stale preview from an earlier session could in principle linger on disk.
This is harmless in practice — `capture_calibration`'s cross-check compares
the preview's recorded `frame_id`/hashes against the *freshly* re-selected
init frame, so a stale preview simply fails the match with a clear error
rather than being silently accepted. Not asking for a change.

### Verdict

**PASS.** The amendment does exactly what it claims: moves the shared
initialization window to `[7,8)` for both rates, adds a real green-box
overlay that never touches the underlying raw sensor frame, and closes the
confirmation gap the user identified with a multi-layered hash-bound
check-then-archive chain. I independently reproduced the key claims (test
suite, config/Assets diff emptiness, and the retained frame 35 hash/timestamp/
visual-separation evidence) rather than accepting the report at face value.
Nothing here should delay resuming calibration and the 12 measured
`UT-P1-M2-RATE-001-001` sessions.

Handing back to Codex.

## Round 4 — S1 post-launch measurement-window amendment

Reviewer/role: Claude Sonnet / independent verification

Round: 4

Date: 2026-07-24

Implementation snapshot: candidate `fad91da` (focused review range
`3cb0655..fad91da`, as requested); docs handoff `6a47c7a` on top is
docs-only (confirmed below).

Verdict: **PASS**

### Why this round exists

After 8/12 measured sessions, the real `rate20-follow-r1`/`r2` runs were
classified `rate_sustainable=false` because the pre-amendment S1 formula
(`(N-1)/(last-first)` over the *entire* `frames.jsonl` span) counted the
mandatory operator pause between staging and launch confirmation as if Unity
were failing to capture frames — a `99.03 s`/`74.76 s` wall-clock gap against
only `0.055 s`/`0.067 s` of simulation advance. This is exactly a "changes
coordinate/time semantics" work item per the mandatory-stop list, so it
correctly came back for a focused review rather than being silently patched.

### Scope discipline

`git diff 3cb0655..fad91da --stat`: 6 files, 294 insertions/16 deletions —
`controller/run_log.py`, `tools/run_rate_study.py` (code), plus
`docs/phase1-single-drone-design.md`,
`docs/proposals/P1-M2-RATE-001-frozen-rate-study.md`,
`tests/test_rate_study.py`, `tests/test_run_log.py`. `git diff
3cb0655..fad91da --stat -- config/ Assets/` is empty — confirmed zero files
under those paths changed. `git diff fad91da..6a47c7a --stat -- config/
Assets/ controller/ tools/ tests/` is also empty, so `fad91da` is the correct
code snapshot and `6a47c7a` is docs-only. No implementation code was
modified during this review.

### Verification performed

Reran the automated evidence myself:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 43 tests in 0.296s — OK
$ .venv-track/bin/python -m pip check
No broken requirements found.
$ python3 -m py_compile controller/*.py tools/*.py tests/*.py
(clean)
$ git diff --check
(clean)
```

I did not stop at reading the diagnosis document's claimed numbers. The real
`rate20-follow-r1`/`r2` run directories are still on disk, so I recomputed
their post-launch cadence myself, from the raw `frames.jsonl` and
`manifest.json`, using the actual current code — not by reading the
already-written `summary.json`:

```
$ .venv-track/bin/python -c "
from pathlib import Path
from controller.run_log import read_frame_records, build_summary
import json
for run in ('rate20-follow-r1', 'rate20-follow-r2'):
    d = Path(f'runtime/runs/{run}')
    records, truncated = read_frame_records(d / 'frames.jsonl')
    created = json.load(open(d / 'manifest.json')).get('created_unix_s')
    s = build_summary(records, truncated, post_launch_not_before_unix_s=created)
    print(run, s['wall_clock_capture_cadence']['rate_hz'],
          s['wall_clock_capture_cadence_post_launch']['rate_hz'],
          s['wall_clock_capture_window']['eligible_samples'])
"
rate20-follow-r1 14.620359801405344 19.999694311421656 5235
rate20-follow-r2 15.65336808821594 20.0007625176826 5247
```

This is an exact match to the diagnosis document's claimed
`14.62035980/15.65336809 Hz` raw and `19.99969431/20.00076252 Hz` corrected
rates — reproduced from primary timestamps, not read off a report. I also
confirmed the preserved `summary.pre-s1-amendment.json` backups still contain
the old raw-only summary shape (no `wall_clock_capture_cadence_post_launch`
key, same old raw `14.620359801405344`), so nothing was silently overwritten
without a recoverable prior copy — this was a pure read; I did not call
`finalize_run` or write to either run directory.

### Per-focus-area verification

**Raw retention.** `build_summary()`'s existing
`"wall_clock_capture_cadence": _cadence(capture_times)` line
([run_log.py](../../controller/run_log.py)) is untouched — same expression,
same inputs, computed exactly as before. The new
`wall_clock_capture_cadence_post_launch` and `wall_clock_capture_window`
fields are purely additive.

**Cutoff/fail-close semantics.** `_post_launch_capture_window()` reuses the
already-reviewed `_cadence()` helper on a filtered cohort rather than
reimplementing rate/interval math, so "at least two strictly increasing
samples" is inherited for free. A missing, non-finite, or (notably) boolean
`not_before_unix_s` — `isinstance(x, bool)` is explicitly excluded even
though `bool` is an `int` subclass in Python, so a stray JSON `true`/`false`
can't masquerade as a numeric cutoff — all correctly yield an empty eligible
cohort, `rate_hz=None`, and therefore `s1_wall_capture_rate_ge_19hz=False` in
`summarize_attempt`'s sustainability block
([run_rate_study.py:882-885](../../tools/run_rate_study.py)). I confirmed via
`test_summary_fails_s1_closed_without_post_launch_cadence` that even an
**old-format** `summary.json` missing the new key entirely (simulating a
pre-fix artifact) fails S1 closed rather than defaulting to some other value.

**Mid-run stall retention.** This is the property I most wanted to see held:
the cutoff is a one-sided filter (`capture_unix_s >= cutoff`, no upper bound,
no internal gap removal), so a genuine slowdown *after* the tracker launches
would still lower the computed rate. `test_post_launch_cadence_retains_midrun_stall`
proves this directly with a synthetic 1-second post-cutoff gap among three
otherwise-fast samples; I hand-computed the expected rate
(`2/1.05 ≈ 1.905 Hz`) and `p95` interval (`0.05·0.05 + 1.00·0.95 = 0.9525`)
and both match the test's assertions exactly. This means the fix cannot be
used to paper over a real post-launch capture problem — only the
pre-launch human-confirmation pause is excluded.

**Generated report.** `summarize_attempt` now reports
`wall_clock_capture_cadence`, `wall_clock_capture_cadence_post_launch`, and
`wall_clock_capture_window` side by side per run, and `render_markdown` adds
explicit "raw wall Hz" / "S1 post-launch Hz" columns
([run_rate_study.py:1071-1072](../../tools/run_rate_study.py)). I confirmed
`test_markdown_reports_raw_and_post_launch_wall_rates` renders both numbers
(a low raw rate next to a passing post-launch rate, matching the real r1/r2
shape) in the same row rather than hiding the raw diagnostic once the
corrected one is available.

**Real r1/r2 re-analysis.** Covered above — independently reproduced from
primary data, not re-stated from the report.

### Findings

**Blocking**: none.

**Non-blocking**: none actionable. One purely cosmetic observation: when the
cutoff itself is missing, `excluded_prelaunch_samples` reports *every* finite
record as "excluded" (since the eligible set is empty by construction), which
is a slightly imprecise label for "there was no cutoff to filter against" —
but this field is diagnostic-only and doesn't feed any decision (S1 already
correctly fails closed in this case regardless of the count's wording). Not
asking for a change.

One thing worth naming explicitly, since it reflects well on how this was
handled: the diagnosis document's own "Tracking result unaffected" section
is correct and I have no reason to doubt it — this fix corrects a
measurement-window artifact in the *sustainability gate*, not the
`C_track`/`C_geom`/`C_track_given_geom`/`time_to_first_lost_s` values
themselves (untouched by this diff), so it doesn't and can't make the
underlying CSRT finding look better than it is. Both 20 Hz follow runs still
show `C_track=0` and first `LOST` near 3.45 s — the same essential failure
mode as the 5 Hz cells — which is precisely the kind of number a
motivated-reasoning fix would be tempted to touch and didn't.

### Verdict

**PASS.** The amendment does exactly what the diagnosis proposed: excludes
only the human confirmation pause from S1 (verified via the mid-run-stall
test), fails closed on any missing/invalid/insufficient cutoff, preserves
the raw whole-span cadence as an honest diagnostic rather than replacing it,
and reports both numbers transparently. I independently reproduced the
corrected r1/r2 rates from primary timestamps rather than trusting the
report, and confirmed the pre-amendment backups are intact. Nothing here
should delay r3, `rate20-nadir`, or any of the remaining four measured
sessions.

Handing back to Codex.
