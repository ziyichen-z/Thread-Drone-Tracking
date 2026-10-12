# P1-DETECT-001 qualification attempt 2 evidence

Date: 2026-07-29

Owner: Codex

Run ID: `p1-detect-001-qual-2`

Disposition: `PROTOCOL_INVALID_RELEASE_BOUNDARY`

This attempt is retained and its ID is permanently consumed. It is neither a
qualification PASS nor a model-performance FAIL. No threshold, model, scene,
truth path, metric, or acceptance gate has been changed.

## Operator observations and initialization

The user entered one fresh Unity Play domain, paused in the required reference
window, later ran to approximately 170–180 seconds with no Console error,
paused, and then exited Play.

Codex inspected sensor frames only before initialization; Unity truth was not
read. The user confirmed frame 159 at `7.981178283691406 s` and pixel
top-left `xywh=(353,82,72,43)`, normalized as
`(0.5515625,0.17083333333333334,0.1125,0.08958333333333333)`.
The v3 image, metadata, and overlay SHA-256 values are respectively:

- `8ae67217023b53526a14e003020f12d4f28f01a3957d425dec0de692b188ddde`
- `15632d3a9e0f10c4439c614fd33a6b6c38d95cd62f65ac5621d47d219c86a52d`
- `f31a89c2e81794a0471ee85470df71067cb8c0d1a574c25a23b9808a2663e668`

The frame carries `tethered-sensor-frame/v3`,
`capture_monotonic_clock_id=system-stopwatch/v1`, and the expected
`p1-scene-004` identity. NanoTrack and both re-anchor models initialized
successfully. The tracker remained alive while paused, then terminated
normally with a summary rather than an exception.

## Preserved run evidence

The immutable run remains under
`runtime/runs/p1-detect-001-qual-2/`. Primary SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| `manifest.json` | `09df3701635c66307dd7594d43d4290a80ddeced9a31ba5ef778a077c4dca684` |
| `frames.jsonl` | `72d351b62a9d88b504a8e3fa6ecd04813dc07204fdaa0d9f1a7626cb72556788` |
| `summary.json` | `53774dda89f412356a2854a81572ba28ece37efa27e0bcebfb4d447ad2890574` |
| `metrics.final.json` | `b58b48a6172af58bf82ae5b240da1468ae6c8a3d703dfcfe6e312647fa1ab4a6` |
| `init-frame-box-preview.json` | `d74e2f488599cf30ad969db6781c6b06c9615c3235bdd047d1147677bfc3f2f7` |

The summary contains 3,001 measurement frame records over a nominal
`150.00165557861328 s` simulation span, 0 gap, 0 reinit, 0 LOST, and
NanoTrack compute p50/p95 `8.626/13.084 ms`. Post-launch capture cadence is
`19.997992 Hz`. Re-anchor events comprise 75 `ROUND_STARTED`, 34 `AGREE`,
23 `TENTATIVE`, 18 `NO_CANDIDATE`, one busy skip, and no DISAGREE/reseed or
wrong-recapture event.

`CoverageEvaluator` is the only Unity-truth source used for the following
descriptive result. The tracker-stop snapshot reports:

| Quantity | Value | Frozen gate |
|---|---:|---:|
| `C_geom` | 1.0 | descriptive |
| `C_track_given_geom` | 0.8902833462 | ≥ 0.4 |
| matched observations | 2,985 | > 0 |
| incorrect observations | 172 | reported |
| incorrect / matched | 0.0576214405 | < 0.5 |
| unmatched observations | 0 | reported |

These values pass the tracking-quality, identity-error, gap/reinit, compute,
and nominal simulation-span/loop-count conditions. They remain descriptive
because the release/cadence boundary is invalid.

After the tracker stopped, Unity continued to `183.380615234375 s`; the
user-reported no-error observation therefore covers the requested operator
window. That later evaluator snapshot is retained separately and is not
substituted for the tracker's create-once `metrics.final.json`.

## Protocol-invalid diagnosis

The accepted design binds the cadence denominator to all planned ticks after
acknowledged release. The non-RATE qualification path has no explicit release
barrier. It treats every post-init frame as released:

1. initialization and retained backlog frames 159–170 were captured while
   Unity was paused;
2. frame 160 established the re-anchor motion anchor and next planned tick;
3. the first fresh post-resume frame was frame 171;
4. its host-monotonic timestamp was about 1,958 seconds after the paused
   initialization cohort;
5. `ReanchorRuntime` converted that operator wait into 977 skipped cadence
   ticks.

The emitted channel summary is therefore 75 completed unexpired rounds /
1,053 planned ticks = `0.0712250712`, below the frozen 0.8 gate. During the
actual continuous measurement interval, all 75 started rounds completed
unexpired; `75/75 = 1.0` is diagnostic only and must not overwrite the
create-once summary.

The same missing release origin makes the nominal 150.0017-second simulation
duration unsuitable for the wall-clock duration gate. Twelve pre-resume
records contribute about 0.60 seconds. The first post-launch live capture
(frame 171) to the final tracker capture (frame 3159) spans only
`149.41499996185303 s` by `capture_unix_s` and `149.3966134 s` by the shared
monotonic clock. The user's later continued run cannot extend a tracker
artifact that had already finalized.

This is a phase-boundary/instrumentation defect, not evidence that detector
inference missed its 2-second cadence under load. Reinterpreting the frozen
denominator or accepting the descriptive `75/75` would change a primary
qualification gate after seeing the result, so Codex does not do that.

## Recoverable cleanup and authorization boundary

After the user exited Play, the shared exchange was moved recoverably to
`runtime/test-results/p1-detect-001-qual-2-protocol-invalid-exchange/`.
It contains 7,343 files / 162,236,758 bytes. The logical tree SHA-256 over
sorted relative-path/content-hash pairs is identical before and after:
`d321f164159e433420b923d03b2f41b9e684ec09d73ae5f2aea79d42dccbcde0`.
The canonical run directory was not moved or modified. Live frames and output
slots are empty, while the installed scenario remains in place.

A safe successor requires an explicit non-RATE qualification release boundary
that excludes pre-release retained frames from the re-anchor anchor/tick
origin and starts planned duration on the first acknowledged live frame.
That changes a phase boundary and the cadence/duration qualification
semantics. Per repository policy, implementation and any fresh run ID remain
blocked pending explicit user authorization, a stable candidate, and Sonnet
independent review.
