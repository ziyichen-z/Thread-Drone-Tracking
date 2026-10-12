from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import check_ledger as cl
from tools import make_supervisor_drill as drill

TOOL_PATH = Path(drill.__file__).resolve()


class DrillFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = drill.build_drill_repo(Path(self.tmp.name) / "fixture")

    def test_fixture_builds_expected_files(self):
        for rel in (
            "DRILL.md",
            "docs/current-status.md",
            "docs/authorizations.md",
            "docs/proposals/DRILL-001-synthetic-drill.md",
            "docs/evidence/DRILL-001-ledger.json",
            "docs/evidence/supervisor-dispatch.jsonl",
            "docs/roles/supervisor.md",
            ".claude/commands/supervisor.md",
        ):
            self.assertTrue((self.root / rel).exists(), msg=rel)

    def test_fixture_is_synthetic_git_repo(self):
        mark = drill.SYNTHETIC_MARK
        for rel in ("DRILL.md", "docs/current-status.md", "docs/authorizations.md"):
            self.assertIn(mark, (self.root / rel).read_text(encoding="utf-8"))
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root,
                                capture_output=True, text=True, check=True)
        self.assertRegex(result.stdout.strip(), r"^[0-9a-f]{40}$")
        subject = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=self.root,
                                 capture_output=True, text=True, check=True).stdout.strip()
        self.assertTrue(subject.startswith(f"{drill.DRILL_WORK_ID} D0 "), msg=subject)

    def test_fixture_ledger_passes_ledger_structural_check(self):
        text = (self.root / "docs/authorizations.md").read_text(encoding="utf-8")
        self.assertEqual(cl.structural_errors(cl.parse_entries(text)), [])

    def test_fixture_board_parseable_by_expiry_check(self):
        text = (self.root / "docs/current-status.md").read_text(encoding="utf-8")
        self.assertFalse(cl.board_expired(text, drill.DRILL_WORK_ID, "K4"))

    def test_inject_open_items_targets_round_section(self):
        # COORD-015 R2@落地 R2-1 债（COORD-016 §3/A5，BC-6）：open_items: 行须插入
        # `### D<round_no>` 节末，而非追加到文件尾；插入后 check_ledger 的 BC-14 节绑定可读出。
        proposal = self.root / "docs/proposals/DRILL-001-synthetic-drill.md"
        drill.inject_open_items(proposal, ["AD1-1", "AD1-2", "AD1-3"], 1)
        drill.inject_open_items(proposal, ["AD2-1"], 2)
        lines = proposal.read_text(encoding="utf-8").splitlines()
        self.assertEqual(cl._round_open_items(lines, 1), ("AD1-1, AD1-2, AD1-3", None))
        self.assertEqual(cl._round_open_items(lines, 2), ("AD2-1", None))

    def test_fixture_proposal_has_d7_sample_lines(self):
        # COORD-016 §3：夹具提案带 d7_range:/d7_recommend: 样例行（D7 演练用）。
        text = (self.root / "docs/proposals/DRILL-001-synthetic-drill.md").read_text(encoding="utf-8")
        self.assertIn("d7_range: ", text)
        self.assertIn("d7_recommend: ", text)


class DispatchLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = drill.build_drill_repo(Path(self.tmp.name) / "fixture")

    def test_event_roundtrip(self):
        events = [
            drill.dispatch_event("requested", "DRILL-001-D1-20260925T090000Z-ab12",
                                 role="ideation", round="D1", base_head="a" * 40,
                                 requested_at="2026-09-25T09:00:00Z"),
            drill.dispatch_event("started", "DRILL-001-D1-20260925T090000Z-ab12",
                                 runner_id="sub-1", started_at="2026-09-25T09:00:05Z"),
            drill.dispatch_event("end_confirmed", "DRILL-001-D1-20260925T090000Z-ab12",
                                 source="callback"),
            drill.dispatch_event("finished", "DRILL-001-D1-20260925T090000Z-ab12",
                                 report="合成报告", commits=["b" * 40],
                                 candidate="b" * 40),
        ]
        for event in events:
            drill.append_dispatch_event(self.root, event)
        loaded = drill.read_dispatch_log(self.root)
        self.assertEqual([e["event"] for e in loaded],
                         ["requested", "started", "end_confirmed", "finished"])
        self.assertTrue(all(e["synthetic"] for e in loaded))
        self.assertEqual(loaded[3]["candidate"], "b" * 40)

    def test_event_closed_sets_enforced(self):
        with self.assertRaises(ValueError):
            drill.dispatch_event("bogus", "d-1")
        with self.assertRaises(ValueError):
            drill.dispatch_event("end_confirmed", "d-1", source="magic")


class ScaffoldingTests(unittest.TestCase):
    def test_open_items_injection_matches_ledger_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            proposal = Path(tmp) / "proposal.md"
            proposal.write_text("# 合成\n", encoding="utf-8")
            proposal.write_text("# 合成\n\n### D2 裁定\n\n原文。\n\n### D1 裁定\n\n原文。\n",
                                encoding="utf-8")
            drill.inject_open_items(proposal, ["AD1-1", "AD1-2", "AD1-3"], 1)
            drill.inject_open_items(proposal, [], 2)
            lines = [m.group(1) for m in
                     (cl.OPEN_ITEMS_RE.match(l)
                      for l in proposal.read_text(encoding="utf-8").splitlines()) if m]
            self.assertEqual(lines, ["none", "AD1-1, AD1-2, AD1-3"])

    def test_open_items_line_format(self):
        self.assertEqual(drill.open_items_line(["AD2-1", "AD2-2"]),
                         "open_items: AD2-1, AD2-2")
        self.assertEqual(drill.open_items_line([]), "open_items: none")

    def test_commit_subject_and_trailers(self):
        subject = drill.commit_subject("DRILL-001", "D2", "合成提交")
        self.assertEqual(subject, "DRILL-001 D2 合成提交")
        trailers = drill.commit_trailers("DRILL-001-D2-20260925T100000Z-cd34", "ideation")
        self.assertEqual(trailers,
                         "Dispatch-Id: DRILL-001-D2-20260925T100000Z-cd34\n"
                         "Role-Check: ideation pass")

    def test_cli_generates_into_given_dest(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-fixture"
            result = subprocess.run(
                [sys.executable, str(TOOL_PATH), "--dest", str(dest)],
                capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((dest / "DRILL.md").exists())
            self.assertIn(drill.SYNTHETIC_MARK, result.stdout)


if __name__ == "__main__":
    unittest.main()
