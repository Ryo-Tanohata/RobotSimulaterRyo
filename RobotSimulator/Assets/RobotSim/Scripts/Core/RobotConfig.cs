using System;

namespace RobotSim.Core
{
    /// <summary>
    /// 四足ロボットの寸法・質量・制御パラメータ。
    /// Unity の座標系 (x = 右, y = 上, z = 前) で表す。
    /// 寸法は小型四足ロボット (体重 13kg 前後) を想定。
    /// </summary>
    [Serializable]
    public sealed class RobotConfig
    {
        public const int LegCount = 4;
        public const int JointsPerLeg = 3;
        public const int JointCount = LegCount * JointsPerLeg;

        // 胴体
        public float TrunkLength = 0.267f;
        public float TrunkWidth = 0.194f;
        public float TrunkHeight = 0.114f;
        public float TrunkMass = 6.0f;

        // 股関節 (胴体中心からのオフセット)
        public float HipOffsetForward = 0.183f;
        public float HipOffsetSide = 0.047f;
        public float HipLinkLength = 0.08f;   // 外転軸から太もも関節までの横方向距離
        public float HipMass = 0.7f;

        // 太もも・すね
        public float ThighLength = 0.2f;
        public float ThighRadius = 0.025f;
        public float ThighMass = 1.0f;
        public float CalfLength = 0.2f;
        public float CalfRadius = 0.013f;
        public float CalfMass = 0.25f;
        public float FootRadius = 0.022f;

        // PD 制御 (単位: N·m/rad, N·m·s/rad)
        public float Kp = 40f;
        public float Kd = 1.0f;
        public float TorqueLimit = 33.5f;

        /// <summary>方策の出力 [-1,1] を関節角オフセット [rad] に変換する倍率。</summary>
        public float ActionScale = 0.5f;

        // 基準姿勢 (rad)。関節の正方向は「親の関節軸まわりの Unity の回転 (左手系)」。
        //   外転 (軸 +z): 正で足先が右 (+x) へ
        //   太もも/すね (軸 +x): 正で足先が後ろ (-z) へ
        public float DefaultHip = 0f;
        public float DefaultThigh = 0.8f;
        public float DefaultCalf = -1.5f;

        public float HipLimit = 0.8f;
        public float ThighMin = -1.0f, ThighMax = 3.0f;
        public float CalfMin = -2.7f, CalfMax = -0.6f;

        /// <summary>スポーン時の胴体中心の高さ (足裏から)。</summary>
        public float SpawnHeight = 0.36f;

        public float TotalMass => TrunkMass + LegCount * (HipMass + ThighMass + CalfMass);

        public static bool IsFront(int leg) => leg < 2;           // 0:FL 1:FR 2:RL 3:RR
        public static float SideSign(int leg) => (leg % 2 == 0) ? -1f : 1f; // 左 = -1, 右 = +1
        public static readonly string[] LegNames = { "FL", "FR", "RL", "RR" };

        /// <summary>胴体座標系での股関節 (外転軸) の位置。</summary>
        public Vec3 HipPosition(int leg) =>
            new Vec3(SideSign(leg) * HipOffsetSide, 0f, IsFront(leg) ? HipOffsetForward : -HipOffsetForward);

        public float[] DefaultJointAngles()
        {
            var q = new float[JointCount];
            for (int leg = 0; leg < LegCount; leg++)
            {
                q[leg * 3 + 0] = DefaultHip;
                q[leg * 3 + 1] = DefaultThigh;
                q[leg * 3 + 2] = DefaultCalf;
            }
            return q;
        }

        public void JointLimits(int joint, out float lower, out float upper)
        {
            switch (joint % 3)
            {
                case 0: lower = -HipLimit; upper = HipLimit; break;
                case 1: lower = ThighMin; upper = ThighMax; break;
                default: lower = CalfMin; upper = CalfMax; break;
            }
        }
    }
}
