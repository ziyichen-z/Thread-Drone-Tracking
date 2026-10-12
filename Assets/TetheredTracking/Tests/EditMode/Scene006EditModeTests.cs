using System;
using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 batch-1 offline tool tests. Fidelity to the frozen
    /// runtime semantics is verified against the real components and the
    /// internal originals (this assembly has InternalsVisibleTo access);
    /// gate arithmetic is verified on synthetic rigs.
    /// </summary>
    public sealed class Scene006EditModeTests
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

        static string Sha256OfFile(string projectRelativePath)
        {
            string path = Path.Combine(
                Path.GetFullPath(Path.Combine(Application.dataPath, "..")),
                projectRelativePath);
            return Scene006RouteGeometry.Sha256Hex(File.ReadAllBytes(path));
        }

        [Test]
        public void FrozenInputsMatchAcceptedHashes()
        {
            Assert.AreEqual(
                "f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3",
                Sha256OfFile("config/scenario.default.json"));
            Assert.AreEqual(
                "111e0759d4b52821d08ce4ddd1aae3fc8cc8d24e12e6fa62513403c00b401894",
                Sha256OfFile("config/road_data.json"));
        }

        [Test]
        public void RouteGeometryMatchesInternalSampling()
        {
            float expectedPerimeter = RateStudyScouting.ClosedRoutePerimeter(
                FrozenRoute);
            Assert.AreEqual(
                expectedPerimeter,
                Scene006RouteGeometry.ClosedRoutePerimeter(FrozenRoute),
                0f);
            float[] distances = { 0f, 1.3f, 50f, 123.4f, expectedPerimeter - 0.01f };
            foreach (float s in distances)
            {
                RateStudyScouting.RouteSample expected =
                    RateStudyScouting.SampleClosedRoute(FrozenRoute, s);
                Scene006RouteGeometry.RouteSample actual =
                    Scene006RouteGeometry.SampleClosedRoute(FrozenRoute, s);
                Assert.AreEqual(expected.NextWaypointIndex, actual.NextWaypointIndex);
                Assert.AreEqual(expected.Position.x, actual.Position.x, 0f);
                Assert.AreEqual(expected.Position.y, actual.Position.y, 0f);
                Assert.AreEqual(expected.Position.z, actual.Position.z, 0f);
            }
        }

        [Test]
        public void DistanceToClosedRouteMatchesHandComputed()
        {
            Assert.AreEqual(
                3f,
                Scene006RouteGeometry.DistanceToClosedRoute(
                    new Vector2(5f, -3f), SquareRoute),
                1e-5f);
            Assert.AreEqual(
                2f,
                Scene006RouteGeometry.DistanceToClosedRoute(
                    new Vector2(12f, 5f), SquareRoute),
                1e-5f);
        }

        [Test]
        public void ArgminOffAxisPhasePicksSmallestTiedPhase()
        {
            Vector3 body = new Vector3(5f, 20f, 5f);
            // All four edges offer a distance-5 foot; the smallest s wins.
            Assert.AreEqual(
                5f,
                Scene006RouteGeometry.ArgminOffAxisPhase(body, SquareRoute),
                1e-4f);
            // The perpendicular foot on the eastern edge (10, 5) is 4 m
            // away, beating the 5 m foot on the southern edge (6, 0): the
            // off-axis argmin is not the smallest-s foot.
            Assert.AreEqual(
                15f,
                Scene006RouteGeometry.ArgminOffAxisPhase(
                    new Vector3(6f, 20f, 5f), SquareRoute),
                1e-4f);
        }

        [Test]
        public void TraceMatchesRealVehicleStepForStep()
        {
            foreach (float sInit in new[] { 0f, 123.4f })
            {
                var go = new GameObject("TraceEquivalenceTarget");
                try
                {
                    var vehicle = go.AddComponent<LoopTargetVehicle>();
                    vehicle.Configure("target-0", FrozenRoute, 2f);
                    vehicle.PlaceAtRouteDistance(sInit);
                    Scene006Trace.State[] expected = new Scene006Trace.State[541];
                    expected[0] = new Scene006Trace.State(
                        go.transform.position, go.transform.rotation);
                    for (int k = 1; k <= 540; k++)
                    {
                        vehicle.Step(Scene006Trace.StepSeconds);
                        expected[k] = new Scene006Trace.State(
                            go.transform.position, go.transform.rotation);
                    }
                    Scene006Trace.State[] actual = Scene006Trace.Generate(
                        FrozenRoute, 2f, sInit);
                    Assert.AreEqual(541, actual.Length);
                    float maxPositionError = 0f;
                    float maxAngleError = 0f;
                    for (int k = 0; k <= 540; k++)
                    {
                        maxPositionError = Mathf.Max(
                            maxPositionError,
                            Vector3.Distance(
                                expected[k].Position, actual[k].Position));
                        maxAngleError = Mathf.Max(
                            maxAngleError,
                            Quaternion.Angle(
                                expected[k].Rotation, actual[k].Rotation));
                    }
                    Assert.AreEqual(
                        0f, maxPositionError, 1e-6f,
                        $"trace position drift at s_init {sInit}");
                    Assert.AreEqual(
                        0f, maxAngleError, 1e-3f,
                        $"trace rotation drift at s_init {sInit}");
                }
                finally
                {
                    UnityEngine.Object.DestroyImmediate(go);
                }
            }
        }

        [Test]
        public void TraceHashIsDeterministicAndSensitive()
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                FrozenRoute, 2f, 0f);
            string first = Scene006Trace.HashStates(trace);
            string second = Scene006Trace.HashStates(
                Scene006Trace.Generate(FrozenRoute, 2f, 0f));
            Assert.AreEqual(first, second);
            StringAssert.IsMatch("^[0-9a-f]{64}$", first);
            var modified = (Scene006Trace.State[])trace.Clone();
            modified[17] = new Scene006Trace.State(
                modified[17].Position + new Vector3(1e-4f, 0f, 0f),
                modified[17].Rotation);
            Assert.AreNotEqual(first, Scene006Trace.HashStates(modified));
        }

        [Test]
        public void FirstLapClosesInsideHorizonOnFrozenRoute()
        {
            Scene006Trace.State[] trace = Scene006Trace.Generate(
                FrozenRoute, 2f, 0f);
            int lap = Scene006Trace.FirstLapSteps(FrozenRoute, 0f, trace);
            // The frozen route's measured first lap alternates 538/539 steps
            // (proposal §5.2.2); the 540-step horizon must cover it.
            Assert.Greater(lap, 500);
            Assert.LessOrEqual(lap, 540);
        }

        [Test]
        public void GimbalReplayMatchesHandComputedUpdate()
        {
            Quaternion initial = Scene006GimbalReplay.InitialRotation;
            Assert.AreEqual(
                Quaternion.Euler(90f, 0f, 0f).x, initial.x, 1e-6f);
            Vector3 origin = new Vector3(0f, 20f, 0f);
            // Target directly below: desired equals the initial rotation.
            Quaternion nadir = Scene006GimbalReplay.Update(
                initial, origin, new Vector3(0f, 0f, 0f));
            Assert.AreEqual(0f, Quaternion.Angle(initial, nadir), 1e-4f);
            // Target at exactly 45 deg east: desired is Euler(45, 90, 0) and
            // one 24 deg step does not reach it from nadir.
            Quaternion east = Scene006GimbalReplay.Update(
                initial, origin, new Vector3(20f, 0f, 0f));
            Quaternion desiredEast = Quaternion.Euler(45f, 90f, 0f);
            Assert.AreEqual(
                24f, Quaternion.Angle(initial, east), 1e-2f);
            Assert.AreEqual(
                Quaternion.Angle(desiredEast,
                    Quaternion.RotateTowards(initial, desiredEast, 24f)),
                Quaternion.Angle(desiredEast, east),
                1e-3f);
            // Beyond the clamp: requested 63.4 deg clamps to 45 deg.
            Quaternion clamped = Scene006GimbalReplay.Update(
                initial, origin, new Vector3(40f, 0f, 0f));
            Assert.AreEqual(
                Quaternion.Angle(east, clamped), 0f, 1e-3f);
            // horizontal <= 0.001 keeps the current yaw: from pitch 30 the
            // 24 deg step cannot reach the pitch-90 desired, and the yaw
            // component stays at 33 throughout the geodesic.
            Quaternion yawKept = Scene006GimbalReplay.Update(
                Quaternion.Euler(30f, 33f, 0f), origin, new Vector3(0f, 19f, 0f));
            Assert.AreEqual(33f, yawKept.eulerAngles.y, 1e-2f);
            Assert.AreEqual(54f, yawKept.eulerAngles.x, 1e-2f);
        }

        [Test]
        public void VisibilitySampleConstructionMatchesEvaluator()
        {
            var bounds = new Bounds(
                new Vector3(1f, 2f, 3f), new Vector3(4f, 2f, 6f));
            Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
            Vector3[] expectedCorners = CoverageEvaluator.BoundsCorners(bounds);
            Assert.AreEqual(expectedCorners.Length, corners.Length);
            for (int index = 0; index < corners.Length; index++)
                Assert.AreEqual(expectedCorners[index], corners[index]);
            Vector3[] samples = Scene006Visibility.VisibilitySamples(
                bounds, corners);
            Vector3[] expectedSamples = CoverageEvaluator.VisibilitySamples(
                bounds, corners);
            Assert.AreEqual(expectedSamples.Length, samples.Length);
            Assert.AreEqual(15, samples.Length);
            for (int index = 0; index < samples.Length; index++)
                Assert.AreEqual(expectedSamples[index], samples[index]);
        }

        [Test]
        public void VisibilityThresholdUsesConstantDenominator()
        {
            // 3/15 == 0.2 passes the >= 0.2 frozen threshold; 2/15 fails.
            Assert.IsTrue(
                new Scene006Visibility.Snapshot(3, 3).FrustumVisible);
            Assert.IsFalse(
                new Scene006Visibility.Snapshot(2, 2).FrustumVisible);
            Assert.IsTrue(
                new Scene006Visibility.Snapshot(15, 3).GeometricallyVisible);
            Assert.IsFalse(
                new Scene006Visibility.Snapshot(15, 2).GeometricallyVisible);
        }

        [Test]
        public void VisibilityFrustumAndOcclusionOnSyntheticRig()
        {
            var cameraGo = new GameObject("Scene006TestCamera");
            var targetGo = new GameObject("Scene006TestTarget");
            var occluderGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                // Keep the rig far from any open-scene geometry.
                cameraGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 20f, 5000f),
                    Quaternion.Euler(90f, 0f, 0f));
                Camera camera = cameraGo.AddComponent<Camera>();
                camera.fieldOfView = 60f;
                camera.aspect = 640f / 480f;
                camera.nearClipPlane = 0.3f;
                camera.farClipPlane = 500f;

                GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
                body.transform.SetParent(targetGo.transform, false);
                body.transform.localPosition = new Vector3(0f, 0.5f, 0f);
                body.transform.localScale = new Vector3(2f, 1f, 4f);
                UnityEngine.Object.DestroyImmediate(
                    body.GetComponent<Collider>());
                targetGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 0f, 5000f), Quaternion.identity);

                Renderer[] renderers = targetGo.GetComponentsInChildren<Renderer>();
                Bounds bounds = renderers[0].bounds;
                Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
                Func<Vector3, Vector3, bool> los =
                    (origin, point) => Scene006Visibility.HasClearLineOfSight(
                        origin, point, targetGo.transform);

                // Unoccluded: all 15 samples in frustum and clear.
                Scene006Visibility.Snapshot open = Scene006Visibility.Evaluate(
                    camera, bounds, corners, los);
                Assert.AreEqual(15, open.FrustumSampleCount);
                Assert.AreEqual(15, open.VisibleSampleCount);
                Assert.IsTrue(open.FrustumVisible);
                Assert.IsTrue(open.GeometricallyVisible);

                // A solid occluder between camera and target: frustum holds,
                // rays fail.
                occluderGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 10f, 5000f),
                    Quaternion.identity);
                occluderGo.transform.localScale = new Vector3(10f, 1f, 10f);
                Physics.SyncTransforms();
                Scene006Visibility.Snapshot blocked =
                    Scene006Visibility.Evaluate(camera, bounds, corners, los);
                Assert.AreEqual(15, blocked.FrustumSampleCount);
                Assert.AreEqual(0, blocked.VisibleSampleCount);
                Assert.IsTrue(blocked.FrustumVisible);
                Assert.IsFalse(blocked.GeometricallyVisible);
                occluderGo.SetActive(false);
                Physics.SyncTransforms();

                // Far off-axis: nothing in frustum.
                targetGo.transform.position =
                    new Vector3(5000f, 0f, 5100f);
                bounds = renderers[0].bounds;
                corners = Scene006Visibility.BoundsCorners(bounds);
                Scene006Visibility.Snapshot outside =
                    Scene006Visibility.Evaluate(camera, bounds, corners, los);
                Assert.AreEqual(0, outside.FrustumSampleCount);
                Assert.IsFalse(outside.FrustumVisible);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraGo);
                UnityEngine.Object.DestroyImmediate(targetGo);
                UnityEngine.Object.DestroyImmediate(occluderGo);
            }
        }

        [Test]
        public void ProjectionMatchesInternalProjectRenderers()
        {
            var cameraGo = new GameObject("Scene006ProjectionCamera");
            var cubeGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                Camera camera = cameraGo.AddComponent<Camera>();
                camera.fieldOfView = 60f;
                camera.aspect = 640f / 480f;
                camera.nearClipPlane = 0.3f;
                camera.farClipPlane = 500f;
                cubeGo.transform.localScale = new Vector3(2f, 1f, 4f);
                Renderer[] renderers =
                    cubeGo.GetComponentsInChildren<Renderer>();
                var poses = new[]
                {
                    new KeyValuePair<Vector3, Quaternion>(
                        new Vector3(5000f, 20f, 5000f),
                        Quaternion.Euler(90f, 0f, 0f)),
                    new KeyValuePair<Vector3, Quaternion>(
                        new Vector3(5000f, 25f, 5000f),
                        Quaternion.Euler(55f, 37f, 0f)),
                    new KeyValuePair<Vector3, Quaternion>(
                        new Vector3(5000f, 30f, 4990f),
                        Quaternion.Euler(70f, -25f, 0f)),
                };
                cubeGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 0f, 5000f),
                    Quaternion.Euler(0f, 41f, 0f));
                foreach (KeyValuePair<Vector3, Quaternion> pose in poses)
                {
                    cameraGo.transform.SetPositionAndRotation(
                        pose.Key, pose.Value);
                    NormalizedBoundingBox expected =
                        CoverageEvaluator.ProjectRenderers(
                            camera, renderers, 640f / 480f);
                    NormalizedBoundingBox actual =
                        Scene006Visibility.ProjectRenderers(camera, renderers);
                    if (expected == null)
                    {
                        Assert.IsNull(actual);
                        continue;
                    }
                    Assert.NotNull(actual);
                    // P1-EVAL-001: the evaluator now projects with its own
                    // pinned-aspect math instead of camera.WorldToViewportPoint.
                    // Unity's native path computes at higher precision than the
                    // float matrices exposed to scripts, so the two paths differ
                    // by float-path noise that scales with scene-coordinate
                    // magnitude: <=1.4e-5 observed at these 5000 m probe
                    // coordinates (~0.009 px at 640 px), and orders of magnitude
                    // less at production distances. Tolerance is 5e-5 (was
                    // 1e-6 when both sides shared the identical Unity call);
                    // structural defects still fail far above it.
                    Assert.AreEqual(expected.x, actual.x, 5e-5f);
                    Assert.AreEqual(expected.y, actual.y, 5e-5f);
                    Assert.AreEqual(expected.width, actual.width, 5e-5f);
                    Assert.AreEqual(expected.height, actual.height, 5e-5f);
                }
                // Behind the camera: both null.
                cameraGo.transform.SetPositionAndRotation(
                    new Vector3(5000f, 20f, 5000f),
                    Quaternion.Euler(-90f, 0f, 0f));
                Assert.IsNull(
                    CoverageEvaluator.ProjectRenderers(
                        camera, renderers, 640f / 480f));
                Assert.IsNull(
                    Scene006Visibility.ProjectRenderers(camera, renderers));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(cameraGo);
                UnityEngine.Object.DestroyImmediate(cubeGo);
            }
        }

        [Test]
        public void QuantileType7MatchesHandComputed()
        {
            var values = new List<float> { 1f, 2f, 3f, 4f };
            Assert.AreEqual(
                1.15, Scene006Visibility.QuantileType7(values, 0.05), 1e-9);
            Assert.AreEqual(
                2.5, Scene006Visibility.QuantileType7(values, 0.5), 1e-9);
            Assert.AreEqual(
                3.85, Scene006Visibility.QuantileType7(values, 0.95), 1e-9);
            Assert.AreEqual(
                7.0,
                Scene006Visibility.QuantileType7(
                    new List<float> { 7f }, 0.05),
                1e-9);
            Assert.Throws<InvalidOperationException>(
                () => Scene006Visibility.QuantileType7(
                    new List<float>(), 0.05));
        }
    }
}

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 batch-1 gate-arithmetic tests: station set, path
    /// certificates, T5 preflight composition and an end-to-end synthetic
    /// baseline run.
    /// </summary>
    public sealed class Scene006GateEditModeTests
    {
        static readonly Vector3[] SquareRoute =
        {
            new Vector3(0f, 0f, 0f),
            new Vector3(10f, 0f, 0f),
            new Vector3(10f, 0f, 10f),
            new Vector3(0f, 0f, 10f),
        };

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

        [Test]
        public void StationSetMatchesFrozenConstruction()
        {
            Vector3 anchor = new Vector3(132f, 0.2f, 117f);
            Scene006StationSet.Station[] stations = Scene006StationSet.Build(
                anchor, 0.2f, 25f);
            int expected = 0;
            foreach (float h in Scene006StationSet.HeightsM)
            {
                double radiusSquared = 35.0 * 35.0 - (double)h * h;
                int extent = (int)Math.Floor(Math.Sqrt(radiusSquared) / 4.0);
                for (int i = -extent; i <= extent; i++)
                {
                    for (int j = -extent; j <= extent; j++)
                    {
                        double dx = i * 4.0;
                        double dz = j * 4.0;
                        if (dx * dx + dz * dz <= radiusSquared + 1e-9)
                            expected++;
                    }
                }
            }
            // The 25 m hover point has no lattice duplicate.
            Assert.AreEqual(expected + 1, stations.Length);
            for (int index = 1; index < stations.Length; index++)
            {
                Scene006StationSet.Station left = stations[index - 1];
                Scene006StationSet.Station right = stations[index];
                int byHeight = left.HeightAglM.CompareTo(right.HeightAglM);
                int byX = left.World.x.CompareTo(right.World.x);
                int byZ = left.World.z.CompareTo(right.World.z);
                bool ordered = byHeight < 0
                    || (byHeight == 0 && byX < 0)
                    || (byHeight == 0 && byX == 0 && byZ <= 0);
                Assert.IsTrue(ordered, "stations must be sorted by (h, x, z)");
            }
            Assert.AreEqual(8f, stations[0].HeightAglM);
            Assert.AreEqual(100f, stations[0].World.x, 1e-5f);
            Assert.AreEqual(109f, stations[0].World.z, 1e-5f);
            int hoverCount = 0;
            foreach (Scene006StationSet.Station station in stations)
            {
                if (!station.IsHover) continue;
                hoverCount++;
                Assert.AreEqual(25.2f, station.World.y, 1e-4f);
                Assert.AreEqual(132f, station.World.x, 1e-5f);
                Assert.AreEqual(117f, station.World.z, 1e-5f);
            }
            Assert.AreEqual(1, hoverCount);
        }

        [Test]
        public void StationSetMergesHoverIntoLatticeDuplicate()
        {
            Scene006StationSet.Station[] stations = Scene006StationSet.Build(
                new Vector3(150f, 0f, 90f), 0f, 20f);
            int hoverCount = 0;
            int atHover = 0;
            foreach (Scene006StationSet.Station station in stations)
            {
                if (station.IsHover) hoverCount++;
                if (station.World == new Vector3(150f, 20f, 90f))
                {
                    atHover++;
                    Assert.IsTrue(station.IsHover);
                }
            }
            Assert.AreEqual(1, hoverCount);
            Assert.AreEqual(1, atHover);
        }

        [Test]
        public void TrapezoidDurationMatchesAnalytic()
        {
            Assert.AreEqual(
                3.5f, Scene006PathCertificate.TrapezoidDuration(10f), 1e-5f);
            Assert.AreEqual(
                2f, Scene006PathCertificate.TrapezoidDuration(4f), 1e-5f);
            Assert.AreEqual(
                2f * Mathf.Sqrt(0.5f),
                Scene006PathCertificate.TrapezoidDuration(2f),
                1e-5f);
        }

        [Test]
        public void CertificateOpenFieldPasses()
        {
            Scene006PathCertificate.Certificate certificate =
                Scene006PathCertificate.Evaluate(
                    Vector3.zero,
                    new Vector3(0f, 20f, 0f),
                    0f,
                    new Vector3(0f, 20f, 10f),
                    Array.Empty<Scene006PathCertificate.ObstaclePrism>(),
                    null);
            Assert.IsTrue(certificate.Passed);
            Assert.AreEqual(3.5f, certificate.DurationSeconds, 1e-4f);
            Assert.AreEqual(41, certificate.SampleCount);
        }

        [Test]
        public void CertificateClassifiesBodyAndTetherSeparately()
        {
            // Obstacle beside the station, offset from the tether fan by
            // more than the inflated tether radius: body rejection only.
            Scene006PathCertificate.Certificate body =
                Scene006PathCertificate.Evaluate(
                    Vector3.zero,
                    new Vector3(0f, 20f, 0f),
                    0f,
                    new Vector3(0f, 20f, 10f),
                    new[] { Prism("body-block", 0.5f, 2f, 9f, 11f, 19f, 21f) },
                    null);
            Assert.IsTrue(body.BodyRejected);
            Assert.IsFalse(body.TetherRejected);
            Assert.IsFalse(body.Passed);
            Assert.AreEqual("body-block", body.BlockingObstacle);

            // Thin obstacle under the tether fan far below the body path:
            // tether rejection only.
            Scene006PathCertificate.Certificate tether =
                Scene006PathCertificate.Evaluate(
                    Vector3.zero,
                    new Vector3(0f, 20f, 0f),
                    0f,
                    new Vector3(0f, 20f, 10f),
                    new[] { Prism("tether-block", -0.2f, 0.8f, 1f, 1.5f, 0f, 6f) },
                    null);
            Assert.IsFalse(tether.BodyRejected);
            Assert.IsTrue(tether.TetherRejected);
            Assert.IsFalse(tether.Passed);
        }

        [Test]
        public void CertificateRejectsPathOutsideBallAndBand()
        {
            Scene006PathCertificate.Certificate certificate =
                Scene006PathCertificate.Evaluate(
                    Vector3.zero,
                    new Vector3(0f, 20f, 0f),
                    0f,
                    new Vector3(0f, 40f, 0f),
                    Array.Empty<Scene006PathCertificate.ObstaclePrism>(),
                    null);
            Assert.IsTrue(certificate.PathRejected);
            Assert.IsFalse(certificate.Passed);
        }

        [Test]
        public void PrismDistancesMatchHandComputed()
        {
            Scene006PathCertificate.ObstaclePrism prism = Prism(
                "p", 1f, 2f, 4f, 6f, -1f, 1f);
            Assert.AreEqual(
                Mathf.Sqrt(17f),
                Scene006PathCertificate.PointPrismDistance(
                    Vector3.zero, prism),
                1e-4f);
            Assert.AreEqual(
                1f,
                Scene006PathCertificate.SegmentPrismDistance(
                    Vector3.zero, new Vector3(0f, 0f, 10f), prism),
                1e-3f);
            // A segment passing through the prism: distance zero.
            Assert.AreEqual(
                0f,
                Scene006PathCertificate.SegmentPrismDistance(
                    new Vector3(1.5f, 0f, 0f),
                    new Vector3(1.5f, 0f, 10f),
                    prism),
                1e-6f);
        }

        static RoadSceneData SyntheticRoadData()
        {
            return new RoadSceneData
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
                    new RoadObstacleFootprint
                    {
                        canonical_name = "Buildings_Test",
                        classification = "ground-obstacle",
                        group = "building",
                        full_min_x_m = -15f,
                        full_max_x_m = 15f,
                        full_min_y_m = 0f,
                        full_max_y_m = 30f,
                        full_min_z_m = -15f,
                        full_max_z_m = 15f,
                        ground_min_x_m = -15f,
                        ground_max_x_m = 15f,
                        ground_min_z_m = -15f,
                        ground_max_z_m = 15f,
                        overhead_min_y_m = 30f,
                    },
                },
            };
        }

        static ScenarioConfig SyntheticScenario()
        {
            ScenarioConfig config = ScenarioConfig.CreateDefault();
            config.road_data_sha256 =
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
            return config;
        }

        const string FakeSha =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

        [Test]
        public void PreflightContractMatchesFrozenParameters()
        {
            P1Scene003AnchorPlacementContract contract =
                Scene006AnchorPreflight.BuildContract(
                    new Vector3(150f, 0f, 90f), 20f);
            Assert.AreEqual(0f, contract.RequestedAnchor.y);
            Assert.AreEqual(20f, contract.hover_offset_y_m);
            Assert.AreEqual(
                new[] { "Natures_Grass Tile", "Natures_Grass Tile Small" },
                contract.support_surface_allowlist);
            Assert.AreEqual(0.05f, contract.support_height_tolerance_m);
            Assert.AreEqual(1.5f, contract.AnchorEffectiveRadius);
            Assert.AreEqual(1.5f, contract.HoverEffectiveRadius);
            Assert.AreEqual(1.0f, contract.CorridorEffectiveRadius);
            Assert.AreEqual(0.5f, contract.lattice_step_m);
            Assert.AreEqual(10f, contract.lattice_radius_m);
            Assert.AreEqual(
                Scene006AnchorPreflight.ContractSha256(contract),
                Scene006AnchorPreflight.ContractSha256(
                    Scene006AnchorPreflight.BuildContract(
                        new Vector3(150f, 0f, 90f), 20f)));
        }

        [Test]
        public void PreflightReportsCandidatesAvailableOnGrass()
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
                Scene006AnchorPreflight.ModeReport report =
                    Scene006AnchorPreflight.RunMode(
                        Scene006AnchorPreflight.ModeCandidatePreflight,
                        SyntheticScenario(),
                        FakeSha,
                        SyntheticRoadData(),
                        new[] { grass.transform },
                        new Vector3(150f, 0f, 90f),
                        20f,
                        farRoute);
                Assert.AreEqual(1257, report.candidate_count);
                Assert.AreEqual(
                    "CANDIDATES_AVAILABLE", report.status);
                Assert.Greater(report.legal_candidate_count, 0);
                Assert.AreEqual(0, report.route_rejection_count);
                Assert.AreEqual(
                    "PASS", report.candidates[0].support_status);
                Assert.AreEqual(
                    0.02f, report.candidates[0].support_surface_y_m, 1e-5f);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void PreflightAppliesRouteDistanceSubGate()
        {
            var grass = new GameObject("Natures_Grass Tile");
            try
            {
                grass.transform.position = new Vector3(150f, 0f, 90f);
                // The square frames the grass tile at its boundary, so
                // supported candidates within 1.5 m of an edge exist.
                Vector3[] route =
                {
                    new Vector3(147f, 0f, 87f),
                    new Vector3(153f, 0f, 87f),
                    new Vector3(153f, 0f, 93f),
                    new Vector3(147f, 0f, 93f),
                };
                Scene006AnchorPreflight.ModeReport report =
                    Scene006AnchorPreflight.RunMode(
                        Scene006AnchorPreflight.ModeCandidatePreflight,
                        SyntheticScenario(),
                        FakeSha,
                        SyntheticRoadData(),
                        new[] { grass.transform },
                        new Vector3(150f, 0f, 90f),
                        20f,
                        route);
                Assert.Greater(report.route_rejection_count, 0);
                // The lattice centre is 10 m from every edge: it survives.
                Assert.AreEqual(
                    "PASS", report.candidates[0].route_gate_status);
                Assert.AreEqual(
                    3f, report.candidates[0].route_distance_m, 1e-4f);
                Assert.IsNull(report.candidates[0].rejection_reason);
                bool foundRouteRejection = false;
                foreach (Scene006AnchorPreflight.CandidateRecord candidate
                    in report.candidates)
                {
                    if (candidate.rejection_reason == "ROUTE_ANCHOR_DISTANCE")
                        foundRouteRejection = true;
                }
                Assert.IsTrue(foundRouteRejection);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(grass);
            }
        }

        [Test]
        public void PreflightAllRejectedYieldsBlockedV2()
        {
            Vector3[] farRoute =
            {
                new Vector3(500f, 0f, 500f),
                new Vector3(510f, 0f, 500f),
                new Vector3(510f, 0f, 510f),
                new Vector3(500f, 0f, 510f),
            };
            Scene006AnchorPreflight.ModeReport report =
                Scene006AnchorPreflight.RunMode(
                    Scene006AnchorPreflight.ModeCandidatePreflight,
                    SyntheticScenario(),
                    FakeSha,
                    SyntheticRoadData(),
                    Array.Empty<UnityEngine.Transform>(),
                    new Vector3(150f, 0f, 90f),
                    20f,
                    farRoute);
            Assert.AreEqual(0, report.legal_candidate_count);
            Assert.AreEqual("BLOCKED_ANCHOR_PLACEMENT_V2", report.status);
            Assert.AreEqual(
                report.candidate_count, report.support_rejection_count);
        }

        [Test]
        public void SyntheticBaselineRunProducesExpectedGates()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            try
            {
                rig.CreateTargetReplica();
                rig.CreateEvaluationCamera(60f, 640, 480);
                Vector3 anchor = new Vector3(5f, 0f, 5f);
                Scene006Trace.State[] trace = Scene006Trace.Generate(
                    SquareRoute, 2f, 0f);
                string traceSha = Scene006Trace.HashStates(trace);
                int firstLap = Scene006Trace.FirstLapSteps(
                    SquareRoute, 0f, trace);
                var inputs = new Scene006Evaluation.Inputs
                {
                    ScenarioId = "synthetic-test",
                    ScenarioSha256 = FakeSha,
                    RoadDataSha256 = FakeSha,
                    Route = SquareRoute,
                    Trace = trace,
                    SInit = 0f,
                    TraceSha256 = traceSha,
                    FirstLapSteps = firstLap,
                    Anchor = anchor,
                    SupportY = 0f,
                    HoverHeightM = 20f,
                    VerticalFovDeg = 60f,
                    ImageWidth = 640,
                    ImageHeight = 480,
                    TargetRoot = rig.TargetReplica.transform,
                    TargetRenderers = rig.TargetRenderers,
                    Cam = rig.EvaluationCamera,
                    Obstacles =
                        Array.Empty<Scene006PathCertificate.ObstaclePrism>(),
                    LineOfSight = null,
                };
                Scene006Evaluation.BaselineReport report =
                    Scene006Evaluation.Run(inputs);

                Assert.AreEqual(541, report.samples.Length);
                Assert.AreEqual(0f, report.samples[0].t_s);
                Assert.AreEqual("MEASURED", report.trace_first_lap_status);
                // Camera directly above the loop centre, no occluders:
                // everything visible from every certified station.
                Assert.AreEqual(1f, report.t2.c_frustum, 1e-6f);
                Assert.AreEqual("FAIL", report.t2.gate);
                Assert.AreEqual(1f, report.t3.c_geom, 1e-6f);
                Assert.AreEqual(0f, report.t3.l_occ, 1e-6f);
                Assert.AreEqual("FAIL", report.t3.gate);
                Assert.AreEqual(540, report.t1.domain_count);
                Assert.IsFalse(report.t1.fidelity_contradiction);
                Assert.AreEqual("PASS", report.t1.gate);
                Assert.AreEqual(0, report.t6.k_star);
                Assert.AreEqual(
                    report.t6.prompt_min_side_px
                        >= report.t6.t1_domain_median_px
                        ? "PASS" : "FAIL",
                    report.t6.gate);
                Assert.AreEqual(1f, report.t4.c_hold, 1e-6f);
                Assert.AreEqual(0, report.t4.path_rejection_count);
                Assert.AreEqual(0, report.t4.body_rejection_count);
                Assert.AreEqual(0, report.t4.tether_rejection_count);
                Assert.AreEqual(1f, report.t4.best_c_station, 1e-6f);
                Assert.AreEqual(0f, report.t4.g_station, 1e-6f);
                Assert.AreEqual("FAIL", report.t4.gate);
            }
            finally
            {
                rig.Cleanup();
            }
        }
    }
}
