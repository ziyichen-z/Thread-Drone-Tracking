# P1-DETECT-001 qual-3 — step-0 attribution package

Work ID: `P1-DETECT-001` (blockage caused by `P1-M2-RATE-003` batches 1–2)
Role: implementation — **input for adjudication, not a verdict**
Date: 2026-07-31

The Attempt 3 operator sequence (`docs/unity-test-log.md`, step 0) refuses
Play when the checked-out tree differs from reviewed candidate `f1868dd`
in measurement implementation. It does. Play was **not** entered and no
qual-3 identity was created. This file is the attribution material the
step-0 rule sends to acceptance; every judgement below is offered as
input, and none of it clears the gate.

## Step-0 facts as recorded

- `git rev-parse HEAD` → `2469053309ee136e67408d7ccff70bb548c6ddf2`
- `git status --porcelain` → empty (clean worktree)
- Reserved run ID `p1-detect-001-qual-3` is unused. Runtime live slots are
  empty: no `p1_detect_qualification_release.json` pointer, no
  `runs/p1-detect-001-qual-3`, `runtime/frames/` empty, and the installed
  `runtime/scenario_config.json` still matches the frozen SCENE-004 hash
  `00c8802a…b514`.
- `git diff --stat f1868dd..HEAD -- Assets controller config tools tests`
  → **34 files, +10,889 / −80**. The gate therefore fails.

## Which batches produced the difference

`git log --oneline f1868dd..HEAD -- Assets controller config tools tests`:

| Commit | Batch | Role |
|---|---|---|
| `ab8ae73` | RATE-003 batch 2, review round-3 fixes | implementation |
| `dea5111` | RATE-003 batch 2, BC-B2-CQ1/CQ2 rework | implementation |
| `6417dc3` | RATE-003 batch 2, first implementation | implementation |
| `57f2561` | RATE-003 batch 1, review round-1 finding 1 | implementation |
| `feaf475` | RATE-003 batch 1, shared-clock v3 protocol | implementation |
| `312e08b` | COORD-002 review findings 1–6 | coordination |
| `02d90b5` | COORD-002 role/write boundaries | coordination |

Most of the volume is additive and unreachable from qual-3 (new rate3
modules, new configs, new tools, new tests, the scouting tool, the
difficulty-audit tool). The adjudication only needs the files that sit on
qual-3's own execution path.

## The five files on qual-3's execution path

qual-3 runs `controller/track_loop.py` with
`--qualification-release-barrier`, no `--rate2-session` and no
`--rate3-session`, against Unity's ordinary (non-RATE) frame path, with
`CoverageEvaluator` as the sole truth source.

### 1. `Assets/.../SensorFrameWriter.cs` (`feaf475`, +3/−1)

The only change narrows the v2 selector:

```csharp
bool rateStudyV2 = scenario.ExperimentController != null
    && scenario.ExperimentController.IsActive
+   && !scenario.ExperimentController.UsesSharedHostClock;
```

qual-3 installs no RATE session, so `IsActive` is false and the whole
conjunction was already false. Frames take `HostMonotonicSeconds()` and
schema v3 before and after. **Assessed inert; the added term cannot change
a `false` conjunction.**

### 2. `Assets/.../CoverageEvaluator.cs` (`6417dc3`, +121)

Adds the RATE-003 evaluation-truth sidecar: one new call in
`OnFramePublished`, a nested record type, a `StreamWriter` field and
`OnDestroy`/`OnApplicationQuit` disposal. The writer returns immediately
unless a RATE-003 session is active **and** `Released`:

```csharp
if (experiment == null || !experiment.IsActive
    || !experiment.UsesSharedHostClock
    || experiment.State != RateStudyExperimentState.Released
    || experiment.Session == null) return;
```

No aggregation, threshold, box, IoU or duration path was touched.
**Assessed inert for qual-3**, but this is a change inside qual-3's sole
truth source, so it deserves acceptance's own read rather than mine.

### 3. `controller/reanchor_runtime.py` (`feaf475`, +23/−3)

Adds the P5 clock-identity binding: a `monotonic_clock_id` constructor
argument that defaults to `system-stopwatch/v1` when `monotonic` is
`time.monotonic`, and one extra key in `manifest_identity()`. The triple
gate, the staleness rule and every threshold are untouched.
**Assessed inert for behaviour**, with one caveat worth stating: the run
manifest now carries an extra `reanchor.monotonic_clock_id` field, so a
byte-level manifest comparison against qual-1/qual-2 will differ.

### 4. `controller/run_log.py` (`feaf475`, +32/−6)

Adds an optional `release_clock_id` argument to `build_summary` (clock
identity is enforced only when it is passed), a `rate3` provenance branch
in `finalize_run`, and generalises the "two release protocols at once"
refusal from a rate2/qualification pair to all three. For qual-3 the
qualification branch is selected exactly as before and `release_clock_id`
is `None`, so the new per-frame check does not run. **Assessed inert**;
the summary document gains a `release_clock_id: null` field.

### 5. `controller/track_loop.py` (`feaf475`, `57f2561`, +219/−58) — the item that needs real scrutiny

This is **not** purely additive. `TrackLoop` gained
`self._rate_lifecycle = rate2_lifecycle if … else rate3_lifecycle`, and
several existing control-flow conditions on qual-3's path were rewritten
from `self.rate2_lifecycle` to `self._rate_lifecycle`, including:

- the completion predicate in `complete()`;
- `allow_control=self._rate_lifecycle is None`;
- the ready/ack publication guards;
- a new `_invalid_clock_fail_closed` flag and the `INVALID_CLOCK` terminal
  path around the frame-protocol read.

For qual-3 both lifecycles are `None`, so `_rate_lifecycle` is `None` and
every rewritten condition evaluates exactly as `self.rate2_lifecycle is
None` did; `_invalid_clock_fail_closed` is `False`, so the new terminal
path is unreachable. The constructor also gained an explicit refusal when
more than one release lifecycle is installed, which is strictly stricter.

**This is a refactor of the shared loop qual-3 executes, not an additive
guard.** By construction it should be behaviour-identical for qual-3, but
that is precisely the claim an independent reader should confirm rather
than take from the author of the refactor.

## Summary for the adjudicator

| File | Change class | Implementation's read |
|---|---|---|
| `SensorFrameWriter.cs` | narrowing a already-false conjunction | inert |
| `CoverageEvaluator.cs` | additive, session-gated sidecar | inert, but inside the truth source |
| `reanchor_runtime.py` | additive identity binding | inert; manifest gains a field |
| `run_log.py` | optional argument + new sibling branch | inert; summary gains a null field |
| `track_loop.py` | **refactor of shared control flow** | should be inert; needs independent confirmation |

Nothing here is a verdict. Two outcomes are available to the adjudicator:
re-bind qual-3 to a new candidate after attributing these changes as
semantically inert, or require qual-3 to run on a tree at `f1868dd`.

## What implementation did not do

- Did not enter Play, did not create a session, run directory or the
  `p1-detect-001-qual-3` identity.
- Did not write `docs/unity-test-log.md` or `docs/authorizations.md`
  (read-only to this role).
- Did not self-clear the step-0 gate. The rule says return to acceptance;
  this file is that return.
