"""2 足歩行のお手本 (関節角の時間変化) を数式で作る。モーションキャプチャなど他人のデータは使わない。

人の歩行の一般的な関節角度の形 (教科書的な値の大まかな形) をまねた、周期的な曲線:
- 股関節: 足を着いた瞬間に約 25° 前へ曲げ、蹴り出しで約 10° 後ろへ伸ばす
- 膝: 着地後に少し曲げて衝撃を受け、振り出しで約 60° 曲げる
- 足首: 蹴り出しでつま先を下げ、振り出しではつま先を上げる
- 腕: 反対側の脚と逆に振る (左脚が前のとき左腕は後ろ)
phase は 0〜1 (左足が着いた瞬間が 0)。右脚は半周期ずらす。角度の符号は body.py の関節の向きに合わせる
(股関節・肩: + が後ろ、膝: + が曲げる、足首: + がつま先を下げる、肘: - が曲げる)。
"""
import jax.numpy as jp

from body import actuated_joints

FREQ = 1.6  # 1 秒あたりの歩数の半分 (左右 1 周期 / 秒)


def _bump(ph, center, width):
    """周期的なこぶ (ph の近くが center のとき 1)"""
    d = (ph - center + 0.5) % 1.0 - 0.5
    return jp.exp(-0.5 * (d / width) ** 2)


def _leg(ph):
    rad = jp.pi / 180
    hip = (-7.5 - 17.5 * jp.cos(2 * jp.pi * ph)) * rad
    knee = (5 + 12 * _bump(ph, 0.12, 0.07) + 55 * _bump(ph, 0.72, 0.11)) * rad
    ankle = (15 * _bump(ph, 0.6, 0.06) - 8 * _bump(ph, 0.35, 0.12) - 6 * _bump(ph, 0.82, 0.08)) * rad
    return hip, knee, ankle


def reference(phase):
    """phase (0〜1) → actuated_joints() の順の目標角 (rad)"""
    rad = jp.pi / 180
    q = {}
    for side, off, sign in (("l", 0.0, 1.0), ("r", 0.5, -1.0)):
        ph = (phase + off) % 1.0
        hip, knee, ankle = _leg(ph)
        q[f"{side}_hip_y"], q[f"{side}_knee"], q[f"{side}_ankle_y"] = hip, knee, ankle
        q[f"{side}_hip_x"] = q[f"{side}_hip_z"] = q[f"{side}_ankle_x"] = 0.0 * ph
        q[f"{side}_shoulder_y"] = 15 * rad * jp.cos(2 * jp.pi * ph)
        q[f"{side}_shoulder_x"] = sign * 6 * rad + 0.0 * ph  # 腕を少し外へ (体に当たらないように)
        q[f"{side}_elbow"] = -20 * rad + 0.0 * ph
    q["waist"] = 3 * rad + 0.0 * phase
    return jp.stack([jp.asarray(q[n]) for n in actuated_joints()])


# ---- 4 足 (拳を地面に着けて歩く、ナックルウォーク) のお手本 ----
# チンパンジーなどの霊長類は「斜め順」の歩き方 (左後ろ → 右前 → 右後ろ → 左前) をすることが多いとされる。
# 胴体を前へ QUAD_PITCH 度倒し、腕はほぼ真下に伸ばして拳で、脚は膝を曲げて足の裏で体を支える。
# 姿勢の角度は体の長さ (s) から計算する (肩と骨盤の高さが、腕と脚の長さにつり合うように)。
QUAD_FREQ = 1.4
QUAD_PITCH = 75.0  # 胴体を前へ倒す角度 (度)。0 = まっすぐ立つ
QUAD_DUTY = 0.7    # 1 周期のうち地面に着いている割合
QUAD_OFFSET = {"l_hip": 0.0, "r_arm": 0.25, "r_hip": 0.5, "l_arm": 0.75}  # 斜め順


def quad_pose(s):
    """体の形 s に合わせた 4 足の基本姿勢 (度): 股関節・膝・足首・肩"""
    import math

    from body import TRUNK, shape
    sh = shape(s)
    shoulder_h = sh.upper_arm + sh.forearm + 0.075  # 腕を真下に伸ばしたときの肩の高さ (拳の球の分を含む)
    trunk = TRUNK + 0.05
    pelvis_h = shoulder_h - trunk * math.cos(math.radians(QUAD_PITCH))
    legs = sh.thigh + sh.shank
    a = math.degrees(math.acos(max(-1.0, min(1.0, (pelvis_h - 0.05) / legs))))  # 大腿と下腿を同じ角度だけ傾ける
    return {"hip": -(QUAD_PITCH + a), "knee": 2 * a, "ankle": -a, "shoulder": -QUAD_PITCH}


def _limb(ph, amp):
    """地面に着いている間は前 → 後ろへ、浮いている間は後ろ → 前へ。戻り (度, 持ち上げ 0〜1)"""
    stance = ph < QUAD_DUTY
    u = jp.where(stance, ph / QUAD_DUTY, (ph - QUAD_DUTY) / (1 - QUAD_DUTY))
    sweep = jp.where(stance, amp * (2 * u - 1), amp * (1 - 2 * u))  # + が後ろ
    lift = jp.where(stance, 0.0, jp.sin(jp.pi * u))
    return sweep, lift


def make_quad(s):
    base = quad_pose(s)
    rad = jp.pi / 180

    def ref(phase):
        q = {}
        for side, sign in (("l", 1.0), ("r", -1.0)):
            sw, lift = _limb((phase + QUAD_OFFSET[f"{side}_hip"]) % 1.0, 15.0)
            q[f"{side}_hip_y"] = (base["hip"] + sw) * rad
            q[f"{side}_knee"] = (base["knee"] + 25 * lift) * rad
            q[f"{side}_ankle_y"] = (base["ankle"] - sw) * rad
            q[f"{side}_hip_x"] = q[f"{side}_hip_z"] = q[f"{side}_ankle_x"] = 0.0 * sw
            sw, lift = _limb((phase + QUAD_OFFSET[f"{side}_arm"]) % 1.0, 15.0)
            q[f"{side}_shoulder_y"] = (base["shoulder"] + sw) * rad
            q[f"{side}_shoulder_x"] = sign * 6 * rad + 0.0 * sw
            q[f"{side}_elbow"] = -35 * lift * rad
        q["waist"] = 0.0 * phase
        return jp.stack([jp.asarray(q[n]) for n in actuated_joints()])

    return ref


# ---- 実験 2: 体の形に合わせたお手本 ----
# (1) 周期を脚の長さに合わせる: 振り子のように、脚が短いほど速く振る (周期 ∝ √(脚の長さ))。人型 (脚 0.83 m) を基準にする
# (2) チンパンジー型の 2 足は「股関節と膝を曲げたまま歩く」(bent-hip bent-knee) 姿勢にする。人に近づくほど伸びる
#     曲げる量 (s = 0 で膝 +25°、股関節 -20°、胴体の前傾 +15°) は、文献の定性的な記述に合わせた仮定の値
HUMAN_LEG = 0.83


def _leg_length(s):
    from body import shape
    sh = shape(s)
    return sh.thigh + sh.shank


def make_biped_scaled(s):
    rad = jp.pi / 180
    k = 1.0 - s  # 曲げる強さ
    knee_off, hip_off = 25.0 * k, -20.0 * k
    ankle_off = -(hip_off + knee_off)  # 足の裏を床と平らに

    def ref(phase):
        q = reference(phase)
        names = actuated_joints()
        add = jp.zeros(len(names))
        for i, n in enumerate(names):
            if n.endswith("_knee"):
                add = add.at[i].set(knee_off * rad)
            elif n.endswith("_hip_y"):
                add = add.at[i].set(hip_off * rad)
            elif n.endswith("_ankle_y"):
                add = add.at[i].set(ankle_off * rad)
            elif n == "waist":
                add = add.at[i].set(12.0 * k * rad)
        return q + add

    return ref


def make(gait, s, scaled=False):
    """(お手本の関数, 1 秒あたりの周期, 胴体を前へ倒す角度 (度))。scaled=True は実験 2 (体の形に合わせる)"""
    f = (HUMAN_LEG / _leg_length(s)) ** 0.5 if scaled else 1.0
    if gait == "quad":
        return make_quad(s), QUAD_FREQ * f, QUAD_PITCH
    if scaled:
        return make_biped_scaled(s), FREQ * f, 0.0
    return reference, FREQ, 0.0

# ---- 人型の歩き方 2 (人間らしさを優先) ----
# 実験 1 の 2 足のお手本は 1 秒に 1.6 周期 (3.2 歩) で、0.8 m/s だと 1 歩 25 cm の小股になっていた。
# 人の歩行 (1.0〜1.3 m/s で 1 秒に約 0.9〜1 周期、1 周期の歩幅 1.0〜1.4 m) に近づける:
# - 速さ v に合わせて、周期と歩幅をどちらも √(v / 1.0) 倍にする (v = 周期 × 歩幅)
# - 腕を大きく振り (±25°)、前へ振るときに肘を曲げる
# - かかとから着地し (つま先を上げる)、足裏全体 → つま先で蹴り出す
HUMAN2_V0 = 1.0     # 基準の速さ (m/s)
HUMAN2_FREQ0 = 0.95  # 基準の速さでの 1 秒あたりの周期


def human2_freq(v):
    return HUMAN2_FREQ0 * jp.sqrt(v / HUMAN2_V0)


def human2(phase, v):
    """phase (0〜1、左足のかかとが着いた瞬間が 0) と速さ v (m/s) → 目標角 (rad)"""
    rad = jp.pi / 180
    a = jp.clip(jp.sqrt(v / HUMAN2_V0), 0.6, 1.4)
    q = {}
    for side, off, sign in (("l", 0.0, 1.0), ("r", 0.5, -1.0)):
        ph = (phase + off) % 1.0
        c = jp.cos(2 * jp.pi * ph)
        q[f"{side}_hip_y"] = (-7.5 - 17.5 * a * c) * rad
        q[f"{side}_knee"] = (4 + 14 * a * _bump(ph, 0.12, 0.06) + (52 + 8 * a) * _bump(ph, 0.72, 0.1)) * rad
        q[f"{side}_ankle_y"] = (-6 * _bump(ph, 0.0, 0.035)             # かかとから着地 (つま先を上げる)
                                - 8 * _bump(ph, 0.42, 0.1)              # 体が足の上を越える (すねが前へ傾く)
                                + 20 * a * _bump(ph, 0.6, 0.05)         # つま先で蹴り出す
                                - 7 * _bump(ph, 0.82, 0.07)) * rad      # 振り出しでつま先を上げる (つまずかないように)
        q[f"{side}_hip_x"] = q[f"{side}_hip_z"] = q[f"{side}_ankle_x"] = 0.0 * c
        q[f"{side}_shoulder_y"] = 25 * a * c * rad                     # 脚と逆に振る (左脚が前 → 左腕は後ろ)
        q[f"{side}_shoulder_x"] = sign * 6 * rad + 0.0 * c
        q[f"{side}_elbow"] = -(15 + 20 * a * (1 - c) / 2) * rad         # 腕が前のときほど肘を曲げる
    q["waist"] = (3 + 2 * a) * rad
    return jp.stack([jp.asarray(q[n]) for n in actuated_joints()])