using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 batch-2 tool stage (§30 BC-B2-1/2): the candidate T1′
    /// binding loader. The formal candidate probe runs only after the
    /// config stage writes `config/scenario.p1-scene-006.json`; this loader
    /// binds that config fail-closed to the frozen BC-B2-3/4 values and to
    /// the reviewed P3 artifact (`C_1c`), so a wrong config byte can never
    /// reach the renderer:
    ///
    /// * scenario_id must be `p1-scene-006-difficult-v1`;
    /// * anchor x/z exactly 197.0/30.0, anchor y within 1e-9 of the frozen
    ///   0.0000013113417480781209 (the JSON print of the P1-measured grass
    ///   support height differs from the artifact print by one float32 ULP);
    /// * initial_altitude_m / vertical_fov_deg must equal the reviewed P3
    ///   finalist's (16.0 / 40.0);
    /// * the target route must equal the frozen family-B (+60, -60)
    ///   translation of the default route, vertex by vertex;
    /// * scene_adjustments must be exactly the §3.3.2 five authorized rows
    ///   (matched by prefab + original xz, order-independent), all
    ///   `mark_as_distractor = false`, zero removals,
    ///   `expected_distractor_count = 0` (BC-B2-4);
    /// * every field not listed in BC-B2-3 must equal the frozen default
    ///   config (sensor size/rate, gimbal limits, drone limits, target
    ///   speed, evaluation thresholds, corridor parameters, road-data
    ///   hash, random seed).
    ///
    /// Any divergence throws (fail closed); no tool-state artifact is
    /// produced by the loader itself.
    /// </summary>
    public static class Scene006CandidateProbe
    {
        public const string CandidateConfigPath =
            "config/scenario.p1-scene-006.json";
        public const string CandidateScenarioId = "p1-scene-006-difficult-v1";
        public const string P3ArtifactPath =
            "docs/evidence/P1-SCENE-006-p3-finalist.json";
        public const string ProbeId = "p1-scene-006-candidate-vfov40";
        public const string ProbeDirectory =
            "runtime/p1-scene-006/probe-candidate-vfov40";

        /// <summary>
        /// §3.5.1 new artifact identity for the T1′(v2) parity redirection.
        /// The v1 probe id/directory above stay read-only history: the two
        /// captures are never merged, and the retired v1 entry point must
        /// not be re-run now that the replica is painted.
        /// </summary>
        public const string ProbeIdP2 = "p1-scene-006-candidate-vfov40-p2";
        public const string ProbeDirectoryP2 =
            "runtime/p1-scene-006/probe-candidate-vfov40-p2";
        public const double FrozenAnchorY = 0.0000013113417480781209;
        public const float AnchorYTolerance = 1e-9f;

        /// <summary>
        /// C3: the batch-2 candidate config bytes are frozen; this run may
        /// not introduce a new config commit. Independently pinned by the
        /// F21 EditMode regression test, which carries its own literal.
        /// </summary>
        public const string FrozenCandidateConfigSha256 =
            "ec4154d1c7a945b70a8d8ed9fa1c6937552fde1a3fc88e364eb83881eb31c831";

        /// <summary>
        /// The §5.6 frozen tool path set, listed verbatim in the batch-1b
        /// stop record (`docs/evidence/P1-SCENE-006-batch1b.md` §1) and
        /// unchanged since: adding, deleting or discovering an omission of
        /// any executable tool path is itself a tool change (R16). The stop
        /// record writes the two directories as `dir/**`; a bare directory
        /// is the identical git pathspec.
        /// </summary>
        public static readonly string[] FrozenToolPaths =
        {
            "Assets/TetheredTracking/Editor/Scene006",
            "Assets/TetheredTracking/Tests/EditMode",
            "tools/run_scene006_probe.py",
            "tools/scene006_trace_hash.py",
            "tools/scene006_candidate_check.py",
            "tests/test_scene006_probe.py",
            "tests/test_scene006_trace_hash.py",
            "tests/test_scene006_candidate_check.py",
            "tests/fixtures/scene006-trace-v2-sample.json",
        };

        /// <summary>
        /// §3.5.2 frozen tool path set v2: the nine batch-1b paths verbatim
        /// plus `Assets/TetheredTracking/Scripts`. Once the target visual is
        /// built by a runtime factory, the runtime scripts are part of T1′'s
        /// rendering semantics, so the `tool_commit..capture_commit`
        /// zero-diff proof has to cover them too.
        /// </summary>
        public static readonly string[] FrozenToolPathsV2 = BuildV2Paths();

        static string[] BuildV2Paths()
        {
            var paths = new string[FrozenToolPaths.Length + 1];
            Array.Copy(FrozenToolPaths, paths, FrozenToolPaths.Length);
            paths[FrozenToolPaths.Length] = "Assets/TetheredTracking/Scripts";
            return paths;
        }

        public sealed class CandidateIdentity
        {
            public ScenarioConfig Config;
            public string ConfigSha256;
            public float SInit;
            public string TraceSha256;
            public int KStar;
            public string P3ArtifactSha256;
            /// <summary>
            /// The reviewed P3 T6 record, so the prompt-law v2 selection can
            /// cross-check its warmup replay bit for bit (§3.2.5).
            /// </summary>
            public Scene006Evaluation.T6Record T6;
        }

        /// <summary>
        /// The §5.6 identity pair's tool half, plus the evidence that
        /// discharges the zero-diff obligation.
        /// </summary>
        public sealed class ToolCommitBinding
        {
            public string ToolCommit;
            public string[] FrozenPaths;
            public bool ZeroDiffVerified;
        }

        /// <summary>
        /// §5.6 `tool_commit`: <b>the last commit along the actual capture
        /// history that introduced changes inside the frozen tool path
        /// set</b> — deliberately not the capture HEAD. On every execution
        /// path BC-B2-5 permits for the formal T1′ the config commit (or a
        /// tool-path-zero-diff successor) is strictly after the last tool
        /// commit, so stamping HEAD would mis-state the identity and vacate
        /// the zero-diff obligation by making `tool_commit..capture_commit`
        /// empty by construction.
        ///
        /// Derivation and proof are both in-process: the commit comes from
        /// `git log -1` restricted to the frozen path set, and whenever it
        /// differs from the capture commit the frozen paths must be
        /// byte-identical across `tool_commit..capture_commit`. A
        /// mis-derivation therefore cannot pass silently — the diff check
        /// fails closed before any frame or manifest is produced.
        /// </summary>
        /// <param name="runGit">
        /// Runs `git &lt;arguments&gt;` in the project root and returns its
        /// stdout; throws on a non-zero exit.
        /// </param>
        /// <param name="captureCommit">The clean capture HEAD.</param>
        /// <summary>
        /// Production overload: derives the §5.6 tool commit through real
        /// git in the project root.
        /// </summary>
        public static ToolCommitBinding ResolveToolCommit(
            string captureCommit) =>
            ResolveToolCommit(RunGit, captureCommit);

        /// <summary>
        /// Production overload for the T1′(v2) capture: the same derivation
        /// over the frozen path set v2.
        /// </summary>
        public static ToolCommitBinding ResolveToolCommitV2(
            string captureCommit) =>
            ResolveToolCommit(RunGit, captureCommit, FrozenToolPathsV2);

        public static ToolCommitBinding ResolveToolCommit(
            Func<string, string> runGit,
            string captureCommit) =>
            ResolveToolCommit(runGit, captureCommit, FrozenToolPaths);

        public static ToolCommitBinding ResolveToolCommit(
            Func<string, string> runGit,
            string captureCommit,
            string[] frozenPaths)
        {
            if (runGit == null)
                throw new ArgumentNullException(nameof(runGit));
            Require(frozenPaths != null && frozenPaths.Length > 0,
                "the frozen tool path set must be non-empty");
            Require(IsCommitHash(captureCommit),
                "capture commit must be a 40-hex commit hash");

            string pathspec = string.Join(" ", frozenPaths);
            string toolCommit = Trimmed(runGit(
                "log -1 --format=%H " + captureCommit + " -- " + pathspec));
            Require(IsCommitHash(toolCommit),
                "no commit in the capture history introduces changes in the "
                + "frozen tool path set; the §5.6 tool_commit cannot be "
                + "derived (git returned '" + toolCommit + "')");

            if (toolCommit != captureCommit)
            {
                string drift = Trimmed(runGit(
                    "diff --name-only " + toolCommit + ".." + captureCommit
                    + " -- " + pathspec));
                Require(drift.Length == 0,
                    "the frozen tool paths differ between tool_commit "
                    + toolCommit + " and capture_commit " + captureCommit
                    + "; the §5.6 zero-diff proof fails:\n" + drift);
            }

            return new ToolCommitBinding
            {
                ToolCommit = toolCommit,
                FrozenPaths = (string[])frozenPaths.Clone(),
                ZeroDiffVerified = true,
            };
        }

        public static CandidateIdentity LoadAndBind(
            string candidateConfigPath,
            string p3ArtifactPath,
            ScenarioConfig defaultConfig)
        {
            if (defaultConfig == null)
                throw new ArgumentNullException(nameof(defaultConfig));

            // The reviewed P3 artifact is the source of the finalist
            // identity (s_init, trace hash, k*); it must be P3_OK. Hash the
            // raw file bytes (as for the config below) so the recorded
            // provenance SHA is the file's, not a re-encoding's.
            byte[] p3Bytes = File.ReadAllBytes(p3ArtifactPath);
            string p3Sha256 = Scene006RouteGeometry.Sha256Hex(p3Bytes);
            string p3Json = System.Text.Encoding.UTF8.GetString(p3Bytes);
            Scene006FinalistGenerator.P3Report p3 =
                JsonUtility.FromJson<Scene006FinalistGenerator.P3Report>(
                    p3Json);
            if (p3 == null
                || p3.schema_version != Scene006FinalistGenerator.P3Schema
                || p3.status != "P3_OK"
                || p3.selection == null
                || p3.selection.finalist == null
                || p3.t6 == null)
            {
                throw new InvalidOperationException(
                    "candidate probe requires the reviewed P3_OK artifact");
            }
            Scene006FinalistSelection.ScoredCell finalist =
                p3.selection.finalist;

            byte[] configBytes = File.ReadAllBytes(candidateConfigPath);
            string configSha = Scene006RouteGeometry.Sha256Hex(configBytes);
            ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                System.Text.Encoding.UTF8.GetString(configBytes));
            if (config.scenario_id != CandidateScenarioId)
                throw new InvalidOperationException(
                    "candidate scenario_id must be " + CandidateScenarioId);

            // BC-B2-3 frozen fields.
            Require(config.anchor_world_m.x == 197.0f
                && config.anchor_world_m.z == 30.0f,
                "candidate anchor x/z must be exactly 197.0/30.0");
            Require(
                Math.Abs(config.anchor_world_m.y - (float)FrozenAnchorY)
                    <= AnchorYTolerance,
                "candidate anchor y diverges from the frozen support height");
            Require(
                config.drone.initial_altitude_m
                    == finalist.initial_altitude_m,
                "candidate altitude must equal the reviewed P3 finalist");
            Require(
                config.sensor.vertical_fov_deg == finalist.vertical_fov_deg,
                "candidate vfov must equal the reviewed P3 finalist");
            Require(
                Mathf.Abs(finalist.anchor_x_m - 197.0f) <= 1e-6f
                && Mathf.Abs(finalist.anchor_z_m - 30.0f) <= 1e-6f
                && finalist.initial_altitude_m == 16.0f
                && finalist.vertical_fov_deg == 40.0f,
                "reviewed P3 finalist is not the BC-B2-3 candidate point");

            // Route: the frozen family-B translation, vertex by vertex.
            Vector3[] expectedRoute = Scene006CandidateContract.FamilyRoute(
                Scene006CandidateContract.FamilyB,
                defaultConfig.TargetRoute());
            Vector3[] candidateRoute = config.TargetRoute();
            Require(candidateRoute.Length == expectedRoute.Length,
                "candidate route length differs from the family-B route");
            for (int index = 0; index < expectedRoute.Length; index++)
            {
                Require(
                    candidateRoute[index] == expectedRoute[index],
                    $"candidate route vertex {index} differs from the "
                    + "frozen family-B translation");
            }

            // BC-B2-4: exactly the five authorized relocations, all flags
            // false, zero distractors.
            Require(config.scene_adjustments != null,
                "candidate scene_adjustments missing");
            Require(
                config.scene_adjustments.expected_distractor_count == 0,
                "candidate expected_distractor_count must be 0");
            VehicleRelocationScenarioConfig[] rows =
                config.scene_adjustments.vehicle_relocations;
            Require(rows != null
                && rows.Length
                    == Scene006CandidateContract.FamilyBRelocations.Length,
                "candidate must carry exactly the five authorized rows");
            foreach (Scene006CandidateContract.AuthorizedRelocation authorized
                in Scene006CandidateContract.FamilyBRelocations)
            {
                VehicleRelocationScenarioConfig match = null;
                foreach (VehicleRelocationScenarioConfig row in rows)
                {
                    if (row.prefab_name == authorized.PrefabName
                        && Mathf.Abs(row.original_xz_m.x
                                - authorized.OriginalXz.x) <= 1e-4f
                        && Mathf.Abs(row.original_xz_m.z
                                - authorized.OriginalXz.y) <= 1e-4f)
                    {
                        match = row;
                    }
                }
                Require(match != null,
                    "missing authorized relocation row: "
                    + authorized.PrefabName);
                Require(!match.mark_as_distractor
                    && !match.remove_from_scene,
                    "relocation flags must be false/false: "
                    + authorized.PrefabName);
                Require(
                    Mathf.Abs(match.match_tolerance_m
                            - Scene006CandidateContract
                                .RelocationMatchToleranceM) <= 1e-6f,
                    "relocation tolerance must be 0.1: "
                    + authorized.PrefabName);
                Require(
                    Mathf.Abs(match.new_position_m.x
                            - authorized.NewPosition.x) <= 1e-4f
                    && Mathf.Abs(match.new_position_m.y
                            - authorized.NewPosition.y) <= 1e-4f
                    && Mathf.Abs(match.new_position_m.z
                            - authorized.NewPosition.z) <= 1e-4f,
                    "relocation landing differs from the authorized row: "
                    + authorized.PrefabName);
            }

            // Everything not listed in BC-B2-3 stays identical to the
            // frozen default config.
            Require(config.schema_version == defaultConfig.schema_version,
                "schema_version changed");
            Require(config.random_seed == defaultConfig.random_seed,
                "random_seed changed");
            Require(config.road_data_sha256 == defaultConfig.road_data_sha256,
                "road_data_sha256 changed");
            Require(
                config.drone.tether_length_m
                    == defaultConfig.drone.tether_length_m
                && config.drone.minimum_altitude_m
                    == defaultConfig.drone.minimum_altitude_m
                && config.drone.maximum_altitude_m
                    == defaultConfig.drone.maximum_altitude_m
                && config.drone.maximum_speed_mps
                    == defaultConfig.drone.maximum_speed_mps
                && config.drone.maximum_acceleration_mps2
                    == defaultConfig.drone.maximum_acceleration_mps2,
                "drone fields other than initial_altitude_m changed");
            Require(
                config.gimbal.maximum_off_nadir_deg
                    == defaultConfig.gimbal.maximum_off_nadir_deg
                && config.gimbal.slew_rate_deg_per_second
                    == defaultConfig.gimbal.slew_rate_deg_per_second,
                "gimbal fields changed");
            Require(
                config.sensor.width == defaultConfig.sensor.width
                && config.sensor.height == defaultConfig.sensor.height
                && config.sensor.capture_hz == defaultConfig.sensor.capture_hz
                && config.sensor.jpeg_quality
                    == defaultConfig.sensor.jpeg_quality
                && config.sensor.retained_frame_count
                    == defaultConfig.sensor.retained_frame_count,
                "sensor fields other than vertical_fov_deg changed");
            Require(
                config.target.track_id == defaultConfig.target.track_id
                && config.target.speed_mps == defaultConfig.target.speed_mps,
                "target fields other than the route changed");
            Require(
                config.evaluation.minimum_visible_sample_fraction
                    == defaultConfig.evaluation.minimum_visible_sample_fraction
                && config.evaluation.tracking_iou_threshold
                    == defaultConfig.evaluation.tracking_iou_threshold
                && config.evaluation.maximum_pending_frame_count
                    == defaultConfig.evaluation.maximum_pending_frame_count,
                "evaluation fields changed");
            Require(
                config.scene_adjustments.route_corridor.target_half_width_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .target_half_width_m
                && config.scene_adjustments.route_corridor.clearance_margin_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .clearance_margin_m
                && config.scene_adjustments.route_corridor
                        .target_bottom_offset_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .target_bottom_offset_m
                && config.scene_adjustments.route_corridor.target_height_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .target_height_m
                && config.scene_adjustments.route_corridor
                        .vertical_clearance_margin_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .vertical_clearance_margin_m
                && config.scene_adjustments.route_corridor
                        .road_sample_spacing_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .road_sample_spacing_m
                && config.scene_adjustments.route_corridor.jump_epsilon_m
                    == defaultConfig.scene_adjustments.route_corridor
                        .jump_epsilon_m
                && config.scene_adjustments.route_corridor
                        .enable_dynamic_intersection_audit
                    == defaultConfig.scene_adjustments.route_corridor
                        .enable_dynamic_intersection_audit
                && config.scene_adjustments.route_corridor
                        .enable_jump_diagnostic
                    == defaultConfig.scene_adjustments.route_corridor
                        .enable_jump_diagnostic,
                "route corridor fields changed");

            return new CandidateIdentity
            {
                Config = config,
                ConfigSha256 = configSha,
                SInit = p3.finalist_trace_s_init,
                TraceSha256 = p3.finalist_trace_sha256,
                KStar = p3.t6.k_star,
                P3ArtifactSha256 = p3Sha256,
                T6 = p3.t6,
            };
        }

        /// <summary>
        /// Runs `git &lt;arguments&gt;` in the project root and returns its
        /// trimmed stdout; a non-zero exit throws. Byte-identical to the
        /// reviewed helper in `Scene006CandidateGenerator` /
        /// `Scene006EvidenceGenerator` (the frozen tools keep the reviewed
        /// pattern verbatim rather than de-duplicating it).
        /// </summary>
        public static string RunGit(string arguments)
        {
            string projectRoot = Path.GetFullPath(
                Path.Combine(Application.dataPath, ".."));
            var startInfo = new System.Diagnostics.ProcessStartInfo(
                "git", arguments)
            {
                WorkingDirectory = projectRoot,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
            };
            using (System.Diagnostics.Process process =
                System.Diagnostics.Process.Start(startInfo))
            {
                string stdout = process.StandardOutput.ReadToEnd();
                string stderr = process.StandardError.ReadToEnd();
                process.WaitForExit();
                if (process.ExitCode != 0)
                {
                    throw new InvalidOperationException(
                        "git " + arguments + " failed: " + stderr);
                }
                return stdout.Trim();
            }
        }

        static void Require(bool condition, string message)
        {
            if (!condition)
                throw new InvalidOperationException(
                    "candidate-config binding failed: " + message);
        }

        static string Trimmed(string value) =>
            value == null ? string.Empty : value.Trim();

        static bool IsCommitHash(string value)
        {
            if (value == null || value.Length != 40) return false;
            foreach (char character in value)
            {
                bool hex = (character >= '0' && character <= '9')
                    || (character >= 'a' && character <= 'f');
                if (!hex) return false;
            }
            return true;
        }
    }
}
