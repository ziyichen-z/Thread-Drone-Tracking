#!/usr/bin/env python3
"""S0–S9 生产 driver：把已接受的阶段函数接成**唯一**生产入口。

接受轮 14 §26.2 授权本模块，**只算代码**：不得复制或重新解释阶段算法、
阈值、F1–F4、schema、split、verifier 或审计状态机，本模块因此一行算法也不
自己实现——它只做四件事：

1. 按 S0→S9 顺序调用既有阶段函数；
2. 每一次跨阶段取数都走 `ArtifactStore.read(..., requesting_stage=N)`，
   让 §2 的禁行边**真的**参与生产路径，而不是只在单测里被断言；
3. 每一次产出都走 `ArtifactStore.write`（create-once + 字节幂等）；
4. 把 §2.5/§2.6 需要的像素交给 `pixel_source` 适配器。

**未授权边界（本模块不越）**：不渲染、不执行 A1/A2/A3 人工审计；S6 的审计
工件必须由人工审计步骤先行写入，driver **拒绝合成**——F1 的冻结定义是
「验证 = S5 判定 + A1 通过」，没有 A1 就没有双验证对象，凭空当作通过是
fail-open。真实归档上的完整运行需要用户另行授权；`preflight()` 是本模块
唯一被授权对真实归档执行的动作，它一个字节也不写。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
from typing import Any

from tools.dist_data import (
    bind_layout,
    build_catalog,
    build_inventory,
    contract,
    g0_report,
    gen_mother_templates,
    make_splits,
    pixel_source,
    project_boxes,
    roots,
)
from tools.dist_data import artifacts as artifacts_module
from tools.dist_data.artifacts import ArtifactStore, DistDataError, ForbiddenEdgeError

# S9 收束终态（本模块只记录，不新增终态名）。
STOP_GATE_OPEN = "GATE_OPEN_MOTHER_SET_MATERIALISED"
STOP_GATE_CLOSED = g0_report.GATE_INSUFFICIENT

# attempt 身份的闭集形式（复核 R2@stageA F6）。前导零同样不合式：
# `attempt-01` 会在 `attempt-01/` 下另开一棵工件树，却与 `attempt-1` 同号，
# 正是 §6 授权 #2「attempt 身份上限 = 2」要挡的第三个身份。
ATTEMPT_NAME = re.compile(r"^attempt-[1-9][0-9]*$")


class PipelineError(DistDataError):
    """driver 组合失败（缺前置工件、缺授权步骤、真值不可 join 等）。"""


class CatalogStream:
    """可重复迭代的类型化 `frames_catalog` 行流（BC-DATA-25 (5)）。

    每次 `__iter__` 都重新打开并逐 shard 复核身份/行数/顺序，末尾复核累积
    哈希——所以「多遍扫描」是确定性的，且**本类自身**不驻留全集。`__len__`
    取自 manifest 的 `frame_count`，供只需要总数的既有汇总函数使用。

    本类**只**强制一件事：消费者必须经这个可重复、逐 shard 校验的迭代接口
    取数。它不支持下标，但缺少下标**并不阻止**消费者用 `list()` 或逐行
    `append` 物化派生全集——复核轮 6 F21 实测反证了原先「正是为了让任何试图
    物化全集的写法直接失败」的说法。**有界性因此必须由每个消费点分别证明**：
    S5 已由 `build_catalog.BoundedObservationSelector` 闭合；S6/S7/S8 的帧
    线性派生物仍是 `DEFERRED_BOUNDEDNESS_DEBT_BEFORE_STAGE_AUTHORIZATION`
    （证据 §20.2），在各自阶段的执行授权前必须先回接受角色。
    """

    def __init__(self, store: ArtifactStore, attempt: str, requesting_stage: int) -> None:
        self._store = store
        self._attempt = attempt
        self._stage = requesting_stage
        manifest, reference = store.composite_manifest(
            "frames_catalog", attempt, requesting_stage=requesting_stage
        )
        self._manifest = manifest
        self._reference = reference

    @property
    def manifest(self) -> dict[str, Any]:
        return self._manifest

    @property
    def reference(self):
        """本次实际读取的 manifest `ArtifactRef`（供下游写 lineage）。"""
        return self._reference

    def __len__(self) -> int:
        return int(self._manifest["frame_count"])

    def __iter__(self):
        return self._store.read_composite_rows(
            "frames_catalog", self._attempt, requesting_stage=self._stage
        )


class SplitDecoratedStream:
    """`CatalogStream` + S4 派生的 `split` 键（复核轮 6 F20）。

    修前 `catalog["entries"]` 是同一批**可变** dict：S7 先逐 entry 打上
    `entry["split"]`，`build_g0_report()` 随后读到的就是带键的同批对象。
    流式化后每次迭代都由 `json.loads` 产出新对象，一次性打键的侧信道因此
    被切断，F2、`station_keys` 与 `frames_by_split` 被静默归零。

    本适配器把 split 变成**流本身的属性**：每一次 `__iter__` 都重新装饰，
    所以多遍消费（`build_g0_report` 内 5+ 遍）每遍都拿到同一份 split，
    且**不物化任何全集**——装饰在行流上逐条完成，驻留仍是一条 entry。
    `split_of_frame` 只此一份，与 `freeze_mother_candidates` 用的是同一个
    映射，两处不可能各说各话。
    """

    def __init__(
        self, stream: CatalogStream, split_of_frame: dict[str, str]
    ) -> None:
        self._stream = stream
        self._split_of_frame = split_of_frame

    def __len__(self) -> int:
        return len(self._stream)

    def __iter__(self):
        for entry in self._stream:
            # 每次迭代都是新 dict（`read_composite_rows` 逐行 `json.loads`），
            # 就地打键不会污染任何其它消费者。
            entry["split"] = self._split_of_frame.get(entry["frame_id"])
            yield entry


@dataclass
class PipelineDriver:
    """S0–S9 的唯一生产入口。"""

    repo_root: Path
    attempt: str = "attempt-1"
    pixels: Any | None = None
    # P1-VLM-DATA-002 §2.2 第 4/5 条：S0–S5 的六个写点各自 supersede 该阶段
    # **最新已发布前身**。前身**按阶段从 store 解析**，不取操作员传入的单值——
    # 单值在某阶段未发布时会写出 `supersedes: null`，那是断链而不是「不伪造」
    # （复核 R1@stageA F1）。操作员只需给出归因。
    supersession_reason: str | None = None
    _store: ArtifactStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # 复核 R2@stageA F6：不合式 attempt 会静默绕过 §2.2 的 supersession
        # 谱系门（`_attempt_number` 返回 `None` → `_supersession_kwargs` 返回
        # `{}` → 写出整棵无前身工件树）。命名在**构造时**就 fail-closed，
        # 因此不合式身份下一件工件也写不出。`attempt-1` 行为不变。
        if not ATTEMPT_NAME.match(self.attempt):
            raise PipelineError(
                f"attempt 身份不合式：{self.attempt!r}。生产入口只接受 "
                "attempt-<正整数>（attempt-1/attempt-2/…，无前导零）；"
                "不合式身份会绕过 §2.2 第 4/5 条的前身解析，写出无谱系的 "
                "create-once 工件树，并占用 §6 授权 #2 之外的第三个 attempt 身份"
            )
        self.repo_root = Path(self.repo_root)
        self._store = ArtifactStore(self.repo_root)
        if self.pixels is None:
            self.pixels = pixel_source.ArchivePixelSource(self.repo_root)

    # --- 取数：一律经 store，让禁行边参与生产路径 --------------------------
    def _read(self, artifact: str, requesting_stage: int) -> dict[str, Any]:
        return self._read_ref(artifact, requesting_stage)[0]

    def _read_ref(self, artifact: str, requesting_stage: int):
        """→ `(payload, ArtifactRef)`。

        BC-DATA-25 (3) 要求组合工件 manifest 记录**本次实际读取**的输入
        artifact refs，所以取数点必须把 ref 一并交出来——事后按路径重建的
        引用不算（接受轮 22 SP22-1）。
        """
        attempt = self.resolve_read_attempt(artifact)
        try:
            payload, reference = self._store.read(
                artifact, attempt, requesting_stage=requesting_stage
            )
        except ForbiddenEdgeError:
            raise  # 禁行边必须原样冒泡，不得被「缺前置工件」的措辞掩盖
        except DistDataError as exc:
            raise PipelineError(
                f"缺前置工件 {artifact}@{attempt}：请先跑到该阶段（{exc}）"
            ) from exc
        return payload, reference

    def _composite_manifest(self, artifact: str, requesting_stage: int):
        """组合工件 manifest 的**跨阶段**取数点（证据 §17 / I17）。

        与 `_read_ref`、`_catalog_stream` 同样按 BC-SURVEY-4 解析读取 attempt：
        写入 attempt 与读取 attempt 解绑。此前 S7/S8 直接用 `self.attempt` 取
        `splits`，于是 attempt-2 发布到 S4、attempt-3 从 S5 续跑时，S7 会去找
        从未发布也不该发布的 `splits@attempt-3`——报错点名的正是续跑自己决定
        跳过的工件，而唯一被暗示的出路（重发 splits）为 §2.2 第 5 条与
        create-once 所禁止。
        """
        attempt = self.resolve_read_attempt(artifact)
        try:
            return self._store.composite_manifest(
                artifact, attempt, requesting_stage=requesting_stage
            )
        except ForbiddenEdgeError:
            raise
        except DistDataError as exc:
            raise PipelineError(
                f"缺前置工件 {artifact}@{attempt}：请先跑到该阶段（{exc}）"
            ) from exc

    def _assert_splits_lineage(self, splits_reference, catalog_reference) -> None:
        """splits 与本次实际读到的 `frames_catalog` 必须是同一代（I17）。

        BC-SURVEY-4 解绑的是「写入 attempt 与读取 attempt」，**不是**「同一次运行
        里各输入可以来自任意代」：splits 的行是按它自己 lineage 里那一份
        frames_catalog 建的，混代会让 G0 门建立在对不上的帧集合上，而且是静默的。
        两个 ref 都现成（splits 信封的 `inputs` 与 `CatalogStream.reference`），
        所以在本阶段写出**任何**工件之前比对。
        """
        envelope = json.loads(Path(splits_reference.path).read_bytes().decode("utf-8"))
        recorded = [
            entry
            for entry in envelope.get("inputs", [])
            if entry.get("artifact") == "frames_catalog"
        ]
        actual = catalog_reference.as_reference()
        if recorded != [actual]:
            raise PipelineError(
                f"lineage 不一致：splits@{splits_reference.attempt} 记录的 frames_catalog "
                f"输入是 {recorded}，本次实际读到的是 {actual}。BC-SURVEY-4 未授权在同一次"
                "运行里混用不同代的 frames_catalog；本阶段零写入"
            )

    def _catalog_stream(self, requesting_stage: int) -> CatalogStream:
        """S4–S8 取 `frames_catalog` 的**唯一**入口（BC-DATA-25 (5)）。

        与 `_read_ref` 同样按 BC-SURVEY-4 解析读取 attempt。
        """
        attempt = self.resolve_read_attempt("frames_catalog")
        try:
            return CatalogStream(self._store, attempt, requesting_stage)
        except ForbiddenEdgeError:
            raise
        except DistDataError as exc:
            raise PipelineError(
                f"缺前置工件 frames_catalog@{attempt}：请先跑到该阶段（{exc}）"
            ) from exc

    def read_chain(self) -> tuple[str, ...]:
        """BC-SURVEY-4：直接依赖的读取顺序，「已发布 attempt-N 优先，否则回退」。

        写入 attempt 与读取 attempt 因此**解绑**：attempt-3 从首个未发布阶段
        续跑时，每条直接依赖各自解析到它实际存在的最新已发布 attempt
        （attempt-3 优先，否则 attempt-2），而不是一律读 `self.attempt`。
        attempt-1 是旧表示的不可变基线，不参与混合路线。
        """
        number = self._attempt_number()
        if number < 2:
            return (self.attempt,)
        return tuple(f"attempt-{index}" for index in range(number, 1, -1))

    def resolve_read_attempt(self, artifact: str) -> str:
        """按 `read_chain()` 解析该 artifact 实际可读的 attempt；全缺即失败。"""
        for attempt in self.read_chain():
            if self._store.path_for(artifact, attempt).exists():
                return attempt
        raise PipelineError(
            f"缺前置工件 {artifact}：{list(self.read_chain())} 均未发布；"
            "BC-SURVEY-4 禁止按写入 attempt 事后合成 ref"
        )

    def _attempt_number(self) -> int:
        """`attempt-<n>` 的 n。

        命名已由 `__post_init__` 收束为闭集 `attempt-<正整数>`（复核 F6），
        所以本方法不再有「解析不出就返回 `None`」的分支——那个分支正是让
        谱系门被静默绕过的入口。
        """
        return int(self.attempt.rpartition("-")[2])

    def resolve_predecessor(self, artifact: str) -> str | None:
        """该阶段在**当前 attempt 之前**最新已发布的 attempt；没有则 `None`。"""
        current = self._attempt_number()
        if current <= 1:
            return None
        for index in range(current - 1, 0, -1):
            candidate = f"attempt-{index}"
            if self._store.path_for(artifact, candidate).exists():
                return candidate
        return None

    def _supersession_kwargs(self, artifact: str) -> dict[str, Any]:
        """本次写入该 artifact 的 supersession 参数（§2.2 第 4/5 条）。

        BC-SURVEY-4：**读**取的 attempt 由 `_read_ref` 各自解析，与**写**入的
        attempt 解绑；本方法只管写入侧的归因。前身按阶段解析为「当前 attempt
        之前最新已发布者」；attempt ≥ 2 若解析不到前身或缺归因，**拒绝写入**
        而不是静默省略——静默省略会写出 `supersedes: null` 的断链工件
        （复核 R1@stageA F1）。
        """
        current = self._attempt_number()
        if current <= 1:
            return {}
        predecessor = self.resolve_predecessor(artifact)
        if predecessor is None:
            raise PipelineError(
                f"{artifact}@{self.attempt} 解析不到已发布前身："
                f"attempt-1..{current - 1} 均未发布该阶段。§2.2 第 4/5 条要求每件"
                "各自 supersede 最新已发布前身，不得写出 supersedes: null 的断链"
            )
        if not self.supersession_reason:
            raise PipelineError(
                f"{artifact}@{self.attempt} 缺 supersession 归因；"
                "§2.2 禁止无归因重做（--supersession-reason）"
            )
        return {
            "supersedes": predecessor,
            "supersession_reason": self.supersession_reason,
        }

    def _camera_for(self, frame_id: str) -> project_boxes.Camera:
        """由帧自己的 sidecar 源字节构相机；不往 S3 载荷里加字段改 schema。"""
        sidecar_path = (self.repo_root / frame_id).with_suffix(".json")
        try:
            document = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PipelineError(f"sidecar 不可解析：{sidecar_path}（{exc}）") from exc
        return project_boxes.Camera.from_sidecar(document)

    # --- S0 ----------------------------------------------------------------
    def stage0_contract(self) -> dict[str, Any]:
        # §2.2 第 4 条 + BC-SURVEY-14：`survey_sessions` 无条件写入（零归档即
        # 空表）。写成 `sessions or None` 会让零归档时的 attempt-2 少一个键，
        # 与「差异键恰为五键」冲突。
        sessions = contract.build_survey_sessions(self.repo_root)
        reference = contract.write_contract(
            self.repo_root,
            self.attempt,
            survey_sessions=sessions,
            **self._supersession_kwargs("contract"),
        )
        return {
            "artifact": "contract",
            "sha256": reference.sha256,
            "survey_sessions": len(sessions),
        }

    # --- S1 ----------------------------------------------------------------
    def stage1_inventory(self) -> dict[str, Any]:
        # BC-SURVEY-4：直接依赖按「已发布 attempt-3 优先，否则 attempt-2」
        # 实际读取（`_read_ref` 内解析），并把实际 ref 写进 lineage。
        contract_payload, contract_ref = self._read_ref("contract", requesting_stage=1)
        # BC-SURVEY-7：S0 没有 `root_manifest` 就没有可对账的根清单——
        # fail-closed，绝不写成 `.get(...) or {}`（那等于「无可对账」）。
        # 键**存在**还不够：`"root_manifest": null` 会通过存在性检查，然后走进
        # `build_inventory` 的「无声明」诊断分支、什么都不比。两个键都要求是对象。
        for key, bc in (("root_manifest", "BC-SURVEY-7"), ("survey_acquisition", "BC-SURVEY-14")):
            if not isinstance(contract_payload.get(key), dict):
                raise PipelineError(
                    f"S0 {contract_ref.artifact}@{contract_ref.attempt} 的 {key} 不是对象"
                    f"（实测 {type(contract_payload.get(key)).__name__}）；{bc} 起 S1 必须"
                    "对账它——请先发布带该键的 contract attempt"
                )
        payload = build_inventory.build_inventory(
            self.repo_root,
            survey_sessions=list(contract_payload.get("survey_sessions") or []),
            root_manifest=contract_payload["root_manifest"],
            survey_acquisition=contract_payload["survey_acquisition"],
        )
        reference = self._store.write(
            "inventory",
            self.attempt,
            payload,
            inputs=[contract_ref.as_reference()],
            **self._supersession_kwargs("inventory"),
        )
        return {
            "artifact": "inventory",
            "sha256": reference.sha256,
            "records": payload["record_count"],
        }

    # --- S2 ----------------------------------------------------------------
    def stage2_layout(self) -> dict[str, Any]:
        # `build_layout` 自己经 store 读 inventory（禁行边在其内部生效）。
        # BC-SURVEY-4：S2 的直接依赖是 inventory，按同一规则解析实际读取的
        # attempt，而不是绑到写入 attempt。
        payload = bind_layout.build_layout(
            self.repo_root,
            self.resolve_read_attempt("inventory"),
            pixels=self.pixels,
        )
        reference = self._store.write(
            "layout", self.attempt, payload, **self._supersession_kwargs("layout")
        )
        bound = [
            partition
            for partition in payload["scenario_partitions"].values()
            if partition["binding_status"] == bind_layout.BINDING_BOUND
        ]
        return {
            "artifact": "layout",
            "sha256": reference.sha256,
            "partitions": len(payload["scenario_partitions"]),
            "bound_partitions": len(bound),
        }

    # --- S3 ----------------------------------------------------------------
    @staticmethod
    def _partition_of_unit(
        layout: dict[str, Any]
    ) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        """→ `(只含 BOUND 的几何查找表, 逐 unit 的状态表)`。

        BC-DATA-23 (6)：source-unit 查找**不得映入非 BOUND partition**——几何
        表因此只装 BOUND；状态表单独保留，供 INVALID 帧的退出计数使用，
        这样计数不必靠往几何表里塞不可用的记录换取。
        """
        bound: dict[str, dict[str, Any]] = {}
        status: dict[str, str] = {}
        for partition in layout["scenario_partitions"].values():
            for unit in partition.get("source_units", []):
                status[unit] = partition["binding_status"]
                if partition["binding_status"] == bind_layout.BINDING_BOUND:
                    bound[unit] = partition
        return bound, status

    def stage3_frames_catalog(self) -> dict[str, Any]:
        inventory, inventory_ref = self._read_ref("inventory", requesting_stage=3)
        layout, layout_ref = self._read_ref("layout", requesting_stage=3)
        if "cross_validation" not in layout:
            raise PipelineError(
                "layout 缺 `cross_validation`：BC-DATA-23 (5) 要求它是必有成员，"
                "S3 不接受未经交叉验证的 layout 工件"
            )
        bound_by_unit, status_by_unit = self._partition_of_unit(layout)

        # BC-DATA-25 (5)：**不得**累积全部 entry。此处只做流，逐条交给
        # `write_composite`；计数放在可变盒子里，manifest 汇总在流耗尽后求值。
        counts = {"frames": 0, "skipped_unbound": 0, "skipped_invalid": 0}

        def _entries():
          for record in inventory["records"]:
              if record["kind"] != roots.KIND_IMAGE or record["decision"] != "INCLUDED":
                  continue
              unit = roots.source_unit_for(record["path"])
              partition = bound_by_unit.get(unit)
              if partition is None:
                  # BC-DATA-18 的 partition 局域隔离在 S3 同样成立：未绑定或派生/
                  # 交叉验证失败的 partition 只让**它自己**的帧退出，其余照常产出。
                  # 原实现把全部 partition（含 INVALID）映进查找表再取
                  # `partition["instances"]`，而 `build_layout` 的异常分支不写该键，
                  # 一个失败的 partition 会 KeyError 掉整个 S3（复核轮 4 F17）。
                  if status_by_unit.get(unit) is None:
                      counts["skipped_unbound"] += 1
                  else:
                      counts["skipped_invalid"] += 1
                  continue
              sidecar_path = (self.repo_root / record["path"]).with_suffix(".json")
              try:
                  sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
              except (OSError, ValueError) as exc:
                  raise PipelineError(
                      f"sidecar 不可解析：{sidecar_path}（{exc}）"
                  ) from exc
              # BC-DATA-23 (3)：S2 与 S3 共用同一 truth join 实现。
              truth_row, truth_schema = bind_layout.load_frame_truth(
                  self.repo_root, record["path"]
              )
              if truth_schema is None and roots.is_survey_unit(unit):
                  # P1-VLM-DATA-002 §2.2 第 3 条：巡览族没有逐帧真值文件，
                  # 停放位姿由本 partition 的归档 `route_world_m` 派生，
                  # 走 `target_parked` 而不是扫掠代理。
                  truth_row = build_catalog.parked_target_truth_row(
                      partition.get("route_world_m", [])
                  )
                  truth_schema = contract.TARGET_SCHEMA_PARKED
              bodies = list(partition["instances"]) + list(partition["phantoms"])
              frame = build_catalog.FrameInput(
                  frame_id=record["path"],  # BC-DATA-3：frame_id = inventory 全局路径
                  sidecar=sidecar,
                  family=record["family"],
                  layout_class=record["layout_class"],
                  usage_class=record["usage_class"],
                  # BC-DATA-23 (6)：由实际 partition 状态派生，禁止字面量 True。
                  layout_binding_valid=(
                      partition["binding_status"] == bind_layout.BINDING_BOUND
                  ),
                  sidecar_complete=bool(record["sidecar_join"]["complete"]),
                  truth_row=truth_row,
                  truth_schema=truth_schema,
              )
              counts["frames"] += 1
              yield build_catalog.build_frame_entry(
                  frame,
                  bodies,
                  partition.get("route_world_m", []),
                  build_catalog.vehicle_envelope_half_extents(partition["instances"]),
              )

        def _summary() -> dict[str, Any]:
            return {
                "stage": 3,
                "frame_count": counts["frames"],
                "skipped_unbound_frames": counts["skipped_unbound"],
                "skipped_invalid_frames": counts["skipped_invalid"],
            }

        reference = self._store.write_composite(
            "frames_catalog",
            self.attempt,
            _summary,
            _entries(),
            # BC-DATA-25 (3)：lineage 取自**本次实际读取**的两个 ref。
            inputs=[inventory_ref.as_reference(), layout_ref.as_reference()],
            **self._supersession_kwargs("frames_catalog"),
        )
        return {
            "artifact": "frames_catalog",
            "sha256": reference.sha256,
            "frames": counts["frames"],
            "skipped_unbound_frames": counts["skipped_unbound"],
            "skipped_invalid_frames": counts["skipped_invalid"],
        }

    # --- S4 ----------------------------------------------------------------
    def stage4_splits(self) -> dict[str, Any]:
        stream = self._catalog_stream(requesting_stage=4)

        # 第 1 遍：族映射 + pHash 签名（每帧只留两个小值，不留 entry）。
        family_of_frame: dict[str, str] = {}
        phash_of_frame: dict[str, int] = {}
        for entry in stream:
            family_of_frame[entry["frame_id"]] = entry["family"]
            phash_of_frame[entry["frame_id"]] = self.pixels.phash(entry["frame_id"])
        merged = make_splits.merge_atoms(family_of_frame, phash_of_frame)
        atom_of_family = {
            family: atom
            for atom, families in merged["atoms"].items()
            for family in families
        }

        # 第 2 遍：逐 atom 汇总（只留帧 id、布局类、站位键、对象 id 的集合）。
        buckets: dict[str, dict[str, Any]] = {}
        object_ids: set[str] = set()
        for entry in stream:
            bucket = buckets.setdefault(
                atom_of_family[entry["family"]],
                {"floor": [], "non_floor": [], "layouts": set(), "stations": set(),
                 "objects": set()},
            )
            if build_catalog.pre_split_floor_eligible(entry):
                bucket["floor"].append(entry["frame_id"])
            else:
                bucket["non_floor"].append(entry["frame_id"])
            bucket["layouts"].add(entry["layout_class"])
            if entry["station_bin"]["key"] is not None:
                bucket["stations"].add(entry["station_bin"]["key"])
            for item in entry["objects"]:
                bucket["objects"].add(item["object_id"])
                object_ids.add(item["object_id"])
        atoms = [
            make_splits.AtomSummary(
                atom_id=atom_id,
                families=sorted(merged["atoms"][atom_id]),
                layout_classes=sorted(buckets[atom_id]["layouts"]),
                floor_eligible_frames=sorted(buckets[atom_id]["floor"]),
                non_floor_frames=sorted(buckets[atom_id]["non_floor"]),
                station_keys=sorted(buckets[atom_id]["stations"]),
                object_ids=sorted(buckets[atom_id]["objects"]),
            )
            for atom_id in sorted(buckets)
        ]
        held_out = make_splits.held_out_objects(sorted(object_ids))

        # 第 3 遍：流式角色行 + 同遍累加 exposure 汇总（BC-DATA-25 (4)）。
        try:
            summary_of, roles = make_splits.assign_splits_streaming(atoms, iter(stream))
        except make_splits.SplitTerminal as terminal:
            # BC-DATA-2：收束终态保全已有工件、不执行 S8。
            return {
                "artifact": "splits",
                "terminal": terminal.terminal,
                "detail": terminal.detail,
            }

        def _summary() -> dict[str, Any]:
            return {
                "stage": 4,
                **summary_of(),
                "atoms": merged,
                "held_out_objects": held_out,
            }

        try:
            reference = self._store.write_composite(
                "splits",
                self.attempt,
                _summary,
                roles,
                # BC-DATA-25 (3)：lineage 取自本次实际读取的 frames_catalog ref。
                inputs=[stream.reference.as_reference()],
                **self._supersession_kwargs("splits"),
            )
        except make_splits.SplitTerminal as terminal:
            return {
                "artifact": "splits",
                "terminal": terminal.terminal,
                "detail": terminal.detail,
            }
        manifest, _ref = self._store.composite_manifest(
            "splits", self.attempt, requesting_stage=4
        )
        return {
            "artifact": "splits",
            "sha256": reference.sha256,
            "atoms": len(merged["atoms"]),
            "frame_counts": manifest["frame_counts"],
        }

    # --- S5 ----------------------------------------------------------------
    @staticmethod
    def _color_observation_rows(entries: Any):
        """S5 观测行的**唯一**过滤定义：状态 `OK` 且有 visible 框的对象。

        对象域与观测流因此不可能各用一套判据（两遍扫描共用本生成器）。
        """
        for entry in entries:
            for item in entry["objects"]:
                if item["status"] != "OK" or item["visible_px"] is None:
                    continue
                yield entry["frame_id"], item

    @classmethod
    def _color_observations(cls, entries: Any):
        """S5 的观测行流，逐条产出、不返回列表。

        `build_field_catalog` 逐条收进 `BoundedObservationSelector`，全程只
        驻留逐对象最小 K 条（复核轮 6 F21）。
        """
        for frame_id, item in cls._color_observation_rows(entries):
            yield build_catalog.ObjectObservation(
                frame_id,
                item["object_id"],
                tuple(item["visible_px"]),
                # BC-DATA-15：最近 K 帧按**相机前向深度**排序。
                item["camera_depth_m"],
            )

    def stage5_field_catalog(self) -> dict[str, Any]:
        stream = self._catalog_stream(requesting_stage=5)
        layout, layout_ref = self._read_ref("layout", requesting_stage=5)
        relocated: set[str] = set()
        for partition in layout["scenario_partitions"].values():
            relocated.update(partition.get("relocation_marks", {}))

        # 第 1 遍：只收对象域（≤ 对象数个字符串），一条观测也不构造。
        object_ids = {
            item["object_id"] for _frame_id, item in self._color_observation_rows(stream)
        }
        # 第 2 遍：观测以生成器交给 S5，逐条被有界选择器收敛。`CatalogStream`
        # 可重复迭代正是为此，两遍各自有界，任何一遍都不物化全集。
        payload = build_catalog.build_field_catalog(
            sorted(object_ids),
            self._color_observations(stream),
            self.pixels,
            relocated=sorted(relocated),
        )
        # P1-VLM-DATA-002 §2.2 第 6 条（S5 lineage 精确合同）：`inputs` 只能
        # 由**本次实际读取**得到的两个 ref 组成，顺序固定
        # `[frames_catalog_ref, layout_ref]`，每个 ref 恰含
        # `{artifact, attempt, sha256}`。禁止事后按路径合成。
        inputs = [stream.reference.as_reference(), layout_ref.as_reference()]
        reference = self._store.write(
            "field_catalog",
            self.attempt,
            payload,
            inputs=inputs,
            **self._supersession_kwargs("field_catalog"),
        )
        return {
            "artifact": "field_catalog",
            "sha256": reference.sha256,
            "objects": len(payload["objects"]),
            "dual_verified": len(payload["dual_verified_object_ids"]),
        }

    # --- S6 ----------------------------------------------------------------
    def audit_strata(self) -> dict[str, Any]:
        """BC-DATA-15：A1/A2 的距离三分位按 `camera_forward_depth` 装配。

        只产出人工审计**需要的分层输入**，不判定、不生成 panel、不推进审计
        状态机——那三件事都在 §26.2 的明确不包含清单里。
        """
        samples: list[tuple[float, str]] = []
        for entry in self._catalog_stream(requesting_stage=6):
            for item in entry["objects"]:
                if item["status"] != "OK" or item["camera_depth_m"] is None:
                    continue
                # §2.7 的 A1/A2 样本域是**目录车辆**（类别映射、颜色 crop、框
                # 身份、可见像素 gold 规则都以车辆为对象）。BC-DATA-16 只把
                # building/nature/prop 挡在 blocking/referable/exposure 外，
                # **不挡在状态机外**——它们照样能取得 OK 状态，若不在此过滤就会
                # 混进三分位样本池、虚增 12 格配额与分母（复核轮 4 F18，与 F2
                # 同族）。phantom 另有 `status == "PHANTOM"`，已被上一行排除。
                if contract.class_for_scene_object(item["object_id"]) is None:
                    continue
                samples.append(
                    (float(item["camera_depth_m"]), f"{entry['frame_id']}@{item['object_id']}")
                )
        # 先按 (z_depth, sample_id UTF-8) 排序，再等分三段（BC-DATA-15）。
        samples.sort(key=lambda pair: (pair[0], pair[1].encode("utf-8")))
        total = len(samples)
        cuts = (total // 3, (2 * total) // 3)
        strata: dict[str, list[str]] = {"near": [], "mid": [], "far": []}
        for index, (_depth, sample_id) in enumerate(samples):
            name = "near" if index < cuts[0] else ("mid" if index < cuts[1] else "far")
            strata[name].append(sample_id)
        return {
            "sample_count": total,
            "cuts": list(cuts),
            "stratum_of_sample": {
                sample_id: name for name, members in strata.items() for sample_id in members
            },
            "counts": {name: len(members) for name, members in sorted(strata.items())},
        }

    def require_audit(self) -> dict[str, Any]:
        """S6 审计工件必须由人工审计步骤先行写入；driver 拒绝合成。"""
        try:
            payload, _reference = self._store.read(
                "audit", self.attempt, requesting_stage=7
            )
        except ForbiddenEdgeError:
            raise
        except DistDataError as exc:
            raise PipelineError(
                f"缺 audit@{self.attempt}：F1 的冻结定义是「验证 = S5 判定 + "
                "A1 通过」，没有人工审计结果就没有双验证对象。driver 不合成"
                "审计结论（接受轮 14 §26.2 明确不包含 A1/A2/A3 的渲染与执行），"
                "人工审计需用户另行授权后执行并落盘。"
            ) from exc
        return payload

    # --- S7 ----------------------------------------------------------------
    def stage7_gate(self) -> dict[str, Any]:
        catalog_stream = self._catalog_stream(requesting_stage=7)
        splits, splits_ref = self._composite_manifest("splits", requesting_stage=7)
        self._assert_splits_lineage(splits_ref, catalog_stream.reference)
        field_catalog = self._read("field_catalog", requesting_stage=7)
        audit = self.require_audit()

        downgraded = build_catalog.apply_audit_downgrades(
            field_catalog, audit.get("downgraded_group_keys", [])
        )
        split_of_frame = {
            frame: split
            for split, frames in splits["frames"].items()
            for frame in frames
        }
        # 复核轮 6 F20：split 必须是流的属性，一次性打键在多遍消费下会失效。
        stream = SplitDecoratedStream(catalog_stream, split_of_frame)
        atom_of_family = {
            family: atom
            for atom, families in splits["atoms"]["atoms"].items()
            for family in families
        }
        atom_of_frame = {
            entry["frame_id"]: atom_of_family[entry["family"]] for entry in stream
        }
        held_out = splits["held_out_objects"]["held_out_object_ids"]
        candidates = []
        for entry in stream:
            world = build_catalog.frame_world(entry, downgraded)
            for object_id in entry["referable"]:
                candidate = build_catalog.prospective_mother_eligible(
                    entry, object_id, world, downgraded
                )
                if candidate is not None:
                    candidates.append(candidate)
        frozen = g0_report.freeze_mother_candidates(
            candidates,
            split_of_frame,
            atom_of_frame,
            held_out,
            dropped_frames=splits["dropped_frames"],
        )
        report = g0_report.build_g0_report(
            entries=stream,
            frozen=frozen,
            field_catalog=downgraded,
            splits_payload=splits,
            # BC-DATA-23 (5)：交叉验证结果是 layout 的必有成员，缺则硬失败；
            # 原来的 `.get("cross_validation", {})` 会把「从未验证」静默成空表。
            layout_payload=self._read("layout", requesting_stage=7),
            audit_results=audit,
            relation_availability={},
        )
        frozen_reference = self._store.write("mother_candidates", self.attempt, frozen)
        report_reference = self._store.write("g0_report", self.attempt, report)
        return {
            "artifact": "g0_report",
            "mother_candidates_sha256": frozen_reference.sha256,
            "sha256": report_reference.sha256,
            "gate": report["gate"],
            "unmet_floors": report["unmet_floors"],
            "candidates": frozen["candidate_count"],
        }

    # --- S8 ----------------------------------------------------------------
    def stage8_mother_set(self) -> dict[str, Any]:
        frozen = self._read("mother_candidates", requesting_stage=8)
        report = self._read("g0_report", requesting_stage=8)
        stream = self._catalog_stream(requesting_stage=8)
        splits, splits_ref = self._composite_manifest("splits", requesting_stage=8)
        self._assert_splits_lineage(splits_ref, stream.reference)

        amodal_box_of: dict[str, list[float]] = {}
        for entry in stream:
            camera = self._camera_for(entry["frame_id"])
            for item in entry["objects"]:
                if item["amodal_px"] is None:
                    continue
                candidate_id = f"{entry['frame_id']}|{item['object_id']}"
                amodal_box_of[candidate_id] = list(
                    project_boxes.normalized_xywh(tuple(item["amodal_px"]), camera)
                )
        payload = gen_mother_templates.build_d0(
            frozen,
            report,
            amodal_box_of,
            splits["held_out_objects"]["held_out_object_ids"],
        )
        mother_reference = self._store.write(
            "mother_set", self.attempt, payload["mother_set"]
        )
        template_reference = self._store.write(
            "template_expressions", self.attempt, payload["template_expressions"]
        )
        return {
            "artifact": "mother_set",
            "sha256": mother_reference.sha256,
            "template_expressions_sha256": template_reference.sha256,
            "count": payload["mother_set"]["count"],
        }

    # --- S9 ----------------------------------------------------------------
    def stage9_stop_point(self, outcome: str, detail: dict[str, Any]) -> dict[str, Any]:
        payload = {"stage": 9, "outcome": outcome, "detail": detail}
        reference = self._store.write("stop_point", self.attempt, payload)
        return {"artifact": "stop_point", "sha256": reference.sha256, "outcome": outcome}

    # --- 只读 preflight（唯一被授权对真实归档执行的动作） ------------------
    def preflight(self) -> dict[str, Any]:
        """S1 + S2 在内存里跑一遍，**一个字节也不写**。

        产出的是诊断计数，不是 G0 verdict；调用方不得把它当门结果引用。
        """
        artifact_root = self._store.artifact_dir("inventory").parent
        before = artifact_root.exists()
        inventory = build_inventory.build_inventory(self.repo_root)
        # 走**完整的** S2（含逐 partition 几何派生），不是只到 bind_families：
        # 候选 4 的阻断缺陷正是「只跑了 build_inventory + bind_families、
        # 从未触及 build_layout」才漏掉的，实现证据 §11.1 已把整条链列为固定
        # 自查项。in-memory 入参使这一步不产生任何工件。
        layout = bind_layout.build_layout(
            self.repo_root, self.attempt, inventory=inventory
        )
        partitions = list(layout["scenario_partitions"].values())
        included_images = sum(
            1
            for record in inventory["records"]
            if record["kind"] == roots.KIND_IMAGE and record["decision"] == "INCLUDED"
        )
        bound = [
            partition
            for partition in partitions
            if partition["binding_status"] == bind_layout.BINDING_BOUND
        ]
        bound_frames = sum(partition["frame_count"] for partition in bound)
        after = artifact_root.exists()
        return {
            "mode": "preflight",
            # 由前后存在性**派生**，不写死字面量（复核轮 4 观察项）。
            "wrote_nothing": (not before) and (not after),
            "artifact_root_existed_before": before,
            "artifact_root_exists_after": after,
            "records": inventory["record_count"],
            "match_audit": inventory["match_audit"],
            "decision_histogram": dict(sorted(inventory["decision_histogram"].items())),
            "included_images": included_images,
            "partitions": sorted(
                (
                    {
                        "partition_id": partition["partition_id"],
                        "binding_status": partition["binding_status"],
                        "frames": partition["frame_count"],
                        "instances": partition.get("instance_count"),
                        "phantoms": partition.get("phantom_count"),
                        # BC-DATA-23 (5)/(7)：逐 partition 如实报告交叉验证诊断，
                        # 这是诊断计数，不是 G0 verdict。
                        "cross_validation": layout["cross_validation"].get(
                            partition["partition_id"]
                        ),
                    }
                    for partition in partitions
                ),
                key=lambda item: item["partition_id"],
            ),
            "bound_frames": bound_frames,
            "unbound_source_units": sorted(
                unit
                for family in layout["families"].values()
                for unit in family["unbound_source_units"]
            ),
            "invalid_partitions": sorted(
                partition["partition_id"]
                for partition in partitions
                if partition["binding_status"] != bind_layout.BINDING_BOUND
            ),
        }


def _frame_index(frame_relative: str) -> int | None:
    stem = Path(frame_relative).stem
    digits = stem.rsplit("_", 1)[-1]
    return int(digits) if digits.isdigit() else None


def default_stage_order(driver: PipelineDriver) -> list[tuple[str, Any]]:
    """`--run` 的固定阶段序（S6 人工审计不在其中：driver 不执行审计）。"""
    return [
        ("contract", driver.stage0_contract),
        ("inventory", driver.stage1_inventory),
        ("layout", driver.stage2_layout),
        ("frames_catalog", driver.stage3_frames_catalog),
        ("splits", driver.stage4_splits),
        ("field_catalog", driver.stage5_field_catalog),
        ("g0_report", driver.stage7_gate),
        ("mother_set", driver.stage8_mother_set),
    ]


def first_unpublished_stage(
    driver: PipelineDriver, order: list[tuple[str, Any]]
) -> str | None:
    """相对**被 supersede 的 attempt** 的首个未发布阶段（§2.2 第 5 条）。

    attempt-2 在某阶段发布前失败时，attempt-3 从该阶段起重跑；此前已发布的
    阶段**不重发**，下游按 BC-SURVEY-4 回退读它们。attempt ≤ 2 没有可续跑的
    参照，返回 `None`（从头跑）。
    """
    current = driver._attempt_number()
    if current <= 2:
        return None
    reference = f"attempt-{current - 1}"
    for name, _step in order:
        if name not in artifacts_module.STAGES:
            continue
        if not driver._store.path_for(name, reference).exists():
            return name
    return None


def run_stages(
    driver: PipelineDriver,
    order: list[tuple[str, Any]],
    through: str,
    emit: Any = print,
    resume: bool = True,
) -> list[dict[str, Any]]:
    """按序推进并在收束点写 S9；`--run` 的全部流程判断都在这里，便于复核。

    `resume=True`（生产默认）时按 §2.2 第 5 条从首个未发布阶段起跑：把此前
    已在被 supersede 的 attempt 上发布的阶段整体跳过，从而让 BC-SURVEY-4 的
    「attempt-3 优先、否则 attempt-2」回退在**生产入口**真正发生，而不是只在
    逐阶段直接调用的测试里可达（复核 R1@stageA F2）。
    """
    results: list[dict[str, Any]] = []
    resume_note: dict[str, Any] | None = None
    if resume:
        start = first_unpublished_stage(driver, order)
        if start is not None:
            skipped = []
            for index, (name, _step) in enumerate(order):
                if name == start:
                    order = order[index:]
                    break
                skipped.append(name)
            if skipped:
                resume_note = {"from": start, "skipped": skipped}

    # 复核 R2@stageA F5：`--through` 是操作员的执行停止界（DATA-001 接受轮 28
    # 「只放行一次 S3→S4→S5」），不是提示。续跑把它指向的阶段整体跳过后，
    # 循环里的 `name == through` 永不命中，工具会一路跑到 S7 并沿途写出
    # create-once 工件——那些工件按合同永不删除，且占用该 attempt 身份。
    # 停止界不在实际会跑的阶段序里时，**一个阶段也不跑**。
    runnable = [name for name, _step in order]
    if through not in runnable:
        detail = (
            f"；续跑从 {resume_note['from']} 起，"
            f"已发布并被跳过的阶段：{resume_note['skipped']}"
            if resume_note is not None
            else ""
        )
        raise PipelineError(
            f"--through {through} 不在本次会跑的阶段序 {runnable} 内{detail}。"
            "停止界必须落在实际会跑的阶段上：若该阶段已发布则无须重跑（§2.2 "
            "第 5 条禁止重发），若拼写有误请更正；本次零阶段、零写入"
        )

    if resume_note is not None:
        emit(
            json.dumps(
                {
                    "resumed_from": resume_note["from"],
                    "skipped_published_stages": resume_note["skipped"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        results.append({"resume": dict(resume_note)})

    def _stop(outcome: str, detail: dict[str, Any]) -> list[dict[str, Any]]:
        stop = driver.stage9_stop_point(outcome, detail)
        emit(json.dumps({"stop_point": stop}, ensure_ascii=False, sort_keys=True))
        results.append({"stop_point": stop})
        return results

    for name, step in order:
        result = step()
        results.append({name: result})
        emit(json.dumps({name: result}, ensure_ascii=False, sort_keys=True))
        if result.get("terminal"):
            # BC-DATA-2 收束终态：保全已有工件、S8 永不执行。
            return _stop(result["terminal"], result)
        if name == "g0_report" and result["gate"] != g0_report.GATE_OPEN:
            # 门未过 → 以 INSUFFICIENT_SYMBOLIC_GROUNDING_DATA 收束，不进 S8。
            return _stop(STOP_GATE_CLOSED, result)
        if name == "mother_set":
            return _stop(STOP_GATE_OPEN, result)
        if name == through:
            break
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P1-VLM-DATA-001 S0–S9 生产 driver（默认只跑只读 preflight）"
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--attempt", default="attempt-1")
    # 前身由 driver 按阶段从 store 解析（复核 R1@stageA F1）；操作员只给归因。
    parser.add_argument(
        "--supersession-reason", default=None, help="supersession 归因（attempt ≥ 2 必填）"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="执行会落盘的阶段；缺省只跑 preflight。真实归档上的完整运行需用户另行授权。",
    )
    parser.add_argument(
        "--through",
        default="g0_report",
        help="--run 时跑到哪个阶段为止（contract/inventory/layout/frames_catalog/"
        "splits/field_catalog/g0_report/mother_set）",
    )
    args = parser.parse_args(argv)

    driver = PipelineDriver(
        Path(args.repo_root).resolve(),
        args.attempt,
        supersession_reason=args.supersession_reason,
    )
    if not args.run:
        report = driver.preflight()
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    order = default_stage_order(driver)
    names = [name for name, _ in order]
    if args.through not in names:
        parser.error(f"--through 必须是 {names} 之一")
    run_stages(driver, order, args.through)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
