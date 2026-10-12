# P1-M2-RATE-002 rerun stand-down for P1-SCENE-001

Date: 2026-07-27

Disposition: `SUPERSEDED_SCENE_DEFECT` / fail-closed

The user stopped the prepared `UT-P1-M2-RATE-002-002` rerun after the target
route was found to intersect three parked scene vehicles. The active runtime
state was not clean: in addition to the restored immutable `rs2-pilot`
session, it contained a complete five-second release/run transaction. That
transaction is preserved as untrusted scene-defect evidence and is not
promoted to a PASS, qualification, formal attempt, or rate conclusion.

All active B1 material was moved without deletion to:

`runtime/test-results/ut-p1-m2-rate-002-002-rerun-stopped-scene-defect/`

The archive contains:

- the restored `rate_study_session.json` and all release/tracker/evaluator
  runtime slots;
- the installed defective-scene 20 Hz scenario config
  (`sha256=4bddb2f2dcca564bd5637b77e94e6d616d3cf2ca7db85a3060e6599913be79d2`);
- the complete retained frame directory;
- `runs/rs2-pilot/` including release provenance, summary and cutoff metrics;
- the restored `P1-M2-RATE-002-B1` campaign and frozen 20 Hz calibration.

Integrity facts captured at stand-down:

- session SHA-256:
  `74b79e5890c909db1ba5056c787ced71514cebfa38a3a72bcb4c5ed4284b7956`;
- B1 campaign SHA-256:
  `62aaf124113731505fb430922c352a8d801c255bc7ae0d0413b08df792dcab37`;
- B1 20 Hz calibration manifest SHA-256:
  `2406fb8faae113f0026593a3040f8ed21a5e23e98bfb4620ca0673cab216b9c0`;
- deterministic SHA-256 over the sorted per-file hash list:
  `6a1494724f40a72d312a0ed0d4b1aa86200a071bc4e24ee9260a1bf356058d8b`.

No active `runtime/rate_study_session.json`,
`runtime/runs/rs2-pilot/`, or
`runtime/rate-study/P1-M2-RATE-002-B1/` remains; the old
`runtime/scenario_config.json` override is also absent. B1 and its run IDs
must not be restored or reused. The first `P1-M2-RATE-002-B2` campaign smoke
on the corrected scene inherits the pending metrics-cutoff integration objective.
Sonnet Round 6 `PASS` for candidate `9c9ceb9` remains valid; this disposition
is a scene-validity stop, not a reversal of that code review.
