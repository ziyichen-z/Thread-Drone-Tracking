# P1-M2-RATE-002 — Independent review

Reviewer: Claude Sonnet (independent review role)

**Latest round: see Round 7.**

## Round 7 — B2 release-coordinator transport-race fix (2026-07-27)

Candidate: `433d816` ("Fix RATE-002 release transport race")
Range reviewed: `1dd7d30..433d816`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-b2-backlog-race-fix.md`

**Scope:** the first corrected-scene B2 smoke reached a healthy moving
heartbeat but its release was rejected by Unity as `backlog_out_of_range`
(ready embedded frame 177, but `frames/latest.json`/tracker-ready had
already advanced to 496 by the time Unity processed the command) and the
session stayed in `HOLD` with no formal attempt produced. This candidate is
the isolated coordinator-side fix, stopped at the mandatory Sonnet gate
before any Unity rerun. Only 2 files changed, +56/-8:
`tools/run_rate2_study.py` and `tests/test_rate2_protocol.py`; zero files
under `Assets/` or `controller/` touched (confirmed by `git diff --stat`).

**Verdict: PASS**

### 1. Is coordinator-side zero backlog plus a second latest read a valid, stricter implementation of the accepted `[0,1]` transaction?

Yes. I read `coordinate_release` and `read_consistent_ready`
(`controller/rate2_protocol.py`, unchanged in this diff) together, not the
diff in isolation. `read_consistent_ready` already read `frames/latest.json`
*before* `tracker_ready.json` and enforced `backlog ∈ [0,1]` at that single
read, returning the observed frame id as its third element (previously
discarded with `_`, now bound to `observed_frame_id`). The fix adds two
things on top, both stricter subsets of what the old code accepted: (a) it
only proceeds when `observed_frame_id == ready_frame_id` — i.e. backlog was
exactly `0`, not `1`, at that read; (b) it then calls `latest_frame_id(runtime)`
a *second*, independent time, immediately before committing, and only
proceeds if that also still equals `ready_frame_id`. This reserves a full
frame of "transport budget": by only ever submitting a ready record that was
confirmed to have zero backlog at two temporally-separated checks, the
command-construction-and-write path (pure in-memory JSON/hash work, no I/O
wait) has a full inter-frame period of slack before Unity's own authoritative
`0 <= current_frame_id - last_processed_frame_id <= 1` check can plausibly
be violated. Root cause was correctly attributed to the coordinator, not
Unity: I confirmed `RateStudyExperimentController.cs`'s backlog check is
untouched by this diff and by the whole `1dd7d30..433d816` range (`git diff
--stat -- Assets/` is empty), so Unity remains the sole authoritative
acceptor and this is purely a client-side heuristic that submits less often,
never differently.

### 2. Do the sequence-advance/freshness requirements still apply to skipped backlog-1 records?

Yes. When a read is skipped (`observed_frame_id != ready_frame_id`, i.e.
backlog was `1`), the `else` branch still advances `previous_seq =
ready_seq` before looping. Since `read_consistent_ready` requires the
*next* read's `ready["seq"]` to be strictly greater than `previous_seq`, a
skipped record cannot be silently reused or compared against a stale
baseline — the next candidate must be a genuinely fresh, newly-published
heartbeat, exactly the pre-existing "two advancing reads" requirement
established in earlier rounds. I hand-traced this against the new test
below and confirmed the second (skipped) read's seq becomes the baseline
that the third (accepted) read's seq must exceed.

### 3. Does 5 ms polling / the CLI override introduce busy-wait, timeout, provenance, or compatibility risk?

No material risk found. `RELEASE_POLL_INTERVAL_S = 0.005` still goes through
`sleeper(poll)` (real `time.sleep`, not a spin loop) between iterations, so
tightening the interval 10× only raises the poll rate to ~200 Hz for local
JSON file reads — well within reasonable bounds for a short-lived (10 s
default timeout, unchanged) coordination script, not a resource-exhaustion
risk. `--poll-interval-s` is wired through `argparse` → `main()` →
`coordinate_release(poll_interval_s=...)` and passes through the
pre-existing `_finite`/positivity validation unchanged (`poll <= 0.0` still
raises `ValueError`), so a bad CLI value fails closed exactly as before. I
grepped `controller/rate2_protocol.py` for `poll_interval`/`RELEASE_POLL`:
zero matches — the interval is a pure orchestration-timing knob that never
enters `build_release_command`, `validate_release_bundle`, or any
hashed/provenance document. Ran `python -m tools.run_rate2_study release
--help` myself and confirmed the flag is genuinely wired, not just declared.
One non-blocking observation below on the theoretical liveness edge case
this stricter check introduces.

### 4. Would the regression fail the old implementation, and does it correctly model one frame of transport?

Yes, and I verified this two ways rather than trusting the narrative claim.
First, by hand-tracing the renamed
`test_coordinator_reserves_transport_frame_then_archives_ack` against the
*new* code frame-by-frame: latest/ready start at `20/20` (backlog 0, but
the first read never accepts — only sets the seq baseline); the sleeper
hook then advances latest to `21` and publishes ready `frame_id=20, seq=21`
(backlog 1) — the second read correctly observes `observed_frame_id(21) !=
ready_frame_id(20)` and skips it; the sleeper then publishes ready
`frame_id=21, seq=22` (backlog back to 0, latest unchanged at 21) — the
third read observes `observed_frame_id(21) == ready_frame_id(21)` *and* the
second, independent `latest_frame_id(runtime)` call also reads `21`, so it
accepts and embeds frame `21` — exactly matching the test's
`state["command_ready_frame"] == 21` assertion. The simulated Unity ack then
reports `release_frame=22` (one more frame having elapsed during transport),
giving `accepted_backlog_frames = 22 - 21 = 1`, within Unity's `[0,1]` gate —
exactly matching the second assertion and exactly modeling "one frame of
command transport" consumed, not zero and not unbounded.

Second, and more decisively, I did not stop at hand-tracing: I checked out
the pre-fix commit (`1dd7d30`) into an isolated `git worktree`, copied only
the new `tests/test_rate2_protocol.py` from `433d816` into it, and ran the
renamed test directly against the *actual* old `coordinate_release` and
unmodified `controller/rate2_protocol.py`. It failed exactly as predicted —
not with an assertion mismatch but with the old code raising
`Rate2ProtocolError: ack backlog is invalid` out of
`validate_release_bundle`, i.e. the old coordinator genuinely constructs a
release transaction that the shared backlog-validation logic (which models
Unity's own gate) rejects, reproducing the real `backlog_out_of_range`
failure mode end-to-end rather than a synthetic assertion difference. The
worktree was removed after verification; no repository state was left
behind.

### 5. Does Unity remain the sole authoritative state owner, with no identity/metric/truth-boundary change?

Yes. `git diff --stat 1dd7d30..433d816` touches exactly
`tools/run_rate2_study.py` and `tests/test_rate2_protocol.py`; zero
`Assets/*.cs` or `controller/*.py` files changed, so `RateStudySession`
validation, the release-command/ack schema, hash binding, and Unity's own
backlog check are all byte-for-byte what Rounds 1–6 already verified. The
new `latest_frame_id` import is the same pre-existing, side-effect-free
function `read_consistent_ready` already used internally; calling it a
second time from the orchestration layer adds no new file, schema, or
identity concept.

### Automated evidence — independently reproduced

- `.venv-track/bin/python -m unittest
  tests.test_rate2_protocol.Rate2ProtocolTests.test_coordinator_reserves_transport_frame_then_archives_ack
  -v` → 1/1 PASS (against the real, unmodified fix).
- `.venv-track/bin/python -m unittest discover -s tests -v` → **76/76**,
  matching the evidence document exactly (no discrepancy to reconcile this
  round).
- `py_compile controller/*.py tools/*.py tests/*.py` → clean; `pip check` →
  no broken requirements; `git diff 1dd7d30..433d816 --check` → clean.
- Checked live `runtime/` state directly rather than trusting the "slots are
  absent" claim: no `experiment_control.json`, `release_ack.json`,
  `release_command.accepted.json`, `tracker_ready.json`, or
  `rate_study_session.json` exists at the runtime root; the frozen
  `runtime/rate-study/P1-M2-RATE-002-B2/` campaign contains only
  `campaign.json` and the `rate20` calibration preview/artifacts — no
  `rs2-pilot` directory anywhere under `runtime/runs/` or
  `runtime/rate-study/`. The qualification pilot and B2 formal measurement
  remain genuinely unconsumed.

### Non-blocking note

The stricter double-zero-backlog check trades a small liveness risk for
safety: if the tracker were ever *chronically* exactly one frame behind for
the tracked run's entire polling window (not just transiently, as in the
real failure), `coordinate_release` would never find a qualifying record and
would correctly time out into the existing `TimeoutError` +
`release_coordinator_failure.json` diagnostic path (unchanged, already
fail-closed) rather than releasing. Under the RATE study's own premise — the
configured capture rate should leave genuine per-frame idle time for the
tracker to catch up, and the coordinator now polls at 5 ms versus a 50–200 ms
frame period — this is an unlikely and already diagnosably-handled edge
case, not a functional defect in this diff.

### Outcome

The fix is minimal, correctly attributes the failure to the coordinator (not
Unity, whose gate is unmodified and remains authoritative), is a strictly
more conservative subset of the previously-accepted `[0,1]` transaction, and
is backed by a regression I confirmed both by hand-derivation and by
actually running it against the real pre-fix code in an isolated worktree,
where it failed with the real `backlog_out_of_range`-shaped error. No
blocking defects found. Per the evidence document's own stated boundary,
this verdict authorizes rebuilding the smoke-only `rs2-pilot` session and
rerunning B2 attempt 2; the shared formal 30 s qualification pilot remains
blocked until that smoke passes.

## Round 6 — Batch B evaluator metrics-cutoff publication fix (2026-07-26)

Candidate: `9c9ceb9` ("fix: publish RATE-002 metrics at frame cutoff")
Focused range reviewed: `0a128b4..9c9ceb9` (the entire range is this one commit)
Implementer evidence: `docs/evidence/P1-M2-RATE-002-metrics-cutoff-fix.md`

**Scope:** the first live Batch B integration smoke (`UT-P1-M2-RATE-002-002`)
passed the heartbeat/release/provenance chain but failed its authoritative
evaluator cutoff: the tracker's `actual_duration_s=5.040644 s` was compared
against a stale `metrics.final.elapsed_simulation_s=4.301775 s`, a `0.739 s`
deficit far outside the `0.05 s` (20 Hz) tolerance. This candidate is the
isolated fix, stopped at the mandatory Sonnet gate before any Unity rerun.
Only 2 files changed, 52 insertions, 0 deletions:
`CoverageEvaluator.cs` and `RateStudyBatchAEditModeTests.cs`.

**Verdict: PASS**

### 1. Is the root cause correctly diagnosed and the fix correctly scoped?

Yes. I read the full current `CoverageEvaluator.cs`, not just the diff.
`Update()` still writes `metrics.json` on a bare one-second `writeTimer`
(lines 187–193, untouched). `OnFramePublished` (lines 195–214) already
recorded the frame's contribution to the in-memory accumulators via
`RecordFrame` *before* this fix existed; the only thing missing was any
mechanism to flush that fresher in-memory state to disk before the next
periodic tick. The added code is exactly that: after `RecordFrame`, if
`RequiresImmediateMetricsWrite(scenario.ExperimentController, frame.FrameId)`
is true, it resets `writeTimer` and calls the existing `WriteMetrics()`
immediately. This is a pure "publish sooner," not a change to what is
computed — `BuildMetricsDocument()`, `AggregateMetrics`, and the JSON schema
are byte-for-byte unchanged (confirmed by rereading the full file; the diff
touches only `OnFramePublished` and adds two new methods).

### 2. Does the new gate correctly target only accepted RATE-002 measurement frames — not HOLD, not the release-boundary frame, not ordinary sessions?

Yes, verified by hand-deriving the boolean logic against
`RateStudyExperimentController`, not by trusting the evidence document's
description:

- `RequiresImmediateMetricsWrite(experiment, frameId)` is `experiment != null
  && experiment.IsActive && MeasurementFrameAllowed(experiment, frameId)`,
  and `MeasurementFrameAllowed` for a non-null experiment is exactly
  `experiment.AcceptsMeasurementFrame(frameId)`.
- `AcceptsMeasurementFrame(frameId)` (`RateStudyExperimentController.cs:359–364`,
  unmodified in this diff) is `!IsActive || (State == Released && frameId >
  ReleaseFrameId)`. Composed with the explicit `IsActive` requirement above,
  the net condition for a non-null, active experiment collapses to `State ==
  Released && frameId > ReleaseFrameId` — i.e. strictly *after* the release
  frame, never during `Hold`, never during `Aborted`, and never on the
  release frame itself (`>`, not `>=`). This is exactly the accepted design's
  release-origin boundary already established in Round 3.
- For an ordinary/non-RATE-002 session, `scenario.ExperimentController` is
  either `null` or present-but-`IsActive == false` (the "no session file"
  passthrough branch in `Initialize()`); both cases make
  `RequiresImmediateMetricsWrite` return `false` unconditionally via the
  explicit `experiment != null && experiment.IsActive` guard, so `writeTimer`
  is never touched and `Update()`'s existing 1 Hz periodic path is the only
  writer — I confirmed no other code path resets or reads `writeTimer` besides
  `Update()` and the new branch.
- I independently traced the new test,
  `Evaluator_Rate2AcceptedFramesRequireImmediateMetricsPublication`, against
  `ControllerFixture.Create()` (which calls `InitializeForTests` and lands in
  `Hold` with `IsActive=true`) and `RateStudySession`/`ProcessCommandForTests`:
  frame 41 while still in `Hold` → `False` (correct: HOLD excluded); after
  `ProcessCommandForTests` accepts a release at frame 42 (`State` flips to
  `Released`, `ReleaseFrameId = 42`), frame 42 itself → `False` (the release
  boundary frame is correctly excluded, matching the pre-existing
  `frameId > ReleaseFrameId` strictness already verified in Round 1's
  `Evaluator_ExcludesHoldFramesAndStartsAtRelease`); frame 43 (first frame
  strictly after release) → `True`; and `RequiresImmediateMetricsWrite(null,
  43)` → `False` (ordinary sessions unaffected). All four assertions check out
  against the real state machine, not just against what the test claims.

### 3. Does this introduce any new risk (partial writes, main-thread cost, or interference with ordinary-session cadence)?

No new risk found. `WriteMetrics()` calls the pre-existing
`AtomicFile.WriteAllText`, which writes to a GUID-suffixed temporary file and
publishes via `File.Replace`/`File.Move` (I read `AtomicFile.cs` directly) —
the same atomicity guarantee already relied on for the periodic 1 Hz case, so
raising the write frequency during a RATE-002 measurement window (up to the
scenario's capture rate, e.g. 20 Hz) does not introduce a torn-read hazard.
`OnFramePublished` runs synchronously on Unity's main thread as a
`SensorFrameWriter.FramePublished` subscriber, so there is no concurrent
writer to race against. The `writeTimer = 0f` reset happens only inside the
new gated branch, so it cannot suppress or delay a periodic write for
ordinary/non-RATE sessions, which never enter that branch.

### 4. Coverage note (non-blocking)

The new test exercises only the extracted static predicate
`RequiresImmediateMetricsWrite`, which is pure and side-effect-free. No test
in this repository invokes the real `OnFramePublished` event handler or
asserts that `metrics.json` on disk is actually refreshed at the moment the
predicate is true — the same structural gap Round 1 flagged for
`RateStudyExperimentController.Initialize()` (both depend on
`TetheredScenarioBootstrap.Instance` and real `Renderer`/camera state that the
Edit Mode fixtures deliberately avoid wiring up). I verified the wiring is
correct by direct code reading (see §1–2 above), but the unit suite alone
cannot distinguish "predicate wired correctly" from "predicate computed but
never consulted." The actual end-to-end proof — that a live `TrackLoop`
cutoff read no longer observes a stale document — remains exactly what the
pending `UT-P1-M2-RATE-002-002` rerun is for, and it should stay the
authoritative confirmation rather than being treated as already covered by
Edit Mode tests.

### 5. Automated evidence — independently reproduced, not trusted from the document

- Both cited Unity result files match the evidence document's claimed SHA-256
  exactly (`shasum -a 256`): `p1-rate-002-metrics-cadence-editmode.xml` →
  `0ee05785a9f88328545a075b9f410f52ddb88b384521eecf9a01b7537981b2d5`;
  `-playmode.xml` →
  `f8ffc801ae2353aff6537f9da4988553ef742ee6a861aeb6412e5c32537b560c`. I read
  both directly rather than trusting the hash alone: Edit Mode
  `testcasecount="45" passed="45" failed="0"`, and the new
  `Evaluator_Rate2AcceptedFramesRequireImmediateMetricsPublication` case is
  present with `result="Passed"`; Play Mode `testcasecount="2" passed="2"
  failed="0"`.
- Reran the Python suite myself: `python3 -m unittest discover -s tests -v` →
  **72/72**, not the evidence document's stated 69/69. I diffed
  `9c9ceb9..HEAD` (current branch tip `eae01b3`) and confirmed the discrepancy
  is fully explained by unrelated post-candidate doc-governance commits: only
  `tools/check_docs.py` and `tests/test_check_docs.py` (3 new test methods,
  confirmed by counting `def test_` in that file) changed between the
  reviewed candidate and HEAD — zero files inside `0a128b4..9c9ceb9` touch
  Python at all (`git diff --stat 0a128b4..9c9ceb9 -- '*.py'` is empty). 69 + 3
  = 72 exactly, so this is not a discrepancy in the reviewed candidate.
- `py_compile controller/*.py tools/*.py tests/*.py` → clean; `pip check` → no
  broken requirements; `git diff 0a128b4..9c9ceb9 --check` → clean;
  `git show 9c9ceb9 --stat` confirms exactly the two files and line counts
  the evidence document claims, no more.

### Outcome

The fix is minimal, correctly targeted at a genuine publication-timing defect
(not a change to any metric definition, formula, or schema), and its
boundary logic — HOLD excluded, release-boundary frame excluded, first
post-release frame triggers an immediate write, ordinary/inactive sessions
keep the unmodified 1 Hz periodic path — is verified correct by direct
derivation against `RateStudyExperimentController`'s state machine, not taken
on the evidence document's word. No blocking defects found. Per the evidence
document's own stated boundary, this verdict authorizes rerunning
`UT-P1-M2-RATE-002-002` only; the formal 30-second qualification pilot
remains blocked until that rerun passes.

## Round 5 — Batch B frozen session-order fix (2026-07-25)

Candidate: `9d33dab` ("fix: enforce frozen RATE-002 session order")
Focused range reviewed: `6d77bc0..9d33dab`
Semantic delta from the Round 4 candidate: `045eb38..9d33dab`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-batch-b.md` (updated in place, "Post-Round-4 fixed-order gate closure" section)

**Scope:** this is a focused fix for Round 4 note 1. Codex did not accept the
asymmetry as intentional: A1 freezes the *entire* execution order, not only
the 20 Hz follow cell, so `authorize_session` must require every predecessor
formal run to be admissible before the next one starts, for every cell (20 Hz
nadir, the 5 Hz calibration boundary, 5 Hz follow, 5 Hz nadir), not just
follow. Only 2 files changed (+62/-17): `tools/run_rate2_study.py` and
`tests/test_rate2_protocol.py`.

**Verdict: PASS**

### What was verified

- **`SESSION_ORDER` is unchanged, just reconstructed.** The 16-item frozen
  session order is no longer hand-written twice (once implicitly via the
  old follow-only gate, once as the literal tuple); it is now built from one
  new `FORMAL_RUN_ORDER` (the 12 formal measurement runs only, in order) via
  slicing: `("rs2-r20-calib", "rs2-pilot", *FORMAL_RUN_ORDER[:3],
  "decision-a", *FORMAL_RUN_ORDER[3:6], "rs2-r5-calib",
  *FORMAL_RUN_ORDER[6:])`. I ran this construction directly in the actual
  module (not just read it) and confirmed the resulting tuple is
  byte-for-byte identical, in the same order, to the literal tuple it
  replaced. This matters because `load_campaign` rejects any campaign whose
  frozen `session_order` differs from the current constant — an accidental
  reordering here would have silently invalidated every campaign frozen
  under the old code, or worse, silently accepted a different order for new
  campaigns. Neither happened.
- **The actual gap is closed.** `authorize_session`'s generic branch (every
  session after `decision-a`) now computes how many formal predecessors a
  session must have — `FORMAL_RUN_ORDER.index(run_id)` for a formal run, or
  a hardcoded `6` for `rs2-r5-calib` (which sits after all six 20 Hz runs but
  is not itself a member of `FORMAL_RUN_ORDER`) — and calls a new
  `_require_admissible_predecessors` helper over that prefix before
  authorizing. I traced every index by hand: `rs2-r20-nadir-2` now requires
  `rs2-r20-nadir-1` (the exact case the original gap allowed to be skipped);
  `rs2-r5-calib` requires all six 20 Hz runs; each 5 Hz run requires every
  formal run before it in the frozen order, all the way through
  `rs2-r5-nadir-3` requiring `rs2-r5-nadir-1`/`-2`.
- **The new predecessor check is a real re-verification, not a flag read.**
  `_require_admissible_predecessors` calls the existing `attempt_row()` for
  each predecessor rather than just reading `rate2-status.json`'s
  `admissible` boolean (which is what the old follow-cell-only code did).
  Since `attempt_row()` re-hashes and cross-checks the manifest, release
  provenance, summary, and metrics files against the status file's own
  recorded hashes and fully re-runs `validate_provenance()`, this is
  actually *stricter* than the check it replaced, not merely extended to
  more cells — a predecessor whose artifacts were tampered with after being
  marked admissible would now be caught here too. I confirmed `attempt_row()`
  is read-only (no `atomic_json`/`create_once_json` calls in its body), so
  using it as a gate here has no side effects.
- **The new test exercises the original defect directly, not just the
  fixed behavior.** The diff to `test_decision_a_is_data_driven_create_
  once_and_gates_remaining_sessions` inserts, immediately after
  `rs2-r20-nadir-1` is first authorized (with no artifacts yet created for
  it): an assertion that authorizing `rs2-r20-nadir-2` now raises
  `PermissionError` mentioning `rs2-r20-nadir-1`, and the same for
  `rs2-r5-calib`. This is exactly the scenario Round 4 note 1 described as
  unguarded. The test then walks every remaining formal run in frozen order,
  authorizing then materializing artifacts for each via `make_run_artifacts`
  before moving to the next, confirming the happy path still works when
  sessions are actually completed in order.
- Independently reran all evidence: `python -m unittest
  tests.test_rate2_protocol -v` → 14/14; `python -m unittest discover -s
  tests -v` → 69/69; `pip check` → no broken requirements; `py_compile
  controller/*.py tools/*.py tests/*.py` → clean; `git diff 6d77bc0..9d33dab
  --check` → clean; confirmed via `git diff --stat` that no file besides
  `tools/run_rate2_study.py` and `tests/test_rate2_protocol.py` changed in
  this range.

### Outcome

The fix is minimal, correctly targeted at the exact gap identified in Round
4, verifiably preserves the frozen session order's byte identity, and is
backed by a test that reproduces the original unguarded-skip scenario before
confirming the fix. Round 4 notes 2 and 3 (the harmless extra heartbeat field
and the optional HOLD-period diagnostic computation) remain accepted as
non-blocking and are unaffected by this change. No new defects found. Batch
B's Python implementation remains cleared; per the user's stated intent, no
Unity integration test or qualification-pilot session is authorized to start
before this verdict, and none should be consumed prematurely once it does.

## Round 4 — Batch B Python release pipeline (2026-07-25)

Candidate: `045eb38` ("feat: implement RATE-002 Python release pipeline")
Review range: `a662af3..045eb38`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-batch-b.md`
Handoff commit: `8f9fb2d`

**Scope:** Batch B implements the Python side of RATE-002 — the tracker-ready
heartbeat and coordinator, the exact-byte release/provenance evidence chain,
`TrackLoop`'s release-origin time base, v1/v2 sensor-schema consumer
migration, the calibration/pilot binding flow, per-run admission, and the
Decision A statistics/execution gate — against the accepted proposal §§2, 4,
5, 7–10 and the A1 amendment. This is a large candidate (2 new files, 604 +
1331 lines; +3023/-40 total); every file was read in full, not sampled.

**Verdict: PASS**

### What was independently verified (not taken on the evidence document's word)

- **`controller/rate2_protocol.py`** (604 lines, new, read in full): confirmed
  `validate_session`/`validate_ready`/`validate_identity` mirror Unity's
  Batch A `RateStudySession`/`TrackerReadyDocument` field-for-field (same
  batch/tracker/run-scenario/hash rules, same `minimum_ready_seq`/
  `minimum_processed_frames == 20`); confirmed `HEARTBEAT_MAX_AGE_S = 2.0` is
  exactly 2× `HEARTBEAT_INTERVAL_S = 1.0`, matching the accepted "≤ 2× 声明
  心跳间隔" freshness rule; confirmed `create_once_bytes`/`create_once_json`
  use `os.link` (a hard link, which atomically fails with `FileExistsError`
  if the destination already exists) rather than `os.replace`, which is the
  correct OS-level primitive for true create-once semantics — a check-then-
  write race here would have been a real immutability hole; hand-traced
  `read_consistent_ready`'s ordering (read `latest.json` before the ready
  heartbeat) against the accepted "读 frames/latest.json → 读心跳" order and
  confirmed it is the conservative direction (biases toward the tracker
  having *more* time to catch up, not less); hand-traced
  `validate_release_bundle` field-by-field against Unity's actual
  `ExperimentControlDocument`/`ReleaseAckDocument` fields from the Batch A
  review (command/ready/ack identity, command hash, ready hash, embedded-byte
  re-hash, ready-seq/processed/last-frame cross-check against the ack's own
  echoed values, `current_frame_id == release_frame_id`, independently
  recomputed backlog `∈ [0,1]` cross-checked against the ack's own
  `accepted_backlog_frames`); confirmed `validate_provenance` can
  reconstruct an effective session purely from `manifest["rate2"]` (no live
  `rate_study_session.json` required), which is necessary since finalization
  can happen long after a live session file was replaced by a later run.
- **`controller/track_loop.py`/`run_log.py`**: read the complete current
  files, not just the diff, specifically to answer whether the *first*
  logged record (from `initialize()`) is correctly tagged `phase="hold"`
  under RATE-002 — confirmed `_append_record` (called from `initialize()`)
  runs *before* `self.rate2_lifecycle.publish_ready(...)`, so
  `self.release_ack` is still `None` at that point and `frame_phase()`
  correctly returns `"hold"` for the init record, which is exactly what
  excludes it from `measurement_records` in `build_summary`. Confirmed the
  per-frame (not per-batch) `frame_phase(bundle.metadata) == "measurement"`
  gate on `allow_control` in `process_available` — even within one batch of
  frames processed together after a release is noticed, each frame's own
  `capture_monotonic_s` decides whether it may drive a control command, not
  a single "have we ever released" flag. Hand-verified that for **non**-
  RATE-002 runs `measurement_elapsed_s = simulation_time_s -
  initial_simulation_time_s` computed via the new code path is
  mathematically identical to the old `max(simulation_times) -
  min(simulation_times)` formula (since `initial_simulation_time_s` is a
  per-run constant equal to the minimum `simulation_time_s` under normal
  monotonic frame ordering) — i.e., no behavior change for RATE-001/ordinary
  runs, only a code-path change. Confirmed the R3′ right-censoring value is
  the *planned* duration (`manifest.get("planned_duration_s")`, a
  pre-existing field, passed only when `provenance is not None`), not the
  observed `actual_duration_s`, matching the accepted "无 LOST 则取 release
  基线的 planned duration" rule exactly — and confirmed this new behavior is
  gated to RATE-002 only (`planned_duration_s=None` for ordinary runs
  preserves the old right-censoring value). Confirmed `finalize_run` is
  fail-closed on any provenance-chain problem (`INVALID_RELEASE`) and that
  `build_summary`'s own monotonic-cadence check separately fails closed
  (`INVALID_CLOCK`) on a missing, non-finite, pre-release, or
  non-strictly-increasing post-release monotonic capture time.
- **`tools/run_rate_study.py`** (17-line diff): confirmed the exact
  historical "silent skip" anti-pattern is gone — a frame matching the
  requested `scenario_id` but the *wrong* schema now raises instead of being
  silently `continue`d past — and that RATE-001's own internal call site is
  unchanged (still defaults to v1), while `run_rate2_study.py` is the one
  real caller that passes `expected_sensor_schema=SENSOR_SCHEMA` (v2).
  Grepped for all call sites to confirm this division.
- **`tools/run_rate2_study.py`** (1331 lines, new, read in full): traced the
  entire session lifecycle — `prepare_campaign` (create-once, and explicitly
  refuses to freeze if any `rs2-*` run directory already exists, closing the
  "freeze before data" requirement) → `build_session`/`prepare_session`
  (rejects stale runtime slots, binds non-calibration sessions to the
  already-frozen calibration's exact frame/hash) → `preview_calibration`/
  `freeze_calibration` (unlimited-HOLD preview, `confirmed=True` required,
  re-verifies every hash before copying into the frozen calibration
  directory) → `coordinate_release` (the live consistent-read loop: reads
  one baseline `seq`, then blocks until a *strictly newer* seq is observed
  before immediately binding those exact bytes into the release command —
  matching "无人工停顿" between final check and release; archives a
  diagnostic `release_coordinator_failure.json` on every failure path) →
  `finalize_attempt` (evaluator/tracker duration cross-check with a
  one-frame-period tolerance, S1′ computed from the *monotonic* post-release
  cadence rather than civil wall-clock time, S2/S3 gated only for the 20 Hz
  cell exactly as accepted design item 5 specifies) → `attempt_row`/
  `build_decision_a`/`validate_decision_a`. `validate_decision_a` in
  particular fully *recomputes* the medians, per-rule thresholds/
  comparisons, the OR aggregation, the sensitivity table, and the actual
  execution order from the live on-disk artifacts on every call, rather than
  just checking the frozen file's internal schema — meaning no version of
  `decision_a.json` can be trusted merely because it parses; it must
  continue to match freshly-rehashed, freshly-recomputed reality. Confirmed
  the R1′/R2′ zero-input overrides (`c_geom<=0.0 or matched==0 →
  c_track_given_geom:=0`; `matched==0 → incorrect_over_matched:=1.0`) and
  that R3′ always contributes *exactly one* value per run regardless of
  which runs happen to report LOST, so the median population size is fixed
  at 3 by construction. Confirmed `authorize_session`'s execution gate:
  `rs2-r20-follow-{2,3}` require all prior follow runs to already be
  admissible; every session after `decision-a` (nadir cell, 5 Hz calibration
  and cells) requires `validate_decision_a(...)["final_action"] ==
  "CONTINUE_REMAINING_CELLS"`, and `BLOCKED_INVALID_CELL` can only be
  recorded once every missing run has exhausted the 3-attempt limit
  (1 initial + 2 reruns, matching the accepted 补跑上限 2 次).
- **`tests/test_rate2_protocol.py`** (840 lines, new, all 14 cases read in
  full): these are genuine end-to-end tests against real temporary-directory
  I/O (including a real `cv2`-written JPEG for the calibration-overlay test
  and a real `TrackLoop`/`RecordingTracker`/`Rate2TrackerLifecycle`
  integration test), not shallow mocks. I independently hand-recomputed the
  numeric expectations in the two most load-bearing cases rather than
  trusting the assertions: in
  `test_track_loop_holds_controls_then_uses_release_phase`, given the test's
  own written frame timestamps (`simulation_time_s = 7.0 + frame_id·0.05`)
  and release ack (`release_simulation_s = 7.075`), frame 2's measurement-
  elapsed value is `7.10 − 7.075 = 0.025` and frame 3's is `7.15 − 7.075 =
  0.075` — both match the asserted values exactly, and `0.075 ≥
  planned_duration_s(0.05)` correctly flips `loop.complete` to `True` only
  at frame 3, not frame 2. In `test_long_hold_is_excluded_from_all_
  measurement_outcomes`, mutating the second measurement record's
  `capture_monotonic_s` from `510.0` to `500.05` (below the first
  measurement record's `500.1`) creates a non-strictly-increasing monotonic
  sequence and correctly raises `INVALID_CLOCK` — I confirmed this is the
  *only* mutation needed to flip the result, isolating the exact code path
  being tested.
- Independently reran all automated evidence rather than trusting the
  reported counts: `.venv-track/bin/python -m unittest discover -s tests -v`
  → 69/69; `python -m unittest tests.test_rate2_protocol -v` → 14/14 (all
  named cases individually `ok`); `pip check` → no broken requirements;
  `py_compile controller/*.py tools/*.py tests/*.py` → clean; `git diff
  a662af3..045eb38 --check` → clean; `python -m tools.run_rate2_study --help`
  → works. Independently recomputed the real pinned NanoTrack-v2 identity
  hashes myself from the on-disk models (not from the evidence document) and
  got `tracker_identity_sha256 = 51b58a238c706c96fda64a4592aa8695cf7f5afea
  6307e3134e581e908beda8e` and `model_identity_sha256 =
  fe6505f5ef0ca94d74807b85c4d60c9f8776575035365e0d2996d4a88caf4d23`, exactly
  matching the evidence document's claimed values. Ran a real
  `python -m tools.run_rate2_study prepare-campaign` against a scratch
  runtime directory (outside the project's real `runtime/`) and confirmed it
  produces a schema-correct `campaign.json` with the exact frozen session
  order and `trigger_branch="stop"` — the CLI wiring itself is genuinely
  functional, not just exercised through unit-test call sites.

### Notes (non-blocking; none indicate incorrect behavior)

1. `authorize_session` enforces strict in-order admissibility only for the
   20 Hz follow cell (`rs2-r20-follow-2`/`-3` each require every prior follow
   run to already be admissible); the nadir cell and 5 Hz cells only require
   Decision A's `CONTINUE_REMAINING_CELLS` once, with no equivalent
   run-to-run ordering check. This appears deliberate — only the follow cell
   feeds the pre-registered Decision A statistics, so it is the one place
   where run-quality gating actually matters for scientific validity — but
   it is worth confirming with Codex that this asymmetry is intentional
   rather than an oversight, since nothing in the accepted design explicitly
   states it either way.
2. The Python-published `p1-rate2-tracker-ready/v2` heartbeat now includes a
   `heartbeat_interval_s` field that has no counterpart in Unity's Batch A
   `TrackerReadyDocument` C# type. This is harmless (Unity's `JsonUtility`
   silently ignores unrecognized JSON properties, and the hash/byte-binding
   chain operates on raw bytes regardless of which fields either side's
   parser recognizes), but it is a minor schema asymmetry between the two
   languages' notions of "the same" v2 ready schema.
3. Under RATE-002, `TrackLoop._publish_latest(..., allow_control=False)`
   returns immediately after publishing the tracking observation, skipping
   the ground-intersection/look-at computation entirely during HOLD. The
   accepted design's §6 permits (not requires — "可内部计算并记录…（诊断）")
   retaining this computation for diagnostic value even while suppressing
   publication; the current implementation does the minimum compliant thing
   (skip both) rather than the optional stronger one (compute but don't
   publish). Not a defect, just a foregone diagnostic opportunity.

### Outcome

Every accepted-design requirement I could check against real code and real
tests — the heartbeat/coordinator protocol, the exact-byte/hash provenance
chain and its create-once immutability, the release-origin time base and
HOLD exclusion on both the tracker and evaluator sides, the real v1/v2
schema-enforcement points, the calibration/pilot identity binding, the S1′
monotonic sustainability gate, the R1′/R2′/R3′ statistics and their
zero-input/right-censoring edge cases, and Decision A's tri-state,
create-once, fully-reverifying execution gate — was implemented correctly
and is backed by tests that exercise the actual failure mode, not a
convenient stand-in for it. No blocking defects were found. Batch B's Python
implementation is cleared; no Unity integration, qualification pilot, or
measurement is authorized by this verdict, consistent with the evidence
document's own stated boundary.

## Round 3 — Batch A release-origin elapsed-time fix (2026-07-25)

Candidate: `af165eb` ("fix: measure evaluator elapsed time from release")
Focused range reviewed: `bacbbc7..af165eb`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-batch-a.md` (updated in place)
Handoff commit: `56333dc`

**Context:** the first real user run of `UT-P1-M2-RATE-002-001` (recorded in
`docs/unity-test-log.md`) passed HOLD/v2 publication and command suppression,
and even proved the release transaction/evidence chain, but case 3 found that
`metrics.json.elapsed_simulation_s` read `11.982766 s` about `0.95 s` after
release — the field was serializing the frame's absolute simulation-clock
reading rather than a release-gated duration. This candidate is the isolated
fix plus regression coverage, still stopped at the mandatory Sonnet gate
before the user reruns cases 3–4.

**Verdict: PASS**

### 1. Does `elapsed_simulation_s` now genuinely accumulate from release?

Yes. `CoverageEvaluator.cs`'s only substantive change is deleting the
`lastSimulationTime` field (previously set to `frame.SimulationTimeSeconds`,
an absolute since-scenario-start clock reading, inside `RecordFrame`) and
reporting `elapsed_simulation_s = totalDuration` instead. `totalDuration` is
not a clock reading — it is the same incrementally-accumulated
duration-weighted counter (`totalDuration += weight` per accepted frame) that
already backs the `c_geom`/`c_track` denominators, and `RecordFrame` (the only
place either quantity is touched) is reachable only through
`OnFramePublished`/`RecordAggregationFrameForTests`, both gated by the
pre-existing `MeasurementFrameAllowed(experiment, frameId)` check. Since that
gate accepts only frames strictly after the acknowledged release
frame (or everything when no RATE session is active), `totalDuration` starts
at exactly `0` at the first accepted frame after release and grows only by
each accepted frame's delta thereafter — which is precisely "elapsed time
since release," not "elapsed time since scenario start." I traced this by
hand against the actual field, not just the evidence document's description.

### 2. Would the new long-HOLD public-JSON regression actually have caught the original defect?

Yes — I hand-simulated the pre-fix code against the new test
(`Evaluator_PublicElapsedTimeExcludesLongHoldAndUsesAcceptedDuration`) rather
than trusting the claim. The test records a rejected HOLD frame at absolute
simulation time `1000.0 s` (frame 41, before release — correctly excluded by
the pre-existing gate under both old and new code), releases at
`simulationSeconds: 1000.0`, then records two accepted frames at `1000.05 s`
and `1000.10 s` (frames 43/44, each contributing a `0.05 s` weight). It reads
the field back through the new `evaluator.MetricsJsonForTests()` seam and
asserts `elapsed_simulation_s == 0.10 s`. Under the *old* code, `lastSimulationTime`
would still have been set to the last accepted frame's absolute
`SimulationTimeSeconds` (`1000.10 s`, since frame 41 never reaches `RecordFrame`
either way) — the assertion `Is.EqualTo(0.10f).Within(1e-6f)` would fail by
three orders of magnitude against an actual `1000.10`. This is not a
coincidental match to the real defect's shape (a huge absolute value where a
small relative one was expected); it is the same defect, reproduced
deterministically. The test also asserts `SensorFrames == 2`, reconfirming
frame 41 is excluded exactly as in the Round 1/2 evaluator-gating tests.

### 3. Are the other aggregate metrics unchanged?

Yes. I reread the full file. `AggregateMetrics`'s other seven fields
(`c_geom`, `c_track`, `c_track_given_geom`, `mean_visible_sample_fraction`,
`mean_target_bbox_area_px_when_visible`, `rms_target_center_error_px_when_visible`,
`sensor_frames`, `matched/unmatched/incorrect_tracking_observations`),
`AggregationSnapshot`, and `OnGUI()`'s live readout are byte-for-byte
unchanged — they were never touched by this diff and were already backed by
the same accepted-frame-only accumulators (`geometricDuration`,
`trackingDuration`, `visibleFractionIntegral`, `visibleAreaIntegral`,
`visibleCenterErrorSquaredIntegral`, `sensorFrames`,
`matched/unmatched/incorrectObservations`), none of which ever stored a raw
clock reading the way the deleted `lastSimulationTime` did. The defect was
genuinely isolated to the one field built differently from the rest, and the
fix does not touch anything else. The refactor that extracted
`BuildMetricsDocument(geometry, gimbalSaturated, tetherSaturated)` out of
`WriteMetrics()` (to add the test-only `MetricsJsonForTests()` seam) is a pure
parameter-passing extraction — the production `WriteMetrics()` still sources
`geometry`/`gimbalSaturated`/`tetherSaturated` from
`TetheredScenarioBootstrap.Instance` exactly as before and passes them in
unchanged.

### 4. Is the Play Mode 0.02 s wait only removing test-timing flakiness?

Yes. The diff adds exactly one line
(`yield return new WaitForSeconds(0.02f);`) between the two existing
`yield return null;` calls in `Hold_FollowAndNadirHaveIdenticalPreReleasePlatformAndCameraPose`;
no assertion, expected value, or tolerance in that test changed. The rig's
`Gimbal.slewRateDegPerSecond = 10000f` is a test-only exaggerated rate (set in
`ConditionRig.Create()`, unchanged in this diff): closing the deliberately
displaced `follow` gimbal's angular gap to the declared nadir orientation
needs only a few milliseconds at that rate, but two bare `yield return null`
frames do not guarantee any particular amount of elapsed `Time.deltaTime` in
the Editor Test Runner. `WaitForSeconds(0.02f)` waits on the same scaled-time
clock the gimbal's rotation uses, so it guarantees at least `20 ms` — roughly
4–5x the time actually needed — regardless of how many discrete Update ticks
occur inside that span. This is consistent with the evidence document's
account of the first post-fix run reaching `x=0.675188` instead of
`x=0.707107` (an incomplete slew, not a wrong target) and requires no change
to `GimbalCommandReceiver`, `TetheredGimbal`, or any other production file to
explain.

### Additional checks performed

- Confirmed via `git diff bacbbc7..af165eb --stat -- Assets/` that the only
  runtime file touched is `CoverageEvaluator.cs`; `BodyCommandReceiver.cs`,
  `GimbalCommandReceiver.cs`, `RateStudyExperimentController.cs`,
  `SensorFrameWriter.cs`, and `TetheredScenarioBootstrap.cs` are untouched in
  this range (the Round 1/2 findings about those files still stand as of
  their last review).
- Reran both automated suites myself: `runtime/test-results/p1-rate-002-elapsed-fix-editmode.xml`
  (`testcasecount="44" passed="44" failed="0"`, with the new test's own
  `<test-case ... result="Passed">` entry read directly) and
  `-playmode.xml` (`testcasecount="2" passed="2" failed="0"`, both cases
  individually `result="Passed"`).
  `.venv-track/bin/python -m unittest discover -s tests -v`: 55/55 pass;
  `pip check`: no broken requirements; `git diff bacbbc7..af165eb --check`:
  clean; zero Python files changed in this range.
- Noted in passing (out of scope for this focused code review, and not
  implemented in this range): the same commit also bundles a separate,
  already Codex-accepted design amendment ("修订 A1 round 2") to
  `docs/proposals/P1-M2-RATE-002-successor-rate-study.md` and
  `docs/phase1-single-drone-design.md`, reordering the measurement session
  sequence and adding a pre-registered "Decision A" stop point. This is a
  design/orchestration decision with no C#/protocol change and is not part of
  what I verified here; it belongs to a future Batch B orchestration review
  when it is actually implemented.

### Outcome

The fix is minimal, correctly scoped to the one defective field, and directly
verified against the pre-fix behavior by hand rather than taken on the
evidence document's word. `docs/unity-test-log.md`'s failed case-3 attempt is
correctly preserved as real evidence rather than overwritten. This candidate
is cleared for the user to rerun `UT-P1-M2-RATE-002-001` cases 3–4.

## Round 2 — Batch A note-fix focused review (2026-07-25)

Candidate: `94dbe70` ("test: close RATE-002 Batch A review notes")
Focused range reviewed: `bcdb92d..94dbe70`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-batch-a.md` (updated in place)

**Scope:** per the evidence document's "Required next gates," this round
checks only that all four Round 1 notes are closed and that the
dependency-injection refactor to `BodyCommandReceiver`/`GimbalCommandReceiver`
leaves production resolution behavior unchanged. It does not re-review the
Round 1 material that this candidate does not touch.

**Verdict: PASS**

### Verification performed

- Read the full diff (`bcdb92d..94dbe70`, 5 files, +364/-30) in full:
  `BodyCommandReceiver.cs`, `GimbalCommandReceiver.cs`,
  `RateStudyExperimentController.cs`, and both updated test files.
- **Note 1 (missing follow/nadir pre-release pose-identity assertion) — closed.**
  New Play Mode test
  `Hold_FollowAndNadirHaveIdenticalPreReleasePlatformAndCameraPose` builds two
  fully independent rigs (`ConditionRig`, one `follow`-run-ID, one
  `nadir`-run-ID), each with its own platform/camera/drone/gimbal/controller,
  wired via the new `ConfigureForTests` injection so the test does not depend
  on a shared `TetheredScenarioBootstrap` singleton. It deliberately diverges
  the two rigs' initial gimbal state before any gating runs
  (`follow.Gimbal.LookAtWorld(...)` vs `nadir.Gimbal.LookNadir()`, asserting
  `HasTarget` differs first), lets two real frames elapse, then asserts both
  remain in `Hold`, both gimbals converge to `HasTarget == false`, both
  drones' `CommandedVelocity == Vector3.zero`, and then compares platform
  position/rotation and camera position/rotation component-by-component
  (`Within(1e-6f)` on every `x/y/z/w`) — exactly the accepted design's
  "两条件平台位姿逐分量一致" requirement. It further checks the shared pose
  equals `Quaternion.Euler(90f, 0f, 0f)`, the same literal nadir-camera
  constant already used by `RateStudyScoutingTool`'s nadir scouting pose, so
  the test confirms the shared state is the *declared* nadir pose, not merely
  an accidental match between the two rigs. I confirmed `TetheredGimbal
  .HasTarget`/`LookAtWorld`/`LookNadir` and `TetheredDronePlant
  .CommandedVelocity`/`Hold()` (both pre-existing, unmodified in this range)
  behave exactly as the test assumes.
- **Note 2 (`Initialize()` production entry point untested) — closed.** Three
  new Edit Mode tests exercise the real `Initialize()` method (via a new
  4-argument internal overload that accepts an explicit runtime-root path
  instead of hardcoding `RuntimePaths.Root`, used only by tests — the
  production 3-argument `Initialize()` now just delegates to it with
  `RuntimePaths.Root`, so the production call site and its behavior are
  unchanged): `ProductionInitialize_NoSessionPreservesOrdinaryPassthrough`
  (no session file → `IsActive=false`, no `experiment_state.json` written),
  `ProductionInitialize_InvalidScenarioOrStaleSlotBlocksHold` (parameterized:
  scenario mismatch → `invalid_session_scenario`; a stale `tracker_ready.json`
  left on disk with an otherwise-valid, matching session →
  `stale_runtime_slot`), and `ProductionInitialize_ValidSessionEntersHoldFromDisk`
  (a genuinely valid on-disk session is loaded, `controller.Session.run_id`
  confirms the real file was parsed, and `experiment_state.json` shows `HOLD`
  with no rejection code). Together these cover all three branches of
  `Initialize()` plus the happy path, all through the disk-loading path the
  test previously skipped.
- **Note 3 (shared-reference test-isolation smell) — closed.** The test
  (renamed `InvalidSessionIdentity_...`) now calls the new
  `ControllerFixture.CloneSession(...)`, a `JsonUtility` round-trip deep copy,
  instead of aliasing `fixture.Session` directly.
- **Note 4 (only one identity dimension tested) — closed.** The same test is
  now `[TestCase("study")]`/`["tracker"]`/`["run_scenario"]`/`["hash"]`
  parameterized, independently corrupting `study_id`, `tracker_id`,
  `scenario_id` (against the same `run_id`, producing a real
  run/scenario-pairing mismatch), and `model_identity_sha256` respectively,
  each asserted to block in `Hold` with `ControlEnabled`/`MeasurementEnabled`
  false and no invented state — I traced each case against
  `RateStudySession.Validate()` and confirmed each one lands on a distinct
  validation branch (batch/tracker identity, run/scenario pairing, hash
  well-formedness).
- **Dependency-injection refactor leaves production resolution unchanged.**
  `BodyCommandReceiver`/`GimbalCommandReceiver` gained private
  `experimentOverride`/`droneOverride`/`gimbalOverride` fields and an
  `internal ConfigureForTests(...)` setter; every read site changed from
  `TetheredScenarioBootstrap.Instance?.X` to `override ?? scenario?.X`. I
  grepped the whole `Assets/` tree and confirmed `ConfigureForTests` is called
  nowhere except the new Play Mode test — in production the override fields
  are always null, so `?? scenario?.X` evaluates identically to the prior
  direct lookup. `TetheredScenarioBootstrap.cs` itself is not part of this
  diff, confirming the real bootstrap wiring is untouched.
- Reran both automated suites myself rather than trusting the reported counts:
  - `runtime/test-results/p1-rate-002-notes-editmode.xml`: `testcasecount="43"
    passed="43" failed="0"`; every `fullname` matches an actual test method
    (including all four `InvalidSessionIdentity_...` cases and all three new
    `ProductionInitialize_...` tests).
  - `runtime/test-results/p1-rate-002-notes-playmode.xml`: `testcasecount="2"
    passed="2" failed="0"`, matching both
    `HoldAndRelease_GateMotionAndMeasurementAcrossFrames` and the new
    `Hold_FollowAndNadirHaveIdenticalPreReleasePlatformAndCameraPose`; both
    raw logs end with `Test run completed. Exiting with code 0 (Ok)`.
  - `.venv-track/bin/python -m unittest discover -s tests -v`: 55/55 pass;
    `pip check`: no broken requirements; `git diff bcdb92d..94dbe70 --stat --
    '*.py'` is empty, confirming this candidate is still Unity-only.
  - `git diff bcdb92d..94dbe70 --check`: clean.

### Outcome

All four Round 1 notes are closed with real, targeted regression tests (not
just narrative claims), and the dependency-injection seam added to make them
possible is verifiably inert in production. No new defects were found in this
focused range. `P1-M2-RATE-002` Batch A's infrastructure stop point is now
fully satisfied from an independent-review standpoint; the focused user Unity
infrastructure case `UT-P1-M2-RATE-002-001` may proceed.

## Round 1 — Batch A only (2026-07-25)

Candidate: `21eaeca` ("feat: add RATE-002 Unity release barrier")
Range reviewed: `4c9ca32..21eaeca`
Implementer evidence: `docs/evidence/P1-M2-RATE-002-batch-a.md`
Accepted design: `docs/proposals/P1-M2-RATE-002-successor-rate-study.md` (round 3,
`ACCEPTED_WITH_BINDING_CLARIFICATIONS`)
Formal design: `docs/phase1-single-drone-design.md` §3 (RATE-002 paragraph)

**Scope note:** per explicit instruction, this round reviews only the Batch A
Unity infrastructure candidate, not the full RATE-002 work item. Batch B
(Python heartbeat/coordinator/provenance validation/v2 consumer migration/
release-based statistics) is out of scope and has not started.

**Verdict: PASS_WITH_NOTES**

### What was verified directly (not taken on the evidence document's word)

- Read the full diff `4c9ca32..21eaeca` (24 files, +1960/-39) and every new/
  changed source and test file in full: `RateStudyExperimentController.cs`,
  `RateStudyProtocol.cs`, `RateStudyScouting.cs`, `RateStudyScoutingTool.cs`,
  `RateStudyDistractor.cs`, and the diffs to `BodyCommandReceiver.cs`,
  `CoverageEvaluator.cs`, `GimbalCommandReceiver.cs`, `LoopTargetVehicle.cs`,
  `SensorFrameWriter.cs`, `TetheredScenarioBootstrap.cs`, `AssemblyInfo.cs`.
- Read all 21 new Edit Mode cases (`RateStudyBatchAEditModeTests.cs`) and the
  1 new Play Mode case (`RateStudyBatchAPlayModeTests.cs`) and hand-traced
  every assertion against the implementation rather than trusting the
  evidence document's category list.
- Confirmed the state machine matches the accepted round-3 design exactly:
  `HOLD → RELEASED`, terminal `ABORTED`; no independent `ARMED` state exists
  anywhere in the code. The two accepted abort triggers (explicit `abort`
  command, and fatal command/ready identity mismatch detected during
  transaction verification) are the only call sites of `Abort()`
  (`RateStudyExperimentController.cs:199,204,263`). A release replay after
  `RELEASED` is rejected and persisted while state stays `RELEASED`
  (`ProcessCommand`, lines 207–211) — matches the round-3 binding
  clarification that this is *not* an abort.
- Confirmed the backlog check `0 <= current_frame_id - last_processed_frame_id
  <= 1` is evaluated inline inside `ProcessCommand`, using
  `frameWriter.LastPublishedFrameId` sampled at the same `Update()` tick that
  detects the command-file change (`PollControl`, lines 118–136) — this is
  the same-Update authoritative re-verification the round-2→round-3 revision
  was written to guarantee, not a narrative claim.
- Confirmed exact-byte/hash binding: the release command embeds
  `ready_json_base64` + `ready_sha256`; `ProcessCommand` recomputes the SHA-256
  of the decoded bytes and rejects on mismatch before parsing
  (`ready_hash_mismatch`, lines 231–235); the accepted command's raw bytes and
  the ack's exact fields (`release_command_sha256`, `ready_sha256`, full
  tracker/model/init identity, accepted frame pair, backlog, three clocks) are
  written atomically via the pre-existing `AtomicFile` helper.
- Confirmed stale-slot hygiene: `PrepareRuntimeSlots` deletes all five
  transaction files and the `experiment_rejections/` directory;
  `HasStaleRuntimeSlot` is checked at `Initialize()` and blocks Hold
  (`invalid_session_scenario`/`stale_runtime_slot` fail-closed) rather than
  inventing a new state.
- Confirmed the evaluator gating is minimally invasive to frozen metric
  semantics: `OnFramePublished`/`OnObservationReceived` each gained exactly
  one early-return line (`MeasurementFrameAllowed`), and the actual
  `C_geom`/`C_track`/`C_track_given_geom` arithmetic in `WriteMetrics()` is
  byte-for-byte unchanged from the version already reviewed in
  `P1-M2-RATE-001`. A frame equal to the release frame itself is excluded
  (`frameId > ReleaseFrameId`, strictly greater); I hand-traced the new
  `Evaluator_ExcludesHoldFramesAndStartsAtRelease` test and confirmed it
  actually exercises this exact boundary (release frame excluded, release+1
  included), not just a coarse before/after check.
- Confirmed the scouting math against the accepted numeric constants: the
  exact candidate set `{k·0.5 | k·0.5 < perimeter}` correctly excludes the
  wrap endpoint (verified by hand for both an exact-multiple and a
  non-multiple perimeter), the closing-segment interpolation is correct
  (hand-computed the `RouteSampling_...` test's expected `(0,0,0.5)` result
  from the square-route fixture myself), "nearest distractor" is defined as
  the minimum-by-distance candidate (not a scan over all distractors for any
  nonzero IoU) and the code/tests are internally consistent on this point
  (`Qualification_UsesMinimumAcrossAllActiveDistractors` deliberately places a
  farther, non-overlapping distractor alongside a closer, overlapping one and
  asserts rejection), and the 1×-target-width separation boundary is tested
  at the exact epsilon-tolerant equality point (127px reject / 128px accept
  for a 128px-wide box).
- Confirmed `SensorFrameWriter`'s v1/v2 schema split is conditional on
  `ExperimentController.IsActive` (not on `State`), so ordinary/non-RATE
  scenarios keep v1 unconditionally; `JsonUtility.ToJson(FrameMetadata)` is
  called on a variable statically typed as the base class but holding a
  `FrameMetadataV2` instance in `BuildMetadata()` — I confirmed this
  serializes the derived fields correctly (Unity's `JsonUtility.ToJson(object)`
  dispatches on the runtime type via reflection, not the compile-time
  reference type), which the new `SensorMetadataV2_...`/`SensorMetadataV1_...`
  tests independently confirm by asserting on the actual emitted JSON string.
- Confirmed the Null-graphics-device capture guard
  (`captureSupported = SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null`)
  only short-circuits `SensorFrameWriter.Update()`/`Start()`'s render-texture
  path; it does not touch the frame-ID counter, manifest schema, or any other
  production behavior when a real graphics device is present.
- Independently reran both automated suites rather than trusting the reported
  counts:
  - `runtime/test-results/p1-rate-002-batch-a-editmode.xml`: read directly,
    `testcasecount="36" passed="36" failed="0"`, and every `fullname` in the
    file matches an actual test method I read in
    `RateStudyBatchAEditModeTests.cs` plus the pre-existing M0/TEST-001/
    RATE-001 Edit Mode fixtures — no orphaned or mismatched test names.
  - `runtime/test-results/p1-rate-002-batch-a-playmode.xml`: read directly,
    `testcasecount="1" passed="1" failed="0"`, matching
    `RateStudyBatchAPlayModeTests.HoldAndRelease_GateMotionAndMeasurementAcrossFrames`.
  - Read the raw Play Mode log and independently confirmed the two
    specific artifacts the evidence document describes as benign: a
    transient licensing-handshake error at startup (`HandshakeResponse
    reported an error`, resolved a few lines later) and a
    `Failed to set the active render target, ensure that it is a valid
    render target.` warning — both present exactly once, followed by
    `Test run completed. Exiting with code 0`.
  - Reran `.venv-track/bin/python -m unittest discover -s tests -v`: 55/55
    pass, matching the evidence document; confirmed via
    `git diff 4c9ca32..21eaeca --stat -- '*.py'` that zero Python files
    changed in this range, consistent with the claimed Unity-only Batch A
    scope.
  - Reran `pip check`: no broken requirements.
  - Ran `git diff 4c9ca32..21eaeca --check`: clean (no whitespace/conflict
    markers), consistent with the evidence document's claim.

### Notes (non-blocking on Batch A's own correctness, but should close before Batch B / the focused Unity case)

1. **Missing regression test for a binding acceptance-criterion item: identical
   pre-release platform/camera pose between follow and nadir.** The accepted
   proposal's Round 1 required revision #4 ("Add a Play Mode assertion for
   identical pre-release platform/camera state") was carried forward
   unchanged through round 2 (§6) and is listed verbatim in round 3's
   acceptance criterion 1 ("释放前指令抑制断言（两条件平台位姿逐分量一致）").
   The underlying *behavior* does appear correctly implemented:
   `GimbalCommandReceiver.Update()` now unconditionally forces
   `Gimbal.LookNadir()` every frame while `!ControlEnabled`
   (`GimbalCommandReceiver.cs:26–29`), and `BodyCommandReceiver.Update()`
   forces `drone.Hold()` under the same condition — both are gated by the
   same `RateStudyExperimentController.ControlEnabled` regardless of whether
   the run is configured as `follow` or `nadir`, which should make the
   pre-release pose declaratively identical across both conditions by
   construction. But no test in either new file (`RateStudyBatchA
   EditModeTests.cs`, `RateStudyBatchAPlayModeTests.cs`) instantiates
   `GimbalCommandReceiver`/`TetheredGimbal` or asserts anything about camera/
   platform pose, let alone compares a `follow`-configured run against a
   `nadir`-configured run component-by-component before release. I searched
   both files for `Gimbal`/`nadir`/`LookAt`/`platform` and found only the
   two generic `AuthorizeControl("gimbal", ...)` rejection-counter
   assertions in `Hold_SuppressesControlAndTargetMotionForSimulatedSixty
   Seconds`, which do not touch pose. This is a concrete, checkable gap
   against the accepted design's own explicit, repeatedly-reaffirmed
   requirement, not a matter of reviewer judgment — Codex should add it
   before treating "基础设施停点" as fully satisfied, ideally before the
   focused `UT-P1-M2-RATE-002-001` Unity case is prepared.
2. **The actual production entry point (`RateStudyExperimentController
   .Initialize()`) has zero automated test coverage.** Every test in both new
   files calls `InitializeForTests(...)`, which bypasses disk I/O entirely
   and — critically — skips the `HasStaleRuntimeSlot()` check that
   `Initialize()` performs at startup. `Initialize()` is the method
   `TetheredScenarioBootstrap` actually calls in production
   (`TetheredScenarioBootstrap.cs`, new wiring order:
   `FrameWriter` → `ScoutingTool` → `ExperimentController.Initialize(Config,
   Target, FrameWriter)` → `BodyCommandReceiver`/`GimbalCommandReceiver`), and
   it contains three branches with no direct coverage: (a) no
   `rate_study_session.json` on disk → ordinary passthrough
   (`IsActive=false`), (b) a present-but-invalid/scenario-mismatched session →
   `BlockHold`, and (c) a stale runtime slot detected at startup →
   `BlockHold("stale_runtime_slot")`. I read the code and it looks correct,
   but this is exactly the kind of production wiring that a future refactor
   could silently break without any test failing, since `RuntimePaths.Root`
   is not test-overridable (hardcoded to `<project>/runtime`), which is
   presumably why the test suite avoids exercising `Initialize()` directly.
   Worth a lightweight test (e.g. temporarily pointing at a real-but-scratch
   `runtime`-shaped directory, or making the root injectable) before this
   candidate is considered to have full regression coverage of its own
   startup path.
3. **Minor test-isolation smell, not a correctness bug.**
   `InvalidBatchIdentity_BlocksInHoldWithoutInventingAbortTransition`
   (`RateStudyBatchAEditModeTests.cs:288`) does
   `RateStudySession invalid = fixture.Session;` — a reference alias, not a
   copy — then mutates `invalid.study_id`, silently corrupting the shared
   fixture's session object for the remainder of the test method. No
   assertion after that point depends on `fixture.Controller`'s original
   session, so this does not currently cause a false pass, but it is fragile:
   a future added assertion against `fixture.Controller` later in the same
   test would silently observe the mutated identity. A cheap fix is a JSON
   round-trip copy or a small copy constructor.
4. **Only one identity dimension is exercised by the invalid-identity test.**
   `RateStudySession.Validate()` independently checks batch/tracker identity,
   run/scenario pairing, and hash well-formedness, but the only regression
   test for "invalid identity fails closed into Hold, not a new state"
   mutates `study_id` alone. A wrong `tracker_id` or mismatched
   `run_id`/`scenario_id` pairing takes the same code path but isn't
   independently asserted. Low risk given the shared implementation, but
   cheap to close.

None of these four notes indicate incorrect behavior in the reviewed code —
every code path I traced by hand for the specific gaps above (gimbal/body
gating during Hold, `Initialize()`'s three branches, `Validate()`'s other
identity checks) appears to do the right thing. The notes are about
regression-test coverage against the accepted design's own explicit
requirements, which is why the verdict is `PASS_WITH_NOTES` rather than
`REWORK_REQUIRED`: nothing here contradicts a claim in the evidence document,
and the 36/36 Edit Mode + 1/1 Play Mode + 55/55 Python results are genuine
(independently reproduced, not just read from the summary).

### Explicitly out of scope for this round (per the user's instruction)

Batch B (Python tracker-ready heartbeat, release coordinator, `TrackLoop`
release baseline, `release_provenance.json` chain, v2 sensor-metadata
consumer migration, S1′/statistics tooling, final run summary), the shared
20 Hz follow qualification pilot, and any RATE-002 measurement are not
reviewed here and are not authorized by this verdict.
