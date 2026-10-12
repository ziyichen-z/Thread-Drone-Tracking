# P1-M2-RATE-002 — Batch A Unity infrastructure evidence

Date: 2026-07-25

Implementer: Codex

Candidate: `21eaeca`

Review range: `4c9ca32..21eaeca`

Round 1 review: `PASS_WITH_NOTES`
(`docs/reviews/P1-M2-RATE-002.md`)

Note-fix candidate: `94dbe70`

Focused review range: `bcdb92d..94dbe70`

Status: `ELAPSED_FIX_IMPLEMENTED_AWAITING_FOCUSED_SONNET`

Elapsed-fix candidate: `af165eb`

Focused elapsed-fix review range: `bacbbc7..af165eb`

## Scope and boundary

This candidate implements the accepted **Batch A Unity side** of RATE-002:

- Unity-owned `HOLD` / `RELEASED` / `ABORTED` state and the atomic release
  transaction;
- exact ready-byte and SHA-256 binding in the release command;
- full study/run/scenario/tracker/model/init identity checks and the
  authoritative same-Update `0 <= backlog <= 1` check;
- target, body-command, gimbal-command, evaluator, and measurement gates;
- immutable accepted-command/ack output, rejection persistence, and stale-slot
  cleanup support;
- RATE-session sensor metadata v2 with Unity monotonic capture time;
- deterministic scouting over the closed route; and
- focused Edit Mode and Play Mode regression coverage.

Batch A intentionally does **not** implement the Python-side ready heartbeat,
release coordinator, `TrackLoop` release baseline, immutable run-manifest /
command / ack `release_provenance.json` chain, v2 Python consumer migration,
S1-prime/statistics, or final run summary. Those are Batch B and may not start
until this candidate passes Sonnet and the focused Unity infrastructure gate.
No qualification pilot, calibration, or RATE-002 measurement is authorized by
this evidence.

## Implemented contracts and behavior

### Session and state ownership

`runtime/rate_study_session.json` (`p1-rate2-session/v1`) is the immutable
Unity-side expectation record. It validates the exact batch
`P1-M2-RATE-002-B1`, allowed `rs2-*` run/scenario pairing, the frozen
`nanotrack-v2` tracker, complete tracker/model/init hashes, and the fixed
20-frame / `seq >= 20` warm-up.

If no RATE session exists, ordinary simulation keeps its prior behavior. If a
session exists, Unity starts fail-closed in HOLD. An invalid session or stale
transaction slot remains blocked in HOLD; it does not invent an additional
ABORT transition.

### Release transaction

`runtime/experiment_control.json` accepts versioned release and explicit abort
commands. A release embeds the exact `tracker_ready.json` bytes as Base64 plus
their SHA-256. In one Unity Update, the controller:

1. validates command, ready schema/state, and all identities;
2. enforces the frozen warm-up and
   `0 <= current_frame_id - last_processed_frame_id <= 1`;
3. atomically enables target motion, control application, evaluator
   accumulation, and the measurement time base; and
4. writes the accepted command bytes and `p1-rate2-release-ack/v1`.

The ack contains command/ready hashes, all frozen identities, accepted frame
pair/backlog, and Unix/Unity-monotonic/simulation release times. A release
replay after RELEASED is persisted as a rejection and leaves the state
RELEASED. Only an explicit versioned abort or a fatal command/ready identity
mismatch enters ABORTED.

Rejections are persisted under `runtime/experiment_rejections/` and summarized
in `runtime/experiment_state.json`. `PrepareRuntimeSlots()` removes ready,
control, ack, accepted-command, state, and rejection slots before a new
attempt; startup detects stale transaction material and blocks HOLD.

### Gates and time boundary

`LoopTargetVehicle`, `BodyCommandReceiver`, `GimbalCommandReceiver`, and
`CoverageEvaluator` consume the shared experiment controller. HOLD suppresses
target motion and both control channels. Rejected HOLD commands are never
applied later. The evaluator excludes HOLD frames and observations and accepts
only frames strictly after the acknowledged release frame, so a stale
pre-release observation cannot become a measurement match.

For an active RATE session, sensor bundles use
`tethered-sensor-frame/v2` and add finite `capture_monotonic_s` from
`Time.realtimeSinceStartupAsDouble`, the same Unity clock epoch used by the
release ack. Outside RATE-002, the existing v1 schema and field set remain
unchanged until Batch B migrates the real Python consumers. The frame manifest
schema is unchanged.

Headless Unity with a Null graphics device now disables camera capture rather
than entering the URP render path. This affects only `-nographics` test
execution; normal graphical capture is unchanged.

### Deterministic scouting

The scouting implementation enumerates exactly
`{k * 0.5 m | k * 0.5 m < route perimeter}`, including deterministic
interpolation of the closing segment. It evaluates every active
`RateStudyDistractor`, keeps projections unclipped for border rejection,
requires the frozen 0.15 normalized margin, zero target/distractor IoU, and at
least one projected target width of separation. It writes the full
`p1-rate2-scouting/v1` qualification table and the minimum qualifying route
distance to `runtime/scouting_qualification.json`, or fails explicitly with
`INVALID_SCOUTING`.

## Automated evidence

| Check | Result | Durable raw artifact |
|---|---:|---|
| Unity 6000.4.1f1 Edit Mode | 43/43 passed, 0 failed, 0 skipped | `runtime/test-results/p1-rate-002-notes-editmode.xml` |
| Unity 6000.4.1f1 Play Mode | 2/2 passed, 0 failed, 0 skipped | `runtime/test-results/p1-rate-002-notes-playmode.xml` |
| Python regression suite | 55/55 passed | terminal run, 2026-07-25 |
| Python environment integrity | `pip check` reports no broken requirements | terminal run, 2026-07-25 |
| Runtime/Edit/Play C# assemblies | Unity Roslyn direct compilation passes | terminal run, 2026-07-25 |
| Assembly definitions / diff | JSON parse and `git diff --check` pass | terminal run, 2026-07-25 |

The 28 RATE-002 Edit Mode cases cover:

- exact-byte/hash acceptance and complete ack fields;
- future-frame and more-than-one-frame backlog rejection;
- fatal identity mismatch, pre-warm-up ready, tampered ready, and non-finite
  release clock;
- RELEASED replay and the exact ABORT trigger set;
- simulated 60-second HOLD invariance and control rejection;
- stale-slot cleanup and invalid-session fail-closed behavior;
- evaluator exclusion before and at the release frame;
- v1 ordinary / v2 RATE sensor metadata behavior; and
- exact scouting grid, closing segment, unclipped border test, all-distractor
  minimum, margin, IoU, and separation rules.

They additionally exercise the real production `Initialize()` disk-loading
entry point for no-session passthrough, valid-session HOLD, scenario mismatch,
and stale startup slots; invalid study, tracker, run/scenario, and hash
dimensions are each tested with an independent session copy.

The two Play Mode tests cross real Unity frames. One asserts that target motion
and measurement remain disabled in HOLD, then become enabled only after a
valid release transaction. The other creates separate follow and nadir
conditions, drives the actual body/gimbal receiver gates, and compares
pre-release platform position/rotation and camera position/rotation
component-by-component before independently checking nadir orientation.

The original Batch A headless Play Mode attempt reached a native URP `Camera.Render`
failure on the Null graphics device. The candidate added the explicit Null
graphics guard, and the final Play Mode XML above passed. The final log still
contains Unity's transient startup licensing handshake message and a benign
Null-render-target startup warning, followed by a completed test run with exit
code 0.

During the 2026-07-25 note-fix rerun, a stale Unity 6000.4.1 licensing child
process repeatedly connected the editor to an incompatible generic Hub
protocol and prevented test execution before any XML was produced. Terminating
that single stale child allowed the editor to launch its version-specific
client. The subsequent real runs produced the passing 43/43 and 2/2 XML files
listed above; the pre-XML environment attempts are not counted as test
failures.

## Unity case-3 elapsed-time defect and focused fix

The user production-path smoke passed HOLD/v2 publication and pre-release
body/gimbal command suppression. Its first atomic-release attempt also proved
the state transaction and evidence chain:

- accepted command `smoke-release-1785014137993652000`;
- `HOLD -> RELEASED` with accepted backlog `1`;
- accepted-command bytes were identical to the submitted command;
- command and ready SHA-256 values matched the release ack;
- release frame `220`, followed by 19 evaluator frames and changed target
  imagery.

The attempt nevertheless failed the accepted release-origin metric contract.
About `0.95 s` after release, `metrics.json.elapsed_simulation_s` reported
`11.982766 s`. Source tracing found that `CoverageEvaluator.WriteMetrics()`
serialized the absolute last frame simulation time. The duration-weighted
aggregates themselves already used only accepted post-release frame weights,
so the defect was isolated to the public elapsed field.

The focused fix removes the unused absolute `lastSimulationTime` state and
serializes `totalDuration`, the same release-gated accepted-frame duration
used by the aggregate denominators. The shared metrics-document builder is
also exposed as JSON only to the friend test assembly. A new Edit Mode
regression places a rejected HOLD frame at absolute simulation time
`1000.0 s`, releases, accepts two `0.05 s` frames at `1000.05/1000.10 s`, and
directly parses the public JSON to require
`elapsed_simulation_s == 0.10 s` and `sensor_frames == 2`.

The first post-fix Play Mode run returned 1/2 because the existing pose test
waited only two unconstrained batch frames for a deliberately displaced
gimbal to slew back to nadir. It reached quaternion x `0.675188` instead of
`0.707107`; no production file on that path changed. The test now waits a
fixed `0.02 s` of simulation time at its test-only `10000 deg/s` slew rate,
which covers the full 45-degree travel, before applying the same component-
wise assertions. This is a test determinism correction, not a relaxed
expected value or production behavior change.

Focused post-fix evidence:

| Check | Result | Durable raw artifact |
|---|---:|---|
| Unity 6000.4.1f1 Edit Mode | 44/44 passed, 0 failed, 0 skipped; new public elapsed test explicitly `Passed` | `runtime/test-results/p1-rate-002-elapsed-fix-editmode.xml` |
| Unity 6000.4.1f1 Play Mode final rerun | 2/2 passed, 0 failed, 0 skipped | `runtime/test-results/p1-rate-002-elapsed-fix-playmode.xml` |
| Python regression suite | 55/55 passed | terminal run, 2026-07-25 |
| Python environment / static checks | `pip check`, `py_compile`, and `git diff --check` pass | terminal run, 2026-07-25 |

## Focused user Unity gate

`UT-P1-M2-RATE-002-001` is PASS 4/4 after preserving the first case-3
failure. The successful release rerun accepted backlog 0 with exact ready,
command and ack hashes. Public evaluator elapsed was `6.599400 s` for 132
accepted 20 Hz frames (`6.600000 s` by frame weighting), while absolute
simulation time was `10.482029 s`. A second valid release was persisted as
`release_replay_after_released`; state remained `RELEASED`, the original ack
SHA-256 remained
`e5f54ebcbf5e8079a407e5bde9b4fcd1b46dd6f9e847702825e94df2ec3de78a`,
and the accepted command remained byte-identical.

The failed attempt and successful rerun are retained separately under
`runtime/test-results/ut-p1-m2-rate-002-001-case3-attempt1/` and
`runtime/test-results/ut-p1-m2-rate-002-001-case3-4-rerun-pass/`. After the
user exited Play, the temporary `rs2-pilot` session and every smoke
transaction/control/frame/metrics slot were removed; no
`runtime/runs/rs2-pilot/` directory exists.

## Required next gates

1. Sonnet's focused review of candidate `af165eb` over
   `bacbbc7..af165eb` passed, covering the release-origin elapsed semantic,
   shared metrics builder, direct JSON regression, and Play Mode wait
   stabilization.
2. The user cases 3–4 rerun passed. Batch A is closed and Batch B
   implementation may begin.
3. Batch B must form its own stable candidate and pass Sonnet before the
   shared 20 Hz follow qualification pilot or any measurement.
