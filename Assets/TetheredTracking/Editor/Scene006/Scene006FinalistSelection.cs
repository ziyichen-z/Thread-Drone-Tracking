using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 amendment 1 §5.4 finalist selection (batch 1c, frozen
    /// scoring, BC-B1C-1): the finalist set F is exactly the reviewed P2
    /// in-band cells; scoring takes the unrounded stored inputs, computes
    /// the four band margins in IEEE-754 binary64, and orders by score
    /// descending, then vertical_fov ascending, initial_altitude ascending,
    /// family name ordinal, and the §5.5 lattice rank of the anchor
    /// (distance, then x, then z from the family lattice centre).
    ///
    /// Frozen margin formulas (§5.4):
    ///   m_T2  = min(L_point − 0.10, 0.50 − L_point) / 0.20
    ///   m_T3a = min(L_occ   − 0.05, 0.40 − L_occ)   / 0.175
    ///   m_T3b = min(total   − 0.15, 0.60 − total)   / 0.225
    ///   m_T1  = min((min_side_p05 − 25.0) / 25.0, 1.0)
    ///   score = min(m_T1, m_T2, m_T3a, m_T3b)
    ///
    /// Finiteness (R14): any non-finite input fails the cell closed as
    /// SCORE_INPUT_NOT_FINITE before any margin arithmetic (a +Inf p05
    /// would otherwise launder through min(…, 1.0)); any non-finite margin
    /// or score is SCORE_NOT_FINITE. Score equality is binary64 == (no
    /// tolerance; +0.0 == −0.0). The full ranking table is written to the
    /// artifact.
    /// </summary>
    public static class Scene006FinalistSelection
    {
        public const double T2Min = 0.10;
        public const double T2Max = 0.50;
        public const double T2Normalizer = 0.20;
        public const double T3aMin = 0.05;
        public const double T3aMax = 0.40;
        public const double T3aNormalizer = 0.175;
        public const double T3bMin = 0.15;
        public const double T3bMax = 0.60;
        public const double T3bNormalizer = 0.225;
        public const double T1ThresholdPx = 25.0;

        public sealed class CellInput
        {
            public string Family;
            public float AnchorX;
            public float AnchorZ;
            public float AltitudeM;
            public float VerticalFovDeg;
            public float SInit;
            public string TraceSha256;
            public double LPoint;
            public double LOcc;
            public double TotalLoss;
            public double MinSideP05Px;
        }

        [Serializable]
        public sealed class ScoredCell
        {
            public string family;
            public float anchor_x_m;
            public float anchor_z_m;
            public float initial_altitude_m;
            public float vertical_fov_deg;
            public float s_init;
            public string trace_sha256;
            public double l_point;
            public double l_occ;
            public double total_loss;
            public double min_side_p05_px;
            public double m_t1 = double.NaN;
            public double m_t2 = double.NaN;
            public double m_t3a = double.NaN;
            public double m_t3b = double.NaN;
            public double score = double.NaN;
            public string terminal = "";
            public int anchor_rank = -1;
            public int rank = -1;
        }

        public sealed class SelectionResult
        {
            public readonly List<ScoredCell> Ordered = new List<ScoredCell>();
            public readonly List<ScoredCell> Table = new List<ScoredCell>();
            public ScoredCell Finalist;
            public string Status;
        }

        static bool Finite(double value) =>
            !double.IsNaN(value) && !double.IsInfinity(value);

        /// <summary>
        /// §5.5 candidate-lattice rank of an anchor within its family
        /// lattice: ordering by squared distance to the lattice centre, then
        /// x, then z (the T5 audit's CandidatePositions order).
        /// </summary>
        public static int AnchorRank(string family, float anchorX, float anchorZ)
        {
            Vector2 centre = Scene006CandidateContract.LatticeCenter(family);
            const float step = 0.5f;
            const float radius = 10.0f;
            int extent = Mathf.CeilToInt(radius / step);
            var keys = new List<Vector3>(); // (distanceSquared, x, z)
            for (int xi = -extent; xi <= extent; xi++)
            {
                for (int zi = -extent; zi <= extent; zi++)
                {
                    float dx = xi * step;
                    float dz = zi * step;
                    if (dx * dx + dz * dz > radius * radius + 1e-5f) continue;
                    keys.Add(new Vector3(dx * dx + dz * dz, centre.x + dx, centre.y + dz));
                }
            }
            keys.Sort((left, right) =>
            {
                int byDistance = left.x.CompareTo(right.x);
                if (byDistance != 0) return byDistance;
                int byX = left.y.CompareTo(right.y);
                if (byX != 0) return byX;
                return left.z.CompareTo(right.z);
            });
            for (int index = 0; index < keys.Count; index++)
            {
                if (Mathf.Abs(keys[index].y - anchorX) <= 1e-6f
                    && Mathf.Abs(keys[index].z - anchorZ) <= 1e-6f)
                {
                    return index;
                }
            }
            throw new InvalidOperationException(
                $"anchor ({anchorX}, {anchorZ}) is not on the family "
                + $"{family} lattice");
        }

        public static ScoredCell Score(CellInput input)
        {
            var cell = new ScoredCell
            {
                family = input.Family,
                anchor_x_m = input.AnchorX,
                anchor_z_m = input.AnchorZ,
                initial_altitude_m = input.AltitudeM,
                vertical_fov_deg = input.VerticalFovDeg,
                s_init = input.SInit,
                trace_sha256 = input.TraceSha256,
                l_point = input.LPoint,
                l_occ = input.LOcc,
                total_loss = input.TotalLoss,
                min_side_p05_px = input.MinSideP05Px,
                anchor_rank = AnchorRank(
                    input.Family, input.AnchorX, input.AnchorZ),
            };
            if (!Finite(cell.l_point) || !Finite(cell.l_occ)
                || !Finite(cell.total_loss) || !Finite(cell.min_side_p05_px))
            {
                cell.terminal = "SCORE_INPUT_NOT_FINITE";
                return cell;
            }
            cell.m_t2 = Math.Min(
                cell.l_point - T2Min, T2Max - cell.l_point) / T2Normalizer;
            cell.m_t3a = Math.Min(
                cell.l_occ - T3aMin, T3aMax - cell.l_occ) / T3aNormalizer;
            cell.m_t3b = Math.Min(
                cell.total_loss - T3bMin, T3bMax - cell.total_loss)
                / T3bNormalizer;
            cell.m_t1 = Math.Min(
                (cell.min_side_p05_px - T1ThresholdPx) / T1ThresholdPx, 1.0);
            cell.score = Math.Min(
                Math.Min(cell.m_t1, cell.m_t2),
                Math.Min(cell.m_t3a, cell.m_t3b));
            if (!Finite(cell.m_t1) || !Finite(cell.m_t2)
                || !Finite(cell.m_t3a) || !Finite(cell.m_t3b)
                || !Finite(cell.score))
            {
                cell.terminal = "SCORE_NOT_FINITE";
            }
            return cell;
        }

        /// <summary>
        /// Orders F by the frozen tie-break chain. Every tie-break field is
        /// deterministic; the anchor lattice rank makes the order total, so
        /// the finalist (rank 0) is unique whenever F is non-empty. Cells
        /// with terminals exit F and never enter the ranking, but they are
        /// still recorded in <see cref="SelectionResult.Table"/> with their
        /// terminal label (§5.4: 排序表整体写入工件，含每格的终态标签).
        /// </summary>
        public static SelectionResult Select(IReadOnlyList<CellInput> inputs)
        {
            var result = new SelectionResult();
            var terminalCells = new List<ScoredCell>();
            foreach (CellInput input in inputs)
            {
                ScoredCell cell = Score(input);
                if (cell.terminal != "")
                {
                    terminalCells.Add(cell);
                    continue;
                }
                result.Ordered.Add(cell);
            }
            result.Ordered.Sort((left, right) =>
            {
                // §5.4: score equality is binary64 == (so +0.0 == -0.0);
                // Double.CompareTo would order -0.0 below +0.0 and is not
                // the frozen semantics. Descending.
                if (left.score != right.score)
                    return left.score > right.score ? -1 : 1;
                int byFov = left.vertical_fov_deg.CompareTo(
                    right.vertical_fov_deg);
                if (byFov != 0) return byFov;
                int byAltitude = left.initial_altitude_m.CompareTo(
                    right.initial_altitude_m);
                if (byAltitude != 0) return byAltitude;
                int byFamily = string.CompareOrdinal(
                    left.family, right.family);
                if (byFamily != 0) return byFamily;
                return left.anchor_rank.CompareTo(right.anchor_rank);
            });
            for (int index = 0; index < result.Ordered.Count; index++)
                result.Ordered[index].rank = index;
            result.Table.AddRange(result.Ordered);
            result.Table.AddRange(terminalCells);
            if (result.Ordered.Count == 0)
            {
                result.Status = "BLOCKED_GEOMETRY_INFEASIBLE";
                return result;
            }
            result.Finalist = result.Ordered[0];
            result.Status = "FINALIST_SELECTED";
            return result;
        }
    }
}
