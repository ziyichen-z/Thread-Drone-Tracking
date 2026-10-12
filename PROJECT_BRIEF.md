# Tethered Drone Tracking

## Research starting point

Phase 1 started from one tethered drone tracking one moving ground vehicle in a
city (the tether is a historical setting from the earlier two-drone design). The
camera gimbal and aircraft body are independent control channels. With the
tether enabled, the body is constrained by a fixed ground anchor, tether length,
altitude, speed, and acceleration limits. `P1-ENG-FRAME-001` makes the tether
switchable and the new mainline default untethered: an operator-declared
geofence, the altitude band, speed/acceleration limits and body obstacle
clearance replace the cable workspace (implemented to the K2 candidate;
independent review and Unity validation pending, see `docs/current-status.md`).

The primary outcome is correct-identity tracking coverage (`C_track`). Physical
visibility (`C_geom`) is a diagnostic upper bound, and `C_track_given_geom`
separates perception failure from unavoidable occlusion. Unity ground truth is
evaluator-only and must never enter perception or control inputs.

The authoritative research design is
`docs/phase1-single-drone-design.md`. Current progress and role handoffs are in
`docs/current-status.md`; this brief intentionally does not duplicate live task
state.

## Default simulation contract

The mainline default is versioned in `config/scenario.untethered.json` (tether
off, geofence x 110-190 m, z 50-130 m). Three entry points select it when
nothing else is given: Unity `ScenarioConfig.Load()` without
`runtime/scenario_config.json`, the `tools/run_track_experiment.py` default,
and the Python effective-scenario resolver; `controller/track_loop.py` always
takes scenario files explicitly. The tethered configuration stays byte-identical
in `config/scenario.default.json` and is used by passing that path explicitly or
through a `runtime/scenario_config.json` override, which always wins.

- Unity `6000.4.1f1`, URP.
- Anchor: `(132, 0.2, 117)` metres in Unity world coordinates.
- Initial drone altitude: `25 m`.
- Tether length (tethered scenarios only): `35 m`; altitude range: `8-32 m`
  (capped by the tether length only when tethered).
- Maximum body speed: `4 m/s`.
- Gimbal: independent pointing, `45 deg` maximum off-nadir.
- Target: one red vehicle on a configurable route; the current default route is
  deterministic.
- Sensor: `640x480`, `60 deg` vertical FOV, `5 Hz` frame export by default.

## Scope discipline

- SOT, YOLOE, ReID, search, planning, and optional VLM are staged components,
  not assumptions of the initial integration smoke test.
- The active Phase 1 work is desktop simulation: Unity plus isolated local
  Python inference. TensorRT, CUDA, and Jetson packages are not current
  dependencies and must not be installed or treated as M0-M6 blockers.
- In tethered scenarios Phase 1 uses a kinematic tether-sphere workspace
  approximation (taut-tether assumption); it does not yet claim tension, sag,
  reel, or aerodynamic fidelity. Untethered scenarios have no cable model.
- Phase 2 extends the validated single-drone interfaces toward geometry-driven
  two-drone handoff and a distilled policy for an 8GB Jetson Orin Nano.
  Hardware deployment is a later M7 track that starts only when the user
  explicitly activates it.
- Work follows `docs/collaboration-workflow.md`: Fable proposes, Codex reviews
  and implements, Sonnet independently verifies, and the user validates Unity.
