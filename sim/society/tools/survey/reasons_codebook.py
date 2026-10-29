"""論文 2・実験 2 の「わけ」(1,150 件) を、修士論文 (2017) の考え方の分類で分ける (探索。事前登録の仮説ではない)。

    python3 reasons_codebook.py            # out_exp2/reasons.csv → out_exp2/reasons_coded.csv・reasons_summary.md・fig_reasons.png
    python3 reasons_codebook.py --sample 60  # 確かめ用に、くじで 60 件を出す (--seed。1 回目 20261031・2 回目 20261101)

LLM は使わない。下の正規表現 (日本語) だけで、決まったとおりに分ける。何度動かしても同じ結果になる。
1 つのわけに、いくつの分類がついてもよい (多重のラベル)。どれにも当たらなければ「その他・分けられない」(UNC)。

分類 (修士論文の「グレーゾーンで決まりからはみ出す 7 つの考え方」+ 決まりに従う側のわけ 4 つ):
  はみ出す側 (BEND):
    JUST  正当な理由があれば自由に扱ってよい
    RESP  自分の行動に責任を持つ
    HARM  被害が許容できるものであれば行為する
    NOMAL 悪意がない行為は許される
    MAJ   多数派を支持する
    CLEAR 条件が明らかなものは考慮して損害の無いように行為する
    UNCL  条件が不明なものは自分にとって都合よく解釈する
  決まりに従う側 (RULE):
    LAW   違法・規則 (違法・著作権・無断・授業や研修で習った・捕まる話を聞いた)
    CRTR  作り手への対価・敬意
    REL   関係・礼儀 (一言ことわる・許可・借りた物は返す)
    PRIV  個人情報への配慮
  UNC   その他・分けられない

決め方 (Claude が答えを読んで決めた。答えを読んだあとで決めたので、探索):
- 「捕まった人を聞いたことがない」は、修士論文では「はみ出しやすい時」(様子) で、7 つの考え方ではない。
  ここでは「取り締まられるかどうか (条件) がわからないことを、自分に都合よく読む」として UNCL に入れた。
  「捕まる話も聞く」は LAW。
- 「友人なら後で話せば分かり合える / 済む」は、相手との関係 (条件) がわかっているので、損のないようにできる、として CLEAR。
  D1〜D3 の暮らしの文に「何かあっても、あとで話せば分かり合える間柄だ」という文がある人が多く、その写しが多い (結果に書く)。
- MAJ は向きを問わない (「みんなお金を払うので無料は気になる」も MAJ)。
- 「少し気になる」「微妙」だけのわけは、どちらの側とも言えないので UNC。
"""
import argparse
import csv
import json
import os
import random
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out_exp2")

BEND = ["JUST", "RESP", "HARM", "NOMAL", "MAJ", "CLEAR", "UNCL"]
RULE = ["LAW", "CRTR", "REL", "PRIV"]
CODES = BEND + RULE + ["UNC"]
LABEL_JA = {
    "JUST": "正当な理由があれば自由に扱ってよい", "RESP": "自分の行動に責任を持つ",
    "HARM": "被害が許容できるものであれば行為する", "NOMAL": "悪意がない行為は許される", "MAJ": "多数派を支持する",
    "CLEAR": "条件が明らかなものは考慮して損害の無いように行為する", "UNCL": "条件が不明なものは自分にとって都合よく解釈する",
    "LAW": "違法・規則", "CRTR": "作り手への対価・敬意", "REL": "関係・礼儀", "PRIV": "個人情報への配慮", "UNC": "その他・分けられない"}
LABEL_EN = {
    "JUST": "Free use if justified", "RESP": "Take responsibility oneself", "HARM": "Act if harm is tolerable",
    "NOMAL": "No malice, so forgivable", "MAJ": "Follow the majority", "CLEAR": "Known conditions: act so no one loses",
    "UNCL": "Unclear conditions: read in own favour", "LAW": "Illegal / rules", "CRTR": "Pay / respect creators",
    "REL": "Relationship / courtesy", "PRIV": "Personal information", "UNC": "Other / uncodable"}

# ---------- 型 (正規表現)。1 つでも当たれば、その分類をつける ----------
PATTERNS = {
    "JUST": [
        r"お金(も|が)?(ない|足りない)", r"余裕がない", r"仕方(ない|がない|ない面)", r"気持ちは分か",
        r"応援の気持ち", r"私的", r"個人(で|的に)?(見る|視聴)", r"自分用", r"人が上げた", r"公開側の問題",
        r"公開済み", r"手軽だから", r"延長", r"(に|と)近(く|い感覚)",
    ],
    "RESP": [
        r"自分の(品|分|こと)", r"自分次第", r"自己責任", r"自宅で処分", r"家庭内", r"自分(では|は)気にしない",
        r"返すつもり", r"返す気", r"いずれ返", r"(気づ|気付)いたら返", r"次(に)?会う時",
    ],
    "HARM": [
        r"大ごと(では|で)?(ない|は)", r"大事(では|で)(ない|も)", r"大きな(害|問題)(は|では|で)?(ない|はない)", r"害は小さい",
        r"影響は小さい", r"実害", r"大した(こと|問題)?(は|では|じゃ|で)?(ない|じゃない)", r"あまり問題(ない|ではない|でない)", r"抵抗は小さい", r"大したことない",
        r"重大(ではない|でない|とまでは)", r"深刻(ではない|では|とは思わない|ではなく)", r"軽(い|め|く)", r"大げさ(では|で)?(ない|もない)",
        r"そこまで(重く|悪く|悪い|大事|問題|では|でも|深刻|気に)", r"見るだけ", r"保存だけ", r"保存くらい", r"(服|借りただけ)(くらい|程度|で強く)",
        r"大差ない", r"大きくない", r"強い(問題|罪悪感)", r"大きな問題でない", r"重大でない", r"甘め", r"まあいい", r"問題にならない", r"そう悪くない",
    ],
    "NOMAL": [r"悪意", r"悪気", r"うっかり", r"忘れ", r"わざと", r"つい"],
    "MAJ": [
        r"みんな", r"皆", r"周り", r"まわり", r"よくある", r"よくやる", r"よく見る", r"ありがち", r"よくあり", r"よくやって",
        r"身近(?!に不利益)(?!で捕ま)", r"日常的", r"(普通|ふつう)のこと", r"(普通|ふつう)に(ある|やる|捨て|あること)",
        r"気にする人は少ない", r"気にしない人も多い", r"家の人がやって", r"貸し借りは(普通|日常)", r"よく使う", r"普段(使う|見て|のこと)",
        r"見慣れ", r"買う人が多い", r"よくあること",
    ],
    "CLEAR": [
        r"(話せば|謝れば|言えば|返せば|返す|言われたら|話せる)[^。]*?(済|分か|大丈夫|平気|いい|良い|よい|許(?!可))",
        r"分かり合え", r"大目に見", r"許してくれ", r"許され", r"分かってくれ", r"分かってもらえ",
        r"(友人|友達|仲良し|仲が良|仲がい|仲いい|親しい|親しけ|気心)[^。]*?(気にしない|怒らない|大丈夫|平気|許(?!可)|軽)",
        r"気をつければ", r"剥が", r"はが", r"消せば", r"塗りつぶ", r"後で話せ", r"あとで話せ",
    ],
    "UNCL": [
        # 取り締まりがわからない → 都合よく
        r"捕まらない", r"捕ま(る|った)(話|人)(も|は)聞か", r"注意された話も聞かない", r"捕まる話は聞かない",
        r"捕まった話も聞かない",
        # 不確かさ + ゆるめる言葉 (同じわけの中に両方)
        r"(かも|っぽ|よく分から|グレー|怪し|疑い|そう)[^。]*?(まあ|仕方|気にしない|強くは|そこまで|軽|大丈夫|大差ない|問題ない|甘め|身近|迷う)",
        r"(まあ|気にしない|大丈夫)[^。]*?(かも|かもしれ)",
    ],
    "LAW": [
        r"違法", r"著作権", r"権利侵害", r"侵害", r"無断", r"勝手", r"公式でな", r"正規でな", r"授業", r"研修", r"習っ", r"習う",
        r"学ん", r"教わ", r"学校", r"決まり", r"ルール", r"禁止", r"不可", r"捕まる話も聞く", r"捕まる話も聞いた",
        r"注意された話も聞く", r"捕まった話もあり", r"捕まる話を聞", r"職場(で|でも)?(も)?厳し", r"情報管理", r"権利上",
        r"捕まる話も聞くが", r"無断転載",
    ],
    "CRTR": [
        r"作り手", r"作者", r"作った人", r"作家", r"歌手", r"音楽家", r"創作者", r"権利者", r"本人の利益", r"対価",
        r"お金が入ら", r"お金が 入ら", r"収入", r"稼", r"還元", r"払われ", r"利益(が|に)", r"応援", r"買うべき", r"払うべき",
        r"払うのが", r"買うもの", r"売り物", r"買わず", r"買う方針", r"お金を払", r"タダ", r"ずるい", r"損", r"買う人",
        r"売れず", r"不利", r"作品", r"買う音楽",
    ],
    "REL": [
        r"一言", r"ことわ", r"断る", r"断れ", r"断ら", r"礼儀", r"失礼", r"許可", r"了解", r"信頼", r"気まず", r"嫌がる", r"迷惑",
        r"筋", r"返すべき", r"返すのが", r"返さない", r"返していない", r"返してない", r"返した方", r"返したい", r"早く返",
        r"借りた(物|もの)", r"借りっぱなし", r"借りは借り", r"配慮", r"気持ちも確認", r"聞くべき", r"聞かず", r"言い出しにく",
        r"返さないと", r"早めに返", r"すぐ返", r"返せば",
    ],
    "PRIV": [r"個人情報", r"住所", r"名前", r"伝票", r"情報", r"漏れ", r"知られ", r"見られ", r"不用心", r"顔"],
}
COMPILED = {c: [re.compile(p) for p in ps] for c, ps in PATTERNS.items()}


def code(text):
    """わけ 1 件 → 当たった分類の list (CODES の順)。どれもなければ ["UNC"]。"""
    t = text.replace(" ", "")
    hit = [c for c in CODES[:-1] if any(p.search(t) for p in COMPILED[c])]
    return hit or ["UNC"]


def family(codes):
    b = any(c in BEND for c in codes)
    r = any(c in RULE for c in codes)
    return "mixed" if (b and r) else "bend" if b else "rule" if r else "unc"


FAM_EN = {"rule": "Rule-following only", "mixed": "Mixed (rule + bending)", "bend": "Bending only", "unc": "Uncodable"}
FAM_JA = {"rule": "決まりに従う側だけ", "mixed": "両方", "bend": "はみ出す側だけ", "unc": "分けられない"}
FAMS = ["rule", "mixed", "bend", "unc"]


def load():
    rows = list(csv.DictReader(open(os.path.join(OUT, "reasons.csv"), encoding="utf-8")))
    sit = {s["situation_id"]: s for s in json.load(open(os.path.join(HERE, "situations.json"), encoding="utf-8"))["situations"]}
    for r in rows:
        r["codes"] = code(r["reason"])
        r["family"] = family(r["codes"])
        s = sit[r["situation_id"]]
        r["close"] = int(bool(s.get("close")))
        for k, v in s["surround"].items():
            # 様子は D2 の紙にだけ書いた。D1・D3 では空にする
            r["s_" + k] = v if r["condition"] == "D2" else ""
    return rows


def share(rows, c):
    return sum(c in r["codes"] for r in rows) / len(rows) if rows else float("nan")


def fshare(rows, f):
    return sum(r["family"] == f for r in rows) / len(rows) if rows else float("nan")


def pct(x):
    return f"{100 * x:.0f}%"


def table(groups, title_cols):
    """groups: [(名前, rows)] → 分類ごとの割合 (多重ラベル) と系統の割合の markdown 表。"""
    head = "| 分類 | " + " | ".join(f"{g} (n={len(rs)})" for g, rs in groups) + " |"
    lines = [head, "|---|" + "---|" * len(groups)]
    for c in CODES:
        lines.append(f"| {c} {LABEL_JA[c]} | " + " | ".join(pct(share(rs, c)) for _, rs in groups) + " |")
    lines.append("| **はみ出す側を 1 つ以上** | " + " | ".join(
        pct(sum(any(c in BEND for c in r["codes"]) for r in rs) / len(rs)) for _, rs in groups) + " |")
    for f in FAMS:
        lines.append(f"| 系統: {FAM_JA[f]} | " + " | ".join(pct(fshare(rs, f)) for _, rs in groups) + " |")
    lines.append("| 答えの平均 (1〜5) | " + " | ".join(f"{sum(int(r['answer']) for r in rs) / len(rs):.2f}" for _, rs in groups) + " |")
    return "\n".join(lines)


def boot_diff(a, b, fn, n=2000, seed=20261031):
    """2 組の割合の差 (a − b) の 95% CI (人を引き直す)。"""
    rng = random.Random(seed)
    ida, idb = sorted({r["id"] for r in a}), sorted({r["id"] for r in b})
    by = defaultdict(list)
    for r in a + b:
        by[r["id"]].append(r)
    out = []
    for _ in range(n):
        ra = [x for i in rng.choices(ida, k=len(ida)) for x in by[i]]
        rb = [x for i in rng.choices(idb, k=len(idb)) for x in by[i]]
        out.append(fn(ra) - fn(rb))
    out.sort()
    return fn(a) - fn(b), out[int(0.025 * n)], out[int(0.975 * n) - 1]


def bend_any(rs):
    return sum(any(c in BEND for c in r["codes"]) for r in rs) / len(rs)


def fig(rows, path):
    import analyze as A
    plt = A.setup_mpl()
    cols = {"rule": "#2a78d6", "mixed": "#1baf7a", "bend": "#eb6834", "unc": "#c3c2b7"}
    groups = [("D1\nsituation\n(sonnet)", [r for r in rows if r["condition"] == "D1"]),
              ("D2\nsituation +\nsurroundings\n(sonnet)", [r for r in rows if r["condition"] == "D2"]),
              ("D3\nsituation\n(opus)", [r for r in rows if r["condition"] == "D3"]),
              ("D2,\n'everyone\ndoes it' = 0", [r for r in rows if r["condition"] == "D2" and r["s_everyone"] == 0]),
              ("D2,\n'everyone\ndoes it' = 1", [r for r in rows if r["condition"] == "D2" and r["s_everyone"] == 1])]
    fig_, ax = plt.subplots(figsize=(8.2, 4.6))
    x = [0, 1, 2, 3.4, 4.4]
    for xi, (g, rs) in zip(x, groups):
        bottom = 0
        for f in FAMS:
            v = 100 * fshare(rs, f)
            ax.bar(xi, v, bottom=bottom, width=0.7, color=cols[f], edgecolor="white", linewidth=2,
                   label=FAM_EN[f] if xi == 0 else None)
            if v >= 6:
                ax.text(xi, bottom + v / 2, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                        color="white" if f != "unc" else A.INK)
            bottom += v
        ax.text(xi, 101.5, f"n={len(rs)}", ha="center", va="bottom", fontsize=7, color=A.MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([g for g, _ in groups], fontsize=8)
    ax.set_ylim(0, 108)
    ax.set_ylabel("share of reasons (%)")
    ax.axvline(2.7, color=A.MUTED, lw=0.8, ls=":")
    ax.grid(axis="x", visible=False)
    ax.set_title("One-phrase reasons (items A08, A09, A23, B08, B11), dictionary-coded (exploratory)",
                 fontsize=9.5, color=A.INK, loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=4)
    fig_.tight_layout()
    fig_.savefig(path, dpi=150)
    plt.close(fig_)


def summary(rows):
    by_cond = {c: [r for r in rows if r["condition"] == c] for c in ["D1", "D2", "D3"]}
    unc = sum(r["family"] == "unc" for r in rows)
    L = ["# 実験 2 の「わけ」の分け方 (探索。reasons_codebook.py が書いた)", "",
         "事前登録 (`paper2_exp2_prereg.md`) では、わけを数えるのは空の数だけで、分け方は「あとで別に決める」とした。"
         "ここの分け方は、答えを読んだあとで Claude が決めた正規表現の辞書 (`reasons_codebook.py`) による。**仮説の判定ではなく、探索**。"
         "LLM は使っていない (同じ入力なら、いつも同じ結果)。", "",
         f"- わけ: {len(rows)} 件 (5 問 × 230 人)。1 件にいくつの分類がついてもよい (多重のラベル。割合の合計は 100% をこえる)。",
         f"- **分けられなかったわけ (UNC): {unc} 件 ({pct(unc / len(rows))})**。多くは「少し気になる」「微妙」だけのわけ。",
         "- 系統: はみ出す側 (修士論文の 7 つの考え方) だけ / 決まりに従う側 (違法・作り手・関係・個人情報) だけ / 両方 / 分けられない。",
         "", "## 条件ごと (D1 暮らし sonnet・D2 暮らし + まわりの様子 sonnet・D3 暮らし opus)", "",
         table([(c, by_cond[c]) for c in by_cond], None), ""]
    d, lo, hi = boot_diff(by_cond["D2"], by_cond["D1"], bend_any)
    L.append(f"- はみ出す側を 1 つ以上ふくむわけの割合 D2 − D1 = {100 * d:+.1f} 点 [{100 * lo:+.1f}, {100 * hi:+.1f}] (人を引き直す 95% CI。D1 と D2 は同じ暮らしの対だが、ここでは別々に引き直した)")
    d, lo, hi = boot_diff(by_cond["D2"], by_cond["D1"], lambda rs: share(rs, "MAJ"))
    L.append(f"- 多数派を支持する (MAJ) の割合 D2 − D1 = {100 * d:+.1f} 点 [{100 * lo:+.1f}, {100 * hi:+.1f}]")
    d1s = [r for r in by_cond["D1"] if int(r["situation_id"][1:]) <= 30]
    d, lo, hi = boot_diff(by_cond["D3"], d1s, bend_any)
    L.append(f"- 同じ暮らし S001〜S030 で、はみ出す側の割合 D3 (opus) − D1 (sonnet) = {100 * d:+.1f} 点 [{100 * lo:+.1f}, {100 * hi:+.1f}]")
    L += ["", "## D2: 最近のまわりの様子 (修士論文の「はみ出しやすい時」) ごと", "",
          "D2 の 100 人は、4 つの様子をそれぞれ 50 人ずつ「はみ出しやすい側 (1)」で読んだ (互いにほぼ独立)。", "",
          "| 様子 | 側 | n (わけ) | はみ出す側を 1 つ以上 | MAJ 多数派 | UNCL 条件不明→都合よく | HARM 被害が許容 | LAW 違法・規則 | 答えの平均 |",
          "|---|---|---|---|---|---|---|---|---|"]
    from items import SURROUND
    d2 = by_cond["D2"]
    for k, ja in SURROUND:
        for v in (1, 0):
            rs = [r for r in d2 if r["s_" + k] == v]
            L.append(f"| {ja} | {v} | {len(rs)} | {pct(bend_any(rs))} | {pct(share(rs, 'MAJ'))} | {pct(share(rs, 'UNCL'))} | "
                     f"{pct(share(rs, 'HARM'))} | {pct(share(rs, 'LAW'))} | {sum(int(r['answer']) for r in rs) / len(rs):.2f} |")
    L.append("")
    for k, ja in SURROUND:
        a = [r for r in d2 if r["s_" + k] == 1]
        b = [r for r in d2 if r["s_" + k] == 0]
        d, lo, hi = boot_diff(a, b, bend_any)
        dm, lom, him = boot_diff(a, b, lambda rs: share(rs, "MAJ"))
        L.append(f"- {ja} (1 − 0): はみ出す側 {100 * d:+.1f} 点 [{100 * lo:+.1f}, {100 * hi:+.1f}]、MAJ {100 * dm:+.1f} 点 [{100 * lom:+.1f}, {100 * him:+.1f}]")
    L += ["", "## 問いごと (D1〜D3 をまとめて)", "",
          table([(i, [r for r in rows if r["item"] == i]) for i in ["A08", "A09", "A23", "B08", "B11"]], None), "",
          "## 系統ごとの答えの平均 (わけと数が合っているかの確かめ)", "",
          "| 系統 | n | 答えの平均 |", "|---|---|---|"]
    for f in FAMS:
        rs = [r for r in rows if r["family"] == f]
        L.append(f"| {FAM_JA[f]} | {len(rs)} | {sum(int(r['answer']) for r in rs) / len(rs):.2f} |")
    # 暮らしの文の写し
    copy = [r for r in rows if re.search(r"(後で|あとで)話せば", r["reason"])]
    close_copy = sum(r["close"] for r in copy)
    L += ["", "## 暮らしの文の写し", "",
          f"- 「後で / あとで話せば」をふくむわけ: {len(copy)} 件。そのうち、暮らしの文に「何かあっても、あとで話せば分かり合える間柄だ」がある人: "
          f"{close_copy} 件 ({pct(close_copy / len(copy)) if copy else '-'})。CLEAR の多くは、紙の文の言いかえ (写し) と見られる。"]
    for it in ["A23", "B11"]:
        a = [r for r in rows if r["item"] == it and r["close"] == 1]
        b = [r for r in rows if r["item"] == it and r["close"] == 0]
        L.append(f"- {it} の CLEAR: 近い間柄の文がある人 {pct(share(a, 'CLEAR'))} (n={len(a)}) / ない人 {pct(share(b, 'CLEAR'))} (n={len(b)})")
    L += ["", "## 確かめ (Claude が 60 件を読んだ)", "", "VALIDATION_PLACEHOLDER", "",
          "## 限界", "",
          "- 辞書は、答えを読んでから作った。同じ答えで当てはめて数えているので、当たりは多めに出る (新しい答えに使えば、もっと外れる見込み)。",
          "- 修士論文の 7 つの考え方は、インタビュー (人の長い話) から出た分類。20 字の一言には、考え方の全体は出にくい。",
          "- 1 人が分けた (別の人とのくらべ・κ はない)。60 件の確かめも、辞書を作った Claude 自身が読んだ。",
          "- MAJ は向きを問わない。「みんなお金を払うので」のような、決まりに従う側の多数派も MAJ に入る (数件)。",
          "- わけは 54 問の数を書いたあとに書かせた。わけは、数を決めた理由ではなく、あとからの説明かもしれない。"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args()
    rows = load()
    if a.sample:
        rng = random.Random(a.seed)
        for r in rng.sample(rows, a.sample):
            print(r["id"], r["item"], r["answer"], r["reason"], "→", ",".join(r["codes"]))
        return
    with open(os.path.join(OUT, "reasons_coded.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "condition", "situation_id", "item", "answer", "reason", "codes", "family", "close",
                    "s_everyone", "s_no_arrest", "s_weak", "s_easy"] + CODES)
        for r in rows:
            w.writerow([r["id"], r["condition"], r["situation_id"], r["item"], r["answer"], r["reason"], ";".join(r["codes"]),
                        r["family"], r["close"], r["s_everyone"], r["s_no_arrest"], r["s_weak"], r["s_easy"]]
                       + [int(c in r["codes"]) for c in CODES])
    s = summary(rows)
    vpath = os.path.join(HERE, "reasons_validation.md")
    val = open(vpath, encoding="utf-8").read().strip() if os.path.exists(vpath) else "(まだ)"
    s = s.replace("VALIDATION_PLACEHOLDER", val)
    open(os.path.join(OUT, "reasons_summary.md"), "w", encoding="utf-8").write(s)
    fig(rows, os.path.join(OUT, "fig_reasons.png"))
    print(s)


if __name__ == "__main__":
    main()
