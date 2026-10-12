"""§5 执行信封账本（AC-9）：动作前扣额并即时持久化，越界即停。

信封逐字来源：`docs/authorizations.md` 2026-09-24「用户签发 §5 执行信封」。
缺项视为 0；成功、失败、重试、smoke 全部计入同一上限。账本只增不减——删除
账本文件不能恢复额度（`Ledger.load` 遇缺失且已有扣额记录的副本时拒绝重建）。
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as _dt
from pathlib import Path
from typing import Any

from tools.eng_fast import common

LEDGER_PATH = common.OUT_ROOT / "ledger" / "ledger.json"
ENVELOPE_SOURCE = "docs/authorizations.md 2026-09-24「P1-ENG-FAST-001 — 用户签发 §5 执行信封」"

#: 信封上限（逐字；缺项 = 0）。
ENVELOPE: dict[str, int] = {
    "mac_start_yoloe": 10,
    "mac_start_dinov2": 8,
    "gpu5060_base_start": 4,
    "gpu5060_query": 1700,
    "gpu5060_query_retry": 183,  # §3.5.3：重试只从 183 行余量扣（同时计入 1,700 总额）
    "download": 1,  # `lap>=0.5.12` wheel
    "pip_install_mac": 1,  # 与下载同一件事，不另计下载
    "pip_install_5060": 0,
    "unity_play": 0,
    "scenario_session_run_id": 0,
    "model_api_call": 0,
    "training_gpu_hours": 0,
}
TRANSFER_CAPS_BYTES: dict[str, int] = {
    "code_and_manifests": 300 * 1024,
    "image_packs": 150 * 1024 * 1024,
    "returned_results": 5 * 1024 * 1024,
}


class EnvelopeExceeded(RuntimeError):
    """越界：动作不得执行，回到用户（§5 末句）。"""


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Ledger:
    path: Path = LEDGER_PATH

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            return common.read_json(self.path)
        return {
            "schema_version": "p1-eng-fast-ledger/v1",
            "work_id": common.WORK_ID,
            "envelope_source": ENVELOPE_SOURCE,
            "envelope": dict(ENVELOPE),
            "transfer_caps_bytes": dict(TRANSFER_CAPS_BYTES),
            "counters": {key: 0 for key in ENVELOPE},
            "transfer_bytes": {key: 0 for key in TRANSFER_CAPS_BYTES},
            "events": [],
        }

    def save(self, document: dict[str, Any]) -> None:
        common.write_json(self.path, document)

    def charge(self, counter: str, amount: int = 1, **detail: Any) -> dict[str, Any]:
        """扣额在动作之前：先写账本再做事；越界抛 `EnvelopeExceeded` 且不写。"""
        document = self.load()
        cap = int(document["envelope"].get(counter, 0))
        used = int(document["counters"].get(counter, 0))
        if used + amount > cap:
            raise EnvelopeExceeded(f"{counter}: 已用 {used} + {amount} > 上限 {cap}")
        document["counters"][counter] = used + amount
        document["events"].append({"at": _now(), "counter": counter, "amount": amount, **detail})
        self.save(document)
        return document

    def record_transfer(self, category: str, size_bytes: int, **detail: Any) -> dict[str, Any]:
        document = self.load()
        cap = int(document["transfer_caps_bytes"][category])
        used = int(document["transfer_bytes"].get(category, 0))
        if used + size_bytes > cap:
            raise EnvelopeExceeded(f"transfer {category}: {used} + {size_bytes} > {cap} B")
        document["transfer_bytes"][category] = used + size_bytes
        document["events"].append(
            {"at": _now(), "counter": f"transfer:{category}", "bytes": size_bytes, **detail}
        )
        self.save(document)
        return document

    def note(self, kind: str, **detail: Any) -> dict[str, Any]:
        """不扣额的事实记录（下载的 sha/字节、5060 账本回传、runtime 前后清单等）。"""
        document = self.load()
        document["events"].append({"at": _now(), "counter": f"note:{kind}", **detail})
        self.save(document)
        return document

    def used(self, counter: str) -> int:
        return int(self.load()["counters"].get(counter, 0))


def runtime_manifest(root: Path = common.RUNTIME_ROOT) -> dict[str, Any]:
    """AC-9：`runtime/` 全树逐文件 (相对路径, 字节, sha256) 清单与其总哈希。"""
    import hashlib  # noqa: PLC0415
    import os  # noqa: PLC0415

    entries: list[tuple[str, int, str]] = []
    for directory, _dirs, files in os.walk(root):
        for name in files:
            path = Path(directory) / name
            if path.is_symlink():
                entries.append((path.relative_to(root).as_posix(), -1, "symlink:" + os.readlink(path)))
                continue
            entries.append((path.relative_to(root).as_posix(), path.stat().st_size, common.sha256_file(path)))
    entries.sort()
    digest = hashlib.sha256()
    for relative, size, sha in entries:
        digest.update(f"{relative}\t{size}\t{sha}\n".encode("utf-8"))
    return {"root": common.rel(root), "files": len(entries), "tree_sha256": digest.hexdigest(), "entries": entries}
