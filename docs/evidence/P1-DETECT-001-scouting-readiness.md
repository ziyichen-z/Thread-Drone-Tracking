# P1-DETECT-001 scouting readiness audit

Date: 2026-07-28  
Role: Codex (implementation/readiness audit)  
Candidate entering the audit: `0434de3` (Sonnet Round 2 `PASS`)

## Outcome

The accepted §8 scouting gate is **not yet executable as a formal go/no-go
measurement**. No admissible non-measurement validation capture currently on
disk covers the remote segment, and the accepted proposal does not freeze four
definitions that determine the recall denominator and result.

No scouting result was computed, no old measurement frame was reused, no
geometry was changed, and no qualification or successor campaign was started.

## Disk evidence checked

- `runtime/test-results/ut-p1-m2-rate-002-002-b2-smoke/calibration-hold/frames/`
  contains 98 JPEGs and 99 metadata documents, ending at frame 97 /
  `simulation_time_s=4.881182670593262`. This is a short HOLD smoke and does
  not reach the remote route segment.
- The retained `rs2-r20-follow-*` and archived B2 formal artifacts are
  RATE-002 measurement data. Proposal §8 explicitly requires validation-session
  frames (non-measurement data), so those frames are inadmissible for scouting.
- Current `CoverageEvaluator` output exposes aggregate/current visibility and
  target-box area, but not the per-frame target/distractor boxes needed to
  score detector recall and target-vs-distractor embedding similarity.
  Controller sensor frames correctly contain no Unity truth.

## Binding definitions still required

Before looking at a new validation capture, the following must be frozen:

1. the exact remote-visible frame set (geometric segment/range and visibility
   rule);
2. deterministic sampling cadence and phase, including missing-frame handling
   and the denominator;
3. the IoU rule that turns a frozen YOLOE proposal into a target recall hit;
4. the exact reference crop used for target/distractor DINOv2 cosine
   distributions.

These are not harmless report formatting choices: each can change whether
recall crosses the pre-registered `0.5` gate. Codex therefore did not invent
them after inspecting available frames.

## Recommended clarification for user approval

- Use one dedicated, explicitly non-measurement 20 Hz follow validation
  session covering one complete `106.485 s` route loop.
- Let `CoverageEvaluator` be the only Unity-truth consumer and, only in this
  validation mode, export an immutable per-frame truth sidecar. The offline
  scouting tool may read the sidecar; the controller and re-anchor runtime may
  not.
- Define remote-visible samples as evaluator-visible target frames whose
  camera-to-target slant range is at least `65.0 m`; sample at `2 Hz` on fixed
  simulation-time half-second ticks, selecting the first published frame at or
  after each tick. Missing image/truth pairs remain in the denominator and
  fail closed as misses.
- Count recall when at least one frozen YOLOE proposal (`conf >= 0.25`) has
  IoU `>= 0.30` with the evaluator target box. Use the exact run initialization
  target crop as the DINOv2 reference, and report its cosine against the target
  box and every marked distractor box at each sampled frame. Do not tune
  `tau_reid=0.5` or `m_margin=0.1` from these distributions.

This recommendation preserves proposal §8's `recall >= 0.5` go rule and the
existing truth boundary, but it is a binding measurement clarification and
therefore requires the user's explicit decision before implementation or data
capture.
