using UnityEngine;
#if !ENABLE_LEGACY_INPUT_MANAGER && ROBOTSIM_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace RobotSim
{
    /// <summary>
    /// 旧 Input Manager と新 Input System のどちらの設定でも動くようにする小さなラッパー。
    /// (ROBOTSIM_INPUT_SYSTEM は Input System パッケージがあるときだけ asmdef で定義される)
    /// </summary>
    public static class SimInput
    {
#if ENABLE_LEGACY_INPUT_MANAGER || !ROBOTSIM_INPUT_SYSTEM
        public static bool Key(KeyCode k) => Input.GetKey(k);
        public static bool KeyDown(KeyCode k) => Input.GetKeyDown(k);
        public static bool MouseButton(int b) => Input.GetMouseButton(b);
        public static Vector2 MouseDelta => new Vector2(Input.GetAxis("Mouse X"), Input.GetAxis("Mouse Y")) * 10f;
        public static float Scroll => Input.mouseScrollDelta.y;
#else
        static UnityEngine.InputSystem.Controls.KeyControl Map(KeyCode k)
        {
            var kb = Keyboard.current;
            if (kb == null) return null;
            switch (k)
            {
                case KeyCode.UpArrow: return kb.upArrowKey;
                case KeyCode.DownArrow: return kb.downArrowKey;
                case KeyCode.LeftArrow: return kb.leftArrowKey;
                case KeyCode.RightArrow: return kb.rightArrowKey;
                case KeyCode.Space: return kb.spaceKey;
                case KeyCode.Tab: return kb.tabKey;
                case KeyCode.Equals: return kb.equalsKey;
                case KeyCode.Minus: return kb.minusKey;
                case KeyCode.KeypadPlus: return kb.numpadPlusKey;
                case KeyCode.KeypadMinus: return kb.numpadMinusKey;
                case KeyCode.LeftShift: return kb.leftShiftKey;
            }
            if (k >= KeyCode.Alpha0 && k <= KeyCode.Alpha9) return kb[UnityEngine.InputSystem.Key.Digit0 + (k - KeyCode.Alpha0)];
            if (k >= KeyCode.A && k <= KeyCode.Z) return kb[UnityEngine.InputSystem.Key.A + (k - KeyCode.A)];
            return null;
        }
        public static bool Key(KeyCode k) { var c = Map(k); return c != null && c.isPressed; }
        public static bool KeyDown(KeyCode k) { var c = Map(k); return c != null && c.wasPressedThisFrame; }
        public static bool MouseButton(int b)
        {
            var m = Mouse.current;
            if (m == null) return false;
            return b == 0 ? m.leftButton.isPressed : b == 1 ? m.rightButton.isPressed : m.middleButton.isPressed;
        }
        public static Vector2 MouseDelta => Mouse.current != null ? Mouse.current.delta.ReadValue() * 0.5f : Vector2.zero;
        public static float Scroll => Mouse.current != null ? Mouse.current.scroll.ReadValue().y / 120f : 0f;
#endif
    }
}
