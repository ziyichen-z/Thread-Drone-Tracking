"""P1-SCENE-006 batch 1 gate T1′ — offline detector-probe analyzer.

Consumes a probe capture directory written by the Unity Editor probe tool
(`--probe-root`) and emits the single JSON artifact named by `--output`
(schema `p1-scene-006-probe-result/v1`). The analyzer is strictly
read-only against the probe root; the artifact path is the only write.

Fail-closed validation (any violation raises ValueError, no artifact):

* manifest schema/work_id match, `ticks` exactly `[15, 20, ..., 540]`
  (106 entries), `tick_count == 106`, `k_star` an integer in [0, 10]
  outside `ticks`, and every sha256 field a lowercase 64-hex digest;
* every present tick sidecar and the prompt sidecar matches the manifest
  on schema/work_id/probe_id/scenario, `tick_k` matches the capture
  filename, and `trace_sha256`/`scenario_sha256` match the manifest;
* the prompt reference files exist and hash-match `manifest.prompt`, the
  prompt sidecar is geometrically visible with an OK non-null target box,
  and its filename tick equals `k_star`;
* on the v3 (T1′ parity redirection) schema: `t1prime_protocol == 2`,
  `expected_k_star_p2 == k_star` with no leftover `expected_k_star`, the
  committed selection artifact's hash bound in both the manifest and the
  `prompt_eligibility` echo, `k*'` the smallest eligible warmup tick in
  that echo, both bands computed type-7 over all `|D|` members, the
  capture's own V=1 count equal to the committed `|D|` assertion, and the
  full F20 identity block present (echoed into the artifact as
  `capture_identity`, with `manifest_sha256`).

Frozen 7-step disposition chain — evaluated IN ORDER, first hit decides:

1. Weight-hash binding: `config/detector-reanchor.models.json` must load
   through `load_reanchor_config`, and the detector weights, the DINOv2
   weights, the DINOv2 source archive plus its extracted tree and LICENSE
   (same `verify_file`/`verify_extracted_source` helpers the
   `controller/reanchor_models.py` constructors use), and both
   `config/nanotrack-v2.models.json` ONNX files (plain sha256 vs the
   spec's `sha256` fields; no cv2-tracker code is imported for this) must
   byte-match. Any mismatch or exception -> tool_state `FAIL`
   (`FAIL_WEIGHT_HASH`), no recall, stop.
2. Completeness: any pre-registered tick with `geometrically_visible ==
   true` (V=1) that is missing its image or truth sidecar -> tool_state
   `PROBE_INCOMPLETE` (FAIL class), all offending ticks listed, no
   recall. A tick whose sidecar is absent cannot be proven geometrically
   invisible, so fail-closed it counts as an incompleteness offense.
3. Fidelity: on a v3 capture the `target_appearance` block must equal
   `TARGET_APPEARANCE_CONTRACT` field for field; any difference ->
   `PROBE_FIDELITY_CONTRADICTION` (`TARGET_APPEARANCE_MISMATCH`), stop.
   Then, for every schema, any V=1 tick whose truth box is unprojectable
   (`TARGET_VISIBLE_UNPROJECTABLE`, or V=1 with a null box) -> tool_state
   `PROBE_FIDELITY_CONTRADICTION` (FAIL class), stop.
4. Sample floors: target samples (V=1 ticks) < 40 or distractor samples
   (box_status `OK` with non-null box across V=1 ticks) < 40 ->
   `INCONCLUSIVE`, both counts recorded, stop.
5. Strict recall = hits / target samples, hit = max IoU over proposals
   with confidence >= 0.25 vs the tick's truth box >= 0.30.
   recall < 0.85 -> `FAIL`.
6. recall in [0.85, 0.90) -> `INCONCLUSIVE`.
7. recall >= 0.90 -> `AWAITING_EMBEDDING_FEASIBILITY_REVIEW`.

The tool NEVER emits `PASS`. The final gate state is owned by the
Acceptance role: `gate_state` is always null and `gate_state_owner` is
`"acceptance"`. Embedding/margin evidence is REPORT-ONLY and is computed
whenever step >= 5 is reached (i.e. recall was computed): per-frame
target cosine against the prompt reference embedding, per-frame max
distractor cosine, per-frame margin, the fraction of frames satisfying
`target_cos >= 0.5 AND margin >= 0.1`, and type-7 quantile summaries
(p05/p25/median/p75/p95) of each distribution.

Detection flow: `YoloeProposer(load_reanchor_config(REANCHOR_CONFIG))`,
`initialize` once on the prompt acquisition frame, `propose` per tick;
`DinoV2Embedder` reference embedding from the prompt crop, per-crop
cosines via `_cosine_or_none`. Real models are constructed lazily only
when the chain reaches step 5, and never when `proposer=`/`embedder=`
are injected (tests).

Weight-binding verification seam (step 1): `verify_weight_binding` takes
an injectable reanchor config path, an injectable nanotrack spec path,
and a `resolver` mapping the configs' project-relative weight paths to
filesystem paths (default: `_resolve_project_path`). Tests redirect
individual weight files to tampered copies through this seam, so the
FAIL_WEIGHT_HASH path is exercisable without touching the pinned
weights.

Import safety: torch/ultralytics stay deferred inside the
`controller/reanchor_models.py` constructors, so this module imports
under the cv2+numpy-only track venv.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
from typing import Any, Callable, Mapping, Sequence

from controller.rate3_decision import quantile_type7
from controller.reanchor import (
    ReanchorConfig,
    _resolve_project_path,
    load_reanchor_config,
    verify_file,
)
from controller.reanchor_models import (
    DinoV2Embedder,
    YoloeProposer,
    verify_extracted_source,
)
from tools.run_detector_scouting import (
    DETECTOR_CONFIDENCE_MIN,
    DETECTOR_IOU_MIN,
    REANCHOR_CONFIG,
    REID_MARGIN,
    REID_THRESHOLD,
    _cosine_or_none,
    _read_image,
    _read_object,
    intersection_over_union,
    normalize_box,
    sha256_file,
)

WORK_ID = "P1-SCENE-006"
MANIFEST_SCHEMA = "p1-scene-006-probe-manifest/v1"
CANDIDATE_MANIFEST_SCHEMA = "p1-scene-006-probe-manifest/v2"
CANDIDATE_MANIFEST_SCHEMA_P2 = "p1-scene-006-probe-manifest/v3"
TRUTH_SCHEMA = "p1-scene-006-probe-truth/v1"
RESULT_SCHEMA = "p1-scene-006-probe-result/v1"
NANOTRACK_SPEC_SCHEMA = "tethered-tracker-models/v1"

T1PRIME_PROTOCOL_P2 = 2

# BC-P2-9: the only tolerance in the appearance contract, per RGBA
# component and absolute. `Material.color` does not round-trip exactly in a
# Linear-colour-space project (writing 0.12 reads back 0.119999953), so an
# exact comparison against the author-frozen literal is unachievable through
# the frozen material path. Observed representation error is about 4.4e-8;
# any real repaint is orders of magnitude outside this bound. No relative
# tolerance, no rounding, no composite norm, and the expected values below
# stay the author's contract rather than a read-back. Every other field --
# mesh, shader, role, TRS -- stays exact.
COLOR_COMPONENT_TOLERANCE = 1e-6
COLOR_FIELDS = ("color_r", "color_g", "color_b", "color_a")

# Oracle copy 4/4 (§3.1.4a): the frozen target-visual appearance, restated
# here as independent constants in the author's own decimals — the same
# numbers the production factory's C# literals carry, never a value read
# back from the manifest, the config or the factory. TRS is compared after
# the single-precision quantization Unity applied (`_float32`); only RGBA
# carries the representation tolerance above. A repaint or resize on the
# production side that is not mirrored here turns the probe into
# PROBE_FIDELITY_CONTRADICTION instead of a recall.
TARGET_APPEARANCE_CONTRACT: tuple[dict[str, Any], ...] = (
    {
        "role": "body",
        "mesh_name": "Cube",
        "shader_name": "Universal Render Pipeline/Lit",
        "local_position": {"x": 0.0, "y": 0.5, "z": 0.0},
        "local_rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "local_scale": {"x": 2.0, "y": 1.0, "z": 4.0},
        "color_r": 0.9,
        "color_g": 0.12,
        "color_b": 0.1,
        "color_a": 1.0,
    },
    {
        "role": "roof",
        "mesh_name": "Cube",
        "shader_name": "Universal Render Pipeline/Lit",
        "local_position": {"x": 0.0, "y": 1.2, "z": -0.2},
        "local_rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "local_scale": {"x": 1.7, "y": 0.7, "z": 2.0},
        "color_r": 0.65,
        "color_g": 0.08,
        "color_b": 0.07,
        "color_a": 1.0,
    },
)

# F20: the identity fields a v3 gate artifact must echo verbatim. A missing
# field or one that disagrees with the manifest is fail-closed — the point
# is that the committed artifact stays checkable after the gitignored
# capture directory is gone.
IDENTITY_ECHO_FIELDS = (
    "capture_commit",
    "tool_commit",
    "git_status_porcelain",
    "frozen_tool_paths",
    "tool_path_zero_diff_verified",
    "scene_file_sha256_before",
    "scene_file_sha256_after",
    "baseline_scenario_sha256",
    "scenario_sha256",
    "trace_sha256",
    "selection_artifact",
    "selection_artifact_sha256",
    "detector_models_config_sha256",
    "tracker_models_config_sha256",
)

EXPECTED_TICKS = tuple(range(15, 541, 5))
TICK_COUNT = 106
K_STAR_MIN = 0
K_STAR_MAX = 10

# Frozen protocol constants. Do not retune after seeing a result.
MINIMUM_TARGET_SAMPLES = 40
MINIMUM_DISTRACTOR_SAMPLES = 40
RECALL_FAIL_MAX = 0.85
RECALL_PROCEED_MIN = 0.90

TARGET_BOX_STATUSES = ("OK", "TARGET_VISIBLE_UNPROJECTABLE", "TARGET_NOT_VISIBLE")
DISTRACTOR_BOX_STATUSES = ("OK", "NOT_IN_FRAME")

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
PROMPT_STEM_PATTERN = re.compile(r"prompt_(\d{6})")


def _reject_non_finite(token: str) -> float:
    """BC-P2-10: `NaN` / `Infinity` are not JSON, so reading one fails."""
    raise ValueError(
        f"non-standard JSON constant {token!r}: unavailable numbers must be "
        "serialized as null"
    )


def read_strict_json(path: Path) -> Any:
    """Parse a file with a strict RFC 8259 reader (no NaN/Infinity).

    Python's default decoder silently accepts the `JsonUtility` dialect, so
    a lenient read is exactly how a bare `NaN` reached a committed artifact
    unnoticed. Every v3 input goes through this.
    """
    return json.loads(
        Path(path).read_text(), parse_constant=_reject_non_finite
    )


def _default_path_resolver(value: Any) -> Path:
    """Map a config's project-relative weight path to a filesystem path."""
    return _resolve_project_path(value, "weight binding path")


def _sha256_field(value: Any, label: str) -> str:
    text = str(value)
    if not SHA256_PATTERN.fullmatch(text):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return text


def verify_weight_binding(
    *,
    reanchor_config_path: Path = REANCHOR_CONFIG,
    nanotrack_config_path: Path | None = None,
    resolver: Callable[[Any], Path] = _default_path_resolver,
) -> tuple[ReanchorConfig, dict[str, Any]]:
    """Prove the pinned detector/appearance/tracker bytes are in place.

    Any failure raises; the caller maps that to `FAIL_WEIGHT_HASH`.
    Returns the loaded reanchor config and the model identity block.
    """
    config = load_reanchor_config(reanchor_config_path)
    detector = config.detector
    verify_file(
        resolver(detector["path"]),
        size_bytes=detector["size_bytes"],
        sha256=detector["sha256"],
        label="YOLOE weights",
    )
    appearance = config.appearance
    source = appearance["source"]
    weights = appearance["weights"]
    archive = resolver(source["archive_path"])
    source_dir = resolver(source["directory"])
    verify_file(
        archive,
        size_bytes=source["archive_size_bytes"],
        sha256=source["archive_sha256"],
        label="DINOv2 source archive",
    )
    verify_extracted_source(archive, source_dir)
    verify_file(
        source_dir / str(source["license_path"]),
        size_bytes=source["license_size_bytes"],
        sha256=source["license_sha256"],
        label="DINOv2 LICENSE",
    )
    verify_file(
        resolver(weights["path"]),
        size_bytes=weights["size_bytes"],
        sha256=weights["sha256"],
        label="DINOv2 weights",
    )
    factory = config.tracker_factory
    spec_path = (
        Path(nanotrack_config_path)
        if nanotrack_config_path is not None
        else resolver(factory["spec"])
    )
    spec = _read_object(spec_path)
    if (
        spec.get("schema_version") != NANOTRACK_SPEC_SCHEMA
        or spec.get("tracker") != "nanotrack-v2"
    ):
        raise ValueError("nanotrack model spec identity mismatch")
    models = spec.get("models")
    if not isinstance(models, Mapping):
        raise ValueError("nanotrack model spec lacks models")
    model_dir = resolver(factory["model_dir"])
    onnx_sha256: dict[str, str] = {}
    for role in ("backbone", "neckhead"):
        entry = models.get(role)
        if not isinstance(entry, Mapping):
            raise ValueError(f"nanotrack model spec lacks models.{role}")
        filename = str(entry.get("filename"))
        if Path(filename).name != filename:
            raise ValueError(f"nanotrack {role} filename must be a bare name")
        expected = _sha256_field(entry.get("sha256"), f"nanotrack {role} sha256")
        path = model_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"nanotrack {role} model is missing: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(
                f"nanotrack {role} SHA-256 mismatch: "
                f"expected {expected}, got {actual}"
            )
        onnx_sha256[role] = actual
    identity = {
        "reanchor_config_path": str(config.path),
        "reanchor_config_sha256": config.sha256,
        "detector_weights_sha256": str(detector["sha256"]),
        "appearance_weights_sha256": str(weights["sha256"]),
        "appearance_source_sha256": str(source["archive_sha256"]),
        "nanotrack_config_path": str(spec_path),
        "nanotrack_config_sha256": sha256_file(spec_path),
        "nanotrack_backbone_sha256": onnx_sha256["backbone"],
        "nanotrack_neckhead_sha256": onnx_sha256["neckhead"],
    }
    return config, identity


def _float32(value: float) -> float:
    """The C# `float` literal above as Unity serializes it.

    The constants stay the author's decimal contract (`1.2`, not
    `1.2000000476837158`) so a reader can check them against the factory
    source; this applies the same single-precision quantization Unity did
    before writing, keeping the TRS comparison exact.
    """
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _within_color_tolerance(field: str, expected: float, actual: float) -> bool:
    """BC-P2-9: RGBA absorbs the Unity colour round-trip, nothing else does."""
    if field not in COLOR_FIELDS:
        return actual == _float32(expected)
    return abs(actual - expected) <= COLOR_COMPONENT_TOLERANCE


def _appearance_differences(manifest: Mapping[str, Any]) -> list[str]:
    """Compare `target_appearance` against the frozen constants.

    Returns every difference (empty when the block matches). A non-empty
    result is the §3.1.4(b) fidelity contradiction: the probe rendered
    something other than the runtime target, so no recall may be reported.

    Exactness by field: mesh, shader and role compare as strings, TRS
    compares exactly after single-precision quantization, and only the four
    RGBA components carry the BC-P2-9 representation tolerance.
    """
    differences: list[str] = []
    block = manifest.get("target_appearance")
    cubes = block.get("cubes") if isinstance(block, Mapping) else None
    if not isinstance(cubes, list) or len(cubes) != len(
        TARGET_APPEARANCE_CONTRACT
    ):
        return [
            "target_appearance.cubes must hold "
            f"{len(TARGET_APPEARANCE_CONTRACT)} entries"
        ]
    for index, expected in enumerate(TARGET_APPEARANCE_CONTRACT):
        actual = cubes[index]
        if not isinstance(actual, Mapping):
            differences.append(f"cube[{index}] is not an object")
            continue
        for key, want in expected.items():
            got = actual.get(key)
            if isinstance(want, Mapping):
                if not isinstance(got, Mapping):
                    differences.append(f"cube[{index}].{key} is not an object")
                    continue
                for axis, axis_value in want.items():
                    actual_axis = got.get(axis)
                    if (
                        not isinstance(actual_axis, (int, float))
                        or isinstance(actual_axis, bool)
                        or float(actual_axis) != _float32(axis_value)
                    ):
                        differences.append(
                            f"cube[{index}].{key}.{axis}: expected "
                            f"{axis_value}, got {actual_axis}"
                        )
                continue
            if isinstance(want, float):
                if (
                    not isinstance(got, (int, float))
                    or isinstance(got, bool)
                    or not _within_color_tolerance(key, want, float(got))
                ):
                    differences.append(
                        f"cube[{index}].{key}: expected {want}, got {got}"
                    )
                continue
            if got != want:
                differences.append(
                    f"cube[{index}].{key}: expected {want!r}, got {got!r}"
                )
    return differences


def _identity_echo(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """F20: the self-contained identity block, verified against the manifest.

    Every field must be present and must equal what the manifest carries;
    anything else raises, so the analyzer cannot emit a gate artifact whose
    identity is partial.
    """
    echo: dict[str, Any] = {}
    for field in IDENTITY_ECHO_FIELDS:
        if field not in manifest:
            raise ValueError(f"manifest.{field} is required for the F20 echo")
        echo[field] = manifest[field]
    for field, value in echo.items():
        if value != manifest[field]:
            raise ValueError(f"identity echo diverges from manifest.{field}")
    return echo


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    schema = manifest.get("schema_version")
    if schema not in (
        MANIFEST_SCHEMA,
        CANDIDATE_MANIFEST_SCHEMA,
        CANDIDATE_MANIFEST_SCHEMA_P2,
    ):
        raise ValueError("probe manifest schema mismatch")
    if manifest.get("work_id") != WORK_ID:
        raise ValueError("probe manifest work_id mismatch")
    for key in ("probe_id", "scenario_id"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise ValueError(f"manifest.{key} must be a non-empty string")
    if manifest.get("ticks") != list(EXPECTED_TICKS):
        raise ValueError(
            "manifest ticks differ from the pre-registered [15, 20, ..., 540]"
        )
    tick_count = manifest.get("tick_count")
    if isinstance(tick_count, bool) or tick_count != TICK_COUNT:
        raise ValueError(f"manifest tick_count must be {TICK_COUNT}")
    k_star = manifest.get("k_star")
    if (
        isinstance(k_star, bool)
        or not isinstance(k_star, int)
        or not K_STAR_MIN <= k_star <= K_STAR_MAX
        or k_star in EXPECTED_TICKS
    ):
        raise ValueError("manifest k_star must be an integer in [0, 10] outside ticks")
    for key in ("scenario_sha256", "road_data_sha256", "trace_sha256"):
        _sha256_field(manifest.get(key), f"manifest.{key}")
    prompt = manifest.get("prompt")
    if not isinstance(prompt, Mapping):
        raise ValueError("manifest.prompt must be an object")
    if prompt.get("tick_k") != k_star:
        raise ValueError("manifest.prompt.tick_k must equal k_star")
    for key in ("image_file", "truth_file"):
        if not isinstance(prompt.get(key), str) or not prompt[key]:
            raise ValueError(f"manifest.prompt.{key} must be a non-empty string")
    _sha256_field(prompt.get("image_sha256"), "manifest.prompt.image_sha256")
    _sha256_field(prompt.get("truth_sha256"), "manifest.prompt.truth_sha256")
    if schema in (CANDIDATE_MANIFEST_SCHEMA, CANDIDATE_MANIFEST_SCHEMA_P2):
        # v2/v3 (candidate probes): the BC-B2-5 / F20 binding fields.
        _sha256_field(
            manifest.get("baseline_scenario_sha256"),
            "manifest.baseline_scenario_sha256",
        )
        if (
            not isinstance(manifest.get("candidate_config_path"), str)
            or not manifest["candidate_config_path"]
        ):
            raise ValueError(
                "manifest.candidate_config_path must be a non-empty string"
            )
        if schema == CANDIDATE_MANIFEST_SCHEMA:
            if (
                not isinstance(manifest.get("k_star_binding_artifact"), str)
                or not manifest["k_star_binding_artifact"]
            ):
                raise ValueError(
                    "manifest.k_star_binding_artifact must be a non-empty string"
                )
            expected_k_star = manifest.get("expected_k_star")
            if (
                isinstance(expected_k_star, bool)
                or not isinstance(expected_k_star, int)
                or expected_k_star != k_star
            ):
                raise ValueError(
                    "manifest.expected_k_star must equal the discovered k_star"
                )
            _sha256_field(
                manifest.get("k_star_binding_artifact_sha256"),
                "manifest.k_star_binding_artifact_sha256",
            )
        else:
            _validate_manifest_p2(manifest, k_star)
        for key in ("capture_commit", "tool_commit"):
            value = manifest.get(key)
            if not isinstance(value, str) or not COMMIT_PATTERN.fullmatch(value):
                raise ValueError(f"manifest.{key} must be a 40-hex commit")
        # §5.6 identity: the frozen tool path set the tool_commit was derived
        # over, plus the in-process zero-diff proof over tool..capture.
        frozen_tool_paths = manifest.get("frozen_tool_paths")
        if (
            not isinstance(frozen_tool_paths, list)
            or not frozen_tool_paths
            or any(
                not isinstance(path, str) or not path
                for path in frozen_tool_paths
            )
        ):
            raise ValueError(
                "manifest.frozen_tool_paths must be a non-empty list of paths"
            )
        if manifest.get("tool_path_zero_diff_verified") is not True:
            raise ValueError(
                "manifest.tool_path_zero_diff_verified must be true"
            )
        if manifest.get("git_status_porcelain") != "":
            raise ValueError("manifest.git_status_porcelain must be empty")
        scene_before = _sha256_field(
            manifest.get("scene_file_sha256_before"),
            "manifest.scene_file_sha256_before",
        )
        scene_after = _sha256_field(
            manifest.get("scene_file_sha256_after"),
            "manifest.scene_file_sha256_after",
        )
        if scene_before != scene_after:
            raise ValueError(
                "manifest scene file hash changed during the capture; the "
                "zero-write contract is violated"
            )


def _validate_manifest_p2(manifest: Mapping[str, Any], k_star: int) -> None:
    """v3-only structure: prompt-law v2 binding plus the F20 additions."""
    if manifest.get("t1prime_protocol") != T1PRIME_PROTOCOL_P2:
        raise ValueError(
            f"manifest.t1prime_protocol must be {T1PRIME_PROTOCOL_P2}"
        )
    expected_k_star = manifest.get("expected_k_star_p2")
    if (
        isinstance(expected_k_star, bool)
        or not isinstance(expected_k_star, int)
        or expected_k_star != k_star
    ):
        raise ValueError(
            "manifest.expected_k_star_p2 must equal the rendered k_star"
        )
    if "expected_k_star" in manifest:
        raise ValueError(
            "v3 replaces expected_k_star with expected_k_star_p2; both "
            "present means two prompt bindings"
        )
    if (
        not isinstance(manifest.get("selection_artifact"), str)
        or not manifest["selection_artifact"]
    ):
        raise ValueError("manifest.selection_artifact must be a non-empty string")
    _sha256_field(
        manifest.get("selection_artifact_sha256"),
        "manifest.selection_artifact_sha256",
    )
    for key in ("detector_models_config_sha256", "tracker_models_config_sha256"):
        _sha256_field(manifest.get(key), f"manifest.{key}")

    # A missing or malformed appearance block is a malformed v3 manifest
    # (fail closed, no artifact); a well-formed block whose *values* differ
    # is the step-3 fidelity contradiction.
    appearance = manifest.get("target_appearance")
    cubes = appearance.get("cubes") if isinstance(appearance, Mapping) else None
    if (
        not isinstance(cubes, list)
        or len(cubes) != len(TARGET_APPEARANCE_CONTRACT)
        or any(not isinstance(cube, Mapping) for cube in cubes)
    ):
        raise ValueError(
            "manifest.target_appearance.cubes must describe "
            f"{len(TARGET_APPEARANCE_CONTRACT)} rendered cubes"
        )

    eligibility = manifest.get("prompt_eligibility")
    if not isinstance(eligibility, Mapping):
        raise ValueError("manifest.prompt_eligibility must be an object")
    if eligibility.get("selected_tick") != k_star:
        raise ValueError(
            "prompt_eligibility.selected_tick must equal the rendered k_star"
        )
    if eligibility.get("status") != "SELECTION_OK":
        raise ValueError(
            "prompt_eligibility.status must be SELECTION_OK for a formal run"
        )
    if eligibility.get("selection_artifact_sha256") != manifest[
        "selection_artifact_sha256"
    ]:
        raise ValueError(
            "prompt_eligibility and manifest bind different selection artifacts"
        )
    if eligibility.get("d_v_all_members_box_ok") is not True:
        raise ValueError(
            "prompt_eligibility.d_v_all_members_box_ok must be true; a non-OK "
            "D_V member is a pre-run fidelity contradiction"
        )
    visible_count = eligibility.get("d_v_visible_count")
    if (
        isinstance(visible_count, bool)
        or not isinstance(visible_count, int)
        or visible_count <= 0
    ):
        raise ValueError("prompt_eligibility.d_v_visible_count must be positive")
    if eligibility.get("d_v_denominator_assertion_count") != visible_count:
        raise ValueError(
            "prompt_eligibility denominator assertion disagrees with |D|"
        )
    for key in ("min_side_band", "off_nadir_band"):
        band = eligibility.get(key)
        if not isinstance(band, Mapping):
            raise ValueError(f"prompt_eligibility.{key} must be an object")
        if band.get("computed") is not True:
            raise ValueError(f"prompt_eligibility.{key} must be computed")
        if band.get("quantile_method") != "type-7":
            raise ValueError(f"prompt_eligibility.{key} must be a type-7 band")
        if band.get("count") != visible_count:
            raise ValueError(
                f"prompt_eligibility.{key} must be derived from all |D| members"
            )
    warmup = eligibility.get("warmup_ticks")
    if not isinstance(warmup, list) or not warmup:
        raise ValueError(
            "prompt_eligibility.warmup_ticks must carry the full pool evidence"
        )
    selected = [record for record in warmup if record.get("k") == k_star]
    if len(selected) != 1 or selected[0].get("eligible") is not True:
        raise ValueError(
            "the rendered prompt tick must be the eligible warmup entry"
        )
    for record in warmup:
        if record.get("k") == k_star:
            break
        if record.get("eligible") is True:
            raise ValueError(
                "k*' must be the smallest eligible warmup tick"
            )


def _validate_sidecar(
    value: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    expected_tick_k: int,
    path: Path,
) -> None:
    tick_k = value.get("tick_k")
    if (
        value.get("schema_version") != TRUTH_SCHEMA
        or value.get("work_id") != WORK_ID
        or value.get("probe_id") != manifest.get("probe_id")
        or value.get("scenario_id") != manifest.get("scenario_id")
        or value.get("scenario_sha256") != manifest.get("scenario_sha256")
        or value.get("trace_sha256") != manifest.get("trace_sha256")
        or isinstance(tick_k, bool)
        or tick_k != expected_tick_k
    ):
        raise ValueError(f"{path.name} has mismatched probe truth identity")
    if not isinstance(value.get("geometrically_visible"), bool):
        raise ValueError(f"{path.name} geometrically_visible must be a boolean")
    if value.get("target_box_status") not in TARGET_BOX_STATUSES:
        raise ValueError(f"{path.name} has unknown target_box_status")
    distractors = value.get("distractors")
    if not isinstance(distractors, list):
        raise ValueError(f"{path.name} distractors must be a list")
    for distractor in distractors:
        if (
            not isinstance(distractor, Mapping)
            or distractor.get("box_status") not in DISTRACTOR_BOX_STATUSES
        ):
            raise ValueError(f"{path.name} has invalid distractor truth")


def _probe_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("probe file path escapes the probe root")
    return path


def _prompt_reference(
    root: Path,
    manifest: Mapping[str, Any],
    reader: Callable[[Path], Any] = _read_object,
) -> dict[str, Any]:
    prompt = manifest["prompt"]
    image_path = _probe_file(root, str(prompt["image_file"]))
    truth_path = _probe_file(root, str(prompt["truth_file"]))
    if not image_path.is_file():
        raise ValueError("probe prompt image is missing")
    if sha256_file(image_path) != prompt["image_sha256"]:
        raise ValueError("probe prompt image hash mismatch")
    if not truth_path.is_file():
        raise ValueError("probe prompt truth sidecar is missing")
    if sha256_file(truth_path) != prompt["truth_sha256"]:
        raise ValueError("probe prompt truth hash mismatch")
    stem_match = PROMPT_STEM_PATTERN.fullmatch(image_path.stem)
    if stem_match is None:
        raise ValueError("probe prompt image filename must be prompt_<k*>")
    expected_tick_k = int(stem_match.group(1))
    if expected_tick_k != int(manifest["k_star"]):
        raise ValueError("probe prompt filename tick differs from k_star")
    truth = reader(truth_path)
    _validate_sidecar(
        truth,
        manifest=manifest,
        expected_tick_k=expected_tick_k,
        path=truth_path,
    )
    if not truth["geometrically_visible"]:
        raise ValueError("probe prompt frame must be geometrically visible")
    if truth.get("target_box_status") != "OK":
        raise ValueError("probe prompt frame target box must be OK")
    box = truth.get("target_bbox_xywh_norm")
    if box is None:
        raise ValueError("probe prompt frame must carry a target box")
    normalize_box(box)
    return {"image_path": image_path, "truth_path": truth_path, "truth": truth}


def _scan_ticks(
    root: Path,
    manifest: Mapping[str, Any],
    reader: Callable[[Path], Any] = _read_object,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for tick in EXPECTED_TICKS:
        image_path = root / "frames" / f"frame_{tick:06d}.jpg"
        truth_path = root / "truth" / f"frame_{tick:06d}.json"
        image_present = image_path.is_file()
        truth_present = truth_path.is_file()
        truth = None
        if truth_present:
            truth = reader(truth_path)
            _validate_sidecar(
                truth,
                manifest=manifest,
                expected_tick_k=tick,
                path=truth_path,
            )
        records.append(
            {
                "tick_k": tick,
                "image_file": f"frames/frame_{tick:06d}.jpg",
                "image_path": image_path,
                "image_present": image_present,
                "truth_present": truth_present,
                "geometrically_visible": (
                    bool(truth["geometrically_visible"])
                    if truth is not None
                    else None
                ),
                "truth": truth,
            }
        )
    return records


def _completeness_report(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_inputs: list[dict[str, Any]] = []
    for record in records:
        if not record["truth_present"]:
            missing_inputs.append(
                {"tick_k": record["tick_k"], "missing": "truth_sidecar"}
            )
        elif record["geometrically_visible"] is True and not record["image_present"]:
            missing_inputs.append({"tick_k": record["tick_k"], "missing": "image"})
    return {
        "ticks": [
            {
                "tick_k": record["tick_k"],
                "image_present": record["image_present"],
                "truth_present": record["truth_present"],
                "geometrically_visible": record["geometrically_visible"],
            }
            for record in records
        ],
        "image_present_count": sum(
            1 for record in records if record["image_present"]
        ),
        "truth_present_count": sum(
            1 for record in records if record["truth_present"]
        ),
        "visible_tick_count": sum(
            1 for record in records if record["geometrically_visible"] is True
        ),
        "missing_inputs": missing_inputs,
    }


def _quantile_summary(values: Sequence[float]) -> dict[str, Any]:
    sample = [float(value) for value in values]
    if not sample:
        return {
            "count": 0,
            "p05": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p95": None,
        }
    return {
        "count": len(sample),
        "p05": quantile_type7(sample, 0.05),
        "p25": quantile_type7(sample, 0.25),
        "median": quantile_type7(sample, 0.5),
        "p75": quantile_type7(sample, 0.75),
        "p95": quantile_type7(sample, 0.95),
    }


def run_probe(
    probe_root: Path,
    *,
    proposer: Any | None = None,
    embedder: Any | None = None,
    reanchor_config_path: Path = REANCHOR_CONFIG,
    nanotrack_config_path: Path | None = None,
    path_resolver: Callable[[Any], Path] | None = None,
) -> dict[str, Any]:
    root = Path(probe_root).resolve()
    if not root.is_dir():
        raise ValueError(f"probe root {root} does not exist")
    manifest_path = root / "manifest.json"
    # The manifest is always read strictly: no schema has ever needed a
    # non-finite number, so a `NaN` here is a defect, not a value.
    manifest = read_strict_json(manifest_path)
    _validate_manifest(manifest)
    manifest_sha256 = sha256_file(manifest_path)
    is_p2 = manifest["schema_version"] == CANDIDATE_MANIFEST_SCHEMA_P2
    identity_echo: dict[str, Any] | None = None
    appearance_differences: list[str] = []
    if is_p2:
        identity_echo = _identity_echo(manifest)
        identity_echo["manifest_sha256"] = manifest_sha256
        appearance_differences = _appearance_differences(manifest)
    # v3 captures are written by the strict boundary, so their sidecars are
    # read strictly too. The retired v1/v2 captures are preserved read-only
    # with `NaN` sidecars and stay analyzable through the lenient reader.
    reader = read_strict_json if is_p2 else _read_object
    prompt = _prompt_reference(root, manifest, reader=reader)
    records = _scan_ticks(root, manifest, reader=reader)
    completeness = _completeness_report(records)
    visible_records = [
        record for record in records if record["geometrically_visible"] is True
    ]
    sample_counts = {
        "target_samples": len(visible_records),
        "distractor_samples": sum(
            1
            for record in visible_records
            for distractor in record["truth"]["distractors"]
            if distractor.get("box_status") == "OK"
            and distractor.get("bbox_xywh_norm") is not None
        ),
    }
    if is_p2:
        # §3.2.2: the committed |D| assertion is re-verified against the
        # capture's own V=1 count, so a selection artifact bound to a
        # different domain cannot reach the recall step.
        committed_denominator = manifest["prompt_eligibility"][
            "d_v_visible_count"
        ]
        if sample_counts["target_samples"] != committed_denominator:
            raise ValueError(
                "the capture's V=1 target sample count "
                f"({sample_counts['target_samples']}) does not match the "
                f"committed |D| assertion ({committed_denominator})"
            )
    contradictions = [
        {
            "tick_k": record["tick_k"],
            "target_box_status": record["truth"].get("target_box_status"),
        }
        for record in visible_records
        if record["truth"]["target_box_status"] == "TARGET_VISIBLE_UNPROJECTABLE"
        or record["truth"].get("target_bbox_xywh_norm") is None
    ]

    probe_echo = {
        "manifest_sha256": manifest_sha256,
        "probe_id": manifest["probe_id"],
        "scenario_id": manifest["scenario_id"],
        "scenario_sha256": manifest["scenario_sha256"],
        "road_data_sha256": manifest["road_data_sha256"],
        "trace_sha256": manifest["trace_sha256"],
        "tick_count": TICK_COUNT,
        "k_star": manifest["k_star"],
        "s_init": manifest.get("s_init"),
        "optics": {
            "vertical_fov_deg": manifest.get("vertical_fov_deg"),
            "image_width": manifest.get("image_width"),
            "image_height": manifest.get("image_height"),
            "jpeg_quality": manifest.get("jpeg_quality"),
        },
        "prompt": {
            "tick_k": manifest["prompt"]["tick_k"],
            "image_file": manifest["prompt"]["image_file"],
            "truth_file": manifest["prompt"]["truth_file"],
            "image_sha256": manifest["prompt"]["image_sha256"],
            "truth_sha256": manifest["prompt"]["truth_sha256"],
        },
        "pairing_rule": manifest.get("pairing_rule"),
        "weights_binding_detector_config": manifest.get(
            "weights_binding_detector_config"
        ),
        "weights_binding_tracker_config": manifest.get(
            "weights_binding_tracker_config"
        ),
        "created_by": manifest.get("created_by"),
    }
    frozen_protocol = {
        "detector_confidence_min": DETECTOR_CONFIDENCE_MIN,
        "detector_iou_min": DETECTOR_IOU_MIN,
        "reid_threshold": REID_THRESHOLD,
        "reid_margin": REID_MARGIN,
        "minimum_target_samples": MINIMUM_TARGET_SAMPLES,
        "minimum_distractor_samples": MINIMUM_DISTRACTOR_SAMPLES,
        "recall_fail_max": RECALL_FAIL_MAX,
        "recall_proceed_min": RECALL_PROCEED_MIN,
        "registered_tick_count": TICK_COUNT,
    }

    def result(
        tool_state: str,
        fail_reason: str | None,
        *,
        model_identity: dict[str, Any] | None = None,
        weight_verification: dict[str, Any],
        recall: dict[str, Any] | None = None,
        embedding: dict[str, Any] | None = None,
        samples: Sequence[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        return {
            "schema_version": RESULT_SCHEMA,
            "work_id": WORK_ID,
            "tool_state": tool_state,
            "fail_reason": fail_reason,
            "gate_state": None,
            "gate_state_owner": "acceptance",
            "probe": probe_echo,
            "capture_identity": identity_echo,
            "prompt_eligibility": manifest.get("prompt_eligibility"),
            "target_appearance": manifest.get("target_appearance"),
            "target_appearance_differences": appearance_differences,
            "model_identity": model_identity,
            "weight_verification": weight_verification,
            "frozen_protocol": frozen_protocol,
            "completeness": completeness,
            "sample_counts": sample_counts,
            "fidelity_contradictions": contradictions,
            "recall": recall,
            "embedding": embedding,
            "samples": list(samples),
        }

    # Step 1 — weight-hash binding.
    resolver = path_resolver or _default_path_resolver
    try:
        config, model_identity = verify_weight_binding(
            reanchor_config_path=reanchor_config_path,
            nanotrack_config_path=nanotrack_config_path,
            resolver=resolver,
        )
    except Exception as exception:
        return result(
            "FAIL",
            "FAIL_WEIGHT_HASH",
            weight_verification={
                "verified": False,
                "error": f"{type(exception).__name__}: {exception}",
            },
        )
    weight_verification = {"verified": True, "error": None}

    # Step 2 — completeness over the V=1 ticks (full scan already done).
    if completeness["missing_inputs"]:
        return result(
            "PROBE_INCOMPLETE",
            "MISSING_TICK_IMAGE_OR_TRUTH",
            model_identity=model_identity,
            weight_verification=weight_verification,
        )

    # Step 3 — fidelity contradiction. The appearance block comes first:
    # if the rendered target is not the runtime target, no per-tick number
    # in this capture means anything (§3.1.4b).
    if appearance_differences:
        return result(
            "PROBE_FIDELITY_CONTRADICTION",
            "TARGET_APPEARANCE_MISMATCH",
            model_identity=model_identity,
            weight_verification=weight_verification,
        )
    if contradictions:
        return result(
            "PROBE_FIDELITY_CONTRADICTION",
            "VISIBLE_TICK_UNPROJECTABLE",
            model_identity=model_identity,
            weight_verification=weight_verification,
        )

    # Step 4 — sample floors.
    if (
        sample_counts["target_samples"] < MINIMUM_TARGET_SAMPLES
        or sample_counts["distractor_samples"] < MINIMUM_DISTRACTOR_SAMPLES
    ):
        return result(
            "INCONCLUSIVE",
            "INSUFFICIENT_TARGET_OR_DISTRACTOR_SAMPLES",
            model_identity=model_identity,
            weight_verification=weight_verification,
        )

    # Steps 5–7 — strict recall plus report-only embedding evidence.
    if proposer is None:
        proposer = YoloeProposer(config)
    if embedder is None:
        embedder = DinoV2Embedder(config)
    prompt_image = _read_image(prompt["image_path"])
    prompt_box = normalize_box(prompt["truth"]["target_bbox_xywh_norm"])
    proposer.initialize(prompt_image, prompt_box)
    reference_embedding = embedder.embed(prompt_image, prompt_box)

    samples: list[dict[str, Any]] = []
    target_cosines: list[float] = []
    max_distractor_cosines: list[float] = []
    margins: list[float] = []
    evaluable_frames = 0
    passing_frames = 0
    hits = 0
    for record in visible_records:
        truth = record["truth"]
        image = _read_image(record["image_path"])
        target_box = normalize_box(truth["target_bbox_xywh_norm"])
        batch = proposer.propose(image)
        proposal_ious = [
            intersection_over_union(box, target_box)
            for box, confidence in zip(batch.boxes_norm, batch.confidences)
            if float(confidence) >= DETECTOR_CONFIDENCE_MIN
        ]
        maximum_iou = max(proposal_ious, default=0.0)
        hit = maximum_iou >= DETECTOR_IOU_MIN
        if hit:
            hits += 1

        target_cosine, target_error = _cosine_or_none(
            embedder,
            reference_embedding,
            image,
            truth["target_bbox_xywh_norm"],
        )
        per_distractor: list[dict[str, Any]] = []
        frame_distractor_cosines: list[float] = []
        for distractor in truth["distractors"]:
            if (
                distractor.get("box_status") != "OK"
                or distractor.get("bbox_xywh_norm") is None
            ):
                continue
            cosine, error = _cosine_or_none(
                embedder,
                reference_embedding,
                image,
                distractor["bbox_xywh_norm"],
            )
            per_distractor.append(
                {
                    "distractor_id": distractor.get("distractor_id"),
                    "cosine": cosine,
                    "error": error,
                }
            )
            if cosine is not None:
                frame_distractor_cosines.append(cosine)
        max_distractor_cosine = (
            max(frame_distractor_cosines) if frame_distractor_cosines else None
        )
        margin = (
            target_cosine - max_distractor_cosine
            if target_cosine is not None and max_distractor_cosine is not None
            else None
        )
        if target_cosine is not None:
            target_cosines.append(target_cosine)
        if max_distractor_cosine is not None:
            max_distractor_cosines.append(max_distractor_cosine)
        if margin is not None:
            margins.append(margin)
            evaluable_frames += 1
            if target_cosine >= REID_THRESHOLD and margin >= REID_MARGIN:
                passing_frames += 1

        samples.append(
            {
                "tick_k": record["tick_k"],
                "frame_file": record["image_file"],
                "maximum_target_iou": maximum_iou,
                "recall_hit": hit,
                "target_cosine": target_cosine,
                "target_embedding_error": target_error,
                "distractors": per_distractor,
                "max_distractor_cosine": max_distractor_cosine,
                "margin": margin,
            }
        )

    denominator = len(visible_records)
    recall_value = hits / denominator
    recall = {
        "hits": hits,
        "denominator": denominator,
        "value": recall_value,
        "interpretation": "ORACLE_POINTED_DETECTABILITY_UPPER_BOUND",
        "closed_loop_recall_claimed": False,
    }
    embedding = {
        "report_only": True,
        "reference": "prompt acquisition frame",
        "target_cosine": _quantile_summary(target_cosines),
        "max_distractor_cosine": _quantile_summary(max_distractor_cosines),
        "margin": _quantile_summary(margins),
        "gate_fraction": {
            "evaluable_frames": evaluable_frames,
            "passing_frames": passing_frames,
            "value": (
                passing_frames / evaluable_frames if evaluable_frames else None
            ),
        },
    }
    if recall_value < RECALL_FAIL_MAX:
        tool_state, fail_reason = "FAIL", "RECALL_BELOW_FAIL_MAX"
    elif recall_value < RECALL_PROCEED_MIN:
        tool_state, fail_reason = "INCONCLUSIVE", "RECALL_IN_INCONCLUSIVE_BAND"
    else:
        tool_state, fail_reason = "AWAITING_EMBEDDING_FEASIBILITY_REVIEW", None
    return result(
        tool_state,
        fail_reason,
        model_identity=model_identity,
        weight_verification=weight_verification,
        recall=recall,
        embedding=embedding,
        samples=samples,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="P1-SCENE-006 batch 1 gate T1′ offline detector-probe analyzer."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument(
        "--probe-root",
        required=True,
        help="probe capture directory written by the Unity Editor probe tool",
    )
    analyze.add_argument(
        "--output",
        required=True,
        help="path of the probe result artifact (the only write)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    arguments = build_argument_parser().parse_args(argv)
    if arguments.command == "analyze":
        result = run_probe(Path(arguments.probe_root))
        output = Path(arguments.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        # BC-P2-10: the gate artifact is a committed evidence boundary.
        output.write_text(
            json.dumps(result, indent=1, sort_keys=True, allow_nan=False)
            + "\n"
        )
        line = f"tool_state={result['tool_state']}"
        recall = result["recall"]
        if recall is not None:
            line += (
                f" recall={recall['value']:.6f} "
                f"({recall['hits']}/{recall['denominator']})"
            )
        print(line)
    else:
        raise AssertionError(arguments.command)


if __name__ == "__main__":
    main()
