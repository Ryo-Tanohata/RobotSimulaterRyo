namespace RobotSim.Core
{
    /// <summary>
    /// 方策への観測ベクトル (45 次元)。カメラ・LiDAR・地形の高さ情報は一切使わない
    /// 「目の見えない」ロボット: 体の内部センサ (IMU と関節エンコーダ) だけで歩く。
    /// </summary>
    public static class Observation
    {
        public const int Size = 3 + 3 + 3 + RobotConfig.JointCount * 3; // 45

        public const float AngVelScale = 0.25f;
        public const float LinCmdScale = 2.0f;
        public const float YawCmdScale = 0.25f;
        public const float DofVelScale = 0.05f;

        /// <summary>観測を <paramref name="obs"/> に書き込む。</summary>
        public static void Build(RobotState s, VelocityCommand cmd, float[] defaultJoints, float[] lastActions, float[] obs)
        {
            int i = 0;
            obs[i++] = s.AngularVelocity.x * AngVelScale;   // IMU: 角速度
            obs[i++] = s.AngularVelocity.y * AngVelScale;
            obs[i++] = s.AngularVelocity.z * AngVelScale;
            obs[i++] = s.ProjectedGravity.x;                // IMU: 重力方向 (傾き)
            obs[i++] = s.ProjectedGravity.y;
            obs[i++] = s.ProjectedGravity.z;
            obs[i++] = cmd.Forward * LinCmdScale;           // 速度指令
            obs[i++] = cmd.Side * LinCmdScale;
            obs[i++] = cmd.Yaw * YawCmdScale;
            for (int j = 0; j < RobotConfig.JointCount; j++) obs[i++] = s.JointPositions[j] - defaultJoints[j];
            for (int j = 0; j < RobotConfig.JointCount; j++) obs[i++] = s.JointVelocities[j] * DofVelScale;
            for (int j = 0; j < RobotConfig.JointCount; j++) obs[i++] = lastActions[j];
        }
    }
}
