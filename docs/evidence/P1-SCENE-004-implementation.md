# P1-SCENE-004 implementation evidence

Work ID: `P1-SCENE-004`
Design: `docs/proposals/P1-SCENE-004-benign-coverage-circuit.md`
(revision 2, `ACCEPTED_WITH_BINDING_CLARIFICATIONS`, Codex round 2, 2026-07-29)
Formal design: `docs/phase1-single-drone-design.md` v0.3.7

This is implementer evidence. `IMPLEMENTED` is not `DONE`: nothing here has
been independently reviewed by Sonnet or validated in Unity by the user.

## Gate 0 — read-only near-field detectability probe (2026-07-29)

**Result: `PROCEED_TO_IMPLEMENTATION`. Recall 0.897059 (183/204).**

Gate 0 is the accepted first step after acceptance; its pre-registered read
could have terminated the work item before any scenario edit. It did not.

### What was run

`tools/run_scene004_gate0_probe.py` replays the pinned YOLOE proposer and the
pinned DINOv2 embedder over the already-frozen `p1-detect-001-scout-1`
capture, restricted to the near-field band (slant range in [25.0, 31.0] m) —
the same geometry band SCENE-004 proposes. The DETECT-001 §8 gate had only
ever measured the remote tail (≥65 m), where recall was 0/45 with
`proposal_count` 0 on all 27 real remote samples.

The probe's band, thresholds, headline denominator and decision bands are
frozen as module constants and were written before the first execution; they
were not adjusted afterwards.

### Read-only discipline (all verified, not asserted)

| Guard | Evidence |
|---|---|
| Sandbox byte-copy only | 2,253 files copied from `runtime/frames` and `runtime/p1-detect-scouting`; per-file SHA-256 of source and copy compared and equal; capture manifest SHA-256 `c8301d7caaee8234707948720fb6eaf0f05cbc2be3711bd7a439961fb97f60cc` |
| Live runtime refused | `--capture-root runtime` raises `Gate 0 refuses to read the live runtime tree; pass a sandbox copy`; verified by direct invocation |
| Real capture unchanged | The same 2,253 files re-hashed after the run: byte-identical to the pre-run manifest |
| No frozen artifact written | The only output is `docs/evidence/P1-SCENE-004-gate0-probe.json`; no create-once identity claimed or reused; `scouting-result*.json`, supersession and completion documents untouched |
| Pinned model config untouched (BC5) | `config/detector-reanchor.models.json` read and hash-recorded (`593734d6…`), `minimum_crop_side_px` still 2 |

Environment matches the pins exactly: torch 2.13.0, torchvision 0.28.0,
ultralytics 8.4.104, OpenCV 5.0.0 in `.venv-yoloe`. Wall clock 22.3 s.

### Detector result

| Quantity | Value |
|---|---|
| Recall (headline, all near-field paired visible frames) | **0.897059 (183/204)** |
| Recall (2 Hz tick subset, §8 sampling discipline) | 0.875 (56/64) |
| Unpaired frames inside the band | 0 |
| Misses with zero class-level proposals | 21 of 21 |

The two denominators agree to within 2.2 pp, so the headline is not an
artifact of the sampling choice.

**Descriptive finding worth carrying into scout-3.** The 21 misses are not
small-target failures: their median minimum box side is 66.7 px, *larger*
than the 42.9 px median over all probe samples, and their median slant range
(27.09 m) is indistinguishable from the hits' (26.50 m). They cluster in time
at t ≈ 3.0–3.8 s, 101.9–104.7 s and 110.6–111.5 s — the segments where the
vehicle presents an aspect different from the single-frame visual prompt
(reference frame 47 at 7.112 s, on the east-bound leg). SCENE-004's circuit
has two opposite headings plus two end turns, so it presents *more* aspect
diversity than this probe band. The ≥0.7 gating line has 20 pp of headroom
against the probe, but aspect change — not range — is the mechanism to watch
in the scout-3 report.

### Embedding result (H2), descriptive, no auto-GO

Reference frame 47 and its immediate neighbours are excluded from these
statistics (BC4a): 3 frames excluded, so the reference crop never
self-compares at ~1.0.

| Quantity | Gate 0 near-field | scout-1 remote (frozen) |
|---|---|---|
| Target cosine samples | 201 | 27 |
| Target cosine median | **0.7687** | 0.3984 |
| Target cosine max | 0.9395 | 0.5272 |
| Target ≥ 0.5 passes | 161 / 201 | 1 / 27 |
| Distractor cosine samples | **157** | 0 (all 27 `CROP_INVALID`) |
| Distractor cosine median | 0.6000 | — |
| Separation opportunities | 157 | 0 |
| Margin passes (target ≥0.5 and target − max distractor ≥0.1) | 142 / 157 | 0 |

H2 is supported: the same-scale comparison lifts the target cosine median
from 0.398 to 0.769, which is consistent with the round 1 finding that
scout-1's low cosines were a cross-scale artifact (near-field ~40×69 px
anchor crop versus ~21–31 px remote samples) rather than an appearance-model
verdict. Honest caveats: 40 of 201 target cosines still sit below the 0.5
threshold, and the single distractor's own median is 0.600 — the absolute
separation is modest and rests on the margin test, not on distinct score
ranges. The feasibility decision stays `REQUIRES_REVIEW`; Gate 0 grants no GO.

### Box-size cross-check against BC1

Measured over the same 204 samples, in the proposed slant band:

| Quantity | min | p05 | p25 | median | max |
|---|---|---|---|---|---|
| Box height (px) | 43.63 | 57.97 | 64.48 | 69.58 | 86.47 |
| Box width (px) | 29.58 | 30.50 | 35.35 | 42.91 | 87.02 |
| `min(w, h)` (px) | 29.58 | 30.50 | 35.35 | 42.91 | 86.47 |

This confirms BC1 independently of the round 2 review: a `min box height
≥ 60 px` gate would have been violated by this band's own data (minimum
43.63 px), while the pose-invariant `p05 of min(w,h) ≥ 25 px` gate clears
with 5.5 px of margin (measured p05 30.50 px).

### Artifacts

- `tools/run_scene004_gate0_probe.py` — the probe (new)
- `docs/evidence/P1-SCENE-004-gate0-probe.json` — hash-bound result with all
  204 per-frame samples
- `tests/test_scene004_gate0_probe.py` — decision-band, guard and statistics
  regression tests

### Automated checks

| Check | Result |
|---|---|
| Full Python suite, `.venv-track` (`python -m unittest discover -s tests`) | **116/116 passed** (109 pre-existing + 7 new) |
| New probe tests only | 7/7 passed |
| Gate 0 probe execution, `.venv-yoloe` (real pinned models) | completed in 22.3 s, 204 samples |

The same full suite run under `.venv-yoloe` reports 2 failures
(`test_trackers.test_pinned_opencv_csrt_initializes_and_updates` and
`test_track_loop.test_cli_runs_pinned_csrt_to_a_versioned_summary`). Both are
the pre-existing environment split, not a regression from this batch: that
venv carries plain `opencv-python` 5.0.0, which does not expose
`TrackerCSRT_create`, while `.venv-track` carries
`opencv-contrib-python==5.0.0.93`. No file touched in this batch is on either
test's code path.

Commands:

```
.venv-track/bin/python -m unittest discover -s tests

.venv-yoloe/bin/python -m tools.run_scene004_gate0_probe \
  --capture-root <sandbox-copy> \
  --output docs/evidence/P1-SCENE-004-gate0-probe.json
```

## Circuit geometry — pre-freeze derivation (2026-07-29)

This is the **design-input derivation**, not the acceptance-1 artifact. The
artifact must be re-derived from the frozen scenario bytes once the scenario
config exists; these numbers are what those bytes will be chosen to produce,
and they are recorded now so the choice of vertices is reviewable rather than
reverse-engineered from a passing gate.

### Road geometry, measured

`config/road_data.json` stores **local** (pre-yaw) half extents; consumers
rotate the query point by `-yaw` into the tile frame
(`RoadSceneAudit.TrySurfaceAt`, `P1Scene003AnchorAudit` line 490). The z=120
east-west road is therefore `Road Lane_01` tiles at centres (140, 120) and
(160, 120) with yaw 90° and local half extents (6, 10), giving world
footprints x∈[130,150] and x∈[150,170], both z∈**[114, 126]** — a 12 m band,
surface y = 0.2000004. It meets `Road Intersection_01` (x∈[110,130],
z∈[110,130]) to the west and `Road T_Intersection_01` (x∈[170,190]) to the
east. Probed directly: z=114.5 and z=125.5 are on the surface with 0.5 m
edge margin, z=113.6 and z=126.4 are off it.

### Frozen inputs

| Input | Value |
|---|---|
| Anchor candidate centre | (140.0, 112.0) |
| Anchor y | derived from the measured support surface (not 0.2) |
| Hover altitude | 25.0 m above the support surface |
| Target speed | 2.0 m/s |
| Circuit vertices | (128,117) (152,117) (155,120) (152,123) (128,123) (125,120) |

Two-lane, right-hand traffic: east-bound on the south lane z=117, west-bound
on the north lane z=123, joined by 3 m SCENE-002-style chamfers at both ends.
Extent 30 × 6 m; each lane centre sits 3 m inside the asphalt edge.

### Envelope, derived and margin-reported (BC6)

Camera y = support_y + 25.0 ≈ 25.0; the target drives on the road surface at
y = 0.2, so Δy = 24.8 m. Horizontal distance to the anchor over a 0.25 m
sampling of the whole circuit: min 5.000 m, max 17.000 m.

| Derived quantity | Value | Gate | Margin |
|---|---|---|---|
| Max slant range | 30.0673 m | ≤ 32 m | **1.933 m** |
| Min slant range | 25.2990 m | — | — |
| Max off-nadir | 34.4300° | ≤ 45° and margin ≥ 5° | **10.570°** |
| Loop period | 32.4853 s (perimeter 64.9706 m) | ∈ [30, 45] s | 2.49 s / 12.51 s |
| Box height (measured scale `h_px·R ≈ 1955`) | 65.0–77.3 px | — | — |

The off-nadir margin is the one that killed SCENE-001 and SCENE-003; here it
is 10.6°, and the slant margin is the tightest gate at 1.93 m. Both are
reported rather than reduced to pass/fail, as BC6 requires.

### Legality pre-checks, run in Python against the same rotation logic

| Check | Result |
|---|---|
| Circuit centreline (0.25 m sampling) on an allowlisted road surface | **0 samples off surface**; traverses `Road Lane_01` and `Road Intersection_01` |
| Corridor ±1.5 m (half width 1.0 + margin 0.5) on allowlisted asphalt | **fully inside** |
| Anchor disc r=1.5 m at (140, 112) versus the asphalt band | **disjoint** (2,880 boundary samples, 0 on asphalt; nearest asphalt edge z=114, disc reaches z=113.5) |
| Anchor centre on a road surface | no — the anchor is off-road, as intended |

These are pre-checks only. Whether (140, 112) sits on an **allowlisted
support surface** (grass) and whether the anchor column, tether corridor and
hover sphere clear every obstacle can only be answered by the audit against
the real Unity scene, which is the next step and is the same gate that
returned `BLOCKED_ANCHOR_PLACEMENT` for SCENE-003.

## Anchor audit against the real city scene (2026-07-29)

**Result: `CLEAR`. Legal anchor at (140.0, 1.3113418617649586e-06, 108.0).**

This is the gate that returned `BLOCKED_ANCHOR_PLACEMENT` for SCENE-003, and
the elevation above is the *same* grass-tile surface height
(`1.3113418617649586e-06 m`) that produced 1,257/1,257 rejections there. It
is accepted here because the elevation is derived from the measured support
surface rather than asserted as `y = 0.2 ± 0.05` — which was the road surface
height all along.

### What the audit implements

`Assets/TetheredTracking/Scripts/P1Scene004AnchorAudit.cs`, driven by the
frozen contract `config/p1-scene-004-anchor-placement.json`. Geometry
primitives are reused from `P1Scene003AnchorAuditor` (their accessibility was
widened from `private` to `internal`; no behaviour changed, and the SCENE-003
tests still pass) so the two audits cannot drift apart. Four ordered gates,
each evaluated per lattice candidate:

1. **Support** — the whole 1.5 m expanded disc must lie strictly inside an
   allowlisted support patch, not merely its centre point. SCENE-003 tested
   the centre only, which would let a disc hang over a boundary. Support now
   comes exclusively from allowlisted scene prefabs: `RoadSceneData.Validate`
   already forces every `surfaces` entry to be an allowlisted *road*, and a
   road is never legal anchor support, so SCENE-003's acceptance of any
   road-data surface as support is closed rather than carried over. The
   elevation is an output; the tolerance now only detects disagreement
   between several support surfaces under one candidate.
2. **Road disjointness** (C6) — the disc must not touch the asphalt band;
   tangency counts as a violation.
3. **Envelope** (BC3) — max slant range and max off-nadir against the frozen
   circuit, so the deterministic fallback cannot return an anchor a later
   gate would reject. Margins are recorded on the failing path too (BC6).
4. **Clearance** — the SCENE-003 Minkowski anchor-column / tether-corridor /
   hover-sphere volumes, unchanged, using the derived elevation.

### Real-scene result

| Quantity | Value |
|---|---|
| Candidates in the 0.5 m / 10 m lattice | 1,257 |
| `SUPPORT_NOT_FOUND` | 924 |
| `ANCHOR_DISC_OVERLAPS_ROAD` | 0 |
| `ENVELOPE_OUT_OF_BOUNDS` | 288 |
| `CLEARANCE_INTERSECTION` | 20 |
| Legal candidates | **25** |
| Selected (rank 194, 4.00 m from the requested centre) | **(140.0, 1.3113418617649586e-06, 108.0)** |
| Max slant / margin | 30.5866 m / **1.4134 m** |
| Max off-nadir / margin | 35.8246° / **9.1754°** |

Contract SHA-256 `e95f6f4e865a6155e79527c118dd02dae63743fe2686c3a40d054eecd4d54320`,
road data `111e0759…01894`. Full artifact:
`docs/evidence/P1-SCENE-004-anchor-audit.json`.

The requested centre (140, 112) itself is **not** legal — no grass patch can
contain the 1.5 m disc there. Measured grass support near the circuit spans
z ∈ [102, 108], x ∈ [132, 149], so z = 108 is the closest legal row to the
road and the deterministic fallback selects it. The 20 clearance rejections
confirm that gate is doing real work rather than passing vacuously.

### The circuit was re-frozen before the vertices were committed (BC6)

The first audit run, against the pre-freeze circuit
(lanes z=117/123, chamfer apexes at x=125/155), returned `CLEAR` with a max
slant of 31.3694 m — a margin of only **0.6306 m** under the 32 m cap.
BC6 requires narrowing the circuit before freezing rather than freezing and
then failing disposition row 2, so the circuit was re-shaped and re-audited.
The binding constraint is a genuine tension: the anchor sits 8 m back from
the near lane, the loop period floor (30 s at 2.0 m/s) forces a perimeter
≥ 60 m, and a longer loop pushes the slant. Resolving it meant moving the
lane pair south within the asphalt band rather than keeping it centred:

| | Pre-freeze | Frozen |
|---|---|---|
| Lanes (z) | 117 / 123 | **116 / 121** |
| Straight length | 24 m | 24 m |
| Chamfer apexes | x = 125 / 155 | x = 125.5 / 154.5 |
| Perimeter / period | 64.9706 m / 32.4853 s | 62.1421 m / **31.0711 s** |
| Max slant / margin | 31.3694 m / 0.6306 m | 30.5866 m / **1.4134 m** |
| Off-nadir margin | 7.2397° | **9.1754°** |
| South corridor edge clearance | 1.5 m | 0.5 m |

Frozen vertices: (128, 116) (152, 116) (154.5, 118.5) (152, 121) (128, 121)
(125.5, 118.5). Re-verified in Python against the same `-yaw` rotation the
audit uses: the corridor at ±1.5 m has **0 samples off allowlisted asphalt**,
and the anchor disc has **0 samples on asphalt** over 1,440 boundary points.

### Predicted target size against the BC1 gate

Measured from Gate 0's 204 samples, `min(w,h) · R` has p05 920.3 px·m and
median 1086.4 px·m. At the frozen max slant of 30.5866 m that predicts a p05
minimum side of **30.09 px** against the BC1 gate of ≥ 25 px, and a box
height band of roughly 54–72 px across the circuit. The gate is a
measured-scale prediction here; the acceptance-1 artifact must re-derive it
from the frozen scenario bytes, and scout-3 measures it for real.

### Automated checks

| Check | Result |
|---|---|
| Focused Edit Mode `P1Scene004AnchorAuditTests` | **8/8 passed** |
| Full Edit Mode `TetheredTracking.Tests` | **100/100 passed** (92 pre-existing + 8 new) |
| Full Python suite, `.venv-track` | **116/116 passed** |

The full Edit Mode pass is what confirms the `private` → `internal`
accessibility widening in `P1Scene003AnchorAudit.cs` changed no behaviour:
the SCENE-003 audit tests still pass unmodified.

**Environment note, recorded rather than hidden:** the first two batchmode
attempts failed with ~107 Unity licensing handshake errors
(`Failed to handshake to channel: "LicenseClient-zc"`), and that degraded
session then reported bogus compile errors across untouched files
(`JsonUtility does not exist`, `MeshCollider` forwarded to
`UnityEngine.PhysicsModule`) because the engine modules were not resolvable.
Killing the stale licensing client and re-running produced
`Successfully resolved entitlement details` and a clean compile. The results
above are all from licensed, clean-compile runs.

## Scenario, geometry artifact, scout-3 profile and the N4 fix (2026-07-29)

### Scene deconfliction and `config/scenario.p1-scene-004.json`

The SCENE-001/002 corridor generator is hardwired to `scenario.default.json`
and asserts exactly three baseline violations, so
`P1Scene004SceneEvidenceGenerator` runs the same audit machinery against the
SCENE-004 scenario without expected-count assertions — the before state is an
observation, only the after state is a gate — and additionally surveys parked
vehicles near the circuit, because a distractor has to be close enough to
appear in frame, not merely marked.

| Quantity | Value |
|---|---|
| Corridor violations before adjustments | 2 (`Vehicle_Taxi (2)`, `Vehicle_SUV_color01 (1)`) |
| Corridor violations after adjustments | **0** |
| Audited vehicles | 104 |
| Marked distractors / expected | **2 / 2** |

Both violators were also the two closest vehicles to the circuit (0.40 m and
2.57 m), so they are relocated *and* marked as distractors: `Vehicle_Taxi` to
(162.0, 117.0) and `Vehicle_SUV_color01` to (118.0, 121.0), both on asphalt
beyond the loop ends. Artifact: `docs/evidence/P1-SCENE-004-scene-survey.json`.

### Geometry artifact (acceptance 1)

`tools/build_scene004_geometry.py` derives the envelope from the **frozen
scenario bytes** (SHA-256 `00c8802a…b514`) and refuses to run unless the
scenario anchor equals the audited anchor and `road_data_sha256` matches.
Result `ENVELOPE_OK`, every gate reported with its margin (BC6):

| Gate | Value | Limit | Margin |
|---|---|---|---|
| Max slant range | 30.5866 m | ≤ 32 m | 1.4134 m |
| Max off-nadir | 35.8246° | ≤ 45°, margin ≥ 5° | 9.1754° |
| Loop period | 31.0711 s | [30, 45] s | 1.0711 s |
| Predicted `min(w,h)` p05 | 30.0883 px | ≥ 25 px | 5.0883 px |
| Distractor opportunities | 49 | ≥ 10 | 39 |

The pixel gate is BC1's pose-invariant percentile, predicted from the scale
Gate 0 measured over 204 real samples (`min_side · R`: p05 920.3, median
1086.4 px·m) and recorded in the artifact so the prediction's basis is
visible. The distractor precheck projects each relocated vehicle's full box
through the truth-directed camera at 2 Hz over a loop and counts ticks where
the box is **fully in frame with a minimum side ≥ 16 px**: 23/62 for the taxi
and 26/62 for the SUV, minimum sides around 80 px. This is what C8 asked for —
the ≥10 opportunity floor is readable *before* the capture, instead of
disposition row 5 firing after one is burnt. Per BC5 the 16 px floor lives
only in the geometry artifact; `config/detector-reanchor.models.json` and its
`minimum_crop_side_px = 2` are byte-identical, and a test asserts it.

### N4 truth-writer fix and the `TARGET_VISIBLE_UNPROJECTABLE` class (BC2)

`P1DetectScoutingTruthWriter.Write` used to throw when a visible target's box
could not be canonicalised. Throwing left **no sidecar on disk**, so the
offline analyzer scored the tick as `MISSING_IMAGE_TRUTH_PAIR` — a detector
miss. That is how scout-1 lost 18 of its 45 samples: a pointing/geometry fact
laundered into a recall number. Sonnet flagged the throw as non-blocking note
N4 in round 3; it was never fixed.

Now the document is always written, carrying an explicit status
(`VALID`, `TARGET_VISIBLE_UNPROJECTABLE`, `TARGET_NOT_VISIBLE`) on the target
and on each distractor box, under schema `p1-detect-scouting-truth/v2`. A
blank distractor id still fails closed. scout-1's frozen v1 documents are
untouched and stay readable.

### `scout-3` profile

`tools/run_scene004_scouting.py` is a separate module by design: the legacy
`run_detector_scouting.py` carries the frozen §8 protocol and the closed
scout-1 chain, and the accepted design keeps that profile and its read-only
audit exactly as they are. Only pure helpers are shared, so no legacy
behaviour can drift. It adds:

* **Four accounting classes**, of which only `PAIRED_VISIBLE` enters the
  gating denominator. `TARGET_VISIBLE_UNPROJECTABLE` gets its own class and
  its own rate gate; `MISSING_IMAGE_TRUTH_PAIR` is capture health;
  `TARGET_NOT_VISIBLE` is outside the analysis.
* **Health before recall (B3)**: missing-pair rate > 5% or unprojectable rate
  > 2% is `CAPTURE_INCOMPLETE`, decided before any recall comparison.
* **Two denominators, one gate**: strict gates at ≥ 0.7, conservative is
  reported alongside, and which one gates is frozen in code before any
  capture exists.
* **Dual truth schema**: v2 with explicit status; v1 accepted read-only,
  where an absent box takes the class that stays *out* of the gating
  denominator.
* **Cross-profile rejection**: a capture whose frames carry a different
  `scenario_id` is refused, and the session manifest must match both the
  scenario bytes and the geometry artifact hash.
* No auto-approval: sufficient evidence yields
  `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`, never a GO.

The regression that matters most reproduces scout-1's exact failure mode: a
capture with 40% missing pairs and a **perfect** detector now returns
`CAPTURE_INCOMPLETE` / `MISSING_PAIR_RATE_ABOVE_LIMIT` with strict recall
1.0, where the old accounting would have reported conservative recall 0.60
and declared the benign envelope infeasible.

## Automated checks at the stop point

| Check | Result |
|---|---|
| Full Python suite, `.venv-track` | **132/132 passed** (109 pre-existing + 23 new) |
| Full Edit Mode `TetheredTracking.Tests` | **100/100 passed** |
| Full Play Mode | **3/3 passed** |
| Focused Edit Mode `P1Scene004AnchorAuditTests` | 8/8 passed |
| Gate 0 probe, `.venv-yoloe` with the real pinned models | 204 samples, 22.3 s |

The same Python suite under `.venv-yoloe` reports 2 failures
(`test_trackers`/`test_track_loop` CSRT cases). That is the pre-existing
environment split — that venv carries plain `opencv-python`, which does not
expose `TrackerCSRT_create`, while `.venv-track` carries
`opencv-contrib-python==5.0.0.93`. No file in this batch is on either test's
code path.

Commands:

```
.venv-track/bin/python -m unittest discover -s tests
```

```
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -projectPath ~/TetheredDroneTracking -runTests -testPlatform EditMode -testFilter TetheredTracking.Tests -testResults runtime/test-results/p1-scene-004-editmode.xml -logFile runtime/test-results/p1-scene-004-editmode.log
```

## scout-3 session lifecycle and the round 1 notes (2026-07-29)

Sonnet round 1 returned `PASS_WITH_NOTES` on `d93e38e` with no blocking
findings (`docs/reviews/P1-SCENE-004.md`). This batch adds the deferred
session lifecycle and closes all five notes.

### Note 1 closed at the root, not at the symptom

The hazard was real: `P1DetectScoutingTruthWriter` hardcoded its sidecar
directory to the literal `p1-detect-scouting`, while
`tools/run_scene004_scouting.py` reads `p1-scene-004-scouting`. Reusing the
writer for scout-3 would have written every sidecar where nothing reads it,
so every tick would have returned `MISSING_IMAGE_TRUTH_PAIR` and tripped
`CAPTURE_INCOMPLETE` regardless of detector performance — bypassing the very
health gate this work item built to stop that class of false report.

Rather than rename one literal, the directory is now **derived**. A new
`IScoutingTruthSession` contract supplies `SessionRoot`, `SessionId`,
`WorkId`, `ScenarioId`, `GimbalDriver`, `TruthSchema` and
`ScenarioConfigSha256`; the writer composes
`runtimeRoot / session.SessionRoot / session.SessionId / "truth"` and
validates document identity against the session rather than against
constants. `P1DetectScoutingSession` returns the legacy root unchanged, and
the new `P1Scene004ScoutingSession` returns its own. A future profile
therefore cannot silently inherit another profile's path. A test asserts the
C# root constant and the Python `SESSION_ROOT` still name the same
directory, and that the writer contains no directory literal.

`CoverageEvaluator` now selects between the two session markers and **fails
closed if both are present** (`multiple_active_scouting_sessions`), since two
active profiles would make a capture's identity ambiguous. The truth
document's `work_id` follows the session instead of defaulting to the
DETECT-001 literal.

### Notes 2–5

- **N2**: the review scope below now states the v2 write path precisely
  (write path is v2-only henceforth; v1 is read-only for the frozen scout-1
  archive), and the same clause is recorded in the formal design so scout-2
  does not rediscover it after M3.
- **N3**: distractors get their own `NOT_IN_FRAME` status for the ordinary
  off-screen case instead of borrowing the target-shaped
  `TARGET_VISIBLE_UNPROJECTABLE`. Consumers still gate on `!= VALID`, so no
  accounting number moves.
- **N4**: `ClearanceIntersectionRejectsAnObstacleInsideTheHoverSphere` adds
  the missing isolated case for the fourth gate — a thin column at hover
  height, clear of the ground volumes' height band but through the hover
  sphere.
- **N5**: the audit's top-level `status` no longer collapses disposition rows.
  `BlockingStatus` returns `ENVELOPE_OUT_OF_BOUNDS` when candidates reached
  the envelope gate and `BLOCKED_ANCHOR_PLACEMENT` only when none did.
  Regenerating the real-scene artifact after this refactor produced a
  **byte-identical** file (SHA-256 `4e1eca2c…`), confirming the change is
  behaviour-free on the `CLEAR` path.

### Session lifecycle

`tools/run_scene004_scouting.py` gains `prepare` / `preview` / `bind` /
`analyze` / `close`. The session document is deterministic in `session_id`
alone and binds both the scenario bytes and the geometry artifact hash; the
loop period is read from the artifact rather than restated, so the session
cannot drift from the circuit the envelope gates were computed on. Every
document is create-once, with a repeat write allowed only when the bytes are
identical. Preparing a *different* session while one is active is refused
rather than silently taking over the marker, and `close` refuses to run
without a result.

### Automated checks

| Check | Result |
|---|---|
| Full Python suite, `.venv-track` | **137/137 passed** |
| Full Edit Mode `TetheredTracking.Tests` | **102/102 passed** |
| Full Play Mode | **3/3 passed** |
| Anchor artifact regenerated after the N5 refactor | byte-identical |

One guard was widened deliberately: the truth-leak audit's allowlist gains
`P1Scene004Scouting.cs`. That guard confines truth references to the
evaluator and the scouting profile files, and the scout-3 session type is one
of those; nothing on the controller or perception path is on the list.

### Post-review `prepare` conflict-order follow-up

Sonnet round 2 passed candidate `617f933` with a non-blocking finding:
`prepare_session` created a different candidate session's directory and
manifest before noticing that another session already owned the active
marker. The marker was never replaced, so identity and accounting were safe,
but a refused command left an orphaned directory.

The conflict check now runs before any candidate-directory creation, matching
the legacy tool's check-then-create order. The lifecycle regression asserts
that a refused second session leaves no directory at all. This changes no
manifest field, metric, model, truth path, scenario byte or Unity behavior.

| Check | Result |
|---|---|
| Focused `test_scene004_scouting.py` | **21/21 passed** |
| Full Python suite, `.venv-track` | **137/137 passed** |
| `py_compile` on the changed tool and test | **passed** |
| Unity rerun | **not applicable** — Python-only pre-write ordering |

No real session or capture was created while applying or testing the fix.

### Operator simulation-timer HUD follow-up

Before starting the real capture, the user paused the handoff and requested a
visible timer. `SimulationTimerHud` is a separate read-only IMGUI component,
mounted by `TetheredScenarioBootstrap` and anchored 10 px from the upper-right
corner. It displays `SIMULATION TIME` as `MM:SS.t`.

The value comes directly from
`SensorFrameWriter.CurrentSimulationTimeSeconds`, the same clock used for
sensor-frame `simulation_time_s`; the HUD neither owns nor alters time and
does not read truth, tracking observations, metrics or session state. Tests
cover formatting, the 59.99 s carry into the next minute, invalid-value
fail-closed behavior and upper-right geometry.

| Check | Result |
|---|---|
| Unity Roslyn compile, full `TetheredTracking.Runtime` | **passed** (4 pre-existing obsolete-API warnings) |
| Unity Roslyn compile, full Edit Mode test assembly against the rebuilt runtime | **passed** |
| Full Python suite, `.venv-track` | **137/137 passed** |
| Unity Test Runner | **pending** — a post-fix batch launch reached assembly reload without the former GUID/`CS0246` diagnostics, but headless licensing then failed before tests ran |

That statement was true when the timer code was written, but a subsequent
live-artifact recheck found that the user had already started and paused the
canonical Play capture before requesting the HUD. Codex did not alter the
manifest, marker or partial capture: frame/image/truth IDs 0–829 are present,
the last frame is at `simulation_time_s = 41.482582`, and the manifest/marker
remain byte-identical (`41f45eaa…8551`). The timer cannot hot-load into that
paused Play domain.

The first timer commit also carried a malformed 64-hex-character GUID in
`SimulationTimerHud.cs.meta`. The user's Unity screenshot retained the
resulting invalid-GUID/YAML-parser error and the dependent `CS0246` diagnostic.
The repair changes only that unused asset identity to a unique, lowercase
32-hex-character Unity GUID. Static validation passes, and a new Unity
batch launch contains none of the former GUID or `SimulationTimerHud`
compilation diagnostics. It could not produce a Test Runner result because
the local headless licensing client repeatedly rejected the protocol
handshake; interactive editor import remains the final smoke.

The first interactive reopen did not reach that smoke. `Editor.log` shows
successful package-manager connection and Mono assembly reload, followed by
licensing IPC timeouts and `505 Unsupported protocol version '1.18.1'`.
Process inspection then found no live Unity Editor or Package Manager, only
the Hub licensing client and an orphaned per-editor licensing client holding
the `Unity-LicenseClient-zc-6000.4.1` mutex. The visible `Connection Lost`
loading state is therefore an environment blocker, not a timer compile result.
The user authorized narrow process cleanup; Codex sent `SIGTERM` only to the
orphaned versioned client (PID 53707) and verified it exited. Hub and its
normal licensing service remain running, with no Editor, Package Manager or
versioned client left. No cache, project file or capture artifact was removed.

### Still not done

The user later reopened Unity successfully and ran the same
`p1-scene-004-scout-3` identity to 121.531937 s before pausing. This is not a
continuation: the new Play domain restarted frame IDs at zero. All 830 old
truth sidecars for IDs 0–829 rejected the new writes with `IOException`,
while sensor images/metadata at those IDs were replaced by the second run.
IDs 830–2430 then produced new matching truth. The directory therefore holds
2,431 continuous files of each kind but crosses two Play domains at the
829/830 boundary. It is a protocol-invalid hybrid, regardless of the close
simulation timestamps, and must not be previewed, bound, analyzed or closed.
The user exited Play while paused. Codex moved the complete failed exchange
recoverably to
`runtime/test-results/p1-scene-004-scout-3-protocol-invalid-same-id-retry-20260729/`.
Its 7,297 files total 118,729,222 bytes; the logical tree SHA-256 is
`451311daacf7f0bd40090bdd5e0977d4f2c37bc40582ae48eca82c76cffab2e6`
both before and after the move. The archive contains 4,863 frame-slot files,
2,432 session files, `metrics.json` and the former active marker. Live
`runtime/frames` is empty; live metrics, marker and scout-3 directory are
absent. Nothing was deleted, and no new identity was prepared. A clean
restart still requires explicit authorization for a fresh session ID.

The user explicitly authorized `p1-scene-004-scout-4`. The first direct-file
CLI invocation failed during imports and was confirmed to have written
nothing; the supported module entry point then prepared the new create-once
session. Manifest and active marker are byte-identical SHA-256
`7f18c71003bd107bfea920644baa23e9d178ffab304c26267e0b104650c908d8`;
an identical second `prepare` validates idempotence. Installed scenario
configuration remains `00c8802a…b514`, geometry remains `248ae0b3…fefe`,
and live frames/truth are empty with no `metrics.json`. The editor remains
outside Play and no capture has started.

The user then ran exactly one scout-4 Play domain and reported exiting with
no Console error. Machine inspection finds 2,405 JPEGs, 2,405 frame documents
and 2,405 truth sidecars, all continuous IDs 0–2404 with identical ID sets.
The last frame/truth pair has the identical simulation timestamp
`120.23035430908203`; manifest and active marker remain `7f18c710…08d8`.
The 0.23 s overshoot above the requested 120 s is below the 128 s retention
boundary and does not affect the three-loop requirement.

`preview` froze frame 140 at `7.030570030212402 s`; raw image SHA-256 is
`0704650f…05f8` and metadata SHA-256 is `f73b08c4…6124`. Without reading the
truth box, Codex manually proposed normalized top-left
`xywh = (0.440625, 0.4375, 0.11875, 0.10625)`, rendered as pixel rectangle
`(282,210,76,51)` in a separate overlay (`ef477c20…7d0f`). No
`reference.json` existed at that point: binding remained blocked on the
user's visual confirmation.

### Scout-4 binding, analysis and closure

The user confirmed the overlay, including the expected axis-aligned box
around the angled vehicle. `reference.json` was created once with the exact
confirmed box; SHA-256 is `8105b0d3…33bb`. The first analysis invocation used
the tracker-only environment and stopped before inference because
`ultralytics` was absent; it created no result. The existing `.venv-yoloe`
environment then loaded the frozen YOLOE/DINOv2 assets and completed.

The create-once result (`4a29f20d…188b`) records 187/187
`PAIRED_VISIBLE`, zero missing pairs and zero unprojectable samples.
Strict detector recall is 172/187 = **0.919786**, above the frozen 0.7 gate.
There are 203 valid distractor cosines; target similarity median/mean is
0.698531/0.713489 versus distractor 0.459004/0.472703. Target threshold
passes are 181/187 and the 0.1 separation margin passes 174/187. The
non-gating upper-range quartile is 40/48 = 0.833333 recall.

The frozen result is
`AWAITING_EMBEDDING_FEASIBILITY_REVIEW /
RECALL_AND_SEPARATION_EVIDENCE_SUFFICIENT`. This is explicitly not automatic
GO: the user must decide whether the overlap/tail risk is acceptable before
the ≥150 s/≥4-loop qualification stage. `close` created completion
`d095b300…840d` bound to the result and removed the active marker. The
session is closed and retained; no qualification session has started.

### User GO and qualification-slot preparation

After manually inspecting the authoritative result, the user explicitly
answered `GO` on 2026-07-29. This fires the pre-registered disposition-table
row 7, `GO_FOR_QUALIFICATION`. It authorizes only DETECT-001 acceptance 6 on
the explicitly benign SCENE-004 geometry; it does not authorize RATE-003,
retune any threshold/model, or turn this carrier-development scene into a
formal difficulty claim.

Codex reserved fresh run ID `p1-detect-001-qual-1`. Before any new Play
domain, the closed scout-4 shared exchange was moved recoverably to
`runtime/test-results/p1-scene-004-scout-4-closed-exchange/`. It contains
4,812 files / 114,484,446 bytes; the logical relative-path/content tree
SHA-256 is
`55fc5fff03f6b71f45748b2fcdf914e19a6279eb4ca2a732b16a4e3b6a94196a`
both before and after the move. Durable scout-4 truth, manifest, reference,
result and completion remain in the closed session directory. Live frames
are empty, live `metrics.json` is absent, and no scouting or RATE active
marker exists.

The next operator boundary is a fresh exact-frame initialization capture:
enter Play once, keep Game view active, pause in `[7,8) s`, and do not resume
until Codex freezes and overlays that frame and starts the already reviewed
20 Hz NanoTrack-v2 + triple-gated re-anchor runtime. Qualification gates
remain wall-clock/simulation span ≥150 s, ≥4 loops, `C_track|geom ≥0.4`,
incorrect/matched <0.5, no gap/reinit, detector cadence completion ≥0.8 and
honest wrong-recapture reporting.

### Qualification attempt 1 — fail-closed monotonic-clock blocker

The user entered one fresh Play domain and paused with latest frame 187 at
`9.380409240722656 s`. Twenty complete sensor candidates existed in
`[7,8) s`. Frame 140 was partly crossed by a street-light pole, so Codex
selected frame 159 at `7.981109619140625 s`, which shows the target fully.
Without reading truth, Codex proposed pixel `xywh=(353,82,72,43)`, normalized
`(0.5515625,0.17083333333333334,0.1125,0.08958333333333333)`. The user
confirmed it. Image, metadata and overlay SHA-256 values are respectively
`8ae67217023b53526a14e003020f12d4f28f01a3957d425dec0de692b188ddde`,
`ec509a31ed6207f0b174ff40df183a25189a7ea862bdb8fce2f31778f5d59159`
and `9069bef3917d0af8b74ad85963ab1ba942c8949b2dcb060439694d044b7d6de7`.

Codex started the already reviewed carrier as
`p1-detect-001-qual-1` while Unity remained paused. Model and NanoTrack
loading completed, the run manifest was created, and one INIT observation
was published. `ReanchorRuntime.initialize()` then failed immediately with
`KeyError: 'capture_monotonic_s'`: the SCENE-004 ordinary sensor document is
`tethered-sensor-frame/v1`, whose contract intentionally omits that field.
The process exited code 1 before the user resumed and before any qualification
measurement. The preserved manifest / frame log / summary / metric snapshot
SHA-256 values are `606969a4…dd79` / `8d08f5de…cb0c` /
`32c11445…a943` / `de3d1211…971f`. Summary duration is 0 s with exactly one
INIT frame. The confirmed reference and overlay were copied into the same
run directory. This ID is consumed and must not be reused.

There is no safe configuration-only workaround. RATE v2 does expose
`capture_monotonic_s`, but Unity produces it from
`Time.realtimeSinceStartupAsDouble` (seconds relative to that Editor process)
whereas the re-anchor worker uses Python `time.monotonic()` (a system
monotonic epoch). The result-age and atomic-swap paths directly subtract
worker completion from frame capture time, so feeding v2 would make the
2-second stale-result decision cross incompatible epochs. A repair therefore
changes frame/time semantics and model-decision behavior; it requires
explicit user authorization, a new stable candidate and Sonnet independent
review before any fresh qualification identity.

### Qualification attempt 2 — reviewed v3 preparation

Clock A4 candidate `cd684fc` passed Sonnet Round 6
`PASS_WITH_NOTES`; its sole note affected only the synthetic latency benchmark
and Codex closed it with a direct test and successful real-model benchmark.
The failed qual-1 shared exchange was moved recoverably to
`runtime/test-results/p1-detect-001-qual-1-premeasurement-exchange/`: 383
files / 5,054,706 bytes and logical tree SHA-256
`58327b0cc0bfde80d1d33549a12de2dac6901ed3893d19661e7a783ab1047a36`
before and after. The canonical qual-1 run directory remains untouched.

Fresh run ID `p1-detect-001-qual-2` is reserved. Its run directory does not
exist; live frames and output slots are empty; no scouting/RATE marker exists;
installed `runtime/scenario_config.json` exactly matches
`config/scenario.p1-scene-004.json` at SHA-256
`00c8802aaacfe9732b7128f6a143895f088a8e9a3f44fb2eb39f2eed7bb8b514`.
The next boundary is one new Play domain, paused in `[7,8) s` for a fresh
no-truth box confirmation before the tracker starts.

### Qualification attempt 2 disposition

The user completed the fresh Play domain with no Console error. Qual-2's
descriptive `CoverageEvaluator` result is strong
(`C_track_given_geom=0.8902833462`, incorrect/matched `172/2985`, no
gap/reinit/LOST), and the SCENE-004 geometry remained valid. The session is
nevertheless `PROTOCOL_INVALID_RELEASE_BOUNDARY`: the DETECT non-RATE runtime
treated retained paused frames as released, charged the operator wait as 977
planned detector ticks, and stopped after only 149.415 seconds of fresh
post-resume capture. This is not a SCENE-004 failure. The consumed ID,
artifact hashes, recoverable exchange archive, and authorization boundary are
recorded in
`docs/evidence/P1-DETECT-001-qualification-attempt-2.md`.

## Closed review scope and remaining notes

Sonnet round 2 independently reviewed the complete scout-3 lifecycle on
candidate `617f933` and returned `PASS_WITH_NOTES`; the mandatory stop is
closed. The reviewed scope includes `CoverageEvaluator.cs`,
`P1DetectScouting.cs`, `P1Scene004Scouting.cs`,
`tools/run_scene004_scouting.py`, the anchor/status changes and their tests.
The authoritative findings and reproduced test evidence are in
`docs/reviews/P1-SCENE-004.md`.

The post-review change above is limited to the Python `prepare` pre-write
order and its regression. It does not reopen the truth-sidecar/accounting
protocol stop. Remaining non-blockers are recorded rather than hidden: the
two-active-profile branch lacks a direct Unity regression; the health-rate
denominator wording is cosmetically different from the proposal; and
`analyze_session` validates the create-once reference image hash but not every
reference identity field. Annex A's A1 probe-mid and A2/AC3/AC4 healthcheck
work remains a separate future Sonnet stop because AC3 changes the manifest
schema and Unity writer construction.
