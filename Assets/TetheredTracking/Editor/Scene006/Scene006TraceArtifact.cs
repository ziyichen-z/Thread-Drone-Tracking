using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.2.2 trace artifact schema v2 (F1 fix, batch 1b): the serialized
    /// states carry the exact float32 bit patterns next to the float values,
    /// so the recorded <c>sha256</c> is externally recomputable from the
    /// published bytes alone. The hash itself is unchanged —
    /// <see cref="Scene006Trace.HashStates"/> over int32-LE k followed by the
    /// float32-LE bit patterns of position x/y/z and quaternion x/y/z/w; the
    /// v2 artifact simply publishes those bit patterns as 8-digit hex, which
    /// JsonUtility string serialization preserves byte-exactly (unlike
    /// floats, whose textual form may normalize e.g. negative zero).
    ///
    /// Cross-process recomputation: read the artifact, decode each
    /// <c>*_bits</c> field as a big-endian-agnostic uint32 hex, emit the
    /// canonical layout and SHA-256 it; <c>tools/scene006_trace_hash.py</c>
    /// implements exactly that and is pinned by
    /// <c>tests/test_scene006_trace_hash.py</c>.
    /// </summary>
    public static class Scene006TraceArtifact
    {
        public const string Schema = "p1-scene-006-trace/v2";
        public const string HashLayout =
            "sha256 over concatenated per-state records: int32-LE k, then "
            + "float32-LE bit patterns of px, py, pz, qx, qy, qz, qw; the "
            + "*_bits fields are the authoritative big-hex uint32 encodings "
            + "of those bit patterns";

        [Serializable]
        public sealed class StateRecord
        {
            public int k;
            public float t_s;
            public float px;
            public float py;
            public float pz;
            public float qx;
            public float qy;
            public float qz;
            public float qw;
            public string px_bits;
            public string py_bits;
            public string pz_bits;
            public string qx_bits;
            public string qy_bits;
            public string qz_bits;
            public string qw_bits;
        }

        [Serializable]
        public sealed class Artifact
        {
            public string schema_version = Schema;
            public string work_id = "P1-SCENE-006";
            public string scenario_id;
            public string scenario_sha256;
            public string family;
            public Scene006Evaluation.Vec3 anchor_world_m;
            public float support_y_m;
            public float s_init;
            public float dt_s = Scene006Trace.StepSeconds;
            public int steps = Scene006Trace.HorizonSteps;
            public int state_count;
            public int first_lap_steps;
            public string first_lap_status;
            public string hash_layout = HashLayout;
            public string sha256;
            // §5.6: EVERY artifact carries the dual commit identity, the
            // clean-porcelain record and the scene zero-write proof; a
            // trace artifact missing any of these fields fails closed.
            public Scene006CandidateGenerator.CaptureIdentity capture;
            public StateRecord[] states;
        }

        public static string Bits(float value) =>
            BitConverter.SingleToInt32Bits(value).ToString(
                "x8", CultureInfo.InvariantCulture);

        public static StateRecord[] BuildStates(Scene006Trace.State[] trace)
        {
            if (trace == null) throw new ArgumentNullException(nameof(trace));
            var records = new StateRecord[trace.Length];
            for (int k = 0; k < trace.Length; k++)
            {
                records[k] = new StateRecord
                {
                    k = k,
                    t_s = k * Scene006Trace.StepSeconds,
                    px = trace[k].Position.x,
                    py = trace[k].Position.y,
                    pz = trace[k].Position.z,
                    qx = trace[k].Rotation.x,
                    qy = trace[k].Rotation.y,
                    qz = trace[k].Rotation.z,
                    qw = trace[k].Rotation.w,
                    px_bits = Bits(trace[k].Position.x),
                    py_bits = Bits(trace[k].Position.y),
                    pz_bits = Bits(trace[k].Position.z),
                    qx_bits = Bits(trace[k].Rotation.x),
                    qy_bits = Bits(trace[k].Rotation.y),
                    qz_bits = Bits(trace[k].Rotation.z),
                    qw_bits = Bits(trace[k].Rotation.w),
                };
            }
            return records;
        }

        /// <summary>
        /// Rebuilds the canonical hash input from the serialized records
        /// alone (the cross-process contract): int32-LE k followed by the
        /// decoded float32 bit patterns in field order.
        /// </summary>
        public static byte[] CanonicalBytes(IReadOnlyList<StateRecord> states)
        {
            if (states == null) throw new ArgumentNullException(nameof(states));
            var bytes = new List<byte>(states.Count * 32);
            for (int k = 0; k < states.Count; k++)
            {
                StateRecord state = states[k];
                if (state.k != k)
                {
                    throw new InvalidOperationException(
                        "trace state records must be ordered by k");
                }
                AppendInt32(bytes, k);
                AppendInt32(bytes, DecodeBits(state.px_bits, nameof(state.px_bits)));
                AppendInt32(bytes, DecodeBits(state.py_bits, nameof(state.py_bits)));
                AppendInt32(bytes, DecodeBits(state.pz_bits, nameof(state.pz_bits)));
                AppendInt32(bytes, DecodeBits(state.qx_bits, nameof(state.qx_bits)));
                AppendInt32(bytes, DecodeBits(state.qy_bits, nameof(state.qy_bits)));
                AppendInt32(bytes, DecodeBits(state.qz_bits, nameof(state.qz_bits)));
                AppendInt32(bytes, DecodeBits(state.qw_bits, nameof(state.qw_bits)));
            }
            return bytes.ToArray();
        }

        public static string RecomputeSha256(IReadOnlyList<StateRecord> states) =>
            Scene006RouteGeometry.Sha256Hex(CanonicalBytes(states));

        static int DecodeBits(string hex, string field)
        {
            if (string.IsNullOrEmpty(hex) || hex.Length != 8)
            {
                throw new InvalidOperationException(
                    "trace bit field " + field + " must be 8 hex digits");
            }
            return int.Parse(
                hex, NumberStyles.HexNumber, CultureInfo.InvariantCulture);
        }

        static void AppendInt32(List<byte> bytes, int value)
        {
            bytes.Add((byte)(value & 0xFF));
            bytes.Add((byte)((value >> 8) & 0xFF));
            bytes.Add((byte)((value >> 16) & 0xFF));
            bytes.Add((byte)((value >> 24) & 0xFF));
        }

        public static Artifact Build(
            string scenarioId,
            string scenarioSha256,
            string family,
            Vector3 anchor,
            float supportY,
            float sInit,
            Scene006Trace.State[] trace,
            int firstLap)
        {
            StateRecord[] states = BuildStates(trace);
            return new Artifact
            {
                scenario_id = scenarioId,
                scenario_sha256 = scenarioSha256,
                family = family,
                anchor_world_m = new Scene006Evaluation.Vec3
                {
                    x = anchor.x,
                    y = anchor.y,
                    z = anchor.z,
                },
                support_y_m = supportY,
                s_init = sInit,
                state_count = trace.Length,
                first_lap_steps = firstLap,
                first_lap_status = firstLap > 0 ? "MEASURED" : "HORIZON_SHORT",
                sha256 = Scene006Trace.HashStates(trace),
                states = states,
            };
        }

        public static void Write(string projectRelativePath, Artifact artifact)
        {
            // Fail closed if the published bytes would not reproduce the
            // recorded hash: this is the F1 self-check at write time.
            string recomputed = RecomputeSha256(artifact.states);
            if (!string.Equals(recomputed, artifact.sha256, StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "trace artifact self-check failed: serialized bit patterns "
                    + "do not reproduce the recorded sha256");
            }
            // §5.6 fail-closed: an artifact missing any identity field
            // (dual commits, clean porcelain record, scene zero-write
            // proof) must not be produced (B1B-R1).
            Scene006CandidateGenerator.CaptureIdentity capture =
                artifact.capture;
            if (capture == null
                || string.IsNullOrEmpty(capture.capture_commit)
                || string.IsNullOrEmpty(capture.tool_commit)
                || capture.git_status_porcelain == null
                || capture.git_status_porcelain.Length != 0
                || string.IsNullOrEmpty(capture.scene_state_sha256)
                || string.IsNullOrEmpty(capture.scene_file_sha256_before)
                || capture.scene_file_sha256_before
                    != capture.scene_file_sha256_after
                || capture.scene_saved)
            {
                throw new InvalidOperationException(
                    "trace artifact identity incomplete: §5.6 requires the "
                    + "dual commit fields, an empty porcelain record and the "
                    + "scene zero-write proof on every artifact");
            }
            AtomicFile.WriteAllText(
                RuntimePaths.ProjectFile(projectRelativePath.Split('/')),
                JsonUtility.ToJson(artifact, true) + "\n");
        }
    }
}
