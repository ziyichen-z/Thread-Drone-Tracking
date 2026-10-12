#!/usr/bin/env python3
"""docs/authorizations.md 信封与代拍条目的机检（COORD-015 §5.4–5.6，仅标准库）。

默认模式（pre-commit）：对暂存的 docs/authorizations.md 做 §5.4 失败关闭、
§5.5 事件全序/历史合法性与 §5.6 事件型到期判定。待提交条目（暂存区有、
HEAD 中无其标题）按预提交视图判定：首父即当前 HEAD（precheck_head 须等于
HEAD）、D1 提案快照取当时 HEAD 的已提交提案、暂存的
docs/current-status.md 当作紧随 HEAD 的虚拟提交检查到期条件 (i)(ii)；
未暂存差异不参与。已入账的新格式条目按其首次入账提交复判：SUB 的
precheck_head 须为 commit(E) 首父，D1 提案快照取 commit(E) 首父的提案。

COORD-016（§2.1/§2.2，BC-1…3）：D1 判据改非递增（now > prev 拒绝）并按同
work ID 的 D1 条目累计 ≤ 3；新增 D7（预注册合同数值按接受角色推荐）：提案快照
（待提交：HEAD 已提交提案且 precheck_head == HEAD；历史：commit(E) 首父且
precheck_head 必须等于它）的 Status: 行以 `Status: ACCEPTED` 开头、该题
d7_range 恰 1 行且位于 BC/AC 表行条款格、kind=/bc= 各恰 1 次、d7_recommend
恰 1 行且不在 `### D<n>` 节；区间端点、闭集元素与推荐值均须为数值字面
（R1-1）；decision/range 逐字相等；区间用 decimal.Decimal 精确比较、闭集逐字
比较；同 (work_id, <id>) 第 2 条拒绝。
现存历史条目（无 at:、无机读行的旧格式）一律判为合法存量，机检只约束
信封块与代拍/撤销/否决新格式条目。

--first-invalidation <work_id> --envelope <标题>（§5.6 解析器，机检与
supervisor 运行时派发守卫共用）：输出该信封的 S（首次把标题写入账本的
提交）与 X（首次失效提交）；X 存在即退出码非零。日期型到期不用解析器。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = "docs/authorizations.md"
BOARD_PATH = "docs/current-status.md"
PROPOSALS_DIR = "docs/proposals"

D_CLASSES = ("D1", "D2a", "D2b", "D3", "D4", "D5", "D6", "D7")
DELEGATED_CLASSES = D_CLASSES + ("SUB",)

DELEGATED_KEYS = frozenset({
    "at", "delegated_class", "cites_decision_envelope",
    "cites_execution_envelope", "decision", "reason", "increment",
    "request_id", "counter_key", "dispatch_id", "precheck_head",
    "veto_until", "round", "open_items_now", "open_items_prev", "question_id",
    "range", "代录会话",
})
REVOKE_KEYS = frozenset({"at", "supervisor_envelope_revoke", "代录会话"})
VETO_KEYS = frozenset({"at", "代录会话"})
ENVELOPE_ENTRY_KEYS = frozenset({"at", "代录会话"})
DECISION_BLOCK_KEYS = frozenset({"enabled", "classes", "expires_at", "veto_window_days"})
SUB_BLOCK_KEYS = frozenset({"enabled", "max_increment", "max_total", "expires_at"})

HEADER_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) (\S+) — (\S.*?)\s*$")
MACHINE_RE = re.compile(r"^(?:- )?([A-Za-z_][A-Za-z0-9_]*|代录会话): (\S.*?)\s*$")
BLOCK_START_RE = re.compile(r"^(supervisor_decision_envelope|supervisor_subdelegation):\s*(?:#.*)?$")
BLOCK_KV_RE = re.compile(r"^ +([A-Za-z_][A-Za-z0-9_]*): (\S.*?)\s*$")
COMMENT_RE = re.compile(r"\s+#.*$")
SHA_RE = re.compile(r"[0-9a-f]{40}")
ROUND_RE = re.compile(r"D(\d+)")
SHORTNAME_RE = re.compile(r"[A-Z]+\d+")
OPEN_ITEMS_RE = re.compile(r"^\s*open_items:\s*(\S.*?)\s*$")
SECTION_END_RE = re.compile(r"^#{1,3} ")

D1_MAX_PER_WORK_ID = 3  # COORD-016 §2.1 / U1=A
D7_KINDS = ("门值", "最小样本量", "阈值", "容差")
D7_ID_RE = re.compile(r"[A-Za-z0-9_.-]+")
D7_NUMBER_RE = re.compile(r"-?[0-9]+(?:\.[0-9]+)?")
D7_RANGE_FRAGMENT_RE = re.compile(r"d7_range:[^`|]*")
D7_RANGE_BODY_RE = re.compile(r"^d7_range: (\S+) in (\[[^\]]*\]|\{[^}]*\})((?: \S+)*)$")
D7_RECOMMEND_RE = re.compile(r"^(?:- )?d7_recommend: (\S+) = (\S+)$")
ROUND_HEADING_RE = re.compile(r"^### D\d+(?![0-9A-Za-z])")


@dataclass
class Entry:
    date: str
    work_id: str
    title: str
    pos: int
    kind: str = "legacy"
    fields: dict = field(default_factory=dict)
    blocks: dict = field(default_factory=dict)


def parse_entries(text: str) -> list:
    entries = []
    current = None
    block_name = None
    for index, line in enumerate(text.splitlines()):
        header = HEADER_RE.match(line)
        if header:
            current = Entry(date=header.group(1), work_id=header.group(2),
                            title=header.group(3), pos=index)
            entries.append(current)
            block_name = None
            continue
        if current is None:
            continue
        start = BLOCK_START_RE.match(line)
        if start:
            block_name = start.group(1)
            current.blocks.setdefault(block_name, {})
            continue
        if block_name is not None:
            kv = BLOCK_KV_RE.match(line)
            if kv:
                current.blocks[block_name][kv.group(1)] = COMMENT_RE.sub("", kv.group(2)).strip()
                continue
            block_name = None
        machine = MACHINE_RE.match(line)
        if machine:
            current.fields.setdefault(machine.group(1), machine.group(2))
    for entry in entries:
        entry.kind = _classify(entry)
    return entries


def _classify(entry: Entry) -> str:
    if "用户撤回信封：" in entry.title:
        return "revoke"
    if "用户否决代拍：" in entry.title:
        return "veto"
    if "supervisor 代拍：" in entry.title:
        return "delegated"
    if entry.blocks:
        return "envelope"
    return "legacy"


def parse_bool(raw: str):
    if raw == "true":
        return True
    if raw == "false":
        return False
    return None


def parse_nonneg_int(raw: str):
    if not re.fullmatch(r"-?\d+", raw):
        return None
    value = int(raw)
    return value if value >= 0 else None


def parse_dim_map(raw: str):
    raw = raw.strip()
    if not (raw.startswith("{") and raw.endswith("}")):
        return None
    inner = raw[1:-1].strip()
    if not inner:
        return {}
    result = {}
    for part in inner.split(","):
        key, sep, value = part.partition(":")
        if not sep:
            return None
        key = key.strip()
        number = parse_nonneg_int(value.strip())
        if not key or number is None:
            return None
        result[key] = number
    return result


def parse_class_list(raw: str):
    raw = raw.strip()
    if not (raw.startswith("[") and raw.endswith("]")):
        return None
    inner = raw[1:-1].strip()
    if not inner:
        return []
    return [part.strip() for part in inner.split(",")]


def parse_datetime(raw: str):
    # §5.4：at:/veto_until 只接受 UTC，后缀必须是 Z 或 +00:00；其他偏移失败关闭。
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    elif not raw.endswith("+00:00"):
        return None
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if moment.utcoffset() != timedelta(0):
        return None
    return moment.astimezone(timezone.utc)


def parse_date(raw: str):
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_expires_tokens(raw: str) -> list:
    parsed = parse_class_list(raw)
    tokens = parsed if parsed is not None else [raw.strip()]
    return [token for token in tokens if token]


def order_key(entry: Entry):
    moment = parse_datetime(entry.fields.get("at", ""))
    if moment is None:
        day = parse_date(entry.date)
        moment = (datetime.combine(day, time.min, timezone.utc) if day
                  else datetime.min.replace(tzinfo=timezone.utc))
    # §5.5：at: 与日期都相同时按文件位置，同日靠上者更新（账本最新在前），
    # 故位置取反：pos 越小键越大（越新）。所有先后比较均为「键小 = 更早」。
    return (moment, entry.date, -entry.pos)


def envelope_enabled(entry: Entry) -> bool:
    for block in entry.blocks.values():
        if parse_bool(block.get("enabled", "")) is False:
            return False
    return True


def envelope_stop(entry: Entry):
    block = entry.blocks.get("supervisor_subdelegation")
    if not block:
        return None
    for token in parse_expires_tokens(block.get("expires_at", "")):
        if re.fullmatch(SHORTNAME_RE, token):
            return token
    return None


def envelope_date_expiries(entry: Entry, block_name: str) -> list:
    block = entry.blocks.get(block_name) or {}
    return [day for day in
            (parse_date(token) for token in parse_expires_tokens(block.get("expires_at", "")))
            if day]


def _label(entry: Entry) -> str:
    return f"第 {entry.pos + 1} 行条目「{entry.title}」"


def structural_errors(entries: list) -> list:
    errors = []
    for entry in entries:
        if entry.kind != "legacy":
            errors.extend(_entry_errors(entry))
    errors.extend(_cross_errors(entries))
    return errors


def _entry_errors(entry: Entry) -> list:
    label = _label(entry)
    errors = []
    allowed = {"delegated": DELEGATED_KEYS, "revoke": REVOKE_KEYS,
               "veto": VETO_KEYS}.get(entry.kind, ENVELOPE_ENTRY_KEYS)
    for key in sorted(set(entry.fields) - allowed):
        errors.append(f"{label}：未知机读键 {key}")
    at_raw = entry.fields.get("at")
    if entry.kind in ("delegated", "revoke", "envelope", "veto") and at_raw is None:
        errors.append(f"{label}：缺必填 at:（ISO 8601 UTC）")
    elif at_raw is not None and parse_datetime(at_raw) is None:
        errors.append(f"{label}：at: 不是可解析的 ISO 8601 UTC 时间戳")
    if entry.kind == "delegated":
        errors.extend(_delegated_errors(entry, label))
    elif entry.kind == "revoke":
        errors.extend(_revoke_errors(entry, label))
    elif entry.kind == "envelope":
        errors.extend(_envelope_errors(entry, label))
    return errors


def _delegated_errors(entry: Entry, label: str) -> list:
    errors = []
    cls = entry.fields.get("delegated_class")
    if cls is None:
        errors.append(f"{label}：缺必填 delegated_class")
    elif cls not in DELEGATED_CLASSES:
        errors.append(f"{label}：delegated_class 不在闭集：{cls}")
    for key in ("decision", "counter_key"):
        if not entry.fields.get(key):
            errors.append(f"{label}：缺必填 {key}")
    if cls is not None and cls not in ("D1", "D7") and not entry.fields.get("reason"):
        errors.append(f"{label}：缺必填 reason（D1、D7 之外必填）")
    if not re.fullmatch(SHA_RE, entry.fields.get("precheck_head", "")):
        errors.append(f"{label}：缺必填 precheck_head 或不是 40 位 SHA")
    if cls == "SUB":
        if not entry.fields.get("cites_execution_envelope"):
            errors.append(f"{label}：SUB 缺必填 cites_execution_envelope")
        if entry.fields.get("cites_decision_envelope"):
            errors.append(f"{label}：SUB 引用决策信封")
        if entry.fields.get("veto_until"):
            errors.append(f"{label}：SUB 不得写 veto_until（无否决窗口）")
        if not entry.fields.get("request_id"):
            errors.append(f"{label}：SUB 缺必填 request_id")
        increment = entry.fields.get("increment")
        if increment is None:
            errors.append(f"{label}：SUB 缺必填 increment")
        elif parse_dim_map(increment) is None:
            errors.append(f"{label}：increment 含负数、非整数或非有限值，或不是 {{维度: n}} 映射")
    if cls in D_CLASSES:
        if not entry.fields.get("cites_decision_envelope"):
            errors.append(f"{label}：D 类缺必填 cites_decision_envelope")
        if entry.fields.get("cites_execution_envelope"):
            errors.append(f"{label}：D 类引用执行信封")
        veto_until = entry.fields.get("veto_until")
        if not veto_until:
            errors.append(f"{label}：D 类缺必填 veto_until")
        elif parse_datetime(veto_until) is None:
            errors.append(f"{label}：veto_until 不是可解析的时间戳")
        for key in ("increment", "request_id"):
            if entry.fields.get(key):
                errors.append(f"{label}：D 类不得写 {key}（仅 SUB）")
    if cls == "D1":
        if not re.fullmatch(ROUND_RE, entry.fields.get("round", "")):
            errors.append(f"{label}：D1 缺必填 round: D<n>")
        for key in ("open_items_now", "open_items_prev"):
            if parse_nonneg_int(entry.fields.get(key, "")) is None:
                errors.append(f"{label}：D1 缺必填 {key} 或不是非负整数")
    if cls == "D7":
        question_id = entry.fields.get("question_id")
        if not question_id:
            errors.append(f"{label}：D7 缺必填 question_id")
        elif not re.fullmatch(D7_ID_RE, question_id):
            errors.append(f"{label}：D7 question_id 不匹配 [A-Za-z0-9_.-]+：{question_id}")
        if not entry.fields.get("range"):
            errors.append(f"{label}：D7 缺必填 range（逐字复制 d7_range 行片段）")
    return errors


def _revoke_errors(entry: Entry, label: str) -> list:
    errors = []
    target = entry.fields.get("supervisor_envelope_revoke")
    if not target:
        errors.append(f"{label}：缺必填 supervisor_envelope_revoke: <标题>")
    else:
        suffix = entry.title.split("用户撤回信封：", 1)[1].strip()
        if suffix != target.strip():
            errors.append(f"{label}：标题与 supervisor_envelope_revoke 值不一致")
    return errors


def _envelope_errors(entry: Entry, label: str) -> list:
    errors = []
    for name, block in entry.blocks.items():
        allowed = DECISION_BLOCK_KEYS if name == "supervisor_decision_envelope" else SUB_BLOCK_KEYS
        for key in sorted(set(block) - allowed):
            errors.append(f"{label}：信封块 {name} 未知键 {key}")
        if parse_bool(block.get("enabled", "")) is None:
            errors.append(f"{label}：信封块 {name} 缺 enabled: true/false")
        expires = block.get("expires_at")
        if not expires:
            errors.append(f"{label}：信封块 {name} 缺必填 expires_at")
        else:
            tokens = parse_expires_tokens(expires)
            if not tokens:
                errors.append(f"{label}：信封块 {name} expires_at 为空")
            for token in tokens:
                if parse_date(token) is None and not re.fullmatch(SHORTNAME_RE, token):
                    errors.append(f"{label}：expires_at 含无法解析的停点/日期：{token}")
            if (name == "supervisor_decision_envelope" and tokens
                    and any(parse_date(token) is None for token in tokens)):
                errors.append(f"{label}：决策信封 expires_at 须为日期型")
        if name == "supervisor_decision_envelope":
            classes = block.get("classes")
            parsed = parse_class_list(classes) if classes else None
            if not parsed:
                errors.append(f"{label}：决策信封缺 classes 闭集列表")
            else:
                for cls in parsed:
                    if cls not in D_CLASSES:
                        errors.append(f"{label}：classes 含闭集外类：{cls}")
            if parse_nonneg_int(block.get("veto_window_days", "")) is None:
                errors.append(f"{label}：决策信封缺必填 veto_window_days 或不是非负整数")
        else:
            for key in ("max_increment", "max_total"):
                mapping = block.get(key)
                if mapping is None:
                    errors.append(f"{label}：子额度块缺必填 {key}")
                elif parse_dim_map(mapping) is None:
                    errors.append(f"{label}：{key} 含负数、非整数或非有限值，或不是映射")
    return errors


def _cross_errors(entries: list) -> list:
    errors = []
    news = [entry for entry in entries if entry.kind != "legacy"]
    by_title = {}
    for entry in news:
        by_title.setdefault(entry.title, []).append(entry)
    for title, group in by_title.items():
        if len(group) > 1:
            revocation = (all(entry.kind == "envelope" for entry in group)
                          and sum(1 for entry in group if envelope_enabled(entry)) == 1)
            if not revocation:
                errors.append(f"同标题重复条目：「{title}」出现 {len(group)} 次")
    envelopes = {}
    for entry in news:
        if entry.kind == "envelope" and envelope_enabled(entry) and entry.title not in envelopes:
            envelopes[entry.title] = entry
    revocations = []
    for entry in news:
        if entry.kind == "revoke":
            revocations.append((order_key(entry), entry.fields.get("supervisor_envelope_revoke", "")))
        elif entry.kind == "envelope" and not envelope_enabled(entry):
            revocations.append((order_key(entry), entry.title))
    delegated = sorted((entry for entry in news if entry.kind == "delegated"), key=order_key)
    seen_request_ids = set()
    seen_counter_keys = set()
    seen_d1_rounds = set()
    d1_counts = {}
    seen_d7_ids = set()
    cumulative = {}
    for entry in delegated:
        label = _label(entry)
        cls = entry.fields.get("delegated_class")
        request_id = entry.fields.get("request_id")
        if request_id:
            if request_id in seen_request_ids:
                errors.append(f"{label}：同一 request_id 已有条目（{request_id}）")
            seen_request_ids.add(request_id)
        counter_key = entry.fields.get("counter_key")
        if counter_key:
            if counter_key in seen_counter_keys:
                errors.append(f"{label}：counter_key 超该类次数上限（{counter_key} 重复）")
            seen_counter_keys.add(counter_key)
        if cls == "D1":
            round_match = re.fullmatch(ROUND_RE, entry.fields.get("round", ""))
            if round_match:
                d1_key = (entry.work_id, int(round_match.group(1)))
                if d1_key in seen_d1_rounds:
                    errors.append(f"{label}：同一轮第二条 D1 代拍（{entry.work_id} D{round_match.group(1)}）")
                seen_d1_rounds.add(d1_key)
            # COORD-016 §2.1 / BC-1：同 work ID 的 D1 条目累计 ≤ 3；计数含已入账而后
            # 被否决/撤销的条目（全部代拍条目都计，不返还）。
            d1_counts[entry.work_id] = d1_counts.get(entry.work_id, 0) + 1
            if d1_counts[entry.work_id] > D1_MAX_PER_WORK_ID:
                errors.append(f"{label}：D1 代拍超每提案累计上限 {D1_MAX_PER_WORK_ID}"
                              f"（{entry.work_id} 第 {d1_counts[entry.work_id]} 条）")
        if cls == "D7":
            question_id = entry.fields.get("question_id")
            if question_id:
                d7_key = (entry.work_id, question_id)
                if d7_key in seen_d7_ids:
                    errors.append(f"{label}：D7 同一 <id> 第 2 条代拍"
                                  f"（计数键 {entry.work_id}:D7:{question_id}）")
                seen_d7_ids.add(d7_key)
        cited = (entry.fields.get("cites_execution_envelope") if cls == "SUB"
                 else entry.fields.get("cites_decision_envelope"))
        if not cited:
            continue
        env = envelopes.get(cited)
        if env is None:
            errors.append(f"{label}：引用的信封「{cited}」不存在")
            continue
        if cls == "SUB" and "supervisor_subdelegation" not in env.blocks:
            errors.append(f"{label}：SUB 引用决策信封")
            continue
        if cls in D_CLASSES and "supervisor_decision_envelope" not in env.blocks:
            errors.append(f"{label}：D 类引用执行信封")
            continue
        if env.work_id != entry.work_id:
            errors.append(f"{label}：串用他工作项信封（信封属 {env.work_id}）")
        entry_key = order_key(entry)
        if not order_key(env) < entry_key:
            errors.append(f"{label}：信封「{cited}」签发不先于代拍（事件全序）")
        block_name = "supervisor_subdelegation" if cls == "SUB" else "supervisor_decision_envelope"
        entry_day = parse_date(entry.date)
        for expiry in envelope_date_expiries(env, block_name):
            if entry_day and expiry < entry_day:
                errors.append(f"{label}：信封「{cited}」已于 {expiry.isoformat()} 到期")
        for revoke_key, target in revocations:
            if target == cited and revoke_key < entry_key:
                errors.append(f"{label}：信封「{cited}」已先于该代拍被撤销")
        if cls in D_CLASSES:
            classes = parse_class_list(env.blocks["supervisor_decision_envelope"].get("classes", "")) or []
            if cls not in classes:
                errors.append(f"{label}：类 {cls} 不在被引信封 classes")
        if cls == "SUB":
            block = env.blocks.get("supervisor_subdelegation", {})
            max_increment = parse_dim_map(block.get("max_increment", "")) or {}
            max_total = parse_dim_map(block.get("max_total", "")) or {}
            increment = parse_dim_map(entry.fields.get("increment", "")) or {}
            for dim, amount in increment.items():
                if dim not in max_increment or dim not in max_total:
                    errors.append(f"{label}：SUB 维度不在块内（{dim}）")
                    continue
                if amount > max_increment[dim]:
                    errors.append(f"{label}：increment 超 max_increment（{dim}: {amount} > {max_increment[dim]}）")
                total_key = (cited, dim)
                cumulative[total_key] = cumulative.get(total_key, 0) + amount
                if cumulative[total_key] > max_total[dim]:
                    errors.append(f"{label}：累计追加超 max_total（{dim}: {cumulative[total_key]} > {max_total[dim]}）")
    for entry in news:
        if entry.kind != "veto":
            continue
        label = _label(entry)
        target_title = entry.title.split("用户否决代拍：", 1)[1].strip()
        target = next((d for d in delegated if d.title == target_title), None)
        if target is None:
            errors.append(f"{label}：否决目标「{target_title}」不是已有代拍条目")
            continue
        veto_at = parse_datetime(entry.fields.get("at", ""))
        veto_until = parse_datetime(target.fields.get("veto_until", ""))
        if veto_at and veto_until and veto_at > veto_until:
            errors.append(f"{label}：否决晚于否决窗口 veto_until")
    return errors


def run_git(args: list, repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def show_file(repo: Path, ref: str, path: str):
    result = run_git(["show", f"{ref}:{path}"], repo)
    return result.stdout if result.returncode == 0 else None


def staged_file(repo: Path, path: str):
    result = run_git(["show", f":{path}"], repo)
    return result.stdout if result.returncode == 0 else None


def head_sha(repo: Path):
    result = run_git(["rev-parse", "--verify", "--quiet", "HEAD"], repo)
    return result.stdout.strip() if result.returncode == 0 else None


def first_commit_adding(repo: Path, needle: str, path: str):
    result = run_git(["log", "--reverse", "--first-parent", "--format=%H", "-S", needle, "--", path], repo)
    if result.returncode != 0:
        return None
    commits = result.stdout.split()
    return commits[0] if commits else None


def commits_touching(repo: Path, range_spec: str, path: str) -> list:
    result = run_git(["log", "--reverse", "--first-parent", "--format=%H", range_spec, "--", path], repo)
    if result.returncode != 0:
        return []
    return result.stdout.split()


def first_parent(repo: Path, sha: str):
    result = run_git(["rev-parse", "--verify", "--quiet", f"{sha}^"], repo)
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    return run_git(["merge-base", "--is-ancestor", older, newer], repo).returncode == 0


def _section_rows(text: str, section: str):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("## ") and section in line), None)
    if start is None:
        return [], []
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    if not rows:
        return [], []
    header = rows[0]
    body = [row for row in rows[1:] if not all(set(cell) <= set("-: ") for cell in row)]
    return header, body


def _column(header: list, name: str):
    return next((i for i, cell in enumerate(header) if name in cell), None)


def board_expired(text: str, work_id: str, stop: str) -> bool:
    header, rows = _section_rows(text, "Gate board")
    id_col = _column(header, "Work ID")
    lifecycle_col = _column(header, "Lifecycle")
    gate_row = next((row for row in rows
                     if id_col is not None and len(row) > id_col
                     and f"`{work_id}`" in row[id_col]), None)
    if gate_row is None:
        return True
    if (lifecycle_col is not None and len(gate_row) > lifecycle_col
            and gate_row[lifecycle_col].strip("`").strip() in ("PAUSED", "ENDED")):
        return True
    header, rows = _section_rows(text, "Active handoffs")
    id_col = _column(header, "Work ID")
    status_col = _column(header, "Status")
    if id_col is None or status_col is None:
        return True  # 表头或 Status 列缺失：无法判定即按到期处理（§5.4 失败关闭）
    pattern = re.compile(rf"AWAITING_C\d+_(?:AT_)?{re.escape(stop)}(?![0-9A-Za-z])")
    for row in rows:
        if (len(row) > max(id_col, status_col) and f"`{work_id}`" in row[id_col]
                and pattern.search(row[status_col])):
            return True
    return False


def resolve_x(repo: Path, work_id: str, stop: str, start: str, extra_board=None):
    board_text = show_file(repo, start, BOARD_PATH)
    if board_text is not None and board_expired(board_text, work_id, stop):
        return start
    for commit in commits_touching(repo, f"{start}..HEAD", BOARD_PATH):
        board_text = show_file(repo, commit, BOARD_PATH)
        if board_text is not None and board_expired(board_text, work_id, stop):
            return commit
    if extra_board is not None and board_expired(extra_board, work_id, stop):
        return "VIRTUAL"
    return None


def _find_proposal(repo: Path, ref: str, work_id: str):
    result = run_git(["ls-tree", "-r", "--name-only", ref, "--", PROPOSALS_DIR], repo)
    if result.returncode != 0:
        return None
    matches = [path for path in result.stdout.splitlines()
               if Path(path).name.startswith(f"{work_id}-") and path.endswith(".md")]
    return matches[0] if len(matches) == 1 else None


def _parse_open_items(raw: str):
    if raw == "none":
        return []
    ids = [part.strip() for part in raw.split(",")]
    if any(not item for item in ids) or len(set(ids)) != len(ids):
        return None
    return ids


def _round_open_items(lines: list, round_no: int):
    """BC-14：第 n 轮的 open_items: 取值 = 唯一 `### D<n>` 节内恰好 1 行且为节末非空行。

    节 = 唯一一行匹配 `^### D<n>(?![0-9A-Za-z])` 的标题起，至其后第一行匹配
    `^#{1,3} ` 的标题（不含）或文件尾止；与各节在文件中的先后无关。
    返回 (取值, None) 或 (None, 失败关闭原因)。
    """
    heading = re.compile(rf"^### D{round_no}(?![0-9A-Za-z])")
    starts = [index for index, line in enumerate(lines) if heading.match(line)]
    if len(starts) != 1:
        return None, (f"提案第 {round_no} 轮裁定节标题 `### D{round_no}` 有 {len(starts)} 行"
                      "（须恰好 1 行），无法定位该轮 open_items: 行")
    start = starts[0]
    end = next((index for index in range(start + 1, len(lines))
                if SECTION_END_RE.match(lines[index])), len(lines))
    body = lines[start + 1:end]
    matches = [index for index, line in enumerate(body) if OPEN_ITEMS_RE.match(line)]
    if len(matches) != 1:
        return None, (f"提案第 {round_no} 轮裁定节（`### D{round_no}`）内 open_items: 机读行有 "
                      f"{len(matches)} 行（须恰好 1 行）")
    last_nonempty = max(index for index, line in enumerate(body) if line.strip())
    if matches[0] != last_nonempty:
        return None, (f"提案第 {round_no} 轮裁定节（`### D{round_no}`）的 open_items: 行"
                      "不是该节最后一个非空行")
    return OPEN_ITEMS_RE.match(body[matches[0]]).group(1), None


def _d1_errors(repo: Path, entry: Entry, ref) -> list:
    label = _label(entry)
    round_match = re.fullmatch(ROUND_RE, entry.fields.get("round", ""))
    if not round_match:
        return []
    round_no = int(round_match.group(1))
    if round_no < 2:
        return [f"{label}：D1 代拍 round 须 >= D2（需上一轮基线）"]
    if ref is None:
        return [f"{label}：无法确定提案快照（commit(E) 无首父）"]
    path = _find_proposal(repo, ref, entry.work_id)
    if path is None:
        return [f"{label}：docs/proposals/ 下找不到唯一的 {entry.work_id}-*.md 提案快照"]
    lines = (show_file(repo, ref, path) or "").splitlines()
    now_raw, now_error = _round_open_items(lines, round_no)
    prev_raw, prev_error = _round_open_items(lines, round_no - 1)
    failures = [error for error in (now_error, prev_error) if error]
    if failures:
        return [f"{label}：{error}" for error in failures]
    now_items = _parse_open_items(now_raw)
    prev_items = _parse_open_items(prev_raw)
    if now_items is None or prev_items is None:
        return [f"{label}：提案 open_items: 行格式不合（空 ID 或重复 ID）"]
    errors = []
    now_field = parse_nonneg_int(entry.fields.get("open_items_now", ""))
    prev_field = parse_nonneg_int(entry.fields.get("open_items_prev", ""))
    if now_field is not None and now_field != len(now_items):
        errors.append(f"{label}：open_items_now={now_field} 与提案第 {round_no} 轮 open_items: 行（{len(now_items)} 项）不符")
    if prev_field is not None and prev_field != len(prev_items):
        errors.append(f"{label}：open_items_prev={prev_field} 与提案第 {round_no - 1} 轮 open_items: 行（{len(prev_items)} 项）不符")
    if len(now_items) > len(prev_items):
        errors.append(f"{label}：open_items 残留数增加（{len(now_items)} > {len(prev_items)}）")
    return errors


def _table_context(lines: list, index: int):
    """返回 index 所在表格的表头单元格列表（表格 = 连续以 | 开头的行块的首行）。"""
    start = index
    while start > 0 and lines[start - 1].lstrip().startswith("|"):
        start -= 1
    return _split_row(lines[start])


def _split_row(line: str) -> list:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _clean_cell(cell: str) -> str:
    return cell.replace("`", "").replace("*", "").strip()


def _d7_range_lines(lines: list, question_id: str) -> list:
    """快照内该 <id> 的 d7_range 片段所在行（行号, 片段）；一行多片段按多行计。"""
    found = []
    for index, line in enumerate(lines):
        for match in D7_RANGE_FRAGMENT_RE.finditer(line):
            fragment = match.group(0).strip()
            parts = fragment.split()
            if len(parts) >= 2 and parts[1] == question_id:
                found.append((index, fragment))
    return found


def _d7_parse_set(raw: str):
    """区间 [lo, hi] → ("interval", lo, hi)；闭集 {v1, v2} → ("set", [...])；不合语法 → None。"""
    inner = raw[1:-1]
    items = [item.strip() for item in inner.split(",")]
    if any(not item or " " in item for item in items):
        return None
    if raw.startswith("["):
        if len(items) != 2 or not all(re.fullmatch(D7_NUMBER_RE, item) for item in items):
            return None
        low, high = Decimal(items[0]), Decimal(items[1])
        if low > high:
            return None
        return ("interval", low, high)
    # COORD-016 R1-1（§2.2 语法闭集）：闭集元素同样须为数值字面（不带单位、不带指数）。
    if not all(re.fullmatch(D7_NUMBER_RE, item) for item in items):
        return None
    if len(set(items)) != len(items):
        return None
    return ("set", items)


def _d7_errors(repo: Path, entry: Entry, ref) -> list:
    """COORD-016 §2.2 / BC-2 / BC-3：D7 条目按提交前已提交、`Status: ACCEPTED` 的提案快照判定。"""
    label = _label(entry)
    question_id = entry.fields.get("question_id", "")
    if not re.fullmatch(D7_ID_RE, question_id):
        return []  # 结构错误已由 _entry_errors 报告
    if ref is None:
        return [f"{label}：D7 无法确定提案快照（commit(E) 无首父）"]
    path = _find_proposal(repo, ref, entry.work_id)
    if path is None:
        return [f"{label}：D7 docs/proposals/ 下找不到唯一的 {entry.work_id}-*.md 提案快照"]
    lines = (show_file(repo, ref, path) or "").splitlines()
    errors = []
    status = next((line for line in lines if line.startswith("Status:")), "")
    if not status.startswith("Status: ACCEPTED"):
        errors.append(f"{label}：D7 快照提案 Status: 行不以 `Status: ACCEPTED` 开头")
    ranges = _d7_range_lines(lines, question_id)
    if len(ranges) != 1:
        errors.append(f"{label}：D7 快照中题 {question_id} 的 d7_range 行有 {len(ranges)} 行（须恰好 1 行）")
    recommends = [(index, D7_RECOMMEND_RE.match(line.strip())) for index, line in enumerate(lines)
                  if line.strip().startswith(("d7_recommend:", "- d7_recommend:"))]
    mine = [(index, match) for index, match in recommends
            if match is not None and match.group(1) == question_id]
    malformed = [index for index, match in recommends if match is None
                 and question_id in lines[index].split()]
    if len(mine) + len(malformed) != 1 or malformed:
        errors.append(f"{label}：D7 快照中题 {question_id} 的 d7_recommend 行有 "
                      f"{len(mine) + len(malformed)} 行（须恰好 1 行且合 `d7_recommend: <id> = <值>`）")
    if len(ranges) != 1 or len(mine) != 1 or malformed:
        return errors
    range_index, fragment = ranges[0]
    rec_index, rec_match = mine[0]
    recommended = rec_match.group(2)
    # 推荐行须在非 `### D<n>` 裁定节（BC-3）：向上找最近的 1–3 级标题。
    heading = next((lines[i] for i in range(rec_index, -1, -1) if SECTION_END_RE.match(lines[i])), "")
    if ROUND_HEADING_RE.match(heading):
        errors.append(f"{label}：D7 d7_recommend 行位于 `### D<n>` 裁定节内（须在非 D 轮裁定节）")
    # 资格片段结构（BC-2）。
    line = lines[range_index]
    if len(D7_RANGE_FRAGMENT_RE.findall(line)) != 1:
        errors.append(f"{label}：D7 d7_range 所在行含多个片段（一行只含一个 <id>）")
    body = D7_RANGE_BODY_RE.match(fragment)
    parsed = _d7_parse_set(body.group(2)) if body else None
    if body is None or parsed is None:
        errors.append(f"{label}：D7 d7_range 片段语法不合：{fragment}")
    if fragment.count("kind=") != 1:
        errors.append(f"{label}：D7 d7_range 片段 kind= 须恰好 1 次")
    if fragment.count("bc=") != 1:
        errors.append(f"{label}：D7 d7_range 片段 bc= 须恰好 1 次")
    attrs = body.group(3).split() if body else []
    if any(not attr.startswith(("kind=", "bc=")) for attr in attrs):
        errors.append(f"{label}：D7 d7_range 片段含 kind=/bc= 之外的字段")
    kind = next((attr[len("kind="):] for attr in attrs if attr.startswith("kind=")), None)
    bc_value = next((attr[len("bc="):] for attr in attrs if attr.startswith("bc=")), None)
    if kind is not None and kind not in D7_KINDS:
        errors.append(f"{label}：D7 kind 不在闭集 {{{', '.join(D7_KINDS)}}}：{kind}")
    # 行绑定：片段位于 BC/AC 表行的条款格（第 2 格），bc= 等于行首格编号。
    in_clause = False
    if line.lstrip().startswith("|"):
        cells = _split_row(line)
        header = _table_context(lines, range_index)
        first = _clean_cell(cells[0]) if cells else ""
        in_clause = (len(cells) > 1 and len(header) > 1
                     and _clean_cell(header[0]) == "编号"
                     and _clean_cell(header[1]).startswith(("条款", "验收项"))
                     and re.fullmatch(r"(?:BC|AC)-\d+", first) is not None
                     and fragment in cells[1])
        if in_clause and bc_value is not None and bc_value != first:
            errors.append(f"{label}：D7 bc= 与所在行首格编号不符（bc={bc_value}，行首 {first}）")
    if not in_clause:
        errors.append(f"{label}：D7 d7_range 不在 BC/AC 表行的条款格内")
    # 条目字段逐字相等。
    if entry.fields.get("decision", "") != recommended:
        errors.append(f"{label}：D7 decision 与推荐值字面不逐字相等"
                      f"（decision={entry.fields.get('decision', '')}，推荐 {recommended}）")
    if entry.fields.get("range", "") != fragment:
        errors.append(f"{label}：D7 range 与快照 d7_range 片段不逐字相等")
    # 推荐值须为数值字面（区间与闭集同，COORD-016 R1-1）；再判在区间（精确十进制）或闭集（逐字）。
    if not re.fullmatch(D7_NUMBER_RE, recommended):
        errors.append(f"{label}：D7 推荐值不是数值字面：{recommended}")
    elif parsed is not None:
        if parsed[0] == "interval":
            if not parsed[1] <= Decimal(recommended) <= parsed[2]:
                errors.append(f"{label}：D7 推荐值出区间（{recommended} ∉ {body.group(2)}）")
        elif recommended not in parsed[1]:
            errors.append(f"{label}：D7 推荐值不在闭集（{recommended} ∉ {body.group(2)}）")
    return errors


def check_precommit(repo: Path) -> list:
    staged = staged_file(repo, LEDGER_PATH)
    if staged is None:
        staged = show_file(repo, "HEAD", LEDGER_PATH)
    if staged is None:
        return []
    head = head_sha(repo)
    head_text = show_file(repo, "HEAD", LEDGER_PATH) or ""
    entries = parse_entries(staged)
    errors = structural_errors(entries)
    head_titles = {entry.title for entry in parse_entries(head_text)}
    virtual_board = staged_file(repo, BOARD_PATH)
    if virtual_board is None:
        virtual_board = show_file(repo, "HEAD", BOARD_PATH)
    envelopes = {entry.title: entry for entry in entries
                 if entry.kind == "envelope" and envelope_enabled(entry)}
    for entry in entries:
        if entry.kind != "delegated":
            continue
        label = _label(entry)
        cls = entry.fields.get("delegated_class")
        precheck = entry.fields.get("precheck_head", "")
        pending = entry.title not in head_titles
        commit_e = None
        if pending:
            if head is None:
                errors.append(f"{label}：仓库尚无 HEAD，无法判定预提交视图")
                continue
            parent = head
            if precheck != head:
                errors.append(f"{label}：预提交视图要求 precheck_head == HEAD")
        else:
            commit_e = first_commit_adding(repo, entry.title, LEDGER_PATH)
            if commit_e is None:
                errors.append(f"{label}：找不到首次入账提交 commit(E)")
                continue
            parent = first_parent(repo, commit_e)
            if cls == "SUB" and (parent is None or precheck != parent):
                errors.append(f"{label}：precheck_head 不是 commit(E) 的首父")
            if cls == "D7" and (parent is None or precheck != parent):
                errors.append(f"{label}：D7 precheck_head 不是 commit(E) 的首父")
        if cls == "SUB":
            env = envelopes.get(entry.fields.get("cites_execution_envelope", ""))
            stop = envelope_stop(env) if env is not None else None
            if stop:
                start = first_commit_adding(repo, env.title, LEDGER_PATH)
                if start is None:
                    x = ("VIRTUAL" if virtual_board is not None
                         and board_expired(virtual_board, entry.work_id, stop) else None)
                else:
                    x = resolve_x(repo, entry.work_id, stop, start,
                                  extra_board=virtual_board if pending else None)
                if pending:
                    if x is not None:
                        errors.append(f"{label}：信封「{env.title}」已失效（X={x}），代拍拒绝")
                elif (x is not None and x != "VIRTUAL" and commit_e is not None
                      and (x == commit_e or is_ancestor(repo, x, commit_e))):
                    errors.append(f"{label}：首次失效提交 X={x} 不晚于 commit(E)，历史不合法")
        if cls == "D1":
            errors.extend(_d1_errors(repo, entry, "HEAD" if pending else parent))
        if cls == "D7":
            errors.extend(_d7_errors(repo, entry, "HEAD" if pending else parent))
    return errors


def first_invalidation(repo: Path, work_id: str, envelope_title: str):
    text = show_file(repo, "HEAD", LEDGER_PATH)
    if text is None:
        return None, None
    entries = parse_entries(text)
    env = next((entry for entry in entries
                if entry.kind == "envelope" and entry.title == envelope_title
                and envelope_enabled(entry)), None)
    start = first_commit_adding(repo, envelope_title, LEDGER_PATH)
    if env is None or start is None:
        return start, None
    stop = envelope_stop(env)
    if stop is None:
        return start, None
    return start, resolve_x(repo, work_id, stop, start)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="docs/authorizations.md 信封与代拍条目机检（COORD-015 §5.4–5.6；COORD-016 D1/D7）"
    )
    parser.add_argument("--first-invalidation", metavar="WORK_ID",
                        help="§5.6 解析器：解析该 work ID 引用信封的首次失效提交 X")
    parser.add_argument("--envelope", metavar="标题",
                        help="--first-invalidation 的信封标题")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT,
                        help="仓库根目录（默认：本脚本所在仓库）")
    args = parser.parse_args(argv)
    repo = args.root.resolve()
    if args.first_invalidation or args.envelope:
        if not (args.first_invalidation and args.envelope):
            print("--first-invalidation 与 --envelope 必须同时给出。")
            return 2
        start, x = first_invalidation(repo, args.first_invalidation, args.envelope)
        if start is None:
            print(f"未找到信封「{args.envelope}」的签发提交 S。")
            return 2
        print(f"S: {start}")
        if x is None:
            print("X: none（信封未失效）")
            return 0
        print(f"X: {x}（信封已失效；引用它的代拍与消耗性派发应拒绝）")
        return 1
    errors = check_precommit(repo)
    if errors:
        print(f"账本机检未通过，共 {len(errors)} 项：")
        for index, error in enumerate(errors, start=1):
            print(f"  {index}. {error}")
        return 1
    print("账本机检通过（COORD-015 §5.4–5.6）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
