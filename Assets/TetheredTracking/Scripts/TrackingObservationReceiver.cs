using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    [Serializable]
    public class NormalizedBoundingBox
    {
        public float x;
        public float y;
        public float width;
        public float height;
    }

    public readonly struct TrackingObservation
    {
        public readonly long FrameId;
        public readonly string TrackId;
        public readonly NormalizedBoundingBox Box;
        public readonly float Confidence;
        public readonly double PublishedUnixSeconds;

        public TrackingObservation(
            long frameId,
            string trackId,
            NormalizedBoundingBox box,
            float confidence,
            double publishedUnixSeconds)
        {
            FrameId = frameId;
            TrackId = trackId;
            Box = box;
            Confidence = confidence;
            PublishedUnixSeconds = publishedUnixSeconds;
        }
    }

    public class TrackingObservationReceiver : MonoBehaviour
    {
        [Serializable]
        class ObservationPayload
        {
            public long frame_id;
            public string track_id;
            public NormalizedBoundingBox bbox_xywh_norm;
            public float confidence;
        }

        [Serializable]
        class ObservationPacket
        {
            public string protocol;
            public string channel;
            public long command_id;
            public double issued_unix_s;
            public float expires_after_s;
            public ObservationPayload observation;
        }

        public event Action<TrackingObservation> ObservationReceived;

        public float pollInterval = 0.02f;
        float timer;
        long lastCommandId = long.MinValue;

        void Update()
        {
            timer += Time.deltaTime;
            if (timer < pollInterval) return;
            timer = 0f;
            ReadObservation();
        }

        void ReadObservation()
        {
            string path = RuntimePaths.File("tracking_observation.json");
            if (!File.Exists(path)) return;
            string json;
            try
            {
                using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
                using var reader = new StreamReader(stream);
                json = reader.ReadToEnd();
            }
            catch (IOException) { return; }

            ObservationPacket packet;
            try { packet = JsonUtility.FromJson<ObservationPacket>(json); }
            catch (Exception) { return; }
            if (!Valid(packet) || packet.command_id == lastCommandId) return;

            lastCommandId = packet.command_id;
            ObservationPayload observation = packet.observation;
            ObservationReceived?.Invoke(new TrackingObservation(
                observation.frame_id,
                observation.track_id,
                observation.bbox_xywh_norm,
                Mathf.Clamp01(observation.confidence),
                packet.issued_unix_s));
        }

        static bool Valid(ObservationPacket packet)
        {
            if (packet == null || packet.protocol != "tethered-tracking-observation/v1"
                || packet.channel != "tracking_observation" || packet.observation == null) return false;
            if (packet.expires_after_s > 0f && UnixNow() > packet.issued_unix_s + packet.expires_after_s)
                return false;
            ObservationPayload observation = packet.observation;
            NormalizedBoundingBox box = observation.bbox_xywh_norm;
            if (observation.frame_id < 0 || string.IsNullOrWhiteSpace(observation.track_id) || box == null)
                return false;
            return Finite(box.x) && Finite(box.y) && Finite(box.width) && Finite(box.height)
                && Finite(observation.confidence)
                && box.x >= 0f && box.y >= 0f
                && box.width > 0f && box.height > 0f
                && box.x + box.width <= 1f
                && box.y + box.height <= 1f;
        }

        static bool Finite(float value) => !float.IsNaN(value) && !float.IsInfinity(value);

        static double UnixNow() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
    }
}
