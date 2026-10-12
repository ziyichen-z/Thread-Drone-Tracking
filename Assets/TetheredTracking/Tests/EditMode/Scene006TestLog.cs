using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.TestTools;

namespace TetheredTracking.Tests
{
    /// <summary>
    /// Shared Edit-Mode log policy for tests that build the target visual.
    /// </summary>
    internal static class Scene006TestLog
    {
        /// <summary>
        /// The one known message: Unity answers the §3.1.1 frozen
        /// `renderer.material` getter with a `LogType.Error` outside play
        /// mode. It is informational for this tool — the instanced material
        /// belongs to a `DontSave` object that the rig destroys in
        /// `Cleanup`, the batch runs never save the scene, and the §5.6
        /// before/after scene-file hash proves nothing reached the scene
        /// file.
        /// </summary>
        internal static readonly Regex MaterialInstantiation = new Regex(
            @"^Instantiating material due to calling renderer\.material "
            + @"during edit mode\.");

        /// <summary>
        /// BC-P2-11: expect that message exactly as often as the test builds
        /// a cube, and nothing else. This is deliberately not a blanket
        /// `LogAssert.ignoreFailingMessages` — an unexpected error still
        /// fails the test, and a missing expectation fails it too, so the
        /// count itself is pinned.
        /// </summary>
        /// <param name="cubeCount">
        /// Cubes the test is about to construct; each one touches
        /// `renderer.material` once. A target visual is two cubes.
        /// </param>
        internal static void ExpectMaterialInstantiation(int cubeCount = 2)
        {
            for (int index = 0; index < cubeCount; index++)
                LogAssert.Expect(LogType.Error, MaterialInstantiation);
        }
    }
}
