"""川辺の五人の見た目の設定。PEOPLE / STYLES は MakeHuman の道 (セナだけ)、VROID は VRoid の道 (五人)。

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

# ---------------------------------------------------------------- VRoid の素体から作る道
# build_person_vroid.py が使う。どれも VRoid の CC0 サンプル (madjin/vrm-samples の vroid/beta/)。
# 体と骨組み (body_src): 女は「HairSample_Female」、男は「HairSample_Male」(服の下の肌が全部ある)。
# 顔 (face_src) と髪の部品 (hair.parts) は人ごとに選ぶ。数値はすべて「素体からどれだけ変えるか」。
# 高さ (tie_z, outfit など) は女の素体の高さで書く。男の体へは骨の高さで写す (Frame.z)。
#
# 主なキー
#   skin.tan       肌: テクスチャの中央値をこの色 (sRGB) に合わせる掛け算。顔と体で別々に合わせる
#   skin.fill_dark 体のテクスチャに描かれた下着・靴下 (暗いところ) を肌の色でうめる (男の素体)
#   skin.scars     古い傷の線 (骨の上の区間 s、ずらし off、斜め slant)。patches は煤などのしみ
#   hair.parts     髪の部品: {"src": サンプル, "part": "Hair001"(前・横・後ろ) か "HairBack"(地肌に近い後ろ髪),
#                  "drop": 消す材質, "drop_parts": 消す束 (頭の骨からの重心の位置)}
#   hair.style     keep (そのまま) / tie (低く結ぶ) / braid (結んで三つ編み)。hair.crop で短く刈る
#   hair.dark/light 髪は明るさだけを使い、この 2 色の間に置く
#   body           肩幅 (m)・腰・胴まわり・胸板 (割合)、腕と脚の太さ (骨の軸から外へ。負なら細く)
#   scale/legs/arms 背の高さ・脚の長さ・腕の長さ (倍)
#   face.round     ほお・あごを横に (負ならこけた頬)。face.brow_thick 眉を縦に何倍
#   expr           ふだんの顔 (VRM の表情キーを少しずつ)。gaze_down 目を下へ (度、描くときだけ)
#   outfit         無地の胸の帯 (top、女だけ) と短パン (shorts)
SHINO, HS_F, HS_M = "Sendagaya_Shino.vrm", "HairSample_Female.vrm", "HairSample_Male.vrm"
FUMI, VICT = "Sakurada_Fumiriya.vrm", "Victoria_Rubin.vrm"
LINES_DARK = {"brow": "#231814", "eyeline": "#2c1612", "lash": "#24120f"}
SHORTS = {"color": "#161514", "top": None, "shorts": (0.805, 1.0)}

# ---------------------------------------------------------------- 服 (2026-11-25 本人「以前服を作ったのでそれを着せてください」)
# ソナ85 と解説の係に着せた、ヤギのなめし革の貫頭衣と革紐の帯を、村の人みなに。女はすねまで、男と子はひざのあたりまで。色は人ごとに少し変える
LEATHER = ["#7a5638", "#8a6242", "#6e4c32", "#94704c", "#7e5a3e", "#86603e", "#705034"]
BELTS = ["#3e2a1c", "#4a3020", "#3a281a"]
# 2026-11-25 本人「各時代や世代、フェーズに合わせてファッションも進化させてください」→ docs/society_phase/fashion.md
# 時代 (ERA): hide = Society 1.0〜G1 (けものの生皮をそのまま。灰色がかった茶、丈は短め、すそはまっすぐ、細い紐)。
#              leather = ヤギを飼ってから (ヤギのなめし革。明るい茶、女はすねまで、男はひざ、革紐の帯)。この先の時代は fashion.md の表
HIDE = ["#5e4a38", "#6a5440", "#54402e", "#73604a", "#4e3e30", "#665040"]
ERA = __import__("os").environ.get("PEOPLE_ERA", "leather")


def tunic(sex, k, child=False, era=None):
    era = era or ERA
    if era == "hide":
        long_ = sex == "女" and not child
        return {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
                "dress": {"color": HIDE[k % len(HIDE)], "belt": "#2e2418", "waist": 1.00, "arm": 1.215,
                          "neck": 1.335, "hem": 0.50 if long_ else 0.66, "flare": 0.06, "push": 0.008, "sleeve_x": 0.22}}
    long_ = sex == "女" and not child
    return {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
            "dress": {"color": LEATHER[k % len(LEATHER)], "belt": BELTS[k % len(BELTS)], "waist": 1.00, "arm": 1.215,
                      "neck": 1.335, "hem": 0.40 if long_ else 0.60, "flare": 0.2 if long_ else 0.12, "push": 0.008, "sleeve_x": 0.26}}


VROID = {
    "sena": {
        "name": "sena",
        "label": "セナ (女・1日目 29歳・54.5kg)",
        "body_src": HS_F,   # 体・骨組み (服の下の肌が全部ある)
        "face_src": SHINO,  # 顔: 千駄ヶ谷 篠
        "skin": {"tan": "#9a6448", "sss": 0.15, "rough": 0.5,
                 "blush": "#c0584a", "blush_alpha": 0.32,
                 # 左の前腕の外側 (上を向いた面) に古い傷
                 "scars": [{"bone": "J_Bip_L_LowerArm", "s": (0.35, 0.57), "slant": (0, 0.022, 0),
                            "off": (0, 0, 0.06), "color": "#c9907e", "alpha": 0.75, "width": 2.2}]},
        # 髪: 篠の髪 (髪どめ HAIR_02 を消す) を黒くして、うなじで低く結ぶ
        "hair": {"parts": [{"src": SHINO, "part": "Hair001", "drop": ["HAIR_02"]},
                           {"src": SHINO, "part": "HairBack"}],
                 "style": "tie",
                 "dark": "#080606", "light": "#1e1815", "ramp_lo": 0.35, "rough": 0.5,
                 "tie_z": 1.30, "gather_from": 1.385, "tail_width": 0.028,
                 "front_from": 1.37, "front_keep": 0.6, "tie_color": "#5a3b26"},
        # 眉・目の線・まつ毛の色 (アニメの線のまま、光の影響なし)
        "lines": LINES_DARK,
        "iris": {"hue": 0.0, "sat": 0.85, "val": 1.0, "tint": "#9a6a4c", "highlight": 0.8},
        # 体: がっしり (肩幅・腰・腕と脚の太さ・胴まわり)
        "body": {"shoulder": 0.018, "hips": 0.07, "waist": 0.13,
                 "limbs": {"UpperArm": 0.12, "LowerArm": 0.09, "UpperLeg": 0.07, "LowerLeg": 0.06}},
        # 顔: 丸み (ほお・あごを横に)
        "face": {"round": 0.06},
        # ふだんの顔: おだやかな笑顔
        "expr": {"Fcl_MTH_Fun": 0.55, "Fcl_EYE_Joy": 0.22, "Fcl_BRW_Fun": 0.45},
        "outfit": {"color": "#161514", "top": (1.115, 1.235), "shorts": (0.805, 0.975)},
    },
    "ruo": {
        "name": "ruo",
        "label": "ルオ (男・1日目 39歳・52.2kg)",
        "body_src": HS_M,
        "face_src": HS_M,   # 切れ長で細い目の顔
        # いちばん濃い日焼け。狩人なので腕に小さな古傷を 1 つ
        "skin": {"tan": "#7a4a32", "sss": 0.12, "rough": 0.55, "fill_dark": 0.6,
                 "blush": "#a8503e", "blush_alpha": 0.06,
                 "scars": [{"bone": "J_Bip_R_LowerArm", "s": (0.45, 0.6), "slant": (0, -0.015, 0),
                            "off": (0, 0, 0.06), "color": "#b07c66", "alpha": 0.55, "width": 2.0}]},
        # 髪: 素体の短い髪を頭へ寄せて短く刈る。こげ茶
        "hair": {"parts": [{"src": HS_M, "part": "Hair001"}, {"src": FUMI, "part": "HairBack"}],
                 "style": "keep",
                 "crop": {"k": 0.45, "z_front": 0.10, "z_back": 0.0, "k_len": 0.35, "gap": 0.003},
                 "dark": "#120b07", "light": "#4e3220", "ramp_lo": 0.3, "rough": 0.55},
        "lines": {"brow": "#1c120d", "eyeline": "#24120e", "lash": "#1e100c"},
        "iris": {"hue": 0.0, "sat": 0.15, "val": 0.85, "tint": "#7a5a42", "highlight": 0.55},
        # 引きしまった狩人の体: 肩と腕に筋肉、腰は細い
        "body": {"shoulder": 0.02, "hips": -0.04, "waist": -0.08, "chest": 0.08,
                 "limbs": {"UpperArm": 0.13, "LowerArm": 0.10, "UpperLeg": 0.03, "LowerLeg": 0.04}},
        "scale": 0.97,
        # 頬のこけた年長の顔、太くまっすぐな眉
        "face": {"round": -0.06, "brow_thick": 1.45},
        # 目を細めた鋭いまなざし
        "expr": {"Fcl_EYE_Close": 0.22, "Fcl_BRW_Angry": 0.35, "Fcl_MTH_Close": 0.3},
        "outfit": SHORTS,
    },
    "tahi": {
        "name": "tahi",
        "label": "タヒ (男・1日目 18歳・54.4kg)",
        "body_src": HS_M,
        "face_src": FUMI,   # 若い顔 (桜田 フミリヤ)
        # 日焼け。ザガに 4 回けが: 左の前腕・右の上腕・左の太もも・右のすねに古い傷
        "skin": {"tan": "#a06a4a", "sss": 0.15, "rough": 0.5, "fill_dark": 0.6,
                 "blush": "#b85848", "blush_alpha": 0.12,
                 "scars": [
                     {"bone": "J_Bip_L_LowerArm", "s": (0.3, 0.55), "slant": (0, 0.02, 0),
                      "off": (0, 0, 0.06), "color": "#c99a84", "alpha": 0.75, "width": 2.2},
                     {"bone": "J_Bip_R_UpperArm", "s": (0.4, 0.62), "slant": (0, -0.025, 0),
                      "off": (0, 0, 0.065), "color": "#c99a84", "alpha": 0.7, "width": 2.4},
                     {"bone": "J_Bip_L_UpperLeg", "s": (0.35, 0.6), "slant": (0.03, 0, 0),
                      "off": (0, 0.1, 0), "color": "#c99a84", "alpha": 0.7, "width": 2.6},
                     {"bone": "J_Bip_R_LowerLeg", "s": (0.25, 0.42), "slant": (-0.02, 0, 0),
                      "off": (0, 0.08, 0), "color": "#c99a84", "alpha": 0.65, "width": 2.2}]},
        # 髪: 素体の乱れた短い髪 (はねた毛つき) をそのまま、赤茶に
        "hair": {"parts": [{"src": HS_M, "part": "Hair001"}],
                 "style": "keep",
                 "dark": "#3a1206", "light": "#b8501f", "ramp_lo": 0.25, "rough": 0.5},
        "lines": {"brow": "#3a1a10", "eyeline": "#2c1612", "lash": "#24120f"},
        # 灰色の瞳
        "iris": {"hue": 0.0, "sat": 0.0, "val": 1.0, "tint": "#a9b0b8", "highlight": 0.8},
        # 細身で手足が長い
        "body": {"shoulder": 0.0, "hips": -0.02, "waist": -0.05, "chest": 0.0,
                 "limbs": {"UpperArm": -0.04, "LowerArm": -0.04, "UpperLeg": -0.05, "LowerLeg": -0.03}},
        "scale": 0.96, "legs": 1.05, "arms": 1.04,
        "face": {"round": -0.02},
        # よく笑う顔、上がった眉
        "expr": {"Fcl_MTH_Fun": 0.65, "Fcl_MTH_Joy": 0.12, "Fcl_EYE_Joy": 0.28, "Fcl_BRW_Surprised": 0.55},
        "outfit": SHORTS,
    },
    "wiro": {
        "name": "wiro",
        "label": "ウィロ (女・1日目 21歳・54.3kg)",
        "body_src": HS_F,
        "face_src": HS_F,   # やわらかい目の顔 (HairSample_Female)
        # 日焼けは浅め (家の近くの仕事)。両手に煤
        "skin": {"tan": "#b58466", "sss": 0.15, "rough": 0.5,
                 "blush": "#c86a5a", "blush_alpha": 0.26,
                 "patches": [
                     {"bone": "J_Bip_L_Hand", "s": (0.1, 1.7), "spread": 0.018, "n": 160,
                      "color": "#2e2622", "alpha": 0.5, "radius": 5.0},
                     {"bone": "J_Bip_R_Hand", "s": (0.1, 1.7), "spread": 0.018, "n": 160,
                      "color": "#2e2622", "alpha": 0.5, "radius": 5.0}]},
        # 髪: Victoria Rubin の長めの髪 (リボンと横の小さな房を消す) を赤茶にして、うなじで結んで三つ編みに
        "hair": {"parts": [{"src": VICT, "part": "Hair001", "drop": ["HAIR_03"], "drop_parts": [{"x_lt": -0.11}, {"x_lt": -0.09, "z_gt": 0.085}]},
                           {"src": VICT, "part": "HairBack"}],
                 "style": "braid",
                 "dark": "#260b04", "light": "#622a13", "ramp_lo": 0.6, "rough": 0.5,
                 "tie_z": 1.31, "gather_from": 1.385, "tail_width": 0.024,
                 "front_from": 1.37, "front_keep": 0.9, "tie_color": "#6a4a30",
                 "braid": {"len": 0.34, "width": 0.032, "strand_r": 0.0085, "period": 0.07,
                           "taper": 0.35, "tuft": 0.045}},
        "lines": {"brow": "#3a1a10", "eyeline": "#2c1612", "lash": "#24120f"},
        "iris": {"hue": 0.0, "sat": 0.35, "val": 0.95, "tint": "#8c6c5c", "highlight": 0.8},
        # ふつう。やわらかい体つき
        "body": {"shoulder": 0.0, "hips": 0.04, "waist": 0.05,
                 "limbs": {"UpperArm": 0.05, "LowerArm": 0.03, "UpperLeg": 0.05, "LowerLeg": 0.03}},
        "face": {"round": 0.03},
        # おだやかな垂れ目、ゆるい眉、やわらかい笑み
        "expr": {"Fcl_MTH_Fun": 0.35, "Fcl_EYE_Sorrow": 0.28, "Fcl_EYE_Joy": 0.12, "Fcl_BRW_Sorrow": 0.3},
        "outfit": {"color": "#161514", "top": (1.115, 1.235), "shorts": (0.805, 0.975)},
    },
    "isa": {
        "name": "isa",
        "label": "イサ (男・1日目 20歳・47.2kg)",
        "body_src": HS_M,
        "face_src": FUMI,
        "skin": {"tan": "#9a6648", "sss": 0.15, "rough": 0.5, "fill_dark": 0.6,
                 "blush": "#b05a4a", "blush_alpha": 0.06},
        # 髪: 桜田 フミリヤの短い髪 (後ろの刈り上げも) を、ひとつの栗色に
        "hair": {"parts": [{"src": FUMI, "part": "Hair001"}, {"src": FUMI, "part": "HairBack"}],
                 "style": "keep",
                 "dark": "#28160b", "light": "#5c341d", "ramp_lo": 0.1, "rough": 0.55,
                 "ramp_mat": {"HairBack": (0.0, 0.5), "HAIR_02": (0.0, 0.5)}},
        "lines": {"brow": "#2a1810", "eyeline": "#2c1612", "lash": "#24120f"},
        "iris": {"hue": 0.0, "sat": 0.15, "val": 0.8, "tint": "#6e4c38", "highlight": 0.5},
        # いちばん細い。頬と腕がやせている
        "body": {"shoulder": -0.012, "hips": -0.05, "waist": -0.12, "chest": -0.05,
                 "limbs": {"UpperArm": -0.16, "LowerArm": -0.12, "UpperLeg": -0.1, "LowerLeg": -0.08}},
        "scale": 0.96,
        "face": {"round": -0.08},
        # 伏し目がち、口を結んだ無口な顔
        "expr": {"Fcl_EYE_Close": 0.28, "Fcl_BRW_Sorrow": 0.25, "Fcl_MTH_Close": 0.5},
        "gaze_down": 8.0,
        "outfit": SHORTS,
    },
}

# ---------------------------------------------------------------- 案内役 (年報と統計のページを説明する人)
# ソナ85: 251年30日目 (30149 日目) に生きている村の人から選んだ (docs/society_phase/guide_character.md)。
# 女・74 歳・51.0 kg・生きた日 8910 日。24 歳で南の村19 から来て 50 年。家の代表 200 季節、子らに字を教えた 180 日。
# 布を織る技は村にない (技の木の「布を織る」は届かなかった) ので、服はヤギのなめし革の長い貫頭衣と革紐の帯。
VROID["sona85"] = {
    "name": "sona85",
    "label": "ソナ85 (女・74歳・51.0kg・案内役)",
    "body_src": HS_F,
    "face_src": VICT,   # 顔: Victoria Rubin (五人のだれとも別の顔)
    # 畑と原の仕事で日に焼けた肌。年寄りなので、目じりと口のわきにうすいしわ
    "skin": {"tan": "#94664a", "sss": 0.15, "rough": 0.55,
             "blush": "#b86656", "blush_alpha": 0.12,
             "face_lines": [
                 # ほうれい線 (小鼻のわきから口のわきへ)
                 {"a": (0.015, 0.019), "b": (0.023, -0.001), "bow": 0.0, "color": "#6e4632", "alpha": 0.5, "width": 2.0},
                 # 目じりのしわ (2 本ずつ)
                 {"a": (0.049, 0.040), "b": (0.058, 0.043), "color": "#6e4632", "alpha": 0.32, "width": 1.2, "n": 16},
                 {"a": (0.049, 0.036), "b": (0.058, 0.034), "color": "#6e4632", "alpha": 0.28, "width": 1.2, "n": 16},
             ]},
    # 髪: Victoria Rubin の長めの髪 (リボンと横の小さな房を消す) を白髪まじりの灰色にして、うなじで低く結ぶ
    "hair": {"parts": [{"src": VICT, "part": "Hair001", "drop": ["HAIR_03"], "drop_parts": [{"x_lt": -0.11}, {"x_lt": -0.09, "z_gt": 0.085}]},
                       {"src": VICT, "part": "HairBack"}],
             "style": "tie",
             "dark": "#3a3633", "light": "#9c968e", "ramp_lo": 0.5, "rough": 0.55,
             "tie_z": 1.30, "gather_from": 1.385, "tail_width": 0.022,
             "front_from": 1.37, "front_keep": 0.6, "tie_color": "#4a3322"},
    "lines": {"brow": "#4a423c", "eyeline": "#2c1612", "lash": "#3a2a22"},
    "iris": {"hue": 0.0, "sat": 0.5, "val": 0.85, "tint": "#7a5a44", "highlight": 0.6},
    # 年をとって少しやせた体 (51 kg)。畑で働く腕はまだしっかり
    "body": {"shoulder": -0.004, "hips": 0.02, "waist": 0.05, "chest": -0.03,
             "limbs": {"UpperArm": -0.02, "LowerArm": 0.0, "UpperLeg": -0.04, "LowerLeg": -0.03}},
    "scale": 0.96,
    "face": {"round": -0.01},
    # ふだんの顔: おだやかに細めた目と、小さな笑み
    "expr": {"Fcl_MTH_Fun": 0.3, "Fcl_EYE_Joy": 0.12, "Fcl_BRW_Sorrow": 0.08},
    "outfit": {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
               "dress": {"color": "#7a5638", "belt": "#3e2a1c", "waist": 1.00, "arm": 1.215,
                         "neck": 1.335, "hem": 0.36, "flare": 0.22, "push": 0.008, "sleeve_x": 0.26}},
    # 吹き出しの絵 (--only guide): 表情ごとの VRM の表情キー
    "guide": {"bg": "#e6e1d8", "lens": 85, "dist": 1.05, "dz": 0.005, "arm_down": 68,
              "expr": {"neutral": {"Fcl_MTH_Fun": 0.25, "Fcl_EYE_Joy": 0.08},
                       "smile": {"Fcl_MTH_Fun": 0.7, "Fcl_MTH_Joy": 0.15, "Fcl_EYE_Joy": 0.55, "Fcl_BRW_Fun": 0.5},
                       "concern": {"Fcl_BRW_Sorrow": 1.0, "Fcl_EYE_Sorrow": 0.6, "Fcl_MTH_Sorrow": 0.55},
                       "surprise": {"Fcl_BRW_Surprised": 1.0, "Fcl_EYE_Surprised": 0.85, "Fcl_MTH_O": 0.55}}},
}

# ---------------------------------------------------------------- G1 からの村の人 (動画 G1F2V・G1F3V。2026-11-25 本人「あと 3 本」)
# よそから来た二人 (629 日目、ナギの家)。記録: ナギ (女・来た日 32 歳)・ソル (男・来た日 22 歳)。五人とちがう顔・髪の組み合わせにする
# (同じ動画に出る セナ・タヒ・ウィロ とは、顔のもと・髪の色・結い方で分ける)
VROID["nagi"] = {
    "name": "nagi",
    "label": "ナギ (女・629日目に来た日 32歳)",
    "body_src": HS_F,
    "face_src": VICT,   # 顔: Victoria Rubin (セナ=篠・ウィロ=HairSample_Female とちがう顔)
    "skin": {"tan": "#a8765a", "sss": 0.15, "rough": 0.5, "blush": "#c0605a", "blush_alpha": 0.2},
    # 髪: Victoria Rubin の髪をこげ茶にして、うなじで低く結ぶ
    "hair": {"parts": [{"src": VICT, "part": "Hair001", "drop": ["HAIR_03"], "drop_parts": [{"x_lt": -0.11}, {"x_lt": -0.09, "z_gt": 0.085}]},
                       {"src": VICT, "part": "HairBack"}],
             "style": "tie",
             "dark": "#1a0f0a", "light": "#4a2e1e", "ramp_lo": 0.4, "rough": 0.5,
             "tie_z": 1.30, "gather_from": 1.385, "tail_width": 0.026,
             "front_from": 1.37, "front_keep": 0.6, "tie_color": "#5a3b26"},
    "lines": {"brow": "#2a1810", "eyeline": "#2c1612", "lash": "#24120f"},
    "iris": {"hue": 0.0, "sat": 0.6, "val": 0.9, "tint": "#7a5640", "highlight": 0.75},
    "body": {"shoulder": 0.006, "hips": 0.03, "waist": 0.06,
             "limbs": {"UpperArm": 0.05, "LowerArm": 0.04, "UpperLeg": 0.04, "LowerLeg": 0.03}},
    "scale": 0.98,
    "face": {"round": 0.0},
    # 落ちついた顔 (来たばかりで少し用心深い)
    "expr": {"Fcl_MTH_Fun": 0.25, "Fcl_EYE_Joy": 0.06, "Fcl_BRW_Sorrow": 0.12},
    "outfit": {"color": "#161514", "top": (1.115, 1.235), "shorts": (0.805, 0.975)},
}
VROID["sol"] = {
    "name": "sol",
    "label": "ソル (男・629日目に来た日 22歳)",
    "body_src": HS_M,
    "face_src": HS_M,   # 切れ長の目の顔 (ルオと同じ顔のもと。ルオは 84 日目に亡くなり、同じ動画には出ない)
    "skin": {"tan": "#93603f", "sss": 0.14, "rough": 0.52, "fill_dark": 0.6,
             "blush": "#a8503e", "blush_alpha": 0.08},
    # 髪: 桜田 フミリヤの短い髪を黒に
    "hair": {"parts": [{"src": FUMI, "part": "Hair001"}, {"src": FUMI, "part": "HairBack"}],
             "style": "keep",
             "dark": "#070505", "light": "#241a14", "ramp_lo": 0.2, "rough": 0.5},
    "lines": {"brow": "#1c120d", "eyeline": "#24120e", "lash": "#1e100c"},
    "iris": {"hue": 0.0, "sat": 0.2, "val": 0.85, "tint": "#6a4a36", "highlight": 0.6},
    # 若い働き手: 肩と腕に少し筋肉
    "body": {"shoulder": 0.01, "hips": -0.02, "waist": -0.04, "chest": 0.04,
             "limbs": {"UpperArm": 0.06, "LowerArm": 0.05, "UpperLeg": 0.02, "LowerLeg": 0.02}},
    "scale": 0.99,
    "face": {"round": -0.02, "brow_thick": 1.2},
    # 明るく人なつこい顔
    "expr": {"Fcl_MTH_Fun": 0.45, "Fcl_EYE_Joy": 0.15, "Fcl_BRW_Fun": 0.3},
    "outfit": SHORTS,
}

# 七人に服を着せる (前の下着と短パンの姿は、D1V などで撮った動画のまま)
for _k, (_n, _sx) in enumerate([("ruo", "男"), ("sena", "女"), ("tahi", "男"), ("wiro", "女"), ("isa", "男"), ("nagi", "女"), ("sol", "男")]):
    VROID[_n]["outfit"] = tunic(_sx, _k)

# 並べる順 (本人の絵と同じ、左から)
LINEUP = ["ruo", "sena", "tahi", "wiro", "isa"]

# ---------------------------------------------------------------- 解説の係 (年報の動画で、分野ごとに話す村の人)
# 251年59日目 (30179 日目) に生きている村の人から、記録で選んだ (docs/society_phase/guide_character.md の「解説の係」)。
# 服はソナ85 と同じヤギのなめし革の貫頭衣 (色と丈を人ごとに変える)。吹き出し・動画の顔は --only guide。
GUIDE_EXPR = {"neutral": {"Fcl_MTH_Fun": 0.25, "Fcl_EYE_Joy": 0.08},
              "smile": {"Fcl_MTH_Fun": 0.7, "Fcl_MTH_Joy": 0.15, "Fcl_EYE_Joy": 0.55, "Fcl_BRW_Fun": 0.5},
              "concern": {"Fcl_BRW_Sorrow": 1.0, "Fcl_EYE_Sorrow": 0.6, "Fcl_MTH_Sorrow": 0.55},
              "surprise": {"Fcl_BRW_Surprised": 1.0, "Fcl_EYE_Surprised": 0.85, "Fcl_MTH_O": 0.55}}


def _guide(**kw):
    g = {"bg": "#e6e1d8", "lens": 85, "dist": 1.05, "dz": 0.005, "arm_down": 68, "expr": GUIDE_EXPR}
    g.update(kw)
    return g


# 人口の係 キオ85: 女・50 歳。村で生まれた。子 10 人 (いま 5 人が生きている。4 人を小さいうちに亡くした)。家の代表 58 季節
VROID["kio85"] = {
    "name": "kio85",
    "label": "キオ85 (女・50歳・人口の係)",
    "body_src": HS_F,
    "face_src": HS_F,   # やわらかい目の顔 (子の多い母)
    "skin": {"tan": "#9c6a4c", "sss": 0.15, "rough": 0.52, "blush": "#bf5e4e", "blush_alpha": 0.2},
    # 髪: 篠の髪 (髪どめを消す) をこげ茶に、少し白いものがまじる。うなじで結ぶ
    "hair": {"parts": [{"src": SHINO, "part": "Hair001", "drop": ["HAIR_02"]}, {"src": SHINO, "part": "HairBack"}],
             "style": "tie",
             "dark": "#140d09", "light": "#4a3628", "ramp_lo": 0.4, "rough": 0.55,
             "tie_z": 1.30, "gather_from": 1.385, "tail_width": 0.026,
             "front_from": 1.37, "front_keep": 0.6, "tie_color": "#5a3b26"},
    "lines": {"brow": "#2e1e16", "eyeline": "#2c1612", "lash": "#24120f"},
    "iris": {"hue": 0.0, "sat": 0.5, "val": 0.9, "tint": "#7e5a42", "highlight": 0.7},
    "body": {"shoulder": 0.008, "hips": 0.06, "waist": 0.1,
             "limbs": {"UpperArm": 0.07, "LowerArm": 0.05, "UpperLeg": 0.05, "LowerLeg": 0.04}},
    "face": {"round": 0.05},
    "expr": {"Fcl_MTH_Fun": 0.45, "Fcl_EYE_Joy": 0.18, "Fcl_BRW_Fun": 0.3},
    "outfit": {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
               "dress": {"color": "#8a6242", "belt": "#4a3020", "waist": 1.00, "arm": 1.215,
                         "neck": 1.335, "hem": 0.40, "flare": 0.2, "push": 0.008, "sleeve_x": 0.26}},
    "guide": _guide(),
}

# くらし・食べ物の係 ネイ75: 男・61 歳。村で生まれた。草の種をまいた量が村で 3 番め (39,300 つかみ)、水の道を掘った 1,020 日
VROID["nei75"] = {
    "name": "nei75",
    "label": "ネイ75 (男・61歳・くらし・食べ物の係)",
    "body_src": HS_M,
    "face_src": HS_M,
    # 畑と水の道の仕事で、いちばん濃い日焼け
    "skin": {"tan": "#7e4e34", "sss": 0.12, "rough": 0.58, "fill_dark": 0.6, "blush": "#a8503e", "blush_alpha": 0.06},
    # 髪: 短く刈った白髪まじりの灰色
    "hair": {"parts": [{"src": HS_M, "part": "Hair001"}, {"src": FUMI, "part": "HairBack"}],
             "style": "keep",
             "crop": {"k": 0.5, "z_front": 0.10, "z_back": 0.0, "k_len": 0.4, "gap": 0.003},
             "dark": "#2a2622", "light": "#a49c92", "ramp_lo": 0.4, "rough": 0.6},
    "lines": {"brow": "#4a423c", "eyeline": "#24120e", "lash": "#2a1c16"},
    "iris": {"hue": 0.0, "sat": 0.2, "val": 0.85, "tint": "#6e5040", "highlight": 0.5},
    # 畑で働く太い腕と、がっしりした肩
    "body": {"shoulder": 0.016, "hips": 0.0, "waist": 0.02, "chest": 0.05,
             "limbs": {"UpperArm": 0.12, "LowerArm": 0.10, "UpperLeg": 0.04, "LowerLeg": 0.04}},
    "scale": 0.97,
    "face": {"round": -0.03, "brow_thick": 1.25},
    "expr": {"Fcl_MTH_Fun": 0.35, "Fcl_EYE_Joy": 0.15},
    "outfit": {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
               "dress": {"color": "#6e4c32", "belt": "#3a281a", "waist": 1.00, "arm": 1.215,
                         "neck": 1.335, "hem": 0.62, "flare": 0.12, "push": 0.008, "sleeve_x": 0.26}},
    "guide": _guide(),
}

# 知恵・技術の係 ケセ98: 男・39 歳。村で生まれた。字を教えた日が村でいちばん多い (954 日)。知らせを書く 10 日・帳をつける 30 日
VROID["kese98"] = {
    "name": "kese98",
    "label": "ケセ98 (男・39歳・知恵・技術の係)",
    "body_src": HS_M,
    "face_src": FUMI,
    # 屋根の下で字を教える日が多いので、日焼けは浅め
    "skin": {"tan": "#a87252", "sss": 0.15, "rough": 0.5, "fill_dark": 0.6, "blush": "#b05a4a", "blush_alpha": 0.08},
    "hair": {"parts": [{"src": FUMI, "part": "Hair001"}, {"src": FUMI, "part": "HairBack"}],
             "style": "keep",
             "dark": "#120c08", "light": "#3e2a1c", "ramp_lo": 0.1, "rough": 0.55,
             "ramp_mat": {"HairBack": (0.0, 0.5), "HAIR_02": (0.0, 0.5)}},
    "lines": {"brow": "#1e140e", "eyeline": "#2c1612", "lash": "#24120f"},
    "iris": {"hue": 0.0, "sat": 0.3, "val": 0.85, "tint": "#5e4434", "highlight": 0.7},
    "body": {"shoulder": -0.004, "hips": -0.03, "waist": -0.05, "chest": -0.02,
             "limbs": {"UpperArm": -0.05, "LowerArm": -0.04, "UpperLeg": -0.04, "LowerLeg": -0.03}},
    "face": {"round": -0.01},
    "expr": {"Fcl_MTH_Fun": 0.3, "Fcl_EYE_Joy": 0.1},
    "outfit": {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
               "dress": {"color": "#94704c", "belt": "#4a3020", "waist": 1.00, "arm": 1.215,
                         "neck": 1.335, "hem": 0.58, "flare": 0.12, "push": 0.008, "sleeve_x": 0.26}},
    "guide": _guide(),
}

# よその村・町の係 ナセ110: 女・30 歳。村で生まれた。川下の町の頼みで燃える石を背負って町へ 9 回 (村でいちばん多い)。知らせを書く 32 日
VROID["nase110"] = {
    "name": "nase110",
    "label": "ナセ110 (女・30歳・よその村・町の係)",
    "body_src": HS_F,
    "face_src": SHINO,
    # 川を下る道で日に焼けた肌
    "skin": {"tan": "#93603f", "sss": 0.15, "rough": 0.5, "blush": "#c0584a", "blush_alpha": 0.24},
    # 髪: Victoria Rubin の長めの髪を黒にして、うなじで結んで短い三つ編み (歩くときにじゃまにならない)
    "hair": {"parts": [{"src": VICT, "part": "Hair001", "drop": ["HAIR_03"], "drop_parts": [{"x_lt": -0.11}, {"x_lt": -0.09, "z_gt": 0.085}]},
                       {"src": VICT, "part": "HairBack"}],
             "style": "braid",
             "dark": "#060404", "light": "#2a1e18", "ramp_lo": 0.5, "rough": 0.5,
             "tie_z": 1.31, "gather_from": 1.385, "tail_width": 0.024,
             "front_from": 1.37, "front_keep": 0.8, "tie_color": "#6a4a30",
             "braid": {"len": 0.26, "width": 0.03, "strand_r": 0.008, "period": 0.07, "taper": 0.35, "tuft": 0.04}},
    "lines": LINES_DARK,
    "iris": {"hue": 0.0, "sat": 0.7, "val": 0.95, "tint": "#8a5e44", "highlight": 0.8},
    # 背負って歩く人の、引きしまった脚と肩
    "body": {"shoulder": 0.01, "hips": 0.02, "waist": 0.0,
             "limbs": {"UpperArm": 0.06, "LowerArm": 0.04, "UpperLeg": 0.07, "LowerLeg": 0.06}},
    "face": {"round": 0.0},
    "expr": {"Fcl_MTH_Fun": 0.5, "Fcl_EYE_Joy": 0.2, "Fcl_BRW_Fun": 0.3},
    "outfit": {"color": "#161514", "top": None, "shorts": (0.805, 0.975),
               "dress": {"color": "#7e5a3e", "belt": "#3e2a1c", "waist": 1.00, "arm": 1.215,
                         "neck": 1.335, "hem": 0.50, "flare": 0.16, "push": 0.008, "sleeve_x": 0.26}},
    "guide": _guide(),
}

# 年報の動画の顔ぶれ (案内役 + 4 つの分野の係)。video/yearly/voices.json と同じ順
CAST = ["sona85", "kio85", "nei75", "kese98", "nase110"]
