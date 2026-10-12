using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// Amendment-1 §5.3 P2 candidate cell evaluation: T1/T2/T3 only (T4/T6
    /// are authoritative in P3 and are NOT computed here), with per-tick
    /// occlusion attribution. The per-sample loop replicates
    /// Scene006Evaluation.Run exactly — same gimbal replay from the frozen
    /// initial quaternion, same 15-sample predicate (denominator 15,
    /// fraction &gt;= 0.2), same projection and type-7 quantiles — and
    /// additionally records, for every tick with at least one in-frustum
    /// occluded sample, the sorted scene-root names blocking that tick.
    ///
    /// Per-cell terminals: first-lap &gt; 540 is reported by the caller as
    /// HORIZON_SHORT (the trace is per-anchor); a T1-domain member whose
    /// truth box does not project is PROBE_FIDELITY_CONTRADICTION and the
    /// cell produces no gate values (BC-SC6-3).
    /// </summary>
    public static class Scene006CandidateEvaluation
    {
        public sealed class Inputs
        {
            public string Family;
            public Vector2 AnchorXz;
            public float SupportY;
            public float AltitudeM;
            public float VerticalFovDeg;
            public int ImageWidth;
            public int ImageHeight;
            public Vector3[] Route;
            public Scene006Trace.State[] Trace;
            public float SInit;
            public string TraceSha256;
            public string TraceArtifactPath;
            public int FirstLapSteps;
            public Transform TargetRoot;
            public Renderer[] TargetRenderers;
            public Camera Cam;
        }

        [Serializable]
        public sealed class OccludedTickRecord
        {
            public int k;
            public float t_s;
            public int frustum_sample_count;
            public int visible_sample_count;
            public string[] blocking_roots;
        }

        [Serializable]
        public sealed class CellRecord
        {
            public string family;
            public float anchor_x_m;
            public float anchor_z_m;
            public float support_y_m;
            public float initial_altitude_m;
            public float vertical_fov_deg;
            public float s_init;
            public string trace_sha256;
            public string trace_artifact;
            public int trace_first_lap_steps;
            public string terminal = "";
            public int t1_domain_count;
            public float t1_min_side_p05_px = float.NaN;
            public float t1_min_side_median_px = float.NaN;
            public float t1_min_side_min_px = float.NaN;
            public float t1_min_side_max_px = float.NaN;
            public float[] t1_domain_min_sides_px;
            public float c_frustum = float.NaN;
            public float l_point = float.NaN;
            public string t2_gate = "";
            public float c_geom = float.NaN;
            public float l_occ = float.NaN;
            public float total_loss = float.NaN;
            public string t3_gate = "";
            public bool gates_in_band;
            public OccludedTickRecord[] occluded_ticks;
        }

        public static CellRecord RunCell(Inputs inputs)
        {
            if (inputs == null) throw new ArgumentNullException(nameof(inputs));
            if (inputs.Trace == null
                || inputs.Trace.Length != Scene006Trace.HorizonSteps + 1)
                throw new InvalidOperationException("trace must have 541 states");

            var cell = new CellRecord
            {
                family = inputs.Family,
                anchor_x_m = inputs.AnchorXz.x,
                anchor_z_m = inputs.AnchorXz.y,
                support_y_m = inputs.SupportY,
                initial_altitude_m = inputs.AltitudeM,
                vertical_fov_deg = inputs.VerticalFovDeg,
                s_init = inputs.SInit,
                trace_sha256 = inputs.TraceSha256,
                trace_artifact = inputs.TraceArtifactPath,
                trace_first_lap_steps = inputs.FirstLapSteps,
            };

            Vector3 pHover = Scene006StationSet.HoverPosition(
                new Vector3(inputs.AnchorXz.x, 0f, inputs.AnchorXz.y),
                inputs.SupportY,
                inputs.AltitudeM);
            inputs.Cam.fieldOfView = inputs.VerticalFovDeg;

            var memberMinSides = new List<float>();
            var occludedTicks = new List<OccludedTickRecord>();
            bool fidelity = false;
            int frustumCount = 0;
            int visibleCount = 0;
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

                Bounds bounds = inputs.TargetRenderers[0].bounds;
                for (int index = 1; index < inputs.TargetRenderers.Length; index++)
                    bounds.Encapsulate(inputs.TargetRenderers[index].bounds);
                Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
                Vector3[] samples =
                    Scene006Visibility.VisibilitySamples(bounds, corners);

                int frustumSamples = 0;
                int visibleSamples = 0;
                var tickBlockers = new HashSet<string>(StringComparer.Ordinal);
                Vector3 origin = inputs.Cam.transform.position;
                foreach (Vector3 point in samples)
                {
                    Vector3 viewport = inputs.Cam.WorldToViewportPoint(point);
                    bool inFrustum = viewport.z > 0f
                        && viewport.x >= 0f && viewport.x <= 1f
                        && viewport.y >= 0f && viewport.y <= 1f;
                    if (!inFrustum) continue;
                    frustumSamples++;
                    string[] blockers = Scene006Visibility.OccludingRoots(
                        origin, point, inputs.TargetRoot);
                    if (blockers.Length == 0)
                    {
                        visibleSamples++;
                    }
                    else
                    {
                        foreach (string blocker in blockers)
                            tickBlockers.Add(blocker);
                    }
                }
                bool frustumVisible =
                    frustumSamples / (float)Scene006Visibility.SampleCount
                        >= Scene006Visibility.VisibleFractionThreshold;
                bool geometricallyVisible =
                    visibleSamples / (float)Scene006Visibility.SampleCount
                        >= Scene006Visibility.VisibleFractionThreshold;

                NormalizedBoundingBox box = Scene006Visibility.ProjectBounds(
                    inputs.Cam, corners);
                bool contradiction = frustumVisible && box == null;
                fidelity |= contradiction;
                float minSide = box == null
                    ? float.NaN
                    : Scene006Visibility.MinSidePx(
                        box, inputs.ImageWidth, inputs.ImageHeight);

                if (k >= 1)
                {
                    if (frustumVisible) frustumCount++;
                    if (geometricallyVisible) visibleCount++;
                    if (frustumVisible && !contradiction)
                        memberMinSides.Add(minSide);
                    if (frustumSamples > visibleSamples)
                    {
                        var blockers = new string[tickBlockers.Count];
                        tickBlockers.CopyTo(blockers);
                        Array.Sort(blockers, StringComparer.Ordinal);
                        occludedTicks.Add(new OccludedTickRecord
                        {
                            k = k,
                            t_s = k * Scene006Trace.StepSeconds,
                            frustum_sample_count = frustumSamples,
                            visible_sample_count = visibleSamples,
                            blocking_roots = blockers,
                        });
                    }
                }
            }

            cell.occluded_ticks = occludedTicks.ToArray();
            if (fidelity)
            {
                cell.terminal = "PROBE_FIDELITY_CONTRADICTION";
                cell.t1_domain_min_sides_px = memberMinSides.ToArray();
                return cell;
            }

            cell.t1_domain_count = memberMinSides.Count;
            cell.t1_domain_min_sides_px = memberMinSides.ToArray();
            if (memberMinSides.Count > 0)
            {
                cell.t1_min_side_p05_px = (float)Scene006Visibility
                    .QuantileType7(memberMinSides, 0.05);
                cell.t1_min_side_median_px = (float)Scene006Visibility
                    .QuantileType7(memberMinSides, 0.5);
                float min = float.PositiveInfinity;
                float max = float.NegativeInfinity;
                foreach (float value in memberMinSides)
                {
                    min = Mathf.Min(min, value);
                    max = Mathf.Max(max, value);
                }
                cell.t1_min_side_min_px = min;
                cell.t1_min_side_max_px = max;
            }
            cell.c_frustum = frustumCount / 540f;
            cell.c_geom = visibleCount / 540f;
            cell.l_point = 1f - cell.c_frustum;
            cell.l_occ = cell.c_frustum - cell.c_geom;
            cell.total_loss = 1f - cell.c_geom;
            bool t1Pass = memberMinSides.Count > 0
                && cell.t1_min_side_p05_px
                    >= Scene006Evaluation.T1MinSideP05ThresholdPx;
            cell.t2_gate = InInterval(
                cell.l_point,
                Scene006Evaluation.T2LossMin,
                Scene006Evaluation.T2LossMax) ? "PASS" : "FAIL";
            cell.t3_gate = InInterval(
                    cell.l_occ,
                    Scene006Evaluation.T3OccLossMin,
                    Scene006Evaluation.T3OccLossMax)
                && InInterval(
                    cell.total_loss,
                    Scene006Evaluation.T3TotalLossMin,
                    Scene006Evaluation.T3TotalLossMax)
                ? "PASS" : "FAIL";
            cell.gates_in_band = t1Pass
                && cell.t2_gate == "PASS"
                && cell.t3_gate == "PASS";
            return cell;
        }

        static bool InInterval(float value, float min, float max) =>
            value >= min && value <= max;
    }
}
