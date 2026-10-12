using System;
using System.Text;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §3.1.4 target-appearance description and the Editor-side frozen
    /// expectation used by the P-stage dry-run precheck.
    ///
    /// Two halves that must stay apart:
    ///
    /// * <see cref="Describe"/> reads the <b>actual</b> replica renderers.
    ///   Its output is what the renderer stamps into the v3 manifest's
    ///   `target_appearance` block and what the Python analyzer compares
    ///   against its own frozen constants (oracle table row 4).
    /// * <see cref="Expected"/> / <see cref="Verify"/> are oracle table row
    ///   3: an independent hardcoded copy of the same numbers. They must
    ///   never read `TargetVisualFactory`, the built objects, the manifest
    ///   or the scenario config — otherwise a production edit could drift
    ///   together with its own check (BC-P2-3).
    /// </summary>
    public static class Scene006AppearanceContract
    {
        /// <summary>
        /// BC-P2-9: the only tolerance in this contract, and it covers the
        /// four RGBA components alone. `Material.color` does not round-trip
        /// exactly in a Linear-colour-space project — writing `0.12` reads
        /// back `0.119999953` — so an exact comparison of an author-frozen
        /// literal is unachievable through the frozen material path. The
        /// bound is a per-component absolute error: no relative tolerance,
        /// no rounding, no composite norm, and the expected values stay the
        /// author's contract rather than anything read back from the built
        /// object. Observed representation error is ≈4.4e-8, four orders of
        /// magnitude inside this bound, while any real repaint is orders of
        /// magnitude outside it. Nothing else here is tolerant: mesh,
        /// shader, role, count and the full TRS stay bit-exact.
        /// </summary>
        public const float ColorComponentTolerance = 1e-6f;

        [Serializable]
        public sealed class AppearanceCube
        {
            public string role;
            public string mesh_name;
            public string shader_name;
            public Scene006Evaluation.Vec3 local_position;
            public Scene006ProbeRenderer.Vec4 local_rotation;
            public Scene006Evaluation.Vec3 local_scale;
            public float color_r;
            public float color_g;
            public float color_b;
            public float color_a;
        }

        [Serializable]
        public sealed class TargetAppearance
        {
            public string source =
                "replica renderers, read before the manifest write";
            public AppearanceCube[] cubes;
        }

        /// <summary>
        /// The frozen expectation (oracle row 3). Deliberately duplicates
        /// the production literals; `role`/`mesh_name`/`shader_name` are the
        /// unchanged Unity primitive contract under the project's URP asset.
        /// </summary>
        public static TargetAppearance Expected()
        {
            return new TargetAppearance
            {
                cubes = new[]
                {
                    new AppearanceCube
                    {
                        role = "body",
                        mesh_name = "Cube",
                        shader_name = "Universal Render Pipeline/Lit",
                        local_position = Vec3(0f, 0.5f, 0f),
                        local_rotation = Identity(),
                        local_scale = Vec3(2f, 1f, 4f),
                        color_r = 0.9f,
                        color_g = 0.12f,
                        color_b = 0.1f,
                        color_a = 1f,
                    },
                    new AppearanceCube
                    {
                        role = "roof",
                        mesh_name = "Cube",
                        shader_name = "Universal Render Pipeline/Lit",
                        local_position = Vec3(0f, 1.2f, -0.2f),
                        local_rotation = Identity(),
                        local_scale = Vec3(1.7f, 0.7f, 2f),
                        color_r = 0.65f,
                        color_g = 0.08f,
                        color_b = 0.07f,
                        color_a = 1f,
                    },
                },
            };
        }

        /// <summary>
        /// Reads the actual replica. `renderers` must be the two ordered
        /// target renderers (body, roof) exactly as the rig hands them to
        /// the probe; anything else fails closed.
        /// </summary>
        public static TargetAppearance Describe(Renderer[] renderers)
        {
            if (renderers == null || renderers.Length != 2)
            {
                throw new InvalidOperationException(
                    "target appearance requires exactly two renderers "
                    + "(body, roof); got "
                    + (renderers == null ? "null" : renderers.Length.ToString()));
            }
            string[] roles = { "body", "roof" };
            var cubes = new AppearanceCube[2];
            for (int index = 0; index < 2; index++)
            {
                Renderer renderer = renderers[index];
                if (renderer == null)
                    throw new InvalidOperationException(
                        "target appearance renderer " + index + " is null");
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null)
                    throw new InvalidOperationException(
                        "target appearance renderer " + index + " has no mesh");
                Material material = renderer.sharedMaterial;
                if (material == null || material.shader == null)
                    throw new InvalidOperationException(
                        "target appearance renderer " + index
                        + " has no material/shader");
                Transform transform = renderer.transform;
                Color color = material.color;
                cubes[index] = new AppearanceCube
                {
                    role = roles[index],
                    mesh_name = filter.sharedMesh.name,
                    shader_name = material.shader.name,
                    local_position = Vec3(transform.localPosition),
                    local_rotation = Rotation(transform.localRotation),
                    local_scale = Vec3(transform.localScale),
                    color_r = color.r,
                    color_g = color.g,
                    color_b = color.b,
                    color_a = color.a,
                };
            }
            return new TargetAppearance { cubes = cubes };
        }

        /// <summary>
        /// P-stage dry-run precheck: compare an actual description against
        /// the frozen expectation field by field. Throws with the full
        /// mismatch list; the caller maps that to
        /// `T1P2_PRECHECK_FAIL_TARGET_APPEARANCE` (zero execution quota).
        /// </summary>
        public static void Verify(TargetAppearance actual)
        {
            string[] differences = Compare(actual);
            if (differences.Length == 0) return;
            var message = new StringBuilder(
                "target appearance diverges from the frozen contract:");
            foreach (string difference in differences)
                message.Append("\n  ").Append(difference);
            throw new InvalidOperationException(message.ToString());
        }

        /// <summary>
        /// The field-by-field comparison behind <see cref="Verify"/>;
        /// returns every difference rather than the first, so a regression
        /// reports the whole appearance delta at once.
        /// </summary>
        public static string[] Compare(TargetAppearance actual)
        {
            var differences = new System.Collections.Generic.List<string>();
            TargetAppearance expected = Expected();
            if (actual == null || actual.cubes == null
                || actual.cubes.Length != expected.cubes.Length)
            {
                differences.Add(
                    "cube count: expected " + expected.cubes.Length
                    + ", got "
                    + (actual == null || actual.cubes == null
                        ? "none"
                        : actual.cubes.Length.ToString()));
                return differences.ToArray();
            }
            for (int index = 0; index < expected.cubes.Length; index++)
            {
                AppearanceCube want = expected.cubes[index];
                AppearanceCube got = actual.cubes[index];
                string prefix = "cube[" + index + "]." ;
                CompareText(differences, prefix + "role", want.role, got.role);
                CompareText(
                    differences, prefix + "mesh_name",
                    want.mesh_name, got.mesh_name);
                CompareText(
                    differences, prefix + "shader_name",
                    want.shader_name, got.shader_name);
                CompareVec3(
                    differences, prefix + "local_position",
                    want.local_position, got.local_position);
                CompareRotation(
                    differences, prefix + "local_rotation",
                    want.local_rotation, got.local_rotation);
                CompareVec3(
                    differences, prefix + "local_scale",
                    want.local_scale, got.local_scale);
                CompareColor(
                    differences, prefix + "color_r", want.color_r, got.color_r);
                CompareColor(
                    differences, prefix + "color_g", want.color_g, got.color_g);
                CompareColor(
                    differences, prefix + "color_b", want.color_b, got.color_b);
                CompareColor(
                    differences, prefix + "color_a", want.color_a, got.color_a);
            }
            return differences.ToArray();
        }

        static void CompareText(
            System.Collections.Generic.List<string> differences,
            string label,
            string expected,
            string actual)
        {
            if (!string.Equals(expected, actual, StringComparison.Ordinal))
                differences.Add(
                    label + ": expected '" + expected + "', got '"
                    + actual + "'");
        }

        static void CompareFloat(
            System.Collections.Generic.List<string> differences,
            string label,
            float expected,
            float actual)
        {
            // Bit comparison: the contract is an exact byte-level freeze, so
            // no tolerance is admissible. No appearance field is ever NaN,
            // so payload-sensitive NaN handling does not arise here.
            if (BitConverter.SingleToInt32Bits(expected)
                != BitConverter.SingleToInt32Bits(actual))
            {
                differences.Add(
                    label + ": expected " + expected.ToString("R")
                    + ", got " + actual.ToString("R"));
            }
        }

        /// <summary>
        /// The single BC-P2-9 comparison: expected stays the author's
        /// literal, and only the Unity colour-representation round-trip is
        /// absorbed, per component.
        /// </summary>
        static void CompareColor(
            System.Collections.Generic.List<string> differences,
            string label,
            float expected,
            float actual)
        {
            float error = Math.Abs(expected - actual);
            if (error <= ColorComponentTolerance
                && !float.IsNaN(actual)
                && !float.IsNaN(expected))
            {
                return;
            }
            differences.Add(
                label + ": expected " + expected.ToString("R")
                + ", got " + actual.ToString("R")
                + " (|error| " + error.ToString("R") + " > "
                + ColorComponentTolerance.ToString("R") + ")");
        }

        static void CompareVec3(
            System.Collections.Generic.List<string> differences,
            string label,
            Scene006Evaluation.Vec3 expected,
            Scene006Evaluation.Vec3 actual)
        {
            if (actual == null)
            {
                differences.Add(label + ": missing");
                return;
            }
            CompareFloat(differences, label + ".x", expected.x, actual.x);
            CompareFloat(differences, label + ".y", expected.y, actual.y);
            CompareFloat(differences, label + ".z", expected.z, actual.z);
        }

        static void CompareRotation(
            System.Collections.Generic.List<string> differences,
            string label,
            Scene006ProbeRenderer.Vec4 expected,
            Scene006ProbeRenderer.Vec4 actual)
        {
            if (actual == null)
            {
                differences.Add(label + ": missing");
                return;
            }
            CompareFloat(differences, label + ".x", expected.x, actual.x);
            CompareFloat(differences, label + ".y", expected.y, actual.y);
            CompareFloat(differences, label + ".z", expected.z, actual.z);
            CompareFloat(differences, label + ".w", expected.w, actual.w);
        }

        static Scene006Evaluation.Vec3 Vec3(float x, float y, float z) =>
            new Scene006Evaluation.Vec3 { x = x, y = y, z = z };

        static Scene006Evaluation.Vec3 Vec3(Vector3 value) =>
            new Scene006Evaluation.Vec3
            {
                x = value.x,
                y = value.y,
                z = value.z,
            };

        static Scene006ProbeRenderer.Vec4 Identity() =>
            new Scene006ProbeRenderer.Vec4 { x = 0f, y = 0f, z = 0f, w = 1f };

        static Scene006ProbeRenderer.Vec4 Rotation(Quaternion value) =>
            new Scene006ProbeRenderer.Vec4
            {
                x = value.x,
                y = value.y,
                z = value.z,
                w = value.w,
            };
    }
}
