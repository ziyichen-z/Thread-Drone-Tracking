# P1-DETECT-001 — independent verification

Reviewer/role: Claude Sonnet / independent verification  
Round: 1  
Date: 2026-07-28
Implementation snapshot: candidate `f2555d5`, range `15bff60..f2555d5`  
Verdict: **REWORK_REQUIRED**

## Round 1 handoff

Status: `AWAITING_INDEPENDENT_REVIEW`

This subsection is a Codex handoff, not an independent verdict. Review the
actual accepted proposal/formal design and implementation, keeping runtime
implementation files read-only. Record the independent verdict and findings
below, then return any fixes to Codex.

Focused scope:

1. Strict YOLOE and DINOv2 source/weight/license identity, local-only loading,
   official preprocessing and normalized 384-d output.
2. Deterministic class/appearance/world-LOS gates, tie/margin/K semantics,
   acknowledged-release anchor and permitted anchor refreshes.
3. Deeply immutable six-second history, exact detection-source NanoTrack
   initialization, ordered replay, four discard paths, catch-up convergence
   and atomic consumed-frame replacement.
4. Zero-queue single-flight worker, timeout/live-thread shutdown, one confirmed
   death restart, independent worker/reseed failure counters, cadence
   numerator/denominator and fail-closed terminal paths.
5. Track-loop integration, LOST scanning, manifest identity, main-thread
   event persistence, `record_kind=event` metric isolation, and the no-Unity-
   truth boundary.
6. Focused/full tests and the model/package/synthetic timing evidence in
   `docs/evidence/P1-DETECT-001-implementation.md`.

Do not run scouting, Unity qualification, anchor relocation, a successor
campaign, or any implementation that depends on this verdict.

## Accepted requirements checked

Against the accepted base revision 3 + Amendment A1 revision 2
(`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md`) and the six
Round 2 binding clarifications:

1. Strict YOLOE/DINOv2 source/weight/license identity, local-only loading,
   official bicubic preprocessing, normalized 384-d output — **verified**.
2. Deterministic class/appearance/world-LOS gates, tie-break/margin/K
   semantics, acknowledged-release anchor and refresh rules — **verified**,
   with one concurrency caveat (see Blocking).
3. Immutable six-second history, exact-source NanoTrack init, ordered
   replay, four discard paths, catch-up, atomic replacement (binding 1) —
   **verified**.
4. Zero-queue single-flight worker, timeout/live-thread semantics, one
   confirmed-death restart, independent worker/reseed counters, cadence
   numerator/denominator (bindings 2, 6) — **verified for the worker's own
   bookkeeping**, but the `reseed_failures` counter itself is exposed to the
   same race as finding B1 below.
5. Track-loop integration, LOST scanning, manifest identity, main-thread
   event persistence, `record_kind=event` denominator isolation, no-Unity-
   truth boundary — **verified**.
6. Focused/full tests and model/package/synthetic timing evidence in
   `docs/evidence/P1-DETECT-001-implementation.md` — **independently
   rerun and reproduced** (see below).

## Files and tests read

Read in full, not by summary: `controller/reanchor.py`,
`controller/reanchor_models.py`, `controller/reanchor_runtime.py`, the
`controller/track_loop.py` and `controller/run_log.py` diffs (and
surrounding unchanged code for context), `controller/trackers.py`,
`controller/geolocate.py` (for the pre-existing camera-basis convention),
`controller/rate2_protocol.py` (`frame_phase`/`record_fields`),
`config/detector-reanchor.models.json`, `tools/fetch_dinov2.py`,
`tools/benchmark_reanchor.py`, `tests/test_reanchor.py`,
`tests/test_run_log.py`, `tests/test_track_loop.py` (to confirm what is
*not* covered), the accepted proposal/amendment and its two prior Codex
rounds, and the `docs/phase1-single-drone-design.md` v0.3.3 diff.

Independently reproduced rather than trusted from the evidence doc:

- `.venv-track/bin/python -m unittest discover -s tests -v` → **89/89
  pass** (matches the claim).
- `UV_CACHE_DIR=... uv pip check --python .venv-yoloe/bin/python` →
  **42 packages, all compatible** (matches the claim).
- Independently hashed the four on-disk artifacts (`sha256`/`shasum`) named
  in `config/detector-reanchor.models.json` and
  `docs/evidence/P1-DETECT-001-implementation.md`: DINOv2 source archive
  (`c27dcda...aed4b`), extracted `LICENSE` (`600cc67...935b7`), DINOv2
  weights (`b938bf1...f60cd9`), YOLOE weights (`8e43944...4dce3e3`) — **all
  match exactly**. Also independently hashed
  `config/detector-reanchor.models.json` itself against the evidence doc's
  claimed `593734d...706d2` — **matches**.
- Ran a real (non-synthetic-benchmark) smoke of the actual runtime classes
  — `DinoV2Embedder.embed()` on a random RGB image and `YoloeProposer`
  init/propose — via `.venv-yoloe`. Produced a finite 384-d vector with
  measured norm `0.9999999588748264` (unit-normalized) and a working
  YOLOE `propose()` call. This independently confirms the model-loading
  and preprocessing pipeline actually runs, not just that it was claimed
  to run.
- Confirmed `runtime/models/resnet18-f37072fd.pth` remains on disk,
  untouched, and is never referenced by any import path in
  `controller/reanchor_models.py`; `.gitignore`'s `/runtime/*` keeps every
  model artifact out of git (`git status --ignored` shows `runtime/yoloe/`
  and `.venv-yoloe/` as ignored).
- Confirmed `camera_right_world`/`camera_up_world`/`camera_forward_world`/
  `camera_rotation_xyzw`/`intrinsics_px` are pre-existing fields already
  published by `Assets/TetheredTracking/Scripts/SensorFrameWriter.cs` and
  already consumed by the pre-DETECT-001 `controller/geolocate.py` — the
  new `world_los()` reprojection is not inventing new sensor fields, and
  its ray formula (`right*(u-cx)/fx - up*(v-cy)/fy + forward`) is
  byte-for-byte the same convention already used by
  `box_ground_intersection`, just evaluated at the box center instead of
  the box bottom-center (correct per design §3: "候选框中心像素"). The
  quaternion-rotation self-consistency check in `validate_camera_basis`
  implements the standard optimized quaternion-rotation formula correctly
  (hand-verified the cross-product algebra).
- Confirmed `frame_phase`/`record_fields` in `controller/rate2_protocol.py`
  (used to compute the `released` flag threaded into
  `reanchor_runtime.after_frame`) reads only frame metadata
  (`capture_monotonic_s`) and the already-accepted release-ack's
  `release_monotonic_s` — no Unity truth read anywhere on the re-anchor
  path.

## Findings

### Blocking

**B1. Unsynchronized concurrent mutation of `ReanchorRuntime`/`TripleGateState` shared state between the worker thread and the main thread (thread-safety / atomicity defect).**

`ReanchorRuntime._lock` protects `self.history`, `self._pending`/
`self._pending_fields`, and `self._events` consistently from both threads.
It does **not** protect `self.gate` (a `TripleGateState` instance) or
`self.reseed_failures` on the worker-thread side, even though both are
mutated from two different threads:

- Worker thread (inside the `round_work` closure submitted via
  `self.worker.submit(round_work)` in `after_frame`,
  [reanchor_runtime.py:174-227](controller/reanchor_runtime.py:174)):
  reads `self.gate.anchor.los_world`
  ([reanchor_runtime.py:178,181](controller/reanchor_runtime.py:178)) and
  calls `self.gate.evaluate(...)`
  ([reanchor_runtime.py:201-207](controller/reanchor_runtime.py:201)) —
  **neither is wrapped in `with self._lock:`**. `_catch_up`, also called
  from the worker thread inside `round_work`, increments
  `self.reseed_failures` at three sites
  ([reanchor_runtime.py:241,260,265](controller/reanchor_runtime.py:241))
  — **also outside any lock** (only its `self.history.snapshot()`/
  `head_frame_id` reads at lines 237 and 262 are locked).
- Main thread (`before_update`,
  [reanchor_runtime.py:64-126](controller/reanchor_runtime.py:64)): calls
  `self.gate.reseed_succeeded(...)` and mutates
  `self.reseed_failures` — **inside** `with self._lock:`
  ([reanchor_runtime.py:70,89,93,102,113,115,116](controller/reanchor_runtime.py:70)).

`TripleGateState.evaluate()`
([controller/reanchor.py:488-553](controller/reanchor.py:488)) and
`reseed_succeeded()`
([controller/reanchor.py:555-560](controller/reanchor.py:555)) both
read-modify-write the same instance fields:
`self.anchor`, `self._disagree_count`, `self._previous_winner`,
`self._previous_capture_s`, `self._round_index`, `self._last_reseed_round`.
Because the worker-thread side never acquires `ReanchorRuntime._lock`, the
lock on the main-thread side provides no actual mutual exclusion — this is
a real, unguarded data race, not merely a theoretical one made safe by
holding a lock on only one side.

**This window is not a rare edge case given the measured latencies.** The
implementation's own synthetic benchmark
(`docs/evidence/P1-DETECT-001-implementation.md`) reports a complete
worker round at ~95 ms (detector 74.075 ms + appearance gate 20.994 ms),
which spans roughly two main-loop frames at 20 Hz (50 ms/frame). Tracing
the exact call order inside `TrackLoop.process_available`'s per-bundle
loop
([controller/track_loop.py:327-358](controller/track_loop.py:327)):
`before_update` runs before `after_frame`/`poll` on every single frame,
so it is entirely possible — and, given the ~95 ms round duration versus
50 ms frame period, likely under sustained 20 Hz operation once reseeds
start recurring — for round *N*'s `round_work()` to still be executing on
the worker thread (inside `evaluate()`/`_catch_up()`) at the exact moment
`before_update()` on the main thread is consuming a **different**,
already-completed round *N-1*'s pending swap via `reseed_succeeded()`.
This is precisely the scenario the carrier exists to handle (recurring
re-anchor rounds while breaking a background lock), so the race is not
confined to a corner case outside the design's own motivating scenario.

**Consequence:** a race here can corrupt exactly the bookkeeping that
Round 2 binding clarifications rely on for anti-oscillation safety —
`_round_index`/`_last_reseed_round` (the `n_min=2` minimum-reseed-interval
guard against oscillation, §5 "最小重播种间隔") and `_disagree_count`/
`_previous_winner` (the `K=2` hysteresis guard). A lost or torn update
here could let a reseed fire before `n_min` rounds have elapsed, or drop
part of the K-round consistency streak — silently, with no exception and
no failed test, since CPython's GIL prevents a crash but does not make
multi-statement read-modify-write sequences atomic across threads. The
separate `self.reseed_failures` race can similarly under-count failures,
weakening the `consecutive_failure_limit=3` fail-closed guarantee
(binding 6).

This is squarely inside the review's mandatory scope ("并发/原子性" per
`docs/collaboration-workflow.md` §4.4) and undermines an explicit binding
intent, not just a hypothetical robustness nice-to-have. The fix is
narrow: wrap the `self.gate.anchor`/`self.gate.evaluate(...)` access in
`round_work` and the three `self.reseed_failures += 1` sites in
`_catch_up` in `self._lock`, matching the discipline already used
everywhere else in this file.

### Non-blocking

**N1. `TrackLoop`-level integration of the re-anchor carrier has zero
automated test coverage.** `tests/test_track_loop.py` was not touched by
this candidate (confirmed via `git diff --stat 15bff60..f2555d5` and by
`grep -c reanchor tests/test_track_loop.py` → 0 matches). All 12 new
`test_reanchor.py` tests exercise `TripleGateState`/`FrameHistory`/
`SingleFlightWorker`/`ReanchorRuntime` in isolation or via hand-constructed
`ReanchorRuntime` fixtures; none constructs a `TrackLoop` with
`reanchor_runtime` set and drives it through `initialize()`/
`process_available()`. That is exactly the site of the `before_update` →
`tracker.update()` → `after_frame()` → `poll()` sequencing that binding 1
("原子交换检查同一临界区") depends on, and where `_drain_reanchor_events`
and the `fatal_reason` → `_record_terminal_error` → `terminal=True`
shutdown path live. I hand-traced this sequencing and found it correct
(see below), but it is currently unverified by any automated test — a
future refactor of `track_loop.py` could silently break the ordering with
no red test to catch it.

**N2. The event log cannot distinguish a LOST-triggered immediate reseed
from a normal K-hysteresis DISAGREE reseed.** Design §3 explicitly treats
these as two different paths ("LOST 期间...无歧义 D+ 直接进入重播种路径
并置 `recovered_from_lost`" vs. the K=2/`n_min` gated path used to break a
confident-but-wrong B2-style lock). In the implementation,
`TripleGateState.evaluate()`
([controller/reanchor.py:552](controller/reanchor.py:552)) returns
`outcome="DISAGREE"` for both cases (the only difference is that
`lost=True` forces `trigger=True` immediately, bypassing the `K`/`n_min`
checks via `trigger = (lost or self._disagree_count >= ...) and
spacing_ok`), and no `lost` flag or trigger-reason is threaded into the
persisted `REANCHOR`/`DISAGREE` event fields
(`reanchor_runtime.py:117-125`, `_pending_fields` at
`reanchor_runtime.py:308-314`). I confirmed the frame-level
`recovered_from_lost` field in `track_loop.py` happens to end up correct
in practice (it is driven independently by the post-swap tracker's own
`result.ok` transition, which coincidentally realigns with the gate's
`lost` input since both derive from the same SOT `result.ok` at the same
source frame), so this is not a correctness bug — but it is a real gap
against acceptance criterion 1's call for "REANCHOR/RESEED_FAILED/
RESEED_DISCARDED/LOST 事件完整性": an auditor reading `frames.jsonl` alone
cannot tell which of the two design-distinct reseed paths produced a given
`REANCHOR` event without cross-referencing the source frame's own SOT
state.

**N3. The `WORKER_DIED`/one-confirmed-restart path is effectively
unexercised.** `SingleFlightWorker.poll()`'s `WORKER_DIED` branch fires
only when a thread finishes with `self._result is None`, which given
`target()`'s `except BaseException` wrapper is close to unreachable except
via direct state manipulation. No test constructs this scenario (the
existing `test_single_flight_busy_failure_and_timeout` only exercises the
timeout-then-late-completion path). Given the design explicitly enumerates
"worker 死亡→允许一次重启（计失败）" as a required semantic
(acceptance criterion 1), this is worth at least a directly-constructed
unit test even though the natural trigger is rare.

## Hand-traced (not just read) correctness confirmations

To avoid rubber-stamping the design-conformance claims, I independently
traced these end-to-end by hand rather than trusting the evidence doc's
prose:

- **Exact-frame atomic swap (binding 1).** Walked the exact call order in
  `TrackLoop.process_available`'s per-bundle loop: `consumed_frame_id`
  starts at `self.last_frame_id`; `before_update(consumed_frame_id)` runs
  *before* `tracker.update()`, and `after_frame` (which appends the
  just-consumed bundle to `self.history` under `self._lock`) runs *after*
  `tracker.update()` and updates `consumed_frame_id = bundle.frame_id`
  before the next iteration. This guarantees `self.history.head_frame_id`
  always equals the frame just handed to `before_update` as
  `last_consumed_frame_id`, so the "replay head == last consumed frame"
  check in `before_update` is checking a value that cannot have changed
  between the read and the swap (both happen inside one `with
  self._lock:` block, and the worker thread's own `self.history.append`
  path doesn't exist — only `after_frame`, main-thread-only, appends).
  This part of the atomicity contract is sound, independent of finding B1.
- **World-LOS/quaternion formula.** Independently re-derived the
  quaternion-rotation identity used in `validate_camera_basis` (the
  `t = 2*cross(q_xyz, v); v' = v + w*t + cross(q_xyz, t)` optimized
  Rodrigues form) and confirmed by hand it matches
  `_rotate_quaternion`'s unrolled arithmetic component-by-component.
- **Release-anchor semantics (binding 3).** Confirmed
  `ReanchorRuntime.initialize()` always calls `after_frame(...,
  released=False)` for the operator's initial frame — so the frozen
  appearance embedding (from the operator's box) can never leak into the
  motion anchor — and that the anchor is set for the first time only
  inside `after_frame` when `released=True` and `self.gate.anchor is
  None`, using *that frame's* SOT `result.box_norm`, not the operator's
  box. This matches "运动锚在 acknowledged release 帧上取该帧当前 SOT
  框的 LOS" and generalizes sensibly to non-RATE-002 runs (where
  `released` is always `True` after init, so the anchor is set from the
  first `process_available` frame's own SOT result).
- **Counters/denominators (binding 6).** Traced `planned_ticks` (always
  incremented in `after_frame` before the busy check, so busy/timeout/
  failure stay in the denominator) versus
  `completed_unexpired_rounds` (incremented in `poll()` only for
  `ROUND_COMPLETE` within `maximum_result_age_s`) and confirmed this
  matches "busy-skip/timeout/failure 均留在分母，完成且未超龄的 round 才
  进分子" exactly.
- **`event_counts` commingling of frame and audit-event names is
  intentional, not a bug.** I initially flagged this as a possible defect
  (event records carry `phase="measurement"` and their `event` values
  therefore land in the same `event_counts` dict as frame-level
  GAP/LOST/GEO_REJECT names), but `tests/test_run_log.py`'s
  `test_event_records_are_audited_without_entering_frame_denominators`
  explicitly pins this as intended ("audited" events), and no reanchor
  event name collides with an existing frame-level event name. Not a
  finding.

## Missing or weak tests

- No `TrackLoop`-level integration test with `reanchor_runtime` set (N1).
- No test directly exercising `SingleFlightWorker`'s `WORKER_DIED` →
  restart-allowed → second death → `_dead_permanently` chain (N3).
- No test exercises `reseed_failures`/`worker.consecutive_failures`
  reaching `consecutive_failure_limit=3` and producing
  `fatal_reason="reanchor_consecutive_failure_limit"` end-to-end.
- No test exercises `ROUND_SKIPPED_CADENCE_GAP` (`due_ticks > 1` in
  `after_frame`).
- No concurrency/stress test would have caught B1 — understandable since
  timing-dependent races are inherently hard to pin with a deterministic
  unit test, but worth a targeted test that forces the interleaving
  deterministically (e.g., inject a slow `evaluate()`/`propose()` via a
  fake and assert `self.gate`'s internal counters are lock-consistent
  under a concurrently-driven `before_update`), once B1 is fixed.

## Requirement-to-evidence mapping

| Accepted requirement | Evidence | Status |
|---|---|---|
| YOLOE/DINOv2 strict identity, offline load, official preprocessing, 384-d normalized output | `reanchor_models.py`, real smoke rerun, hash reproduction | Verified |
| Deterministic three gates, tie-break, margin/AMBIGUOUS, K hysteresis | `reanchor.py:TripleGateState`, `test_reanchor.py` | Verified (logic); race risk under concurrent worker/main access (B1) |
| Frame-consistent source-init + ordered replay + catch-up + atomic swap (binding 1) | `reanchor.py:replay_tracker`, `reanchor_runtime.py:before_update` | Verified, sound independent of B1 |
| Worker timeout/live-thread/restart/fail-closed semantics (binding 2) | `SingleFlightWorker` | Verified for the worker's own state; `reseed_failures` shares B1's race |
| World-LOS fixed reprojection + release-anchor semantics (binding 3) | `world_los`, `validate_camera_basis`, `after_frame` | Verified |
| Motion envelope as heuristic parameters, no truth reads (binding 4) | `config/detector-reanchor.models.json`, `frame_phase` | Verified |
| Supply-chain evidence before use (binding 5) | hash reproduction against disk artifacts | Verified |
| Counters/denominators exact semantics (binding 6) | traced above | Verified |
| No-truth boundary | grep + read of `reanchor.py`/`reanchor_models.py`/`reanchor_runtime.py` | Verified — no Unity truth reference anywhere in the new code |
| Tests genuinely cover claimed behavior | reran 89/89; read all new tests | Mostly, with gaps N1/N3 |

## Requested Codex action

1. **Fix B1**: extend `ReanchorRuntime._lock` coverage to the worker-thread
   side — wrap the `self.gate.anchor` read and `self.gate.evaluate(...)`
   call inside `round_work`, and the three `self.reseed_failures += 1`
   sites inside `_catch_up`, in `with self._lock:` (or otherwise make
   `TripleGateState` access single-writer-safe across both threads).
   Re-run the full suite and add a regression that would have caught this
   class of bug if feasible.
2. Consider closing N1 (a `TrackLoop`+`reanchor_runtime` integration test)
   and N3 (a direct `WORKER_DIED`/restart unit test) in the same batch,
   since both are inexpensive and this is a mandatory Sonnet stop point.
3. N2 is optional/non-blocking — if addressed, thread the gate's `lost`
   boolean (or an equivalent trigger-reason) into the persisted event
   fields for auditability; not required to close this round.
4. Return to the same Sonnet stop point with a new candidate commit;
   do not start scouting, Unity qualification, anchor relocation, or any
   successor-campaign work until this round closes with a `PASS`.

## Re-review result

PENDING — awaiting a fixed candidate from Codex.

## Round 2 handoff — concurrency rework

Status: `AWAITING_INDEPENDENT_REREVIEW`

This subsection is a Codex handoff, not an independent verdict.

Focused candidate: `0434de3`; range `f2555d5..0434de3`. Verify:

1. All worker/main accesses to `TripleGateState` and all reseed-failure
   increments/limit reads share `ReanchorRuntime._lock`; expensive detector
   and embedding work stays outside the critical section, with motion angles
   rebased under lock if the anchor changed meanwhile.
2. The deterministic interleaving test would fail on the Round 1 candidate:
   a worker blocked inside `gate.evaluate()` excludes a concurrent
   `before_update()` until the shared lock is released.
3. `TrackLoop` integration tests cover swap-before-update, event persistence
   and fatal termination; worker tests cover the one-death restart budget and
   reseed fail limit.
4. Persisted decision and REANCHOR records distinguish `LOST_DIRECT` from
   `K_HYSTERESIS`.
5. Full Python passes 96/96, `pip check` passes, and post-fix synthetic
   20 Hz main-loop p95 remains `13.981 ms` (`<50 ms`).

Do not run scouting, Unity qualification, anchor relocation or a successor
campaign before the focused verdict passes.

## Round 2 — independent re-review (concurrency fix): PASS

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-28
Candidate: `0434de3`, range `f2555d5..0434de3`
Verdict: **PASS**

### Scope of this round

Focused re-review per the Round 2 handoff above. Did not re-litigate
Round 1's already-verified findings (supply-chain hashes, model
smokes, world-LOS/quaternion math, exact-frame atomic-swap contract,
counters/denominators, no-truth boundary) since `git diff f2555d5..0434de3`
touches only `controller/reanchor_runtime.py` (implementation) plus tests
and docs — confirmed via `git diff --stat`, no other implementation file
changed.

### What was checked

1. **Read the full diff and the full post-fix file.** Enumerated every
   `self.gate` and `self.reseed_failures` access site in the new
   `controller/reanchor_runtime.py` via `grep -n`. All are now inside
   `with self._lock:` (directly, or via the new `_increment_reseed_failure()`
   helper): the worker-thread `round_work` closure snapshots
   `self.gate.anchor` under lock *before* the expensive
   `propose()`/`build_candidates()` calls (which correctly stay outside the
   lock — the fix does not naively serialize the async work with the main
   loop), then re-acquires the lock afterward, re-reads the current anchor,
   **rebases every candidate's `motion_angle_rad` via `angular_distance`
   against the current anchor if it changed while the lock was released**,
   and only then calls `self.gate.evaluate(...)` — all under the same lock.
   This closes B1 correctly, and the anchor-rebase is a genuine correctness
   improvement beyond just fixing the race: `TripleGateState.evaluate()`
   compares `candidate.motion_angle_rad` (precomputed) against a threshold
   derived from `self.anchor.capture_monotonic_s` — without the rebase, a
   concurrently-changed anchor would leave the angle and the threshold
   basis inconsistent even with the lock in place. The three
   `_catch_up` (worker thread) and one `poll()` (main thread)
   `reseed_failures` increments now all funnel through
   `_increment_reseed_failure()`, and `_refresh_fatal()` reads
   `self.reseed_failures` under lock. No remaining unlocked access found.
2. **Read every new/changed test** in `tests/test_reanchor.py` and
   `tests/test_track_loop.py` (`git diff f2555d5..0434de3`).
   `test_gate_evaluation_and_main_swap_share_runtime_lock` is a genuine
   deterministic interleaving test: a `BlockingGate` fake blocks inside
   `evaluate()` on a `threading.Event` until released; the test confirms a
   concurrently-started `before_update()` call does **not** complete within
   30 ms while the worker thread is parked inside the locked `evaluate()`
   call, then completes once released — this is a real proof of mutual
   exclusion, not a smoke test.
3. **Empirically reproduced that this new test would have caught the
   original bug** (not just trusted that it should, in the spirit of the
   project's existing empirical-verification standard set by earlier
   `P1-M2-RATE-002` rounds): checked out `f2555d5` into an isolated
   `git worktree`, copied the new `tests/test_reanchor.py` in, and ran
   `test_gate_evaluation_and_main_swap_share_runtime_lock` against the
   pre-fix `reanchor_runtime.py`. **It failed** — `before_update()`
   completed immediately instead of blocking
   (`AssertionError: True is not false` on
   `self.assertFalse(main_completed.wait(0.03))`) — confirming both that
   B1 was real and that the regression test genuinely detects it. Worktree
   removed after use.
4. Read `test_reseed_failure_increment_uses_runtime_lock` (proves
   `_increment_reseed_failure()` blocks on the held lock),
   `test_reseed_failure_limit_sets_fail_closed_reason_without_worker_message`
   (closes the "no test exercises the failure limit end-to-end" gap),
   `test_single_flight_allows_only_one_confirmed_death_restart` (directly
   constructs the `WORKER_DIED` → restart-allowed → second-death →
   `_dead_permanently`/`WORKER_RESTART_EXHAUSTED` chain, closing N3), and
   `test_events_distinguish_lost_direct_and_k_hysteresis_reseeds` (drives a
   real LOST round and a real two-round K-hysteresis sequence through the
   actual `TripleGateState`/`build_candidates` pipeline with lightweight
   fakes, and confirms `trigger_reason` is `"LOST_DIRECT"` on the
   immediate-bypass path, `None` then `"K_HYSTERESIS"` on the K=2 path, and
   that both propagate into the final `REANCHOR` event — closing N2). Hand
   -traced the K-hysteresis math by hand (disagree count 0→1→2 against
   `disagree_rounds_required=2`) and confirmed it matches.
5. Read the two new `tests/test_track_loop.py` integration tests using a
   `RecordingReanchorRuntime` fake:
   `test_reanchor_integration_swaps_before_update_and_audits_events`
   directly proves the swap-before-update ordering I had previously only
   hand-traced (the original tracker's `update()` is never called once a
   replacement is returned from `before_update`, and `before_update` is
   called with frame IDs `[0, 1]` in the correct sequence) and that
   `_drain_reanchor_events` persists exactly the audited events as
   `record_kind="event"`.
   `test_reanchor_fatal_reason_terminates_track_loop` proves the
   `fatal_reason` → `_record_terminal_error` → `terminal=True` shutdown
   path, including that already-queued events are still drained and
   persisted before termination. This closes N1.
6. **Independently reran everything**, not trusting the evidence doc's
   numbers: `.venv-track/bin/python -m unittest discover -s tests -v` →
   **96/96 pass** (matches); `uv pip check --python .venv-yoloe/bin/python`
   → **42/42 compatible** (matches, config/model artifacts untouched by
   this diff so no need to re-hash); reran
   `python -m tools.benchmark_reanchor --frames 60 --rate-hz 20` against
   the real DINOv2/YOLOE models myself and independently got main-loop
   p50/p95/max `8.687/10.500/10.545 ms` (evidence doc reports
   `11.195/13.981/18.671 ms` from a separate run — both comfortably under
   the 50 ms budget; the difference is ordinary machine-load variance
   between runs, not a discrepancy), detector `69.573 ms`, worker
   `91.240 ms`, cadence `1/1` qualified, `fatal_reason: null`.

### Findings

No new blocking or non-blocking findings. All of Round 1's items are
closed:

| Round 1 item | Disposition |
|---|---|
| B1 (unlocked worker/main `TripleGateState`/`reseed_failures` race) | **Fixed**, verified by reading the diff, enumerating all access sites, and empirically reproducing the pre-fix test failure |
| N1 (no `TrackLoop` integration test) | **Closed** — two new integration tests |
| N2 (LOST-bypass vs K-hysteresis indistinguishable) | **Closed** — `trigger_reason` field, tested end-to-end |
| N3 (`WORKER_DIED`/restart unexercised) | **Closed** — direct unit test |

I looked for new issues introduced by the fix specifically (double-checked
locking in the release-anchor-init path re-reading `self.gate.anchor is
None` after re-acquiring the lock; possible lock re-entrancy; whether
raising inside a `with self._lock:` block could leak the lock) and found
none — `after_frame` is main-thread-only so the double-checked pattern
isn't racing with itself, `threading.Lock.__exit__` runs on exception
propagation, and there is no nested/reentrant lock acquisition anywhere in
the new code.

### Re-review result

**PASS.** `P1-DETECT-001` candidate `0434de3` is independently verified
against the accepted design and Round 2 binding clarifications, with the
concurrency defect fixed and empirically confirmed, and all non-blocking
notes closed with real tests. This closes the Sonnet independent-review
gate for this work item. Remaining before `DONE`: the §8 remote-recall
scouting gate, the §Acceptance-6 qualification run, and Unity validation
(`UT-P1-DETECT-001-001`) — none of which are in this review's scope and
none of which I ran.

## Round 3 handoff — §8 scouting protocol implementation

Status: `SCOUTING_TOOL_STABLE_CANDIDATE_AWAITING_REVIEW`

This subsection is a Codex handoff, not an independent verdict.

Focused candidate: `d0c2dde`; range `296a0de..d0c2dde`. The runtime carrier
itself (`0434de3`) is unchanged by this diff — only the evaluator-only
scouting truth path, the offline scouting tool, a dedicated scenario config,
and docs are new. Verify:

1. Active/durable session identity and scenario-hash binding
   (`P1DetectScoutingSession`, `ConfigureScouting`).
2. Create-once truth/reference/result semantics and stale-artifact refusal.
3. `CoverageEvaluator`-only truth production and controller non-consumption
   (no-truth-leak boundary).
4. Fixed-tick selection, conservative missing-pair denominator, and IoU
   recall in `tools/run_detector_scouting.py:analyze_session`.
5. Reference/model hash chain and target/distractor cosine reporting.
6. The explicit refusal to auto-decide embedding feasibility or tune/move
   anything.
7. Seven Python tests plus five focused Unity Edit Mode tests (the latter
   were compiled but not claimed executed by Codex because another Unity
   instance owned the project).

Do not prepare/capture scouting data, move geometry, qualify, or start a
successor campaign before the focused verdict passes.

## Round 3 — independent review (§8 scouting protocol implementation): PASS_WITH_NOTES

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-28
Candidate: `d0c2dde`, range `296a0de..d0c2dde`
Verdict: **PASS_WITH_NOTES**

### Scope of this round

Focused review per the Round 3 handoff above and the Round 3 evidence doc
(`docs/evidence/P1-DETECT-001-scouting-implementation.md`). Confirmed via
`git diff --stat 296a0de..d0c2dde` that the diff touches only
`Assets/TetheredTracking/Scripts/CoverageEvaluator.cs` (additive),
`Assets/TetheredTracking/Scripts/P1DetectScouting.cs` (new),
`Assets/TetheredTracking/Tests/EditMode/P1DetectScoutingEditModeTests.cs`
(new), `config/scenario.p1-detect-scouting.json` (new),
`tools/run_detector_scouting.py` (new), `tests/test_detector_scouting.py`
(new), `runtime/README.md`, and docs — the Round 2-verified runtime carrier
(`controller/reanchor*.py`, `controller/track_loop.py`) is untouched, so
Round 1/2's findings were not re-litigated.

### What was checked

1. **Read every new/changed file in full**: `CoverageEvaluator.cs`'s diff
   (`ConfigureScouting`, `WriteScoutingTruth`, `ProjectRenderers`,
   `StableObjectId`), all of `P1DetectScouting.cs`
   (`P1DetectScoutingSession`, `P1DetectScoutingTruthWriter`), all of
   `tools/run_detector_scouting.py` (`prepare_session` through
   `close_session`), the new Edit Mode and Python test files, and
   `config/scenario.p1-detect-scouting.json`.
2. **Session/config identity binding.** Independently diffed
   `config/scenario.p1-detect-scouting.json` against
   `config/scenario.rate-study-20hz.json`: confirmed by hand (not just by
   trusting the evidence doc) that the only differences are `scenario_id`,
   `sensor.retained_frame_count` (512→2560) and
   `evaluation.maximum_pending_frame_count` (2048→4096) — matching the
   claim that geometry/route/gimbal/drone parameters are byte-identical to
   the already-frozen 20 Hz follow scenario.
   `tools.run_detector_scouting.validate_scouting_config` independently
   re-derives this same equivalence at runtime (normalizes both configs and
   compares), and `CoverageEvaluator.ConfigureScouting` separately verifies
   `config.scenario_id`, the on-disk scenario file's SHA-256, and the
   distractor count/identity before ever constructing a truth writer — a
   real defense-in-depth chain, not a single point of trust.
3. **Create-once semantics.** Traced `_create_once`
   (`os.O_WRONLY|O_CREAT|O_EXCL`) on the Python side and
   `P1DetectScoutingTruthWriter.WriteCreateOnce` (write-to-temp +
   `File.Move`, which throws `IOException` on an existing destination — the
   2-argument `File.Move` overload does not overwrite) on the C# side.
   Confirmed both raise on a second write via the existing tests, and
   confirmed by reading (not just trusting) that `prepare_session`,
   `preview_reference`, `bind_reference`, and `analyze_session` all
   create-once their respective manifest/preview/reference/result files, so
   no step in the pipeline can be silently re-run with different inputs to
   fish for a different outcome.
4. **No-truth-leak boundary.** Reran
   `test_truth_sidecar_is_not_referenced_by_controller_runtime` and then
   independently reproduced its grep myself outside the test
   (`grep -rl "p1-detect-scouting\|p1_detect_scouting\|P1DetectScouting"
   controller/` → no matches; equivalent C# grep → only
   `CoverageEvaluator.cs`/`P1DetectScouting.cs`, the two intended files).
   `WriteScoutingTruth` is gated on `scoutingTruthWriter != null`, which is
   only set when a valid session file is present, so non-scouting scenarios
   are unaffected.
5. **Fixed-tick sampling and missing-pair semantics
   (`analyze_session`).** Hand-traced the tick loop against the approved
   binding text (`docs/evidence/P1-DETECT-001-scouting-readiness.md`):
   `bisect.bisect_left` selects the first frame at/after each fixed
   half-second tick (correct); a tick with no frame inside
   `[tick, tick+0.5)` or with a missing image/truth file increments both
   `denominator` and `missing_pair_misses` and is recorded as a miss
   (correct fail-closed direction — matches "missing pairs remain in the
   denominator and fail closed as misses"). A tick whose truth *is* present
   but shows the target not remote-visible is correctly excluded from the
   denominator entirely (it is not a "remote-visible sample" at all, not a
   miss) — this is the right reading of "remote-visible samples" as the
   denominator population, not "all ticks." Confirmed the recall/embedding
   computation only ever counts a hit via `IoU >= 0.30` against a
   `confidence >= 0.25` YOLOE proposal, and never auto-tunes
   `tau_reid=0.5`/`m_margin=0.1` — `reid_threshold`/`reid_margin` are only
   read from the frozen re-anchor config for a consistency assertion, never
   fit from the observed distributions. `overall_decision` is
   `RETURN_TO_USER_OPTION_B` whenever recall `< 0.5`, and otherwise
   `AWAITING_EMBEDDING_FEASIBILITY_REVIEW` (never an automatic "go") since
   the approved protocol never defined an automatic feasibility statistic —
   this matches the evidence doc's claim and the spirit of "不自动改几何."
6. **Reference/model hash chain.** Confirmed `preview_reference` picks the
   first complete frame in `[7,8)` s — reusing the already-accepted
   `INIT_WINDOW_S = (7.0, 8.0)` constant from `tools/run_rate_study.py`
   verbatim, not a newly-invented window for this decision. Confirmed
   `bind_reference`/`analyze_session` hash-check the reference image and
   metadata before use, and that `analyze_session` cross-checks
   `detector_threshold`/`reid_threshold`/`ambiguity_margin` in
   `config/detector-reanchor.models.json` against the frozen scouting
   constants before running — config/model artifacts are unchanged by this
   diff (confirmed via `git diff --stat`), so I did not need to re-hash the
   model weights already verified in Rounds 1–2.
7. **Independently reran everything, not trusting the evidence doc's
   numbers:**
   - `.venv-track/bin/python -m unittest discover -s tests -v` →
     **103/103 pass** (matches the claim exactly, including the seven new
     `test_detector_scouting.py` cases).
   - `uv pip check --python .venv-yoloe/bin/python` → **42/42 compatible**
     (matches; model/package artifacts untouched by this diff).
   - **Closed the evidence doc's own open gap**: Codex's candidate stopped
     short of running the five new Edit Mode tests because another Unity
     instance owned the project at the time. No Unity instance was running
     when I started this review (`ps aux` showed no `Unity` process, no
     `Temp/UnityLockfile`), so I ran them myself in batch mode:
     `Unity -batchmode -nographics -projectPath . -runTests -testPlatform
     EditMode -testFilter P1DetectScoutingEditModeTests` →
     **10/10 test cases pass** (5 test methods, one parameterized ×6). I
     then went further and ran the **full** Edit Mode suite (no filter) to
     check for regressions beyond the review's minimum scope: **83/83
     pass**. `git status --short` was clean before and after (no tracked
     files changed; the temp directories the tests use are outside the
     repo). This closes the "compiled but not claimed executed" gap from
     the evidence doc with real, independently-observed pass results
     instead of leaving it open for a future round.
   - Confirmed `git status --short` under `runtime/` shows no new scouting
     artifacts before or after my review session (no `p1_detect_scouting_session.json`,
     no `runtime/p1-detect-scouting/` directory) — I did not run
     `tools.run_detector_scouting prepare` or any other step that would
     start a real session, per the handoff's explicit instruction.

### Findings

No blocking findings.

**N4 (non-blocking).** `P1DetectScoutingTruthWriter.Write()`
([P1DetectScouting.cs:150-154](Assets/TetheredTracking/Scripts/P1DetectScouting.cs:150))
throws `InvalidOperationException("invalid_scouting_truth")` whenever
`target_visible == true` but `target_bbox_xywh_norm` is `null` or
degenerate. This is reachable: `target_visible` comes from
`VisibilitySnapshot.GeometricallyVisible`, which is `true` whenever `>=20%`
of 15 sample points (8 AABB corners + center + 6 face-centers) are
simultaneously in-frustum and have clear line of sight, while
`target_bbox_xywh_norm` comes from `ProjectBounds`, which only needs *one*
corner with `viewport.z > 0` to attempt a box and returns `null` if the
clamped corner span collapses to zero width/height. I worked through the
projective-geometry argument by hand: if all 8 AABB corners are in front of
the camera (`z > 0`), the corner-derived bounding rectangle *must* contain
every interior sample's projection (perspective projection of a convex hull
does not introduce new extreme points when every vertex is on the same
side of the camera plane), so `GeometricallyVisible == true` and
`box == null` can only co-occur when at least one AABB corner is behind the
camera's local z-plane — a low-altitude (8–32 m), close-range or
rapid-gimbal-slew edge case that is physically atypical for this scenario
but not proven impossible.

This is a real inconsistency with the same file's own established
convention: `BuildMetricsDocument` already tolerates `box == null` for a
geometrically-visible frame (`areaPixels = box == null ? 0f : ...`), and
`P1DetectScoutingTruthWriter.Write`'s own distractor-box validation is
explicitly lenient (`distractor.bbox_xywh_norm != null && !ValidBox(...)`,
i.e. `null` is allowed) — only the target-visible case is strict. I traced
the consequence carefully rather than assuming it is severe: the throw
happens *before* any file write (all validation precedes
`WriteCreateOnce`), so no truth file is corrupted, just skipped for that
one frame; `analyze_session` would then classify that tick via
`MISSING_IMAGE_TRUTH_PAIR` (`truth_path.is_file()` is false), which is
counted as a denominator+miss — the *exact same* outcome
(denominator+1, not a hit) that a hypothetical graceful null-box write
would produce via the `TARGET_BOX_MISSING` branch. So this does not bias
the recall go/no-go number differently than the intended fail-closed
design; it only means (a) a Console error is logged and that frame's
`RecordFrame`/`metrics.json` aggregation is skipped (metrics.json is not
consumed by the scouting analysis), and (b) the `missing_pair_misses`
diagnostic counter would under-report by one relative to a "graceful null"
implementation, purely as a reporting/diagnostic wrinkle. `CoverageEvaluator`'s
own `OnFramePublished` is the last subscriber on `SensorFrameWriter.FramePublished`
(confirmed by reading `TetheredScenarioBootstrap.Awake()`'s subscription
order), so no other frame-processing subscriber is starved by the
exception, and nothing indicates the exception disables the component for
subsequent frames (Unity does not disable a `MonoBehaviour` because one
`Update`-chain callback threw).

Given the single, costly, manually-run ~110 s+ continuous capture session
this candidate exists to protect, I recommend (not require) aligning
`Write()`'s target-box validation with the file's own established
null-tolerant convention before the real capture is attempted, so a
transient edge case produces a quiet, already-anticipated
`MISSING_IMAGE_TRUTH_PAIR` miss instead of a Console exception mid-session.
Not blocking because the go/no-go recall computation is unaffected either
way and the failure is self-healing frame-to-frame.

**N5 (non-blocking, informational).** `analyze_session`'s tick loop
(`tick_count = floor(LOOP_DURATION_S * SAMPLE_HZ) + 1` = 213 ticks) samples
`start + 0.0s` through `start + 106.0s`, not through `start + 106.485s`
(the full loop duration). This is a reasonable, deterministic, pre-data
choice — sampling exactly at the loop seam would nearly duplicate the
first sample, since a full loop returns to the start position — and the
frozen text does not specify an exact tick-count formula. Since the loop's
close/seam point is on the near side of the route (close to the `[7,8)` s
init position, not the `>=65 m` remote segment that determines the
recall denominator), this is very unlikely to materially change the
remote-visible sample population. Documenting this interpretation for the
record since it was an implementation judgment call, not something
Codex needs to act on.

### Requirement-to-evidence mapping

| Reviewed item | Evidence | Status |
|---|---|---|
| Session/config identity + scenario-hash binding | `P1DetectScoutingSession`, `ConfigureScouting`, `validate_scouting_config`; hand-diffed config | Verified |
| Create-once truth/reference/result, stale-artifact refusal | `_create_once`/`WriteCreateOnce`, traced pipeline | Verified |
| `CoverageEvaluator`-only truth, controller non-consumption | Independent grep (not just the test) | Verified — no leak |
| Fixed-tick selection, missing-pair denominator, IoU recall | Hand-traced `analyze_session` against the approved binding text | Verified, with N5 noted |
| Reference/model hash chain, cosine reporting | Traced hash checks; `INIT_WINDOW_S` reuse confirmed | Verified |
| No auto-decided embedding feasibility / no tuning | `overall_decision` logic, frozen-threshold consistency assertion | Verified |
| Seven Python + five Edit Mode tests | Reran all: 103/103 Python, 10/10 focused + 83/83 full Edit Mode | Verified — gap from evidence doc closed |
| Boundary condition: visible-but-unprojectable target box | `P1DetectScoutingTruthWriter.Write` | **N4** — real but non-blocking, bounded/self-healing |

### Re-review result

**PASS_WITH_NOTES.** `P1-DETECT-001` scouting-tool candidate `d0c2dde` is
independently verified against the user-approved §8 protocol and the
readiness clarification: session/config identity, create-once semantics,
the evaluator-only no-truth-leak boundary, fixed-tick/missing-pair/IoU
recall arithmetic, the hash chain, and the no-auto-tuning/no-auto-go
decision logic are all correct. All seven Python tests and all five
focused Unity Edit Mode tests pass — I closed the previously-open "not
claimed executed" gap myself by running them (10/10 focused, 83/83 full
suite), since no Unity instance was holding the project lock. Two
non-blocking notes (N4, N5) go to the backlog; N4 is worth a defensive fix
before the real capture given the session's one-shot cost, but neither
changes the recall go/no-go arithmetic or blocks this gate. Per the
handoff, I did not prepare or capture any scouting session, move geometry,
or start a qualification/successor campaign — `runtime/` shows no scouting
artifacts before or after this review. This closes the Sonnet review gate
for the scouting-tool candidate; the real Unity validation capture,
embedding-feasibility human review, qualification, and
`UT-P1-DETECT-001-001` remain and are return to Codex.

## Round 4 handoff — Capture Amendment A2 (validation-only truth-directed follow)

Status: `TRUTH_FOLLOW_STABLE_CANDIDATE_AWAITING_REVIEW`

This subsection restates the Codex handoff (`docs/current-status.md` Active
handoffs table and the evidence doc's "Capture Amendment A2 Sonnet scope"),
not an independent verdict.

Focused candidate: `fa1156d`; range `67223c4..fa1156d`. The Round 2-verified
runtime carrier and Round 3-verified scouting-tool candidate are unchanged by
this diff (confirmed via `git diff --stat`) — only the driver-identity
extension to the session/truth schema and the new Unity-only gimbal driver are
new. Verify:

1. Strict active/durable `gimbal_driver` identity and per-frame sidecar
   binding, including offline mismatch rejection.
2. `CoverageEvaluator`-only driver construction after the complete
   non-measurement scenario/hash/distractor gate (post-gate construction, not
   pre-gate).
3. Deterministic external `GimbalCommandReceiver` disable/log behavior and
   moving-target refresh through the unchanged 45°/slew/saturation
   `TetheredGimbal.LookAtWorld` plant.
4. Zero controller references to session, driver or Unity truth (expanded
   audit).
5. The explicit `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND` /
   `closed_loop_recall_claimed=false` result contract.
6. The new Python, Edit Mode and Play Mode tests, rerun independently.

Do not prepare/capture a session, move geometry, qualify, or start a
successor campaign before the focused verdict passes. Keep implementation
read-only.

## Round 4 — independent review (Capture Amendment A2: validation-only truth-directed follow): PASS

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-28
Candidate: `fa1156d`, range `67223c4..fa1156d`
Verdict: **PASS**

### Scope of this round

Focused review per the Round 4 handoff above, against the accepted "Capture
Amendment A2" text in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` (Fable
clarification + Codex `ACCEPTED`, 2026-07-28) and the four binding
constraints therein. Confirmed via `git diff --stat 67223c4..fa1156d` that
the code diff touches only
`Assets/TetheredTracking/Scripts/CoverageEvaluator.cs` (additive: one new
field, one `Update()` call, `ConfigureScoutingGimbal`/
`UpdateScoutingGimbalForTests`), `Assets/TetheredTracking/Scripts/P1DetectScouting.cs`
(new `gimbal_driver` field/identity check plus the new
`P1DetectScoutingGimbalDriver` class), `tools/run_detector_scouting.py`
(constants, session document, truth-load check, result labeling), two test
files, and docs — `controller/reanchor*.py`, `controller/track_loop.py`, and
`TetheredGimbal.cs`/`GimbalCommandReceiver.cs` (the pre-existing plant and
external command path) are untouched, so Rounds 1–3's findings were not
re-litigated.

### What was checked

1. **Read every changed file in full and the two unchanged files that this
   design depends on** (`TetheredGimbal.cs`, `GimbalCommandReceiver.cs`), not
   just the diff, to confirm what "unchanged 45° plant" and "external
   receiver disable" actually mean at the code level.
2. **Driver identity chain.** `P1DetectScoutingSession.Validate()` now
   rejects any `gimbal_driver` other than the `TruthDirectedGimbalDriver`
   constant (`"truth_directed_scouting"`) as part of
   `invalid_scouting_session_identity`, so a session file cannot be loaded at
   all without the correct driver tag. `P1DetectScoutingTruthWriter.Write()`
   independently re-checks `document.gimbal_driver != session.gimbal_driver`
   before every frame write (defense-in-depth, not a single point of trust —
   consistent with the pattern already established for `session_id`/
   `scenario_id` in Round 3). `WriteScoutingTruth` in `CoverageEvaluator.cs`
   sets `gimbal_driver = scoutingSession.gimbal_driver` from the already-
   validated session, not a hardcoded literal. On the offline side,
   `tools/run_detector_scouting.py`'s `_session_document` writes
   `"gimbal_driver": GIMBAL_DRIVER` into the create-once session manifest,
   and `_load_truth` rejects any truth file whose `gimbal_driver` field
   doesn't match `GIMBAL_DRIVER` before it can be used by `analyze_session`.
   I independently re-derived (not just read) that this closes the loop: a
   session or truth sidecar cannot claim the driver identity without the
   Unity-side driver actually being constructed (see next point), and
   `analyze_session` cannot consume truth produced under a different/absent
   driver.
3. **Post-gate, Unity-only construction (not pre-gate).** Read
   `CoverageEvaluator.ConfigureScouting` end-to-end: `P1DetectScoutingSession.TryLoad`
   (file existence + JSON parse + `Validate()`) runs first and throws on any
   error; then the non-measurement/active-experiment check; then the
   scenario-identity and on-disk scenario-file SHA-256 check; then the
   distractor count/identity/collision checks. Only *after* all of these
   pass does the method construct `scoutingTruthWriter` and then call
   `ConfigureScoutingGimbal(loaded, scenario.Gimbal, scenario.Target.transform,
   scenario.GetComponent<GimbalCommandReceiver>())` — the driver literally
   cannot be constructed on any path that throws earlier in the gate chain.
   `P1DetectScoutingGimbalDriver.Configure` itself re-validates
   `session.Validate() != null` as a second, independent check before doing
   anything, so even a hypothetical future caller that skips
   `ConfigureScouting`'s gate chain cannot get a live driver from an invalid
   session. Confirmed this call path is Unity-only: `ConfigureScouting` is
   private/internal and only ever invoked from `CoverageEvaluator.Start()`;
   grepped the whole repo for `ConfigureScoutingGimbal` and found only the
   production call site plus the two new test call sites.
4. **External receiver disable/log.** Read `GimbalCommandReceiver.cs` in
   full: it is a plain `MonoBehaviour` whose only externally-visible command
   path (`ReadCommand`, called from its own `Update()`) has no knowledge of
   scouting at all — it is disabled purely from the outside via
   `Behaviour.enabled = false`, which is a standard Unity guarantee that
   `Update()` will not fire on a disabled component. Traced the actual
   wiring: `TetheredScenarioBootstrap.Awake()` adds both
   `GimbalCommandReceiver` and `CoverageEvaluator` to the *same* GameObject
   (`gameObject.AddComponent<GimbalCommandReceiver>()` at line 56, then
   `gameObject.AddComponent<CoverageEvaluator>()` at line 58), so
   `scenario.GetComponent<GimbalCommandReceiver>()` in `ConfigureScouting`
   correctly resolves to the real receiver, not a wiring no-op. Because Unity
   guarantees all `Awake()`/`Start()` calls complete before any `Update()`
   call in a given frame, disabling the receiver inside
   `CoverageEvaluator.Start()` is guaranteed to take effect before the
   receiver's `Update()` ever runs even once — confirmed this is the correct
   reading of Unity's script lifecycle, not an assumption papered over by the
   test. `Configure()` logs one of two distinct `Debug.Log` messages
   (disabled vs. absent) and exposes `ExternalCommandReceiverDisabled` for
   tests to assert on. The new focused Edit Mode test
   (`TruthDirectedGimbalUsesPlantAndDisablesExternalReceiver`) constructs a
   real `GimbalCommandReceiver` and asserts `receiver.enabled == false` after
   `Configure`, and the absent-receiver branch (`externalCommandReceiver ==
   null`) is exercised implicitly by every other scouting test that doesn't
   attach a receiver.
5. **Unchanged 45°/slew/saturation plant.** Confirmed `TetheredGimbal.cs` is
   byte-identical to before this diff (absent from `git diff --stat`) —
   `LookAtWorld` only records `TargetWorld`/`HasTarget`; the actual clamp
   (`Mathf.Min(requested, maximumOffNadirDeg)`), saturation flag, and
   `Quaternion.RotateTowards` slew all live in the pre-existing, untouched
   `LateUpdate()`, executed identically regardless of whether the caller is
   the external `GimbalCommandReceiver` or the new
   `P1DetectScoutingGimbalDriver` — the new driver is just another caller of
   the same executor, not a parallel implementation that could drift from
   the production clamp. This is not just a structural read: the new
   `TruthDirectedScoutingFollowUsesTheClampedGimbalPlant` Play Mode test
   places the target at a geometry that requests an off-nadir angle well
   past 45° (100 m horizontal offset at 25 m altitude ⇒ `atan2(100, 25) ≈
   76°`), drives one real physics frame with `LateUpdate` actually running,
   and asserts `gimbal.Saturated == true` **and** the camera's actual forward
   vector is `45°` off nadir to within `1e-3°` — an empirical proof that the
   clamp is live under the new driver, not merely unmodified source.
6. **Expanded controller zero-reference audit.** Independently re-ran the
   grep from Round 3 with the two new terms added, exactly as the new test
   does: `grep -rln "truth_directed_scouting\|gimbal_driver"
   controller/*.py tools/*.py` → only `tools/run_detector_scouting.py`
   matches (confirmed `tools/run_rate_study.py`, the actual measurement CLI,
   has zero references). Separately grepped
   `Assets/TetheredTracking/Scripts/*.cs` for the same two terms outside the
   two allowed files (`CoverageEvaluator.cs`, `P1DetectScouting.cs`) and
   found none — in particular `GimbalCommandReceiver.cs` itself contains no
   reference to scouting identifiers, confirming the disable is a one-way,
   external action and the production command path was not modified to grow
   scouting-awareness. This matches and extends
   `test_truth_sidecar_is_not_referenced_by_controller_runtime`'s new
   assertions, which I re-derived independently rather than trusting.
7. **Oracle-upper-bound result label.** Read `analyze_session`'s result dict
   construction in `tools/run_detector_scouting.py`: `recall.interpretation`
   is hardcoded to the module-level constant
   `RECALL_INTERPRETATION = "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND"` (not
   computed, not conditional) and `recall.closed_loop_recall_claimed` is
   hardcoded `False` on every path, so there is no code path through
   `analyze_session` that could omit or invert this label. Also confirmed
   `frozen_protocol.gimbal_driver` is included in the result document,
   giving the offline artifact a self-contained record of which driver
   produced the underlying truth. Cross-checked this against the accepted
   proposal text ("scouting 结果把 recall 标为
   `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND`，明确
   `closed_loop_recall_claimed=false`") — exact match, not a paraphrase.
8. **Independently reran everything myself, not trusting the evidence doc's
   numbers, using a fresh session with no Unity editor already holding the
   project** (`ps aux` showed no `Unity` editor process; no
   `Temp/UnityLockfile`; used the project's own configured editor version
   `6000.4.1f1` per `ProjectSettings/ProjectVersion.txt`, batchmode/nographics):
   - `.venv-track/bin/python -m unittest discover -s tests -v` → **105/105
     pass** (matches the claim exactly).
   - `uv pip check --python .venv-yoloe/bin/python` → **42/42 compatible**
     (matches; model/package artifacts untouched by this diff, consistent
     with `git diff --stat` showing no `config/detector-reanchor.models.json`
     or model-loading file changed).
   - Focused Edit Mode (`-testFilter P1DetectScoutingEditModeTests`) →
     **12/12 pass** (matches).
   - Full Edit Mode (no filter) → **85/85 pass** (matches).
   - Focused Play Mode (`-testFilter
     TruthDirectedScoutingFollowUsesTheClampedGimbalPlant`) → **1/1 pass**
     (matches).
   - Full Play Mode (no filter) → **3/3 pass** (matches).
   - `python3 tools/check_docs.py` → passes on the disk state I am about to
     write.
   - Confirmed no side effects from running the tests: `git status --short`
     is clean (no tracked-file changes, no untracked files) before and after,
     and `runtime/p1-detect-scouting/` and
     `runtime/p1_detect_scouting_session.json` do not exist — no real
     scouting session, capture, reference or result was created by this
     review, per the handoff's explicit instruction.

### Findings

No blocking findings.

I looked specifically for ways this change could let a stale or foreign
`gimbal_driver` value leak into a truth artifact or let the driver activate
before the identity gate — the three-layer check (session `Validate()` at
load time, `P1DetectScoutingGimbalDriver.Configure`'s independent
re-validation, and the truth writer's per-frame
`document.gimbal_driver != session.gimbal_driver` check) leaves no path I
could find where a mismatched or missing driver identity reaches either a
live gimbal command or a persisted truth file. I also checked whether the
new `Update()` call (`scoutingGimbalDriver?.UpdateTarget()`) could throw
after `Configure()` in a way that disables only the truth-writing half of
scouting while leaving the disabled `GimbalCommandReceiver` unable to
recover control (it would need a full Play restart either way, since
`enabled` is never set back to `true` anywhere in this diff or the
pre-existing code) — this is fail-closed by omission, not a silent partial
failure, and matches the project's established fail-closed convention for
this file.

**N6 (non-blocking, informational).** The Play Mode/Edit Mode tests
construct `GimbalCommandReceiver`/`CoverageEvaluator` directly and call
`ConfigureScoutingGimbal` synchronously, rather than going through the full
`TetheredScenarioBootstrap.Awake()` → `Start()` sequence. This is consistent
with how prior rounds' tests are structured (hand-constructed fixtures
rather than full-scene bootstrap) and does exercise the real disable
mechanism, but it does not by itself exercise the same-frame
Awake-before-Update ordering guarantee that production relies on for the
receiver to never fire even once before being disabled. I independently
verified that ordering by reading Unity's documented script lifecycle and
the exact `AddComponent` call sequence in
`TetheredScenarioBootstrap.Awake()` (§ point 4 above) rather than trusting
it, so I am not blocking on this — but a full-bootstrap integration test
would remove the last inch of reliance on engine-ordering knowledge if
Codex wants to close it before the real capture. Not required.

### Requirement-to-evidence mapping

| Reviewed item | Evidence | Status |
|---|---|---|
| Strict `gimbal_driver` identity + per-frame sidecar binding + offline mismatch rejection | `P1DetectScoutingSession.Validate`, `P1DetectScoutingTruthWriter.Write`, `_load_truth`; `test_analyze_rejects_truth_from_another_gimbal_driver` | Verified |
| Post-gate, Unity-only driver construction | Hand-traced `ConfigureScouting` call order; grepped for other call sites | Verified |
| External `GimbalCommandReceiver` disable/log | Read `GimbalCommandReceiver.cs`, `TetheredScenarioBootstrap.Awake()` wiring, focused Edit Mode test | Verified |
| Unchanged 45°/slew/saturation plant | Confirmed `TetheredGimbal.cs` untouched; empirical Play Mode saturation proof | Verified |
| Zero controller/Unity-script references outside the two allowed files | Independent grep, expanded to new terms | Verified |
| `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND` / `closed_loop_recall_claimed=false` | Read `analyze_session`'s hardcoded result fields | Verified |
| Python + Edit Mode + Play Mode tests genuinely cover claimed behavior | Reran all myself: 105/105, 12/12, 85/85, 1/1, 3/3 | Verified |
| No session/capture created during review | `git status --short`, `runtime/` inspection before/after | Verified |

### Re-review result

**PASS.** `P1-DETECT-001` Capture Amendment A2 stable candidate `fa1156d` is
independently verified against the accepted amendment text and its four
binding constraints: the `gimbal_driver` identity chain is closed end-to-end
(session load, per-frame sidecar, offline analysis), the truth-directed
driver is constructed by `CoverageEvaluator` only after the complete
non-measurement/hash/distractor gate, the external `GimbalCommandReceiver`
is disabled and logged with no scouting-awareness added to its own source,
the pre-existing 45°/slew/saturation `TetheredGimbal` plant is unmodified
and empirically proven to still clamp under the new driver, the controller
and Unity-script zero-reference audit was independently re-derived and
holds, and the offline result contract hardcodes the oracle-upper-bound
label with no closed-loop claim. All new Python, Edit Mode and Play Mode
tests pass under an independent rerun (105/105, 12/12, 85/85, 1/1, 3/3), and
no scouting session, capture, reference or result exists in `runtime/`
before or after this review — I did not prepare, capture, move geometry, or
start a qualification/successor campaign, per the handoff. This closes the
Sonnet independent-review gate for `P1-DETECT-001` end-to-end (runtime
carrier, scouting tool, and Capture A2 control-protocol change all now
`PASS`/`PASS_WITH_NOTES`). Remaining before `DONE`: the real Unity
validation capture, embedding-feasibility human review, the §8 go/no-go
qualification, and `UT-P1-DETECT-001-001` — none of which are in this
review's scope and none of which I ran. Return to Codex.

## Round 5 handoff — Recovery Amendment A3 (bbox-schema reanalysis)

Status: `A3_STABLE_CANDIDATE_AWAITING_REVIEW`

This subsection restates the Codex handoff (`docs/current-status.md` Active
handoffs table and the evidence doc's "Recovery Amendment A3 Sonnet scope"),
not an independent verdict.

Focused candidate: `28b9e84`; range `5ffacd9..28b9e84`. Between Round 4 and
this candidate, Codex ran the reviewed `prepare` exactly once, the user
completed the single real Unity capture, and the first real `analyze` exposed
a bbox-schema mismatch (Unity truth writes `{x,y,width,height}` objects;
the offline IoU/embedding validator only accepted four-element sequences),
leaving all 27 remote-visible target crops falsely `CROP_INVALID` and the
canonical result `c7876364…f8b4` with empty embedding evidence. The user
authorized a narrow Recovery Amendment A3; Codex accepted it with two
additional bindings (canonical-result immutability/unclosability via the old
path, and a `1e-5`-bounded Unity write-side roundoff clamp). Verify:

1. Exact dual-schema box normalization (object with exactly `{x,y,width,height}`,
   or a finite four-element sequence) shared by IoU and embedding, fail-closed
   on every other shape (bool, string, wrong key set, non-finite, degenerate).
2. Byte-for-byte real-capture fixture provenance and direct use in tests.
3. Create-once plan/result/supersession/completion identities; preservation
   of the canonical invalid result `c7876364…f8b4`.
4. Refusal of legacy close once an A3 plan exists, and complete A3-close
   hash-chain validation.
5. The Unity `1e-5` right/bottom-only canonicalization bound, and rejection
   of material/non-finite/negative/degenerate boxes.
6. No real capture, threshold, or geometry change; no real A3 artifact
   created during implementation.

Do not run the real `reanalyze-a3` or `close` against the real session
during review. Keep implementation read-only.

## Round 5 — independent review (Recovery Amendment A3: bbox-schema reanalysis): PASS

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-28
Candidate: `28b9e84`, range `5ffacd9..28b9e84`
Verdict: **PASS**

### Scope of this round

Focused review per the Round 5 handoff above, against the accepted "Recovery
Amendment A3" text in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` (Fable
recommendation + user authorization, and Codex
`ACCEPTED_WITH_BINDING_CLARIFICATIONS`, both 2026-07-28). Confirmed via
`git diff --stat 5ffacd9..28b9e84` that the code diff touches only
`Assets/TetheredTracking/Scripts/P1DetectScouting.cs` (Unity writer
canonicalization), `tools/run_detector_scouting.py` (dual-schema parser,
reanalysis/close lifecycle), `tests/fixtures/p1_detect_scouting_truth_frame_0000000312.json`
(new real fixture), two test files, and docs — `CoverageEvaluator.cs`, the
gimbal driver, `TetheredGimbal.cs`/`GimbalCommandReceiver.cs`, and the entire
Python re-anchor runtime carrier are untouched, so Rounds 1–4's findings
were not re-litigated.

### What was checked

1. **Read every changed file in full.** `normalize_box` (new), the rewritten
   `intersection_over_union`/`_cosine_or_none` call sites, `analyze_session`'s
   new optional redirection parameters, the new `_create_or_validate_document`
   helper, `reanalyze_a3_session` and the updated `close_session`, plus
   `P1DetectScoutingTruthWriter`'s new `TryCanonicalizeBox`.
2. **Dual-schema parser correctness, hand-traced.** `normalize_box` accepts
   only a `Mapping` whose key set is *exactly* `{x, y, width, height}` (both
   directions of the set-equality check, so missing keys, extra keys, and
   wrong keys are all rejected), or a non-`str`/`bytes`/`bytearray`
   `Sequence`; every extracted value must be `(int, float)` and explicitly
   *not* `bool` (Python's `bool` is an `int` subclass, so this exclusion is
   load-bearing, not redundant) before delegating numeric/range validation to
   the pre-existing, unchanged `_validate_box`. Traced both call sites
   (`intersection_over_union`, `_cosine_or_none`) and confirmed every truth
   box (target and each distractor) now flows through this single shared
   entry point — there is no second, unpatched box-parsing path left in the
   file (`grep -n "_validate_box(" tools/run_detector_scouting.py` shows only
   the one call inside `normalize_box` itself plus the pre-existing,
   unrelated `bind_reference` operator-entered box). `_cosine_or_none`'s
   `except (CropInvalid, TypeError, ValueError)` still correctly demotes a
   `None` distractor box (not a `Mapping`/`Sequence` at all) to
   `CROP_INVALID` exactly as it did before this diff — read this specific
   path since a regression here would have silently broken the pre-existing,
   already-reviewed null-distractor handling.
3. **Real fixture provenance, verified independently, not trusted.**
   Independently hashed `tests/fixtures/p1_detect_scouting_truth_frame_0000000312.json`
   myself: SHA-256 `a661652b…7a1`, matching both the evidence doc's claim and
   the value hard-coded in `test_real_capture_truth_fixture_is_byte_exact_and_object_parses`.
   Cross-checked its content against the **real, still-on-disk** immutable
   capture at
   `runtime/p1-detect-scouting/p1-detect-001-scout-1/truth/frame_0000000312.json`
   — byte-identical (confirmed via `diff`), so this is genuinely the real
   capture's own sidecar, not a look-alike hand-written file. This directly
   satisfies binding requirement 5 ("byte-for-byte real fixture") rather than
   trusting the claim.
4. **Create-once identity chain and canonical-result immutability, hand-traced
   then empirically proven against the real capture (see §5 below).**
   `reanalyze_a3_session` re-hashes `scouting-result.json` fresh on every call
   (never a cached/trusted value) and requires it to equal the caller-supplied
   `supersedes_result_sha256` before doing anything else; the plan, versioned
   result, and supersession receipt all live at distinct paths
   (`reanalysis-bbox-schema-v2.json`, `scouting-result-bbox-schema-v2.json`,
   `supersession-bbox-schema-v2.json`) and are never written to
   `scouting-result.json`. `_create_or_validate_document` makes plan/receipt
   writes idempotent-safe (a second call with the *same* content is a no-op
   read-back; a second call with *different* content — e.g., a different
   `supersedes_result_sha256` — fails closed with `ValueError`), which closes
   an obvious "what if this is re-run" question without needing a second
   destructive create-once. `close_session(analysis_id=None)` now refuses
   with `RuntimeError` the instant `reanalysis-bbox-schema-v2.json` exists
   on disk, closing binding-clarification 1's "不允许旧 close 路径把无效结果签成
   A3 completion" requirement — verified this guard fires *before* any file
   is read/written by that path (checked immediately after `_load_session`).
   `close_session(analysis_id="bbox-schema-v2")`'s supersession-receipt check
   re-derives all four hashes (`superseded_result_sha256`,
   `reanalysis_result_sha256` on both the receipt and the result's own
   `analysis_identity`) from the **current on-disk bytes** at close time, not
   from values cached at reanalysis time — this is a real defense against the
   canonical result or the A3 result being tampered with between reanalysis
   and close, not just a formality.
5. **Unity write-side canonicalization, hand-traced then test-verified.**
   `TryCanonicalizeBox` only relaxes the right/bottom-endpoint check (never
   `x`/`y`/negative/non-finite/non-positive-size, which stay at zero
   tolerance exactly as before); it accepts overflow only up to
   `BoundaryRoundoffTolerance = 1e-5`, then clamps `width`/`height` down to
   `1 - x`/`1 - y` and re-validates through the unchanged `ValidBox`, so a
   box that clamps to zero or negative size (e.g. `x == 1.0` exactly) still
   correctly fails closed rather than silently becoming a degenerate
   zero-area box. Read `TruthWriterCanonicalizesOnlyBoundaryRoundoff`: a
   `1e-7` bottom overflow is accepted and the stored box's `y+height <= 1`
   afterward; a `1e-3` bottom overflow on the very next frame still throws
   `invalid_scouting_distractor_truth`. This matches binding clarification 2's
   "微小越界接受规范化 / 实质越界仍拒绝" exactly, and matches the amendment's own
   stated scope (right/bottom endpoints only, `1e-5` cap).
6. **Root-cause corroboration against the real capture, not just the
   evidence doc's narrative.** Read the real, still-on-disk
   `runtime/p1-detect-scouting/p1-detect-001-scout-1/scouting-result.json`
   myself: SHA-256 `c7876364…f8b4` (matches the claimed canonical-invalid
   hash exactly), `recall = {hits:0, denominator:45, missing_pair_misses:18,
   value:0.0}`, and `embedding.target_cosine.count = 0` /
   `embedding.distractor_cosine.count = 0` — independently confirming the
   claimed defect (all 27 `REMOTE_VISIBLE` samples produced zero embedding
   evidence) directly from the preserved artifact, not from Codex's
   description of it.
7. **Empirical end-to-end verification against the real captured data, in an
   isolated sandbox — the strongest check in this round.** Reading the code
   and rerunning hand-built-fixture tests proves the parser is internally
   consistent, but does not by itself prove the fix actually unlocks the
   real, already-broken capture's embedding evidence. Rather than trust that
   inference, I copied the real `runtime/frames/`,
   `runtime/p1-detect-scouting/p1-detect-001-scout-1/`, and
   `runtime/p1_detect_scouting_session.json` byte-for-byte into an isolated
   scratch directory outside the repo (verified byte-identical via `diff -rq`
   and `sha256` before proceeding), then ran the real
   `reanalyze_a3_session(...)` — with the actual pinned YOLOE/DINOv2 models,
   not fakes — against that **isolated copy only**, exactly the same
   technique Round 2 used with an isolated `git worktree` to prove a fix
   empirically rather than by inspection alone. Results, on the real
   captured images:
   - `recall` stayed `{hits: 0, denominator: 45, value: 0.0,
     missing_pair_misses: 18}`, i.e. unchanged from the canonical invalid
     result — confirming the evidence doc's claim that the recall direction
     was never caused by the schema bug (all 27 remote frames independently
     report zero YOLOE proposals at that range, an unrelated, pre-declared
     far-range detectability limitation).
   - `embedding.target_cosine` went from `count: 0` (broken) to **`count: 27,
     min: 0.313, median: 0.398, max: 0.527`** — real, finite, non-degenerate
     DINOv2 cosine similarities computed from the real captured crops. This
     is direct, empirical proof that the dual-schema fix genuinely unlocks
     the previously-empty embedding evidence on the actual data this
     recovery exists to recover, not just on synthetic test fixtures.
   - I then also ran the real `close_session` lifecycle in the same sandbox:
     the legacy `close_session(runtime)` correctly raised
     `RuntimeError("A3 reanalysis plan exists; canonical result cannot be
     closed")`, and `close_session(runtime, analysis_id="bbox-schema-v2")`
     succeeded with a correct hash-chain-validated completion document and
     removed the active-session marker — proving the full lifecycle, not
     just `reanalyze_a3_session` in isolation, on real data.
   - **Confirmed the real `runtime/` was untouched throughout**: before and
     after both sandbox runs, `runtime/p1-detect-scouting/p1-detect-001-scout-1/scouting-result.json`
     still hashes to `c7876364…f8b4`, the real session directory still
     contains exactly its original eight files (no `completion.json`, no
     `reanalysis-bbox-schema-v2.json`, no `scouting-result-bbox-schema-v2.json`,
     no `supersession-bbox-schema-v2.json`), `git status --short` stayed
     clean, and the sandbox copy was deleted afterward. I did not run the
     real `reanalyze-a3`/`close` against the real session, per the handoff.
8. **Independently reran the standard evidence, not trusting the doc's
   numbers**, with no Unity editor already holding the project:
   - `.venv-track/bin/python -m unittest discover -s tests -v` →
     **109/109 pass** (matches).
   - `uv pip check --python .venv-yoloe/bin/python` → **42/42 compatible**
     (matches).
   - Focused Edit Mode (`-testFilter P1DetectScoutingEditModeTests`) →
     **13/13 pass** (matches).
   - Full Edit Mode (no filter) → **86/86 pass** (matches).
   - Play Mode was not rerun, matching the evidence doc's own claim that
     this candidate does not touch the A2 gimbal driver/plant/capture path
     (confirmed via `git diff --stat`: no Play Mode test file and no
     `CoverageEvaluator.cs`/`TetheredGimbal.cs` changes in this diff) — the
     prior A2 Play Mode 1/1 + 3/3 evidence remains applicable unchanged.
   - `python3 tools/check_docs.py` passes on the disk state I am about to
     write.

### Findings

No blocking findings.

I looked specifically for ways the new dual-schema parser could be tricked
into accepting an out-of-range or wrong-typed box, or for a second unpatched
box-parsing path left in the file that the fix might have missed — found
neither. I also checked whether `_create_or_validate_document`'s
read-then-compare pattern could be raced by concurrent invocations, but this
tool is only ever run as a single sequential manual CLI invocation (not from
the concurrent controller runtime), so a TOCTOU race is not a realistic
concern here, consistent with the rest of this offline tool's existing
design.

**N7 (non-blocking, informational).** The pre-existing, unchanged
`_validate_box` still enforces a strict, zero-tolerance `x + width <= 1.0` /
`y + height <= 1.0` on the Python side; all boundary-roundoff tolerance lives
only in the new Unity-side `TryCanonicalizeBox`. This is a deliberate,
already-reviewed scope choice ("A3 同时纳入写入侧防御", write-side only), not an
oversight — I verified it does not affect the current real capture (every
on-disk truth box I sampled parses cleanly) — but it does mean any *future*
truth producer other than this exact Unity writer version would need to
reproduce the same clamping to stay compatible. Recording for the record,
not requesting action.

### Requirement-to-evidence mapping

| Reviewed item | Evidence | Status |
|---|---|---|
| Exact dual-schema box normalization, shared IoU/embedding boundary | `normalize_box`, hand-traced call sites, `test_box_parser_accepts_only_exact_object_or_four_number_sequence` | Verified |
| Byte-for-byte real-capture fixture | Independently hashed and diffed against the real on-disk sidecar | Verified |
| Canonical result immutability + create-once plan/result/supersession/completion chain | Hand-traced `reanalyze_a3_session`/`close_session`; empirically re-verified in an isolated sandbox against real data | Verified |
| Legacy-close refusal once A3 begins; A3-close hash-chain validation | Hand-traced guard ordering; empirically exercised both paths in the sandbox | Verified |
| Unity `1e-5` right/bottom-only canonicalization; material/degenerate rejection | `TryCanonicalizeBox`, `TruthWriterCanonicalizesOnlyBoundaryRoundoff` (rerun: 13/13, 86/86) | Verified |
| No real capture/threshold/geometry change; no real A3 artifact from implementation | Diffed frozen constants (unchanged); confirmed real `runtime/` byte-identical before/after review | Verified |
| Fix genuinely resolves the reported defect on real data | Isolated-sandbox `reanalyze_a3_session` against the real capture: embedding count 0→27 | Verified empirically |
| Python + Edit Mode tests genuinely cover claimed behavior | Reran all myself: 109/109, 13/13, 86/86 | Verified |

### Re-review result

**PASS.** `P1-DETECT-001` Recovery Amendment A3 stable candidate `28b9e84`
is independently verified against the accepted amendment text and Codex's
two binding clarifications: the dual-schema parser is exact and shared by
both IoU and embedding with no second unpatched path, the byte-for-byte real
fixture genuinely comes from the real capture, the canonical invalid result
`c7876364…f8b4` is provably immutable and unclosable via the legacy path
once A3 begins, the A3 close path validates the full hash chain against
current on-disk bytes, and the Unity write-side clamp accepts only
sub-`1e-5` right/bottom roundoff while still rejecting material or
degenerate overflow. Beyond static review, I ran the real recovery pipeline
end-to-end — including the real pinned models — against an isolated,
byte-verified copy of the actual immutable capture, and confirmed the fix
concretely turns the previously-empty embedding evidence (0 samples) into 27
real, finite cosine scores while leaving the (unrelated, detector-driven)
0/45 recall unchanged; the real `runtime/` session was byte-identical before
and after, and the sandbox was discarded. All Python and Edit Mode tests
pass under an independent rerun (109/109, 13/13, 86/86); Play Mode is
correctly unaffected and was not required to be rerun. One non-blocking,
informational note (N7) requires no action. This closes the Sonnet
independent-review gate for Recovery Amendment A3. Remaining before `DONE`:
Codex may now run the real `reanalyze-a3`/`close` against the actual
session and route the completed recall/embedding report to the user's
Option B decision, then qualification and `UT-P1-DETECT-001-001` — none of
which I ran. Return to Codex.

## Round 6 handoff — Clock Amendment A4

This subsection is a Codex handoff, not an independent verdict.

Implementation candidate: `cd684fcc333a4aee1a9949950c942585df691af5`
(`cd684fc`), based on the pushed blocker record `c4e3711`. The commit after
`cd684fc` is handoff-only documentation and must also be included when checking
the accepted requirement/evidence/status consistency.

Review Clock A4 in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` and
`docs/evidence/P1-DETECT-001-clock-protocol-repair.md`, then independently
inspect:

- `Assets/TetheredTracking/Scripts/SensorFrameWriter.cs` and its EditMode
  tests: ordinary v3 must use `Stopwatch.GetTimestamp()/Frequency` with exact
  `system-stopwatch/v1`; active RATE-002 must remain v2 on its unchanged
  process-relative clock.
- `controller/sensor_protocol.py`, `controller/track_loop.py` and
  `controller/reanchor_runtime.py`: legacy/wrong/non-finite clocks must reject
  before tracker/model/run side effects, and the runtime entry must repeat the
  check. RATE-002 + re-anchor must reject before runtime access.
- Both scouting readers and tests: historical v1 remains readable offline;
  v3 is accepted only with its exact clock contract; frozen Gate 0 behavior is
  unchanged.
- The complete diff `c4e3711..cd684fc`: no model identity/weights, gate
  threshold, stale limit, main metric, Unity-truth boundary, scene geometry,
  RATE-002 evidence or qualification gate may have changed.

Implementer evidence is Python 143/143, focused EditMode 26/26, full EditMode
110/110, PlayMode 3/3, plus a five-sample cross-process clock bracket on the
frozen macOS/Unity Mono host. Reproduce proportionate checks rather than
trusting these counts. Do not start a real qualification, reuse qual-1, or
sign user Unity validation. Record findings and an independent Round 6
verdict below this handoff, then return to Codex.

### Round 6 (Clock Amendment A4, `cd684fc` + handoff-only `8554e75`): PASS_WITH_NOTES

Fresh context. Read the accepted A4 text in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` (lines 938–977)
and the evidence doc, then read every changed file in
`c4e3711..cd684fc` directly rather than trusting the implementer summary.
Implementation code was not modified.

1. **Clock separation, no epoch mixing.** `SensorFrameWriter.Capture()`
   computes `captureMonotonic` once per frame from a single ternary keyed on
   the same `rateStudyV2` flag used to pick the metadata class: RATE-002
   active → `Time.realtimeSinceStartupAsDouble` wrapped in the unchanged
   `FrameMetadataV2`; otherwise → the new
   `HostMonotonicSeconds() = Stopwatch.GetTimestamp()/Stopwatch.Frequency`
   wrapped in `FrameMetadataV3`, which carries a field-initialized
   `capture_monotonic_clock_id = "system-stopwatch/v1"`
   (`Assets/TetheredTracking/Scripts/SensorFrameWriter.cs:73-91,178-186,254-260`).
   Ordinary frames can no longer be emitted as bare v1 — `BuildMetadata`'s
   only two branches are `FrameMetadataV2`/`FrameMetadataV3`. On the Python
   side `controller/sensor_protocol.py` centralizes the schema/clock-id/
   finite/non-negative/non-bool check in one function
   (`validate_system_monotonic_frame`), and `FrameRepository.load()` only
   invokes it when `expected_frame_schema == FRAME_SCHEMA` (v3, i.e. never
   for the unchanged RATE-002 v2 path). `reanchor_runtime.py`'s
   `age = self.monotonic() - source_capture` (Python `time.monotonic()`,
   unchanged default) now only ever consumes a value that passed that same
   validator. No path mixes a v2/process-relative value into a v3/host
   comparison or vice versa.
2. **Reject before side effects, and again at runtime.** In
   `controller/track_loop.py:run_tracker`, the RATE-002/re-anchor mutual
   exclusion raises before `FrameRepository` is even constructed; frame
   load + `_validate_frame_scenario` run immediately after, strictly before
   `create_tracker(...)`, before `ReanchorRuntime(...)`, before `run_id`
   allocation, and before `RunLogger(...)` (which eagerly `mkdir`s the run
   directory in `controller/run_log.py:430`). I didn't just read this order —
   `tests/test_track_loop.py`'s new
   `test_cli_rejects_legacy_init_frame_before_tracker_or_run_creation` mocks
   `create_tracker` and asserts it is never called, and asserts
   `runtime/runs` never gets created, for a legacy-v1 init frame; a sibling
   test does the same for the RATE-002+re-anchor combination. At runtime,
   `ReanchorRuntime.after_frame` (called every processed frame at
   `track_loop.py:358`, and once more from inside `initialize()` for the
   first frame) now calls the same centralized validator instead of the old
   bare `float(bundle.metadata["capture_monotonic_s"])` that produced the
   original `KeyError`. `tests/test_reanchor.py`'s new
   `test_runtime_rejects_legacy_or_mismatched_capture_clock` directly drives
   `after_frame` with wrong schema, wrong clock id, and NaN, and asserts all
   three reject with the expected message.
3. **Historical v1 stays read-only; Gate 0 unaffected.** Both offline
   scouting readers (`tools/run_detector_scouting.py:_frame_metadata`,
   `tools/run_scene004_scouting.py:_frames`) now accept
   `{v1, v3}` schemas; the monotonic/clock-id validator only runs on the v3
   branch, so v1 records (all of Gate 0's frozen scout-1 bytes) take exactly
   the code path they always did — no new validation is imposed on them, and
   the scenario/frame-id checks below are unchanged. Each reader has a new
   test that writes a v1 record, confirms it reads, mutates it to a valid
   v3 record, confirms it still reads, then breaks the v3 clock field and
   confirms rejection
   (`test_scouting_reader_accepts_historical_v1_and_validated_v3`,
   `test_frame_reader_accepts_historical_v1_and_validated_v3`).
4. **No model/threshold/metric/truth/scene/qualification drift.** Read the
   complete `c4e3711..cd684fc` diff file-by-file (18 files). The only
   non-doc, non-test production files are `SensorFrameWriter.cs`,
   `sensor_protocol.py` (new), `track_loop.py` and `reanchor_runtime.py`,
   and every change in them is the clock contract described above — no
   detector/embedder weights, gate thresholds, `maximum_result_age_s`,
   metric definitions, Unity-truth boundary, scenario geometry, RATE-002
   protocol semantics, or qualification acceptance criteria are touched.
   `docs/current-status.md`, `docs/implementation-status.md`,
   `docs/phase1-single-drone-design.md` and `runtime/README.md` accurately
   describe the implemented contract; the handoff-only commit `8554e75`
   only adds this review's scope section and rotates one old batch entry
   into `docs/archive/current-status-2026-07.md` (checked with
   `git diff cd684fc..8554e75` — nothing under `docs/reviews/` was deleted,
   only appended to).
5. **Reran every number myself, none trusted from the evidence doc.**
   `.venv-track/bin/python -m unittest discover -s tests -v` → **143/143**
   pass, including the four new/modified clock tests. `.venv-yoloe`
   (real DINOv2/YOLOE stack) reruns of the individual suites the evidence
   doc cites separately: `test_reanchor.py` **18/18**,
   `test_detector_scouting.py` **14/14**, `test_scene004_scouting.py`
   **22/22** — all match exactly. Unity `6000.4.1f1` batchmode
   (`-testFilter TetheredTracking.Tests`, output written outside the repo):
   EditMode **110/110** (including `SensorMetadataV3_...`,
   `SharedHostMonotonicClock_...`, and the untouched `SensorMetadataV2_...`,
   all `Passed`), PlayMode **3/3** — both match. `python3 tools/check_docs.py`
   and `git diff --check` pass; `git status` stayed clean throughout (no
   Unity output written into the repo, implementation code untouched).

**One real, non-blocking finding.** `tools/benchmark_reanchor.py` — the
same real-model re-anchor latency benchmark a prior round independently
reran as evidence (`docs/reviews/P1-DETECT-001.md` round 3, "`python -m
tools.benchmark_reanchor --frames 60 --rate-hz 20`... p50/p95/max
`8.687/10.500/10.545 ms`") — was not updated for A4 and is now unconditionally
broken: its synthetic `SyntheticFrame.metadata` dict
(`tools/benchmark_reanchor.py:49-66`) has no `schema_version` or
`capture_monotonic_clock_id`, so the very first call into
`ReanchorRuntime.initialize()` → `after_frame()` now raises
`ValueError: reanchor requires sensor frame schema 'tethered-sensor-frame/v3';
received None`. I reproduced this directly:
`.venv-yoloe/bin/python -m tools.benchmark_reanchor --frames 50 --rate-hz 5`
fails with exactly that traceback. This tool is unreachable from the
qualification/tracking path and no currently open gate depends on it (it has
no test coverage of its own, which is how this slipped through 143/143 green),
so it does not block this candidate. But it is real evidence tooling that a
future round (M2/M5, or any future re-anchor latency re-check) will need
working — Codex should give its synthetic frame metadata a
`"schema_version": "tethered-sensor-frame/v3"` and matching
`"capture_monotonic_clock_id": "system-stopwatch/v1"` before it's needed
again.

**Verdict: PASS_WITH_NOTES.** Clock A4 is implemented exactly as accepted:
v3/v2 clock selection never mixes epochs, every re-anchor entry (CLI
preflight and runtime `after_frame`) rejects legacy/wrong/non-finite clocks
before any model/run side effect and is now directly tested for that
ordering (not just for the rejection itself), historical v1 offline reading
is unchanged including Gate 0, and the full diff introduces no other
model/threshold/metric/truth/scene/qualification change. The one finding
(`tools/benchmark_reanchor.py`) is a real but isolated regression in an
offline dev tool with no path into qualification — it does not need to block
this stable candidate. Codex may close this Sonnet gate; qualification
`p1-detect-001-qual-1` stays consumed and a fresh qualification ID may now be
prepared and run under the repaired v3 protocol. Return to Codex.

### Codex disposition of Round 6 note

This is an implementer disposition, not a second independent verdict.
`tools/benchmark_reanchor.py` now imports the central v3 schema/clock constants
for every synthetic frame; `tests/test_benchmark_reanchor.py` locks that
contract. Full Python passes 144/144, and the real-model 45-frame/5 Hz
benchmark completes with cadence 4/4, no fatal reason and a clean worker
close. The fix is offline evidence-tool compatibility only and does not reopen
Clock A4's passed production candidate.

## Round 7 handoff — Release Boundary Amendment A5

Status: `AWAITING_SONNET_RELEASE_A5`

This subsection restates the Codex handoff (`docs/current-status.md` Active
handoffs table and `docs/evidence/P1-DETECT-001-release-boundary-repair.md`),
not an independent verdict.

Implementation candidate: `705c4428e86998a152ab3e7b276be202c9a263ae`
(`705c442`); the range since the last Sonnet-verified point is
`cd684fc..705c442` (four commits: the Round 6 handoff-only commit already
reviewed, the benchmark-tool note closure, the qual-2 failure record, and the
A5 implementation itself). Qual-2 is permanently `PROTOCOL_INVALID_RELEASE_
BOUNDARY`; the user explicitly authorized this narrow repair. Verify:

1. Exact ready/command/active/ack/provenance byte/hash and create-once chain.
2. Unix + host-monotonic ordering and first-v3-frame origin agreement between
   Python and Unity.
3. HOLD exclusion from observation/control, re-anchor, logs, cadence/duration
   and all `CoverageEvaluator` truth aggregates.
4. Dual simulation/monotonic-wall completion and metrics-origin fail closure.
5. RATE-002/v2 isolation, historical v1 scouting compatibility and unchanged
   model/threshold/metric/scene/hardware scope.
6. Full diff audit that Unity truth remains confined to `CoverageEvaluator`.

Do not prepare or run `p1-detect-001-qual-3` before the focused verdict
passes. Keep implementation read-only.

## Round 7 — independent review (Release Boundary Amendment A5): REWORK_REQUIRED

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-29
Candidate: `705c442`, range `cd684fc..705c442` (handoff-only `e548b09` also
read for doc-state consistency)
Verdict: **REWORK_REQUIRED**

### Scope of this round

Focused review per the Round 7 handoff above, against the accepted "Release
Boundary Amendment A5" text in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md` (lines 979–1041)
and design v0.3.8
(`docs/phase1-single-drone-design.md`). Confirmed via `git diff --stat
cd684fc..705c442` that the only non-doc, non-test production files touched
are `controller/qualification_protocol.py` (new), `controller/track_loop.py`,
`controller/run_log.py`,
`Assets/TetheredTracking/Scripts/QualificationReleaseGate.cs` (new), and
`Assets/TetheredTracking/Scripts/CoverageEvaluator.cs`; no `config/*.json`
scenario/threshold file changed, so Rounds 1–6's findings were not
re-litigated. Also confirmed `705c442..e548b09` (the handoff-only commit at
current `HEAD`) touches only docs.

### What was checked

1. **Read every changed/new file in full**, not the diff alone:
   `controller/qualification_protocol.py` (753 lines), the full post-diff
   `controller/track_loop.py` (init/`process_available`/`_protocol_fields`/
   `run_tracker`/CLI), `controller/run_log.py`'s `build_summary`/
   `finalize_run`, `Assets/TetheredTracking/Scripts/QualificationReleaseGate.cs`
   (all 284 lines), and `CoverageEvaluator.cs`'s diff plus enough surrounding
   unchanged code to see exactly how the new gate is wired into
   `Start()`/`OnFramePublished`/`OnObservationPublished`.
2. **Hand-traced the create-once ready→command→active→ack→provenance chain.**
   `_manifest`/`_validate_ready`/`_validate_command`/`_active_value`/
   `_publish_active`/`validate_provenance` in `qualification_protocol.py` bind
   every stage to the SHA-256 of the previous stage's exact bytes (not a
   re-serialized copy), `request_release` is idempotent (a second call with
   the same run_id re-validates and re-publishes the same content rather than
   mutating), and `_publish_active`'s hardlink-based `create_once_json` at
   `runtime/p1_detect_qualification_release.json` correctly refuses a second,
   *different* concurrently active qualification run's marker
   (`FileExistsError` → `"another qualification active marker occupies the
   runtime slot"`). `validate_provenance` re-derives every hash from
   on-disk bytes at call time rather than trusting cached values, so tampering
   between acknowledgement and finalization is caught
   (`test_provenance_rejects_ack_hash_tampering`, independently reread and
   understood, not just rerun).
3. **Unix + host-monotonic ordering and first-v3-frame origin agreement,
   independently re-derived, not trusted from the evidence doc's prose.**
   Python's `QualificationReleaseLifecycle.record_fields` is called once per
   processed frame, in strict frame-id order, including backlog/catch-up
   frames (`TrackLoop.process_available`'s per-bundle loop calls
   `self._protocol_fields(bundle)` — which delegates to `record_fields` —
   for *every* bundle in the batch, not just the latest); the first frame
   whose `capture_monotonic_s >= command.not_before_capture_monotonic_s`
   latches `_acknowledge()` exactly once (`self.release_ack is None` guard),
   and every later frame in the same or a later batch reuses that latch.
   Unity's `QualificationReleaseGate.EvaluateFrame` implements the
   byte-for-byte identical rule (`frame.CaptureMonotonicSeconds <
   marker.not_before_capture_monotonic_s` on the *same* shared-host-monotonic
   field written into the *same* per-frame JSON sidecar Python reads), so
   both sides are deterministic functions over the identical ordered
   `(frame_id, capture_monotonic_s)` sequence and cannot disagree on which
   physical frame is the release origin, given the retained-frame window is
   sufficient for Python's catch-up to see everything Unity's real-time
   evaluator saw (already an accepted contract from earlier SCENE-004/DETECT
   rounds, unchanged here).
4. **HOLD exclusion, verified by reading and by an existing end-to-end
   test.** In `TrackLoop.process_available`, `released` passed into
   `reanchor_runtime.after_frame` is `protocol_fields.get("phase") ==
   "measurement"`, and publication (`_publish_latest`, i.e. the
   `tracking_observation.json`/`gimbal_command.json` writers) is skipped
   unless `is_latest and qualification_measurement`. On the Unity side,
   `ApplyQualificationDisposition` returns `false` (blocking `RecordFrame`/
   truth aggregation) for `Hold`/`ResetAndHold`, and
   `qualificationReleaseGate.AllowsObservation` independently gates
   `OnObservationPublished`. `tests/test_track_loop.py`'s new
   `test_qualification_release_excludes_paused_backlog_from_all_origins`
   exercises this for real through `TrackLoop.initialize`/
   `process_available`: I reran it and independently confirmed (by reading,
   not just trusting green) that `reanchor.after_calls == [(1, True, False),
   (2, True, True), (3, True, True)]`, `published_observation == [False,
   False, True, True]`, and `frames[2]["measurement_elapsed_s"] ==
   frames[2]["measurement_wall_elapsed_s"] == 0.0` — a real proof of the
   exact-frame HOLD→measurement cutover, not a synthetic assertion on
   internal state alone.
5. **Dual simulation/monotonic-wall completion and metrics-origin fail
   closure, hand-traced and test-verified.** `TrackLoop.complete` for a
   qualification lifecycle requires *both*
   `elapsed_simulation_s >= planned_duration_s` *and*
   `last_measurement_wall_elapsed_s >= planned_duration_s` — confirmed
   `last_measurement_wall_elapsed_s` is only ever populated from
   `protocol_fields["measurement_wall_elapsed_s"]`, itself only non-`None`
   once `record_fields` has latched a release, so a run cannot spuriously
   "complete" on stale/pre-release timing. `run_tracker`'s `finally:` block
   calls `qualification_lifecycle.validate_metrics(metrics,
   planned_duration_s=...)` before ever snapshotting `metrics.json`, and
   `validate_metrics` requires an *exact* field-for-field match (with a
   `1e-6` float tolerance, `set(identity) != set(expected)` rejecting extra
   fields) between the metrics document's `qualification_release` block and
   the Python-side `self.release_ack`-derived identity — confirmed via
   `test_metrics_fail_closed_without_matching_unity_release_origin` (reran)
   that a metrics document lacking this identity is rejected before any
   snapshot. `finalize_run` independently re-validates the *entire*
   ready/command/active/ack/provenance chain from disk a second time (not
   reusing the in-memory `release_ack`) before computing
   `actual_wall_duration_s`/`release_monotonic_s`, matching the same
   defense-in-depth pattern already established for RATE-002's
   `validate_provenance` call in the same function — read both branches
   side by side to confirm the qualification branch is structurally
   identical, not a weaker copy.
6. **RATE-002/v2 mutual exclusion, checked on both sides.**
   `TrackLoop.__init__` raises if both `rate2_lifecycle` and
   `qualification_lifecycle` are set; `run_tracker`/`main`'s CLI validation
   raises before any runtime/model access if `--qualification-release-barrier`
   is combined with `--rate2-session`; `run_log.finalize_run` raises
   `INVALID_RELEASE: multiple release protocols in manifest` if a manifest
   somehow carries both keys. On the Unity side,
   `CoverageEvaluator.OnFramePublished` throws
   `multiple_release_protocols_are_active` if `scenario.ExperimentController.
   IsActive` and the qualification disposition are simultaneously non-trivial.
   Historical v1 scouting compatibility is untouched (confirmed via
   `git diff --stat` that `tools/run_detector_scouting.py`,
   `tools/run_scene004_scouting.py` and their readers are absent from this
   diff).
7. **Independently reran every number myself, none trusted from the evidence
   doc**, using an isolated `git worktree` at the exact candidate commit for
   the Unity reproduction described in finding B2 below (removed after use;
   `git status --short` on the main checkout stayed clean throughout, and the
   two Unity auto-upgraded files
   (`ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json`,
   `Packages/packages-lock.json`) that `6000.4.10f1` rewrites on open were
   reverted after each run, matching the evidence doc's own noted mitigation):
   - `.venv-track/bin/python -m unittest discover -s tests -v` → **151/151
     pass** (matches).
   - `.venv-yoloe` focused reruns: `test_reanchor.py` **18/18**,
     `test_detector_scouting.py` **14/14**, `test_scene004_scouting.py`
     **22/22** — all match.
   - `uv pip check --python .venv-yoloe/bin/python` → **42/42 compatible**
     (matches; no model/package artifact touched by this diff).
   - Unity `6000.4.10f1` batchmode (no editor holding the project lock;
     `6000.4.1f1`'s licensing handshake was still unavailable, matching the
     evidence doc's own noted environment constraint): focused
     `-testFilter QualificationReleaseEditModeTests` → **3/3 pass**; full
     EditMode (no filter) → **113/113 pass**; full PlayMode → **3/3 pass** —
     all match.
   - `python3 tools/check_docs.py` and `git diff --check` both pass on the
     disk state at `HEAD` (`e548b09`).
   - Confirmed no qualification session/run artifact exists in `runtime/`
     before or after this review
     (`find runtime -iname "*qualif*"` shows only the unrelated, pre-existing
     `runtime/rate-study/P1-M2-RATE-002-B2/qualification.json`); I did not
     prepare or run `p1-detect-001-qual-3`, per the handoff.

### Findings

#### Blocking

**B2. A stale/leftover qualification active-pointer marker
(`runtime/p1_detect_qualification_release.json`) silently or fatally affects
*any* later `CoverageEvaluator` session, not only the qualification attempt
that created it — and A5 gives this file no way to be recognized as stale.**

`CoverageEvaluator.Start()` now unconditionally constructs
`qualificationReleaseGate = new QualificationReleaseGate(RuntimePaths.Root,
config.scenario_id)`
([CoverageEvaluator.cs:182](Assets/TetheredTracking/Scripts/CoverageEvaluator.cs:182))
for *every* scenario config, and `OnFramePublished` unconditionally calls
`qualificationReleaseGate.EvaluateFrame(frame)`
([CoverageEvaluator.cs:213](Assets/TetheredTracking/Scripts/CoverageEvaluator.cs:213))
on every published frame, in every scene. `QualificationReleaseGate.TryArm()`
([QualificationReleaseGate.cs:157-225](Assets/TetheredTracking/Scripts/QualificationReleaseGate.cs:157))
arms the moment `runtime/p1_detect_qualification_release.json` exists and its
hash-bound chain validates — it has no concept of "this marker belongs to a
different, already-finished or abandoned attempt" and no concept of "this
particular Unity session was actually configured to expect a qualification
barrier." By design (A5 §7, "active marker仅在...成功后清理"), this exact
file is *only* ever cleared on full success — every failed or aborted
attempt leaves it behind on disk permanently, by design. Given this project
has already produced two real qualification-style failures (qual-1, qual-2)
under two different protocol generations, a third failure leaving this
marker behind is not a hypothetical.

Two distinct, concrete failure modes follow, both empirically reproduced
(see below), depending on the *next* Unity session's `scenario_id`:

- **Any scenario other than `p1-scene-004`** (`scenario.default.json`,
  `scenario.rate-study-5hz.json`/`20hz.json`, `scenario.scene-validation.json`,
  `scenario.p1-detect-scouting.json` — confirmed these are real, distinct,
  currently-used scenario ids via `config/scenario*.json`): `TryArm()`'s
  `ValidateMarker`
  ([QualificationReleaseGate.cs:227-249](Assets/TetheredTracking/Scripts/QualificationReleaseGate.cs:227))
  rejects `value.scenario_id != expectedScenarioId` and **throws**
  `InvalidOperationException("qualification_active_marker_run_invalid")` on
  the very first frame that `CoverageEvaluator` ever publishes. This is not
  caught anywhere in the call chain, so it propagates out of the
  `FramePublished` event — i.e. **any Unity Play session for any other
  scenario, including plain regression testing and Play Mode tests that go
  through the real bootstrap, breaks with an unhandled exception** as long
  as this one file exists anywhere in `runtime/`, with no message connecting
  the crash to its actual cause.
- **`scenario_id == "p1-scene-004"` for a session that is *not* the intended
  qualification run** (e.g. a plain, non-`--qualification-release-barrier`
  manual/regression tracker session against the same geometry — a real,
  already-used mode per the SCENE-004 scouting/qualification history): the
  marker's `scenario_id` matches, so `TryArm()` succeeds against a foreign
  run's identity. The gate silently arms, immediately or shortly resets that
  session's evaluator aggregation (`ApplyQualificationDisposition` →
  `ResetAggregation()`), and stamps `metrics.json`'s `qualification_release`
  block with the **stale run's own `run_id`/`command_id`** — an unrelated
  session's output is silently mislabeled with foreign provenance, with no
  error, no log line, and no test anywhere that would catch it.

**Empirically reproduced, not just inferred from reading.** I added two
temporary EditMode tests to an isolated `git worktree` at commit `705c442`
(never touching the reviewed working tree; worktree removed after use):

- Constructing a second `QualificationReleaseGate` with a *different*
  scenario id (`"rate-study-20hz"`) against the same on-disk marker/command
  chain used by the existing
  `Gate_ResetsAtMarkerAndUsesFirstFrameAtHostBoundary` fixture: calling
  `EvaluateFrame` **threw `InvalidOperationException`**, confirming the
  cross-scenario crash.
- Constructing a second `QualificationReleaseGate` with the *same*
  `"p1-scene-004"` scenario id against that same foreign marker, then
  evaluating a frame already past the stale boundary: it returned
  `ResetAndMeasure` and `MetricsOrigin.run_id` reported the foreign
  `"p1-detect-001-qual-99"` identity — confirming the silent same-scenario
  hijack.

Both temporary tests **passed** (i.e. both failure modes reproduce exactly
as analyzed) under Unity `6000.4.10f1` batchmode. The temporary test file
and the worktree were discarded after this confirmation; no change was made
to the reviewed candidate.

**This is not a novel category of risk for this codebase — the sibling
RATE-002 protocol already defends against exactly this class of failure, and
A5 does not carry the same defense over.**
`RateStudyExperimentController.Initialize`
([RateStudyExperimentController.cs:55-91](Assets/TetheredTracking/Scripts/RateStudyExperimentController.cs:55))
calls `HasStaleRuntimeSlot(runtimeRoot)`
([RateStudyExperimentController.cs:446-453](Assets/TetheredTracking/Scripts/RateStudyExperimentController.cs:446))
— an explicit check for leftover files from a prior incomplete attempt — and
safely `BlockHold`s (logs a rejection, sets `Hold` state, disables target
motion) rather than proceeding, if any are found; it also safely `BlockHold`s
rather than throwing on a `session.scenario_id != scenarioConfig.scenario_id`
mismatch. `QualificationReleaseGate` has no equivalent staleness check and
fails hard (throw) or fails silent (foreign-identity arm) instead of failing
soft, on the exact analogous inputs.

**Consequence and why this blocks the gate:** this sits squarely in the
review's mandatory scope ("边界条件、失败路径" and "`CoverageEvaluator` truth
aggregates" per the handoff and `docs/collaboration-workflow.md` §4.4). It
does not corrupt a *clean-state* qual-3 attempt's own measurement — the
primary A5 chain itself (items 1–6 above) is correct. But given this
project's own demonstrated two-for-two qualification-failure history, a
third failure under A5 is a real possibility, and if it happens, every
subsequent Unity session for *any other* purpose — including the Play Mode
regression suite Codex/Sonnet themselves rely on to certify future
candidates — would start failing with an unrelated-looking crash, or silently
produce mislabeled data, until someone thinks to delete this one specific,
undocumented file. `runtime/README.md` documents no such precondition.

### Requirement-to-evidence mapping

| Reviewed item | Evidence | Status |
|---|---|---|
| Exact ready/command/active/ack/provenance hash/create-once chain | Hand-traced `qualification_protocol.py`; reran `test_release_is_create_once_and_first_fresh_frame_is_the_only_origin`, tamper tests | Verified |
| Unix + host-monotonic ordering, first-v3-frame Python/Unity agreement | Hand-traced both sides' identical ordered-sequence rule | Verified |
| HOLD exclusion from control/re-anchor/logs/evaluator | Hand-traced + reran `test_qualification_release_excludes_paused_backlog_from_all_origins` | Verified, for the intended single-session flow |
| Dual simulation/monotonic-wall completion + metrics-origin fail closure | Hand-traced `complete`/`validate_metrics`/`finalize_run`; reran fail-closed tests | Verified |
| RATE-002/v2 isolation, no model/threshold/metric/scene drift | `git diff --stat` scope audit; mutual-exclusion checks on both sides | Verified |
| Historical v1 scouting compatibility | Confirmed scouting files absent from this diff | Verified |
| Truth confined to `CoverageEvaluator`, no cross-session leak | Empirically reproduced — **fails**: a stale marker leaks a foreign run's identity/state into an unrelated session (B2) | **Blocking** |
| Python + Unity tests genuinely cover claimed behavior | Reran all: 151/151, 18/18/14/14/22/22, Unity 3/3 focused + 113/113 Edit + 3/3 Play | Verified for what they cover; no test exercises B2's scenario |

### Requested Codex action

1. **Fix B2** before this gate can pass. The exact mechanism is Codex's
   choice, but it must ensure a Unity session that was not specifically
   configured/expecting the qualification barrier cannot be crashed or
   silently mislabeled by a leftover marker from a prior, unrelated attempt —
   e.g. (a) an explicit staleness check mirroring
   `RateStudyExperimentController.HasStaleRuntimeSlot`, refusing to arm
   against a marker whose referenced run is not the one this session was
   told to expect; and/or (b) failing soft to `Ordinary` (matching
   `RateStudyExperimentController.BlockHold`'s philosophy) instead of
   throwing, on any marker/scenario mismatch, so an unrelated scenario is
   never crashed; and/or (c) scoping `QualificationReleaseGate` construction
   itself so it is inert by default and only activated when this specific
   session is deliberately running under the barrier.
2. Add a regression test for both reproduced failure modes (cross-scenario
   throw, same-scenario silent hijack) so a future change cannot reintroduce
   this silently.
3. None of items 1–6 in "What was checked" need further work — do not
   re-litigate them in the next round unless the B2 fix touches that code.
4. Return to the same Sonnet stop point with a new candidate commit. Continue
   to not prepare or run `p1-detect-001-qual-3` until this round closes with
   a `PASS`.

### Re-review result

PENDING — awaiting a fixed candidate from Codex.

## Round 8 handoff — B2 evaluator-session freshness/ownership fix

Status: `AWAITING_SONNET_ROUND_8`

This subsection restates the Codex handoff (`docs/current-status.md` Active
handoffs table and `docs/evidence/P1-DETECT-001-release-boundary-repair.md`
"Round 7 B2 repair"), not an independent verdict.

Implementation candidate: `f1868dd1dcaf269918cc7a666339f709058580db`
(`f1868dd`); range since the Round 7-reviewed candidate is `705c442..f1868dd`
(one code commit plus the Round 7 handoff-only commit `e548b09`, already
covered). Verify:

1. A `QualificationReleaseGate` may arm only when the referenced release
   command's `issued_unix_s` and `not_before_capture_monotonic_s` are both
   strictly later than the current Unity evaluator session's own Unix and
   shared host-monotonic start values, and the marker's scenario matches.
2. A foreign-scenario, older-than-session, structurally invalid, or
   chain-incomplete marker leaves the gate `Ordinary` for that session:
   observations remain allowed, aggregation is untouched, `MetricsOrigin`
   stays `null` — no exception, no reset, no foreign identity.
3. Once a marker passes ownership/freshness admission, the original
   command/manifest/ready hash-binding and tamper rejection remain exactly
   as strict as before (fail closed on any mismatch).
4. The two new permanent regressions
   (`ForeignMarker_IsInertForDifferentScenario`,
   `StaleMarker_CannotHijackSameScenarioSession`) actually reproduce and
   close the two Round 7 findings, not just assert something adjacent.
5. No other file in scope — confirm via `git diff --stat` that
   `controller/qualification_protocol.py`, `controller/track_loop.py`,
   `controller/run_log.py`, and `CoverageEvaluator.cs` are untouched since
   `705c442`, so Round 7's items 1–6 (the release chain itself) do not need
   re-litigating.

Do not prepare or run `p1-detect-001-qual-3` before the Round 8 verdict
passes. Keep implementation read-only.

## Round 8 — independent review (B2 evaluator-session freshness/ownership fix): PASS

Reviewer/role: Claude Sonnet / independent verification
Date: 2026-07-29
Candidate: `f1868dd`, range `705c442..f1868dd`
Verdict: **PASS**

### Scope of this round

Focused review per the Round 8 handoff above. Confirmed via `git diff --stat
705c442..f1868dd` that the only non-doc production files touched since my
Round 7-reviewed candidate are
`Assets/TetheredTracking/Scripts/QualificationReleaseGate.cs` and
`Assets/TetheredTracking/Tests/EditMode/QualificationReleaseEditModeTests.cs`
— `qualification_protocol.py`, `track_loop.py`, `run_log.py` and
`CoverageEvaluator.cs` are byte-identical to the candidate I already verified
correct in Round 7, so items 1–6 from that round were not re-litigated. Also
confirmed the current `HEAD` (`1cfa14e`, handoff-only past `f1868dd`) touches
only docs.

### What was checked

1. **Read the full post-fix `QualificationReleaseGate.cs` and the exact
   diff**, not a summary. The constructor now takes two optional
   `double?` parameters (`configuredSessionStartedUnixSeconds`/
   `configuredSessionStartedMonotonicSeconds`), defaulting to
   `DateTimeOffset.UtcNow`/`SensorFrameWriter.HostMonotonicSeconds()` —
   the same host-monotonic function every real per-frame timestamp already
   uses, not a divergent clock source — captured once and stored in
   `readonly` fields, with a finite/non-negative guard. Confirmed
   `CoverageEvaluator.cs` is unchanged (absent from the diff), so it still
   calls the two-argument constructor and gets the "now, at `Start()`" default
   — no call-site change was needed for the fix to take effect.
2. **Hand-traced the new `TryArm()` ordering.** Two new gate functions run
   *before* any throwing validation: `MarkerCanTargetThisSession` (schema/
   protocol id, run-id pattern, scenario-id match against both the expected
   scenario and the literal `"p1-scene-004"`, `not_before_capture_monotonic_s`
   finite/non-negative) and `CommandWasIssuedForThisSession`
   (`command.issued_unix_s > sessionStartedUnixSeconds` **and**
   `command.not_before_capture_monotonic_s > sessionStartedMonotonicSeconds`,
   both required). Any failure at these two gates, at the
   `command_relative_path` check, at command-file-existence, or at command
   JSON parsing now calls `IgnoreMarker(sha256)` — which caches the marker's
   hash and returns `false` from `TryArm()` — instead of throwing. Only
   *after* a marker clears both checks does the code reach `ValidateMarker`
   and the rest of the original hash/tamper chain (`ValidateCommand`,
   `ValidateBoundArtifact` on manifest/ready), which are otherwise byte-for-
   byte unchanged from the Round 7 candidate and still throw hard on any
   mismatch. This is the correct shape: session-ownership is a soft pre-filter,
   not a replacement for the original fail-closed tamper checks — a marker
   that *is* for this session is held to exactly the same strict standard as
   before.
3. **Verified `AllowsObservation` was brought in line.** Previously it had its
   own, simpler existence-only check (`!armed` + raw `File.Exists` → block if
   a marker file merely exists) that would have been fooled by the exact same
   stale-file hazard independent of `EvaluateFrame`. It now calls
   `!armed && !TryArm()` — the identical ownership/freshness-aware path — so
   a foreign/stale marker cannot block observations via this second entry
   point either, and I confirmed by reading that `TryArm()`'s side effects
   (`armed`, `marker`, `activeMarkerSha256`) are safe to trigger from
   `AllowsObservation` before any `EvaluateFrame` call: `TryArm()` never
   touches `released`/`resetIssued`, so the first real `EvaluateFrame` call
   still performs the reset exactly once regardless of which entry point
   armed the gate first.
4. **Read every new test and independently reasoned about what it proves**,
   not just that it's green. `ForeignMarker_IsInertForDifferentScenario`
   constructs a gate for `"rate-study-20hz"` against a marker written for
   `"p1-scene-004"` and asserts `Ordinary` + `AllowsObservation(10) == true` +
   `MetricsOrigin == null` — this is exactly my Round 7 cross-scenario
   reproduction, now asserting the fixed (non-throwing) outcome.
   `StaleMarker_CannotHijackSameScenarioSession` constructs a gate for the
   *same* `"p1-scene-004"` scenario but with a session-start timestamp *later*
   than the marker's own `issued_unix_s`/`not_before_capture_monotonic_s`
   (i.e. simulating exactly "this marker predates my session") and asserts
   the same `Ordinary`/allowed/null outcome — my Round 7 same-scenario
   reproduction, now fixed. It goes further than my own throwaway
   reproduction did: it also builds a real `CoverageEvaluator`, seeds one
   real aggregated frame, applies `ApplyQualificationDisposition(Ordinary)`,
   and asserts `SensorFrames` is still `1` afterward — a direct, real proof
   that an unrelated session's aggregation is not reset by the stale marker,
   not just that the disposition enum is right.
5. **Looked specifically for a new gap the fix itself could introduce**,
   rather than only confirming the two known scenarios are closed:
   - *Could the dual-clock freshness check ever reject a genuinely fresh,
     legitimate marker for the current session?* No: the release command can
     only be created by the operator's `--release-qualification` call, which
     necessarily happens after tracker init (itself after Unity `Start()`),
     so `issued_unix_s`/`not_before_capture_monotonic_s` are always later
     than session start in the intended flow — confirmed the still-passing
     `Gate_ResetsAtMarkerAndUsesFirstFrameAtHostBoundary` test uses session
     start `(90.0, 490.0)` against a command at `(100.0, 500.0)`, i.e. the
     positive case is still exercised and still passes.
   - *Could a stale marker from before a host reboot spoof "freshness" via
     the monotonic clock alone*, since a fresh boot's `HostMonotonicSeconds()`
     starts back near zero while a very old marker could carry a
     numerically larger leftover value from a previous boot? Traced this by
     hand: `CommandWasIssuedForThisSession` requires **both** the Unix *and*
     the monotonic check via `&&`. Unix epoch time is not reset by a reboot,
     so a genuinely stale marker's `issued_unix_s` remains less than any
     later session's `sessionStartedUnixSeconds` regardless of what the
     monotonic clock does across the reboot — the Unix check alone still
     correctly rejects it. This is a real, if narrow, defense-in-depth
     property of requiring both clocks, not an accident.
   - *Could a marker that is genuinely fresh for this session but internally
     malformed (e.g. bad `not_before_capture_monotonic_s`) be silently
     swallowed by `IgnoreMarker` instead of failing loud?*
     `MarkerCanTargetThisSession` only checks a subset of the fields
     `ValidateMarker` checks (it omits `command_id`/hash-format checks), so a
     fresh marker malformed in one of *those* fields still passes the
     soft pre-filter and reaches `ValidateMarker`'s hard throw. The only
     way to be silently ignored despite being "fresh" is a malformed
     `not_before_capture_monotonic_s`/schema/protocol/run-id/scenario field —
     but Python's own `_finite()`/`_string()` validators already reject
     writing such a value in the first place, so reaching this path requires
     independent on-disk corruption *after* a valid write. Even then, the
     outcome is "gate never arms" (`Ordinary`), which the already-verified
     Round 7 Python-side `validate_metrics` chain independently rejects at
     finalization time (`metrics.json` would carry no `qualification_release`
     identity) — so this residual, essentially unreachable edge case still
     cannot produce a false qualification pass, only a correctly-rejected one.
6. **Independently reran everything myself**, not trusting the evidence
   doc's numbers, with no Unity editor holding the project lock:
   - `.venv-track/bin/python -m unittest discover -s tests -v` → **151/151
     pass** (matches; unaffected, as expected, since no Python file changed
     in this range).
   - `.venv-yoloe` focused reruns: `test_reanchor.py` **18/18**,
     `test_detector_scouting.py` **14/14**, `test_scene004_scouting.py`
     **22/22** — all match.
   - `uv pip check --python .venv-yoloe/bin/python` → **42/42 compatible**.
   - Unity `6000.4.10f1` batchmode (`6000.4.1f1`'s licensing handshake still
     unavailable, matching both evidence docs' noted constraint): focused
     `-testFilter QualificationReleaseEditModeTests` → **5/5 pass**; full
     EditMode → **115/115 pass**; full PlayMode → **3/3 pass** — all match
     the evidence doc's claims exactly.
   - Reverted the two Unity-version auto-upgrade files
     (`ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json`,
     `Packages/packages-lock.json`) after each run; `git status --short`
     clean throughout on the real checkout.
   - Confirmed no qualification session/run artifact exists in `runtime/`
     before or after this review; I did not prepare or run
     `p1-detect-001-qual-3`, per the handoff.

### Findings

No blocking findings. Both Round 7 reproductions are closed, verified by
reading the fix, by independently rerunning the two new permanent
regressions for real (not a synthetic rebuild), and by reasoning through
several adversarial variations (reboot-clock spoofing, malformed-but-fresh
marker) that the fix's design already defends against or that remain
fail-closed downstream. No new gap was found. The original hash/tamper
fail-closure for a marker that *does* belong to the current session is
unchanged and still verified strict.

### Requirement-to-evidence mapping

| Reviewed item | Evidence | Status |
|---|---|---|
| Gate arms only for exact-scenario, session-fresh commands (both clocks) | Hand-traced `MarkerCanTargetThisSession`/`CommandWasIssuedForThisSession`; reran both new regressions | Verified |
| Foreign/old markers stay `Ordinary`: observations allowed, aggregation untouched, `MetricsOrigin` null | `StaleMarker_CannotHijackSameScenarioSession`'s real `CoverageEvaluator` assertion; reran | Verified |
| Original hash/tamper fail-closure preserved once admitted | Confirmed `ValidateMarker`/`ValidateCommand`/`ValidateBoundArtifact` byte-identical to Round 7; `Gate_FailsClosedWhenBoundReadyArtifactChanges` still passes | Verified |
| No wider-scope drift | `git diff --stat 705c442..f1868dd` — only the gate file and its tests, plus docs | Verified |
| Reboot/clock-spoofing and malformed-but-fresh-marker adversarial cases | Hand-traced; both converge to safe/fail-closed outcomes | Verified, no new finding |
| Python + Unity tests genuinely cover claimed behavior | Reran all myself: 151/151, 18/18+14/14+22/22, 42/42, Unity 5/5 + 115/115 + 3/3 | Verified |

### Re-review result

**PASS.** `P1-DETECT-001` Release A5 candidate `f1868dd` correctly closes
Round 7's blocking finding B2: a `QualificationReleaseGate` now arms only for
a release command that is both scenario-matched and strictly newer (on both
the Unix and shared host-monotonic clocks) than the current Unity evaluator
session's own start, so a marker left behind by any failed attempt is inert
for every other session — no crash, no reset, no foreign identity — while
the original hash/tamper fail-closure for a marker that legitimately belongs
to the current session is unchanged. Verified by reading the full fix, by
independently rerunning both new permanent regressions and the full
Python/Unity suites (all matching), and by reasoning through adversarial
variations the fix's design already handles safely. This closes the Sonnet
independent-review gate for `P1-DETECT-001` Release A5. Codex may now
prepare and run `p1-detect-001-qual-3`; the real Unity qualification capture
and `UT-P1-DETECT-001-001` remain and are return to Codex/the user — neither
is in this review's scope and neither was run.
