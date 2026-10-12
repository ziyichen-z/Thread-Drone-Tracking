# P1-DETECT-001 implementation evidence

Date: 2026-07-28  
Owner: Codex  
Status: `IMPLEMENTED_AWAITING_INDEPENDENT_REVIEW`
Candidate: `f2555d5` over `15bff60..f2555d5`

## Scope and boundaries

This batch implements the accepted base revision 3 plus DINOv2 Amendment A1
revision 2. It adds the minimal triple-gated re-anchor carrier to the existing
NanoTrack-v2 track loop. It does not run scouting, inspect Unity truth, move
the anchor, start a qualification run, or resume a successor rate campaign.
`CoverageEvaluator` remains the only Unity-truth consumer.

The ignored ResNet18 artifact remains unloaded and its negative supply-chain
evidence remains in
`docs/evidence/P1-DETECT-001-resnet18-supply-chain-gate.md`.

## Download and identity gate

The user explicitly authorized the pinned DINOv2 source and standard
`dinov2_vits14_pretrain.pth` download on 2026-07-28. The reproducible fetch
entry point requires an explicit `--authorized` flag:

```text
.venv-yoloe/bin/python -m tools.fetch_dinov2 --authorized
```

The strict config is
`config/detector-reanchor.models.json`, SHA-256
`593734d67ada73a0304d67d27c6ae536be616d2180f744336b85ff6e0ac706d2`.
All runtime artifacts remain excluded by `.gitignore` `/runtime/*`.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| commit `7764ea0f912e53c92e82eb78a2a1631e92725fc8` source archive | 2,869,642 | `c27dcdaf50e9fb5bbdf2bb529da357716372e19c6afab17d5350f3f0094aed4b` |
| extracted pinned `LICENSE` | 11,359 | `600cc67cc4cb2f5ea317dcfc687ad1c74dc4bec8782bbe9db0afd83513b935b7` |
| `dinov2_vits14_pretrain.pth` | 88,283,115 | `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9` |
| `yoloe-11s-seg.pt` | 27,803,986 | `8e439445c87338b79d9ce21dec109f4621e26df67e94d26ea1a98c1e64dce3e3` |

Before import or deserialization, runtime code verifies the archive, every
non-cache extracted source file against that archive, the Apache-2.0 LICENSE,
and the DINOv2/YOLOE weights. DINOv2 is constructed locally with
`pretrained=False`, loaded with `weights_only=True` and `strict=True`, and
never uses `torch.hub.load`.

## Implemented behavior

- Strict hash-bound model/config identity and frozen parameter values.
- Official PIL RGB bicubic 256 → center-crop 224 preprocessing, BGR→RGB,
  finite 384-d normalized `x_norm_clstoken`, and deterministic
  `CROP_INVALID`/`EMBED_INVALID` handling.
- YOLOE visual-prompt class proposals using `Results.boxes.xyxy/conf`.
- Deterministic class/appearance/world-LOS gates, ambiguity margin,
  tie-break, K=2 hysteresis, AGREE and catch-up-head anchor refresh.
- Six-second deeply immutable frame history; exact detection-source
  initialization; ordered replay; missing/stale/non-converged/invalid-box
  discard events; atomic replacement only at the consumed-frame boundary.
- One in-flight worker with zero queue, busy-drop cadence accounting,
  timeout/live-thread termination semantics, one confirmed-death restart,
  independent worker/reseed failure budgets, and fail-closed termination.
- Main-thread-only JSONL persistence. Re-anchor events carry
  `record_kind=event`, remain auditable, and do not contaminate frame-count,
  cadence, LOST, or RATE-002 monotonic-clock denominators.
- Manifest identity includes detector, DINOv2, preprocessing, NanoTrack
  factory, runtime pins, strict config hash and every frozen parameter.

## Automated checks

The full existing Python suite, including 12 focused re-anchor tests and a
new event-denominator regression, passes:

```text
.venv-track/bin/python -m unittest discover -s tests -v
Ran 89 tests in 0.513s
OK
```

Focused coverage includes strict config rejection, top-left/world-frame rays
under gimbal rotation, four-level ranking and ambiguity reset, K hysteresis,
crop-invalid semantics, deeply immutable history, exact-source ordered replay,
missing/stale/timeout/out-of-bounds replay rejection, busy/timeout worker
behavior, and atomic fresh/stale swap paths.

The merged runtime package set is internally consistent:

```text
UV_CACHE_DIR=/private/tmp/p1-detect-uv-cache \
  uv pip check --python .venv-yoloe/bin/python
Checked 42 packages
All installed packages are compatible
```

Installed pins/load surface: OpenCV `5.0.0`, torch `2.13.0`, torchvision
`0.28.0`, ultralytics `8.4.104`, and `TrackerNano_create=True`.
Real local smokes produced a finite 384-d DINOv2 vector with measured squared
norm `1.000000087`; YOLOE visual-prompt initialization and a later inference
completed successfully.

`python3 -m py_compile` passes for all new/modified Python entry points,
`git diff --check` passes, and `python3 tools/check_docs.py` passes.

## Synthetic end-to-end timing

The checked-in benchmark uses generated checker pixels only; it is an
implementation timing smoke, not project-data scouting:

```text
MPLCONFIGDIR=/private/tmp/p1-detect-mpl-cache \
XDG_CACHE_HOME=/private/tmp/p1-detect-xdg-cache \
.venv-yoloe/bin/python -m tools.benchmark_reanchor \
  --frames 60 --rate-hz 20
```

On macOS arm64 / Python 3.12.13 / CPU, one planned round completed unexpired:

| Channel | Result |
|---|---:|
| main NanoTrack + re-anchor bookkeeping p50 / p95 / max | 11.512 / 13.283 / 13.617 ms |
| detector | 74.075 ms |
| appearance gate | 20.994 ms |
| complete worker | 95.303 ms |
| initialization | 190.970 ms |
| cadence | 1/1 = 1.0 (`>= 0.8`) |

The worker closed cleanly, `fatal_reason` was null, and the main-loop p95 is
below the accepted 50 ms budget. No DISAGREE/reseed occurred on this synthetic
AGREE smoke, so replay latency is covered by deterministic unit tests rather
than claimed as a measured domain result.

## Remaining gates

This is implementer evidence only. Sonnet must independently review the stable
candidate before any scouting or qualification. Unity validation is also
pending; therefore this work is not `DONE`.

## Round 1 rework evidence

Sonnet independently returned `REWORK_REQUIRED` on candidate `f2555d5`
because worker-thread `TripleGateState` and `reseed_failures` mutations were
not serialized with main-thread `before_update()` mutations. The correction
is stable candidate `0434de3` over `f2555d5..0434de3`. It keeps model work
outside the runtime lock:

1. The worker snapshots the motion anchor under `ReanchorRuntime._lock`.
2. Detection and candidate embeddings run outside the lock.
3. The worker reacquires the lock, rebases candidate motion angles if the
   anchor changed, and calls `TripleGateState.evaluate()` while locked.
4. Every reseed-failure increment and fail-limit read now uses the same lock.

A deterministic interleaving regression blocks inside `gate.evaluate()` and
proves a concurrent main-boundary `before_update()` cannot pass until the
worker releases the lock. A second regression proves reseed-failure increments
also wait for that lock.

The same batch closes all three non-blocking test/audit notes:

- two `TrackLoop` integration tests pin replacement-before-update ordering,
  event persistence and fatal fail-closed termination;
- persisted DISAGREE/REANCHOR fields now distinguish `LOST_DIRECT` from
  `K_HYSTERESIS`;
- a direct worker-state regression pins one confirmed-death restart followed
  by permanent fail-closed behavior, and another test pins the reseed failure
  limit without requiring a worker message.

Post-fix checks:

```text
.venv-track/bin/python -m unittest discover -s tests -v
Ran 96 tests
OK

UV_CACHE_DIR=/private/tmp/p1-detect-uv-cache \
  uv pip check --python .venv-yoloe/bin/python
Checked 42 packages
All installed packages are compatible
```

The real-model synthetic 20 Hz benchmark still passes the 50 ms main-loop
budget after the lock change: main p50/p95/max
`11.195/13.981/18.671 ms`, detector `97.991 ms`, appearance gate
`25.649 ms`, total worker `124.915 ms`, cadence `1/1`, clean worker shutdown,
and no fatal reason. The config and model artifacts are unchanged.
