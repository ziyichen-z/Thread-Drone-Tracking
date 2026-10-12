using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace TetheredTracking
{
    [Serializable]
    public sealed class P1M3BodyObstacleInstance
    {
        public string scene_object_name;
        public string canonical_name;
        public string group;
        public string classification;
        public float min_x_m;
        public float max_x_m;
        public float min_y_m;
        public float max_y_m;
        public float min_z_m;
        public float max_z_m;
    }

    [Serializable]
    public sealed class P1M3BodySceneGeometryArtifact
    {
        public const string Schema = "p1-m3-body-001-scene-geometry/v1";

        public string schema_version = Schema;
        public string work_id = P1M3BodyAnchorPlacementContract.WorkId;
        public string scene_path;
        public string source_scenario_id;
        public string source_scenario_sha256;
        public string road_data_sha256;
        public bool scene_adjustments_applied;
        public int relocated_vehicle_count;
        public int scene_root_count;
        public int road_surface_root_count;
        public int instance_count;
        // Independent cross-check: the road audit's own count for this
        // scenario, produced in the same traversal, so the published basis
        // certifies itself instead of being asserted against a literal from
        // another scenario's artifact.
        public int road_audit_obstacle_count;
        public string road_audit_status;
        public P1M3BodyObstacleInstance[] instances;
    }

    /// <summary>
    /// P1-M3-BODY-001 batch 1a-alpha: the single scene traversal both offline
    /// consumers derive from.
    ///
    /// It publishes the world-frame axis-aligned prism of every scene
    /// obstacle instance on the <b>road-audit basis</b> - every active
    /// renderable root whose canonical prefab name is not a road surface -
    /// which is the "782 instance set" BC-BODY1-4 names. Prisms come from the
    /// <c>road_data.json</c> footprints transformed by each root's TRS, the
    /// same construction <see cref="P1Scene003AnchorAuditor"/> and
    /// <see cref="RoadSceneAuditor"/> use, so the three cannot drift apart. A
    /// root with no footprint classification throws, exactly as the road
    /// audit does, so the published basis is provably the audited one.
    ///
    /// Why this artifact is separate from the frozen corridor prism config:
    /// BC-BODY1-4 forbids any visibility/occlusion prediction, estimator or
    /// measurement-window logic from reading the corridor artifact during
    /// batch 1. Tool 2 computes exactly such things (the C_geom occlusion
    /// bound and the visible-arc measurement window), so it reads this
    /// evidence artifact and never the corridor config; the corridor config
    /// is derived from this file offline by `tools/build_m3_corridor.py` and
    /// is the only static geometry the runtime side will ever load.
    /// </summary>
    public static class P1M3BodySceneGeometry
    {
        public static P1M3BodySceneGeometryArtifact Build(
            ScenarioConfig scenario,
            string scenarioSha256,
            RoadSceneData roadData,
            IEnumerable<Transform> sceneRoots,
            string scenePath,
            bool sceneAdjustmentsApplied,
            int relocatedVehicleCount,
            RoadSceneAuditReport roadAudit)
        {
            if (scenario == null) throw new ArgumentNullException(nameof(scenario));
            if (roadData == null) throw new ArgumentNullException(nameof(roadData));
            if (sceneRoots == null) throw new ArgumentNullException(nameof(sceneRoots));
            if (!RateStudyProtocol.IsSha256(scenarioSha256))
                throw new InvalidOperationException(
                    "scene geometry inputs need a lowercase SHA-256 identity");
            roadData.Validate();

            Transform[] roots = sceneRoots
                .Where(root => root != null && root.gameObject.activeInHierarchy)
                .OrderBy(root => root.name, StringComparer.Ordinal)
                .ToArray();
            var roadNames = new HashSet<string>(
                roadData.road_surface_allowlist,
                StringComparer.Ordinal);
            Dictionary<string, RoadObstacleFootprint> footprints =
                roadData.obstacle_footprints.ToDictionary(
                    item => item.canonical_name,
                    StringComparer.Ordinal);

            var instances = new List<P1M3BodyObstacleInstance>();
            int roadRoots = 0;
            foreach (Transform root in roots)
            {
                string canonical =
                    SceneVehicleAdjustmentApplier.CanonicalPrefabName(root.name);
                if (roadNames.Contains(canonical))
                {
                    roadRoots++;
                    continue;
                }
                if (!footprints.TryGetValue(
                    canonical,
                    out RoadObstacleFootprint footprint))
                {
                    throw new InvalidOperationException(
                        "Road data has no classification/footprint for active "
                        + $"renderer root '{root.name}' (canonical "
                        + $"'{canonical}'); the published basis would not be "
                        + "the audited one.");
                }
                P1Scene003AnchorAuditor.Footprint transformed =
                    P1Scene003AnchorAuditor.TransformFootprint(root, footprint);
                // Pitch and roll are inadmissible (RequireSupportedTransform),
                // so the four ground corners already carry the exact world XZ
                // extent and the eight-corner sweep carries the Y extent.
                instances.Add(new P1M3BodyObstacleInstance
                {
                    scene_object_name = root.name,
                    canonical_name = canonical,
                    group = footprint.group,
                    classification = footprint.classification,
                    min_x_m = transformed.Corners.Min(item => item.x),
                    max_x_m = transformed.Corners.Max(item => item.x),
                    min_y_m = transformed.MinY,
                    max_y_m = transformed.MaxY,
                    min_z_m = transformed.Corners.Min(item => item.y),
                    max_z_m = transformed.Corners.Max(item => item.y),
                });
            }
            instances.Sort((left, right) => string.CompareOrdinal(
                left.scene_object_name,
                right.scene_object_name));

            return new P1M3BodySceneGeometryArtifact
            {
                scene_path = scenePath,
                source_scenario_id = scenario.scenario_id,
                source_scenario_sha256 = scenarioSha256,
                road_data_sha256 = scenario.road_data_sha256,
                scene_adjustments_applied = sceneAdjustmentsApplied,
                relocated_vehicle_count = relocatedVehicleCount,
                scene_root_count = roots.Length,
                road_surface_root_count = roadRoots,
                instance_count = instances.Count,
                road_audit_obstacle_count =
                    roadAudit?.audited_obstacle_count ?? -1,
                road_audit_status = roadAudit?.status ?? "",
                instances = instances.ToArray(),
            };
        }
    }
}
