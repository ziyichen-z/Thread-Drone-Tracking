# P1-SCENE-002 independent review

Status: ROUND_1_PASS_WITH_NOTES; ROUND_2_FOCUSED_FIX_PASS; ROUND_3_FOCUSED_FIX_PASS

Reviewer: Claude Sonnet (independent review role)

Implementation author: Codex

This file began as a review handoff prepared by Codex. Claude Sonnet
subsequently completed the independent Round 1 review below without modifying
implementation code.

## Candidate and requirements

- Accepted design:
  `docs/proposals/P1-SCENE-002-road-legal-route-and-placement.md`, Codex
  Round 2 `ACCEPTED` plus five binding clarifications.
- Formal design: `docs/phase1-single-drone-design.md`, P1-SCENE-002 section.
- Candidate: `4fcd6d3`; review range `7818edf..4fcd6d3`.
- Implementer evidence:
  `docs/evidence/P1-SCENE-002-implementation.md`.
- Machine evidence:
  `docs/evidence/P1-SCENE-002-audit-before.json`,
  `docs/evidence/P1-SCENE-002-audit-after.json`, and
  `docs/evidence/P1-SCENE-002-audit-summary.json`.

## Required independent scope

1. Diff the real candidate, not the implementer summary. Confirm the new route
   is clockwise/right-hand, on the measured surface, and changes no sensor,
   controller, tracker, metric, drone, gimbal, or anchor semantics.
2. Independently recompute the exact `config/road_data.json` SHA-256 and all
   checked-in scenario references. Trace missing file, hash mismatch, unknown
   schema/class/group, duplicates, missing active footprint, malformed new
   scenario fields, and unsupported TRS to fail-closed behavior and direct
   tests.
3. Inspect the editor generator's real mesh/material method, 6 m straight-lane
   asphalt boundary, 2.25 m world envelope top, 91 surface patches, 89
   canonical footprints, and unchanged vendor scene. Confirm non-uniform scale
   is exact and pitch/roll/zero scale rejects rather than approximates.
4. Verify the 3D decision combines exact transformed-footprint horizontal
   distance with road-surface-relative vertical overlap. Check ground props,
   overhead signal exemption, road-surface exemption, and non-uniform-scale
   regressions.
5. Check all six vehicle keys against real scene roots. Confirm three move to
   the cited curb positions, three user-requested conflicts deactivate, every
   match is unique/fail-closed, and all changes precede evaluator proxy
   construction.
6. Trace ordinary first-published-frame and RATE release measurement
   boundaries into `PlacementPhaseGuard`. Confirm post-boundary target/scene
   placement throws, the jump threshold is exactly
   `2 × speed × deltaTime + epsilon`, production configs disable diagnostics,
   and the explicit validation config enables both independent artifacts.
7. Grep the repository to confirm road truth, route truth, placement state,
   classifications, and diagnostic results do not enter `CoverageEvaluator`,
   sensor frames, tracker/VLM, or controllers.
8. Rerun or independently inspect Unity `6000.4.1f1` results (70/70 Edit,
   2/2 Play), Python 76/76, and real-scene evidence (road 80→0, obstacles
   13→0). Hand-check at least one legacy prop/vehicle violation and the
   corrected route edge-clearance arithmetic.
9. Confirm `UT-P1-SCENE-001-001` remains a retained FAIL,
   `UT-P1-SCENE-002-001` is blocked until this review passes, and no B2
   campaign/session artifact has been created.

## Verdict

### Round 1 (2026-07-27): PASS_WITH_NOTES

Candidate `4fcd6d3` over `7818edf..4fcd6d3` (handoff-only follow-up commit
`1b0ca17` fills in the candidate hash into docs and touches no
implementation file — confirmed by diff).

**Route, protocol, and truth-boundary scope (item 1, 7).** Diffed the
range directly. The redrawn route in `config/scenario.default.json` is a
clockwise, right-hand loop (north/south legs run east/west respectively,
matching the frozen lane semantics); hand-recomputed its perimeter from
the eight checked-in vertices and got `212.970563 m`, matching the
implementer's figure and the `route_sample_count=427` in
`P1-SCENE-002-audit-after.json` (`ceil(212.970563 / 0.5) + 1 = 427`,
exact). Independently recomputed the legacy route's perimeter the same
way and got `208.970563 m`, exactly reproducing `route_sample_count=419`
in `P1-SCENE-002-audit-before.json`. No sensor, controller, tracker,
metric, drone, gimbal, or anchor file appears in the diff; `git diff
--stat` confirms the changed set is limited to scenario config, the two
new scene-legality/placement scripts, one editor tool, docs, and tests.
Grepped the whole repo for `RoadScene`, `PlacementPhase`,
`RouteCorridor`, and `PlacementJump`: every reference is confined to
`LoopTargetVehicle.cs`, `PlacementPhase.cs`, `RoadSceneAudit.cs`,
`SceneVehicleAdjustments.cs`, and `TetheredScenarioBootstrap.cs`.
`CoverageEvaluator.cs` contains zero matches, and no Python file
(`controller/`, `tools/`) references `road_scene`, `road_data`,
`placement_jump`, or `route_corridor`. Truth boundary holds.

**Road-data hash binding and fail-closed paths (item 2).** Independently
computed `shasum -a 256 config/road_data.json` myself:
`111e0759d4b52821d08ce4ddd1aae3fc8cc8d24e12e6fa62513403c00b401894`,
exactly matching the `road_data_sha256` field in all four checked-in
scenario configs and the implementer's claim. Independently computed
`shasum -a 256 config/scenario.scene-validation.json`:
`f6005eb4365c8b598937dcbd422712914f4266b101d9147ff91e429fe246cd54`,
exactly matching the cited validation-config hash. Read
`RoadSceneDataLoader.LoadVerified` and `RoadSceneData.Validate`
end-to-end: missing file, hash mismatch, unsupported schema, empty/
duplicate allowlist or surface id, unknown surface classification,
duplicate/unknown obstacle classification, unknown obstacle group,
non-finite/inverted bounds, and a road/obstacle name collision all throw
`InvalidOperationException`/`FileNotFoundException` with no fallback.
`ScenarioConfig.FromJsonStrict` requires the eight new field names to be
textually present in the raw JSON before `Normalize()` runs, which then
independently re-validates every corridor field as finite via
`RequireFinite`/`RequirePositiveFinite`/`RequireNonNegativeFinite` and
`road_data_sha256` via `RateStudyProtocol.IsSha256` (confirmed this
helper rejects any string that is not exactly 64 lowercase hex
characters). All of these paths have a direct test in
`RoadSceneAuditEditModeTests.cs`
(`LoaderFailsClosedForMissingFileAndHashMismatch`,
`LoaderFailsClosedForUnknownSchemaAndDuplicateSurface`,
`LoaderFailsClosedForUnknownClassification`,
`AuditFailsClosedWhenActiveRendererRootHasNoFootprint`,
`PresentAdjustmentsRequireEveryNewAuditField`), which I confirmed are
all present with `result="Passed"` in the checked-in Edit Mode XML.

**Generator method and 3D swept-envelope decision (item 3, 4).** Read
`RoadSceneEvidenceGenerator.cs` in full: it opens the unchanged vendor
scene in Edit Mode, measures asphalt submeshes by material name, freezes
the straight-lane half-width at the documented `6.0 m` curb-seam reading
rather than the misleading combined-mesh extent, and splits each
prefab's triangles into "ground" (world Y at/below the `2.25 m`
envelope-top constant, matching `0.2 (surface) + 1.55 (target height) +
0.5 (margin)`) and "overhead" sets, producing separate ground/full XZ
footprints and an `overhead_min_y_m` per prefab — this is exactly the
mechanism the L-shaped-fixture requirement (a traffic light's pole vs.
its arm) needs. At runtime, `RoadSceneAuditor.AuditObstacle` computes
`envelopeMin`/`envelopeMax` from `SurfaceHeightAt(...)` — the per-sample
road-surface height read out of `road_data.json` — plus
`target_height_m`/`vertical_clearance_margin_m`, never a hardcoded world
`[0, ...]` bound; this satisfies binding clarification 2. Horizontal
distance is computed by transforming the exact footprint corners through
`Transform.TransformPoint` (full Unity TRS, including non-uniform scale)
and taking a true segment/polygon distance to the closed route, not an
approximation — `RequireSupportedFootprintTransform` rejects zero/
non-finite scale and any pitch/roll (`Vector3.Angle(root.up, Vector3.up)
> 0.01f`) instead of silently approximating, satisfying binding
clarification 3. Hand-traced the four-way classification: `road-surface`
objects are excluded before footprint lookup via
`roadData.road_surface_allowlist`; `runtime-actor` objects (anchor,
drone, target, the bootstrap's own root) are excluded from
`FindStaticRenderableRoots`'s input set by
`TetheredScenarioBootstrap.ApplySceneAdjustments` before the audit ever
runs; `overhead`-classified prefabs (four `Props_Roof *` roof fixtures in
the real data) exit early once `obstacleMin` clears the envelope; and the
generic ground/full split gives every other `ground-obstacle` prefab
(including the three real traffic-light/street-light prefabs, which do
have a measured pole-vs-arm footprint split in `road_data.json`) the
"pole inside → violation, pole outside/arm-only-over → exempt" behavior
via `overheadWorldY > envelopeMax`.

**Real-scene evidence, hand-verified (item 8).** Independently
re-derived the reported obstacle distances from
`docs/evidence/P1-SCENE-002-audit-before.json`: the three vehicle
entries report `centerline_distance_m` of `0.5936`, `0.1510`, and
`0.8546` for the taxi, container, and police car — matching the
`0.60 m`/`0.15 m`/`0.85 m` figures the proposal cites from the original
independent parse. The nine prop violations report `0.63 m` (four
billboards), `1.26 m` (hydrant), `1.40–1.42 m` (two big signals), and
`1.55 m` (two street lights) — again matching the proposal's §1.1a table
exactly. `before`→`after`: `road_violation_count` 80→0,
`obstacle_violation_count` 13→0 (3 vehicle + 9 prop + 1 building → 0),
`audited_obstacle_count` 779, `status` `INVALID_SCENE_LEGALITY`→`CLEAR` —
all match the implementer's evidence doc exactly.

**Vehicle removal/relocation uniqueness and bootstrap order (item 5).**
`config/scenario.default.json` now has six `vehicle_relocations` entries:
three relocations (taxi, container, one police car) and three
`remove_from_scene: true` removals (a second container, a second police
car at a different `original_xz_m`, and one sedan) — `Vehicle_Police Car`
appears twice with distinct `original_xz_m`, which `Apply`'s
position-tolerance matching (not name-only matching) correctly
disambiguates; confirmed the `matches.Length != 1` fail-closed check and
the `selected.Add(match)` double-selection guard are unchanged from the
already-reviewed SCENE-001 logic and are exercised by
`ApplyDeactivatesAnExactlyMatchedRemoval`. Re-read
`TetheredScenarioBootstrap.Awake()`: the order is still `CreateAnchor →
CreateDrone → CreateTarget → ApplySceneAdjustments →
CreateEvaluationOcclusionGeometry`, i.e. all relocations/removals commit
before occlusion-proxy construction, matching the SCENE-001-reviewed
invariant.

**Placement-timing structural guard and validation-only diagnostics
(item 6).** `PlacementPhaseGuard.RequirePlacementAllowed` is called from
both `LoopTargetVehicle.PlaceAtRouteDistance` and
`SceneVehicleAdjustmentApplier.Apply`, and `StartMeasurement` is invoked
from two call sites: `TetheredScenarioBootstrap.OnFramePublished` (first
published frame of an ordinary session) and
`RateStudyExperimentController` at the instant `State` becomes
`Released` (the RATE release frame) — exactly the two measurement
boundaries the binding clarification requires. Confirmed
`LoopTargetVehicle.Step` (the per-frame kinematic advance used during
ordinary motion) never calls `PlaceAtRouteDistance`, so the guard cannot
false-positive against normal target movement; `PlaceAtRouteDistance` is
only used by the scouting tool and the RATE `HOLD` re-anchor, both of
which run strictly before release. `PlacementJumpDiagnostic
.AllowedDisplacement` is exactly `2 × configuredSpeed × deltaTime +
epsilon` as required, confirmed both by reading the one-line
implementation and by the direct test asserting `AllowedDisplacement(2f,
0.1f, 0.01f) == 0.41f`. Confirmed the write-only, `CoverageEvaluator`-free
JSON artifact path, and re-ran the `ProductionConfigsDisableDiagnostics
AndValidationEnablesThem` test logic by hand against the checked-in
configs: `scenario.default.json`, `scenario.rate-study-5hz.json`, and
`scenario.rate-study-20hz.json` all set `enable_dynamic_intersection_audit:
false` and `enable_jump_diagnostic: false`; only
`scenario.scene-validation.json` sets both `true`.

**Automated evidence, reproduced myself (item 8).** Ran
`.venv-track/bin/python -m unittest discover -s tests -v` myself: `76/76`
passed, matching the cited count exactly (no cited-vs-observed drift, unlike
a prior round's incidental +3 in a different work item). Independently
computed SHA-256 of the checked-in Unity artifacts and got exact matches
to the implementer's cited digests for all three files
(`p1-scene-002-editmode.xml`, `p1-scene-002-playmode.xml`,
`p1-scene-002-evidence.log`), then read the XML directly and confirmed
`total="70" passed="70" failed="0"` (Edit) and `total="2" passed="2"
failed="0"` (Play), with all sixteen new SCENE-002 test names present and
`result="Passed"`. Did not attempt an independent Unity batch-mode rerun
this round since the prior `P1-SCENE-001` round already established the
`ResponseCode: 505` licensing handshake failure as a genuine, reproducible
environment limitation in this workspace, not a fabricated excuse — SHA-256
provenance on the checked-in XML is the available substitute.

**Documentation consistency (item 9).** `docs/unity-test-log.md` retains
`UT-P1-SCENE-001-001` as `Status: FAIL — VISUAL_PLACEMENT_AND_ROUTE_LEGALITY`
unmodified, and the new `UT-P1-SCENE-002-001` entry is `Status:
PENDING_SONNET — do not run before independent review passes`. Searched
`runtime/` for any B2 campaign or `rs2-pilot`-style live artifact: the
only matches are inside the already-archived
`ut-p1-m2-rate-002-002-batch-b-integration` test-results directory (the
preserved B1/stopped-rerun evidence the current-status log already
describes), and no `P1-M2-RATE-002-B2` campaign directory exists.
`docs/phase1-single-drone-design.md` and `docs/implementation-status.md`
both accurately describe the accepted design and the implemented
behavior against what the diff actually contains.

**Non-blocking notes.**

1. **Untested exemption branch matching the real hazard case.** The
   acceptance criteria and Round 2 binding clarification 1 both call for
   a direct regression case for "an arm crosses over the corridor while
   its pole sits outside it → not a violation" for a `ground-obstacle`
   classified fixture — the realistic shape of the actual
   `Props_Street Light`/`Props_Traffic Signal_*` prefabs, which do carry
   a measured pole-vs-arm footprint split in `road_data.json`. The one
   test that exercises an exemption
   (`OverheadSignalWithClearGroundFootprintIsExempt`) instead uses
   `classification == "overhead"`, which returns early through a
   *different* condition (`obstacleMin > envelopeMax`) before the
   general `ground-obstacle` pole/arm exemption branch
   (`fullIntersects && !groundIntersects && overheadWorldY >
   envelopeMax`) is ever reached. I hand-traced that second branch
   against the real `Props_Traffic Signal_big` footprint
   (`ground_max_x_m≈0.26`, `full_max_x_m≈2.49`, `overhead_min_y_m≈5.0`)
   and the geometry checks out, but it is empirically unexercised: both
   `docs/evidence/P1-SCENE-002-audit-before.json` and `-after.json`
   report `overhead_exemption_count: 0`, because in the corrected scene
   these props now sit far enough from the route (~5–6 m) that neither
   their ground nor full footprint reaches the corridor at all — the
   exemption logic that motivated splitting ground/full footprints in
   the first place is not what clears the real scene. A direct unit test
   for this specific branch (a `ground-obstacle` fixture whose ground
   footprint clears the corridor but whose full footprint does not, with
   `overhead_min_y_m` above the envelope) would close this gap before a
   future route change or M5 randomization relies on it for real.
2. Minor, same family: `RequireSupportedFootprintTransform`'s zero-scale
   rejection (`IsFiniteNonZero`) has no direct test alongside the
   pitch/roll test that exercises the same guard method.

Neither note blocks this candidate: both are coverage gaps in code paths
I independently traced and found geometrically correct, not observed or
suspected defects. `UT-P1-SCENE-002-001` may proceed under the exact
validation-config hash recorded above once the user is ready; `P1-SCENE-001`'s
`FAIL` stays authoritative and B2 remains forbidden until that combined
case passes.

## Focused revision handoff — inactive removal filter

Status: PASS

This subsection is a Codex handoff, not an independent verdict. The first user
`UT-P1-SCENE-002-001` attempt loaded the exact validation config but failed
before the new road/dynamic/jump gates: `RouteCorridorAuditor` received the
bootstrap's pre-adjustment roots and counted three already-deactivated removal
objects. The failed attempt is permanently recorded in
`docs/unity-test-log.md`.

Focused candidate: `380e13c`; range `d6bca18..380e13c`. Sonnet should review
only:

1. `RouteCorridorAuditor.Audit` now filters `activeInHierarchy=false` roots
   before renderer-bound auditing for both discovered and explicit candidates.
2. `ApplyDeactivatesAnExactlyMatchedRemoval` passes removed+retained roots to
   the real legacy audit and requires audited count 1, violations 0, `CLEAR`.
3. `RoadSceneEvidenceGenerator.GenerateEvidence` runs the same legacy gate
   after all six real-scene adjustments; summary reports active vehicles 101,
   violations 0, while road 80→0 and obstacles 13→0 remain unchanged.
4. Focused artifacts pass Unity Edit 70/70, Play 2/2, Python 76/76; hashes are
   listed in `docs/evidence/P1-SCENE-002-implementation.md`.
5. No Unity rerun or B2 work may start before Sonnet records a focused verdict
   here.

### Round 2 (2026-07-27): PASS

Focused candidate `380e13c` over `d6bca18..380e13c`. Confirmed `d6bca18` is my
own prior Round 1 review commit and touches no implementation file. The
implementation diff between the passed Round 1 candidate `4fcd6d3` and this
focused fix is exactly three files, 28 lines total
(`Assets/TetheredTracking/Editor/RoadSceneEvidenceGenerator.cs`,
`Assets/TetheredTracking/Scripts/SceneVehicleAdjustments.cs`,
`Assets/TetheredTracking/Tests/EditMode/SceneAdjustmentsEditModeTests.cs`) —
nothing else in `Assets/` or `config/` changed, so the Round 1 findings (route
geometry, hash bindings, classification logic, placement guard, truth
boundary) remain valid and were not re-litigated.

**Root cause, independently confirmed (item 1).** Read the preserved user
attempt-1 artifact directly:
`runtime/test-results/ut-p1-scene-002-001-attempt1/route_corridor_audit.json`
reports `status: INVALID_ROUTE_CORRIDOR`, `audited_vehicle_count: 104`,
`violation_count: 3`, with violators named exactly
`Vehicle_Container_color02 (4)`, `Vehicle_Police Car (2)`, and
`Vehicle_Car_color03 (2)` — precisely the three `remove_from_scene: true`
entries in `config/scenario.default.json`. Independently verified this
artifact's SHA-256 (`7bcc8c2e519bd64cb0212ffa0d9bed34b63d1b15c60cfe39e766a7263ccc7b0a`)
and the companion config/log hashes all match the truncated forms cited in
`docs/unity-test-log.md`. Re-read `TetheredScenarioBootstrap
.ApplySceneAdjustments`: it captures `roots` via `FindSceneVehicleRoots()`
*before* calling `Apply`, then passes that same array into
`RouteCorridorAuditor.Audit` *after* `Apply` has deactivated three of its
members — the array holds live Transform references, so the audit saw three
now-inactive vehicles still sitting at their original route-conflicting
positions. `RoadSceneAuditor.Audit` (the new SCENE-002 gate) was never
vulnerable to this because it already filters
`root.gameObject.activeInHierarchy`; only the legacy
`RouteCorridorAuditor.Audit`, carried over unchanged from SCENE-001, lacked
that filter.

**Fix correctness (item 1, 2).** `RouteCorridorAuditor.Audit` now adds
`.Where(root => root.gameObject.activeInHierarchy)` to its root pipeline,
applied uniformly whether roots are discovered or explicitly supplied —
exactly closing the gap, since the bootstrap's stale pre-`Apply` array is an
explicitly-supplied case. Confirmed by reasoning through Unity semantics that
this is the correct and sufficient fix regardless of `TryRendererBounds`'s own
inactive-object behavior, since the new filter runs before any renderer
lookup. `ApplyDeactivatesAnExactlyMatchedRemoval` now also calls
`RouteCorridorAuditor.Audit` directly on `{removed, retained}` (`removed` at
world `(1,0,0)`, squarely inside the test route/corridor, so it would have
been a violation had the filter not applied) and asserts
`audited_vehicle_count == 1`, `violation_count == 0`, `status == "CLEAR"` —
this is a precise regression test that encodes the exact bug shape (an
explicit candidate array containing a since-deactivated object), not a
generic re-check. Confirmed present with `result="Passed"` in the checked-in
fix XML.

**Real-scene re-validation (item 3, 8).** `RoadSceneEvidenceGenerator
.GenerateEvidence` now also runs `RouteCorridorAuditor.Audit` on the
post-adjustment `vehicleRoots` and throws if `violation_count != 0`, adding
`corrected_vehicle_corridor_audited`/`corrected_vehicle_corridor_violations`
to the evidence summary. Read `docs/evidence/P1-SCENE-002-audit-summary.json`
directly: `corrected_vehicle_corridor_audited: 101` (104 − 3, exactly the
three removals), `corrected_vehicle_corridor_violations: 0`, while
`corrected_road_violations`/`corrected_obstacle_violations` remain `0`/`0` —
the unrelated Round 1 geometry is untouched by this fix, confirmed by rereading
the same before/after JSON files I already hand-verified in Round 1 (byte-
identical `road`/`obstacle` fields).

**Automated evidence, reproduced myself (item 4).** Reran
`.venv-track/bin/python -m unittest discover -s tests -v`: `76/76` passed.
Independently computed SHA-256 for all three focused Unity artifacts
(`p1-scene-002-fix-editmode.xml`, `p1-scene-002-fix-playmode.xml`,
`p1-scene-002-fix-evidence.log`) and got exact matches to the cited digests;
read the XML directly and confirmed `total="70" passed="70" failed="0"`
(Edit) and `total="2" passed="2" failed="0"` (Play), with
`ApplyDeactivatesAnExactlyMatchedRemoval` present and `Passed`.

**Documentation and gate consistency (item 5).** `docs/unity-test-log.md`'s
`UT-P1-SCENE-002-001` entry correctly reclassifies all five expected cases as
`FAIL_ATTEMPT_1`/`NOT_SCORED_ATTEMPT_1` rather than silently leaving stale
`PENDING` rows, and its new "Attempt 1" narrative matches the artifact
evidence exactly. `docs/current-status.md`'s gate board and active-handoffs
entries accurately describe the focused-fix state. No B2 artifact or new Unity
rerun exists yet.

**One tangential, non-blocking observation (not a finding against this
candidate).** `Assets/TetheredTracking/Editor/SceneCorridorEvidenceGenerator
.cs` is a SCENE-001-era offline tool with a hardcoded
`before.violation_count != 3` assertion; it is not referenced by any test or
menu item anywhere in the codebase (`grep` confirms zero other references), so
it does not run as part of the 70/70 Edit count and is not affected by
today's fix. It has, however, been stale since the SCENE-002 route/relocation
changes (the "before" state against the corrected route now has six
route-adjacent vehicles, not three) and would throw if anyone resurrected it.
Worth deleting or updating whenever someone next touches scene evidence
tooling; does not block this candidate.

No blocking findings. This closes the bootstrap integration gap that caused
`UT-P1-SCENE-002-001` attempt 1 to fail before its road/dynamic/jump gates
ever ran. The user may rerun `UT-P1-SCENE-002-001` under the same exact
validation-config hash recorded above. `UT-P1-SCENE-001-001`'s FAIL and
`UT-P1-SCENE-002-001` attempt 1's FAIL both stay permanently retained records;
B2 remains forbidden until a passing `UT-P1-SCENE-002-001` attempt exists.

## Round 3 handoff — dynamic-monitor classification/geometry fix

Status: AWAITING_INDEPENDENT_REVIEW

This subsection is a Codex handoff, not an independent verdict. User
`UT-P1-SCENE-002-001` attempt 2 reached every new gate with the exact
validation config. Static legality, jump, and anti-ceiling evidence passed,
but `route_corridor_dynamic.json` reported 108801/108801 intersections naming
road tiles/intersections and four traffic-signal roots. The attempt is
permanently retained in `docs/unity-test-log.md`.

Focused candidate: `932fc36`; range `c827e94..932fc36`. Sonnet should review:

1. The diagnosed source path: bootstrap supplied all static render roots while
   `RouteCorridorDynamicMonitor` treated them as vehicle roots and used
   aggregate renderer AABBs, making road overlap unavoidable.
2. Monitor configuration now consumes the already hash-verified
   `RoadSceneData`, excludes the canonical road allowlist, maps every active
   non-road root to its frozen footprint, and fails closed on an unknown root.
3. `TargetBoundsIntersectObstacle` uses transformed ground/full XZ rectangles,
   SAT overlap, transformed vertical bounds, and `overhead_min_y_m` so a pole
   is detected while a sufficiently high signal arm is exempt. Unsupported
   TRS continues to fail closed through the shared guard.
4. Bootstrap passes `RoadData` plus the same post-adjustment static-root set;
   outputs remain validation-only and absent from `CoverageEvaluator`, sensor,
   tracker, and controller paths.
5. Direct tests cover road exclusion, a clear elevated arm, a real ground
   blocker, unknown-root failure, and the checked-in SimplePoly scene at 2130
   target positions over the full route against 779 obstacles.

Implementer evidence: Unity `6000.4.1f1` Edit 73/73 and Play 2/2, Python
76/76, real-scene dynamic samples 2130/0; exact artifact hashes are in
`docs/evidence/P1-SCENE-002-implementation.md`. Attempts 1–2 and the earlier
SCENE-001 FAIL remain authoritative. Do not authorize attempt 3 or B2 unless
this focused candidate independently passes.

### Round 3 (2026-07-27): PASS

Focused candidate `932fc36` over `c827e94..932fc36`. `c827e94` (docs-only,
confirmed by diff) records my own Round 2 `PASS`; `932fc36` is the sole
commit in range and contains the fix. Implementation diff versus
the Round 2-passed candidate `380e13c`: three files
(`RoadSceneAudit.cs`, `SceneVehicleAdjustments.cs`,
`TetheredScenarioBootstrap.cs`), all additive to the already-reviewed
Round 1/2 geometry and placement machinery — no route, hash-binding,
placement-guard, or removal-uniqueness logic changed, so those Round 1/2
findings stand and were not re-litigated.

**Root cause, independently confirmed (item 1).** Read the preserved
attempt-2 artifacts directly.
`runtime/test-results/ut-p1-scene-002-001-attempt2/route_corridor_dynamic.json`
reports `checked_frames: 108801`, `intersection_frames: 108801`, and names
exactly 4 distinct `Props_Traffic Signal_big (*)` roots plus 11 `Road *`
tile/intersection roots — no other names. The companion
`road_scene_audit.json` in the same directory independently confirms
`status: CLEAR`, `route_sample_count: 427`, `audited_obstacle_count: 779`,
`0`/`0` violations; `route_corridor_audit.json` (legacy vehicle gate) shows
`101`/`0`/`CLEAR` (confirming the Round 2 fix held); `placement_jump_diagnostic.json`
shows `108801`/`0`; and `metrics.json` shows
`elapsed_simulation_s: 425.982421875` and `aggregate.c_geom:
0.21498790383338928` — every one of these independently reproduces the
narrative in `docs/unity-test-log.md`'s "Attempt 2" entry exactly, digit for
digit. Re-read the pre-fix `RouteCorridorDynamicMonitor` (via `git show
c827e94:...SceneVehicleAdjustments.cs`): it received the bootstrap's full
`staticRoots` set (all static renderables, per SCENE-002's generalization)
but still ran the old vehicle-only logic —
`Bounds.Intersects(vehicleBounds)` on raw renderer AABBs with no road
exclusion — so a flat road tile's AABB, which always spans the target's XZ
footprint and overlaps its Y-range wherever the target drives on the road,
guaranteed an intersection every single frame; a signal's whole-root AABB
(pole+arm undivided) did the same whenever the target passed under it. This
fully explains the 100% intersection rate and the exact object list.

**Fix correctness (item 2, 3).** `RouteCorridorDynamicMonitor.Configure` now
takes `RoadSceneData`, re-validates it, builds an allowlist from
`road_surface_allowlist`, and for every active non-target candidate root
either (a) excludes it if its canonical name is in the road allowlist, (b)
looks up its precomputed footprint and includes it as a `MonitoredObstacle`,
or (c) throws `InvalidOperationException` naming the root if no footprint
exists — exactly the fail-closed-on-unknown-root behavior required. Read the
new `RoadSceneAuditor.TargetBoundsIntersectObstacle` in full and hand-traced
its logic against the new `ExcludesRoadAndUsesGroundAndOverheadFootprints`
test's own geometry (target box `y:[0,1.55]` at world origin; a "Signal"
whose ground/pole footprint at world `x:[2.5,3]` never overlaps the target's
`x:[-1,1]`, whose full/arm footprint at `x:[-3,3]` does overlap, and whose
`overhead_min_y_m=3` sits above the target's top `1.55` — I independently
derived `groundIntersects=false`, `fullIntersects=true`,
`verticalIntersects=true` from `TransformVerticalBounds` using
`full_min_y=0`/`full_max_y=4`, and the final `overheadWorldY(3) <=
targetBounds.max.y(1.55)` comparison correctly evaluates false, so the
method returns `false`/exempt — matching the test's first assertion) and
against the "Blocker" repositioning to directly overlap the target
(`groundIntersects=true` on the second sample, short-circuiting to `true`
before the overhead branch even runs — matching `IntersectionFrames=1`).
The horizontal test itself
(`ConvexPolygonsIntersect`/`HasSeparatingAxis`) is a textbook two-polygon
Separating Axis Theorem implementation — axes drawn from both polygons'
edge normals, projected intervals checked for a gap — which is the
mathematically correct and necessary test for two arbitrarily-yawed
rectangles, not an approximation. `RequireSupportedFootprintTransform` (the
same guard Round 1 already verified) is reused unchanged, so pitch/roll and
zero/non-finite scale continue to fail closed here too.

**Bootstrap wiring and truth boundary (item 4).** `TetheredScenarioBootstrap
.ApplySceneAdjustments` now passes `RoadData` (already hash-verified at
`Awake()`) and the same `staticRoots` used for the static SCENE-002 audit —
confirmed this is a live re-query via `FindObjectsByType(...,
FindObjectsInactive.Exclude)` computed *after* `Apply()`, not a stale
pre-`Apply` array, so it does not carry the Round-2-class staleness bug.
Grepped `CoverageEvaluator.cs`, the sensor/frame path, tracker code, and all
Python (`controller/`, `tools/`) for `RoadScene`, `RouteCorridor`,
`PlacementJump`, and `TargetBoundsIntersectObstacle`: all matches confined
to the same four implementation files already listed in Round 1/2. Truth
boundary holds.

**Automated evidence, reproduced myself (item 5).** Reran
`.venv-track/bin/python -m unittest discover -s tests -v`: `76/76` passed.
Independently computed SHA-256 for all four focused artifacts
(`p1-scene-002-dynamic-fix-editmode.xml/.log`,
`-playmode.xml/.log`) and got exact matches to the cited digests; read the
XML directly and confirmed `total="73" passed="73" failed="0"` (Edit,
+3 over Round 2's 70) and `total="2" passed="2" failed="0"` (Play), with
`ExcludesRoadAndUsesGroundAndOverheadFootprints`,
`ConfigureFailsClosedForUnknownActiveRenderableRoot`, and
`CheckedInCitySceneStaysClearAcrossFullDynamicLoop` all present and
`Passed`. The real-scene test's `MonitoredObstacleCount == 779` assertion
matches Round 1's already-verified `audited_obstacle_count`, an internal
cross-check the implementer didn't have to add but strengthens confidence;
it samples the corrected `212.970563 m` route at `0.1 m` spacing (2130
samples, denser than the static audit's own `0.5 m`) and requires zero
intersections across the full loop — direct, real-data reproduction of
exactly the scenario that failed in attempt 2.

**Documentation consistency.** `docs/unity-test-log.md`'s "Attempt 2" entry
matches the artifact evidence exactly (spot-checked every number above).
`docs/current-status.md`'s gate board, active handoffs, and implementation
batch entries accurately describe the fix. No B2 campaign or session
artifact exists; both `UT-P1-SCENE-001-001` and `UT-P1-SCENE-002-001`
attempts 1–2 remain permanently retained FAIL records.

No blocking findings. Minor, non-blocking observation: `Sample()` now runs
`RequireSupportedFootprintTransform` plus a SAT test per obstacle every
frame (up to 779 per sample in the real scene), and this check happens
lazily inside `Sample()` rather than upfront in `Configure()` — an object
with unsupported TRS would only be caught on the first frame it's sampled,
not at configuration time. This is validation-only diagnostic code that is
off by default and already exercised cleanly against the full real scene
(2130 samples, zero exceptions), so it does not block; a `Configure()`-time
pre-check would be marginally earlier-failing but is not required.

This closes the dynamic-monitor integration gap that caused
`UT-P1-SCENE-002-001` attempt 2's `FAIL_DYNAMIC_MONITOR_ROOT_CLASSIFICATION`.
The user may attempt `UT-P1-SCENE-002-001` a third time under the same exact
validation-config hash. `UT-P1-SCENE-001-001` and both retained SCENE-002
attempt FAILs stay authoritative; B2 remains forbidden until a passing
`UT-P1-SCENE-002-001` attempt exists.
