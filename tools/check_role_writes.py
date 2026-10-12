#!/usr/bin/env python3
"""按角色写入白名单核对当前工作批次的文件改动（仅标准库）。

对应 docs/collaboration-workflow.md §7 与 AGENTS.md 的角色边界：每个角色
收工提交前运行

    python3 tools/check_role_writes.py --role <role>

默认检查 `git status --porcelain`（含未跟踪文件）中的每个路径；出现该
角色白名单之外的路径即逐条列出并以非零码退出。已提交的批次可用
`--base <commit>` 改查 `git diff --name-only <commit>..HEAD`（注：原
workflow §4.3.1 条件 5 的停点归因义务已按 COORD-007 R2 移除，本模式
仅作诊断保留）。

角色语义见 docs/roles/。工作流基础设施（AGENTS.md、CLAUDE.md、
docs/collaboration-workflow.md、docs/engineering-workflow.md、.claude/、
.cursor/、docs/roles/、tools/check_*.py、tools/githooks/）对所有角色只读，
只能在用户直接授权的协调批次中修改。唯一例外（COORD-007 R5，复核角色除外）：非复核
角色修复自检工具假阴性/坏夹具的单独提交可只改 tools/check_*.py 与
tests/test_check_*.py，用 `--infra-fix` 模式核对该批次未越出这两类
路径；复核角色的五路径绝对禁令优先，缺陷只写复核文件。
"""

from __future__ import annotations

import argparse
from fnmatch import fnmatch
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 工作流基础设施：任何角色会话都不得修改（用户直接授权的协调批次除外）。
# COORD-007 R5：改用通配 tools/check_*.py，修复原先只点名三个字面工具、
# 其余 check 工具"规则说保护、工具不保护"的假阴性。
INFRA_PATTERNS = (
    "AGENTS.md",
    "CLAUDE.md",
    "docs/collaboration-workflow.md",
    # COORD-010 批 1（用户授权 2026-09-07）：工程流程规范与旧流程规范同级，
    # 常规角色只读。实现角色的 allow "*" 也先被本表拦下（见
    # violations_for_role 的 INFRA 优先分支），无须另设 deny 项。
    "docs/engineering-workflow.md",
    ".claude/*",
    ".cursor/*",
    "docs/roles/*",
    "tools/check_*.py",
    "tools/githooks/*",
)

# COORD-007 R5 自修复例外：单独提交只允许触碰这两类路径。
INFRA_FIX_PATTERNS = (
    "tools/check_*.py",
    "tests/test_check_*.py",
)

# allow：白名单模式（fnmatch，`*` 可跨路径分隔符）；deny：显式黑名单，
# 优先于 allow。实现角色采用"默认允许 + 黑名单"，其余角色采用白名单。
ROLE_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "ideation": {
        "allow": (
            "docs/proposals/*",
            "docs/current-status.md",
            "docs/archive/*",
            "docs/authorizations.md",
        ),
        "deny": (),
    },
    "acceptance": {
        "allow": (
            "docs/proposals/*",
            "docs/phase1-single-drone-design.md",
            "docs/current-status.md",
            "docs/implementation-status.md",
            "docs/unity-test-log.md",
            # COORD-007 R4：CLASS_3 逐字替换补丁与操作单修订由接受角色应用。
            "docs/evidence/*",
            "docs/archive/*",
            "docs/authorizations.md",
            # COORD-010 批 1：长期背景记忆（个人背景与项目长期目标）；
            # 只记背景与目标，不存任务进度、门状态或证据。
            "docs/project-background.md",
            # COORD-013（用户直接授权 2026-09-21）：非活跃项台账（事实源，开工不读）；
            # 关闭时整行移入、暂停时移入叙述，随 Lifecycle 由接受角色维护。
            "docs/parked-status.md",
        ),
        "deny": (),
    },
    "implementation": {
        "allow": ("*",),
        "deny": (
            "docs/reviews/*",
            "docs/design-reviews/*",
            "docs/proposals/*",
            "docs/phase1-single-drone-design.md",
            # 证据与信任根对实现者只读：Unity 日志由接受/辅助代录，
            # 授权账本中的实现会话授权转交接受/辅助记录。
            "docs/unity-test-log.md",
            "docs/authorizations.md",
        ),
    },
    "review": {
        "allow": (
            "docs/reviews/*",
            "docs/current-status.md",
            "docs/archive/*",
            "docs/authorizations.md",
        ),
        "deny": (),
    },
    "audit": {
        "allow": (
            "docs/design-reviews/*",
            "docs/current-status.md",
            "docs/archive/*",
            "docs/authorizations.md",
        ),
        "deny": (),
    },
    "supervisor": {
        "allow": (
            # COORD-015 §2.3（用户授权 2026-09-25 协调落地批次）：supervisor
            # 常规写权。U7 缺省 = B，docs/parked-status.md 不列入；tools/、
            # tests/ 只在用户逐字授权的协调批次内改，不在常规 allow 内。
            "docs/proposals/COORD-*.md",
            "docs/current-status.md",
            "docs/authorizations.md",
            "docs/unity-test-log.md",
            "docs/evidence/COORD-*",
            "docs/evidence/supervisor-dispatch.jsonl",
            "docs/project-background.md",
            "docs/workflow-changelog.md",
        ),
        "deny": (
            "docs/reviews/*",
            "docs/design-reviews/*",
            "docs/implementation-status.md",
            "docs/phase1-single-drone-design.md",
            "docs/status-history.md",
        ),
    },
    "chore": {
        "allow": (
            "docs/archive/*",
            "docs/current-status.md",
            "docs/unity-test-log.md",
            "docs/reviews/*-prescreen.md",
            "docs/authorizations.md",
            # COORD-010 批 1：辅助角色可代录长期背景记忆，同样不存任务进度。
            "docs/project-background.md",
            # COORD-012 U3（用户签字授权 2026-09-20）：状态板 `## Log` 压缩/删除
            # 移出叙述的单向沉淀池，写入方仅 chore（在压缩轮内移动而非复制）；
            # 不是事实源、不进必读、check_docs 不扫描，其余白名单角色不放宽。
            "docs/status-history.md",
        ),
        "deny": (),
    },
}


def run_git(args: list[str], repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=False
    )


def changed_paths_from_status(repo_root: Path) -> list[str] | None:
    result = run_git(["status", "--porcelain"], repo_root)
    if result.returncode != 0:
        return None
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:]
        # 重命名/复制行形如 "old -> new"，新旧路径都算本批次改动。
        for path in entry.split(" -> "):
            path = path.strip().strip('"')
            if path and path not in paths:
                paths.append(path)
    return paths


def changed_paths_from_base(repo_root: Path, base: str) -> list[str] | None:
    result = run_git(["diff", "--name-only", f"{base}..HEAD"], repo_root)
    if result.returncode != 0:
        return None
    paths: list[str] = []
    for line in result.stdout.splitlines():
        path = line.strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.rstrip("/")
    for pattern in patterns:
        if fnmatch(normalized, pattern):
            return True
        # 未跟踪目录在 porcelain 中只显示目录本身（如 "docs/roles/"），
        # 让 "docs/roles/*" 这类模式同时命中裸目录。
        if pattern.endswith("/*") and fnmatch(normalized, pattern[:-2]):
            return True
    return False


def violations_for_role(role: str, paths: list[str]) -> list[str]:
    rules = ROLE_RULES[role]
    violations = []
    for path in paths:
        if matches_any(path, INFRA_PATTERNS):
            violations.append(
                f"{path}（工作流基础设施对所有角色只读，仅用户直接授权的协调批次可改）"
            )
        elif matches_any(path, rules["deny"]) or not matches_any(path, rules["allow"]):
            violations.append(f"{path}（不在角色 '{role}' 的允许写入范围内）")
    return violations


def violations_for_infra_fix(paths: list[str]) -> list[str]:
    """COORD-007 R5 自修复例外：批次只许含 check 工具及其测试。"""
    return [
        f"{path}（--infra-fix 批次只允许 tools/check_*.py 与 tests/test_check_*.py）"
        for path in paths
        if not matches_any(path, INFRA_FIX_PATTERNS)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="按角色写入白名单核对本批次文件改动（角色语义见 docs/roles/）"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--role", choices=sorted(ROLE_RULES))
    mode.add_argument(
        "--infra-fix",
        action="store_true",
        help="COORD-007 R5 自修复例外：批次只许含 tools/check_*.py 与 tests/test_check_*.py",
    )
    parser.add_argument("--base", help="改查 <base>..HEAD 的已提交改动")
    parser.add_argument(
        "--root", type=Path, default=PROJECT_ROOT, help="仓库根目录（默认：本脚本所在仓库）"
    )
    args = parser.parse_args(argv)
    repo_root = args.root.resolve()
    if args.base:
        paths = changed_paths_from_base(repo_root, args.base)
    else:
        paths = changed_paths_from_status(repo_root)
    if paths is None:
        print("无法执行 git；请确认在仓库内运行且 base 引用存在。")
        return 2
    label = "--infra-fix" if args.infra_fix else f"角色 '{args.role}'"
    if args.infra_fix:
        violations = violations_for_infra_fix(paths)
    else:
        violations = violations_for_role(args.role, paths)
    if violations:
        print(f"{label} 写入范围检查未通过，共 {len(violations)} 个越权路径：")
        for index, violation in enumerate(violations, start=1):
            print(f"  {index}. {violation}")
        print("处置：恢复越权文件（git checkout -- <path>；未跟踪文件直接删除或移出仓库），")
        print("把发现改写进本角色的权威产出；确属需要的范围变更交回对应角色决定。")
        return 1
    scope = f"{args.base}..HEAD" if args.base else "未提交改动"
    print(
        f"{label} 写入范围检查通过（检查对象：{scope}，共 {len(paths)} 个路径）。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
