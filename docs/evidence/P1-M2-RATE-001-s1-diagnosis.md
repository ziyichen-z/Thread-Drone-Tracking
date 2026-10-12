# P1-M2-RATE-001 — S1 measurement-window diagnosis

Date: 2026-07-24
Status: amendment accepted, implemented in candidate `fad91da`, and
independently verified by Sonnet Round 4 `PASS`; measured sessions may resume

## Finding

The pre-amendment generated summaries classified `rate20-follow-r1/r2` as
`rate_sustainable=false`, but the raw evidence does **not** show sustained
capture below 19 Hz. The former S1 formula included the mandatory operator
pause between staging and launch.

The accepted workflow selects an initialization frame, pauses Unity, displays
the frozen box, waits for explicit user confirmation, and only then launches
the tracker. `frames.jsonl` begins with that retained pre-confirmation frame.
The former whole-run calculation,
`(N-1)/(last_capture_unix_s-first_capture_unix_s)`, therefore counts the
operator-confirmation pause as if Unity were attempting and failing to capture
frames.

## Raw evidence

| Run | Raw whole-span rate | Largest wall gap | Frames around gap | Simulation gap | First-frame age |
|---|---:|---:|---|---:|---:|
| `rate20-follow-r1` | 14.62035980 Hz | 99.03100014 s | 285 → 286 | 0.05522251 s | 92.5817 s |
| `rate20-follow-r2` | 15.65336809 Hz | 74.75700021 s | 273 → 274 | 0.06702328 s | 67.8996 s |

The wall clock advances by 75–99 s across each gap while Unity simulation
advances only 55–67 ms. This is a paused-editor interval, not slow continuous
capture. The ordinary interval diagnostics agree: median is 50 ms and p99 is
about 55–56 ms in both runs.

The run manifest already records `created_unix_s` when the tracker launch
begins. Restricting the existing raw `capture_unix_s` values to frames captured
at or after that timestamp yields the first post-unpause continuous segment:

| Run | First eligible frame | Eligible samples | Corrected continuous rate | Largest eligible gap |
|---|---:|---:|---:|---:|
| `rate20-follow-r1` | 286 | 5235 | 19.99969431 Hz | 0.12000012 s |
| `rate20-follow-r2` | 274 | 5247 | 20.00076252 Hz | 0.12899995 s |

Both are above the pre-registered 19 Hz floor. S2 and S3 also pass in both
runs. Consequently, the pre-amendment generated `sustainable=false` values
were invalid S1 verdicts caused by a measurement-window defect; they are not
evidence that this computer cannot sustain the 20 Hz simulation.

## Root cause

`controller.run_log._cadence()` correctly implements the accepted whole-span
formula. The defect is at the design boundary: the formula defines the
admitted span from the staged initialization frame, while the operating
protocol deliberately inserts an unbounded human confirmation pause after
that frame. The tool faithfully measures a contradictory specification.

No raw artifact is corrupt, and no run needs to be deleted. The preserved
timestamps are sufficient for deterministic re-analysis.

## Proposed amendment

For S1 only, define the eligible capture cohort before looking at its rate:

1. read `manifest.created_unix_s`;
2. select finite `capture_unix_s >= created_unix_s`;
3. require at least two strictly increasing eligible samples;
4. compute `(N-1)/(last-first)` and interval p50/p95 on that cohort;
5. record the cutoff, first eligible frame, eligible/excluded sample counts,
   and corrected cadence in the generated evidence.

This uses a timestamp frozen before the user unpauses and excludes only frames
captured before tracker launch. It does not remove mid-run stalls: any pause or
slowdown after the first eligible frame remains inside the S1 span.

Required regression tests:

- a large pre-launch retained-frame gap is excluded;
- a genuine mid-run gap still lowers S1 and fails the 19 Hz floor;
- missing/non-finite cutoff or fewer than two eligible samples fails closed;
- the raw whole-span cadence remains reported as a diagnostic;
- existing r1/r2 artifacts re-summarize to the values above.

Because this changes accepted time semantics and the S1 decision path, Codex
must not implement and self-approve it silently. It requires explicit design
acceptance, automated tests, a stable candidate, and focused Sonnet
independent review before r3 or any 20 Hz nadir session.

## Implemented candidate

The user accepted the amendment on 2026-07-24. Candidate `fad91da`:

- preserves `wall_clock_capture_cadence` as the raw whole-span diagnostic;
- adds `wall_clock_capture_cadence_post_launch` and an explicit window record
  containing cutoff source/value, eligible/excluded counts, and first eligible
  frame/time;
- makes S1 consume only the post-launch cadence and fail closed when it is
  absent or insufficient;
- retains every cutoff-and-later stall in the S1 span;
- reports raw and S1 rates side by side in generated Markdown.

The full pinned Python suite passes 43/43; byte compilation, `pip check`, and
`git diff --check` pass. Deterministic re-finalization of the preserved r1/r2
artifacts gives exactly the corrected values above. Copies of both prior
summaries remain as `summary.pre-s1-amendment.json`. No Unity rerun is required
for those two runs.

## Independent verification

Sonnet Round 4 returned `PASS` for `3cb0655..fad91da`. The reviewer reran
43/43 tests, checked the fail-closed and mid-run-stall cases, independently
recomputed both real rates from raw `frames.jsonl` and `manifest.json`, and
verified that the pre-amendment backups remain intact. There were no blocking
or actionable non-blocking findings. The S1 time-semantics gate is closed and
the remaining four measured sessions may resume.

## Tracking result unaffected

This S1 correction does not improve the tracker result. Both 20 Hz follow runs
still have `C_track=0` and first LOST near 3.45 s, essentially the same
physical failure time as the 5 Hz cells. The eventual SOT-upgrade decision
must wait for a valid completed 20 Hz follow cell, but the current evidence
already indicates that raising the simulation sampling rate alone did not
rescue CSRT.
