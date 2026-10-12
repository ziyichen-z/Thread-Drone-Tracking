#!/usr/bin/env python3
"""S6 审计协议：三互斥 panel 的有限状态机与判定规则（§2.7，BC-DATA-5）。

本模块只做**协议**：panel 生成、配额分配、通过线计算与 attempt 状态机。
它不渲染叠加图、不调用模型、不代替用户作判定；正式的 A1/A2/A3 人工审计
在当前授权下**未获批准执行**（提案 §15），此处交付的是可复核的机械半边。

BC-DATA-5 要点：A1 的 9 条类别映射是每次 attempt 都重跑的固定穷举
checklist，**不属于**三个互斥随机 panel；其余样本以完整元组为 sample id，
panel-0/1/2 间不得重复；容量降序并列按 stratum key UTF-8 升序，样本并列按
`(hash 原始字节, sample id UTF-8 字节)`；panel 按 0→1→2 从剩余池填充；
确定性转移后仍不足配额 → `AUDIT_PANEL_CAPACITY_INSUFFICIENT`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
from typing import Any, Iterable, Sequence

from tools.dist_data import contract
from tools.dist_data.artifacts import DistDataError

STAGE = 6

AUDITS: tuple[str, ...] = ("A1", "A2", "A3")
VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"


class AuditError(DistDataError):
    """S6 协议违反。"""


class AuditTerminal(DistDataError):
    """§2.7 / BC-DATA-5 的终态（`AUDIT_EXHAUSTED_FAIL` 等）。"""

    def __init__(self, terminal: str, detail: str) -> None:
        super().__init__(f"{terminal}：{detail}")
        self.terminal = terminal
        self.detail = detail


def panel_seed(audit: str, panel: int) -> str:
    if audit not in AUDITS:
        raise AuditError(f"未知审计 {audit!r}")
    if not 0 <= panel < contract.AUDIT_PANEL_COUNT:
        raise AuditError(f"panel 越界：{panel}")
    return contract.AUDIT_SEED_TEMPLATE.format(audit=audit, panel=panel)


def sample_sort_key(audit: str, panel: int, sample_id: str) -> tuple[bytes, bytes]:
    """样本并列判定键 = `(SHA-256(seed ‖ id) 原始字节, sample id UTF-8 字节)`。"""
    digest = hashlib.sha256(
        f"{panel_seed(audit, panel)}/{sample_id}".encode("utf-8")
    ).digest()
    return (digest, sample_id.encode("utf-8"))


def allocate_quota(
    capacities: dict[str, int], *, base: int, total: int
) -> dict[str, int]:
    """分层配额：格内 `base` 起步，不足则全取，余额按格实测容量降序转移。

    并列按冻结的 stratum key UTF-8 字节升序。总额不可达即
    `AUDIT_PANEL_CAPACITY_INSUFFICIENT`（不得缩小分母后作通过判定）。
    """
    allocation = {key: min(base, capacities.get(key, 0)) for key in sorted(capacities)}
    assigned = sum(allocation.values())
    if assigned > total:  # base × 格数超过总额：按同一确定性序回收
        overflow = assigned - total
        for key in sorted(
            capacities, key=lambda item: (-capacities[item], item.encode("utf-8"))
        )[::-1]:
            if overflow <= 0:
                break
            take = min(overflow, allocation[key])
            allocation[key] -= take
            overflow -= take
        return allocation
    remaining = total - assigned
    for key in sorted(capacities, key=lambda item: (-capacities[item], item.encode("utf-8"))):
        if remaining <= 0:
            break
        headroom = capacities[key] - allocation[key]
        take = min(headroom, remaining)
        allocation[key] += take
        remaining -= take
    if remaining > 0:
        raise AuditTerminal(
            "AUDIT_PANEL_CAPACITY_INSUFFICIENT",
            f"确定性转移后仍缺 {remaining} 个样本（目标 {total}，容量 {sum(capacities.values())}）",
        )
    return allocation


def build_panels(
    audit: str,
    stratum_of_sample: dict[str, str],
    *,
    total: int,
    base: int,
    minimum_per_stratum: int = 0,
) -> dict[str, list[str]]:
    """一次性生成三个互斥 panel（S6 开始时冻结，之后才渲染任何叠加图）。"""
    pool = dict(stratum_of_sample)
    panels: dict[str, list[str]] = {}
    for panel in range(contract.AUDIT_PANEL_COUNT):
        capacities: dict[str, int] = {}
        for sample_id, stratum in pool.items():
            capacities[stratum] = capacities.get(stratum, 0) + 1
        if minimum_per_stratum:
            for stratum, capacity in capacities.items():
                if capacity < minimum_per_stratum:
                    raise AuditTerminal(
                        "AUDIT_PANEL_CAPACITY_INSUFFICIENT",
                        f"panel-{panel} 分层 {stratum} 容量 {capacity} < 最低 {minimum_per_stratum}",
                    )
        allocation = allocate_quota(capacities, base=base, total=total)
        chosen: list[str] = []
        for stratum in sorted(allocation):
            quota = allocation[stratum]
            if quota <= 0:
                continue
            members = sorted(
                (sample for sample, key in pool.items() if key == stratum),
                key=lambda sample: sample_sort_key(audit, panel, sample),
            )
            picked = members[:quota]
            chosen.extend(picked)
            for sample in picked:
                pool.pop(sample)
        panels[f"panel-{panel}"] = sorted(chosen)
    overlaps = _panel_overlaps(panels)
    if overlaps:
        raise AuditError(f"panel 互斥性被破坏：{overlaps}")
    return panels


def _panel_overlaps(panels: dict[str, list[str]]) -> list[str]:
    seen: dict[str, str] = {}
    overlaps: list[str] = []
    for name, members in sorted(panels.items()):
        for sample in members:
            if sample in seen:
                overlaps.append(f"{sample}（{seen[sample]} 与 {name}）")
            seen[sample] = name
    return overlaps


# --- 判定规则 -------------------------------------------------------------
def evaluate_a1(
    class_map_failures: int,
    class_crop_results: Sequence[bool],
    instance_color_results: Sequence[bool],
    group_color_rejections: Iterable[str],
) -> dict[str, Any]:
    """A1：映射表 0 失败；类别 crop ≤1；实例颜色 crop ≤1。

    **组级颜色错不是 attempt 失败而是数据结论**：被判错词的组立即永久
    `UNVERIFIED`，不计入 (b)/(c) 的失败条数。
    """
    class_failures = sum(1 for passed in class_crop_results if not passed)
    instance_failures = sum(1 for passed in instance_color_results if not passed)
    reasons: list[str] = []
    if class_map_failures > contract.AUDIT_A1_CLASS_MAP_MAX_FAILURES:
        reasons.append(f"类别映射失败 {class_map_failures} 条（上限 0）")
    if class_failures > contract.AUDIT_A1_CLASS_CROP_MAX_FAILURES:
        reasons.append(
            f"类别 crop 失败 {class_failures} 条（上限 {contract.AUDIT_A1_CLASS_CROP_MAX_FAILURES}）"
        )
    if instance_failures > contract.AUDIT_A1_INSTANCE_COLOR_MAX_FAILURES:
        reasons.append(
            f"实例颜色 crop 失败 {instance_failures} 条"
            f"（上限 {contract.AUDIT_A1_INSTANCE_COLOR_MAX_FAILURES}）"
        )
    return {
        "audit": "A1",
        "verdict": VERDICT_PASS if not reasons else VERDICT_FAIL,
        "reasons": reasons,
        "class_map_failures": class_map_failures,
        "class_crop_failures": class_failures,
        "instance_color_failures": instance_failures,
        "permanently_unverified_groups": sorted(set(group_color_rejections)),
    }


def evaluate_a2(
    sample_count: int, ok_sample_count: int, rejections: int, false_includes: int
) -> dict[str, Any]:
    """A2 人工轨：总体拒绝 ≤ floor(0.05×N)；false-INCLUDE ≤ floor(0.02×N_OK)。

    false-INCLUDE 的分母是 **panel 内 `OK` 样本数**，不是 200、不是全 eligible
    （方向性：宁可错排除）。
    """
    reject_limit = math.floor(contract.AUDIT_A2_REJECT_RATE * sample_count)
    false_include_limit = math.floor(
        contract.AUDIT_A2_FALSE_INCLUDE_RATE * ok_sample_count
    )
    reasons: list[str] = []
    if rejections > reject_limit:
        reasons.append(f"总体拒绝 {rejections} > floor(0.05×{sample_count})={reject_limit}")
    if false_includes > false_include_limit:
        reasons.append(
            f"false-INCLUDE {false_includes} > floor(0.02×{ok_sample_count})={false_include_limit}"
        )
    return {
        "audit": "A2",
        "verdict": VERDICT_PASS if not reasons else VERDICT_FAIL,
        "reasons": reasons,
        "sample_count": sample_count,
        "ok_sample_count": ok_sample_count,
        "reject_limit": reject_limit,
        "false_include_limit": false_include_limit,
    }


def evaluate_a2_mechanical(center_hit_ratio: float, iou_median: float) -> dict[str, Any]:
    """A2 机械轨：全量可检归档真值对，通过线 = §2.3 交叉验证阈值。"""
    passed = (
        center_hit_ratio >= contract.CROSSCHECK_CENTER_HIT_MIN_RATIO
        and iou_median >= contract.CROSSCHECK_IOU_MEDIAN_MIN
    )
    return {
        "audit": "A2",
        "track": "mechanical",
        "verdict": VERDICT_PASS if passed else VERDICT_FAIL,
        "center_hit_ratio": center_hit_ratio,
        "iou_median": iou_median,
    }


def evaluate_a3(false_unique_count: int) -> dict[str, Any]:
    """A3：零假唯一容忍，任何一例假唯一 = attempt 失败。"""
    passed = false_unique_count <= contract.AUDIT_A3_MAX_FAILURES
    return {
        "audit": "A3",
        "verdict": VERDICT_PASS if passed else VERDICT_FAIL,
        "false_unique_count": false_unique_count,
        "reasons": [] if passed else [f"假唯一 {false_unique_count} 例（上限 0）"],
    }


# --- attempt 有限状态机 ---------------------------------------------------
@dataclass
class AuditAttempt:
    panel: str
    verdict: str
    fix_registered: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditStateMachine:
    """至多 3 个 attempt；进入下一 attempt 的前置是登记一条具体修复。"""

    audit: str
    catalog_supersessions: int = 0
    attempts: list[AuditAttempt] = field(default_factory=list)

    def panel_for_next_attempt(self) -> str:
        index = len(self.attempts)
        if index >= contract.AUDIT_MAX_ATTEMPTS:
            raise AuditTerminal(
                "AUDIT_EXHAUSTED_FAIL",
                f"{self.audit} 已用尽 {contract.AUDIT_MAX_ATTEMPTS} 个 attempt；"
                "本批次以 REWORK_REQUIRED 返回实现侧，重新审计须走 supersession",
            )
        if index > 0 and not self.attempts[-1].fix_registered:
            raise AuditError("无修复登记不得重审（§2.7 有限状态机通则）")
        return f"panel-{index}"

    def record(self, verdict: str, detail: dict[str, Any] | None = None) -> AuditAttempt:
        attempt = AuditAttempt(
            panel=self.panel_for_next_attempt(), verdict=verdict, detail=detail or {}
        )
        self.attempts.append(attempt)
        return attempt

    def register_fix(self, description: str, change_ref: str) -> None:
        if not self.attempts:
            raise AuditError("尚无失败 attempt，不存在待登记的修复")
        if self.attempts[-1].verdict == VERDICT_PASS:
            raise AuditError("通过的 attempt 不需要修复登记")
        if not description or not change_ref:
            raise AuditError("修复登记必须同时给出缺陷描述与代码/数据变更引用")
        self.attempts[-1].fix_registered = f"{description}|{change_ref}"

    def note_catalog_supersession(self) -> None:
        """连续 2 次 catalog supersession 后仍未过 → 上交用户裁定。"""
        self.catalog_supersessions += 1
        self.attempts = []
        if self.catalog_supersessions > contract.AUDIT_MAX_CATALOG_SUPERSESSIONS:
            raise AuditTerminal(
                "AUDIT_ESCALATE_TO_USER",
                f"{self.audit} 已用满 {contract.AUDIT_MAX_CATALOG_SUPERSESSIONS} 次 catalog"
                " supersession 仍未通过；由用户裁定继续投入或收束",
            )

    def max_panel_attempts(self) -> int:
        """同一审计最多 9 个 panel attempt，不存在继续换 seed 的隐含路径。"""
        return contract.AUDIT_MAX_ATTEMPTS * (contract.AUDIT_MAX_CATALOG_SUPERSESSIONS + 1)


def user_workload_estimate(color_group_count: int) -> dict[str, int]:
    """每 attempt 的用户判定量（§2.7 的量级说明，用于人力预算核对）。"""
    total = (
        contract.AUDIT_A1_CLASS_MAP_CHECKLIST
        + contract.AUDIT_A1_CLASS_CROPS
        + color_group_count
        + contract.AUDIT_A1_INSTANCE_COLOR_CROPS
        + contract.AUDIT_A2_PANEL_SAMPLES
        + contract.AUDIT_A3_PANEL_SAMPLES
    )
    return {
        "class_map_checklist": contract.AUDIT_A1_CLASS_MAP_CHECKLIST,
        "a1_class_crops": contract.AUDIT_A1_CLASS_CROPS,
        "a1_color_group_crops": color_group_count,
        "a1_instance_color_crops": contract.AUDIT_A1_INSTANCE_COLOR_CROPS,
        "a2_panel_samples": contract.AUDIT_A2_PANEL_SAMPLES,
        "a3_panel_samples": contract.AUDIT_A3_PANEL_SAMPLES,
        "total": total,
    }
