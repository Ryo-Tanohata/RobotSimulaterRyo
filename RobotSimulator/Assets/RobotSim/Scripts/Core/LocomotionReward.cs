using System;

namespace RobotSim.Core
{
    /// <summary>1 制御ステップ分のロボットの状態 (すべて胴体座標系)。</summary>
    public sealed class RobotState
    {
        public Vec3 LinearVelocity;       // 胴体座標系の速度 (z = 前, x = 右)
        public Vec3 AngularVelocity;      // 胴体座標系の角速度 (y = ヨー)
        public Vec3 ProjectedGravity;     // 胴体座標系での重力方向 (水平時 (0,-1,0))
        public float BaseHeight;          // 足元の地面からの胴体高さ
        public readonly float[] JointPositions = new float[RobotConfig.JointCount];
        public readonly float[] JointVelocities = new float[RobotConfig.JointCount];
        public readonly float[] JointTorques = new float[RobotConfig.JointCount];
        public readonly bool[] FootContact = new bool[RobotConfig.LegCount];
        public int BodyCollisions;        // 太もも・すねが地面に当たっている数
        public bool BaseContact;          // 胴体が地面に接触 (= 転倒)
    }

    /// <summary>速度指令 (胴体座標系)。</summary>
    public struct VelocityCommand
    {
        public float Forward, Side, Yaw;
        public VelocityCommand(float forward, float side, float yaw) { Forward = forward; Side = side; Yaw = yaw; }
        public bool IsZero => Math.Abs(Forward) < 0.1f && Math.Abs(Side) < 0.1f && Math.Abs(Yaw) < 0.1f;
    }

    /// <summary>
    /// 歩行の報酬。オープンソースの legged_gym (ETH / NVIDIA, 4096 体並列学習の元祖) の
    /// 報酬設計を参考にした構成。各項目に制御周期 dt を掛ける。
    /// </summary>
    public sealed class LocomotionReward
    {
        // 報酬スケール
        public float TrackingLinVel = 1.0f;
        public float TrackingAngVel = 0.5f;
        public float LinVelZ = -2.0f;
        public float AngVelXY = -0.05f;
        public float Orientation = -0.2f;
        public float Torques = -1e-4f;
        public float DofAcc = -2.5e-7f;
        public float ActionRate = -0.01f;
        public float Collision = -1.0f;
        public float FeetAirTime = 1.0f;
        public float Termination = -10.0f;
        public float TrackingSigma = 0.25f;

        readonly float[] _airTime = new float[RobotConfig.LegCount];

        // 最後に計算した内訳 (HUD 表示用)
        public float LastTrackingLin, LastTrackingAng, LastPenalty, LastAirTime;

        public void Reset()
        {
            Array.Clear(_airTime, 0, _airTime.Length);
        }

        public float Compute(RobotState s, VelocityCommand cmd, float[] actions, float[] lastActions,
                             float[] lastJointVel, float dt)
        {
            // --- 速度指令への追従 (指数型: 誤差 0 で 1)
            float linErr = MathUtil.Sq(cmd.Forward - s.LinearVelocity.z) + MathUtil.Sq(cmd.Side - s.LinearVelocity.x);
            float angErr = MathUtil.Sq(cmd.Yaw - s.AngularVelocity.y);
            float trackLin = (float)Math.Exp(-linErr / TrackingSigma);
            float trackAng = (float)Math.Exp(-angErr / TrackingSigma);

            // --- ペナルティ
            float linVelZ = MathUtil.Sq(s.LinearVelocity.y);
            float angVelXY = MathUtil.Sq(s.AngularVelocity.x) + MathUtil.Sq(s.AngularVelocity.z);
            float orient = MathUtil.Sq(s.ProjectedGravity.x) + MathUtil.Sq(s.ProjectedGravity.z);
            float torque = 0f, dofAcc = 0f, actRate = 0f;
            for (int j = 0; j < RobotConfig.JointCount; j++)
            {
                torque += MathUtil.Sq(s.JointTorques[j]);
                dofAcc += MathUtil.Sq((lastJointVel[j] - s.JointVelocities[j]) / dt);
                actRate += MathUtil.Sq(lastActions[j] - actions[j]);
            }

            // --- 足の滞空時間: 着地した瞬間に (滞空時間 - 0.5 秒) を与え、大きな歩幅を促す
            float airReward = 0f;
            for (int i = 0; i < RobotConfig.LegCount; i++)
            {
                bool contact = s.FootContact[i];
                bool firstContact = _airTime[i] > 0f && contact;
                _airTime[i] += dt;
                if (firstContact) airReward += _airTime[i] - 0.5f;
                if (contact) _airTime[i] = 0f;
            }
            if (cmd.IsZero) airReward = 0f;

            LastTrackingLin = TrackingLinVel * trackLin * dt;
            LastTrackingAng = TrackingAngVel * trackAng * dt;
            LastAirTime = FeetAirTime * airReward * dt;
            LastPenalty = (LinVelZ * linVelZ + AngVelXY * angVelXY + Orientation * orient
                           + Torques * torque + DofAcc * dofAcc + ActionRate * actRate
                           + Collision * s.BodyCollisions) * dt;

            return LastTrackingLin + LastTrackingAng + LastAirTime + LastPenalty;
        }
    }
}
