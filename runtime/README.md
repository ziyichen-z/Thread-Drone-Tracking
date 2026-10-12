# Runtime exchange

Unity and Python communicate only through this generated directory. Writers
publish JSON files atomically.

- `body_command.json`: aircraft-body velocity or hold command
- `gimbal_command.json`: independent camera look-at or nadir command
- `frames/frame_<id>.jpg` + `frames/frame_<id>.json`: immutable image/metadata
  bundle. Ordinary live frames use `tethered-sensor-frame/v3` and carry
  finite non-negative `capture_monotonic_s` plus
  `capture_monotonic_clock_id=system-stopwatch/v1`; the reviewed re-anchor
  path accepts only that exact contract. Historical scouting readers may
  read v1 archives. RATE-002 retains its dedicated v2 process-relative clock
  and cannot be combined with detector re-anchor.
- `frames/latest.json`: atomically published pointer to the latest complete
  bundle; consumers must read this first
- `tracking_observation.json`: external tracker output tied to a sensor
  `frame_id`, using normalized top-left `xywh` coordinates
- `language_request.json`: single-slot operator request for the
  `P1-ENG-LOOP-001` language-select loop (`tethered-language-request/v1`).
  Writers must hold `language_request.lock` (O_EXCL, carrying pid and
  `request_id`); a writer that bypasses the lock is illegal and its overwrite
  is not guaranteed to be detectable. Every accepted request is answered
  exactly once through the `last_request` receipt in `tracker_state.json`.
- `language_result.json`: the current epoch's most recent language result
  (`tethered-language-result/v1`). It carries the model's three-state answer
  (`unique`/`ambiguous`/`none`), the closed-loop statuses that replace it on
  failure, the bound frame identity, and the model identity block. Every
  result is also appended to the session's own `results.jsonl`; this file is
  only the latest snapshot.
- `tracker_state.json`: operator-facing session state
  (`tethered-tracker-state/v1`): the eight session states, the suspect and
  reason closed sets, the `publishing` gate flag, retired `track_id` lineage
  and the request receipt. `tracking_observation.json` is unchanged and still
  carries no state. Its `confidence_source` stays the closed set
  {`tracker`, `placeholder`} and is **uncalibrated**: `placeholder` means the
  frozen NanoTrack-v2 core exposes no score, so the published confidence is
  not a detection probability and must never be thresholded by a consumer.
  Model identity lives only in `language_result.json`, never in the
  observation bridge.
  P1-ENG-ACQ-001 resident sessions (`SessionConfig.resident`, pointer fast
  layer) add a ninth state `ACQUIRING`, the reasons `acquire_failed` /
  `slew_timeout` / `adopt_timeout`, keep `publishing` true in `QUERYING` and
  `AWAITING_CONFIRMATION` while a pointer track exists, and add the field
  `designation {designation_id, frame_id_k, head_frame_id, result,
  resolution_level, track_id, level2, candidates, acquire}` whose `result` is
  the closed set `BOUND` / `BOUND_COASTING` / `TRACK_ENDED` / `NO_TRACK_AT_K` /
  `AMBIGUOUS` / `FRAME_NOT_IN_HISTORY` (`track_id` there is the resident
  associator's integer id; the published observation still carries only the
  pointer's `<session>-t<n>` id and schema v1 is unchanged). The session's
  `publish-receipts.jsonl` gains the channel `slew_look_at` (at most one
  `WRITTEN` per `designation_id`; a repeat is `PUBLISH_REJECTED(slew_repeated)`).
  LOOP-001 segment sessions write none of these fields.
  P1-ENG-LOOP-002 (resident sessions only; segment/threshold paths unchanged):
  the reason closed set gains `rebuild_limit` and `geometry_rejected`
  (appended, not reordered); a resident session ends `TERMINAL` with
  `duration_reached`, `backend_fatal` or `rebuild_limit` (third carrier
  rebuild) besides `operator_stop`. The `language_result.json` model block may
  carry six conditionally required llama keys (`mmproj_sha256`,
  `runtime_binary_sha256`, `runtime_build` `^b[0-9]{1,7}$`, `quantization`
  `{Q4_K_M}`, `response_format_sha256`, `decode_config_sha256`): all or none,
  and only with `backend http` + `model_form c2-merged`; older readers drop
  them silently, so only LOOP-002 code consumes them. `language_request.json`
  bodies for `ask`/`respecify` may carry optional `delay_s` (0–8 s
  presentation delay) and `intent` (operator label written only to the session
  journal receipt, never to a query or decision). `publish-receipts.jsonl`
  records explicit `hold_body()` calls on the existing `body_safety_hold`
  channel with `detail {mode: hold, explicit: true, reason: loop_start |
  acquiring | acquire_failed}`. The session journal (`language-session.jsonl`)
  uses the closed `JOURNAL_KINDS` set, adds `result_arrived` /
  `result_presented` / `presentation_discarded` / `resident_rebuild_limit`,
  and `frames_processed` carries `metadata_sha256` (sha256 of
  `frames/frame_<id>.json` bytes at write time, same order as `frame_ids`,
  `null` plus `metadata_sha256_missing_reason` when unreadable).
- `language_session.lock`: single active language-session slot (pid plus
  `session_id`); a live holder makes a second session start refuse with
  `SESSION_SLOT_BUSY`.
- `metrics.json`: `C_geom`, correct-ID `C_track`, conditional coverage, image
  quality, and saturation diagnostics
- `scenario_config.json`: optional scenario override; the versioned fallback is
  `config/scenario.default.json`
- `runs/<run_id>/`: P1-TRACK-001 versioned manifest, per-frame JSONL,
  reconstructed summary, and the final evaluator metrics snapshot when
  available. Raw run directories stay local; acceptance summaries and artifact
  hashes are recorded under `docs/evidence/`.
- `rate-study/previews/`: transient first-frame previews selected from the
  frozen `[7,8)` simulation-time window.
- `rate-study/staging/<attempt_id>/`: exact init image/metadata staged for
  visual confirmation before a P1-M2 rate-study run.
- `p1_detect_scouting_session.json`: create-once active marker for a dedicated
  `P1-DETECT-001` non-measurement validation capture. Its exact bytes match the
  durable session manifest and bind the checked-in scenario hash plus all
  frozen scouting thresholds.
- `p1-detect-scouting/<session_id>/truth/frame_<id>.json`: immutable
  evaluator-only target/distractor truth sidecars. Controller code and tracker
  inputs must never read this path.
- `p1-detect-scouting/<session_id>/{reference.json,scouting-result.json}`:
  hash-bound initialization crop and create-once offline scouting report.
- `p1_detect_qualification_release.json`: create-once top-level pointer for an
  active non-RATE `P1-DETECT-001` qualification release. A failed attempt
  deliberately leaves it for diagnosis, but `CoverageEvaluator` only arms it
  when the bound command was issued after the current Unity evaluator
  session's Unix and shared host-monotonic starts and the scenario matches.
  Older/foreign markers are inert for ordinary Unity sessions: they do not
  block observations, reset aggregation, or enter `metrics.json`. The stale
  pointer still blocks a different qualification release until its run-local
  artifacts are preserved and the top-level slot is explicitly cleared; never
  delete the immutable `runs/<run_id>/qualification-release-*.json` chain.

`P1-M2-RATE-001` sessions are managed from the project root with
`.venv-track/bin/python -m tools.run_rate_study`. The helper installs only the
checked-in 5/20 Hz configs, removes runtime exchange slots without touching
`runs/`, freezes rate-specific calibration images/boxes, requires explicit
visual confirmation of a generated rectangle overlay before calibration and
before launch, and refuses ambiguous, early-terminated, or incomplete N=3
summaries. `preview-box` draws on a separate inspection copy; raw sensor images
remain unchanged. A bad calibration is preserved and released for redo with
`invalidate-calibration`; measured runs use the corresponding stage/run
invalidation commands. Run `... run_rate_study --help` for subcommands.

`P1-DETECT-001` scouting is managed with
`.venv-yoloe/bin/python -m tools.run_detector_scouting`. The `prepare`
subcommand refuses active RATE measurement state or unarchived frame/metric
slots, installs only `config/scenario.p1-detect-scouting.json`, and creates a
non-measurement session. Its Unity-only
`gimbal_driver=truth_directed_scouting` disables the external gimbal command
receiver and points through the existing 45-degree-clamped `LookAtWorld`
plant. After the user captures simulation time 0–114/120 s,
`preview-reference` selects the first complete `[7,8)` frame and
`bind-reference --box X Y W H` freezes the exact initialization crop.
`analyze` applies the pre-data 2 Hz / 65 m / confidence 0.25 / IoU 0.30
contract, counts missing image/truth pairs as misses, and writes target versus
distractor DINOv2 distributions without tuning thresholds. Recall is
explicitly an oracle-pointed detectability upper bound, never closed-loop
recall. If and only if a preserved result is invalidated by the reviewed A3
bbox-schema recovery, `reanalyze-a3 --supersedes-result-sha256 HASH` writes a
new versioned result plus a create-once plan and supersession receipt; it never
overwrites or deletes the original. `close --analysis-id bbox-schema-v2`
verifies that complete two-result hash chain before removing only the active
marker. No command moves the anchor or starts a successor campaign.

`P1-ENG-LOOP-002` stage-B operations (OpsK1K2K3K4 increment, not yet reviewed or
run on the board) go through one staged entry,
`.venv-yoloe/bin/python -m tools.eng_loop2.play_ops`, documented in
`docs/evidence/P1-ENG-LOOP-002-play-ops.md` section 0A. It never writes a bridge
file or lock itself: every ask/respecify/confirm/reject/release/stop is the
original `python -m controller.language_loop <action>` CLI, issued through one
shared submit record by the local operator page
(`tools/eng_loop2/operator_web.py`, `127.0.0.1` only). The page only reads
`tracker_state.json`, `language_result.json`, `frames/latest.json` and the frame
it points to, plus the session's own `previews/`; it never reads truth files.
Its records (`ops-web.jsonl`, `feedback.jsonl`, `play-record.json`,
`ops-summary.*`) live under `outputs/eng-loop2/P1-ENG-LOOP-002/`, not here.
After a Play the entry only renames this attempt's `frames/frame_*`,
`retained_frame_metadata/`, `m3_body_truth.jsonl`, `runs/<SID>-resident*/` and
`scenario_config.json` into that output tree (an existing target stops it; no
deletion). The diagnostic mode (`--mode diagnostic diag`, the single signed
`P1-ENG-LOOP-002:9bac8fd0:SUB:3` run; diagnostic only, never evidence, no gate)
first renames any existing `scenario_config.json`, `frames/` and
`m3_body_truth.jsonl` into its own root
`outputs/eng-loop/P1-ENG-LOOP-002/diagnostics/<UTC>/hold/held/`, writes its
own overlay, runs one `--diagnostic` session whose session and segment roots are
inside that diagnostic root (nothing under `runtime/runs/`), renames that Play's
`frames/` and truth file into `play/<diag SID>/`, moves its overlay to
`hold/overlay-diag.json` and renames the held items back at closeout. It never
deletes anything here and never reads the truth file.
