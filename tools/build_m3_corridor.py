#!/usr/bin/env python3
"""P1-M3-BODY-001 batch 1a-alpha: the frozen tether-corridor prism artifact.

BC-BODY1-4 keeps the section 3.5 corridor check but puts it under artifact
discipline. The artifact is the world-frame AABB prism set of the scene
obstacle instances that match a ``config/road_data.json`` footprint type - the
road-audit basis, 779 instances - built **offline** here from the Editor-side
scene geometry evidence, versioned, and pinned by SHA-256 in
``config/p1-m3-body-001.json``. At run time the planner loads this file and
nothing else, and the only query it may ask is "does the anchor -> candidate
body position segment intersect a prism", plus the section 3.5 shorten/hold
rule.

Two disciplines this file exists to make checkable:

* **Provenance.** The prisms are not re-derived here from the scene; they are
  copied from the road-audit basis published by
  ``P1M3BodySceneGeometry``, whose own traversal throws on any root the road
  audit would not have classified. ``--check`` rebuilds and compares, so a
  hand-edited corridor file fails closed.
* **Single use.** BC-BODY1-4 forbids any visibility/occlusion prediction,
  estimator or measurement-window logic in batch 1 from reading this
  artifact. That is why tool 2 reads the scene geometry evidence directly and
  never this file: the corridor artifact is the runtime side's only static
  geometry input and carries exactly one permitted query.

CLI:
    python3 tools/build_m3_corridor.py            # write the artifact
    python3 tools/build_m3_corridor.py --check    # verify, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACT_SCHEMA = "p1-m3-body-001-corridor-prisms/v1"
SCENE_GEOMETRY_SCHEMA = "p1-m3-body-001-scene-geometry/v1"
WORK_ID = "P1-M3-BODY-001"

SCENE_GEOMETRY_PATH = (
    PROJECT_ROOT / "docs" / "evidence" / "P1-M3-BODY-001-scene-geometry.json"
)
CORRIDOR_PATH = PROJECT_ROOT / "config" / "p1-m3-body-001-corridor-prisms.json"
ROAD_DATA_PATH = PROJECT_ROOT / "config" / "road_data.json"
SCENARIO_PATH = PROJECT_ROOT / "config" / "scenario.default.json"

# BC-BODY1-4 names "the 782 instance set". That number is the
# `audited_obstacle_count` of `runtime/road_scene_audit.json`, which was
# produced under `config/scenario.p1-scene-004.json`; it also happens to equal
# the count of the *unadjusted* authored scene. Neither is the basis for this
# batch's carrier: `config/scenario.default.json` moves three vehicles off the
# route and deletes three more, so its own road audit reports **779**. Three
# of the six are among the heaviest occluders on the circuit, so carrying the
# unadjusted set would freeze a corridor artifact describing a scene the
# simulation never runs.
#
# The basis is therefore certified against the road audit the Editor query
# runs in the same traversal, not against a literal. The 782/779 conflict is
# reported to Acceptance rather than resolved here (the implementation role
# does not reinterpret a binding clarification), and this builder fails closed
# if the two counts ever disagree.
BC_BODY1_4_QUOTED_INSTANCE_COUNT = 782


class BuildFailure(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BuildFailure(message)


def build_corridor(
    scene_geometry_path: Path = SCENE_GEOMETRY_PATH,
) -> dict[str, Any]:
    """Derive the frozen prism artifact from the scene geometry evidence."""
    geometry = _load(scene_geometry_path)
    scenario = _load(SCENARIO_PATH)

    _require(
        geometry.get("schema_version") == SCENE_GEOMETRY_SCHEMA,
        f"scene geometry schema must be {SCENE_GEOMETRY_SCHEMA}",
    )
    _require(geometry.get("work_id") == WORK_ID, "scene geometry work_id is wrong")
    road_sha = sha256_file(ROAD_DATA_PATH)
    _require(
        geometry.get("road_data_sha256") == road_sha == scenario["road_data_sha256"],
        "road_data identity disagrees between the scene geometry, the "
        "scenario and config/road_data.json",
    )
    _require(
        geometry.get("source_scenario_sha256") == sha256_file(SCENARIO_PATH),
        "scene geometry was built from different scenario bytes",
    )

    instances = geometry["instances"]
    _require(
        bool(geometry.get("scene_adjustments_applied")),
        "the scene geometry was harvested before the scenario's vehicle "
        "relocations and removals; the corridor would describe a scene the "
        "simulation never runs",
    )
    _require(
        geometry.get("road_audit_status") == "CLEAR",
        "the road audit for this scenario is not CLEAR",
    )
    _require(
        len(instances)
        == int(geometry["instance_count"])
        == int(geometry["road_audit_obstacle_count"]),
        "the published basis does not match the road audit's own count "
        f"({len(instances)} vs {geometry.get('road_audit_obstacle_count')})",
    )

    prisms = []
    for instance in instances:
        for low, high in (("min_x_m", "max_x_m"), ("min_y_m", "max_y_m"), ("min_z_m", "max_z_m")):
            _require(
                float(instance[low]) <= float(instance[high]),
                f"prism for {instance['scene_object_name']} has inverted bounds",
            )
        prisms.append(
            {
                "scene_object_name": instance["scene_object_name"],
                "canonical_name": instance["canonical_name"],
                "group": instance["group"],
                "min_x_m": float(instance["min_x_m"]),
                "max_x_m": float(instance["max_x_m"]),
                "min_y_m": float(instance["min_y_m"]),
                "max_y_m": float(instance["max_y_m"]),
                "min_z_m": float(instance["min_z_m"]),
                "max_z_m": float(instance["max_z_m"]),
            }
        )
    prisms.sort(key=lambda item: item["scene_object_name"])

    return {
        "schema_version": ARTIFACT_SCHEMA,
        "work_id": WORK_ID,
        "permitted_query": (
            "anchor -> candidate body position segment vs prism intersection, "
            "plus the proposal section 3.5 shorten/hold rule; no visibility "
            "or occlusion prediction (BC-BODY1-4)"
        ),
        "source_scene_geometry_sha256": sha256_file(scene_geometry_path),
        "source_scenario_sha256": sha256_file(SCENARIO_PATH),
        "road_data_sha256": road_sha,
        "basis": (
            "road-audit basis for config/scenario.default.json: active "
            "renderable roots minus road surfaces, after the scenario's "
            "vehicle relocations and removals"
        ),
        "instance_count": len(prisms),
        "road_audit_obstacle_count": int(geometry["road_audit_obstacle_count"]),
        "bc_body1_4_quoted_instance_count": BC_BODY1_4_QUOTED_INSTANCE_COUNT,
        "bc_body1_4_count_conflict": (
            len(prisms) != BC_BODY1_4_QUOTED_INSTANCE_COUNT
        ),
        "prisms": prisms,
    }


def serialize(artifact: Mapping[str, Any]) -> str:
    return json.dumps(artifact, indent=1, sort_keys=True) + "\n"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild and compare against the checked-in artifact; write nothing",
    )
    parser.add_argument("--output", type=Path, default=CORRIDOR_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    try:
        artifact = build_corridor()
    except BuildFailure as failure:
        print(f"corridor build FAILED: {failure}")
        return 1
    payload = serialize(artifact)
    if arguments.check:
        existing = Path(arguments.output)
        if not existing.exists():
            print(f"corridor check FAILED: {existing} does not exist")
            return 1
        if existing.read_text() != payload:
            print("corridor check FAILED: checked-in artifact is not reproducible")
            return 1
        print(
            f"corridor check OK: {artifact['instance_count']} prisms, "
            f"sha256={hashlib.sha256(payload.encode()).hexdigest()}"
        )
        return 0
    Path(arguments.output).write_text(payload)
    print(
        f"corridor artifact written: {artifact['instance_count']} prisms, "
        f"sha256={hashlib.sha256(payload.encode()).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
