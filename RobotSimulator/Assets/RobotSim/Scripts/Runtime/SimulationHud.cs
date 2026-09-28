using RobotSim.Core;
using UnityEngine;

namespace RobotSim
{
    /// <summary>画面左上の情報表示と操作説明 (IMGUI)。H キーで表示切り替え。</summary>
    public sealed class SimulationHud : MonoBehaviour
    {
        bool _show = true;
        GUIStyle _style;

        void Update()
        {
            if (SimInput.KeyDown(KeyCode.H)) _show = !_show;
        }

        void OnGUI()
        {
            var mgr = SimulationManager.Instance;
            if (!_show || mgr == null) return;
            if (_style == null)
            {
                _style = new GUIStyle(GUI.skin.label) { fontSize = 14, richText = true };
                _style.normal.textColor = Color.white;
            }

            var a = mgr.Selected;
            string mode = mgr.IsTraining ? "<color=#ffcc55>TRAINING (mlagents-learn)</color>"
                : mgr.PolicyModel != null ? "<color=#88ff88>INFERENCE (trained model)</color>"
                : "<color=#88ccff>HEURISTIC (scripted trot gait)</color>";

            string text = $"<b>Quadruped RL Simulator</b>   robots: {mgr.Agents.Count}   {mode}\n";
            if (a != null)
            {
                var s = a.Robot.State;
                var type = TerrainGenerator.Types[a.Column];
                text += $"Robot #{mgr.SelectedIndex}  terrain: {type}  level: {a.Level}/{mgr.Levels - 1}" +
                        $"   control: {(a.ManualControl ? "<color=#ffff66>KEYBOARD</color>" : "random command")}\n" +
                        $"cmd  fwd {a.Command.Forward:+0.00;-0.00}  side {a.Command.Side:+0.00;-0.00}  yaw {a.Command.Yaw:+0.00;-0.00}\n" +
                        $"vel  fwd {s.LinearVelocity.z:+0.00;-0.00}  side {s.LinearVelocity.x:+0.00;-0.00}  yaw {s.AngularVelocity.y:+0.00;-0.00}" +
                        $"   height {s.BaseHeight:0.00} m\n" +
                        $"episode {a.EpisodeTime:0.0}s  reward {a.GetCumulativeReward():0.00}  distance {a.DistanceFromSpawn:0.0} m" +
                        $"   feet [{Foot(s, 0)}{Foot(s, 1)}{Foot(s, 2)}{Foot(s, 3)}]\n";
            }
            text += $"pushes: {(mgr.PushRobots ? "ON" : "OFF")}   time x{Time.timeScale:0}\n\n" +
                    "<color=#cccccc>[W/S] fwd/back  [A/D] side  [Q/E] turn  [M] keyboard control on/off\n" +
                    "[Space] kick  [R] reset  [Tab/B] next/prev robot  [F] overview\n" +
                    "[1-5] terrain: rough/slope/stairs up/stairs down/blocks  [+/-] level\n" +
                    "[P] random pushes  [T] fast x4  [H] hide   right-drag: rotate  wheel: zoom</color>";

            var rect = new Rect(10, 10, 640, 230);
            GUI.color = new Color(0, 0, 0, 0.55f);
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUI.Label(new Rect(18, 14, 630, 224), text, _style);
        }

        static string Foot(RobotState s, int leg) => s.FootContact[leg] ? "■" : "□";
    }
}
