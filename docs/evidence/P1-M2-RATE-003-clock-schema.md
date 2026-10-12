# P1-M2-RATE-003 batch 1 — shared-clock rate3 protocol: implementation evidence

Date: 2026-07-30
Work ID: `P1-M2-RATE-003` (batch 1 of the suggested implementation scope:
single clock contract + v2/v3 version routing + regressions)
Role: implementation (Cursor pool)
Design basis: `docs/proposals/P1-M2-RATE-003-difficulty-paired-rate-study.md`
revision 3 (acceptance round 3 `ACCEPTED`, BC-R3-1/BC-R3-2), design v0.3.9.

This batch changes time semantics and is a mandatory review stop point. It
contains **no** scouting/calibration/probe/formal session, no D2 config, no
slot orchestration, no probe, no decision function — those are batch 2.

## Scope implemented (proposal §1, §1.1, §1.2, §2)

- P1: RATE-session frames now write `tethered-sensor-frame/v3` +
  `HostMonotonicSeconds()` + `capture_monotonic_clock_id` when the installed
  session is `p1-rate3-session/v1`; RATE-002 v2 sessions keep byte-identical
  v2 frames (`SensorFrameWriter.cs:183-185`).
- P3: the release ack monotonic source for rate3 sessions is the same
  `HostMonotonicSeconds()` sampled in the same `Update` as command processing
  (`RateStudyExperimentController.cs:149-154`); ack schema
  `p1-rate3-release-ack/v1` carries `release_clock_id`
  (`RateStudyProtocol.cs:214-222`).
- P4: `p1-rate3-tracker-ready/v1` carries `publisher_clock_id`
  (`Rate3TrackerLifecycle.publish_ready`, `controller/rate3_protocol.py:484`).
- P5: `ReanchorRuntime` binds its in-process monotonic source by (i)
  constructor declaration (non-default injection must explicitly declare
  `monotonic_clock_id="system-stopwatch/v1"`, else `ValueError`), (ii) the
  pre-existing per-frame `validate_system_monotonic_frame` before any
  subtraction, (iii) `monotonic_clock_id` written into the run manifest via
  `manifest_identity()` (`controller/reanchor_runtime.py:38-51,444-450`).
- C1 (`Rate3TrackerLifecycle.frame_phase`/`record_fields`): both sides'
  clock IDs are validated before the capture-vs-release comparison;
  mismatch raises `INVALID_CLOCK_IDENTITY`
  (`controller/rate3_protocol.py:519-578`).
- C2 (`controller/run_log.py:315-322`): `build_summary(release_clock_id=…)`
  rejects any measurement record whose `capture_monotonic_clock_id` differs
  from the release clock; `finalize_run` routes `manifest["rate3"]` to the
  rate3 provenance validator and passes the clock ID through
  (`run_log.py:418-489`).
- C3: unchanged mechanism (per-frame `validate_system_monotonic_frame`
  inside `ReanchorRuntime.after_frame`); now also terminates the run
  fail-closed under rate3 (below).
- C4 (`RateStudyExperimentController.ValidReadyRate3Error`, lines 400-420):
  `publisher_clock_id == system-stopwatch/v1`, finite non-negative
  `publisher_monotonic_s`, `0 < heartbeat_interval_s ≤ 1.0`, and
  `0 ≤ now − publisher_monotonic_s ≤ 2 × heartbeat_interval_s` (i.e. [0, 2.0]
  s, future rejected) with `now` sampled in the same `Update`; failure →
  rejection `invalid_ready_clock_identity`, state stays HOLD. v3 release
  commands must carry `release_clock_id` before the RELEASED transition
  (`invalid_release_clock_id`, lines 217-223).
- §1.1(a) startup ordering: the rate3 session is loaded/validated before
  `create_tracker`, run-ID creation and `RunLogger`; the init frame's schema
  and `capture_monotonic_clock_id` are validated by `FrameRepository.load`
  before model construction (`controller/track_loop.py:893-913`).
- §1.1(b) runtime layering: under a rate3 lifecycle, a clock/schema failure
  at frame load, `_protocol_fields`, or `ReanchorRuntime.after_frame`
  terminates the run with event `INVALID_CLOCK` — the bad frame produces no
  observation/control/re-anchor/record side effect, previously processed
  frames keep theirs, and the run finalizes fail-closed with exit code 2
  (`controller/track_loop.py:389-402,425-471`).
- §1.2 clock-smoke identity: `P1-M2-RATE-003-CLOCKSMOKE` /
  `rs3-clock-smoke`, mutually exclusive with the `P1-M2-RATE-003-B1`
  research ID space in both validators and the tooling
  (`controller/rate3_protocol.py:76-97`, `tools/run_rate3_clock_smoke.py`);
  smoke artifacts archive under
  `runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/`, no attempt limit, and
  `verify_run` computes no `C_track`/`C_geom`.
- §2 routing: archived v2 stays frozen — `controller/rate2_protocol.py` is
  untouched; `tools/run_rate2_study.py` now pins `SENSOR_FRAME_SCHEMA_V2`
  explicitly. The active path routes on the session file's declared
  schema/study: `track_loop --rate3-session` takes
  `expected_frame_schema` from `session["sensor_frame_schema"]`
  (`track_loop.py:901-913`). `track_loop.py:795`'s RATE-002/re-anchor
  exclusion is unchanged; it is genuinely lifted for rate3 because the
  shared clock is pinned end-to-end, guarded by an explicit
  `reanchor.monotonic_clock_id == session["capture_monotonic_clock_id"]`
  check (`track_loop.py:969-986`).
- Completion gate: rate3 runs complete only when both release-origin
  simulation duration and shared-host monotonic wall duration reach
  `planned_duration_s` (`requires_wall_completion`;
  `track_loop.py:274-288`), per §10.
- Frozen values: `planned_duration_s = 150.0` for `P1-M2-RATE-003-B1`
  sessions (BC-R3-1); the non-measurement clock-smoke session uses 30.0 s
  (operational value, RATE-002 30 s pilot precedent; smoke produces no
  measurement data).

## Schema inventory (new, all `/v1`)

`p1-rate3-session/v1` (adds `planned_duration_s`, `sensor_frame_schema`,
`capture_monotonic_clock_id`), `p1-rate3-tracker-ready/v1` (adds
`publisher_clock_id`), `p1-rate3-release-command/v1` (adds
`release_clock_id`), `p1-rate3-release-ack/v1` (adds `release_clock_id`),
`p1-rate3-abort-command/v1`, `p1-rate3-release-provenance/v1` (adds
`release_clock_id`), `p1-rate3-coordinator-failure/v1`. RATE-002's
`p1-rate2-*` schemas and v2 serialized bytes are unchanged (asserted by
tests).

## Review round 1 follow-up: finding 1 closed (commit `57f2561`)

Independent review round 1 returned `PASS_WITH_NOTES`
(`docs/reviews/P1-M2-RATE-003.md`). Finding 1 — CLI
`--planned-duration-s` was not cross-checked against the session's frozen
`planned_duration_s`, letting a manifest carry two contradictory values —
is now closed ahead of batch 2: `run_tracker`'s rate3 startup path rejects
any CLI value differing from `session["planned_duration_s"]` (tolerance
1e-9) before model construction and before any run side effect
(`controller/track_loop.py`, rate3 branch immediately after
`load_rate3_session`). Regression
`test_cli_planned_duration_must_match_frozen_session_value` proves a 60.0 s
CLI value against the frozen 30.0 s clock-smoke session raises before
`create_tracker` and creates no run directory. Findings 2 (cosmetic
freshness-window expression) and 3 (harmless constructor asymmetry)
required no change per the review. Verification rerun after the fix:
`.venv-track` full suite **200 passed** (199 + 1 new), `.venv-yoloe`
reanchor/scouting **54 passed**; no Unity-affecting change, Edit/Play
results from `feaf475` remain valid. This fix is a review-requested note
closure and is subject to the next review round's verification.

## Verification actually run (this machine, this tree)

- `.venv-track/bin/python -m pytest tests/ -q` → **199 passed, 41 subtests
  passed** (baseline at HEAD `ba06ef2` is 163 = 151 from the A5 batch + 12
  COORD-002 infrastructure tests; this batch adds 36 in
  `tests/test_rate3_protocol.py`).
- `.venv-yoloe/bin/python -m pytest tests/test_reanchor.py
  tests/test_detector_scouting.py tests/test_scene004_scouting.py -q` →
  **54 passed, 18 subtests passed** (18+14+22, unchanged).
- Archived-artifact regression (proposal §2(a)) ran unskipped against the
  real RATE-002 archive: `validate_decision_a(runtime/)` passes and
  reproduces R1′ = 0.2496313750743866 and R2′ = 0.8475073313782991;
  `attempt_row` recomputation of the three `rs2-r20-follow-*` runs matches
  `decision_a.json` value-for-value. Cross-feed (§2(c)) is covered both
  directions by unit tests (v2 artifacts through rate3 validators and vice
  versa fail closed; `FrameRepository` rejects the other generation's
  frames).
- Unity Edit Mode: `/Applications/Unity/Hub/Editor/6000.4.10f1/... -batchmode
  -nographics -runTests -testPlatform EditMode -testFilter
  TetheredTracking.Tests` → **150/150 passed, 0 failed**
  (`runtime/test-results/p1-rate3-clock-editmode.xml`), including the new 35
  `RateStudyRate3EditModeTests` and the unchanged 115 prior tests.
- Unity Play Mode (same binary, `PlayMode`) → **3/3 passed**
  (`runtime/test-results/p1-rate3-clock-playmode.xml`).
- Unity version note: `ProjectVersion.txt` pins 6000.4.1f1, but that editor
  cannot compile/run this repo headlessly (pre-existing condition, same as
  documented in `docs/evidence/P1-DETECT-001-release-boundary-repair.md`);
  all Unity evidence above used the installed 6000.4.10f1, consistent with
  recent batches.
- `python3 tools/check_docs.py` → pass. `python3
  tools/check_role_writes.py --role implementation` reports exactly two
  out-of-scope paths — `docs/phase1-single-drone-design.md` and
  `docs/proposals/P1-M2-RATE-003-difficulty-paired-rate-study.md` — which
  are the **acceptance round-3 batch's** uncommitted edits (design v0.3.9,
  round-3 decision), not this batch's writes; they are left uncommitted for
  the acceptance role's stop-point audit/attribution and are excluded from
  the candidate commit.

## Environment repair (no dependency additions beyond requirements)

`.venv-track` was incomplete; `tools/requirements-track.txt`
(opencv-contrib-python==5.0.0.93) and pytest were installed per repo
convention. `.venv-yoloe` received pytest via `uv pip install`. No new
runtime dependencies.

## Not verified / known limits

- No real `rs3-clock-smoke` Unity session has run; the end-to-end
  clock-smoke (prepare → launch → release → verify → archive) is the
  focused Unity gate after independent review. Python-side coverage of the
  tooling is synthetic-fixture only.
- `SensorFrameWriter`'s rate3 branch selection depends on the render path
  and is not unit-testable in Edit Mode; it is covered by the clock-smoke
  gate (noted in the test file).
- D2 scenario mapping (`p1-scene-004-d2`) is validated structurally; the
  actual D2 config file is batch 2.
- The `planned_duration_s = 30.0` clock-smoke value is an operational
  choice, not a measurement parameter; flagged for review.

## Review scope (for the independent reviewer)

Candidate diff vs prior passed candidate `f1868dd` (implementation files
only; the two acceptance-owned docs above and `docs/current-status.md`
coordination entries are not part of the implementation batch):

- `controller/rate3_protocol.py` (new, 578 lines)
- `controller/track_loop.py` (rate3 routing, INVALID_CLOCK layering,
  completion gate, CLI)
- `controller/run_log.py` (C2 check, rate3 finalize routing)
- `controller/reanchor_runtime.py` (P5 binding)
- `tools/run_rate2_study.py` (explicit v2 pin; 2 lines)
- `tools/run_rate3_clock_smoke.py` (new)
- `Assets/TetheredTracking/Scripts/{SensorFrameWriter,RateStudyProtocol,
  RateStudyExperimentController}.cs`
- `Assets/TetheredTracking/Tests/EditMode/RateStudyRate3EditModeTests.cs`
  (new, 35 tests)
- `tests/test_rate3_protocol.py` (new, 36 tests),
  `tests/test_reanchor.py` (2 lines: explicit clock declaration)

Key contract points to re-verify: P1–P5 producer clocks, C1–C4 comparison
points, §1.1(a)/(b) ordering, clock-smoke/research mutual exclusion, v2/v3
cross-feed fail-closure, archived RATE-002 recomputation, and that every
v2-path byte and behavior is unchanged.

## Unity case (after review passes)

`rs3-clock-smoke` focused gate, all via
`tools/run_rate3_clock_smoke.py`: `prepare-session` (binds the reviewed
init frame), user enters Play with the SCENE-004 carrier, tracker launched
with `--rate3-session --reanchor-config`, warm-up ≥ 20 frames/seq, then
`release --confirmed`, run to 30.0 s, `verify` (provenance + per-frame
clock identity/monotonicity), `archive`. The smoke writes no measurement
identity and feeds no disposition.
