"""形のつまみ s (0 = チンパンジー型、1 = 人型) から、学習に使う体 (MuJoCo の MJCF) を作る。

長さの単位は m、重さは kg。胴体の長さは 0.5 m にそろえ、腕と脚の長さを変える。
- 腕と脚の長さの比 (intermembral index) は s = 0 で約 107、s = 0.5 で約 84 (ルーシーに近い)、s = 1 で約 69
  (チンパンジー 約 106、ルーシー 約 85〜88、人 約 68〜72。docs/bipedal_plan.md 2.1)
- それ以外 (股関節・膝を伸ばせる角度、足の長さ、重さの配分) は定性的な違いを表した仮定の値
"""
from dataclasses import dataclass

TRUNK = 0.5        # 胴体の長さ (骨盤から肩まで)
TOTAL_MASS = 45.0  # 体重 (すべての s で同じにして比べる)
GAP = 0.035        # 棒人間の見た目で、関節のつなぎ目を空ける長さ


def lerp(a, b, s):
    return a + (b - a) * s


@dataclass
class Shape:
    s: float
    thigh: float      # 大腿 (股関節 → 膝)
    shank: float      # 下腿 (膝 → 足首)
    upper_arm: float  # 上腕 (肩 → 肘)
    forearm: float    # 前腕 (肘 → 手首)
    foot: float       # 足の長さ
    heel: float       # 足首より後ろの長さ (かかと)
    hip_ext: float    # 股関節を胴体の線より後ろへ伸ばせる角度 (度)
    knee_min: float   # 膝を伸ばしきれない角度 (度。0 = まっすぐまで伸びる)
    arm_frac: float   # 両腕の重さ ÷ 体重
    leg_frac: float   # 両脚の重さ ÷ 体重
    muzzle: float     # 口の突き出し (見た目だけ)
    fur: tuple        # 体の色 (見た目だけ)

    @property
    def imi(self):
        return 100 * (self.upper_arm + self.forearm) / (self.thigh + self.shank)


def shape(s):
    return Shape(
        s=s,
        thigh=lerp(0.29, 0.45, s), shank=lerp(0.25, 0.38, s),
        upper_arm=lerp(0.30, 0.32, s), forearm=lerp(0.28, 0.25, s),
        foot=lerp(0.12, 0.22, s), heel=lerp(0.02, 0.05, s),
        hip_ext=lerp(5, 30, s), knee_min=lerp(15, 0, s),
        arm_frac=lerp(0.16, 0.10, s), leg_frac=lerp(0.24, 0.32, s),
        muzzle=lerp(0.07, 0.0, s),
        fur=tuple(lerp(a, b, s) for a, b in zip((0.25, 0.17, 0.12), (0.93, 0.76, 0.62))),
    )


def _f(*v):
    return " ".join(f"{x:.4g}" for x in v)


def body_xml(s, prefix="", pos=(0, 0, 1.0), tendon=False):
    """1 体ぶんの <body> (根元は骨盤、自由に動ける)"""
    sh = shape(s)
    p = prefix
    col = _f(*sh.fur, 1)
    skin = _f(*(lerp(c, 1, 0.25) for c in sh.fur), 1)
    m_arm = TOTAL_MASS * sh.arm_frac / 2
    m_leg = TOTAL_MASS * sh.leg_frac / 2
    m_head = TOTAL_MASS * 0.075
    m_trunk = TOTAL_MASS - 2 * m_arm - 2 * m_leg - m_head
    hw = 0.12  # 骨盤・肩の半分の幅
    # 見た目は棒人間: 当たり判定と重さの形 (group 3) は表示せず、細い線を重さ 0 で重ねる。つなぎ目は GAP だけ空ける
    vis = f'contype="0" conaffinity="0" mass="0" rgba="{col}"'
    stick = lambda a, b, r=0.045: f'<geom type="capsule" fromto="0 0 {a + GAP * (1 if b > a else -1):.4f} 0 0 {b - GAP * (1 if b > a else -1):.4f}" size="{r}" {vis}/>'
    stick_x = lambda a, b, z: f'<geom type="capsule" fromto="{a:.4f} 0 {z} {b:.4f} 0 {z}" size="0.035" {vis}/>'

    # tendon=True: 足首にばね (アキレス腱の代わり、実験 2)。人に近いほど強い (s = 1 で 60 N·m/rad、仮定の値)。
    # ばねの力は関節を動かす力 (actuator) に数えないので、ばねが蓄えて返したエネルギーは「仕事のコスト」に入らない
    ankle_spring = f' stiffness="{60 * s:.1f}" springref="0"' if tendon and s > 0 else ""

    def leg(side, y):
        # 脚の重さは 大腿 : 下腿 : 足 = 0.6 : 0.3 : 0.1 (仮定)
        return f"""
      <body name="{p}{side}_thigh" pos="0 {y} 0">
        <joint name="{p}{side}_hip_y" axis="0 1 0" range="{-135} {sh.hip_ext:.1f}"/>
        <joint name="{p}{side}_hip_x" axis="1 0 0" range="-30 30"/>
        <joint name="{p}{side}_hip_z" axis="0 0 1" range="-30 30"/>
        <geom type="capsule" fromto="0 0 0 0 0 {-sh.thigh:.4f}" size="0.05" mass="{m_leg * 0.6:.3f}" group="3"/>{stick(0, -sh.thigh)}
        <body name="{p}{side}_shank" pos="0 0 {-sh.thigh:.4f}">
          <joint name="{p}{side}_knee" axis="0 1 0" range="{sh.knee_min:.1f} 150"/>
          <geom type="capsule" fromto="0 0 0 0 0 {-sh.shank:.4f}" size="0.04" mass="{m_leg * 0.3:.3f}" group="3"/>{stick(0, -sh.shank)}
          <body name="{p}{side}_foot" pos="0 0 {-sh.shank:.4f}">
            <joint name="{p}{side}_ankle_y" axis="0 1 0" range="-45 45"{ankle_spring}/>
            <joint name="{p}{side}_ankle_x" axis="1 0 0" range="-25 25"/>
            <geom name="{p}{side}_foot" type="box" pos="{(sh.foot / 2 - sh.heel):.4f} 0 -0.025" size="{sh.foot / 2:.4f} 0.045 0.025"
                  mass="{m_leg * 0.1:.3f}" group="3"/>{stick_x(-sh.heel + GAP, sh.foot - sh.heel, -0.04)}
          </body>
        </body>
      </body>"""

    def arm(side, y):
        # 腕の重さは 上腕 : 前腕 : 手 = 0.5 : 0.35 : 0.15 (仮定)。手は拳 (ナックル) の球
        return f"""
        <body name="{p}{side}_upper_arm" pos="0 {y} {TRUNK:.4f}">
          <joint name="{p}{side}_shoulder_y" axis="0 1 0" range="-180 60"/>
          <joint name="{p}{side}_shoulder_x" axis="1 0 0" range="-20 120" ref="0"/>
          <geom type="capsule" fromto="0 0 0 0 0 {-sh.upper_arm:.4f}" size="0.04" mass="{m_arm * 0.5:.3f}" group="3"/>{stick(0, -sh.upper_arm)}
          <body name="{p}{side}_forearm" pos="0 0 {-sh.upper_arm:.4f}">
            <joint name="{p}{side}_elbow" axis="0 1 0" range="-150 0"/>
            <geom type="capsule" fromto="0 0 0 0 0 {-sh.forearm:.4f}" size="0.035" mass="{m_arm * 0.35:.3f}" group="3"/>{stick(0, -sh.forearm)}
            <geom name="{p}{side}_hand" type="sphere" pos="0 0 {-sh.forearm - 0.03:.4f}" size="0.045" mass="{m_arm * 0.15:.3f}" group="3"/>
          </body>
        </body>"""

    # 左右で肩の外転 (x 軸) の向きが逆になるよう、右腕は range を反転する
    left_arm = arm("l", hw + 0.05)
    right_arm = arm("r", -hw - 0.05).replace('range="-20 120"', 'range="-120 20"')
    return f"""
  <body name="{p}pelvis" pos="{_f(*pos)}">
    <freejoint name="{p}root"/>
    <geom type="capsule" fromto="0 {-hw} 0 0 {hw} 0" size="0.07" mass="{m_trunk * 0.4:.3f}" group="3"/>
    {leg("l", hw * 0.8)}
    {leg("r", -hw * 0.8)}
    <body name="{p}chest" pos="0 0 0.05">
      <joint name="{p}waist" axis="0 1 0" range="-30 45"/>
      <geom type="capsule" fromto="0 0 0.05 0 0 {TRUNK - 0.08:.4f}" size="0.11" mass="{m_trunk * 0.45:.3f}" group="3"/>{stick(-0.05, TRUNK, 0.07)}
      <geom type="capsule" fromto="0 {-hw - 0.04} {TRUNK - 0.05:.4f} 0 {hw + 0.04} {TRUNK - 0.05:.4f}" size="0.06" mass="{m_trunk * 0.15:.3f}" group="3"/>
      <body name="{p}head" pos="0 0 {TRUNK + 0.14:.4f}">
        <geom type="sphere" size="0.1" mass="{m_head:.3f}" group="3"/>
        <geom type="sphere" size="0.085" {vis}/>
      </body>
      {left_arm}
      {right_arm}
    </body>
  </body>"""


def actuated_joints(prefix=""):
    names = []
    for side in "lr":
        names += [f"{prefix}{side}_{j}" for j in ("hip_y", "hip_x", "hip_z", "knee", "ankle_y", "ankle_x")]
    names.append(f"{prefix}waist")
    for side in "lr":
        names += [f"{prefix}{side}_{j}" for j in ("shoulder_y", "shoulder_x", "elbow")]
    return names


def model_xml(bodies, with_actuators=True, tendon=False):
    """bodies: [(s, prefix, pos), ...] を 1 つの世界に並べた MJCF"""
    parts = "".join(body_xml(s, p, pos, tendon) for s, p, pos in bodies)
    acts = ""
    if with_actuators:
        # 位置制御 (PD)。力の大きさは体重に合わせた仮の値。消費エネルギーは |力 × 角速度| で測る
        acts = "<actuator>" + "".join(
            f'<position joint="{j}" kp="{120 if "arm" not in j and "shoulder" not in j and "elbow" not in j else 60}" kv="3" forcerange="-150 150"/>'
            for _, p, _ in bodies for j in actuated_joints(p)) + "</actuator>"
    return f"""<mujoco model="ape_to_human">
  <compiler angle="degree" autolimits="true"/>
  <option timestep="0.004"/>
  <default><joint damping="1" armature="0.02" limited="true"/><geom friction="1 0.05 0.01" condim="3"/></default>
  <visual><headlight diffuse="0.6 0.6 0.6" ambient="0.35 0.35 0.35"/><global offwidth="1600" offheight="700"/></visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.75 0.85 0.95" rgb2="0.95 0.97 1" width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.55 0.68 0.52" rgb2="0.5 0.63 0.47" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="8 8"/>
  </asset>
  <worldbody>
    <light pos="0 -2 4" dir="0 0.4 -1" diffuse="0.6 0.6 0.6"/>
    <geom name="floor" type="plane" size="20 20 0.1" material="grid"/>
    {parts}
  </worldbody>
  {acts}
</mujoco>"""


if __name__ == "__main__":
    print(" s    脚    腕    腕÷脚×100  足    股関節伸展  膝の最小角")
    for s in (0, 0.25, 0.5, 0.75, 1):
        sh = shape(s)
        print(f"{s:4.2f} {sh.thigh + sh.shank:.3f} {sh.upper_arm + sh.forearm:.3f} {sh.imi:8.1f}   "
              f"{sh.foot:.2f}  {sh.hip_ext:5.1f}°     {sh.knee_min:4.1f}°")
