"""記録から村の人の姿を自動で決める (2026-11-25 本人「新しい人の作り方はおすすめで進めて下さい」)。docs/society_phase/people_making_design.md 4.

    python3 auto_people.py --names ミラ,ケト,ハユ --day 1229 --out /dev/shm/sena/auto.json
    python3 auto_people.py --days 510,1229 --out /dev/shm/sena/auto.json      # その日々にいる人のうち、五人とナギ・ソル以外の全員

出力の json: {"configs": {ファイル名: people.py の VROID と同じ形の設定}, "files": {名前: ファイル名}, "babies": [名前...]}
build_person_vroid.py --config <json> --person <ファイル名> で作る。名前は人の名前から決まるくじで、何度作っても同じ姿になる。

決まり (people_making_design.md 4.2〜4.4):
- 体と骨組み: 女は HairSample_Female、男は HairSample_Male。
- 顔・髪の形・髪の色・目の色: 母がいれば母から受けつぐ (少しだけずらす)。いなければ、名前のくじで選ぶ。
- 肌: 外の仕事の腕前 (採集・狩り) が高いほど濃い日焼け。子は少し浅い。
- 体つき: 体重 (性別の平均とのちがい) と狩りの腕前 (肩と腕)。
- 表情: 性格 (社交・大胆・好奇心)。
- 年れい (その日の): 2〜14 歳は小さく (背・脚・腕)、0〜1 歳は人のモデルを作らず、親が抱く包みで見せる (babies)。55 歳からは白髪まじり。
"""
import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import people  # noqa: E402

V = people.VROID
SHINO, HS_F, HS_M, FUMI, VICT = people.SHINO, people.HS_F, people.HS_M, people.FUMI, people.VICT
YEAR = 120
HAND = {"ルオ": "ruo", "セナ": "sena", "タヒ": "tahi", "ウィロ": "wiro", "イサ": "isa", "ナギ": "nagi", "ソル": "sol"}  # 手で決めた人 (people.py)

# 顔のもとと髪の形 (どれも五人・ナギ・ソルで使って、組み立てられると確かめた部品)
FACES = {"女": [SHINO, HS_F, VICT], "男": [HS_M, FUMI]}
HAIRS = {"女": [("sena", "tie"), ("wiro", "braid"), ("nagi", "tie"), ("sona85", "tie")],
         "男": [("tahi", "keep"), ("ruo", "keep"), ("isa", "keep"), ("sol", "keep")]}
HAIR_COLORS = [("#080606", "#1e1815"), ("#120b07", "#4e3220"), ("#1a0f0a", "#4a2e1e"), ("#3a1206", "#b8501f"),
               ("#28160b", "#5c341d"), ("#260b04", "#622a13"), ("#070505", "#241a14"), ("#2a1a10", "#7a5a3a")]
IRIS = ["#9a6a4c", "#7a5a42", "#6e4c38", "#8c6c5c", "#a9b0b8", "#6a4a36", "#7a5640"]


def fnv(s):
    x = 2166136261
    for ch in s:
        x ^= ord(ch)
        x = (x * 16777619) & 0xFFFFFFFF
    return x


def pick(lst, name, salt):
    return lst[(fnv(name + "|" + salt) >> 9) % len(lst)]  # 下の位は名前の字で偏るので、上の位を使う


def hx(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, u):
    A, B = hx(a), hx(b)
    return "#" + "".join(f"{round(A[i] + (B[i] - A[i]) * u):02x}" for i in range(3))


def jitter(c, name, k=10):
    d = ((fnv(name + "|j") >> 9) % (2 * k + 1)) - k
    return "#" + "".join(f"{max(0, min(255, v + d)):02x}" for v in hx(c))


def fname(rec):
    return "p" + rec["id"][1:].lower()  # P123 → p123


def genes(name, R, A, memo):
    """受けつぐもの: 顔のもと・髪の形・髪の色・目の色・肌のもと。母がいれば母から、いなければ名前のくじ"""
    if name in memo:
        return memo[name]
    r, a = R.get(name, {}), A.get(name, {})
    sex = r.get("sex") or a.get("sex") or "女"
    mom = a.get("mother")
    if name in HAND:  # 手で決めた人は、その設定から
        P = V[HAND[name]]
        g = {"face": P["face_src"], "hair": (HAND[name], P["hair"].get("style", "keep")), "hc": (P["hair"]["dark"], P["hair"]["light"]),
             "iris": P["iris"]["tint"], "tan": P["skin"]["tan"]}
    elif mom and mom in A:
        m = genes(mom, R, A, memo)
        face = m["face"] if m["face"] in FACES[sex] else pick(FACES[sex], name, "face")
        hair = pick(HAIRS[sex], name, "hair") if sex != (R.get(mom, {}).get("sex") or "女") else m["hair"]
        g = {"face": face, "hair": hair, "hc": (jitter(m["hc"][0], name, 6), jitter(m["hc"][1], name, 12)), "iris": m["iris"], "tan": m["tan"]}
    else:
        g = {"face": pick(FACES[sex], name, "face"), "hair": pick(HAIRS[sex], name, "hair"), "hc": pick(HAIR_COLORS, name, "hc"),
             "iris": pick(IRIS, name, "iris"), "tan": None}
    memo[name] = g
    return g


def config(name, day, R, A, memo):
    r, a = R[name], A.get(name, {})
    sex = r.get("sex") or "女"
    age = (day - r["born_day"]) / YEAR if r.get("born_day") is not None else 30
    g = genes(name, R, A, memo)
    sk, ps = a.get("skills") or {}, a.get("personality") or {}
    base = V[g["hair"][0]]
    P = {"name": fname(r), "label": f"{name} ({sex}・{day}日目 {int(age)}歳・自動)",
         "body_src": HS_F if sex == "女" else HS_M, "face_src": g["face"]}
    out = min(1.0, (sk.get("採集", 0.5) + sk.get("狩り", 0.2)) / 1.6)
    tan = g["tan"] or mix("#b58466", "#7a4a32", out)
    if age < 15:
        tan = mix(tan, "#c4977a", 0.35)
    P["skin"] = {"tan": tan, "sss": 0.15, "rough": 0.5, "blush": "#c0605a", "blush_alpha": 0.18 if sex == "女" else 0.08}
    if sex == "男":
        P["skin"]["fill_dark"] = 0.6
    H = copy.deepcopy(base["hair"])
    H["style"] = g["hair"][1]
    dark, light = g["hc"]
    if age >= 55:  # 白髪まじり
        u = min(0.85, (age - 55) / 20 + 0.3)
        dark, light = mix(dark, "#5a5652", u), mix(light, "#b8b2aa", u)
    H["dark"], H["light"] = dark, light
    P["hair"] = H
    P["lines"] = copy.deepcopy(base["lines"])
    P["iris"] = {"hue": 0.0, "sat": 0.4, "val": 0.9, "tint": g["iris"], "highlight": 0.7}
    mean = 52.0 if sex == "女" else 56.0
    b = max(-1.0, min(1.0, ((a.get("mass") or mean) - mean) / 8))
    hunt = sk.get("狩り", 0.2)
    P["body"] = {"shoulder": round(0.012 * hunt + 0.004 * b, 4), "hips": round(0.04 * b, 3), "waist": round(0.08 * b, 3), "chest": round(0.05 * hunt * (sex == "男"), 3),
                 "limbs": {"UpperArm": round(0.06 * b + 0.08 * hunt, 3), "LowerArm": round(0.04 * b + 0.06 * hunt, 3), "UpperLeg": round(0.05 * b, 3), "LowerLeg": round(0.04 * b, 3)}}
    if age < 15:  # 子: 背を低く、手足を短めに (頭は大人のままなので、体に対して大きく見える)
        P["scale"] = round(0.5 + 0.034 * max(2, age), 3)
        P["legs"], P["arms"] = round(0.88 + 0.008 * age, 3), round(0.92 + 0.005 * age, 3)
    elif age >= 60:
        P["scale"] = 0.96
    P["face"] = {"round": round(0.05 if age < 15 else 0.04 * b, 3)}
    soc, bold, cur = ps.get("社交", 0.5), ps.get("大胆", 0.5), ps.get("好奇心", 0.5)
    P["expr"] = {"Fcl_MTH_Fun": round(0.15 + 0.55 * soc, 2), "Fcl_EYE_Joy": round(0.25 * soc, 2), "Fcl_BRW_Surprised": round(0.45 * cur * bold, 2)}
    if soc < 0.3:
        P["expr"]["Fcl_MTH_Close"] = 0.35
    if sex == "女" and age >= 12:
        P["outfit"] = {"color": "#161514", "top": [1.115, 1.235], "shorts": [0.805, 0.975]}
    else:
        P["outfit"] = {"color": "#161514", "top": None, "shorts": [0.805, 1.0]}
    return P, age


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parents[1] / "data"))
    ap.add_argument("--names", default="")
    ap.add_argument("--days", default="", help="この日々にいる人 (手で決めた人のほか) を全部")
    ap.add_argument("--day", type=int, default=None, help="年れいを数える日 (なければ --days のはじめ)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    data = Path(a.data)
    R = {r["name"]: r for r in json.load(open(data / "records" / "people.json", encoding="utf-8"))}
    A = {p["name"]: p for p in json.load(open(data / "app_data.json", encoding="utf-8"))["people"]}
    days = [int(x) for x in a.days.split(",") if x]
    day = a.day if a.day is not None else (min(days) if days else 0)
    names = [n for n in a.names.split(",") if n]
    if days:
        for n, p in A.items():
            since, left = p.get("since") or 0, p.get("left")
            died = (R.get(n) or {}).get("died_day")
            if any(since <= d and (p.get("born_day") is None or p["born_day"] <= d) and not (left and left < d) and not (died is not None and died < d) for d in days):  # noqa: E501
                names.append(n)
    out = {"configs": {}, "files": {}, "babies": []}
    memo = {}
    def present(n, d):
        p, r = A.get(n, {}), R.get(n, {})
        return (p.get("since") or 0) <= d and (r.get("born_day") is None or r["born_day"] <= d) and not (p.get("left") and p["left"] < d) \
            and not (r.get("died_day") is not None and r["died_day"] < d)
    for n in dict.fromkeys(names):
        if n in HAND or n not in R:
            continue
        ds = [d for d in days if present(n, d)] or [day]
        b = R[n].get("born_day")
        ref = ds[-1] if b is not None and (ds[-1] - b) / YEAR < 15 else ds[0]  # 年れいは、大人はその人が初めて出る日、子は最後に出る日で数える (2 歳までの日は包みで見せる)
        P, age = config(n, ref, R, A, memo)
        if R[n].get("born_day") is not None and (ds[-1] - R[n]["born_day"]) / YEAR < 2:  # 出る日々のずっと 2 歳まで: 親が抱く包み
            out["babies"].append(n)
            continue
        out["configs"][P["name"]] = P
        out["files"][n] = P["name"]
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out['configs'])} 人 ({', '.join(out['files'])}) / 包み {len(out['babies'])} ({', '.join(out['babies'])}) → {a.out}")


if __name__ == "__main__":
    main()
