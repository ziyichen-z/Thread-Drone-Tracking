using System;
using System.Collections.Generic;
using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.2.2 frozen target trace: 541 states s_0..s_540.
    ///
    /// Initialization is the Configure(route)-equivalent initial state
    /// followed by PlaceAtRouteDistance(s_init) literal semantics
    /// (Scripts/LoopTargetVehicle.cs:15-28, 40-58); each subsequent state is
    /// the float32 reproduction of LoopTargetVehicle.Step(0.2)
    /// (Scripts/LoopTargetVehicle.cs:65-81), including the pause semantics
    /// ("advance the index without moving when within &lt; 0.5f of the
    /// destination vertex") and the delta.y = 0 horizontal projection.
    /// s_0 is the post-placement pre-Step t = 0 state; s_k (k >= 1) is the
    /// state after the k-th Step with time label t_k = k * 0.2 s.
    ///
    /// The internal members of LoopTargetVehicle are not accessible from this
    /// assembly, so the semantics are replicated with identical operation
    /// order and UnityEngine float32 math; EditMode tests verify the
    /// replication against a real LoopTargetVehicle component step for step.
    /// </summary>
    public static class Scene006Trace
    {
        public const int HorizonSteps = 540;
        public const float StepSeconds = 0.2f;
        public const float TurnRateDegPerSecond = 240f;
        public const float WaypointPauseDistanceM = 0.5f;

        public readonly struct State
        {
            public readonly Vector3 Position;
            public readonly Quaternion Rotation;

            public State(Vector3 position, Quaternion rotation)
            {
                Position = position;
                Rotation = rotation;
            }
        }

        /// <summary>
        /// Full trace including s_0: the returned array has steps + 1 states.
        /// </summary>
        public static State[] Generate(
            IReadOnlyList<Vector3> route,
            float speedMps,
            float sInit,
            int steps = HorizonSteps)
        {
            if (route == null) throw new ArgumentNullException(nameof(route));
            if (!Scene006RouteGeometry.Finite(speedMps) || speedMps < 0f)
                throw new ArgumentOutOfRangeException(nameof(speedMps));
            if (steps < 0)
                throw new ArgumentOutOfRangeException(nameof(steps));
            float perimeter = Scene006RouteGeometry.ClosedRoutePerimeter(route);
            // PlaceAtRouteDistance domain check (LoopTargetVehicle.cs:46-49).
            if (!Scene006RouteGeometry.Finite(sInit)
                || sInit < 0f
                || sInit >= perimeter)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(sInit),
                    "Frozen route distance must satisfy 0 <= s < perimeter.");
            }

            Scene006RouteGeometry.RouteSample sample =
                Scene006RouteGeometry.SampleClosedRoute(route, sInit);
            Vector3 position = sample.Position;
            int waypointIndex = sample.NextWaypointIndex;
            // Configure(route) leaves the GameObject rotation untouched; a
            // freshly created vehicle starts at identity, and
            // PlaceAtRouteDistance only overrides it on a significant
            // horizontal direction (LoopTargetVehicle.cs:54-57).
            Quaternion rotation = Quaternion.identity;
            Vector3 initialDirection = route[waypointIndex] - position;
            initialDirection.y = 0f;
            if (initialDirection.sqrMagnitude > 0.0001f)
                rotation = Quaternion.LookRotation(initialDirection.normalized);

            var states = new State[steps + 1];
            states[0] = new State(position, rotation);
            for (int k = 1; k <= steps; k++)
            {
                // LoopTargetVehicle.Step(float32) literal reproduction.
                Vector3 destination = route[waypointIndex];
                Vector3 delta = destination - position;
                delta.y = 0f;
                if (delta.magnitude < WaypointPauseDistanceM)
                {
                    waypointIndex = (waypointIndex + 1) % route.Count;
                    // Pause step: no movement, no rotation change.
                }
                else
                {
                    Vector3 direction = delta.normalized;
                    position += direction * speedMps * StepSeconds;
                    rotation = Quaternion.RotateTowards(
                        rotation,
                        Quaternion.LookRotation(direction),
                        TurnRateDegPerSecond * StepSeconds);
                }
                states[k] = new State(position, rotation);
            }
            return states;
        }

        /// <summary>
        /// Measured first-lap length in steps: the first k >= 1 whose
        /// waypoint index has returned to the initial index while the
        /// position is again within the pause distance of the s_0 position.
        /// Returns -1 (reported as HORIZON_SHORT) when no lap closes inside
        /// the horizon; the trace must never be silently extended or rolled.
        /// </summary>
        public static int FirstLapSteps(
            IReadOnlyList<Vector3> route,
            float sInit,
            State[] states)
        {
            if (states == null || states.Length < 2) return -1;
            Scene006RouteGeometry.RouteSample sample =
                Scene006RouteGeometry.SampleClosedRoute(route, sInit);
            int initialIndex = sample.NextWaypointIndex;
            Vector3 start = states[0].Position;
            // Re-derive the index evolution; the trace states do not carry
            // it, so replay the pause/advance rule positions-only.
            int waypointIndex = initialIndex;
            Vector3 position = start;
            bool indexAdvanced = false;
            for (int k = 1; k < states.Length; k++)
            {
                Vector3 destination = route[waypointIndex];
                Vector3 delta = destination - position;
                delta.y = 0f;
                if (delta.magnitude < WaypointPauseDistanceM)
                {
                    waypointIndex = (waypointIndex + 1) % route.Count;
                }
                else
                {
                    position = states[k].Position;
                }
                if (waypointIndex != initialIndex)
                {
                    indexAdvanced = true;
                    continue;
                }
                if (!indexAdvanced) continue;
                Vector3 gap = states[k].Position - start;
                gap.y = 0f;
                if (gap.magnitude < WaypointPauseDistanceM) return k;
            }
            return -1;
        }

        /// <summary>
        /// SHA-256 binding over the whole trace (§5.2.2). Canonical byte
        /// layout per state k: int32-LE k, then float32-LE bit patterns of
        /// position x/y/z and quaternion x/y/z/w. Any float difference in
        /// any state changes the hash.
        /// </summary>
        public static string HashStates(IReadOnlyList<State> states)
        {
            if (states == null) throw new ArgumentNullException(nameof(states));
            var bytes = new List<byte>(states.Count * 32);
            for (int k = 0; k < states.Count; k++)
            {
                AppendInt32(bytes, k);
                AppendFloat(bytes, states[k].Position.x);
                AppendFloat(bytes, states[k].Position.y);
                AppendFloat(bytes, states[k].Position.z);
                AppendFloat(bytes, states[k].Rotation.x);
                AppendFloat(bytes, states[k].Rotation.y);
                AppendFloat(bytes, states[k].Rotation.z);
                AppendFloat(bytes, states[k].Rotation.w);
            }
            return Scene006RouteGeometry.Sha256Hex(bytes.ToArray());
        }

        static void AppendInt32(List<byte> bytes, int value)
        {
            bytes.Add((byte)(value & 0xFF));
            bytes.Add((byte)((value >> 8) & 0xFF));
            bytes.Add((byte)((value >> 16) & 0xFF));
            bytes.Add((byte)((value >> 24) & 0xFF));
        }

        static void AppendFloat(List<byte> bytes, float value)
        {
            AppendInt32(bytes, BitConverter.SingleToInt32Bits(value));
        }
    }
}
