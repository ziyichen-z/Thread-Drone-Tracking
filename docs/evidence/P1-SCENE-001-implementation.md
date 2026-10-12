# P1-SCENE-001 implementation evidence

Date: 2026-07-27

Implementer: Codex

Gate: stable candidate `70d5101` over `4d10a91..70d5101`; independent review
and user Unity validation remain pending

## Implemented behavior

- `scene_adjustments` is an optional `tethered-scenario/v1` block. When absent,
  legacy config behavior is unchanged. When present, malformed/missing/
  non-finite adjustment fields fail closed instead of falling back.
- Scene vehicle selection uses root objects only, strips only Unity's numeric
  ` (N)` suffix, then requires exactly one match inside the configured original
  XZ tolerance. Zero matches, multiple matches and duplicate selection throw.
- The taxi, container truck and police car are moved deterministically before
  occlusion proxies are built. The taxi receives the runtime-only
  `RateStudyDistractor` marker.
- The bootstrap audits all active scene vehicle renderer bounds against the
  closed route corridor after relocation and atomically writes
  `runtime/route_corridor_audit.json`. Any remaining violation aborts scenario
  construction.
- An explicitly enabled validation-only monitor writes target/vehicle XZ
  renderer intersection counts to `runtime/route_corridor_dynamic.json`. It is
  disabled in all checked-in ordinary and RATE configs and does not feed the
  evaluator, sensor, tracker or control path.
- RATE-002 scouting now requires actual active distractor cardinality to equal
  the scenario-level expected count. Mismatch writes `INVALID_SCOUTING` with
  `active_distractor_count_mismatch`.
- The successor campaign identity is `P1-M2-RATE-002-B2` in both C# and Python.
  The archived B1 session, transaction, campaign, config and run IDs cannot
  validate against or be reused by the new code.

## Real city-scene audit

The editor evidence generator opens the vendor demo scene without saving it,
loads `config/scenario.default.json`, audits the original scene, applies the
runtime adjustments, audits again, and builds the real evaluator proxy set.

| Check | Result |
|---|---|
| Active scene vehicles audited | 104 |
| Original route-corridor violations | 3 exactly |
| Original objects | `Vehicle_Taxi (2)`, `Vehicle_Container_color01`, `Vehicle_Police Car (5)` |
| Original centerline distances | `0.59359 m`, `0.150986 m`, `0.854630 m` |
| Post-adjustment violations | 0 (`CLEAR`) |
| Occlusion candidates/proxies | 916/916 |
| Existing colliders / proxy failures | 0 / 0 |
| Every relocated vehicle has a proxy | true |

Machine-readable artifacts:

- `docs/evidence/P1-SCENE-001-corridor-before.json`
- `docs/evidence/P1-SCENE-001-corridor-after.json`
- `docs/evidence/P1-SCENE-001-corridor-summary.json`

The vendor `.unity` scene and vehicle prefabs are unchanged.

## Automated verification

| Command/check | Result |
|---|---|
| Unity Edit Mode full suite | 53/53 passed, including all 8 new config/matching/audit/proxy/cardinality checks |
| Unity Play Mode full suite | 2/2 passed |
| `.venv-track/bin/python -m unittest discover -s tests -v` | 72/72 passed |
| `python3 -m py_compile controller/rate2_protocol.py tools/run_rate2_study.py` | passed |
| `git diff --check` | passed |

Unity batch evidence was produced with installed `6000.4.10f1`; the project
version and package files were restored byte-for-byte to their required
`6000.4.1f1` state afterward. A direct `6000.4.1f1` batch attempt did not reach
script execution because its local licensing client repeatedly rejected
protocol `1.18.1` with handshake response 505. This is retained in
`runtime/test-results/p1-scene-001-evidence.log` as an environment/tooling
limitation, not counted as a passing test.

Primary local test artifacts:

- `runtime/test-results/p1-scene-001-editmode.xml`
- `runtime/test-results/p1-scene-001-playmode.xml`
- `runtime/test-results/p1-scene-001-evidence-6000.4.10f1.log`

## Remaining independent and Unity gates

Sonnet must review the accepted proposal, config strictness, unique matching,
renderer-bound geometry, bootstrap order, truth boundary, scouting mismatch
path, B1→B2 identity boundary, tests and evidence generator.

After Sonnet passes, user case `UT-P1-SCENE-001-001` must use Unity
`6000.4.1f1` to:

1. visually confirm the taxi, container truck and police car are on plausible
   road/parking surfaces and do not overlap buildings, trees or props;
2. enable only the dynamic validation flag and run at least one full target
   loop (`>=105 s`), requiring zero target/vehicle intersection frames;
3. confirm the runtime static report is `CLEAR`, the active distractor count is
   exactly one, and occlusion proxy counts remain complete;
4. record a follow loop with `C_geom` significantly below 100%, proving
   building/tree occlusion difficulty was retained.

Only after that scene case and the independent review pass may Codex prepare
the first B2 campaign smoke. That smoke inherits the stopped
`UT-P1-M2-RATE-002-002` metrics-cutoff integration objective; the formal
qualification pilot remains blocked until it passes.
