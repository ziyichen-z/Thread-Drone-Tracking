# P1-TEST-001 — independent verification

Reviewer/role: Claude Sonnet / independent verification

Round: 1

Date: 2026-07-23

Implementation snapshot: candidate `424609e` (full SHA
`424609e6330ade656ccca8a36c141c8d0e191695`, confirmed via `git rev-parse`).
Review range as requested: `efb6bc3..424609e`.

Verdict: **PASS_WITH_NOTES**

## Scope

Per the active handoff, the reviewable code scope is
`Assets/TetheredTracking/Scripts/` and `Assets/TetheredTracking/Tests/`;
`docs/current-status.md`, `docs/implementation-status.md`, and
`docs/evidence/P1-TEST-001-editmode.md` are context. `git diff efb6bc3..424609e --stat`
touches 18 files (774 insertions, 44 deletions); restricted to `Assets/` it is
15 files (599 insertions, 24 deletions): five modified runtime scripts, two
new `.asmdef` pairs (+ `.meta` files), one new `AssemblyInfo.cs`, and one new
452-line test file with 11 tests across 6 fixtures. No implementation code
was modified during this review.

`efb6bc3` itself (docs recording `P1-TRACK-001`'s Unity acceptance) is
included only as the diff's start boundary — that work item is already
`DONE` on the gate board (my prior `PASS_WITH_NOTES` plus a passed Unity run)
and is not reopened here. I did a light internal-consistency pass over its
numbers as context (below) but the verdict in this document is about
`P1-TEST-001` only.

## Accepted requirements checked

From the debt accepted in `docs/reviews/P1-M0-001.md` ("Consider adding a
minimal Unity Edit Mode test assembly so `ScenarioConfig`, IoU/visibility
math, and atomic-publish ordering gain regression coverage beyond manual
Play-mode passes"), as narrowed by the implementer evidence document's
"Accepted scope": scenario normalization, box/IoU and visibility-sample math,
plant constraints, atomic frame publication, and evaluator proxy exclusion.

## Files read

- `Assets/TetheredTracking/Scripts/AssemblyInfo.cs`,
  `TetheredTracking.Runtime.asmdef` (new)
- `Assets/TetheredTracking/Tests/EditMode/TetheredTracking.EditModeTests.asmdef`,
  `TetheredTrackingEditModeTests.cs` (new, full 452 lines, all 6 fixtures)
- Full diffs of the five modified runtime scripts: `CoverageEvaluator.cs`,
  `ScenarioConfig.cs`, `TetheredDronePlant.cs`,
  `EvaluationOcclusionGeometry.cs`, `SensorFrameWriter.cs`
- `docs/evidence/P1-TEST-001-editmode.md`
- Confirmed no other `.cs`/`.asmdef` files exist in `Assets/` outside
  `TetheredTracking/`, so the new assembly boundary cannot affect unrelated
  project code (there is none)

## Independent verification performed

I found the actual Unity test-runner artifacts still on disk (git-ignored,
left over from Codex's real run) and read them directly rather than trusting
the evidence document's summary:

```
$ python3 -c "... parse runtime/test-results/p1-test-001-editmode.xml ..."
root: testcasecount=11 result=Passed total=11 passed=11 failed=0
  AtomicFileTests.Write_ReplacesDestinationAndLeavesNoTemporaryFile -> Passed
  CoverageMathTests.IntersectionOverUnion_HandlesIdenticalPartialAndDisjointBoxes -> Passed
  CoverageMathTests.ProjectBounds_UsesNormalizedTopLeftOrigin -> Passed
  CoverageMathTests.VisibilitySamples_ContainCornersCenterAndFaceCenters -> Passed
  EvaluationOcclusionGeometryTests.Build_RequiresExplicitNonNullExclusionRoots -> Passed
  EvaluationOcclusionGeometryTests.BuildFromRenderers_ExcludesRuntimeRootsAndBuildsOnlyNeededProxy -> Passed
  ScenarioConfigTests.Normalize_ReconstructsMissingNestedSectionsAndRoute -> Passed
  ScenarioConfigTests.Normalize_ReplacesNonFiniteValuesAndClampsLimits -> Passed
  SensorFrameWriterTests.PublishFrameBundle_PublishesManifestForCompleteImmutablePair -> Passed
  TetheredDronePlantTests.Step_ClampsAltitudeAndTetherSphere -> Passed
  TetheredDronePlantTests.Step_ClampsCommandSpeedAndAcceleration -> Passed
```

All 11 test names and results match the evidence document exactly, and I
confirmed `runtime/test-results/p1-test-001-unity.log` independently ends
with `Test run completed. Exiting with code 0 (Ok).`, with the earlier
`Licensing::Module` handshake errors matching the evidence doc's account of
a transient stale-license-client issue that resolved before the run that
produced this XML (i.e., the log's overall trajectory is a transient early
failure followed by a clean pass, not a passed-but-actually-broken run).

I also reran the Python regression myself rather than trusting the reported
count:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 28 tests in 0.164s — OK
```

## Runtime-script diff review (the part that could regress prior gates)

These five files were the subject of my `P1-M0-001` Round 1/2 review, so I
read every changed line against what I already verified there, not just the
implementer's characterization of "extraction only":

- **`CoverageEvaluator.cs`, `ScenarioConfig.cs`**: `static`/(implicit
  `private`) → `internal static`/`internal` on `ProjectBounds`,
  `BoundsCorners`, `VisibilitySamples`, `IntersectionOverUnion`, and
  `Normalize()`. Visibility-modifier-only changes; zero lines of logic
  touched. Lowest possible risk.
- **`TetheredDronePlant.cs`**: `Update()` now reads `Step(Time.deltaTime)`;
  the entire physics body (`MoveTowards`, tether-sphere clamp,
  altitude clamp, yaw) moved verbatim into
  `internal void Step(float deltaTime)`, substituting the parameter for
  `Time.deltaTime` everywhere it previously appeared. Byte-for-byte
  equivalent to the previously-reviewed algorithm when called with the real
  frame delta.
- **`EvaluationOcclusionGeometry.cs`**: `Build(...)` is now a one-line
  wrapper calling the new `internal BuildFromRenderers(IEnumerable<MeshRenderer>, ...)`
  with `FindObjectsByType<MeshRenderer>(FindObjectsInactive.Exclude)` as the
  argument — the exact call it made inline before. The candidate/exclusion/proxy
  loop body is unchanged, now iterating the injected sequence instead of a
  locally-fetched array. `OnDestroy()` gained
  `if (Application.isPlaying) Destroy(proxy); else DestroyImmediate(proxy);`
  — the Play-mode branch is the exact prior call; `DestroyImmediate` only
  triggers in Edit Mode, which is necessary for Editor test teardown (Unity's
  `Destroy` is a no-op/error outside Play mode) and cannot fire during the
  reviewed runtime path.
- **`SensorFrameWriter.cs`**: the three-step atomic publish (image bytes,
  then metadata text, then `latest.json` referencing both) is now inside
  `internal static PublishFrameBundle(...)`, called from `Capture()` in the
  same relative order as before. One genuinely new detail: the manifest's
  `published_unix_s` is now computed by a `UnixNow()` call made in `Capture()`
  just *before* invoking `PublishFrameBundle`, rather than inline at the point
  the old code built the manifest object (i.e., after the metadata file was
  already written). This shifts the recorded timestamp earlier by however
  long the image+metadata writes take — sub-millisecond in practice, and
  nothing downstream treats `published_unix_s` as more precise than that. Not
  a correctness concern, noted for completeness (see Non-blocking note 1).

## Test-by-test verification

I hand-checked the numeric expectations in each fixture against the
underlying algorithm rather than trusting the assertions at face value:

- **`ScenarioConfigTests.Normalize_ReplacesNonFiniteValuesAndClampsLimits`**:
  sets every scalar/vector field to `NaN`/`Infinity`/out-of-range, including
  a route array with a `null` element and an all-non-finite element. I
  traced `Normalize()`'s actual fallback chain for several of these by hand
  (e.g. `maximum_altitude_m=100` clamped down to the tether length `35`;
  `initial_altitude_m=NaN` falling back to the default `25`; the `null` route
  element replaced by default waypoint 0, the fully-non-finite element
  replaced component-wise by default waypoint 1) and every asserted value
  matched. This is the direct regression test for the `NaN`/`Infinity`
  guarding gap I flagged in `P1-M0-001` Round 1 and confirmed fixed in Round 2
  — it is good to see it now locked in by an automated test rather than only
  a one-time manual verification.
- **`IntersectionOverUnion_...`**: re-derived the partial-overlap case by
  hand (intersection area `0.04` over union area `0.28` = `1/7`) and it
  matches the assertion exactly.
- **`ProjectBounds_UsesNormalizedTopLeftOrigin`**: this test doesn't hand-code
  expected viewport coordinates; it cross-checks `ProjectBounds`'s output
  against Unity's own `camera.WorldToViewportPoint()` for the same points
  (`box.y == 1 - upperViewport.y`, etc.), which is a robust way to pin the
  top-left-origin/image-y-flip convention without needing to duplicate
  Unity's projection math. This is the direct regression test for the box-
  orientation convention I could previously only confirm by reading code plus
  the user's one-time visual confirmation in `docs/unity-test-log.md`.
- **`VisibilitySamples_ContainCornersCenterAndFaceCenters`**: confirms all 8
  corners plus center plus the 6 explicit `center ± extents` face points,
  matching `VisibilitySamples()`'s literal formula.
- **`TetheredDronePlantTests`**: both tests use a generous `deltaTime` so the
  plant reaches steady state, then check exact clamped positions. I
  recomputed the tether-sphere case by hand: position `(0,8,0)`, command
  `(4,0,0)`, `Step(10)` → unclamped `(40,8,0)` → vertical clamps to `8`
  (already at max altitude) → horizontal budget `sqrt(10²−8²)=6` → clamped to
  `(6,8,0)`, `distance-from-anchor=10`, `TetherSaturated=true` — matches the
  assertions exactly, including the minimum- and maximum-altitude sub-cases.
- **`AtomicFileTests`**: writes twice to the same path (exercising the
  `File.Replace` branch, not just `File.Move` for a new file), confirms the
  final content is the *second* write, and confirms no `.tmp` file remains.
  Direct regression coverage for a contract I previously verified only by
  reading `AtomicFile.cs`.
- **`SensorFrameWriterTests.PublishFrameBundle_...`**: calls the real
  extracted method directly with synthetic bytes/metadata and confirms the
  manifest's `image_file`/`metadata_file` point at files that actually exist
  with the exact content passed in — a real regression test for "frame
  publication cannot expose a manifest pointing to a partial pair," again
  previously verified only by reading code.
- **`EvaluationOcclusionGeometryTests.BuildFromRenderers_...`**: builds a
  synthetic renderer set (an excluded child, a plain candidate, and one with
  a pre-existing `BoxCollider`) and checks not just the diagnostic counters
  (`ExcludedRendererCount=1`, `CandidateRendererCount=2`,
  `ProxyColliderCount=1`, `ExistingColliderCount=1`) but the actual Unity
  side effects: `candidate.GetComponentsInChildren<MeshCollider>()` has
  exactly one entry, and `excludedRoot.GetComponentsInChildren<MeshCollider>()`
  is empty. Checking the real component graph, not just counters that could
  drift independently of it, is exactly the kind of test that would have
  caught a regression in the self-occlusion exclusion logic — the gap I
  flagged in `P1-M0-001` Round 1 (finding 3) and Codex hardened in Round 2.
  `Build_RequiresExplicitNonNullExclusionRoots` directly tests the
  `ArgumentException` guards from that same Round 2 fix.
- **Test hygiene**: every fixture that creates `GameObject`s cleans them up
  in a `finally` block with `DestroyImmediate` (destroying a parent
  `Transform` cascades to its children, so `excludedVisual` doesn't need a
  separate destroy call); temp-directory-based tests clean up via
  `Directory.Delete(..., true)`. No test leaks Editor-scene state that could
  make a later test order-dependent.

## Context: `P1-TRACK-001` Unity acceptance sanity pass (not re-reviewed)

Since `efb6bc3` is inside the requested range, I did a light internal-
consistency check on the numbers recorded there (already `DONE`, not
reopened): follow (269.00065 s) and nadir (268.99964 s) both land just above
the ~268.97 s planned duration the experiment runner computes for the
default scenario, consistent with the loop only checking completion at
its own poll granularity. Nadir's higher `C_track` (0.0311135) than follow's
(0.00296718) is counterintuitive at first glance, but matches the accepted
proposal's own predicted failure mode ("CSRT drifting while still returning
success, with no confidence signal to catch it, driving `follow`'s gimbal
away from the target") rather than indicating a bridge or logging defect. I
did not re-derive this from raw run logs; this is a plausibility check, not
a new review round.

## Findings

### Blocking

None found.

### Non-blocking

1. **`published_unix_s` is now timestamped slightly earlier in the publish
   sequence.** See "Runtime-script diff review" above. Sub-millisecond in
   practice; no current consumer depends on tighter precision. Not
   actionable, noted for completeness only.
2. **`CoverageEvaluator`'s duration-weighted aggregation remains without
   direct unit coverage.** `OnFramePublished`/`OnObservationReceived`/`WriteMetrics`
   (the `C_geom`/`C_track`/`C_track_given_geom` continuous integration, frame
   pruning, and matched/unmatched/incorrect counting) is not exercised by
   this suite — only the pure static math helpers it calls
   (`IntersectionOverUnion`, `ProjectBounds`, `VisibilitySamples`) were
   extracted and tested. The evidence document discloses this directly
   ("Duration-weighted aggregate coverage is not newly unit-tested here...
   outside this minimal accepted debt item"), and it genuinely was outside
   the scope I described as the accepted debt in `P1-M0-001` Round 1, so this
   is not a shortfall against this candidate's own commitments. Given
   `C_track` is the paper's primary metric, I'd still suggest a future,
   separately-scoped test item for this state machine before it is relied on
   for load-bearing experimental comparisons (e.g. `P1-M2-RATE-001` or M5).

## Missing or weak tests

Beyond non-blocking note 2 above, none. This is a second consecutive round
(after `P1-TRACK-001`) where I found no gap between "claimed passing tests"
and "tests that actually exercise the claimed behavior when I hand-checked
the math" — a marked improvement from `P1-M0-001` Round 1's finding of zero
Unity Test Framework coverage at all.

## Requirement-to-evidence mapping

| Requirement | Evidence | Verdict |
|---|---|---|
| Scenario normalization (NaN/Infinity guards, missing sections, route reconstruction) | `ScenarioConfigTests` (2 tests, rerun via raw XML, hand-verified) | Met |
| Box/IoU math and top-left-origin projection | `CoverageMathTests.IntersectionOverUnion_...`, `ProjectBounds_...` (hand-verified against Unity's own `WorldToViewportPoint`) | Met |
| Visibility-sample geometry | `CoverageMathTests.VisibilitySamples_...` (hand-verified against the literal formula) | Met |
| Plant speed/acceleration/altitude/tether-sphere limits | `TetheredDronePlantTests` (2 tests, hand-verified including the `TetherSaturated` flag) | Met |
| Atomic publication, no partial manifest | `AtomicFileTests`, `SensorFrameWriterTests` (exercise the real `AtomicFile`/`PublishFrameBundle` code) | Met |
| Proxy exclusion (self-occlusion avoidance) | `EvaluationOcclusionGeometryTests` (2 tests; verifies actual `MeshCollider` component graph, not just counters) | Met |
| Runtime call paths unchanged (no protocol/metric/limit/selection-rule change) | Full diff read of all 5 modified scripts, traced line-by-line | Met |
| 11/11 Unity Edit Mode pass; 28/28 Python pass | Raw `p1-test-001-editmode.xml` and Unity log read directly; Python suite rerun myself | Met |

## Requested Codex action

None blocking. Consider a separately-scoped follow-up test item for
`CoverageEvaluator`'s duration-weighted aggregation state machine (note 2)
before `P1-M2-RATE-001` or M5 rely on `C_track` comparisons across
conditions. `P1-M2-RATE-001` is not blocked by anything in this review.

## Re-review result

Not started. Required only if a future round changes any of the five
runtime scripts touched here, the two `.asmdef` files, or
`TetheredTrackingEditModeTests.cs`.

## Codex gate closure

Date: 2026-07-24

Status: **DONE**

Codex accepted the blocking-free `PASS_WITH_NOTES` verdict after confirming
that candidate `424609e`, Unity Test Runner 11/11, Python 28/28, and this
independent review satisfy all three gates for the bounded test-debt item. The
minor `published_unix_s` timing shift remains informational. Direct coverage
of the duration-weighted aggregation state machine is assigned to the detailed
`P1-M2-RATE-001` proposal before comparative `C_track` results are accepted;
it does not reopen `P1-TEST-001`.
