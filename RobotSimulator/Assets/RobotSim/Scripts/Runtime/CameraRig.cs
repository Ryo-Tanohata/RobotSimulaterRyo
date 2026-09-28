using UnityEngine;

namespace RobotSim
{
    /// <summary>
    /// 選択中のロボットを追いかけるカメラ。右ドラッグで回転、ホイールでズーム、F で全体表示切り替え。
    /// </summary>
    public sealed class CameraRig : MonoBehaviour
    {
        public float Distance = 2.2f;
        public float Yaw = 35f;     // 度
        public float Pitch = 20f;   // 度
        public bool Overview;

        Vector3 _focus;

        void Start()
        {
            var cam = GetComponent<Camera>();
            cam.nearClipPlane = 0.03f;
            cam.farClipPlane = 500f;
            cam.fieldOfView = 55f;
        }

        void LateUpdate()
        {
            var mgr = SimulationManager.Instance;
            if (mgr == null) return;

            if (SimInput.KeyDown(KeyCode.F)) Overview = !Overview;
            if (SimInput.MouseButton(1))
            {
                Vector2 d = SimInput.MouseDelta;
                Yaw += d.x * 0.3f;
                Pitch = Mathf.Clamp(Pitch - d.y * 0.3f, -5f, 85f);
            }
            float scroll = SimInput.Scroll;
            if (Mathf.Abs(scroll) > 0.01f) Distance = Mathf.Clamp(Distance * (1f - scroll * 0.1f), 0.6f, 60f);

            Vector3 target;
            float dist;
            if (Overview || mgr.Selected == null)
            {
                target = mgr.TerrainCenter;
                dist = Mathf.Max(Distance * 12f, 25f);
            }
            else
            {
                target = mgr.Selected.Robot.transform.position;
                dist = Distance;
            }
            _focus = Vector3.Lerp(_focus, target, 1f - Mathf.Exp(-8f * Time.unscaledDeltaTime));
            if ((_focus - target).sqrMagnitude > 100f) _focus = target;

            Quaternion rot = Quaternion.Euler(Pitch, Yaw, 0f);
            transform.position = _focus - rot * Vector3.forward * dist;
            transform.rotation = rot;
        }
    }
}
