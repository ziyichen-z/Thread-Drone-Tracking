# P1-SCENE-003 implementation evidence

Date: 2026-07-28  
Implementer: Codex  
Accepted design: `docs/proposals/P1-SCENE-003-anchor-relocation.md`

## Outcome

The first ordered implementation gate returns
**`BLOCKED_ANCHOR_PLACEMENT`**. The accepted fallback lattice contains 1,257
points (0.5 m spacing, radius at most 10 m, ordered by distance then x then
z). In the real checked-in city scene, every point lies strictly inside the
allowlisted `Natures_Grass Tile`, whose transformed support elevation is about
`0.0000013 m`. The accepted candidate anchor elevation is `0.2 m` with
`±0.05 m` support tolerance, so all 1,257 candidates deterministically fail
with `SUPPORT_HEIGHT_MISMATCH`.

This is disposition-table row 1, not an implementation defect or a free
fallback choice. The support gate precedes obstacle clearance, therefore the
formal artifact correctly reports zero clearance evaluations and does not
pretend that any candidate reached the second gate. No new scenario, geometry
profile, scout-2 session, capture, qualification run or RATE-003 artifact was
created.

## Implemented gate

- `config/p1-scene-003-anchor-placement.json` freezes the accepted center,
  hover offset, support allowlist/tolerance, Minkowski radii/margin and
  lattice. SHA-256:
  `edb9d646dff6b04876b27a2b8e2631ed08788ac22768ec89f9a78ab1bd7581b1`.
- `P1Scene003AnchorAudit.cs` loads and validates that contract, enumerates the
  complete deterministic lattice, applies a strict-interior support gate,
  rejects zero/conflicting-height support, and implements the second-stage
  exact yaw/TRS-transformed footprint intersection against the effective
  anchor cylinder, tether corridor and hover sphere. Tangency and unsupported
  TRS fail closed.
- `P1Scene003AnchorEvidenceGenerator.cs` loads the actual city scene, applies
  the accepted SCENE-002 adjustments, derives the active root set, runs the
  audit and refuses success unless the checked-in scene reproduces the
  pre-registered blocked disposition.
- The full machine-readable artifact is
  `docs/evidence/P1-SCENE-003-anchor-audit.json`: 641,616 bytes, SHA-256
  `dcfb040d2965611935d4e31ff4c3f1c8a0af575ef4b80ad673fbb135c291ca06`.
  It binds source scenario
  `68170d801b559c7dea238cf57873f2b2eab6a47bbbb9904e7fa8b5498723c61c`,
  road data
  `111e0759d4b52821d08ce4ddd1aae3fc8cc8d24e12e6fa62513403c00b401894`
  and the contract hash above, and records every candidate and rejection.

The scene also contains `Building_Stadium` centered near `(150, 87.4)`.
Its frozen canonical full footprint, transformed by the real 90° scene yaw,
covers the entire 10 m fallback disk. This is a secondary design warning:
merely relaxing the support-height rule would still not establish a legal
candidate. It is not used to override the prescribed support-first decision.

## Automated verification

Unity was closed before execution. Installed `6000.4.1f1` could not complete
headless startup because its local Licensing Client reported an unsupported
protocol version. The already-installed `6000.4.10f1` was therefore used for
the checks below; its automatic package/project-version edits were reverted
byte-for-byte afterward, leaving the repository pinned to `6000.4.1f1`.

| Check | Result |
|---|---|
| Focused Edit Mode `P1Scene003AnchorAuditTests` | **6/6 passed** |
| Full Edit Mode `TetheredTracking.Tests` | **92/92 passed** |
| Python merged YOLOE + contrib environment | **109/109 passed** |
| `uv pip check` for `.venv-yoloe` | **42/42 compatible** |
| `git diff --check` | passed |

The focused suite directly covers the real scene, exact-center success under
a valid synthetic support surface, deterministic fallback, strict boundary
rejection, support height/conflict paths, tangent obstacle rejection and
unsupported obstacle TRS.

## Blocker and required authority

Proceeding requires a design change to at least one accepted geometric
constraint: select a different anchor region, enlarge/redefine the fallback
set, alter the support-height interpretation, or change/remove the stadium.
Each changes the accepted safety geometry and resulting scouting difficulty;
Codex cannot choose one during implementation. Fable/user direction and a
revised accepted proposal are required before scenario/profile/scout-2 work
can resume.
