using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    public class GimbalCommandReceiver : MonoBehaviour
    {
        [Serializable] class Point { public float x; public float y; public float z; }
        [Serializable] class Command { public string mode; public Point target_world_m; }
        [Serializable] class Packet
        {
            public string channel;
            public long command_id;
            public double issued_unix_s;
            public float expires_after_s;
            public Command command;
        }

        public float pollInterval = 0.05f;
        private float timer;
        private long lastId = long.MinValue;
        private RateStudyExperimentController experimentOverride;
        private TetheredGimbal gimbalOverride;

        void Update()
        {
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            RateStudyExperimentController experiment =
                experimentOverride ?? scenario?.ExperimentController;
            TetheredGimbal gimbal = gimbalOverride ?? scenario?.Gimbal;
            if (experiment != null && !experiment.ControlEnabled)
                gimbal?.LookNadir();
            timer += Time.deltaTime;
            if (timer < pollInterval) return;
            timer = 0f;
            ReadCommand();
        }

        void ReadCommand()
        {
            string path = RuntimePaths.File("gimbal_command.json");
            if (!File.Exists(path)) return;
            string json;
            try
            {
                using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (var reader = new StreamReader(stream)) json = reader.ReadToEnd();
            }
            catch (IOException) { return; }
            Packet packet;
            try { packet = JsonUtility.FromJson<Packet>(json); }
            catch (Exception) { return; }
            if (packet == null || packet.channel != "gimbal" || packet.command == null) return;
            if (packet.command_id == lastId || Expired(packet)) return;
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            RateStudyExperimentController experiment =
                experimentOverride ?? scenario?.ExperimentController;
            TetheredGimbal gimbal = gimbalOverride ?? scenario?.Gimbal;
            if (gimbal == null) return;
            lastId = packet.command_id;
            if (experiment != null
                && !experiment.AuthorizeControl("gimbal", packet.command_id))
            {
                gimbal.LookNadir();
                return;
            }
            if (packet.command.mode == "look_at_world" && packet.command.target_world_m != null)
            {
                Point point = packet.command.target_world_m;
                gimbal.LookAtWorld(new Vector3(point.x, point.y, point.z));
            }
            else if (packet.command.mode == "nadir") gimbal.LookNadir();
        }

        internal void ConfigureForTests(
            RateStudyExperimentController experiment,
            TetheredGimbal gimbal)
        {
            experimentOverride = experiment;
            gimbalOverride = gimbal;
        }

        static bool Expired(Packet packet)
        {
            double now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
            return packet.expires_after_s > 0f && now > packet.issued_unix_s + packet.expires_after_s;
        }
    }
}
