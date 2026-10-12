"""§5 线 A 执行信封账本（AC-9 / AC-13）：动作前扣额并即时持久化，越界即停。

信封逐字来源：`docs/authorizations.md` 2026-09-27「P1-ENG-FAST-002 — 用户按推荐确认阶段 1
门值与合取映射、AC-12 通过条件四条、§7(h) 本项独立 1 次诊断 Play，并选签 §5 线 A」的
「信封 · 阶段 1（线 A）」。缺项视为 0；成功、失败、重试全部计入同一上限。

账本文件即证据（`docs/evidence/P1-ENG-FAST-002-ledger.json`，只增不减）。模型启动不限次但
逐次记账（上限 None）。训练墙钟按秒计：每次 ≤ 6 h、合计 ≤ 14 h。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as _dt
from pathlib import Path
from typing import Any

from tools.eng_det import common

LEDGER_PATH = common.evidence("ledger.json")
ENVELOPE_SOURCE = (
    "docs/authorizations.md 2026-09-27「P1-ENG-FAST-002 — 用户按推荐确认阶段 1 门值与合取映射、"
    "AC-12 通过条件四条、§7(h) 本项独立 1 次诊断 Play，并选签 §5 线 A」·「信封 · 阶段 1（线 A）」"
)

#: 计数型信封（None = 不限次但逐次记账）。
ENVELOPE: dict[str, int | None] = {
    "download": 1,  # 官方 yolo11n.pt（≈5.6 MB）
    "training_run": 3,
    "h_evaluation": 1,
    "model_start": None,
    "transfer": 0,
    "pip_install": 0,
    "unity_play": 0,
    "scenario_session_run_id": 0,
    "model_api_call": 0,
    "cloud_gpu_hour": 0,
}
TRAINING_RUN_WALL_S = 6 * 3600
TRAINING_TOTAL_WALL_S = 14 * 3600
DISK_CAP_BYTES = 5 * 1024**3


class EnvelopeExceeded(RuntimeError):
    """越界：动作不得执行，回到用户（§5 末句）。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Ledger:
    path: Path = field(default_factory=lambda: LEDGER_PATH)

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            return common.read_json(self.path)
        return {
            "schema_version": "p1-eng-fast-002-ledger/v1",
            "work_id": common.WORK_ID,
            "envelope_source": ENVELOPE_SOURCE,
            "line": "A（Mac .venv-yoloe）",
            "envelope": dict(ENVELOPE),
            "training_run_wall_cap_s": TRAINING_RUN_WALL_S,
            "training_total_wall_cap_s": TRAINING_TOTAL_WALL_S,
            "disk_cap_bytes": DISK_CAP_BYTES,
            "counters": {key: 0 for key in ENVELOPE},
            "training_wall_s_used": 0.0,
            "events": [],
        }

    def save(self, document: dict[str, Any]) -> None:
        common.write_json(self.path, document)

    def charge(self, counter: str, amount: int = 1, **detail: Any) -> dict[str, Any]:
        """扣额在动作之前：先写账本再做事；越界抛 `EnvelopeExceeded` 且不写。"""
        document = self.load()
        if counter not in document["envelope"]:
            raise EnvelopeExceeded(f"{counter}: 信封无此维度（缺项 = 0）")
        cap = document["envelope"][counter]
        used = int(document["counters"].get(counter, 0))
        if cap is not None and used + amount > int(cap):
            raise EnvelopeExceeded(f"{counter}: 已用 {used} + {amount} > 上限 {cap}")
        document["counters"][counter] = used + amount
        document["events"].append({"at": _now(), "counter": counter, "amount": amount, **detail})
        self.save(document)
        return document

    def remaining_training_wall_s(self) -> float:
        document = self.load()
        return min(
            float(document["training_run_wall_cap_s"]),
            float(document["training_total_wall_cap_s"]) - float(document["training_wall_s_used"]),
        )

    def add_training_wall(self, seconds: float, **detail: Any) -> dict[str, Any]:
        document = self.load()
        document["training_wall_s_used"] = round(float(document["training_wall_s_used"]) + float(seconds), 3)
        document["events"].append({"at": _now(), "counter": "note:training_wall_s", "seconds": round(seconds, 3), **detail})
        self.save(document)
        if float(document["training_wall_s_used"]) > float(document["training_total_wall_cap_s"]):
            raise EnvelopeExceeded("训练墙钟合计超过 14 h")
        return document

    def note(self, kind: str, **detail: Any) -> dict[str, Any]:
        document = self.load()
        document["events"].append({"at": _now(), "counter": f"note:{kind}", **detail})
        self.save(document)
        return document

    def used(self, counter: str) -> int:
        return int(self.load()["counters"].get(counter, 0))

    def check_disk(self) -> int:
        used = common.disk_usage_bytes()
        if used > DISK_CAP_BYTES:
            raise EnvelopeExceeded(f"outputs/eng-det/ {used} B > 5 GB")
        return used


def runtime_trees() -> dict[str, Any]:
    """AC-9：两处 `runtime/`（仓库与数据根）全树逐文件哈希清单的总哈希（复用 FAST-001 纯函数）。"""
    from tools.eng_fast import ledger as fast_ledger  # noqa: PLC0415

    result = {}
    for label, root in (("repo_runtime", common.PROJECT_ROOT / "runtime"), ("data_root_runtime", common.DATA_ROOT / "runtime")):
        manifest = fast_ledger.runtime_manifest(root)
        result[label] = {"root": str(root), "files": manifest["files"], "tree_sha256": manifest["tree_sha256"]}
    return result


def main(argv: list[str] | None = None) -> None:
    import argparse  # noqa: PLC0415
    import json  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-FAST-002 账本：runtime 前后哈希")
    parser.add_argument("mode", choices=("baseline", "verify"))
    args = parser.parse_args(argv)
    ledger = Ledger()
    trees = runtime_trees()
    if args.mode == "baseline":
        ledger.note("runtime_trees_before", **trees)
        print(json.dumps(trees, ensure_ascii=False))
        return
    before = [e for e in ledger.load()["events"] if e["counter"] == "note:runtime_trees_before"]
    if not before:
        raise SystemExit("无 baseline 记录")
    same = all(before[-1][k]["tree_sha256"] == trees[k]["tree_sha256"] for k in trees)
    ledger.note("runtime_trees_after", identical=same, **trees)
    print(json.dumps({"identical": same, **trees}, ensure_ascii=False))
    if not same:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
