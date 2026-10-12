# P1-M2-RATE-001 — final-run wall-clock regression diagnosis

Date: 2026-07-24  
Status: `DIAGNOSIS_COMPLETE_DECISION_REQUIRED`  
Affected run: `runtime/runs/rate20-nadir-r3/`

## Finding

All 12 predeclared measured-session artifacts exist. The final run completed
the planned simulation duration and passed the compute/backlog checks, but its
post-launch capture timestamp series contains one backwards wall-clock step.
The frozen S1 rule requires a strictly increasing wall-clock series, so the
generated study decision correctly fails closed as
`BLOCKED_RATE_UNSUSTAINABLE`.

This is a clock-integrity anomaly, not evidence of a 20 Hz capture stall:

| Transition | Capture Unix time | Delta | Simulation time | Delta |
|---|---:|---:|---:|---:|
| frame 3782 → 3783 | 1784937968.747 → 1784937968.718 | **-0.029000 s** | 189.130997 → 189.184097 | +0.053101 s |

The surrounding positive capture intervals are normal. Across the final run,
positive intervals have a median of `0.04999995 s`; the diagnostic
first-to-last rate is `20.00676907 Hz`. These diagnostics do not override the
registered strict-increase condition.

## Cross-run audit

- Eligible post-launch samples across all 12 sessions: `39,292`.
- Non-increasing adjacent capture pairs in the other 11 sessions: `0`.
- Non-increasing adjacent capture pairs in `rate20-nadir-r3`: `1`.
- Simulation timestamps in the affected transition remain strictly
  increasing.

The current Unity publisher records capture time with
`DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0` in
`SensorFrameWriter.cs`. This civil wall clock can be adjusted by the operating
system. The existing frame contract does not also publish a monotonic capture
clock, so the saved artifact cannot retrospectively recover an authoritative
monotonic timestamp.

## Final-run evidence

```text
classification=COMPLETE
admissible=true
tracker_exit_code=0
actual/planned_duration_s=269.0019464492798/268.97056274847716
duration_complete=true
total_frame_records=5381
simulation_rate_hz=19.999855283628577
post_launch_wall_rate_hz=null
post_launch_wall_strictly_increasing=false
compute_latency_p50/p95_ms=5.299896001815796/6.513056575204246
backlog_p50/p95=0/0
gap_events=0
reinit_required_records=0
artifact_errors=[]
C_track=0
C_geom=0.1691424399614334
C_track_given_geom=0
time_to_first_lost_s=3.4502573013305664
```

The run is structurally complete and remains preserved. The strict study
summary reports:

```text
decision.status=BLOCKED_RATE_UNSUSTAINABLE
missing=[]
duplicates={}
invalid=[]
unexpected=[]
```

## Effect on the tracking conclusion

The clock anomaly does not improve or weaken CSRT accuracy. If the
sustainability gate were independently cleared, both pre-registered SOT
trigger predicates would be true:

- 20 Hz follow median `C_track_given_geom=0`, below `0.25`.
- 20 Hz follow median first LOST is `3.45044184 s`, below one route loop
  (`104.48528137 s`).

These are diagnostic observations only while the overall decision is blocked.

## Decision paths

1. **Keep the frozen result blocked.** This is the literal current-protocol
   outcome and requires no semantic change.
2. **Adopt an explicit clock-invalid retry amendment.** Preserve this run as a
   clock-invalid artifact, define a backwards civil-clock step as an invalid
   instrumentation session rather than rate unsustainability, and recollect
   only `rate20-nadir-r3`. This is the shortest recovery, but the same civil
   clock remains vulnerable.
3. **Add a versioned monotonic capture timestamp.** Keep Unix time for
   correlation, add a monotonic field for cadence, update the contract and
   tests, and decide which sessions must be recollected. This is the robust
   long-term fix, but it changes time/frame semantics and therefore requires
   accepted design, a stable candidate, and Sonnet review before more Unity
   evidence is admitted.

Codex will not silently choose path 2 or 3, retry the run, or relax the frozen
S1 rule. The retained artifacts and this diagnosis are the handoff for an
explicit decision.
