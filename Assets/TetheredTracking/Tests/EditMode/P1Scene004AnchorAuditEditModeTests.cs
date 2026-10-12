using System;
using System.Linq;
using NUnit.Framework;
using TetheredTracking;
using UnityEngine;

namespace TetheredTracking.Tests
{
    public sealed class P1Scene004AnchorAuditTests
    {
        const string GrassName = "Natures_Grass Tile";
        const float GrassHalfExtent = 10f;

        [Test]
        public void CheckedInContractFreezesTheAcceptedInputsAndEnvelopeGates()
        {
            P1Scene004AnchorPlacementContract contract =
                P1Scene004AnchorPlacementContractLoader.Load(out string hash);

            Assert.That(RateStudyProtocol.IsSha256(hash), Is.True);
            Assert.That(contract.RequestedAnchor, Is.EqualTo(new Vector2(140f, 112f)));
            Assert.That(contract.hover_offset_y_m, Is.EqualTo(25f));
            Assert.That(contract.target_plane_y_m, Is.EqualTo(0.2f));
            Assert.That(contract.AnchorEffectiveRadius, Is.EqualTo(1.5f));
            Assert.That(contract.CorridorEffectiveRadius, Is.EqualTo(1f));
            Assert.That(contract.envelope_max_slant_range_m, Is.EqualTo(32f));
            Assert.That(contract.envelope_max_off_nadir_deg, Is.EqualTo(45f));
            Assert.That(
                contract.envelope_off_nadir_margin_min_deg,
                Is.EqualTo(5f));
            Assert.That(contract.circuit_world_m.Length, Is.EqualTo(6));
            Assert.That(
                contract.circuit_world_m.Select(item => item.Value).ToArray(),
                Is.EqualTo(new[]
                {
                    new Vector2(128f, 116f),
                    new Vector2(152f, 116f),
                    new Vector2(154.5f, 118.5f),
                    new Vector2(152f, 121f),
                    new Vector2(128f, 121f),
                    new Vector2(125.5f, 118.5f),
                }));
            Assert.That(
                contract.support_surface_allowlist,
                Is.EqualTo(new[]
                {
                    "Natures_Grass Tile",
                    "Natures_Grass Tile Small",
                }));
        }

        [Test]
        public void AnchorElevationIsDerivedFromTheMeasuredSupportSurface()
        {
            // The SCENE-003 blocker in one assertion: a grass surface at
            // ~1.3e-6 m used to be rejected against a hardcoded y=0.2
            // contract. Here the elevation is an output, not an input.
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            GameObject grass = Grass(new Vector3(0f, 0f, 0f), 0.0000013f);
            try
            {
                P1Scene004AnchorAuditReport report = Audit(contract, grass);

                Assert.That(report.candidates[0].support_status, Is.EqualTo("PASS"));
                Assert.That(
                    report.candidates[0].derived_anchor_y_m,
                    Is.EqualTo(0.0000013f).Within(1e-9f));
                Assert.That(
                    report.selected_anchor_world_m.Value.y,
                    Is.EqualTo(0.0000013f).Within(1e-9f));
                Assert.That(report.status, Is.EqualTo("CLEAR"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void DiscHangingOverTheSupportBoundaryIsNotSupported()
        {
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            // Centre the grass so the anchor point is inside the patch but
            // only 1.0 m from its edge, which is less than the 1.5 m disc.
            GameObject grass = Grass(
                new Vector3(-(GrassHalfExtent - 1f), 0f, 0f),
                0f);
            try
            {
                P1Scene004AnchorAuditReport report = Audit(contract, grass);

                Assert.That(
                    report.candidates[0].rejection_reason,
                    Is.EqualTo("SUPPORT_NOT_FOUND"));
                Assert.That(
                    report.candidates[0].road_disjoint_status,
                    Is.EqualTo("NOT_EVALUATED"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void AnchorDiscTouchingTheAsphaltBandIsRejected()
        {
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            GameObject grass = Grass(Vector3.zero, 0f);
            try
            {
                // Road edge exactly 1.5 m from the anchor: tangency counts.
                RoadSceneData tangent = Road(centerZ: 1.5f + 2f, halfZ: 2f);
                RoadSceneData clear = Road(centerZ: 1.5f + 2f + 0.01f, halfZ: 2f);

                P1Scene004AnchorAuditReport tangentReport =
                    Audit(contract, grass, tangent);
                P1Scene004AnchorAuditReport clearReport =
                    Audit(contract, grass, clear);

                Assert.That(
                    tangentReport.candidates[0].rejection_reason,
                    Is.EqualTo("ANCHOR_DISC_OVERLAPS_ROAD"));
                Assert.That(
                    tangentReport.candidates[0].support_status,
                    Is.EqualTo("PASS"));
                Assert.That(
                    tangentReport.candidates[0].envelope_status,
                    Is.EqualTo("NOT_EVALUATED"));
                Assert.That(
                    clearReport.candidates[0].road_disjoint_status,
                    Is.EqualTo("PASS"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void EnvelopeGateRejectsCandidatesTheFallbackWouldOtherwiseAccept()
        {
            // BC3: an anchor can be perfectly supported and clear, yet push
            // the circuit past the off-nadir margin. The lattice must not be
            // able to hand that back as a legal anchor.
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            contract.circuit_world_m = new[]
            {
                Vertex(0f, 30f),
                Vertex(1f, 30f),
                Vertex(1f, 31f),
            };
            GameObject grass = Grass(Vector3.zero, 0f);
            try
            {
                P1Scene004AnchorAuditReport report = Audit(contract, grass);

                // Note 5: candidates reached the envelope gate, so this is a
                // circuit-geometry failure (row 2), not anchor placement.
                Assert.That(report.status, Is.EqualTo("ENVELOPE_OUT_OF_BOUNDS"));
                Assert.That(report.legal_candidate_count, Is.Zero);
                Assert.That(report.envelope_rejection_count, Is.GreaterThan(0));
                P1Scene004AnchorCandidateAudit first = report.candidates[0];
                Assert.That(first.support_status, Is.EqualTo("PASS"));
                Assert.That(first.road_disjoint_status, Is.EqualTo("PASS"));
                Assert.That(first.rejection_reason, Is.EqualTo("ENVELOPE_OUT_OF_BOUNDS"));
                Assert.That(first.clearance_status, Is.EqualTo("NOT_EVALUATED"));
                // Margins are reported even on the failing path (BC6).
                Assert.That(first.maximum_off_nadir_deg, Is.GreaterThan(45f));
                Assert.That(first.off_nadir_margin_deg, Is.LessThan(0f));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void EnvelopeMarginsMatchTheClosedFormGeometry()
        {
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            contract.circuit_world_m = new[]
            {
                Vertex(10f, 0f),
                Vertex(10f, 0.5f),
                Vertex(9.5f, 0f),
            };
            GameObject grass = Grass(Vector3.zero, 0f);
            try
            {
                P1Scene004AnchorAuditReport report = Audit(contract, grass);

                float drop = 25f - 0.2f;
                float horizontal = Mathf.Sqrt(10f * 10f + 0.5f * 0.5f);
                float slant = Mathf.Sqrt(horizontal * horizontal + drop * drop);
                float offNadir =
                    Mathf.Atan2(horizontal, drop) * Mathf.Rad2Deg;

                P1Scene004AnchorCandidateAudit first = report.candidates[0];
                Assert.That(
                    first.maximum_slant_range_m,
                    Is.EqualTo(slant).Within(1e-3f));
                Assert.That(
                    first.maximum_off_nadir_deg,
                    Is.EqualTo(offNadir).Within(1e-3f));
                Assert.That(
                    first.slant_range_margin_m,
                    Is.EqualTo(32f - slant).Within(1e-3f));
                Assert.That(
                    first.off_nadir_margin_deg,
                    Is.EqualTo(45f - offNadir).Within(1e-3f));
                Assert.That(first.envelope_status, Is.EqualTo("PASS"));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void SupportHeightConflictFailsClosedBeforeAnyOtherGate()
        {
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            GameObject low = Grass(Vector3.zero, 0f);
            GameObject high = Grass(Vector3.zero, 1f);
            high.name = GrassName + " (1)";
            try
            {
                P1Scene004AnchorAuditReport report = Audit(contract, low, high);

                Assert.That(
                    report.candidates[0].rejection_reason,
                    Is.EqualTo("SUPPORT_HEIGHT_CONFLICT"));
                Assert.That(report.candidates[0].support_ids.Length, Is.EqualTo(2));
                Assert.That(
                    report.candidates[0].derived_anchor_y_m,
                    Is.NaN);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(low);
                UnityEngine.Object.DestroyImmediate(high);
            }
        }

        [Test]
        public void FallbackLatticeIsDeterministicAndOrderedByDistance()
        {
            P1Scene004AnchorPlacementContract contract = Contract();
            GameObject grass = Grass(Vector3.zero, 0f);
            try
            {
                P1Scene004AnchorAuditReport first = Audit(contract, grass);
                P1Scene004AnchorAuditReport second = Audit(contract, grass);

                Assert.That(first.candidate_count, Is.EqualTo(1257));
                Assert.That(
                    first.candidates.Select(item => (item.x_m, item.z_m)),
                    Is.EqualTo(second.candidates.Select(item => (item.x_m, item.z_m))));
                float[] distances = first.candidates
                    .Select(item => item.center_distance_m)
                    .ToArray();
                for (int index = 1; index < distances.Length; index++)
                {
                    Assert.That(
                        distances[index],
                        Is.GreaterThanOrEqualTo(distances[index - 1] - 1e-4f));
                }
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void ClearanceIntersectionRejectsAnObstacleInsideTheHoverSphere()
        {
            // Sonnet round 1 note 4: support, road-disjointness and envelope
            // each had an isolated case; the fourth gate only had end-to-end
            // coverage from the real-scene artifact.
            P1Scene004AnchorPlacementContract contract = Contract();
            contract.lattice_radius_m = 0.5f;
            GameObject grass = Grass(Vector3.zero, 0f);
            GameObject mast = new GameObject("Prop_Mast");
            mast.transform.position = Vector3.zero;
            try
            {
                RoadSceneData data = Road(centerZ: 500f, halfZ: 2f);
                data.obstacle_footprints = data.obstacle_footprints
                    .Concat(new[]
                    {
                        // A thin column reaching the 25 m hover height, one
                        // metre away: clear of the ground volumes' height
                        // band but straight through the hover sphere.
                        Footprint("Prop_Mast", -0.2f, 0.2f, 24f, 26f),
                    })
                    .ToArray();

                P1Scene004AnchorAuditReport report =
                    Audit(contract, new[] { grass, mast }, data);
                P1Scene004AnchorCandidateAudit first = report.candidates[0];

                Assert.That(first.support_status, Is.EqualTo("PASS"));
                Assert.That(first.road_disjoint_status, Is.EqualTo("PASS"));
                Assert.That(first.envelope_status, Is.EqualTo("PASS"));
                Assert.That(first.clearance_status, Is.EqualTo("FAIL"));
                Assert.That(
                    first.rejection_reason,
                    Is.EqualTo("CLEARANCE_INTERSECTION"));
                Assert.That(first.blocking_object, Is.EqualTo("Prop_Mast"));
                Assert.That(report.clearance_rejection_count, Is.GreaterThan(0));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(mast);
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void BlockedStatusDistinguishesAnchorFailureFromEnvelopeFailure()
        {
            // Sonnet round 1 note 5: the proposal's disposition table sends
            // row 1 and row 2 to different places, so the top-level status
            // must not collapse them.
            var supported = new P1Scene004AnchorCandidateAudit
            {
                support_status = "PASS",
                road_disjoint_status = "PASS",
                envelope_status = "FAIL",
                rejection_reason = "ENVELOPE_OUT_OF_BOUNDS",
            };
            var unsupported = new P1Scene004AnchorCandidateAudit
            {
                support_status = "FAIL",
                road_disjoint_status = "NOT_EVALUATED",
                rejection_reason = "SUPPORT_NOT_FOUND",
            };
            var legal = new P1Scene004AnchorCandidateAudit
            {
                support_status = "PASS",
                road_disjoint_status = "PASS",
                envelope_status = "PASS",
                clearance_status = "PASS",
            };

            Assert.That(
                P1Scene004AnchorAuditor.BlockingStatus(
                    null,
                    new[] { unsupported, supported }),
                Is.EqualTo("ENVELOPE_OUT_OF_BOUNDS"));
            Assert.That(
                P1Scene004AnchorAuditor.BlockingStatus(
                    null,
                    new[] { unsupported }),
                Is.EqualTo("BLOCKED_ANCHOR_PLACEMENT"));
            Assert.That(
                P1Scene004AnchorAuditor.BlockingStatus(
                    legal,
                    new[] { legal }),
                Is.EqualTo("CLEAR"));
        }

        static P1Scene004AnchorAuditReport Audit(
            P1Scene004AnchorPlacementContract contract,
            params GameObject[] roots) =>
            Audit(contract, roots, Road(centerZ: 500f, halfZ: 2f));

        static P1Scene004AnchorAuditReport Audit(
            P1Scene004AnchorPlacementContract contract,
            GameObject root,
            RoadSceneData roadData) =>
            Audit(contract, new[] { root }, roadData);

        static P1Scene004AnchorAuditReport Audit(
            P1Scene004AnchorPlacementContract contract,
            GameObject[] roots,
            RoadSceneData roadData)
        {
            var scenario = new ScenarioConfig
            {
                scenario_id = "p1-scene-004-audit-fixture",
                road_data_sha256 = new string('c', 64),
            };
            return P1Scene004AnchorAuditor.Audit(
                scenario,
                new string('a', 64),
                roadData,
                roots.Select(item => item.transform).ToArray(),
                contract,
                new string('b', 64));
        }

        static P1Scene004AnchorPlacementContract Contract()
        {
            return new P1Scene004AnchorPlacementContract
            {
                schema_version = P1Scene004AnchorPlacementContract.Schema,
                work_id = P1Scene004AnchorPlacementContract.WorkId,
                requested_anchor_world_m = new SceneXZ { x = 0f, z = 0f },
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
                lattice_step_m = 0.5f,
                lattice_radius_m = 10f,
                target_plane_y_m = 0.2f,
                envelope_max_slant_range_m = 32f,
                envelope_max_off_nadir_deg = 45f,
                envelope_off_nadir_margin_min_deg = 5f,
                envelope_route_sample_spacing_m = 0.25f,
                circuit_world_m = new[]
                {
                    Vertex(3f, 0f),
                    Vertex(3f, 1f),
                    Vertex(2f, 0f),
                },
            };
        }

        static SceneXZ Vertex(float x, float z) => new SceneXZ { x = x, z = z };

        static GameObject Grass(Vector3 position, float surfaceY)
        {
            var root = new GameObject(GrassName);
            root.transform.position = new Vector3(
                position.x,
                surfaceY,
                position.z);
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
                        0f),
                },
            };
        }

        static RoadObstacleFootprint Footprint(
            string canonicalName,
            float minXZ,
            float maxXZ,
            float minY,
            float maxY)
        {
            return new RoadObstacleFootprint
            {
                canonical_name = canonicalName,
                classification = "ground-obstacle",
                group = "nature",
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
