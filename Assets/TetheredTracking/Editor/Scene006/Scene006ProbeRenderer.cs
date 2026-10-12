using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.6 T1' probe frame generator: Edit-Mode offline rendering over the
    /// §5.2 frozen trace. The probe set is the 106 pre-registered ticks
    /// k = 15, 20, ..., 540 plus the T6 acquisition frame s_k* (k* &lt;= 10,
    /// structurally disjoint from the tick set) as the visual-prompt frame.
    /// Zero Play, zero formal session; everything lands in a new runtime/
    /// directory.
    ///
    /// Batch 1 runs this only at the current 60 deg optics as the tool
    /// self-check; candidate-optics execution belongs to batch 2 and no
    /// batch may claim "new-optics T1' done" before candidate bytes exist.
    /// </summary>
    public static class Scene006ProbeRenderer
    {
        public const string ProbeId = "baseline-vfov60-selfcheck";
        public const string ProbeSchema = "p1-scene-006-probe-truth/v1";
        public const string ManifestSchema = "p1-scene-006-probe-manifest/v1";
        public const string CandidateManifestSchema =
            "p1-scene-006-probe-manifest/v2";

        /// <summary>
        /// v3 (T1′ parity redirection): adds the target-appearance block,
        /// the prompt-law v2 eligibility echo and the F20 self-contained
        /// identity fields, and replaces `expected_k_star` with
        /// `expected_k_star_p2` + the selection artifact hash.
        /// </summary>
        public const string CandidateManifestSchemaP2 =
            "p1-scene-006-probe-manifest/v3";
        public const int JpegQuality = 85;

        [Serializable]
        public sealed class Vec4
        {
            public float x;
            public float y;
            public float z;
            public float w;
        }

        [Serializable]
        public sealed class DistractorRecord
        {
            public string distractor_id;
            public string kind;
            public string box_status;
            public NormalizedBoundingBox bbox_xywh_norm;
        }

        [Serializable]
        public sealed class TruthRecord
        {
            public string schema_version = ProbeSchema;
            public string work_id = "P1-SCENE-006";
            public string probe_id;
            public string scenario_id;
            public string scenario_sha256;
            public string trace_sha256;
            public int tick_k;
            public float simulation_time_s;
            public Scene006Evaluation.Vec3 camera_position;
            public Vec4 camera_rotation;
            public int frustum_sample_count;
            public int visible_sample_count;
            public float visible_sample_fraction;
            public bool frustum_visible;
            public bool geometrically_visible;
            public float target_slant_range_m;
            public string target_box_status;
            public NormalizedBoundingBox target_bbox_xywh_norm;
            public float target_min_side_px;
            public DistractorRecord[] distractors;
        }

        [Serializable]
        public sealed class PromptReference
        {
            public int tick_k;
            public string image_file;
            public string truth_file;
            public string image_sha256;
            public string truth_sha256;
        }

        [Serializable]
        public class Manifest
        {
            public string schema_version = ManifestSchema;
            public string work_id = "P1-SCENE-006";
            public string probe_id;
            public string scenario_id;
            public string scenario_sha256;
            public string road_data_sha256;
            public string trace_sha256;
            public float s_init;
            public int k_star;
            public float vertical_fov_deg;
            public int image_width;
            public int image_height;
            public int jpeg_quality = JpegQuality;
            public Scene006Evaluation.Vec3 anchor_world_m;
            public float support_y_m;
            public float ground_plane_y_m = Scene006AnchorPreflight.GroundPlaneYM;
            public float hover_height_m;
            public Scene006Evaluation.Vec3 p_hover_world_m;
            public int[] ticks;
            public int tick_count;
            public PromptReference prompt;
            public string pairing_rule =
                "target samples are the truth crops of the V=1 pre-registered "
                + "ticks; distractor samples are every same-frame "
                + "RateStudyDistractor and scene-vehicle crop; the prompt "
                + "frame is the T6 acquisition frame s_{k*} with V=1";
            public string weights_binding_detector_config =
                "config/detector-reanchor.models.json";
            public string weights_binding_tracker_config =
                "config/nanotrack-v2.models.json";
            public string created_by =
                "TetheredTracking.Scene006.Scene006EvidenceGenerator.RenderProbeFrames";
        }

        /// <summary>
        /// v2 manifest (batch-2 candidate probe): v1 fields plus the
        /// BC-B2-5 bindings — the old default config hash, the candidate
        /// config path, and the reviewed-P3 prompt binding (expected k*
        /// with the artifact identity it came from).
        /// </summary>
        [Serializable]
        public sealed class CandidateManifest : Manifest
        {
            public string baseline_scenario_sha256;
            public string candidate_config_path;
            public int expected_k_star;
            public string k_star_binding_artifact;
            public string k_star_binding_artifact_sha256;
            public string capture_commit;
            public string tool_commit;
            public string[] frozen_tool_paths;
            public bool tool_path_zero_diff_verified;
            public string git_status_porcelain;
            public string scene_file_sha256_before;
            public string scene_file_sha256_after;

            public CandidateManifest()
            {
                schema_version = CandidateManifestSchema;
                created_by = "TetheredTracking.Scene006."
                    + "Scene006EvidenceGenerator.RunCandidateProbe";
            }
        }

        /// <summary>
        /// §5.5 prompt-law v2 echo: the committed selection artifact's
        /// identity plus the full warmup eligibility table and the two
        /// domain-derived bands, so the gate artifact states where the
        /// prompt sits relative to `D` without reading the artifact file.
        /// </summary>
        [Serializable]
        public sealed class PromptEligibility
        {
            public string selection_artifact;
            public string selection_artifact_sha256;
            public string status;
            public int selected_tick;
            public int diagnostic_tick;
            public int d_v_visible_count;
            public bool d_v_all_members_box_ok;
            public int d_v_denominator_assertion_count;
            public float truncation_margin_px;
            public string off_nadir_definition;
            public Scene006PromptSelection.Band min_side_band;
            public Scene006PromptSelection.Band off_nadir_band;
            public Scene006PromptSelection.WarmupTick[] warmup_ticks;
        }

        /// <summary>
        /// v3 manifest (T1′ parity redirection). Inherits the v1 fields and
        /// re-states the batch-2 bindings, so the block is self-contained
        /// for F20: every identity field the gate artifact must echo lives
        /// here verbatim.
        /// </summary>
        [Serializable]
        public sealed class CandidateManifestP2 : Manifest
        {
            public int t1prime_protocol =
                Scene006PromptSelection.T1PrimeProtocol;
            public string baseline_scenario_sha256;
            public string candidate_config_path;
            public int expected_k_star_p2;
            public string selection_artifact;
            public string selection_artifact_sha256;
            public string capture_commit;
            public string tool_commit;
            public string[] frozen_tool_paths;
            public bool tool_path_zero_diff_verified;
            public string git_status_porcelain;
            public string scene_file_sha256_before;
            public string scene_file_sha256_after;
            public string detector_models_config_sha256;
            public string tracker_models_config_sha256;
            public Scene006AppearanceContract.TargetAppearance target_appearance;
            public PromptEligibility prompt_eligibility;

            public CandidateManifestP2()
            {
                schema_version = CandidateManifestSchemaP2;
                created_by = "TetheredTracking.Scene006."
                    + "Scene006EvidenceGenerator.RunCandidateProbeP2";
                pairing_rule =
                    "target samples are the truth crops of the V=1 "
                    + "pre-registered ticks; distractor samples are every "
                    + "same-frame RateStudyDistractor and scene-vehicle crop; "
                    + "the prompt frame is the warmup tick k*' selected by "
                    + "the committed prompt-law v2 artifact";
            }
        }

        /// <summary>
        /// v3 candidate-run extras. `PromptTick` is the committed `k*'`, not
        /// a discovered value: the renderer must render exactly that warmup
        /// frame, and `RecomputeSelection` re-derives the whole selection
        /// before the manifest is written so a drifted artifact aborts the
        /// run instead of producing a consumable capture (§3.2.6 / B3).
        /// </summary>
        public sealed class CandidateExtrasP2
        {
            public int PromptTick;
            public string BaselineScenarioSha256;
            public string CandidateConfigPath;
            public string SelectionArtifactPath;
            public string SelectionArtifactSha256;
            public Scene006PromptSelection.Artifact Selection;
            public Func<Scene006PromptSelection.Artifact> RecomputeSelection;
            public string CaptureCommit;
            public string ToolCommit;
            public string[] FrozenToolPaths;
            public bool ToolPathZeroDiffVerified;
            public string GitStatusPorcelain;
            public string SceneFileSha256Before;
            public Func<string> SceneFileHash;
            public string DetectorModelsConfigSha256;
            public string TrackerModelsConfigSha256;
        }

        /// <summary>
        /// Candidate-run extras. When non-null, Render produces the v2
        /// manifest and enforces, before that manifest is written, both the
        /// reviewed-P3 prompt binding (the discovered acquisition frame must
        /// equal ExpectedKStar) and the §5.6 zero-write contract (the scene
        /// file must hash to SceneFileSha256Before). A violated run
        /// therefore leaves no consumable manifest behind, mirroring the
        /// reviewed StampAndWrite order.
        /// </summary>
        public sealed class CandidateExtras
        {
            public int ExpectedKStar;
            public string BaselineScenarioSha256;
            public string CandidateConfigPath;
            public string KStarBindingArtifact;
            public string KStarBindingArtifactSha256;
            public string CaptureCommit;
            public string ToolCommit;
            public string[] FrozenToolPaths;
            public bool ToolPathZeroDiffVerified;
            public string GitStatusPorcelain;
            public string SceneFileSha256Before;
            public Func<string> SceneFileHash;
        }

        public static int[] ProbeTicks()
        {
            var ticks = new List<int>();
            for (int k = 15; k <= Scene006Trace.HorizonSteps; k += 5)
                ticks.Add(k);
            return ticks.ToArray();
        }

        static Scene006Evaluation.Vec3 ToVec3(Vector3 value) =>
            new Scene006Evaluation.Vec3
            {
                x = value.x,
                y = value.y,
                z = value.z,
            };

        static Vec4 ToVec4(Quaternion value) =>
            new Vec4 { x = value.x, y = value.y, z = value.z, w = value.w };

        static string StableObjectId(Transform transform)
        {
            string value = transform.name;
            Transform parent = transform.parent;
            while (parent != null)
            {
                value = parent.name + "/" + value;
                parent = parent.parent;
            }
            return value;
        }

        public static Manifest Render(
            Scene006SceneRig rig,
            Vector3[] route,
            Scene006Trace.State[] trace,
            string traceSha256,
            float sInit,
            Vector3 anchor,
            float supportY,
            float hoverHeightM,
            int imageWidth,
            int imageHeight,
            string outputDirectory,
            string probeId,
            CandidateExtras extras = null,
            CandidateExtrasP2 extrasP2 = null)
        {
            if (trace == null
                || trace.Length != Scene006Trace.HorizonSteps + 1)
                throw new InvalidOperationException("trace must have 541 states");
            if (extras != null && extrasP2 != null)
            {
                throw new InvalidOperationException(
                    "v2 and v3 candidate extras are mutually exclusive");
            }
            int[] ticks = ProbeTicks();
            var tickSet = new HashSet<int>(ticks);
            if (extrasP2 != null && tickSet.Contains(extrasP2.PromptTick))
            {
                throw new InvalidOperationException(
                    "the selected prompt tick must stay disjoint from the "
                    + "pre-registered measurement tick set");
            }
            string framesDirectory = Path.Combine(outputDirectory, "frames");
            string truthDirectory = Path.Combine(outputDirectory, "truth");
            Directory.CreateDirectory(framesDirectory);
            Directory.CreateDirectory(truthDirectory);

            Transform[] vehicleRoots = SceneVehicleAdjustmentApplier
                .FindSceneVehicleRoots()
                .Where(root => root != null && root.gameObject.activeInHierarchy)
                .ToArray();
            Vector3 pHover = Scene006StationSet.HoverPosition(
                anchor, supportY, hoverHeightM);
            Func<Vector3, Vector3, bool> los =
                (origin, point) => Scene006Visibility.HasClearLineOfSight(
                    origin, point, rig.TargetReplica.transform);

            var renderTexture = new RenderTexture(imageWidth, imageHeight, 24);
            var pixels = new Texture2D(
                imageWidth, imageHeight, TextureFormat.RGB24, false);
            int kStar = -1;
            PromptReference prompt = null;
            int renderedTicks = 0;
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            try
            {
                for (int k = 0; k < trace.Length; k++)
                {
                    Scene006Trace.State state = trace[k];
                    rig.TargetReplica.transform.SetPositionAndRotation(
                        state.Position, state.Rotation);
                    if (k >= 1)
                    {
                        gimbal = Scene006GimbalReplay.Update(
                            gimbal, pHover, state.Position);
                    }
                    rig.EvaluationCamera.transform.SetPositionAndRotation(
                        pHover, gimbal);

                    // v1/v2 discover the prompt as the first visible warmup
                    // frame; v3 renders exactly the committed k*'.
                    bool promptCandidate = extrasP2 != null
                        ? k == extrasP2.PromptTick
                        : kStar < 0 && k <= Scene006Evaluation.T6AcquisitionWindow;
                    bool isTick = tickSet.Contains(k);
                    if (!promptCandidate && !isTick) continue;

                    Scene006Visibility.Snapshot snapshot = EvaluateSnapshot(
                        rig, los, out Bounds bounds, out Vector3[] corners);
                    if (promptCandidate && !snapshot.GeometricallyVisible)
                    {
                        if (extrasP2 != null)
                        {
                            throw new InvalidOperationException(
                                "the committed prompt tick "
                                + extrasP2.PromptTick
                                + " is not geometrically visible at capture "
                                + "time; the selection artifact and the scene "
                                + "disagree");
                        }
                        continue;
                    }
                    if (promptCandidate) kStar = k;

                    NormalizedBoundingBox box = Scene006Visibility.ProjectBounds(
                        rig.EvaluationCamera, corners);
                    string frameName = (isTick ? "frame_" : "prompt_")
                        + k.ToString("D6");
                    WriteFrame(
                        rig,
                        renderTexture,
                        pixels,
                        Path.Combine(framesDirectory, frameName + ".jpg"));
                    TruthRecord truth = BuildTruth(
                        rig,
                        state,
                        k,
                        snapshot,
                        box,
                        imageWidth,
                        imageHeight,
                        vehicleRoots,
                        traceSha256,
                        probeId);
                    // One text for both the file and its hash: an
                    // unprojectable box prints `min_side_px: null` rather
                    // than a bare `NaN` (BC-P2-10).
                    string truthJson = StrictJson(truth);
                    AtomicFile.WriteAllText(
                        Path.Combine(truthDirectory, frameName + ".json"),
                        truthJson);
                    if (isTick)
                    {
                        renderedTicks++;
                    }
                    else
                    {
                        prompt = new PromptReference
                        {
                            tick_k = k,
                            image_file = "frames/" + frameName + ".jpg",
                            truth_file = "truth/" + frameName + ".json",
                            image_sha256 = Scene006RouteGeometry.Sha256Hex(
                                File.ReadAllBytes(Path.Combine(
                                    framesDirectory, frameName + ".jpg"))),
                            truth_sha256 = Scene006RouteGeometry.Sha256Hex(
                                Encoding.UTF8.GetBytes(truthJson)),
                        };
                    }
                }
            }
            finally
            {
                renderTexture.Release();
                UnityEngine.Object.DestroyImmediate(pixels);
            }
            if (renderedTicks != ticks.Length)
            {
                throw new InvalidOperationException(
                    $"probe rendered {renderedTicks} of {ticks.Length} "
                    + "pre-registered ticks");
            }
            if (prompt == null)
            {
                throw new InvalidOperationException(
                    "T6 acquisition frame not found within K_acq = 10; "
                    + "the probe cannot bind a visual prompt");
            }
            if (extras != null && kStar != extras.ExpectedKStar)
            {
                throw new InvalidOperationException(
                    $"prompt_k_star_mismatch: discovered {kStar}, "
                    + $"reviewed P3 binds {extras.ExpectedKStar}");
            }
            if (extrasP2 != null && kStar != extrasP2.PromptTick)
            {
                throw new InvalidOperationException(
                    $"prompt_k_star_p2_mismatch: rendered {kStar}, the "
                    + $"committed artifact binds {extrasP2.PromptTick}");
            }

            if (extrasP2 != null)
            {
                return WriteCandidateManifestP2(
                    rig,
                    extrasP2,
                    traceSha256,
                    sInit,
                    kStar,
                    anchor,
                    supportY,
                    hoverHeightM,
                    imageWidth,
                    imageHeight,
                    ticks,
                    prompt,
                    probeId,
                    outputDirectory);
            }

            if (extras != null)
            {
                // §5.6 zero-write contract, in the reviewed StampAndWrite
                // order: compare the scene-file hash *before* the manifest
                // exists, so a violated run cannot leave a fully-formed,
                // consumable probe directory behind.
                if (extras.SceneFileHash == null)
                {
                    throw new InvalidOperationException(
                        "candidate probe requires a scene-file hash probe "
                        + "for the zero-write check");
                }
                if (!extras.ToolPathZeroDiffVerified)
                {
                    throw new InvalidOperationException(
                        "candidate probe requires a verified §5.6 frozen "
                        + "tool-path zero-diff proof");
                }
                string sceneFileAfter = extras.SceneFileHash();
                if (sceneFileAfter != extras.SceneFileSha256Before)
                {
                    throw new InvalidOperationException(
                        "scene file changed during the candidate probe; the "
                        + "zero-write contract is violated");
                }
                var candidateManifest = new CandidateManifest
                {
                    probe_id = probeId,
                    scenario_id = rig.Config.scenario_id,
                    scenario_sha256 = rig.ScenarioSha256,
                    road_data_sha256 = rig.Config.road_data_sha256,
                    trace_sha256 = traceSha256,
                    s_init = sInit,
                    k_star = kStar,
                    vertical_fov_deg = rig.EvaluationCamera.fieldOfView,
                    image_width = imageWidth,
                    image_height = imageHeight,
                    anchor_world_m = ToVec3(anchor),
                    support_y_m = supportY,
                    hover_height_m = hoverHeightM,
                    p_hover_world_m = ToVec3(pHover),
                    ticks = ticks,
                    tick_count = ticks.Length,
                    prompt = prompt,
                    baseline_scenario_sha256 =
                        extras.BaselineScenarioSha256,
                    candidate_config_path = extras.CandidateConfigPath,
                    expected_k_star = extras.ExpectedKStar,
                    k_star_binding_artifact = extras.KStarBindingArtifact,
                    k_star_binding_artifact_sha256 =
                        extras.KStarBindingArtifactSha256,
                    capture_commit = extras.CaptureCommit,
                    tool_commit = extras.ToolCommit,
                    frozen_tool_paths = extras.FrozenToolPaths,
                    tool_path_zero_diff_verified =
                        extras.ToolPathZeroDiffVerified,
                    git_status_porcelain = extras.GitStatusPorcelain,
                    scene_file_sha256_before = extras.SceneFileSha256Before,
                    scene_file_sha256_after = sceneFileAfter,
                };
                AtomicFile.WriteAllText(
                    Path.Combine(outputDirectory, "manifest.json"),
                    StrictJson(candidateManifest));
                return candidateManifest;
            }

            var manifest = new Manifest
            {
                probe_id = probeId,
                scenario_id = rig.Config.scenario_id,
                scenario_sha256 = rig.ScenarioSha256,
                road_data_sha256 = rig.Config.road_data_sha256,
                trace_sha256 = traceSha256,
                s_init = sInit,
                k_star = kStar,
                vertical_fov_deg = rig.EvaluationCamera.fieldOfView,
                image_width = imageWidth,
                image_height = imageHeight,
                anchor_world_m = ToVec3(anchor),
                support_y_m = supportY,
                hover_height_m = hoverHeightM,
                p_hover_world_m = ToVec3(pHover),
                ticks = ticks,
                tick_count = ticks.Length,
                prompt = prompt,
            };
            AtomicFile.WriteAllText(
                Path.Combine(outputDirectory, "manifest.json"),
                StrictJson(manifest));
            return manifest;
        }

        /// <summary>
        /// The v3 write step, in the fail-closed order the amendment fixes:
        /// re-derive the whole prompt-law selection and compare it to the
        /// committed artifact (§3.2.6), read the actual target appearance
        /// (§3.1.4b), then re-check the scene-file hash — all strictly
        /// before the manifest exists, so a violated run leaves no
        /// consumable capture behind.
        /// </summary>
        static Manifest WriteCandidateManifestP2(
            Scene006SceneRig rig,
            CandidateExtrasP2 extras,
            string traceSha256,
            float sInit,
            int kStar,
            Vector3 anchor,
            float supportY,
            float hoverHeightM,
            int imageWidth,
            int imageHeight,
            int[] ticks,
            PromptReference prompt,
            string probeId,
            string outputDirectory)
        {
            if (extras.SceneFileHash == null || extras.RecomputeSelection == null)
            {
                throw new InvalidOperationException(
                    "the v3 candidate probe requires both a scene-file hash "
                    + "probe and a selection recompute");
            }
            if (!extras.ToolPathZeroDiffVerified)
            {
                throw new InvalidOperationException(
                    "the v3 candidate probe requires a verified §5.6 frozen "
                    + "tool-path zero-diff proof");
            }
            if (extras.Selection == null
                || extras.Selection.status
                    != Scene006PromptSelection.StatusSelected)
            {
                throw new InvalidOperationException(
                    "the committed selection artifact must carry status "
                    + Scene006PromptSelection.StatusSelected);
            }
            Scene006PromptSelection.Artifact recomputed =
                extras.RecomputeSelection();
            string[] differences = Scene006PromptSelection.Compare(
                extras.Selection, recomputed);
            if (differences.Length != 0)
            {
                throw new InvalidOperationException(
                    "the committed selection artifact does not reproduce at "
                    + "capture time:\n  "
                    + string.Join("\n  ", differences));
            }
            Scene006AppearanceContract.TargetAppearance appearance =
                Scene006AppearanceContract.Describe(rig.TargetRenderers);
            string sceneFileAfter = extras.SceneFileHash();
            if (sceneFileAfter != extras.SceneFileSha256Before)
            {
                throw new InvalidOperationException(
                    "scene file changed during the candidate probe; the "
                    + "zero-write contract is violated");
            }
            Scene006PromptSelection.Artifact selection = extras.Selection;
            var manifest = new CandidateManifestP2
            {
                probe_id = probeId,
                scenario_id = rig.Config.scenario_id,
                scenario_sha256 = rig.ScenarioSha256,
                road_data_sha256 = rig.Config.road_data_sha256,
                trace_sha256 = traceSha256,
                s_init = sInit,
                k_star = kStar,
                vertical_fov_deg = rig.EvaluationCamera.fieldOfView,
                image_width = imageWidth,
                image_height = imageHeight,
                anchor_world_m = ToVec3(anchor),
                support_y_m = supportY,
                hover_height_m = hoverHeightM,
                p_hover_world_m = ToVec3(
                    Scene006StationSet.HoverPosition(
                        anchor, supportY, hoverHeightM)),
                ticks = ticks,
                tick_count = ticks.Length,
                prompt = prompt,
                baseline_scenario_sha256 = extras.BaselineScenarioSha256,
                candidate_config_path = extras.CandidateConfigPath,
                expected_k_star_p2 = extras.PromptTick,
                selection_artifact = extras.SelectionArtifactPath,
                selection_artifact_sha256 = extras.SelectionArtifactSha256,
                capture_commit = extras.CaptureCommit,
                tool_commit = extras.ToolCommit,
                frozen_tool_paths = extras.FrozenToolPaths,
                tool_path_zero_diff_verified = extras.ToolPathZeroDiffVerified,
                git_status_porcelain = extras.GitStatusPorcelain,
                scene_file_sha256_before = extras.SceneFileSha256Before,
                scene_file_sha256_after = sceneFileAfter,
                detector_models_config_sha256 =
                    extras.DetectorModelsConfigSha256,
                tracker_models_config_sha256 = extras.TrackerModelsConfigSha256,
                target_appearance = appearance,
                prompt_eligibility = new PromptEligibility
                {
                    selection_artifact = extras.SelectionArtifactPath,
                    selection_artifact_sha256 = extras.SelectionArtifactSha256,
                    status = selection.status,
                    selected_tick = selection.selected_tick,
                    diagnostic_tick = selection.diagnostic_tick,
                    d_v_visible_count = selection.d_v.visible_count,
                    d_v_all_members_box_ok = selection.d_v.all_members_box_ok,
                    d_v_denominator_assertion_count =
                        selection.d_v.denominator_assertion_count,
                    truncation_margin_px = selection.truncation_margin_px,
                    off_nadir_definition = selection.off_nadir_definition,
                    min_side_band = selection.min_side_band,
                    off_nadir_band = selection.off_nadir_band,
                    warmup_ticks = selection.warmup_ticks,
                },
            };
            AtomicFile.WriteAllText(
                Path.Combine(outputDirectory, "manifest.json"),
                StrictJson(manifest));
            return manifest;
        }

        /// <summary>
        /// BC-P2-10: every artifact this renderer writes leaves as standard
        /// JSON. Non-finite floats (an unprojectable box's `min_side_px`,
        /// the warmup edge margins echoed from the selection artifact)
        /// become `null`; the re-scan afterwards is fail-closed.
        /// </summary>
        static string StrictJson<T>(T value)
        {
            string json = Scene006Json.ToStrictJson(
                JsonUtility.ToJson(value, true)) + "\n";
            if (Scene006Json.ContainsNonFiniteToken(json))
            {
                throw new InvalidOperationException(
                    "refusing to write non-standard JSON: a bare non-finite "
                    + "token survived the strict rewrite");
            }
            return json;
        }

        static Scene006Visibility.Snapshot EvaluateSnapshot(
            Scene006SceneRig rig,
            Func<Vector3, Vector3, bool> los,
            out Bounds bounds,
            out Vector3[] corners)
        {
            bounds = rig.TargetRenderers[0].bounds;
            for (int index = 1; index < rig.TargetRenderers.Length; index++)
                bounds.Encapsulate(rig.TargetRenderers[index].bounds);
            corners = Scene006Visibility.BoundsCorners(bounds);
            return Scene006Visibility.Evaluate(
                rig.EvaluationCamera, bounds, corners, los);
        }

        static TruthRecord BuildTruth(
            Scene006SceneRig rig,
            Scene006Trace.State state,
            int k,
            Scene006Visibility.Snapshot snapshot,
            NormalizedBoundingBox box,
            int imageWidth,
            int imageHeight,
            Transform[] vehicleRoots,
            string traceSha256,
            string probeId)
        {
            string boxStatus;
            if (!snapshot.GeometricallyVisible)
                boxStatus = "TARGET_NOT_VISIBLE";
            else if (box == null)
                boxStatus = "TARGET_VISIBLE_UNPROJECTABLE";
            else
                boxStatus = "OK";
            var distractors = new List<DistractorRecord>();
            foreach (Transform root in vehicleRoots)
            {
                NormalizedBoundingBox distractorBox =
                    Scene006Visibility.ProjectRenderers(
                        rig.EvaluationCamera,
                        root.GetComponentsInChildren<Renderer>());
                distractors.Add(new DistractorRecord
                {
                    distractor_id = StableObjectId(root),
                    kind = root.GetComponent<RateStudyDistractor>() != null
                        ? "rate_study_distractor"
                        : "scene_vehicle",
                    box_status = distractorBox == null ? "NOT_IN_FRAME" : "OK",
                    bbox_xywh_norm = distractorBox,
                });
            }
            return new TruthRecord
            {
                probe_id = probeId,
                scenario_id = rig.Config.scenario_id,
                scenario_sha256 = rig.ScenarioSha256,
                trace_sha256 = traceSha256,
                tick_k = k,
                simulation_time_s = k * Scene006Trace.StepSeconds,
                camera_position = ToVec3(rig.EvaluationCamera.transform.position),
                camera_rotation = ToVec4(rig.EvaluationCamera.transform.rotation),
                frustum_sample_count = snapshot.FrustumSampleCount,
                visible_sample_count = snapshot.VisibleSampleCount,
                visible_sample_fraction = snapshot.VisibleFraction,
                frustum_visible = snapshot.FrustumVisible,
                geometrically_visible = snapshot.GeometricallyVisible,
                target_slant_range_m = Vector3.Distance(
                    rig.EvaluationCamera.transform.position, state.Position),
                target_box_status = boxStatus,
                target_bbox_xywh_norm = box,
                target_min_side_px = box == null
                    ? float.NaN
                    : Scene006Visibility.MinSidePx(box, imageWidth, imageHeight),
                distractors = distractors.ToArray(),
            };
        }

        static void WriteFrame(
            Scene006SceneRig rig,
            RenderTexture renderTexture,
            Texture2D pixels,
            string path)
        {
            Camera camera = rig.EvaluationCamera;
            RenderTexture previous = camera.targetTexture;
            camera.targetTexture = renderTexture;
            try
            {
                camera.Render();
                RenderTexture.active = renderTexture;
                pixels.ReadPixels(
                    new Rect(0f, 0f, renderTexture.width, renderTexture.height),
                    0,
                    0);
                pixels.Apply();
                AtomicFile.WriteAllBytes(path, pixels.EncodeToJPG(JpegQuality));
            }
            finally
            {
                RenderTexture.active = null;
                camera.targetTexture = previous;
            }
        }
    }
}
