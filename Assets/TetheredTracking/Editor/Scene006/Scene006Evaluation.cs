using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 batch-1 offline evaluation orchestrator: T1 (min(w,h)
    /// resource gate), T2/T3 (frustum/occlusion loss decomposition), T4
    /// (station pre-screen with §5.4 certificates) and T6 (initialization
    /// acquisition scan) over the §5.2 frozen common evaluation domain.
    ///
    /// Domain (§5.2): 541-state trace s_0..s_540 with dt = 0.2 s; coverage
    /// denominators are exactly s_1..s_540 (540 samples, equal weight);
    /// s_0 serves only T6 and the T1' prompt. T1/T2/T3 are evaluated at
    /// p_hover; T4 enumerates the station set with an independent gimbal
    /// replay per station from the frozen initial quaternion; T6 scans
    /// k in [0, 10] at p_hover. Every interval gate is closed-interval.
    ///
    /// All truth-derived values live only in the evaluation artifact; they
    /// never become controller or WorldModel inputs.
    /// </summary>
    public static class Scene006Evaluation
    {
        public const float T1MinSideP05ThresholdPx = 25f;
        public const float T2LossMin = 0.10f;
        public const float T2LossMax = 0.50f;
        public const float T3OccLossMin = 0.05f;
        public const float T3OccLossMax = 0.40f;
        public const float T3TotalLossMin = 0.15f;
        public const float T3TotalLossMax = 0.60f;
        public const float T4GainMin = 0.05f;
        public const int T6AcquisitionWindow = 10;

        public sealed class Inputs
        {
            public string ScenarioId;
            public string ScenarioSha256;
            public string RoadDataSha256;
            public Vector3[] Route;
            public Scene006Trace.State[] Trace;
            public float SInit;
            public string TraceSha256;
            public int FirstLapSteps;
            public Vector3 Anchor;
            public float SupportY;
            public float HoverHeightM;
            public float VerticalFovDeg;
            public int ImageWidth;
            public int ImageHeight;
            public Transform TargetRoot;
            public Renderer[] TargetRenderers;
            public Camera Cam;
            public Scene006PathCertificate.ObstaclePrism[] Obstacles;
            public string SupportInstanceId;
            public Func<Vector3, Vector3, bool> LineOfSight;
        }

        [Serializable]
        public sealed class Vec3
        {
            public float x;
            public float y;
            public float z;
        }

        [Serializable]
        public sealed class SampleRecord
        {
            public int k;
            public float t_s;
            public int frustum_sample_count;
            public int visible_sample_count;
            public bool frustum_visible;
            public bool geometrically_visible;
            public float min_side_px;
            public float slant_m;
        }

        [Serializable]
        public sealed class T1Record
        {
            public int domain_count;
            public bool fidelity_contradiction;
            public float min_side_p05_px;
            public float min_side_median_px;
            public float min_side_min_px;
            public float min_side_max_px;
            public float gate_threshold_px = T1MinSideP05ThresholdPx;
            public string quantile_method = "type-7";
            public string gate;
        }

        [Serializable]
        public sealed class T2Record
        {
            public float c_frustum;
            public float l_point;
            public float interval_min = T2LossMin;
            public float interval_max = T2LossMax;
            public string gate;
        }

        [Serializable]
        public sealed class T3Record
        {
            public float c_geom;
            public float l_occ;
            public float total_loss;
            public float l_occ_min = T3OccLossMin;
            public float l_occ_max = T3OccLossMax;
            public float total_min = T3TotalLossMin;
            public float total_max = T3TotalLossMax;
            public string gate;
        }

        [Serializable]
        public sealed class CertificateRecord
        {
            public bool passed;
            public bool path_rejected;
            public bool body_rejected;
            public bool tether_rejected;
            public string blocking_obstacle;
            public float duration_s;
            public int sample_count;
        }

        [Serializable]
        public sealed class StationRecord
        {
            public int index;
            public float height_agl_m;
            public Vec3 world_m;
            public bool is_hover;
            public CertificateRecord certificate;
            public float c_station = float.NaN;
        }

        [Serializable]
        public sealed class T4Record
        {
            public float c_hold;
            public int station_count;
            public int certificate_pass_count;
            public int body_rejection_count;
            public int tether_rejection_count;
            public int path_rejection_count;
            public int best_station_index = -1;
            public float best_c_station = float.NaN;
            public float g_station = float.NaN;
            public float gate_threshold = T4GainMin;
            public string gate;
            public float trim_distance_m = Scene006PathCertificate.TrimDistanceM;
            public float min_tether_elevation_deg =
                Scene006PathCertificate.MinTetherElevationDeg;
            public string trim_note =
                "literal §5.4.4 (F2): the head segment [0, 1.70 m] of every "
                + "tether capsule queries all colliders and ignores only "
                + "the bound measured support instance; the remainder "
                + "ignores nothing (1.70 * sin(13.212980 deg) = 0.388571 "
                + ">= 0.375 discharges the support plane beyond the trim)";
            public StationRecord[] stations;
        }

        [Serializable]
        public sealed class T6SampleRecord
        {
            public int k;
            public bool frustum_visible;
            public bool geometrically_visible;
            public float min_side_px;
        }

        [Serializable]
        public sealed class T6Record
        {
            public int k_acq = T6AcquisitionWindow;
            public int k_star = -1;
            public float prompt_min_side_px = float.NaN;
            public float t1_domain_median_px = float.NaN;
            public string gate;
            public T6SampleRecord[] samples;
        }

        [Serializable]
        public sealed class BaselineReport
        {
            public string schema_version = "p1-scene-006-baseline/v1";
            public string work_id = "P1-SCENE-006";
            public int batch = 1;
            public string scenario_id;
            public string scenario_sha256;
            public string road_data_sha256;
            public float vertical_fov_deg;
            public int image_width;
            public int image_height;
            public Vec3 anchor_world_m;
            public float support_y_m;
            public float ground_plane_y_m = 0.2000004f;
            public float hover_height_m;
            public Vec3 p_hover_world_m;
            public float minimum_visible_sample_fraction =
                Scene006Visibility.VisibleFractionThreshold;
            public int visibility_sample_count = Scene006Visibility.SampleCount;
            public int coverage_samples = Scene006Trace.HorizonSteps;
            public float time_step_s = Scene006Trace.StepSeconds;
            public float s_init;
            public int trace_state_count;
            public int trace_first_lap_steps;
            public string trace_first_lap_status;
            public string trace_sha256;
            public T1Record t1;
            public T2Record t2;
            public T3Record t3;
            public T4Record t4;
            public T6Record t6;
            public SampleRecord[] samples;
        }

        static Vec3 ToVec3(Vector3 value) =>
            new Vec3 { x = value.x, y = value.y, z = value.z };

        public static BaselineReport Run(Inputs inputs)
        {
            if (inputs == null) throw new ArgumentNullException(nameof(inputs));
            if (inputs.Trace == null
                || inputs.Trace.Length != Scene006Trace.HorizonSteps + 1)
                throw new InvalidOperationException("trace must have 541 states");
            if (inputs.TargetRoot == null || inputs.Cam == null)
                throw new InvalidOperationException("rig actors are required");

            Vector3 pHover = Scene006StationSet.HoverPosition(
                inputs.Anchor, inputs.SupportY, inputs.HoverHeightM);

            var samples = new SampleRecord[inputs.Trace.Length];
            var memberMinSides = new List<float>();
            bool fidelity = false;
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            for (int k = 0; k < inputs.Trace.Length; k++)
            {
                Scene006Trace.State state = inputs.Trace[k];
                inputs.TargetRoot.SetPositionAndRotation(
                    state.Position, state.Rotation);
                if (k >= 1)
                {
                    gimbal = Scene006GimbalReplay.Update(
                        gimbal, pHover, state.Position);
                }
                inputs.Cam.transform.SetPositionAndRotation(pHover, gimbal);
                Snapshot snapshot = EvaluateAt(
                    inputs, out float minSide, out bool contradiction);
                fidelity |= contradiction;
                samples[k] = new SampleRecord
                {
                    k = k,
                    t_s = k * Scene006Trace.StepSeconds,
                    frustum_sample_count = snapshot.FrustumSampleCount,
                    visible_sample_count = snapshot.VisibleSampleCount,
                    frustum_visible = snapshot.FrustumVisible,
                    geometrically_visible = snapshot.GeometricallyVisible,
                    min_side_px = minSide,
                    slant_m = Vector3.Distance(pHover, state.Position),
                };
                // §5.2.3/§5.2.8: the T1 domain is s_1..s_540 frustum members.
                if (k >= 1 && snapshot.FrustumVisible && !contradiction)
                    memberMinSides.Add(minSide);
            }

            int frustumCount = 0;
            int visibleCount = 0;
            for (int k = 1; k < samples.Length; k++)
            {
                if (samples[k].frustum_visible) frustumCount++;
                if (samples[k].geometrically_visible) visibleCount++;
            }
            float cFrustum = frustumCount / 540f;
            float cGeom = visibleCount / 540f;

            T1Record t1 = BuildT1(memberMinSides, fidelity);
            var t2 = new T2Record
            {
                c_frustum = cFrustum,
                l_point = 1f - cFrustum,
                gate = Interval(1f - cFrustum, T2LossMin, T2LossMax)
                    ? "PASS" : "FAIL",
            };
            float lOcc = cFrustum - cGeom;
            float totalLoss = 1f - cGeom;
            var t3 = new T3Record
            {
                c_geom = cGeom,
                l_occ = lOcc,
                total_loss = totalLoss,
                gate = Interval(lOcc, T3OccLossMin, T3OccLossMax)
                    && Interval(totalLoss, T3TotalLossMin, T3TotalLossMax)
                    ? "PASS" : "FAIL",
            };
            T6Record t6 = BuildT6(samples, t1);
            T4Record t4 = BuildT4(inputs, pHover, cGeom);

            return new BaselineReport
            {
                scenario_id = inputs.ScenarioId,
                scenario_sha256 = inputs.ScenarioSha256,
                road_data_sha256 = inputs.RoadDataSha256,
                vertical_fov_deg = inputs.VerticalFovDeg,
                image_width = inputs.ImageWidth,
                image_height = inputs.ImageHeight,
                anchor_world_m = ToVec3(inputs.Anchor),
                support_y_m = inputs.SupportY,
                hover_height_m = inputs.HoverHeightM,
                p_hover_world_m = ToVec3(pHover),
                s_init = inputs.SInit,
                trace_state_count = inputs.Trace.Length,
                trace_first_lap_steps = inputs.FirstLapSteps,
                trace_first_lap_status = inputs.FirstLapSteps > 0
                    ? "MEASURED" : "HORIZON_SHORT",
                trace_sha256 = inputs.TraceSha256,
                t1 = t1,
                t2 = t2,
                t3 = t3,
                t4 = t4,
                t6 = t6,
                samples = samples,
            };
        }

        struct Snapshot
        {
            public int FrustumSampleCount;
            public int VisibleSampleCount;
            public bool FrustumVisible;
            public bool GeometricallyVisible;
        }

        static Snapshot EvaluateAt(
            Inputs inputs,
            out float minSide,
            out bool fidelityContradiction)
        {
            Bounds bounds = inputs.TargetRenderers[0].bounds;
            for (int index = 1; index < inputs.TargetRenderers.Length; index++)
                bounds.Encapsulate(inputs.TargetRenderers[index].bounds);
            Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
            Scene006Visibility.Snapshot snapshot = Scene006Visibility.Evaluate(
                inputs.Cam, bounds, corners, inputs.LineOfSight);
            NormalizedBoundingBox box = Scene006Visibility.ProjectBounds(
                inputs.Cam, corners);
            fidelityContradiction = snapshot.FrustumVisible && box == null;
            minSide = box == null
                ? float.NaN
                : Scene006Visibility.MinSidePx(
                    box, inputs.ImageWidth, inputs.ImageHeight);
            return new Snapshot
            {
                FrustumSampleCount = snapshot.FrustumSampleCount,
                VisibleSampleCount = snapshot.VisibleSampleCount,
                FrustumVisible = snapshot.FrustumVisible,
                GeometricallyVisible = snapshot.GeometricallyVisible,
            };
        }

        static T1Record BuildT1(List<float> memberMinSides, bool fidelity)
        {
            var t1 = new T1Record
            {
                domain_count = memberMinSides.Count,
                fidelity_contradiction = fidelity,
                min_side_p05_px = float.NaN,
                min_side_median_px = float.NaN,
                min_side_min_px = float.NaN,
                min_side_max_px = float.NaN,
            };
            if (fidelity)
            {
                t1.gate = "PROBE_FIDELITY_CONTRADICTION";
                return t1;
            }
            if (memberMinSides.Count == 0)
            {
                t1.gate = "FAIL";
                return t1;
            }
            t1.min_side_p05_px = (float)Scene006Visibility.QuantileType7(
                memberMinSides, 0.05);
            t1.min_side_median_px = (float)Scene006Visibility.QuantileType7(
                memberMinSides, 0.5);
            float min = float.PositiveInfinity;
            float max = float.NegativeInfinity;
            foreach (float value in memberMinSides)
            {
                min = Mathf.Min(min, value);
                max = Mathf.Max(max, value);
            }
            t1.min_side_min_px = min;
            t1.min_side_max_px = max;
            t1.gate = t1.min_side_p05_px >= T1MinSideP05ThresholdPx
                ? "PASS" : "FAIL";
            return t1;
        }

        static T6Record BuildT6(
            SampleRecord[] samples,
            T1Record t1)
        {
            var window = new T6SampleRecord[T6AcquisitionWindow + 1];
            int kStar = -1;
            for (int k = 0; k <= T6AcquisitionWindow; k++)
            {
                window[k] = new T6SampleRecord
                {
                    k = k,
                    frustum_visible = samples[k].frustum_visible,
                    geometrically_visible = samples[k].geometrically_visible,
                    min_side_px = samples[k].min_side_px,
                };
                if (kStar < 0 && samples[k].geometrically_visible) kStar = k;
            }
            var t6 = new T6Record
            {
                k_star = kStar,
                t1_domain_median_px = t1.min_side_median_px,
                samples = window,
            };
            if (kStar >= 0)
                t6.prompt_min_side_px = samples[kStar].min_side_px;
            bool promptSizeKnown = kStar >= 0
                && Scene006RouteGeometry.Finite(t6.prompt_min_side_px);
            if (kStar >= 0 && !promptSizeKnown)
            {
                // A V = 1 sample whose truth box does not project is the
                // §5.2.8 renderer/evaluator fidelity contradiction; it is a
                // named FAIL-class disposition, never a silent exclusion.
                t6.gate = "PROBE_FIDELITY_CONTRADICTION";
            }
            else
            {
                t6.gate = kStar >= 0
                    && promptSizeKnown
                    && t6.prompt_min_side_px >= t6.t1_domain_median_px
                    ? "PASS" : "FAIL";
            }
            return t6;
        }

        static T4Record BuildT4(Inputs inputs, Vector3 pHover, float cHold)
        {
            Scene006StationSet.Station[] stations = Scene006StationSet.Build(
                inputs.Anchor, inputs.SupportY, inputs.HoverHeightM);
            var records = new StationRecord[stations.Length];
            var t4 = new T4Record
            {
                c_hold = cHold,
                station_count = stations.Length,
                stations = records,
            };
            float bestC = float.NegativeInfinity;
            for (int index = 0; index < stations.Length; index++)
            {
                Scene006StationSet.Station station = stations[index];
                Scene006PathCertificate.Certificate certificate =
                    Scene006PathCertificate.Evaluate(
                        inputs.Anchor,
                        pHover,
                        inputs.SupportY,
                        station.World,
                        inputs.Obstacles,
                        inputs.SupportInstanceId);
                records[index] = new StationRecord
                {
                    index = index,
                    height_agl_m = station.HeightAglM,
                    world_m = ToVec3(station.World),
                    is_hover = station.IsHover,
                    certificate = new CertificateRecord
                    {
                        passed = certificate.Passed,
                        path_rejected = certificate.PathRejected,
                        body_rejected = certificate.BodyRejected,
                        tether_rejected = certificate.TetherRejected,
                        blocking_obstacle = certificate.BlockingObstacle,
                        duration_s = certificate.DurationSeconds,
                        sample_count = certificate.SampleCount,
                    },
                };
                if (certificate.BodyRejected) t4.body_rejection_count++;
                if (certificate.TetherRejected) t4.tether_rejection_count++;
                if (certificate.PathRejected) t4.path_rejection_count++;
                // §5.4.5: certificate failures never enter max_p.
                if (!certificate.Passed) continue;
                t4.certificate_pass_count++;
                float cStation = EvaluateCoverageAt(inputs, station.World);
                records[index].c_station = cStation;
                if (cStation > bestC)
                {
                    bestC = cStation;
                    t4.best_station_index = index;
                }
            }
            if (t4.best_station_index >= 0)
            {
                t4.best_c_station = bestC;
                t4.g_station = bestC - cHold;
            }
            t4.gate = t4.best_station_index >= 0
                && t4.g_station >= T4GainMin
                ? "PASS" : "FAIL";
            return t4;
        }

        /// <summary>
        /// C_station(p): an independent replay from the same trace and the
        /// frozen initial gimbal quaternion (§5.2.5); no gimbal state is
        /// inherited across stations.
        /// </summary>
        static float EvaluateCoverageAt(Inputs inputs, Vector3 bodyPosition)
        {
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            int visible = 0;
            for (int k = 1; k < inputs.Trace.Length; k++)
            {
                Scene006Trace.State state = inputs.Trace[k];
                inputs.TargetRoot.SetPositionAndRotation(
                    state.Position, state.Rotation);
                gimbal = Scene006GimbalReplay.Update(
                    gimbal, bodyPosition, state.Position);
                inputs.Cam.transform.SetPositionAndRotation(
                    bodyPosition, gimbal);
                Bounds bounds = inputs.TargetRenderers[0].bounds;
                for (int index = 1; index < inputs.TargetRenderers.Length; index++)
                    bounds.Encapsulate(inputs.TargetRenderers[index].bounds);
                Scene006Visibility.Snapshot snapshot =
                    Scene006Visibility.Evaluate(
                        inputs.Cam,
                        bounds,
                        Scene006Visibility.BoundsCorners(bounds),
                        inputs.LineOfSight);
                if (snapshot.GeometricallyVisible) visible++;
            }
            return visible / 540f;
        }

        static bool Interval(float value, float min, float max) =>
            value >= min && value <= max;
    }
}
