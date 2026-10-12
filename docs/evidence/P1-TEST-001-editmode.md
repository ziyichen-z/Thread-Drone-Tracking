# P1-TEST-001 — Unity Edit Mode regression evidence

Date: 2026-07-23

Implementation snapshot: candidate `424609e` (full SHA
`424609e6330ade656ccca8a36c141c8d0e191695`).

Status: stable candidate; implementation and implementer-side execution
complete; independent Sonnet review pending.

## Accepted scope

This work closes the Unity Test Framework debt accepted in
`docs/reviews/P1-M0-001.md`: add a minimal Edit Mode assembly covering
scenario normalization, box/IoU and visibility-sample math, plant constraints,
atomic frame publication, and evaluator proxy exclusion before the M2 stable
candidate.

## Implementation

- Added runtime assembly `TetheredTracking.Runtime` and editor-only test
  assembly `TetheredTracking.EditModeTests`.
- Added `InternalsVisibleTo` so tests can exercise narrow deterministic seams
  without making them public API.
- Extracted `TetheredDronePlant.Step(deltaTime)` from `Update()`; the runtime
  path still calls it with `Time.deltaTime`.
- Extracted `SensorFrameWriter.PublishFrameBundle(...)`; `Capture()` still
  builds the same image and metadata, then the helper atomically publishes the
  image, metadata, and finally `latest.json`.
- Added an explicit renderer-input seam to
  `EvaluationOcclusionGeometry.BuildFromRenderers(...)`; the runtime
  `Build(...)` still supplies all active scene `MeshRenderer` objects.
- Exposed the existing normalization, projection, IoU, bounds-corner, and
  visibility-sample calculations internally for direct tests.
- In edit mode, generated evaluator proxies are destroyed immediately during
  teardown; play-mode destruction remains deferred through `Destroy`.

These are extraction/accessibility changes for deterministic testing. They do
not change the frame schema, tracker/control protocol, metric definition,
plant constraints, visibility thresholds, or proxy-selection rules.

## Test-to-requirement mapping

| Requirement | Edit Mode coverage |
|---|---|
| Scenario normalization | Reconstructs missing sections/route; replaces non-finite scalar/vector inputs and clamps limits |
| Box/IoU math | Identical, partial, disjoint, and null IoU; normalized top-left projection including image-y flip |
| Visibility sampling | Verifies the fixed 15-point set: 8 corners, center, and 6 face centers |
| Plant constraints | Command-speed and acceleration limiting; minimum/maximum altitude and tether-sphere limiting |
| Atomic publication | Atomic text replacement and byte write leave no `.tmp`; frame-bundle publication leaves a manifest whose immutable image and metadata both exist and match |
| Proxy exclusion | Excluded actor renderer gets no proxy; a valid mesh gets one; an existing collider is counted but not duplicated; missing exclusion roots are rejected |

The assembly contains 11 tests across six fixtures.

## Reproduction and result

Final Unity command:

```text
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  -batchmode \
  -projectPath ~/TetheredDroneTracking \
  -runTests \
  -testPlatform EditMode \
  -testFilter TetheredTracking.Tests \
  -testResults ~/TetheredDroneTracking/runtime/test-results/p1-test-001-editmode.xml \
  -logFile ~/TetheredDroneTracking/runtime/test-results/p1-test-001-unity.log
```

Machine-generated XML result at `2026-07-24 03:47:39Z`:

```text
result=Passed
total=11
passed=11
failed=0
inconclusive=0
skipped=0
duration=0.0356503 s
```

The Unity log ends with `Test run completed. Exiting with code 0 (Ok).` The
run initially encountered a stale Unity licensing-client protocol and waited
for the versioned licensing channel; after terminating the orphaned
editor-specific client, Unity connected successfully, resolved the Personal
license, compiled the project, ran all 11 tests, and exited normally. No C#
compiler diagnostic or test failure is present.

Regression checks after the Unity run:

```text
.venv-track/bin/python -m unittest discover -s tests -v
Ran 28 tests in 0.182s — OK

.venv-track/bin/python -m py_compile \
  controller/*.py tools/run_track_experiment.py tools/check_track_env.py
clean

python3 -m json.tool <both new asmdef files>
clean

git diff --check
clean
```

## Deliberate limits

- This is an Edit Mode unit/regression suite, not a replacement for the
  completed Play Mode city, body, gimbal, observation, and physical-occlusion
  sessions in `docs/unity-test-log.md`.
- The frame-bundle test executes the real persistence helper and verifies the
  published manifest refers to a complete pair. It does not interrupt the
  process between individual renames to emulate a crash.
- The proxy test injects a small renderer set so counts and exclusions are
  deterministic. Full-scene discovery and the 916-city-proxy result remain
  covered by the earlier user-run Unity evidence.
- The visibility test protects the sample-set geometry; real Physics raycast
  occlusion transitions remain covered by the earlier Unity runs.
- Duration-weighted aggregate coverage is not newly unit-tested here. Its
  current implementation and empirical output remain independently reviewable,
  but expanding that private state machine is outside this minimal accepted
  debt item.
