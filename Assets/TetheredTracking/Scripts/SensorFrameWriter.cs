using System;
using System.IO;
using DiagnosticsStopwatch = System.Diagnostics.Stopwatch;
using UnityEngine;
using UnityEngine.Rendering;

namespace TetheredTracking
{
    public readonly struct SensorFrameInfo
    {
        public readonly long FrameId;
        public readonly float SimulationTimeSeconds;
        public readonly float DeltaSimulationSeconds;
        public readonly double CaptureUnixSeconds;
        public readonly double CaptureMonotonicSeconds;

        public SensorFrameInfo(
            long frameId,
            float simulationTimeSeconds,
            float deltaSimulationSeconds,
            double captureUnixSeconds,
            double captureMonotonicSeconds)
        {
            FrameId = frameId;
            SimulationTimeSeconds = simulationTimeSeconds;
            DeltaSimulationSeconds = deltaSimulationSeconds;
            CaptureUnixSeconds = captureUnixSeconds;
            CaptureMonotonicSeconds = captureMonotonicSeconds;
        }
    }

    public class SensorFrameWriter : MonoBehaviour
    {
        [Serializable]
        internal class CameraIntrinsics
        {
            public float fx;
            public float fy;
            public float cx;
            public float cy;
        }

        [Serializable]
        internal class FrameMetadata
        {
            public string schema_version = "tethered-sensor-frame/v1";
            public string scenario_id;
            public long frame_id;
            public float simulation_time_s;
            public double capture_unix_s;
            public float[] camera_position_world_m;
            public float[] camera_rotation_xyzw;
            public float[] camera_forward_world;
            public float[] camera_right_world;
            public float[] camera_up_world;
            public float vertical_fov_deg;
            public float horizontal_fov_deg;
            public int width;
            public int height;
            public CameraIntrinsics intrinsics_px;
            public bool gimbal_saturated;
            public bool tether_saturated;
        }

        [Serializable]
        internal sealed class FrameMetadataV2 : FrameMetadata
        {
            public double capture_monotonic_s;

            public FrameMetadataV2()
            {
                schema_version = "tethered-sensor-frame/v2";
            }
        }

        [Serializable]
        internal sealed class FrameMetadataV3 : FrameMetadata
        {
            public double capture_monotonic_s;
            public string capture_monotonic_clock_id = SharedHostClockId;

            public FrameMetadataV3()
            {
                schema_version = "tethered-sensor-frame/v3";
            }
        }

        internal const string SharedHostClockId = "system-stopwatch/v1";

        [Serializable]
        class FrameManifest
        {
            public string schema_version = "tethered-frame-manifest/v1";
            public long frame_id;
            public string image_file;
            public string metadata_file;
            public double published_unix_s;
        }

        public event Action<SensorFrameInfo> FramePublished;

        public float captureInterval = 0.2f;
        public int width = 640;
        public int height = 480;
        public int jpegQuality = 85;
        public int retainedFrameCount = 128;
        public long LastPublishedFrameId { get; private set; } = -1;
        public double CurrentSimulationTimeSeconds =>
            Math.Max(Time.timeAsDouble - startTime, 0.0);

        float timer;
        float startTime;
        float previousCaptureTime;
        long frameIndex;
        RenderTexture renderTexture;
        Texture2D texture;
        bool captureSupported = true;

        public void Configure(SensorScenarioConfig config)
        {
            width = config.width;
            height = config.height;
            jpegQuality = config.jpeg_quality;
            retainedFrameCount = config.retained_frame_count;
            captureInterval = 1f / config.capture_hz;
        }

        void Start()
        {
            startTime = Time.time;
            previousCaptureTime = startTime;
            Directory.CreateDirectory(RuntimePaths.File("frames"));
            captureSupported = SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null;
            if (!captureSupported)
            {
                Debug.LogWarning(
                    "Sensor frame capture is disabled because no graphics device is available.");
                return;
            }
            renderTexture = new RenderTexture(width, height, 24);
            texture = new Texture2D(width, height, TextureFormat.RGB24, false);
        }

        void Update()
        {
            if (!captureSupported) return;
            timer += Time.deltaTime;
            if (timer < captureInterval) return;
            timer -= captureInterval;
            Capture();
        }

        void OnDestroy()
        {
            if (texture != null) Destroy(texture);
            if (renderTexture != null) Destroy(renderTexture);
        }

        void Capture()
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            Camera camera = scenario?.SensorCamera;
            TetheredDronePlant drone = scenario?.Drone;
            if (camera == null || drone == null || renderTexture == null || texture == null) return;

            camera.targetTexture = renderTexture;
            camera.Render();
            RenderTexture previousActive = RenderTexture.active;
            RenderTexture.active = renderTexture;
            texture.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            texture.Apply();
            byte[] bytes = texture.EncodeToJPG(jpegQuality);
            camera.targetTexture = null;
            RenderTexture.active = previousActive;

            long publishedFrameId = frameIndex++;
            float simulationTime = Time.time - startTime;
            float deltaSimulation = Mathf.Max(Time.time - previousCaptureTime, 0f);
            previousCaptureTime = Time.time;
            double captureUnix = UnixNow();
            string framesDirectory = RuntimePaths.File("frames");

            bool rateStudyV2 = scenario.ExperimentController != null
                && scenario.ExperimentController.IsActive
                && !scenario.ExperimentController.UsesSharedHostClock;
            double captureMonotonic = rateStudyV2
                ? Time.realtimeSinceStartupAsDouble
                : HostMonotonicSeconds();
            FrameMetadata metadata = BuildMetadata(
                scenario,
                camera,
                drone,
                publishedFrameId,
                simulationTime,
                captureUnix,
                captureMonotonic,
                rateStudyV2);
            PublishFrameBundle(
                framesDirectory,
                publishedFrameId,
                bytes,
                JsonUtility.ToJson(metadata, true) + "\n",
                UnixNow());

            LastPublishedFrameId = publishedFrameId;
            FramePublished?.Invoke(new SensorFrameInfo(
                publishedFrameId,
                simulationTime,
                deltaSimulation,
                captureUnix,
                captureMonotonic));
            DeleteExpiredFrame(framesDirectory, publishedFrameId - retainedFrameCount);
        }

        internal static void PublishFrameBundle(
            string framesDirectory,
            long publishedFrameId,
            byte[] imageBytes,
            string metadataJson,
            double publishedUnixSeconds)
        {
            string stem = "frame_" + publishedFrameId.ToString("D10");
            string imageName = stem + ".jpg";
            string metadataName = stem + ".json";
            AtomicFile.WriteAllBytes(Path.Combine(framesDirectory, imageName), imageBytes);
            AtomicFile.WriteAllText(Path.Combine(framesDirectory, metadataName), metadataJson);

            var manifest = new FrameManifest
            {
                frame_id = publishedFrameId,
                image_file = imageName,
                metadata_file = metadataName,
                published_unix_s = publishedUnixSeconds,
            };
            AtomicFile.WriteAllText(
                Path.Combine(framesDirectory, "latest.json"),
                JsonUtility.ToJson(manifest, true) + "\n");
        }

        FrameMetadata BuildMetadata(
            TetheredScenarioBootstrap scenario,
            Camera camera,
            TetheredDronePlant drone,
            long publishedFrameId,
            float simulationTime,
            double captureUnix,
            double captureMonotonic,
            bool rateStudyV2)
        {
            Vector3 position = camera.transform.position;
            Quaternion rotation = camera.transform.rotation;
            float verticalRadians = camera.fieldOfView * Mathf.Deg2Rad;
            float horizontalFov = 2f * Mathf.Atan(
                Mathf.Tan(verticalRadians * 0.5f) * width / (float)height) * Mathf.Rad2Deg;
            float focalPixels = 0.5f * height / Mathf.Tan(verticalRadians * 0.5f);
            FrameMetadata metadata = rateStudyV2
                ? new FrameMetadataV2 { capture_monotonic_s = captureMonotonic }
                : new FrameMetadataV3 { capture_monotonic_s = captureMonotonic };
            metadata.scenario_id = scenario.Config.scenario_id;
            metadata.frame_id = publishedFrameId;
            metadata.simulation_time_s = simulationTime;
            metadata.capture_unix_s = captureUnix;
            metadata.camera_position_world_m = V(position);
            metadata.camera_rotation_xyzw =
                new[] { rotation.x, rotation.y, rotation.z, rotation.w };
            metadata.camera_forward_world = V(camera.transform.forward);
            metadata.camera_right_world = V(camera.transform.right);
            metadata.camera_up_world = V(camera.transform.up);
            metadata.vertical_fov_deg = camera.fieldOfView;
            metadata.horizontal_fov_deg = horizontalFov;
            metadata.width = width;
            metadata.height = height;
            metadata.intrinsics_px = new CameraIntrinsics
            {
                fx = focalPixels,
                fy = focalPixels,
                cx = width * 0.5f,
                cy = height * 0.5f,
            };
            metadata.gimbal_saturated = scenario.Gimbal.Saturated;
            metadata.tether_saturated = drone.TetherSaturated;
            return metadata;
        }

        static void DeleteExpiredFrame(string directory, long frameId)
        {
            if (frameId < 0) return;
            string stem = "frame_" + frameId.ToString("D10");
            DeleteIfPresent(Path.Combine(directory, stem + ".jpg"));
            DeleteIfPresent(Path.Combine(directory, stem + ".json"));
        }

        static void DeleteIfPresent(string path)
        {
            try { if (File.Exists(path)) File.Delete(path); }
            catch (IOException exception) { Debug.LogWarning($"Could not delete old frame {path}: {exception.Message}"); }
        }

        static float[] V(Vector3 value) => new[] { value.x, value.y, value.z };

        internal static double HostMonotonicSeconds() =>
            DiagnosticsStopwatch.GetTimestamp() / (double)DiagnosticsStopwatch.Frequency;

        static double UnixNow() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
    }
}
