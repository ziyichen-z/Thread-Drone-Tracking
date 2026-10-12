using UnityEngine;

namespace TetheredTracking
{
    // Independent world-frame camera pointing. Body yaw never changes the
    // requested view direction because the camera rotation is set absolutely.
    public class TetheredGimbal : MonoBehaviour
    {
        public float maximumOffNadirDeg = 45f;
        public float slewRateDegPerSecond = 120f;

        public bool HasTarget { get; private set; }
        public Vector3 TargetWorld { get; private set; }
        public bool Saturated { get; private set; }

        public void LookAtWorld(Vector3 target)
        {
            TargetWorld = target;
            HasTarget = true;
        }

        public void LookNadir()
        {
            HasTarget = false;
        }

        void LateUpdate()
        {
            Quaternion desired = Quaternion.Euler(90f, 0f, 0f);
            Saturated = false;
            if (HasTarget)
            {
                Vector3 delta = TargetWorld - transform.position;
                float horizontal = new Vector2(delta.x, delta.z).magnitude;
                float height = Mathf.Max(0.1f, -delta.y);
                float requested = Mathf.Atan2(horizontal, height) * Mathf.Rad2Deg;
                float applied = Mathf.Min(requested, maximumOffNadirDeg);
                Saturated = requested > maximumOffNadirDeg + 0.1f;
                float yaw = horizontal > 0.001f
                    ? Mathf.Atan2(delta.x, delta.z) * Mathf.Rad2Deg
                    : transform.eulerAngles.y;
                desired = Quaternion.Euler(90f - applied, yaw, 0f);
            }
            transform.rotation = Quaternion.RotateTowards(
                transform.rotation, desired, slewRateDegPerSecond * Time.deltaTime);
        }
    }
}
