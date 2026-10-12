using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// P1-SCENE-006 T1′ parity redirection §3.1 (R17): the <b>single
    /// production construction source</b> for the target vehicle visual.
    ///
    /// F23 recorded that the offline probe rendered an unpainted grey
    /// replica while the runtime target is painted red, so the probe recall
    /// and the Play-mode detector baselines were not on a common scale.
    /// Both construction sites now delegate here, so geometry *and*
    /// appearance are defined exactly once:
    ///
    /// * runtime — <see cref="TetheredScenarioBootstrap"/>.AddCarVisual;
    /// * offline probe — `Scene006SceneRig.CreateTargetReplica`.
    ///
    /// The colour, size and position literals below are the definition of
    /// the object `P1-DETECT-001` scout-4 and qual-3 measured; they are
    /// frozen and must not be edited. Independent expected copies live in
    /// the versioned oracles (§3.1.4a): the factory-contract EditMode test,
    /// the rig-entry EditMode test, `Scene006AppearanceContract` and the
    /// analyzer's Python constant block. None of them reads back from this
    /// class, so changing a literal here without changing every oracle
    /// fails the suite.
    ///
    /// The factory builds and paints only. Collider removal, `hideFlags`
    /// and any parent/root naming belong to the consumer (§3.1.2); those
    /// three are the exhaustive list of permitted consumer differences.
    /// </summary>
    public static class TargetVisualFactory
    {
        public static readonly Color BodyColor = new Color(0.9f, 0.12f, 0.1f);
        public static readonly Color RoofColor = new Color(0.65f, 0.08f, 0.07f);

        /// <summary>
        /// Everything the two consumers need to finish their own bookkeeping:
        /// the two created objects, their renderers and the primitive
        /// colliders the factory deliberately leaves in place.
        /// </summary>
        public readonly struct Build
        {
            public readonly GameObject Body;
            public readonly GameObject Roof;
            public readonly Renderer BodyRenderer;
            public readonly Renderer RoofRenderer;
            public readonly Collider BodyCollider;
            public readonly Collider RoofCollider;

            public Build(
                GameObject body, GameObject roof,
                Renderer bodyRenderer, Renderer roofRenderer,
                Collider bodyCollider, Collider roofCollider)
            {
                Body = body;
                Roof = roof;
                BodyRenderer = bodyRenderer;
                RoofRenderer = roofRenderer;
                BodyCollider = bodyCollider;
                RoofCollider = roofCollider;
            }
        }

        /// <summary>
        /// Creates the body and roof cubes under <paramref name="parent"/>
        /// and paints them. Local TRS is written explicitly after
        /// `SetParent(parent, false)`, so the result does not depend on the
        /// parent's transform or on which `SetParent` overload the caller
        /// would have used.
        /// </summary>
        public static Build AddTargetVisual(Transform parent)
        {
            GameObject body = AddCube(
                parent,
                new Vector3(0f, 0.5f, 0f),
                new Vector3(2f, 1f, 4f),
                BodyColor);
            GameObject roof = AddCube(
                parent,
                new Vector3(0f, 1.2f, -0.2f),
                new Vector3(1.7f, 0.7f, 2f),
                RoofColor);
            return new Build(
                body,
                roof,
                body.GetComponent<Renderer>(),
                roof.GetComponent<Renderer>(),
                body.GetComponent<Collider>(),
                roof.GetComponent<Collider>());
        }

        static GameObject AddCube(
            Transform parent,
            Vector3 localPosition,
            Vector3 localScale,
            Color color)
        {
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.SetParent(parent, false);
            cube.transform.localPosition = localPosition;
            cube.transform.localRotation = Quaternion.identity;
            cube.transform.localScale = localScale;
            cube.GetComponent<Renderer>().material.color = color;
            return cube;
        }
    }
}
