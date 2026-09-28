using System.Collections.Generic;
using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// 実行時に作るメッシュ・マテリアル・物理マテリアルの共有キャッシュ。
    /// (アセットファイルを用意しなくても、どのレンダーパイプラインでも表示できるようにする)
    /// </summary>
    public static class SimAssets
    {
        static readonly Dictionary<PrimitiveType, Mesh> Meshes = new Dictionary<PrimitiveType, Mesh>();
        static readonly Dictionary<Color, Material> Materials = new Dictionary<Color, Material>();
        static Material _baseMaterial;
        static Texture2D _checker;

#if UNITY_2023_1_OR_NEWER
        static PhysicsMaterial _foot, _robot, _ground;
        public static PhysicsMaterial FootMaterial => _foot ??= MakePhysics("Foot", 1.0f);
        public static PhysicsMaterial RobotMaterial => _robot ??= MakePhysics("Robot", 0.6f);
        public static PhysicsMaterial GroundMaterial => _ground ??= MakePhysics("Ground", 1.0f);
        static PhysicsMaterial MakePhysics(string name, float friction) =>
            new PhysicsMaterial(name) { staticFriction = friction, dynamicFriction = friction, bounciness = 0f };
#else
        static PhysicMaterial _foot, _robot, _ground;
        public static PhysicMaterial FootMaterial => _foot ??= MakePhysics("Foot", 1.0f);
        public static PhysicMaterial RobotMaterial => _robot ??= MakePhysics("Robot", 0.6f);
        public static PhysicMaterial GroundMaterial => _ground ??= MakePhysics("Ground", 1.0f);
        static PhysicMaterial MakePhysics(string name, float friction) =>
            new PhysicMaterial(name) { staticFriction = friction, dynamicFriction = friction, bounciness = 0f };
#endif

        public static Mesh PrimitiveMesh(PrimitiveType type)
        {
            if (Meshes.TryGetValue(type, out var mesh) && mesh != null) return mesh;
            var go = GameObject.CreatePrimitive(type);
            mesh = go.GetComponent<MeshFilter>().sharedMesh;
            if (_baseMaterial == null) _baseMaterial = go.GetComponent<MeshRenderer>().sharedMaterial;
            Object.DestroyImmediate(go);
            Meshes[type] = mesh;
            return mesh;
        }

        /// <summary>現在のレンダーパイプラインの既定マテリアルを複製して色を付ける。</summary>
        public static Material ColoredMaterial(Color color)
        {
            if (Materials.TryGetValue(color, out var m) && m != null) return m;
            if (_baseMaterial == null) PrimitiveMesh(PrimitiveType.Cube);
            m = new Material(_baseMaterial) { color = color };
            Materials[color] = m;
            return m;
        }

        /// <summary>地面用: 1m 四方の市松模様 (動きがわかりやすいように)。</summary>
        public static Material GroundMaterialVisual(Color tint)
        {
            if (_checker == null)
            {
                _checker = new Texture2D(2, 2, TextureFormat.RGBA32, false)
                {
                    filterMode = FilterMode.Point,
                    wrapMode = TextureWrapMode.Repeat,
                };
                var a = new Color(1f, 1f, 1f);
                var b = new Color(0.82f, 0.82f, 0.82f);
                _checker.SetPixels(new[] { a, b, b, a });
                _checker.Apply();
            }
            if (_baseMaterial == null) PrimitiveMesh(PrimitiveType.Cube);
            return new Material(_baseMaterial) { color = tint, mainTexture = _checker };
        }

        /// <summary>当たり判定を持たない見た目だけの子オブジェクトを作る。</summary>
        public static GameObject AddVisual(Transform parent, PrimitiveType type, Vector3 localPos, Quaternion localRot,
                                           Vector3 scale, Color color)
        {
            var go = new GameObject(type + "_visual");
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localRotation = localRot;
            go.transform.localScale = scale;
            go.AddComponent<MeshFilter>().sharedMesh = PrimitiveMesh(type);
            go.AddComponent<MeshRenderer>().sharedMaterial = ColoredMaterial(color);
            return go;
        }
    }
}
