using System;
using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 batch-2 tool stage (C_b2tool): the candidate-config
    /// binding loader. Every check is fail-closed; the happy path mirrors
    /// the BC-B2-3/4 frozen fields against the reviewed P3 identity.
    /// </summary>
    public sealed class Scene006CandidateProbeEditModeTests
    {
        const string FakeSha =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

        static ScenarioConfig SyntheticDefault()
        {
            ScenarioConfig config = ScenarioConfig.CreateDefault();
            config.road_data_sha256 = new string('a', 64);
            config.scene_adjustments = new SceneAdjustmentsScenarioConfig
            {
                vehicle_relocations =
                    Array.Empty<VehicleRelocationScenarioConfig>(),
                expected_distractor_count = 0,
                route_corridor = new RouteCorridorScenarioConfig
                {
                    target_half_width_m = 1.0f,
                    clearance_margin_m = 0.5f,
                    target_bottom_offset_m = 0.0f,
                    target_height_m = 1.55f,
                    vertical_clearance_margin_m = 0.5f,
                    road_sample_spacing_m = 0.5f,
                    enable_dynamic_intersection_audit = false,
                    enable_jump_diagnostic = false,
                    jump_epsilon_m = 0.001f,
                },
            };
            return config;
        }

        static ScenarioConfig SyntheticCandidate()
        {
            ScenarioConfig config = SyntheticDefault();
            config.scenario_id = "p1-scene-006-difficult-v1";
            config.anchor_world_m = new ScenarioVector3(
                197f, (float)Scene006CandidateProbe.FrozenAnchorY, 30f);
            config.drone.initial_altitude_m = 16f;
            config.sensor.vertical_fov_deg = 40f;
            Vector3[] route = Scene006CandidateContract.FamilyRoute(
                Scene006CandidateContract.FamilyB,
                ScenarioConfig.CreateDefault().TargetRoute());
            var routeJson = new ScenarioVector3[route.Length];
            for (int index = 0; index < route.Length; index++)
            {
                routeJson[index] = new ScenarioVector3(
                    route[index].x, route[index].y, route[index].z);
            }
            config.target.route_world_m = routeJson;
            var rows =
                new VehicleRelocationScenarioConfig[
                    Scene006CandidateContract.FamilyBRelocations.Length];
            for (int index = 0;
                index < Scene006CandidateContract.FamilyBRelocations.Length;
                index++)
            {
                Scene006CandidateContract.AuthorizedRelocation authorized =
                    Scene006CandidateContract.FamilyBRelocations[index];
                rows[index] = new VehicleRelocationScenarioConfig
                {
                    prefab_name = authorized.PrefabName,
                    original_xz_m = new ScenarioVector2(
                        authorized.OriginalXz.x, authorized.OriginalXz.y),
                    match_tolerance_m =
                        Scene006CandidateContract.RelocationMatchToleranceM,
                    new_position_m = new ScenarioVector3(
                        authorized.NewPosition.x,
                        authorized.NewPosition.y,
                        authorized.NewPosition.z),
                    mark_as_distractor = false,
                    remove_from_scene = false,
                };
            }
            config.scene_adjustments.vehicle_relocations = rows;
            return config;
        }

        static string WriteTemp(object document, string name)
        {
            string path = Path.Combine(
                Path.GetTempPath(),
                "scene006-" + Guid.NewGuid().ToString("N") + "-" + name);
            File.WriteAllText(path, JsonUtility.ToJson(document, true) + "\n");
            return path;
        }

        static string WriteP3Artifact()
        {
            var report = new Scene006FinalistGenerator.P3Report
            {
                status = "P3_OK",
                selection = new Scene006FinalistGenerator.SelectionSection
                {
                    finalist = new Scene006FinalistSelection.ScoredCell
                    {
                        family = "B",
                        anchor_x_m = 197f,
                        anchor_z_m = 30f,
                        initial_altitude_m = 16f,
                        vertical_fov_deg = 40f,
                        s_init = 184.22793579101562f,
                        trace_sha256 = FakeSha,
                    },
                },
                finalist_trace_s_init = 184.22793579101562f,
                finalist_trace_sha256 = FakeSha,
                t6 = new Scene006Evaluation.T6Record { k_star = 2 },
            };
            return WriteTemp(report, "p3.json");
        }

        static string WriteCandidate(ScenarioConfig config) =>
            WriteTemp(config, "candidate.json");

        [Test]
        public void HappyPathBindsReviewedIdentity()
        {
            string p3 = WriteP3Artifact();
            string candidate = WriteCandidate(SyntheticCandidate());
            try
            {
                Scene006CandidateProbe.CandidateIdentity identity =
                    Scene006CandidateProbe.LoadAndBind(
                        candidate, p3, SyntheticDefault());
                Assert.AreEqual(
                    "p1-scene-006-difficult-v1",
                    identity.Config.scenario_id);
                Assert.AreEqual(184.22793579101562f, identity.SInit, 1e-6f);
                Assert.AreEqual(FakeSha, identity.TraceSha256);
                Assert.AreEqual(2, identity.KStar);
                Assert.AreEqual(64, identity.ConfigSha256.Length);
                Assert.AreEqual(64, identity.P3ArtifactSha256.Length);
            }
            finally
            {
                File.Delete(p3);
                File.Delete(candidate);
            }
        }

        [Test]
        public void RejectsEveryBindingViolation()
        {
            (string name, Action<ScenarioConfig> mutate)[] cases =
            {
                ("scenario-id", c =>
                    c.scenario_id = "wrong"),
                ("anchor-y", c =>
                    c.anchor_world_m = new ScenarioVector3(197f, 0.2f, 30f)),
                ("altitude", c =>
                    c.drone.initial_altitude_m = 20f),
                ("vfov", c =>
                    c.sensor.vertical_fov_deg = 30f),
                ("route", c =>
                    c.target.route_world_m[0] = new ScenarioVector3(
                        185.6f, 0.2f, 57.5f)),
                ("relocation-landing", c =>
                    c.scene_adjustments.vehicle_relocations[0]
                        .new_position_m.z += 0.5f),
                ("distractor-flag", c =>
                    c.scene_adjustments.vehicle_relocations[0]
                        .mark_as_distractor = true),
                ("distractor-count", c =>
                    c.scene_adjustments.expected_distractor_count = 1),
                ("capture-hz", c =>
                    c.sensor.capture_hz = 20f),
                ("corridor", c =>
                    c.scene_adjustments.route_corridor
                        .clearance_margin_m = 0.6f),
                ("schema-version", c =>
                    c.schema_version = "tethered-scenario/v2"),
                ("corridor-intersection-audit-flag", c =>
                    c.scene_adjustments.route_corridor
                        .enable_dynamic_intersection_audit = true),
                ("corridor-jump-diagnostic-flag", c =>
                    c.scene_adjustments.route_corridor
                        .enable_jump_diagnostic = true),
            };
            // Collect every case that failed to throw instead of aborting on
            // the first, so a regression reports the full set of fields that
            // stopped being frozen.
            var accepted = new List<string>();
            foreach ((string name, Action<ScenarioConfig> mutate) in cases)
            {
                string p3 = WriteP3Artifact();
                ScenarioConfig config = SyntheticCandidate();
                mutate(config);
                string candidate = WriteCandidate(config);
                try
                {
                    Scene006CandidateProbe.LoadAndBind(
                        candidate, p3, SyntheticDefault());
                    accepted.Add(name);
                }
                catch (InvalidOperationException)
                {
                    // Expected: the binding is fail-closed for this field.
                }
                finally
                {
                    File.Delete(p3);
                    File.Delete(candidate);
                }
            }
            CollectionAssert.IsEmpty(
                accepted, "binding accepted violations: " + accepted.Count);
        }

        [Test]
        public void RejectsMissingRelocationRowAndNonOkP3()
        {
            string p3 = WriteP3Artifact();
            ScenarioConfig config = SyntheticCandidate();
            config.scene_adjustments.vehicle_relocations =
                new VehicleRelocationScenarioConfig[4];
            Array.Copy(
                SyntheticCandidate().scene_adjustments.vehicle_relocations,
                config.scene_adjustments.vehicle_relocations,
                4);
            string candidate = WriteCandidate(config);
            try
            {
                Assert.Throws<InvalidOperationException>(
                    () => Scene006CandidateProbe.LoadAndBind(
                        candidate, p3, SyntheticDefault()));
            }
            finally
            {
                File.Delete(p3);
                File.Delete(candidate);
            }

            var report = new Scene006FinalistGenerator.P3Report
            {
                status = "BLOCKED_FINALIST_AUDIT_FAILED",
            };
            string badP3 = WriteTemp(report, "p3-not-ok.json");
            string goodCandidate = WriteCandidate(SyntheticCandidate());
            try
            {
                Assert.Throws<InvalidOperationException>(
                    () => Scene006CandidateProbe.LoadAndBind(
                        goodCandidate, badP3, SyntheticDefault()));
            }
            finally
            {
                File.Delete(badP3);
                File.Delete(goodCandidate);
            }
        }

        /// <summary>
        /// Records every `git &lt;arguments&gt;` call and replays canned
        /// stdout, so the §5.6 tool_commit semantics can be pinned without a
        /// real repository.
        /// </summary>
        sealed class GitStub
        {
            public readonly List<string> Calls = new List<string>();
            public string LogOutput = string.Empty;
            public string DiffOutput = string.Empty;

            public string Run(string arguments)
            {
                Calls.Add(arguments);
                if (arguments.StartsWith("log ", StringComparison.Ordinal))
                    return LogOutput;
                if (arguments.StartsWith("diff ", StringComparison.Ordinal))
                    return DiffOutput;
                throw new InvalidOperationException(
                    "unexpected git call: " + arguments);
            }
        }

        const string HeadCommit = "1111111111111111111111111111111111111111";
        const string ToolCommit = "2222222222222222222222222222222222222222";

        [Test]
        public void ToolCommitIsTheLastToolPathCommitNotTheCaptureHead()
        {
            var git = new GitStub { LogOutput = ToolCommit + "\n" };
            Scene006CandidateProbe.ToolCommitBinding binding =
                Scene006CandidateProbe.ResolveToolCommit(
                    git.Run, HeadCommit);

            Assert.AreEqual(ToolCommit, binding.ToolCommit);
            Assert.AreNotEqual(
                HeadCommit,
                binding.ToolCommit,
                "tool_commit must not be stamped as the capture HEAD");
            Assert.IsTrue(binding.ZeroDiffVerified);
            CollectionAssert.AreEqual(
                Scene006CandidateProbe.FrozenToolPaths, binding.FrozenPaths);

            // Derivation is restricted to the frozen path set along the
            // capture history, and the zero-diff proof spans tool..capture.
            Assert.AreEqual(2, git.Calls.Count);
            StringAssert.Contains("log -1 --format=%H", git.Calls[0]);
            StringAssert.Contains(HeadCommit + " --", git.Calls[0]);
            StringAssert.Contains("diff --name-only", git.Calls[1]);
            StringAssert.Contains(
                ToolCommit + ".." + HeadCommit, git.Calls[1]);
            foreach (string path in Scene006CandidateProbe.FrozenToolPaths)
            {
                StringAssert.Contains(path, git.Calls[0]);
                StringAssert.Contains(path, git.Calls[1]);
            }
        }

        [Test]
        public void ToolCommitEqualToCaptureNeedsNoZeroDiffProof()
        {
            var git = new GitStub { LogOutput = HeadCommit };
            Scene006CandidateProbe.ToolCommitBinding binding =
                Scene006CandidateProbe.ResolveToolCommit(
                    git.Run, HeadCommit);

            Assert.AreEqual(HeadCommit, binding.ToolCommit);
            Assert.IsTrue(binding.ZeroDiffVerified);
            Assert.AreEqual(1, git.Calls.Count);
        }

        [Test]
        public void ToolCommitFailsClosedOnFrozenToolPathDrift()
        {
            var git = new GitStub
            {
                LogOutput = ToolCommit,
                DiffOutput = "tools/run_scene006_probe.py\n",
            };
            Assert.Throws<InvalidOperationException>(
                () => Scene006CandidateProbe.ResolveToolCommit(
                    git.Run, HeadCommit));
        }

        [Test]
        public void ToolCommitFailsClosedOnUnusableGitOutput()
        {
            string[] outputs =
            {
                string.Empty,
                "\n",
                ToolCommit.Substring(1),
                "gggggggggggggggggggggggggggggggggggggggg",
                ToolCommit + "\n" + HeadCommit,
            };
            foreach (string output in outputs)
            {
                var git = new GitStub { LogOutput = output };
                Assert.Throws<InvalidOperationException>(
                    () => Scene006CandidateProbe.ResolveToolCommit(
                        git.Run, HeadCommit),
                    "tool_commit must fail closed on: '" + output + "'");
            }

            var clean = new GitStub { LogOutput = ToolCommit };
            Assert.Throws<InvalidOperationException>(
                () => Scene006CandidateProbe.ResolveToolCommit(
                    clean.Run, "HEAD"),
                "a non-commit capture id must fail closed");
        }

        /// <summary>
        /// The stub tests above pin the semantics; this one pins the
        /// plumbing. The nine frozen pathspecs travel to git inside a single
        /// argument string, so a splitting change (or a path with a space)
        /// would hand git one joined pathspec that matches nothing — git
        /// then prints no commit and the derivation must fail closed rather
        /// than produce an identity. Running it against the real repository
        /// is the only way to observe that end of the contract.
        /// </summary>
        [Test]
        public void ResolveToolCommitDerivesTheToolCommitFromTheRealRepository()
        {
            string head = Scene006CandidateProbe.RunGit("rev-parse HEAD");
            Scene006CandidateProbe.ToolCommitBinding binding =
                Scene006CandidateProbe.ResolveToolCommit(head);

            string pathspec = string.Join(
                " ", Scene006CandidateProbe.FrozenToolPaths);
            Assert.AreEqual(40, binding.ToolCommit.Length);
            StringAssert.IsMatch("^[0-9a-f]{40}$", binding.ToolCommit);
            Assert.IsTrue(binding.ZeroDiffVerified);

            // §5.6's definition, re-checked through different plumbing than
            // the derivation used: the commit itself changes frozen tool
            // paths, and no commit after it does.
            Assert.AreNotEqual(
                string.Empty,
                Scene006CandidateProbe.RunGit(
                    "show --pretty=format: --name-only "
                    + binding.ToolCommit + " -- " + pathspec),
                "the derived tool_commit must itself change frozen paths");
            Assert.AreEqual(
                string.Empty,
                Scene006CandidateProbe.RunGit(
                    "log --format=%H " + binding.ToolCommit + ".." + head
                    + " -- " + pathspec),
                "no later commit may change frozen paths");
            Assert.AreEqual(
                string.Empty,
                Scene006CandidateProbe.RunGit(
                    "diff --name-only " + binding.ToolCommit + ".." + head
                    + " -- " + pathspec));
        }

        [Test]
        public void FrozenToolPathsMatchTheBatch1bStopRecord()
        {
            string[] expected =
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
            CollectionAssert.AreEquivalent(
                expected, Scene006CandidateProbe.FrozenToolPaths);
        }
    }
}
