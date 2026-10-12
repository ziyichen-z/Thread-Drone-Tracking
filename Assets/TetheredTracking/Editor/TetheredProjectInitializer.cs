using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;

namespace TetheredTracking.Editor
{
    [InitializeOnLoad]
    public static class TetheredProjectInitializer
    {
        public const string ScenePath =
            "Assets/SimplePoly City - Low Poly Assets/Demo/"
            + "SimplePoly City - Low Poly Assets_Demo Scene.unity";

        static TetheredProjectInitializer()
        {
            EditorApplication.delayCall += OpenSceneOnFirstImport;
        }

        static void OpenSceneOnFirstImport()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            Scene active = SceneManager.GetActiveScene();
            if (active.path == ScenePath || active.isDirty) return;
            if (!string.IsNullOrEmpty(active.path)) return;
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }

        [MenuItem("Tethered Tracking/Open City Scenario")]
        public static void OpenScene()
        {
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        }
    }
}
