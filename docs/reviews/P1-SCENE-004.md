# P1-SCENE-004 independent review

Status: ROUND_2_PASS_WITH_NOTES

Reviewer: Claude Sonnet (independent review role)

Implementation author: Codex

## Candidate and requirements

- Accepted design: `docs/proposals/P1-SCENE-004-benign-coverage-circuit.md`,
  revision 2, Codex Round 2 `ACCEPTED_WITH_BINDING_CLARIFICATIONS` (BC1–BC6).
- Formal design: `docs/phase1-single-drone-design.md` v0.3.7.
- Candidate: `d93e38e` over `b4a2dae..d93e38e` (the only implementation
  commit in range; `1e4bbb2` is a status-board-only follow-up, confirmed by
  `git show --stat`).
- Implementer evidence: `docs/evidence/P1-SCENE-004-implementation.md`,
  plus the four generated artifacts (`P1-SCENE-004-gate0-probe.json`,
  `P1-SCENE-004-anchor-audit.json`, `P1-SCENE-004-scene-survey.json`,
  `P1-SCENE-004-geometry.json`).

## Required independent scope (from the Active-handoffs entry)

1. The BC2 write path: a fail-closed throw became a written document — check
   nothing that should fail closed now passes, and that the classifier keys
   off `target_box_status`, not the box.
2. The accounting classes: `TARGET_VISIBLE_UNPROJECTABLE` cannot enter the
   gating denominator by any path; health gate strictly precedes recall;
   legacy v1 takes the conservative class.
3. Legacy isolation: `tools/run_detector_scouting.py` and the frozen
   `p1-detect-001-scout-1` chain must be behaviourally unchanged.
4. The `private` → `internal` widening in `P1Scene003AnchorAudit.cs`.
5. The audit's four gates, especially whole-disc support, tangency-as-
   violation, and BC3's envelope constraint binding every lattice candidate.
6. The geometry artifact's measured-scale pixel prediction.

## Verdict

### Round 1 (2026-07-29): PASS_WITH_NOTES

Candidate `d93e38e`. Diffed the real range directly rather than trusting the
implementer narrative, reran every automated check myself, and independently
reproduced both of the stop point's two central empirical claims (Gate 0's
recall and the geometry envelope) from the pinned models and the checked-in
scenario bytes rather than reading the JSON as given.

**Automated evidence, reproduced myself.** Ran
`.venv-track/bin/python -m unittest discover -s tests`: **132/132** passed,
matching the cited count exactly. Ran a full Unity `6000.4.1f1` batchmode
Edit Mode pass myself (`-testPlatform EditMode`, no filter): **100/100**
passed, 0 failed, including all 8
`P1Scene004AnchorAuditTests`. Ran a full Play Mode pass: **3/3** passed. None
of these numbers came from the implementer's log; all three are fresh runs
in this session.

**Gate 0, independently re-executed with the real pinned models (item 6,
partially item 3).** Built my own sandbox byte-copy of `runtime/frames` and
`runtime/p1-detect-scouting` (SHA-256 of every file matched the live
`runtime/` tree before the run), then ran
`tools/run_scene004_gate0_probe` myself under `.venv-yoloe` against that
copy — not the checked-in `docs/evidence/P1-SCENE-004-gate0-probe.json`.
Result: `decision=PROCEED_TO_IMPLEMENTATION recall=0.897059 (183/204)`,
exactly reproducing the implementer's figure to six decimal places. Re-hashed
the live `runtime/p1-detect-scouting` tree afterward: byte-identical to
before my run. The frozen scout-1 archive is untouched by both the
implementer's run and mine.

**Geometry artifact, independently re-derived (item 6).** Ran
`tools.build_scene004_geometry.build_geometry()` myself against the
checked-in scenario bytes: `status=ENVELOPE_OK`, all five gates pass, max
slant `30.586599...` m and max off-nadir `35.824596...` deg — matching the
checked-in artifact to eight significant figures. This confirms the artifact
is genuinely re-derivable from the frozen scenario/road/contract bytes, not
hand-edited to pass.

**Anchor audit, spot-checked against the real-scene artifact (item 5).**
Parsed `docs/evidence/P1-SCENE-004-anchor-audit.json` directly:
`924 + 288 + 20 + 25 = 1257` (support + envelope + clearance + legal =
total), `status=CLEAR`, selected anchor `(140.0, 1.3113418617649586e-06,
108.0)`, max slant `30.5866` m / margin `1.4134` m, max off-nadir `35.8246`°
/ margin `9.1754`° — all match the evidence doc and the checked-in
`config/scenario.p1-scene-004.json`'s `anchor_world_m` exactly.

**The four gates, read in full (item 5).** `P1Scene004AnchorAuditor
.AuditCandidate` evaluates support → road-disjointness → envelope →
clearance in strict sequence per candidate, short-circuiting on the first
failure and recording `"NOT_EVALUATED"` for gates not reached — confirmed
this against `EnvelopeGateRejectsCandidatesTheFallbackWouldOtherwiseAccept`
and `AnchorDiscTouchingTheAsphaltBandIsRejected`, both of which assert the
downstream gates stay `"NOT_EVALUATED"` on a failing candidate. `SupportUnderDisc`
requires `StrictlyInsideConvex` on the *centre* **and**
`DistanceToBoundary(...) > radius + epsilon`, i.e. the whole 1.5 m disc
strictly inside the patch with margin, not merely its centre point —
this is the literal SCENE-003 lesson and is directly tested
(`DiscHangingOverTheSupportBoundaryIsNotSupported`). `DiscTouchesSurface`
treats `distance <= radius + epsilon` as a violation, so tangency fails,
confirmed by `AnchorDiscTouchingTheAsphaltBandIsRejected`'s exact-tangent
case. BC3 (every lattice candidate must satisfy the envelope, not just a
support/clearance-selected winner) is directly exercised by
`EnvelopeGateRejectsCandidatesTheFallbackWouldOtherwiseAccept`: a
candidate that passes support and road-disjointness but whose frozen
circuit pushes off-nadir past 45° is correctly rejected with
`ENVELOPE_OUT_OF_BOUNDS`, `clearance_status` never evaluated. Margin
arithmetic (`off_nadir_margin_deg`, `slant_range_margin_m`) is verified
against closed-form trigonometry in
`EnvelopeMarginsMatchTheClosedFormGeometry` to `1e-3` — I re-derived the
same closed form by hand and it matches. Candidate ordering is
distance→x→z as required
(`FallbackLatticeIsDeterministicAndOrderedByDistance`).

**`private` → `internal` widening (item 4).** Diffed
`P1Scene003AnchorAuditor.cs`: seven members (`GeometryEpsilon`,
`Footprint`, `StrictlyInsideSurface`, `TransformFootprint`,
`RequireSupportedTransform`, `StrictlyInsideConvex`, `DistanceToConvex`,
`IntervalsOverlap`, `ToXZ`) go from `private`/no-modifier to `internal`;
zero logic lines changed. Access-modifier widening cannot alter runtime
behaviour by itself, and the full Edit Mode run I reproduced above (100/100,
which includes the unmodified SCENE-003 audit tests) confirms no regression.

**BC2 write path (item 1).** Read `P1DetectScoutingTruthWriter.Write` in
full. For the target box: if a box is offered and canonicalizes, status is
`VALID`; if offered but not canonicalizable, the document is now written
(not thrown away) with `target_bbox_xywh_norm = null` and status
`TARGET_VISIBLE_UNPROJECTABLE`; if no box is offered at all, status follows
`target_visible` (`UNPROJECTABLE` if visible, `NOT_VISIBLE` otherwise). A
blank distractor id still throws (verified: still fail-closed, per the new
Edit Mode assertion `Assert.Throws<InvalidOperationException>` on
`distractors[0].distractor_id = "  "`). Confirmed nothing that should fail
closed now passes: identity/type/range checks on `frame_id`,
`simulation_time_s`, `target_slant_range_m`, `target_visible_sample_fraction`,
and `target_track_id` are unchanged, still throw before the box-status
branch is ever reached. On the Python side, `classify_truth` keys off
`target_box_status`/`target_visible`, never off box presence for v2
documents, and a v2 document with `target_visible=True` but no status set is
explicitly rejected (`test_v2_visible_target_without_a_status_is_rejected`,
which I re-ran as part of the 132/132). This closes the exact hole BC2 named:
a zeroed `JsonUtility`-serialized box with an explicit `UNPROJECTABLE`
status is correctly classified off the status, not the box shape
(`test_zeroed_box_with_unprojectable_status_is_not_gating`).

**Accounting classes and health gate (item 2).** `analyze_session` computes
`strict = counts[PAIRED_VISIBLE]` and
`conservative = strict + counts[UNPROJECTABLE] + counts[MISSING_PAIR]`, and
decides in order: missing-rate → unprojectable-rate → zero-paired-visible →
strict-recall → distractor-sample-floor → awaiting-review. This is health
strictly before recall, exactly as BC2/B3 require, and is exercised by a
direct regression reproducing scout-1's own failure mode
(`test_missing_pairs_trip_the_health_gate_before_recall`: 40% missing pairs,
perfect detector, decision `CAPTURE_INCOMPLETE` / `MISSING_PAIR_RATE_ABOVE_LIMIT`,
strict recall still `1.0`) plus a symmetric one for the unprojectable-rate
gate. `TARGET_NOT_VISIBLE` never enters either denominator. Legacy v1
documents (no `target_box_status` field) are classified conservatively —
absent box on a v1 document becomes `CLASS_UNPROJECTABLE`, never
`PAIRED_VISIBLE` — confirmed by `test_legacy_v1_is_readable_and_conservative`.

**Legacy isolation — real scout-1 chain (item 3).** `tools/run_detector_scouting.py`
is not in the changed-file list for this commit (confirmed via
`git show d93e38e --stat`); its `TRUTH_SCHEMA` constant is still hardcoded
to the v1 string. The frozen `p1-detect-001-scout-1` archive on disk is
still schema v1 throughout (spot-checked several sidecars), and both the
implementer's Gate 0 run and my independent rerun re-hashed it
byte-identical before and after. This part of "legacy isolation" holds.

### Round 2 (2026-07-29): PASS_WITH_NOTES

Candidate `617f933` over `d93e38e..617f933` (the scout-3 session lifecycle
and the closure of all five round 1 notes). Fresh context: re-read
`docs/current-status.md`, `AGENTS.md`, `docs/collaboration-workflow.md`, the
accepted proposal (revision 2 + Annex A, Codex round 3
`ACCEPTED_WITH_BINDING_CLARIFICATIONS`), and the round 1 review above before
touching anything. Confirmed `9558492` and `9946fac` (the two commits between
`617f933` and `HEAD`) touch only `docs/current-status.md`,
`docs/archive/`, and the proposal's Annex A section — no code changed, so I
reviewed at `HEAD` directly (`git diff --stat 617f933..HEAD -- ':!docs'
':!*.md'` is empty). Annex A (A1 probe-mid, A2 healthcheck) is accepted but
explicitly out of scope for this candidate per the proposal itself ("两项均
不属于候选 `617f933` 的停点范围") — I did not review or expect any A1/A2 code.

**Automated evidence, reproduced myself, not read from the log.** Ran
`.venv-track/bin/python -m unittest discover -s tests`: **137/137** passed,
matching exactly. Ran a full Unity `6000.4.1f1` batchmode Edit Mode pass
(no filter): **102/102** passed (0 failed), including both new anchor-audit
tests. Ran a full Play Mode pass: **3/3** passed. Regenerated
`docs/evidence/P1-SCENE-004-anchor-audit.json` myself via
`-executeMethod TetheredTracking.Editor.P1Scene004AnchorEvidenceGenerator.Generate`
after saving the pre-run file: byte-identical, SHA-256
`4e1eca2c48f789641a517494b654fba89f0576fdf81c31555c31d6a30b7313a6` before and
after, `git status --short` clean throughout. Independently rebuilt the
geometry artifact with `tools.build_scene004_geometry.build_geometry()`:
`ENVELOPE_OK`, all five gate margins match the checked-in artifact exactly
(slant 1.4134005642575858, off-nadir 9.17540428837038, period
1.0710678118654755, pixel 5.088339893207287, distractor opportunities 39).
Confirmed no `p1-scene-004-scouting` directory exists anywhere under
`runtime/` before or after my test runs, and nothing under the frozen
`runtime/p1-detect-scouting/p1-detect-001-scout-1` archive has a newer mtime
than `docs/current-status.md` — no scout-3 session, capture or measurement
was created by this review, and the frozen scout-1 chain is untouched.

**Note 1 closure (item: the `IScoutingTruthSession` refactor and the
legacy-path byte-equivalence).** Read `IScoutingTruthSession`,
`P1DetectScoutingSession`, and the new `P1Scene004ScoutingSession` in full.
The writer (`P1DetectScoutingTruthWriter`) composes its directory from
`session.SessionRoot`/`session.SessionId` only — grepped the constructor and
confirmed no directory-literal string remains. `P1DetectScoutingSession`
returns the unchanged legacy constant (`RuntimeSessionRoot =
"p1-detect-scouting"`); `P1Scene004ScoutingSession` returns its own
(`"p1-scene-004-scouting"`), matching the Python `SESSION_ROOT` constant
exactly (`test_python_and_unity_agree_on_the_session_root`, which I reran).
`document.work_id` now comes from `scoutingSession.WorkId` at the one real
call site (`CoverageEvaluator.WriteScoutingTruth`) instead of the old
`P1DetectScoutingTruthDocument` field default of the literal
`"P1-DETECT-001"` — I grepped for every construction site of
`P1DetectScoutingTruthDocument` and the only production one now sets
`work_id` explicitly, so removing the default introduces no silent-null risk.
This closes the hazard as claimed.

**The two-active-profile fail-closed check (item: "cannot be bypassed"),
the item the handoff named as highest risk.** Read
`CoverageEvaluator.ConfigureScouting` in full: it loads both
`p1_detect_scouting_session.json` and `p1_scene_004_scouting_session.json`
independently (`hasLegacy`, `hasScene004`), throws
`multiple_active_scouting_sessions` when both exist — before either error
string or scenario-hash check runs, so a stale file from an abandoned profile
cannot be silently ignored even if it itself fails its own validation — and
otherwise proceeds with whichever one loaded. I traced this by hand rather
than trusting the diff summary and it is correct. **However, this exact
branch has zero automated test coverage** — I grepped the whole `Tests/`
tree for `ConfigureScouting`, `p1_detect_scouting_session`, and
`p1_scene_004_scouting_session` and found no hits; nothing calls the private
`ConfigureScouting` method at all (existing tests only call the public
`ConfigureScoutingGimbal`, bypassing the file-loading/selection logic
entirely). This is not a regression specific to this batch — the whole
method, including its pre-existing `scouting_scenario_identity_mismatch` and
`scouting_distractor_count_mismatch` branches, has never had direct
Edit/Play Mode coverage either, so the new branch inherits a pre-existing
blind spot rather than introducing a fresh one. I confirmed correctness by
reading, not by a regression that will catch a future refactor breaking it.
Non-blocking, but worth closing before this exact path is what stands
between a real capture and a corrupted identity.

**Notes 2–5 closures.** N2: `docs/phase1-single-drone-design.md` v0.3.7 now
states precisely "写路径自 SCENE-004 起只发 v2；v1 仅作为已冻结 scout-1 档案
的只读格式保留", matching the evidence doc's corrected framing. N3: distractors
now get `NOT_IN_FRAME` (`P1DetectScoutingTruthWriter.Write`'s distractor
loop); `run_scene004_scouting.py`'s per-distractor handling still only
branches on `status != BOX_STATUS_VALID`, so no accounting number moved —
confirmed by reading `analyze_session`'s distractor loop. N4: reran
`ClearanceIntersectionRejectsAnObstacleInsideTheHoverSphere` — a thin column
at hover height, clear of the ground-volume height bands, correctly trips
`CLEARANCE_INTERSECTION` via the hover-sphere term only. N5: reran
`BlockedStatusDistinguishesAnchorFailureFromEnvelopeFailure` and independently
confirmed `BlockingStatus` derives `ENVELOPE_OUT_OF_BOUNDS` vs
`BLOCKED_ANCHOR_PLACEMENT` from whether any candidate cleared support +
road-disjointness; the real-scene regeneration above is byte-identical,
confirming this is behaviour-free on the `CLEAR` path as claimed.

**Session lifecycle (`prepare`/`preview`/`bind`/`analyze`/`close`).** Read
`tools/run_scene004_scouting.py`'s lifecycle functions and reran the full
`Scene004SessionLifecycleTests` class. `session_document` reads
`loop_period_s` from the geometry artifact rather than restating it, and
binds both `scenario_config_sha256` and `geometry_sha256` — confirmed
`analyze_session` refuses when either differs from the current file bytes.
Every document is create-once via `_create_once`/`_create_or_validate`;
`prepare_session` correctly refuses to let a second, different session take
over the single active-session marker at the runtime root
(`test_prepare_is_create_once_and_refuses_a_second_session`, reran). The
`[7,8) s` reference-preview window and the `≥3`-loop analysis window are
exactly as coded; both remain unproven on real Unity data, as the evidence
doc states.

**Truth-leak allowlist widening.** Reran
`test_truth_sidecar_is_not_referenced_by_controller_runtime`. The allowlist
gained exactly `P1Scene004Scouting.cs`, nothing else; every other file under
`Assets/TetheredTracking/Scripts/*.cs` is still scanned for the truth-shaped
literals. Read `P1Scene004Scouting.cs` end to end: it references
`P1DetectScoutingTruthWriter.TruthSchemaV2` and
`P1DetectScoutingSession.TruthDirectedGimbalDriver` (which is why it needs
the allowlist entry) and touches nothing on the controller or perception
path.

**New, non-blocking findings from this round (none block `617f933`):**

1. **`prepare_session` writes the candidate session's directory and manifest
   before checking whether a different session is already active, unlike the
   legacy `run_detector_scouting.py`'s `prepare_session`, which checks first
   and creates nothing on conflict.** Reproduced directly: preparing
   `p1-scene-004-scout-3` then attempting `p1-scene-004-scout-3b` in the same
   runtime raises the correct `ValueError` and leaves the active marker
   correctly pointed at the original session (no gating or identity impact —
   confirmed the marker's `session_id` is unchanged after the failed call),
   but it also leaves an orphaned
   `p1-scene-004-scout-3b/manifest.json` on disk despite the "refusing to
   replace it" framing. Not reachable by anything that affects a real
   capture's accounting, since Unity only ever reads the active marker at the
   runtime root, but it breaks the create-once discipline the module
   otherwise holds itself to. Recommend reordering to check-then-create,
   matching the legacy tool.
2. **The health gate's `missing_pair_rate`/`unprojectable_rate` denominator
   is `strict + unprojectable + missing` ("conservative"), not the proposal's
   literal wording of `visible_paired + missing_pair_misses` for the
   missing-rate specifically.** Worked the algebra: since the unprojectable
   cap is 2%, the two formulas can disagree about crossing the 5% missing
   line only when the implemented rate sits within about 0.1 percentage
   points of the boundary — under 1 tick at the ~190–220-tick scale scout-3
   actually captures at (3–3.5 loops), so this is not reachable at the sizes
   this profile runs, and both branches still resolve to `CAPTURE_INCOMPLETE`
   whenever either cap is actually crossed. Cosmetic: a one-line comment
   tying the code's denominator to the proposal text would stop a future
   reader from assuming they must match literally.
3. **`analyze_session` does not check `reference.json`'s `schema_version`/
   `work_id`/`scenario_id` fields, only that the preview image hash still
   matches.** Not reachable in the normal flow — `reference.json` is
   create-once and only ever written by `bind_reference`, which populates
   those fields correctly — but it is a smaller validation than `manifest.json`
   gets, which is checked field-by-field.
4. **The evidence doc's own "Sonnet review scope" section (the very end of
   `docs/evidence/P1-SCENE-004-implementation.md`) is stale: it still lists
   round 1's changed-file set (no `CoverageEvaluator.cs`, no
   `P1Scene004Scouting.cs`) and round 1's "known limitations" (**"the scout-3
   session lifecycle... is not implemented"**), even though the section two
   headings above it in the same file describes that lifecycle as built this
   round.** I used `docs/current-status.md`'s Active-handoffs entry as the
   authoritative round 2 scope instead (it is accurate), so this did not
   block or mislead this review, but the next person who jumps straight to
   the evidence doc's tail could be misled into reviewing against the wrong
   file list. Recommend updating that section the next time this file is
   touched.

None of the four new items above are defects in what scout-3's accounting,
the anchor audit, or the session lifecycle actually compute — every claim I
independently re-derived (test counts, the anchor artifact hash, the
geometry margins, the four gate-closure claims) matches exactly. Round 1
notes 1–5 are all closed, verified by rereading the code and rerunning the
relevant tests myself rather than trusting the evidence doc's narrative. No
scout-3 session, capture, or measurement was created by this candidate or by
this review. Codex may proceed: the real scout-3 capture
(`UT-P1-SCENE-004-001`) may now be attempted, and item 1 above (the
`prepare_session` ordering) is worth a small fix first since it is the exact
tool the user will run.

## Non-blocking notes (carried to the todo, not blocking this candidate)

1. **Real forward-compatibility hazard for the next batch: a runtime
   subdirectory name mismatch between the shared Unity writer and the
   scout-3 analyzer.** `P1DetectScoutingTruthWriter`'s constructor
   ([P1DetectScouting.cs:156-161](../../Assets/TetheredTracking/Scripts/P1DetectScouting.cs))
   hardcodes the truth-sidecar directory to
   `Path.Combine(runtimeRoot, "p1-detect-scouting", session.session_id, "truth")`
   — this literal is unconditional and does not vary by scenario/profile.
   `tools/run_scene004_scouting.py`'s `analyze_session`
   ([run_scene004_scouting.py:199](../../tools/run_scene004_scouting.py))
   instead reads
   `runtime / "p1-scene-004-scouting" / session_id / "truth" / ...` — a
   *different* directory name. `P1DetectScoutingSession.Validate()` also
   hardcodes `scenario_id != "p1-detect-scouting"` as an error, so the
   *current* writer/session classes cannot literally be reused unmodified
   for a scout-3 capture regardless — some new or adapted Unity-side
   session/writer code is unavoidable for the "session lifecycle" batch the
   evidence doc defers. But because this commit already modified
   `P1DetectScoutingTruthWriter.Write()`'s box-status logic specifically so
   the *same* writer class could serve scout-3's BC2 accounting, the most
   likely path for the next batch is to keep reusing this class and just add
   a scout-3-shaped session type — and if that happens without also
   reconciling the directory name, every scout-3 capture tick will silently
   read back as `MISSING_IMAGE_TRUTH_PAIR` (the analyzer will find no
   `truth/` directory at all under `p1-scene-004-scouting/<session_id>/`),
   immediately tripping `CAPTURE_INCOMPLETE` regardless of true detector
   performance — a scout-1-shaped failure mode recurring for a different
   reason. Not exercised by this stop point's own tests or evidence (no
   scout-3 Unity-side session/capture code exists yet, correctly, per the
   evidence doc's own stated limitation), so it does not block this
   candidate. Recommend closing this explicitly as part of the scout-3
   session lifecycle batch, before any real capture is attempted.
2. **The "legacy profile kept as-is" characterization is accurate only for
   the already-archived scout-1 data, not for any hypothetical brand-new
   capture under the current code.** The diff flips
   `P1DetectScoutingTruthDocument.schema_version`'s default and
   `Write()`'s validation from the v1 literal to `TruthSchemaV2`
   unconditionally (confirmed: `grep`-ing the whole repo for
   `TruthSchemaV1`/`p1-detect-scouting-truth/v1` shows it is referenced
   nowhere except its own declaration — no code path can make the shared
   writer emit v1 anymore). `tools/run_detector_scouting.py`'s `_load_truth`
   still requires the schema to equal `TRUTH_SCHEMA` (v1) exactly, with no
   upgrade path. In practice this is likely fine: `docs/proposals/P1-SCENE-003-anchor-relocation.md`
   already committed to a *new*, profile-aware tool for `scout-2`
   ("离线分析按 profile 化的 A3 工具运行"), not a raw reuse of
   `run_detector_scouting.py` against a live capture, so a future scout-2
   implementer will be writing new code anyway and can account for v2 then.
   But the evidence doc's framing ("a deliberate cross-rejection") reads as
   if the write path is unchanged, when it is not — only the *read* path for
   the frozen archive is unchanged. Recommend the design/evidence record this
   precisely (write path is v2-only henceforth; v1 is read-only for the
   frozen scout-1 chain) so it is not rediscovered as a surprise when scout-2
   resumes post-M3.
3. **Distractor `box_status` reuses target-oriented naming for an ordinary
   case.** `P1DetectScoutingTruthWriter.Write`'s distractor loop sets
   `box_status = BoxStatusUnprojectable` whenever `bbox_xywh_norm` is null —
   which is the *common* case of a distractor simply being off-screen, not
   only the rarer "was visible but couldn't be projected" case the constant's
   name and doc-comment describe for the target. There is no
   distractor-equivalent of `TARGET_NOT_VISIBLE`. This is harmless in
   practice: `run_scene004_scouting.py`'s per-distractor handling only checks
   `status != BOX_STATUS_VALID`, never branching on which non-valid value it
   is, so no gating or accounting number is affected. Purely a naming/
   documentation-clarity nit inherited from reusing a target-shaped enum for
   distractors.
4. **No isolated Edit Mode test for the fourth gate
   (`CLEARANCE_INTERSECTION`) in the new SCENE-004 composition.** Unlike
   support, road-disjointness, and envelope, which each get a dedicated,
   minimal test, `IntersectsEffectiveVolumes`'s anchor-cylinder/corridor-
   cylinder/hover-sphere composition (new code, though built from
   already-tested primitives shared with SCENE-003) has no small synthetic
   regression case isolating a clearance-only rejection. The real-scene
   artifact does exercise it end to end (20 real `CLEARANCE_INTERSECTION`
   rejections in `docs/evidence/P1-SCENE-004-anchor-audit.json`), which is
   reassuring but not a substitute for a fast, isolated unit test guarding
   against a future regression in this specific composition.
5. **The audit's top-level `status` field collapses two different disposition
   rows.** If every lattice candidate failed, `status` is always
   `"BLOCKED_ANCHOR_PLACEMENT"`, even when every rejection was actually
   `ENVELOPE_OUT_OF_BOUNDS` (which the proposal's disposition table treats as
   a distinct row 2 outcome, `BLOCKED_ROUTE_LEGALITY`/`ENVELOPE_OUT_OF_BOUNDS`,
   not row 1's `BLOCKED_ANCHOR_PLACEMENT`). The granular per-gate rejection
   counts and per-candidate reason codes are all still recorded in the
   artifact, so no information is lost, but a reader relying on the
   top-level `status` string alone could misattribute an envelope-only
   failure to anchor placement. Did not manifest here since the real audit
   returned `CLEAR`; worth a cheap fix (derive `status` from which rejection
   reason dominates, or add a secondary field) whenever this file is next
   touched.

None of the five notes above are defects in what this candidate actually
measured or claims: Gate 0's recall, the anchor audit's `CLEAR` result, the
geometry envelope, the BC2 write-path fix, and the four-gate audit logic are
all independently reproduced and correct. Notes 1 and 2 are forward-looking
risks for the *next*, not-yet-written batch (the scout-3 session lifecycle)
and should shape that batch's design; notes 3–5 are minor clarity/coverage
items. No scout-3 session, capture, or measurement exists, consistent with
the stop-point's own scope. Codex may proceed to close out this stop point
and begin the scout-3 session lifecycle batch, addressing note 1 before any
real capture is attempted.
