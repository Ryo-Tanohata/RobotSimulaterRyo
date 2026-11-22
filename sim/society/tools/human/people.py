"""川辺の五人の見た目の設定。いまはセナだけ。ほかの四人も同じ形で足せる。

macro は MakeHuman の大きなつまみ (0..1)。
- gender: 0=女 1=男
- age: 0.5=25歳, 1.0=90歳。25歳より上は 0.5 + (年齢-25)/65*0.5
- weight / muscle: 0.5 がふつう
targets は MakeHuman の細かい形 (顔・体) の名前と強さ。
"""


def mh_age(years):
    if years >= 25:
        return min(1.0, 0.5 + (years - 25) / 65 * 0.5)
    if years >= 11:
        return 0.1875 + (years - 11) / 14 * (0.5 - 0.1875)
    return max(0.0, (years - 1) / 10 * 0.1875)


# 姿勢: 骨の名前 -> (X, Y, Z) 回転 (度、骨のローカル軸)
STAND = {"rot": {
    "upperarm01.L": (0, 0, 8), "upperarm01.R": (0, 0, -8),
    "lowerarm01.L": (12, 0, 0), "lowerarm01.R": (12, 0, 0),
}}

GATHER = {"rot": {
    # しゃがんで、右手を地面の草へのばす
    "spine05": (0, 0, 0),
    "spine04": (14, 0, 0), "spine03": (14, 0, 0), "spine02": (8, 0, 0),
    "neck01": (-10, 0, 0), "head": (-12, 0, 0),
    "upperleg01.L": (-95, 0, -8), "upperleg01.R": (-80, 0, 10),
    "lowerleg01.L": (140, 0, 0), "lowerleg01.R": (120, 0, 0),
    "foot.L": (-40, 0, 0), "foot.R": (-30, 0, 0),
    "shoulder01.R": (0, 0, 0),
    "upperarm01.R": (60, 0, -20), "lowerarm01.R": (20, 0, 0),
    "upperarm01.L": (30, 0, 25), "lowerarm01.L": (60, 0, 0),
}}

PEOPLE = {
    "sena": {
        "name": "sena",
        "label": "セナ (女・1日目 29歳・54.5kg)",
        "seed": 29,
        "macro": {
            "gender": 0.0, "age": mh_age(29),
            "muscle": 0.62, "weight": 0.6,   # がっしり
            "proportions": 0.5, "height": 0.42, "cupsize": 0.45, "firmness": 0.6,
            "race": {"asian": 0.6, "african": 0.25, "caucasian": 0.15},
        },
        "targets": {
            # 顔: 丸み・口角が上がった笑顔・大きめの瞳
            "head-round": 0.7, "head-fat-incr": 0.25,
            "mouth-angles-up": 0.9, "mouth-laugh-lines-in": 0.0,
            "l-cheek-volume-incr": 0.35, "r-cheek-volume-incr": 0.35,
            "l-eye-scale-incr": 0.9, "r-eye-scale-incr": 0.9,
            "l-eye-height2-incr": 0.4, "r-eye-height2-incr": 0.4,
            "nose-scale-horiz-incr": 0.15,
            # 体: 肩幅と腰がしっかり
            "measure-shoulder-dist-incr": 0.45, "torso-scale-horiz-incr": 0.2,
            "hip-scale-horiz-incr": 0.3, "measure-hips-circ-incr": 0.2,
            "l-upperarm-muscle-incr": 0.3, "r-upperarm-muscle-incr": 0.3,
        },
        "face": {"brow_h": 0.021},
        "skin": {"color": "#8a5636", "lips": "#7a4232", "scar": "#b98c78"},
        "hair": {
            "color": "#0e0b0a", "clump": 0.0105, "cap_off": 0.006,
            "line_front": 32, "line_temple": 14, "line_ear": -14, "line_nape": -52,
            "bang_span": 46, "bang_step": 7.5, "bang_end": 4,
            "side_az": [62, 72, 80], "side_end": -38,
            "back_step": 11, "tie_el": -55, "tie_off": 0.025, "tie_r": 0.02,
            "tail_clumps": 5, "tail_len": 0.36, "tail_gap": 0.03, "tail_width": 0.04,
        },
        "tunic": {
            "color": "#5c3f2a", "cord": "#4a3a2a",
            "neck_drop": 0.03, "sleeve": 0.05, "hem_above_knee": 0.03,
            "push_top": 0.012, "push_skirt": 0.012, "flare": 0.08,
        },
        "poses": {"stand": STAND, "gather": GATHER},
    },
}

# 見た目の「作風」。同じ人を、ちがう絵づくりで出す。
# targets は人の targets に足される (上書き)。hair / skin も上書き。
STYLES = {
    # 写実寄り (最初の版): MakeHuman そのままの顔、輪郭線つき
    "real": {
        "prefix": "", "freestyle": True, "samples": 96, "exposure": -0.5,
        "targets": {}, "hair": {}, "skin": {},
    },
    # 中間 (様式化した写実): 実在の体の比率と PBR はそのまま、顔を少し整える
    "mid": {
        "prefix": "mid_", "outfit": "underwear", "freestyle": False, "samples": 128, "exposure": -0.9,
        "targets": {
            # 目を 1 割ほど大きく、鼻を小さく、あごの線をすっきり
            "l-eye-scale-incr": 0.45, "r-eye-scale-incr": 0.45,
            "nose-scale-horiz-decr": 0.35, "nose-scale-vert-decr": 0.2,
            "nose-scale-horiz-incr": 0.0, "nose-volume-decr": 0.3,
            "nose-point-width-decr": 0.3, "nose-flaring-decr": 0.3,
            "chin-jaw-drop-decr": 0.3, "chin-width-decr": 0.15,
            "chin-prominent-incr": 0.15, "head-fat-incr": 0.1,
            "mouth-scale-horiz-decr": 0.1, "mouth-lowerlip-volume-decr": 0.25,
            "mouth-upperlip-volume-decr": 0.2,
        },
        # 細い束を多く (カード状の髪の代わり)、異方性のつや
        "hair": {"clump": 0.0068, "bang_step": 4.5, "back_step": 5.5,
                 "side_az": [58, 63, 68, 73, 78, 83], "tail_clumps": 11,
                 "strand_tex": True, "aniso": 0.5},
        "skin": {"sss": 0.22, "rough": 0.48, "lip_mix": 0.55},
    },
}
