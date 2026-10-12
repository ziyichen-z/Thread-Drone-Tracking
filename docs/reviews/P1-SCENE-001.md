# P1-SCENE-001 — independent review

Reviewer: Claude Sonnet (independent review role)

## Round 1 — 2026-07-27

Candidate: `70d5101` over `4d10a91..70d5101` (HEAD at review time: `d4160fd`,
a docs-only commit on top; verified via `git show --stat d4160fd`).

Verdict: **PASS**

### Scope covered

Reread the accepted proposal
(`docs/proposals/P1-SCENE-001-scene-vehicle-deconfliction.md`, including its
six binding clarifications) and the real diff, not the implementer's summary.
Read in full: `ScenarioConfig.cs`, `SceneVehicleAdjustments.cs`,
`TetheredScenarioBootstrap.cs`, `RateStudyScoutingTool.cs`,
`RateStudyProtocol.cs`, `SceneCorridorEvidenceGenerator.cs`,
`RateStudyDistractor.cs`, `SceneAdjustmentsEditModeTests.cs`, the three
checked-in scenario configs, `controller/rate2_protocol.py`, and the three
JSON evidence artifacts.

### What was independently verified

1. **Config strictness (binding clarification 1–2).**
   `ScenarioConfig.NormalizeSceneAdjustments()` only runs when
   `scene_adjustments` is present; when present it throws on null
   `vehicle_relocations`/`route_corridor`, negative
   `expected_distractor_count`, non-positive/non-finite `target_half_width_m`,
   negative/non-finite `clearance_margin_m`, missing `original_xz_m`/
   `new_position_m`, non-positive `match_tolerance_m`, non-finite
   `new_position_m`, and duplicate `prefab_name`+`original_xz` keys — with no
   fallback path, matching "不使用普通场景配置的容错回退." When
   `scene_adjustments` is absent, `Normalize()` never touches it and
   `MissingAdjustmentPreservesLegacyConfigBehavior` (present, Passed in the
   cited XML) confirms the field stays `null`, i.e. byte-identical legacy
   behavior (acceptance criterion 5).
2. **Unique matching / fail-closed selection.** `SceneVehicleAdjustmentApplier
   .Apply` matches by `CanonicalPrefabName` (strips only a trailing Unity
   numeric ` (N)` suffix — verified the digit-only guard rejects
   `"Vehicle_Taxi (copy)"`) plus `original_xz_m` within tolerance, requires
   exactly one match, and throws on zero or multiple. A second guard
   (`selected.Add(match)`) also rejects two different relocation entries
   resolving to the same physical transform. Covered by
   `ApplyFailsClosedForZeroOrMultipleMatches` and
   `ApplyUsesCanonicalPrefabNameAndUniqueOriginalPosition` (both Passed).
3. **Bootstrap ordering (binding clarification 2).**
   `TetheredScenarioBootstrap.Awake()` calls `CreateTarget()` →
   `ApplySceneAdjustments()` → `CreateEvaluationOcclusionGeometry()` in that
   order (`TetheredScenarioBootstrap.cs:34-38`). `ApplySceneAdjustments()`
   relocates vehicles first, then runs `RouteCorridorAuditor.Audit` on the
   same live `Transform` references (already moved), and throws
   `InvalidOperationException` fail-closed if `violation_count != 0` — there
   is no try/catch around `Awake()`, so this genuinely aborts scenario
   construction rather than logging and continuing.
4. **Renderer-bound geometry / proxy consistency (acceptance criterion 4).**
   `EvaluationOcclusionGeometry.Build()` scans `FindObjectsByType<MeshRenderer>`
   over the whole scene and parents each proxy `MeshCollider` to
   `renderer.transform` with local identity offset, so proxies track the
   relocated vehicles' new world position by construction. Confirmed via
   `OcclusionProxyIsBuiltUnderTheRelocatedVehicle` (proxy position equals the
   post-relocation vehicle position) and the real-scene evidence
   (`every_relocated_vehicle_has_proxy: true`, 916/916 proxies, 0 failures).
5. **Truth/evaluator boundary.** `grep -rn` for
   `route_corridor_audit|route_corridor_dynamic|RouteCorridorAuditor|
   RouteCorridorDynamicMonitor|RateStudyDistractor` across `*.cs`/`*.py`
   shows these symbols are only used inside `SceneVehicleAdjustments.cs`,
   `TetheredScenarioBootstrap.cs`, `RateStudyScoutingTool.cs`, and the editor
   evidence generator — never referenced from `CoverageEvaluator`, the
   sensor/frame writer, tracker code, or the Python controller. The dynamic
   monitor only writes its own diagnostic JSON.
6. **Scouting cardinality gate (binding clarification 3).**
   `RateStudyScoutingTool.DistractorCountValidationError` returns null when
   `scene_adjustments` is absent (`expected == -1` sentinel), and otherwise
   requires an exact match, writing `status="INVALID_SCOUTING"` with
   `validation_error="active_distractor_count_mismatch"` and both the
   expected and actual counts into `scouting_qualification.json` before
   returning `false` — it does not silently pass. Covered by
   `DistractorCardinalityGateIsExactAndOptionalOnlyWhenAbsent` (Passed), and
   `NormalizeSceneAdjustments` additionally forces `expected_distractor_count
   >= 0` whenever the block is present, closing the "leave it negative to
   disable the gate" loophole.
7. **B1 → B2 identity boundary (binding clarification 5).**
   `RateStudyProtocol.cs` and `controller/rate2_protocol.py` both hardcode
   `"P1-M2-RATE-002-B2"`; a repo-wide `grep -rln "P1-M2-RATE-002-B1"` over
   `*.cs`/`*.py` (excluding stray `.claude/worktrees/` copies from unrelated
   background sessions) returns nothing — no code path can still validate a
   B1-identified session, and both EditMode/PlayMode test session builders
   were updated to `B2` alongside the production code.
8. **Real scene audit numbers.** Hand-recomputed the taxi case from
   `docs/evidence/P1-SCENE-001-corridor-before.json`/`-after.json`: original
   centerline distance `0.5936 m` against the closed-loop segment
   `(132,117)→(180,117)`; required clearance `target_half_width(1.0) +
   vehicle_half_extent(≈1.479) + margin(0.5) = 2.979 m`, so the reported
   `INVALID_ROUTE_CORRIDOR` violation is correct. After relocation to
   `z=112.5`, lateral clearance is `4.5 m > 2.979 m`, consistent with the
   reported `CLEAR` status. The container truck and police car were both
   relocated far outside the route's `x` range entirely, so their `CLEAR`
   result is not sensitive to the corridor-distance formula at all. Violation
   count (3→0) and audited-vehicle count (104, unchanged before/after) match
   the implementation evidence doc.
9. **Reran the Python suite myself** (not trusted from the report):
   `.venv-track/bin/python -m unittest discover -s tests -v` →
   **72/72 passed**, matching the cited number exactly (HEAD `d4160fd`, a
   docs-only commit past the candidate — confirmed via `git show --stat`, so
   this is a legitimate rerun of the same code).
10. **Unity artifacts.** Read the checked-in NUnit XML result files directly:
    `runtime/test-results/p1-scene-001-editmode.xml` reports
    `total=53 passed=53 failed=0`, and by name/result I confirmed all 8 new
    `SceneAdjustmentConfigTests`/`SceneVehicleAdjustmentTests` cases are
    present with `result="Passed"`.
    `p1-scene-001-playmode.xml` reports `total=2 passed=2 failed=0`. These
    match the implementation evidence doc's cited counts.
11. **Doc/state consistency.** `docs/unity-test-log.md` and
    `docs/implementation-status.md` correctly leave `UT-P1-SCENE-001-001` and
    the Sonnet-review checklist item unchecked/`PENDING` — no runtime claim
    was marked `DONE` prematurely. `runtime/` has no active RATE session,
    campaign, or `route_corridor_*` artifacts left over (checked directly),
    consistent with the stated clean pre-review state.

### Non-blocking notes

1. **Unity batch-mode rerun could not be independently executed in this
   sandbox.** I attempted `Unity ... -runTests -testPlatform EditMode` with
   the pinned `6000.4.1f1` editor myself and hit the exact same failure the
   implementation evidence describes: `[Licensing::Client] Error:
   HandshakeResponse ... ResponseCode: 505, Unsupported protocol version
   '1.18.1'`. This independently corroborates that the licensing limitation
   is a genuine environment constraint in this sandbox, not a fabricated
   excuse — but it also means my Unity verification is limited to reading
   the checked-in XML/log artifacts (note 10 above) rather than a fresh
   from-scratch execution. This is the same limitation prior review rounds
   have hit and does not block this candidate; it is an argument for the
   user's own `UT-P1-SCENE-001-001` Unity run remaining the authoritative
   gate, which it already is.
2. **Visual/geometric plausibility of the new positions (container truck at
   `x=168.25,z=110.5`; police car at `x=190.0,z=89.07`) is unverifiable from
   source alone** — this is explicitly deferred to the user's Unity visual
   check in `UT-P1-SCENE-001-001` case 1, as the proposal's own open question
   1 anticipates. Correctly scoped as out of this review's reach.

### Conclusion

The implementation matches the accepted proposal and all six binding
clarifications; fail-closed paths are real (no swallowed exceptions,
no silent fallbacks) and are backed by direct unit tests that are present
and passing in the cited artifacts; the truth/evaluator boundary is intact;
and the B1→B2 identity change is complete with no stale references. No
rework is required. The candidate may proceed to
`UT-P1-SCENE-001-001` (user Unity validation); only after that passes may
Codex prepare the first B2 campaign smoke, per the existing handoff.
