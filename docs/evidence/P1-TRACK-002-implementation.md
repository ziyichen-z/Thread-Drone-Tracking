# P1-TRACK-002 implementer evidence

Work ID: `P1-TRACK-002`

Implementation candidate: `46747d8`

Status: `STABLE_CANDIDATE_AWAITING_SONNET`

This evidence covers only the accepted core implementation: the frozen
OpenCV TrackerNano/NanoTrack-v2 adapter, model identity and acquisition,
tracker selection, run-manifest identity, failure paths, and standalone
latency. It does not implement `P1-M2-RATE-002`, authorize a Unity campaign,
or close `P1-TRACK-002`.

## Frozen artifact identity

The identity is checked in at `config/nanotrack-v2.models.json`. Both ONNX
files are descendants of `NanoTrack/`, whose upstream directory contains
`NanoTrack/LICENSE` (Apache-2.0) at the same immutable source commit.

| Field | Frozen value |
|---|---|
| Repository | `https://github.com/HonglinChu/SiamTrackers` |
| Commit | `248663fde6bf7c40190cf10ee396d5662919ecd3` |
| Artifact license | `Apache-2.0`, `NanoTrack/LICENSE` |
| License SHA-256 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| Backbone | `nanotrack_backbone_sim.onnx`, 1,056,849 bytes |
| Backbone SHA-256 | `530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4` |
| Neck/head | `nanotrack_head_sim.onnx`, 726,198 bytes |
| Neck/head SHA-256 | `0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9` |
| OpenCV package | `opencv-contrib-python==5.0.0.93` (`cv2==5.0.0`) |
| DNN target | `DNN_BACKEND_DEFAULT` / `DNN_TARGET_CPU` |
| Preprocessing identity | `opencv-tracker-nano-5.0.0-default-v1` |

The preprocessing record points to the matching OpenCV 5.0.0 implementation
and freezes its 127 px exemplar, 255 px search input, scale 1.0, zero blob
mean, RGB swap, and per-image-channel-mean padding. The downloader uses the
two commit-qualified raw URLs, writes a temporary file, verifies size and
SHA-256, and only then atomically installs it under the ignored local runtime
model directory:

```text
.venv-track/bin/python -m tools.fetch_tracker_models
```

The controller never imports a network client. Model loading is local-only;
missing files, malformed identity, wrong size, wrong hash, incompatible
OpenCV, and constructor failure all terminate without a CSRT fallback.

## Runtime behavior

- `--tracker {csrt|nanotrack-v2}` is accepted by
  `controller.track_loop`, `tools.run_track_experiment`, and the existing
  rate-study launch boundary. The default remains `csrt`, so archived
  RATE-001 behavior is not reinterpreted.
- NanoTrack returns `getTrackingScore()` unchanged after finite/range
  validation, with `confidence_source="tracker"`.
- There is no score threshold: manifests record `score_threshold=null` and
  `threshold_source="none"`. A normal low score does not create `LOST`.
- Update/score exceptions, invalid output, and explicit backend failure are
  fail-closed. Output box clipping remains at the existing
  `_publication_ready_result` boundary.
- NanoTrack manifests include tracker/backend, OpenCV version and package pin,
  DNN backend/target, both model hashes, preprocessing ID, immutable source
  URLs/commit, and artifact-license evidence.
- No detector fallback, YOLOE arbitration, ReID, L1-L4 escalation, protocol
  clock/barrier change, or model/threshold tuning is present.

## Automated verification

Commands run from the repository root in `.venv-track`:

```text
.venv-track/bin/python -m unittest discover -s tests -v
.venv-track/bin/python -m pip check
.venv-track/bin/python -m py_compile controller/trackers.py controller/track_loop.py tools/run_track_experiment.py tools/run_rate_study.py tools/fetch_tracker_models.py tools/benchmark_tracker.py
git diff --check
```

Results:

- Python: **55/55 pass**.
- The suite includes a real installed-OpenCV NanoTrack constructor/update
  smoke and a real CLI-to-`p1-track-run/v1` manifest round trip.
- Covered failure paths: model missing, corrupt size, same-size hash mismatch,
  constructor exception, update exception, non-finite/out-of-range score,
  invalid box, unknown selector, and local loading with socket creation
  prohibited.
- Selector propagation is directly checked through both orchestration
  boundaries.
- `pip check`: no broken requirements.
- Python byte compilation and `git diff --check`: pass.

OpenCV 5.0.0 emits a warning that an explicit target is not separately
supported by its new graph engine when both selected values are the documented
defaults. The effective selected target remains the default CPU path; real
construction, update, CLI integration, and the CPU latency gate all pass.

## Standalone latency and zero-mutation check

Command:

```text
.venv-track/bin/python -m tools.benchmark_tracker --output runtime/models/nanotrack-v2/benchmark-640x480.json
```

Method: deterministic synthetic 640×480 BGR frame, 20 warm-up updates, then
100 measured updates, `time.perf_counter()` around `tracker.update()`.

| Statistic | ms |
|---|---:|
| minimum | 2.516708 |
| mean | 2.998161 |
| p50 | 3.010063 |
| p95 | **3.332854** |
| maximum | 3.503375 |

Acceptance is p95 `< 50 ms`; result is **PASS**. Both model SHA-256 values
were recomputed before and after this benchmark and remained exactly equal to
the frozen values above.

## Remaining gates

1. Sonnet must independently review implementation candidate `46747d8` over
   `ef24414..46747d8`.
2. The exact shared post-release 30 s qualification pilot waits for the
   separately owned and accepted `P1-M2-RATE-002` infrastructure.
3. The user Unity case `UT-P1-TRACK-002-001` remains required.

Therefore this work item is a stable core candidate, not `DONE`.
