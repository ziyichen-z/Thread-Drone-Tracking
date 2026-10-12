# P1-TRACK-001 implementation evidence

Work item: `P1-TRACK-001`

Implementation candidate: `5b37f7b613f10f59a06e60968866ecf2c89f1a9e`

Date: 2026-07-23

Scope: desktop-only 5 Hz M2a CSRT/LOS baseline. This is not formal M2 closure
and does not include the deferred 5/20 Hz comparison, YOLOE arbitration,
Kalman filtering, body motion, TensorRT, CUDA, or Jetson work.

## Delivered behavior

- A lazy-loaded OpenCV CSRT adapter with normalized/pixel box conversion,
  clipping, integer initialization boxes for the OpenCV 5 binding, and the
  documented protocol placeholder `confidence=1.0`,
  `confidence_source="placeholder"`.
- Exact retained-frame initialization, strictly increasing sequential tracker
  updates, latest-only publication over the single observation slot, explicit
  backlog/skipped logging, recoverable `LOST`, and terminal
  `ERROR_REINIT_REQUIRED` for missing retained frames or frame-ID rollback.
- Metadata-basis bottom-center LOS projection using the accepted top-left image
  sign convention and a required explicit `--ground-plane-y-m`. Invalid,
  upward, parallel, non-positive, or over-range intersections do not write a
  new gimbal command.
- Body hold plus two experiment conditions: per-frame LOS `follow` and
  setup-once `nadir`.
- Per-run `p1-track-run/v1` directories with manifest, frame JSONL, summary,
  truncated-tail reconstruction, separate initialization/update latency, frame
  age, publication flags, and a scenario-matched final evaluator metrics
  snapshot when available.
- A scenario-aware orchestration tool that alone reads route/speed to calculate
  the accepted two-loop duration. The tracker command receives only scalar
  `scenario_id` and `planned_duration_s`; it receives no route, speed, or
  target state.

## Dependency evidence

Dedicated environment: `.venv-track` (not committed, intentionally isolated
from `.venv-yoloe`)

| Component | Tested value |
|---|---|
| Python | 3.12.13 |
| `opencv-contrib-python` package | 5.0.0.93 |
| `cv2.__version__` | 5.0.0 |
| NumPy | 2.5.1 |
| CSRT constructor | `cv2.TrackerCSRT_create` |

Commands:

```bash
.venv-yoloe/bin/python -m venv .venv-track
.venv-track/bin/python -m pip install -r tools/requirements-track.txt
.venv-track/bin/python -m pip check
.venv-track/bin/python tools/check_track_env.py
```

Results: installation succeeded; `pip check` reported no broken requirements;
the smoke tool instantiated a real `TrackerCSRT` through
`cv2.TrackerCSRT_create`.

The first real-constructor smoke exposed that OpenCV 5 rejects floating-point
initialization rectangles. The adapter now converts a normalized box to an
integer rectangle with floor-left/top, ceil-right/bottom, image clipping, and
a minimum one-pixel extent. Both fake-binding and installed-binding regression
tests cover this behavior.

## Automated verification

Primary command:

```bash
.venv-track/bin/python -m unittest discover -s tests -v
```

Result: **28/28 PASS**.

The 28 tests include the pre-existing four protocol regressions plus:

- CSRT root/legacy constructor selection, installed constructor
  initialization/update, placeholder confidence, failure, clipping, and
  normalized/pixel conversion;
- exact init-frame failure, sequential backlog updates, latest-only
  publication, forced failure with byte-identical observation/gimbal slots,
  post-loss recovery, missing-frame and rollback terminal states, nadir
  persistence, and geometry-rejection publication behavior;
- a subprocess-level end-to-end CLI run using the installed CSRT, synthetic
  JPEG frame bundles, versioned run output, summary reconstruction, and final
  metrics snapshot;
- top-left image-y sign, nadir and rotated camera bases, plus parallel,
  upward, non-positive, and over-range LOS rejection;
- JSONL truncation recovery, rejection of corruption before the tail,
  initialization/update latency separation, and geometry-rejection counts;
- two-loop duration calculation and an audit that the generated tracker
  command contains scalar orchestration values but no route or speed fields;
- rejection of a tracking run that omits the explicit ground-plane calibration.

Additional checks:

```bash
python3 -m py_compile controller/*.py \
  tools/run_track_experiment.py tools/check_track_env.py tests/test_*.py
git diff --check
```

Both passed.

## Acceptance status

| Requirement | Implementer evidence | Remaining gate |
|---|---|---|
| B0 follow run and nonzero bridge check | CLI, logger, metrics snapshot implemented | User Unity run |
| Fresh-session nadir comparison | condition and orchestration implemented | User Unity run |
| update p95 `< 200 ms`, frame age separate | schema/summary/test implemented | Real Unity run measurement |
| forced failure and frame sequencing | automated tests pass | Sonnet review |
| empirical Cube occlusion classification | logging path implemented | User Unity run |
| LOS geometry | automated tests pass | Sonnet review and Unity behavior |
| isolated dependency and test matrix | installed smoke plus 28 tests pass | Sonnet review |
| no target-truth path in tracker | code boundary and command audit test | Sonnet review |

## Known limits at this gate

- No real Unity follow/nadir baseline has been run on this candidate yet, so
  there is no claim about CSRT accuracy, full-loop retention, real p95, or
  `C_track` improvement.
- Raw run directories remain ignored local artifacts. After user acceptance
  runs, this document must be extended with the exact commands, manifest and
  summary contents, metrics, and hashes/locations of those raw directories.
- The initial box remains an operator-supplied normalized top-left `xywh`.
  `--dump-frame` copies the exact retained image for selection; no Unity box UI
  is included.
- The ground-plane value is a deliberate per-fixture calibration argument with
  no default. Neither the tracker nor orchestration helper derives it from the
  target route.

## Independent review

Claude Sonnet independently reviewed candidate `5b37f7b` and returned
**PASS_WITH_NOTES** on 2026-07-23. The reviewer independently reran all 28 tests
in `.venv-track` (including both real-OpenCV integration tests), `pip check`,
byte-compilation, and diff checks; manually re-derived representative LOS
geometry; and audited the truth-isolation boundary. No blocking finding was
reported. The full five non-blocking notes and evidence mapping are in
`docs/reviews/P1-TRACK-001.md`.

Codex deferred the four code/test polish notes until after Unity evidence so
the reviewed implementation snapshot stays frozen. The remaining note—reliance
on existing Unity C# nadir/hold-last behavior—is an explicit observation in
`UT-P1-TRACK-001-001`.
