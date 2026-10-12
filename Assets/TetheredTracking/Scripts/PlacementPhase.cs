using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace TetheredTracking
{
    public sealed class PlacementPhaseGuard
    {
        public bool MeasurementStarted { get; private set; }
        public string MeasurementBoundary { get; private set; }

        public void RequirePlacementAllowed(string operation)
        {
            if (MeasurementStarted)
                throw new InvalidOperationException(
                    $"Placement operation '{operation}' is forbidden after "
                    + $"measurement boundary '{MeasurementBoundary}'.");
        }

        public void StartMeasurement(string boundary)
        {
            if (string.IsNullOrWhiteSpace(boundary))
                throw new ArgumentException(
                    "Measurement boundary is required.",
                    nameof(boundary));
            if (MeasurementStarted) return;
            MeasurementStarted = true;
            MeasurementBoundary = boundary;
        }
    }

    public sealed class PlacementJumpDiagnostic : MonoBehaviour
    {
        [Serializable]
        public sealed class JumpEvent
        {
            public string actor_name;
            public int frame;
            public float displacement_m;
            public float allowed_displacement_m;
            public float delta_time_s;
        }

        [Serializable]
        sealed class Report
        {
            public string schema_version = "p1-scene-placement-jumps/v1";
            public string scenario_id;
            public int checked_frames;
            public int jump_count;
            public JumpEvent[] jumps;
        }

        sealed class ActorState
        {
            public Transform transform;
            public float configuredSpeed;
            public Vector3 previous;
        }

        string scenarioId;
        float epsilon;
        int checkedFrames;
        string outputPath;
        readonly List<ActorState> actors = new List<ActorState>();
        readonly List<JumpEvent> jumps = new List<JumpEvent>();

        public void Configure(
            string configuredScenarioId,
            IEnumerable<Transform> configuredActors,
            IEnumerable<float> configuredSpeeds,
            float configuredEpsilon,
            string configuredOutputPath = null)
        {
            if (configuredActors == null)
                throw new ArgumentNullException(nameof(configuredActors));
            if (configuredSpeeds == null)
                throw new ArgumentNullException(nameof(configuredSpeeds));
            if (!IsNonNegativeFinite(configuredEpsilon))
                throw new ArgumentException(
                    "Jump epsilon must be finite and non-negative.",
                    nameof(configuredEpsilon));
            Transform[] actorArray = configuredActors.ToArray();
            float[] speedArray = configuredSpeeds.ToArray();
            if (actorArray.Length == 0 || actorArray.Length != speedArray.Length)
                throw new ArgumentException(
                    "Actors and configured speeds must have the same non-zero length.");
            actors.Clear();
            for (int index = 0; index < actorArray.Length; index++)
            {
                Transform actor = actorArray[index];
                if (actor == null || !IsNonNegativeFinite(speedArray[index]))
                    throw new ArgumentException(
                        "Jump diagnostic actors/speeds contain an invalid value.");
                actors.Add(new ActorState
                {
                    transform = actor,
                    configuredSpeed = speedArray[index],
                    previous = actor.position,
                });
            }
            scenarioId = configuredScenarioId;
            epsilon = configuredEpsilon;
            outputPath = configuredOutputPath
                ?? RuntimePaths.File("placement_jump_diagnostic.json");
            checkedFrames = 0;
            jumps.Clear();
            Write();
        }

        void LateUpdate()
        {
            Sample(Time.deltaTime, Time.frameCount);
        }

        internal void Sample(float deltaTime, int frame)
        {
            if (!IsNonNegativeFinite(deltaTime))
                throw new ArgumentException(
                    "Diagnostic delta time must be finite and non-negative.",
                    nameof(deltaTime));
            checkedFrames++;
            foreach (ActorState actor in actors)
            {
                float displacement = Vector3.Distance(
                    actor.previous,
                    actor.transform.position);
                float allowed = AllowedDisplacement(
                    actor.configuredSpeed,
                    deltaTime,
                    epsilon);
                if (displacement > allowed)
                {
                    jumps.Add(new JumpEvent
                    {
                        actor_name = actor.transform.name,
                        frame = frame,
                        displacement_m = displacement,
                        allowed_displacement_m = allowed,
                        delta_time_s = deltaTime,
                    });
                }
                actor.previous = actor.transform.position;
            }
            Write();
        }

        internal static float AllowedDisplacement(
            float configuredSpeed,
            float deltaTime,
            float epsilon)
        {
            if (!IsNonNegativeFinite(configuredSpeed)
                || !IsNonNegativeFinite(deltaTime)
                || !IsNonNegativeFinite(epsilon))
            {
                throw new ArgumentException(
                    "Speed, delta time, and epsilon must be finite and non-negative.");
            }
            return 2f * configuredSpeed * deltaTime + epsilon;
        }

        void Write()
        {
            AtomicFile.WriteAllText(
                outputPath,
                JsonUtility.ToJson(new Report
                {
                    scenario_id = scenarioId,
                    checked_frames = checkedFrames,
                    jump_count = jumps.Count,
                    jumps = jumps.ToArray(),
                }, true) + "\n");
        }

        static bool IsNonNegativeFinite(float value)
        {
            return value >= 0f && !float.IsNaN(value) && !float.IsInfinity(value);
        }
    }
}
