using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class RoadSceneDataTests
    {
        string tempDirectory;

        [SetUp]
        public void SetUp()
        {
            tempDirectory = Path.Combine(
                Path.GetTempPath(),
                "p1-scene-002-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tempDirectory);
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(tempDirectory))
                Directory.Delete(tempDirectory, true);
        }

        [Test]
        public void LoaderFailsClosedForMissingFileAndHashMismatch()
        {
            string missing = Path.Combine(tempDirectory, "missing.json");
            Assert.Throws<FileNotFoundException>(() =>
                RoadSceneDataLoader.LoadVerified(new string('0', 64), missing));

            string path = Write(ValidData());
            Assert.Throws<InvalidOperationException>(() =>
                RoadSceneDataLoader.LoadVerified(new string('0', 64), path));
        }

        [Test]
        public void LoaderFailsClosedForUnknownSchemaAndDuplicateSurface()
        {
            RoadSceneData unknownSchema = ValidData();
            unknownSchema.schema_version = "p1-scene-road-data/v999";
            AssertInvalidAfterVerifiedLoad(unknownSchema, "schema");

            RoadSceneData duplicate = ValidData();
            duplicate.surfaces = new[]
            {
                duplicate.surfaces[0],
                duplicate.surfaces[0],
            };
            AssertInvalidAfterVerifiedLoad(duplicate, "duplicate");
        }

        [Test]
        public void LoaderFailsClosedForUnknownClassification()
        {
            RoadSceneData data = ValidData();
            data.obstacle_footprints[0].classification = "mystery";

            AssertInvalidAfterVerifiedLoad(data, "classification");
        }

        [Test]
        public void AuditFailsClosedWhenActiveRendererRootHasNoFootprint()
        {
            GameObject root = GameObject.CreatePrimitive(PrimitiveType.Cube);
            root.name = "UnknownProp";
            try
            {
                InvalidOperationException exception =
                    Assert.Throws<InvalidOperationException>(() =>
                        RoadSceneAuditor.Audit(
                            "missing-footprint",
                            Route(),
                            Corridor(),
                            ValidData(),
                            new[] { root.transform }));

                StringAssert.Contains("no classification/footprint", exception.Message);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void CheckedInConfigsPinExactRoadDataBytes()
        {
            byte[] bytes = File.ReadAllBytes(RoadSceneDataLoader.ProjectPath);
            string actual = RoadSceneDataLoader.Sha256(bytes);
            string[] names =
            {
                "scenario.default.json",
                "scenario.rate-study-5hz.json",
                "scenario.rate-study-20hz.json",
                "scenario.scene-validation.json",
            };

            foreach (string name in names)
            {
                ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                    File.ReadAllText(RuntimePaths.ProjectFile("config", name)));
                Assert.That(config.road_data_sha256, Is.EqualTo(actual), name);
                Assert.DoesNotThrow(() =>
                    RoadSceneDataLoader.LoadVerified(config.road_data_sha256));
            }
        }

        [Test]
        public void CheckedInLegacyRouteFailsAndRedrawnRouteIsRoadLegal()
        {
            ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(
                    RuntimePaths.ProjectFile("config", "scenario.default.json")));
            RoadSceneData data =
                RoadSceneDataLoader.LoadVerified(config.road_data_sha256);
            Vector3[] legacyRoute =
            {
                new Vector3(132f, 0.2f, 117f),
                new Vector3(180f, 0.2f, 117f),
                new Vector3(183f, 0.2f, 114f),
                new Vector3(183f, 0.2f, 66f),
                new Vector3(180f, 0.2f, 63f),
                new Vector3(132f, 0.2f, 63f),
                new Vector3(129f, 0.2f, 66f),
                new Vector3(129f, 0.2f, 114f),
            };

            RoadSceneAuditReport before = RoadSceneAuditor.Audit(
                "legacy",
                legacyRoute,
                config.scene_adjustments.route_corridor,
                data,
                Array.Empty<Transform>());
            RoadSceneAuditReport after = RoadSceneAuditor.Audit(
                "redrawn",
                config.TargetRoute(),
                config.scene_adjustments.route_corridor,
                data,
                Array.Empty<Transform>());

            Assert.That(before.road_violation_count, Is.GreaterThan(0));
            Assert.That(after.road_violation_count, Is.Zero);
            Assert.That(after.status, Is.EqualTo("CLEAR"));
        }

        [Test]
        public void PresentAdjustmentsRequireEveryNewAuditField()
        {
            string json = File.ReadAllText(
                RuntimePaths.ProjectFile("config", "scenario.default.json"));
            json = json.Replace(
                "      \"target_height_m\": 1.55,\n",
                string.Empty);

            InvalidOperationException exception =
                Assert.Throws<InvalidOperationException>(() =>
                    ScenarioConfig.FromJsonStrict(json));

            StringAssert.Contains("target_height_m", exception.Message);
        }

        static RoadSceneData ValidData()
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.01f,
                road_surface_allowlist = new[] { "Road Lane" },
                surfaces = new[]
                {
                    new RoadSurfacePatch
                    {
                        id = "road-0",
                        canonical_name = "Road Lane",
                        center_x_m = 5f,
                        center_z_m = 0f,
                        half_extent_x_m = 10f,
                        half_extent_z_m = 5f,
                        surface_y_m = 0f,
                    },
                },
                obstacle_footprints = new[]
                {
                    Footprint("KnownProp", "ground-obstacle"),
                },
            };
        }

        internal static RoadObstacleFootprint Footprint(
            string name,
            string classification,
            string group = "prop")
        {
            return new RoadObstacleFootprint
            {
                canonical_name = name,
                classification = classification,
                group = group,
                full_min_x_m = -0.5f,
                full_max_x_m = 0.5f,
                full_min_y_m = 0f,
                full_max_y_m = 1f,
                full_min_z_m = -0.5f,
                full_max_z_m = 0.5f,
                ground_min_x_m = -0.5f,
                ground_max_x_m = 0.5f,
                ground_min_z_m = -0.5f,
                ground_max_z_m = 0.5f,
                overhead_min_y_m = 0f,
            };
        }

        internal static RouteCorridorScenarioConfig Corridor()
        {
            return new RouteCorridorScenarioConfig
            {
                target_half_width_m = 1f,
                clearance_margin_m = 0.5f,
                target_bottom_offset_m = 0f,
                target_height_m = 1.55f,
                vertical_clearance_margin_m = 0.5f,
                road_sample_spacing_m = 0.5f,
                jump_epsilon_m = 0.001f,
            };
        }

        internal static Vector3[] Route()
        {
            return new[]
            {
                new Vector3(0f, 0f, 0f),
                new Vector3(10f, 0f, 0f),
            };
        }

        string Write(RoadSceneData data)
        {
            string path = Path.Combine(tempDirectory, "road_data.json");
            File.WriteAllText(path, JsonUtility.ToJson(data, true) + "\n");
            return path;
        }

        void AssertInvalidAfterVerifiedLoad(
            RoadSceneData data,
            string expectedMessage)
        {
            string path = Write(data);
            string hash = RoadSceneDataLoader.Sha256(File.ReadAllBytes(path));
            InvalidOperationException exception =
                Assert.Throws<InvalidOperationException>(() =>
                    RoadSceneDataLoader.LoadVerified(hash, path));
            StringAssert.Contains(expectedMessage, exception.Message.ToLowerInvariant());
        }
    }

    public sealed class RoadObstacleAuditTests
    {
        [Test]
        public void GroundPropBlocksCorridor()
        {
            GameObject root = Root("GroundProp", new Vector3(5f, 0f, 0f));
            try
            {
                bool blocked = RoadSceneAuditor.AuditObstacle(
                    RoadSceneDataTests.Route(),
                    RoadSceneDataTests.Corridor(),
                    Data(RoadSceneDataTests.Footprint(
                        "GroundProp",
                        "ground-obstacle")),
                    root.transform,
                    RoadSceneDataTests.Footprint(
                        "GroundProp",
                        "ground-obstacle"),
                    out SceneObstacleViolation violation,
                    out bool overheadExempt);

                Assert.That(blocked, Is.True);
                Assert.That(violation.group, Is.EqualTo("prop"));
                Assert.That(overheadExempt, Is.False);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void OverheadSignalWithClearGroundFootprintIsExempt()
        {
            GameObject root = Root("Signal", new Vector3(5f, 0f, 0f));
            RoadObstacleFootprint footprint =
                RoadSceneDataTests.Footprint("Signal", "overhead");
            footprint.full_min_y_m = 3f;
            footprint.full_max_y_m = 4f;
            footprint.overhead_min_y_m = 3f;
            footprint.ground_min_z_m = 4f;
            footprint.ground_max_z_m = 5f;
            try
            {
                bool blocked = RoadSceneAuditor.AuditObstacle(
                    RoadSceneDataTests.Route(),
                    RoadSceneDataTests.Corridor(),
                    Data(footprint),
                    root.transform,
                    footprint,
                    out SceneObstacleViolation violation,
                    out bool overheadExempt);

                Assert.That(blocked, Is.False);
                Assert.That(violation, Is.Null);
                Assert.That(overheadExempt, Is.True);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void RoadSurfaceRootsAreExcludedFromObstacleCounts()
        {
            GameObject road = Root("Road Lane", Vector3.zero);
            try
            {
                RoadSceneAuditReport report = RoadSceneAuditor.Audit(
                    "road-exemption",
                    RoadSceneDataTests.Route(),
                    RoadSceneDataTests.Corridor(),
                    Data(RoadSceneDataTests.Footprint(
                        "KnownProp",
                        "ground-obstacle")),
                    new[] { road.transform });

                Assert.That(report.audited_obstacle_count, Is.Zero);
                Assert.That(report.obstacle_violation_count, Is.Zero);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(road);
            }
        }

        [Test]
        public void NonUniformScaleUsesTransformedFootprint()
        {
            GameObject root = Root("ScaledProp", new Vector3(5f, 0f, 2f));
            root.transform.localScale = new Vector3(1f, 1f, 2f);
            RoadObstacleFootprint footprint =
                RoadSceneDataTests.Footprint("ScaledProp", "ground-obstacle");
            try
            {
                bool blocked = RoadSceneAuditor.AuditObstacle(
                    RoadSceneDataTests.Route(),
                    RoadSceneDataTests.Corridor(),
                    Data(footprint),
                    root.transform,
                    footprint,
                    out SceneObstacleViolation violation,
                    out _);

                Assert.That(blocked, Is.True);
                Assert.That(
                    violation.required_centerline_distance_m,
                    Is.EqualTo(2.5f).Within(1e-5f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void UnsupportedPitchRollFailsClosedInsteadOfApproximating()
        {
            GameObject root = Root("TiltedProp", new Vector3(5f, 0f, 2f));
            root.transform.rotation = Quaternion.Euler(5f, 0f, 0f);
            RoadObstacleFootprint footprint =
                RoadSceneDataTests.Footprint("TiltedProp", "ground-obstacle");
            try
            {
                InvalidOperationException exception =
                    Assert.Throws<InvalidOperationException>(() =>
                        RoadSceneAuditor.AuditObstacle(
                            RoadSceneDataTests.Route(),
                            RoadSceneDataTests.Corridor(),
                            Data(footprint),
                            root.transform,
                            footprint,
                            out _,
                            out _));

                StringAssert.Contains("pitch/roll", exception.Message);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
            }
        }

        static GameObject Root(string name, Vector3 position)
        {
            var root = new GameObject(name);
            root.transform.position = position;
            return root;
        }

        static RoadSceneData Data(RoadObstacleFootprint footprint)
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.01f,
                road_surface_allowlist = new[] { "Road Lane" },
                surfaces = new[]
                {
                    new RoadSurfacePatch
                    {
                        id = "road-0",
                        canonical_name = "Road Lane",
                        center_x_m = 5f,
                        center_z_m = 0f,
                        half_extent_x_m = 10f,
                        half_extent_z_m = 5f,
                        surface_y_m = 0f,
                    },
                },
                obstacle_footprints = new[] { footprint },
            };
        }
    }

    public sealed class P1Scene003AnchorAuditTests
    {
        const string CityScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        [Test]
        public void CheckedInContractFreezesAcceptedSearchAndClearanceParameters()
        {
            P1Scene003AnchorPlacementContract contract =
                P1Scene003AnchorPlacementContractLoader.Load(out string hash);

            Assert.That(RateStudyProtocol.IsSha256(hash), Is.True);
            Assert.That(
                contract.RequestedAnchor,
                Is.EqualTo(new Vector3(150f, 0.2f, 90f)));
            Assert.That(contract.hover_offset_y_m, Is.EqualTo(25f));
            Assert.That(contract.support_height_tolerance_m, Is.EqualTo(0.05f));
            Assert.That(contract.AnchorEffectiveRadius, Is.EqualTo(1.5f));
            Assert.That(contract.HoverEffectiveRadius, Is.EqualTo(1.5f));
            Assert.That(contract.CorridorEffectiveRadius, Is.EqualTo(1f));
            Assert.That(contract.lattice_step_m, Is.EqualTo(0.5f));
            Assert.That(contract.lattice_radius_m, Is.EqualTo(10f));
            Assert.That(
                contract.support_surface_allowlist,
                Is.EqualTo(new[]
                {
                    "Natures_Grass Tile",
                    "Natures_Grass Tile Small",
                }));
        }

        [Test]
        public void ExactRequestedAnchorWinsWhenSupportAndClearanceAreValid()
        {
            P1Scene003AnchorPlacementContract contract =
                Contract(new Vector3(0f, 0.2f, 0f));
            ScenarioConfig scenario = Scenario(contract.RequestedAnchor);
            RoadSceneData data = SupportData(0.2f);

            P1Scene003AnchorAuditReport report =
                P1Scene003AnchorAuditor.Audit(
                    scenario,
                    new string('a', 64),
                    data,
                    Array.Empty<Transform>(),
                    contract,
                    new string('b', 64));

            Assert.That(report.status, Is.EqualTo("CLEAR"));
            Assert.That(report.candidate_count, Is.EqualTo(1257));
            Assert.That(report.legal_candidate_count, Is.GreaterThan(0));
            Assert.That(
                report.selected_anchor_world_m.Value,
                Is.EqualTo(contract.RequestedAnchor));
            Assert.That(report.candidates[0].rank, Is.Zero);
            Assert.That(report.candidates[0].support_status, Is.EqualTo("PASS"));
            Assert.That(report.candidates[0].clearance_status, Is.EqualTo("PASS"));
        }

        [Test]
        public void SupportBoundaryAndHeightMismatchFailBeforeClearance()
        {
            P1Scene003AnchorPlacementContract contract =
                Contract(new Vector3(0f, 0.2f, 0f));
            contract.lattice_radius_m = 0.1f;
            ScenarioConfig scenario = Scenario(contract.RequestedAnchor);
            RoadSceneData boundary = SupportData(0.2f);
            boundary.surfaces[0].center_x_m = -20f;
            RoadSceneData wrongHeight = SupportData(0f);

            P1Scene003AnchorAuditReport boundaryReport =
                P1Scene003AnchorAuditor.Audit(
                    scenario,
                    new string('a', 64),
                    boundary,
                    Array.Empty<Transform>(),
                    contract,
                    new string('b', 64));
            P1Scene003AnchorAuditReport heightReport =
                P1Scene003AnchorAuditor.Audit(
                    scenario,
                    new string('a', 64),
                    wrongHeight,
                    Array.Empty<Transform>(),
                    contract,
                    new string('b', 64));

            Assert.That(
                boundaryReport.candidates[0].rejection_reason,
                Is.EqualTo("SUPPORT_NOT_FOUND"));
            Assert.That(
                heightReport.candidates[0].rejection_reason,
                Is.EqualTo("SUPPORT_HEIGHT_MISMATCH"));
            Assert.That(
                heightReport.candidates[0].clearance_status,
                Is.EqualTo("NOT_EVALUATED"));
        }

        [Test]
        public void TangentObstacleRejectsCandidateAndFallbackIsDeterministic()
        {
            P1Scene003AnchorPlacementContract contract =
                Contract(new Vector3(0f, 0.2f, 0f));
            ScenarioConfig scenario = Scenario(contract.RequestedAnchor);
            RoadObstacleFootprint footprint =
                RoadSceneDataTests.Footprint("Blocker", "ground-obstacle");
            footprint.full_min_x_m = -0.1f;
            footprint.full_max_x_m = 0.1f;
            footprint.full_min_z_m = -0.1f;
            footprint.full_max_z_m = 0.1f;
            RoadSceneData data = SupportData(0.2f, footprint);
            GameObject blocker = new GameObject("Blocker");
            blocker.transform.position = new Vector3(1.6f, 0.2f, 0f);
            try
            {
                P1Scene003AnchorAuditReport report =
                    P1Scene003AnchorAuditor.Audit(
                        scenario,
                        new string('a', 64),
                        data,
                        new[] { blocker.transform },
                        contract,
                        new string('b', 64));

                Assert.That(
                    report.candidates[0].rejection_reason,
                    Is.EqualTo("CLEARANCE_INTERSECTION"));
                Assert.That(report.status, Is.EqualTo("CLEAR"));
                Assert.That(report.selected_anchor_world_m, Is.Not.Null);
                Assert.That(
                    report.selected_anchor_world_m.Value,
                    Is.Not.EqualTo(contract.RequestedAnchor));
                P1Scene003AnchorCandidateAudit selected =
                    report.candidates.First(item => item.rejection_reason == null);
                Assert.That(
                    report.selected_anchor_world_m.Value,
                    Is.EqualTo(new Vector3(
                        selected.x_m,
                        selected.y_m,
                        selected.z_m)));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(blocker);
            }
        }

        [Test]
        public void ConflictingSupportsAndUnsupportedObstacleTrsFailClosed()
        {
            P1Scene003AnchorPlacementContract contract =
                Contract(new Vector3(0f, 0.2f, 0f));
            contract.lattice_radius_m = 0.1f;
            ScenarioConfig scenario = Scenario(contract.RequestedAnchor);
            RoadSceneData conflicting = SupportData(0.2f);
            RoadSurfacePatch second = new RoadSurfacePatch
            {
                id = "support-other-height",
                canonical_name = "Road Support",
                center_x_m = 0f,
                center_z_m = 0f,
                yaw_deg = 0f,
                half_extent_x_m = 20f,
                half_extent_z_m = 20f,
                surface_y_m = 0.3f,
            };
            conflicting.surfaces = new[] { conflicting.surfaces[0], second };

            P1Scene003AnchorAuditReport conflictReport =
                P1Scene003AnchorAuditor.Audit(
                    scenario,
                    new string('a', 64),
                    conflicting,
                    Array.Empty<Transform>(),
                    contract,
                    new string('b', 64));
            Assert.That(
                conflictReport.candidates[0].rejection_reason,
                Is.EqualTo("SUPPORT_HEIGHT_CONFLICT"));

            RoadObstacleFootprint footprint =
                RoadSceneDataTests.Footprint("Tilted", "ground-obstacle");
            RoadSceneData obstacleData = SupportData(0.2f, footprint);
            GameObject tilted = new GameObject("Tilted");
            tilted.transform.rotation = Quaternion.Euler(5f, 0f, 0f);
            try
            {
                P1Scene003AnchorAuditReport trsReport =
                    P1Scene003AnchorAuditor.Audit(
                        scenario,
                        new string('a', 64),
                        obstacleData,
                        new[] { tilted.transform },
                        contract,
                        new string('b', 64));
                Assert.That(
                    trsReport.candidates[0].rejection_reason,
                    Is.EqualTo("UNSUPPORTED_OBSTACLE_TRS"));
                Assert.That(
                    trsReport.candidates[0].blocking_object,
                    Is.EqualTo("Tilted"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(tilted);
            }
        }

        [Test]
        public void CheckedInCitySceneFailsClosedAtAcceptedSupportGate()
        {
            string scenarioPath = RuntimePaths.ProjectFile(
                "config",
                "scenario.p1-detect-scouting.json");
            byte[] scenarioBytes = File.ReadAllBytes(scenarioPath);
            ScenarioConfig scenario =
                ScenarioConfig.FromJsonStrict(File.ReadAllText(scenarioPath));
            P1Scene003AnchorPlacementContract contract =
                P1Scene003AnchorPlacementContractLoader.Load(
                    out string contractHash);
            try
            {
                EditorSceneManager.OpenScene(CityScenePath, OpenSceneMode.Single);
                RoadSceneData roadData =
                    RoadSceneDataLoader.LoadVerified(scenario.road_data_sha256);
                SceneVehicleAdjustmentApplier.Apply(scenario.scene_adjustments);
                IReadOnlyList<Transform> roots =
                    RoadSceneAuditor.FindStaticRenderableRoots();

                P1Scene003AnchorAuditReport report =
                    P1Scene003AnchorAuditor.Audit(
                        scenario,
                        P1Scene003AnchorPlacementContractLoader.Sha256(
                            scenarioBytes),
                        roadData,
                        roots,
                        contract,
                        contractHash);

                Assert.That(
                    report.status,
                    Is.EqualTo("BLOCKED_ANCHOR_PLACEMENT"));
                Assert.That(report.candidate_count, Is.EqualTo(1257));
                Assert.That(report.legal_candidate_count, Is.Zero);
                Assert.That(report.support_rejection_count, Is.EqualTo(1257));
                Assert.That(report.clearance_rejection_count, Is.Zero);
                Assert.That(
                    report.candidates.All(item =>
                        item.rejection_reason == "SUPPORT_HEIGHT_MISMATCH"),
                    Is.True);
                Assert.That(
                    report.candidates[0].support_ids,
                    Does.Contain("Natures_Grass Tile"));
                Assert.That(
                    report.candidates[0].support_surface_y_m,
                    Is.EqualTo(0f).Within(1e-4f));
                Assert.That(
                    report.candidates[0].clearance_status,
                    Is.EqualTo("NOT_EVALUATED"));
            }
            finally
            {
                EditorSceneManager.OpenScene(CityScenePath, OpenSceneMode.Single);
            }
        }

        static P1Scene003AnchorPlacementContract Contract(Vector3 anchor)
        {
            return new P1Scene003AnchorPlacementContract
            {
                schema_version = P1Scene003AnchorPlacementContract.Schema,
                work_id = P1Scene003AnchorPlacementContract.WorkId,
                requested_anchor_world_m =
                    new ScenarioVector3(anchor.x, anchor.y, anchor.z),
                hover_offset_y_m = 25f,
                support_surface_allowlist = new[] { "Grass" },
                support_height_tolerance_m = 0.05f,
                anchor_nominal_radius_m = 1f,
                hover_nominal_radius_m = 1f,
                corridor_nominal_radius_m = 0.5f,
                clearance_margin_m = 0.5f,
                lattice_step_m = 0.5f,
                lattice_radius_m = 10f,
            };
        }

        static ScenarioConfig Scenario(Vector3 anchor)
        {
            ScenarioConfig scenario = ScenarioConfig.CreateDefault();
            scenario.scenario_id = "anchor-audit-test";
            scenario.road_data_sha256 = new string('c', 64);
            scenario.anchor_world_m =
                new ScenarioVector3(anchor.x, anchor.y, anchor.z);
            return scenario;
        }

        static RoadSceneData SupportData(
            float surfaceY,
            params RoadObstacleFootprint[] footprints)
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.01f,
                road_surface_allowlist = new[] { "Road Support" },
                surfaces = new[]
                {
                    new RoadSurfacePatch
                    {
                        id = "support",
                        canonical_name = "Road Support",
                        center_x_m = 0f,
                        center_z_m = 0f,
                        yaw_deg = 0f,
                        half_extent_x_m = 20f,
                        half_extent_z_m = 20f,
                        surface_y_m = surfaceY,
                    },
                },
                obstacle_footprints = footprints.Length == 0
                    ? new[]
                    {
                        RoadSceneDataTests.Footprint(
                            "Unused",
                            "ground-obstacle"),
                    }
                    : footprints,
            };
        }
    }

    public sealed class PlacementPhaseTests
    {
        [Test]
        public void MeasurementBoundaryRejectsTargetAndScenePlacement()
        {
            GameObject targetObject = new GameObject("Target");
            GameObject vehicle = new GameObject("Vehicle_Taxi (1)");
            var guard = new PlacementPhaseGuard();
            LoopTargetVehicle target =
                targetObject.AddComponent<LoopTargetVehicle>();
            target.Configure(RoadSceneDataTests.Route());
            target.SetPlacementGuard(guard);
            guard.StartMeasurement("first-published-frame");
            try
            {
                Assert.Throws<InvalidOperationException>(() =>
                    target.PlaceAtRouteDistance(1f));
                Assert.Throws<InvalidOperationException>(() =>
                    SceneVehicleAdjustmentApplier.Apply(
                        SceneAdjustmentConfigTests.Adjustments(),
                        new[] { vehicle.transform },
                        guard));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(targetObject);
                UnityEngine.Object.DestroyImmediate(vehicle);
            }
        }

        [Test]
        public void ConfigurePlacesTargetBeforeItsFirstMotionStep()
        {
            GameObject targetObject = new GameObject("Target");
            LoopTargetVehicle target =
                targetObject.AddComponent<LoopTargetVehicle>();
            Vector3[] route = RoadSceneDataTests.Route();
            try
            {
                target.Configure("target-0", route, 2f);
                Assert.That(target.transform.position, Is.EqualTo(route[0]));

                target.Step(0.25f);

                Assert.That(
                    target.transform.position,
                    Is.EqualTo(new Vector3(0.5f, 0f, 0f)));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(targetObject);
            }
        }

        [Test]
        public void JumpDiagnosticUsesSpecifiedThresholdAndIndependentArtifact()
        {
            string directory = Path.Combine(
                Path.GetTempPath(),
                "p1-scene-jumps-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "jumps.json");
            GameObject actor = new GameObject("Actor");
            GameObject diagnosticObject = new GameObject("Diagnostic");
            PlacementJumpDiagnostic diagnostic =
                diagnosticObject.AddComponent<PlacementJumpDiagnostic>();
            try
            {
                Assert.That(
                    PlacementJumpDiagnostic.AllowedDisplacement(2f, 0.1f, 0.01f),
                    Is.EqualTo(0.41f).Within(1e-6f));
                diagnostic.Configure(
                    "diagnostic",
                    new[] { actor.transform },
                    new[] { 2f },
                    0.01f,
                    path);
                actor.transform.position = new Vector3(0.4f, 0f, 0f);
                diagnostic.Sample(0.1f, 1);
                actor.transform.position = new Vector3(1f, 0f, 0f);
                diagnostic.Sample(0.1f, 2);

                string json = File.ReadAllText(path);
                StringAssert.Contains("\"jump_count\": 1", json);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(diagnosticObject);
                UnityEngine.Object.DestroyImmediate(actor);
                if (Directory.Exists(directory))
                    Directory.Delete(directory, true);
            }
        }

        [Test]
        public void ProductionConfigsDisableDiagnosticsAndValidationEnablesThem()
        {
            foreach (string name in new[]
            {
                "scenario.default.json",
                "scenario.rate-study-5hz.json",
                "scenario.rate-study-20hz.json",
            })
            {
                ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                    File.ReadAllText(RuntimePaths.ProjectFile("config", name)));
                Assert.That(
                    config.scene_adjustments.route_corridor
                        .enable_dynamic_intersection_audit,
                    Is.False,
                    name);
                Assert.That(
                    config.scene_adjustments.route_corridor.enable_jump_diagnostic,
                    Is.False,
                    name);
            }

            ScenarioConfig validation = ScenarioConfig.FromJsonStrict(
                File.ReadAllText(RuntimePaths.ProjectFile(
                    "config",
                    "scenario.scene-validation.json")));
            Assert.That(
                validation.scene_adjustments.route_corridor
                    .enable_dynamic_intersection_audit,
                Is.True);
            Assert.That(
                validation.scene_adjustments.route_corridor.enable_jump_diagnostic,
                Is.True);
        }
    }

    public sealed class RouteCorridorDynamicMonitorTests
    {
        const string CityScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        [Test]
        public void ExcludesRoadAndUsesGroundAndOverheadFootprints()
        {
            string directory = Path.Combine(
                Path.GetTempPath(),
                "p1-scene-dynamic-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "dynamic.json");
            GameObject targetObject = new GameObject("Target");
            GameObject targetVisual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            targetVisual.transform.SetParent(targetObject.transform, false);
            targetVisual.transform.localScale = new Vector3(2f, 1.55f, 4f);
            targetVisual.transform.localPosition = new Vector3(0f, 0.775f, 0f);
            LoopTargetVehicle target =
                targetObject.AddComponent<LoopTargetVehicle>();
            target.Configure(new[] { Vector3.zero, new Vector3(10f, 0f, 0f) });

            GameObject road = GameObject.CreatePrimitive(PrimitiveType.Cube);
            road.name = "Road Lane";
            road.transform.position = Vector3.zero;
            road.transform.localScale = new Vector3(20f, 0.2f, 20f);

            GameObject signal = new GameObject("Signal");
            GameObject signalVisual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            signalVisual.transform.SetParent(signal.transform, false);
            signalVisual.transform.localScale = new Vector3(6f, 4f, 0.5f);
            signalVisual.transform.localPosition = new Vector3(0f, 2f, 0f);

            GameObject blocker = GameObject.CreatePrimitive(PrimitiveType.Cube);
            blocker.name = "Blocker";
            blocker.transform.position = new Vector3(8f, 0.5f, 0f);

            GameObject monitorObject = new GameObject("Monitor");
            RouteCorridorDynamicMonitor monitor =
                monitorObject.AddComponent<RouteCorridorDynamicMonitor>();
            RoadObstacleFootprint signalFootprint =
                RoadSceneDataTests.Footprint("Signal", "ground-obstacle");
            signalFootprint.full_min_x_m = -3f;
            signalFootprint.full_max_x_m = 3f;
            signalFootprint.full_min_y_m = 0f;
            signalFootprint.full_max_y_m = 4f;
            signalFootprint.ground_min_x_m = 2.5f;
            signalFootprint.ground_max_x_m = 3f;
            signalFootprint.overhead_min_y_m = 3f;
            RoadSceneData data = Data(
                signalFootprint,
                RoadSceneDataTests.Footprint("Blocker", "ground-obstacle"));
            try
            {
                monitor.Configure(
                    "dynamic-footprints",
                    target,
                    data,
                    new[] { road.transform, signal.transform, blocker.transform },
                    path);

                monitor.Sample();

                Assert.That(monitor.CheckedFrames, Is.EqualTo(1));
                Assert.That(monitor.IntersectionFrames, Is.Zero);
                Assert.That(monitor.IntersectingNames, Is.Empty);

                blocker.transform.position = new Vector3(0f, 0.5f, 0f);
                monitor.Sample();

                Assert.That(monitor.CheckedFrames, Is.EqualTo(2));
                Assert.That(monitor.IntersectionFrames, Is.EqualTo(1));
                Assert.That(
                    monitor.IntersectingNames,
                    Is.EqualTo(new[] { "Blocker" }));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(monitorObject);
                UnityEngine.Object.DestroyImmediate(blocker);
                UnityEngine.Object.DestroyImmediate(signal);
                UnityEngine.Object.DestroyImmediate(road);
                UnityEngine.Object.DestroyImmediate(targetObject);
                if (Directory.Exists(directory))
                    Directory.Delete(directory, true);
            }
        }

        [Test]
        public void ConfigureFailsClosedForUnknownActiveRenderableRoot()
        {
            string path = Path.Combine(
                Path.GetTempPath(),
                "p1-scene-dynamic-" + Guid.NewGuid().ToString("N") + ".json");
            GameObject targetObject = new GameObject("Target");
            targetObject.AddComponent<MeshRenderer>();
            LoopTargetVehicle target =
                targetObject.AddComponent<LoopTargetVehicle>();
            target.Configure(new[] { Vector3.zero, new Vector3(10f, 0f, 0f) });
            GameObject unknown = new GameObject("Unknown");
            GameObject monitorObject = new GameObject("Monitor");
            RouteCorridorDynamicMonitor monitor =
                monitorObject.AddComponent<RouteCorridorDynamicMonitor>();
            try
            {
                InvalidOperationException exception =
                    Assert.Throws<InvalidOperationException>(() =>
                        monitor.Configure(
                            "dynamic-unknown",
                            target,
                            Data(RoadSceneDataTests.Footprint(
                                "Known",
                                "ground-obstacle")),
                            new[] { unknown.transform },
                            path));

                StringAssert.Contains(
                    "no classification/footprint",
                    exception.Message);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(monitorObject);
                UnityEngine.Object.DestroyImmediate(unknown);
                UnityEngine.Object.DestroyImmediate(targetObject);
                if (File.Exists(path)) File.Delete(path);
            }
        }

        [Test]
        public void CheckedInCitySceneStaysClearAcrossFullDynamicLoop()
        {
            string directory = Path.Combine(
                Path.GetTempPath(),
                "p1-scene-dynamic-real-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            string path = Path.Combine(directory, "dynamic.json");
            GameObject targetObject = null;
            GameObject monitorObject = null;
            try
            {
                EditorSceneManager.OpenScene(
                    CityScenePath,
                    OpenSceneMode.Single);
                ScenarioConfig config = ScenarioConfig.FromJsonStrict(
                    File.ReadAllText(RuntimePaths.ProjectFile(
                        "config",
                        "scenario.scene-validation.json")));
                RoadSceneData roadData =
                    RoadSceneDataLoader.LoadVerified(config.road_data_sha256);
                SceneVehicleAdjustmentApplier.Apply(config.scene_adjustments);

                targetObject = new GameObject("TargetVehicle_Red");
                AddTargetVisual(targetObject.transform);
                LoopTargetVehicle target =
                    targetObject.AddComponent<LoopTargetVehicle>();
                Vector3[] route = config.TargetRoute();
                target.Configure(
                    config.target.track_id,
                    route,
                    config.target.speed_mps);
                target.SetMotionEnabled(false);

                IReadOnlyList<Transform> roots =
                    RoadSceneAuditor.FindStaticRenderableRoots(
                        new[] { target.transform });
                monitorObject = new GameObject("Monitor");
                RouteCorridorDynamicMonitor monitor =
                    monitorObject.AddComponent<RouteCorridorDynamicMonitor>();
                monitor.Configure(
                    config.scenario_id,
                    target,
                    roadData,
                    roots,
                    path);

                float perimeter = RateStudyScouting.ClosedRoutePerimeter(route);
                const float spacing = 0.1f;
                int sampleCount = Mathf.CeilToInt(perimeter / spacing);
                for (int index = 0; index < sampleCount; index++)
                {
                    target.PlaceAtRouteDistance(
                        Mathf.Min(index * spacing, perimeter - 1e-4f));
                    monitor.Sample();
                }

                Assert.That(monitor.MonitoredObstacleCount, Is.EqualTo(779));
                Assert.That(monitor.CheckedFrames, Is.EqualTo(sampleCount));
                Assert.That(monitor.IntersectionFrames, Is.Zero);
                Assert.That(monitor.IntersectingNames, Is.Empty);
            }
            finally
            {
                if (monitorObject != null)
                    UnityEngine.Object.DestroyImmediate(monitorObject);
                if (targetObject != null)
                    UnityEngine.Object.DestroyImmediate(targetObject);
                EditorSceneManager.OpenScene(
                    CityScenePath,
                    OpenSceneMode.Single);
                if (Directory.Exists(directory))
                    Directory.Delete(directory, true);
            }
        }

        static RoadSceneData Data(params RoadObstacleFootprint[] footprints)
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.01f,
                road_surface_allowlist = new[] { "Road Lane" },
                surfaces = new[]
                {
                    new RoadSurfacePatch
                    {
                        id = "road-0",
                        canonical_name = "Road Lane",
                        center_x_m = 5f,
                        center_z_m = 0f,
                        half_extent_x_m = 10f,
                        half_extent_z_m = 5f,
                        surface_y_m = 0f,
                    },
                },
                obstacle_footprints = footprints,
            };
        }

        static void AddTargetVisual(Transform parent)
        {
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.transform.SetParent(parent);
            body.transform.localPosition = new Vector3(0f, 0.5f, 0f);
            body.transform.localScale = new Vector3(2f, 1f, 4f);
            GameObject roof = GameObject.CreatePrimitive(PrimitiveType.Cube);
            roof.transform.SetParent(parent);
            roof.transform.localPosition = new Vector3(0f, 1.2f, -0.2f);
            roof.transform.localScale = new Vector3(1.7f, 0.7f, 2f);
        }
    }
}
