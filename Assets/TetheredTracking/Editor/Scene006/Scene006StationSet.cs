using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.2.6/§5.2.7 frozen body configurations. p_hover uses AGL semantics:
    /// (anchor_x, support_y + initial_altitude_m, anchor_z). The station set
    /// is the world lattice (anchor_x + 4i, support_y + h, anchor_z + 4j)
    /// with i, j integers and h in {8, 12, 16, 20, 24, 28, 32} m, keeping
    /// sqrt((4i)^2 + (4j)^2) &lt;= r(h) = sqrt(35^2 - h^2), plus p_hover;
    /// deterministic order is lexicographic on (h, x, z) and max ties take
    /// the first station in that order.
    /// </summary>
    public static class Scene006StationSet
    {
        public const float TetherLengthM = 35f;
        public const float LatticeStepM = 4f;
        public static readonly float[] HeightsM =
            { 8f, 12f, 16f, 20f, 24f, 28f, 32f };

        public readonly struct Station
        {
            public readonly float HeightAglM;
            public readonly Vector3 World;
            public readonly bool IsHover;

            public Station(float heightAglM, Vector3 world, bool isHover)
            {
                HeightAglM = heightAglM;
                World = world;
                IsHover = isHover;
            }
        }

        public static Vector3 HoverPosition(
            Vector3 anchor,
            float supportY,
            float hoverHeightM) =>
            new Vector3(anchor.x, supportY + hoverHeightM, anchor.z);

        public static Station[] Build(
            Vector3 anchor,
            float supportY,
            float hoverHeightM)
        {
            if (!Scene006RouteGeometry.Finite(supportY)
                || !Scene006RouteGeometry.Finite(hoverHeightM)
                || hoverHeightM <= 0f
                || hoverHeightM >= TetherLengthM)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(hoverHeightM));
            }
            var stations = new List<Station>();
            foreach (float h in HeightsM)
            {
                double radiusSquared =
                    (double)TetherLengthM * TetherLengthM - (double)h * h;
                if (radiusSquared < 0.0) continue;
                double radius = Math.Sqrt(radiusSquared);
                int extent = (int)Math.Floor(radius / LatticeStepM);
                for (int i = -extent; i <= extent; i++)
                {
                    for (int j = -extent; j <= extent; j++)
                    {
                        double dx = i * (double)LatticeStepM;
                        double dz = j * (double)LatticeStepM;
                        if (dx * dx + dz * dz > radiusSquared + 1e-9) continue;
                        stations.Add(new Station(
                            h,
                            new Vector3(
                                anchor.x + i * LatticeStepM,
                                supportY + h,
                                anchor.z + j * LatticeStepM),
                            false));
                    }
                }
            }
            Vector3 hover = HoverPosition(anchor, supportY, hoverHeightM);
            bool hoverPresent = false;
            for (int index = 0; index < stations.Count; index++)
            {
                if (stations[index].World == hover)
                {
                    // The lattice already contains this exact point (e.g. a
                    // 20 m hover on the h = 20 layer at i = j = 0); merging
                    // p_hover into the set is then a no-op.
                    stations[index] = new Station(
                        stations[index].HeightAglM, hover, true);
                    hoverPresent = true;
                    break;
                }
            }
            if (!hoverPresent)
                stations.Add(new Station(hoverHeightM, hover, true));
            stations.Sort((left, right) =>
            {
                int byHeight = left.HeightAglM.CompareTo(right.HeightAglM);
                if (byHeight != 0) return byHeight;
                int byX = left.World.x.CompareTo(right.World.x);
                if (byX != 0) return byX;
                return left.World.z.CompareTo(right.World.z);
            });
            return stations.ToArray();
        }
    }
}
