using UnityEngine;

namespace TetheredTracking
{
    [RequireComponent(typeof(LineRenderer))]
    public class TetherLineVisual : MonoBehaviour
    {
        public Transform drone;
        public Vector3 anchor;
        private LineRenderer line;

        void Awake()
        {
            line = GetComponent<LineRenderer>();
            line.positionCount = 2;
            line.startWidth = 0.12f;
            line.endWidth = 0.06f;
            line.material = new Material(Shader.Find("Sprites/Default"));
            line.startColor = new Color(0.15f, 0.15f, 0.15f);
            line.endColor = new Color(0.25f, 0.25f, 0.25f);
        }

        void LateUpdate()
        {
            if (drone == null) return;
            line.SetPosition(0, anchor);
            line.SetPosition(1, drone.position);
        }
    }
}
