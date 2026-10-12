# P1-DETECT-001 — Clock Amendment A4 implementation evidence

Date: 2026-07-29

Implementer: Codex

Status: `STABLE_CANDIDATE_cd684fc`

Independent verdict: Sonnet Round 6 `PASS_WITH_NOTES` on candidate `cd684fc`
(`docs/reviews/P1-DETECT-001.md`)

## Trigger and preserved failed attempt

`p1-detect-001-qual-1` is preserved as a consumed, zero-duration failure.
Its exact initialization reached `ReanchorRuntime.initialize()` and then
raised `KeyError: 'capture_monotonic_s'`: ordinary sensor v1 omits the field.
RATE-002 v2 cannot substitute because its Unity value is process-relative
while Python worker completion uses the host system monotonic epoch. No
qualification measurement occurred, and this repair never reuses that ID.

The user exited Play and explicitly authorized the protocol repair. Accepted
requirements are Clock Amendment A4 in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md`.

## Implemented contract

- `SensorFrameWriter` emits ordinary `tethered-sensor-frame/v3` metadata with
  `capture_monotonic_s` from
  `System.Diagnostics.Stopwatch.GetTimestamp()/Frequency` and exact clock ID
  `system-stopwatch/v1`.
- Active RATE-002 sessions still emit v2 using
  `Time.realtimeSinceStartupAsDouble`; no historical RATE behavior changed.
- Python centralizes v3/clock validation in `controller/sensor_protocol.py`.
  The ordinary frame repository validates before image decode; `run_tracker`
  preflights the exact initialization bundle and scenario before tracker/model
  construction, run-ID allocation, or `RunLogger` creation.
- `ReanchorRuntime.after_frame` independently repeats the schema/clock/finite
  non-negative validation. RATE-002 and re-anchor CLI modes are mutually
  rejected before runtime access.
- The two offline scouting readers accept historical v1 plus strictly
  validated v3. The frozen Gate 0 legacy reader is unchanged.
- Models, model hashes, detector/ReID/motion thresholds, stale limit, metrics,
  Unity-truth boundary, scenario geometry and qualification gates are
  byte/semantically unchanged.

## Cross-process clock probe

The same Unity Mono runtime used by the Editor compiled and executed a C#
probe that prints `Stopwatch.GetTimestamp()/Stopwatch.Frequency`. Each
subprocess call was bracketed by Python `time.monotonic()` reads.

- Python implementation:
  `mach_absolute_time()`, monotonic, non-adjustable.
- C# `Stopwatch.Frequency`: `10,000,000`.
- Five of five C# samples fell inside their Python before/after brackets.
- After the first Mono cold start, midpoint deltas ranged from
  `-3.819 ms` to `-3.310 ms`; the cold-start sample also remained inside its
  bracket.

This establishes the shared host epoch on the frozen macOS/Unity Mono
qualification environment; it does not claim cross-machine synchronization.

## Automated evidence

Focused checks completed before candidate formation:

- `.venv-track` tracking-loop tests: 15/15 pass, including v1/wrong-clock
  rejection before model factory/run-directory side effects and RATE-002
  re-anchor incompatibility.
- `.venv-yoloe` re-anchor tests: 18/18 pass.
- Detector scouting tests: 14/14 pass.
- SCENE-004 scouting tests: 22/22 pass.
- Unity focused EditMode
  `TetheredTracking.Tests.RateStudyProtocolTests`: 26/26 pass, including
  v2 preservation, v3 serialization/clock identity and finite monotonic
  advancement.

The candidate commit is added at the stable-candidate handoff. These are
implementer checks, not an independent verdict.

Full regression:

- `.venv-track/bin/python -m unittest discover -s tests -v`: 143/143 pass.
- Unity EditMode, full `TetheredTracking.Tests` filter: 110/110 pass.
- Unity PlayMode, full `TetheredTracking.Tests` filter: 3/3 pass.
- `python3 tools/check_docs.py` and `git diff --check`: pass.

The focused and full Unity XML/log outputs were written outside the repository
under `/private/tmp`; no qualification/session artifact was created.

Implementation candidate: `cd684fcc333a4aee1a9949950c942585df691af5`
(`cd684fc`). This commit is the code/test/design/evidence candidate; the
subsequent handoff-only commit records its hash and does not change runtime
behavior.

## Post-review note closure

Sonnet Round 6's sole note was confirmed and closed without changing runtime
behavior: `tools/benchmark_reanchor.py` now gives synthetic frames the same
central v3 schema/clock constants, with a direct regression test. Full Python
passes 144/144. A real-model 45-frame/5 Hz benchmark completes with 4/4
unexpired detector rounds, cadence rate 1.0, no fatal reason and a clean
worker close; main-loop p50/p95/max are
`10.238/11.469/12.919 ms`. This remains synthetic latency evidence only.

## Sonnet Round 6 review boundary

Review implementation candidate `cd684fc` against the previously pushed
blocker commit `c4e3711`, plus the subsequent handoff-only documentation
commit. Concentrate on:

1. whether ordinary v3 and RATE v2 select the intended clocks without mixing
   epochs;
2. whether every re-anchor entry rejects v1/v2, wrong ID and invalid values
   before model/run side effects and again at runtime;
3. whether the exact-frame/scenario preflight preserves existing run behavior;
4. whether historical scouting v1 remains readable without letting legacy
   frames enter measurement;
5. whether any model, threshold, metric, truth, scene or qualification
   semantics changed outside A4.

Do not run a real qualification or sign Unity validation. Return findings and
an independent verdict to Codex; no dependent implementation starts first.
