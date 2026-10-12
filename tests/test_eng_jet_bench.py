#!/usr/bin/env python3
"""P1-ENG-JET-001 AC-1/AC-2/AC-3 判定件与线束注入（零硬件、零模型推理）。

- S0：tegrastats 解析与预注册判定（按 §2.1 表内顺序取第一个失败原因码；MAXN_SUPER 可选未选、非 headless 不记 PASS）；
- S1：检测级比对（同类贪心 IoU 配对、帧 0…49 计数窗口、帧 1…320 判门窗口、未配对即不一致；AC-2 修订 1）与两分量 verdict；
- S2：回放节拍丢帧、5 min 分格、降频事件（AC-3 修订 1）与 verdict；trtexec 摘要解析；
- 分位数 nearest-rank（n = 25 → 第 24 个；n = 320 → 第 304 个）；
- 线束只经构造函数注入：插件身份仍报告冻结 `.pt` 的 sha，规格文件不被改写。
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.eng_jet import common, env_probe, fastlayer_bench as bench  # noqa: E402

LINE = ("10-02-2026 15:16:16 RAM 723/7485MB (lfb 5x4MB) CPU [2%@729,1%@729,7%@729,2%@729,0%@729,1%@729] GR3D_FREQ 0% "
        "cpu@48.375C/48.375C soc2@48.156C/48.156C soc0@48.812C/48.812C gpu@47.75C/47.75C tj@48.812C/48.812C "
        "soc1@48.218C/48.218C VDD_IN 4541mW/4541mW/4541mW")


def readings(**over):
    base = {
        "nv_boot_control": "TNSPEC 3767-300-0005-W.1-1-1-jetson-orin-nano-devkit-super-\n",
        "gpu_devfreq": "max_freq=1020000000\navailable_frequencies=306000000 1020000000\ngovernor=nvhost_podgov\n",
        "cpu_cpufreq": "\n".join(f"cpu{i} online=1 cpuinfo_max_freq=1728000 scaling_max_freq=1728000 scaling_governor=schedutil" for i in range(6)),
        "nvpmodel_q": "NV Power Mode: MAXN_SUPER\n2\n",
        "default_target": "multi-user.target\n",
        "display_manager": "is-active=inactive\nis-enabled=not-found\n",
    }
    base.update(over)
    return {k: {"stdout": v} for k, v in base.items()}


class S0Verdict(unittest.TestCase):
    def test_parse_tegrastats(self):
        sample = env_probe.parse_tegrastats([LINE, "garbage"])[0]
        self.assertEqual((sample["ram_used_mb"], sample["ram_total_mb"]), (723, 7485))
        self.assertEqual(sample["cpu_mhz"], [729] * 6)
        self.assertEqual(sample["gr3d_pct"], 0)
        self.assertAlmostEqual(sample["temps_c"]["gpu"], 47.75)

    def test_pass(self):
        tegra = env_probe.parse_tegrastats([LINE] * 300)
        self.assertEqual(env_probe.evaluate(readings(), tegra)["verdict"], "PASS")

    def test_stop_codes_in_table_order(self):
        tegra = env_probe.parse_tegrastats([LINE] * 3)
        cases = {
            "NOT_SUPER": readings(nv_boot_control="TNSPEC 3767-300-0005-jetson-orin-nano-devkit-\n"),
            "FREQ_CAPPED": readings(gpu_devfreq="max_freq=624750000\navailable_frequencies=306000000 624750000\n"),
            "POWER_MODE_NOT_MAXN_SUPER": readings(nvpmodel_q="NV Power Mode: 25W\n1\n"),
            "NOT_HEADLESS": readings(default_target="graphical.target\n"),
        }
        for code, value in cases.items():
            self.assertEqual(env_probe.evaluate(value, tegra)["verdict"], f"STOP({code})", code)
        heavy = env_probe.parse_tegrastats([LINE.replace("RAM 723/", "RAM 1300/")])
        self.assertEqual(env_probe.evaluate(readings(), heavy)["verdict"], "STOP(IDLE_RAM_OVER)")
        both = env_probe.evaluate(readings(nv_boot_control="x", default_target="graphical.target"), tegra)
        self.assertEqual(both["failing_codes"], ["NOT_SUPER", "NOT_HEADLESS"])
        dm_active = env_probe.evaluate(readings(display_manager="is-active=active\n"), tegra)
        self.assertEqual(dm_active["verdict"], "STOP(NOT_HEADLESS)")


class Quantiles(unittest.TestCase):
    def test_nearest_rank(self):
        values = list(range(1, 26))
        self.assertEqual(common.nearest_rank(values, 0.95), 24)
        self.assertEqual(common.nearest_rank(list(range(1, 321)), 0.95), 304)
        self.assertEqual(common.nearest_rank([5.0], 0.5), 5.0)
        self.assertIsNone(common.nearest_rank([], 0.5))
        self.assertEqual(common.summary([3, 1, 2])["n"], 3)


def det(x, y, w, h, conf=0.9, cls=1.0):
    return [x, y, w, h, conf, cls]


class S1Comparison(unittest.TestCase):
    def test_identical_frames(self):
        ref = {i: [det(0.1, 0.2, 0.05, 0.1), det(0.5, 0.5, 0.1, 0.1, cls=0.0)] for i in range(60)}
        result = bench.compare_detections(ref, ref, list(range(60)))
        self.assertEqual(result["count_mismatch_frames_first_window"], 0)
        self.assertEqual(result["box_max_abs_diff_norm"], 0.0)
        self.assertEqual(result["inconsistent_frames"], [])
        self.assertEqual(result["matched_pairs"], 118)  # 判门窗口 = 帧 1…59（帧 0 为 init 帧，另报）
        verdict = bench.s1_verdict([10.0] * 320, result)
        self.assertEqual(verdict["verdict"], "PASS")
        self.assertTrue(verdict["latency"]["within_50ms"])

    def test_divergence_and_count_mismatch(self):
        ref = {i: [det(0.1, 0.2, 0.05, 0.1)] for i in range(60)}
        eng = {i: [det(0.1 + (0.002 if i == 55 else 0.0), 0.2, 0.05, 0.1)] for i in range(60)}
        eng[3] = eng[3] + [det(0.7, 0.7, 0.05, 0.05)]
        result = bench.compare_detections(eng, ref, list(range(60)))
        self.assertEqual(result["count_mismatch_frames_first_window"], 1)
        self.assertAlmostEqual(result["box_max_abs_diff_norm"], 0.002, places=9)
        self.assertEqual([r["frame_id"] for r in result["inconsistent_frames"]], [3, 55])
        self.assertEqual(bench.s1_verdict([10.0] * 320, result)["verdict"], "STOP(FP16_BOX_DIVERGENCE)")
        self.assertEqual(bench.s1_verdict([250.0] * 320, result)["verdict"], "STOP(LATENCY_OVER)")

    def test_class_must_match(self):
        row = bench.compare_frame([det(0.1, 0.1, 0.1, 0.1, cls=0.0)], [det(0.1, 0.1, 0.1, 0.1, cls=1.0)])
        self.assertEqual(row["matched"], 0)
        self.assertEqual(row["unmatched_engine"], 1)

    def test_count_window_is_first_50_only_but_unmatched_fails(self):
        # AC-2 修订 1 / IR-6：计数检查只看帧 0…49，但两侧任一未配对检测都使一致性分量不通过（不只在配对框上判 PASS）。
        ref = {i: [det(0.1, 0.2, 0.05, 0.1)] for i in range(60)}
        eng = dict(ref)
        eng[57] = []
        result = bench.compare_detections(eng, ref, list(range(60)))
        self.assertEqual(result["count_mismatch_frames_first_window"], 0)
        self.assertEqual(result["count_mismatch_frames_all"], 1)
        self.assertEqual(result["unmatched_reference_total"], 1)
        self.assertEqual([r["frame_id"] for r in result["inconsistent_frames"]], [57])
        verdict = bench.s1_verdict([10.0] * 320, result)
        self.assertEqual(verdict["verdict"], "STOP(FP16_BOX_DIVERGENCE)")
        self.assertEqual(verdict["consistency"]["unmatched_detections"], 1)

    def test_unmatched_with_equal_counts_fails(self):
        ref = {i: [det(0.1, 0.2, 0.05, 0.1)] for i in range(5)}
        eng = dict(ref)
        eng[2] = [det(0.6, 0.6, 0.05, 0.1)]  # 计数相等、但无法配对
        result = bench.compare_detections(eng, ref, list(range(5)))
        self.assertEqual(result["count_mismatch_frames_all"], 0)
        self.assertEqual((result["unmatched_engine_total"], result["unmatched_reference_total"]), (1, 1))
        self.assertEqual(bench.s1_verdict([10.0] * 4, result)["verdict"], "STOP(FP16_BOX_DIVERGENCE)")

    def test_gate_window_excludes_init_frame(self):
        # 判门窗口为帧 1…320（n = 320）；帧 0 的框差另报、不进判门。
        ref = {i: [det(0.1, 0.2, 0.05, 0.1)] for i in range(321)}
        eng = dict(ref)
        eng[0] = [det(0.1 + 0.004, 0.2, 0.05, 0.1)]
        result = bench.compare_detections(eng, ref, list(range(321)))
        self.assertEqual(result["gate_window"], {"frame_ids": [1, 320], "n": 320})
        self.assertEqual(result["count_window"], {"frame_ids": [0, 49], "n": 50})
        self.assertEqual(result["box_max_abs_diff_norm"], 0.0)
        self.assertAlmostEqual(result["init_frames_box_max_abs_diff_norm"][0]["max_abs_diff"], 0.004, places=9)
        self.assertEqual(result["matched_pairs"], 320)
        self.assertEqual(bench.s1_verdict([10.0] * 320, result)["verdict"], "PASS")


class S2Pieces(unittest.TestCase):
    def test_count_drops(self):
        self.assertEqual(bench.count_drops(5, 5 / 15.0 - 0.001, 15.0), (5, 0))
        self.assertEqual(bench.count_drops(5, 7.5 / 15.0, 15.0), (7, 2))

    def test_bins_and_verdict(self):
        rows = [{"t_s": t, "t_update_ms": 20.0 + (5.0 if t >= 1500 else 0.0), "dropped_before": 0} for t in range(0, 1800, 2)]
        bins = bench.bin_rows(rows, duration_s=1800)
        self.assertEqual(len(bins), 6)
        self.assertEqual(bins[0]["p95"], 20.0)
        # AC-3 修订 1 / IR-7：末/首 p95 比值 > 1.2 是预注册时延线未过 → 既有 STOP(LATENCY_OVER)，不另造码。
        over = bench.s2_verdict(bins, [], 0)
        self.assertEqual(over["verdict"], "STOP(LATENCY_OVER)")
        self.assertEqual(over["p95_ratio"], 1.25)
        flat = bench.bin_rows([{**r, "t_update_ms": 20.0} for r in rows], duration_s=1800)
        self.assertEqual(bench.s2_verdict(flat, [], 0)["verdict"], "PASS")
        self.assertEqual(bench.s2_verdict(flat, [], 3)["verdict"], "STOP(FRAME_DROP)")
        self.assertEqual(bench.s2_verdict(flat, [{"t_s": 1}], 0)["verdict"], "STOP(THERMAL_THROTTLE)")
        # 频率证据不能确认（非风扇告警非零、或频率上限读数缺失）→ 不宣称 PASS，verdict 留空并交回裁定。
        pending = bench.s2_verdict(flat, [], 0, unconfirmed=["cooling_device8:soc0-throttle-alert"])
        self.assertIsNone(pending["verdict"])
        self.assertEqual(pending["ruling_needed"], ["unconfirmed_cooling_alert:cooling_device8:soc0-throttle-alert"])
        self.assertIsNone(bench.s2_verdict(flat, [], 0, frequency_gaps=["gpu_max_freq"])["verdict"])

    def test_throttle_events(self):
        # 风扇 cur_state 非零不算降频；明确对应 GPU/CPU 热限频的 cooling device 与上限频率下降才算。
        samples = [{"t_s": 0, "gpu_max_freq": 1020000000, "cpu_max_cpu0": 1728000,
                    "cooling": {"cooling_device2:pwm-fan": 0, "cooling_device12:devfreq-17000000.gpu": 0, "cooling_device8:soc0-throttle-alert": 0}},
                   {"t_s": 1, "gpu_max_freq": 1020000000, "cpu_max_cpu0": 1728000,
                    "cooling": {"cooling_device2:pwm-fan": 2, "cooling_device12:devfreq-17000000.gpu": 0, "cooling_device8:soc0-throttle-alert": 0}},
                   {"t_s": 2, "gpu_max_freq": 918000000, "cpu_max_cpu0": 1728000,
                    "cooling": {"cooling_device2:pwm-fan": 3, "cooling_device12:devfreq-17000000.gpu": 1, "cooling_device8:soc0-throttle-alert": 1}}]
        keys = sorted(e["key"] for e in bench.throttle_events(samples))
        self.assertEqual(keys, ["cooling:cooling_device12:devfreq-17000000.gpu", "gpu_max_freq"])
        self.assertEqual(bench.throttle_events(samples[:2]), [])
        others = bench.other_cooling_changes(samples)
        self.assertEqual(others["devices"]["cooling_device2:pwm-fan"]["max_state"], 3)
        self.assertEqual(others["unconfirmed_alerts"], ["cooling_device8:soc0-throttle-alert"])
        self.assertEqual(bench.other_cooling_changes(samples[:2])["unconfirmed_alerts"], [])
        self.assertEqual(bench.frequency_evidence_gaps(samples), [])
        self.assertEqual(bench.frequency_evidence_gaps([{"t_s": 0, "gpu_max_freq": None, "cpu_max_cpu0": 1}]), ["gpu_max_freq"])


class TrtexecParse(unittest.TestCase):
    def test_parse_summary(self):
        text = ("[10/02/2026-21:30:00] [I] TensorRT version: 10.13.2\n"
                "[I] Latency: min = 5.1 ms, max = 9.2 ms, mean = 5.6 ms, median = 5.5 ms, percentile(90%) = 6.0 ms, "
                "percentile(95%) = 6.3 ms, percentile(99%) = 8.0 ms\n"
                "[I] Throughput: 180.5 qps\n"
                "[I] GPU Compute Time: min = 4.0 ms, max = 7.5 ms, mean = 4.4 ms, median = 4.3 ms, percentile(90%) = 4.8 ms, "
                "percentile(95%) = 5.0 ms, percentile(99%) = 6.9 ms\n")
        parsed = bench.parse_trtexec(text)
        self.assertEqual(parsed["GPU Compute Time"]["median"], 4.3)
        self.assertEqual(parsed["GPU Compute Time"]["percentile(95%)"], 5.0)
        self.assertEqual(parsed["Throughput"], 180.5)
        self.assertIn("10.13.2", parsed["tensorrt_version_line"])


class TorchVerifyPieces(unittest.TestCase):
    """题 4（CLARIFY-B2）安装后先验证：判据纯函数与库来源分组（零硬件）。"""

    MAPS = ("ffff0000-ffff1000 r-xp 00000000 103:01 1 /home/jetson/eng-jet/sysvenv/lib/python3.12/site-packages/nvidia/cu13/lib/libcublas.so.13\n"
            "ffff1000-ffff2000 r-xp 00000000 103:01 2 /usr/lib/aarch64-linux-gnu/libnvinfer.so.10.16.2\n"
            "ffff2000-ffff3000 r--p 00000000 103:01 2 /usr/lib/aarch64-linux-gnu/libnvinfer.so.10.16.2\n"
            "ffff3000-ffff4000 r-xp 00000000 103:01 3 /usr/lib/aarch64-linux-gnu/libc.so.6\n"
            "ffff4000-ffff5000 r-xp 00000000 103:01 4 /usr/lib/aarch64-linux-gnu/nvidia/libcuda.so.1.1\n")

    def test_loaded_libraries_and_origins(self):
        libs = bench.loaded_libraries(self.MAPS)
        self.assertEqual(libs, ["/home/jetson/eng-jet/sysvenv/lib/python3.12/site-packages/nvidia/cu13/lib/libcublas.so.13",
                                "/usr/lib/aarch64-linux-gnu/libnvinfer.so.10.16.2",
                                "/usr/lib/aarch64-linux-gnu/nvidia/libcuda.so.1.1"])
        origins = bench.library_origins(libs, "/home/jetson/eng-jet/sysvenv")
        self.assertEqual(len(origins["venv"]), 1)
        self.assertEqual(len(origins["system"]), 2)

    def test_verify_summary_requires_all(self):
        ok = {"ok": True}
        self.assertTrue(bench.verify_summary(["sm_80", "sm_87", "sm_90"], ok, ok, ok)["pass"])
        # is_available() 为 True 不算通过：arch 列表缺 sm_87 即不过。
        missing = bench.verify_summary(["sm_80", "sm_90"], ok, ok, ok)
        self.assertFalse(missing["pass"])
        self.assertEqual(missing["failed"], ["sm_87_in_arch_list"])
        self.assertEqual(bench.verify_summary(["sm_87"], {"ok": False}, ok, ok)["failed"], ["cuda_matmul_readback"])
        self.assertEqual(bench.verify_summary(["sm_87"], ok, ok, None)["failed"], ["trt_clean_process_without_torch"])

    def test_venv_construction(self):
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "pyvenv.cfg").write_text("home = /usr/bin\ninclude-system-site-packages = true\nversion = 3.12.3\n", encoding="utf-8")
            record = bench.venv_construction(tmp, "/usr")
        self.assertTrue(record["is_venv"])
        self.assertTrue(record["system_site_packages"])
        self.assertEqual(record["pyvenv_cfg"]["version"], "3.12.3")


class FakeBoxes:
    def __init__(self, rows):
        import numpy as np  # noqa: PLC0415

        self.data = np.asarray(rows, dtype=float).reshape(-1, 6)

    def cpu(self):
        return self

    def numpy(self):
        return self

    def __len__(self):
        return len(self.data)


class FakeModel:
    def __init__(self):
        self.calls = []

    def predict(self, **kwargs):
        self.calls.append(kwargs)

        class Result:
            boxes = FakeBoxes([[10, 10, 50, 50, 0.9, 1]])

        return [Result()]


class FakeTracker:
    def __init__(self):
        self.lost_stracks = []

        class Gmc:
            def apply(self, img, dets=None):
                return None

        self.gmc = Gmc()

    def update(self, boxes, image):
        import numpy as np  # noqa: PLC0415

        self.gmc.apply(image)
        return np.asarray([[10, 10, 50, 50, 1, 0.9, 1, 0]], dtype=float)


class InjectionOnly(unittest.TestCase):
    def test_plugin_identity_unchanged_and_timers(self):
        try:
            import numpy as np  # noqa: PLC0415
            import ultralytics  # noqa: F401, PLC0415
        except ImportError:
            self.skipTest("本解释器无 ultralytics/numpy（线束注入测试需要 .venv-yoloe）")
        weights = PROJECT_ROOT / common.read_json(bench.SPEC_PATH)["weights"]["path"]
        if not weights.is_file():
            self.skipTest("冻结权重不在本机")
        spec_before = bench.SPEC_PATH.read_bytes()
        sink: dict = {}
        plugin = bench.make_plugin(Path("/nonexistent/x.engine"), "cuda:0", sink, yolo_factory=lambda path: FakeModel(),
                                   base_tracker_factory=lambda algorithm, args: FakeTracker())
        identity = plugin.manifest_identity()
        self.assertEqual(identity["weights_sha256"], common.read_json(bench.SPEC_PATH)["weights"]["sha256"])
        self.assertEqual(identity["device"], "cuda:0")
        self.assertIsNone(identity["device_fallback"])
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        self.assertTrue(plugin.init(image, (10 / 640, 10 / 480, 40 / 640, 40 / 480)))
        result = plugin.update(image)
        self.assertTrue(result.ok)
        self.assertEqual(len(sink["model"].predict.calls), 2)
        self.assertEqual(len(sink["gmc"].calls), 2)
        self.assertEqual(sink["model"]._model.calls[-1]["device"], "cuda:0")
        self.assertEqual(sink["model"]._model.calls[-1]["imgsz"], 640)
        self.assertEqual(bench.SPEC_PATH.read_bytes(), spec_before)

    def test_rect_engine_imgsz_override_only_in_harness(self):
        model = FakeModel()
        timed = bench.TimedModel(model, imgsz_override=(480, 640))
        timed.predict(source=None, imgsz=640, conf=0.25)
        self.assertEqual(model.calls[-1]["imgsz"], [480, 640])
        self.assertEqual(len(timed.predict.calls), 1)
        square = bench.TimedModel(FakeModel())
        square.predict(source=None, imgsz=640)
        self.assertEqual(square._model.calls[-1]["imgsz"], 640)


class RoundDEvidence(unittest.TestCase):
    """K1K3K4补跑D 证据组装的纯函数：tegrastats RAM 摘要、S2 加测 30 Hz 条件（§2.1 字面）与 S2 步骤 verdict（停止总则）。"""

    def test_tegrastats_ram_summary(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        lines = [LINE, LINE.replace("RAM 723/", "RAM 2000/").replace("GR3D_FREQ 0%", "GR3D_FREQ 55%@[1020]"), "garbage"]
        out = evidence.tegrastats_ram(lines)
        self.assertEqual(out["samples"], 2)
        self.assertEqual(out["ram_total_mb"], 7485)
        self.assertEqual(out["ram_used_mb"]["max"], 2000)
        self.assertEqual(out["gr3d_pct"]["max"], 55)

    def test_s2_plan_30hz_only_when_p95_le_33(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        self.assertEqual(evidence.s2_plan(33.0)["rates_hz"], [15.0, 30.0])
        self.assertEqual(evidence.s2_plan(33.01)["rates_hz"], [15.0])
        self.assertEqual(evidence.s2_plan(None)["rates_hz"], [15.0])

    def test_s2_overall_stop_ruling_missing_pass(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        def run(v):
            return {"verdict": {"verdict": v}}

        both = {"rates_hz": [15.0, 30.0]}
        self.assertEqual(evidence.s2_overall({"15hz": run("PASS"), "30hz": run("PASS")}, both)["verdict"], "PASS")
        self.assertEqual(evidence.s2_overall({"15hz": run("PASS"), "30hz": run("STOP(FRAME_DROP)")}, both)["verdict"], "STOP(FRAME_DROP)")
        self.assertEqual(evidence.s2_overall({"15hz": run("STOP(THERMAL_THROTTLE)")}, both)["verdict"], "STOP(THERMAL_THROTTLE)")
        missing = evidence.s2_overall({"15hz": run("PASS")}, both)
        self.assertIsNone(missing["verdict"])
        self.assertEqual(missing["missing"], ["30hz"])
        self.assertIsNone(evidence.s2_overall({"15hz": run(None)}, {"rates_hz": [15.0]})["verdict"])


class RoundEEvidence(unittest.TestCase):
    """K1K3K4补跑E 证据组装的纯函数：板本地时间戳 tegrastats 按 S2 5 min 格分格（功耗/温度）、AC-12 修订 2 分列、网卡收包。"""

    def test_utc_offset(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        self.assertEqual(evidence.parse_utc_offset("-0400\n"), -14400)
        self.assertEqual(evidence.parse_utc_offset("+0530"), 19800)

    def test_tegrastats_bins_local_time_and_window(self):
        import calendar  # noqa: PLC0415

        from tools.eng_jet import evidence  # noqa: PLC0415

        # 板本地 15:16:16（UTC-4）= UTC 19:16:16；t0 取其 UTC 前 1 s → 落第 0 格；+300 s 的行落第 1 格；t0 之前与窗外的行不计。
        t0 = calendar.timegm((2026, 10, 2, 19, 16, 15))
        hot = LINE.replace("15:16:16", "15:21:16").replace("tj@48.812C/", "tj@61.5C/").replace("VDD_IN 4541mW/", "VDD_IN 7000mW/")
        early = LINE.replace("15:16:16", "15:16:10")
        late = LINE.replace("15:16:16", "15:46:16")
        bins = evidence.tegrastats_bins([LINE, hot, early, late, "garbage"], t0, -14400)
        self.assertEqual(len(bins), 6)
        self.assertEqual([b["samples"] for b in bins], [1, 1, 0, 0, 0, 0])
        self.assertEqual(bins[0]["vdd_mw"]["VDD_IN"], {"p50": 4541.0, "max": 4541})
        self.assertEqual(bins[1]["vdd_mw"]["VDD_IN"]["max"], 7000)
        self.assertEqual(bins[1]["temps_c_max"]["tj"], 61.5)
        self.assertEqual(bins[0]["ram_used_mb_max"], 723)
        self.assertIsNone(bins[2]["gr3d_pct_p50"])

    def test_ac12_split_only_named_driver_cache_index(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        violations = [{"path": "home/cuda-cache/index", "why": "forbidden_path"},
                      {"path": "home/other/index", "why": "forbidden_path"},
                      {"path": "home/cuda-cache/index", "why": "forbidden_json_key"}]
        out = evidence.ac12_split(violations)
        self.assertEqual(out["named_driver_cache_filename_hits"], [violations[0]])
        self.assertEqual(out["true_violations"], violations[1:])
        self.assertEqual(out["true_violation_count"], 2)

    def test_netdev_rx(self):
        from tools.eng_jet import evidence  # noqa: PLC0415

        lines = ["Inter-|   Receive", " face |bytes    packets", "enP8p1s0: 1035051   16234    0 0", "  lo: 12 1 0"]
        self.assertEqual(evidence.netdev_rx(lines), {"enP8p1s0": 1035051, "lo": 12})


if __name__ == "__main__":
    unittest.main()
