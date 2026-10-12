# P1-DETECT-001 scouting protocol implementation

Date: 2026-07-28  
Role: Codex (implementation)  
Candidate: `d0c2dde`; review range `296a0de..d0c2dde`

Input decision: user-approved protocol in
`docs/evidence/P1-DETECT-001-scouting-readiness.md`

## Outcome

The approved §8 scouting protocol is implemented as a stable review candidate.
No scouting session was prepared or captured, no result was computed, no
threshold or geometry was changed, and no qualification/successor campaign was
started. The candidate stops for Sonnet before any Unity data collection.

## Evaluator-only truth path

- `config/scenario.p1-detect-scouting.json` is byte-versioned and differs from
  the frozen 20 Hz follow scenario only in scenario identity plus retention:
  2560 frames (128 s) and 4096 pending evaluator frames. Its SHA-256 is
  `68170d801b559c7dea238cf57873f2b2eab6a47bbbb9904e7fa8b5498723c61c`;
  route timing is `106.48528137423858 s`.
- `P1DetectScoutingSession` validates the dedicated non-measurement identity,
  path-safe session ID, exact scenario hash, and approved `106.485 s`, 2 Hz,
  65 m, confidence 0.25 and IoU 0.30 constants. `CoverageEvaluator` refuses a
  session with an active RATE measurement controller, wrong scenario/hash or
  wrong active distractor count.
- `CoverageEvaluator` remains the only Unity-truth consumer. For each published
  sensor frame it emits a create-once
  `p1-detect-scouting-truth/v1` sidecar containing evaluator visibility,
  target bbox/slant range and sorted marked-distractor boxes. Frame truth files
  cannot be overwritten. Controller/tracker source has a regression audit
  proving it does not reference the session or sidecar path.

## Capture and offline entry points

`python -m tools.run_detector_scouting` provides five fail-closed subcommands:

1. `prepare --session-id`: refuses active measurement state, an active scouting
   marker, or unarchived frame/metric slots; installs the checked-in config and
   writes identical active/durable manifests create-once.
2. `preview-reference`: selects the first complete sensor frame in `[7,8)` and
   freezes an exact raw-image/metadata hash preview.
3. `bind-reference --box X Y W H`: validates a fully clipped normalized box,
   renders a separate overlay, and create-once binds the exact initialization
   crop without changing the raw image.
4. `analyze`: requires capture coverage from the bound initialization time
   through one full loop; samples the first frame at/after fixed half-second
   ticks; filters complete pairs by evaluator-visible target and slant range
   `>=65 m`; counts every missing sensor/image/truth pair conservatively as a
   recall miss; counts a hit only for a frozen YOLOE proposal with confidence
   `>=0.25` and target IoU `>=0.30`; and reports target/distractor DINOv2
   cosine distributions plus the frozen 0.5/0.1 gate pass counts.
5. `close`: hash-binds the create-once result in a completion receipt, then
   removes only the matching active marker. Durable session, truth, reference
   and result artifacts remain.

Recall `<0.5` deterministically returns `RETURN_TO_USER_OPTION_B`. Recall
`>=0.5` returns `GO_CURRENT_GEOMETRY` for the recall clause but the overall
result stays `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`: the approved protocol did
not define a new automatic distribution-feasibility statistic, so the tool
does not invent one or silently promote descriptive distributions into a
claim.

## Implementer checks

- Python regression: **103/103 passed**, including seven new deterministic
  scouting cases (config equivalence, create-once/non-measurement preparation,
  reference hash chain, IoU, remote filtering, missing-pair miss direction,
  below-0.5 return, close receipt and truth-boundary audit).
- Merged YOLOE/DINOv2 environment: `uv pip check` reports **42/42 compatible**.
- Python byte compilation and `git diff --check`: pass.
- Unity Roslyn direct compilation: runtime and Edit Mode test assemblies pass
  against Unity 6000.4.1f1 response files. The already-open Unity 6000.4.10f1
  editor also imported the new source and refreshed both
  `TetheredTracking.Runtime.dll` and `TetheredTracking.EditModeTests.dll`
  without a C# compiler error.
- The focused Unity batch Edit Mode invocation was attempted but correctly
  refused because another Unity instance owns the project. Therefore the five
  new Edit Mode tests are **compiled but not claimed executed**; Sonnet should
  run them after the editor is available.

## Post-review note handling

Sonnet Round 3 returned `PASS_WITH_NOTES` on `d0c2dde` and independently ran
the focused and full Unity suites. Before the first real capture, Codex handled
the two non-blocking notes without changing the approved recall rule, geometry,
thresholds, or model decision in post-review note-fix candidate `f3f815b`:

- N4: evaluator visibility and renderer projection are intentionally distinct.
  A visible target whose renderer projection is null is now written create-once
  with a null target box instead of throwing. Offline analysis already maps
  this exact record to `TARGET_BOX_MISSING`, increments the recall denominator,
  records no hit, and does not classify it as a missing sensor/truth pair.
  Focused Unity and Python regressions cover both halves of that contract.
- N5: `floor(106.485281... * 2) + 1 = 213` fixed ticks cover the inclusive
  interval from initialization through `+106.0 s`. Capture completeness still
  requires sensor coverage through `+106.485281... s`; the unsampled fractional
  seam is therefore retained as coverage evidence but is not a 214th tick.
  This is the deterministic interpretation already implemented, now stated
  explicitly.

Post-review implementer checks:

- The first focused Unity run exposed that `JsonUtility` serializes a null
  reference-type box as a zero-valued object. The writer now converts only
  those validation-impossible zero objects to explicit JSON `null`, for both
  target and distractor boxes. The corrected focused suite passes **11/11**,
  and the full Edit Mode suite passes **84/84** under Unity 6000.4.10f1.
- Python passes **104/104** and the merged YOLOE/DINOv2 environment still
  reports **42/42 compatible**. These are implementer checks after the
  independent `PASS_WITH_NOTES`; they are not represented as a new
  independent review.
- Session preparation remained withheld when the accepted text said “20 Hz
  follow” without declaring its driver. Fable showed baseline SOT would
  condition visibility on known drift and re-anchor would be circular. The
  user then authorized Capture Amendment A2: a scouting-identity-gated
  Unity-only truth driver through the existing clamped `LookAtWorld` plant,
  with external gimbal commands disabled, manifest/sidecar driver identity,
  and an oracle-upper-bound-only result label. This result-determining change
  returns to a Sonnet stable-candidate stop before session preparation.

## Capture Amendment A2 implementation

- The create-once active/durable session now requires
  `gimbal_driver=truth_directed_scouting`; Unity rejects missing or different
  identities. Every truth sidecar repeats the exact driver and offline loading
  rejects any mismatch.
- `CoverageEvaluator` constructs the Unity-only driver only after the full
  non-measurement scenario/hash/distractor gate passes. It disables and logs
  the external `GimbalCommandReceiver`, then refreshes
  `TetheredGimbal.LookAtWorld(target.position)` every Unity update. The plant's
  45° off-nadir clamp, slew and saturation code is unchanged.
- The offline result repeats the driver under `frozen_protocol` and labels
  recall `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND` with
  `closed_loop_recall_claimed=false`. The detector/re-anchor controller still
  has no reference to the session, driver or truth sidecar.
- Automated coverage includes invalid driver identities, create-once
  sidecar identity, external-receiver disablement, moving-target refresh,
  unchanged 45° Play Mode saturation, offline truth mismatch rejection,
  result labeling and the expanded controller-zero-reference audit.
- Final implementer checks pass Python **105/105**, focused Edit Mode
  **12/12**, full Edit Mode **85/85**, focused Play Mode **1/1**, full Play
  Mode **3/3**, and merged-package compatibility **42/42** under Unity
  6000.4.10f1. The first Play assertion was test-only and incorrectly assumed
  one batch frame always supplied enough slew time; the final test isolates
  the clamp with a high test-only slew rate and directly verifies 45°.
- No active/durable scouting session, truth capture, reference or result was
  created. Capture Amendment A2 stops for Sonnet before `prepare`.

## Real session preparation after independent review

After Sonnet Round 4 returned `PASS`, Codex executed the reviewed create-once
`prepare` path exactly once:

- session ID: `p1-detect-001-scout-1`;
- active session and durable manifest: byte-identical, SHA-256
  `63d62c673524c5534cc17b22848f5635f100110501bf8d39921599f2b00d8dfc`;
- installed and checked-in scouting scenario: byte-identical, SHA-256
  `68170d801b559c7dea238cf57873f2b2eab6a47bbbb9904e7fa8b5498723c61c`;
- preserved preexisting scenario config: SHA-256
  `78b06c466fb8724a763948aebbf0f04782881abc5f625bb4f9c1c8b11016804c`.

Immediately after preparation, `runtime/frames`, `runtime/metrics.json`,
the session truth sidecar, reference and result were all absent. This is a
prepared-but-uncaptured state, not scouting evidence. The next authorized
action is one fresh user-run Unity Play session at normal time scale, stopped
between 114 s and 120 s simulation time. No second `prepare` is permitted.

## Real Unity capture and reference preview

The user reported the single Unity Play capture complete on 2026-07-28.
Post-capture validation found:

- 768 strictly increasing sensor metadata files and 768 corresponding images;
- 705 create-once truth sidecars with valid session, scenario, frame, time and
  `gimbal_driver=truth_directed_scouting` identities;
- first `[7,8)` reference candidate: frame 47 at
  `7.111673831939697 s`;
- required one-loop endpoint: `113.5966738319397 s`;
- final sensor frame: frame 767 at `121.11769104003906 s`, leaving
  `7.521017208099366 s` coverage margin;
- zero missing images and 60 missing truth sidecars in the one-loop analysis
  window. Per the pre-data contract, those missing pairs remain recall misses.

The `metrics.json` route-relative elapsed value (`111.11521911621094 s`) is
not substituted for the frozen sensor `simulation_time_s` completeness clock.
The create-once `preview-reference` command selected frame 47 and recorded
image SHA-256
`f3c701926838d1e02259a3f80cde7bebb9622260b74494aa48a5db0966e5f16e`
and metadata SHA-256
`3f6a9d375501f90f0ee6a0d4ab95feb04e98aa2027f9f562aa8a11b7367a681d`.
No `reference.json` or `scouting-result.json` exists. Codex proposed normalized
top-left `xywh` `[0.46875, 0.410416667, 0.0625, 0.14375]` around the central
red target and stopped for the user's visual confirmation before binding.

## First real analysis attempt: retained invalid

The user confirmed the displayed target rectangle. Codex bound it create-once;
the formal overlay SHA-256 is
`8e7e5b144227766ffc070e625160819139999124b6d5988cc7a13ecc0c9977fb`.
The first frozen `analyze` invocation then wrote `scouting-result.json` with
SHA-256
`c7876364d2ca406b23894088df73c9d4a66080070c78bea201ac179a02fcf8b4`.
It is retained but is not a valid complete report and has not been closed.

Root cause is a concrete schema mismatch:

- `P1DetectScoutingTruthWriter` serializes every non-null box as
  `{x,y,width,height}`;
- `_cosine_or_none` and `intersection_over_union` pass truth boxes directly
  to `_validate_box`, which enumerates a four-element sequence;
- enumerating the mapping supplies strings `x`, `y`, `width`, `height`, so
  conversion fails and `_cosine_or_none` reports `CROP_INVALID`.

All 27 `REMOTE_VISIBLE` target samples consequently have null target cosine,
zero target-score count and zero separation opportunities. A read-only probe
normalized frame 312's mapping to a tuple and produced a finite unit DINOv2
embedding with target cosine `0.4280213166942009`, proving that the recorded
crop is usable. The result's recall branch is `0/45`, including 18 missing-pair
misses; all 27 remote samples independently report `proposal_count=0`, so no
IoU call occurred and the Option B recall direction is not caused by this
schema mismatch. The required embedding distribution is still absent, so
`close` was not run and no completion receipt exists.

Recovery requires a narrow protocol addition: preserve the invalid result
under a hash/reason-bound invalidation receipt, normalize only exact Unity box
objects (while retaining sequence support), add direct object-schema tests,
stop for Sonnet re-review, and then reanalyze the same immutable capture.
No recapture, threshold change, geometry change or automatic go decision is
proposed. Because this extends the accepted five-command lifecycle, Codex
stopped for explicit user authorization before implementation.

## Recovery Amendment A3 implementation candidate

The user authorized A3 with Fable's versioned-reanalysis and real-fixture
bindings. Codex accepted it with two additional bindings: the canonical result
must remain byte-identical and unclosable through the A3 path, and Unity may
canonicalize only right/bottom normalized-coordinate overshoot no greater than
`1e-5`.

The stable implementation candidate adds:

- one strict `normalize_box` boundary shared by IoU and embedding. It accepts
  only an object whose key set is exactly `x`, `y`, `width`, `height`, or a
  non-string four-element sequence. Every value must be a finite JSON number;
  bools, strings, missing/extra keys, null, non-finite values, degenerate boxes
  and boxes outside the normalized image fail closed;
- a create-once `reanalyze-a3` lifecycle with analysis identity
  `bbox-schema-v2`. Its plan binds the preserved canonical result hash and
  parser schemas; its versioned result binds the plan and superseded-result
  hashes; its supersession receipt binds both result hashes, reason
  `BBOX_SCHEMA_MISMATCH` and the plan hash. A3 close verifies that chain, while
  canonical close refuses after an A3 plan exists;
- a 765-byte fixture copied byte-for-byte from real sidecar frame 312. Fixture
  and source both have SHA-256
  `a661652b8003af2784a6d134fc7b6fa35ebcb8bdcb3d30c0a80eb8a09fb027a1`;
  the test parses the real object-shaped target/distractor boxes directly;
- Unity writer canonicalization for finite, positive boxes with legal origins
  whose right or bottom endpoint exceeds 1 only by at most `1e-5`. It clamps
  width/height to the remaining boundary. A direct Edit Mode test accepts a
  tiny bottom-edge overshoot and still rejects a material `0.001` overshoot.

The user's Console screenshot was corroborated against `Editor.log`: exactly
63 `invalid_scouting_distractor_truth` exceptions occurred, matching the
full-capture difference between 768 sensor frames and 705 truth sidecars.
The writer already permits explicit null boxes and every distractor identity
was stable, so the boundary-roundoff path is the remaining trigger. Existing
missing sidecars are not repaired or regenerated; the 60 that fall in the
frozen analysis window remain conservative recall misses.

Implementer verification under Unity `6000.4.1f1`:

- focused `P1DetectScoutingEditModeTests`: **13/13**;
- full Edit Mode: **86/86**;
- Python: **109/109**;
- merged `.venv-yoloe` package compatibility: **42/42**;
- Python byte compilation and `git diff --check`: pass.

No Play Mode rerun is required for this candidate: A3 changes the create-once
offline recovery lifecycle and the already directly tested truth writer; it
does not change the A2 gimbal driver, plant, capture loop or Play behavior.
The prior A2 full Play Mode 3/3 evidence remains applicable.

The real immutable state is unchanged after implementation and tests:

- canonical invalid result SHA-256 remains
  `c7876364d2ca406b23894088df73c9d4a66080070c78bea201ac179a02fcf8b4`;
- active session SHA-256 remains
  `63d62c673524c5534cc17b22848f5635f100110501bf8d39921599f2b00d8dfc`;
- no real A3 plan, versioned result, supersession receipt or completion exists.

The candidate stops for Sonnet. Real `reanalyze-a3`, A3 close, qualification
and automatic feasibility/go decisions remain prohibited until independent
review passes.

## Real A3 recovery after independent review

Sonnet Round 5 returned `PASS` on candidate `28b9e84`. Codex then ran the
reviewed recovery commands exactly once against the real immutable session:

```text
.venv-yoloe/bin/python -m tools.run_detector_scouting reanalyze-a3 \
  --runtime runtime \
  --supersedes-result-sha256 \
  c7876364d2ca406b23894088df73c9d4a66080070c78bea201ac179a02fcf8b4
.venv-yoloe/bin/python -m tools.run_detector_scouting close \
  --runtime runtime --analysis-id bbox-schema-v2
```

The create-once recovery chain is:

- preserved canonical invalid result:
  `c7876364d2ca406b23894088df73c9d4a66080070c78bea201ac179a02fcf8b4`;
- A3 plan:
  `fd34cf1f95e6ad33004716f22e42e7fe6a2a0f5c64407e3097d60b4199186112`;
- versioned A3 result:
  `295f17df3bbbb1fd30ca3c4a2afec9789af860672dd4c6351a76867026ff779d`;
- supersession receipt:
  `840e99f62774ac24db56ca112b9865d4af223fb53e49375acd9a1146639ad38c`;
- A3 completion:
  `9760909ee9a08e9eb60cd40ecaa7dbb04cf823059f7f018334f5bb3402ee69f5`.

Close validated the chain, wrote completion schema
`p1-detect-scouting-completion/v2`, and removed the active-session marker.
The original result remains byte-identical.

The completed pre-registered report is:

- oracle-pointed recall: **0/45 = 0.0**, including 18 conservative
  missing-pair misses; all 27 remote-visible frames still have zero YOLOE
  proposals;
- target DINOv2 cosine: **27** samples, min `0.3128710903`, median
  `0.3983915409`, mean `0.3992461348`, max `0.5272393935`; only **1/27**
  reaches the frozen uncalibrated `0.5` threshold;
- distractor cosine: **0** samples; separation opportunities and margin
  passes are both zero, so the report does not establish distractor
  separation feasibility;
- frozen result: `RETURN_TO_USER_OPTION_B`.

Because recall is below the pre-registered `0.5` gate, the current geometry is
not qualified regardless of the embedding interpretation. No qualification
or `UT-P1-DETECT-001-001` run may start. Per accepted §8, the next action is a
user design decision on Option B: move the anchor toward the loop center
(declared far slant-range change approximately 75 m to 46 m, target
approximately 14 px) under a new scenario/batch identity. Codex does not make
that geometry change automatically.

## Sonnet review scope

Review candidate `d0c2dde` over `296a0de..d0c2dde`, while retaining the
existing runtime Round 2 `PASS`, focusing on:

- active/durable session identity and scenario-hash binding;
- create-once truth/reference/result semantics and stale-artifact refusal;
- `CoverageEvaluator`-only truth production and controller non-consumption;
- fixed-tick selection, conservative missing-pair denominator and IoU recall;
- reference/model hash chain and target/distractor cosine reporting;
- the explicit refusal to auto-decide embedding feasibility or tune/move
  anything; and
- the seven Python tests plus five focused Unity Edit Mode tests.

### Capture Amendment A2 Sonnet scope

Review stable candidate `fa1156d` over `67223c4..fa1156d`, while retaining
the earlier Round 2 runtime `PASS` and Round 3 scouting-tool
`PASS_WITH_NOTES`, focusing on:

- strict active/durable `gimbal_driver` identity and per-frame sidecar binding;
- `CoverageEvaluator`-only driver construction after the complete
  non-measurement scenario/hash/distractor gate;
- deterministic external `GimbalCommandReceiver` disable/log behavior and
  moving-target refresh through the unchanged 45°/slew/saturation plant;
- zero controller references to session, driver or Unity truth;
- offline truth-driver mismatch rejection and the explicit
  `ORACLE_POINTED_DETECTABILITY_UPPER_BOUND` /
  `closed_loop_recall_claimed=false` result contract; and
- the new Python, Edit Mode and Play Mode tests. Do not prepare or capture a
  real session during review.

### Recovery Amendment A3 Sonnet scope

Review A3 stable candidate `28b9e84` over `5ffacd9..28b9e84`, retaining the
earlier runtime/scouting/A2 review verdicts. Focus on:

- exact dual-schema normalization and fail-closed rejection at the shared
  IoU/embedding boundary;
- byte-for-byte real-capture fixture provenance and direct use in tests;
- create-once plan/result/supersession/completion identities and preservation
  of the canonical invalid result;
- refusal of canonical close once A3 begins and complete A3 close hash-chain
  validation;
- the Unity `1e-5` right/bottom-only canonicalization bound and rejection of
  material/non-finite/negative/degenerate boxes; and
- proof that no capture data or real A3 artifact was created during
  implementation. Do not run real `reanalyze-a3` or close during review.
