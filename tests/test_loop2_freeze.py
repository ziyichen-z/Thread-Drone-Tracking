"""P1-ENG-LOOP-002 AC-2 / AC-12（及 AC-13 的 PLAY_GOVERNING 禁改路径）：冻结件字节不变。

基线 = 本项阶段 A 派发块的 `base_head`（N-1 答复落实核销后的提交）；各冻结件的 sha 在运行时由
`git show <base>:<path>` 取得，不在本文件手抄任何文件 sha。基线对象不可得（浅克隆等）时跳过并说明。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: 阶段 A 派发块（Dispatch-Id `P1-ENG-LOOP-002-阶段A实现-20261006T231621Z-97fb`）的 `base_head`。
BASE_COMMIT = "259fe54cb2845397aa9bbd69378982d6620d5e8b"

#: AC-2：字节不变的冻结件。
FROZEN_FILES = (
    "controller/standoff_planner.py",
    "config/p1-eng-frame-001-body.json",
    "config/det-assoc-v1.models.json",
    "tools/eng_sft/prompt_v2.py",
    "tools/eng_sft/parse.py",
    "config/scenario.default.json",
)
#: AC-12：围栏读取代码（FRAME-001 R1-3 float32/float64 口径）diff 为空。
FENCE_FILES = ("controller/scenario_tether.py",)
#: §4.1 / AC-13：不在归属表内的 PLAY_GOVERNING 路径（出现在候选 diff 即不满足）。
PLAY_GOVERNING_FORBIDDEN = (
    "controller/standoff_planner.py",
    "controller/det_assoc_tracker.py",
    "controller/resident_core.py",
    "controller/track_loop.py",
    "controller/trackers.py",
    "controller/scenario_tether.py",
    "tools/eng_sft",
    "tools/eng_jet",
    "Assets",
)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, check=False)


def _base_available() -> bool:
    return _git("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}").returncode == 0


@unittest.skipUnless(_base_available(), "baseline commit object not available in this clone")
class Loop2FreezeTests(unittest.TestCase):
    def _base_sha(self, relative: str) -> str:
        completed = _git("show", f"{BASE_COMMIT}:{relative}")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return hashlib.sha256(completed.stdout).hexdigest()

    def test_frozen_files_are_byte_identical_to_the_baseline(self) -> None:
        for relative in FROZEN_FILES:
            with self.subTest(path=relative):
                current = hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(current, self._base_sha(relative))

    def test_fence_reading_code_has_no_diff(self) -> None:
        completed = _git("diff", "--name-only", BASE_COMMIT, "--", *FENCE_FILES)
        self.assertEqual(completed.stdout.decode().strip(), "")

    def test_play_governing_paths_outside_the_ownership_table_have_no_diff(self) -> None:
        completed = _git("diff", "--name-only", BASE_COMMIT, "--", *PLAY_GOVERNING_FORBIDDEN)
        self.assertEqual(completed.stdout.decode().strip(), "")
        scenarios = _git("diff", "--name-only", BASE_COMMIT, "--", "config")
        changed = [line for line in scenarios.stdout.decode().splitlines() if line.startswith("config/scenario.")]
        self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
