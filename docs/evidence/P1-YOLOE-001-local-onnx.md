# P1-YOLOE-001 — local PyTorch/ONNX evidence

Date: 2026-07-22

Owner/role: Codex / implementation and evidence

Scope: local macOS PyTorch + ONNX stage only

Implementation snapshot: `84dbc32`

Status: **REVIEW_PASSED**

## Question

Can one standard YOLOE export accept a new visual prompt at runtime, or does
the export bake the prompt that was active at export time?

This closes the desktop-simulation part of design risk R0. It does not
establish TensorRT behavior, latency, memory, or Orin compatibility; those
questions are intentionally deferred to M7 and are not current dependencies.

## Environment

- macOS 26.5.2 arm64, Apple M4
- CPython 3.12.13 in `.venv-yoloe`
- PyTorch 2.13.0, CPU
- Ultralytics 8.4.104
- ONNX 1.22.0
- ONNX Runtime 1.27.0, CPUExecutionProvider
- onnxslim 0.1.94

The direct probe dependencies are pinned in
`tools/requirements-yoloe-probe.txt`. The environment and all generated model
files live outside version control.

## Inputs

The reference/source images are retained Unity sensor frames. Their hashes make
the run identifiable even though `runtime/` is intentionally ignored.

| Role | File | SHA-256 | Prompt box (`xyxy`, pixels) |
|---|---|---|---|
| Export prompt | `runtime/frames/frame_0000000032.jpg` | `cd9c6552ae114f7cbec8f1d52483fabb12e257c2c4e28022485b896789f00971` | Red target car: `(508, 219, 591, 261)` |
| Inference source | `runtime/frames/frame_0000000033.jpg` | `67032c0cb22c4bb5b4be33a751c5ebf6aeb2a2d5381f8d3dfbdb02ebb63a3072` | N/A |
| Post-export prompt | same frame 32 | same as above | Distinct yellow car: `(380, 228, 491, 274)` |

The report explicitly asserted
`reprompt_differs_from_export_prompt=true`. This prevents a same-prompt retry
from being mistaken for dynamic re-prompt support.

## Reproduction

From the repository root:

```bash
uv venv --python 3.12 .venv-yoloe
uv pip install --python .venv-yoloe/bin/python \
  -r tools/requirements-yoloe-probe.txt
mkdir -p runtime/yoloe
cd runtime/yoloe
../../.venv-yoloe/bin/python ../../tools/yoloe_dynamic_prompt_probe.py \
  --model yoloe-11s-seg.pt \
  --reference ../frames/frame_0000000032.jpg \
  --source ../frames/frame_0000000033.jpg \
  --prompt-box 508 219 591 261 \
  --reprompt-reference ../frames/frame_0000000032.jpg \
  --reprompt-box 380 228 491 274 \
  --export-format onnx \
  --device cpu \
  --output yoloe_dynamic_prompt_probe.json
```

The first run downloads the official `yoloe-11s-seg.pt` weight. Generated
weights, ONNX files, settings, and JSON output remain under ignored
`runtime/yoloe/`.

## Result

| Step | Result | Exploratory timing/count |
|---|---|---|
| PyTorch visual-prompt inference | PASS | 0.774 s, 14 boxes |
| PyTorch cached-prompt inference | PASS | 0.067 s, 14 boxes |
| ONNX export with prompt active | PASS | 0.835 s; 38.7 MB model |
| Exported ONNX static inference | PASS | 0.199 s, 17 boxes |
| Load export as `YOLOE`, submit new prompt | REJECTED | `AttributeError` at `dynamic_prompt_predict`: `'str' object has no attribute 'task'` |
| Load export as generic `YOLO`, submit new prompt | REJECTED | `SyntaxError` at `dynamic_prompt_predict`: `'refer_image' is not a valid YOLO argument.` and `'visual_prompts' is not a valid YOLO argument.` |

The box counts use confidence `0.01` and are only pipeline-liveness
diagnostics. They are not detection-accuracy evidence. Timings are one warm
local CPU run and are not deployment benchmarks.

## Implementer conclusion

The standard export supports static inference but does not expose a runtime
input path for a distinct visual prompt. Therefore one fixed standard ONNX
artifact cannot satisfy “change target by changing only the first-frame
prompt.”

This rules out the naive fixed-export architecture. For the active computer
simulation, the selected runtime is PyTorch YOLOE, which already accepts the
first-frame visual prompt; the ONNX artifact remains a static export experiment,
not the simulation runtime.

Per-target export and custom prompt/VPE splits are future deployment alternatives
only. They will be reconsidered in M7 if the user explicitly starts the
Jetson/TensorRT track. No TensorRT download or NVIDIA environment is required
for M0-M6.

## Independent review

Sonnet recorded `PASS` in `docs/reviews/P1-YOLOE-001.md` after verifying:

1. the pre-export prompt and post-export prompt are genuinely distinct;
2. static exported inference succeeds before the dynamic-reprompt conclusion;
3. both supported exported-model loading paths are tried and failures are
   attributed to `dynamic_prompt_predict`, not download/export failure;
4. the conclusion rules out only the standard fixed export and does not claim
   TensorRT or accuracy evidence;
5. the pinned dependency file and reproduction command match the probe.

Unity validation is `N/A` for this local model/export experiment.
