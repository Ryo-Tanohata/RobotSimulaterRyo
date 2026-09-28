using RobotSim.Core;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;
using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// ML-Agents のエージェント。観測 45 次元 (体内センサのみ) → 行動 12 次元 (関節目標角のオフセット)。
    /// ・Python (mlagents-learn) につながっていれば → 強化学習
    /// ・学習済みモデル (.onnx) が設定されていれば → 推論で歩く
    /// ・どちらもなければ → Heuristic (プログラムされたトロット歩容) で歩く
    /// </summary>
    public sealed class QuadrupedAgent : Agent
    {
        public QuadrupedRobot Robot;
        public SimulationManager Manager;
        public int Column;        // 担当する地形の種類 (列)
        public int Level;         // 現在の難易度

        public VelocityCommand Command;
        public bool ManualControl; // キーボードで速度指令を与える

        readonly float[] _actions = new float[RobotConfig.JointCount];
        readonly float[] _lastActions = new float[RobotConfig.JointCount];
        readonly float[] _lastJointVel = new float[RobotConfig.JointCount];
        readonly float[] _obs = new float[Observation.Size];
        readonly float[] _gaitTargets = new float[RobotConfig.JointCount];
        float[] _defaultAngles;

        readonly LocomotionReward _reward = new LocomotionReward();
        TrotGait _gait;
        readonly System.Random _rng = new System.Random();

        Vector3 _spawnPosition;
        float _episodeTime, _commandTimer, _pushTimer, _fallenTime;
        float _commandedDistance;
        bool _hasStarted;

        public float EpisodeTime => _episodeTime;
        public LocomotionReward Reward => _reward;
        public float DistanceFromSpawn => Vector2.Distance(
            new Vector2(Robot.transform.position.x, Robot.transform.position.z),
            new Vector2(_spawnPosition.x, _spawnPosition.z));

        float ControlDt => Time.fixedDeltaTime * Manager.DecisionPeriod;

        public override void Initialize()
        {
            _defaultAngles = Robot.Config.DefaultJointAngles();
            _gait = new TrotGait(Robot.Config);
            MaxStep = Mathf.RoundToInt(Manager.EpisodeLengthSeconds / Time.fixedDeltaTime);
        }

        public override void OnEpisodeBegin()
        {
            // --- カリキュラム: 前のエピソードの結果で難易度を上げ下げ
            if (_hasStarted && Manager.UseCurriculum && Manager.IsTraining)
            {
                Level = TerrainCurriculum.NextLevel(Level, Manager.Levels - 1, DistanceFromSpawn, _commandedDistance,
                    Manager.TileSize, _rng);
                Academy.Instance.StatsRecorder.Add("Curriculum/TerrainLevel", Level);
            }
            _hasStarted = true;

            float yaw = Manager.RandomizeHeading ? Random.Range(0f, 360f) : 0f;
            _spawnPosition = Manager.SpawnPoint(Column, Level);
            Robot.ResetPose(_spawnPosition, Quaternion.Euler(0f, yaw, 0f));

            System.Array.Clear(_actions, 0, _actions.Length);
            System.Array.Clear(_lastActions, 0, _lastActions.Length);
            System.Array.Clear(_lastJointVel, 0, _lastJointVel.Length);
            _reward.Reset();
            _gait.Reset();
            _episodeTime = 0f;
            _commandedDistance = 0f;
            _fallenTime = 0f;
            _pushTimer = Manager.PushInterval * Random.Range(0.5f, 1f);
            ResampleCommand();
        }

        void ResampleCommand()
        {
            _commandTimer = Manager.CommandResampleSeconds;
            if (ManualControl) return;
            if (Random.value < 0.1f) { Command = new VelocityCommand(0f, 0f, 0f); return; }
            Command = new VelocityCommand(
                Random.Range(-Manager.MaxForwardSpeed * 0.5f, Manager.MaxForwardSpeed),
                Random.Range(-Manager.MaxSideSpeed, Manager.MaxSideSpeed),
                Random.Range(-Manager.MaxYawRate, Manager.MaxYawRate));
        }

        public override void CollectObservations(VectorSensor sensor)
        {
            if (!Robot.IsReady)
            {
                for (int i = 0; i < Observation.Size; i++) sensor.AddObservation(0f);
                return;
            }
            Robot.ReadState();
            Observation.Build(Robot.State, Command, _defaultAngles, _lastActions, _obs);
            for (int i = 0; i < _obs.Length; i++) sensor.AddObservation(_obs[i]);
        }

        public override void OnActionReceived(ActionBuffers actions)
        {
            if (!Robot.IsReady) return;
            var ca = actions.ContinuousActions;
            for (int j = 0; j < RobotConfig.JointCount; j++) _actions[j] = ca[j];

            // --- 報酬 (直前の行動の結果)
            Robot.ReadState();
            float r = _reward.Compute(Robot.State, Command, _actions, _lastActions, _lastJointVel, ControlDt);
            AddReward(r);
            System.Array.Copy(Robot.State.JointVelocities, _lastJointVel, _lastJointVel.Length);
            System.Array.Copy(_actions, _lastActions, _lastActions.Length);

            // --- 行動 → 関節目標角 = 基準姿勢 + 行動 × スケール
            float scale = Robot.Config.ActionScale;
            for (int j = 0; j < RobotConfig.JointCount; j++)
                Robot.SetTarget(j, _defaultAngles[j] + _actions[j] * scale);
        }

        /// <summary>学習済みモデルがないときの手動 / プログラム制御 (トロット歩容)。</summary>
        public override void Heuristic(in ActionBuffers actionsOut)
        {
            var ca = actionsOut.ContinuousActions;
            if (!Robot.IsReady)
            {
                for (int j = 0; j < RobotConfig.JointCount; j++) ca[j] = 0f;
                return;
            }
            Robot.ReadState();
            _gait.Step(ControlDt, Command.Forward, Command.Side, Command.Yaw, Robot.State.ProjectedGravity, _gaitTargets);
            float scale = Robot.Config.ActionScale;
            for (int j = 0; j < RobotConfig.JointCount; j++)
                ca[j] = (_gaitTargets[j] - _defaultAngles[j]) / scale;
        }

        void FixedUpdate()
        {
            if (!Robot.IsReady) return;
            float dt = Time.fixedDeltaTime;
            _episodeTime += dt;
            _commandedDistance += new Vector2(Command.Forward, Command.Side).magnitude * dt;

            if (ManualControl) Command = Manager.KeyboardCommand;
            _commandTimer -= dt;
            if (_commandTimer <= 0f) ResampleCommand();

            // --- ランダムな外乱 (蹴られても倒れないように学習させる)
            if (Manager.PushRobots)
            {
                _pushTimer -= dt;
                if (_pushTimer <= 0f)
                {
                    _pushTimer = Manager.PushInterval;
                    Vector2 v = Random.insideUnitCircle * Manager.MaxPushSpeed;
                    Robot.Push(new Vector3(v.x, 0f, v.y));
                }
            }

            // --- 転倒判定
            var t = Robot.transform;
            bool fallen = t.up.y < 0.3f || Robot.State.BaseContact;
            _fallenTime = fallen ? _fallenTime + dt : 0f;
            if (fallen && Manager.TerminateOnFall)
            {
                AddReward(_reward.Termination * ControlDt);
                EndEpisode();
                return;
            }
            // 手動デモ中は倒れたまま 3 秒経ったら起こす
            if (_fallenTime > 3f) { EndEpisode(); return; }

            // --- 地形の外に出たら (= 十分遠くまで歩けた) エピソード終了
            if (!Manager.IsInsideTerrain(t.position) || t.position.y < -5f) EndEpisode();
        }
    }
}
