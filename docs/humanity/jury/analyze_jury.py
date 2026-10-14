# 陪審団の評定を集め、陪審員どうしの一致（級内相関）と、Claude（作り手）の評定との一致を計算する（D10）
#   python3.13 docs/humanity/jury/analyze_jury.py (本人の PC は py -3。PYTHONUTF8=1)
# 出力: jury/results.json（集計）と、標準出力の要約
import json, pathlib, statistics as st, sys
here = pathlib.Path(__file__).parent

ITEMS = ["sv", "ti", "ts", "au", "fb"]
jobs = json.loads((here / "jobs.json").read_text(encoding="utf-8"))
ids = [j["id"] for j in jobs]
answers = {}
for f in sorted((here / "answers").glob("*.json")):
    a = json.loads(f.read_text(encoding="utf-8"))
    answers[a["juror"]] = a["ratings"]
personas = {x["id"]: x for x in json.loads((here / "personas.json").read_text(encoding="utf-8"))}
swaps = {j for j in answers if personas.get(j, {}).get("swap_of")}  # モデルの違いを見るための入れ替え（正式な平均には入れない）
jurors = sorted(j for j in answers if j not in swaps)
missing = [(j, i) for j in sorted(answers) for i in ids if i not in answers[j] or any(not isinstance(answers[j][i].get(k), int) for k in ITEMS)]
assert not missing, missing

# 作り手（Claude）の評定: 陪審団に置き換える前の値を creator_ratings.json に固定してある
mine = json.loads((here / "creator_ratings.json").read_text(encoding="utf-8"))["ratings"]
assert set(ids) <= set(mine), set(ids) - set(mine)


def icc2(mat):
    """ICC(2,1) と ICC(2,k)（Shrout & Fleiss 1979、二元配置変量・絶対一致）。mat[対象][評定者]"""
    n, k = len(mat), len(mat[0])
    gm = st.mean(x for r in mat for x in r)
    rm = [st.mean(r) for r in mat]
    cm = [st.mean(mat[i][j] for i in range(n)) for j in range(k)]
    ssr = k * sum((m - gm) ** 2 for m in rm)
    ssc = n * sum((m - gm) ** 2 for m in cm)
    sst = sum((x - gm) ** 2 for r in mat for x in r)
    sse = sst - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    single = (msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n)
    avg = (msr - mse) / (msr + (msc - mse) / n)
    return round(single, 2), round(avg, 2)


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** .5
    sy = sum((b - my) ** 2 for b in y) ** .5
    return round(sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy), 2) if sx and sy else None


def ranks(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
            j += 1
        for t in range(i, j + 1):
            r[s[t]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def comps(r, body):
    m = ((r["sv"] + r["ti"] + r["ts"]) / 3 - 1) / 6
    f = (r["fb"] - 1) / 6
    return m, f, (m + f + body) / 3


out = {"jurors": jurors, "jobs": len(ids), "items": {}, "composites": {}}
jmean = {i: {k: st.mean(answers[j][i][k] for j in jurors) for k in ITEMS} for i in ids}
for k in ITEMS:
    mat = [[answers[j][i][k] for j in jurors] for i in ids]
    s1, sk = icc2(mat)
    jm = [jmean[i][k] for i in ids]
    me = [mine[i][k] for i in ids]
    out["items"][k] = {"icc_single": s1, "icc_avg": sk, "r_with_creator": pearson(jm, me),
                       "rho_with_creator": spearman(jm, me), "mean_abs_diff": round(st.mean(abs(a - b) for a, b in zip(jm, me)), 2),
                       "jury_mean": round(st.mean(jm), 2), "creator_mean": round(st.mean(me), 2)}
names = {"meaning": 0, "feedback": 1, "grounding": 2}
for nm, ix in names.items():
    jv = [comps(jmean[i], mine[i]["body"])[ix] for i in ids]
    mv = [comps(mine[i], mine[i]["body"])[ix] for i in ids]
    out["composites"][nm] = {"r": pearson(jv, mv), "rho": spearman(jv, mv), "mean_abs_diff": round(st.mean(abs(a - b) for a, b in zip(jv, mv)), 3)}
# 1 件ごとの接地度（陪審団の平均と作り手）
out["per_job"] = {i: {"jury": round(comps(jmean[i], mine[i]["body"])[2], 3), "creator": round(comps(mine[i], mine[i]["body"])[2], 3),
                      "jury_sd_ti": round(st.pstdev([answers[j][i]["ti"] for j in jurors]), 2),
                      "jury_ratings": {k: round(jmean[i][k], 2) for k in ITEMS}} for i in ids}
# ブラウナーの4つ（印刷・化学・繊維・組立）の順位
bl = ["N06", "N08a", "N07b", "N07"]
out["blauner_order_jury"] = sorted(bl, key=lambda i: -out["per_job"][i]["jury"])
# 人物・モデル・時代の違い
def sd_mean(js):
    return round(st.mean(st.pstdev([answers[j][i][k] for j in js]) for i in ids for k in ITEMS), 2)
def mad(a, b):
    return round(st.mean(abs(answers[a][i][k] - answers[b][i][k]) for i in ids for k in ITEMS), 2)
by_model = {}
for j in jurors:
    by_model.setdefault(personas[j]["model"], []).append(j)
out["spread"] = {"all": sd_mean(jurors)} | {m: sd_mean(js) for m, js in by_model.items() if len(js) > 1}
out["icc_by_model"] = {m: {k: icc2([[answers[j][i][k] for j in js] for i in ids])[0] for k in ITEMS} for m, js in by_model.items() if len(js) > 2}
haiku = by_model.get("haiku", [])
out["model_swap"] = {sw: {"same_persona_other_model": mad(sw, personas[sw]["swap_of"]),
                          "rho_grounding": spearman([comps(answers[sw][i], mine[i]["body"])[2] for i in ids],
                                                    [comps(answers[personas[sw]["swap_of"]][i], mine[i]["body"])[2] for i in ids])}
                     for sw in sorted(swaps)}
out["between_personas_same_model"] = round(st.mean(mad(a, b) for x, a in enumerate(haiku) for b in haiku[x + 1:]), 2) if len(haiku) > 1 else None
out["model_mean_rating"] = {m: round(st.mean(answers[j][i][k] for j in js for i in ids for k in ITEMS), 2) for m, js in by_model.items()}
groups = {}
for j in jurors:
    groups.setdefault(personas[j]["group"], []).append(j)
focus = ["N01", "V:採集", "N03", "N05", "N07", "N09", "N09a"]
out["by_group"] = {g: {i: round(st.mean(comps(answers[j][i], mine[i]["body"])[2] for j in js), 3) for i in focus} for g, js in groups.items()}
(here / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

print("陪審員", jurors, "入れ替え", sorted(swaps), "仕事", len(ids))
for k, v in out["items"].items():
    print(k, v)
for k, v in out["composites"].items():
    print(k, v)
print("ブラウナー（陪審団）", out["blauner_order_jury"], [out["per_job"][i]["jury"] for i in out["blauner_order_jury"]])
big = sorted(ids, key=lambda i: -abs(out["per_job"][i]["jury"] - out["per_job"][i]["creator"]))[:6]
for i in big:
    print("差が大きい", i, out["per_job"][i])
print("ばらつき", out["spread"])
print("モデルごとのICC(1人)", out["icc_by_model"])
print("モデルの入れ替え", out["model_swap"], "同じモデルで人物どうし", out["between_personas_same_model"])
print("モデルごとの平均評定", out["model_mean_rating"])
for g, v in out["by_group"].items():
    print("時代", g, v)
