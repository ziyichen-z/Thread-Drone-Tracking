#!/usr/bin/env python3
"""P1-ENG-JET-001 AC-12 隔离与 AC-1/AC-15 不做项守卫（零硬件、零模型）。

- 受保护写入：主树 `runtime/` 与数据根结构性拒绝；可清空运行目录只在 `outputs/eng-jet/`、`~/eng-jet/` 或临时目录；
- 板上清单扫描：gold、`truth/`、索引、`target_*`/`state` 字段、允许前缀之外的路径一律判违规；
- 代码束只含纯标准库中继件与写桥函数，不含真值/索引/评分模块；
- S0 读数命令不含 `sudo`、`nvpmodel -m`、`systemctl isolate`、`jetson_clocks` 等改系统设置的动作；
- `tools/eng_jet/` 不导入真值/评分包，`controller/` 不导入 `tools.eng_jet`。
"""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_jet import assets, common, env_probe, relay, replay_publish  # noqa: E402

TRUTH_PACKAGES = ("tools.eng_det", "tools.eng_fast", "tools.dist_data", "tools.eng_asset", "tools.eng_acq", "tools.eng_sft")


class ProtectedWrites(unittest.TestCase):
    def test_runtime_and_data_root_refused(self):
        for root in common.PROTECTED_ROOTS:
            with self.assertRaises(PermissionError):
                common.refuse_protected(root / "x.json")
            with self.assertRaises(PermissionError):
                common.atomic_write_bytes(root / "frames" / "latest.json", b"{}")
            with self.assertRaises(PermissionError):
                common.append_jsonl(root / "r.jsonl", {"a": 1})
        common.refuse_protected(common.OUT_DIR / "ok.json")
        common.refuse_protected(common.EVIDENCE_DIR / "ok.json")

    def test_scratch_dirs_only(self):
        with self.assertRaises(PermissionError):
            common.require_scratch(PROJECT_ROOT / "runtime")
        with self.assertRaises(PermissionError):
            common.require_scratch(PROJECT_ROOT / "docs")
        with self.assertRaises(PermissionError):
            common.require_scratch(common.OUT_ROOT)  # 根本身不可整体清空
        with self.assertRaises(PermissionError):
            replay_publish.reset_runtime(PROJECT_ROOT / "runtime")
        common.require_scratch(common.RUNTIME_DESKTOP)
        common.require_scratch(Path(tempfile.gettempdir()) / "eng-jet-x")

    def test_relay_and_echo_refuse_protected_runtime(self):
        with self.assertRaises(PermissionError):
            relay.BoardRelay(PROJECT_ROOT / "runtime", Path(tempfile.mkdtemp()))
        with self.assertRaises(PermissionError):
            relay.EchoResponder(PROJECT_ROOT / "runtime", Path(tempfile.mkdtemp()))


class BoardManifestScan(unittest.TestCase):
    def test_clean_manifest(self):
        lines = ["code/tools/eng_jet/relay.py\t100", "runtime/frames/frame_0000000001.jpg\t30000",
                 "runtime/frames/latest.json\t200", "runtime/tracking_observation.json\t390", "logs/sr-x/relay-receipts.jsonl\t9",
                 "bundle/eng-jet-code.tar\t61440"]
        result = assets.scan_manifest(lines, [])
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["files"], 6)

    def test_forbidden_paths_and_keys(self):
        lines = ["runtime/truth/frame_0000000001.json\t10", "data/eval.jsonl\t10", "code/smoke.jsonl\t1", "gold/x.json\t1",
                 "catalog-index.jsonl.gz\t1", "misc/other.txt\t1"]
        result = assets.scan_manifest(lines, ["./code/smoke.blind.jsonl"])
        whys = sorted(v["why"] for v in result["violations"])
        self.assertEqual(len(result["violations"]), 7)
        self.assertIn("forbidden_json_key", whys)
        self.assertIn("outside_allowed_prefix", whys)

    def test_third_party_venv_name_hits_listed_not_violations(self):
        lines = ["venv/lib/python3.12/site-packages/pip/_internal/index/collector.py\t10", "frames/a7/frame_0000000000.jpg\t31993",
                 "wheels/lap-0.5.13.whl\t1", "home/.config/Ultralytics/settings.json\t9", "code/index.json\t1"]
        result = assets.scan_manifest(lines, ["./venv/lib/python3.12/site-packages/x/y.json"])
        self.assertEqual(result["third_party_name_hits"], ["venv/lib/python3.12/site-packages/pip/_internal/index/collector.py"])
        self.assertEqual(sorted(v["why"] for v in result["violations"]), ["forbidden_json_key", "forbidden_path"])
        self.assertEqual([v["path"] for v in result["violations"] if v["why"] == "forbidden_path"], ["code/index.json"])

    def test_system_venv_prefix_allowed_and_third_party(self):
        lines = ["sysvenv/lib/python3.12/site-packages/pip/_internal/index/collector.py\t10",
                 "sysvenv/lib/python3.12/site-packages/torch/__init__.py\t10", "wheels/sub1/torch-2.9.1.whl\t1"]
        result = assets.scan_manifest(lines, [])
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["third_party_name_hits"], ["sysvenv/lib/python3.12/site-packages/pip/_internal/index/collector.py"])

    def test_forbidden_key_pattern(self):
        self.assertTrue(assets.FORBIDDEN_KEY.search('{"target_box": [0,0,1,1]}'))
        self.assertTrue(assets.FORBIDDEN_KEY.search('{"state": "unique"}'))
        self.assertIsNone(assets.FORBIDDEN_KEY.search('{"observation": {"frame_id": 3, "track_id": "eng-jet-echo"}}'))


class BundleAndImports(unittest.TestCase):
    def test_bundle_is_stdlib_relay_only(self):
        self.assertEqual(set(assets.BUNDLE_FILES), {
            "tools/eng_jet/__init__.py", "tools/eng_jet/common.py", "tools/eng_jet/relay.py",
            "controller/__init__.py", "controller/protocol.py", "controller/tracking_entry.py"})
        for rel in assets.BUNDLE_FILES:
            tree = ast.parse((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module]
                for name in names:
                    top = name.split(".")[0]
                    # `protocol`：`controller/tracking_entry.py` 既有的脚本式回退导入（同一 controller/protocol.py）。
                    allowed = top in sys.stdlib_module_names or top in ("tools", "controller", "__future__", "protocol")
                    self.assertTrue(allowed, f"{rel}: {name}")

    def test_no_truth_imports(self):
        offenders = []
        for path in sorted((PROJECT_ROOT / "tools" / "eng_jet").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if any(node.module == p or node.module.startswith(p + ".") for p in TRUTH_PACKAGES):
                        offenders.append(f"{path.name}:{node.module}")
                elif isinstance(node, ast.Import):
                    offenders.extend(f"{path.name}:{a.name}" for a in node.names if any(a.name.startswith(p) for p in TRUTH_PACKAGES))
        self.assertEqual(offenders, [])
        for path in sorted((PROJECT_ROOT / "controller").glob("*.py")):
            self.assertNotIn("tools.eng_jet", path.read_text(encoding="utf-8"), path.name)


class LedgerSub1(unittest.TestCase):
    """SUB:1（torch/torchvision 及依赖）计数口径：包数 distinct、下载字节取轮子合计与网卡增量之大、新增磁盘取最近一次记录。"""

    def test_sub1_within_and_over(self):
        from tools.eng_jet import ledger  # noqa: PLC0415

        events = [{"kind": "sub1_pip", "package": "torch", "wheel_bytes": 512_448_274},
                  {"kind": "sub1_pip", "package": "Torch", "wheel_bytes": 0, "status": "install_from_local_wheel"},
                  {"kind": "sub1_pip", "package": "torchvision", "wheel_bytes": 7_823_607},
                  {"kind": "sub1_network", "rx_bytes": 600_000_000},
                  {"kind": "sub1_disk", "new_disk_bytes": 9_000_000_000},
                  {"kind": "sub1_disk", "new_disk_bytes": 6_500_000_000}]
        dim = ledger.sub1_dimension(events)
        self.assertEqual(dim["packages"], 2)
        self.assertEqual(dim["download_bytes"], 600_000_000)
        self.assertEqual(dim["new_disk_bytes"], 6_500_000_000)
        self.assertTrue(dim["within"])
        # SUB:3：下载上限 ≤ 6.5 GB（含已计）；3.5 GB 以上、6.5 GB 以内仍在额度内，超过 6.5 GB 即越界。
        self.assertEqual(dim["limit_download_bytes"], 6_500_000_000)
        mid = ledger.sub1_dimension(events + [{"kind": "sub1_network", "rx_bytes": 3_000_000_000}])
        self.assertEqual(mid["download_bytes"], 3_600_000_000)
        self.assertTrue(mid["within"])
        edge = ledger.sub1_dimension(events + [{"kind": "sub1_network", "rx_bytes": 5_900_000_000}])
        self.assertTrue(edge["within"])
        over = ledger.sub1_dimension(events + [{"kind": "sub1_network", "rx_bytes": 5_900_000_001}])
        self.assertFalse(over["within"])
        many = ledger.sub1_dimension([{"kind": "sub1_pip", "package": f"p{i}", "wheel_bytes": 1} for i in range(33)])
        self.assertFalse(many["within"])
        self.assertFalse(ledger.sub1_dimension([])["signed_used"])


class LedgerSub2(unittest.TestCase):
    """SUB:2（AC-10 修订 3）：四种模型分别计数、失败/重试同样计入、未列名模型额度 0、全套至多 1 次；跑前核对不消耗。"""

    def test_sub2_counts_and_limits(self):
        from tools.eng_jet import ledger  # noqa: PLC0415

        precheck = [{"kind": "mac_full_suite_precheck", "decision": "NOT_RUN"}]
        empty = ledger.sub2_dimension(precheck)
        self.assertEqual(empty["model_loads"], {"nanotrack": 0, "yoloe": 0, "dinov2": 0, "csrt": 0})
        self.assertEqual((empty["full_suite_runs"], len(empty["prechecks"])), (0, 1))
        self.assertTrue(empty["within"])
        self.assertEqual(empty["request_id"], "P1-ENG-JET-001:b0a5f79c:SUB:2")
        full = precheck + [{"kind": "mac_full_suite_run"},
                           {"kind": "mac_model_load", "model": "NanoTrack", "count": 3, "status": "success"},
                           {"kind": "mac_model_load", "model": "nanotrack", "count": 1, "status": "failed"},
                           {"kind": "mac_model_load", "model": "yoloe", "count": 2}, {"kind": "mac_model_load", "model": "dinov2", "count": 2},
                           {"kind": "mac_model_load", "model": "csrt", "count": 2}]
        self.assertTrue(ledger.sub2_dimension(full)["within"])
        self.assertFalse(ledger.sub2_dimension(full + [{"kind": "mac_model_load", "model": "nanotrack", "count": 1}])["within"])
        other = ledger.sub2_dimension(precheck + [{"kind": "mac_model_load", "model": "det-assoc-yolo", "count": 1}])
        self.assertEqual(other["other_model_loads"], {"det-assoc-yolo": 1})
        self.assertFalse(other["within"])
        self.assertFalse(ledger.sub2_dimension([{"kind": "mac_full_suite_run"}, {"kind": "mac_full_suite_run"}])["within"])


class LedgerSub5(unittest.TestCase):
    """复核 R1-4：SUB:5 A（AC-10 修订 5/6）det-assoc ≤ 2、具名部分回放 ≤ 2、全套次数与 SUB:2 共用 ≤ 1；越界即 within 为假；
    det-assoc 只计在 sub5、不进 sub2.other_model_loads（不重复扣账）。"""

    def test_sub5_limits_and_shared_full_suite(self):
        from tools.eng_jet import ledger  # noqa: PLC0415

        base = [{"kind": "mac_full_suite_run"},
                {"kind": "mac_sub5_det_assoc_load", "count": 1, "status": "success"},
                {"kind": "mac_sub5_det_assoc_load", "count": 1, "status": "failed"},
                {"kind": "mac_sub5_partial_replay", "count": 2}]
        dim = ledger.sub5_dimension(base)
        self.assertEqual((dim["det_assoc_loads"], dim["partial_replays"], dim["full_suite_runs_shared_with_sub2"]), (2, 2, 1))
        self.assertTrue(dim["within"])
        self.assertEqual(dim["request_id"], "P1-ENG-JET-001:b0a5f79c:SUB:5")
        self.assertEqual(ledger.sub2_dimension(base)["other_model_loads"], {})
        self.assertTrue(ledger.sub2_dimension(base)["within"])
        self.assertFalse(ledger.sub5_dimension(base + [{"kind": "mac_sub5_det_assoc_load", "count": 1}])["within"])
        self.assertFalse(ledger.sub5_dimension(base + [{"kind": "mac_sub5_partial_replay"}])["within"])
        second_run = base + [{"kind": "mac_full_suite_run"}]
        self.assertEqual(ledger.sub5_dimension(second_run)["full_suite_runs_shared_with_sub2"], 2)
        self.assertFalse(ledger.sub5_dimension(second_run)["within"])
        self.assertFalse(ledger.sub2_dimension(second_run)["within"])
        empty = ledger.sub5_dimension([])
        self.assertEqual((empty["det_assoc_loads"], empty["partial_replays"], empty["within"]), (0, 0, True))

    def test_constant_fields_labelled_as_assertions(self):
        from tools.eng_jet import ledger  # noqa: PLC0415

        document = ledger.build([], "HEAD", None, 0)
        dims = document["dimensions"]
        self.assertEqual(dims["mac"]["pip"], 0)
        self.assertIn("常量断言", dims["mac"]["pip_basis"])
        self.assertEqual(dims["system_settings"]["changed"], [])
        self.assertIn("常量断言", dims["system_settings"]["basis"])
        self.assertIn("不检测执行设备", document["within_envelope_basis"])


class DisconnectPass(unittest.TestCase):
    """复核 R1-4：AC-6 断链轮通过线（`evidence.disconnect_pass`，自 `relay_doc_f` 提出的具名纯函数）逐项可证伪。"""

    def _drops(self, **over):
        drops = {"latest_pointing_to_incomplete_bundle": 0, "board_sha_mismatch": 0,
                 "disconnects": [{"recovery": {"within_limit": True}}, {"recovery": {"within_limit": True}}],
                 "process_stops": {"desktop_relay": True, "board_relay": True, "responder": True}}
        drops.update(over)
        return drops

    def test_each_condition_falsifies(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        rc = {"desktop_relay": "rc=0", "replay": "rc=0", "board_relay": "rc=0", "responder": "rc=0"}
        self.assertTrue(evidence.disconnect_pass(self._drops(), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(latest_pointing_to_incomplete_bundle=1), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(board_sha_mismatch=1), rc))
        self.assertFalse(evidence.disconnect_pass(
            self._drops(disconnects=[{"recovery": {"within_limit": True}}, {"recovery": {"within_limit": False}}]), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(disconnects=[{"recovery": {"within_limit": True}}]), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(disconnects=[{"recovery": {"within_limit": True}}] * 3), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(disconnects=[{"recovery": {}}] * 2), rc))
        self.assertFalse(evidence.disconnect_pass(self._drops(), {**rc, "responder": "rc=1"}))
        self.assertFalse(evidence.disconnect_pass(self._drops(), {**rc, "replay": None}))
        self.assertFalse(evidence.disconnect_pass(
            self._drops(process_stops={"desktop_relay": True, "board_relay": False, "responder": True}), rc))
        self.assertFalse(evidence.disconnect_pass({k: v for k, v in self._drops().items() if k != "disconnects"}, rc))


class PureFrameReference(unittest.TestCase):
    """复核 R1-3：AC-11 a7 帧 sha 参照只含 `frame_id`/`sha256`；派生自含标签字段的原文件、原文件不改；读取方拒绝多余键。"""

    PREFIX = common.A7_FRAMES_REL

    def _source(self, tmp: Path, rows) -> Path:
        import gzip  # noqa: PLC0415
        import json  # noqa: PLC0415

        path = tmp / "source.jsonl.gz"
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        return path

    def test_projection_drops_label_fields_and_rejects_conflicts(self):
        rows = [{"frame_id": f"{self.PREFIX}/frame_0000000000.jpg", "sha256": "a" * 64, "positives": [1], "target_visible_flag": True},
                {"frame_id": "runtime/other/frames/frame_0000000000.jpg", "sha256": "b" * 64, "ignores": []}]
        self.assertEqual(assets.project_frame_sha(rows), {f"{self.PREFIX}/frame_0000000000.jpg": "a" * 64})
        with self.assertRaises(ValueError):
            assets.project_frame_sha(rows + [{"frame_id": f"{self.PREFIX}/frame_0000000000.jpg", "sha256": "c" * 64}])

    def test_derived_file_has_only_two_keys_and_source_unchanged(self):
        import gzip  # noqa: PLC0415
        import json  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            rows = [{"frame_id": f"{self.PREFIX}/frame_{i:010d}.jpg", "sha256": f"{i:064x}", "positives": [[0, 0, 1, 1]],
                     "target_visible_flag": True, "ignores": [], "status_counts": {}} for i in range(3)]
            source = self._source(tmp, rows)
            before = common.sha256_file(source)
            info = assets.derive_pure_reference(source, tmp / "pure.jsonl.gz")
            self.assertEqual(common.sha256_file(source), before)
            self.assertEqual((info["frames"], info["source_rows"], info["projected_keys"]), (3, 3, ["frame_id", "sha256"]))
            with gzip.open(tmp / "pure.jsonl.gz", "rt", encoding="utf-8") as handle:
                keys = {tuple(sorted(json.loads(line))) for line in handle}
            self.assertEqual(keys, {("frame_id", "sha256")})
            self.assertEqual(assets.load_pure_reference(tmp / "pure.jsonl.gz"), assets.legacy_frame_reference(source))
            again = assets.derive_pure_reference(source, tmp / "pure2.jsonl.gz")
            self.assertEqual(again["out_sha256"], info["out_sha256"])

    def test_loader_rejects_label_keys(self):
        with tempfile.TemporaryDirectory() as raw:
            bad = self._source(Path(raw), [{"frame_id": f"{self.PREFIX}/frame_0000000000.jpg", "sha256": "a" * 64, "positives": []}])
            with self.assertRaises(ValueError):
                assets.load_pure_reference(bad)

    @unittest.skipUnless(assets.PURE_FRAME_REFERENCE.is_file() and assets.DATASET_FRAMES.is_file(), "参照文件不在本机")
    def test_committed_pure_reference_matches_legacy_projection(self):
        self.assertEqual(assets.frame_reference(), assets.legacy_frame_reference())


class ContractSyncFullSuite(unittest.TestCase):
    """IR-22（AC-12 修订 4）具名协议内容命中分列与 AC-4 修订 2 链路事件分列：只追加读法，原列表不变。"""

    def test_ir22_split_is_named_only(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        true = [{"path": "./runtime/sr-f/f4-track-drops/gimbal_command.json", "why": "forbidden_json_key"},
                {"path": "./runtime/sr-f/f3-track/gimbal_command.json", "why": "forbidden_json_key"},
                {"path": "./runtime/sr-f/f2-echo/gimbal_command.json", "why": "forbidden_json_key"},
                {"path": "./runtime/sr-f/f3-track/tracking_observation.json", "why": "forbidden_json_key"},
                {"path": "./runtime/other/gimbal_command.json", "why": "forbidden_json_key"},
                {"path": "./runtime/sr-f/f3-track/gimbal_command.json", "why": "forbidden_path"}]
        snapshot = [dict(v) for v in true]
        out = evidence.ir22_named_protocol_split(true)
        self.assertEqual(true, snapshot)
        self.assertEqual(sorted(h["round"] for h in out["named_protocol_content_hits"]), ["f3-track", "f4-track-drops"])
        self.assertTrue(all(h["field"] == "command.target_world_m" for h in out["named_protocol_content_hits"]))
        self.assertEqual(out["true_isolation_violation_count_excluding_named"], 4)

    def test_link_event_split_keeps_startup_and_shutdown(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        clean = [{"ev": "connect", "unix": 1.0}, {"ev": "disconnect", "reason": "OSError", "unix": 9.0}]
        out = evidence._link_event_split(clean)
        self.assertEqual((len(out["startup_connect"]), len(out["shutdown_disconnect"]), out["in_transfer_event_count"]), (1, 1, 0))
        self.assertEqual(out["raw"], clean)
        mid = clean[:1] + [{"ev": "disconnect", "unix": 3.0}, {"ev": "connect", "unix": 4.0}] + clean[1:]
        self.assertEqual(evidence._link_event_split(mid)["in_transfer_event_count"], 2)

    def test_link_event_split_reads_full_list_and_refuses_truncated(self):
        """复核 R1-2：分列读全量列表；声明总数大于列表（截断）或无总数且达到旧截断长度 50 时，不从列表派生传输中计数。"""
        from tools.eng_jet import evidence  # noqa: PLC0415

        events = [{"ev": "connect", "unix": 0.0}] + [{"ev": "link_down" if i % 2 else "connect", "unix": float(i)} for i in range(1, 59)] \
            + [{"ev": "disconnect", "reason": "OSError", "unix": 99.0}]
        full = evidence._link_event_split(events, total=60)
        self.assertEqual((full["raw_count"], full["truncated"], full["in_transfer_event_count"]), (60, False, 58))
        cut = evidence._link_event_split(events[:50], total=60)
        self.assertTrue(cut["truncated"])
        self.assertIsNone(cut["in_transfer_event_count"])
        legacy_at_cap = evidence._link_event_split(events[:50])
        self.assertIsNone(legacy_at_cap["truncated"])
        self.assertIsNone(legacy_at_cap["in_transfer_event_count"])
        legacy_short = evidence._link_event_split([{"ev": "connect", "unix": 1.0}, {"ev": "disconnect", "unix": 2.0}])
        self.assertEqual((legacy_short["truncated"], legacy_short["in_transfer_event_count"]), (False, 0))


class CompactListing(unittest.TestCase):
    """板上清单入证据前压缩：第三方包树按前缀汇总，其余逐文件保留，违规与名单列不变。"""

    def test_third_party_trees_summarised(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        manifest = {"files": 4, "violations": [], "third_party_name_hits": ["sysvenv/x/index.py"],
                    "listing": [{"path": "code/a.py", "bytes": 3}, {"path": "sysvenv/x/index.py", "bytes": 5},
                                {"path": "sysvenv/y.so", "bytes": 7}, {"path": "venv/z.py", "bytes": 11}]}
        out = evidence.compact_listing(manifest)
        self.assertEqual(out["listing"], [{"path": "code/a.py", "bytes": 3}])
        self.assertEqual(out["third_party_tree_summary"], {"sysvenv/": {"files": 2, "bytes": 12}, "venv/": {"files": 1, "bytes": 11}})
        self.assertEqual(out["third_party_name_hits"], ["sysvenv/x/index.py"])
        self.assertEqual(out["files"], 4)
        self.assertEqual(len(manifest["listing"]), 4)


class NoSystemSettingChanges(unittest.TestCase):
    FORBIDDEN = ("sudo ", "nvpmodel -m", "systemctl isolate", "jetson_clocks", "systemctl set-default", "sysctl -w", "reboot")

    def test_s0_probe_commands_read_only(self):
        for probe in env_probe.PROBES:
            for token in self.FORBIDDEN:
                self.assertNotIn(token, probe["command"], probe["key"])

    def test_no_forbidden_tokens_in_package_commands(self):
        for path in sorted((PROJECT_ROOT / "tools" / "eng_jet").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for token in ("nvpmodel -m", "systemctl isolate", "jetson_clocks", "pip install"):
                for line in source.splitlines():
                    if token in line:
                        self.assertTrue(line.strip().startswith(("#", '"', "'")) or "不" in line, f"{path.name}: {line.strip()}")


if __name__ == "__main__":
    unittest.main()
