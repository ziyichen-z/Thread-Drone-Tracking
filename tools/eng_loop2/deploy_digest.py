"""P1-ENG-LOOP-002 A2(a)/(d)：部署摘要与身份摘要的唯一定义（纯标准库，板端与桌面端同一份）。

* **规范 JSON**：`sort_keys`、分隔符 `(",", ":")`、`ensure_ascii=False`、UTF-8。
* **部署摘要** `serve_code_sha256`：对 `config/p1-eng-loop-002-board-deploy.json` 所列路径
  （含清单文件自身），按仓库相对路径升序取 `[路径, 文件字节 sha256]` 对组成列表，规范 JSON
  后求 sha256。板端 `language_serve` 对其源码根求值，桌面端（`language_latency`/会话）对干净
  工作树求值——两端调用这同一个函数。
* **解码配置与 response_format**：常量 `DECODE_CONFIG` 与 `response_format_object()` 也定义在
  这里，`tools/eng_loop2/llama_adapter.py` 以同一对象导出使用（实现读法 IR-1：`controller/`
  只允许导入本模块（AC-9 闭集），而会话启动须桌面重算这两项身份，故唯一定义放在纯标准库的
  本模块，适配器不另写第二份）。

本模块不读真值、不导入任何第三方包，`controller/` 可导入（AC-9 闭集第 5 项）。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

#: 部署清单相对路径（清单自身也是闭集成员，随包部署）。
MANIFEST_RELATIVE = "config/p1-eng-loop-002-board-deploy.json"
MANIFEST_SCHEMA = "p1-eng-loop-002-board-deploy/v1"
#: 新入仓三态 schema（`c2q4-json-v1` 推理条件，A2(c)）。
SCHEMA_RELATIVE = "config/vlm-three-state.schema.json"
#: 本项新推理条件名（A2(c)；K3）。
DECODE_CONDITION = "c2q4-json-v1"
#: A2(b)/(d)：解码配置常量（桌面 `k-receipt` 与会话启动对它重算 `decode_config_sha256`）。
DECODE_CONFIG: Mapping[str, Any] = {
    "temperature": 0,
    "max_tokens": 160,
    "cache_prompt": False,
    "image_encoding": "base64-original-bytes",
}
#: `response_format` 外层（OpenAI 兼容 `json_schema` 形状；llama-server b11381 是否接受该形状在
#: 本机未核，列阶段 B 板上收据前置假设，不符即 STOP `S-RECEIPT`/`S-IDENTITY`，提案 A2(c)）。
RESPONSE_FORMAT_NAME = "vlm_three_state"


class DeployDigestError(ValueError):
    """清单缺失、格式错、路径越界或所列文件不存在。"""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_relative(path: Any) -> str:
    if not isinstance(path, str) or not path:
        raise DeployDigestError("manifest path must be a non-empty string")
    pure = Path(path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in path or path != pure.as_posix():
        raise DeployDigestError(f"manifest path must be a plain repository-relative POSIX path: {path!r}")
    return path


def manifest_paths(root: Path) -> list[str]:
    """读 `root` 下的部署清单，返回升序路径列表（清单自身必须在列）。"""
    manifest = Path(root) / MANIFEST_RELATIVE
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeployDigestError(f"deploy manifest missing under {root}") from exc
    except (OSError, ValueError) as exc:
        raise DeployDigestError(f"deploy manifest unreadable: {exc}") from exc
    if not isinstance(document, dict) or document.get("schema_version") != MANIFEST_SCHEMA:
        raise DeployDigestError("deploy manifest schema_version mismatch")
    paths = document.get("paths")
    if not isinstance(paths, list) or not paths:
        raise DeployDigestError("deploy manifest paths must be a non-empty list")
    checked = [_checked_relative(path) for path in paths]
    if len(set(checked)) != len(checked):
        raise DeployDigestError("deploy manifest lists a path twice")
    if MANIFEST_RELATIVE not in checked:
        raise DeployDigestError("deploy manifest must list itself")
    return sorted(checked)


def deploy_pairs(root: Path) -> list[list[str]]:
    pairs: list[list[str]] = []
    for relative in manifest_paths(root):
        path = Path(root) / relative
        if not path.is_file():
            raise DeployDigestError(f"deploy closed-set file missing: {relative}")
        pairs.append([relative, sha256_path(path)])
    return pairs


def deploy_digest(root: Path) -> str:
    """A2(a) 唯一定义：`sha256(规范 JSON([[路径, 字节 sha256], …] 按路径升序))`。"""
    return canonical_sha256(deploy_pairs(Path(root)))


def load_schema(root: Path) -> dict[str, Any]:
    document = json.loads((Path(root) / SCHEMA_RELATIVE).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise DeployDigestError("three-state schema must be a JSON object")
    return document


def response_format_object(schema: Mapping[str, Any]) -> dict[str, Any]:
    """实际随请求发送的 `response_format` 对象（schema 原样嵌入）。"""
    return {
        "type": "json_schema",
        "json_schema": {"name": RESPONSE_FORMAT_NAME, "strict": True, "schema": dict(schema)},
    }


def response_format_sha256(schema: Mapping[str, Any]) -> str:
    return canonical_sha256(response_format_object(schema))


def decode_config_sha256() -> str:
    return canonical_sha256(dict(DECODE_CONFIG))


def desktop_identity_digests(root: Path) -> dict[str, str]:
    """桌面重算（`k-receipt` 与会话 jetson 启动共用）：response_format / decode / 部署摘要。"""
    root = Path(root)
    return {
        "response_format_sha256": response_format_sha256(load_schema(root)),
        "decode_config_sha256": decode_config_sha256(),
        "serve_code_sha256": deploy_digest(root),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description="P1-ENG-LOOP-002 部署摘要（A2(a)）")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    arguments = parser.parse_args(argv)
    print(json.dumps({"root": str(arguments.root), **desktop_identity_digests(arguments.root),
                      "pairs": deploy_pairs(arguments.root)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
