using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// Builds invisible physics proxies for scene meshes so evaluator raycasts
    /// match rendered city geometry without modifying third-party prefabs.
    /// Runtime actor roots are supplied explicitly and never become occluders.
    /// </summary>
    public sealed class EvaluationOcclusionGeometry : MonoBehaviour
    {
        public const string LayerName = "EvaluationOccluder";
        const string ProxyName = "__EvaluationMeshCollider";

        readonly List<GameObject> proxies = new();
        bool built;

        public int CandidateRendererCount { get; private set; }
        public int ProxyColliderCount { get; private set; }
        public int ExistingColliderCount { get; private set; }
        public int FailedProxyCount { get; private set; }
        public int ExcludedRendererCount { get; private set; }
        public int OcclusionLayer { get; private set; }
        public bool UsedDefaultLayerFallback { get; private set; }

        public void Build(params Transform[] excludedRoots)
        {
            BuildFromRenderers(
                FindObjectsByType<MeshRenderer>(FindObjectsInactive.Exclude),
                excludedRoots);
        }

        internal void BuildFromRenderers(
            IEnumerable<MeshRenderer> renderers,
            params Transform[] excludedRoots)
        {
            if (built) return;
            if (renderers == null)
                throw new ArgumentNullException(nameof(renderers));
            if (excludedRoots == null || excludedRoots.Length == 0)
                throw new ArgumentException(
                    "At least one runtime actor root must be excluded.", nameof(excludedRoots));
            foreach (Transform root in excludedRoots)
            {
                if (root == null)
                    throw new ArgumentException(
                        "Runtime actor exclusion roots must not contain null.", nameof(excludedRoots));
            }
            built = true;

            int evaluationLayer = LayerMask.NameToLayer(LayerName);
            if (evaluationLayer < 0)
            {
                evaluationLayer = 0;
                UsedDefaultLayerFallback = true;
                Debug.LogWarning(
                    $"Unity has not loaded layer '{LayerName}' in this editor session; "
                    + "evaluator proxies will use Default until the next editor restart.");
            }
            OcclusionLayer = evaluationLayer;

            foreach (MeshRenderer renderer in renderers)
            {
                if (renderer == null || !renderer.enabled) continue;
                if (IsExcluded(renderer.transform, excludedRoots))
                {
                    ExcludedRendererCount++;
                    continue;
                }
                MeshFilter filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null) continue;
                CandidateRendererCount++;

                if (HasUsableCollider(renderer.gameObject))
                {
                    ExistingColliderCount++;
                    continue;
                }

                GameObject proxy = null;
                try
                {
                    proxy = new GameObject(ProxyName)
                    {
                        layer = evaluationLayer,
                        hideFlags = HideFlags.DontSave,
                    };
                    proxy.transform.SetParent(renderer.transform, false);
                    MeshCollider collider = proxy.AddComponent<MeshCollider>();
                    collider.sharedMesh = filter.sharedMesh;
                    collider.convex = false;
                    if (collider.sharedMesh == null)
                        throw new InvalidOperationException("Unity rejected the shared collision mesh.");

                    proxies.Add(proxy);
                    ProxyColliderCount++;
                }
                catch (Exception exception)
                {
                    FailedProxyCount++;
                    if (proxy != null) Destroy(proxy);
                    Debug.LogWarning(
                        $"Could not create evaluator occlusion proxy for '{renderer.name}': "
                        + exception.Message);
                }
            }

            Physics.SyncTransforms();
            Debug.Log(
                $"Evaluation occlusion geometry ready: {ProxyColliderCount} mesh proxies, "
                + $"{ExistingColliderCount} existing colliders, {FailedProxyCount} failures "
                + $"from {CandidateRendererCount} candidate renderers; "
                + $"{ExcludedRendererCount} runtime renderers excluded; layer "
                + $"{OcclusionLayer}{(UsedDefaultLayerFallback ? " (Default fallback)" : "")}.");
        }

        static bool IsExcluded(Transform candidate, Transform[] roots)
        {
            foreach (Transform root in roots)
            {
                if (candidate == root || candidate.IsChildOf(root)) return true;
            }
            return false;
        }

        static bool HasUsableCollider(GameObject source)
        {
            Collider[] colliders = source.GetComponents<Collider>();
            foreach (Collider collider in colliders)
            {
                if (collider != null && collider.enabled && !collider.isTrigger) return true;
            }
            return false;
        }

        void OnDestroy()
        {
            foreach (GameObject proxy in proxies)
            {
                if (proxy == null) continue;
                if (Application.isPlaying) Destroy(proxy);
                else DestroyImmediate(proxy);
            }
            proxies.Clear();
        }
    }
}
