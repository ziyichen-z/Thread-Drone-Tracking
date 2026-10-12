using System.Linq;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-M3-BODY-001 batch 1a-alpha hard gate 1. These tests pin the gate's
    /// behaviour on synthetic geometry; the verdict on the real scene comes
    /// from the Editor query and is checked again, independently, by
    /// `tools/check_anchor_placement.py`.
    /// </summary>
    public sealed class P1M3BodyAnchorAuditTests
    {
        const string GrassName = "Natures_Grass Tile";
        const string ObstacleName = "Props_Street Light";
        const float GrassHalfExtent = 10f;

        [Test]
        public void CheckedInContractFreezesTheMainLoopAnchorAndPriorSafetyValues()
        {
            P1M3BodyAnchorPlacementContract contract =
                P1M3BodyAnchorPlacementContractLoader.Load(out string hash);

            Assert.That(RateStudyProtocol.IsSha256(hash), Is.True);
            // The anchor under audit is the frozen main-loop anchor; the
            // accepted proposal section 5.1 forbids moving it.
            Assert.That(
                contract.AuditedAnchor,
                Is.EqualTo(new Vector3(132f, 0.2f, 117f)));
            // Every safety value is byte-identical to the two prior accepted
            // anchor contracts, so this batch proposes no new safety value
            // (BC-BODY1-10 requests no user authorization).
            Assert.That(contract.hover_offset_y_m, Is.EqualTo(25f));
            Assert.That(contract.support_height_tolerance_m, Is.EqualTo(0.05f));
            Assert.That(contract.anchor_nominal_radius_m, Is.EqualTo(1f));
            Assert.That(contract.hover_nominal_radius_m, Is.EqualTo(1f));
            Assert.That(contract.corridor_nominal_radius_m, Is.EqualTo(0.5f));
            Assert.That(contract.clearance_margin_m, Is.EqualTo(0.5f));
            Assert.That(contract.AnchorEffectiveRadius, Is.EqualTo(1.5f));
            Assert.That(contract.HoverEffectiveRadius, Is.EqualTo(1.5f));
            // Matches the proposal section 3.5 pre-registration 0.5 + 0.5.
            Assert.That(contract.CorridorEffectiveRadius, Is.EqualTo(1f));
            Assert.That(
                contract.support_surface_allowlist,
                Is.EqualTo(new[]
                {
                    "Natures_Grass Tile",
                    "Natures_Grass Tile Small",
                }));
        }

        [Test]
        public void CheckedInContractAuditsTheAnchorTheFrozenScenarioRuns()
        {
            P1M3BodyAnchorPlacementContract contract =
                P1M3BodyAnchorPlacementContractLoader.Load(out _);
            ScenarioConfig scenario = ScenarioConfig.FromJsonStrict(
                System.IO.File.ReadAllText(
                    RuntimePaths.ProjectFile("config", "scenario.default.json")));

            Assert.That(scenario.Anchor, Is.EqualTo(contract.AuditedAnchor));
        }

        [Test]
        public void AnchorThatDisagreesWithTheScenarioIsRejectedOutright()
        {
            // A contract that drifted from the scenario bytes would produce a
            // clean report about a position nothing runs.
            P1M3BodyAnchorPlacementContract contract = Contract(5f, 0.2f, 0f);
            var exception = Assert.Throws<System.InvalidOperationException>(
                () => Audit(
                    contract,
                    new GameObject[0],
                    Road(0f, 50f),
                    scenarioAnchor: new Vector3(0f, 0.2f, 0f)));
            Assert.That(
                exception.Message,
                Is.EqualTo("audited_anchor_differs_from_scenario_anchor"));
        }

        [Test]
        public void RoadSurfaceUnderTheAnchorIsLegitimateSupport()
        {
            // The main-loop anchor sits at road elevation, so road surfaces
            // are its support - the SCENE-003 semantics the proposal names.
            // SCENE-004 required the disc to be disjoint from the road
            // because it was authoring a *roadside* anchor; that gate is
            // specific to that work item and is not imported here.
            P1M3BodyAnchorAuditReport report =
                Audit(Contract(0f, 0.2f, 0f), new GameObject[0], Road(0f, 50f));

            Assert.That(report.support_status, Is.EqualTo("PASS"));
            Assert.That(report.support_matches.Length, Is.EqualTo(1));
            Assert.That(report.support_matches[0].source, Is.EqualTo("road_surface"));
            Assert.That(report.support_surface_y_m, Is.EqualTo(0.2f).Within(1e-6f));
            Assert.That(report.support_height_error_m, Is.EqualTo(0f).Within(1e-6f));
            Assert.That(report.clearance_status, Is.EqualTo("PASS"));
            Assert.That(report.status, Is.EqualTo("CLEAR"));
            Assert.That(report.rejection_reason, Is.EqualTo(string.Empty));
        }

        [Test]
        public void AnchorWithNoSupportUnderneathFailsTheGate()
        {
            // Road band moved far away and no support prefab present.
            P1M3BodyAnchorAuditReport report =
                Audit(Contract(0f, 0.2f, 0f), new GameObject[0], Road(500f, 2f));

            Assert.That(report.support_status, Is.EqualTo("FAIL"));
            Assert.That(report.rejection_reason, Is.EqualTo("SUPPORT_NOT_FOUND"));
            Assert.That(report.status, Is.EqualTo("ANCHOR_PLACEMENT_AUDIT_FAILED"));
            Assert.That(report.clearance_status, Is.EqualTo("NOT_EVALUATED"));
        }

        [Test]
        public void DeclaredElevationOutsideTheToleranceFailsTheGate()
        {
            // 0.2 m road surface, anchor declared 0.4 m up: 0.2 > 0.05.
            P1M3BodyAnchorAuditReport report =
                Audit(Contract(0f, 0.4f, 0f), new GameObject[0], Road(0f, 50f));

            Assert.That(report.support_status, Is.EqualTo("FAIL"));
            Assert.That(report.rejection_reason, Is.EqualTo("SUPPORT_HEIGHT_MISMATCH"));
            Assert.That(
                report.support_height_error_m,
                Is.EqualTo(0.2f).Within(1e-5f));
        }

        [Test]
        public void SupportSurfacesThatDisagreeOnElevationFailTheGate()
        {
            GameObject grass = Grass(Vector3.zero, 1.5f);
            try
            {
                P1M3BodyAnchorAuditReport report = Audit(
                    Contract(0f, 0.2f, 0f),
                    new[] { grass },
                    Road(0f, 50f));

                Assert.That(report.support_matches.Length, Is.EqualTo(2));
                Assert.That(report.support_status, Is.EqualTo("FAIL"));
                Assert.That(
                    report.rejection_reason,
                    Is.EqualTo("SUPPORT_HEIGHT_CONFLICT"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void ObstacleInsideTheAnchorCylinderBlocksTheGate()
        {
            // Effective anchor radius is 1.5 m; the obstacle spans +/-0.5 m
            // around x = 1.0, so its nearest face is 0.5 m from the anchor.
            GameObject obstacle = Obstacle(new Vector3(1f, 0f, 0f));
            try
            {
                P1M3BodyAnchorAuditReport report = Audit(
                    Contract(0f, 0.2f, 0f),
                    new[] { obstacle },
                    Road(0f, 50f));

                Assert.That(report.support_status, Is.EqualTo("PASS"));
                Assert.That(report.clearance_status, Is.EqualTo("FAIL"));
                Assert.That(report.blocker_count, Is.EqualTo(1));
                Assert.That(
                    report.blockers[0].reason,
                    Is.EqualTo("CLEARANCE_INTERSECTION"));
                Assert.That(report.blockers[0].anchor_cylinder, Is.True);
                Assert.That(report.blockers[0].corridor_cylinder, Is.True);
                Assert.That(report.blockers[0].hover_sphere, Is.False);
                Assert.That(
                    report.status,
                    Is.EqualTo("ANCHOR_PLACEMENT_AUDIT_FAILED"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(obstacle);
            }
        }

        [Test]
        public void ObstacleAtHoverHeightBlocksThroughTheHoverSphereAlone()
        {
            // 1.2 m horizontally away - outside the 1.0 m corridor cylinder -
            // but spanning the 25.2 m hover point, so only the hover sphere
            // can catch it.
            GameObject obstacle = Obstacle(new Vector3(1.7f, 25f, 0f));
            try
            {
                P1M3BodyAnchorAuditReport report = Audit(
                    Contract(0f, 0.2f, 0f),
                    new[] { obstacle },
                    Road(0f, 50f));

                Assert.That(report.blocker_count, Is.EqualTo(1));
                Assert.That(report.blockers[0].anchor_cylinder, Is.False);
                Assert.That(report.blockers[0].corridor_cylinder, Is.False);
                Assert.That(report.blockers[0].hover_sphere, Is.True);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(obstacle);
            }
        }

        [Test]
        public void EveryBlockerIsReportedNotOnlyTheFirst()
        {
            // The one reporting difference from the SCENE-003 auditor: that
            // one returned on the first blocker because it was ranking 1,257
            // lattice candidates. Here a FAIL stops the whole batch, so the
            // full attribution has to be in the artifact.
            GameObject first = Obstacle(new Vector3(1f, 0f, 0f), name: "A obstacle");
            GameObject second = Obstacle(new Vector3(-1f, 0f, 0f), name: "B obstacle");
            try
            {
                P1M3BodyAnchorAuditReport report = Audit(
                    Contract(0f, 0.2f, 0f),
                    new[] { second, first },
                    Road(0f, 50f));

                Assert.That(report.blocker_count, Is.EqualTo(2));
                Assert.That(
                    report.blockers.Select(item => item.scene_object_name),
                    Is.EqualTo(new[] { "A obstacle", "B obstacle" }));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(first);
                UnityEngine.Object.DestroyImmediate(second);
            }
        }

        [Test]
        public void ObstacleWithNoRoadDataClassificationBlocksTheGate()
        {
            var unknown = new GameObject("Vehicle_Unmapped");
            try
            {
                P1M3BodyAnchorAuditReport report = Audit(
                    Contract(0f, 0.2f, 0f),
                    new[] { unknown },
                    Road(0f, 50f));

                Assert.That(report.blocker_count, Is.EqualTo(1));
                Assert.That(
                    report.blockers[0].reason,
                    Is.EqualTo("UNCLASSIFIED_OBSTACLE"));
                Assert.That(report.audited_obstacle_count, Is.EqualTo(0));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(unknown);
            }
        }

        [Test]
        public void RouteDiagnosticIsRecordedButNeverGates()
        {
            // BC-M34-4 (c) freezes the audit as support + clearance. The
            // anchor's distance to the frozen route centreline is published
            // for Acceptance to rule on, and must not change the verdict.
            P1M3BodyAnchorAuditReport report =
                Audit(Contract(0f, 0.2f, 0f), new GameObject[0], Road(0f, 50f));

            Assert.That(report.status, Is.EqualTo("CLEAR"));
            Assert.That(
                report.route_centerline_distance_m,
                Is.EqualTo(1f).Within(1e-5f));
            Assert.That(
                report.route_corridor_half_width_m,
                Is.EqualTo(1.5f).Within(1e-5f));
        }

        static P1M3BodyAnchorAuditReport Audit(
            P1M3BodyAnchorPlacementContract contract,
            GameObject[] roots,
            RoadSceneData roadData,
            Vector3? scenarioAnchor = null)
        {
            Vector3 anchor = scenarioAnchor ?? contract.AuditedAnchor;
            var scenario = new ScenarioConfig
            {
                scenario_id = "p1-m3-body-001-audit-fixture",
                road_data_sha256 = new string('c', 64),
                anchor_world_m =
                    new ScenarioVector3(anchor.x, anchor.y, anchor.z),
                target = new TargetScenarioConfig
                {
                    route_world_m = new[]
                    {
                        new ScenarioVector3(-5f, 0.2f, 1f),
                        new ScenarioVector3(5f, 0.2f, 1f),
                        new ScenarioVector3(5f, 0.2f, 5f),
                        new ScenarioVector3(-5f, 0.2f, 5f),
                    },
                },
                scene_adjustments = new SceneAdjustmentsScenarioConfig
                {
                    route_corridor = new RouteCorridorScenarioConfig
                    {
                        target_half_width_m = 1f,
                        clearance_margin_m = 0.5f,
                    },
                },
            };
            return P1M3BodyAnchorAuditor.Audit(
                scenario,
                new string('a', 64),
                roadData,
                roots.Select(item => item.transform).ToArray(),
                contract,
                new string('b', 64));
        }

        static P1M3BodyAnchorPlacementContract Contract(float x, float y, float z)
        {
            return new P1M3BodyAnchorPlacementContract
            {
                schema_version = P1M3BodyAnchorPlacementContract.Schema,
                work_id = P1M3BodyAnchorPlacementContract.WorkId,
                audited_anchor_world_m = new ScenarioVector3(x, y, z),
                hover_offset_y_m = 25f,
                support_surface_allowlist = new[]
                {
                    "Natures_Grass Tile",
                    "Natures_Grass Tile Small",
                },
                support_height_tolerance_m = 0.05f,
                anchor_nominal_radius_m = 1f,
                hover_nominal_radius_m = 1f,
                corridor_nominal_radius_m = 0.5f,
                clearance_margin_m = 0.5f,
            };
        }

        static GameObject Grass(Vector3 position, float surfaceY)
        {
            var root = new GameObject(GrassName);
            root.transform.position =
                new Vector3(position.x, surfaceY, position.z);
            return root;
        }

        static GameObject Obstacle(
            Vector3 position,
            string name = ObstacleName)
        {
            var root = new GameObject(name);
            root.transform.position = position;
            return root;
        }

        static RoadSceneData Road(float centerZ, float halfZ)
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.01f,
                road_surface_allowlist = new[] { "Road Lane_01" },
                surfaces = new[]
                {
                    new RoadSurfacePatch
                    {
                        id = "road",
                        canonical_name = "Road Lane_01",
                        center_x_m = 0f,
                        center_z_m = centerZ,
                        yaw_deg = 0f,
                        half_extent_x_m = 200f,
                        half_extent_z_m = halfZ,
                        surface_y_m = 0.2f,
                    },
                },
                obstacle_footprints = new[]
                {
                    Footprint(
                        GrassName,
                        -GrassHalfExtent,
                        GrassHalfExtent,
                        0f,
                        0f,
                        "nature"),
                    Footprint(ObstacleName, -0.5f, 0.5f, -1f, 1f, "prop"),
                    Footprint("A obstacle", -0.5f, 0.5f, -1f, 1f, "prop"),
                    Footprint("B obstacle", -0.5f, 0.5f, -1f, 1f, "prop"),
                },
            };
        }

        static RoadObstacleFootprint Footprint(
            string canonicalName,
            float minXZ,
            float maxXZ,
            float minY,
            float maxY,
            string group)
        {
            return new RoadObstacleFootprint
            {
                canonical_name = canonicalName,
                classification = "ground-obstacle",
                group = group,
                full_min_x_m = minXZ,
                full_max_x_m = maxXZ,
                full_min_y_m = minY,
                full_max_y_m = maxY,
                full_min_z_m = minXZ,
                full_max_z_m = maxXZ,
                ground_min_x_m = minXZ,
                ground_max_x_m = maxXZ,
                ground_min_z_m = minXZ,
                ground_max_z_m = maxXZ,
                overhead_min_y_m = maxY,
            };
        }
    }
}
