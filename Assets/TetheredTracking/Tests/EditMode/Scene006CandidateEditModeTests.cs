using System;
using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 amendment-1 batch-1b tests: F1 (externally recomputable
    /// trace hash), F2 (literal §5.4.4 head trim), F4 (legal boolean plus
    /// the "" no-value convention), the §3.3.2 relocation solver, the
    /// full-instance certificate prism set and the candidate T1/T2/T3 cell
    /// evaluation with occlusion attribution.
    /// </summary>
    public sealed class Scene006CandidateEditModeTests
    {
        static readonly Vector3[] FrozenRoute =
        {
            new Vector3(125.5f, 0.2f, 117.5f),
            new Vector3(174.5f, 0.2f, 117.5f),
            new Vector3(177.5f, 0.2f, 114.5f),
            new Vector3(177.5f, 0.2f, 65.5f),
            new Vector3(174.5f, 0.2f, 62.5f),
            new Vector3(125.5f, 0.2f, 62.5f),
            new Vector3(122.5f, 0.2f, 65.5f),
            new Vector3(122.5f, 0.2f, 114.5f),
        };

        static readonly Vector3[] SquareRoute =
        {
            new Vector3(0f, 0f, 0f),
            new Vector3(10f, 0f, 0f),
            new Vector3(10f, 0f, 10f),
            new Vector3(0f, 0f, 10f),
        };

        static string ProjectFile(string projectRelativePath) =>
            Path.Combine(
                Path.GetFullPath(Path.Combine(Application.dataPath, "..")),
                projectRelativePath);

        static Scene006PathCertificate.ObstaclePrism Prism(
            string id,
            float minX,
            float maxX,
            float minZ,
            float maxZ,
            float minY,
            float maxY) =>
            new Scene006PathCertificate.ObstaclePrism(
                id,
                new[]
                {
                    new Vector2(minX, minZ),
                    new Vector2(maxX, minZ),
                    new Vector2(maxX, maxZ),
                    new Vector2(minX, maxZ),
                },
                minY,
                maxY);

        // ------------------------------------------------------------ F1

        [Test]
        public void TraceArtifactBitsReproduceHashAfterJsonRoundTrip()
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                FrozenRoute, 2f, 0f);
            string expected = Scene006Trace.HashStates(trace);
            Scene006TraceArtifact.Artifact artifact =
                Scene006TraceArtifact.Build(
                    "test", new string('0', 64), "A",
                    new Vector3(150f, 0f, 108f), 0f, 0f, trace, 538);
            Assert.AreEqual(expected, artifact.sha256);
            Assert.AreEqual(
                expected,
                Scene006TraceArtifact.RecomputeSha256(artifact.states));

            // The published bytes alone must reproduce the hash: serialize,
            // parse back, recompute (F1's JsonUtility normalization hole is
            // closed by the *_bits fields, which travel as plain strings).
            string json = JsonUtility.ToJson(artifact, true) + "\n";
            Scene006TraceArtifact.Artifact parsed =
                JsonUtility.FromJson<Scene006TraceArtifact.Artifact>(json);
            Assert.AreEqual(
                expected,
                Scene006TraceArtifact.RecomputeSha256(parsed.states));
            // The float fields round-trip bit-exactly for this trace, so the
            // readable values and the authoritative bits agree.
            for (int k = 0; k < parsed.states.Length; k++)
            {
                Assert.AreEqual(
                    artifact.states[k].px_bits, parsed.states[k].px_bits);
                Assert.AreEqual(
                    artifact.states[k].qw_bits, parsed.states[k].qw_bits);
                Assert.AreEqual(
                    artifact.states[k].px, parsed.states[k].px);
            }
        }

        [Test]
        public void TraceArtifactMatchesCrossProcessFixture()
        {
            // tests/fixtures/scene006-trace-v2-sample.json was produced by
            // an independent Python byte construction; recomputing it in C#
            // must yield its recorded sha256 (cross-process contract).
            string json = File.ReadAllText(
                ProjectFile("tests/fixtures/scene006-trace-v2-sample.json"));
            Scene006TraceArtifact.Artifact fixture =
                JsonUtility.FromJson<Scene006TraceArtifact.Artifact>(json);
            Assert.AreEqual(
                "b09b28261ddd03b2af8af102c23629d3b1b5a37b7b14ed8aaee0bc6b138b95cd",
                fixture.sha256);
            Assert.AreEqual(
                fixture.sha256,
                Scene006TraceArtifact.RecomputeSha256(fixture.states));
            // The fixture pins a negative-zero bit pattern.
            Assert.AreEqual("80000000", fixture.states[0].py_bits);
        }

        static Scene006CandidateGenerator.CaptureIdentity SyntheticCapture() =>
            new Scene006CandidateGenerator.CaptureIdentity
            {
                capture_commit = new string('c', 40),
                tool_commit = new string('c', 40),
                git_status_porcelain = "",
                scene_state_sha256 = new string('d', 64),
                scene_file_sha256_before = new string('e', 64),
                scene_file_sha256_after = new string('e', 64),
                scene_saved = false,
            };

        [Test]
        public void TraceArtifactWriteRefusesInconsistentArtifact()
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                SquareRoute, 2f, 0f);
            Scene006TraceArtifact.Artifact artifact =
                Scene006TraceArtifact.Build(
                    "test", new string('0', 64), "A",
                    Vector3.zero, 0f, 0f, trace, 40);
            artifact.capture = SyntheticCapture();
            artifact.states[3].px_bits = "deadbeef";
            Assert.Throws<InvalidOperationException>(
                () => Scene006TraceArtifact.Write(
                    "runtime/test-results/should-not-exist.json", artifact));
        }

        [Test]
        public void TraceArtifactWriteRefusesMissingOrDirtyIdentity()
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                SquareRoute, 2f, 0f);
            Scene006TraceArtifact.Artifact artifact =
                Scene006TraceArtifact.Build(
                    "test", new string('0', 64), "A",
                    Vector3.zero, 0f, 0f, trace, 40);
            // §5.6: no capture identity at all fails closed.
            Assert.Throws<InvalidOperationException>(
                () => Scene006TraceArtifact.Write(
                    "runtime/test-results/should-not-exist.json", artifact));
            // A non-empty porcelain record fails closed as well.
            artifact.capture = SyntheticCapture();
            artifact.capture.git_status_porcelain = " M dirty";
            Assert.Throws<InvalidOperationException>(
                () => Scene006TraceArtifact.Write(
                    "runtime/test-results/should-not-exist.json", artifact));
            // A scene-file before/after mismatch fails closed.
            artifact.capture = SyntheticCapture();
            artifact.capture.scene_file_sha256_after = new string('f', 64);
            Assert.Throws<InvalidOperationException>(
                () => Scene006TraceArtifact.Write(
                    "runtime/test-results/should-not-exist.json", artifact));
            // The complete identity serializes round-trip with the capture.
            artifact.capture = SyntheticCapture();
            string json = JsonUtility.ToJson(artifact, true);
            Scene006TraceArtifact.Artifact parsed =
                JsonUtility.FromJson<Scene006TraceArtifact.Artifact>(json);
            Assert.AreEqual(new string('c', 40), parsed.capture.capture_commit);
            Assert.AreEqual(
                new string('d', 64), parsed.capture.scene_state_sha256);
            Assert.IsFalse(parsed.capture.scene_saved);
        }

        // ------------------------------------------------------------ F2

        [Test]
        public void LiteralHeadTrimIgnoresOnlyTheBoundSupportInstance()
        {
            // Anchor on the bound support prism; a second grass plane beside
            // it overlapping the head segment is NOT exempt (literal §5.4.4:
            // only the measured support instance is ignored in [0, 1.70]).
            Scene006PathCertificate.ObstaclePrism support = Prism(
                "grass-bound", -2f, 2f, -2f, 2f, -0.02f, 0f);
            Scene006PathCertificate.ObstaclePrism road = Prism(
                "road-next-door", 0.2f, 0.4f, 3f, 5f, 0f, 0.2f);
            Vector3 anchor = Vector3.zero;
            Vector3 pHover = new Vector3(0f, 20f, 0f);
            Vector3 station = new Vector3(0f, 20f, 10f);

            // Bound support only: passes (support exempt inside the trim,
            // cleared beyond it by the 0.388571 >= 0.375 bound).
            Scene006PathCertificate.Certificate clean =
                Scene006PathCertificate.Evaluate(
                    anchor, pHover, 0f, station, new[] { support },
                    "grass-bound");
            Assert.IsTrue(clean.Passed);

            // A road surface within 0.375 m of the tether fails the capsule
            // even inside the head segment — the batch-1 structural form
            // never saw this instance.
            Scene006PathCertificate.ObstaclePrism roadAtTether = Prism(
                "road-at-tether", 0.2f, 0.4f, -0.5f, 0.5f, 0f, 0.2f);
            Scene006PathCertificate.Certificate blocked =
                Scene006PathCertificate.Evaluate(
                    anchor, pHover, 0f, station,
                    new[] { support, roadAtTether },
                    "grass-bound");
            Assert.IsTrue(blocked.TetherRejected);
            Assert.AreEqual("road-at-tether", blocked.BlockingObstacle);

            // Without a bound instance the support plane itself fails the
            // head segment: the trim is instance-bound, not class-bound.
            Scene006PathCertificate.Certificate unbound =
                Scene006PathCertificate.Evaluate(
                    anchor, pHover, 0f, station, new[] { support }, null);
            Assert.IsTrue(unbound.TetherRejected);

            // Naming an absent instance fails closed.
            Assert.Throws<InvalidOperationException>(
                () => Scene006PathCertificate.Evaluate(
                    anchor, pHover, 0f, station, new[] { support },
                    "grass-elsewhere"));
        }

        [Test]
        public void TrimmedSegmentDistanceSkipsTheHeadSegment()
        {
            Scene006PathCertificate.ObstaclePrism plane = Prism(
                "plane", -2f, 2f, -2f, 2f, -0.02f, 0f);
            // Full segment from the anchor hits the plane; the trimmed
            // segment (start advanced 1.70 m along the tether) clears it.
            Assert.Less(
                Scene006PathCertificate.SegmentPrismDistance(
                    Vector3.zero, new Vector3(0f, 20f, 10f), plane),
                0.375f);
            Assert.Greater(
                Scene006PathCertificate.TrimmedSegmentPrismDistance(
                    Vector3.zero, new Vector3(0f, 20f, 10f), plane),
                0.375f);
            // A segment shorter than d_trim trims to nothing.
            Assert.AreEqual(
                float.PositiveInfinity,
                Scene006PathCertificate.TrimmedSegmentPrismDistance(
                    Vector3.zero, new Vector3(0f, 1f, 0f), plane));
        }

        // ------------------------------------------------------------ F4

        [Test]
        public void PreflightLegalBooleanAndEmptyStringConventionReconcile()
        {
            var grass = new GameObject("Natures_Grass Tile");
            try
            {
                grass.transform.position = new Vector3(150f, 0f, 90f);
                Vector3[] farRoute =
                {
                    new Vector3(500f, 0f, 500f),
                    new Vector3(510f, 0f, 500f),
                    new Vector3(510f, 0f, 510f),
                    new Vector3(500f, 0f, 510f),
                };
                var roadData = new RoadSceneData
                {
                    schema_version = RoadSceneData.Schema,
                    road_surface_tolerance_m = 0.5f,
                    road_surface_allowlist = new[] { "Roads_Asphalt" },
                    surfaces = new[]
                    {
                        new RoadSurfacePatch
                        {
                            id = "road-0",
                            canonical_name = "Roads_Asphalt",
                            center_x_m = 500f,
                            center_z_m = 500f,
                            yaw_deg = 0f,
                            half_extent_x_m = 1f,
                            half_extent_z_m = 1f,
                            surface_y_m = 0.2f,
                        },
                    },
                    obstacle_footprints = new[]
                    {
                        new RoadObstacleFootprint
                        {
                            canonical_name = "Natures_Grass Tile",
                            classification = "ground-obstacle",
                            group = "nature",
                            full_min_x_m = -3f,
                            full_max_x_m = 3f,
                            full_min_y_m = 0f,
                            full_max_y_m = 0.02f,
                            full_min_z_m = -3f,
                            full_max_z_m = 3f,
                            ground_min_x_m = -3f,
                            ground_max_x_m = 3f,
                            ground_min_z_m = -3f,
                            ground_max_z_m = 3f,
                            overhead_min_y_m = 0.02f,
                        },
                    },
                };
                ScenarioConfig config = ScenarioConfig.CreateDefault();
                config.road_data_sha256 = new string('a', 64);
                Scene006AnchorPreflight.ModeReport report =
                    Scene006AnchorPreflight.RunMode(
                        Scene006AnchorPreflight.ModeCandidatePreflight,
                        config,
                        new string('b', 64),
                        roadData,
                        new[] { grass.transform },
                        new Vector3(150f, 0f, 90f),
                        20f,
                        farRoute);
                int legalBool = 0;
                int legalEmptyString = 0;
                foreach (Scene006AnchorPreflight.CandidateRecord candidate
                    in report.candidates)
                {
                    if (candidate.legal)
                    {
                        legalBool++;
                        Assert.IsNull(candidate.rejection_reason);
                    }
                    // The consumer-side convention: "" means no value.
                    if (string.IsNullOrEmpty(candidate.rejection_reason))
                        legalEmptyString++;
                }
                Assert.AreEqual(report.legal_candidate_count, legalBool);
                Assert.AreEqual(report.legal_candidate_count, legalEmptyString);
                Assert.Greater(legalBool, 0);

                // JsonUtility flattens the null strings to "" on write; the
                // legal boolean survives the round trip.
                string json = JsonUtility.ToJson(report, true);
                Scene006AnchorPreflight.ModeReport parsed =
                    JsonUtility.FromJson<
                        Scene006AnchorPreflight.ModeReport>(json);
                int parsedLegal = 0;
                int parsedEmpty = 0;
                foreach (Scene006AnchorPreflight.CandidateRecord candidate
                    in parsed.candidates)
                {
                    if (candidate.legal) parsedLegal++;
                    if (candidate.rejection_reason == "") parsedEmpty++;
                    Assert.IsNotNull(candidate.rejection_reason);
                }
                Assert.AreEqual(report.legal_candidate_count, parsedLegal);
                Assert.AreEqual(report.legal_candidate_count, parsedEmpty);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        // -------------------------------------------- relocation solver

        static Scene006RelocationSolver.InstanceFootprint Footprint(
            string name,
            float centerX,
            float centerZ,
            float halfX,
            float halfZ,
            float minY = 0f,
            float maxY = 1.5f)
        {
            return new Scene006RelocationSolver.InstanceFootprint
            {
                Name = name,
                Corners = new[]
                {
                    new Vector2(centerX - halfX, centerZ - halfZ),
                    new Vector2(centerX + halfX, centerZ - halfZ),
                    new Vector2(centerX + halfX, centerZ + halfZ),
                    new Vector2(centerX - halfX, centerZ + halfZ),
                },
                MinY = minY,
                MaxY = maxY,
                Center = new Vector2(centerX, centerZ),
                RootPosition = new Vector3(centerX, 0f, centerZ),
            };
        }

        static RoadSceneData RoadDataWithSurfaces(
            params RoadSurfacePatch[] surfaces)
        {
            return new RoadSceneData
            {
                schema_version = RoadSceneData.Schema,
                road_surface_tolerance_m = 0.5f,
                road_surface_allowlist = new[] { "Roads_Asphalt" },
                surfaces = surfaces,
                obstacle_footprints = Array.Empty<RoadObstacleFootprint>(),
            };
        }

        static RoadSurfacePatch Surface(
            string id, float cx, float cz, float halfX, float halfZ)
        {
            return new RoadSurfacePatch
            {
                id = id,
                canonical_name = "Roads_Asphalt",
                center_x_m = cx,
                center_z_m = cz,
                yaw_deg = 0f,
                half_extent_x_m = halfX,
                half_extent_z_m = halfZ,
                surface_y_m = 0.2f,
            };
        }

        [Test]
        public void RelocationSearchTakesTheOnlyFeasibleSide()
        {
            // Vehicle parked 0.5 m south of segment 0 of the square; the
            // road covers only z <= 0, so the left (north, into the square)
            // direction is infeasible and the right solution wins.
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0.5f, 1f, 1f);
            RoadSceneData roadData = RoadDataWithSurfaces(
                Surface("south-road", 5f, -6f, 20f, 6f));
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    roadData,
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsTrue(landing.Solved);
            Assert.AreEqual(0, landing.NearestSegmentIndex);
            Assert.AreEqual("right", landing.Direction);
            // d = 3.5 puts the footprint at z in [-4.5, -2.5], 2.5 m clear.
            Assert.AreEqual(3.5f, landing.DisplacementM, 1e-4f);
            Assert.AreEqual(5f, landing.NewPosition.x, 1e-4f);
            Assert.AreEqual(-3f, landing.NewPosition.z, 1e-4f);
        }

        [Test]
        public void RelocationSearchTieTakesLeft()
        {
            // Vehicle centred on the route: both sides solve at d = 3.0,
            // and the displacement tie takes the left normal.
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0f, 1f, 1f);
            RoadSceneData roadData = RoadDataWithSurfaces(
                Surface("everywhere", 5f, 0f, 20f, 20f));
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    roadData,
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsTrue(landing.Solved);
            Assert.AreEqual("left", landing.Direction);
            Assert.AreEqual(3.0f, landing.DisplacementM, 1e-4f);
        }

        [Test]
        public void RelocationSearchTakesSmallerDisplacement()
        {
            // Off-centre vehicle: left solves at 2.5, right at 3.5; the
            // smaller displacement wins.
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0.5f, 1f, 1f);
            RoadSceneData roadData = RoadDataWithSurfaces(
                Surface("everywhere", 5f, 0f, 20f, 20f));
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    roadData,
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsTrue(landing.Solved);
            Assert.AreEqual("left", landing.Direction);
            Assert.AreEqual(2.5f, landing.DisplacementM, 1e-4f);
        }

        [Test]
        public void RelocationSearchRespectsObstaclesAndPlacedVehicles()
        {
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0.5f, 1f, 1f);
            RoadSceneData roadData = RoadDataWithSurfaces(
                Surface("everywhere", 5f, 0f, 20f, 20f));
            // A tree blocking the left solution's landing spot: the left
            // search must step past it or lose to the right side.
            Scene006RelocationSolver.InstanceFootprint tree =
                Footprint("tree", 5f, 4f, 0.5f, 0.5f, 0f, 6f);
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    roadData,
                    new[] { tree },
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsTrue(landing.Solved);
            // Left d = 3.5 lands the footprint z in [3, 5] on the tree;
            // d = 4.5 clears it (footprint z in [4, 6] vs tree [3.5, 4.5]
            // would still touch -> d = 5.5: footprint z in [5, 7]).
            Assert.AreEqual("right", landing.Direction);
            Assert.AreEqual(3.5f, landing.DisplacementM, 1e-4f);

            // An already-placed vehicle occupying the right landing forces
            // the left side again (past the tree).
            Scene006RelocationSolver.InstanceFootprint placedCar =
                Footprint("placed", 5f, -3f, 1.5f, 1.5f);
            landing = Scene006RelocationSolver.Recompute(
                vehicle,
                SquareRoute,
                roadData,
                new[] { tree },
                new[] { placedCar });
            Assert.IsTrue(landing.Solved);
            Assert.AreEqual("left", landing.Direction);
            Assert.Greater(landing.DisplacementM, 3.5f);
        }

        [Test]
        public void RelocationSearchNoLegalLandingWithinLimit()
        {
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0.5f, 1f, 1f);
            // No road surface anywhere: both sides infeasible.
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    RoadDataWithSurfaces(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsFalse(landing.Solved);
        }

        [Test]
        public void RelocationLandingPositionIsRootShiftedByOffset()
        {
            // The footprint centroid is not the anchor point: with the root
            // offset from the centroid, the landing position is the root
            // plus the displacement offset (the §3.3.2 new_position_m
            // semantics), not the shifted centroid.
            Scene006RelocationSolver.InstanceFootprint vehicle =
                Footprint("car", 5f, 0.5f, 1f, 1f);
            vehicle.RootPosition = new Vector3(5.3f, 0f, 0.9f);
            RoadSceneData roadData = RoadDataWithSurfaces(
                Surface("south-road", 5f, -6f, 20f, 6f));
            Scene006RelocationSolver.RecomputedLanding landing =
                Scene006RelocationSolver.Recompute(
                    vehicle,
                    SquareRoute,
                    roadData,
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>(),
                    Array.Empty<Scene006RelocationSolver.InstanceFootprint>());
            Assert.IsTrue(landing.Solved);
            Assert.AreEqual("right", landing.Direction);
            Assert.AreEqual(3.5f, landing.DisplacementM, 1e-4f);
            Assert.AreEqual(5.3f, landing.NewPosition.x, 1e-4f);
            Assert.AreEqual(0.9f - 3.5f, landing.NewPosition.z, 1e-4f);
        }

        [Test]
        public void NearestSegmentTieTakesLowestIndex()
        {
            // The square's corner (10, 0) belongs to segments 0 and 1.
            Assert.AreEqual(
                0,
                Scene006RelocationSolver.NearestSegmentIndex(
                    new Vector2(10f, 0f), SquareRoute));
        }

        [Test]
        public void PolygonOverlapTreatsTangencyAsOverlap()
        {
            Scene006RelocationSolver.InstanceFootprint a =
                Footprint("a", 0f, 0f, 1f, 1f);
            Scene006RelocationSolver.InstanceFootprint touching =
                Footprint("b", 2f, 0f, 1f, 1f);
            Scene006RelocationSolver.InstanceFootprint apart =
                Footprint("c", 2.1f, 0f, 1f, 1f);
            Assert.IsTrue(Scene006RelocationSolver.Overlaps(
                a.Corners, touching.Corners));
            Assert.IsFalse(Scene006RelocationSolver.Overlaps(
                a.Corners, apart.Corners));
        }

        // --------------------------------------------- candidate cells

        [Test]
        public void CandidateCellMatchesBaselineArithmeticAndAttributes()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            var occluderGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                // A square route placed far from any open-scene geometry.
                Vector3[] route =
                {
                    new Vector3(5000f, 0f, 5000f),
                    new Vector3(5010f, 0f, 5000f),
                    new Vector3(5010f, 0f, 5010f),
                    new Vector3(5000f, 0f, 5010f),
                };
                rig.CreateTargetReplica();
                rig.CreateEvaluationCamera(60f, 640, 480);
                Scene006Trace.State[] trace = Scene006Trace.Generate(
                    route, 2f, 0f);
                string traceSha = Scene006Trace.HashStates(trace);
                int firstLap = Scene006Trace.FirstLapSteps(
                    route, 0f, trace);

                var inputs = new Scene006CandidateEvaluation.Inputs
                {
                    Family = "A",
                    AnchorXz = new Vector2(5005f, 5005f),
                    SupportY = 0f,
                    AltitudeM = 20f,
                    VerticalFovDeg = 60f,
                    ImageWidth = 640,
                    ImageHeight = 480,
                    Route = route,
                    Trace = trace,
                    SInit = 0f,
                    TraceSha256 = traceSha,
                    TraceArtifactPath = "synthetic",
                    FirstLapSteps = firstLap,
                    TargetRoot = rig.TargetReplica.transform,
                    TargetRenderers = rig.TargetRenderers,
                    Cam = rig.EvaluationCamera,
                };
                Scene006CandidateEvaluation.CellRecord open =
                    Scene006CandidateEvaluation.RunCell(inputs);
                Assert.AreEqual("", open.terminal);
                Assert.AreEqual(1f, open.c_frustum, 1e-6f);
                Assert.AreEqual(1f, open.c_geom, 1e-6f);
                Assert.AreEqual("FAIL", open.t2_gate);
                Assert.AreEqual("FAIL", open.t3_gate);
                Assert.IsFalse(open.gates_in_band);
                Assert.AreEqual(0, open.occluded_ticks.Length);
                Assert.AreEqual(540, open.t1_domain_count);

                // A vertical wall between the hover point and the northern
                // half of the loop: the attribution must name its root.
                occluderGo.name = "Buildings_TestOccluder";
                occluderGo.transform.SetPositionAndRotation(
                    new Vector3(5005f, 10f, 5008f), Quaternion.identity);
                occluderGo.transform.localScale =
                    new Vector3(30f, 20f, 0.5f);
                Physics.SyncTransforms();
                Scene006CandidateEvaluation.CellRecord blocked =
                    Scene006CandidateEvaluation.RunCell(inputs);
                Assert.Less(blocked.c_geom, blocked.c_frustum);
                Assert.Greater(blocked.occluded_ticks.Length, 0);
                foreach (Scene006CandidateEvaluation.OccludedTickRecord tick
                    in blocked.occluded_ticks)
                {
                    Assert.Greater(
                        tick.frustum_sample_count, tick.visible_sample_count);
                    CollectionAssert.Contains(
                        tick.blocking_roots, "Buildings_TestOccluder");
                }
                Assert.AreEqual(1f, blocked.c_frustum, 1e-6f);
            }
            finally
            {
                rig.Cleanup();
                UnityEngine.Object.DestroyImmediate(occluderGo);
            }
        }

        [Test]
        public void OccludingRootsMatchesClearLineOfSightPredicate()
        {
            var cameraGo = new GameObject("AttrCamera");
            var targetGo = new GameObject("AttrTarget");
            var occluderGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                cameraGo.transform.position = new Vector3(5000f, 20f, 5000f);
                targetGo.transform.position = new Vector3(5000f, 0f, 5000f);
                occluderGo.name = "Props_Blocker";
                occluderGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 10f, 5000f), Quaternion.identity);
                occluderGo.transform.localScale = new Vector3(10f, 1f, 10f);
                Physics.SyncTransforms();
                Vector3 origin = cameraGo.transform.position;
                Vector3 point = targetGo.transform.position;
                Assert.IsFalse(Scene006Visibility.HasClearLineOfSight(
                    origin, point, targetGo.transform));
                string[] blockers = Scene006Visibility.OccludingRoots(
                    origin, point, targetGo.transform);
                Assert.AreEqual(1, blockers.Length);
                Assert.AreEqual("Props_Blocker", blockers[0]);
                occluderGo.SetActive(false);
                Physics.SyncTransforms();
                Assert.IsTrue(Scene006Visibility.HasClearLineOfSight(
                    origin, point, targetGo.transform));
                Assert.AreEqual(
                    0,
                    Scene006Visibility.OccludingRoots(
                        origin, point, targetGo.transform).Length);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraGo);
                UnityEngine.Object.DestroyImmediate(targetGo);
                UnityEngine.Object.DestroyImmediate(occluderGo);
            }
        }

        [Test]
        public void TranslatedFamilyRouteMatchesAmendmentListing()
        {
            // §3.3: the family-B route is the frozen route's pure
            // (+60, -60) translation, listed verbatim in the amendment.
            Vector3[] translated = Scene006CandidateContract.FamilyRoute(
                Scene006CandidateContract.FamilyB, FrozenRoute);
            var expected = new[]
            {
                new Vector3(185.5f, 0.2f, 57.5f),
                new Vector3(234.5f, 0.2f, 57.5f),
                new Vector3(237.5f, 0.2f, 54.5f),
                new Vector3(237.5f, 0.2f, 5.5f),
                new Vector3(234.5f, 0.2f, 2.5f),
                new Vector3(185.5f, 0.2f, 2.5f),
                new Vector3(182.5f, 0.2f, 5.5f),
                new Vector3(182.5f, 0.2f, 54.5f),
            };
            Assert.AreEqual(expected.Length, translated.Length);
            for (int index = 0; index < expected.Length; index++)
                Assert.AreEqual(expected[index], translated[index]);
        }

        [Test]
        public void AuthorizedRelocationRowsMatchAmendmentOrder()
        {
            // Application order is lexicographic on
            // (prefab_name, original_x, original_z); the frozen table is
            // already in that order.
            Scene006CandidateContract.AuthorizedRelocation[] rows =
                Scene006CandidateContract.FamilyBRelocations;
            Assert.AreEqual(5, rows.Length);
            for (int index = 1; index < rows.Length; index++)
            {
                int byName = string.CompareOrdinal(
                    rows[index - 1].PrefabName, rows[index].PrefabName);
                Assert.LessOrEqual(byName, 0);
                if (byName == 0)
                {
                    Assert.Less(
                        rows[index - 1].OriginalXz.x,
                        rows[index].OriginalXz.x);
                }
            }
            Assert.AreEqual("Vehicle_Ambulance", rows[0].PrefabName);
            Assert.AreEqual("Vehicle_Taxi", rows[4].PrefabName);
        }
    }
}
