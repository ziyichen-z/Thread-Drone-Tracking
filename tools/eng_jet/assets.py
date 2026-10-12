"""AC-11 资产核实、AC-12 板上清单与隔离检查、到板代码束（桌面机运行）。

- 资产核实：使用前逐项核 sha256 与体积（`.pt`、`freeze.json`、`frozen-V.jsonl.gz`、a7 帧逐帧对 JPEG sha 参照；
  参照自复核 R1-3 起为只含 `frame_id`/`sha256` 的派生文件 `docs/evidence/P1-ENG-JET-001-a7-frame-sha256.jsonl.gz`，
  由 `docs/evidence/P1-ENG-FAST-002-dataset-frames.jsonl.gz` 投影，原文件含标签字段、补丁前亦仅投影 sha）；阶段 B 资产（smoke、C2 adapter、base、
  评估集、C2 bf16 预测、GGUF、量化产物）在阶段 A 不读取、不上板，记 `NOT_USED(阶段 B 信封未签)`。
- 代码束：只含板上需要的纯标准库件（`tools/eng_jet/` 与写桥函数 `controller/{__init__,protocol,tracking_entry}.py`），
  逐文件 sha 与总字节计入「到板传输」。
- 板上清单：`find ~/eng-jet -type f` 全量列出；路径与 JSON/JSONL 内容按禁项扫描（gold、`truth/`、索引、
  `target_*`/`state` 字段、数据根其他内容）。
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from typing import Any, Mapping, Sequence

from tools.eng_jet import common

BUNDLE_DIR = common.OUT_DIR / "bundle"
BUNDLE_FILES = (
    "tools/eng_jet/__init__.py",
    "tools/eng_jet/common.py",
    "tools/eng_jet/relay.py",
    "controller/__init__.py",
    "controller/protocol.py",
    "controller/tracking_entry.py",
)
FROZEN_V = common.PROJECT_ROOT / "outputs" / "eng-det" / "dets" / "frozen-V.jsonl.gz"
FROZEN_V_SHA = "783ec7e26b6b33decf6a96c2026fb69987e8571b586637e240f7743ac65a7c41"  # docs/evidence/P1-ENG-ACQ-001-assets.json
FROZEN_V_BYTES = 130702
DATASET_FRAMES = common.EVIDENCE_DIR / "P1-ENG-FAST-002-dataset-frames.jsonl.gz"
SPEC = common.PROJECT_ROOT / "config" / "det-assoc-v1.models.json"

#: 板上禁项（AC-12）：路径片段与 JSON 键。
FORBIDDEN_PATH = re.compile(r"(^|/)(truth|gold|index|catalog|labels?)(/|[-_.]|$)|eval\.jsonl$|smoke\.jsonl$|catalog-index", re.IGNORECASE)
FORBIDDEN_KEY = re.compile(r'"(target_[a-z_]*|state|gold[a-z_]*|truth[a-z_]*|positives)"\s*:')
#: 第三方包树（pip 安装件，来源 = 账本 board_pip 逐轮子 sha）：文件名命中禁项名（如 pip 自带的 `index` 模块）只单列
#: `third_party_name_hits`、不记违规；内容禁键命中仍记违规。
THIRD_PARTY_PREFIX = ("venv/", "sysvenv/")
#: 允许的板上前缀：代码束、运行目录（中继镜像）、日志、结果；S1/S2 容器路径另加 a7 帧、容器 venv、pip 轮子、容器 HOME；
#: 系统栈（K1K3K4补跑B）另加系统 Python venv `sysvenv/`（torch 轮子下载落 `wheels/` 子目录）。
ALLOWED_PREFIX = ("code/", "runtime/", "logs/", "results/", "bundle/", "frames/", "venv/", "wheels/", "home/", "sysvenv/")


def asset(label: str, path: Path, expected_sha: str | None, expected_bytes: int | None, source: str) -> dict[str, Any]:
    record: dict[str, Any] = {"label": label, "path": common.rel_project(path), "source": source}
    if not path.is_file():
        return {**record, "present": False, "match": False}
    sha = common.sha256_file(path)
    size = path.stat().st_size
    match = (expected_sha is None or sha == expected_sha) and (expected_bytes is None or size == expected_bytes)
    return {**record, "present": True, "sha256": sha, "size_bytes": size, "expected_sha256": expected_sha,
            "expected_bytes": expected_bytes, "match": match}


#: AC-11 a7 帧 sha 的纯参照（复核 R1-3）：每行只有 `frame_id`、`sha256` 两键，由 `DATASET_FRAMES` 投影派生
#: （`python -m tools.eng_jet.assets derive-frame-reference`）；参照使用方只读本文件，不再解析含标签字段的原文件整行。
PURE_FRAME_REFERENCE = common.EVIDENCE_DIR / "P1-ENG-JET-001-a7-frame-sha256.jsonl.gz"
PURE_REFERENCE_KEYS = ("frame_id", "sha256")
LEGACY_REFERENCE_NOTE = ("原参照 docs/evidence/P1-ENG-FAST-002-dataset-frames.jsonl.gz 每行含标签类字段（positives、target_visible_flag、"
                         "ignores 等）；补丁前桌面机解析整行后仅投影 frame_id → sha256，不上板、不进插件/控制器/中继负载（复核 R1-3，非泄漏）。"
                         "补丁后参照改为只含 frame_id/sha256 的派生文件，原文件不改")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def project_frame_sha(rows: Any, prefix: str = common.A7_FRAMES_REL) -> dict[str, str]:
    """纯函数：从参照行只投影 a7 帧的 `frame_id → sha256`（其余键一律丢弃）；同一 frame_id 出现不同 sha 即拒绝。"""
    ref: dict[str, str] = {}
    for row in rows:
        frame_id = str(row["frame_id"])
        if f"{prefix}/" not in frame_id:
            continue
        sha = str(row["sha256"])
        if ref.setdefault(frame_id, sha) != sha:
            raise ValueError(f"参照中同一帧 sha 冲突：{frame_id}")
    return ref


def legacy_frame_reference(source: Path = DATASET_FRAMES) -> dict[str, str]:
    """补丁前的参照读法（保留供派生与对照）：逐行解析含标签字段的原文件，只取 sha（见 `LEGACY_REFERENCE_NOTE`）。"""
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        return project_frame_sha(json.loads(line) for line in handle if line.strip())


def pure_reference_bytes(ref: Mapping[str, str]) -> bytes:
    """纯参照文件的确定性字节（gzip mtime=0、无文件名；行按 frame_id 排序；每行只有两键）。"""
    lines = "".join(json.dumps({"frame_id": k, "sha256": ref[k]}, sort_keys=True) + "\n" for k in sorted(ref))
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as handle:
        handle.write(lines.encode("utf-8"))
    return buffer.getvalue()


def load_pure_reference(path: Path = PURE_FRAME_REFERENCE, prefix: str = common.A7_FRAMES_REL) -> dict[str, str]:
    """读纯参照：每行须恰为 `frame_id`/`sha256` 两键、sha 为 64 位小写十六进制、frame_id 在 a7 前缀下；否则拒绝（不静默跳过）。"""
    ref: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or tuple(sorted(row)) != PURE_REFERENCE_KEYS:
                raise ValueError(f"纯参照第 {number} 行键不是 {PURE_REFERENCE_KEYS}：{sorted(row) if isinstance(row, dict) else type(row)}")
            if f"{prefix}/" not in str(row["frame_id"]) or not _SHA256_HEX.match(str(row["sha256"])):
                raise ValueError(f"纯参照第 {number} 行 frame_id/sha256 不合格")
            if ref.setdefault(row["frame_id"], row["sha256"]) != row["sha256"]:
                raise ValueError(f"纯参照中同一帧 sha 冲突：{row['frame_id']}")
    return ref


def derive_pure_reference(source: Path = DATASET_FRAMES, out: Path = PURE_FRAME_REFERENCE) -> dict[str, Any]:
    """由原参照派生纯参照（只读原文件、不改原文件）；记来源 sha、来源行数与投影帧数（工程轨道 §7 数据核验：计数、哈希、来源指针）。"""
    with gzip.open(source, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    ref = project_frame_sha(rows)
    payload = pure_reference_bytes(ref)
    common.atomic_write_bytes(out, payload)
    return {"out": common.rel_project(out), "out_sha256": common.sha256_bytes(payload), "out_bytes": len(payload),
            "frames": len(ref), "projected_keys": list(PURE_REFERENCE_KEYS), "prefix": common.A7_FRAMES_REL,
            "source": common.rel_project(source), "source_sha256": common.sha256_file(source), "source_rows": len(rows),
            "note": LEGACY_REFERENCE_NOTE}


def frame_reference(path: Path = PURE_FRAME_REFERENCE) -> dict[str, str]:
    """AC-11 a7 帧 sha 参照（R1-3 后）：只读纯参照文件。"""
    return load_pure_reference(path)


def verify_frames(count: int, label: str) -> dict[str, Any]:
    ref = frame_reference()
    frames_dir = common.a7_frames_dir()
    ok, bad, missing, total = 0, [], [], 0
    for index in range(count):
        key = f"{common.A7_FRAMES_REL}/{common.frame_name(index, 'jpg')}"
        path = frames_dir / common.frame_name(index, "jpg")
        payload = path.read_bytes()
        total += len(payload)
        if key not in ref:
            missing.append(index)
        elif common.sha256_bytes(payload) == ref[key]:
            ok += 1
        else:
            bad.append(index)
    return {"label": label, "frames_dir": common.rel_project(frames_dir), "frames": count, "sha_match": ok, "sha_mismatch": bad,
            "missing_reference": missing, "jpeg_bytes": total, "reference": common.rel_project(PURE_FRAME_REFERENCE),
            "reference_sha256": common.sha256_file(PURE_FRAME_REFERENCE), "reference_keys": list(PURE_REFERENCE_KEYS),
            "reference_derived_from": common.rel_project(DATASET_FRAMES), "reference_note": LEGACY_REFERENCE_NOTE, "match": ok == count}


def verify_local(sr_frames: int) -> dict[str, Any]:
    spec = common.read_json(SPEC)
    weights = common.PROJECT_ROOT / spec["weights"]["path"]
    freeze = common.PROJECT_ROOT / spec["freeze"]["path"]
    records = [
        asset("detector weights last.pt", weights, spec["weights"]["sha256"], int(spec["weights"]["size_bytes"]),
              "config/det-assoc-v1.models.json weights（事实 3）"),
        asset("freeze.json", freeze, spec["freeze"]["sha256"], None, "config/det-assoc-v1.models.json freeze（事实 3）"),
        asset("frozen-V.jsonl.gz", FROZEN_V, FROZEN_V_SHA, FROZEN_V_BYTES,
              "docs/evidence/P1-ENG-ACQ-001-assets.json（事实 5；10-02 从 Mac mini 只读复制）"),
        asset("det-assoc-v1.models.json", SPEC, None, None, "冻结规格（记录本次 sha，AC-10 要求 config/ diff 为空）"),
    ]
    frames = [verify_frames(321, "a7 帧 0..320（S1 口径：init 帧 0 + 320 帧 update）"),
              verify_frames(sr_frames, f"a7 帧 0..{sr_frames - 1}（SR 回放）")]
    stage_b = ["smoke.jsonl 与其 25 帧", "C2 adapter", "base 各分片", "eval.jsonl / eval.blind.jsonl", "C2 bf16 预测",
               "官方 GGUF + mmproj", "自产量化产物"]
    return {
        "work_id": common.WORK_ID,
        "assets": records,
        "frames": frames,
        "stage_b_assets": [{"label": label, "status": "NOT_USED(阶段 B 信封未签)", "read": False, "uploaded": False} for label in stage_b],
        "all_used_match": all(r["match"] for r in records) and all(f["match"] for f in frames),
    }


def make_bundle() -> dict[str, Any]:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    target = BUNDLE_DIR / "eng-jet-code.tar"
    common.refuse_protected(target)
    files = []
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel in BUNDLE_FILES:
            data = (common.PROJECT_ROOT / rel).read_bytes()
            info = tarfile.TarInfo(rel)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
            files.append({"path": rel, "sha256": common.sha256_bytes(data), "bytes": len(data)})
    common.atomic_write_bytes(target, buffer.getvalue())
    return {"bundle": common.rel_project(target), "sha256": common.sha256_file(target), "bytes": target.stat().st_size, "files": files}


#: S1/S2 到板件（容器路径，提案决策记录「S1/S2 容器栈落实」）：快层线束 + 冻结插件代码 + 冻结规格/freeze/权重 + frozen-V，
#: 以仓库相对路径落在板上 `~/eng-jet/code/`；a7 帧 0..320 只放 JPEG（不带 sidecar），落在 `~/eng-jet/frames/a7/`。
S1S2_CODE_FILES = (
    "tools/eng_jet/__init__.py",
    "tools/eng_jet/common.py",
    "tools/eng_jet/fastlayer_bench.py",
    "controller/__init__.py",
    "controller/det_assoc_tracker.py",
    "controller/pose_gmc.py",
    "controller/reanchor.py",
    "controller/resident_core.py",
    "controller/trackers.py",
    "config/det-assoc-v1.models.json",
    "docs/evidence/P1-ENG-FAST-002-freeze.json",
    "outputs/eng-det/runs/run-1/weights/last.pt",
    "outputs/eng-det/dets/frozen-V.jsonl.gz",
)
S1S2_FRAMES = 321


def make_s1s2_bundle() -> dict[str, Any]:
    """S1/S2 到板件：代码与冻结资产（`code/<仓库相对路径>`）+ a7 帧 0..320 JPEG（`frames/a7/`）。逐文件 sha 与总字节计入「到板传输」。"""
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    target = BUNDLE_DIR / "eng-jet-s1s2.tar"
    common.refuse_protected(target)
    files = []
    buffer = io.BytesIO()
    frames_dir = common.a7_frames_dir()
    entries = [(f"code/{rel}", common.PROJECT_ROOT / rel) for rel in S1S2_CODE_FILES]
    entries += [(f"frames/a7/{common.frame_name(i, 'jpg')}", frames_dir / common.frame_name(i, "jpg")) for i in range(S1S2_FRAMES)]
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for arcname, source in entries:
            data = source.read_bytes()
            info = tarfile.TarInfo(arcname)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
            files.append({"path": arcname, "sha256": common.sha256_bytes(data), "bytes": len(data)})
    common.atomic_write_bytes(target, buffer.getvalue())
    return {"bundle": common.rel_project(target), "sha256": common.sha256_file(target), "bytes": target.stat().st_size,
            "code_files": [f for f in files if f["path"].startswith("code/")],
            "frames": {"count": S1S2_FRAMES, "dir": "frames/a7", "jpeg_bytes": sum(f["bytes"] for f in files if f["path"].startswith("frames/")),
                       "sha256_list_digest": common.sha256_bytes("\n".join(f["sha256"] for f in files if f["path"].startswith("frames/")).encode())}}


#: 系统栈补跑的代码更新件：线束与插件代码（冻结资产 `.pt`/frozen-V/a7 帧已在板上，由 `board-sha` 逐文件复核，不重传）。
S1S2_CODE_UPDATE_FILES = tuple(rel for rel in S1S2_CODE_FILES if not rel.startswith("outputs/"))


def make_s1s2_code_update() -> dict[str, Any]:
    """K1K3K4补跑B 到板件：只含代码/规格/freeze（逐文件 sha），落 `~/eng-jet/code/<仓库相对路径>`；计入「到板传输」。"""
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    target = BUNDLE_DIR / "eng-jet-s1s2-code.tar"
    common.refuse_protected(target)
    files = []
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel in S1S2_CODE_UPDATE_FILES:
            data = (common.PROJECT_ROOT / rel).read_bytes()
            info = tarfile.TarInfo(f"code/{rel}")
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
            files.append({"path": f"code/{rel}", "sha256": common.sha256_bytes(data), "bytes": len(data)})
    common.atomic_write_bytes(target, buffer.getvalue())
    return {"bundle": common.rel_project(target), "sha256": common.sha256_file(target), "bytes": target.stat().st_size, "code_files": files}


#: K1K3K4补跑F（SR (b) 与正式 SR）到板件：中继/应答器线束 + 真实 TrackLoop 及其导入链（`controller/` 原件，零改动）+ 规格；
#: 落 `~/eng-jet/code/<仓库相对路径>`，逐文件 sha 与总字节计入「到板传输」。冻结权重/freeze/引擎已在板上（使用前 sha 复核）。
SR_CODE_FILES = (
    "tools/eng_jet/__init__.py", "tools/eng_jet/common.py", "tools/eng_jet/relay.py", "tools/eng_jet/track_responder.py",
    "tools/eng_jet/fastlayer_bench.py",
    *(f"controller/{name}.py" for name in (
        "__init__", "body_entry", "body_planner", "det_assoc_tracker", "geolocate", "gimbal_entry", "pose_gmc", "protocol",
        "qualification_protocol", "rate2_protocol", "rate3_protocol", "reanchor", "resident_core", "run_log", "scenario_tether",
        "sensor_protocol", "standoff_planner", "track_loop", "trackers", "tracking_entry", "world_estimate")),
    "config/det-assoc-v1.models.json",
)
#: 板上已有、SR (b) 使用前须 sha 复核的冻结件（不重传）。
SR_FROZEN_ON_BOARD = ("outputs/eng-det/runs/run-1/weights/last.pt", "docs/evidence/P1-ENG-FAST-002-freeze.json")


def make_sr_code_update() -> dict[str, Any]:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    target = BUNDLE_DIR / "eng-jet-sr-code-f.tar"
    common.refuse_protected(target)
    files = []
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel in SR_CODE_FILES:
            data = (common.PROJECT_ROOT / rel).read_bytes()
            info = tarfile.TarInfo(f"code/{rel}")
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
            files.append({"path": f"code/{rel}", "sha256": common.sha256_bytes(data), "bytes": len(data)})
    common.atomic_write_bytes(target, buffer.getvalue())
    frozen = [{"path": f"code/{rel}", "sha256": common.sha256_file(common.PROJECT_ROOT / rel)} for rel in SR_FROZEN_ON_BOARD]
    return {"bundle": common.rel_project(target), "sha256": common.sha256_file(target), "bytes": target.stat().st_size, "code_files": files,
            "frozen_on_board": frozen}


def board_sha_check(expected: Sequence[Mapping[str, Any]], host: str = common.BOARD_HOST) -> dict[str, Any]:
    """板上逐文件 sha256 复核（`~/eng-jet/<path>`）：expected = [{path, sha256}]。"""
    paths = " ".join(f"'{e['path']}'" for e in expected)
    out = subprocess.run(["ssh", *common.SSH_OPTS, host, f"cd {common.BOARD_ROOT} && sha256sum {paths}"],
                         capture_output=True, text=True).stdout.splitlines()
    got = {line.split()[1]: line.split()[0] for line in out if len(line.split()) == 2}
    rows = [{"path": e["path"], "expected": e["sha256"], "board": got.get(e["path"]), "match": got.get(e["path"]) == e["sha256"]} for e in expected]
    return {"files": len(rows), "matched": sum(r["match"] for r in rows), "mismatched": [r for r in rows if not r["match"]],
            "all_match": all(r["match"] for r in rows)}


def scan_manifest(lines: Sequence[str], key_hits: Sequence[str]) -> dict[str, Any]:
    """`find -printf '%P\\t%s\\n'` 行 + 内容禁键命中文件 → 违规清单（空 = 满足 AC-12 路径/字段检查）。"""
    files, violations, third_party = [], [], []
    for line in lines:
        if not line.strip():
            continue
        rel, _, size = line.partition("\t")
        files.append({"path": rel, "bytes": int(size) if size.isdigit() else None})
        if FORBIDDEN_PATH.search(rel) and rel.startswith(THIRD_PARTY_PREFIX):
            third_party.append(rel)
        elif FORBIDDEN_PATH.search(rel):
            violations.append({"path": rel, "why": "forbidden_path"})
        elif not rel.startswith(ALLOWED_PREFIX):
            violations.append({"path": rel, "why": "outside_allowed_prefix"})
    for hit in key_hits:
        if hit.strip():
            violations.append({"path": hit.strip(), "why": "forbidden_json_key"})
    return {"files": len(files), "bytes": sum(f["bytes"] or 0 for f in files), "violations": violations,
            "third_party_name_hits": third_party, "listing": files}


def board_manifest(host: str = common.BOARD_HOST) -> dict[str, Any]:
    root = common.BOARD_ROOT
    listing = subprocess.run(["ssh", *common.SSH_OPTS, host, f"cd {root} && find . -type f -printf '%P\\t%s\\n' | sort"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
    keys = subprocess.run(["ssh", *common.SSH_OPTS, host,
                           f"cd {root} && grep -rlE --include='*.json' --include='*.jsonl' "
                           f"'\"(target_[a-z_]*|state|gold[a-z_]*|truth[a-z_]*|positives)\"[[:space:]]*:' . || true"],
                          capture_output=True, text=True, check=True).stdout.splitlines()
    du = subprocess.run(["ssh", *common.SSH_OPTS, host, f"du -sb {root} | cut -f1"], capture_output=True, text=True, check=True).stdout.strip()
    result = scan_manifest(listing, keys)
    result["du_bytes"] = int(du) if du.isdigit() else None
    result["command"] = f"find {root} -type f; grep -rlE <禁键> {root}; du -sb {root}"
    return result


def zero_write_check(since_utc: str) -> dict[str, Any]:
    """主树 `runtime/` 与数据根自 `since_utc` 起零写入：`find <root> -newermt <since>` 计数（mtime 口径；只读不改 mtime）。"""
    out = {"since_utc": since_utc, "roots": []}
    for root in common.PROTECTED_ROOTS:
        if not root.exists():
            out["roots"].append({"root": str(root), "exists": False, "modified": 0})
            continue
        found = subprocess.run(["find", str(root), "-newermt", since_utc], capture_output=True, text=True).stdout.splitlines()
        out["roots"].append({"root": common.rel_project(root), "exists": True, "modified": len(found), "examples": found[:10]})
    out["zero_write"] = all(r["modified"] == 0 for r in out["roots"])
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "bundle", "bundle-s1s2", "bundle-s1s2-code", "bundle-sr", "board-sha", "manifest", "zero-write",
                                           "derive-frame-reference"))
    parser.add_argument("--host", default=common.BOARD_HOST, help="board-sha / manifest 的 ssh 目标（正式 SR：common.WIRED_BOARD_HOST）")
    parser.add_argument("--expected", type=Path, default=None, help="board-sha：含 code_files/files 列表的 JSON（如 bundle-s1s2.json）")
    parser.add_argument("--since-utc", default=None)
    parser.add_argument("--sr-frames", type=int, default=1500)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.action == "verify":
        result = verify_local(args.sr_frames)
    elif args.action == "derive-frame-reference":
        result = derive_pure_reference()
    elif args.action == "bundle":
        result = make_bundle()
    elif args.action == "bundle-s1s2":
        result = make_s1s2_bundle()
    elif args.action == "bundle-s1s2-code":
        result = make_s1s2_code_update()
    elif args.action == "bundle-sr":
        result = make_sr_code_update()
    elif args.action == "board-sha":
        source = common.read_json(args.expected)
        result = board_sha_check(source.get("code_files") or source.get("files"), host=args.host)
    elif args.action == "zero-write":
        result = zero_write_check(args.since_utc)
    else:
        result = board_manifest(host=args.host)
    if args.out:
        common.write_json(args.out, result)
    print(json.dumps({k: v for k, v in result.items() if k != "listing"}, ensure_ascii=False)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
