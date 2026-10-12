using System;
using System.IO;
using UnityEngine;

namespace TetheredTracking
{
    public class BodyCommandReceiver : MonoBehaviour
    {
        [Serializable] class VectorXYZ { public float x; public float y; public float z; }
        [Serializable] class Command { public string mode; public VectorXYZ velocity_world_mps; }
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
        private Packet active;
        private RateStudyExperimentController experimentOverride;
        private TetheredDronePlant droneOverride;

        void Update()
        {
            timer += Time.deltaTime;
            if (timer >= pollInterval)
            {
                timer = 0f;
                ReadCommand();
            }

            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            TetheredDronePlant drone = droneOverride ?? scenario?.Drone;
            if (drone == null) return;
            RateStudyExperimentController experiment =
                experimentOverride ?? scenario?.ExperimentController;
            if (experiment != null && !experiment.ControlEnabled)
            {
                drone.Hold();
                active = null;
                return;
            }
            if (active == null || Expired(active) || active.command == null)
            {
                drone.Hold();
                return;
            }
            if (active.command.mode == "velocity_world" && active.command.velocity_world_mps != null)
            {
                drone.SetVelocity(new Vector3(
                    active.command.velocity_world_mps.x,
                    active.command.velocity_world_mps.y,
                    active.command.velocity_world_mps.z));
            }
            else drone.Hold();
        }

        void ReadCommand()
        {
            string path = RuntimePaths.File("body_command.json");
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
            if (packet == null || packet.channel != "body" || packet.command == null) return;
            if (packet.command_id == lastId || Expired(packet)) return;
            lastId = packet.command_id;
            TetheredScenarioBootstrap scenario = TetheredScenarioBootstrap.Instance;
            RateStudyExperimentController experiment =
                experimentOverride ?? scenario?.ExperimentController;
            if (experiment != null
                && !experiment.AuthorizeControl("body", packet.command_id))
            {
                active = null;
                return;
            }
            active = packet;
        }

        internal void ConfigureForTests(
            RateStudyExperimentController experiment,
            TetheredDronePlant drone)
        {
            experimentOverride = experiment;
            droneOverride = drone;
        }

        static bool Expired(Packet packet)
        {
            double now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
            return packet.expires_after_s > 0f && now > packet.issued_unix_s + packet.expires_after_s;
        }
    }
}
