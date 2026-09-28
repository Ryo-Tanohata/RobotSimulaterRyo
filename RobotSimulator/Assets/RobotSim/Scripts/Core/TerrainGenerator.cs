using System;

namespace RobotSim.Core
{
    public enum TerrainType
    {
        Rough = 0,       // でこぼこの平地
        SlopeDown = 1,   // 中央が高い坂 (外へ向かって下る)
        SlopeUp = 2,     // 中央が低い坂 (外へ向かって登る)
        StairsDown = 3,  // 中央が高い階段 (外へ向かって降りる)
        StairsUp = 4,    // 中央が低い階段 (外へ向かって登る)
        Obstacles = 5,   // ランダムな段差ブロック
    }

    /// <summary>1 枚のタイル (正方形) の高さマップ。</summary>
    public sealed class TerrainTile
    {
        public TerrainType Type;
        public int Level;            // 難易度 0 .. levels-1
        public float Difficulty;     // 0 .. 1
        public bool Blocky;          // true: セルごとに平らな面 + 垂直な壁 (階段・段差用)
        public float[,] Heights;     // [ix, iz]
        public float CellSize;
        public int Cells;

        public float SizeMeters => Cells * CellSize;

        /// <summary>タイル中心からの相対位置 (m) の高さ。</summary>
        public float HeightAtLocal(float x, float z)
        {
            int ix = (int)Math.Floor(x / CellSize + Cells * 0.5f);
            int iz = (int)Math.Floor(z / CellSize + Cells * 0.5f);
            ix = Math.Max(0, Math.Min(Cells - 1, ix));
            iz = Math.Max(0, Math.Min(Cells - 1, iz));
            return Heights[ix, iz];
        }
    }

    /// <summary>
    /// 難易度カリキュラム用の地形を生成する。行 (z 方向) が難易度、列 (x 方向) が地形の種類。
    /// ロボットはタイル中央の平らな台からスタートして外側へ歩く。
    /// </summary>
    public sealed class TerrainGenerator
    {
        public int Levels = 6;
        public float TileSize = 8f;
        public float CellSize = 0.1f;
        public float PlatformSize = 2.0f;
        public int Seed = 1;

        public static readonly TerrainType[] Types =
        {
            TerrainType.Rough, TerrainType.SlopeDown, TerrainType.SlopeUp,
            TerrainType.StairsDown, TerrainType.StairsUp, TerrainType.Obstacles,
        };

        public int Columns => Types.Length;

        public TerrainTile[,] Generate()
        {
            var rng = new Random(Seed);
            var tiles = new TerrainTile[Columns, Levels];
            for (int col = 0; col < Columns; col++)
                for (int level = 0; level < Levels; level++)
                {
                    float difficulty = Levels > 1 ? level / (float)(Levels - 1) : 0f;
                    tiles[col, level] = GenerateTile(Types[col], level, difficulty, rng);
                }
            return tiles;
        }

        public TerrainTile GenerateTile(TerrainType type, int level, float difficulty, Random rng)
        {
            int cells = (int)Math.Round(TileSize / CellSize);
            var t = new TerrainTile
            {
                Type = type, Level = level, Difficulty = difficulty, CellSize = CellSize, Cells = cells,
                Heights = new float[cells, cells],
                Blocky = type == TerrainType.StairsDown || type == TerrainType.StairsUp || type == TerrainType.Obstacles,
            };

            float half = TileSize * 0.5f;
            float platformHalf = PlatformSize * 0.5f;

            switch (type)
            {
                case TerrainType.Rough:
                    AddNoise(t, rng, 0.01f + 0.05f * difficulty);
                    break;

                case TerrainType.SlopeDown:
                case TerrainType.SlopeUp:
                {
                    float slope = 0.05f + 0.35f * difficulty; // 勾配 (高さ/距離)
                    float sign = type == TerrainType.SlopeDown ? 1f : -1f;
                    ForEachCell(t, (x, z) =>
                    {
                        float r = Math.Max(Math.Abs(x), Math.Abs(z));
                        float dist = half - Math.Max(r, platformHalf); // 端で 0
                        return sign * slope * dist;
                    });
                    if (difficulty > 0.3f) AddNoise(t, rng, 0.02f);
                    break;
                }

                case TerrainType.StairsDown:
                case TerrainType.StairsUp:
                {
                    float stepHeight = 0.05f + 0.15f * difficulty;
                    float stepWidth = 0.3f;
                    float sign = type == TerrainType.StairsDown ? 1f : -1f;
                    ForEachCell(t, (x, z) =>
                    {
                        float r = Math.Max(Math.Abs(x), Math.Abs(z));
                        float dist = half - Math.Max(r, platformHalf);
                        int steps = (int)Math.Floor(dist / stepWidth + 1e-4f);
                        return sign * stepHeight * steps;
                    });
                    break;
                }

                case TerrainType.Obstacles:
                {
                    float maxH = 0.05f + 0.15f * difficulty;
                    int count = 40;
                    for (int n = 0; n < count; n++)
                    {
                        int w = 3 + rng.Next(8), d = 3 + rng.Next(8);
                        int x0 = rng.Next(cells - w), z0 = rng.Next(cells - d);
                        float h = (float)(rng.NextDouble() * 2 - 1) * maxH;
                        for (int ix = x0; ix < x0 + w; ix++)
                            for (int iz = z0; iz < z0 + d; iz++)
                                t.Heights[ix, iz] = h;
                    }
                    break;
                }
            }

            FlattenPlatform(t, platformHalf);
            return t;
        }

        static void ForEachCell(TerrainTile t, Func<float, float, float> f)
        {
            for (int ix = 0; ix < t.Cells; ix++)
                for (int iz = 0; iz < t.Cells; iz++)
                {
                    float x = (ix + 0.5f) * t.CellSize - t.SizeMeters * 0.5f;
                    float z = (iz + 0.5f) * t.CellSize - t.SizeMeters * 0.5f;
                    t.Heights[ix, iz] = f(x, z);
                }
        }

        static void AddNoise(TerrainTile t, Random rng, float amplitude)
        {
            // 2 セルごとに乱数を置いて補間 (なめらかなでこぼこ)
            int n = t.Cells / 2 + 2;
            var coarse = new float[n, n];
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++)
                    coarse[i, j] = (float)(rng.NextDouble() * 2 - 1) * amplitude;
            for (int ix = 0; ix < t.Cells; ix++)
                for (int iz = 0; iz < t.Cells; iz++)
                {
                    float fx = ix * 0.5f, fz = iz * 0.5f;
                    int x0 = (int)fx, z0 = (int)fz;
                    float tx = fx - x0, tz = fz - z0;
                    float a = MathUtil.Lerp(coarse[x0, z0], coarse[x0 + 1, z0], tx);
                    float b = MathUtil.Lerp(coarse[x0, z0 + 1], coarse[x0 + 1, z0 + 1], tx);
                    t.Heights[ix, iz] += MathUtil.Lerp(a, b, tz);
                }
        }

        /// <summary>中央のスタート台を平らにする (台の高さ = 台の縁の高さ)。</summary>
        static void FlattenPlatform(TerrainTile t, float platformHalf)
        {
            float half = t.SizeMeters * 0.5f;
            float h = t.HeightAtLocal(platformHalf - t.CellSize * 0.5f, 0f);
            for (int ix = 0; ix < t.Cells; ix++)
                for (int iz = 0; iz < t.Cells; iz++)
                {
                    float x = (ix + 0.5f) * t.CellSize - half;
                    float z = (iz + 0.5f) * t.CellSize - half;
                    if (Math.Abs(x) < platformHalf && Math.Abs(z) < platformHalf) t.Heights[ix, iz] = h;
                }
        }
    }

    /// <summary>
    /// 地形カリキュラム: 遠くまで歩けたら難しいタイルへ、歩けなかったら易しいタイルへ。
    /// </summary>
    public static class TerrainCurriculum
    {
        public static int NextLevel(int level, int maxLevel, float distanceWalked, float commandedDistance,
                                    float tileSize, Random rng)
        {
            if (distanceWalked > tileSize * 0.5f)
            {
                level++;
                // 最難関を突破したらランダムなレベルに戻す (忘却防止)
                if (level > maxLevel) level = rng.Next(maxLevel + 1);
            }
            else if (distanceWalked < commandedDistance * 0.5f)
            {
                level = Math.Max(0, level - 1);
            }
            return level;
        }
    }
}
