using System;

namespace RobotSim.Core
{
    /// <summary>
    /// 学習前でもロボットを歩かせるための、プログラムされたトロット歩容 (対角脚を交互に振る)。
    /// ML-Agents の Heuristic (手動操作モード) と動作確認に使う。
    /// 強化学習ではこの代わりにニューラルネットが関節角を決める。
    /// </summary>
    public sealed class TrotGait
    {
        readonly RobotConfig _c;

        // 既定値は Web 版 (web/test/evolve.mjs) で遺伝的アルゴリズムにより平地歩行に最適化した値
        public float Frequency = 2.4f;     // 1 周期 / 秒
        public float StepHeight = 0.085f;  // 遊脚の持ち上げ高さ [m]
        public float StandHeight = 0.27f;  // 股関節から足先までの高さ [m]
        public float StrideGain = 1.13f;   // 歩幅の倍率
        public float MaxStride = 0.16f;    // 1 歩の最大長さ [m]
        public float BalanceGain = 0.28f;  // 胴体の傾きに応じて脚を伸縮させる強さ
        public float FootSpread = 0.028f;  // 足先を外側に広げる量 [m]
        public float BodyPitch = -0.03f;   // 前脚と後脚の高さの差 [m]
        public float FootOffset = -0.055f; // 足の前後の基準位置 [m] (脚の重さで重心が胴体中心より後ろにあるため)
        public float PhaseLead = 0.07f;    // 関節の追従遅れを見越して目標を先の位相で出す

        float _phase;
        public float Phase => _phase;

        // 対角ペア: FL と RR は位相 0、FR と RL は位相 0.5
        static readonly float[] PhaseOffset = { 0f, 0.5f, 0.5f, 0f };

        public TrotGait(RobotConfig config) { _c = config; }

        public void Reset() { _phase = 0f; }

        /// <summary>
        /// 1 ステップ進めて 12 関節の目標角を計算する。
        /// </summary>
        /// <param name="vForward">前進速度指令 [m/s]</param>
        /// <param name="vSide">横 (右) 方向速度指令 [m/s]</param>
        /// <param name="yawRate">旋回速度指令 [rad/s] (Unity の y 軸まわり, 正 = 右旋回)</param>
        /// <param name="gravityBody">胴体座標系での重力方向 (単位ベクトル)。傾きの補正に使う。</param>
        public void Step(float dt, float vForward, float vSide, float yawRate, Vec3 gravityBody, float[] targets)
        {
            bool moving = Math.Abs(vForward) > 0.05f || Math.Abs(vSide) > 0.05f || Math.Abs(yawRate) > 0.05f;
            // 止まれの指令でも足踏みは続ける (その場でバランスを取るため) が、小さめに
            _phase = MathUtil.Wrap01(_phase + dt * Frequency);
            float stanceTime = 0.5f / Frequency;

            for (int leg = 0; leg < RobotConfig.LegCount; leg++)
            {
                float side = RobotConfig.SideSign(leg);
                float front = RobotConfig.IsFront(leg) ? 1f : -1f;
                Vec3 hip = _c.HipPosition(leg);

                // 股関節の速度 = v + ω × r   (ω = (0, yawRate, 0))
                float hipVelX = vSide + yawRate * hip.z;
                float hipVelZ = vForward - yawRate * hip.x;
                float strideZ = MathUtil.Clamp(hipVelZ * stanceTime * StrideGain, -MaxStride, MaxStride);
                float strideX = MathUtil.Clamp(hipVelX * stanceTime * StrideGain, -MaxStride * 0.6f, MaxStride * 0.6f);

                float p = MathUtil.Wrap01(_phase + PhaseOffset[leg] + PhaseLead);
                float s;      // -0.5 .. 0.5 : 足先の前後位置 (+ が前)
                float lift;
                if (p < 0.5f)
                {
                    // 立脚: 前 → 後ろへ等速で動かす
                    s = 0.5f - p / 0.5f;
                    lift = 0f;
                }
                else
                {
                    // 遊脚: 先に足を持ち上げてから前へ振り、前で止めてから下ろす (引きずり防止)
                    float t = (p - 0.5f) / 0.5f;
                    s = -0.5f + SmoothStep((t - 0.2f) / 0.6f);
                    lift = (moving ? StepHeight : StepHeight * 0.6f) * (float)Math.Sin(Math.PI * t);
                }

                // 傾き補正: 前が下がったら前脚を伸ばす / 右が下がったら右脚を伸ばす
                float balance = BalanceGain * (gravityBody.z * front + gravityBody.x * side);
                float height = MathUtil.Clamp(StandHeight + balance - lift + BodyPitch * front, 0.12f, 0.36f);

                var foot = new Vec3(
                    side * (_c.HipLinkLength + FootSpread) + strideX * s,
                    -height,
                    strideZ * s + FootOffset);

                LegKinematics.Inverse(_c, side, foot, out float qh, out float qt, out float qc);
                ClampJoint(leg * 3 + 0, ref qh);
                ClampJoint(leg * 3 + 1, ref qt);
                ClampJoint(leg * 3 + 2, ref qc);
                targets[leg * 3 + 0] = qh;
                targets[leg * 3 + 1] = qt;
                targets[leg * 3 + 2] = qc;
            }
        }

        static float SmoothStep(float x)
        {
            x = MathUtil.Clamp01(x);
            return x * x * (3f - 2f * x);
        }

        void ClampJoint(int j, ref float q)
        {
            _c.JointLimits(j, out float lo, out float hi);
            q = MathUtil.Clamp(q, lo, hi);
        }
    }
}
