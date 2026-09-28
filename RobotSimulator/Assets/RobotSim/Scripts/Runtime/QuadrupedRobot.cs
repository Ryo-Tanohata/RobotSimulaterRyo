using RobotSim.Core;
using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// ArticulationBody (PhysX の多関節ソルバ) で作る四足ロボット。
    /// 胴体 1 + 脚 4 本 × (股 / 太もも / すね) = 13 リンク、12 関節。
    /// 関節は PD 制御 (ArticulationDrive) で目標角に追従する。
    /// </summary>
    public sealed class QuadrupedRobot : MonoBehaviour
    {
        public const int RobotLayer = 8; // ロボット同士・自己衝突を無効化するためのレイヤー

        public RobotConfig Config { get; private set; }
        public ArticulationBody Root { get; private set; }
        public readonly RobotState State = new RobotState();

        /// <summary>関節の符号の自動判定が終わり、制御してよい状態か。</summary>
        public bool IsReady => _calibrated;

        readonly ArticulationBody[] _joints = new ArticulationBody[RobotConfig.JointCount];
        readonly Vector3[] _jointAxes = new Vector3[RobotConfig.JointCount]; // 親座標系での関節軸
        readonly float[] _sign = new float[RobotConfig.JointCount];
        readonly float[] _targets = new float[RobotConfig.JointCount];
        readonly Transform[] _thighs = new Transform[RobotConfig.LegCount];
        readonly Transform[] _calves = new Transform[RobotConfig.LegCount];
        float[] _defaultAngles;

        bool _calibrated;
        int _stepsSinceSpawn;
        Vector3 _resetPosition;
        Quaternion _resetRotation = Quaternion.identity;

        static int GroundMask => ~(1 << RobotLayer) & Physics.DefaultRaycastLayers;

        // ------------------------------------------------------------------ 生成

        public static QuadrupedRobot Create(RobotConfig c, Transform parent, Vector3 position, Color bodyColor)
        {
            var rootGo = new GameObject("Quadruped");
            rootGo.layer = RobotLayer;
            rootGo.transform.SetParent(parent, false);
            rootGo.transform.position = position;

            var robot = rootGo.AddComponent<QuadrupedRobot>();
            robot.Config = c;
            robot._defaultAngles = c.DefaultJointAngles();

            // --- 胴体
            var root = rootGo.AddComponent<ArticulationBody>();
            root.mass = c.TrunkMass;
            root.linearDamping = 0f;
            root.angularDamping = 0f;
            var box = rootGo.AddComponent<BoxCollider>();
            box.size = new Vector3(c.TrunkWidth, c.TrunkHeight, c.TrunkLength);
            box.sharedMaterial = SimAssets.RobotMaterial;
            SimAssets.AddVisual(rootGo.transform, PrimitiveType.Cube, Vector3.zero, Quaternion.identity,
                box.size, bodyColor);
            // 前方がわかるように「顔」を付ける
            SimAssets.AddVisual(rootGo.transform, PrimitiveType.Cube, new Vector3(0, 0.01f, c.TrunkLength * 0.5f),
                Quaternion.identity, new Vector3(c.TrunkWidth * 0.6f, c.TrunkHeight * 0.4f, 0.01f), Color.black);
            robot.Root = root;

            var legColor = new Color(0.18f, 0.18f, 0.2f);
            for (int leg = 0; leg < RobotConfig.LegCount; leg++)
            {
                float side = RobotConfig.SideSign(leg);
                Vec3 hp = c.HipPosition(leg);
                string n = RobotConfig.LegNames[leg];

                // 股 (外転: 前後軸まわり)
                var hip = CreateLink(n + "_hip", rootGo.transform, new Vector3(hp.x, hp.y, hp.z), c.HipMass);
                var hipCol = hip.gameObject.AddComponent<SphereCollider>();
                hipCol.radius = 0.04f;
                SimAssets.AddVisual(hip.transform, PrimitiveType.Cylinder, new Vector3(side * c.HipLinkLength * 0.5f, 0, 0),
                    Quaternion.Euler(0, 0, 90), new Vector3(0.07f, c.HipLinkLength * 0.5f + 0.02f, 0.07f), legColor);
                // anchor の X 軸を胴体の +z (前) に向ける
                robot.SetupJoint(leg * 3 + 0, hip, Quaternion.Euler(0, -90, 0), Vector3.forward);

                // 太もも (ピッチ: 左右軸まわり)
                var thigh = CreateLink(n + "_thigh", hip.transform, new Vector3(side * c.HipLinkLength, 0, 0), c.ThighMass);
                var thighCol = thigh.gameObject.AddComponent<CapsuleCollider>();
                thighCol.direction = 1;
                thighCol.radius = c.ThighRadius;
                thighCol.height = c.ThighLength + 2 * c.ThighRadius;
                thighCol.center = new Vector3(0, -c.ThighLength * 0.5f, 0);
                SimAssets.AddVisual(thigh.transform, PrimitiveType.Capsule, thighCol.center, Quaternion.identity,
                    new Vector3(c.ThighRadius * 2, thighCol.height * 0.5f, c.ThighRadius * 2), bodyColor * 0.8f);
                robot.SetupJoint(leg * 3 + 1, thigh, Quaternion.identity, Vector3.right);

                // すね + 足先
                var calf = CreateLink(n + "_calf", thigh.transform, new Vector3(0, -c.ThighLength, 0), c.CalfMass);
                var calfCol = calf.gameObject.AddComponent<CapsuleCollider>();
                calfCol.direction = 1;
                calfCol.radius = c.CalfRadius;
                calfCol.height = c.CalfLength;
                calfCol.center = new Vector3(0, -c.CalfLength * 0.5f, 0);
                var foot = calf.gameObject.AddComponent<SphereCollider>();
                foot.radius = c.FootRadius;
                foot.center = new Vector3(0, -c.CalfLength, 0);
                foot.sharedMaterial = SimAssets.FootMaterial;
                SimAssets.AddVisual(calf.transform, PrimitiveType.Capsule, calfCol.center, Quaternion.identity,
                    new Vector3(c.CalfRadius * 2, c.CalfLength * 0.5f, c.CalfRadius * 2), legColor);
                SimAssets.AddVisual(calf.transform, PrimitiveType.Sphere, foot.center, Quaternion.identity,
                    Vector3.one * c.FootRadius * 2, new Color(0.1f, 0.1f, 0.1f));
                robot.SetupJoint(leg * 3 + 2, calf, Quaternion.identity, Vector3.right);

                robot._thighs[leg] = thigh.transform;
                robot._calves[leg] = calf.transform;
            }

            robot._resetPosition = position;
            robot._resetRotation = Quaternion.identity;
            robot.ApplyCalibrationPose();
            return robot;
        }

        static ArticulationBody CreateLink(string name, Transform parent, Vector3 localPos, float mass)
        {
            var go = new GameObject(name);
            go.layer = RobotLayer;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var body = go.AddComponent<ArticulationBody>();
            body.mass = mass;
            body.linearDamping = 0f;
            body.angularDamping = 0f;
            body.jointFriction = 0.02f;
            return body;
        }

        void SetupJoint(int j, ArticulationBody body, Quaternion anchorRotation, Vector3 axisInParent)
        {
            body.jointType = ArticulationJointType.RevoluteJoint;
            body.anchorPosition = Vector3.zero;
            body.anchorRotation = anchorRotation;
            body.matchAnchors = true;
            // 符号が確定するまでは、どちらの符号でも収まる対称な可動範囲にしておく
            // (実行中に twistLock を切り替えると関節が作り直されるので、ここで LimitedMotion にしておく)
            body.twistLock = ArticulationDofLock.LimitedMotion;
            Config.JointLimits(j, out float lo, out float hi);
            float wide = Mathf.Max(Mathf.Abs(lo), Mathf.Abs(hi)) * Mathf.Rad2Deg;
            var d = body.xDrive;
            d.lowerLimit = -wide;
            d.upperLimit = wide;
            d.stiffness = Config.Kp;
            d.damping = Config.Kd;
            d.forceLimit = Config.TorqueLimit;
            body.xDrive = d;
            _joints[j] = body;
            _jointAxes[j] = axisInParent;
            _sign[j] = 1f;
        }

        // ------------------------------------------------------------------ 関節の符号の自動判定
        //
        // ArticulationBody の jointPosition の正方向は Unity の回転方向と逆になる場合があるため、
        // 生成直後に 1 ステップだけ既知の角度をセットし、実際の Transform の回転と比べて符号を決める。

        static readonly float[] CalibrationPose = { 0.3f, 0.8f, -1.5f };

        void ApplyCalibrationPose()
        {
            Root.TeleportRoot(_resetPosition, _resetRotation);
            for (int j = 0; j < RobotConfig.JointCount; j++)
            {
                float raw = CalibrationPose[j % 3];
                _joints[j].jointPosition = new ArticulationReducedSpace(raw);
                _joints[j].jointVelocity = new ArticulationReducedSpace(0f);
                SetDriveTarget(j, raw);
            }
        }

        void Calibrate()
        {
            for (int j = 0; j < RobotConfig.JointCount; j++)
            {
                float raw = _joints[j].jointPosition[0];
                float geometric = SignedAngle(_joints[j].transform.localRotation, _jointAxes[j]);
                _sign[j] = (Mathf.Abs(geometric - raw) <= Mathf.Abs(geometric + raw)) ? 1f : -1f;

                // 符号が確定したので可動範囲を設定する
                Config.JointLimits(j, out float lo, out float hi);
                var d = _joints[j].xDrive;
                if (_sign[j] > 0f) { d.lowerLimit = lo * Mathf.Rad2Deg; d.upperLimit = hi * Mathf.Rad2Deg; }
                else { d.lowerLimit = -hi * Mathf.Rad2Deg; d.upperLimit = -lo * Mathf.Rad2Deg; }
                _joints[j].xDrive = d;
            }
            _calibrated = true;
            if (_sign[1] < 0f)
                Debug.Log("[RobotSim] ArticulationBody の関節の符号が Unity の回転方向と逆でした。自動で補正しています。");
            ResetPose(_resetPosition, _resetRotation);
        }

        static float SignedAngle(Quaternion q, Vector3 axis)
        {
            float s = q.x * axis.x + q.y * axis.y + q.z * axis.z;
            float a = 2f * Mathf.Atan2(s, q.w);
            if (a > Mathf.PI) a -= 2f * Mathf.PI;
            if (a < -Mathf.PI) a += 2f * Mathf.PI;
            return a;
        }

        // ------------------------------------------------------------------ リセットと制御

        /// <summary>胴体を指定位置に置き、関節を基準姿勢にして速度をゼロにする。</summary>
        public void ResetPose(Vector3 position, Quaternion rotation)
        {
            _resetPosition = position;
            _resetRotation = rotation;
            if (!_calibrated) { ApplyCalibrationPose(); return; }

            Root.TeleportRoot(position, rotation);
            SetRootVelocity(Vector3.zero, Vector3.zero);
            for (int j = 0; j < RobotConfig.JointCount; j++)
            {
                _joints[j].jointPosition = new ArticulationReducedSpace(_sign[j] * _defaultAngles[j]);
                _joints[j].jointVelocity = new ArticulationReducedSpace(0f);
                SetTarget(j, _defaultAngles[j]);
            }
        }

        /// <summary>関節の目標角 [rad] を設定する (可動範囲でクリップ)。</summary>
        public void SetTarget(int j, float angle)
        {
            Config.JointLimits(j, out float lo, out float hi);
            angle = Mathf.Clamp(angle, lo, hi);
            _targets[j] = angle;
            if (_calibrated) SetDriveTarget(j, _sign[j] * angle);
        }

        public float GetTarget(int j) => _targets[j];

        void SetDriveTarget(int j, float rawRadians)
        {
            var d = _joints[j].xDrive;
            d.target = rawRadians * Mathf.Rad2Deg; // ArticulationDrive の回転の目標は度
            d.stiffness = Config.Kp;
            d.damping = Config.Kd;
            d.forceLimit = Config.TorqueLimit;
            _joints[j].xDrive = d;
        }

        /// <summary>胴体に速度変化を与える (「蹴り」やランダムな外乱)。</summary>
        public void Push(Vector3 deltaVelocity)
        {
            // 1 物理ステップで Δv を与える力 (全質量ぶん)
            Root.AddForce(deltaVelocity * (Config.TotalMass / Time.fixedDeltaTime));
        }

        void SetRootVelocity(Vector3 linear, Vector3 angular)
        {
#if UNITY_2023_3_OR_NEWER
            Root.linearVelocity = linear;
#else
            Root.velocity = linear;
#endif
            Root.angularVelocity = angular;
        }

        Vector3 RootLinearVelocity
        {
            get
            {
#if UNITY_2023_3_OR_NEWER
                return Root.linearVelocity;
#else
                return Root.velocity;
#endif
            }
        }

        void FixedUpdate()
        {
            if (!_calibrated)
            {
                // 1 ステップ物理が進んでから Transform を見て符号を決める
                if (++_stepsSinceSpawn >= 2) Calibrate();
            }
        }

        // ------------------------------------------------------------------ センサ

        public Vector3 FootPosition(int leg) => _calves[leg].TransformPoint(0f, -Config.CalfLength, 0f);

        /// <summary>現在の状態を <see cref="State"/> に読み込む。</summary>
        public void ReadState()
        {
            var t = Root.transform;
            Quaternion inv = Quaternion.Inverse(t.rotation);
            State.LinearVelocity = ToVec(inv * RootLinearVelocity);
            State.AngularVelocity = ToVec(inv * Root.angularVelocity);
            State.ProjectedGravity = ToVec(inv * Vector3.down);

            for (int j = 0; j < RobotConfig.JointCount; j++)
            {
                float q = _sign[j] * _joints[j].jointPosition[0];
                float dq = _sign[j] * _joints[j].jointVelocity[0];
                State.JointPositions[j] = q;
                State.JointVelocities[j] = dq;
                // 暗黙の PD 制御のトルクを推定
                State.JointTorques[j] = Mathf.Clamp(Config.Kp * (_targets[j] - q) - Config.Kd * dq,
                    -Config.TorqueLimit, Config.TorqueLimit);
            }

            int mask = GroundMask;
            State.BodyCollisions = 0;
            for (int leg = 0; leg < RobotConfig.LegCount; leg++)
            {
                State.FootContact[leg] = Physics.CheckSphere(FootPosition(leg), Config.FootRadius + 0.012f, mask,
                    QueryTriggerInteraction.Ignore);
                Vector3 hip = _thighs[leg].position;
                Vector3 knee = _calves[leg].position;
                if (Physics.CheckCapsule(hip, knee, Config.ThighRadius + 0.005f, mask, QueryTriggerInteraction.Ignore))
                    State.BodyCollisions++;
            }

            var half = new Vector3(Config.TrunkWidth, Config.TrunkHeight, Config.TrunkLength) * 0.5f
                       + Vector3.one * 0.01f;
            State.BaseContact = Physics.CheckBox(t.position, half, t.rotation, mask, QueryTriggerInteraction.Ignore);

            State.BaseHeight = Physics.Raycast(t.position, Vector3.down, out RaycastHit hit, 5f, mask,
                QueryTriggerInteraction.Ignore)
                ? t.position.y - hit.point.y
                : 5f;
        }

        static Vec3 ToVec(Vector3 v) => new Vec3(v.x, v.y, v.z);
    }
}
