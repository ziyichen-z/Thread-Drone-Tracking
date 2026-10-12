from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.check_role_writes import (
    ROLE_RULES,
    changed_paths_from_base,
    changed_paths_from_status,
    matches_any,
    violations_for_infra_fix,
    violations_for_role,
)


def run_git(args, cwd):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


class MatchesAnyTests(unittest.TestCase):
    def test_star_crosses_path_separators(self):
        self.assertTrue(matches_any("docs/archive/2026-07/x.md", ("docs/archive/*",)))

    def test_bare_untracked_directory_matches_dir_pattern(self):
        # porcelain 对未跟踪目录只给 "docs/roles/" 这样的裸目录行。
        self.assertTrue(matches_any("docs/roles/", ("docs/roles/*",)))
        self.assertTrue(matches_any(".cursor/", (".cursor/*",)))

    def test_prescreen_suffix_pattern(self):
        self.assertTrue(
            matches_any("docs/reviews/P1-X-001-prescreen.md", ("docs/reviews/*-prescreen.md",))
        )
        self.assertFalse(
            matches_any("docs/reviews/P1-X-001.md", ("docs/reviews/*-prescreen.md",))
        )


class ViolationsForRoleTests(unittest.TestCase):
    def test_review_flags_implementation_file(self):
        violations = violations_for_role("review", ["controller/tracker.py"])
        self.assertEqual(len(violations), 1)
        self.assertIn("controller/tracker.py", violations[0])

    def test_review_allows_review_and_status(self):
        paths = ["docs/reviews/P1-X-001.md", "docs/current-status.md"]
        self.assertEqual(violations_for_role("review", paths), [])

    def test_infra_is_read_only_for_every_role(self):
        for role in ROLE_RULES:
            violations = violations_for_role(role, ["tools/check_role_writes.py"])
            self.assertEqual(len(violations), 1, msg=f"role={role}")
            self.assertIn("工作流基础设施", violations[0])

    def test_every_check_tool_is_infra_protected(self):
        # COORD-007 R5：锁死 round-21 假阴性——通配 tools/check_*.py 必须
        # 覆盖全部 check 工具，而不是只点名三个字面名。
        for path in (
            "tools/check_track_env.py",
            "tools/check_anchor_placement.py",
            "tools/check_scene_body_margin.py",
        ):
            violations = violations_for_role("implementation", [path])
            self.assertEqual(len(violations), 1, msg=path)
            self.assertIn("工作流基础设施", violations[0])

    def test_acceptance_and_chore_can_write_project_background(self):
        # COORD-010 批 1（用户授权 2026-09-07）：长期背景记忆的唯一白名单增项，
        # 由接受/辅助角色维护；文件只记个人背景与项目长期目标。
        for role in ("acceptance", "chore"):
            self.assertEqual(
                violations_for_role(role, ["docs/project-background.md"]),
                [],
                msg=f"role={role}",
            )

    def test_project_background_not_opened_to_other_gate_roles(self):
        # 「其余权限一律不放宽」：构思/复核/设计审查仍在白名单外。
        for role in ("ideation", "review", "audit"):
            violations = violations_for_role(role, ["docs/project-background.md"])
            self.assertEqual(len(violations), 1, msg=f"role={role}")
            self.assertIn("允许写入范围", violations[0])

    def test_project_background_allowance_is_per_file(self):
        # 放行逐文件，不外溢到同名前缀的其他路径。
        for path in ("docs/project-background.md.bak", "docs/project-background/"):
            self.assertEqual(len(violations_for_role("chore", [path])), 1, msg=path)

    def test_engineering_workflow_is_infra_protected(self):
        # COORD-010 批 1：新增的工程流程规范与 AGENTS.md/CLAUDE.md/
        # collaboration-workflow.md 同级，常规角色一律只读；实现角色的
        # allow "*" 也必须被基础设施分支先行拦下。
        for role in ROLE_RULES:
            violations = violations_for_role(role, ["docs/engineering-workflow.md"])
            self.assertEqual(len(violations), 1, msg=f"role={role}")
            self.assertIn("工作流基础设施", violations[0])
        # COORD-007 R5 自修复例外只覆盖 check 工具及其测试，不含流程规范。
        violations = violations_for_infra_fix(["docs/engineering-workflow.md"])
        self.assertEqual(len(violations), 1)
        self.assertIn("--infra-fix", violations[0])

    def test_acceptance_can_write_evidence(self):
        # COORD-007 R4：接受角色应用 CLASS_3 补丁与操作单修订。
        self.assertEqual(
            violations_for_role(
                "acceptance", ["docs/evidence/P1-M3-BODY-001-arm-a-trial-1.md"]
            ),
            [],
        )

    def test_infra_fix_mode_scope(self):
        # COORD-007 R5 自修复例外：只许 check 工具及其测试。
        self.assertEqual(
            violations_for_infra_fix(
                ["tools/check_docs.py", "tests/test_check_docs.py"]
            ),
            [],
        )
        violations = violations_for_infra_fix(["controller/tracker.py"])
        self.assertEqual(len(violations), 1)
        self.assertIn("--infra-fix", violations[0])

    def test_implementation_cannot_touch_trust_roots(self):
        # 锁死审查发现 #1：账本与 Unity 日志对实现者只读。
        for path in (
            "docs/authorizations.md",
            "docs/unity-test-log.md",
            "docs/reviews/P1-X-001.md",
            "docs/proposals/P1-X-001-foo.md",
            "docs/phase1-single-drone-design.md",
        ):
            violations = violations_for_role("implementation", [path])
            self.assertEqual(len(violations), 1, msg=path)

    def test_implementation_allows_code_and_evidence(self):
        paths = [
            "controller/tracker.py",
            "Assets/Scripts/CoverageEvaluator.cs",
            "docs/evidence/P1-X-001-implementation.md",
            "docs/current-status.md",
        ]
        self.assertEqual(violations_for_role("implementation", paths), [])

    def test_chore_can_write_status_history_sink(self):
        # COORD-012 U3（用户签字授权 2026-09-20）：Log 压缩/删除移出叙述的
        # 沉淀池由 chore 在压缩轮内写入；其余白名单角色不放宽，放行逐文件。
        self.assertEqual(violations_for_role("chore", ["docs/status-history.md"]), [])
        for role in ("ideation", "acceptance", "review", "audit"):
            violations = violations_for_role(role, ["docs/status-history.md"])
            self.assertEqual(len(violations), 1, msg=f"role={role}")
            self.assertIn("允许写入范围", violations[0])
        for path in ("docs/status-history.md.bak", "docs/status-history/"):
            self.assertEqual(len(violations_for_role("chore", [path])), 1, msg=path)

    def test_acceptance_can_write_parked_status(self):
        # COORD-013（用户直接授权 2026-09-21）：非活跃项台账随 Lifecycle 变化由
        # 接受角色维护（关闭时整行移入、暂停时移入叙述）；实现角色默认允许；
        # 其余白名单角色不放宽，放行逐文件。
        self.assertEqual(violations_for_role("acceptance", ["docs/parked-status.md"]), [])
        self.assertEqual(violations_for_role("implementation", ["docs/parked-status.md"]), [])
        for role in ("ideation", "review", "audit", "chore"):
            violations = violations_for_role(role, ["docs/parked-status.md"])
            self.assertEqual(len(violations), 1, msg=f"role={role}")
        self.assertEqual(
            len(violations_for_role("acceptance", ["docs/parked-status.md.bak"])), 1
        )

    def test_chore_can_transcribe_ledger_but_not_reviews(self):
        self.assertEqual(
            violations_for_role("chore", ["docs/authorizations.md"]), []
        )
        self.assertEqual(
            len(violations_for_role("chore", ["docs/reviews/P1-X-001.md"])), 1
        )


class SupervisorRoleTests(unittest.TestCase):
    # COORD-015 §2.3 / §10 A1：supervisor 白名单（U7 缺省 B，parked 不列入；
    # tools/、tests/ 只在用户逐字授权的协调批次内改，常规写权不含）。
    def test_supervisor_cannot_write_p1_proposal(self):
        violations = violations_for_role("supervisor", ["docs/proposals/P1-X.md"])
        self.assertEqual(len(violations), 1)
        self.assertIn("docs/proposals/P1-X.md", violations[0])

    def test_supervisor_cannot_write_reviews(self):
        violations = violations_for_role("supervisor", ["docs/reviews/x.md"])
        self.assertEqual(len(violations), 1)
        self.assertIn("docs/reviews/x.md", violations[0])

    def test_supervisor_cannot_write_tests(self):
        violations = violations_for_role("supervisor", ["tests/x.py"])
        self.assertEqual(len(violations), 1)
        self.assertIn("tests/x.py", violations[0])

    def test_supervisor_cannot_write_infra(self):
        violations = violations_for_role("supervisor", ["AGENTS.md"])
        self.assertEqual(len(violations), 1)
        self.assertIn("工作流基础设施", violations[0])

    def test_supervisor_coord_batch_combo_passes(self):
        paths = [
            "docs/proposals/COORD-016-x.md",
            "docs/authorizations.md",
            "docs/evidence/supervisor-dispatch.jsonl",
        ]
        self.assertEqual(violations_for_role("supervisor", paths), [])

    def test_supervisor_parked_status_denied_by_default(self):
        # §13 U7 缺省 = B：parked 写权不给 supervisor。
        violations = violations_for_role("supervisor", ["docs/parked-status.md"])
        self.assertEqual(len(violations), 1)
        self.assertIn("docs/parked-status.md", violations[0])


class GitParsingTests(unittest.TestCase):
    def test_status_parses_rename_untracked_and_base_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(["init", "-q"], root)
            (root / "a.md").write_text("one\n", encoding="utf-8")
            run_git(["add", "-A"], root)
            run_git(["commit", "-q", "-m", "base"], root)

            run_git(["mv", "a.md", "b.md"], root)
            (root / "untracked.md").write_text("new\n", encoding="utf-8")
            paths = changed_paths_from_status(root)
            self.assertIn("a.md", paths)  # rename 的旧路径
            self.assertIn("b.md", paths)  # rename 的新路径
            self.assertIn("untracked.md", paths)

            run_git(["add", "-A"], root)
            run_git(["commit", "-q", "-m", "batch"], root)
            base_paths = changed_paths_from_base(root, "HEAD~1")
            self.assertIn("b.md", base_paths)
            self.assertIn("untracked.md", base_paths)

    def test_bad_base_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(["init", "-q"], root)
            self.assertIsNone(changed_paths_from_base(root, "no-such-ref"))


if __name__ == "__main__":
    unittest.main()
