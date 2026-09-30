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
