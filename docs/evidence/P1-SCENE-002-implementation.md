# P1-SCENE-002 implementation evidence

Date: 2026-07-27

Implementer: Codex

Gate: stable implementation candidate `4fcd6d3` over
`7818edf..4fcd6d3`. Independent Sonnet review and `UT-P1-SCENE-002-001`
remain pending.

## Implemented behavior

- The clockwise/right-hand target route is redrawn at a measured 2.5 m lane
  offset, with 3 m diagonal corner transitions. Its eight points use road
  surface `y=0.2 m`, perimeter `212.97056274847714 m`, and one-loop time
  `106.48528137423857 s` at the unchanged 2 m/s target speed.
- `config/road_data.json` is the single versioned road-data source. All four
  checked-in scenario configs bind its exact bytes with SHA-256
  `111e0759d4b52821d08ce4ddd1aae3fc8cc8d24e12e6fa62513403c00b401894`.
  Missing bytes, hash mismatch, unknown schema/class/group, duplicates,
  missing active-scene footprints, and unsupported transforms fail closed.
- Road legality samples the complete closed route every 0.5 m, requires each
  point to lie in a measured asphalt patch, and checks the configured target
  bottom against that patch's surface height. The target bottom offset is
  `0 m`; measured renderer height is `1.55 m`; vertical clearance margin is
  `0.5 m`.
- Static-scene legality transforms each precomputed local ground/full
  footprint by its instance translation, yaw, and exact uniform or
  non-uniform scale. Version 1 deliberately rejects zero/non-finite scale and
  pitch/roll rather than approximating. The real scene contains non-uniform
  scale (for example `Natures_Grass Bar`, 1×1×2.85), and the full audit
  completes under the exact path.
- Three vehicles move to audited road-side positions. At the user's request,
  the three vehicles overlapping the red route are uniquely matched and
  deactivated instead of being repeatedly hand-adjusted. All adjustments
  happen before evaluator occlusion proxy construction.
- `PlacementPhaseGuard` forbids the target placement API and scene adjustment
  API after the ordinary first-published-frame boundary or RATE release
  boundary. The optional jump diagnostic uses
  `2 × configured_speed × simulation_deltaTime + epsilon` and writes only
  `runtime/placement_jump_diagnostic.json`.
- Production/default and RATE configs keep both validation diagnostics off.
  `config/scenario.scene-validation.json` explicitly enables dynamic
  intersection and jump diagnostics; its exact file SHA-256 is
  `f6005eb4365c8b598937dcbd422712914f4266b101d9147ff91e429fe246cd54`.
- Road data, placement state, and diagnostic outputs do not enter the sensor,
  tracker, VLM, controller, or `CoverageEvaluator`.

## Unity measurement and generation method

`RoadSceneEvidenceGenerator` opens the unchanged vendor SimplePoly demo scene
in Edit Mode and never saves it. It:

1. enumerates active top-level road render roots and reads their real
   `MeshFilter` vertices, instance center, yaw, scale, and road-surface height;
2. takes intersection/corner asphalt extents from their road-material
   submeshes; the straight-lane FBX uses one material across the combined
   road/sidewalk slab, so the editor cross-section curb seam reading
   `x=±6.0 m` is frozen as the straight-lane asphalt half-width rather than
   accepting the misleading 10 m combined-mesh extent;
3. uses the measured surface height (`0.2 m` on the target block) and writes
   91 asphalt patches, 12 canonical road-surface allowlist entries, and 89
   canonical obstacle footprints;
4. filters footprint triangles at the configured swept-envelope top
   (`0.2 + 1.55 + 0.5 = 2.25 m` world height), retaining the ground footprint
   and recording the remaining overhead minimum;
5. validates the generated document before writing it, then hashes the exact
   bytes and separately runs the legacy and corrected scene audits.

Representative raw road-data readings are preserved directly in
`config/road_data.json`: straight lanes have 6.0 m lateral half-width and
5/10/20 m longitudinal half-extents; intersections are approximately
10×10 m half-extents; target-block surface height is 0.2 m. The route center
offset of 2.5 m leaves 2.0 m between the configured 1.5 m horizontal swept
half-width and the straight-lane asphalt edge.

## Real city-scene audit

| Check | Legacy route | Corrected route/layout |
|---|---:|---:|
| Route samples | 419 | 427 |
| Road violations | 80 | 0 |
| Audited active obstacles | 782 | 779 |
| Obstacle violations | 13 | 0 |
| Vehicle violations | 3 | 0 |
| Prop violations | 9 | 0 |
| Building violations | 1 | 0 |
| Status | `INVALID_SCENE_LEGALITY` | `CLEAR` |

The nine legacy prop violations are four small billboards, two street lights,
two large traffic signals, and one hydrant. This mechanically reproduces the
user-observed sidewalk/pole defect in addition to all three SCENE-001 vehicle
conflicts. Machine-readable artifacts:

- `docs/evidence/P1-SCENE-002-audit-before.json`
- `docs/evidence/P1-SCENE-002-audit-after.json`
- `docs/evidence/P1-SCENE-002-audit-summary.json`

## Automated verification

| Command/check | Result |
|---|---|
| Unity `6000.4.1f1` Edit Mode full suite | 70/70 passed |
| Unity `6000.4.1f1` Play Mode full suite | 2/2 passed |
| `.venv-track/bin/python -m unittest discover -s tests -v` | 76/76 passed |
| Real-scene generator/audit | road 80→0, obstacles 13→0 |
| `git diff --check` | passed |

Primary local Unity artifacts (ignored runtime evidence, available to the
independent reviewer on this shared disk):

- `runtime/test-results/p1-scene-002-editmode.xml`
  (`sha256=ac5cb9bbcbb5c4a55f934067f6c60fc22ecc2ab8490940c7088e98e1f7a55d89`)
- `runtime/test-results/p1-scene-002-playmode.xml`
  (`sha256=0c4ed877121da8bf8101ff5c583fd463dc9bdd74c56708a4a4e19f77b96f41ee`)
- `runtime/test-results/p1-scene-002-evidence.log`
  (`sha256=14adebbbccbff7d58e5bcf296f6bcb30095666d9216c216b484ded8717bb5e58`)

## Focused inactive-removal filter fix

Candidate: `380e13c`; focused range `d6bca18..380e13c`.

The first user `UT-P1-SCENE-002-001` attempt exposed a bootstrap-only
integration gap: the adjustment applier deactivated all three configured
removals, but the legacy `RouteCorridorAuditor` still inspected inactive roots
when passed the bootstrap's pre-adjustment root array. It reported those exact
three objects as violations and aborted before the new road audit or validation
diagnostics were constructed.

The focused fix filters `!activeInHierarchy` roots inside
`RouteCorridorAuditor.Audit` regardless of whether roots are discovered or
explicitly supplied. The existing exact-removal unit test now immediately runs
the legacy gate over both removed and retained roots and requires one audited
active vehicle, zero violations, and `CLEAR`.

The real-scene generator now also runs this exact legacy gate after applying
all six adjustments. Updated evidence retains road 80→0 and obstacles 13→0,
and adds `corrected_vehicle_corridor_audited=101` with
`corrected_vehicle_corridor_violations=0`.

Focused verification:

| Check | Result |
|---|---|
| Unity `6000.4.1f1` Edit Mode | 70/70 passed; strengthened removal test passed |
| Unity `6000.4.1f1` Play Mode | 2/2 passed |
| Python | 76/76 passed |
| Real-scene generator | legacy active-vehicle gate 101/0; road 80→0; obstacles 13→0 |

Focused local artifacts:

- `runtime/test-results/p1-scene-002-fix-editmode.xml`
  (`sha256=38194f7f17fa60d81a3cbce0bc684b1dd9ecb5ce9c0d5c007da8b3c600ef2e40`)
- `runtime/test-results/p1-scene-002-fix-playmode.xml`
  (`sha256=7da99ee90a6d5fc97c355aade6f38e2cf710ee4af7119c472cf1adcbe9d4919d`)
- `runtime/test-results/p1-scene-002-fix-evidence.log`
  (`sha256=2718cf3ab27a4f4885f5c8d85b10bd189a5453ce19d29480801d6b0d6f893a65`)

## Focused dynamic-monitor classification/geometry fix

`UT-P1-SCENE-002-001` attempt 2 reached every new gate but exposed a second
real-scene integration defect. Static reports were `CLEAR` (legacy active
vehicles 101/0; road 427 samples / 0 violations; obstacles 779/0), the jump
diagnostic was 108801/0, and evaluator evidence retained
`C_geom=0.214987904` over 425.982422 simulation seconds. The dynamic report,
however, claimed intersections in 108801/108801 frames and named road
tiles/intersections plus coarse traffic-signal roots.

Direct tracing showed that bootstrap passed every static render root into a
monitor whose field/loop still assumed vehicle-only input. Whole-root renderer
AABBs therefore guaranteed a road intersection on every frame and collapsed
traffic-signal poles plus elevated arms into one coarse volume.

The focused fix:

- binds monitor configuration to the already hash-verified `RoadSceneData`;
- excludes canonical `road-surface` roots through the accepted allowlist;
- fails closed if any active non-road render root lacks a frozen footprint;
- uses exact transformed ground/full XZ footprints plus transformed vertical
  bounds; ground geometry is tested directly, while full-only overlap is
  rejected when its frozen `overhead_min_y_m` clears the target renderer;
- keeps the report validation-only and outside sensor, tracker, controller,
  and `CoverageEvaluator` paths.

Three direct tests cover road exclusion plus an L-shaped signal arm, a real
ground blocker, unknown-root fail-closed behavior, and the complete checked-in
SimplePoly scene. The real-scene test applies the exact validation config,
monitors 779 classified obstacles, places the runtime-shaped target every
0.1 m over the 212.970563 m closed route (2130 samples), and requires zero
intersection samples/names.

Focused verification:

| Check | Result |
|---|---|
| Unity `6000.4.1f1` Edit Mode | 73/73 passed; all 3 dynamic-monitor tests passed |
| Unity `6000.4.1f1` Play Mode | 2/2 passed |
| Python | 76/76 passed |
| Real-scene dynamic loop | 779 obstacles; 2130 target samples; 0 intersections |
| Truth boundary / B2 slots | clean; no B2 campaign/session/run exists |

Focused local artifacts:

- `runtime/test-results/p1-scene-002-dynamic-fix-editmode.xml`
  (`sha256=d4c4eed48856c372b97f5ccd694fce71180a37ac6fb671eb64079947bc44f624`)
- `runtime/test-results/p1-scene-002-dynamic-fix-editmode.log`
  (`sha256=0b4efff3939448301b006c53639f5ae76d91f8d5f8e6f6334f4ced1132298bfd`)
- `runtime/test-results/p1-scene-002-dynamic-fix-playmode.xml`
  (`sha256=63bb9dd1863ca6b6e62369151401c0654f82d10fffd7f3790d84857c4dbb6614`)
- `runtime/test-results/p1-scene-002-dynamic-fix-playmode.log`
  (`sha256=cc46e25368435bfaaa8f6c64e5785c1353f31ee982d85f90fe456b827f6e2f10`)

Focused stable candidate `932fc36`, review range `c827e94..932fc36`.
Attempt 2 remains a permanent FAIL.

## Independent and user gates

Sonnet Round 3 independently passed candidate `932fc36`, including the
attempt-2 root cause, strict road-data binding, transformed
ground/full/overhead behavior, unknown-root failure, bootstrap wiring, truth
boundary, tests, and exact artifact hashes.

User `UT-P1-SCENE-002-001` attempt 3 passed after 162.983490 s: full visual
checklist; vehicles 101/0, road 427/0, obstacles 779/0; dynamic and jump
40693/0; `C_geom=0.219562724`; 913/913 proxies with zero failures. Evidence is
archived under `runtime/test-results/ut-p1-scene-002-001-attempt3-pass/`.
Attempts 1–2 and SCENE-001's failed visual result remain preserved.
`P1-SCENE-002` is `DONE`; the first reviewed B2 smoke is unblocked.
