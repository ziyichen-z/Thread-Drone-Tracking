# P1-M2-RATE-001 — implementation evidence before measured sessions

Date: 2026-07-24
Original stable candidate: `0642290` (review range `86ffc47..0642290`);
implementation code commit: `d29bc13`; Sonnet Round 1:
`PASS_WITH_NOTES`
Post-review safeguard candidate: `cbff720` (focused review range
`0642290..cbff720`)
Initialization-amendment candidate: `34dd40a` (focused review range
`d70a7cf..34dd40a`)
S1 measurement-window candidate: `fad91da` (focused review range
`3cb0655..fad91da`)

Status: the user accepted the S1 time-window amendment and candidate `fad91da`
implements it. Implementer verification passes 43/43. Existing
`rate20-follow-r1/r2` raw artifacts were deterministically re-finalized:
whole-span rates remain `14.62035980/15.65336809 Hz`, while the new
post-launch S1 cohort reports `19.99969431/20.00076252 Hz`, so both runs pass
S1 without erasing the raw diagnostic. Sonnet Round 4 independently passed
`3cb0655..fad91da`, including
recomputation from the raw r1/r2 timestamps. Both calibrations were revalidated
and `rate20-follow-r3` subsequently completed admissibly. The 20 Hz follow
cell is complete and `rate20-nadir-r1/r2` have also completed admissibly. All
12 measured artifacts now exist. Final `rate20-nadir-r3` is complete and
passes S2/S3, but a single `-29 ms` post-launch Unix timestamp regression
fails strict S1, so the generated study decision is
`BLOCKED_RATE_UNSUSTAINABLE`.

## Measured-session progress

`rate5-nadir-r1` completed automatically and passed all admission checks:

```text
classification=COMPLETE
admissible=true
actual/planned_duration_s=269.0003991127014/268.97056274847716
total_frame_records=1346
simulation_rate_hz=4.999992581559307
artifact_errors=[]
gap_events=0
reinit_required_records=0
C_track=0.0
C_geom=0.16878269612789154
time_to_first_lost_s=3.3996071815490723
```

This is the fourth of 12 measured sessions. The zero tracking coverage is
retained as an experimental result rather than treated as a runtime failure.

`rate5-nadir-r2` also completed and passed admission:

```text
classification=COMPLETE
admissible=true
actual/planned_duration_s=269.0010242462158/268.97056274847716
total_frame_records=1346
simulation_rate_hz=4.999980962038737
artifact_errors=[]
gap_events=0
reinit_required_records=0
C_track=0.0
C_geom=0.16877074539661407
time_to_first_lost_s=3.3991165161132812
```

This is the fifth of 12 measured sessions and closely repeats nadir r1.

`rate5-nadir-r3` completed with the same outcome:

```text
classification=COMPLETE
admissible=true
actual/planned_duration_s=269.0016531944275/268.97056274847716
total_frame_records=1346
simulation_rate_hz=4.99996927166789
artifact_errors=[]
gap_events=0
reinit_required_records=0
C_track=0.0
C_geom=0.1687866896390915
time_to_first_lost_s=3.3989157676696777
```

The 5 Hz nadir cell is complete. Its median/range are:

```text
C_track=0.0 / [0.0,0.0]
C_geom=0.16878269612789154 / [0.16877074539661407,0.1687866896390915]
first_LOST_s=3.3991165161132812 / [3.3989157676696777,3.3996071815490723]
```

Both 5 Hz cells are complete (6/6).

`rate20-follow-r1` completed with the required 20 Hz simulation cadence:

```text
classification=COMPLETE
admissible=true
actual/planned_duration_s=269.0008807182312/268.97056274847716
total_frame_records=5381
simulation_rate_hz=19.999934519305004
wall_clock_capture_rate_hz=14.620359801405344
post_launch_wall_clock_capture_rate_hz=19.999694311421656
compute_latency_p95_ms=6.214254195219837
backlog_p95=0.0
artifact_errors=[]
gap_events=0
reinit_required_records=0
C_track=0.0
C_geom=0.16914327442646027
time_to_first_lost_s=3.450441837310791
```

The preserved raw whole-span diagnostic is `14.6204 Hz`, but the accepted S1
cohort begins at `manifest.created_unix_s`, excludes 146 pre-launch samples,
and starts at frame 286. Its `19.99969431 Hz` rate passes S1; S2 and S3 also
pass.

`rate20-follow-r2` completed with the same outcome:

```text
classification=COMPLETE
admissible=true
actual/planned_duration_s=268.9990887641907/268.97056274847716
total_frame_records=5381
simulation_rate_hz=20.000067750103803
wall_clock_capture_rate_hz=15.65336808821594
post_launch_wall_clock_capture_rate_hz=20.0007625176826
compute_latency_p95_ms=5.876360434922391
backlog_p95=0.0
artifact_errors=[]
gap_events=0
reinit_required_records=0
C_track=0.0
C_geom=0.16914314031600952
time_to_first_lost_s=3.449410915374756
```

The raw whole-span diagnostic remains `15.6534 Hz`. The post-launch cohort
excludes 134 pre-launch samples, starts at frame 274, and reports
`20.00076252 Hz`; S1–S3 pass. Both re-finalizations preserve copies of the
pre-amendment summaries as `summary.pre-s1-amendment.json`.

## Implemented scope

- Added checked-in 5 Hz and 20 Hz scenario configs. A validator proves that
  they differ only in the accepted `scenario_id`, `capture_hz`,
  `retained_frame_count`, and `maximum_pending_frame_count` fields.
- Added `tools.run_rate_study` with explicit commands for validation, runtime
  preparation, deterministic `[7,8)` init-frame preview, rate-specific
  calibration capture, measured-run staging, hash-bound rectangle-overlay
  confirmation, immutable invalid-attempt retention, tracker launch, and
  strict N=3 summary.
- Extended `p1-track-run/v1` manifests with a bounded `rate_study` section:
  rate, replicate/attempt identity, loop duration, config/init/reference
  hashes, and reference frame/time. No sensor, observation, gimbal, or body
  protocol changed.
- Extended run summaries with raw wall-clock capture cadence, an auditable
  post-launch S1 cohort/window, simulation-time cadence, backlog percentiles,
  and right-censored time to first `LOST`.
- The strict summary requires one admissible attempt for all 12 predeclared
  replicates, reports run values plus cell median/range, blocks decisions when
  any 20 Hz run fails S1–S3, and applies both accepted `P1-TRACK-002` gates and
  the 15/25/35% sensitivity table.
- Refactored the existing `CoverageEvaluator` frame/observation aggregation
  into internal instance methods used by both production callbacks and direct
  Edit Mode tests. The arithmetic, counters, pending-frame semantics, metric
  names, thresholds, and output schema are unchanged.

## Post-review safeguards

Codex accepted Sonnet note 1 as load-bearing for the pre-registered R2
decision. `launch` now reads `summary.actual_duration_s`, compares it with the
staged planned duration, and classifies a short attempt `INVALID` with
`planned_duration_not_reached`. `summarize` repeats the check independently
against the run manifest, so manually changing the status cannot admit a short
right-censored run. The only tolerance is `1e-6 s`, for numeric serialization;
the tracker uses the same simulation-time difference to decide completion.
Actual/planned duration and shortfall are retained in status JSON and generated
run tables.

Sonnet note 2 is resolved with `invalidate-calibration`. It validates and moves
the original `rate{5|20}-calib` directory to a unique
`rate{5|20}-calib-invalid-*` evidence directory with its reason, then permits a
fresh canonical calibration. Sonnet note 4 now has a direct test that creates
two admissible attempts for one replicate and verifies strict summary
rejection. Note 3 (sharing `AggregationSnapshot`/`WriteMetrics` ratio helpers)
is deliberately deferred because it does not change measured behavior and
would touch the already-reviewed frozen C# metric path.

## Unity-driven initialization amendment

The first real 5 Hz calibration selected frame 15 at
`3.1802380084991455 s`. The red target overlapped a yellow distractor, and all
five retained candidates in `[3,4)` (frames 15–19, `3.180–3.982 s`) remained
ambiguous. The attempt was rejected before `rate5-calib` existed. Retained
evidence showed separation beginning near 6.18 s and a clear gap by frame 35.
The user approved replacing the shared half-open initialization interval with
`[7.0,8.0)`.

Candidate `34dd40a` applies the new interval to both rates and excludes the old
frames. It also adds `preview-box`, which writes a separate JPEG with the
proposed rectangle while leaving the raw sensor image byte-for-byte unchanged.
`calibrate --confirmed` rejects missing confirmation and rechecks the preview
frame ID, raw image and metadata hashes, normalized box, overlay path, and
overlay hash. The metadata hash binds the selected simulation timestamp.
Calibration archives the overlay evidence;
staging regenerates, verifies, and later archives the run-specific overlay.

## Frozen configuration evidence

Command:

```bash
.venv-track/bin/python -m tools.run_rate_study validate
```

Result:

```text
rates_hz=[5,20]
replicates_per_cell=3
calibration_sessions=2
measured_sessions=12
init_window_simulation_s=[7.0,8.0]
route_perimeter_m=208.97056274847716
loop_duration_s=104.48528137423858
planned_duration_s=268.97056274847716
5 Hz config SHA-256=7bfceabb95e51a0e09659b22e000277d9beada91045e4f31e24d11f0257a4f14
20 Hz config SHA-256=4bddb2f2dcca564bd5637b77e94e6d616d3cf2ca7db85a3060e6599913be79d2
```

The 5 Hz retention/pending durations are `128/5=25.6 s` and
`512/5=102.4 s`; the 20 Hz durations are `512/20=25.6 s` and
`2048/20=102.4 s`.

## Automated verification

Pinned tracker environment:

```bash
.venv-track/bin/python -m unittest discover -s tests -v
```

Result: `Ran 34 tests ... OK`. This includes real installed CSRT construction
and subprocess CLI execution, config-invariant validation, deterministic frame
selection, calibration/staging/invalidation, authoritative artifact archival,
strict fixed-replicate aggregation, both SOT gates, and the
`RATE_UNSUSTAINABLE` decision block.

Post-review safeguard result:

```text
Ran 37 tests ... OK
```

The three added cases verify launch-time rejection of an early attempt,
summary-time rejection even when status falsely says `COMPLETE`, and rejection
of duplicate admissible replicates. The existing calibration/staging test now
also invalidates, archives, and recreates a rate calibration.

Initialization-amendment result remains:

```text
Ran 37 tests ... OK
```

The amended suite now additionally proves that an old 3.1 s frame is excluded,
the earliest complete 7.1 s frame is selected, box-overlay pixel geometry is
correct, rendering does not modify the raw JPEG, explicit confirmation is
required, a mismatched confirmed box is rejected, and the matching overlay is
archived through calibration, staging, and launch. The overall count remains
37 because these assertions extend existing workflow cases.

S1 measurement-window amendment:

```text
Ran 43 tests ... OK
```

The added cases prove that pre-launch retained frames are excluded, a
post-launch mid-run stall remains inside the cadence and lowers it,
missing/invalid eligibility fails closed, S1 consumes only the post-launch
field, and the generated Markdown reports both raw and S1 rates. Real r1/r2
re-finalization reproduces `19.99969431/20.00076252 Hz`.

Additional checks:

```text
.venv-track/bin/python -m pip check
No broken requirements found.

python3 -m py_compile controller/*.py tools/*.py tests/*.py
clean

git diff --check
clean
```

Unity 6000.4.1f1 Edit Mode command:

```text
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode \
  -projectPath ~/TetheredDroneTracking \
  -runTests \
  -testPlatform EditMode \
  -testFilter TetheredTracking.Tests \
  -testResults ~/TetheredDroneTracking/runtime/test-results/p1-m2-rate-001-editmode.xml \
  -logFile ~/TetheredDroneTracking/runtime/test-results/p1-m2-rate-001-unity.log
```

Machine result:

```text
result=Passed
total=15
passed=15
failed=0
inconclusive=0
skipped=0
```

The four new cases directly exercise `CoverageEvaluator`:

1. duration weighting plus the `1/capture_hz` fallback;
2. matched, incorrect, duplicate, and unmatched observations;
3. 5 Hz pending pruning at 512 frames;
4. 20 Hz pending pruning at 2048 frames.

Both pruning tests verify that already accepted tracking duration remains
attributed after the corresponding frame leaves the pending dictionary.

## Session helper contract

All commands run from the project root using the pinned interpreter:

```bash
.venv-track/bin/python -m tools.run_rate_study --help
```

The helper never starts or controls the Unity editor. `prepare` removes only
the runtime exchange slots and `frames/`; it preserves every `runs/` directory.
Calibration and measured attempts fail on existing destination IDs. A
pre-launch visual failure is archived with `invalidate-stage`; a completed
attempt can be made inadmissible with `invalidate-run`, after which a retry
uses an explicit suffix such as `retry-a`. Existing evidence is not deleted or
reused.

An incorrect frozen calibration is archived and released for redo with:

```bash
.venv-track/bin/python -m tools.run_rate_study invalidate-calibration \
  --rate <5|20> \
  --suffix invalid-a \
  --reason "<reason>"
```

`launch --confirmed` rechecks the installed config hash, calibration hashes,
and exact staged init image/metadata before starting the tracker. The tracker
captures the scenario-matched `metrics.final.json` when planned duration ends,
before the user stops Play. The helper validates both that snapshot and the
actual/planned run duration; it does not replace the snapshot with a later
`runtime/metrics.json`.

Before `calibrate`, the operator must render and inspect the actual proposed
rectangle:

```bash
.venv-track/bin/python -m tools.run_rate_study preview-box \
  --rate <5|20> \
  --box <X> <Y> <WIDTH> <HEIGHT>
```

The generated raw preview and overlay are distinct files. A real retained 5 Hz
smoke selected frame 35 at `7.180588722229004 s`:

```text
raw image SHA-256=00a86024b75a917f5c3d33489ee4ebfe9eecc29f4bb81ecbf1711844d2c83def
metadata SHA-256=9d94c6190c5ff9ac9b17f96514b85f4361a818c10ce4c2ebc2da9d8be01c3650
normalized box=[0.828125,0.4604166667,0.125,0.0791666667]
pixel box=[530,221,80,39]
overlay SHA-256=43a7808492bfc9b653838c8a8f5c15d8b80faf6339b432f577e6f0604a9d6ce8
```

Visual inspection confirmed the green rectangle encloses the red car with a
clear gap from the yellow distractor. This is a tool smoke only, not a captured
calibration or measured result.

## Accepted 5 Hz calibration evidence

The clean post-review Unity session selected frame 35 at
`7.18242883682251 s`. After the user inspected and explicitly confirmed the
green overlay, `calibrate --rate 5 --confirmed` created
`runtime/runs/rate5-calib/`. A subsequent `load_calibration` revalidated the
complete hash chain:

```text
scenario config SHA-256=7bfceabb95e51a0e09659b22e000277d9beada91045e4f31e24d11f0257a4f14
reference image SHA-256=863e579fd310a5f05ebf67bb6543f58b5977d30d56ca4c91ff013a67e4d699a8
reference metadata SHA-256=58020d5a66650fe1644b49226d24a00d70a8d9b10b452084e05acec592eb738a
reference overlay SHA-256=f91b991875caec2ae74c766773861a25dfa24e5d3882806478ba50bd5b86f3c8
box norm=[0.828125,0.4604166667,0.125,0.0791666667]
```

The directory contains the immutable raw reference image/metadata, confirmed
overlay image/manifest, and calibration manifest. No measured run was started.

## Accepted 20 Hz calibration evidence

The clean 20 Hz Unity session selected frame 140 at
`7.030401229858398 s`. After the user inspected and explicitly confirmed the
green overlay, `calibrate --rate 20 --confirmed` created
`runtime/runs/rate20-calib/`. A subsequent reload of both rate calibrations
passed:

```text
scenario config SHA-256=4bddb2f2dcca564bd5637b77e94e6d616d3cf2ca7db85a3060e6599913be79d2
reference image SHA-256=4bb59b7b4cc7768a0288d76d89620cc93d3cdf3bac4cec2b2b2c41153786ac3d
reference metadata SHA-256=6c9c248d7870d8d5c04a18008782020e03fb4884c04d86d8e53078f261a5e028
reference overlay SHA-256=60d37324af5e316a503fdab81d16029e559c2a6b6778a1ab01deb9db26b7174d
box norm=[0.81875,0.4604166667,0.125,0.0791666667]
```

Both immutable calibration directories coexist and validate. Calibration is
complete at 2/2; at that calibration checkpoint no measured run had started.

## Accepted measured-session evidence

| Run | Status | Actual/planned s | C_track | C_geom | C_track_given_geom | First LOST s |
|---|---|---:|---:|---:|---:|---:|
| `rate5-follow-r1` | `COMPLETE`, admissible, duration complete | 268.999538 / 268.970563 | 0.0 | 0.168068916 | 0.0 | 3.400535 |
| `rate5-follow-r2` | `COMPLETE`, admissible, duration complete | 269.001818 / 268.970563 | 0.0 | 0.168767348 | 0.0 | 3.400732 |
| `rate5-follow-r3` | `COMPLETE`, admissible, duration complete | 269.000966 / 268.970563 | 0.0 | 0.168053791 | 0.0 | 3.399935 |
| `rate5-nadir-r1` | `COMPLETE`, admissible, duration complete | 269.000399 / 268.970563 | 0.0 | 0.168782696 | 0.0 | 3.399607 |
| `rate5-nadir-r2` | `COMPLETE`, admissible, duration complete | 269.001024 / 268.970563 | 0.0 | 0.168770745 | 0.0 | 3.399117 |
| `rate5-nadir-r3` | `COMPLETE`, admissible, duration complete | 269.001653 / 268.970563 | 0.0 | 0.168786690 | 0.0 | 3.398916 |
| `rate20-follow-r1` | `COMPLETE`, admissible, duration complete, S1–S3 pass | 269.000881 / 268.970563 | 0.0 | 0.169143274 | 0.0 | 3.450442 |
| `rate20-follow-r2` | `COMPLETE`, admissible, duration complete, S1–S3 pass | 268.999089 / 268.970563 | 0.0 | 0.169143140 | 0.0 | 3.449411 |
| `rate20-follow-r3` | `COMPLETE`, admissible, duration complete, S1–S3 pass | 269.004238 / 268.970563 | 0.000179681 | 0.212632224 | 0.000845032 | 3.450604 |
| `rate20-nadir-r1` | `COMPLETE`, admissible, duration complete, S1–S3 pass | 269.000731 / 268.970563 | 0.0 | 0.169156730 | 0.0 | 3.450379 |
| `rate20-nadir-r2` | `COMPLETE`, admissible, duration complete, S1–S3 pass | 269.001466 / 268.970563 | 0.0 | 0.169174269 | 0.0 | 3.450955 |
| `rate20-nadir-r3` | `COMPLETE`, admissible, duration complete, S2/S3 pass; S1 clock regression | 269.001946 / 268.970563 | 0.0 | 0.169142440 | 0.0 | 3.450257 |

The three 5 Hz follow runs exited normally with 1346 records apiece, zero artifact errors,
zero gaps, zero geolocation rejects, and zero reinit-required events.
The 5 Hz follow cell median/range is `C_track=0/[0,0]`,
`C_geom=0.168068916/[0.168053791,0.168767348]`, and first LOST
`3.400535/[3.399935,3.400732] s`. Compute-latency p50 was
`5.093/5.182/5.030 ms`, and backlog p50/p95 was `0/0` throughout. The
closely repeated early LOST and zero tracking coverage are retained as the
honest CSRT result, not an operational failure. All six 5 Hz runs and six
20 Hz runs listed above are preserved artifacts; the S1 amendment changes
only the timing cohort, not their tracking results. The final run's one
backwards civil-clock sample makes the strict summary report
`decision=BLOCKED_RATE_UNSUSTAINABLE`.

## Deliberate limits and next gate

- All 12 measured artifacts are captured. Five 20 Hz runs pass S1–S3 under
  the accepted post-launch rule; final nadir r3 passes S2/S3 but fails strict
  S1 because one Unix timestamp regresses by `29 ms`. The follow-cell medians
  satisfy both pre-registered SOT predicates, but the generated global
  decision is blocked pending an explicit clock-integrity decision.
- The user must visually verify each staged normalized box. The helper records
  confirmation but cannot determine target identity from ground truth.
- The closed-loop interaction remains descriptive, not a causal separation of
  image sampling and gimbal-command cadence.
- No TensorRT, CUDA, Jetson, YOLOE, deep SOT, M3, or metric-semantic change is
  included.
- Sonnet passed the focused `3cb0655..fad91da` review. No further session may
  be silently substituted for final r3. The diagnosis and recovery choices
  are in `P1-M2-RATE-001-clock-regression-diagnosis.md`; formal M2 closure
  also requires `DR-P1-M2-001`.
