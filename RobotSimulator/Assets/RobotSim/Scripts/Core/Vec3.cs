using System;

namespace RobotSim.Core
{
    /// <summary>UnityEngine に依存しない最小限の 3 次元ベクトル (Core をテスト可能に保つため)。</summary>
    [Serializable]
    public struct Vec3
    {
        public float x, y, z;

        public Vec3(float x, float y, float z) { this.x = x; this.y = y; this.z = z; }

        public static readonly Vec3 Zero = new Vec3(0f, 0f, 0f);

        public static Vec3 operator +(Vec3 a, Vec3 b) => new Vec3(a.x + b.x, a.y + b.y, a.z + b.z);
        public static Vec3 operator -(Vec3 a, Vec3 b) => new Vec3(a.x - b.x, a.y - b.y, a.z - b.z);
        public static Vec3 operator *(Vec3 a, float s) => new Vec3(a.x * s, a.y * s, a.z * s);

        public float SqrMagnitude => x * x + y * y + z * z;
        public float Magnitude => (float)Math.Sqrt(SqrMagnitude);

        public override string ToString() => $"({x:F3}, {y:F3}, {z:F3})";
    }

    public static class MathUtil
    {
        public static float Clamp(float v, float lo, float hi) => v < lo ? lo : (v > hi ? hi : v);
        public static float Clamp01(float v) => Clamp(v, 0f, 1f);
        public static float Lerp(float a, float b, float t) => a + (b - a) * t;
        public static float Sq(float v) => v * v;

        /// <summary>[0,1) に折り返す。</summary>
        public static float Wrap01(float v)
        {
            v -= (float)Math.Floor(v);
            return v >= 1f ? 0f : v;
        }
    }
}
