using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// どのシーンで Play しても SimulationManager が無ければ自動で作る。
    /// (シーンファイルを用意しなくても「開いて Play」だけで動くようにするため)
    /// </summary>
    public static class SimulationBootstrap
    {
        public static bool Enabled = true;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void CreateIfMissing()
        {
            if (!Enabled || Object.FindFirstObjectByType<SimulationManager>() != null) return;
            new GameObject("RobotSimulation").AddComponent<SimulationManager>();
        }
    }
}
