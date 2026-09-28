using System.Collections.Generic;
using RobotSim.Core;
using UnityEngine;
using UnityEngine.Rendering;

namespace RobotSim
{
    /// <summary>
    /// Core の高さマップからメッシュ (見た目 + MeshCollider) を作る。
    /// タイル (列, 難易度) の中心は ワールド座標 ((列+0.5)*size, 0, (難易度+0.5)*size)。
    /// </summary>
    public static class TerrainBuilder
    {
        static readonly Color[] TypeColors =
        {
            new Color(0.55f, 0.75f, 0.55f), // Rough
            new Color(0.75f, 0.70f, 0.50f), // SlopeDown
            new Color(0.80f, 0.60f, 0.45f), // SlopeUp
            new Color(0.55f, 0.65f, 0.85f), // StairsDown
            new Color(0.65f, 0.55f, 0.85f), // StairsUp
            new Color(0.80f, 0.55f, 0.55f), // Obstacles
        };

        public static Vector3 TileCenter(int column, int level, float tileSize) =>
            new Vector3((column + 0.5f) * tileSize, 0f, (level + 0.5f) * tileSize);

        public static GameObject Build(TerrainTile[,] tiles, float tileSize, Transform parent)
        {
            var root = new GameObject("Terrain");
            root.transform.SetParent(parent, false);
            int cols = tiles.GetLength(0), levels = tiles.GetLength(1);
            var materials = new Material[TypeColors.Length];
            for (int i = 0; i < materials.Length; i++) materials[i] = SimAssets.GroundMaterialVisual(TypeColors[i]);

            for (int c = 0; c < cols; c++)
                for (int l = 0; l < levels; l++)
                {
                    var tile = tiles[c, l];
                    var go = new GameObject($"Tile_{tile.Type}_L{l}");
                    go.transform.SetParent(root.transform, false);
                    go.transform.position = TileCenter(c, l, tileSize);
                    var mesh = tile.Blocky ? BuildBlocky(tile, go.transform.position) : BuildSmooth(tile, go.transform.position);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    go.AddComponent<MeshRenderer>().sharedMaterial = materials[(int)tile.Type % materials.Length];
                    var col = go.AddComponent<MeshCollider>();
                    col.sharedMesh = mesh;
                    col.sharedMaterial = SimAssets.GroundMaterial;
                }
            return root;
        }

        const float SkirtBottom = -3f;

        sealed class MeshData
        {
            public readonly List<Vector3> V = new List<Vector3>();
            public readonly List<Vector3> N = new List<Vector3>();
            public readonly List<Vector2> UV = new List<Vector2>();
            public readonly List<int> T = new List<int>();
            public Vector3 Origin;

            public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
            {
                // a-b-c-d は法線側から見て時計回り (Unity の表面)
                int i = V.Count;
                V.Add(a); V.Add(b); V.Add(c); V.Add(d);
                for (int k = 0; k < 4; k++) N.Add(normal);
                AddUv(a, normal); AddUv(b, normal); AddUv(c, normal); AddUv(d, normal);
                T.Add(i); T.Add(i + 1); T.Add(i + 2);
                T.Add(i); T.Add(i + 2); T.Add(i + 3);
            }

            void AddUv(Vector3 p, Vector3 n)
            {
                Vector3 w = p + Origin;
                // 市松模様 1 マス = 1m (テクスチャ 2x2 なので 0.5 倍)
                UV.Add(Mathf.Abs(n.y) > 0.5f ? new Vector2(w.x, w.z) * 0.5f
                    : Mathf.Abs(n.x) > 0.5f ? new Vector2(w.z, w.y) * 0.5f : new Vector2(w.x, w.y) * 0.5f);
            }

            public Mesh ToMesh(string name)
            {
                var m = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
                m.SetVertices(V);
                m.SetNormals(N);
                m.SetUVs(0, UV);
                m.SetTriangles(T, 0);
                m.RecalculateBounds();
                return m;
            }
        }

        /// <summary>セルごとに水平な面と垂直な壁を作る (階段・段差を正確に表現)。</summary>
        static Mesh BuildBlocky(TerrainTile t, Vector3 origin)
        {
            var md = new MeshData { Origin = origin };
            int n = t.Cells;
            float cs = t.CellSize, half = t.SizeMeters * 0.5f;
            float X(int i) => i * cs - half;

            for (int ix = 0; ix < n; ix++)
                for (int iz = 0; iz < n; iz++)
                {
                    float h = t.Heights[ix, iz];
                    float x0 = X(ix), x1 = X(ix + 1), z0 = X(iz), z1 = X(iz + 1);
                    md.Quad(new Vector3(x0, h, z0), new Vector3(x0, h, z1), new Vector3(x1, h, z1), new Vector3(x1, h, z0), Vector3.up);

                    // +x 側の壁
                    float hx = ix + 1 < n ? t.Heights[ix + 1, iz] : SkirtBottom;
                    if (!Mathf.Approximately(h, hx)) WallX(md, x1, z0, z1, h, hx);
                    // +z 側の壁
                    float hz = iz + 1 < n ? t.Heights[ix, iz + 1] : SkirtBottom;
                    if (!Mathf.Approximately(h, hz)) WallZ(md, z1, x0, x1, h, hz);
                    // タイル外周 (-x, -z) のスカート
                    if (ix == 0) WallX(md, x0, z0, z1, SkirtBottom, h);
                    if (iz == 0) WallZ(md, z0, x0, x1, SkirtBottom, h);
                }
            return md.ToMesh("BlockyTile");
        }

        /// <summary>x = const の壁。hA が -x 側、hB が +x 側の高さ。</summary>
        static void WallX(MeshData md, float x, float z0, float z1, float hA, float hB)
        {
            float lo = Mathf.Min(hA, hB), hi = Mathf.Max(hA, hB);
            if (hA > hB) // -x 側が高い → 壁は +x を向く
                md.Quad(new Vector3(x, lo, z0), new Vector3(x, hi, z0), new Vector3(x, hi, z1), new Vector3(x, lo, z1), Vector3.right);
            else
                md.Quad(new Vector3(x, lo, z1), new Vector3(x, hi, z1), new Vector3(x, hi, z0), new Vector3(x, lo, z0), Vector3.left);
        }

        /// <summary>z = const の壁。hA が -z 側、hB が +z 側の高さ。</summary>
        static void WallZ(MeshData md, float z, float x0, float x1, float hA, float hB)
        {
            float lo = Mathf.Min(hA, hB), hi = Mathf.Max(hA, hB);
            if (hA > hB) // -z 側が高い → 壁は +z を向く
                md.Quad(new Vector3(x1, lo, z), new Vector3(x1, hi, z), new Vector3(x0, hi, z), new Vector3(x0, lo, z), Vector3.forward);
            else
                md.Quad(new Vector3(x0, lo, z), new Vector3(x0, hi, z), new Vector3(x1, hi, z), new Vector3(x1, lo, z), Vector3.back);
        }

        /// <summary>頂点を共有するなめらかな面 (坂・でこぼこ用)。</summary>
        static Mesh BuildSmooth(TerrainTile t, Vector3 origin)
        {
            int n = t.Cells;
            float cs = t.CellSize, half = t.SizeMeters * 0.5f;
            var verts = new Vector3[(n + 1) * (n + 1)];
            var uvs = new Vector2[verts.Length];
            for (int ix = 0; ix <= n; ix++)
                for (int iz = 0; iz <= n; iz++)
                {
                    // 頂点の高さ = 周囲のセルの平均
                    float sum = 0f; int cnt = 0;
                    for (int dx = -1; dx <= 0; dx++)
                        for (int dz = -1; dz <= 0; dz++)
                        {
                            int cx = ix + dx, cz = iz + dz;
                            if (cx < 0 || cz < 0 || cx >= n || cz >= n) continue;
                            sum += t.Heights[cx, cz]; cnt++;
                        }
                    var p = new Vector3(ix * cs - half, sum / cnt, iz * cs - half);
                    verts[ix * (n + 1) + iz] = p;
                    uvs[ix * (n + 1) + iz] = new Vector2(p.x + origin.x, p.z + origin.z) * 0.5f;
                }
            var tris = new List<int>(n * n * 6);
            for (int ix = 0; ix < n; ix++)
                for (int iz = 0; iz < n; iz++)
                {
                    int a = ix * (n + 1) + iz, b = a + 1, c = a + (n + 1) + 1, d = a + (n + 1);
                    tris.Add(a); tris.Add(b); tris.Add(c);
                    tris.Add(a); tris.Add(c); tris.Add(d);
                }
            var m = new Mesh { name = "SmoothTile", indexFormat = IndexFormat.UInt32 };
            m.vertices = verts;
            m.uv = uvs;
            m.SetTriangles(tris, 0);
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }
    }
}
