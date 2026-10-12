using UnityEngine;

namespace TetheredTracking
{
    // Minimal kinematic plant constrained by a physical tether sphere.
    // P1-ENG-FRAME-001 Part T: the tether is switchable. With it enabled the
    // step below is the pre-existing code path, unchanged; with it disabled
    // there is no sphere clamp, TetherSaturated stays false, the altitude
    // band is not capped by the cable length, and an optional horizontal
    // geofence rectangle is a hard clamp (it also applies, stacked, when the
    // tether is enabled and a geofence is configured).
    public class TetheredDronePlant : MonoBehaviour
    {
        public Vector3 anchor = new Vector3(132f, 0f, 117f);
        public float tetherLength = 35f;
        public float minimumAltitude = 8f;
        public float maximumAltitude = 32f;
        public float maximumSpeed = 4f;
        public float maximumAcceleration = 4f;
        public float yawRate = 120f;
        public bool tetherEnabled = true;
        public bool geofenceEnabled;
        public float geofenceMinX;
        public float geofenceMaxX;
        public float geofenceMinZ;
        public float geofenceMaxZ;

        public Vector3 CommandedVelocity { get; private set; }
        public Vector3 AppliedVelocity { get; private set; }
        public bool TetherSaturated { get; private set; }

        public void SetVelocity(Vector3 worldVelocity)
        {
            CommandedVelocity = Vector3.ClampMagnitude(worldVelocity, maximumSpeed);
        }

        public void Hold()
        {
            CommandedVelocity = Vector3.zero;
        }

        void Update()
        {
            Step(Time.deltaTime);
        }

        /// <summary>
        /// Sets the optional horizontal geofence from the scenario
        /// (<c>null</c> = no geofence). Bounds were validated by
        /// <see cref="ScenarioConfig"/>.
        /// </summary>
        public void ConfigureGeofence(GeofenceScenarioConfig fence)
        {
            geofenceEnabled = fence != null;
            if (fence == null) return;
            geofenceMinX = fence.min_x;
            geofenceMaxX = fence.max_x;
            geofenceMinZ = fence.min_z;
            geofenceMaxZ = fence.max_z;
        }

        internal void Step(float deltaTime)
        {
            AppliedVelocity = Vector3.MoveTowards(
                AppliedVelocity, CommandedVelocity, maximumAcceleration * deltaTime);
            Vector3 next = transform.position + AppliedVelocity * deltaTime;
            Vector3 relative = next - anchor;
            if (tetherEnabled)
            {
                TetherSaturated = relative.magnitude > tetherLength;

                float vertical = Mathf.Clamp(relative.y, minimumAltitude, maximumAltitude);
                vertical = Mathf.Min(vertical, tetherLength);
                Vector2 horizontal = new Vector2(relative.x, relative.z);
                float maximumHorizontal = Mathf.Sqrt(Mathf.Max(0f, tetherLength * tetherLength - vertical * vertical));
                if (horizontal.magnitude > maximumHorizontal)
                {
                    horizontal = horizontal.normalized * maximumHorizontal;
                    TetherSaturated = true;
                }
                next = anchor + new Vector3(horizontal.x, vertical, horizontal.y);
            }
            else
            {
                TetherSaturated = false;
                float vertical = Mathf.Clamp(relative.y, minimumAltitude, maximumAltitude);
                next = anchor + new Vector3(relative.x, vertical, relative.z);
            }
            if (geofenceEnabled)
            {
                next.x = Mathf.Clamp(next.x, geofenceMinX, geofenceMaxX);
                next.z = Mathf.Clamp(next.z, geofenceMinZ, geofenceMaxZ);
            }

            transform.position = next;
            Vector3 horizontalVelocity = new Vector3(AppliedVelocity.x, 0f, AppliedVelocity.z);
            if (horizontalVelocity.sqrMagnitude > 0.0001f)
            {
                float yaw = Mathf.Atan2(horizontalVelocity.x, horizontalVelocity.z) * Mathf.Rad2Deg;
                transform.rotation = Quaternion.RotateTowards(
                    transform.rotation, Quaternion.Euler(0f, yaw, 0f), yawRate * deltaTime);
            }
        }
    }
}
