using System;
using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using TetheredTracking.Scene006;
using UnityEngine;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// P1-SCENE-006 T1′ parity redirection, stage T.
    ///
    /// Every expected value in this file is an <b>independent hardcoded
    /// copy</b> (§3.1.4a oracle rows 1 and 2). Nothing here reads
    /// `TargetVisualFactory`, `Scene006AppearanceContract`, the built
    /// objects, a manifest or the scenario config for its expectation, so
    /// editing a production literal without editing this file turns the
    /// suite red — which is exactly acceptance criterion A1.
    /// </summary>
    public sealed class Scene006TargetParityEditModeTests
    {
        // Oracle copy 1/4: the frozen target visual definition.
        const float BodyPositionX = 0f;
        const float BodyPositionY = 0.5f;
        const float BodyPositionZ = 0f;
        const float BodyScaleX = 2f;
        const float BodyScaleY = 1f;
        const float BodyScaleZ = 4f;
        const float BodyColorR = 0.9f;
        const float BodyColorG = 0.12f;
        const float BodyColorB = 0.1f;
        const float RoofPositionX = 0f;
        const float RoofPositionY = 1.2f;
        const float RoofPositionZ = -0.2f;
        const float RoofScaleX = 1.7f;
        const float RoofScaleY = 0.7f;
        const float RoofScaleZ = 2f;
        const float RoofColorR = 0.65f;
        const float RoofColorG = 0.08f;
        const float RoofColorB = 0.07f;
        const float ColorA = 1f;

        static void AssertVector(Vector3 expected, Vector3 actual, string label)
        {
            Assert.AreEqual(expected.x, actual.x, label + ".x");
            Assert.AreEqual(expected.y, actual.y, label + ".y");
            Assert.AreEqual(expected.z, actual.z, label + ".z");
        }

        /// <summary>
        /// BC-P2-9: expected stays the author's literal above; only the
        /// Unity colour-representation round trip is absorbed, per
        /// component and absolutely. `Material.color` cannot round-trip
        /// `0.12` exactly in a Linear-colour-space project (it reads back
        /// `0.119999953`, an error of ≈4.4e-8), so this bound is four
        /// orders of magnitude wider than the representation error and many
        /// orders narrower than any real repaint. Positions, scales,
        /// rotations, mesh and shader stay exact.
        /// </summary>
        const float ColorComponentTolerance = 1e-6f;

        static void AssertColor(Color expected, Color actual, string label)
        {
            Assert.AreEqual(
                expected.r, actual.r, ColorComponentTolerance, label + ".r");
            Assert.AreEqual(
                expected.g, actual.g, ColorComponentTolerance, label + ".g");
            Assert.AreEqual(
                expected.b, actual.b, ColorComponentTolerance, label + ".b");
            Assert.AreEqual(
                expected.a, actual.a, ColorComponentTolerance, label + ".a");
        }

        /// <summary>
        /// §3.1.3(a): the raw factory contract. Both colliders must still be
        /// present — collider removal is the consumer's, so a factory that
        /// cleaned up itself would silently change the two call sites'
        /// contract.
        /// </summary>
        [Test]
        public void FactoryBuildsTheFrozenPaintedTargetAndLeavesColliders()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var parent = new GameObject("factory-contract-parent");
            parent.transform.position = new Vector3(17f, 3f, -9f);
            parent.transform.rotation = Quaternion.Euler(0f, 35f, 0f);
            try
            {
                TargetVisualFactory.Build build =
                    TargetVisualFactory.AddTargetVisual(parent.transform);

                Assert.IsNotNull(build.Body);
                Assert.IsNotNull(build.Roof);
                Assert.IsNotNull(build.BodyRenderer);
                Assert.IsNotNull(build.RoofRenderer);
                Assert.IsNotNull(
                    build.BodyCollider,
                    "the factory must leave collider cleanup to the consumer");
                Assert.IsNotNull(build.RoofCollider, "roof collider");

                Assert.AreSame(parent.transform, build.Body.transform.parent);
                Assert.AreSame(parent.transform, build.Roof.transform.parent);
                Assert.AreEqual(
                    "Cube",
                    build.Body.GetComponent<MeshFilter>().sharedMesh.name);
                Assert.AreEqual(
                    "Cube",
                    build.Roof.GetComponent<MeshFilter>().sharedMesh.name);

                AssertVector(
                    new Vector3(BodyPositionX, BodyPositionY, BodyPositionZ),
                    build.Body.transform.localPosition,
                    "body.localPosition");
                AssertVector(
                    new Vector3(BodyScaleX, BodyScaleY, BodyScaleZ),
                    build.Body.transform.localScale,
                    "body.localScale");
                Assert.AreEqual(
                    Quaternion.identity, build.Body.transform.localRotation);
                AssertColor(
                    new Color(BodyColorR, BodyColorG, BodyColorB, ColorA),
                    build.BodyRenderer.sharedMaterial.color,
                    "body colour");

                AssertVector(
                    new Vector3(RoofPositionX, RoofPositionY, RoofPositionZ),
                    build.Roof.transform.localPosition,
                    "roof.localPosition");
                AssertVector(
                    new Vector3(RoofScaleX, RoofScaleY, RoofScaleZ),
                    build.Roof.transform.localScale,
                    "roof.localScale");
                Assert.AreEqual(
                    Quaternion.identity, build.Roof.transform.localRotation);
                AssertColor(
                    new Color(RoofColorR, RoofColorG, RoofColorB, ColorA),
                    build.RoofRenderer.sharedMaterial.color,
                    "roof colour");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(parent);
            }
        }

        /// <summary>
        /// §3.1.3(b): the real Editor consumer entry point. The replica the
        /// probe renders must be painted (the F23 gap), collider-free and
        /// DontSave, and its renderer order must stay body-then-roof so the
        /// appearance block and the union AABB keep their meaning.
        /// </summary>
        [Test]
        public void RigReplicaIsPaintedColliderFreeAndDontSave()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            try
            {
                rig.CreateTargetReplica();

                Assert.AreEqual(2, rig.TargetRenderers.Length);
                Renderer body = rig.TargetRenderers[0];
                Renderer roof = rig.TargetRenderers[1];
                AssertVector(
                    new Vector3(BodyPositionX, BodyPositionY, BodyPositionZ),
                    body.transform.localPosition,
                    "replica body.localPosition");
                AssertVector(
                    new Vector3(BodyScaleX, BodyScaleY, BodyScaleZ),
                    body.transform.localScale,
                    "replica body.localScale");
                AssertColor(
                    new Color(BodyColorR, BodyColorG, BodyColorB, ColorA),
                    body.sharedMaterial.color,
                    "replica body colour");
                AssertVector(
                    new Vector3(RoofPositionX, RoofPositionY, RoofPositionZ),
                    roof.transform.localPosition,
                    "replica roof.localPosition");
                AssertVector(
                    new Vector3(RoofScaleX, RoofScaleY, RoofScaleZ),
                    roof.transform.localScale,
                    "replica roof.localScale");
                AssertColor(
                    new Color(RoofColorR, RoofColorG, RoofColorB, ColorA),
                    roof.sharedMaterial.color,
                    "replica roof colour");

                foreach (Renderer renderer in rig.TargetRenderers)
                {
                    Assert.IsNull(
                        renderer.GetComponent<Collider>(),
                        "the Editor consumer removes the primitive colliders");
                    Assert.AreEqual(
                        HideFlags.DontSave,
                        renderer.gameObject.hideFlags,
                        "probe-owned objects must never be saved");
                }
                Assert.AreEqual(
                    HideFlags.DontSave, rig.TargetReplica.hideFlags);
            }
            finally
            {
                rig.Cleanup();
            }
        }

        /// <summary>
        /// A3: the automatic appearance regression really is falsifiable —
        /// the frozen Editor contract accepts the untouched replica and
        /// rejects a repainted or resized one.
        /// </summary>
        [Test]
        public void AppearanceContractAcceptsTheReplicaAndCatchesTampering()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            try
            {
                rig.CreateTargetReplica();
                Scene006AppearanceContract.TargetAppearance actual =
                    Scene006AppearanceContract.Describe(rig.TargetRenderers);
                CollectionAssert.IsEmpty(
                    Scene006AppearanceContract.Compare(actual),
                    "the untouched replica must satisfy the frozen contract");
                Assert.DoesNotThrow(
                    () => Scene006AppearanceContract.Verify(actual));

                rig.TargetRenderers[0].sharedMaterial.color = Color.grey;
                Assert.Throws<InvalidOperationException>(
                    () => Scene006AppearanceContract.Verify(
                        Scene006AppearanceContract.Describe(
                            rig.TargetRenderers)),
                    "a grey body must be rejected — this is the F23 failure");

                rig.TargetRenderers[1].transform.localScale =
                    new Vector3(RoofScaleX, RoofScaleY, RoofScaleZ + 0.5f);
                string[] differences = Scene006AppearanceContract.Compare(
                    Scene006AppearanceContract.Describe(rig.TargetRenderers));
                Assert.GreaterOrEqual(
                    differences.Length,
                    2,
                    "every mismatching field is reported, not just the first");
            }
            finally
            {
                rig.Cleanup();
            }
        }

        /// <summary>
        /// BC-P2-9's falsifiability, from both directions: the tolerance is
        /// wide enough for the real Unity round trip and narrow enough that
        /// a deviation past `1e-6` still turns every oracle red. The
        /// numbers below are deltas applied on top of the author literals —
        /// no expected value is read back from the object under test.
        /// </summary>
        [Test]
        public void ColorToleranceAdmitsRepresentationErrorAndNothingElse()
        {
            Scene006TestLog.ExpectMaterialInstantiation();
            var rig = new Scene006SceneRig();
            try
            {
                rig.CreateTargetReplica();
                Color authored = new Color(
                    BodyColorR, BodyColorG, BodyColorB, ColorA);

                // 1. The real round trip is inside the bound.
                Color actual = rig.TargetRenderers[0].sharedMaterial.color;
                Assert.AreNotEqual(
                    authored.g,
                    actual.g,
                    "the Linear-space round trip is genuinely lossy; if this "
                    + "ever becomes exact the tolerance can be removed");
                Assert.Less(
                    Mathf.Abs(authored.g - actual.g),
                    ColorComponentTolerance,
                    "representation error must stay inside the bound");
                Assert.DoesNotThrow(
                    () => AssertColor(authored, actual, "round trip"));

                // 2. A deviation just inside the bound is still accepted.
                Assert.DoesNotThrow(
                    () => AssertColor(
                        authored,
                        new Color(
                            authored.r,
                            authored.g + 5e-7f,
                            authored.b,
                            authored.a),
                        "inside"));

                // 3. A deviation past the bound fails, component by
                // component — the oracle is not a rubber band.
                foreach (int component in new[] { 0, 1, 2, 3 })
                {
                    Color drifted = authored;
                    drifted[component] = authored[component] + 2e-6f;
                    Assert.Throws<AssertionException>(
                        () => AssertColor(authored, drifted, "outside"),
                        "component " + component
                        + " accepted a deviation beyond the tolerance");
                }

                // 4. The Editor contract behaves identically on the live
                // replica: inside the bound is clean, outside is reported.
                CollectionAssert.IsEmpty(
                    Scene006AppearanceContract.Compare(
                        Scene006AppearanceContract.Describe(
                            rig.TargetRenderers)));
                rig.TargetRenderers[1].sharedMaterial.color = new Color(
                    RoofColorR, RoofColorG + 2e-6f, RoofColorB, ColorA);
                string[] differences = Scene006AppearanceContract.Compare(
                    Scene006AppearanceContract.Describe(rig.TargetRenderers));
                Assert.AreEqual(
                    1,
                    differences.Length,
                    "exactly the drifted component is reported: "
                    + string.Join(", ", differences));
                StringAssert.Contains("color_g", differences[0]);
            }
            finally
            {
                rig.Cleanup();
            }
        }

        [Test]
        public void AppearanceDescribeFailsClosedOnAWrongRendererSet()
        {
            Assert.Throws<InvalidOperationException>(
                () => Scene006AppearanceContract.Describe(null));
            Assert.Throws<InvalidOperationException>(
                () => Scene006AppearanceContract.Describe(
                    Array.Empty<Renderer>()));
        }

        /// <summary>
        /// F21 (AR6c): a real-file regression pin on the candidate config.
        /// The expected digest is the full literal frozen by the amendment;
        /// it is never read back from the config, from a manifest or from
        /// any gitignored artifact, so config and expectation cannot drift
        /// together.
        /// </summary>
        [Test]
        public void CandidateConfigFileStaysBitFrozen()
        {
            const string expectedSha256 =
                "ec4154d1c7a945b70a8d8ed9fa1c6937552fde1a3fc88e364eb83881eb31c831";
            const string expectedDefaultSha256 =
                "f9c9205249aacf7487579ca42f727c766800cc329d0523ec82a96140564a2ce3";

            string candidatePath = RuntimePaths.ProjectFile(
                Scene006CandidateProbe.CandidateConfigPath.Split('/'));
            Assert.AreEqual(
                expectedSha256,
                Scene006RouteGeometry.Sha256Hex(
                    File.ReadAllBytes(candidatePath)),
                "config/scenario.p1-scene-006.json is frozen (C3)");

            ScenarioConfig defaultConfig =
                Scene006SceneRig.LoadFrozenScenario(out string defaultSha);
            Assert.AreEqual(
                expectedDefaultSha256,
                defaultSha,
                "the default config the route is derived from is frozen too");

            Scene006CandidateProbe.CandidateIdentity identity =
                Scene006CandidateProbe.LoadAndBind(
                    candidatePath,
                    RuntimePaths.ProjectFile(
                        Scene006CandidateProbe.P3ArtifactPath.Split('/')),
                    defaultConfig);
            ScenarioConfig config = identity.Config;

            Assert.AreEqual(197.0f, config.anchor_world_m.x, "anchor x");
            Assert.AreEqual(30.0f, config.anchor_world_m.z, "anchor z");
            Assert.AreEqual(
                16.0f, config.drone.initial_altitude_m, "initial altitude");
            Assert.AreEqual(
                40.0f, config.sensor.vertical_fov_deg, "vertical fov");
            Assert.AreEqual(
                0,
                config.scene_adjustments.expected_distractor_count,
                "expected_distractor_count");
            Assert.AreEqual(
                5,
                config.scene_adjustments.vehicle_relocations.Length,
                "the five authorized relocation rows");

            Vector3[] defaultRoute = defaultConfig.TargetRoute();
            Vector3[] route = config.TargetRoute();
            Assert.AreEqual(8, route.Length, "eight route vertices");
            Assert.AreEqual(defaultRoute.Length, route.Length);
            for (int index = 0; index < route.Length; index++)
            {
                // Family B is the frozen (+60, -60) translation of default.
                Assert.AreEqual(
                    defaultRoute[index].x + 60f, route[index].x,
                    $"route[{index}].x");
                Assert.AreEqual(
                    defaultRoute[index].y, route[index].y,
                    $"route[{index}].y");
                Assert.AreEqual(
                    defaultRoute[index].z - 60f, route[index].z,
                    $"route[{index}].z");
            }
        }

        [Test]
        public void FrozenToolPathSetV2AddsTheRuntimeScripts()
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
                "Assets/TetheredTracking/Scripts",
            };
            CollectionAssert.AreEquivalent(
                expected, Scene006CandidateProbe.FrozenToolPathsV2);
            CollectionAssert.AreEquivalent(
                new[] { "Assets/TetheredTracking/Scripts" },
                Difference(
                    Scene006CandidateProbe.FrozenToolPathsV2,
                    Scene006CandidateProbe.FrozenToolPaths),
                "v2 adds exactly the runtime script directory");
        }

        [Test]
        public void ToolCommitDerivationUsesTheV2PathSet()
        {
            const string head = "1111111111111111111111111111111111111111";
            const string tool = "2222222222222222222222222222222222222222";
            var calls = new List<string>();
            Func<string, string> git = arguments =>
            {
                calls.Add(arguments);
                return arguments.StartsWith("log ", StringComparison.Ordinal)
                    ? tool
                    : string.Empty;
            };
            Scene006CandidateProbe.ToolCommitBinding binding =
                Scene006CandidateProbe.ResolveToolCommit(
                    git, head, Scene006CandidateProbe.FrozenToolPathsV2);

            Assert.AreEqual(tool, binding.ToolCommit);
            CollectionAssert.AreEqual(
                Scene006CandidateProbe.FrozenToolPathsV2, binding.FrozenPaths);
            foreach (string call in calls)
            {
                StringAssert.Contains(
                    "Assets/TetheredTracking/Scripts",
                    call,
                    "the runtime scripts must take part in both git calls");
            }
        }

        static string[] Difference(string[] left, string[] right)
        {
            var result = new List<string>();
            var known = new HashSet<string>(right, StringComparer.Ordinal);
            foreach (string value in left)
            {
                if (!known.Contains(value)) result.Add(value);
            }
            return result.ToArray();
        }
    }
}
