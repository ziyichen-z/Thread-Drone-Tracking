# P1-M2-RATE-003 — Independent review

Reviewer: review role (independent code review, strongest pool; fresh
context)

**Latest round: see Round 4.**

## Round 4 — Round 3 blocking findings closure (2026-07-31)

Candidate: `ab8ae73` ("Fix RATE-003 batch 2 review round 3 blocking
findings"), at the same stop point confirmed by acceptance in `a1257b3`
Range reviewed: `dea5111..ab8ae73` (full range)
Implementer evidence: rework section in
`docs/evidence/P1-M2-RATE-003-batch2.md`

**Verdict: PASS_WITH_NOTES**

Both round-3 blocking findings are fixed as requested, in the requested
places, with real regression coverage; no new finding blocks. Batch 2's
code-review gate is now closed on `ab8ae73`.

### 0. Range attribution and scope

Reviewed in a fresh disposable worktree at `ab8ae73` (removed at close).
The range contains exactly one implementation commit — `ab8ae73`, touching
`tools/run_rate3_study.py`, `tests/test_rate3_study.py`, the batch-2
evidence file and the status board/archive — plus the acceptance
stop-point confirmation `a1257b3` and my own round 3 record `aa3dd21`,
both docs-only. I reran `check_role_writes.py --role implementation
--base dea5111`: two flagged paths (the RATE-003 proposal from `a1257b3`,
this review file from `aa3dd21`), both attributed to those
non-implementation commits; `ab8ae73` wrote neither. **Zero changes** to
`Assets/`, `config/`, `controller/`, the audit tools or any committed
evidence artifact across the whole range (empty diff, verified) — so
round 3's Unity results (Edit 162/162, Play 3/3 on byte-identical C#) and
artifact verification carry over to `ab8ae73`, the same carry-over logic
round 2 applied to `57f2561`.

### 1. Finding 1 (probe artifact dead end) — closed

Verified in code and re-probed empirically:

- The adjudication is now per attempt: an A0 verdict is written
  create-once to `probe-attempts/attempt-N.json` and `probe.json` stays
  unwritten, so §5's archive-and-rerun path stays adjudicable. Only
  B1/B2/B3 — or `BLOCKED_PROBE` when attempt 3 is still A0 — freezes the
  create-once campaign artifact, which now records `attempt_number`,
  `max_attempts`, `terminal` and the SHA-256 chain of prior attempt
  artifacts.
- A call before any adjudicable attempt exists refuses
  (`Rate3StudyError`) with nothing written — I re-ran my round-3
  reproduction: the premature call that used to permanently brick the
  campaign now refuses, and neither `probe.json` nor an attempt artifact
  appears (closes round-3 note 3).
- The regression I asked for exists and passes:
  `test_an_a0_attempt_then_an_in_place_rerun_reaches_b2` drives A0 →
  archive → rerun → B2 → formal slot 1 authorises. Companions cover the
  premature refusal, A0-does-not-freeze idempotency, and
  `BLOCKED_PROBE` firing exactly at attempt 3 with the formal gate then
  refusing.
- Interlocks verified: an admissible probe run cannot be archived as
  failed (no dodging an unwanted B1 by discarding the run), and a
  terminal `probe.json` blocks any later failure receipt.

### 2. Finding 2 (unarchivable calibration failures) — closed

- The receipt payload is now per slot kind: scouting report; for
  calibration the **installed session file** (required, identity-checked)
  plus preview/overlay and a copy of the referenced reference-frame pair;
  run directory + truth sidecar for probe/formal, falling back to the
  session payload when the §1.1(a) startup checks refused before the run
  directory existed.
- The dividing line is exactly BC-R3-2's: the session file is written by
  `prepare_session` only after `authorize_session` passed, so a refusal
  before it exists is still not a counted attempt — my round-3
  reproduction now refuses with precisely that message and the counter
  stays 0 — while everything past the installed identity is countable.
  Archiving also clears the stale session slot, so reruns need no
  out-of-protocol deletion (empirically re-verified via the rewritten
  tests).
- The two name-only tests are rewritten to drive the real production path
  (authorise → `prepare_session` → archive; no fabricated `runs/<slot>`
  directories anywhere), the batch counter now pauses at 4 across two
  real calibration slots with an intervening success, and new guards are
  covered: a frozen calibration cannot be re-authorised (protecting both
  the BC-R3-2 counter and the BC-DRB-4/5 pairing anchor), a frozen
  scouting table cannot be re-attempted, and receipts hash-bind the
  archived payload.
- Evidence corrections verified: the two claims round 3 flagged as
  contradicted are rewritten (payload table; review-scope item 2), and
  round-3 notes 4/5 are carried forward verbatim.

### 3. Tests rerun myself (not trusted from the report)

In the round-4 worktree at `ab8ae73`: `.venv-track` full suite
**287/287 OK** (zero skips after the same read-only archive copies as
round 3), `tests.test_rate3_study` **43/43**; `.venv-yoloe` **285/287**
with exactly the two pre-existing CSRT environment failures round 3
already attributed (`cv2 5.0.0` without `TrackerCSRT_create`; untouched
by this diff). All counts match the updated evidence table. Unity was not
re-run by me: the compiled Unity code is byte-identical to reviewed
`dea5111`, so round 3's Edit **162/162** / Play **3/3** remain valid for
`ab8ae73`; the implementer additionally re-ran both in place.

### 4. Notes (none blocking)

1. If the third invalid probe attempt is archived **before** `probe` is
   invoked, the terminal `BLOCKED_PROBE` artifact is never minted: the
   run directory is gone, so `build_probe` refuses, and the blocked state
   is enforced only by the per-slot cap plus the missing `probe.json`
   (formal slots still refuse). Fail-closed in every ordering, so
   note-only: the §5 exhaustion disposition is guaranteed as an artifact
   only when adjudication precedes archival of attempt 3. Worth one
   operator-guide sentence or a small backfill in a later batch.
2. Round-3 notes 4 (metrics release-identity binding) and 5 (the
   evaluator truth stream still awaits a live Play session) remain live
   and correctly disclosed; note 5 lands with the batch-2 Unity gate.

### 5. UNITY_NA position and sequencing

No `UNITY_NA` is claimed and none is appropriate. With this round the
batch-2 code-review gate is closed; per the accepted sequencing the
user's Unity step is re-running the Edit/Play suites in place on
`ab8ae73`, and **no scouting/calibration/probe/formal session may start**
— research execution stays gated on `P1-DETECT-001` qual-3 `PASS` with
acceptance attribution, the recorded run gates, and every accepted
protocol gate. Closure attribution returns to acceptance.

Boundary self-check: this session modified no implementation file; the
disposable worktree was removed at close; the only main-tree writes are
this review file and the status board.

## Round 3 — Batch 2 difficulty matrix, calibration, probe, decision (2026-07-31)

Candidate: `dea5111` ("Close RATE-003 batch 2 stop-point rework under
BC-B2-CQ1/CQ2")
Range reviewed: `57f2561..dea5111` (full range, all 36 changed files
attributed commit by commit)
Implementer evidence: `docs/evidence/P1-M2-RATE-003-batch2.md`
Design basis: accepted revision 3 (BC-R3-1/BC-R3-2) + Amendment DR-B
(BC-DRB-1..7, design v0.3.10) + BC-B2-CQ1/CQ2

**Verdict: REWORK_REQUIRED**

Two blocking findings, both in `tools/run_rate3_study.py` orchestration
and both empirically reproduced in the disposable worktree. Everything
else — the decision function, the difficulty audit, the four frozen
configs, the road-audit evidence chain, the C# scouting/truth-stream
changes and every test count — verified faithful to the accepted clauses;
the committed artifacts need no change. The fixes are bounded; after
rework the candidate must return to this same stop point.

### 0. Range attribution and worktree discipline

Reviewed in a disposable worktree
(`.claude/worktrees/review-P1-M2-RATE-003` at `dea5111`, removed at
close). The range contains exactly two implementation commits (`6417dc3`,
`dea5111`) touching only implementation-whitelist paths, plus ten
non-implementation commits: my own rounds 1–2 records (`b3d2164` evidence
follow-up is the implementation role's docs-only batch; `3c91b52` review),
Unity-gate transcription and 0c/Force-Quit ledger entries (`3a30340`,
`33fe919`, acceptance), the three DR-P1-M2-001 rounds (`0f84f07`,
`513f20b`, `27c1d70`), Amendment DR-B ideation (`75c8daa`) and the two
acceptance rounds (`38cc95f`, `3bea810`). I reran
`check_role_writes.py --role implementation --base 57f2561` myself: the
same six flagged paths, each verified per commit to come only from those
non-implementation batches; `6417dc3`/`dea5111` wrote none of them. This
independently confirms the acceptance stop-point audit.

### 1. Tests rerun myself (not trusted from the report)

All in the review worktree at `dea5111`:

- `.venv-track` full suite: **279/279 OK** (3 skips on the bare worktree;
  after read-only copies of the archived RATE-002 artifacts and pinned
  models, **279/279 with zero skips**, and
  `test_archived_decision_a_recomputes_identically` reproduces R1′/R2′).
- `.venv-yoloe` full suite: 277/279; the two failures are exactly
  `test_pinned_opencv_csrt_initializes_and_updates` and
  `test_cli_runs_pinned_csrt_to_a_versioned_summary`, and I confirmed that
  venv ships `cv2 5.0.0` without `TrackerCSRT_create` — environment-caused
  and pre-existing, exactly as the evidence discloses.
- Unity 6000.4.10f1 batchmode in the worktree: Edit Mode **162/162**,
  Play Mode **3/3**, `error CS` count 0 in both logs.
- Focused suites (`test_rate3_decision` 25, `test_rate3_study` 35,
  `test_rate3_difficulty_audit` 19 + new) all inside the 279.

### 2. Evidence chain reproduced value for value

- `python -m tools.build_rate3_difficulty_audit --scenario
  config/scenario.p1-scene-004-d2.json ... --output <scratch>` from the
  worktree root: exit 0, `ENVELOPE_OK`, `failures=0`; field-identical to
  the committed `P1-M2-RATE-003-d2-difficulty-audit.json`
  (`dd931be2…acb2`) except `generated_unix_s`, exactly as pinned by
  `test_committed_evidence_chain_reproduces_envelope_ok`.
- `build_scene004_geometry` rebuilds the archived D1 artifact
  byte-identically (`248ae0b3…fefe`) — B2.3's no-retro-edit clause holds.
- All four config SHA-256 match the BC-B2-CQ1 table; I re-diffed the four
  files independently: within a difficulty exactly
  {`sensor.capture_hz`, `sensor.retained_frame_count`,
  `evaluation.maximum_pending_frame_count`} differ; across difficulties
  exactly {`scenario_id`, `target.speed_mps`}; `scenario_id` never encodes
  the rate. `load_campaign` re-proves all four hashes on every startup
  (BC-B2-CQ1) and I verified the fail-closed comparison.
- Both road reports hash-match (`9dddecaa…1775`, `492d3d1f…8636`), are
  `CLEAR` with 126 samples / 782 obstacles / all-zero counts / empty
  arrays, and differ **only** in `scenario_id`; the report schema carries
  exactly the fourteen BC-DRB-3 fields plus `scenario_id`.

### 3. Clause conformance verified in code

- **§6 + B1 (`controller/rate3_decision.py`)**: rule order (blocked →
  floor → ceiling → positive → inverted → midband) literal; six-value
  closed `final_action` enum, no suffixes; `Δ(D)` median-of-three without
  interpolation; every flag definition matches (dispersion `> 2θ`, H2
  `|C_20(D2) − C_5(D1)| > 0.10` with null + reason when a cell is
  incomplete, `CGEOM_DIVERGENCE_FLAG` per BC-DRB-1 at `θ_geom = 0.05` with
  the two-level OR/null semantics); `ladder_premise_violated`,
  `dr_referral_required` (all four accepted triggers), heterogeneity and
  c_geom qualifier texts with the B1.3 template, pseudo-ceiling caveat,
  zero-effect statement rule and claim rule all present; flags provably
  never change `final_action`
  (`test_cgeom_divergence_never_changes_the_final_action`,
  `test_d1_never_changes_the_final_action_choice`). The type-7 quantile
  reproduces NumPy's `_lerp` upper-anchor branch and the direct reference
  test ran unskipped against installed NumPy.
- **§10 (`finalize_attempt`)**: all four time quantities present;
  shared-host wall duration is `max(measurement capture_monotonic_s) −
  release_monotonic_s` — the accepted definition, not the summary span;
  evaluator cutoff `≥ 150.0` and `|cutoff − simulation| ≤ 0.5`;
  right-censored LOST pinned to exactly 150.0; S1′–S3 applied at **both**
  rates with the rate-relative `≥ 0.95 ×` threshold; `INVALID_CLOCK`
  events/cadence/summary-clock checks all fail the attempt.
- **§5 probe disposition**: A0 (protocol invalid, missing endpoint, <1
  qualified pair, non-finite stats) is evaluated strictly before B1–B3;
  the B1 range [16.3, 31.9] px, B2 floor 0.15 and the single 8→6
  downshift with mandatory 0b match; BC-DRB-6's three quantities are
  recorded and the B3 path refuses `select-d2` without 0b text (tested).
- **§11 lap period**: released-span truth only, directed −→+ crossing of
  the `route[0]`/`+x` section, 1.5 m lateral tolerance, interpolated
  crossing times in release-origin simulation seconds, D1 ≥4 crossings,
  gap-overlapped intervals dropped with the 20% insufficiency rule,
  deviation flag at 5% — and `gating: False` everywhere; nothing feeds a
  gate.
- **BC-DRB-4/5 pairing anchor**: the calibration manifest SHA-256 binds
  frame bytes + metadata + operator box + overlay; `calibration_preflight`
  refuses a mismatched product before the session file, model, run
  directory or any ready/release side effect (test asserts no side
  effects); `pairing_findings` marks **both** runs of a mismatched pair
  non-admissible at decision time; launch refuses a box differing from the
  frozen product; cross-`scenario_id` calibration reuse is refused. The
  superseded `rs3-d{1|2}-calib` identities are rejected on both the C# and
  Python sides (tested both directions).
- **BC-DRB-7 / run gates**: `record_run_gates` refuses without the 0c
  ledger marker plus all three operator assertions, hashes the ledger it
  checked, and `load_run_gates` re-verifies the marker on every later
  call.
- **Execution order**: the frozen 20-slot order is enforced by
  `authorize_session` requiring every predecessor complete (scouting
  frozen, six calibrations frozen, probe disposition ∈ {B2, B3}, prior
  formal runs admissible); a failed slot blocks successors until rerun in
  place; D2 formal runs additionally require the frozen `d2_selection`
  bound to an `ENVELOPE_OK` audit.
- **Ground-truth boundary**: the truth stream is written only inside
  `CoverageEvaluator`, only for an active `p1-rate3-session/v1` in
  `Released` state; it is a stale runtime slot cleared by
  `PrepareRuntimeSlots` (both tested); no `controller/` module references
  `evaluation_truth` (grep), and the existing sidecar truth-leak audit
  passes inside the 279.
- **Scouting (`Rate3ScoutingTool`)**: forward search from each ideal
  phase with a single wrap, `phase_collision` and
  `no_qualified_candidate_for_phase` fail closed, and the full candidate
  table including disqualified candidates is published — no operator
  discretion anywhere.

### 4. Findings

1. **BLOCKING — the immutable probe artifact freezes the first A0 forever
   and kills the §5 rerun path** (`tools/run_rate3_study.py`,
   `build_probe`). `probe.json` is `create_once` at campaign level, and
   the A0 branch writes it too. Empirically reproduced in the worktree:
   (a) calling the `probe` command when the probe run is invalid — or even
   **before any probe attempt exists** ("probe status unavailable") —
   creates the immutable artifact with
   `disposition=PROBE_ATTEMPT_INVALID`; (b) every later call returns the
   stale artifact unchanged, with no supersede or archive path anywhere in
   the module (`archive_failed_attempt` clears only runtime-root slot
   files); (c) `_require_completed_predecessor` then refuses **all twelve
   formal slots permanently**. §5's accepted disposition for A0 is
   "archive, rerun in the same slot (total attempts ≤ 3)"; as implemented
   the first A0 adjudication — or one mis-timed CLI call — makes the
   rerun unadjudicable and the campaign's formal phase unreachable, with
   recovery only by out-of-protocol deletion of an artifact the design
   declares immutable. Direction is fail-closed (no bad data can result),
   but the accepted protocol path is dead. Requested action
   (implementation): make the probe adjudication per-attempt (e.g. bind
   the artifact to the attempt receipt chain, or require an admissible
   probe status before `build_probe` will write, or archive the A0
   artifact with the failed attempt) while keeping the *final* artifact
   immutable, and add a regression that an A0 attempt followed by an
   in-place rerun reaches B1–B3.
2. **BLOCKING — failed calibration attempts can produce no receipt, so
   BC-DRB-4's per-slot cap and BC-R3-2's batch counter cannot bind for
   calibration slots** (`tools/run_rate3_study.py`,
   `archive_failed_attempt`). Calibration slots are HOLD-only and never
   launch the tracker (`rate3_tracker_command` refuses), so
   `runtime/runs/<calib-slot>` never exists in production; the generic
   archive branch requires exactly that directory. Empirically reproduced:
   `archive_failed_attempt(runtime, "rs3-d1-p1-calib", …)` raises
   `FileNotFoundError` and the batch counter stays 0. Consequences: an
   invalid calibration attempt (e.g. operator rejects the overlay, wrong
   HOLD window) is uncountable — the accepted pause-at-4 guard silently
   undercounts, which is fail-open against BC-R3-2 — and the stale
   session file has no sanctioned cleaner (the archive call raises before
   clearing slots), so retries require out-of-protocol manual deletion.
   The two tests that "cover" calibration receipts
   (`test_batch_counter_pauses_at_four_across_slots`,
   `test_per_slot_attempt_cap_is_three_totals`) fabricate
   `runs/<calib-slot>` directories by hand — a state production cannot
   reach — so the test coverage asserts the claim in name only (workflow
   §4.4 "tests really cover the declared behavior"). Requested action
   (implementation): give calibration (and any slot that legitimately
   fails before a run directory exists, while staying inside BC-R3-2's
   "preflight refusals before an attempt identity don't count" rule) a
   real archivable failure path — e.g. archive the session file, preview
   and any HOLD frames as the receipt payload — and rewrite the two tests
   against the real production state.
3. Non-blocking note: `build_probe`'s A0 catch-all conflates "no probe
   attempt exists yet" with "attempt made and protocol-invalid"; the
   finding-1 fix should distinguish them so a premature CLI call is a
   refusal, not an adjudication.
4. Non-blocking note: `finalize_attempt` binds `metrics.final.json` by
   scenario identity and the 0.5 s cutoff delta, not by release identity
   fields; acceptable today because the metrics snapshot is written by
   this run's own tracker process into a create-once run directory whose
   staleness is refused at prepare time, but worth tightening whenever a
   verify-style recheck is added.
5. Non-blocking note (implementer-disclosed, endorsed): the evaluator
   truth stream is not yet proven written by a live Play session;
   Edit-Mode and Python tests cover record shape, gating and stale-slot
   handling only. This stays on the Unity-gate side of the ledger.

### 5. UNITY_NA position

No `UNITY_NA` classification is claimed for this batch, and none would be
appropriate: it changes Unity-side runtime behaviour (evaluator truth
stream, scouting tool, session identities). I concur with the declared
sequencing — after review, the user's Unity step for this batch is
re-running the Edit/Play suites in place on the reviewed candidate; no
scouting/calibration/probe/formal session may start regardless, and my
verdict returns the candidate to implementation first.

### 6. Documentation consistency

`docs/evidence/P1-M2-RATE-003-batch2.md` matches the code and my reruns on
every checked claim (commands, counts, hashes, the in-place Unity re-run,
the ProjectVersion caveat — my worktree run reproduced the same three
transient `ProjectSettings/Packages` modifications, discarded with the
worktree). Two claims are contradicted by finding 2 and must be corrected
in rework: "BC-R3-2 counts scouting/calibration receipts too" (review
scope item 2) and implementation-choice 1's implication that non-scouting
slots archive a run directory — calibration slots have none.

Boundary self-check: this session modified no implementation file; the
disposable worktree was removed at close; the only main-tree writes are
this review file and the status board.

## Round 2 — Round 1 finding 1 closure (2026-07-30)

Candidate: `57f2561` ("Cross-check CLI planned duration against frozen
RATE-003 session value")
Range reviewed: `feaf475..57f2561`
Implementer evidence: follow-up section in
`docs/evidence/P1-M2-RATE-003-clock-schema.md`

**Verdict: PASS**

Scope attribution: the range contains exactly one implementation commit
(`57f2561`: `controller/track_loop.py` +8, `tests/test_rate3_protocol.py`
+41) plus the acceptance stop-point batch (`73b14fe`) and my own Round 1
record (`7cc5f93`), both docs-only and previously attributed. No
`Assets/` or C# file changes anywhere in the range.

1. **The fix is the requested one, in the requested place.** The
   cross-check sits in `run_tracker`'s rate3 branch immediately after
   `load_rate3_session` — before `FrameRepository` construction, the init
   frame load, `create_tracker`, run-ID creation and `RunLogger` — so a
   mismatch now fails under the same §1.1(a) pre-side-effect regime as the
   session validation itself. Tolerance `1e-9` matches
   `validate_session`'s freeze tolerance, and the check applies to both
   the B1 and clock-smoke studies (any `--rate3-session`). The rate2 path
   is untouched. With equality enforced at creation, the manifest's
   top-level and `rate3` duplicate of `planned_duration_s` can no longer
   disagree, which is what Finding 1 required (the alternative — binding
   admissibility to `manifest["rate3"].planned_duration_s` — remains good
   hygiene for batch 2 but is no longer load-bearing).
2. **Empirically re-probed with Round 1's exact scenario** (valid 30.0 s
   clock-smoke session, CLI `--planned-duration-s 60.0`, in a disposable
   worktree at `57f2561`): now rejected with the new error before
   `create_tracker` is ever called and with no `runs/` directory created.
   The matching value (30.0) still passes the check and reaches
   `TrackLoop` with the consistent duration — no false rejection.
3. **The new regression is real coverage, not a mock of the claim**:
   `test_cli_planned_duration_must_match_frozen_session_value` reproduces
   the probe (60.0 vs frozen 30.0, `create_tracker` asserted uncalled, no
   run directory), and the pre-existing sibling test proves the matching
   case still proceeds.
4. **Tests rerun myself**: `.venv-track` full suite **200 passed,
   41 subtests** (archived RATE-002 regression unskipped after read-only
   copies, R1′/R2′ reproduce), `.venv-yoloe` **54/54 + 18 subtests** —
   both matching the follow-up evidence. I endorse not rerunning Unity:
   the compiled Unity code is byte-identical to reviewed `feaf475`, so
   Edit **150/150** / Play **3/3** from Round 1 remain valid for
   `57f2561`.
5. Findings 2 and 3 from Round 1 were notes requiring no change; the
   follow-up evidence records them as such. Nothing else moved.

Round 1's verdict condition is now fully discharged ahead of batch 2. The
reviewed candidate for the `rs3-clock-smoke` focused Unity gate is
`57f2561`; step-0 HEAD/status attribution before Play should reference it.

## Round 1 — Batch 1 shared-clock rate3 protocol + archived-v2 routing (2026-07-30)

Candidate: `feaf475` ("Add RATE-003 shared-clock v3 protocol with
archived-v2 routing")
Range reviewed: `f1868dd..feaf475` (full range, all 46 changed files
attributed; implementation batch is exactly the 14 files of `feaf475`)
Implementer evidence: `docs/evidence/P1-M2-RATE-003-clock-schema.md`
Design basis: proposal revision 3 (`ACCEPTED`, acceptance round 3,
BC-R3-1/BC-R3-2), design v0.3.9

**Verdict: PASS_WITH_NOTES**

No blocking finding. The single-clock contract (P1–P5, C1–C4), the
startup/runtime fail-closure layering (§1.1(a)/(b)), the clock-smoke
identity (§1.2), the v2/v3 routing with a frozen archive (§2) and the
dual-duration completion gate (§10) are implemented literally and are
covered by real tests I reran myself. Three findings, none blocking;
finding 1 must be closed no later than batch 2 (see below).

### 0. Range attribution and worktree discipline

Reviewed in a disposable worktree
(`.claude/worktrees/review-P1-M2-RATE-003`, removed at close). The full
`git diff --stat f1868dd..feaf475` spans 46 files; I verified commit by
commit that the 32 non-implementation paths come only from COORD-002 and
its follow-ups (`02d90b5`, `312e08b`, `a7c4fbc`, `0992c5a`), the
ideation/acceptance RATE-003 submissions (`14ce0df`, `ba06ef2`), the
qual-3/round-8 handoffs (`1cfa14e`, `3fc1d46`, `90a43f4`, `729d6fa`) and
the chore rotation (`9178261`) — none of those commits touches
`controller/`, `Assets/**/Scripts/`, `tools/run_*` or the new tests. This
independently confirms acceptance's stop-point write audit. The
implementation commit `feaf475` touches exactly the declared scope plus
its evidence file.

### 1. Tests rerun myself (not trusted from the report)

All on this machine, inside the review worktree at `feaf475`:

- `.venv-track` pytest full suite: **199 passed, 41 subtests passed**.
  Note the archived-artifact regression and the two pinned-NanoTrack tests
  skip on a bare worktree (gitignored resources); after copying the real
  `runtime/rate-study/P1-M2-RATE-002-B2`, the three `rs2-r20-follow-*` run
  directories and `runtime/models` from the main tree (read-only copies),
  the suite runs **unskipped** and
  `test_archived_decision_a_recomputes_identically` reproduces
  R1′ = 0.2496313750743866 and R2′ = 0.8475073313782991 value-for-value.
- `.venv-yoloe` reanchor/scouting subset: **54 passed, 18 subtests**.
- Unity 6000.4.10f1 batchmode Edit Mode, filter `TetheredTracking.Tests`:
  **150/150 passed**, of which exactly **35** are the new
  `RateStudyRate3EditModeTests` cases (`runtime/test-results/
  review-editmode.xml` in the worktree, discarded with it).
- Unity Play Mode: **3/3 passed**.

All counts match the implementer evidence.

### 2. Clock contract verified in code, not from the diff summary

- **P1** (`SensorFrameWriter.cs:183-188`): the v2 branch now requires
  `IsActive && !UsesSharedHostClock`; a rate3 session therefore takes the
  ordinary v3 path — `FrameMetadataV3` + `HostMonotonicSeconds()` — while
  a v2 session's expression is byte-for-byte the old one. The Edit Mode
  test `Rate2Session_ReleaseFlowAndAckBytesRemainUnchanged` pins v2 ack
  bytes; `rate2_protocol.py` is untouched in the whole range.
- **P3** (`RateStudyExperimentController.cs:149-154, 322-360`): for rate3
  the release ack monotonic source is `HostMonotonicSeconds()` sampled
  once in the same `Update` that validates and performs the RELEASED
  transition; the same sample is both the C4 `now` and the ack's
  `release_monotonic_s`. `ReleaseAckDocumentV3` carries
  `release_clock_id = system-stopwatch/v1`.
- **P4** (`rate3_protocol.py:484-501`): every published ready carries
  `publisher_clock_id` and `heartbeat_interval_s = 1.0`.
- **P5** (`reanchor_runtime.py:38-51,444-450` and
  `Rate3TrackerLifecycle.__init__`): non-default monotonic injection must
  explicitly declare `system-stopwatch/v1` or construction raises;
  the declared ID is written into `manifest_identity()`. The pre-existing
  unconditional per-frame `validate_system_monotonic_frame` in
  `after_frame` supplies binding (ii).
- **C1** (`rate3_protocol.py:555-578`): `frame_phase` validates both the
  frame's `capture_monotonic_clock_id` and the ack's `release_clock_id`
  before the capture-vs-release comparison; mismatch raises
  `INVALID_CLOCK_IDENTITY`.
- **C2** (`run_log.py:315-322,418-489`): `build_summary` rejects any
  measurement record whose clock differs from the provenance's
  `release_clock_id`; `finalize_run` routes `manifest["rate3"]` to the
  rate3 provenance validator and rejects multiple release protocols in one
  manifest. For rate2 the parameter stays `None`, so v2 summaries are
  unchanged.
- **C3**: unchanged per-frame validation in `after_frame`; under rate3 a
  failure now terminates the run (below) instead of only raising.
- **C4** (`RateStudyExperimentController.ValidReadyRate3Error`): exact
  predicate as accepted — v3 ready schema, `publisher_clock_id` pinned,
  finite non-negative timestamp, `0 < heartbeat_interval_s ≤ 1.0`, and
  `0 ≤ now − publisher_monotonic_s ≤ 2 × heartbeat_interval_s` with
  same-Update `now`; future and stale both rejected
  (`FutureReady_RejectedAsClockIdentityAndHolds`,
  `StaleReady_BeyondTwoHeartbeatsRejectedAsClockIdentity`), state stays
  HOLD. v3 release commands without the correct `release_clock_id` are
  rejected before the transition (`invalid_release_clock_id`).

### 3. Ordering and fail-closure (§1.1(a)/(b))

Startup: `load_rate3_session` runs before `FrameRepository` construction,
`repository.load(init_frame)` (which for the v3 schema validates clock
identity via `validate_system_monotonic_frame` on **every** load, not just
init) runs before `create_tracker`, and `RunLogger`/run-directory creation
comes after all of it (`track_loop.py:895-1016`). The test
`test_session_validation_precedes_run_directory_creation` mocks
`create_tracker` and asserts it is never called and no `runs/` directory
appears for an invalid session; I additionally verified with a probe that
a *valid* session reaches `TrackLoop` construction only after all checks.

Runtime: three layers wrap the rate3 path — frame load, `_protocol_fields`
(C1) and `reanchor.after_frame` (C3) — each terminating the run with event
`INVALID_CLOCK` before the bad frame's observation/control/re-anchor/record
side effects (`track_loop.py:392-401,428-439,457-470`), and `terminal`
drives exit code 2. `Rate2ProtocolError` subclasses `ValueError`, so the
handlers do catch clock-identity errors — I checked this explicitly.
`test_bad_clock_frame_terminates_run_without_side_effects` proves the bad
frame publishes nothing, the heartbeat stays at the last good frame, and
previously processed frames keep their records. The rate2 path keeps the
old propagation behavior (`_invalid_clock_fail_closed` is False for it).

### 4. Routing, mutual exclusion, and the §795 guard

- The v2 guard at `track_loop.py` (`--rate2-session` + `--reanchor-config`
  → hard error) is intact and tested
  (`test_rate2_reanchor_guard_is_unchanged`). The rate3 combination is
  genuinely lifted, and additionally guarded by an explicit
  `reanchor.monotonic_clock_id == session["capture_monotonic_clock_id"]`
  check (`track_loop.py:977-984`), with a defensive test injecting a
  wrong-clock reanchor.
- `--rate2-session`/`--rate3-session` are mutually exclusive; the
  qualification barrier rejects both.
- Cross-feed fails closed in both directions at every layer I checked:
  session/ready/release-bundle schema validators
  (`Rate3VersionRoutingTests`, and the Unity equivalents), and
  `FrameRepository` rejects the other generation's frames.
- Clock-smoke/research exclusion: `expected_scenario` pins
  `rs3-clock-smoke` ⟷ `P1-M2-RATE-003-CLOCKSMOKE` and rejects any
  crossing with the `P1-M2-RATE-003-B1` ID space
  (`rate3_protocol.py:76-89`); `prepare_session` additionally fail-closes
  on an installed research session, any `rs3-*` research run directory, or
  stale runtime slots. `verify_run` computes no `C_track`/`C_geom` and the
  smoke archives under `runtime/rate-study/P1-M2-RATE-003-CLOCKSMOKE/`.
- BC-R3-1 in schema: `validate_session` freezes `planned_duration_s` to
  exactly 150.0 for B1 and 30.0 for the non-measurement smoke (both sides,
  C# tolerance 1e-6); the completion gate requires **both** release-origin
  simulation duration and shared-host monotonic wall duration to reach the
  planned value (`requires_wall_completion`, `track_loop.py:274-288`).
- Truth boundary: no truth, scenario-config or evaluator read appears
  anywhere in the new controller/tool code (grep-audited); the tracker
  input path is unchanged.

### 5. Findings (none blocking)

1. **CLI/session `planned_duration_s` mismatch is not cross-checked**
   (must be closed no later than batch 2). `run_tracker` builds the
   completion gate from `args.planned_duration_s` and never compares it to
   the session's frozen `planned_duration_s`. Empirically reproduced in
   the worktree: a valid 30.0 s clock-smoke session launched with
   `--planned-duration-s 60.0` passes every startup check, creates the
   run directory, and hands `TrackLoop` the CLI value 60.0; the manifest
   then carries two contradictory values (top-level 60.0 from args,
   `rate3.planned_duration_s` 30.0 from the session) inside the same hash
   chain, and neither `finalize_run` nor `verify_run` compares them. Both
   provided launchers pass the constant, and no research launcher exists
   yet, so this is unreachable through reviewed tooling today — hence
   non-blocking — but BC-R3-1's freeze is currently only as strong as the
   launcher. Requested action for the implementation role (batch 2 at the
   latest): assert `args.planned_duration_s == session["planned_duration_s"]`
   at startup (or in `Rate3TrackerLifecycle`), and/or bind the §10
   admissibility evaluation to `manifest["rate3"].planned_duration_s`
   rather than the top-level value.
2. **Python-side ready freshness window is fixed at 2.0 s**
   (`HEARTBEAT_MAX_AGE_S`) while Unity's C4 uses
   `2 × heartbeat_interval_s`. They coincide only because the interval is
   frozen at 1.0 (Python also rejects intervals > 1.0, so its window can
   only be ≥ Unity's). Unity is the authoritative gate before RELEASED
   and is strictly the tighter check, so there is no unsafe direction;
   cosmetic divergence only.
3. **A wrong `monotonic_clock_id` argument is silently ignored when the
   default `time.monotonic` is used** in both `Rate3TrackerLifecycle` and
   `ReanchorRuntime` (the declared ID is forced to `system-stopwatch/v1`).
   Harmless — the default source *is* the declared clock — but the
   asymmetry is worth knowing when reading the constructor contract.
   Relatedly, a mid-run invalid release ack surfaces as an uncaught
   `Rate2ProtocolError` from `poll_release_ack` (hard exit, no graceful
   `INVALID_CLOCK` summary); this mirrors the pre-existing rate2 pattern
   and is fail-closed, so no change is requested in this batch.

### 6. UNITY_NA position

No `UNITY_NA` classification is claimed for this batch, and none would be
appropriate: this is a runtime protocol change whose focused Unity gate is
the `rs3-clock-smoke` session. I endorse the declared sequencing — after
this review, only `rs3-clock-smoke` may run (no research-data session),
and research sessions additionally remain blocked on `P1-DETECT-001`
qual-3 `PASS` plus acceptance attribution and on BC-R3-2's global
invalid-attempt guard.

### 7. Documentation consistency

`docs/evidence/P1-M2-RATE-003-clock-schema.md` matches the code: every
cited line range checked (P1/P3/P4/P5, C1–C4, §1.1, §1.2, §2, completion
gate), all test counts reproduced, and the two acceptance-owned doc edits
it flags were committed by the acceptance batch (`73b14fe`), not by the
implementation commit. The 6000.4.1f1-vs-6000.4.10f1 note reflects a
pre-existing condition and matches prior batches' practice.
