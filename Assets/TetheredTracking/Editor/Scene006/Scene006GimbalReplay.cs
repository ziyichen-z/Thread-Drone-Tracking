using UnityEngine;

namespace TetheredTracking.Scene006
{
    /// <summary>
    /// §5.2.4/§5.2.5 frozen gimbal semantics for the offline evaluation
    /// domain: a truth-directed evaluation upper bound that exists only
    /// inside this tool and never enters any runtime controller.
    ///
    /// The per-sample update replicates TetheredGimbal.LateUpdate
    /// (Scripts/TetheredGimbal.cs:27-46) literally with dt = 0.2 s and
    /// HasTarget always true: LookAtWorld(target truth position) sets the
    /// target; requested = atan2(horizontal, max(0.1, -delta.y));
    /// applied = min(requested, 45 deg); yaw holds when horizontal
    /// &lt;= 0.001 else atan2(delta.x, delta.z);
    /// desired = Euler(90 - applied, yaw, 0);
    /// rotation = RotateTowards(rotation, desired, 120 * 0.2 = 24 deg) on
    /// the quaternion geodesic including the yaw component. The evaluated
    /// camera pose is the post-update rotation. s_0 is evaluated under the
    /// frozen initial quaternion with no gimbal update.
    ///
    /// The frozen initial quaternion is Quaternion.Euler(90, 0, 0), matching
    /// the bootstrap camera initialization
    /// (Scripts/TetheredScenarioBootstrap.cs:201). LookNadir() only clears
    /// HasTarget and never rotates the transform, so it cannot substitute
    /// for this explicit initial state.
    /// </summary>
    public static class Scene006GimbalReplay
    {
        public const float MaximumOffNadirDeg = 45f;
        public const float SlewRateDegPerSecond = 120f;
        public const float StepSeconds = 0.2f;

        public static Quaternion InitialRotation => Quaternion.Euler(90f, 0f, 0f);

        /// <summary>
        /// The law's <c>applied</c> off-nadir angle — `requested` clamped to
        /// the 45 deg limit — for one (gimbal, target) pair. Split out of
        /// <see cref="Update"/> without changing its arithmetic so the
        /// prompt-law v2 selection tool reads the same single definition
        /// instead of restating it (§3.2.3e).
        /// </summary>
        public static float AppliedOffNadirDeg(
            Vector3 gimbalPosition,
            Vector3 targetWorld)
        {
            Vector3 delta = targetWorld - gimbalPosition;
            float horizontal = new Vector2(delta.x, delta.z).magnitude;
            float height = Mathf.Max(0.1f, -delta.y);
            float requested = Mathf.Atan2(horizontal, height) * Mathf.Rad2Deg;
            return Mathf.Min(requested, MaximumOffNadirDeg);
        }

        public static Quaternion Update(
            Quaternion current,
            Vector3 gimbalPosition,
            Vector3 targetWorld,
            float dt = StepSeconds)
        {
            Vector3 delta = targetWorld - gimbalPosition;
            float horizontal = new Vector2(delta.x, delta.z).magnitude;
            float applied = AppliedOffNadirDeg(gimbalPosition, targetWorld);
            float yaw = horizontal > 0.001f
                ? Mathf.Atan2(delta.x, delta.z) * Mathf.Rad2Deg
                : current.eulerAngles.y;
            Quaternion desired = Quaternion.Euler(90f - applied, yaw, 0f);
            return Quaternion.RotateTowards(
                current, desired, SlewRateDegPerSecond * dt);
        }
    }
}
