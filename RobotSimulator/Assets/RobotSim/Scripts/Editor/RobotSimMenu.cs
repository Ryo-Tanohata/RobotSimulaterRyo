using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace RobotSim.EditorTools
{
    /// <summary>メニュー「RobotSim」: シミュレーション用シーンを作成してビルド設定に登録する。</summary>
    public static class RobotSimMenu
    {
        const string ScenePath = "Assets/RobotSim/Scenes/Main.unity";

        [MenuItem("RobotSim/Create Main Scene")]
        public static void CreateMainScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            new GameObject("RobotSimulation").AddComponent<SimulationManager>();
            System.IO.Directory.CreateDirectory("Assets/RobotSim/Scenes");
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            Selection.activeGameObject = GameObject.Find("RobotSimulation");
            Debug.Log($"[RobotSim] {ScenePath} を作成しました。Play を押すとシミュレーションが始まります。");
        }

        [MenuItem("RobotSim/Build Training Executable (Headless)")]
        public static void BuildTrainingPlayer()
        {
            if (EditorBuildSettings.scenes.Length == 0) CreateMainScene();
            var target = EditorUserBuildSettings.activeBuildTarget;
            string ext = target == BuildTarget.StandaloneWindows64 ? ".exe" : target == BuildTarget.StandaloneOSX ? ".app" : ".x86_64";
            var options = new BuildPlayerOptions
            {
                scenes = new[] { EditorBuildSettings.scenes[0].path },
                locationPathName = "Builds/Quadruped/Quadruped" + ext,
                target = target,
                options = BuildOptions.None,
            };
            var report = BuildPipeline.BuildPlayer(options);
            Debug.Log($"[RobotSim] Build result: {report.summary.result} → {options.locationPathName}");
        }
    }
}
