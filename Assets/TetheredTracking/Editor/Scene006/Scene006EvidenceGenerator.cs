using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// Headless entry points for the P1-SCENE-006 batch-1 offline tools,
    /// invoked with -executeMethod exactly like the existing evidence
    /// generators:
    ///
    ///   .../Unity -batchmode -nographics -projectPath <repo> \
    ///     -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.GenerateBaseline \
    ///     -quit -logFile runtime/test-results/p1-scene-006-baseline.log
    ///
    ///   .../Unity -batchmode -projectPath <repo> \
    ///     -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RenderProbeFrames \
    ///     -quit -logFile runtime/test-results/p1-scene-006-probe-render.log
    ///
    /// GenerateBaseline needs no GPU (projection and raycasts only);
    /// RenderProbeFrames renders and must run without -nographics.
    /// Both are Edit-Mode offline: zero Play, zero scenario creation, zero
    /// session/run ID, zero config writes.
    /// </summary>
    public static class Scene006EvidenceGenerator
    {
        const string BaselineEvidencePath =
            "docs/evidence/P1-SCENE-006-baseline.json";
        const string PreflightEvidencePath =
            "docs/evidence/P1-SCENE-006-anchor-preflight.json";
        const string TraceRuntimePath =
            "runtime/p1-scene-006/trace-sinit0.json";
        const string ProbeRuntimeDirectory =
            "runtime/p1-scene-006/probe-baseline-vfov60";

        [Serializable]
        public sealed class TraceStateRecord
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
        }

        [Serializable]
        public sealed class TraceArtifact
        {
            public string schema_version = "p1-scene-006-trace/v1";
            public string work_id = "P1-SCENE-006";
            public string scenario_id;
            public string scenario_sha256;
            public float s_init;
            public float dt_s = Scene006Trace.StepSeconds;
            public int steps = Scene006Trace.HorizonSteps;
            public int state_count;
            public int first_lap_steps;
            public string first_lap_status;
            public string sha256;
            public TraceStateRecord[] states;
        }

        public static void GenerateBaseline()
        {
            RunGuarded(() =>
            {
                Scene006SceneRig rig = PrepareRig(
                    out ScenarioConfig config,
                    out string scenarioSha256);
                try
                {
                    Vector3[] route = config.TargetRoute();
                    Vector3 anchor = config.Anchor;
                    float supportY = anchor.y;
                    float hover = config.drone.initial_altitude_m;
                    Scene006Trace.State[] trace = Scene006Trace.Generate(
                        route, config.target.speed_mps, 0f);
                    string traceSha = Scene006Trace.HashStates(trace);
                    int firstLap = Scene006Trace.FirstLapSteps(route, 0f, trace);
                    Scene006PathCertificate.ObstaclePrism[] obstacles =
                        rig.BuildObstaclePrisms(
                            Scene006AnchorPreflight.SupportAllowlist);
                    Debug.Log(
                        $"[SCENE-006] obstacle prisms: {obstacles.Length}, "
                        + $"trace sha256 {traceSha}, first lap "
                        + (firstLap > 0 ? firstLap.ToString() : "HORIZON_SHORT"));

                    var inputs = new Scene006Evaluation.Inputs
                    {
                        ScenarioId = config.scenario_id,
                        ScenarioSha256 = scenarioSha256,
                        RoadDataSha256 = config.road_data_sha256,
                        Route = route,
                        Trace = trace,
                        SInit = 0f,
                        TraceSha256 = traceSha,
                        FirstLapSteps = firstLap,
                        Anchor = anchor,
                        SupportY = supportY,
                        HoverHeightM = hover,
                        VerticalFovDeg = config.sensor.vertical_fov_deg,
                        ImageWidth = config.sensor.width,
                        ImageHeight = config.sensor.height,
                        TargetRoot = rig.TargetReplica.transform,
                        TargetRenderers = rig.TargetRenderers,
                        Cam = rig.EvaluationCamera,
                        Obstacles = obstacles,
                        // Batch-1 baseline path: the T5 obstacle set already
                        // excludes road/support instances, so no bound
                        // support instance applies (structural form).
                        SupportInstanceId = null,
                        LineOfSight =
                            (origin, point) =>
                                Scene006Visibility.HasClearLineOfSight(
                                    origin, point, rig.TargetReplica.transform),
                    };
                    Scene006Evaluation.BaselineReport report =
                        Scene006Evaluation.Run(inputs);
                    WriteEvidence(BaselineEvidencePath, report);
                    WriteTraceArtifact(
                        config, scenarioSha256, 0f, trace, firstLap, traceSha);
                    Debug.Log(
                        $"[SCENE-006] baseline: T1 {report.t1.gate} "
                        + $"(p05 {report.t1.min_side_p05_px:F3} px over "
                        + $"{report.t1.domain_count}), T2 {report.t2.gate} "
                        + $"(L_point {report.t2.l_point:F4}), T3 {report.t3.gate} "
                        + $"(L_occ {report.t3.l_occ:F4}, total "
                        + $"{report.t3.total_loss:F4}), T4 {report.t4.gate} "
                        + $"(G {report.t4.g_station:F4} over "
                        + $"{report.t4.certificate_pass_count} certified of "
                        + $"{report.t4.station_count}), T6 {report.t6.gate} "
                        + $"(k* {report.t6.k_star})");

                    var preflight = new Scene006AnchorPreflight.PreflightReport
                    {
                        source_scenario_id = config.scenario_id,
                        source_scenario_sha256 = scenarioSha256,
                        road_data_sha256 = config.road_data_sha256,
                        candidate_preflight = Scene006AnchorPreflight.RunMode(
                            Scene006AnchorPreflight.ModeCandidatePreflight,
                            config,
                            scenarioSha256,
                            rig.RoadData,
                            rig.StaticRoots,
                            new Vector3(150f, 0f, 90f),
                            Scene006AnchorPreflight.CandidateHoverOffsetM,
                            route),
                        current_anchor_baseline = Scene006AnchorPreflight.RunMode(
                            Scene006AnchorPreflight.ModeCurrentAnchorBaseline,
                            config,
                            scenarioSha256,
                            rig.RoadData,
                            rig.StaticRoots,
                            anchor,
                            hover,
                            route),
                    };
                    preflight.contract_json_sha256 =
                        preflight.candidate_preflight.anchor_contract_sha256;
                    WriteEvidence(PreflightEvidencePath, preflight);
                    Debug.Log(
                        $"[SCENE-006] T5 preflight: "
                        + $"{preflight.candidate_preflight.status} "
                        + $"({preflight.candidate_preflight.legal_candidate_count}"
                        + $"/{preflight.candidate_preflight.candidate_count} legal); "
                        + $"current-anchor baseline: "
                        + $"{preflight.current_anchor_baseline.status} "
                        + $"({preflight.current_anchor_baseline.legal_candidate_count}"
                        + $"/{preflight.current_anchor_baseline.candidate_count} legal)");
                }
                finally
                {
                    rig.Cleanup();
                }
            });
        }

        public static void RenderProbeFrames()
        {
            RunGuarded(() =>
            {
                Scene006SceneRig rig = PrepareRig(
                    out ScenarioConfig config,
                    out string _);
                try
                {
                    Vector3[] route = config.TargetRoute();
                    Vector3 anchor = config.Anchor;
                    float supportY = anchor.y;
                    float hover = config.drone.initial_altitude_m;
                    Scene006Trace.State[] trace = Scene006Trace.Generate(
                        route, config.target.speed_mps, 0f);
                    string traceSha = Scene006Trace.HashStates(trace);
                    string directory = RuntimePaths.ProjectFile(
                        ProbeRuntimeDirectory.Split('/'));
                    PrepareProbeDirectory(
                        directory, Scene006ProbeRenderer.ProbeId);
                    Scene006ProbeRenderer.Manifest manifest =
                        Scene006ProbeRenderer.Render(
                            rig,
                            route,
                            trace,
                            traceSha,
                            0f,
                            anchor,
                            supportY,
                            hover,
                            config.sensor.width,
                            config.sensor.height,
                            directory,
                            Scene006ProbeRenderer.ProbeId);
                    Debug.Log(
                        $"[SCENE-006] probe frames: {manifest.tick_count} ticks "
                        + $"plus prompt k* = {manifest.k_star} rendered into "
                        + directory);
                }
                finally
                {
                    rig.Cleanup();
                }
            });
        }

        static Scene006SceneRig PrepareRig(
            out ScenarioConfig config,
            out string scenarioSha256)
        {
            var rig = new Scene006SceneRig
            {
                Config = Scene006SceneRig.LoadFrozenScenario(
                    out scenarioSha256),
            };
            config = rig.Config;
            rig.ScenarioSha256 = scenarioSha256;
            rig.OpenCityScene();
            rig.ApplySceneAdjustments();
            rig.LoadRoadData();
            rig.CreateTargetReplica();
            rig.CreateEvaluationCamera(
                config.sensor.vertical_fov_deg,
                config.sensor.width,
                config.sensor.height);
            rig.CollectStaticRoots(rig.TargetReplica.transform);
            rig.BuildOcclusionProxies();
            return rig;
        }

        /// <summary>
        /// Batch-2 candidate T1′ frame rendering (§30 BC-B2-5/6). Runs only
        /// after the reviewed config exists; the candidate config is bound
        /// fail-closed to the BC-B2-3/4 frozen values and the reviewed P3
        /// artifact supplies s_init / trace hash / k*.
        ///
        ///   .../Unity -batchmode -projectPath <repo> \
        ///     -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RunCandidateProbe \
        ///     -quit -logFile runtime/test-results/p1-scene-006-probe-candidate.log
        ///
        /// Rendering needs graphics: no -nographics on this one.
        /// </summary>
        public static void RunCandidateProbe()
        {
            RunGuarded(() =>
            {
                ScenarioConfig defaultConfig =
                    Scene006SceneRig.LoadFrozenScenario(out string defaultSha);
                Scene006CandidateProbe.CandidateIdentity candidate =
                    Scene006CandidateProbe.LoadAndBind(
                        RuntimePaths.ProjectFile(
                            Scene006CandidateProbe.CandidateConfigPath),
                        RuntimePaths.ProjectFile(
                            Scene006CandidateProbe.P3ArtifactPath),
                        defaultConfig);

                string head = RunGit("rev-parse HEAD");
                string porcelain = RunGit("status --porcelain");
                if (porcelain.Length != 0)
                {
                    throw new InvalidOperationException(
                        "candidate probe requires a clean worktree; git "
                        + "status --porcelain is non-empty:\n" + porcelain);
                }
                // §5.6 identity pair: tool_commit is the last commit that
                // changed the frozen tool path set along this capture
                // history, not the capture HEAD; ResolveToolCommit also
                // discharges the zero-diff proof when the two differ.
                Scene006CandidateProbe.ToolCommitBinding toolBinding =
                    Scene006CandidateProbe.ResolveToolCommit(head);
                string sceneFileBefore = SceneFileHash();

                var rig = new Scene006SceneRig
                {
                    Config = candidate.Config,
                    ScenarioSha256 = candidate.ConfigSha256,
                };
                try
                {
                    rig.OpenCityScene();
                    rig.ApplySceneAdjustments();
                    rig.LoadRoadData();
                    rig.CreateTargetReplica();
                    rig.CreateEvaluationCamera(
                        candidate.Config.sensor.vertical_fov_deg,
                        candidate.Config.sensor.width,
                        candidate.Config.sensor.height);
                    rig.CollectStaticRoots(rig.TargetReplica.transform);
                    rig.BuildOcclusionProxies();

                    Vector3[] route = candidate.Config.TargetRoute();
                    Scene006Trace.State[] trace = Scene006Trace.Generate(
                        route,
                        candidate.Config.target.speed_mps,
                        candidate.SInit);
                    string traceSha = Scene006Trace.HashStates(trace);
                    if (traceSha != candidate.TraceSha256)
                    {
                        throw new InvalidOperationException(
                            "candidate trace diverges from the reviewed P3 "
                            + "trace binding");
                    }
                    string directory = RuntimePaths.ProjectFile(
                        Scene006CandidateProbe.ProbeDirectory.Split('/'));
                    PrepareProbeDirectory(
                        directory, Scene006CandidateProbe.ProbeId);
                    var extras = new Scene006ProbeRenderer.CandidateExtras
                    {
                        ExpectedKStar = candidate.KStar,
                        BaselineScenarioSha256 = defaultSha,
                        CandidateConfigPath =
                            Scene006CandidateProbe.CandidateConfigPath,
                        KStarBindingArtifact =
                            Scene006CandidateProbe.P3ArtifactPath,
                        KStarBindingArtifactSha256 =
                            candidate.P3ArtifactSha256,
                        CaptureCommit = head,
                        ToolCommit = toolBinding.ToolCommit,
                        FrozenToolPaths = toolBinding.FrozenPaths,
                        ToolPathZeroDiffVerified =
                            toolBinding.ZeroDiffVerified,
                        GitStatusPorcelain = porcelain,
                        SceneFileSha256Before = sceneFileBefore,
                        SceneFileHash = SceneFileHash,
                    };
                    Scene006ProbeRenderer.Manifest manifest =
                        Scene006ProbeRenderer.Render(
                            rig,
                            route,
                            trace,
                            traceSha,
                            candidate.SInit,
                            candidate.Config.Anchor,
                            candidate.Config.Anchor.y,
                            candidate.Config.drone.initial_altitude_m,
                            candidate.Config.sensor.width,
                            candidate.Config.sensor.height,
                            directory,
                            Scene006CandidateProbe.ProbeId,
                            extras);
                    // The zero-write comparison itself runs inside Render,
                    // immediately before the manifest write, so a violation
                    // leaves no consumable artifact; the manifest records
                    // both scene-file hashes.
                    UnityEngine.Debug.Log(
                        $"[SCENE-006] candidate probe: {manifest.tick_count} "
                        + $"ticks plus prompt k* = {manifest.k_star} "
                        + "rendered into " + directory);
                }
                finally
                {
                    rig.Cleanup();
                }
            });
        }

        const string T1PrimeP2EvidencePath =
            "docs/evidence/P1-SCENE-006-t1prime-p2.md";

        /// <summary>
        /// The machine-checkable form of the COORD-005 human-fidelity
        /// record. The P stage only asserts that the confirmation line is
        /// present in the batch evidence file; the substance of the check
        /// is the human's, and the frames themselves never enter the
        /// evidence chain (§3.3).
        /// </summary>
        const string Coord005ConfirmationMarker =
            "COORD-005-CONFIRMATION: CONFIRMED";

        const string DetectorModelsConfigPath =
            "config/detector-reanchor.models.json";
        const string TrackerModelsConfigPath =
            "config/nanotrack-v2.models.json";

        /// <summary>
        /// §3.5.3 stage X — the one formal T1′(v2) capture. Every check in
        /// <see cref="RunPrechecksP2"/> runs first and costs no execution
        /// quota; the quota starts the moment the formal probe directory is
        /// created, and any abort after that point counts as the single
        /// permitted execution.
        ///
        ///   .../Unity -batchmode -projectPath &lt;repo&gt; \
        ///     -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RunCandidateProbeP2 \
        ///     -quit -logFile runtime/test-results/p1-scene-006-probe-candidate-p2.log
        ///
        /// Rendering needs graphics: no -nographics on this one.
        /// </summary>
        public static void RunCandidateProbeP2()
        {
            RunGuarded(() =>
            {
                ScenarioConfig defaultConfig =
                    Scene006SceneRig.LoadFrozenScenario(out string defaultSha);
                Scene006CandidateProbe.CandidateIdentity candidate =
                    BindCandidate(defaultConfig);
                Scene006SceneRig rig = BuildCandidateRig(candidate);
                try
                {
                    Scene006Trace.State[] trace =
                        BuildCandidateTrace(candidate);
                    Scene006PromptSelection.Inputs selectionInputs =
                        BuildSelectionInputs(candidate, rig, trace);
                    Func<Scene006PromptSelection.Artifact> recompute =
                        () => Scene006PromptSelection.Compute(selectionInputs);

                    PrecheckResult precheck = RunPrechecksP2(
                        recompute, rig.TargetRenderers);

                    // ---- stage X starts here: quota is consumed ----
                    string directory = RuntimePaths.ProjectFile(
                        Scene006CandidateProbe.ProbeDirectoryP2.Split('/'));
                    CreateFormalProbeDirectoryP2(directory);
                    var extras = new Scene006ProbeRenderer.CandidateExtrasP2
                    {
                        PromptTick = precheck.Selection.selected_tick,
                        BaselineScenarioSha256 = defaultSha,
                        CandidateConfigPath =
                            Scene006CandidateProbe.CandidateConfigPath,
                        SelectionArtifactPath =
                            Scene006PromptSelection.ArtifactProjectPath,
                        SelectionArtifactSha256 =
                            precheck.SelectionArtifactSha256,
                        Selection = precheck.Selection,
                        RecomputeSelection = recompute,
                        CaptureCommit = precheck.CaptureCommit,
                        ToolCommit = precheck.ToolCommit,
                        FrozenToolPaths = precheck.FrozenToolPaths,
                        ToolPathZeroDiffVerified = true,
                        GitStatusPorcelain = precheck.GitStatusPorcelain,
                        SceneFileSha256Before = precheck.SceneFileSha256Before,
                        SceneFileHash = SceneFileHash,
                        DetectorModelsConfigSha256 =
                            precheck.DetectorModelsConfigSha256,
                        TrackerModelsConfigSha256 =
                            precheck.TrackerModelsConfigSha256,
                    };
                    Vector3 anchor = candidate.Config.Anchor;
                    Scene006ProbeRenderer.Manifest manifest =
                        Scene006ProbeRenderer.Render(
                            rig,
                            candidate.Config.TargetRoute(),
                            trace,
                            candidate.TraceSha256,
                            candidate.SInit,
                            anchor,
                            anchor.y,
                            candidate.Config.drone.initial_altitude_m,
                            candidate.Config.sensor.width,
                            candidate.Config.sensor.height,
                            directory,
                            Scene006CandidateProbe.ProbeIdP2,
                            null,
                            extras);
                    Debug.Log(
                        $"[SCENE-006] candidate probe p2: {manifest.tick_count}"
                        + $" ticks plus prompt k*' = {manifest.k_star} "
                        + "rendered into " + directory);
                }
                finally
                {
                    rig.Cleanup();
                }
            });
        }

        sealed class PrecheckResult
        {
            public Scene006PromptSelection.Artifact Selection;
            public string SelectionArtifactSha256;
            public string CaptureCommit;
            public string ToolCommit;
            public string[] FrozenToolPaths;
            public string GitStatusPorcelain;
            public string SceneFileSha256Before;
            public string DetectorModelsConfigSha256;
            public string TrackerModelsConfigSha256;
        }

        /// <summary>
        /// §3.5.3 stage P: selection cross-check, appearance dry run, model
        /// config hashes, identity chain and the COORD-005 record. Every
        /// failure throws a named `T1P2_PRECHECK_FAIL_&lt;reason&gt;` before
        /// the formal probe directory exists, so none of them consumes the
        /// single execution quota.
        /// </summary>
        static PrecheckResult RunPrechecksP2(
            Func<Scene006PromptSelection.Artifact> recompute,
            Renderer[] targetRenderers)
        {
            string artifactPath = RuntimePaths.ProjectFile(
                Scene006PromptSelection.ArtifactProjectPath.Split('/'));
            if (!File.Exists(artifactPath))
            {
                throw PrecheckFail(
                    "SELECTION_ARTIFACT",
                    "the committed selection artifact is missing: "
                    + Scene006PromptSelection.ArtifactProjectPath);
            }
            byte[] artifactBytes = File.ReadAllBytes(artifactPath);
            Scene006PromptSelection.Artifact committed;
            try
            {
                committed = Scene006PromptSelection.Deserialize(
                    System.Text.Encoding.UTF8.GetString(artifactBytes));
            }
            catch (Exception exception)
            {
                throw PrecheckFail(
                    "SELECTION_ARTIFACT", exception.Message);
            }
            if (committed.status != Scene006PromptSelection.StatusSelected
                || committed.selected_tick
                    == Scene006PromptSelection.NoSelection)
            {
                throw PrecheckFail(
                    "SELECTION_ARTIFACT",
                    "the committed artifact carries status "
                    + committed.status + "; no formal capture is authorized");
            }
            string[] differences = Scene006PromptSelection.Compare(
                committed, recompute());
            if (differences.Length != 0)
            {
                throw PrecheckFail(
                    "SELECTION_ARTIFACT",
                    "the committed artifact does not reproduce:\n  "
                    + string.Join("\n  ", differences));
            }

            try
            {
                Scene006AppearanceContract.Verify(
                    Scene006AppearanceContract.Describe(targetRenderers));
            }
            catch (Exception exception)
            {
                throw PrecheckFail("TARGET_APPEARANCE", exception.Message);
            }

            string detectorSha;
            string trackerSha;
            try
            {
                detectorSha = ProjectFileSha256(DetectorModelsConfigPath);
                trackerSha = ProjectFileSha256(TrackerModelsConfigPath);
            }
            catch (Exception exception)
            {
                throw PrecheckFail("MODEL_CONFIG_HASH", exception.Message);
            }

            string head = RunGit("rev-parse HEAD");
            string porcelain = RunGit("status --porcelain");
            if (porcelain.Length != 0)
            {
                throw PrecheckFail(
                    "IDENTITY_CHAIN",
                    "the candidate probe requires a clean worktree; git "
                    + "status --porcelain is non-empty:\n" + porcelain);
            }
            Scene006CandidateProbe.ToolCommitBinding toolBinding;
            try
            {
                toolBinding =
                    Scene006CandidateProbe.ResolveToolCommitV2(head);
            }
            catch (Exception exception)
            {
                throw PrecheckFail("IDENTITY_CHAIN", exception.Message);
            }

            string evidencePath = RuntimePaths.ProjectFile(
                T1PrimeP2EvidencePath.Split('/'));
            if (!File.Exists(evidencePath)
                || !File.ReadAllText(evidencePath).Contains(
                    Coord005ConfirmationMarker))
            {
                throw PrecheckFail(
                    "COORD005_RECORD",
                    "the COORD-005 human-fidelity confirmation line is not "
                    + "present in " + T1PrimeP2EvidencePath);
            }

            return new PrecheckResult
            {
                Selection = committed,
                SelectionArtifactSha256 =
                    Scene006RouteGeometry.Sha256Hex(artifactBytes),
                CaptureCommit = head,
                ToolCommit = toolBinding.ToolCommit,
                FrozenToolPaths = toolBinding.FrozenPaths,
                GitStatusPorcelain = porcelain,
                SceneFileSha256Before = SceneFileHash(),
                DetectorModelsConfigSha256 = detectorSha,
                TrackerModelsConfigSha256 = trackerSha,
            };
        }

        static string ProjectFileSha256(string projectRelativePath)
        {
            string path = RuntimePaths.ProjectFile(
                projectRelativePath.Split('/'));
            if (!File.Exists(path))
                throw new InvalidOperationException(
                    "missing model config: " + projectRelativePath);
            return Scene006RouteGeometry.Sha256Hex(File.ReadAllBytes(path));
        }

        static InvalidOperationException PrecheckFail(
            string reason, string detail)
        {
            return new InvalidOperationException(
                "T1P2_PRECHECK_FAIL_" + reason + ": " + detail);
        }

        /// <summary>
        /// The quota boundary. An existing non-empty directory means a
        /// formal execution already happened: refuse rather than start a
        /// second one (§3.5.3).
        /// </summary>
        static void CreateFormalProbeDirectoryP2(string directory)
        {
            if (Directory.Exists(directory)
                && (Directory.GetFileSystemEntries(directory).Length != 0))
            {
                throw new InvalidOperationException(
                    "the formal T1'(v2) probe directory already exists and is "
                    + "non-empty; the single execution quota is spent: "
                    + directory);
            }
            Directory.CreateDirectory(directory);
        }

        /// <summary>
        /// §3.2 prompt-law v2 selection: replays the frozen trace/gimbal
        /// geometry over the candidate scene and commits the selection
        /// artifact. Zero rendering, zero detector, zero execution quota —
        /// this runs during the implementation stage and its artifact must
        /// be committed before any diagnostic frame or formal capture.
        ///
        ///   .../Unity -batchmode -nographics -projectPath &lt;repo&gt; \
        ///     -executeMethod TetheredTracking.Scene006.Scene006EvidenceGenerator.RunPromptSelection \
        ///     -quit -logFile runtime/test-results/p1-scene-006-prompt-selection.log
        ///
        /// The two protocol terminals are written as evidence rather than
        /// thrown: a `D_V` fidelity contradiction produces only the named
        /// failure report (BC-P2-4), an empty `E` produces the full
        /// selection artifact with `selected_tick: null` (BC-P2-5).
        /// </summary>
        public static void RunPromptSelection()
        {
            RunGuarded(() =>
            {
                Scene006PromptSelection.Artifact artifact =
                    ComputePromptSelection(out Scene006SceneRig rig);
                try
                {
                    string json =
                        Scene006PromptSelection.Serialize(artifact);
                    bool fidelityFailure = artifact.status
                        == Scene006PromptSelection
                            .StatusFidelityContradiction;
                    string relative = fidelityFailure
                        ? Scene006PromptSelection.FidelityReportProjectPath
                        : Scene006PromptSelection.ArtifactProjectPath;
                    File.WriteAllText(
                        RuntimePaths.ProjectFile(relative.Split('/')), json);
                    Debug.Log(
                        "[SCENE-006] prompt selection: status "
                        + artifact.status + ", |D| "
                        + artifact.d_v.visible_count + ", k*' "
                        + artifact.selected_tick + ", k_diag "
                        + artifact.diagnostic_tick + " -> " + relative);
                }
                finally
                {
                    rig.Cleanup();
                }
            });
        }

        /// <summary>
        /// Builds the candidate rig and runs the prompt-law replay. The rig
        /// is returned so the caller can clean it up after writing, and so
        /// the capture path can reuse the identical construction for its
        /// pre-write recompute.
        /// </summary>
        static Scene006PromptSelection.Artifact ComputePromptSelection(
            out Scene006SceneRig rig)
        {
            ScenarioConfig defaultConfig =
                Scene006SceneRig.LoadFrozenScenario(out string _);
            Scene006CandidateProbe.CandidateIdentity candidate =
                BindCandidate(defaultConfig);
            rig = BuildCandidateRig(candidate);
            Scene006Trace.State[] trace = BuildCandidateTrace(candidate);
            return Scene006PromptSelection.Compute(
                BuildSelectionInputs(candidate, rig, trace));
        }

        static Scene006CandidateProbe.CandidateIdentity BindCandidate(
            ScenarioConfig defaultConfig)
        {
            Scene006CandidateProbe.CandidateIdentity candidate =
                Scene006CandidateProbe.LoadAndBind(
                    RuntimePaths.ProjectFile(
                        Scene006CandidateProbe.CandidateConfigPath),
                    RuntimePaths.ProjectFile(
                        Scene006CandidateProbe.P3ArtifactPath),
                    defaultConfig);
            if (candidate.ConfigSha256
                != Scene006CandidateProbe.FrozenCandidateConfigSha256)
            {
                throw new InvalidOperationException(
                    "candidate config bytes are frozen (C3): expected "
                    + Scene006CandidateProbe.FrozenCandidateConfigSha256
                    + ", got " + candidate.ConfigSha256);
            }
            return candidate;
        }

        static Scene006SceneRig BuildCandidateRig(
            Scene006CandidateProbe.CandidateIdentity candidate)
        {
            var rig = new Scene006SceneRig
            {
                Config = candidate.Config,
                ScenarioSha256 = candidate.ConfigSha256,
            };
            rig.OpenCityScene();
            rig.ApplySceneAdjustments();
            rig.LoadRoadData();
            rig.CreateTargetReplica();
            rig.CreateEvaluationCamera(
                candidate.Config.sensor.vertical_fov_deg,
                candidate.Config.sensor.width,
                candidate.Config.sensor.height);
            rig.CollectStaticRoots(rig.TargetReplica.transform);
            rig.BuildOcclusionProxies();
            return rig;
        }

        static Scene006Trace.State[] BuildCandidateTrace(
            Scene006CandidateProbe.CandidateIdentity candidate)
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                candidate.Config.TargetRoute(),
                candidate.Config.target.speed_mps,
                candidate.SInit);
            string traceSha = Scene006Trace.HashStates(trace);
            if (traceSha != candidate.TraceSha256)
            {
                throw new InvalidOperationException(
                    "candidate trace diverges from the reviewed P3 trace "
                    + "binding");
            }
            return trace;
        }

        static Scene006PromptSelection.Inputs BuildSelectionInputs(
            Scene006CandidateProbe.CandidateIdentity candidate,
            Scene006SceneRig rig,
            Scene006Trace.State[] trace)
        {
            Vector3 anchor = candidate.Config.Anchor;
            return new Scene006PromptSelection.Inputs
            {
                Rig = rig,
                Trace = trace,
                PHover = Scene006StationSet.HoverPosition(
                    anchor, anchor.y, candidate.Config.drone.initial_altitude_m),
                Anchor = anchor,
                ImageWidth = candidate.Config.sensor.width,
                ImageHeight = candidate.Config.sensor.height,
                VerticalFovDeg = candidate.Config.sensor.vertical_fov_deg,
                ScenarioId = candidate.Config.scenario_id,
                ScenarioSha256 = candidate.ConfigSha256,
                RoadDataSha256 = candidate.Config.road_data_sha256,
                TraceSha256 = candidate.TraceSha256,
                SInit = candidate.SInit,
                P3ArtifactPath = Scene006CandidateProbe.P3ArtifactPath,
                P3ArtifactSha256 = candidate.P3ArtifactSha256,
                P3T6 = candidate.T6,
            };
        }

        static string SceneFileHash()
        {
            return Scene006RouteGeometry.Sha256Hex(
                File.ReadAllBytes(Scene006SceneRig.CityScenePath));
        }

        static string RunGit(string arguments)
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

        static void PrepareProbeDirectory(
            string directory, string expectedProbeId)
        {
            if (!Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
                return;
            }
            string manifestPath = Path.Combine(directory, "manifest.json");
            if (!File.Exists(manifestPath))
            {
                throw new InvalidOperationException(
                    "probe directory exists without a manifest; refusing to "
                    + "mix unknown content: " + directory);
            }
            string manifestText = File.ReadAllText(manifestPath);
            if (!manifestText.Contains(
                "\"probe_id\": \"" + expectedProbeId + "\""))
            {
                throw new InvalidOperationException(
                    "probe directory belongs to a different probe; refusing "
                    + "to overwrite: " + directory);
            }
            Directory.Delete(directory, true);
            Directory.CreateDirectory(directory);
        }

        static void WriteTraceArtifact(
            ScenarioConfig config,
            string scenarioSha256,
            float sInit,
            Scene006Trace.State[] trace,
            int firstLap,
            string traceSha)
        {
            var states = new TraceStateRecord[trace.Length];
            for (int k = 0; k < trace.Length; k++)
            {
                states[k] = new TraceStateRecord
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
                };
            }
            var artifact = new TraceArtifact
            {
                scenario_id = config.scenario_id,
                scenario_sha256 = scenarioSha256,
                s_init = sInit,
                state_count = trace.Length,
                first_lap_steps = firstLap,
                first_lap_status = firstLap > 0 ? "MEASURED" : "HORIZON_SHORT",
                sha256 = traceSha,
                states = states,
            };
            AtomicFile.WriteAllText(
                RuntimePaths.ProjectFile(TraceRuntimePath.Split('/')),
                JsonUtility.ToJson(artifact, true) + "\n");
        }

        static void WriteEvidence<T>(string projectRelativePath, T report)
        {
            File.WriteAllText(
                RuntimePaths.ProjectFile(projectRelativePath.Split('/')),
                JsonUtility.ToJson(report, true) + "\n");
        }

        delegate void Run();

        static void RunGuarded(Run run)
        {
            try
            {
                run();
            }
            catch (Exception exception)
            {
                Debug.LogException(exception);
                EditorApplication.Exit(1);
            }
        }
    }
}
