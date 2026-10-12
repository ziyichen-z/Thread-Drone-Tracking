# P1-DETECT-001 Release Boundary Amendment A5 — implementation evidence

Date: 2026-07-29
Work ID: `P1-DETECT-001`
Scope: non-RATE qualification release boundary only
Implementer: Codex
Independent verdict: **PENDING SONNET**

## Authorization and frozen boundary

Qual-2 remains immutable
`PROTOCOL_INVALID_RELEASE_BOUNDARY`; its descriptive tracking result did not
change any threshold or denominator. After Codex disclosed that the repair
changes phase and primary qualification duration/cadence gates and therefore
requires a new Sonnet stop, the user explicitly authorized proceeding.
Release Amendment A5 is recorded and accepted in
`docs/proposals/P1-DETECT-001-detector-reanchor-carrier.md`; formal design
baseline is v0.3.8.

The batch does not change model/weight identity, detector/re-anchor thresholds,
stale limits, main metric formula, scene geometry, hardware target, historical
RATE-002 evidence, or the numeric acceptance-6 gates. It does not prepare or
run qual-3.

## Implemented protocol

- `controller/qualification_protocol.py` defines a qualification-only
  create-once ready → command → active marker → first-frame ack → provenance
  chain. Manifest, ready, command and active marker bytes are SHA-256 bound;
  ready/command Unix and shared host-monotonic ordering is checked; replay
  after acknowledgement and a different active runtime slot fail closed.
- `controller/track_loop.py` adds an explicitly gated
  `--qualification-release-barrier` and a separate
  `--release-qualification RUN_ID` mode. Before the command boundary,
  initialization/retained/backlog frames are HOLD: SOT may catch up in order,
  but observation/gimbal publication and re-anchor release are suppressed.
  The first ordinary v3 frame at or beyond the command's host-monotonic
  boundary defines simulation elapsed, monotonic wall elapsed, re-anchor,
  control and run-log measurement origin.
- Completion requires both release-origin simulation and monotonic wall spans
  to reach the planned duration. `controller/run_log.py` uses the monotonic
  span for `actual_wall_duration_s`; the Unix span remains separately reported
  as `actual_capture_unix_duration_s`.
- `QualificationReleaseGate.cs`, called only inside `CoverageEvaluator`,
  validates the same active marker, command and bound manifest/ready bytes.
  When it observes the marker it clears every pre-release truth aggregate and
  begins again on the exact first frame meeting the same monotonic boundary.
  No Unity truth leaves `CoverageEvaluator`.
- `metrics.json` carries
  `p1-detect-qualification-metrics-origin/v1` with the run, command, active
  marker hash and release frame/simulation/monotonic origins. Python refuses
  the final metrics snapshot unless this identity matches its ack and the
  evaluator duration reaches the plan. The top-level active marker is cleared
  only after a valid snapshot and finalized summary; all run-local artifacts
  remain immutable.

## Direct tests

Python qualification tests cover:

- create-once command/marker publication and idempotence before ack;
- stale retained frames remaining HOLD and the first fresh frame becoming the
  sole simulation/wall origin;
- command/ready/manifest/ack/provenance tamper rejection;
- Unity metrics-origin mismatch and short-duration rejection;
- active pointer cleanup without deleting the run-local marker;
- finalization excluding HOLD frames from duration, cadence and event counts.

Tracking-loop tests directly assert no pre-release observation/gimbal output,
no pre-release re-anchor release, first release-frame publication, dual-span
completion and CLI rejection before tracker/model/run side effects.

Unity `QualificationReleaseEditModeTests` directly assert:

- marker discovery resets at most once and uses the first host-monotonic
  boundary frame;
- observations are blocked until that frame;
- a changed hash-bound ready artifact fails closed;
- evaluator reset removes all pre-release frames, observations and durations.

## Implementer regression evidence

- `.venv-track/bin/python -m unittest discover -s tests -v`:
  **151/151 pass**.
- `.venv-yoloe` focused re-anchor: **18/18 pass**.
- `.venv-yoloe` detector scouting: **14/14 pass**.
- `.venv-yoloe` SCENE-004 scouting: **22/22 pass**.
- Unity 6000.4.10f1 focused
  `QualificationReleaseEditModeTests`: **3/3 pass**.
- Unity full EditMode `TetheredTracking.Tests`: **113/113 pass**.
- Unity full PlayMode `TetheredTracking.Tests`: **3/3 pass**.
- `git diff --check`: pass.

Unity 6000.4.1f1 could not complete its headless licensing handshake with the
currently running 1.18.1 licensing client. Tests were therefore run with the
installed 6000.4.10f1 editor previously used for repository diagnostics. Its
automatic package/project-version updates were reverted; no dependency or
project-version change is part of the candidate.

## Stable-candidate stop and Sonnet scope

Implementation candidate:
`705c4428e86998a152ab3e7b276be202c9a263ae` (`705c442`). The subsequent
handoff-only commit changes no runtime behavior. Sonnet must independently
review the candidate code, not trust this summary, and cover:

1. exact ready/command/active/ack/provenance byte/hash and create-once chain;
2. Unix + host-monotonic ordering and first-v3-frame origin agreement between
   Python and Unity;
3. HOLD exclusion from observation/control, re-anchor, logs, cadence/duration
   and all `CoverageEvaluator` truth aggregates;
4. dual simulation/monotonic-wall completion and metrics-origin fail closure;
5. RATE-002/v2 isolation, historical v1 scouting compatibility and unchanged
   model/threshold/metric/scene/hardware scope;
6. full diff audit that Unity truth remains confined to
   `CoverageEvaluator`.

This evidence is implementer evidence, not an independent review. Codex stops
at the pushed candidate; qual-3 remains unprepared and forbidden until Sonnet
returns a passing verdict.

## Round 7 B2 repair

Round 7 independently confirmed the intended release chain and all original
test counts, but returned `REWORK_REQUIRED` because a valid active pointer
retained after a failed attempt was unconditionally consumed by every later
`CoverageEvaluator`. Sonnet directly reproduced both consequences: an
exception in a different scenario and silent aggregation reset/foreign run
identity in a later ordinary SCENE-004 session.

The fix scopes gate ownership to the current Unity evaluator session without
changing the accepted clean qualification transaction:

- the gate records evaluator-session Unix and shared host-monotonic start
  values at construction;
- marker scenario must match, and the referenced command's `issued_unix_s`
  and `not_before_capture_monotonic_s` must both be strictly later than those
  session starts before the gate may arm;
- foreign, old or structurally unusable markers are cached as inert for the
  current session, so frames remain `Ordinary`, observations stay allowed,
  aggregation is untouched and `MetricsOrigin` remains null;
- a current-session marker still passes the original full marker/command/
  manifest/ready hash validation; changed bound ready bytes still throw and
  fail closed.

Two permanent EditMode regressions reproduce the Round 7 cases directly.
`ForeignMarker_IsInertForDifferentScenario` proves no exception, observation
block or metrics identity. `StaleMarker_CannotHijackSameScenarioSession`
proves the old marker remains `Ordinary`, does not block observations, leaves
`MetricsOrigin` null and preserves an already populated evaluator aggregate.

Post-fix implementer evidence:

- Python full: **151/151 pass**.
- `.venv-yoloe`: **18/18 + 14/14 + 22/22 pass**.
- `.venv-yoloe` dependency check: **42/42 compatible**.
- Unity focused qualification EditMode: **5/5 pass**.
- Unity full EditMode: **115/115 pass**.
- Unity full PlayMode: **3/3 pass**.
- `git diff --check`: pass.

The fixed implementation candidate is
`f1868dd1dcaf269918cc7a666339f709058580db` (`f1868dd`). Round 8 should
review only B2's evaluator-session freshness/
ownership behavior and the two new regressions unless the diff shows broader
scope. Qual-3 remains unprepared.
