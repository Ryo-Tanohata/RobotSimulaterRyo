using System;

namespace RobotSim.Core
{
    /// <summary>
    /// 1 本の脚 (外転 → 太もも → すね) の順運動学と逆運動学。
    /// 座標は胴体座標系で、原点は外転軸 (股関節) の位置。x = 右, y = 上, z = 前。
    /// 関節角の符号は <see cref="RobotConfig"/> のコメントを参照。
    /// </summary>
    public static class LegKinematics
    {
        /// <summary>関節角 → 足先位置 (股関節基準)。</summary>
        public static Vec3 Forward(RobotConfig c, float side, float hip, float thigh, float calf)
        {
            // 脚平面内 (外転前): 前方 f, 上方 u
            float f = -c.ThighLength * (float)Math.Sin(thigh) - c.CalfLength * (float)Math.Sin(thigh + calf);
            float u = -c.ThighLength * (float)Math.Cos(thigh) - c.CalfLength * (float)Math.Cos(thigh + calf);
            // 太もも関節は外転軸から横に side * HipLinkLength
            float lx = side * c.HipLinkLength;
            // +z 軸まわりに hip だけ回転 (Unity: (x,y) → (x cos - y sin, x sin + y cos))
            float ch = (float)Math.Cos(hip), sh = (float)Math.Sin(hip);
            return new Vec3(lx * ch - u * sh, lx * sh + u * ch, f);
        }

        /// <summary>
        /// 足先位置 (股関節基準) → 関節角。届かない場合は最も近い姿勢に丸める。
        /// 膝は後ろ向き (すね角が負) の解を返す。
        /// </summary>
        public static void Inverse(RobotConfig c, float side, Vec3 foot, out float hip, out float thigh, out float calf)
        {
            float lh = c.HipLinkLength;
            float l1 = c.ThighLength, l2 = c.CalfLength;

            // --- 外転角: x-y 平面で (side*lh, -h') を回転させて (foot.x, foot.y) に合わせる
            float r2 = foot.x * foot.x + foot.y * foot.y;
            float hp2 = Math.Max(r2 - lh * lh, 1e-6f);
            float hPrime = (float)Math.Sqrt(hp2); // 脚平面内での下向き距離
            hip = (float)(Math.Atan2(foot.y, foot.x) - Math.Atan2(-hPrime, side * lh));
            hip = WrapPi(hip);

            // --- 脚平面内の 2 リンク IK: 前方 f = foot.z, 上方 u = -h'
            float f = foot.z, u = -hPrime;
            float d2 = f * f + u * u;
            float maxReach = (l1 + l2) * 0.999f, minReach = Math.Abs(l1 - l2) + 0.01f;
            float d = (float)Math.Sqrt(d2);
            if (d > maxReach) { f *= maxReach / d; u *= maxReach / d; d2 = maxReach * maxReach; }
            else if (d < minReach) { float s = minReach / Math.Max(d, 1e-6f); f *= s; u *= s; d2 = minReach * minReach; }

            float cosK = MathUtil.Clamp((d2 - l1 * l1 - l2 * l2) / (2f * l1 * l2), -1f, 1f);
            calf = -(float)Math.Acos(cosK);
            float k1 = l1 + l2 * (float)Math.Cos(calf);
            float k2 = l2 * (float)Math.Sin(calf);
            // -f = k1 sinθ + k2 cosθ,  -u = k1 cosθ - k2 sinθ
            thigh = (float)(Math.Atan2(-f, -u) - Math.Atan2(k2, k1));
        }

        static float WrapPi(float a)
        {
            while (a > Math.PI) a -= (float)(2 * Math.PI);
            while (a < -Math.PI) a += (float)(2 * Math.PI);
            return a;
        }
    }
}
