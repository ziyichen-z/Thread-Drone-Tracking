using System;
using UnityEngine;

namespace TetheredTracking
{
    /// <summary>
    /// Read-only upper-right HUD for the sensor frame simulation clock.
    /// It does not own time and does not feed any runtime decision.
    /// </summary>
    public sealed class SimulationTimerHud : MonoBehaviour
    {
        const float Margin = 10f;
        const float PanelWidth = 230f;
        const float PanelHeight = 70f;

        SensorFrameWriter frameWriter;
        GUIStyle labelStyle;

        public void Configure(SensorFrameWriter configuredFrameWriter)
        {
            frameWriter = configuredFrameWriter;
        }

        internal static string FormatElapsed(double seconds)
        {
            if (double.IsNaN(seconds)
                || double.IsInfinity(seconds)
                || seconds < 0.0)
            {
                seconds = 0.0;
            }

            long totalTenths = (long)Math.Floor(seconds * 10.0 + 0.5);
            long wholeMinutes = totalTenths / 600;
            long remainingTenths = totalTenths % 600;
            long wholeSeconds = remainingTenths / 10;
            long tenths = remainingTenths % 10;
            return $"{wholeMinutes:D2}:{wholeSeconds:D2}.{tenths}";
        }

        internal static Rect TimerRect(float screenWidth)
        {
            return new Rect(
                Mathf.Max(Margin, screenWidth - PanelWidth - Margin),
                Margin,
                PanelWidth,
                PanelHeight);
        }

        void OnGUI()
        {
            if (frameWriter == null) return;

            Rect panel = TimerRect(Screen.width);
            GUI.Box(panel, GUIContent.none);
            if (labelStyle == null)
            {
                labelStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleCenter,
                    fontSize = 18,
                    fontStyle = FontStyle.Bold,
                };
                labelStyle.normal.textColor = Color.white;
            }

            GUI.Label(
                panel,
                "SIMULATION TIME\n"
                    + FormatElapsed(frameWriter.CurrentSimulationTimeSeconds),
                labelStyle);
        }
    }
}
