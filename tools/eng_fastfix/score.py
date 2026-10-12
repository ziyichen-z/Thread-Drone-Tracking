"""P1-ENG-FASTFIX-001 §3.8 评分入口（真值读取者闭集 = 本文件 `score_*` 函数；AC-7、AC-16）。

真值（USER-4A 同批 CoverageEvaluator 产物）只在这里读，只用于给已落盘的回放/会话产物打分；运行时入口（`controller/`、
`tools/eng_fastfix/replay.py`、`meter.py`、`ledger.py`）不导入本模块（AC-12 静态导入图 + 毒化真值 + 打开审计）。
评分结果不回流到任何选择输入（点击、提示、候选键、KF 输入）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT))

from tools.eng_fastfix.common import ADMITTED_ROOT  # noqa: E402

IOU_PASS = 0.5


def score_truth_path() -> Path:
    return ADMITTED_ROOT / "play" / "diag-loop2-214005" / "m3_body_truth.jsonl"


def score_truth_rows(path: Path | None = None) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for line in Path(path or score_truth_path()).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[int(row["frame_id"])] = row
    return rows


def score_truth_box(row: Mapping[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not row or not row.get("truth_box_available") or not row.get("geometrically_visible", True):
        return None
    return (float(row["truth_box_x"]), float(row["truth_box_y"]), float(row["truth_box_width"]), float(row["truth_box_height"]))


def score_iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax, ay, aw, ah = (float(v) for v in a)
    bx, by, bw, bh = (float(v) for v in b)
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return 0.0 if union <= 0 else inter / union


def score_ac7(report: Mapping[str, Any], truth: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    """AC-7 判据：`on` 臂 n_committed ≥ 1 且全部提交实例在提交帧与真值 IoU ≥ 0.5 → PASS；n_committed = 0 →「无成功证据」
    不通过（不空真）；`off` 臂须零自动提交。另报其后 10 帧 IoU ≥ 0.5 比例（读数，带 n）。真值缺失的提交帧记 `truth_missing`
    并判不通过（不能空真）。"""
    rows = []
    on_committed = [r for r in report.get("injections", []) if r["arm"] == "on" and r["outcome"] == "committed"]
    for record in on_committed:
        follow = record.get("followed") or []
        commit = follow[0] if follow else {}
        truth_box = score_truth_box(truth.get(int(record["commit_frame"])))
        commit_iou = None if truth_box is None or commit.get("box_norm") is None else score_iou(commit["box_norm"], truth_box)
        later = []
        for item in follow[1:]:
            box = score_truth_box(truth.get(int(item["frame_id"])))
            if box is None:
                continue
            later.append(item.get("box_norm") is not None and score_iou(item["box_norm"], box) >= IOU_PASS)
        rows.append({
            "f_inj": record["f_inj"],
            "commit_frame": record["commit_frame"],
            "track_key": record.get("track_key"),
            "commit_iou": None if commit_iou is None else round(commit_iou, 4),
            "truth_missing": truth_box is None,
            "follow_iou_ge_0_5": [sum(later), len(later)],
        })
    n_committed = len(rows)
    off_commits = sum(r.get("auto_commits", 0) for r in report.get("injections", []) if r["arm"] == "off") + \
        len([r for r in report.get("injections", []) if r["arm"] == "off" and r["outcome"] == "committed"])
    all_ok = n_committed >= 1 and all(r["commit_iou"] is not None and r["commit_iou"] >= IOU_PASS for r in rows)
    if n_committed == 0:
        verdict = "NO_SUCCESS_EVIDENCE"
    elif all_ok and off_commits == 0:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"verdict": verdict, "n_committed": n_committed, "off_arm_auto_commits": off_commits, "rows": rows,
            "misbound": [r for r in rows if r["commit_iou"] is not None and r["commit_iou"] < IOU_PASS]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P1-ENG-FASTFIX-001 评分（真值只在这里读）")
    sub = parser.add_subparsers(dest="command", required=True)
    ac7 = sub.add_parser("ac7")
    ac7.add_argument("--run-dir", type=Path, required=True)
    arguments = parser.parse_args(argv)
    report = json.loads((arguments.run_dir / "replay-output.json").read_text(encoding="utf-8"))
    result = score_ac7(report, score_truth_rows())
    (arguments.run_dir / "score.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
