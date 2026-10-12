using UnityEngine;

namespace TetheredTracking
{
    public class LoopTargetVehicle : MonoBehaviour
    {
        public string trackId = "target-0";
        public float speed = 2f;
        public float turnRate = 240f;
        public Vector3[] waypoints;
        public bool MotionEnabled { get; private set; } = true;
        private int waypointIndex;
        PlacementPhaseGuard placementGuard;

        public void Configure(Vector3[] route)
        {
            waypoints = route;
            waypointIndex = 1;
            if (route != null && route.Length > 0)
                transform.position = route[0];
        }

        public void Configure(string configuredTrackId, Vector3[] route, float configuredSpeed)
        {
            trackId = configuredTrackId;
            speed = Mathf.Max(0f, configuredSpeed);
            Configure(route);
        }

        internal void SetPlacementGuard(PlacementPhaseGuard guard)
        {
            placementGuard = guard ?? throw new System.ArgumentNullException(nameof(guard));
        }

        public void SetMotionEnabled(bool enabled)
        {
            MotionEnabled = enabled;
        }

        internal void PlaceAtRouteDistance(float distanceMeters)
        {
            placementGuard?.RequirePlacementAllowed("target.PlaceAtRouteDistance");
            if (waypoints == null || waypoints.Length < 2)
                throw new System.InvalidOperationException("Target route is not configured.");
            float perimeter = RateStudyScouting.ClosedRoutePerimeter(waypoints);
            if (distanceMeters < 0f || distanceMeters >= perimeter)
                throw new System.ArgumentOutOfRangeException(
                    nameof(distanceMeters),
                    "Frozen route distance must satisfy 0 <= s < perimeter.");
            RateStudyScouting.RouteSample sample =
                RateStudyScouting.SampleClosedRoute(waypoints, distanceMeters);
            transform.position = sample.Position;
            waypointIndex = sample.NextWaypointIndex;
            Vector3 direction = waypoints[waypointIndex] - transform.position;
            direction.y = 0f;
            if (direction.sqrMagnitude > 0.0001f)
                transform.rotation = Quaternion.LookRotation(direction.normalized);
        }

        void Update()
        {
            Step(Time.deltaTime);
        }

        internal void Step(float deltaTime)
        {
            if (!MotionEnabled) return;
            if (waypoints == null || waypoints.Length < 2) return;
            Vector3 destination = waypoints[waypointIndex];
            Vector3 delta = destination - transform.position;
            delta.y = 0f;
            if (delta.magnitude < 0.5f)
            {
                waypointIndex = (waypointIndex + 1) % waypoints.Length;
                return;
            }
            Vector3 direction = delta.normalized;
            transform.position += direction * speed * deltaTime;
            transform.rotation = Quaternion.RotateTowards(
                transform.rotation, Quaternion.LookRotation(direction), turnRate * deltaTime);
        }
    }
}
