# P1-TRACK-002 — independent verification

Reviewer/role: Claude Sonnet / independent verification

Round: 1

Date: 2026-07-24

Implementation snapshot: candidate `46747d8` (review range `ef24414..46747d8`,
as requested). Evidence handoff `b51179a` and the later
`2018d29` (successor-proposal round 2) on top are both docs-only, confirmed
below.

Verdict: **PASS_WITH_NOTES**

## Scope

`git diff ef24414..46747d8 --stat`: 12 files, 1181 insertions/10 deletions —
`config/nanotrack-v2.models.json` (new), `controller/trackers.py` (+344),
`controller/track_loop.py`, `tools/fetch_tracker_models.py` (new),
`tools/benchmark_tracker.py` (new), `tools/run_track_experiment.py`,
`tools/run_rate_study.py`, and five test files. Independently confirmed
`git diff ef24414..46747d8 --stat -- Assets/ config/scenario.*.json` is empty
— no Unity C# and no frozen rate-study scenario config changed, so the closed
`P1-M0-001`/`P1-TEST-001` gates and the archived RATE-001 conditions cannot
have been disturbed. `git diff 46747d8..b51179a` and `b51179a..2018d29`
restricted to `controller/ tools/ tests/ config/ Assets/` are both empty, so
`46747d8` is the correct code snapshot. No implementation code was modified
during this review.

## Accepted requirements checked

From `docs/proposals/P1-TRACK-002-deep-sot-plugin.md` (Round 2
`ACCEPTED_WITH_BINDING_CLARIFICATIONS`), the items in scope for *this core
candidate* (acceptance 1–3, 6; acceptance 4/5/7 explicitly await
`P1-M2-RATE-002` infrastructure and the Unity case):

1. Adapter + failure-path tests: model missing/corrupt/hash-mismatch,
   constructor/update exceptions, non-finite or out-of-range score, invalid
   box, unknown selector, manifest round trip, deterministic offline loading.
2. Install smoke: both model SHA-256 recorded, constructor usable,
   `pip check` clean.
3. Latency: 640×480 CPU compute p95 `< 50 ms`.
6. Boundary/zero-tuning audit: no ground-truth read, model hashes identical
   before and after the run, `threshold_source="none"` in the manifest.

Plus binding clarifications 1 (immutable upstream commit + exact URLs + both
hashes + affirmative artifact license), 2 (no implicit threshold, no CSRT
fallback, clipping stays centralized in `_publication_ready_result`), and 4
(core may reach a stable-candidate stop before the shared pilot exists).

## Files read

- `config/nanotrack-v2.models.json` (full)
- `controller/trackers.py` (full diff, all 344 new lines: spec loader, hash
  verifier, `create_nanotrack_backend`, `NanoTrackV2Tracker`, `create_tracker`,
  and the `manifest_identity()` additions on all three plugin classes)
- `tools/fetch_tracker_models.py`, `tools/benchmark_tracker.py` (full files)
- Diffs to `controller/track_loop.py`, `tools/run_track_experiment.py`,
  `tools/run_rate_study.py`
- All five test diffs: `tests/test_trackers.py` (+269),
  `tests/test_track_loop.py` (+120), `tests/test_track_experiment.py`,
  `tests/test_rate_study.py`, `tests/test_benchmark_tracker.py` (new)
- `docs/proposals/P1-TRACK-002-deep-sot-plugin.md` (both review rounds),
  `docs/evidence/P1-TRACK-002-implementation.md`

## Independent verification performed

Reran the automated evidence myself rather than trusting the report:

```
$ .venv-track/bin/python -m unittest discover -s tests -v
Ran 55 tests in 0.337s — OK
$ .venv-track/bin/python -m pip check
No broken requirements found.
$ .venv-track/bin/python -m py_compile controller/trackers.py controller/track_loop.py \
    tools/run_track_experiment.py tools/run_rate_study.py \
    tools/fetch_tracker_models.py tools/benchmark_tracker.py
(clean)
$ git diff --check
(clean)
```

Both real-dependency tests actually **ran** rather than skipping, which I
could confirm from the runner output: `test_pinned_opencv_nanotrack_initializes_and_updates`
emitted OpenCV 5.0.0's real `setPreferableTarget` warning inline, and
`test_cli_nanotrack_manifest_contains_frozen_identity` printed a genuine
`p1-track-run/v1` result line (`{"records": 2, "run_id": "nanotrack-cli",
"state": "TRACKING", ...}`). So the suite exercised a real ONNX model load,
a real `TrackerNano` construct/init/update, and a real subprocess-free CLI
round trip to an on-disk manifest — not stubs alone.

**Model identity, recomputed from the actual files rather than read from the
report:**

```
$ shasum -a 256 runtime/models/nanotrack-v2/*.onnx
530bdd0cd00f19afab79a863e71ba71e3312395a5dc9151af675082bdaaa2fc4  nanotrack_backbone_sim.onnx
0d8c0637be849f092cc7236cae02e55c8b9455ebe37ba50601d6115db4247cd9  nanotrack_head_sim.onnx
$ ls -la runtime/models/nanotrack-v2/
1056849 bytes (backbone), 726198 bytes (head)
```

Both hashes and both byte sizes match `config/nanotrack-v2.models.json` and
the evidence table **exactly**. I ran this hash check *after* the full test
suite had executed (which loads and runs both models), independently
confirming the zero-mutation claim in acceptance 6 rather than taking the
implementer's before/after assertion on faith.

**Benchmark artifact, read directly:** `benchmark-640x480.json` on disk
reports `p95 = 3.332854190375656 ms`, `p95_limit_ms = 50.0`,
`p95_below_limit = true`, `warmup_updates=20`, `measured_updates=100`, and
carries the same two model hashes plus `score_threshold: null`,
`threshold_source: "none"`, `preprocessing_id:
"opencv-tracker-nano-5.0.0-default-v1"`. This matches the evidence document's
table to the digit. I also read `tools/benchmark_tracker.py`'s method and
confirmed the reported number is what it computes: `time.perf_counter()` is
taken immediately around `tracker.update()` only (not around frame
synthesis), warm-up updates are excluded from the sample, and `percentile()`
uses ordinary linear interpolation (independently unit-tested in the new
`test_benchmark_tracker.py`, whose three hand-checkable cases —
`percentile([0,10], 95) == 9.5` etc. — I verified by hand).

## Per-requirement verification

**Frozen artifact identity (binding clarification 1).**
`load_nanotrack_v2_spec()` validates far more than schema presence: the
commit must be a lowercase 40-hex Git SHA, both model digests and the license
digest must be lowercase 64-hex, `license_spdx` must be exactly `Apache-2.0`
(a hard equality check, not a substring or truthiness test), `dnn_backend`
must be `DNN_BACKEND_DEFAULT` and `dnn_target` must be `DNN_TARGET_CPU`, and
`size_bytes` must be a positive `int` with an explicit `isinstance(x, bool)`
exclusion (correctly defending against JSON `true` sneaking through as
`int` — the same defensive pattern I checked in the RATE-001 Round 4 cutoff
guard). Both model URLs in the checked-in spec are commit-qualified
`raw.githubusercontent.com` paths pinned to
`248663fde6bf7c40190cf10ee396d5662919ecd3`, not branch-relative, so they
cannot silently drift. A dedicated test
(`test_frozen_spec_has_affirmative_artifact_identity`) asserts the real
checked-in spec's license/commit/URL-prefix rather than only a fixture's.

**Fail-closed with no CSRT fallback (binding clarification 2).** I traced
every failure path in `NanoTrackV2Tracker.__init__` and confirmed each one
`raise`s rather than degrading: missing spec file, malformed JSON, wrong
schema/tracker, any missing/blank required string, wrong OpenCV version,
missing model file, size mismatch, hash mismatch, constructor exception
(wrapped as `RuntimeError("NanoTrack-v2 constructor failed: ...")`), and a
constructor returning `None`. There is **no** `except` anywhere in the module
that substitutes `CsrtTracker`, and `create_tracker()` raises
`ValueError(f"unknown tracker {name!r}")` for anything outside the two
literals — I grepped the whole file to confirm no fallback path exists.
`_verify_model_file` checks size *before* hashing, so a truncated file gets a
precise diagnostic rather than a generic digest mismatch. The three
constructor-rejection cases are covered by
`test_nanotrack_requires_complete_local_model_identity`, and notably the
hash-mismatch fixture keeps the file *size* correct so it genuinely exercises
the digest check rather than short-circuiting on size — a detail that is easy
to get wrong and was not.

**No implicit threshold.** `update()` returns `getTrackingScore()` unchanged
after only a finite/`[0,1]` range check, with `confidence_source="tracker"`.
There is no comparison of the score against any constant anywhere in the
class; a low score does **not** produce `LOST`. `manifest_identity()` hardcodes
`score_threshold: None` and `threshold_source: "none"`. This correctly
implements the proposal's deliberately narrowed claim (no calibrated loss
detection), and the evidence document restates that honestly rather than
overselling the new tracker.

**Clipping stays centralized (binding clarification 2).** This is the subtlest
part of the diff and I checked it carefully. `NanoTrackV2Tracker.update()`
uses the **new** `pixels_to_norm_unclipped()` rather than the clipping
`pixels_to_norm()` that `CsrtTracker` uses — deliberately, so the plugin does
not introduce a second box policy. I traced both paths to the published
result and confirmed they converge: `TrackLoop.process_available` passes every
raw result through `_publication_ready_result`, whose `clip_box_norm` both
clips partial boxes identically and returns `LOST("invalid_tracker_box")` for
a fully-out-of-frame box — exactly what CSRT's earlier in-adapter clip
produces. I also confirmed `pixels_to_norm_unclipped` does not check
`width/height > 0`, but a degenerate box still fails closed downstream
because `clip_box_norm` rejects non-positive extents. So the two trackers
produce equivalent *published and logged* boxes despite the different
internal path — no divergence enters the comparison data.

**Selector plumbing end to end.** `--tracker {csrt|nanotrack-v2}` is an
`argparse` `choices=` constraint (not a free string) at all three
boundaries — `controller.track_loop`, `tools.run_track_experiment`, and
`run_rate_study launch` — so an unknown name is rejected by the parser before
`create_tracker` is even reached, and by `create_tracker` if called
programmatically. The default is `csrt` at every layer, which correctly means
archived RATE-001 evidence is not retroactively reinterpreted. Both
orchestration hops are covered by real tests
(`test_nanotrack_selector_and_model_paths_are_forwarded` and the extended
rate-study launch test asserting `--tracker nanotrack-v2` plus both model
paths actually appear in the launched command).

**Manifest provenance.** `_manifest()` now calls `tracker.manifest_identity()`
when available. For NanoTrack this persists tracker name/backend, OpenCV
version and package pin, DNN backend/target, both model hashes, preprocessing
ID, repository/commit/tree URL, both model URLs, and the license
SPDX/path/URL/hash. `test_cli_nanotrack_manifest_contains_frozen_identity`
verifies this against the **real** on-disk manifest produced by a real CLI
run, asserting the literal frozen hashes — not a fixture's. I confirmed the
asserted hash string constants (split across source lines) concatenate to the
same values I computed myself.

**Truth-isolation boundary.** The new code reads only
`config/nanotrack-v2.models.json` and the two model files. Neither
`trackers.py` nor the new tools import or read any scenario config, route,
speed, or Unity ground truth, and the pre-existing
`test_tracker_command_receives_only_scalar_orchestration_values` audit still
passes with the new `--tracker` flag present in the command.

**Offline determinism.** `controller/trackers.py` imports no network client;
only `tools/fetch_tracker_models.py` (a separate, operator-invoked tool) uses
`urlopen`. That downloader writes to a `.partial` file, verifies size *and*
hash before `os.replace`, unlinks the partial on any exception, and refuses
to overwrite an existing file whose identity does not match the frozen spec.
So a corrupted or tampered download can never be atomically installed.

## Findings

### Blocking

None found.

### Non-blocking

1. **The recorded `license_sha256` is not verifiable offline.** The spec
   records the artifact license's SPDX ID, path, URL, and SHA-256, and
   `load_nanotrack_v2_spec` validates that the digest is *well-formed* and
   that the SPDX ID is exactly `Apache-2.0` — but nothing downloads or retains
   the `NanoTrack/LICENSE` file itself, so no code (and no offline auditor)
   can ever check that digest against real bytes. Every other hash in this
   candidate is checked against a local artifact; this one is an unverifiable
   assertion by comparison. Binding clarification 1 asks for "affirmative
   license evidence," which recording the hash arguably satisfies, so this is
   not a compliance failure — but fetching and retaining the LICENSE file
   alongside the two `.onnx` files (the downloader already has the pattern)
   would make the license claim auditable on the same footing as the models,
   which matters if this artifact provenance is ever cited in the paper.
2. **The manifest's `dnn_backend`/`dnn_target` record what was *requested*,
   not what OpenCV actually applied.** `create_nanotrack_backend` sets
   `params.backend`/`params.target` from `getattr(dnn, "...", 0)`, and
   `manifest_identity()` then reports the *spec's* declared strings. It never
   reads back an effective value from the tracker object. In this build that
   is benign — `DNN_BACKEND_DEFAULT` and `DNN_TARGET_CPU` are both `0`, so
   even the `getattr` fallback coincides with the correct value — but OpenCV
   5.0.0 emits `Targets are not supported by the new graph engine for now`
   (I saw this warning myself in the test output), which means the requested
   target is not necessarily honored as recorded. Codex discloses this warning
   honestly in the evidence document, so nothing is hidden; the note is that
   the manifest field should be read as "requested configuration," and if the
   paper ever quotes the execution target, that distinction should be stated.
3. **`CsrtTracker.init()` still lacks the exception handling
   `NanoTrackV2Tracker.init()` now has.** This is my `P1-TRACK-001` Round 1
   non-blocking note 1, still open. The new tracker does it correctly
   (`except Exception: self._initialized = False; return False`), which makes
   the asymmetry more visible: an init-time backend exception is a clean
   `RuntimeError` for NanoTrack but an uncaught traceback for CSRT. Not
   introduced by this candidate and not blocking it; worth folding into
   whichever batch next touches `CsrtTracker`.
4. **Naming wart:** `NanoTrackV2Tracker.init()` calls `norm_to_csrt_pixels()`.
   The function is generic (normalized box → integer pixel rect with
   floor/ceil and ≥1 px extent) and is the correct thing to call here, but its
   CSRT-specific name now misleads at a NanoTrack call site. Cosmetic only.
5. **`test_nanotrack_local_loading_does_not_open_network` is narrower than its
   name suggests.** It patches `socket.socket` during a construction that uses
   a *stub* backend factory, so it proves the spec-load + hash-verify path
   opens no socket — it does not exercise the real OpenCV ONNX load under the
   same patch. The real-model test runs separately without the patch. The
   claim "local loading is offline" is still well-supported by the stronger
   structural fact that `controller/trackers.py` imports no network client at
   all, so this is a test-naming precision note, not a coverage gap I want
   closed.

## Missing or weak tests

None at a level I would act on. Every acceptance-1 failure path named in the
proposal has a real test that exercises the actual code path (I checked each
against the implementation rather than trusting the test names), and the two
real-dependency integration tests genuinely execute. The only gap worth
naming is the one implied by note 1: there is no test asserting the license
artifact's integrity, because the artifact is not retained locally to test
against.

## Requirement-to-evidence mapping

| Requirement | Evidence | Verdict |
|---|---|---|
| Acceptance 1 — adapter/failure-path tests (missing, corrupt, hash mismatch, constructor/update exception, bad score, invalid box, unknown selector, manifest round trip, offline load) | `tests/test_trackers.py` (7 new methods, all rerun and traced against `trackers.py`); `tests/test_track_loop.py` CLI manifest test | Met |
| Acceptance 2 — install smoke: both SHA-256 recorded, constructor usable, `pip check` | Hashes independently recomputed by me and matching the spec byte-for-byte; real `TrackerNano` construct/init/update test executed (not skipped); `pip check` rerun clean | Met |
| Acceptance 3 — 640×480 CPU compute p95 `< 50 ms` | `benchmark-640x480.json` read directly: p95 `3.332854 ms`; method independently reviewed (timing brackets `update()` only, warm-up excluded, interpolated percentile unit-tested) | Met |
| Acceptance 6 — zero-tuning/boundary audit | No scenario/ground-truth read anywhere in the new code; `threshold_source="none"` and `score_threshold=null` in manifest and benchmark artifact; model hashes recomputed by me *after* the full suite ran and unchanged | Met |
| Clarification 1 — immutable commit, exact URLs, both hashes, artifact license | Commit-qualified raw URLs pinned to a validated 40-hex SHA; both hashes verified against local files; `Apache-2.0` enforced by hard equality | Met, with Non-blocking note 1 on offline license verifiability |
| Clarification 2 — no implicit threshold, no CSRT fallback, centralized clipping | No score comparison in the class; no fallback path exists (whole-module grep); `pixels_to_norm_unclipped` correctly delegates clipping to `_publication_ready_result`, traced to equivalent published output | Met |
| Clarification 4 — core may stop before pilot infrastructure | Evidence document explicitly lists the shared pilot and Unity case as remaining gates and does not claim `DONE` | Met |

## Requested Codex action

None blocking. Consider, in priority order: fetching and retaining
`NanoTrack/LICENSE` so the recorded license hash becomes checkable like the
model hashes (note 1); labeling the manifest's DNN fields as requested rather
than effective configuration, or reading back an effective value if OpenCV 5
exposes one (note 2); and folding the long-open `CsrtTracker.init()`
exception-safety note into the next batch that touches that class (note 3).
Notes 4–5 are cosmetic.

This candidate correctly remains **not `DONE`**: acceptance 4 (the shared
post-release 30 s qualification pilot), acceptance 5 (descriptive occlusion
smoke), and `UT-P1-TRACK-002-001` all still require the separately owned
`P1-M2-RATE-002` infrastructure and a user Unity session. Nothing in this
review blocks Codex from proceeding to that work.

## Re-review result

Not started. Required only if `controller/trackers.py`,
`config/nanotrack-v2.models.json`, the selector plumbing, or the frozen model
artifacts change, or if the qualification pilot surfaces behavior
inconsistent with what is reviewed here.
