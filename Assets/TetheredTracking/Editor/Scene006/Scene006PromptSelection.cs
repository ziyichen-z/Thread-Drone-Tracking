using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §3.2 (R18) prompt law v2: pick the T1′(v2) visual-prompt frame by a
    /// pre-registered eligibility predicate anchored on the probe's own
    /// measurement domain, before any detector or embedder runs.
    ///
    /// F23's second parity gap was that §5.6 only required the prompt frame
    /// to be visible with a non-null OK box, so the accepted `k* = 2` frame
    /// was a border-clipped crop at roughly twice the scale and half the
    /// obliquity of every measured frame. The law below replays the frozen
    /// trace/gimbal geometry, derives the domain's own type-7 [q05, q95]
    /// scale and off-nadir bands, and admits only warmup frames that are
    /// un-truncated and inside both bands.
    ///
    /// Discipline this file implements literally:
    ///
    /// * the candidate pool is the T6 warmup window `P = [0, 10]`
    ///   (BC-P2-1/AR3b); no mid-route frame is eligible, and an empty `E`
    ///   terminates at `T1P2_PROMPT_LAW_UNSATISFIABLE` rather than widening
    ///   the pool;
    /// * `D_V = {k in M : V(s_k) = 1}` is built first and every member must
    ///   carry `target_box_status = OK`. A single non-OK member is a
    ///   renderer/evaluator fidelity contradiction: the tool refuses to
    ///   compute quantiles, refuses to select a prompt and terminates at
    ///   `T1P2_PRECHECK_FAIL_PROBE_FIDELITY_CONTRADICTION` (BC-P2-4). The
    ///   member is never dropped from the domain;
    /// * nothing is read from the retired capture directory
    ///   (`runtime/p1-scene-006/probe-candidate-vfov40/`), and no detector
    ///   score, IoU, cosine or recall enters any threshold here (§5.7).
    ///
    /// Both band endpoints are derived from the frozen geometry; the only
    /// hand-picked constant in the law is the 2.0 px truncation margin
    /// (§5.6 of the amendment).
    /// </summary>
    public static class Scene006PromptSelection
    {
        public const string ArtifactSchema =
            "p1-scene-006-prompt-selection-p2/v1";
        public const string ArtifactProjectPath =
            "docs/evidence/P1-SCENE-006-prompt-selection-p2.json";
        public const string FidelityReportProjectPath =
            "docs/evidence/P1-SCENE-006-prompt-selection-p2-fidelity-fail.json";
        public const int T1PrimeProtocol = 2;

        /// <summary>`P = [0, 10] ∩ ℤ`, the T6 acquisition window.</summary>
        public const int WarmupWindowEnd = Scene006Evaluation.T6AcquisitionWindow;
        public const float TruncationMarginPx = 2.0f;
        public const double BandLowerProbability = 0.05;
        public const double BandUpperProbability = 0.95;
        public const int ImageWidthPx = 640;
        public const int ImageHeightPx = 480;
        public const int NoSelection = -1;

        public const string StatusSelected = "SELECTION_OK";
        public const string StatusPromptLawUnsatisfiable =
            "T1P2_PROMPT_LAW_UNSATISFIABLE";
        public const string StatusFidelityContradiction =
            "T1P2_PRECHECK_FAIL_PROBE_FIDELITY_CONTRADICTION";

        /// <summary>
        /// How `applied off-nadir` is defined for clause (e), recorded in
        /// the artifact so the band's meaning travels with its numbers.
        /// `camera_off_nadir_deg` is reported next to it for every tick but
        /// is not used by any clause.
        /// </summary>
        public const string OffNadirDefinition =
            "gimbal-law applied angle: min(atan2(horizontal, max(0.1, -dy)), "
            + "45 deg) from p_hover to the truth position "
            + "(Scene006GimbalReplay.AppliedOffNadirDeg)";

        [Serializable]
        public sealed class MeasurementTick
        {
            public int k;
            public float t_s;
            public bool frustum_visible;
            public bool geometrically_visible;
            public int frustum_sample_count;
            public int visible_sample_count;
            public float visible_sample_fraction;
            public string target_box_status;
            public float min_side_px;
            public float applied_off_nadir_deg;
            public float camera_off_nadir_deg;
        }

        [Serializable]
        public sealed class WarmupTick
        {
            public int k;
            public float t_s;
            public bool frustum_visible;
            public bool geometrically_visible;
            public string target_box_status;
            public NormalizedBoundingBox target_bbox_xywh_norm;
            public float margin_left_px;
            public float margin_right_px;
            public float margin_top_px;
            public float margin_bottom_px;
            public float min_side_px;
            public float applied_off_nadir_deg;
            public float camera_off_nadir_deg;
            public bool clause_a_visible;
            public bool clause_b_box_ok;
            public bool clause_c_untruncated;
            public bool clause_d_scale_band;
            public bool clause_e_off_nadir_band;
            public bool eligible;
            public string first_failed_clause;
        }

        [Serializable]
        public sealed class Band
        {
            public string metric;
            public string unit;
            public string quantile_method = "type-7";
            public bool computed;
            public int count;
            public double q05;
            public double q95;
        }

        [Serializable]
        public sealed class DomainSection
        {
            public int measurement_tick_count;
            public int visible_count;
            public bool all_members_box_ok;
            public int[] members;
            public int[] non_ok_members;
            public int denominator_assertion_count;
            public bool denominator_assertion_ok;
        }

        [Serializable]
        public sealed class CrossCheck
        {
            public int k;
            public bool frustum_visible_equal;
            public bool geometrically_visible_equal;
            public bool min_side_bit_equal;
            public float p3_min_side_px;
            public float recomputed_min_side_px;
        }

        [Serializable]
        public sealed class Artifact
        {
            public string schema_version = ArtifactSchema;
            public string work_id = "P1-SCENE-006";
            public int t1prime_protocol = T1PrimeProtocol;
            public string status;
            public string terminal;
            public int selected_tick;
            public int diagnostic_tick;
            public string scenario_id;
            public string scenario_sha256;
            public string road_data_sha256;
            public string trace_sha256;
            public float s_init;
            public string p3_artifact;
            public string p3_artifact_sha256;
            public int p3_k_star;
            public float p3_t1_domain_median_px;
            public float vertical_fov_deg;
            public int image_width;
            public int image_height;
            public Scene006Evaluation.Vec3 anchor_world_m;
            public Scene006Evaluation.Vec3 p_hover_world_m;
            public float truncation_margin_px = TruncationMarginPx;
            public string off_nadir_definition = OffNadirDefinition;
            public int[] warmup_pool;
            public int[] measurement_tick_set;
            public MeasurementTick[] measurement_ticks;
            public DomainSection d_v;
            public Band min_side_band;
            public Band off_nadir_band;
            public WarmupTick[] warmup_ticks;
            public CrossCheck[] p3_cross_check;
        }

        public sealed class Inputs
        {
            public Scene006SceneRig Rig;
            public Scene006Trace.State[] Trace;
            public Vector3 PHover;
            public Vector3 Anchor;
            public int ImageWidth;
            public int ImageHeight;
            public float VerticalFovDeg;
            public string ScenarioId;
            public string ScenarioSha256;
            public string RoadDataSha256;
            public string TraceSha256;
            public float SInit;
            public string P3ArtifactPath;
            public string P3ArtifactSha256;
            public Scene006Evaluation.T6Record P3T6;
        }

        public static int[] WarmupPool()
        {
            var pool = new int[WarmupWindowEnd + 1];
            for (int k = 0; k <= WarmupWindowEnd; k++) pool[k] = k;
            return pool;
        }

        /// <summary>
        /// Replays the frozen trace and produces the selection artifact.
        /// Identity and P3 cross-check failures throw (the artifact is
        /// refused outright); the two protocol terminals are returned in
        /// <see cref="Artifact.status"/> instead, because they are evidence
        /// the amendment requires to be recorded.
        /// </summary>
        public static Artifact Compute(Inputs inputs)
        {
            if (inputs == null) throw new ArgumentNullException(nameof(inputs));
            Scene006SceneRig rig = inputs.Rig;
            Scene006Trace.State[] trace = inputs.Trace;
            Require(rig != null && rig.TargetReplica != null
                && rig.TargetRenderers != null && rig.EvaluationCamera != null,
                "prompt selection needs a prepared scene rig");
            Require(
                trace != null && trace.Length == Scene006Trace.HorizonSteps + 1,
                "prompt selection needs the 541-state frozen trace");
            Require(
                inputs.ImageWidth == ImageWidthPx
                && inputs.ImageHeight == ImageHeightPx,
                "the prompt law's truncation clause is stated in the frozen "
                + $"{ImageWidthPx}x{ImageHeightPx} image grid");
            Require(inputs.P3T6 != null && inputs.P3T6.samples != null
                && inputs.P3T6.samples.Length == WarmupWindowEnd + 1,
                "prompt selection needs the reviewed P3 T6 warmup samples");

            int[] measurementTicks = Scene006ProbeRenderer.ProbeTicks();
            var measurementSet = new HashSet<int>(measurementTicks);
            var measurementRecords = new List<MeasurementTick>();
            var warmupRaw = new Dictionary<int, WarmupTick>();
            var crossChecks = new List<CrossCheck>();

            Func<Vector3, Vector3, bool> los =
                (origin, point) => Scene006Visibility.HasClearLineOfSight(
                    origin, point, rig.TargetReplica.transform);
            Quaternion gimbal = Scene006GimbalReplay.InitialRotation;
            for (int k = 0; k < trace.Length; k++)
            {
                Scene006Trace.State state = trace[k];
                rig.TargetReplica.transform.SetPositionAndRotation(
                    state.Position, state.Rotation);
                if (k >= 1)
                {
                    gimbal = Scene006GimbalReplay.Update(
                        gimbal, inputs.PHover, state.Position);
                }
                rig.EvaluationCamera.transform.SetPositionAndRotation(
                    inputs.PHover, gimbal);

                bool warmup = k <= WarmupWindowEnd;
                bool measurement = measurementSet.Contains(k);
                if (!warmup && !measurement) continue;

                Bounds bounds = rig.TargetRenderers[0].bounds;
                for (int index = 1; index < rig.TargetRenderers.Length; index++)
                    bounds.Encapsulate(rig.TargetRenderers[index].bounds);
                Vector3[] corners = Scene006Visibility.BoundsCorners(bounds);
                Scene006Visibility.Snapshot snapshot =
                    Scene006Visibility.Evaluate(
                        rig.EvaluationCamera, bounds, corners, los);
                NormalizedBoundingBox box = Scene006Visibility.ProjectBounds(
                    rig.EvaluationCamera, corners);
                string status = BoxStatus(snapshot, box);
                float minSide = box == null
                    ? float.NaN
                    : Scene006Visibility.MinSidePx(
                        box, inputs.ImageWidth, inputs.ImageHeight);
                float applied = Scene006GimbalReplay.AppliedOffNadirDeg(
                    inputs.PHover, state.Position);
                float cameraOffNadir = Vector3.Angle(
                    rig.EvaluationCamera.transform.forward, Vector3.down);

                if (measurement)
                {
                    measurementRecords.Add(new MeasurementTick
                    {
                        k = k,
                        t_s = k * Scene006Trace.StepSeconds,
                        frustum_visible = snapshot.FrustumVisible,
                        geometrically_visible = snapshot.GeometricallyVisible,
                        frustum_sample_count = snapshot.FrustumSampleCount,
                        visible_sample_count = snapshot.VisibleSampleCount,
                        visible_sample_fraction = snapshot.VisibleFraction,
                        target_box_status = status,
                        min_side_px = minSide,
                        applied_off_nadir_deg = applied,
                        camera_off_nadir_deg = cameraOffNadir,
                    });
                }
                if (warmup)
                {
                    warmupRaw[k] = new WarmupTick
                    {
                        k = k,
                        t_s = k * Scene006Trace.StepSeconds,
                        frustum_visible = snapshot.FrustumVisible,
                        geometrically_visible = snapshot.GeometricallyVisible,
                        target_box_status = status,
                        target_bbox_xywh_norm = box,
                        margin_left_px = box == null
                            ? float.NaN : box.x * inputs.ImageWidth,
                        margin_right_px = box == null
                            ? float.NaN
                            : inputs.ImageWidth - (box.x + box.width)
                                * inputs.ImageWidth,
                        margin_top_px = box == null
                            ? float.NaN : box.y * inputs.ImageHeight,
                        margin_bottom_px = box == null
                            ? float.NaN
                            : inputs.ImageHeight - (box.y + box.height)
                                * inputs.ImageHeight,
                        min_side_px = minSide,
                        applied_off_nadir_deg = applied,
                        camera_off_nadir_deg = cameraOffNadir,
                    };
                    Scene006Evaluation.T6SampleRecord p3Sample =
                        inputs.P3T6.samples[k];
                    crossChecks.Add(new CrossCheck
                    {
                        k = k,
                        frustum_visible_equal =
                            p3Sample.frustum_visible == snapshot.FrustumVisible,
                        geometrically_visible_equal =
                            p3Sample.geometrically_visible
                                == snapshot.GeometricallyVisible,
                        min_side_bit_equal =
                            BitEqual(p3Sample.min_side_px, minSide),
                        p3_min_side_px = p3Sample.min_side_px,
                        recomputed_min_side_px = minSide,
                    });
                }
            }

            Require(
                measurementRecords.Count == measurementTicks.Length,
                "prompt selection must replay all "
                + measurementTicks.Length + " measurement ticks");
            foreach (CrossCheck check in crossChecks)
            {
                if (check.frustum_visible_equal
                    && check.geometrically_visible_equal
                    && check.min_side_bit_equal)
                {
                    continue;
                }
                Scene006Evaluation.T6SampleRecord p3 =
                    inputs.P3T6.samples[check.k];
                WarmupTick replayed = warmupRaw[check.k];
                Require(
                    false,
                    "warmup tick " + check.k + " diverges from the reviewed "
                    + "P3 t6 sample; the selection artifact is refused. "
                    + "frustum_visible p3=" + p3.frustum_visible
                    + " replay=" + replayed.frustum_visible
                    + "; geometrically_visible p3="
                    + p3.geometrically_visible
                    + " replay=" + replayed.geometrically_visible
                    + "; min_side_px p3=" + p3.min_side_px.ToString("R")
                    + " replay=" + replayed.min_side_px.ToString("R"));
            }

            var artifact = new Artifact
            {
                scenario_id = inputs.ScenarioId,
                scenario_sha256 = inputs.ScenarioSha256,
                road_data_sha256 = inputs.RoadDataSha256,
                trace_sha256 = inputs.TraceSha256,
                s_init = inputs.SInit,
                p3_artifact = inputs.P3ArtifactPath,
                p3_artifact_sha256 = inputs.P3ArtifactSha256,
                p3_k_star = inputs.P3T6.k_star,
                p3_t1_domain_median_px = inputs.P3T6.t1_domain_median_px,
                vertical_fov_deg = inputs.VerticalFovDeg,
                image_width = inputs.ImageWidth,
                image_height = inputs.ImageHeight,
                anchor_world_m = ToVec3(inputs.Anchor),
                p_hover_world_m = ToVec3(inputs.PHover),
                warmup_pool = WarmupPool(),
                measurement_tick_set = measurementTicks,
                measurement_ticks = measurementRecords.ToArray(),
                p3_cross_check = crossChecks.ToArray(),
                selected_tick = NoSelection,
                diagnostic_tick = NoSelection,
                min_side_band = EmptyBand("min_side_px", "px"),
                off_nadir_band = EmptyBand("applied_off_nadir_deg", "deg"),
                warmup_ticks = Array.Empty<WarmupTick>(),
            };

            // D_V first (all V = 1 measurement ticks), then the per-member
            // OK check. Nothing is dropped from the domain either way.
            var members = new List<int>();
            var nonOk = new List<int>();
            foreach (MeasurementTick record in artifact.measurement_ticks)
            {
                if (!record.geometrically_visible) continue;
                members.Add(record.k);
                if (record.target_box_status != "OK") nonOk.Add(record.k);
            }
            // Independent recount of the formal target denominator.
            int denominatorAssertion = 0;
            foreach (MeasurementTick record in artifact.measurement_ticks)
            {
                if (record.geometrically_visible) denominatorAssertion++;
            }
            artifact.d_v = new DomainSection
            {
                measurement_tick_count = measurementTicks.Length,
                visible_count = members.Count,
                all_members_box_ok = nonOk.Count == 0,
                members = members.ToArray(),
                non_ok_members = nonOk.ToArray(),
                denominator_assertion_count = denominatorAssertion,
                denominator_assertion_ok = denominatorAssertion == members.Count,
            };
            Require(
                artifact.d_v.denominator_assertion_ok,
                "the |D| assertion disagrees with the recounted target "
                + "denominator");

            if (!artifact.d_v.all_members_box_ok)
            {
                artifact.status = StatusFidelityContradiction;
                artifact.terminal = StatusFidelityContradiction;
                return artifact;
            }
            Require(
                members.Count > 0,
                "D_V is empty; the probe has no target sample at all");

            var minSides = new List<float>(members.Count);
            var offNadirs = new List<float>(members.Count);
            foreach (MeasurementTick record in artifact.measurement_ticks)
            {
                if (!record.geometrically_visible) continue;
                minSides.Add(record.min_side_px);
                offNadirs.Add(record.applied_off_nadir_deg);
            }
            artifact.min_side_band = ComputeBand("min_side_px", "px", minSides);
            artifact.off_nadir_band = ComputeBand(
                "applied_off_nadir_deg", "deg", offNadirs);
            // k_diag: the lower median of D by ascending tick.
            artifact.diagnostic_tick = members[(members.Count - 1) / 2];

            var warmupTicks = new List<WarmupTick>();
            foreach (int k in artifact.warmup_pool)
            {
                WarmupTick record = warmupRaw[k];
                EvaluateEligibility(
                    record,
                    artifact.min_side_band,
                    artifact.off_nadir_band,
                    inputs.ImageWidth,
                    inputs.ImageHeight);
                warmupTicks.Add(record);
            }
            artifact.warmup_ticks = warmupTicks.ToArray();

            foreach (WarmupTick record in artifact.warmup_ticks)
            {
                if (!record.eligible) continue;
                artifact.selected_tick = record.k;
                break;
            }
            bool selected = artifact.selected_tick != NoSelection;
            artifact.status = selected
                ? StatusSelected : StatusPromptLawUnsatisfiable;
            artifact.terminal = selected
                ? string.Empty : StatusPromptLawUnsatisfiable;
            return artifact;
        }

        /// <summary>
        /// The §3.2.3 predicate `E(k)`, clause by clause and in order, so
        /// `first_failed_clause` names the earliest violated requirement.
        /// </summary>
        public static void EvaluateEligibility(
            WarmupTick record,
            Band minSideBand,
            Band offNadirBand,
            int imageWidth,
            int imageHeight)
        {
            if (record == null) throw new ArgumentNullException(nameof(record));
            NormalizedBoundingBox box = record.target_bbox_xywh_norm;
            record.clause_a_visible = record.geometrically_visible;
            record.clause_b_box_ok =
                record.target_box_status == "OK" && box != null;
            record.clause_c_untruncated = record.clause_b_box_ok
                && box.x * imageWidth >= TruncationMarginPx
                && box.y * imageHeight >= TruncationMarginPx
                && (box.x + box.width) * imageWidth
                    <= imageWidth - TruncationMarginPx
                && (box.y + box.height) * imageHeight
                    <= imageHeight - TruncationMarginPx;
            record.clause_d_scale_band = record.clause_b_box_ok
                && InBand(record.min_side_px, minSideBand);
            record.clause_e_off_nadir_band = InBand(
                record.applied_off_nadir_deg, offNadirBand);
            record.eligible = record.clause_a_visible
                && record.clause_b_box_ok
                && record.clause_c_untruncated
                && record.clause_d_scale_band
                && record.clause_e_off_nadir_band;
            if (record.eligible)
            {
                record.first_failed_clause = string.Empty;
                return;
            }
            if (!record.clause_a_visible) record.first_failed_clause = "a_visible";
            else if (!record.clause_b_box_ok)
                record.first_failed_clause = "b_box_ok";
            else if (!record.clause_c_untruncated)
                record.first_failed_clause = "c_untruncated";
            else if (!record.clause_d_scale_band)
                record.first_failed_clause = "d_scale_band";
            else record.first_failed_clause = "e_off_nadir_band";
        }

        static bool InBand(float value, Band band)
        {
            if (band == null || !band.computed) return false;
            if (!Scene006RouteGeometry.Finite(value)) return false;
            double sample = value;
            return sample >= band.q05 && sample <= band.q95;
        }

        public static Band ComputeBand(
            string metric, string unit, IReadOnlyList<float> values)
        {
            return new Band
            {
                metric = metric,
                unit = unit,
                computed = true,
                count = values.Count,
                q05 = Scene006Visibility.QuantileType7(
                    values, BandLowerProbability),
                q95 = Scene006Visibility.QuantileType7(
                    values, BandUpperProbability),
            };
        }

        static Band EmptyBand(string metric, string unit) =>
            new Band { metric = metric, unit = unit, computed = false };

        static string BoxStatus(
            Scene006Visibility.Snapshot snapshot, NormalizedBoundingBox box)
        {
            if (!snapshot.GeometricallyVisible) return "TARGET_NOT_VISIBLE";
            return box == null ? "TARGET_VISIBLE_UNPROJECTABLE" : "OK";
        }

        /// <summary>
        /// Bit equality for the "逐位相等" cross-checks, with one deliberate
        /// exception: any two NaNs count as equal. `min_side_px` is NaN
        /// exactly when the truth box is unprojectable, and a NaN read back
        /// from a committed artifact does not necessarily carry the same
        /// payload as the one this replay produces — comparing payloads
        /// would report a difference where both sides say "no box".
        /// </summary>
        static bool BitEqual(float left, float right)
        {
            if (float.IsNaN(left) && float.IsNaN(right)) return true;
            return BitConverter.SingleToInt32Bits(left)
                == BitConverter.SingleToInt32Bits(right);
        }

        static Scene006Evaluation.Vec3 ToVec3(Vector3 value) =>
            new Scene006Evaluation.Vec3
            {
                x = value.x,
                y = value.y,
                z = value.z,
            };

        const string SelectedTickSentinel = "\"selected_tick\": -1";
        const string SelectedTickNull = "\"selected_tick\": null";

        /// <summary>
        /// Emits standard JSON (BC-P2-10). Two `JsonUtility` limitations are
        /// handled at this boundary and nowhere else:
        ///
        /// * it cannot express a null integer, so the `-1` no-selection
        ///   sentinel becomes the literal `null` BC-P2-5 requires — and an
        ///   unexpected occurrence count fails closed rather than leaking a
        ///   `-1` a reader could mistake for a tick;
        /// * it prints non-finite floats as bare `NaN`, which
        ///   <see cref="Scene006Json.ToStrictJson"/> turns into `null`.
        ///
        /// The result is re-scanned before it is returned, so no artifact
        /// can leave this method unparseable by a strict parser.
        /// </summary>
        public static string Serialize(Artifact artifact)
        {
            if (artifact == null) throw new ArgumentNullException(nameof(artifact));
            string json = Scene006Json.ToStrictJson(
                JsonUtility.ToJson(artifact, true)) + "\n";
            if (artifact.selected_tick == NoSelection)
            {
                int first = json.IndexOf(
                    SelectedTickSentinel, StringComparison.Ordinal);
                int last = json.LastIndexOf(
                    SelectedTickSentinel, StringComparison.Ordinal);
                if (first < 0 || first != last)
                {
                    throw new InvalidOperationException(
                        "the selection artifact cannot express selected_tick "
                        + "= null; refusing to emit the -1 sentinel");
                }
                json = json.Substring(0, first)
                    + SelectedTickNull
                    + json.Substring(first + SelectedTickSentinel.Length);
            }
            if (Scene006Json.ContainsNonFiniteToken(json))
            {
                throw new InvalidOperationException(
                    "the selection artifact still carries a bare non-finite "
                    + "token; refusing to write non-standard JSON");
            }
            return json;
        }

        /// <summary>
        /// Reads a committed selection artifact. `selected_tick: null` maps
        /// back to <see cref="NoSelection"/>; every other `null` is an
        /// unavailable number and maps back to NaN, so the round trip
        /// preserves the float values the artifact was produced from
        /// instead of silently reading zero.
        /// </summary>
        public static Artifact Deserialize(string json)
        {
            if (json == null) throw new ArgumentNullException(nameof(json));
            string normalized = Scene006Json.FromStrictJson(
                json.Replace(SelectedTickNull, SelectedTickSentinel));
            Artifact artifact = JsonUtility.FromJson<Artifact>(normalized);
            if (artifact == null || artifact.schema_version != ArtifactSchema)
            {
                throw new InvalidOperationException(
                    "selection artifact schema mismatch");
            }
            return artifact;
        }

        /// <summary>
        /// §3.2.6 / B3: every field the renderer re-derives before writing
        /// the formal manifest must equal the committed artifact. Returns
        /// every difference, empty when the two agree.
        /// </summary>
        public static string[] Compare(Artifact committed, Artifact recomputed)
        {
            var differences = new List<string>();
            if (committed == null || recomputed == null)
            {
                differences.Add("missing selection artifact");
                return differences.ToArray();
            }
            CompareText(differences, "status",
                committed.status, recomputed.status);
            CompareText(differences, "terminal",
                committed.terminal, recomputed.terminal);
            CompareValue(differences, "selected_tick",
                committed.selected_tick, recomputed.selected_tick);
            CompareValue(differences, "diagnostic_tick",
                committed.diagnostic_tick, recomputed.diagnostic_tick);
            CompareText(differences, "trace_sha256",
                committed.trace_sha256, recomputed.trace_sha256);
            CompareText(differences, "scenario_sha256",
                committed.scenario_sha256, recomputed.scenario_sha256);
            CompareValue(differences, "d_v.visible_count",
                committed.d_v?.visible_count, recomputed.d_v?.visible_count);
            CompareValue(differences, "d_v.all_members_box_ok",
                committed.d_v?.all_members_box_ok,
                recomputed.d_v?.all_members_box_ok);
            CompareBand(differences, "min_side_band",
                committed.min_side_band, recomputed.min_side_band);
            CompareBand(differences, "off_nadir_band",
                committed.off_nadir_band, recomputed.off_nadir_band);
            CompareWarmup(differences, committed, recomputed);
            CompareMeasurement(differences, committed, recomputed);
            return differences.ToArray();
        }

        static void CompareMeasurement(
            List<string> differences, Artifact committed, Artifact recomputed)
        {
            MeasurementTick[] left = committed.measurement_ticks
                ?? Array.Empty<MeasurementTick>();
            MeasurementTick[] right = recomputed.measurement_ticks
                ?? Array.Empty<MeasurementTick>();
            if (left.Length != right.Length)
            {
                differences.Add(
                    "measurement_ticks: " + left.Length + " vs " + right.Length);
                return;
            }
            for (int index = 0; index < left.Length; index++)
            {
                string prefix = "measurement_ticks[" + left[index].k + "].";
                CompareValue(differences, prefix + "k",
                    left[index].k, right[index].k);
                CompareValue(differences, prefix + "geometrically_visible",
                    left[index].geometrically_visible,
                    right[index].geometrically_visible);
                CompareText(differences, prefix + "target_box_status",
                    left[index].target_box_status,
                    right[index].target_box_status);
                CompareFloatBits(differences, prefix + "min_side_px",
                    left[index].min_side_px, right[index].min_side_px);
                CompareFloatBits(differences, prefix + "applied_off_nadir_deg",
                    left[index].applied_off_nadir_deg,
                    right[index].applied_off_nadir_deg);
            }
        }

        static void CompareWarmup(
            List<string> differences, Artifact committed, Artifact recomputed)
        {
            WarmupTick[] left = committed.warmup_ticks
                ?? Array.Empty<WarmupTick>();
            WarmupTick[] right = recomputed.warmup_ticks
                ?? Array.Empty<WarmupTick>();
            if (left.Length != right.Length)
            {
                differences.Add(
                    "warmup_ticks: " + left.Length + " vs " + right.Length);
                return;
            }
            for (int index = 0; index < left.Length; index++)
            {
                string prefix = "warmup_ticks[" + left[index].k + "].";
                CompareValue(differences, prefix + "k",
                    left[index].k, right[index].k);
                CompareValue(differences, prefix + "eligible",
                    left[index].eligible, right[index].eligible);
                CompareText(differences, prefix + "first_failed_clause",
                    left[index].first_failed_clause,
                    right[index].first_failed_clause);
                CompareFloatBits(differences, prefix + "min_side_px",
                    left[index].min_side_px, right[index].min_side_px);
                CompareFloatBits(differences, prefix + "applied_off_nadir_deg",
                    left[index].applied_off_nadir_deg,
                    right[index].applied_off_nadir_deg);
            }
        }

        static void CompareBand(
            List<string> differences, string label, Band left, Band right)
        {
            if (left == null || right == null)
            {
                differences.Add(label + ": missing");
                return;
            }
            CompareValue(differences, label + ".computed",
                left.computed, right.computed);
            CompareValue(differences, label + ".count", left.count, right.count);
            CompareValue(differences, label + ".q05", left.q05, right.q05);
            CompareValue(differences, label + ".q95", left.q95, right.q95);
        }

        static void CompareValue<T>(
            List<string> differences, string label, T left, T right)
        {
            if (Equals(left, right)) return;
            differences.Add(label + ": " + left + " vs " + right);
        }

        /// <summary>
        /// String comparison across the serialization boundary. JsonUtility
        /// writes a null string as `""` and reads it back as `""`, so the
        /// two are indistinguishable once an artifact is committed;
        /// treating them as different would abort a legitimate capture on a
        /// difference the file cannot even express.
        /// </summary>
        static void CompareText(
            List<string> differences, string label, string left, string right)
        {
            if (string.Equals(
                left ?? string.Empty,
                right ?? string.Empty,
                StringComparison.Ordinal))
            {
                return;
            }
            differences.Add(label + ": '" + left + "' vs '" + right + "'");
        }

        static void CompareFloatBits(
            List<string> differences, string label, float left, float right)
        {
            if (BitEqual(left, right)) return;
            differences.Add(
                label + ": " + left.ToString("R") + " vs " + right.ToString("R"));
        }

        static void Require(bool condition, string message)
        {
            if (!condition)
                throw new InvalidOperationException(
                    "prompt selection failed: " + message);
        }
    }
}
