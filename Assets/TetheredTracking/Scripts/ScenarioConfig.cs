using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace TetheredTracking
{
    [Serializable]
    public class ScenarioVector3
    {
        public float x;
        public float y;
        public float z;

        public Vector3 Value => new Vector3(x, y, z);

        public ScenarioVector3() { }

        public ScenarioVector3(float x, float y, float z)
        {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }

    [Serializable]
    public class ScenarioVector2
    {
        public float x;
        public float z;

        public Vector2 Value => new Vector2(x, z);

        public ScenarioVector2() { }

        public ScenarioVector2(float x, float z)
        {
            this.x = x;
            this.z = z;
        }
    }

    [Serializable]
    public class SensorScenarioConfig
    {
        public int width = 640;
        public int height = 480;
        public float vertical_fov_deg = 60f;
        public float capture_hz = 5f;
        public int jpeg_quality = 85;
        public int retained_frame_count = 128;
    }

    [Serializable]
    public class GimbalScenarioConfig
    {
        public float maximum_off_nadir_deg = 45f;
        public float slew_rate_deg_per_second = 120f;
    }

    /// <summary>
    /// P1-ENG-FRAME-001 Part T: operator-declared horizontal operating area
    /// in Unity world metres. Present = enforced; required when the tether
    /// is disabled (proposal section 3.1). NaN means "not set": a non-null
    /// geofence must carry four finite bounds or the scenario is refused.
    /// </summary>
    [Serializable]
    public class GeofenceScenarioConfig
    {
        public float min_x = float.NaN;
        public float max_x = float.NaN;
        public float min_z = float.NaN;
        public float max_z = float.NaN;
    }

    [Serializable]
    public class DroneScenarioConfig
    {
        public float initial_altitude_m = 25f;
        public float tether_length_m = 35f;
        public float minimum_altitude_m = 8f;
        public float maximum_altitude_m = 32f;
        public float maximum_speed_mps = 4f;
        public float maximum_acceleration_mps2 = 4f;
        // P1-ENG-FRAME-001 Part T (section 3.1). FromJsonStrict reads both
        // keys from the direct members of the root "drone" object: a missing
        // tether_enabled means "tether on" (the exact pre-existing
        // behaviour) and a missing geofence_xz_m means no geofence. Unity's
        // serializer cannot represent a null member, so the geofence is kept
        // out of JsonUtility ([NonSerialized]): neither JsonUtility.FromJson
        // nor a JsonUtility.ToJson round trip can produce a geofence, and an
        // explicitly written one is always validated.
        public bool tether_enabled = true;
        [NonSerialized] public GeofenceScenarioConfig geofence_xz_m;
    }

    [Serializable]
    public class TargetScenarioConfig
    {
        public string track_id = "target-0";
        public float speed_mps = 2f;
        public ScenarioVector3[] route_world_m;
    }

    [Serializable]
    public class EvaluationScenarioConfig
    {
        public float minimum_visible_sample_fraction = 0.2f;
        public float tracking_iou_threshold = 0.3f;
        public int maximum_pending_frame_count = 512;
    }

    [Serializable]
    public class VehicleRelocationScenarioConfig
    {
        public string prefab_name;
        public ScenarioVector2 original_xz_m;
        public float match_tolerance_m = 0.5f;
        public ScenarioVector3 new_position_m;
        public bool mark_as_distractor;
        public bool remove_from_scene;
    }

    [Serializable]
    public class RouteCorridorScenarioConfig
    {
        public float target_half_width_m = 1f;
        public float clearance_margin_m = 0.5f;
        public float target_bottom_offset_m = float.NaN;
        public float target_height_m = float.NaN;
        public float vertical_clearance_margin_m = float.NaN;
        public float road_sample_spacing_m = float.NaN;
        public bool enable_dynamic_intersection_audit;
        public bool enable_jump_diagnostic;
        public float jump_epsilon_m = float.NaN;
    }

    [Serializable]
    public class SceneAdjustmentsScenarioConfig
    {
        public VehicleRelocationScenarioConfig[] vehicle_relocations;
        public int expected_distractor_count;
        public RouteCorridorScenarioConfig route_corridor;
    }

    [Serializable]
    public class ScenarioConfig
    {
        public string schema_version = "tethered-scenario/v1";
        public string scenario_id = "deterministic-loop-default";
        public int random_seed;
        public ScenarioVector3 anchor_world_m;
        public DroneScenarioConfig drone;
        public GimbalScenarioConfig gimbal;
        public SensorScenarioConfig sensor;
        public TargetScenarioConfig target;
        public EvaluationScenarioConfig evaluation;
        public SceneAdjustmentsScenarioConfig scene_adjustments;
        public string road_data_sha256;

        [NonSerialized] public string source_path;

        public Vector3 Anchor => anchor_world_m.Value;

        /// <summary>
        /// P1-ENG-FRAME-001 section 3.11 entry 1: the versioned scenario
        /// <see cref="Load"/> falls back to when no runtime override exists.
        /// </summary>
        public static string VersionedDefaultPath =>
            RuntimePaths.ProjectFile("config", "scenario.untethered.json");

        public static ScenarioConfig Load()
        {
            string runtimeOverride = RuntimePaths.File("scenario_config.json");
            string projectDefault = VersionedDefaultPath;
            string path = File.Exists(runtimeOverride) ? runtimeOverride : projectDefault;
            ScenarioConfig config = null;

            if (File.Exists(path))
            {
                try { config = FromJsonStrict(File.ReadAllText(path)); }
                catch (Exception exception)
                {
                    throw new InvalidOperationException(
                        $"Could not load scenario config {path}: {exception.Message}",
                        exception);
                }
            }

            if (config == null) config = CreateDefault();
            config.source_path = File.Exists(path) ? path : "built-in defaults";
            config.Normalize();
            return config;
        }

        public static ScenarioConfig FromJsonStrict(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
                throw new InvalidOperationException("Scenario config JSON is required.");
            // Read before JsonUtility so an explicit section 3.1 value it
            // would coerce or choke on is refused with the contract's reason.
            TetherKeys tetherKeys = ReadTetherKeys(json);
            ScenarioConfig config = JsonUtility.FromJson<ScenarioConfig>(json);
            if (config == null)
                throw new InvalidOperationException("Scenario config JSON produced no document.");
            ApplyTetherKeyPresence(config, tetherKeys);
            if (json.IndexOf("\"scene_adjustments\"", StringComparison.Ordinal) >= 0)
            {
                RequireJsonField(json, "road_data_sha256");
                RequireJsonField(json, "target_bottom_offset_m");
                RequireJsonField(json, "target_height_m");
                RequireJsonField(json, "vertical_clearance_margin_m");
                RequireJsonField(json, "road_sample_spacing_m");
                RequireJsonField(json, "enable_dynamic_intersection_audit");
                RequireJsonField(json, "enable_jump_diagnostic");
                RequireJsonField(json, "jump_epsilon_m");
            }
            config.Normalize();
            return config;
        }

        public static ScenarioConfig CreateDefault()
        {
            return new ScenarioConfig
            {
                anchor_world_m = new ScenarioVector3(132f, 0.2f, 117f),
                drone = new DroneScenarioConfig(),
                gimbal = new GimbalScenarioConfig(),
                sensor = new SensorScenarioConfig(),
                evaluation = new EvaluationScenarioConfig(),
                target = new TargetScenarioConfig
                {
                    route_world_m = new[]
                    {
                        new ScenarioVector3(125.5f, 0.2f, 117.5f),
                        new ScenarioVector3(174.5f, 0.2f, 117.5f),
                        new ScenarioVector3(177.5f, 0.2f, 114.5f),
                        new ScenarioVector3(177.5f, 0.2f, 65.5f),
                        new ScenarioVector3(174.5f, 0.2f, 62.5f),
                        new ScenarioVector3(125.5f, 0.2f, 62.5f),
                        new ScenarioVector3(122.5f, 0.2f, 65.5f),
                        new ScenarioVector3(122.5f, 0.2f, 114.5f),
                    }
                }
            };
        }

        public Vector3[] TargetRoute()
        {
            var route = new Vector3[target.route_world_m.Length];
            for (int index = 0; index < route.Length; index++) route[index] = target.route_world_m[index].Value;
            return route;
        }

        internal void Normalize()
        {
            ScenarioConfig fallback = CreateDefault();
            if (schema_version != "tethered-scenario/v1")
                Debug.LogWarning($"Unknown scenario schema '{schema_version}', expected tethered-scenario/v1.");
            if (string.IsNullOrWhiteSpace(scenario_id)) scenario_id = fallback.scenario_id;
            if (anchor_world_m == null) anchor_world_m = fallback.anchor_world_m;
            if (drone == null) drone = fallback.drone;
            if (gimbal == null) gimbal = fallback.gimbal;
            if (sensor == null) sensor = fallback.sensor;
            if (target == null) target = fallback.target;
            if (evaluation == null) evaluation = fallback.evaluation;
            if (target.route_world_m == null || target.route_world_m.Length < 2)
                target.route_world_m = fallback.target.route_world_m;
            if (string.IsNullOrWhiteSpace(target.track_id)) target.track_id = fallback.target.track_id;
            anchor_world_m = FiniteVector(anchor_world_m, fallback.anchor_world_m);
            for (int index = 0; index < target.route_world_m.Length; index++)
            {
                ScenarioVector3 routeFallback = fallback.target.route_world_m[
                    index % fallback.target.route_world_m.Length];
                target.route_world_m[index] = FiniteVector(
                    target.route_world_m[index], routeFallback);
            }

            drone.tether_length_m = Positive(drone.tether_length_m, fallback.drone.tether_length_m);
            if (drone.tether_enabled)
            {
                drone.minimum_altitude_m = Mathf.Clamp(
                    Positive(drone.minimum_altitude_m, fallback.drone.minimum_altitude_m), 0.1f, drone.tether_length_m);
                drone.maximum_altitude_m = Mathf.Clamp(
                    Positive(drone.maximum_altitude_m, fallback.drone.maximum_altitude_m),
                    drone.minimum_altitude_m, drone.tether_length_m);
            }
            else
            {
                // Tether off: the altitude band is no longer capped by the
                // cable length (proposal section 3.2).
                drone.minimum_altitude_m = Mathf.Max(
                    0.1f, Positive(drone.minimum_altitude_m, fallback.drone.minimum_altitude_m));
                drone.maximum_altitude_m = Mathf.Max(
                    drone.minimum_altitude_m,
                    Positive(drone.maximum_altitude_m, fallback.drone.maximum_altitude_m));
            }
            drone.initial_altitude_m = Mathf.Clamp(
                Finite(drone.initial_altitude_m, fallback.drone.initial_altitude_m),
                drone.minimum_altitude_m, drone.maximum_altitude_m);
            drone.maximum_speed_mps = Positive(drone.maximum_speed_mps, fallback.drone.maximum_speed_mps);
            drone.maximum_acceleration_mps2 = Positive(
                drone.maximum_acceleration_mps2, fallback.drone.maximum_acceleration_mps2);

            gimbal.maximum_off_nadir_deg = Mathf.Clamp(
                Finite(gimbal.maximum_off_nadir_deg, fallback.gimbal.maximum_off_nadir_deg),
                0f, 89f);
            gimbal.slew_rate_deg_per_second = Positive(
                gimbal.slew_rate_deg_per_second, fallback.gimbal.slew_rate_deg_per_second);
            sensor.width = Mathf.Clamp(sensor.width, 64, 4096);
            sensor.height = Mathf.Clamp(sensor.height, 64, 4096);
            sensor.vertical_fov_deg = Mathf.Clamp(
                Finite(sensor.vertical_fov_deg, fallback.sensor.vertical_fov_deg),
                5f, 150f);
            sensor.capture_hz = Mathf.Clamp(
                Finite(sensor.capture_hz, fallback.sensor.capture_hz),
                0.1f, 60f);
            sensor.jpeg_quality = Mathf.Clamp(sensor.jpeg_quality, 1, 100);
            sensor.retained_frame_count = Mathf.Clamp(sensor.retained_frame_count, 4, 10000);
            target.speed_mps = Mathf.Max(
                0f, Finite(target.speed_mps, fallback.target.speed_mps));
            evaluation.minimum_visible_sample_fraction = Mathf.Clamp01(
                Finite(
                    evaluation.minimum_visible_sample_fraction,
                    fallback.evaluation.minimum_visible_sample_fraction));
            evaluation.tracking_iou_threshold = Mathf.Clamp01(
                Finite(
                    evaluation.tracking_iou_threshold,
                    fallback.evaluation.tracking_iou_threshold));
            evaluation.maximum_pending_frame_count = Mathf.Clamp(
                evaluation.maximum_pending_frame_count, 16, 100000);
            NormalizeGeofence();
            NormalizeSceneAdjustments();
        }

        /// <summary>
        /// P1-ENG-FRAME-001 section 3.1: a present geofence must be finite,
        /// ordered and contain home (the anchor x/z); with the tether off it
        /// is mandatory. Any violation refuses the scenario (fail closed).
        /// </summary>
        void NormalizeGeofence()
        {
            // null = absent (no key in the drone object). A non-null geofence
            // is never an "unset" placeholder: every bound must be finite.
            GeofenceScenarioConfig fence = drone.geofence_xz_m;
            if (fence == null)
            {
                if (!drone.tether_enabled)
                    throw new InvalidOperationException(
                        "drone.geofence_xz_m is required when drone.tether_enabled is false.");
                return;
            }
            RequireFinite(fence.min_x, "drone.geofence_xz_m.min_x");
            RequireFinite(fence.max_x, "drone.geofence_xz_m.max_x");
            RequireFinite(fence.min_z, "drone.geofence_xz_m.min_z");
            RequireFinite(fence.max_z, "drone.geofence_xz_m.max_z");
            if (!(fence.min_x < fence.max_x) || !(fence.min_z < fence.max_z))
                throw new InvalidOperationException(
                    "drone.geofence_xz_m must satisfy min < max on both axes.");
            Vector3 home = Anchor;
            if (home.x < fence.min_x || home.x > fence.max_x
                || home.z < fence.min_z || home.z > fence.max_z)
                throw new InvalidOperationException(
                    "drone.geofence_xz_m must contain the home (anchor_world_m) position.");
        }

        /// <summary>The section 3.1 keys as written in the drone object.</summary>
        struct TetherKeys
        {
            public bool? TetherEnabled;              // null = key missing
            public GeofenceScenarioConfig Geofence;  // null = key missing
        }

        /// <summary>
        /// Section 3.1 key presence: a missing <c>tether_enabled</c> means
        /// enabled and a missing <c>geofence_xz_m</c> means no geofence. Only
        /// the direct members of the root <c>drone</c> object count.
        /// </summary>
        static void ApplyTetherKeyPresence(ScenarioConfig config, TetherKeys keys)
        {
            if (config.drone == null) return;
            config.drone.tether_enabled = keys.TetherEnabled ?? true;
            config.drone.geofence_xz_m = keys.Geofence;
        }

        /// <summary>
        /// Reads <c>drone.tether_enabled</c> and <c>drone.geofence_xz_m</c>
        /// from the direct members of the root <c>drone</c> object, with the
        /// same verdicts as <c>controller/scenario_tether.py</c>: the switch
        /// must be a JSON boolean; a present geofence must be an object with
        /// all four bounds, each a finite JSON number. Range checks (min &lt;
        /// max, contains home) stay in <see cref="NormalizeGeofence"/>. A
        /// missing or non-object <c>drone</c> leaves both keys missing (the
        /// pre-existing Normalize fallback is unchanged).
        /// </summary>
        static TetherKeys ReadTetherKeys(string json)
        {
            var keys = new TetherKeys();
            List<JsonText.Member> root = JsonText.RootMembers(json);
            if (!JsonText.TryFindLast(root, "drone", out JsonText.Member drone)
                || json[drone.ValueStart] != '{')
                return keys;
            List<JsonText.Member> members = JsonText.ObjectMembers(json, drone.ValueStart);
            if (JsonText.TryFindLast(members, "tether_enabled", out JsonText.Member tether))
            {
                string token = JsonText.Token(json, tether);
                if (token == "true") keys.TetherEnabled = true;
                else if (token == "false") keys.TetherEnabled = false;
                else
                    throw new InvalidOperationException(
                        "drone.tether_enabled must be a JSON boolean.");
            }
            if (JsonText.TryFindLast(members, "geofence_xz_m", out JsonText.Member fence))
            {
                if (json[fence.ValueStart] != '{')
                    throw new InvalidOperationException(
                        "drone.geofence_xz_m must be an object.");
                List<JsonText.Member> bounds = JsonText.ObjectMembers(json, fence.ValueStart);
                keys.Geofence = new GeofenceScenarioConfig
                {
                    min_x = GeofenceBound(json, bounds, "min_x"),
                    max_x = GeofenceBound(json, bounds, "max_x"),
                    min_z = GeofenceBound(json, bounds, "min_z"),
                    max_z = GeofenceBound(json, bounds, "max_z"),
                };
            }
            return keys;
        }

        static readonly Regex JsonNumber = new Regex(
            @"^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$", RegexOptions.CultureInvariant);

        static float GeofenceBound(string json, List<JsonText.Member> bounds, string name)
        {
            string label = "drone.geofence_xz_m." + name;
            if (!JsonText.TryFindLast(bounds, name, out JsonText.Member bound))
                throw new InvalidOperationException(
                    $"drone.geofence_xz_m is missing '{name}'.");
            string token = JsonText.Token(json, bound);
            if (token == "NaN" || token == "Infinity" || token == "-Infinity")
                throw new InvalidOperationException(label + " must be finite.");
            if (!JsonNumber.IsMatch(token))
                throw new InvalidOperationException(label + " must be a number.");
            if (!double.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out double value)
                || double.IsNaN(value) || double.IsInfinity(value))
                throw new InvalidOperationException(label + " must be finite.");
            float result = (float)value;
            if (float.IsInfinity(result))
                throw new InvalidOperationException(label + " must be finite.");
            return result;
        }

        /// <summary>
        /// Minimal structural JSON reader for the section 3.1 keys. It walks
        /// strings (with escapes), objects, arrays and literal tokens only to
        /// list the direct members of an object, so a key name that appears
        /// in another object or inside a string is never taken for a drone
        /// key. Malformed structure is refused.
        /// </summary>
        static class JsonText
        {
            internal struct Member
            {
                internal string Name;
                internal int ValueStart;
                internal int ValueEnd;
            }

            internal static List<Member> RootMembers(string json)
            {
                int index = SkipWhitespace(json, 0);
                if (index >= json.Length || json[index] != '{') throw Malformed(index);
                List<Member> members = ReadObject(json, ref index);
                if (SkipWhitespace(json, index) != json.Length) throw Malformed(index);
                return members;
            }

            internal static List<Member> ObjectMembers(string json, int start)
            {
                int index = start;
                return ReadObject(json, ref index);
            }

            internal static bool TryFindLast(List<Member> members, string name, out Member found)
            {
                for (int index = members.Count - 1; index >= 0; index--)
                {
                    if (members[index].Name == name)
                    {
                        found = members[index];
                        return true;
                    }
                }
                found = default;
                return false;
            }

            internal static string Token(string json, Member member) =>
                json.Substring(member.ValueStart, member.ValueEnd - member.ValueStart);

            static List<Member> ReadObject(string json, ref int index)
            {
                var members = new List<Member>();
                index = SkipWhitespace(json, index + 1);
                if (index < json.Length && json[index] == '}')
                {
                    index++;
                    return members;
                }
                while (true)
                {
                    if (index >= json.Length || json[index] != '"') throw Malformed(index);
                    string name = ReadString(json, ref index);
                    index = SkipWhitespace(json, index);
                    if (index >= json.Length || json[index] != ':') throw Malformed(index);
                    index = SkipWhitespace(json, index + 1);
                    int start = index;
                    SkipValue(json, ref index);
                    members.Add(new Member { Name = name, ValueStart = start, ValueEnd = index });
                    index = SkipWhitespace(json, index);
                    if (index < json.Length && json[index] == ',')
                    {
                        index = SkipWhitespace(json, index + 1);
                        continue;
                    }
                    if (index < json.Length && json[index] == '}')
                    {
                        index++;
                        return members;
                    }
                    throw Malformed(index);
                }
            }

            static void SkipValue(string json, ref int index)
            {
                if (index >= json.Length) throw Malformed(index);
                char first = json[index];
                if (first == '{')
                {
                    ReadObject(json, ref index);
                    return;
                }
                if (first == '[')
                {
                    index = SkipWhitespace(json, index + 1);
                    if (index < json.Length && json[index] == ']')
                    {
                        index++;
                        return;
                    }
                    while (true)
                    {
                        SkipValue(json, ref index);
                        index = SkipWhitespace(json, index);
                        if (index < json.Length && json[index] == ',')
                        {
                            index = SkipWhitespace(json, index + 1);
                            continue;
                        }
                        if (index < json.Length && json[index] == ']')
                        {
                            index++;
                            return;
                        }
                        throw Malformed(index);
                    }
                }
                if (first == '"')
                {
                    ReadString(json, ref index);
                    return;
                }
                int tokenStart = index;
                while (index < json.Length && !IsDelimiter(json[index])) index++;
                if (index == tokenStart) throw Malformed(index);
            }

            static string ReadString(string json, ref int index)
            {
                var text = new StringBuilder();
                index++;
                while (index < json.Length)
                {
                    char character = json[index++];
                    if (character == '"') return text.ToString();
                    if (character != '\\')
                    {
                        text.Append(character);
                        continue;
                    }
                    if (index >= json.Length) break;
                    char escape = json[index++];
                    switch (escape)
                    {
                        case '"': case '\\': case '/': text.Append(escape); break;
                        case 'b': text.Append('\b'); break;
                        case 'f': text.Append('\f'); break;
                        case 'n': text.Append('\n'); break;
                        case 'r': text.Append('\r'); break;
                        case 't': text.Append('\t'); break;
                        case 'u':
                            if (index + 4 > json.Length
                                || !int.TryParse(
                                    json.Substring(index, 4), NumberStyles.AllowHexSpecifier,
                                    CultureInfo.InvariantCulture, out int code))
                                throw Malformed(index);
                            text.Append((char)code);
                            index += 4;
                            break;
                        default:
                            throw Malformed(index - 1);
                    }
                }
                throw Malformed(index);
            }

            static int SkipWhitespace(string json, int index)
            {
                while (index < json.Length && IsWhitespace(json[index])) index++;
                return index;
            }

            static bool IsWhitespace(char character) =>
                character == ' ' || character == '\t' || character == '\n'
                || character == '\r' || character == '﻿';

            static bool IsDelimiter(char character) =>
                IsWhitespace(character) || character == ',' || character == ':'
                || character == '{' || character == '}' || character == '['
                || character == ']' || character == '"';

            static InvalidOperationException Malformed(int index) =>
                new InvalidOperationException(
                    $"Scenario config JSON is malformed near character {index}.");
        }

        void NormalizeSceneAdjustments()
        {
            if (scene_adjustments == null) return;
            if (scene_adjustments.vehicle_relocations == null)
                throw new InvalidOperationException(
                    "scene_adjustments.vehicle_relocations is required.");
            if (scene_adjustments.route_corridor == null)
                throw new InvalidOperationException(
                    "scene_adjustments.route_corridor is required.");
            if (scene_adjustments.expected_distractor_count < 0)
                throw new InvalidOperationException(
                    "scene_adjustments.expected_distractor_count must be non-negative.");
            RequirePositiveFinite(
                scene_adjustments.route_corridor.target_half_width_m,
                "scene_adjustments.route_corridor.target_half_width_m");
            RequireNonNegativeFinite(
                scene_adjustments.route_corridor.clearance_margin_m,
                "scene_adjustments.route_corridor.clearance_margin_m");
            RequireFinite(
                scene_adjustments.route_corridor.target_bottom_offset_m,
                "scene_adjustments.route_corridor.target_bottom_offset_m");
            RequirePositiveFinite(
                scene_adjustments.route_corridor.target_height_m,
                "scene_adjustments.route_corridor.target_height_m");
            RequireNonNegativeFinite(
                scene_adjustments.route_corridor.vertical_clearance_margin_m,
                "scene_adjustments.route_corridor.vertical_clearance_margin_m");
            RequirePositiveFinite(
                scene_adjustments.route_corridor.road_sample_spacing_m,
                "scene_adjustments.route_corridor.road_sample_spacing_m");
            RequireNonNegativeFinite(
                scene_adjustments.route_corridor.jump_epsilon_m,
                "scene_adjustments.route_corridor.jump_epsilon_m");
            if (!RateStudyProtocol.IsSha256(road_data_sha256))
                throw new InvalidOperationException(
                    "road_data_sha256 must be a lowercase SHA-256 digest.");

            var keys = new HashSet<string>(StringComparer.Ordinal);
            foreach (VehicleRelocationScenarioConfig relocation
                in scene_adjustments.vehicle_relocations)
            {
                if (relocation == null)
                    throw new InvalidOperationException(
                        "scene_adjustments.vehicle_relocations must not contain null.");
                if (string.IsNullOrWhiteSpace(relocation.prefab_name))
                    throw new InvalidOperationException(
                        "vehicle relocation prefab_name is required.");
                relocation.prefab_name = relocation.prefab_name.Trim();
                if (relocation.original_xz_m == null)
                    throw new InvalidOperationException(
                        $"vehicle relocation '{relocation.prefab_name}' needs original_xz_m.");
                if (!relocation.remove_from_scene
                    && relocation.new_position_m == null)
                    throw new InvalidOperationException(
                        $"vehicle relocation '{relocation.prefab_name}' needs new_position_m.");
                if (relocation.remove_from_scene && relocation.mark_as_distractor)
                    throw new InvalidOperationException(
                        $"removed vehicle '{relocation.prefab_name}' cannot be a distractor.");
                RequireFinite(
                    relocation.original_xz_m.x,
                    $"vehicle relocation '{relocation.prefab_name}' original_xz_m.x");
                RequireFinite(
                    relocation.original_xz_m.z,
                    $"vehicle relocation '{relocation.prefab_name}' original_xz_m.z");
                RequirePositiveFinite(
                    relocation.match_tolerance_m,
                    $"vehicle relocation '{relocation.prefab_name}' match_tolerance_m");
                if (!relocation.remove_from_scene)
                {
                    RequireFiniteVector(
                        relocation.new_position_m,
                        $"vehicle relocation '{relocation.prefab_name}' new_position_m");
                }
                string key = relocation.prefab_name + "\n"
                    + relocation.original_xz_m.x.ToString(
                        "R", CultureInfo.InvariantCulture) + "\n"
                    + relocation.original_xz_m.z.ToString(
                        "R", CultureInfo.InvariantCulture);
                if (!keys.Add(key))
                    throw new InvalidOperationException(
                        $"duplicate vehicle relocation key for '{relocation.prefab_name}'.");
            }
        }

        static ScenarioVector3 FiniteVector(ScenarioVector3 value, ScenarioVector3 fallback)
        {
            if (value == null)
                return new ScenarioVector3(fallback.x, fallback.y, fallback.z);
            value.x = Finite(value.x, fallback.x);
            value.y = Finite(value.y, fallback.y);
            value.z = Finite(value.z, fallback.z);
            return value;
        }

        static float Finite(float value, float fallback)
        {
            return float.IsNaN(value) || float.IsInfinity(value) ? fallback : value;
        }

        static float Positive(float value, float fallback)
        {
            value = Finite(value, fallback);
            return value <= 0f ? fallback : value;
        }

        static void RequireFinite(float value, string label)
        {
            if (float.IsNaN(value) || float.IsInfinity(value))
                throw new InvalidOperationException(label + " must be finite.");
        }

        static void RequirePositiveFinite(float value, string label)
        {
            RequireFinite(value, label);
            if (value <= 0f)
                throw new InvalidOperationException(label + " must be positive.");
        }

        static void RequireNonNegativeFinite(float value, string label)
        {
            RequireFinite(value, label);
            if (value < 0f)
                throw new InvalidOperationException(label + " must be non-negative.");
        }

        static void RequireFiniteVector(ScenarioVector3 value, string label)
        {
            RequireFinite(value.x, label + ".x");
            RequireFinite(value.y, label + ".y");
            RequireFinite(value.z, label + ".z");
        }

        static void RequireJsonField(string json, string name)
        {
            if (json.IndexOf("\"" + name + "\"", StringComparison.Ordinal) < 0)
                throw new InvalidOperationException(
                    $"Scenario config is missing required field '{name}'.");
        }
    }
}
