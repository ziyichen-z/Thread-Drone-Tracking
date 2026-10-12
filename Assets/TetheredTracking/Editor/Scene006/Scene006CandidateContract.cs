using System;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// P1-SCENE-006 amendment 1 revision 5 (ACCEPTED, BC-AM1-1–6) frozen
    /// candidate contract: the two family lattice centres, the (+60, -60)
    /// route translation for family B, the preregistered §5.3 screening
    /// grid and the five §3.3.2 authorized vehicle relocations verbatim.
    /// These values are the authorized objects themselves; the relocation
    /// solver recomputes them by the frozen rules and any disagreement is
    /// RELOCATION_RECOMPUTE_MISMATCH (fail closed), never a silent override.
    /// </summary>
    public static class Scene006CandidateContract
    {
        public const string FamilyA = "A";
        public const string FamilyB = "B";

        public static readonly Vector2 FamilyACenter = new Vector2(150f, 108f);
        public static readonly Vector2 FamilyBCenter = new Vector2(195f, 30f);
        public static readonly Vector2 FamilyBTranslation =
            new Vector2(60f, -60f);

        public static readonly float[] AltitudesM =
            { 16f, 20f, 24f, 28f, 32f };
        public static readonly float[] VerticalFovsDeg =
            { 20f, 25f, 30f, 35f, 40f };

        // §5.3 preregistered 2 m subgrid anchors (screening set).
        public static readonly Vector2[] FamilyAGridAnchors =
        {
            new Vector2(148f, 108f),
            new Vector2(150f, 108f),
        };
        public static readonly Vector2[] FamilyBGridAnchors =
        {
            new Vector2(191f, 22f),
            new Vector2(191f, 30f),
            new Vector2(191f, 32f),
            new Vector2(193f, 30f),
            new Vector2(195f, 30f),
            new Vector2(197f, 30f),
        };

        /// <summary>§3.3.2 frozen row (the authorized content).</summary>
        public sealed class AuthorizedRelocation
        {
            public string PrefabName;
            public Vector2 OriginalXz;
            public int NearestSegmentIndex;
            public string Direction;
            public float DisplacementM;
            public Vector3 NewPosition;
        }

        /// <summary>
        /// The five authorized rows in application order — lexicographic on
        /// (prefab_name, original_x, original_z), which coincides with the
        /// §3.3.2 table order.
        /// </summary>
        public static readonly AuthorizedRelocation[] FamilyBRelocations =
        {
            new AuthorizedRelocation
            {
                PrefabName = "Vehicle_Ambulance",
                OriginalXz = new Vector2(183.600f, 29.406f),
                NearestSegmentIndex = 6,
                Direction = "left",
                DisplacementM = 4.6f,
                NewPosition = new Vector3(179.000f, 0.0f, 29.406f),
            },
            new AuthorizedRelocation
            {
                PrefabName = "Vehicle_Container_color01",
                OriginalXz = new Vector2(231.800f, 3.200f),
                NearestSegmentIndex = 4,
                Direction = "left",
                DisplacementM = 4.6f,
                NewPosition = new Vector3(231.800f, 0.0f, -1.400f),
            },
            new AuthorizedRelocation
            {
                PrefabName = "Vehicle_Pick up Truck_color01",
                OriginalXz = new Vector2(179.100f, 2.800f),
                NearestSegmentIndex = 5,
                Direction = "left",
                DisplacementM = 0.8f,
                NewPosition = new Vector3(178.534f, 0.0f, 2.234f),
            },
            new AuthorizedRelocation
            {
                PrefabName = "Vehicle_Pick up Truck_color01",
                OriginalXz = new Vector2(236.937f, 38.580f),
                NearestSegmentIndex = 2,
                Direction = "left",
                DisplacementM = 4.2f,
                NewPosition = new Vector3(241.137f, 0.0f, 38.580f),
            },
            new AuthorizedRelocation
            {
                PrefabName = "Vehicle_Taxi",
                OriginalXz = new Vector2(206.325f, 56.713f),
                NearestSegmentIndex = 0,
                Direction = "left",
                DisplacementM = 4.3f,
                NewPosition = new Vector3(206.325f, 0.0f, 61.013f),
            },
        };

        public const float RelocationMatchToleranceM = 0.1f;

        public static Vector2[] GridAnchors(string family)
        {
            switch (family)
            {
                case FamilyA: return FamilyAGridAnchors;
                case FamilyB: return FamilyBGridAnchors;
                default:
                    throw new ArgumentException("unknown family: " + family);
            }
        }

        public static Vector2 LatticeCenter(string family)
        {
            switch (family)
            {
                case FamilyA: return FamilyACenter;
                case FamilyB: return FamilyBCenter;
                default:
                    throw new ArgumentException("unknown family: " + family);
            }
        }

        /// <summary>
        /// Family route: A reuses the frozen route bytes; B uses the pure
        /// (+60, -60) translation of every vertex (y untouched).
        /// </summary>
        public static Vector3[] FamilyRoute(string family, Vector3[] frozenRoute)
        {
            if (frozenRoute == null) throw new ArgumentNullException(nameof(frozenRoute));
            switch (family)
            {
                case FamilyA:
                    return (Vector3[])frozenRoute.Clone();
                case FamilyB:
                    var translated = new Vector3[frozenRoute.Length];
                    for (int index = 0; index < frozenRoute.Length; index++)
                    {
                        Vector3 point = frozenRoute[index];
                        translated[index] = new Vector3(
                            point.x + FamilyBTranslation.x,
                            point.y,
                            point.z + FamilyBTranslation.y);
                    }
                    return translated;
                default:
                    throw new ArgumentException("unknown family: " + family);
            }
        }
    }
}
