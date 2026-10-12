# P1-TRACK-001 — independent verification

Reviewer/role: Claude Sonnet / independent verification

Round: 1

Date: 2026-07-23

Implementation snapshot: candidate `5b37f7b` (full SHA
`5b37f7b613f10f59a06e60968866ecf2c89f1a9e`, confirmed via `git rev-parse`).
`git diff 5b37f7b..773b276 --stat` (the handoff commit) touches only
`docs/current-status.md`, `docs/evidence/P1-TRACK-001-implementation.md`,
`docs/implementation-status.md`, and `docs/unity-test-log.md` — docs only.
Reviewed at `HEAD` (`773b276`), which is code-identical to `5b37f7b`.

Verdict: **PASS_WITH_NOTES**

## Scope

`git diff 78566f3..5b37f7b --stat` (accepted-proposal boundary to this
candidate) touches 18 files, 2211 insertions: four new `controller/` modules
(`track_loop.py`, `trackers.py`, `geolocate.py`, `run_log.py`), small
`runtime=` parameter additions to the existing `body_entry.py`,
`gimbal_entry.py`, `protocol.py`, `tracking_entry.py`, two new `tools/`
scripts (`run_track_experiment.py`, `check_track_env.py`), a new pinned
`tools/requirements-track.txt`, five new test files (622 lines), and a
4-line `runtime/README.md` note. No `Assets/` (C#) file changed. No
implementation code was modified during this review.

## Accepted requirements checked

From `docs/proposals/P1-TRACK-001-first-sot-baseline.md`'s 9 acceptance
criteria and the Round 2 acceptance's 5 binding clarifications (both quoted
in full below where relevant):

1. B0 follow run: fresh Play session, body hold, LOS follow, duration = two
   loops + 60s computed by the run script, sustained nonzero `C_track`.
2. Fresh-session nadir comparison, same scenario/init policy/duration.
3. Tracker compute-latency p95 < 200ms; end-to-end frame age reported
   separately, no threshold.
4. Automated failure-path proof (no publish on forced failure) and frame
   sequencing coverage (backlog-then-latest-only, gap → `ERROR_REINIT_REQUIRED`,
   rollback rejection, exact-init-frame requirement).
5. Unity occlusion observation classified honestly, not gated on outcome.
6. `geolocate` unit coverage: top-left image-y sign, rotated camera, rejection
   paths.
7. Isolated `.venv-track`; automated coverage of adapter, box conversion,
   forced-failure/no-publish, frame gaps, geolocation, log serialization.
8. Boundary audit: tracker process has no Unity-truth read path; does not
   read `target.route_world_m` or scenario config at runtime.
9. `UT-P1-TRACK-001-001` prepared for the user.

Binding clarifications (Round 2 acceptance): (1) `--ground-plane-y-m` required
with no implicit default; (2) the experiment runner alone reads
route/speed, passing only scalar `scenario_id`/`planned_duration_s` to the
tracker; (3) ordinary tracker failure is recoverable `LOST`, only an
unrecoverable gap or frame-ID reset is terminal `ERROR_REINIT_REQUIRED`; (4)
acceptance criteria 1/9 are a bridge/observation check, not a tracking-quality
gate; (5) raw run directories stay local, durable evidence goes in
`docs/evidence/`.

## Files read

- `controller/track_loop.py` (670 lines, full file — the frame-sequencing
  state machine and CLI entry point)
- `controller/trackers.py` (219 lines, full file — plugin protocol, box
  conversion, CSRT adapter, test fake)
- `controller/geolocate.py` (114 lines, full file — box-to-ground-point math)
- `controller/run_log.py` (236 lines, full file — run directory, manifest,
  JSONL, summary, finalize)
- `tools/run_track_experiment.py`, `tools/check_track_env.py`,
  `tools/requirements-track.txt` (full files)
- The diffs to `controller/protocol.py`, `body_entry.py`, `gimbal_entry.py`,
  `tracking_entry.py` (the `runtime=` parameter addition)
- All five test files: `tests/test_trackers.py`, `test_geolocate.py`,
  `test_run_log.py`, `test_track_experiment.py`, `test_track_loop.py`
  (622 lines total)
- `docs/proposals/P1-TRACK-001-first-sot-baseline.md` (both review rounds and
  the binding acceptance clarifications)
- `docs/evidence/P1-TRACK-001-implementation.md`,
  `docs/implementation-status.md`, `docs/unity-test-log.md`'s new
  `UT-P1-TRACK-001-001` section (prepared, not yet run)

## Independent verification performed

I found `.venv-track` still present on disk (git-ignored, left over from
Codex's real run, with genuine `opencv-contrib-python 5.0.0` and `numpy
2.5.1` importable) and used it to re-run the actual test suite myself rather
than trusting the reported pass count:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 28 tests in 0.212s — OK
```

All 28 passed, including the two `@unittest.skipIf(cv2 is None...)`
real-dependency tests, which therefore actually *ran* (not skipped) in my
environment: `test_pinned_opencv_csrt_initializes_and_updates` (real
`cv2.TrackerCSRT` init/update against a synthetic NumPy image) and
`test_cli_runs_pinned_csrt_to_a_versioned_summary` (a real `subprocess.run`
of `python -m controller.track_loop` against synthetic JPEG frame bundles,
producing a real `summary.json`). I also independently re-ran:

```
$ .venv-track/bin/python -m pip check
No broken requirements found.
$ python3 -m py_compile controller/*.py tools/run_track_experiment.py tools/check_track_env.py tests/test_*.py
(clean)
$ git diff --check
(clean)
```

Beyond running the tests, I hand-verified the geometry math in
`test_geolocate.py` rather than trusting the assertions: for
`test_center_bottom_ray_hits_nadir_origin` (camera at `(0,10,0)`, nadir),
I recomputed the ray and ground intersection and confirmed it lands at
exactly `(0,0,0)`; for `test_rotated_camera_basis_is_used` (a 45°-tilted
camera basis), I recomputed the intersection and confirmed
`point_world_m ≈ (0, 0, 10)`; for the top-left-image-y-sign test, I confirmed
by hand that a below-center pixel (larger `v`) must produce a negative
`-up_world`-direction displacement given the formula
`ray = right·(u−cx)/fx + up·(−(v−cy)/fy) + forward`, matching the test's
assertion. I also hand-verified `norm_to_csrt_pixels`'s floor/ceil/epsilon
box conversion against `test_box_conversion_clips_partial_intersections`'s
expected `(20, 20, 61, 41)` output. All matched.

## Review checklist

- [x] **Confidence contract (binding clarification interacting with revision 1).**
  `CsrtTracker.update()` ([trackers.py:165-188](../../controller/trackers.py))
  never reports a calibrated confidence — a successful update always returns
  `confidence=1.0, confidence_source="placeholder"`, and
  `_publication_ready_result()`
  ([track_loop.py:441-462](../../controller/track_loop.py)) additionally
  rejects any plugin result whose `confidence_source` isn't `"tracker"` or
  `"placeholder"`. `tests/test_trackers.py::test_csrt_adapter_uses_placeholder_not_tracker_confidence`
  asserts this directly, and I reran it against the real installed CSRT
  binding.
- [x] **Failure-path vs. occlusion separation.** An automated
  `RecordingTracker`/`ScriptedTracker`-driven forced-failure test
  (`test_forced_failure_writes_neither_slot_then_can_recover`) proves
  byte-for-byte that neither `tracking_observation.json` nor
  `gimbal_command.json` changes during a `LOST` period, and that a later
  successful update both republishes and marks `recovered_from_lost=true`.
  The real Unity Cube-occlusion classification is correctly left to the
  prepared `UT-P1-TRACK-001-001` case, whose required-observations table
  states "Any classification passes if recorded honestly" — matching binding
  clarification 4.
- [x] **Frame sequencing and backlog.** `TrackLoop.process_available()`
  ([track_loop.py:248-322](../../controller/track_loop.py)) loads every
  retained intermediate frame and feeds it to the tracker in order
  (maintaining internal tracker state), but publishes only the last one
  (confirmed both by reading the code and by
  `test_backlog_updates_every_frame_and_publishes_only_latest`, which checks
  `tracker.update_frame_ids == [1, 2, 3]` while only frame 3 is published). A
  retained-but-missing intermediate frame aborts the whole batch with
  `ERROR_REINIT_REQUIRED` and `event="GAP"` *before* touching the tracker
  (`tracker.update_frame_ids == []` in
  `test_missing_retained_intermediate_frame_requires_reinit`), matching "不做
  无解释跳跃." A `frame_id` below `last_frame_id` is rejected the same way
  with `reason="frame_id_reset_or_rollback"`
  (`test_frame_id_rollback_requires_reinit`). An exact `--init-frame` that
  isn't retained raises `FileNotFoundError` directly
  (`test_initialization_requires_exact_retained_bundle`) — see Non-blocking
  note 2 on how this specific failure surfaces at the CLI level.
- [x] **LOS geometry and calibration.** `box_ground_intersection()`
  ([geolocate.py:57-114](../../controller/geolocate.py)) implements the
  proposal's exact formula (bottom-center pixel, camera-basis ray, ground
  plane intersection, upper-bound distance), verified by hand as described
  above. `ground_plane_y_m` has no default anywhere in the call chain: not in
  `TrackLoop.__init__` ([track_loop.py:162](../../controller/track_loop.py)),
  not in `build_argument_parser()`
  ([track_loop.py:604](../../controller/track_loop.py)) — confirmed by
  `test_cli_has_no_implicit_ground_plane_default`, which invokes the real
  `main()` and asserts `SystemExit(2)` with `--ground-plane-y-m` named in the
  error text; I reran this test myself.
- [x] **Truth-isolation boundary (acceptance criterion 8 / binding
  clarification 2).** `track_loop.py` has no import of `ScenarioConfig`, no
  read of `config/scenario.default.json` or `runtime/scenario_config.json`
  anywhere — confirmed by reading the full file. `tools/run_track_experiment.py`
  reads the scenario file only to extract `scenario_id` (a string) and to
  compute `planned_duration_s` via `two_loop_duration_s()`
  ([run_track_experiment.py:33-61](../../tools/run_track_experiment.py)),
  which consumes `route_world_m`/`speed_mps` locally and returns only a float;
  `tracker_command()`
  ([run_track_experiment.py:64-100](../../tools/run_track_experiment.py))
  builds the subprocess argv from named scalars only. I reran
  `test_tracker_command_receives_only_scalar_orchestration_values`, which
  asserts `"route_world_m"` and `"speed_mps"` do not appear anywhere in the
  joined command string — a real regression guard against this boundary
  being silently broken later, not just a one-time manual check.
- [x] **Dependency isolation.** `tools/requirements-track.txt` pins
  `opencv-contrib-python==5.0.0.93` and `numpy==2.5.1` in a comment-documented
  separate `.venv-track`; `create_csrt_backend()`
  ([trackers.py:123-134](../../controller/trackers.py)) tries the OpenCV 5
  root constructor first, falls back to `.legacy`, and is reused verbatim by
  `tools/check_track_env.py`'s smoke check rather than a re-implementation
  that could drift. I independently confirmed `.venv-track` has real,
  importable `cv2 5.0.0`/`numpy 2.5.1`, and `pip check` reports no broken
  requirements.
- [x] **Unity boundary discipline.** `runtime/README.md` and
  `docs/unity-test-log.md`'s new `UT-P1-TRACK-001-001` section correctly
  describe this as `PREPARED_NOT_RUN` with every result field blank
  (`Overall verdict: PENDING`) — the implementer evidence document is honest
  that "No real Unity follow/nadir baseline has been run on this candidate
  yet," and the gate board correctly separates this from the code-review gate
  I am recording here.

## Findings

### Blocking

None found.

### Non-blocking

1. **`CsrtTracker.init()` is not exception-safe the way `update()` is.**
   [trackers.py:154-163](../../controller/trackers.py) calls
   `tracker.init(image, box_pixels)` with no `try`/`except`, unlike
   `update()`
   ([trackers.py:165-176](../../controller/trackers.py)), which explicitly
   catches `Exception` from the real OpenCV call and converts it to a
   `TrackerResult.lost(...)`. If the real CSRT binding raised instead of
   returning a falsy value on a pathological init box, the exception would
   propagate uncaught through `TrackLoop.initialize()` into `run_tracker()`'s
   `try` block, which only catches `KeyboardInterrupt`
   ([track_loop.py:545-556](../../controller/track_loop.py)), crashing the
   process with a raw traceback rather than a handled `RuntimeError` like the
   adjacent `if not initialized: raise RuntimeError(...)` path one line
   later. Low practical risk (init happens once, under human supervision,
   after the CLI's own box/finite validation), but it is an avoidable
   asymmetry with the rest of the file's defensive style.
2. **Inconsistent error-reporting polish between failure points.**
   A missing intermediate frame or a `frame_id` rollback *during* a run
   produces a clean logged `ERROR_REINIT_REQUIRED` record, a finalized
   `summary.json`, and (via `run_tracker()`) a JSON status line with
   `exit_code=2`. An exact `--init-frame` that isn't retained instead raises
   `FileNotFoundError` straight out of `TrackLoop.initialize()`
   ([track_loop.py:211-214](../../controller/track_loop.py)), which is not
   caught anywhere in `run_tracker()`'s `try`, so it surfaces as an uncaught
   Python traceback (the `finally` block still runs and produces an
   effectively-empty `summary.json`, but the process's own exit code and
   stdout are whatever an unhandled exception produces, not the structured
   `{"run_id":..., "state":...}` line used elsewhere). The proposal only
   requires "明确报错" (a clear error), which this technically satisfies —
   the message names the exact problem — but it is worth deciding whether
   this specific failure should get the same structured handling as the
   other terminal paths for operator consistency.
3. **`gimbal_entry.look_at(x, z, y, ...)`'s parameter order is a latent
   readability risk, inherited from before this candidate.** This function's
   own positional order is `(x, z, y)`, not `(x, y, z)`
   ([gimbal_entry.py:12-18](../../controller/gimbal_entry.py)) — pre-existing
   M0 code, not changed here. `RuntimePublisher.look_at()`
   ([track_loop.py:142-149](../../controller/track_loop.py)) correctly
   threads `point_world_m`'s `(x, y, z)` into that ordering
   (`point_world_m[0], point_world_m[2], point_world_m[1]`), which I verified
   by hand — this candidate does not have a bug here. But this is the first
   caller besides the CLI's own `main()` to have to reason about the
   unusual ordering, and nothing in the type system would catch a future
   caller swapping the second and third arguments (both are plain `float`).
   Worth a rename or keyword-only call at the source sometime, not blocking
   this gate.
4. **The nadir/hold "stays put after one command" behavior is Unity C# code
   that remains outside this and the prior review's file list.** Both
   `condition="nadir"` and the LOST-period "no new command" behavior rely on
   `GimbalCommandReceiver.cs`/`TetheredGimbal.cs` (and `BodyCommandReceiver.cs`
   for hold) continuing to honor the last valid command after
   `expires_after_s` elapses rather than reverting to some other default.
   The accepted proposal itself names this as relying on "既有 C# 行为"
   (existing C# behavior). I did not independently re-read
   `GimbalCommandReceiver.cs`/`TetheredGimbal.cs` for this round either (it
   was flagged as an out-of-scope gap in my `P1-M0-001` Round 1 review too).
   This will be empirically exercised by `UT-P1-TRACK-001-001`'s "Nadir"
   required-observation row, so it is not going unverified — just not
   verified by code reading, and I want that distinction on the record
   rather than implied.
5. **Minor test-coverage completeness note.** `norm_to_csrt_pixels`'s
   `-1e-9` epsilon subtraction (guarding against float round-up exactly at
   an integer box edge)
   ([trackers.py:79-91](../../controller/trackers.py)) isn't exercised by a
   test case where the epsilon actually changes the result — the existing
   tests all use inputs where `ceil()` would land the same either way. I
   confirmed the epsilon logic is correct by hand, so this is a coverage
   nicety, not a doubt about correctness.

## Missing or weak tests

None at the "no automated coverage exists" level this round — this is a
marked contrast with `P1-M0-001`'s C# side: every acceptance criterion that
can be tested without a live Unity session has a real, independently
re-run, passing test, including two genuine integration tests (real CSRT,
real subprocess CLI) that I personally executed rather than took on faith.
The only outstanding verification is the Unity-side empirical run itself
(`UT-P1-TRACK-001-001`, `PREPARED_NOT_RUN`), which is a distinct gate from
this code review by design, not a gap in this candidate's automated
coverage. Non-blocking note 1 above ("`CsrtTracker.init()` is not
exception-safe") is the one place a small additional test (an init-time
exception from a stub backend) would have caught a real, if narrow, gap.

## Requirement-to-evidence mapping

| Requirement | Evidence | Verdict |
|---|---|---|
| CSRT reports no invented confidence | `trackers.py:165-188`; `test_csrt_adapter_uses_placeholder_not_tracker_confidence` (rerun, pass) | Met |
| Forced failure publishes nothing; ordinary failure is recoverable `LOST` | `track_loop.py:441-462`, `:324-354`; `test_forced_failure_writes_neither_slot_then_can_recover` (rerun, pass, byte-identical file check) | Met |
| Backlog fed sequentially, only latest published | `track_loop.py:248-322`; `test_backlog_updates_every_frame_and_publishes_only_latest` (rerun, pass) | Met |
| Unrecoverable gap / rollback → terminal `ERROR_REINIT_REQUIRED` | `track_loop.py:258-279`, `:406-438`; `test_missing_retained_intermediate_frame_requires_reinit`, `test_frame_id_rollback_requires_reinit` (rerun, pass) | Met |
| LOS geometry formula and rejection paths | `geolocate.py:57-114`; `test_geolocate.py` (rerun, pass; math independently re-derived by hand for 3 of 4 tests) | Met |
| `--ground-plane-y-m` required, no default | `track_loop.py:162,604`; `test_cli_has_no_implicit_ground_plane_default` (rerun, pass) | Met |
| Experiment runner isolates route/speed from the tracker process | `run_track_experiment.py:33-100`; `test_tracker_command_receives_only_scalar_orchestration_values` (rerun, pass) | Met |
| Isolated dependency, pinned and smoke-checked | `tools/requirements-track.txt`; `.venv-track` confirmed present and working; `pip check` clean (rerun) | Met |
| Run schema frozen, truncation-tolerant, latency split | `run_log.py` (full file); `test_run_log.py` (rerun, pass) | Met |
| `UT-P1-TRACK-001-001` prepared | `docs/unity-test-log.md` new section, `PREPARED_NOT_RUN`, all result fields blank | Prepared, not yet run — separate gate |

## Requested Codex action

None blocking. Consider before or alongside a future `P1-TRACK-001` round or
`P1-M2-RATE-001`: wrap `CsrtTracker.init()`'s backend call in the same
exception handling `update()` already has (note 1); decide whether the
missing-init-frame path should get the same structured exit-code/JSON
handling as the mid-run terminal paths (note 2); consider a keyword-only or
renamed `gimbal_entry.look_at` signature to remove the `(x, z, y)` ordering
trap (note 3, pre-existing). Note 4 is a reminder, not an action item, unless
`UT-P1-TRACK-001-001`'s nadir/hold observations come back unexpected.

Codex may proceed to schedule the real `UT-P1-TRACK-001-001` Unity run; this
code-review gate does not block that. The work item cannot be recorded
`DONE` until that Unity evidence is captured and reviewed against the
required-observations table, per the standard three-gate rule.

## Re-review result

Not started. Required only if Unity evidence surfaces a behavior
inconsistent with the code reviewed here, or if a future round changes
`track_loop.py`, `trackers.py`, `geolocate.py`, or `run_log.py`.
