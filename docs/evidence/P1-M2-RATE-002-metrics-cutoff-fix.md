# P1-M2-RATE-002 evaluator cutoff publication fix

Date: 2026-07-26
Candidate: `9c9ceb9`
Focused implementation range: `0a128b4..9c9ceb9`
Status: `IMPLEMENTED_AWAITING_FOCUSED_SONNET`

## Production failure reproduced

`UT-P1-M2-RATE-002-002` used the real pinned NanoTrack-v2, v2 heartbeat,
coordinator, Unity release receiver and immutable provenance chain. The
release transaction and tracker run succeeded, but the authoritative
evaluator snapshot failed the accepted one-frame duration bound:

| Artifact value | Result |
|---|---:|
| Tracker `actual_duration_s` | `5.040644030118151` |
| Immediate `metrics.final.elapsed_simulation_s` | `4.3017754554748535` |
| Deficit | `0.7388685746432975 s` |
| 20 Hz tolerance | `0.050001 s` |

The run otherwise had 101 measurement records, 19.996874 Hz monotonic capture,
zero LOST/gap/reinit, backlog p95 0 and compute p95 6.534 ms. Release backlog
was 1 and `validate_provenance()` passed. The live root evaluator later
reported `9.300001 s`, proving that the copied 4.301775 s document was stale
rather than the accumulator stopping early.

Local raw evidence is preserved under
`runtime/test-results/ut-p1-m2-rate-002-002-batch-b-integration/`.
Key frozen artifact hashes:

| Artifact | SHA-256 |
|---|---|
| run manifest | `ce8e05853bd0e4e9166f0cf57f95a38196c95158a3971e0638aa321d8fcc2c3f` |
| release provenance | `09ddad32237d24a8f64ee01b19dc093216a06609c445cbfdcfa24e43af142c64` |
| tracker summary | `661af141fb93776d54e6537717b542455a73e997db2a3cacb895a6316071de64` |
| stale metrics snapshot | `6e999a722d9bff0e08ed1cb90159121f7ed1753b7d68de5c743d19698d830ee7` |

No `qualification.json`, `rate2-status.json`, failed-attempt receipt or active
`runtime/runs/rs2-pilot/` remains, so the smoke did not consume the formal
qualification pilot or its retry budget.

## Root cause

`CoverageEvaluator.RecordFrame()` updates the in-memory duration and metric
integrals on every accepted sensor frame. Before this fix, the public
`runtime/metrics.json` document was written only by a one-second `Update()`
timer. `TrackLoop` snapshots that public file immediately when its
release-origin planned duration is reached. It can therefore copy a document
up to roughly one second older than its own cutoff even while evaluator memory
is current.

Waiting for a later periodic document or widening the admission tolerance was
rejected: both approaches can include post-cutoff frames for which the tracker
has stopped publishing, biasing `C_track` downward.

## Fix

`CoverageEvaluator.OnFramePublished()` now immediately performs the existing
atomic metrics write after every frame accepted by an active RATE-002
measurement gate. HOLD frames and the release boundary remain excluded by
`AcceptsMeasurementFrame()`. Ordinary/non-RATE sessions retain the existing
one-second publication cadence. Metric formulas, accumulated inputs, release
protocol, and JSON schema are unchanged.

The added Edit Mode regression checks all four policy boundaries:

1. HOLD frame: no immediate write;
2. release boundary frame: no immediate write;
3. first post-release measurement frame: immediate write required;
4. ordinary session: retain periodic publication.

## Implementer verification

| Check | Result |
|---|---|
| Unity Edit Mode | `45/45` passed; new regression explicitly present and Passed |
| Unity Play Mode | `2/2` passed |
| Python full suite | `69/69` passed |
| Python compilation | `py_compile controller/*.py tools/*.py tests/*.py` passed |
| Environment | `pip check`: no broken requirements |
| Patch integrity | `git diff --check` passed |

Raw XML hashes:

- Edit Mode:
  `0ee05785a9f88328545a075b9f410f52ddb88b384521eecf9a01b7537981b2d5`
- Play Mode:
  `f8ffc801ae2353aff6537f9da4988553ef742ee6a861aeb6412e5c32537b560c`

## Remaining gate

Sonnet must independently review candidate `9c9ceb9`, focused range
`0a128b4..9c9ceb9`, including whether per-accepted-frame publication is the
correct non-contaminating cutoff mechanism and whether ordinary 1 Hz behavior
is preserved. After PASS, rerun only `UT-P1-M2-RATE-002-002`; the formal
30-second qualification pilot remains blocked.
