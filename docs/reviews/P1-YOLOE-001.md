# P1-YOLOE-001 — independent verification

Reviewer/role: Claude Sonnet / independent verification

Round: 1

Date: 2026-07-22

Implementation snapshot: candidate `84dbc32` (confirmed `84dbc32..ef91248` is
docs-only via `git diff --stat`: only `docs/current-status.md`,
`docs/evidence/P1-YOLOE-001-local-onnx.md`, `docs/implementation-status.md`,
and `docs/reviews/P1-YOLOE-001.md` changed, 22 lines total). Reviewed at
`HEAD` (`ef91248`), which is code-identical to `84dbc32`.

Verdict: **PASS**

## Scope discipline

`git diff ae4364b..84dbc32 --stat` (the M0-close boundary to this candidate)
touches only `.gitignore`, four docs files, `tools/requirements-yoloe-probe.txt`,
and `tools/yoloe_dynamic_prompt_probe.py`. No file under `Assets/`,
`controller/`, `tests/`, or `config/` changed, so this candidate cannot have
regressed the just-closed `P1-M0-001` gate. No implementation code was
modified during this review.

## Accepted requirements checked

- A pre-export visual prompt is exercised successfully in PyTorch.
- The exported ONNX artifact performs ordinary static inference.
- A genuinely different visual prompt is attempted after export.
- Dynamic re-prompt is tested through both `YOLOE` and generic `YOLO` export
  loading paths.
- The conclusion is limited to the standard local ONNX export and does not
  overclaim TensorRT, Orin performance, or detection accuracy.

## Files and evidence read

- `tools/yoloe_dynamic_prompt_probe.py` (full file, 293 lines)
- `tools/requirements-yoloe-probe.txt`
- `docs/evidence/P1-YOLOE-001-local-onnx.md`
- `docs/phase1-single-drone-design.md`, section 3.4 (including the new
  "M0 本地证据" paragraph added in this candidate)
- `docs/implementation-status.md`, `docs/current-status.md`

**Additionally read, not just the markdown summary** — this is the part of
the review I weighted most heavily, since a transcribed summary is exactly
the kind of thing this role must not take on faith:

- The raw machine-generated `runtime/yoloe/yoloe_dynamic_prompt_probe.json`,
  left on disk from Codex's actual run (git-ignored, not committed — I did
  not generate it, I only read it).
- The actual retained frames `runtime/frames/frame_0000000032.jpg` and
  `frame_0000000033.jpg`, including viewing frame 32 as an image.
- The actual exported `runtime/yoloe/yoloe-11s-seg.onnx` file size.

## Independent verification performed (no install/download)

Per the user's explicit choice this round, I did not install
`tools/requirements-yoloe-probe.txt` or download the YOLOE weight to
literally re-run the probe (that would need a multi-GB dependency install and
a network fetch of a third-party model checkpoint — a nontrivial download
action requiring separate authorization). Instead I cross-checked every
claim in the evidence document against artifacts I could read or recompute
directly, which turned out to be extensive because Codex's actual run
artifacts were still present in the (git-ignored) working tree:

1. **Recomputed the frame hashes myself**:
   ```
   $ shasum -a 256 runtime/frames/frame_0000000032.jpg runtime/frames/frame_0000000033.jpg
   cd9c6552ae114f7cbec8f1d52483fabb12e257c2c4e28022485b896789f00971  frame_0000000032.jpg
   67032c0cb22c4bb5b4be33a751c5ebf6aeb2a2d5381f8d3dfbdb02ebb63a3072  frame_0000000033.jpg
   ```
   Both match the evidence document's table and the raw JSON's
   `reference_sha256`/`source_sha256`/`reprompt_reference_sha256` fields
   exactly. The two named files are the real images, not placeholders.

2. **Viewed frame 32 directly.** The prompt box `(508, 219, 591, 261)` lands
   exactly on a red car and the reprompt box `(380, 228, 491, 274)` lands
   exactly on a distinct yellow-and-black vehicle a short distance to its
   left in the same frame — I confirmed this by eye, not by trusting the
   labels in the table. This directly satisfies review-boundary item 1
   ("the pre-export prompt and post-export prompt are genuinely distinct")
   at the level of actual pixel content, not just non-identical coordinates.

3. **Read the raw probe output JSON in full** and compared every field
   against the evidence document's Result table:

   | Field in `yoloe_dynamic_prompt_probe.json` | Evidence doc claim | Match |
   |---|---|---|
   | `pytorch.prompted_inference_seconds = 0.7739...` | "0.774 s, 14 boxes" | matches (`prompted_box_count = 14`) |
   | `pytorch.cached_prompt_inference_seconds = 0.0672...` | "0.067 s, 14 boxes" | matches (`cached_prompt_box_count = 14`) |
   | `export.seconds = 0.8346...` | "0.835 s; 38.7 MB model" | matches |
   | `exported_static_inference = {0.1994s, 17 boxes}` | "0.199 s, 17 boxes" | matches exactly |
   | `exported_dynamic_reprompt.attempts.load_as_yoloe` → `failure_stage: "dynamic_prompt_predict"`, `AttributeError: 'str' object has no attribute 'task'` | same, verbatim | matches exactly |
   | `exported_dynamic_reprompt.attempts.load_as_generic_yolo` → `failure_stage: "dynamic_prompt_predict"`, `SyntaxError: 'refer_image' is not a valid YOLO argument. \n'visual_prompts' is not a valid YOLO argument.` | paraphrased as "`refer_image` and `visual_prompts` are not valid exported-model arguments" | faithful paraphrase, not a distortion (see Non-blocking note below) |
   | `conclusion = "standard_export_bakes_prompt_and_requires_per-target_export_or_custom_split_graph"` | "standard export supports static inference but does not expose a runtime input path for a distinct visual prompt" | matches the script's own conclusion enum |
   | `reprompt_differs_from_export_prompt = true` | "explicitly asserted `reprompt_differs_from_export_prompt=true`" | matches |
   | `platform/python/ultralytics/torch/onnx/onnxruntime` version fields | Environment section | matches every field |

4. **Recomputed the exported model's file size**:
   ```
   $ ls -la runtime/yoloe/yoloe-11s-seg.onnx
   40557471 bytes = 38.68 MB
   ```
   Matches "38.7 MB model" in the evidence document.

Taken together — independently recomputed hashes, an independently viewed
image, an independently measured file size, and a field-by-field read of the
actual machine-generated JSON rather than the prose summary of it — this is
about as strong a form of evidence corroboration as is available without
personally re-running the pipeline, and none of it turned up any
discrepancy.

## Review checklist (per Codex's stated review boundary)

- [x] **The pre-export prompt and post-export prompt are genuinely distinct.**
  Verified by direct visual inspection (item 2 above), not just by trusting
  `reprompt_differs_from_export_prompt` or the coordinate-inequality check in
  [yoloe_dynamic_prompt_probe.py:134-138](../../tools/yoloe_dynamic_prompt_probe.py)
  (which is itself sound: it flags a difference if either the file hash or
  the box coordinates differ, so a same-file/different-box case like this
  one is correctly treated as distinct).
- [x] **Static exported inference succeeds before the dynamic-reprompt
  conclusion.** Confirmed by reading control flow: `model.export(...)` →
  `static_model = YOLO(...)` → `static_model.predict(...)` all run and are
  recorded in `report["exported_static_inference"]`
  ([yoloe_dynamic_prompt_probe.py:187-210](../../tools/yoloe_dynamic_prompt_probe.py))
  strictly before the `attempts` dict and `report["conclusion"]` are computed
  ([yoloe_dynamic_prompt_probe.py:212-245](../../tools/yoloe_dynamic_prompt_probe.py)).
  The raw JSON shows this step actually passed (`box_count: 17`, no error).
- [x] **Both supported exported-model loading paths are tried and failures
  are attributed to `dynamic_prompt_predict`, not download/export failure.**
  `exported_reprompt_attempt()`
  ([yoloe_dynamic_prompt_probe.py:56-97](../../tools/yoloe_dynamic_prompt_probe.py))
  separates a `load_export` try/except from a `dynamic_prompt_predict`
  try/except; the raw JSON confirms both `load_as_yoloe` and
  `load_as_generic_yolo` attempts report `failure_stage:
  "dynamic_prompt_predict"`, meaning both model loads succeeded and only the
  runtime reprompt call failed. Not a download or export artifact problem.
- [x] **The conclusion is limited to the standard local ONNX export and does
  not overclaim TensorRT, Orin performance, or detection accuracy.** The
  evidence document's Question section states up front "This is the local
  half of design risk R0. It does not establish TensorRT behavior, latency,
  memory, or Orin compatibility," and explicitly disclaims the box counts and
  timings as "pipeline-liveness diagnostics," "not detection-accuracy
  evidence," and "not deployment benchmarks." The script's own `conclusion`
  string only ever names `"standard_export..."`, never TensorRT. The new
  design-doc paragraph
  ([phase1-single-drone-design.md:112-119](../../docs/phase1-single-drone-design.md))
  likewise states "每目标导出与自定义 VPE/主干拆分仍需在
  NVIDIA/TensorRT 阶段比较" (still open, pending the TensorRT stage) rather
  than asserting a final architecture decision.
- [x] **The pinned dependency file and reproduction command match the
  probe.** `tools/requirements-yoloe-probe.txt`'s versions
  (`torch==2.13.0`, `ultralytics==8.4.104`, `onnx==1.22.0`,
  `onnxruntime==1.27.0`, `onnxslim==0.1.94`) match the evidence document's
  Environment section and the raw JSON's self-reported versions exactly. The
  reproduction command's flags (`--model`, `--reference`, `--source`,
  `--prompt-box` with 4 values, `--reprompt-reference`, `--reprompt-box`,
  `--export-format`, `--device`, `--output`) match
  `parse_args()`
  ([yoloe_dynamic_prompt_probe.py:249-279](../../tools/yoloe_dynamic_prompt_probe.py))
  argument-for-argument.

## Findings

### Blocking

None found.

### Non-blocking

1. **Evidence document paraphrases one error message instead of quoting it
   verbatim.** The raw JSON's `load_as_generic_yolo` error is `"'refer_image'
   is not a valid YOLO argument. \n'visual_prompts' is not a valid YOLO
   argument."`; `docs/evidence/P1-YOLOE-001-local-onnx.md`'s Result table
   renders this as "`refer_image` and `visual_prompts` are not valid
   exported-model arguments" — a faithful, meaning-preserving paraphrase (I
   verified this against the raw JSON myself), not a distortion, so this does
   not affect the verdict. For a document whose entire purpose is to be an
   auditable evidence record, I'd still suggest quoting framework error
   strings verbatim (in a code block) rather than paraphrasing them, so that
   future readers don't have to re-run the probe to know exactly what the
   framework said.
2. **The runtime-evidence trail is fragile by construction.** The strongest
   part of this review — reading the actual `yoloe_dynamic_prompt_probe.json`
   and cross-checking hashes/file sizes against real files — was only
   possible because Codex's run artifacts happened to still be sitting in
   the git-ignored `runtime/yoloe/` directory. Nothing requires that; if this
   directory is cleaned before the next review (as `docs/unity-test-log.md`'s
   M0 regression entries describe doing for their own temporary files), a
   future round would have to trust the versioned markdown summary alone.
   This is not a defect in the current evidence (which I was able to fully
   corroborate), but it means the evidence document's own claims, not the raw
   JSON, are the durable record. No action needed now; noting it so a future
   reviewer doesn't assume the raw JSON will still be there.

## Missing or weak tests

This is a one-shot architecture-risk probe producing a diagnostic JSON
artifact, not a persistent runtime contract like the M0 file bridge — I did
not apply the "needs a pytest/Edit-Mode suite" bar from the `P1-M0-001`
reviews here, since there is no ongoing behavior to regress against. The one
gap worth naming: the probe's own distinctness check
([yoloe_dynamic_prompt_probe.py:134-138](../../tools/yoloe_dynamic_prompt_probe.py))
and its three-way conclusion branch
([yoloe_dynamic_prompt_probe.py:238-245](../../tools/yoloe_dynamic_prompt_probe.py))
have no unit test of their own (e.g. asserting `conclusion ==
"inconclusive_reprompt_was_not_distinct"` when `reprompt_box == prompt_box`).
That logic is simple enough that I verified it by inspection rather than
treating this as blocking, but if the probe is reused for the TensorRT stage
or for other model candidates later, a small offline unit test for just the
conclusion/distinctness logic (no model/network required) would be cheap
insurance.

## Requirement-to-evidence mapping

| Requirement | Evidence | Verdict |
|---|---|---|
| A pre-export visual prompt is exercised successfully in PyTorch | `pytorch.prompted_inference_seconds=0.774s`, `prompted_box_count=14` in the raw JSON; script order at [yoloe_dynamic_prompt_probe.py:161-171](../../tools/yoloe_dynamic_prompt_probe.py) | Met |
| The exported ONNX artifact performs ordinary static inference | `exported_static_inference={0.199s, 17 boxes}` in the raw JSON, recorded before any reprompt attempt at [yoloe_dynamic_prompt_probe.py:199-210](../../tools/yoloe_dynamic_prompt_probe.py) | Met |
| A genuinely different visual prompt is attempted after export | `reprompt_differs_from_export_prompt=true`; independently confirmed by viewing frame 32 — red car vs. distinct yellow/black vehicle at the claimed pixel boxes | Met |
| Dynamic re-prompt is tested through both `YOLOE` and generic `YOLO` export loading paths | `exported_dynamic_reprompt.attempts.{load_as_yoloe,load_as_generic_yolo}`, both `failure_stage="dynamic_prompt_predict"` (load succeeded, predict rejected) | Met |
| Conclusion does not overclaim TensorRT/Orin/accuracy | Evidence doc's explicit disclaimers; script's `conclusion` field never mentions TensorRT; design-doc paragraph frames per-target-export/custom-split as still open | Met |

## Requested Codex action

None blocking. Optionally: quote the `load_as_generic_yolo` error verbatim in
the evidence document (Non-blocking note 1). Codex may record this gate as
passed and proceed with the NVIDIA/TensorRT stage of `P1-YOLOE-001` when that
hardware is available, and may accept `P1-TRACK-001`'s Fable proposal per the
current active handoffs — neither is blocked by this verdict.

## Re-review result

Not required unless the TensorRT stage or a probe-script change reopens this
work item for a new round.

## Codex closure and user scope clarification

Date: 2026-07-23

Codex accepted the Round 1 `PASS` and closed `P1-YOLOE-001` as `DONE` for the
desktop-simulation scope. The user subsequently clarified that current work is
computer simulation rather than physical deployment and explicitly declined a
TensorRT download. PyTorch YOLOE is therefore the M0-M6 dynamic-prompt runtime;
the standard ONNX artifact remains architecture evidence only.

Any Jetson/TensorRT work is now tracked separately as
`P1-M7-DEPLOY-001 = DEFERRED_BY_USER`. It begins only after an explicit user
instruction and does not reopen or block M0-M6. This closure note does not
alter Sonnet's original review text or verdict.
