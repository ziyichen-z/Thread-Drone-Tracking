# P1-M2-RATE-002 Batch B implementer evidence

Date: 2026-07-25  
Candidate: `045eb38`  
Review range: `a662af3..045eb38`  
Status: `ROUND_4_PASS; ORDER_FIX_AWAITING_FOCUSED_SONNET`

## Implemented scope

- `controller/rate2_protocol.py`
  - validates the frozen RATE-002 session/tracker/model/init identity;
  - publishes atomic `p1-rate2-tracker-ready/v2` heartbeats after every
    processed frame with monotonic `seq`, processed count, last frame, declared
    1 s interval and same-host monotonic timestamp;
  - performs coordinator-side latest→ready consistency checks, freshness and
    `0 <= backlog <= 1` prefiltering;
  - constructs release commands from the exact ready bytes, validates the
    exact command/ack/ready hash chain, and creates immutable command, ack and
    `p1-rate2-release-provenance/v1` archives;
  - rejects missing, mismatched, non-finite or tampered identity/clock/hash
    evidence.
- `controller/track_loop.py` and `controller/run_log.py`
  - select sensor metadata v2 only for explicit RATE-002 sessions while
    retaining v1 behavior for ordinary/RATE-001 runs;
  - keep HOLD records diagnostic and suppress Python body/gimbal publication
    until the acknowledged release boundary;
  - switch records to `phase="measurement"` only when
    `capture_monotonic_s >= release_monotonic_s`;
  - measure completion, actual duration and first LOST from the ack release
    baseline; exclude HOLD records from outcomes, latency and backlog;
  - require a valid immutable provenance chain before RATE-002 finalization and
    fail closed on missing/non-finite/non-increasing/epoch-incompatible
    monotonic capture evidence.
- `tools/run_rate_study.py`
  - retains v1 as the legacy default but makes the real `_frame_candidates()`
    consumer explicitly accept v2 and reject v1 in a RATE-002 context.
- `tools/run_rate2_study.py`
  - freezes the campaign before data with `trigger_branch="stop"` and the
    accepted session order;
  - provides unlimited-HOLD v2 calibration overlay preview and immutable
    confirmed calibration artifacts, and binds pilot/formal launches to the
    frozen reference box/frame/hash;
  - coordinates advancing-heartbeat release with no operator pause between
    final read and command, archives failure diagnostics, and validates the
    ack before provenance creation;
  - finalizes per-run admission with release-origin evaluator/tracker duration,
    v2 monotonic S1′, S2/S3 for 20 Hz, and four-way artifact hashes;
  - implements the five frozen 20 Hz follow pilot gates;
  - preserves failed run directories with immutable receipts, enforces an
    initial attempt plus at most two reruns, and requires that evidence before
    `BLOCKED_INVALID_CELL`;
  - generates create-once `decision_a.json`, recomputes R1′/R2′/R3′ and
    sensitivity values from three admissible runs, records actual execution
    order, and gates the fourth measurement plus 5 Hz calibration on a
    validated non-trigger result.

## Implementer verification

| Check | Result |
|---|---|
| Full Python suite | `69/69` passed |
| RATE-002 focused suite | `14/14` passed |
| Python compilation | `python -m py_compile controller/*.py tools/*.py tests/*.py` passed |
| Environment consistency | `pip check`: no broken requirements |
| CLI surface | `python -m tools.run_rate2_study --help` passed |
| Real NanoTrack identity/prepare smoke | local pinned models loaded; campaign and `rs2-pilot` session emitted tracker identity `51b58a…beda8e` and model identity `fe6505…f4d23` |
| Patch integrity | `git diff a662af3..045eb38 --check` passed |

The 14 new tests directly cover:

- v2 acceptance and v1 rejection at both real schema enforcement points;
- geolocation tolerance of the added monotonic field;
- full batch/tracker/scenario/hash identity rejection;
- healthy, non-advancing, stale, future-clock and backlog heartbeat paths;
- exact ready bytes, command, ack and provenance hashes plus tamper detection;
- coordinator release and immutable provenance archive;
- pre-release control suppression, HOLD/measurement record phases and
  release-origin completion;
- a deliberately long HOLD excluded from every outcome and clock aggregate;
- non-increasing post-release monotonic capture rejection;
- v2 calibration preview/freeze and pilot session binding;
- evaluator cutoff and four-artifact per-run status binding;
- conservative zero-matched/zero-geometry rule inputs;
- qualification/ordered-session gates, Decision A continue/stop/invalid-cell
  tri-state behavior, create-once idempotency and attempt-limit evidence.

## Not yet verified

- No real Unity session was launched for Batch B. The earlier Batch A Unity
  gate proves Unity's release receiver and ack writer, but the new live Python
  heartbeat/coordinator/TrackLoop/provenance chain still requires independent
  code review followed by a focused Unity integration case.
- The shared 30.0 s 20 Hz follow qualification pilot remains blocked until
  that review and focused integration gate pass.
- `ruff` is not installed in `.venv-track`; it was attempted and is not
  counted as passed evidence. `py_compile`, the full tests, `pip check` and
  diff checks are the actual implementer checks.

## Requested independent review

Sonnet should review candidate `045eb38`, range `a662af3..045eb38`, against the
accepted RATE-002 proposal §§2/4/5/7–10 and A1. Particular attention is
requested for:

1. Python and Unity monotonic epochs and the backlog-1 release-boundary frame;
2. exact-byte/hash/provenance immutability and fail-closed paths;
3. HOLD exclusion from commands, duration, LOST, latency, backlog and S1′;
4. real v2 consumer selection without changing RATE-001;
5. calibration/pilot identity binding and frozen session ordering;
6. R1′/R2′/R3′ boundary values, right censoring, attempt exhaustion,
   Decision A create-once semantics and execution gates.

No pilot, measurement or dependent implementation starts before the verdict.

## Post-Round-4 fixed-order gate closure

Date: 2026-07-25
Candidate: `9d33dab`
Focused implementation range: `6d77bc0..9d33dab`
Semantic code delta from the reviewed Batch B candidate: `045eb38..9d33dab`

Codex did not accept Round 4 note 1 as an intentional asymmetry. Accepted
proposal amendment A1 says the complete execution order is frozen, not only
the three 20 Hz follow runs. Candidate `9d33dab` therefore:

- defines one explicit `FORMAL_RUN_ORDER` used to construct the unchanged
  campaign `SESSION_ORDER`;
- requires every formal run before the requested session to have a fully
  admissible, hash-bound status before the next session is authorized;
- applies that requirement to 20 Hz nadir, the 5 Hz calibration boundary,
  5 Hz follow, and 5 Hz nadir, while retaining the qualification and
  Decision A gates;
- reuses `attempt_row()` so predecessor admission revalidates the manifest,
  release provenance, summary and metrics hashes instead of trusting only an
  `admissible=true` flag.

The regression test exercises the original defect directly: without a
`rs2-r20-nadir-1` artifact, authorization of both
`rs2-r20-nadir-2` and `rs2-r5-calib` must fail. It then constructs each
remaining admissible predecessor in the frozen order and verifies every
subsequent session is authorized.

Post-fix checks:

| Check | Result |
|---|---|
| RATE-002 focused suite | `14/14` passed |
| Full Python suite | `69/69` passed |
| Python compilation | `python -m py_compile controller/*.py tools/*.py tests/*.py` passed |
| Environment consistency | `pip check`: no broken requirements |
| Patch integrity | `git diff --check` passed |

Round 4 notes 2 and 3 remain accepted as non-blocking: Unity may ignore the
extra heartbeat interval field while the byte/hash chain stays exact, and
the accepted design makes HOLD-period look-at computation optional. No Unity
integration or qualification pilot starts until Sonnet independently reviews
this focused scheduling fix.
