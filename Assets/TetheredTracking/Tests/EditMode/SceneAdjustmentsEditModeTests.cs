using System;
using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class SceneAdjustmentConfigTests
    {
        [Test]
        public void CheckedInConfigsCarryTheSameStrictSceneAdjustment()
        {
            string[] names =
            {
                "scenario.default.json",
                "scenario.rate-study-5hz.json",
                "scenario.rate-study-20hz.json",
            };
            foreach (string name in names)
            {
                string path = RuntimePaths.ProjectFile("config", name);
                ScenarioConfig config =
                    JsonUtility.FromJson<ScenarioConfig>(File.ReadAllText(path));

                config.Normalize();

                Assert.That(config.scene_adjustments, Is.Not.Null, name);
                Assert.That(
                    config.scene_adjustments.vehicle_relocations,
                    Has.Length.EqualTo(6),
                    name);
                Assert.That(
                    config.scene_adjustments.expected_distractor_count,
                    Is.EqualTo(1),
                    name);
                Assert.That(
                    config.scene_adjustments.route_corridor
                        .enable_dynamic_intersection_audit,
                    Is.False,
                    name);
            }
        }

        [Test]
        public void PresentAdjustmentRejectsInvalidValuesInsteadOfFallingBack()
        {
            ScenarioConfig config = ScenarioConfig.CreateDefault();
            config.road_data_sha256 = new string('0', 64);
            config.scene_adjustments = Adjustments();
            config.scene_adjustments.vehicle_relocations[0].match_tolerance_m =
                float.NaN;

            InvalidOperationException exception =
                Assert.Throws<InvalidOperationException>(() => config.Normalize());

            StringAssert.Contains("match_tolerance_m", exception.Message);
        }

        [Test]
        public void MissingAdjustmentPreservesLegacyConfigBehavior()
        {
            ScenarioConfig config = ScenarioConfig.CreateDefault();

            config.Normalize();

            Assert.That(config.scene_adjustments, Is.Null);
        }

        internal static SceneAdjustmentsScenarioConfig Adjustments(
            Vector3? destination = null)
        {
            return new SceneAdjustmentsScenarioConfig
            {
                vehicle_relocations = new[]
                {
                    new VehicleRelocationScenarioConfig
                    {
                        prefab_name = "Vehicle_Taxi",
                        original_xz_m = new ScenarioVector2(1f, 0f),
                        match_tolerance_m = 0.1f,
                        new_position_m = new ScenarioVector3(
                            (destination ?? new Vector3(1f, 0f, 5f)).x,
                            (destination ?? new Vector3(1f, 0f, 5f)).y,
                            (destination ?? new Vector3(1f, 0f, 5f)).z),
                        mark_as_distractor = true,
                    },
                },
                expected_distractor_count = 1,
                route_corridor = new RouteCorridorScenarioConfig
                {
                    target_half_width_m = 1f,
                    clearance_margin_m = 0.5f,
                    target_bottom_offset_m = 0f,
                    target_height_m = 1.55f,
                    vertical_clearance_margin_m = 0.5f,
                    road_sample_spacing_m = 0.5f,
                    jump_epsilon_m = 0.001f,
                },
            };
        }
    }

    public sealed class SceneVehicleAdjustmentTests
    {
        [Test]
        public void ApplyUsesCanonicalPrefabNameAndUniqueOriginalPosition()
        {
            GameObject near = Vehicle("Vehicle_Taxi (2)", new Vector3(1f, 0f, 0f));
            GameObject far = Vehicle("Vehicle_Taxi (9)", new Vector3(20f, 0f, 0f));
            try
            {
                SceneAdjustmentsScenarioConfig adjustments =
                    SceneAdjustmentConfigTests.Adjustments();

                var relocated = SceneVehicleAdjustmentApplier.Apply(
                    adjustments,
                    new[] { near.transform, far.transform });

                Assert.That(relocated, Has.Count.EqualTo(1));
                Assert.That(near.transform.position, Is.EqualTo(new Vector3(1f, 0f, 5f)));
                Assert.That(far.transform.position, Is.EqualTo(new Vector3(20f, 0f, 0f)));
                Assert.That(near.GetComponent<RateStudyDistractor>(), Is.Not.Null);
                Assert.That(
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName("Vehicle_Taxi (12)"),
                    Is.EqualTo("Vehicle_Taxi"));
                Assert.That(
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName("Vehicle_Taxi (copy)"),
                    Is.EqualTo("Vehicle_Taxi (copy)"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(near);
                UnityEngine.Object.DestroyImmediate(far);
            }
        }

        [Test]
        public void ApplyFailsClosedForZeroOrMultipleMatches()
        {
            GameObject first = Vehicle("Vehicle_Taxi (1)", new Vector3(1f, 0f, 0f));
            GameObject second = Vehicle("Vehicle_Taxi (2)", new Vector3(1.05f, 0f, 0f));
            try
            {
                SceneAdjustmentsScenarioConfig adjustments =
                    SceneAdjustmentConfigTests.Adjustments();
                Assert.Throws<InvalidOperationException>(() =>
                    SceneVehicleAdjustmentApplier.Apply(
                        adjustments,
                        new[] { first.transform, second.transform }));
                first.transform.position = new Vector3(50f, 0f, 0f);
                second.transform.position = new Vector3(60f, 0f, 0f);
                Assert.Throws<InvalidOperationException>(() =>
                    SceneVehicleAdjustmentApplier.Apply(
                        adjustments,
                        new[] { first.transform, second.transform }));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(first);
                UnityEngine.Object.DestroyImmediate(second);
            }
        }

        [Test]
        public void ApplyDeactivatesAnExactlyMatchedRemoval()
        {
            GameObject removed =
                Vehicle("Vehicle_Taxi (2)", new Vector3(1f, 0f, 0f));
            GameObject retained =
                Vehicle("Vehicle_Taxi (9)", new Vector3(20f, 0f, 0f));
            try
            {
                SceneAdjustmentsScenarioConfig adjustments =
                    SceneAdjustmentConfigTests.Adjustments();
                VehicleRelocationScenarioConfig relocation =
                    adjustments.vehicle_relocations[0];
                relocation.remove_from_scene = true;
                relocation.new_position_m = null;
                relocation.mark_as_distractor = false;

                IReadOnlyList<Transform> selected =
                    SceneVehicleAdjustmentApplier.Apply(
                        adjustments,
                        new[] { removed.transform, retained.transform });

                Assert.That(selected, Has.Count.EqualTo(1));
                Assert.That(removed.activeSelf, Is.False);
                Assert.That(retained.activeSelf, Is.True);
                Assert.That(
                    retained.transform.position,
                    Is.EqualTo(new Vector3(20f, 0f, 0f)));

                RouteCorridorAuditReport report = RouteCorridorAuditor.Audit(
                    "removed-vehicle-filter",
                    new[] { Vector3.zero, new Vector3(10f, 0f, 0f) },
                    adjustments.route_corridor,
                    new[] { removed.transform, retained.transform });
                Assert.That(report.audited_vehicle_count, Is.EqualTo(1));
                Assert.That(report.violation_count, Is.Zero);
                Assert.That(report.status, Is.EqualTo("CLEAR"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(removed);
                UnityEngine.Object.DestroyImmediate(retained);
            }
        }

        [Test]
        public void CorridorAuditFindsConflictAndClearsAfterRelocation()
        {
            GameObject vehicle = Vehicle("Vehicle_Taxi (2)", new Vector3(1f, 0f, 0f));
            Vector3[] route =
            {
                Vector3.zero,
                new Vector3(10f, 0f, 0f),
            };
            RouteCorridorScenarioConfig corridor =
                SceneAdjustmentConfigTests.Adjustments().route_corridor;
            try
            {
                RouteCorridorAuditReport before = RouteCorridorAuditor.Audit(
                    "synthetic",
                    route,
                    corridor,
                    new[] { vehicle.transform });
                Assert.That(before.violation_count, Is.EqualTo(1));
                Assert.That(before.violations[0].route_s_m, Is.EqualTo(1f).Within(1e-5f));

                SceneVehicleAdjustmentApplier.Apply(
                    SceneAdjustmentConfigTests.Adjustments(),
                    new[] { vehicle.transform });
                RouteCorridorAuditReport after = RouteCorridorAuditor.Audit(
                    "synthetic",
                    route,
                    corridor,
                    new[] { vehicle.transform });
                Assert.That(after.status, Is.EqualTo("CLEAR"));
                Assert.That(after.violation_count, Is.Zero);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(vehicle);
            }
        }

        [Test]
        public void OcclusionProxyIsBuiltUnderTheRelocatedVehicle()
        {
            GameObject vehicle = Vehicle("Vehicle_Taxi (2)", new Vector3(1f, 0f, 0f));
            GameObject excluded = new GameObject("ExcludedRuntimeRoot");
            GameObject geometryObject = new GameObject("Geometry");
            try
            {
                SceneVehicleAdjustmentApplier.Apply(
                    SceneAdjustmentConfigTests.Adjustments(),
                    new[] { vehicle.transform });
                MeshRenderer renderer = vehicle.GetComponent<MeshRenderer>();
                EvaluationOcclusionGeometry geometry =
                    geometryObject.AddComponent<EvaluationOcclusionGeometry>();

                geometry.BuildFromRenderers(
                    new[] { renderer },
                    excluded.transform);

                MeshCollider proxy =
                    vehicle.GetComponentInChildren<MeshCollider>(true);
                Assert.That(proxy, Is.Not.Null);
                Assert.That(proxy.transform.parent, Is.EqualTo(vehicle.transform));
                Assert.That(proxy.transform.position, Is.EqualTo(new Vector3(1f, 0f, 5f)));
                Assert.That(geometry.ProxyColliderCount, Is.EqualTo(1));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(geometryObject);
                UnityEngine.Object.DestroyImmediate(excluded);
                UnityEngine.Object.DestroyImmediate(vehicle);
            }
        }

        [Test]
        public void DistractorCardinalityGateIsExactAndOptionalOnlyWhenAbsent()
        {
            ScenarioConfig adjusted = ScenarioConfig.CreateDefault();
            adjusted.scene_adjustments = SceneAdjustmentConfigTests.Adjustments();
            Assert.That(
                RateStudyScoutingTool.DistractorCountValidationError(adjusted, 0),
                Is.EqualTo("active_distractor_count_mismatch"));
            Assert.That(
                RateStudyScoutingTool.DistractorCountValidationError(adjusted, 1),
                Is.Null);

            ScenarioConfig legacy = ScenarioConfig.CreateDefault();
            Assert.That(
                RateStudyScoutingTool.DistractorCountValidationError(legacy, 0),
                Is.Null);
        }

        static GameObject Vehicle(string name, Vector3 position)
        {
            GameObject vehicle = GameObject.CreatePrimitive(PrimitiveType.Cube);
            vehicle.name = name;
            vehicle.transform.position = position;
            vehicle.transform.localScale = new Vector3(2f, 1f, 4f);
            UnityEngine.Object.DestroyImmediate(vehicle.GetComponent<Collider>());
            return vehicle;
        }
    }
}
