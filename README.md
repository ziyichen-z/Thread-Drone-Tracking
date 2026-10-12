# Thread Drone Tracking

Language-directed target acquisition and following for a (tethered or untethered) drone:
a **Unity 6** simulation, a **Python** controller with a resident detector + tracker fast layer,
and a **LoRA fine-tuned Qwen3-VL-2B** that grounds a sentence ("the red car", "the taxi to the
right of the bus") to a box, or explicitly answers *ambiguous* / *none*, served with llama.cpp on a
**Jetson Orin Nano 8GB**. The project was built end to end with a multi-role AI collaboration
workflow (proposal → acceptance → implementation → independent review → user Unity validation),
and every number below carries its evidence tier.

> 中文简介：系留/无缆无人机的语言指定目标获取与跟随闭环。Unity 6 仿真提供场景与真值，Python
> 控制器承载常驻快层（在域微调 YOLO11n + BoT-SORT + 位姿补偿 + 指针式指定解析），微调后的
> Qwen3-VL-2B 以 Q4_K_M 量化跑在 Jetson Orin Nano 8GB 上，把一句话映射到画面中的候选框并显式报告
> 歧义与不存在。仓库同时保留了多角色 AI 协作流程的合同、复核与证据文档。

## Repository layout

| Path | What it holds |
|---|---|
| `Assets/TetheredTracking/` | Unity C# runtime (drone plant, independent gimbal, scenario bootstrap, 5 Hz sensor frame writer, tracking-observation receiver, coverage evaluator), editor evidence generators, EditMode / PlayMode tests |
| `controller/` | Python runtime: file-bridge protocol, resident `TrackLoop`, gated publisher, language-session state machine, target manager, resident core (track history + designation resolution), `det-assoc-v1` fast-layer plugin, body planners |
| `tools/` | Data contracts and builders (`eng_sft`), LoRA training + cloud runner + return verification, detector qualification (`eng_det`), Jetson probes (`eng_jet`), replay harnesses (`eng_acq`, `eng_capture`, `eng_fastfix`), closed-loop ops (`eng_loop2`), workflow checkers (`check_docs.py`, `check_role_writes.py`, `githooks/`) |
| `tests/` | `unittest` suite, including ground-truth isolation guards for the controller |
| `config/` | Scenario configs (`scenario.default.json` tethered, `scenario.untethered.json` mainline) and per-work-item parameter files |
| `docs/` | Design baseline (`phase1-single-drone-design.md`), workflow rules, role definitions, proposals with acceptance contracts, independent reviews, evidence reports |
| `runtime/` | File-bridge location, generated at run time (see `runtime/README.md`) |
| `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/` | Role prompts and reading order for the AI collaboration workflow |

## Not included in this public snapshot

- `Assets/SimplePoly City - Low Poly Assets/` — a licensed Unity Asset Store package. Import it
  yourself; its demo scene is the project's startup scene and the runtime scripts spawn the drone,
  gimbal, target vehicle, and evaluator into it at Play time.
- Model weights, LoRA adapters, datasets, captured frames, and everything under `outputs/`.
- Process ledgers tied to the private working tree (status board, authorization ledger, Unity test
  log, archives) and the git history. This repository is a snapshot export.
- Local identifiers: home-directory paths, the board user name and Tailscale addresses in code and
  documents are replaced by placeholders (`~/`, `jetson`, `100.100.100.100`).

## Architecture

```
operator (language / click / confirm)
        │
Unity 6 sim ──frames 5 Hz──▶ file bridge (runtime/, atomic publish, frame_id) ──▶ controller + fast layer
   ▲                                                                                   │   ▲
   └──────────────── body / gimbal commands ◀───────────────────────────────────────────┘   │
   │                                                                     designate(frame k) │ box + frame_id
   └─ ground truth ──▶ offline scorer (CoverageEvaluator) only              Jetson Orin Nano 8GB: llama.cpp Q4_K_M VLM
```

- **Ground-truth isolation**: Unity truth reaches only the offline scorer; unit tests enforce an
  import closure on the controller.
- **frame_id binding**: the VLM answers "a box in frame *k*"; the fast layer keeps 128 frames of
  track history, resolves the designation at *k* (same-frame match → short SOT replay and adoption
  → world-point slew), and only then publishes an observation.
- **Explicit reporting**: `ambiguous`, `none`, lost, and unreachable are first-class outputs; the
  publish gate is fail-closed on integrity errors and drops single frames on timing errors.

## Results (snapshot of 2026-10-12; tier = accepted / reading / diagnostic)

| Item | Value | Tier |
|---|---|---|
| Qwen3-VL-2B zero-shot probe, 405 rows | 68% overall, 0 ambiguity reports | reading |
| LoRA SFT (r16, 17.4 M params, 1× RTX 5090, $1.72) single-target grounding, 609-row frozen eval | 51.0% → 77.6% (+26.6 pp; +5.8 pp vs the older prompt-v1 probe), parse failures 103 → 0, relational instructions 8.1% → 82.6% | reading |
| Functional gates (ambiguity reporting, false-none, …) | 1 of 5 passed | reading |
| Same model merged → GGUF Q4_K_M on Jetson (llama.cpp) | 76.4% vs 77.6% bf16, p50 1.71 s per query, ~3.0 GiB RSS | diagnostic |
| In-domain YOLO11n, held-out recall @IoU 0.5 | target S/M/L 0.879 / 0.987 / 0.731, 0.154 FP per frame; 3 of 8 pre-registered gates missed | reading |
| Detector + VLM co-resident on the 8 GB board, 2 × 30 min | peak 5.09 GiB, swap 0, zero steady-state frame drops | diagnostic |
| Gimbal-turn track loss, root-caused by offline replay | centre-only pose compensation cut synthetic-roll break rate 39% → 6% | diagnostic |
| Body follow (`standoff-band-v1`), 273 s Unity run | centre error p50 37.5 px, follow distance p50 14.0 m, 0 losses | accepted |
| Unity ↔ fast layer ↔ Jetson VLM closed loop | 4 designation → bind → track cycles end to end | diagnostic |

Details and limits: `docs/reviews/P1-ENG-SFT-002-stage-summary.md`, `docs/evidence/P1-ENG-FAST-002-report.md`,
`docs/evidence/P1-ENG-JET-001-report.md`, `docs/evidence/COORD-CORES-DIAG-2026-10-09/`,
`docs/evidence/COORD-RECHARTER-2026-10-09/replay-results-2026-10-09.md`.

## Running

Unity: open the project with Unity `6000.4.1f1` (URP), import SimplePoly City from the Asset Store,
open its demo scene and press Play. Frames are published to `runtime/frames/latest.json`.

Python (from the repository root, Unity in Play mode):

```bash
python3 -m venv .venv-track && .venv-track/bin/pip install -r tools/requirements-track.txt
python3 controller/gimbal_entry.py --mode look-at --x 150 --z 117
python3 controller/body_entry.py --mode velocity --vx 1 --vz 0 --expires 2
python3 controller/tracking_entry.py --latest --x 0.4 --y 0.4 --width 0.2 --height 0.2
```

Tests (no GPU or model needed; tests that need local assets skip):

```bash
python3 -m unittest discover -s tests
```

Expected in this snapshot: five "append-only" guard tests in `test_language_bridge`, `test_pose_gmc`,
`test_capture_session` and `test_capture_click_web` compare the working tree against a pinned git
commit (`accepted_base_commit()`) and cannot pass without the original history; `test_scene006_probe`
carries legacy failures that also exist in the source tree. Everything else passes.

Other requirement sets: `tools/requirements-language.txt` (VLM serving / language loop),
`tools/requirements-eng-sft.txt` (LoRA training), `tools/requirements-yoloe-probe.txt`.

## Workflow

Roles are functions, not models: ideation writes proposals, acceptance rules on them and writes
binding clarifications, implementation delivers code with per-clause evidence, review re-reads the
real code in a throw-away worktree and may only write a review file, and the user runs Unity checks
and signs budget envelopes. Engineering work items carry `AC-n` acceptance contracts and pass
mandatory stops K1–K5. See `AGENTS.md`, `docs/collaboration-workflow.md`,
`docs/engineering-workflow.md`, and `docs/roles/`.

## License

MIT for the code and documents in this repository. The excluded Unity Asset Store package keeps
its own license. Qwen3-VL-2B-Instruct is Apache-2.0; YOLO11 weights follow Ultralytics' license.
