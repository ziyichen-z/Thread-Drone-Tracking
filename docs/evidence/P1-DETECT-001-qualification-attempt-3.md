# P1-DETECT-001 qual-3 — Attempt 3 implementer verification

Work ID: `P1-DETECT-001`
Role: implementation — verification material for acceptance to transcribe
into `docs/unity-test-log.md` (read-only to this role)
Date: 2026-07-31
Run ID: `p1-detect-001-qual-3` (reserved, now consumed by this attempt)
Execution candidate: code-equivalent to `ab8ae73`, re-bound by acceptance
in `83d3487` after the step-0 attribution

**Result: all acceptance-6 gates pass.** The disposition is acceptance's
to record; this file only states what was run and measured.

## Gate chain that authorised the run

| Gate | Where |
|---|---|
| DETECT round 8 `PASS` on `f1868dd` | `docs/reviews/P1-DETECT-001.md` |
| Step-0 candidate mismatch raised and returned | `docs/evidence/P1-DETECT-001-qual3-step0-attribution.md` |
| Acceptance attribution + re-bind to `ab8ae73` | `83d3487` |
| User authorization, verbatim | `68d683b` (`docs/authorizations.md`) |
| Acceptance pre-Play step-0 record | `a923ccc` |
| First-pause handoff to implementation | `49f14b1` |

At the operator's first pause the implementation session re-verified
`git status --porcelain` empty and
`git diff --quiet ab8ae73..HEAD -- Assets controller config tools tests`
exit 0.

## Operator sequence as executed

1. Frozen init frame **159**, `simulation_time_s = 7.980127811431885`
   (inside the frozen `[7,8)` window), schema
   `tethered-sensor-frame/v3`, clock `system-stopwatch/v1`.
   Image SHA-256 `ec01f884…f690`, metadata SHA-256 `371f2a35…1706`.
2. Overlay rendered from the qual-1/qual-2 **no-truth manual box**; no
   truth sidecar was read. Overlay SHA-256 `ae3ef095…ebe9`. The user
   confirmed the displayed rectangle.
   Bound init box: normalized
   `[0.5515625, 0.17083333333333334, 0.1125, 0.08958333333333333]`
   = `(353, 82, 72, 44)` px. **Note:** qual-1/qual-2 record `(…, 43)` px;
   float rounding of the same normalized rectangle renders one extra
   bottom row here. A 43 px variant was offered and the user confirmed
   the 44 px overlay that was actually displayed.
3. Tracker started under `--qualification-release-barrier` with
   `.venv-yoloe` (the triple-gated carrier needs torch + ultralytics;
   `.venv-track` has neither). Ready marker published create-once.
4. User resumed for roughly three minutes of HOLD catch-up, then paused a
   second time.
5. Implementation issued `--release-qualification p1-detect-001-qual-3`
   while paused. The user resumed once more and did not pause again; the
   tracker stopped by itself, the user exited Play and **reported no
   Console error**.

## Release-boundary integrity

- HOLD segment: **5,070 frames, 0 published observations, 0 published
  gimbal commands** — no pre-release contamination.
- Boundary `not_before_capture_monotonic_s = 890454.303948041`; first
  frame at or past it is **5229**, `release_monotonic_s = 890558.4885855`,
  `release_simulation_s = 261.48162841796875`.
- Measurement segment: **3,001 frames with a maximum frame-id gap of 1** —
  fully contiguous. This is the qual-2 failure mode and it did not recur:
  qual-2 converted an operator pause into 977 skipped ticks, whereas the
  80 measurement skips here are isolated single frames
  (`skipped_count = 1`) that all stay `TRACKING`.
- Hash chain closes across six artifacts on `command_id`
  `50c1d4dafb194fa5b8466c2282e52241`, `manifest_sha256` `0c443f3a…aaec`
  and `release_frame_id` 5229.

## Measured result

| Quantity | Value | Gate |
|---|---|---|
| release-origin simulation duration | 150.00360107421875 s | ≥150 |
| shared-host monotonic wall duration | 150.00482199992985 s | ≥150 |
| capture unix duration | 150.00500011444092 s | — |
| metrics `elapsed_simulation_s` | 150.05462646484375 s | — |
| complete loops (nominal 31.071067811865476 s) | 4.8278 | ≥4 |
| `C_track_given_geom` | **0.9204277396202087** | ≥0.4 |
| `c_geom` | 1.0 | — |
| incorrect / matched | 158 / 2920 = 0.05410958904109589 | <0.5 |
| unmatched observations | 0 | — |
| LOST / gap / reinit | 0 / 0 / 0 | 0 |
| detector cadence completion | 1.0 (75 of 75 rounds) | ≥0.8 |
| `time_to_first_lost_s` | 150.0, right-censored | — |

Re-anchor decisions, reported as measured: `ROUND_STARTED` 75, `AGREE` 36,
`TENTATIVE` 19, `NO_CANDIDATE` 20. Cadence 19.9993 Hz strictly increasing,
backlog p95 0.0, compute latency p50 14.05 ms / p95 21.21 ms, frame age
p95 67.50 ms, `qualification_metrics_error: null`.

## Immutable artifacts

`runtime/runs/p1-detect-001-qual-3/` (frames.jsonl is 6,100,479 bytes):

| File | SHA-256 |
|---|---|
| `frames.jsonl` | `14171f3d61053c2aa70d155ebfc9b5c5fe3e8ba5c5c08be90dd00f62f7c911fe` |
| `manifest.json` | `0c443f3aad6c70c0638dc1de85a0a9bca55b1e0439fb99d98e81a3b367adaaec` |
| `metrics.final.json` | `24cf230acd2f2badd86ea1968b60fa3e92ee66e67e5ecff53d2c30bba67e1670` |
| `qualification-release-ready.json` | `a79926581668c836ecfe420cab4af26fd9a0bd80a62582d06bc2998d850a9085` |
| `qualification-release-command.json` | `f6243a6c18d046ae8990e35846391a18380d04eb84f102bea1d8183e28786660` |
| `qualification-release-active.json` | `42735e6b500efc59a406e7a0a7a61173dcd689a72e95948922ebf1e6a9adfcce` |
| `qualification-release-ack.json` | `1f9f240f9b18ed419a3bd91c85175e231dfe73ab29859e6d6d7fb2b7130b744a` |
| `qualification-release-provenance.json` | `a42514988d3e1d1b4bf3de7f58050134b832f60889cf56479d9b17f40804508d` |
| `summary.json` | `f09180d8e80d1efe97a06189d98a84e53fe5982944b643241477bed878505dcb` |

Nothing in the directory has been moved or modified since the tracker
exited. The live `runtime/p1_detect_qualification_release.json` pointer is
still present and matches `qualification-release-active.json`; clearing or
archiving it is a separate step and was not performed.

## For acceptance

- Transcribe this as the Attempt 3 execution entry and record the
  disposition; implementation does not declare `PASS`.
- The 44 px vs 43 px init-box difference from qual-1/qual-2 is disclosed
  above and should be carried into the log rather than smoothed over.
- The run consumed the last reserved qualification ID. If the disposition
  is `PASS`, the RATE-003 research-run gate "qual-3 `PASS` + acceptance
  attribution" becomes satisfiable; every other RATE-003 gate (0c, the
  `record-run-gates` artifact, BC-R3-2) is untouched by this run.
