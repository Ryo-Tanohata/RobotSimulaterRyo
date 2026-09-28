using System.Collections.Generic;
using RobotSim.Core;
using Unity.InferenceEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Policies;
using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// シミュレーション全体の管理: 物理設定、地形の生成、ロボット (エージェント) の並列生成、キーボード操作。
    /// シーンに置かなくても <see cref="SimulationBootstrap"/> が自動で作る。
    /// </summary>
    public sealed class SimulationManager : MonoBehaviour
    {
        public static SimulationManager Instance { get; private set; }

        [Header("並列ロボット数 (PC の性能に合わせて調整。fuRo のデモは 4096 体)")]
        [Range(1, 1024)] public int NumRobots = 16;

        [Header("学習済みモデル (空なら Heuristic = プログラム歩行 で動く)")]
        public ModelAsset PolicyModel;
        public string BehaviorName = "Quadruped";
        public BehaviorType BehaviorType = BehaviorType.Default;

        [Header("物理")]
        public float PhysicsTimeStep = 0.005f;   // 200 Hz
        public int DecisionPeriod = 4;           // 方策は 50 Hz
        public int SolverIterations = 8;

        [Header("エピソード")]
        public float EpisodeLengthSeconds = 20f;
        public float CommandResampleSeconds = 10f;
        public float MaxForwardSpeed = 1.0f;
        public float MaxSideSpeed = 0.5f;
        public float MaxYawRate = 1.0f;
        public bool RandomizeHeading = false;
        public bool TerminateOnFall = true;

        [Header("外乱 (蹴り)")]
        public bool PushRobots = true;
        public float PushInterval = 8f;
        public float MaxPushSpeed = 0.8f;

        [Header("地形")]
        public int Levels = 6;
        public float TileSize = 8f;
        public int TerrainSeed = 1;
        public bool UseCurriculum = true;
        [Tooltip("開始時の難易度の上限 (学習時は 0〜この値からランダム)")]
        public int MaxInitialLevel = 0;

        [Header("ロボット")]
        public RobotConfig Robot = new RobotConfig();

        public readonly List<QuadrupedAgent> Agents = new List<QuadrupedAgent>();
        public int SelectedIndex { get; private set; }
        public QuadrupedAgent Selected => Agents.Count > 0 ? Agents[Mathf.Clamp(SelectedIndex, 0, Agents.Count - 1)] : null;
        public VelocityCommand KeyboardCommand { get; private set; }
        public bool IsTraining => Academy.Instance.IsCommunicatorOn;

        TerrainTile[,] _tiles;
        TerrainGenerator _generator;
        System.Random _rng;

        void Awake()
        {
            Instance = this;
            Time.fixedDeltaTime = PhysicsTimeStep;
            Physics.defaultSolverIterations = SolverIterations;
            Physics.defaultSolverVelocityIterations = 2;
            Physics.IgnoreLayerCollision(QuadrupedRobot.RobotLayer, QuadrupedRobot.RobotLayer, true);
            Application.targetFrameRate = 60;
            _rng = new System.Random(TerrainSeed);
        }

        void Start()
        {
            BuildWorld();
            SpawnRobots();
            if (FindFirstObjectByType<CameraRig>() == null)
            {
                var cam = Camera.main != null ? Camera.main.gameObject : new GameObject("Main Camera", typeof(Camera));
                cam.tag = "MainCamera";
                cam.AddComponent<CameraRig>();
            }
            if (GetComponent<SimulationHud>() == null) gameObject.AddComponent<SimulationHud>();
        }

        void BuildWorld()
        {
            _generator = new TerrainGenerator { Levels = Levels, TileSize = TileSize, Seed = TerrainSeed };
            _tiles = _generator.Generate();
            TerrainBuilder.Build(_tiles, TileSize, transform);

            if (FindFirstObjectByType<Light>() == null)
            {
                var light = new GameObject("Sun").AddComponent<Light>();
                light.type = LightType.Directional;
                light.intensity = 1.1f;
                light.shadows = LightShadows.Soft;
                light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            }
        }

        void SpawnRobots()
        {
            for (int i = 0; i < NumRobots; i++)
            {
                int column = i % _generator.Columns;
                int level = MaxInitialLevel > 0 ? _rng.Next(Mathf.Min(MaxInitialLevel, Levels - 1) + 1) : 0;
                var color = Color.HSVToRGB((i * 0.618f) % 1f, 0.55f, 0.95f);
                var robot = QuadrupedRobot.Create(Robot, transform, SpawnPoint(column, level), color);
                robot.name = $"Quadruped_{i:D3}";

                // Agent の初期化時に BehaviorParameters が読まれるため、非アクティブのまま設定してから有効化する
                robot.gameObject.SetActive(false);
                var bp = robot.gameObject.AddComponent<BehaviorParameters>();
                bp.BehaviorName = BehaviorName;
                bp.BrainParameters.VectorObservationSize = Observation.Size;
                bp.BrainParameters.NumStackedVectorObservations = 1;
                bp.BrainParameters.ActionSpec = ActionSpec.MakeContinuous(RobotConfig.JointCount);
                bp.Model = PolicyModel;
                bp.BehaviorType = BehaviorType;
                bp.UseChildSensors = false;

                var agent = robot.gameObject.AddComponent<QuadrupedAgent>();
                agent.Robot = robot;
                agent.Manager = this;
                agent.Column = column;
                agent.Level = level;

                var dr = robot.gameObject.AddComponent<DecisionRequester>();
                dr.DecisionPeriod = DecisionPeriod;
                dr.TakeActionsBetweenDecisions = false;

                robot.gameObject.SetActive(true);
                Agents.Add(agent);
            }
            if (Agents.Count > 0) Agents[0].ManualControl = !IsTraining;
        }

        /// <summary>タイル中央のスタート台の上 (少しランダムにずらす)。</summary>
        public Vector3 SpawnPoint(int column, int level)
        {
            level = Mathf.Clamp(level, 0, Levels - 1);
            var tile = _tiles[column, level];
            Vector3 c = TerrainBuilder.TileCenter(column, level, TileSize);
            float jitter = _generator.PlatformSize * 0.3f;
            float dx = ((float)_rng.NextDouble() * 2f - 1f) * jitter;
            float dz = ((float)_rng.NextDouble() * 2f - 1f) * jitter;
            float h = tile.HeightAtLocal(dx, dz);
            return new Vector3(c.x + dx, h + Robot.SpawnHeight, c.z + dz);
        }

        public bool IsInsideTerrain(Vector3 p) =>
            p.x > 0f && p.z > 0f && p.x < _generator.Columns * TileSize && p.z < Levels * TileSize;

        public Vector3 TerrainCenter => new Vector3(_generator.Columns * TileSize * 0.5f, 0f, Levels * TileSize * 0.5f);

        // ------------------------------------------------------------------ キーボード操作

        void Update()
        {
            float fwd = 0f, side = 0f, yaw = 0f;
            if (SimInput.Key(KeyCode.W) || SimInput.Key(KeyCode.UpArrow)) fwd += 1f;
            if (SimInput.Key(KeyCode.S) || SimInput.Key(KeyCode.DownArrow)) fwd -= 0.6f;
            if (SimInput.Key(KeyCode.D)) side += 1f;
            if (SimInput.Key(KeyCode.A)) side -= 1f;
            if (SimInput.Key(KeyCode.E) || SimInput.Key(KeyCode.RightArrow)) yaw += 1f;
            if (SimInput.Key(KeyCode.Q) || SimInput.Key(KeyCode.LeftArrow)) yaw -= 1f;
            KeyboardCommand = new VelocityCommand(fwd * MaxForwardSpeed, side * MaxSideSpeed, yaw * MaxYawRate);

            if (Agents.Count == 0) return;
            if (SimInput.KeyDown(KeyCode.Tab) || SimInput.KeyDown(KeyCode.N)) Select(SelectedIndex + 1);
            if (SimInput.KeyDown(KeyCode.B)) Select(SelectedIndex - 1);
            var sel = Selected;
            if (SimInput.KeyDown(KeyCode.M)) sel.ManualControl = !sel.ManualControl;
            if (SimInput.KeyDown(KeyCode.Space))
            {
                // 蹴る: ランダムな横方向に速度を与える
                Vector2 v = Random.insideUnitCircle.normalized * 1.5f;
                sel.Robot.Push(new Vector3(v.x, 0.3f, v.y));
            }
            if (SimInput.KeyDown(KeyCode.R)) sel.EndEpisode();
            if (SimInput.KeyDown(KeyCode.P)) PushRobots = !PushRobots;
            if (SimInput.KeyDown(KeyCode.T)) Time.timeScale = Time.timeScale > 1.5f ? 1f : 4f;
            if (SimInput.KeyDown(KeyCode.Alpha1)) MoveSelectedTo(TerrainType.Rough);
            if (SimInput.KeyDown(KeyCode.Alpha2)) MoveSelectedTo(TerrainType.SlopeUp);
            if (SimInput.KeyDown(KeyCode.Alpha3)) MoveSelectedTo(TerrainType.StairsUp);
            if (SimInput.KeyDown(KeyCode.Alpha4)) MoveSelectedTo(TerrainType.StairsDown);
            if (SimInput.KeyDown(KeyCode.Alpha5)) MoveSelectedTo(TerrainType.Obstacles);
            if (SimInput.KeyDown(KeyCode.Equals) || SimInput.KeyDown(KeyCode.KeypadPlus)) ChangeSelectedLevel(+1);
            if (SimInput.KeyDown(KeyCode.Minus) || SimInput.KeyDown(KeyCode.KeypadMinus)) ChangeSelectedLevel(-1);
        }

        void Select(int index)
        {
            if (Agents.Count == 0) return;
            bool manual = Selected != null && Selected.ManualControl;
            if (Selected != null) Selected.ManualControl = false;
            SelectedIndex = (index % Agents.Count + Agents.Count) % Agents.Count;
            Selected.ManualControl = manual && !IsTraining;
        }

        void MoveSelectedTo(TerrainType type)
        {
            var sel = Selected;
            sel.Column = System.Array.IndexOf(TerrainGenerator.Types, type);
            sel.EndEpisode();
        }

        void ChangeSelectedLevel(int delta)
        {
            var sel = Selected;
            sel.Level = Mathf.Clamp(sel.Level + delta, 0, Levels - 1);
            sel.EndEpisode();
        }
    }
}
