"""Re-anchor carrier environment preflight (`P1-M3-BODY-001`).

Acceptance round 20 §B.4/§B.5 as reworked by round 21 §B. This is an ordinary
implementation tool: it is deliberately *not* part of `tools/check_*.py`, which
is workflow infrastructure that only a user-authorized coordination batch may
touch.

It proves, in the *current* interpreter, that a `--reanchor-config` tracker run
can actually be constructed before a Play is entered:

  (a) the re-anchor config parses under the strict production schema;
  (b) `cv2`, `torch`, `torchvision` and `ultralytics` expose raw `__version__`
      strings that are **verbatim equal** to their config pins — no
      normalization, no truncation, no `+local` stripping;
  (c) the frozen NanoTrack-v2 backend constructs, which gates the OpenCV
      version and both model SHA-256 values;
  (d) `YoloeProposer` and `DinoV2Embedder` really construct, which verifies
      every local weight, source, archive and LICENSE hash.

It reads no frames, runs no inference, fetches nothing remote, and creates no
run ID, run directory, metric or publication. The last guarantee is enforced
mechanically: `runtime/runs/` direct child names plus the present/absent state,
byte size and SHA-256 of the three publication files and `runtime/metrics.json`
are compared before and after, and any difference fails closed.

On success stdout carries exactly one JSON object and nothing else; dependency
chatter is routed to stderr.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Packages pinned by the re-anchor config's frozen `runtime` block.
CONFIG_RUNTIME_PINS = {
    "torch": "torch_pin",
    "torchvision": "torchvision_pin",
    "ultralytics": "ultralytics_pin",
}

# Files whose bytes must not move during a preflight.
GUARDED_FILES = (
    "runtime/body_command.json",
    "runtime/gimbal_command.json",
    "runtime/tracking_observation.json",
    "runtime/metrics.json",
)
RUNS_ROOT = "runtime/runs"


class PreflightError(RuntimeError):
    """A named, fail-closed preflight failure."""


def _import_module(name: str) -> Any:
    return importlib.import_module(name)


def _qualified_type(value: Any) -> str:
    kind = type(value)
    return f"{kind.__module__}.{kind.__qualname__}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def side_effect_fingerprint(project_root: Path) -> dict[str, Any]:
    """Run-directory names plus present/size/SHA-256 for every guarded file."""
    runs_root = project_root / RUNS_ROOT
    runs = (
        sorted(entry.name for entry in runs_root.iterdir() if entry.is_dir())
        if runs_root.is_dir()
        else []
    )
    files: dict[str, Any] = {}
    for relative in GUARDED_FILES:
        path = project_root / relative
        if path.is_file():
            files[relative] = {
                "present": True,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        else:
            files[relative] = {"present": False, "size_bytes": None, "sha256": None}
    return {"run_directories": runs, "guarded_files": files}


def _describe_fingerprint_delta(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> str:
    reasons: list[str] = []
    if before["run_directories"] != after["run_directories"]:
        created = sorted(set(after["run_directories"]) - set(before["run_directories"]))
        removed = sorted(set(before["run_directories"]) - set(after["run_directories"]))
        if created:
            reasons.append(f"run directories created: {created}")
        if removed:
            reasons.append(f"run directories removed: {removed}")
    for relative in GUARDED_FILES:
        old = before["guarded_files"][relative]
        new = after["guarded_files"][relative]
        if old == new:
            continue
        if old["present"] and not new["present"]:
            reasons.append(f"{relative} was deleted")
        elif not old["present"] and new["present"]:
            reasons.append(f"{relative} was created")
        elif old["sha256"] != new["sha256"] or old["size_bytes"] != new["size_bytes"]:
            reasons.append(
                f"{relative} changed bytes "
                f"({old['size_bytes']}→{new['size_bytes']}, "
                f"{old['sha256']}→{new['sha256']})"
            )
    return "; ".join(reasons) or "fingerprint changed"


def compare_raw_version(
    package: str,
    module: Any,
    expected_pin: Any,
    pin_source: str,
) -> dict[str, str]:
    """Require the module's raw `__version__` to equal the pin verbatim.

    Round 21 §B.3: no normalization, truncation or `+local` stripping, so an
    unfrozen local build such as `2.13.0+cpu` fails against pin `2.13.0`.
    """
    raw = getattr(module, "__version__", None)
    if not isinstance(raw, str) or not raw:
        raise PreflightError(f"package {package!r} exposes no usable __version__")
    if not isinstance(expected_pin, str) or not expected_pin:
        raise PreflightError(f"pin for {package!r} ({pin_source}) is missing or not a string")
    if raw != expected_pin:
        raise PreflightError(
            f"package {package!r} raw __version__ {raw!r} is not verbatim equal to "
            f"the pinned {pin_source} {expected_pin!r}"
        )
    return {"raw": raw, "pin": expected_pin, "pin_source": pin_source}


def _default_config_loader(path: Path) -> Any:
    from controller.reanchor import load_reanchor_config

    return load_reanchor_config(path)


def _default_spec_loader(path: Path) -> Mapping[str, Any]:
    from controller.trackers import load_nanotrack_v2_spec

    return load_nanotrack_v2_spec(path)


def _default_nanotrack_factory(spec_path: Path, model_dir: Path) -> Any:
    from controller.trackers import NanoTrackV2Tracker

    return NanoTrackV2Tracker(spec_path=spec_path, model_dir=model_dir)


def _default_yoloe_factory(config: Any) -> Any:
    from controller.reanchor_models import YoloeProposer

    return YoloeProposer(config)


def _default_dinov2_factory(config: Any) -> Any:
    from controller.reanchor_models import DinoV2Embedder

    return DinoV2Embedder(config)


def _construct(
    config_path: Path,
    *,
    project_root: Path,
    importer: Callable[[str], Any],
    config_loader: Callable[[Path], Any],
    spec_loader: Callable[[Path], Mapping[str, Any]],
    nanotrack_factory: Callable[[Path, Path], Any],
    yoloe_factory: Callable[[Any], Any],
    dinov2_factory: Callable[[Any], Any],
) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        raise PreflightError(f"re-anchor config {path} does not exist")

    # (a) strict production schema, including the frozen runtime pin block.
    try:
        config = config_loader(path)
    except Exception as exception:
        raise PreflightError(
            f"re-anchor config {path} failed strict parsing "
            f"({type(exception).__name__}: {exception})"
        ) from exception

    runtime_pins = config.raw["runtime"]
    factory = config.tracker_factory
    spec_path = project_root / str(factory["spec"])
    model_dir = project_root / str(factory["model_dir"])

    # cv2's only config pin that can equal a raw `__version__` is the
    # NanoTrack spec's `opencv.tested_version`; `opencv.package_pin` is a
    # requirement specifier ("opencv-contrib-python==5.0.0.93") and can never
    # equal `cv2.__version__`. Disclosed reading of round 21 §B.3.
    try:
        spec = spec_loader(spec_path)
    except Exception as exception:
        raise PreflightError(
            f"NanoTrack spec {spec_path} failed strict parsing "
            f"({type(exception).__name__}: {exception})"
        ) from exception
    opencv_pin = spec["opencv"]["tested_version"]

    # (b) verbatim raw version equality for all four packages.
    packages: dict[str, dict[str, str]] = {}
    for package, pin, source in (
        ("cv2", opencv_pin, "nanotrack spec opencv.tested_version"),
        *(
            (name, runtime_pins.get(key), f"reanchor config runtime.{key}")
            for name, key in CONFIG_RUNTIME_PINS.items()
        ),
    ):
        try:
            module = importer(package)
        except Exception as exception:
            raise PreflightError(
                f"package {package!r} could not be imported in this interpreter "
                f"({type(exception).__name__}: {exception}); "
                f"the re-anchor carrier cannot be constructed here"
            ) from exception
        packages[package] = compare_raw_version(package, module, pin, source)

    # (c) frozen NanoTrack-v2: OpenCV gate plus both model SHA-256 values.
    try:
        nanotrack = nanotrack_factory(spec_path, model_dir)
    except Exception as exception:
        raise PreflightError(
            f"NanoTrack-v2 backend construction failed "
            f"({type(exception).__name__}: {exception})"
        ) from exception
    identity = dict(nanotrack.manifest_identity())
    if identity.get("name") != factory["name"]:
        raise PreflightError(
            f"NanoTrack identity {identity.get('name')!r} does not match "
            f"tracker_factory.name {factory['name']!r}"
        )
    model_hashes = identity.get("model_sha256")
    if not isinstance(model_hashes, Mapping) or set(model_hashes) != {
        "backbone",
        "neckhead",
    }:
        raise PreflightError(
            "NanoTrack identity does not carry both backbone and neckhead SHA-256 values"
        )

    # (d) real construction of both re-anchor models.
    try:
        proposer = yoloe_factory(config)
    except Exception as exception:
        raise PreflightError(
            f"YoloeProposer construction failed "
            f"({type(exception).__name__}: {exception})"
        ) from exception
    try:
        embedder = dinov2_factory(config)
    except Exception as exception:
        raise PreflightError(
            f"DinoV2Embedder construction failed "
            f"({type(exception).__name__}: {exception})"
        ) from exception

    return {
        "config": config,
        "packages": packages,
        "identity": identity,
        "model_hashes": dict(model_hashes),
        "constructors": {
            "yoloe_proposer": _qualified_type(proposer),
            "dinov2_embedder": _qualified_type(embedder),
            "nanotrack_tracker": _qualified_type(nanotrack),
        },
        "config_path": path,
    }


def run_preflight(
    config_path: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    importer: Callable[[str], Any] | None = None,
    config_loader: Callable[[Path], Any] | None = None,
    spec_loader: Callable[[Path], Mapping[str, Any]] | None = None,
    nanotrack_factory: Callable[[Path, Path], Any] | None = None,
    yoloe_factory: Callable[[Any], Any] | None = None,
    dinov2_factory: Callable[[Any], Any] | None = None,
) -> dict[str, Any]:
    """Construct the whole re-anchor stack or fail closed with a named reason.

    Collaborators default to the production implementations, resolved at call
    time (not bound at definition time) so a test can substitute them on the
    module and still exercise `main`.
    """
    importer = importer or _import_module
    config_loader = config_loader or _default_config_loader
    spec_loader = spec_loader or _default_spec_loader
    nanotrack_factory = nanotrack_factory or _default_nanotrack_factory
    yoloe_factory = yoloe_factory or _default_yoloe_factory
    dinov2_factory = dinov2_factory or _default_dinov2_factory

    before = side_effect_fingerprint(project_root)

    # Dependency imports print to stdout (ultralytics/PIL emit e.g.
    # "Could not import `tifffile`"). stdout is this tool's machine-readable
    # channel, so construction runs with stdout pointed at stderr.
    #
    # A loader or factory can mutate protected runtime state and *then* raise.
    # The after-fingerprint therefore runs exactly once on both the success and
    # the failure path (round 22 §C.1): a construction error must never let a
    # polluted site go unreported.
    built: dict[str, Any] | None = None
    primary: BaseException | None = None
    try:
        with contextlib.redirect_stdout(sys.stderr):
            built = _construct(
                config_path,
                project_root=project_root,
                importer=importer,
                config_loader=config_loader,
                spec_loader=spec_loader,
                nanotrack_factory=nanotrack_factory,
                yoloe_factory=yoloe_factory,
                dinov2_factory=dinov2_factory,
            )
    except Exception as exception:
        primary = exception

    after = side_effect_fingerprint(project_root)
    if after != before:
        # The site is reported as-is; nothing is deleted or written back to
        # hide it (round 22 §C.2).
        message = (
            "preflight changed protected runtime state — it must create no run "
            f"ID, run directory, metric or publication: "
            f"{_describe_fingerprint_delta(before, after)}"
        )
        if primary is not None:
            message += (
                f"; construction also failed and is retained as secondary "
                f"context ({type(primary).__name__}: {primary})"
            )
        raise PreflightError(message) from primary
    if primary is not None:
        raise primary

    assert built is not None  # no primary exception implies a built stack
    config = built["config"]
    identity = built["identity"]
    return {
        "mode": "reanchor-preflight",
        "status": "PASS",
        "interpreter": {
            "executable": sys.executable,
            "prefix": str(Path(sys.prefix).resolve()),
            "python_version": sys.version.split()[0],
        },
        "packages": built["packages"],
        "reanchor_config": {
            "path": str(built["config_path"]),
            "sha256": config.sha256,
            "schema_version": config.raw["schema_version"],
            "carrier": config.raw["carrier"],
            "device": config.raw["runtime"]["device"],
        },
        "nanotrack": {
            "name": identity.get("name"),
            "backend": identity.get("backend"),
            "opencv_version": identity.get("opencv_version"),
            "opencv_package_pin": identity.get("opencv_package_pin"),
            "preprocessing_id": identity.get("preprocessing_id"),
            "model_sha256": built["model_hashes"],
        },
        "constructors": built["constructors"],
        "side_effect_identity": {
            "checked": [
                "runtime/runs direct child directory names",
                *(f"{relative} present/size/sha256" for relative in GUARDED_FILES),
            ],
            "unchanged": True,
            "before": before,
            "after": after,
        },
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prove the re-anchor carrier can be constructed in this interpreter "
            "before a Play is entered. Creates no run ID, directory, metric or "
            "publication."
        )
    )
    parser.add_argument(
        "--reanchor-config",
        type=Path,
        metavar="PATH",
        required=True,
        help="the frozen re-anchor config to preflight",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        report = run_preflight(args.reanchor_config)
    except PreflightError as exception:
        print(
            json.dumps(
                {
                    "mode": "reanchor-preflight",
                    "status": "FAIL",
                    "reason": str(exception),
                    "interpreter": {
                        "executable": sys.executable,
                        "prefix": str(Path(sys.prefix).resolve()),
                    },
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
