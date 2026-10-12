#!/usr/bin/env python3
"""COORD-016 §4 A3 / BC-5 具名路由检查（仅标准库）。

读规格文件（JSON）逐位置断言协调落地后的规则文本：

- `expected`：每项 {id, file, text, count}——当前工作树该文件中 `text` 恰好出现
  `count` 次（缺失或重复均失败）；
- `closure_markers`：每项 {marker, files}——标记词在所列文件中的实际出现总数
  必须等于 `expected` 中位于这些文件、且含该标记词的条目所贡献的次数之和，
  即规格的预期位置是闭集：文件里多出一处未列入规格的位置（漏列）或规格多列
  一处文件里没有的位置，均失败；
- `unchanged`：每项 {id, file, text}——`text` 必须在基线版本该文件中出现，且同时满足
  （C1-1 起绑定原位置，不再只比全文计数）：
  (1) 原位：基线中该句的**每一处**出现，在「基线→当前」对齐下落到当前文件的同一
      位置且逐字相同。对齐分两级（均为 difflib.SequenceMatcher，autojunk=False，
      结果确定）：先按行对齐（行 = 原文按换行切分、续行去行首空白后的片段，
      与下述归一化一致）；该句所跨各行都落在同一个「相同」行块内即为原位。否则
      取该句所跨行所在的改动块（上下以未改行为界；相同行块只截到该句所跨行）做
      字符级对齐，该句须整体落在一个「相同」字符段内。原位句被改写、删除，或被
      改写后在改动块以外另补一句旧句（C1-1 反例），都判失败；
  (2) 计数：当前全文出现次数与基线相同（复制到别处同样失败）。
  判据边界：同一改动块内，若结果文件可被解释为「原句逐字未动、其前后插删了其他
  内容」，按字符级对齐视为原位（结果文件与该解释逐字相同，任何只看结果的检查都
  无法区分）；改动块以外的补句一律不算原位。

基线 = `git log --reverse --format=%H --grep=<baseline_grep>` 的**第一个**提交的
首父（BC-5：不是最后一个同前缀提交的首父），运行时解析并打印。

比对前对文件文本与规格文本做同一归一化：删除每个换行及其后的行首空白
（Markdown 折行不影响句子），其余逐字比较。

退出码：0 全部通过；1 有位置失败；2 规格或基线无法解析。
"""

from __future__ import annotations

import argparse
import bisect
import difflib
import json
from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def normalize(text: str) -> str:
    return re.sub(r"\n[ \t]*", "", text)


def pieces(text: str) -> list:
    """按行切片并去续行行首空白；"".join(pieces(t)) == normalize(t)。"""
    lines = text.split("\n")
    return [lines[0]] + [line.lstrip(" \t") for line in lines[1:]]


def _starts(parts: list) -> list:
    starts = [0]
    for part in parts:
        starts.append(starts[-1] + len(part))
    return starts


def _find_all(body: str, text: str) -> list:
    """不重叠出现位置（与 str.count 同口径）。"""
    found, pos = [], body.find(text)
    while pos >= 0:
        found.append(pos)
        pos = body.find(text, pos + len(text))
    return found


def in_place(base_raw: str, cur_raw: str, text: str) -> list:
    """逐个检查基线中 `text`（已归一化）的出现是否在当前文件原位逐字保留。

    返回 [(基线行号, 当前行号或 None)]；当前行号为 None 即该处不在原位。
    """
    bp, cp = pieces(base_raw), pieces(cur_raw)
    bs, cs = _starts(bp), _starts(cp)
    bnorm, cnorm = "".join(bp), "".join(cp)
    ops = [op for op in difflib.SequenceMatcher(None, bp, cp, autojunk=False).get_opcodes()
           if op[2] > op[1]]  # 纯插入不占基线行

    def piece_of(offset):
        return bisect.bisect_right(bs, offset) - 1

    def op_of(index):
        return next(op for op in ops if op[1] <= index < op[2])

    def line_of_cur(offset):
        return bisect.bisect_right(cs, offset)  # 1 起算

    results = []
    size = len(text)
    for start in _find_all(bnorm, text):
        ia, ib = piece_of(start), piece_of(start + size - 1)
        oa, ob = op_of(ia), op_of(ib)
        if oa is ob and oa[0] == "equal":
            ja = oa[3] + (ia - oa[1])
            pos = cs[ja] + (start - bs[ia])
            ok = cnorm[pos:pos + size] == text
            results.append((ia + 1, line_of_cur(pos) if ok else None))
            continue
        # 改动块：相同行块截到该句所跨行，改动行块取整块，再做字符级对齐。
        r0, c0 = (ia, oa[3] + ia - oa[1]) if oa[0] == "equal" else (oa[1], oa[3])
        r1, c1 = (ib + 1, ob[3] + ib + 1 - ob[1]) if ob[0] == "equal" else (ob[2], ob[4])
        region_b, region_c = bnorm[bs[r0]:bs[r1]], cnorm[cs[c0]:cs[c1]]
        offset = start - bs[r0]
        pos = None
        for tag, i1, i2, j1, _ in difflib.SequenceMatcher(
                None, region_b, region_c, autojunk=False).get_opcodes():
            if tag == "equal" and i1 <= offset and offset + size <= i2:
                pos = cs[c0] + j1 + (offset - i1)
                break
        ok = pos is not None and cnorm[pos:pos + size] == text
        results.append((ia + 1, line_of_cur(pos) if ok else None))
    return results


def run_git(args: list, repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def resolve_baseline(repo: Path, grep: str):
    result = run_git(["log", "--reverse", "--format=%H", f"--grep={grep}"], repo)
    commits = result.stdout.split() if result.returncode == 0 else []
    if not commits:
        return None
    parent = run_git(["rev-parse", "--verify", "--quiet", f"{commits[0]}^"], repo)
    return parent.stdout.strip() if parent.returncode == 0 else None


def baseline_text(repo: Path, sha: str, path: str):
    result = run_git(["show", f"{sha}:{path}"], repo)
    return result.stdout if result.returncode == 0 else None


def current_text(repo: Path, path: str):
    file_path = repo / path
    return file_path.read_text(encoding="utf-8") if file_path.is_file() else None


def check(repo: Path, spec: dict):
    """返回 (baseline, 结果行列表, 失败数)；规格/基线错误抛 ValueError。"""
    for key in ("baseline_grep", "expected", "closure_markers", "unchanged"):
        if key not in spec:
            raise ValueError(f"规格缺字段 {key}")
    baseline = resolve_baseline(repo, spec["baseline_grep"])
    if baseline is None:
        raise ValueError(f"找不到匹配 {spec['baseline_grep']!r} 的提交或其首父，无法确定基线")
    ids = [item.get("id") for item in spec["expected"] + spec["unchanged"]]
    if any(not item for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("规格条目 id 缺失或重复")
    lines = [f"baseline: {baseline}（首个匹配 {spec['baseline_grep']} 的提交的首父）"]
    failures = 0
    cache = {}

    def current(path):
        if path not in cache:
            raw = current_text(repo, path)
            cache[path] = normalize(raw) if raw is not None else None
        return cache[path]

    for item in spec["expected"]:
        text = normalize(item["text"])
        body = current(item["file"])
        want = int(item["count"])
        got = body.count(text) if body is not None else 0
        if body is None:
            failures += 1
            lines.append(f"FAIL {item['id']} expected {item['file']}：文件不存在")
        elif got != want:
            failures += 1
            kind = "缺失" if got < want else "重复"
            lines.append(f"FAIL {item['id']} expected {item['file']}：出现 {got} 次，应为 {want} 次（{kind}）")
        else:
            lines.append(f"PASS {item['id']} expected {item['file']}：{got} 次")
    for item in spec["closure_markers"]:
        marker = normalize(item["marker"])
        files = item["files"]
        actual = sum((current(path) or "").count(marker) for path in files)
        listed = sum(int(entry["count"]) * normalize(entry["text"]).count(marker)
                     for entry in spec["expected"] if entry["file"] in files)
        if actual != listed:
            failures += 1
            lines.append(f"FAIL closure「{item['marker']}」：文件中出现 {actual} 次，规格预期位置合计 "
                         f"{listed} 次（漏列或多列）")
        else:
            lines.append(f"PASS closure「{item['marker']}」：{actual} 次 = 规格合计")
    for item in spec["unchanged"]:
        text = normalize(item["text"])
        raw_base = baseline_text(repo, baseline, item["file"])
        base_count = normalize(raw_base).count(text) if raw_base is not None else 0
        body = current(item["file"])
        now_count = body.count(text) if body is not None else 0
        if base_count == 0:
            failures += 1
            lines.append(f"FAIL {item['id']} unchanged {item['file']}：基线中找不到该句")
            continue
        raw_cur = current_text(repo, item["file"])
        placed = in_place(raw_base, raw_cur if raw_cur is not None else "", text)
        moved = [str(base_line) for base_line, cur_line in placed if cur_line is None]
        if moved:
            failures += 1
            lines.append(f"FAIL {item['id']} unchanged {item['file']}：基线第 {'、'.join(moved)} 行处的该句"
                         f"在当前原位不再逐字相同（改写、删除或移位；全文当前 {now_count} 次，基线 "
                         f"{base_count} 次）")
        elif now_count != base_count:
            failures += 1
            lines.append(f"FAIL {item['id']} unchanged {item['file']}：原位保留，但基线 {base_count} 次，当前 "
                         f"{now_count} 次（别处复制或增删）")
        else:
            where = "、".join(f"{b}→{c}" for b, c in placed)
            lines.append(f"PASS {item['id']} unchanged {item['file']}：与基线原位逐字相同（{now_count} 次；"
                         f"基线行→当前行 {where}）")
    return baseline, lines, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="COORD-016 A3 具名路由检查（规格文件逐位置断言）")
    parser.add_argument("--spec", type=Path, required=True, help="规格 JSON 路径")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="仓库根目录")
    args = parser.parse_args(argv)
    repo = args.root.resolve()
    spec_path = args.spec if args.spec.is_absolute() else repo / args.spec
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        _, lines, failures = check(repo, spec)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR 规格或基线无法解析：{error}")
        return 2
    for line in lines:
        print(line)
    total = len(lines) - 1
    if failures:
        print(f"路由检查未通过：{failures}/{total} 项失败。")
        return 1
    print(f"路由检查通过：{total}/{total} 项。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
