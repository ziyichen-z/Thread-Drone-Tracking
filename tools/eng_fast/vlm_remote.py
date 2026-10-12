#!/usr/bin/env python3
"""P3 臂 B/C 的 5060 自含查询脚本（合同 §2.1「5060 侧」、§3.5.2–§3.5.3、§5）。

只做一件事：按 Mac 生成的盲索引（无 gold）逐条查询冻结 base（`Qwen/Qwen3-VL-2B-Instruct@89644892…`，
bf16、greedy、`max_new_tokens` 64、图像不缩放），结果逐行写 JSONL 回传 Mac 评分。
导入期只用标准库；torch/transformers/PIL 在 `run` 里延迟导入，Mac 端因此可以直接复用本模块的
解析器（单一事实源，`vlm_arms` 不另写一份）。

账本（动作前扣额、即时持久化，额度由索引头携带、Mac 端与 §5 对账）：
- base 启动 ≤ 4：每次加载模型前扣 1；
- 查询 ≤ 1,700（其中 `INVALID` 重试 ≤ 183）：每次 `generate` 前扣 1；到达即停，剩余记 `NOT_RUN(BUDGET)`。
smoke = `row_id` 字典序前 32 行（不额外查询）：某臂在这 32 行首次尝试的 `INVALID` 率 > 10% → 该臂
`STOPPED_FORMAT`，其余行 `NOT_RUN(STOPPED_FORMAT)`，不改 prompt 重试。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence

BASE_REPO = "Qwen/Qwen3-VL-2B-Instruct"
BASE_REVISION = "89644892e4d85e24eaac8bacfd4f463576704203"
MAX_NEW_TOKENS = 64
PROCESSOR_SIZE = {"shortest_edge": 65536, "longest_edge": 16777216}  # 与 prompt_v2.PROCESSOR_SIZE 相同：不缩放
SMOKE_ROWS = 32
SMOKE_INVALID_MAX = 0.10

STATUS_VALUES = ("unique", "ambiguous", "none")
INVALID = "INVALID"
ERR_TRUNCATED = "TRUNCATED"
ERR_JSON = "JSON_ERROR"
ERR_SCHEMA = "SCHEMA_ERROR"
ERR_RANGE = "INDEX_OUT_OF_RANGE"
ERR_DUPLICATE = "DUPLICATE_INDEX"
ERR_FEW = "AMBIGUOUS_FEWER_THAN_2"
TRUNCATING_FINISH_REASONS = frozenset({"length", "max_new_tokens", "TRUNCATED"})
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n?")


# --- 解析器（Mac 评分与 5060 smoke 判定共用）--------------------------------


def strip_fences(raw: str) -> tuple[str, int]:
    """与冻结 `tools/eng_sft/parse.strip_fences` 同式（逐字复刻，保持本脚本自含）。"""
    fences = len(_FENCE_RE.findall(raw))
    cleaned = _FENCE_RE.sub("", raw).replace("```", "")
    return cleaned.strip(), fences


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_index_reply(raw: str, allowed: Sequence[int], finish_reason: str | None = None) -> dict[str, Any]:
    """§3.5.3 闭集：`unique(k)` / `ambiguous(S)` / `none` / `INVALID`（非 JSON、缺字段、越界、重复、
    `ambiguous` 少于 2 个索引、截断）。键集合须逐字（与冻结解析器同样严格）。"""
    stripped, fences = strip_fences(raw or "")
    result: dict[str, Any] = {"status": INVALID, "indices": [], "error": None, "fence_stripped": fences}
    if finish_reason is not None and finish_reason in TRUNCATING_FINISH_REASONS:
        result["error"] = ERR_TRUNCATED
        return result
    try:
        document = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        result["error"] = ERR_JSON
        return result
    if not isinstance(document, dict) or document.get("status") not in STATUS_VALUES:
        result["error"] = ERR_SCHEMA
        return result
    allowed_set = set(int(v) for v in allowed)
    status = document["status"]
    if status == "none":
        if set(document) != {"status"}:
            result["error"] = ERR_SCHEMA
            return result
        result.update(status="none")
        return result
    if status == "unique":
        if set(document) != {"status", "index"} or not _is_int(document["index"]):
            result["error"] = ERR_SCHEMA
            return result
        if document["index"] not in allowed_set:
            result["error"] = ERR_RANGE
            return result
        result.update(status="unique", indices=[int(document["index"])])
        return result
    if set(document) != {"status", "indices"} or not isinstance(document["indices"], list):
        result["error"] = ERR_SCHEMA
        return result
    values = document["indices"]
    if not all(_is_int(v) for v in values):
        result["error"] = ERR_SCHEMA
        return result
    if any(v not in allowed_set for v in values):
        result["error"] = ERR_RANGE
        return result
    if len(set(values)) != len(values):
        result["error"] = ERR_DUPLICATE
        return result
    if len(values) < 2:
        result["error"] = ERR_FEW
        return result
    result.update(status="ambiguous", indices=sorted(int(v) for v in values))
    return result


# --- IO / 账本 -------------------------------------------------------------


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class Budget:
    def __init__(self, path: Path, caps: Mapping[str, int]):
        self.path = path
        if path.exists():
            self.state = json.loads(path.read_text(encoding="utf-8"))
            if self.state["caps"] != dict(caps):
                raise SystemExit(f"账本上限与索引头不符：{self.state['caps']} ≠ {dict(caps)}")
        else:
            self.state = {"caps": dict(caps), "used": {key: 0 for key in caps}, "events": []}
            _atomic_json(path, self.state)

    def remaining(self, key: str) -> int:
        return int(self.state["caps"][key]) - int(self.state["used"][key])

    def charge(self, key: str, **detail: Any) -> bool:
        if self.remaining(key) <= 0:
            return False
        if key in ("query_baseline", "query_retry") and self.remaining("query_total") <= 0:
            return False
        self.state["used"][key] += 1
        if key in ("query_baseline", "query_retry"):
            self.state["used"]["query_total"] += 1
        if key == "base_start":
            self.state["events"].append({"at": _now(), "key": key, **detail})
        _atomic_json(self.path, self.state)
        return True


def load_index(pack: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lines = (pack / "index.jsonl").read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])["header"]
    queries = [json.loads(line) for line in lines[1:] if line.strip()]
    return header, queries


def verify_pack(pack: Path) -> dict[str, Any]:
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    bad = []
    for relative, expected in sorted(manifest["files"].items()):
        path = pack / relative
        if not path.is_file() or sha256_file(path) != expected:
            bad.append(relative)
    if bad:
        raise SystemExit(f"PACK_MISMATCH: {bad[:5]} …（{len(bad)} 个）")
    return {"files": len(manifest["files"]), "manifest_sha256": sha256_file(pack / "manifest.json")}


def done_results(results: Path) -> dict[tuple[str, int], dict[str, Any]]:
    done: dict[tuple[str, int], dict[str, Any]] = {}
    if results.exists():
        for line in results.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done[(row["query_id"], int(row["attempt"]))] = row
    return done


def append_result(results: Path, row: Mapping[str, Any]) -> None:
    with open(results, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


# --- 模型 -------------------------------------------------------------------


class Model:
    def __init__(self, base: Path):
        import torch  # noqa: PLC0415
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration  # noqa: PLC0415

        if not torch.cuda.is_available():
            raise SystemExit("CUDA 不可用")
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(str(base), local_files_only=True)
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            str(base), dtype=torch.bfloat16, attn_implementation="sdpa", local_files_only=True
        ).to("cuda")
        self.model.eval()
        tokenizer = self.processor.tokenizer
        eos = self.model.generation_config.eos_token_id
        self.eos_ids = {int(v) for v in (eos if isinstance(eos, (list, tuple)) else [eos]) if v is not None}
        im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
        if isinstance(im_end, int):
            self.eos_ids.add(im_end)
        self.gpu = torch.cuda.get_device_name(0)

    def query(self, image_path: Path, text: str) -> dict[str, Any]:
        from PIL import Image  # noqa: PLC0415

        with Image.open(image_path) as handle:
            handle.load()
            image = handle.convert("RGB")
        messages = [{"role": "user", "content": [{"type": "image", "image": str(image_path)}, {"type": "text", "text": text}]}]
        rendered = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        begin = time.monotonic()
        inputs = self.processor(
            text=[rendered], images=[image], images_kwargs={"size": dict(PROCESSOR_SIZE)}, padding=True, return_tensors="pt"
        )
        grid = [int(v) for v in inputs["image_grid_thw"][0].tolist()]
        input_tokens = int(inputs["input_ids"].shape[1])
        inputs = inputs.to("cuda")
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, temperature=None, top_p=None, top_k=None
            )
        new_ids = output[0, input_tokens:].tolist()
        latency = (time.monotonic() - begin) * 1000.0
        if new_ids and int(new_ids[-1]) in self.eos_ids:
            finish = "stop"
        elif len(new_ids) >= MAX_NEW_TOKENS:
            finish = "length"
        else:
            finish = "stop"
        raw = self.processor.tokenizer.decode(new_ids, skip_special_tokens=True)
        return {
            "raw_output": raw,
            "finish_reason": finish,
            "gen_tokens": len(new_ids),
            "input_tokens": input_tokens,
            "image_grid_thw": grid,
            "image_size": list(image.size),
            "latency_ms": round(latency, 3),
        }


# --- 主流程 -----------------------------------------------------------------


def base_identity(base: Path) -> dict[str, Any]:
    """加载前记录 base 快照身份（逐文件 sha；目录名须为冻结 revision）。"""
    if base.name != BASE_REVISION:
        raise SystemExit(f"base 快照目录 {base.name} ≠ 冻结 revision {BASE_REVISION}")
    return {path.name: sha256_file(path) for path in sorted(base.iterdir()) if path.is_file()}


def run(pack: Path, work: Path, base: Path) -> dict[str, Any]:
    header, queries = load_index(pack)
    identity = verify_pack(pack)
    manifest_files = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))["files"]
    prompts = header["prompts"]
    caps = {
        "base_start": int(header["caps"]["base_start"]),
        "query_total": int(header["caps"]["query_total"]),
        "query_baseline": int(header["caps"]["query_total"]),
        "query_retry": int(header["caps"]["query_retry"]),
    }
    budget = Budget(work / "budget.json", caps)
    results = work / "results.jsonl"
    done = done_results(results)
    state_path = work / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"stopped_arms": {}}

    pending_first = [q for q in queries if (q["query_id"], 0) not in done]
    if not pending_first and not any(
        r["parse"]["status"] == INVALID and (qid, 1) not in done for (qid, attempt), r in done.items() if attempt == 0
    ):
        return {"status": "NOTHING_TO_DO", **identity}
    base_files = base_identity(base)
    if not budget.charge("base_start", base_model_safetensors=base_files.get("model.safetensors")):
        raise SystemExit("BUDGET: base 启动额度已用尽")
    model = Model(base)
    summary = {"gpu": model.gpu, "pack": identity, "base_files_sha256": base_files, "started": _now()}

    def execute(query: Mapping[str, Any], attempt: int, key: str) -> dict[str, Any] | None:
        if not budget.charge(key):
            return None
        text = prompts[query["prompt_sha256"]]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != query["prompt_sha256"]:
            raise SystemExit(f"prompt sha 不符：{query['query_id']}")
        reply = model.query(pack / query["image"], text)
        parsed = parse_index_reply(reply["raw_output"], query["allowed"], reply["finish_reason"])
        row = {
            "query_id": query["query_id"],
            "arm": query["arm"],
            "row_id": query["row_id"],
            "page": query["page"],
            "attempt": attempt,
            "prompt_sha256": query["prompt_sha256"],
            "image_sha256": manifest_files[query["image"]],
            "model_id": f"{BASE_REPO}@{BASE_REVISION}",
            **reply,
            "parse": parsed,
        }
        append_result(results, row)
        done[(query["query_id"], attempt)] = row
        return row

    # smoke = 全部 609 行按 row_id 字典序的前 32 行（含 K=0 不查询的行；索引头逐条给出）。
    smoke_set = set(header.get("smoke_row_ids") or sorted({q["row_id"] for q in queries})[:SMOKE_ROWS])
    ordered = sorted(queries, key=lambda q: (q["row_id"], q["arm"], q["page"]))
    budget_stop = False
    # 第一遍：smoke 行（两臂），随后判定各臂是否 STOPPED_FORMAT。
    for query in [q for q in ordered if q["row_id"] in smoke_set]:
        if (query["query_id"], 0) in done:
            continue
        if execute(query, 0, "query_baseline") is None:
            budget_stop = True
            break
    if not budget_stop:
        for arm in sorted({q["arm"] for q in queries}):
            first = [done[(q["query_id"], 0)] for q in ordered if q["arm"] == arm and q["row_id"] in smoke_set]
            if first:
                rate = sum(1 for r in first if r["parse"]["status"] == INVALID) / len(first)
                state.setdefault("smoke", {})[arm] = {"queries": len(first), "invalid_rate": round(rate, 6)}
                if rate > SMOKE_INVALID_MAX:
                    state["stopped_arms"][arm] = "STOPPED_FORMAT"
        _atomic_json(state_path, state)
        # 第二遍：其余基线查询（跳过已停臂）。
        for query in ordered:
            if query["row_id"] in smoke_set or query["arm"] in state["stopped_arms"]:
                continue
            if (query["query_id"], 0) in done:
                continue
            if execute(query, 0, "query_baseline") is None:
                budget_stop = True
                break
    # 第三遍：`INVALID` 页各重试 1 次（同 prompt、同参数，retry=1；从 183 余量扣）。
    if not budget_stop:
        for query in ordered:
            if query["arm"] in state["stopped_arms"]:
                continue
            first = done.get((query["query_id"], 0))
            if first is None or first["parse"]["status"] != INVALID or (query["query_id"], 1) in done:
                continue
            if execute(query, 1, "query_retry") is None:
                break
    summary.update(
        {
            "finished": _now(),
            "budget": budget.state["used"],
            "caps": budget.state["caps"],
            "stopped_arms": state["stopped_arms"],
            "smoke": state.get("smoke", {}),
            "results_sha256": sha256_file(results) if results.exists() else None,
            "result_rows": len(done),
        }
    )
    _atomic_json(work / f"run-summary-{int(time.time())}.json", summary)
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--pack", type=Path, required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--pack", type=Path, required=True)
    execute.add_argument("--work", type=Path, required=True)
    execute.add_argument("--base", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "verify":
        header, queries = load_index(args.pack)
        print(json.dumps({**verify_pack(args.pack), "queries": len(queries), "caps": header["caps"]}, indent=2))
        return
    print(json.dumps(run(args.pack, args.work, args.base), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
