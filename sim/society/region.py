"""G7 (王と役所) から: まわりの集落が暮らす模型の土地 (docs/society_phase/G7_design.md 4.B)

作る側が与える「模型の土地」(11×11 ます。1 ます = 歩いて半日 (約 12 km)【仮定】)。走らせたあとは地図を変えない。
G6 までは使わない (era2・g7 が G7 に入ってから読みこむ)。ここは state を読み書きしない、決まりだけの関数にして、
地域の決まりだけの掃き出し (tools/region_sweep.py。6.3) からも同じ関数を使えるようにする。
集落の 1 年の決まり (4.B.3: 増える・役の段・分かれる・出ていく・払い続けるか・求める・答える・戦・逃げる・同盟・なくなる) と、
決める段の数え方 (4.D.2) も、ここに置く (state は g7.py が読み書きする。川辺の村 V0 は g7.py が state から作った「見た目」で加わる)

- 座標は (x, y) = (列, 行)。y は北が 0。距離は、縦と横の大きいほうのます数 (斜めも 1 ます)
- 川は南北に流れる (村の地図の川と、era2.DIRS の「川にそって南へ・北へ」に合わせた)。北の丘は、黒曜石の北の村に合わせた
- 1 ますで暮らせる人数 K【仮定】: 川ぞい 120・雨で育つ畑 60・涸れ川ぞい 60・丘 30・草原 20 人。村のますを除くと合わせて 5,000 人
- 2026-10-16 本人の答え (7. の 10「G7 に入る日に集落を置く」)。置く量 (地域の人数を K の何割にするか) はまだ決めていない
  → step.py next_part --fill の数 (書かなければ 0 = 今のまま、何も置かない)。掃き出しの表 (3.4%・10%・30%・50%) を見て本人が決める
"""
import hashlib
import math
import random

# 地図 (4.B.1)。r 川ぞい / a 雨で育つ畑 / w 涸れ川ぞい / h 丘 / s 乾いた草原
REGION_MAP = """\
sshharahhss
sshharahhss
sssaaraasss
sssaaraasss
sssaaraasss
swwwaraasss
sssaaraasss
sssaaraasss
sssaaraasss
ssssarassss
ssssarassss"""
GRID = REGION_MAP.split("\n")
SIZE = len(GRID)
LAND = {"r": "川ぞい", "a": "雨で育つ畑", "w": "涸れ川ぞい", "h": "丘", "s": "草原"}
K = {"r": 120, "a": 60, "w": 60, "h": 30, "s": 20}  # 【仮定】1 ますで暮らせる人数
VILLAGE = (5, 5)  # 川辺の村 (V0) のます
CELL_DAYS = 0.5  # 1 ます = 歩いて半日 (G6 の「歩いて 1 日」= 2 ます)
# 8 方向 (G7 だけで使う。era2.DIRS は変えない。4 方向は DIRS と同じ言い方と、3D の地図の端)
DIRS8 = {"北": ("川にそって北へ", (49, 0)), "北東": ("北東へ", (79, 0)), "東": ("東へ", (79, 40)), "南東": ("南東へ", (79, 79)),
         "南": ("川にそって南へ", (39, 79)), "南西": ("南西へ", (0, 79)), "西": ("西へ", (0, 40)), "北西": ("北西へ", (0, 0))}
UNIT8 = {"北": (0, -1), "北東": (1, -1), "東": (1, 0), "南東": (1, 1), "南": (0, 1), "南西": (-1, 1), "西": (-1, 0), "北西": (-1, -1)}
# 地域の天気 (4.B.3 の 1。直し 8): 地域が悪い年になる見込みと、そのときに集落も悪い年になる見込み (土地ごと)。よい年は 0.05
WEATHER_BAD = 0.2
WEATHER_BAD0 = WEATHER_BAD  # もとの値 (g7.sync_world が、世界の選び "bad" のない state で戻す。G8 は 0.35)
BAD_IN_BAD = {"r": 0.5, "a": 0.9, "w": 0.9, "h": 1.0, "s": 1.0}
BAD_IN_GOOD = 0.05
# はじめの集落 (4.B.1): 1 つの集落の人数は、そのますの K の 3〜6 割 (等しく引く)。村から 1 ます以内には置かない。2 ます以内なら村が知っている
FILL_SHARE = (0.3, 0.6)
FILL_NEAR, KNOWN_NEAR = 1, 2
CATTLE_PER = 8  # 牛は人 8 人に 1 頭 (小数。4.F の 5)
# 世界の選び (2026-10-24。実験 C のため。g7.sync_world が state の g7.world から入れる。どちらも False ならいつもと同じ):
#   DESERT = 草原 (s) を砂地とみなす (K = 0。住めない。ますの一覧 cells からも除く)。NO_FLEE = 逃げ場がない (refuge がいつも None = 囲まれている)
#   (実験 A1 の tools/lab_region.py の circ "desert"・"nofl" と同じ差しかえを、本物の道に入れたもの)
DESERT = False
NO_FLEE = False


def map_hash():
    """地図のしるし (G7 に入る日に g7.region.map_hash に残す。札の表と同じ扱い)"""
    return hashlib.sha256(REGION_MAP.encode("utf-8")).hexdigest()


def land(cell):
    x, y = cell
    return GRID[y][x]


def _k(ld):
    return 0 if DESERT and ld == "s" else K[ld]


def cap(cell):
    return _k(land(cell))


def cells():
    if DESERT:
        return [(x, y) for y in range(SIZE) for x in range(SIZE) if GRID[y][x] != "s"]
    return [(x, y) for y in range(SIZE) for x in range(SIZE)]


def dist(a, b):
    """ます数 (縦と横の大きいほう。斜めも 1 ます)"""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def days(a, b=VILLAGE):
    """歩いて何日 (2 ます = 1 日。切り上げ。同じますは 0)"""
    return math.ceil(dist(a, b) * CELL_DAYS)


def k_total(skip=(VILLAGE,)):
    """暮らせる人数 K の合計 (村のますを除く)"""
    return sum(cap(c) for c in cells() if c not in skip)


def direction(cell, frm=VILLAGE):
    """村から見た 8 方向 (同じますは None)"""
    dx, dy = cell[0] - frm[0], frm[1] - cell[1]  # dy は北が +
    if dx == 0 and dy == 0:
        return None
    k = round(math.degrees(math.atan2(dy, dx)) / 45) % 8
    return ("東", "北東", "北", "北西", "西", "南西", "南", "南東")[k]


def _clamp(v):
    return min(SIZE - 1, max(0, v))


def place_known(d, n_days, used):
    """G6 からある集落 (方角と歩く日数だけがある) のます: 村から方角に 2 ます × 日数。ふさがっていれば、いちばん近い空いたます (北から、西から)"""
    ux, uy = UNIT8.get(d, (0, 0))
    want = (_clamp(VILLAGE[0] + ux * 2 * n_days), _clamp(VILLAGE[1] + uy * 2 * n_days))
    free = [c for c in cells() if c != VILLAGE and c not in used]
    return min(free, key=lambda c: (dist(c, want), c[1], c[0])) if want in used or want == VILLAGE or cap(want) == 0 else want  # cap 0: 砂地の世界だけ


def fill_cells(used, people_now, share, rng, target=None):
    """はじめの集落を置く (塩 79 の列。G7 に入る日に 1 回だけ。4.B.1): 地域の人数 (村を除く) が「K の合計 (村のますを除く) × share」になるまで、
    空いたますを 1 つずつ K の重みで選び、そのますの K の 3〜6 割の人の集落を置く。村から 1 ます以内と、集落のあるますは選ばない。
    戻り値: [(ます, 人数)] (置いた順)。乱数は、集落ごとに ますを選ぶ 1 回・人数 1 回 (この順)"""
    target = round(k_total() * share) if target is None else target  # target: 置く人数を外から (砂地の世界でも、今の地図の K の割合で置く)
    used = set(used)
    out = []
    total = people_now
    while total < target:
        free = [c for c in cells() if c not in used and dist(c, VILLAGE) > FILL_NEAR]
        if not free:
            break
        w = sum(cap(c) for c in free)
        u = rng.random() * w
        pick = free[-1]
        for c in free:  # K の重みで選ぶ (左上から順に足す)
            u -= cap(c)
            if u < 0:
                pick = c
                break
        n = max(1, round(cap(pick) * rng.uniform(*FILL_SHARE)))
        used.add(pick)
        out.append((pick, n))
        total += n
    return out


def weather(rng, places):
    """地域の天気 (塩 53。年の最後の日の _field_season のはじめに 1 回。4.B.3 の 1): places = [(番号, ます)] (村 V0 を先に、そのあと集落の番号の順)。
    戻り値: (z, 地域が悪い年か, 悪い年の番号の並び)。引く順: z → 村 → 集落の番号の順 (1 つに 1 回)"""
    z = rng.random()
    region_bad = z < WEATHER_BAD
    bad = []
    for pid, c in places:
        p = BAD_IN_BAD[land(c)] if region_bad else BAD_IN_GOOD
        if rng.random() < p:
            bad.append(pid)
    return z, region_bad, bad


# ================= まわりの集落の 1 年の決まり (4.B.3) =================
# 数はみな【仮定】。6.3 の掃き出し (tools/region_sweep.py) で測り、設計書に書いてから決める。走らせたあとは変えない
BIRTH, DEATH = 0.058, 0.049  # 2: 生まれる率・亡くなる率 (1 人 1 年。川辺の村と同じ。fidelity_checklist.md 120 行の 1,000 人あたり 58・49)
OVER_K_DEATH = 0.10  # 2: 人が K をこえたら、亡くなる率に +0.10 × (人/K − 1)
HUNGRY_DEATH, HUNGRY_PP = 0.06, 60  # 2: 悪い年で、蓄えが 1 人 60 つかみ未満なら +0.06
SURPLUS = {"r": 100, "a": 70, "w": 70, "h": 40, "s": 30}  # 3: 1 人 1 年の余り (つかみ)
BAD_SURPLUS, GRAIN_CAP, BAD_KEEP = 0.2, 300, 20  # 3: 悪い年は余り ×0.2。蓄えは 1 人 300 まで。悪い年は蓄えを食べて 1 人 20 まで (G6 と同じ)
OFFICIAL, FEED_PP = 0.05, 20  # 3・4: 役の人の食べ物は、段 1 つにつき余りの 5%。出したあとの余りが 1 人 20 つかみ以上なら「出せた」
ORG1_PEOPLE, ORG_GROUP, ORG_GROUPS = 25, 25, 6  # 4: 人 25 で段 1。決める組 (人/25 の切り上げ + 貢いでくる集落) が 6 をこえたら段 2 (Johnson 1982【記憶】)
ORG_SHORT, HEAD_CHANGE, HEAD_DROP = 2, 0.05, 0.3  # 4: 2 年続けて出せないと 1 下がる。長が代わるのは 1 年 0.05、そのとき 3 割で 1 下がる
SPLIT_AT, SPLIT_P, SPLIT_SHARE = 60, 0.5, (0.3, 0.45)  # 5: 人が 60 × (1 + 段) をこえたら、1 年 0.5 で 3〜4.5 割が出る
MOVE_P, NEW_MIN, SPLIT_NEAR, COMMIT_NEW = 0.5, 5, 2, 0.6  # 5b: K をこえたら 0.5 で、こえた分の半分が出る。5 人以上なら新しい集落。行き先は 2 ます以内。結びつき 0.6
STOP_RATIO, STOP_COMMIT, CLOSE, CASCADE = 0.8, 0.6, 0.2, 10  # 6: やめる損 < 払う損 × 0.8 で結びつき 0.6 未満ならやめる。差が 2 割以内なら集まり。見なおしは 10 回まで
ACT_SHARE, REACH, REACH2 = 0.3, 2, 4  # 7: 1 年に 3 割の集落が動く。届くのは 2 ます (段 2 なら 4 ます)
DEMAND_RATIO = {"ふつう": 1.5, "求める": 1.2}  # 7: 自分がいちばん弱い相手の何倍強ければ求めるか (「守る」は求めない)
DEMAND_SHARE, YEARS_COST, UNIT_YEARS = 0.2, 5, 10  # 7・8: 量は相手の毎年の余りの 2 割。損は 5 年分を、人の数 (1 人 = 余り 10 年分) に直す
FIGHT_SHARE, TRIB_TROOPS, WALL_DEF, HILL_DEF, WAR_EXP = 0.25, 0.5, 1.5, 1.2, 1.5  # 9: 戦える人 0.25 × 人・従う集落の兵 0.5 倍・城壁 ×1.5・丘 ×1.2・比の形の 1.5
WIN_DEATH, LOSE_DEATH, LOOT = (0.02, 0.08), (0.10, 0.25), (0.3, 0.5)  # 9: 戦う人のうち死ぬ割合 (勝った側・負けた側。Keeley 1996【記憶】)・取られる蓄えとヤギ
WAR_DAYS = (10, 50)  # 9: 戦の日は年の 10〜50 日目 (夏の 11 日目〜秋の 21 日目)
RAISE_WAR_DAY = 30  # G8 の重い押し (2026-10-25): 「増やせ」の求めを断られたときの戦の日は、年の 30 日目 (WAR_DAYS のまん中。乱数は引かない。step.py heavy の日にも同じに決める)
COMMIT_PAY, COMMIT_WITH, COMMIT_AGAINST, ALLY_AT = 0.1, 0.1, -0.2, 0.5  # 10: 結びつき (Axelrod【記憶】)。0.5 以上を同盟とよぶ
GONE_AT = 5  # 11: 5 人未満でなくなる
CATTLE_GROW, CATTLE_MAX_PER = 1.2, 4  # 4.F の 5: 牛は年に 2 割ふえ、人 4 人に 1 頭まで (小数)
SICK_BASE, SICK_MAX, SICK_DEATH = 0.005, 0.15, (0.1, 0.3)  # 4.F の 7: 病 (塩 71)。もとの率 0.005・上限 0.15・はやったら 1〜3 割が亡くなる
WALL_YEARS = 2  # 4.F の 6: 段 1 以上で、この 2 年に戦か求めにかかわった集落は、次の年の終わりに壁ができる
COUNCIL_MAX = 6  # 4.B.6: 集まりが答えるのは 1 年 6 体まで (村がかかわる分かれ目を先に)
CHOICES = {"求められた": ("払う", "戦う", "逃げる", "助けを頼む"), "払い続けるか": ("払い続ける", "やめる"), "分かれるか": ("分かれる", "とどめて役を作る")}


def num(sid):
    """集落の番号 (V0 = 0、N12 = 12)。決まりはいつも番号の順に見る"""
    return 0 if sid == "V0" else int(str(sid)[1:])


def _by(setts):
    return {s["id"]: s for s in setts}


def _live(setts):
    return sorted((s for s in setts if not s.get("gone")), key=lambda s: num(s["id"]))


def cell_of(s):
    return tuple(s["cell"])


def kcap(s):
    """暮らせる人数。川辺の村 (V0) は地図の K でなく、世界の計算で決まるので、kcap を大きくして持たせる (g7.py と掃き出し)"""
    return s.get("kcap") or _k(s["land"])


def surplus_pp(s, bad=None):
    """1 人 1 年の余り (3)。bad: 悪い年か (None なら s["bad"] を見る)。人が K をこえたら ×K/人"""
    bad = (s.get("bad") is not None) if bad is None else bad
    v = SURPLUS[s["land"]] * (BAD_SURPLUS if bad else 1.0)
    return v * min(1.0, kcap(s) / s["people"]) if s["people"] else v


def unit(s):
    """損の物差し: 1 人 = ふつうの年の余り 10 年分 (つかみ)"""
    return UNIT_YEARS * SURPLUS[s["land"]]


def base(s):
    """戦える人 × 道具 (川辺の村は、日の戦では実際に戦う人を g7.py が数える)"""
    return FIGHT_SHARE * s["people"] * s.get("tech", 1)


def ties_on(R, status="続く"):
    return [t for t in R.get("ties", []) if t["status"] == status]


def payers(R, sid):
    return sorted({t["payer"] for t in ties_on(R) if t["payee"] == sid}, key=num)


def payees(R, sid):
    return sorted({t["payee"] for t in ties_on(R) if t["payer"] == sid}, key=num)


def above(R, sid):
    """sid が直接・間接に貢いでいる集落 (輪にならないように、ここには求めない)"""
    out, todo = set(), [sid]
    while todo:
        for p in payees(R, todo.pop()):
            if p not in out:
                out.add(p)
                todo.append(p)
    return out


def strength(R, by, s, defend=False, skip=(), own=None):
    """強さ S (9) = 戦える人 × 道具 + 従う集落の兵 (0.5 倍)。守る側は城壁で ×1.5、丘で ×1.2。own: 自分の兵 (日の戦の村)。skip: 数えない従う集落"""
    S = base(s) if own is None else own
    S += TRIB_TROOPS * sum(base(by[p]) for p in payers(R, s["id"]) if p in by and p not in skip and not by[p].get("gone"))
    if defend:
        S *= (WALL_DEF if s.get("walls") is not None else 1.0) * (HILL_DEF if s["land"] == "h" else 1.0)
    return S


def p_win(a, d):
    """攻める側が勝つ見込み (Hirshleifer の比の形【記憶】)"""
    if a <= 0:
        return 0.0
    if d <= 0:
        return 1.0
    return a ** WAR_EXP / (a ** WAR_EXP + d ** WAR_EXP)


def reach(s):
    return REACH2 if s.get("org", 0) >= 2 else REACH


def occupied(setts):
    return {cell_of(s) for s in setts if not s.get("gone")} | {VILLAGE}


def best_cell(cands, frm):
    """K がいちばん大きく、いちばん近います (同じなら北から、西から。乱数なし)"""
    return min(cands, key=lambda c: (-cap(c), dist(c, frm), c[1], c[0])) if cands else None


def near_cell(setts, frm, within=SPLIT_NEAR):
    """分かれる・出ていく行き先: frm から 2 ます以内の空いたます"""
    occ = occupied(setts)
    return best_cell([c for c in cells() if c not in occ and 0 < dist(c, frm) <= within], frm)


def refuge(setts, s, a):
    """逃げ場 (8b): 求めた集落 a の届く範囲の外の空いたます (なければ None = 囲まれている)。NO_FLEE の世界では、いつも None"""
    if NO_FLEE:
        return None
    occ = occupied(setts)
    return best_cell([c for c in cells() if c not in occ and dist(c, cell_of(a)) > reach(a)], cell_of(s))


def amount_of(t):
    """求める量: 相手のふつうの年の余りの 2 割 (草の種のつかみ)"""
    return max(1, round(DEMAND_SHARE * SURPLUS[t["land"]] * min(t["people"], kcap(t))))


def _mean(r):
    return (r[0] + r[1]) / 2


def costs(R, setts, t, a, amount, defend_own=None):
    """求めへの答えの損 (8)。人の数に直す。戻り値: {手: 損} (逃げるは逃げ場があるときだけ) と、助けを頼む相手と、逃げ場"""
    by = _by(setts)
    u = unit(t)
    pay = YEARS_COST * amount / u
    Sa = strength(R, by, a)

    def fight(extra):
        pl = p_win(Sa, strength(R, by, t, defend=True, own=defend_own) + extra)
        deaths = base(t) * ((1 - pl) * _mean(WIN_DEATH) + pl * _mean(LOSE_DEATH))
        return deaths + pl * (pay + _mean(LOOT) * t.get("grain", 0) / u)
    out = {"払う": pay, "戦う": fight(0.0)}
    ally = None
    cands = [c for c in _live(setts) if c["id"] not in (t["id"], a["id"])
             and (c.get("commit") or {}).get(t["id"], 0) > max(0.0, (c.get("commit") or {}).get(a["id"], 0))]
    if cands:
        c = max(cands, key=lambda c: (c["commit"][t["id"]], -num(c["id"])))
        ally = c["id"]
        out["助けを頼む"] = fight(c["commit"][t["id"]] * base(c))
    ref = refuge(setts, t, a)
    if ref is not None:
        out["逃げる"] = (0.3 * t.get("grain", 0) + 0.5 * surplus_pp(t, False) * t["people"]) / u
    return out, ally, ref


def pick(c, allowed=None):
    """いちばん小さい損の手 (同じなら 払う > 助けを頼む > 逃げる > 戦う)"""
    order = [k for k in ("払う", "助けを頼む", "逃げる", "戦う") if k in c and (allowed is None or k in allowed)]
    return min(order, key=lambda k: (round(c[k], 9), order.index(k)))


def _close(a, b):
    return abs(a - b) <= CLOSE * max(abs(a), abs(b), 1e-9)


def commit_add(s, other, d):
    c = s.setdefault("commit", {})
    c[other] = round(min(1.0, max(0.0, c.get(other, 0.0) + d)), 3)


def _ev(out, kind, text, who=(), **data):
    out.append({"kind": kind, "text": text, "who": sorted(set(who), key=num), "data": data})


def _name(s):
    return s.get("name") or s["id"]


# ---------------- 年の終わり (年の最後の日の季節の終わり。塩 59 の列。4.G.1 の 8) ----------------

def year_end(R, setts, rng, year, day, grow_village=False, village_demand=None, out=None, heavy=None):
    """地域の 1 年 (決まりの計算と乱数だけ。集まりが答えうる分かれ目は待ち R["pending"] にする)。
    引く順: 増減 (集落の番号の順。1 人ずつ 2 回) → 役の段 (長が代わるか) → 分かれる・出ていく → 動く順を混ぜる → 戦の日 (求めごと) → seed。
    grow_village: 川辺の村 (V0) も決まりで増減させる (掃き出しだけ。本物の村は era2 が 1 人ずつ計算する)。
    village_demand: 掃き出しの村の動き方 ("いつも" = 毎年いちばん弱い相手に求める / None = 求めない (本物の村の求めは答えから))。
    heavy: G8 の重い押し (2026-10-25) の {"from": 強い集落, "to": "V0", "amount": 重い量} (g7.heavy_now が作る)。None ならいつもと同じ"""
    out = [] if out is None else out
    by = _by(setts)
    live = _live(setts)
    R["year"] = year
    # 2. 人の増減
    for s in live:
        if s.get("village") and not grow_village:
            continue
        n, k, bad = s["people"], kcap(s), s.get("bad") is not None
        b = BIRTH * (0.5 if bad else 1.0)
        d = DEATH + (OVER_K_DEATH * (n / max(1, k) - 1) if n > k else 0.0)  # max: 砂地 (K = 0) の世界の守り (K はふだん 20 以上なので同じ) + (HUNGRY_DEATH if bad and s.get("grain", 0) < HUNGRY_PP * n else 0.0)
        born = sum(1 for _ in range(n) if rng.random() < b)
        died = sum(1 for _ in range(n) if rng.random() < d)
        s["people"] = max(0, n + born - died)
    # 3. 余り (蓄え)
    for s in live:
        if s.get("village") and not grow_village:
            continue
        tot = surplus_pp(s) * s["people"] * (1 - OFFICIAL * s.get("org", 0))
        s["fed"] = s["people"] > 0 and tot >= FEED_PP * s["people"]
        if s.get("bad") is not None:
            s["grain"] = min(s.get("grain", 0), BAD_KEEP * s["people"])
        s["grain"] = max(0, min(GRAIN_CAP * s["people"], round(s.get("grain", 0) + tot)))
    collapse(R, setts, day, out)
    live = _live(setts)
    # 4. 役の段
    for s in live:
        if s.get("village") and not grow_village:
            continue
        tribs = payers(R, s["id"])
        groups = math.ceil(s["people"] / ORG_GROUP) + len(tribs)
        org = s.get("org", 0)
        s["org_short"] = 0 if s.get("fed") else s.get("org_short", 0) + 1
        want = 2 if (groups > ORG_GROUPS or s.pop("org_boost", False)) and s.get("fed") else 1 if (s["people"] >= ORG1_PEOPLE or tribs) else 0
        if want > org:
            org = want
        elif s["org_short"] >= ORG_SHORT and org > 0:
            org, s["org_short"] = org - 1, 0
        if org == 2 and want < 2 and groups <= ORG_GROUPS:
            org = max(want, 1)
        if rng.random() < HEAD_CHANGE:
            s["head_age"] = 0
            if rng.random() < HEAD_DROP and org > 0:
                org -= 1
        else:
            s["head_age"] = s.get("head_age", 0) + 1
        s["org"] = 2 if s.get("strong") else org  # G8 の強い集落は、いつも段 2 (長と集める役。乱数は同じに引く)
    # 5・5b. 分かれる・出ていく (乱数は今引いて待ちにする)
    pend = []
    for s in live:
        if s.get("village") or s.get("strong"):  # 川辺の村は決まりで分かれない (家ごとに出ていくのは、村の人の答え。掃き出しでは村の動き方)。G8 の強い集落も
            continue
        if s["people"] > SPLIT_AT * (1 + s.get("org", 0)):
            pend.append({"kind": "分かれる", "who": s["id"], "u": round(rng.random(), 6), "share": round(rng.uniform(*SPLIT_SHARE), 6)})
        elif s["people"] > kcap(s):
            pend.append({"kind": "出ていく", "who": s["id"], "u": round(rng.random(), 6), "n": math.ceil((s["people"] - kcap(s)) / 2)})
    # 6. 払い続けるか (計算して待ちにする)
    for t in sorted(ties_on(R), key=lambda t: int(t["id"][1:])):
        if t["payer"] == "V0" or t["payer"] not in by or t["payee"] not in by:
            continue
        stop, pay = stop_costs(R, setts, t)
        pend.append({"kind": "払い続けるか", "tie": t["id"], "who": t["payer"], "rule": "やめる" if _stops(by[t["payer"]], t, stop, pay) else "払い続ける",
                     "stop": round(stop, 4), "pay": round(pay, 4), "close": _close(stop, pay)})
    # 牛・城壁 (4.F の 5・6)
    for s in live:
        if s.get("village"):
            continue
        if "cattle_f" in s:
            s["cattle_f"] = round(min(s["people"] / CATTLE_MAX_PER, s["cattle_f"] * CATTLE_GROW), 6)
        if s.get("walls") is None and s.get("org", 0) >= 1 and year - s.get("conflict", -99) <= WALL_YEARS:
            s["walls"] = day
            _ev(out, "城壁", f"{_name(s)} は、まわりに土の壁を積んだ", [s["id"]], who_id=s["id"])
    # 7. 求める (1 年に 3 割の集落が動く。動く順は乱数で混ぜる)
    if heavy:  # G8 の重い押し (2026-10-25): もう払っている村に「増やせ」と求める (乱数は引かない。ほかの集落の求めより先に)
        raise_demand(R, setts, heavy, day, out)
    actors = [s for s in live if not s.get("village")]
    rng.shuffle(actors)
    actors = actors[:round(ACT_SHARE * len(actors))]
    if village_demand == "いつも" and "V0" in by and not by["V0"].get("gone"):
        actors.append(by["V0"])
    actors += [s for s in live if s.get("strong") and s not in actors]  # G8 の強い集落は毎年動く (2026-10-25。外からの押し)
    new = []
    for a in actors:
        q = _demand_target(R, setts, a, "求める" if a.get("village") else a.get("stance", "ふつう"), skip={x["to"] for x in new}, heavy=heavy)
        if q:
            new.append(q)
    for q in new:  # 戦の日 (求めごと。これからの年の 10〜50 日目。年は day + 1 から)
        q["war_day"] = day + rng.randint(*WAR_DAYS)
    for a_id, t_id, amt, war_day, hv in [(q["from"], q["to"], q["amount"], q["war_day"], q.get("heavy")) for q in new]:
        add_demand(R, by[a_id], by[t_id], {"草の種": amt}, day, war_day=war_day, then="戦う", out=out, **({"extra": {"heavy": True}} if hv else {}))
    # 8. 求めへの答え (待ち)
    for q in sorted(open_demands(R), key=lambda q: (num(q["to"]), int(q["id"][1:]))):
        if q.get("answer") or q["to"] not in by or q["from"] not in by:
            continue
        pend.append(_answer_pending(R, setts, q))
    R["pending"] = pend
    # 集まりの分かれ目 (村がかかわるものを先に。6 体まで)
    R["councils"] = choose_councils(R, setts, day)
    R["seed"] = rng.randrange(2 ** 63)
    return out


YEAR_DAYS = 120


def _answer_pending(R, setts, q):
    """求めへの答えの待ち (8。年の終わりと、step.py heavy の日の「増やせ」の求め): 決まりの手 (損のいちばん小さい手) と損"""
    by = _by(setts)
    c, ally, ref = costs(R, setts, by[q["to"]], by[q["from"]], q["what"]["草の種"])
    allowed = None if not by[q["to"]].get("village") else ("払う", "助けを頼む", "戦う")  # 川辺の村は村ごとは逃げない (家ごとに出る。4.B.5)
    rule = pick(c, allowed)
    srt = sorted(v for k, v in c.items() if allowed is None or k in allowed)
    return {"kind": "求めへの答え", "demand": q["id"], "who": q["to"], "rule": rule, "ally": ally, "refuge": ref is not None,
            "costs": {k: round(v, 4) for k, v in c.items()}, "close": len(srt) > 1 and _close(srt[0], srt[1])}


def heavy_tie(R, heavy):
    """G8 の重い押し: 村 (heavy["to"]) が強い集落 (heavy["from"]) に出している、続く貢ぎ (なければ None。番号の若いもの)"""
    return next((t for t in sorted(ties_on(R), key=lambda t: int(t["id"][1:])) if t["payer"] == heavy["to"] and t["payee"] == heavy["from"]), None)


def raise_demand(R, setts, heavy, day, out, pending=False):
    """G8 の重い押し (2026-10-25): 村がもう強い集落に貢いでいて、その貢ぎがまだ重い量でない (tie.heavy がない) なら、強い集落が「増やせ」と
    新しく求める (量は heavy["amount"]。断られたら年の 30 日目に戦)。ふつうの求めと同じに、強い集落が村の 1.5 倍以上強いときだけ。
    答えの済んでいない求めが村にあれば求めない。pending: 求めへの答えの待ちも、ここで足す (step.py heavy の日。年の終わりは 8. で足す)。
    戻り値: 求め (なければ None)"""
    by = _by(setts)
    a, t = by.get(heavy["from"]), by.get(heavy["to"])
    if not a or not t or a.get("gone") or t.get("gone") or a["people"] <= 0 or t["people"] <= 0:
        return None
    tie = heavy_tie(R, heavy)
    if not tie or tie.get("heavy") or any(q["to"] == t["id"] for q in open_demands(R)):
        return None
    if strength(R, by, a) < DEMAND_RATIO["ふつう"] * strength(R, by, t, defend=True):
        return None
    qid = f"Q{R.get('next_demand', 1)}"
    q = add_demand(R, a, t, {"草の種": heavy["amount"]}, day, war_day=(day + 1) // YEAR_DAYS * YEAR_DAYS + RAISE_WAR_DAY, then="戦う", out=out,
                   who_text=f"{_name(a)} が {_name(t)} に、毎年出している {_goods(tie['goods'])} [{tie['id']}] を増やし、"
                            f"毎年 {_goods({'草の種': heavy['amount']})} を出すように求めた [{qid}]",
                   extra={"heavy": True, "raise": tie["id"], "old": dict(tie["goods"])})
    if pending:
        R.setdefault("pending", []).append(_answer_pending(R, setts, q))
    return q


def _stops(s, t, stop, pay):
    return stop < STOP_RATIO * pay and (s.get("commit") or {}).get(t["payee"], 0) < STOP_COMMIT


def stop_costs(R, setts, t):
    """払い続けるかの損 (6): やめる損 (相手が攻めてきたときの戦の損。相手の強さに自分の兵は数えない) と、払う損 (5 年分)"""
    by = _by(setts)
    s, a = by[t["payer"]], by[t["payee"]]
    amt = sum(t["goods"].values())
    u = unit(s)
    pay = YEARS_COST * amt / u
    pl = p_win(strength(R, by, a, skip=(s["id"],)), strength(R, by, s, defend=True))
    stop = base(s) * ((1 - pl) * _mean(WIN_DEATH) + pl * _mean(LOSE_DEATH)) + pl * (pay + _mean(LOOT) * s.get("grain", 0) / u)
    return stop, pay


def _demand_target(R, setts, a, stance, skip=(), heavy=None):
    """求める相手 (7): 届く範囲で、自分の上でなく、もう貢いでいない、いちばん弱い相手。自分がその 1.5 倍 (構えが「求める」なら 1.2 倍) 以上強いとき。
    【仮定】(設計になかったので足した): 答えの済んでいない求めがある相手と、この年にもう求められた相手 (skip) には求めない
    (8 の損のくらべは、求めが 1 つのときの形なので。2026-10-17 の写しの試しで、いちばん弱い 1 つの村に 4 つの村が同じ年に求めた)。
    heavy: G8 の重い押し (2026-10-25)。強い集落 (heavy["from"]) が村 (heavy["to"]) に求める量は、重い量 (heavy["amount"]。相手えらびも、この量でくらべる)"""
    if stance == "守る" or a["people"] <= 0:
        return None
    by = _by(setts)
    up, mine = above(R, a["id"]), set(payers(R, a["id"]))
    busy = {q["to"] for q in open_demands(R)} | {q["from"] for q in open_demands(R) if q["to"] == a["id"]} | set(skip)
    cands = [t for t in _live(setts) if t["id"] != a["id"] and t["id"] not in up and t["id"] not in mine and t["id"] not in busy
             and dist(cell_of(t), cell_of(a)) <= reach(a) and t["people"] > 0
             and (not a.get("village") or t.get("known") is not None)]
    if not cands:
        return None
    if a.get("strong"):  # G8 の強い集落 (2026-10-25): 自分が 1.5 倍以上強い相手のうち、払える余り (求める量) がいちばん多い相手
        Sa, k = strength(R, by, a), DEMAND_RATIO.get(stance, DEMAND_RATIO["ふつう"])
        ok = [t for t in cands if Sa >= k * strength(R, by, t, defend=True)]
        if not ok:
            return None
        hv = heavy if heavy and heavy["from"] == a["id"] else None

        def amt(t):
            return heavy["amount"] if hv and t["id"] == hv["to"] else amount_of(t)
        t = max(ok, key=lambda t: (amt(t), -num(t["id"])))
        return {"from": a["id"], "to": t["id"], "amount": amt(t), **({"heavy": True} if hv and t["id"] == hv["to"] else {})}
    t = min(cands, key=lambda t: (strength(R, by, t, defend=True), num(t["id"])))
    if strength(R, by, a) < DEMAND_RATIO.get(stance, DEMAND_RATIO["ふつう"]) * strength(R, by, t, defend=True):
        return None
    return {"from": a["id"], "to": t["id"], "amount": amount_of(t)}


def open_demands(R):
    return [q for q in R.get("demands", []) if not q.get("end")]


def add_demand(R, a, t, what, day, war_day=None, then="戦う", out=None, who_text=None, extra=None):
    """求めを足す (Q 番号)。war_day: 断られたら戦をする日。extra: 求めに足す鍵 (G8 の重い押しの heavy・raise・old)"""
    R["next_demand"] = R.get("next_demand", 1)
    q = {"id": f"Q{R['next_demand']}", "from": a["id"], "to": t["id"], "what": dict(what), "day": day, "then": then, "war_day": war_day,
         "answer": None, "how": None, "end": None, **(extra or {})}
    R["next_demand"] += 1
    R.setdefault("demands", []).append(q)
    for s in (a, t):
        s["conflict"] = R.get("year", day // YEAR_DAYS)
    if out is not None:
        _ev(out, "求め", who_text or f"{_name(a)} が {_name(t)} に、毎年 {_goods(what)} を出すように求めた [{q['id']}]", [a["id"], t["id"]], demand=q["id"])
    return q


def _goods(g):
    return "・".join(f"{k} {n}" + (" つかみ" if k == "草の種" else "") for k, n in g.items())


def choose_councils(R, setts, day):
    """集まりが答える分かれ目を選ぶ (4.B.6): 求められた / 払い続けるかで迷う (差が 2 割以内) / 分かれるか。村 (V0) がかかわるものを先に、6 体まで。
    川辺の村は集まりではなく、村の人の答え (answer_demand) で答える"""
    by = _by(setts)
    pts = {}
    for p in R.get("pending", []):
        sid = p["who"]
        if sid == "V0" or sid not in by:
            continue
        if p["kind"] == "求めへの答え":
            q = next(x for x in R["demands"] if x["id"] == p["demand"])
            pts.setdefault(sid, []).append({"kind": "求められた", "demand": q["id"], "from": q["from"], "v0": q["from"] == "V0"})
        elif p["kind"] == "払い続けるか" and p["close"]:
            t = next(x for x in R["ties"] if x["id"] == p["tie"])
            pts.setdefault(sid, []).append({"kind": "払い続けるか", "tie": t["id"], "to": t["payee"], "v0": t["payee"] == "V0"})
        elif p["kind"] == "分かれる" and p["u"] < SPLIT_P:
            pts.setdefault(sid, []).append({"kind": "分かれるか", "v0": False})
    order = sorted(pts, key=lambda sid: (not any(x["v0"] for x in pts[sid]), num(sid)))[:COUNCIL_MAX]
    return {"day": day, "ask": order, "points": {sid: pts[sid] for sid in order}, "answers": {}}


# ---------------- 次の歩のはじめ (夏の集まりの日。4.G.1): 待ちを決める → 続くつながりの今年の分を払う ----------------

def decide(R, setts, day, village=None, make=None, out=None):
    """待ち (R["pending"]) を決める。順は 分かれる・出ていく → 払い続けるか → 求めへの答え (それぞれ集落の番号の順)。乱数は使わない。
    答えは R["councils"]["answers"] (集落ごとの {"分かれるか": 手, つながりの K 番号: 手, 求めの Q 番号: 手, "ally": 番号}) と
    village (川辺の村の {Q 番号: 手, "ally": 番号})。答えのない分かれ目は、決まりの手 (年の終わりに計算して残した手と乱数)。
    make(parent, cell, people, kind) は新しい集落を作る関数 (g7.py と掃き出しで別)。戻り値: 出来事の並び"""
    out = [] if out is None else out
    village = village or {}
    ans = (R.get("councils") or {}).get("answers") or {}
    pend, R["pending"] = R.get("pending", []), []
    for p in sorted([p for p in pend if p["kind"] in ("分かれる", "出ていく")], key=lambda p: num(p["who"])):
        by = _by(setts)
        s = by.get(p["who"])
        if not s or s.get("gone"):
            continue
        a = ans.get(s["id"]) or {}
        if p["kind"] == "分かれる":
            ch = a.get("分かれるか")
            if ch == "とどめて役を作る":
                s["org_boost"] = True
                _ev(out, "集落", f"{_name(s)} は分かれず、まとめ役の下に役を置くことにした", [s["id"]], how="集まり")
                continue
            if p["u"] >= SPLIT_P and ch != "分かれる":
                continue
            n = max(1, round(s["people"] * p["share"]))
            _move_out(R, setts, s, n, day, make, out, "分かれた", how="集まり" if ch == "分かれる" else "決まり")
        elif p["u"] < MOVE_P:
            _move_out(R, setts, s, min(p["n"], s["people"] - 1), day, make, out, "出ていった", how="決まり")
    for p in sorted([p for p in pend if p["kind"] == "払い続けるか"], key=lambda p: (num(p["who"]), p["tie"])):
        t = next((x for x in R["ties"] if x["id"] == p["tie"] and x["status"] == "続く"), None)
        if not t:
            continue
        a = (ans.get(p["who"]) or {}).get(t["id"]) if p.get("close") else None  # 集まりに聞いたのは、迷うとき (差が 2 割以内) だけ
        ch = a if a in CHOICES["払い続けるか"] else p["rule"]
        a = a if a in CHOICES["払い続けるか"] else None
        if ch == "やめる":
            end_tie(R, setts, t, day, "やめた", out, how="集まり" if a else "決まり")
            recheck(R, setts, t["payee"], day, out)
    for t in sorted((t for t in ties_on(R) if t["payer"] == "V0"), key=lambda t: int(t["id"][1:])):  # 川辺の村が出している貢ぎ: 村の答えが「やめる」ならやめる
        if village.get(t["id"]) == "やめる" and t["payee"] in _by(setts):
            end_tie(R, setts, t, day, "やめた", out, how="村の答え")
    for p in sorted([p for p in pend if p["kind"] == "求めへの答え"], key=lambda p: (num(p["who"]), p["demand"])):
        q = next((x for x in R["demands"] if x["id"] == p["demand"] and not x.get("end")), None)
        by = _by(setts)
        if not q or q["to"] not in by or q["from"] not in by or by[q["to"]].get("gone") or by[q["from"]].get("gone"):
            if q:
                q.update(end=day, answer="なくなった")
            continue
        if q["to"] == "V0":
            ch, ally, how = village.get(q["id"]), village.get("ally"), "村の答え"
            if ch not in CHOICES["求められた"] or ch == "逃げる":  # 村ごとは逃げない (逃げるは家ごとに出ていくこと。残った家は決まりの手で)
                ch, ally, how = p["rule"], p["ally"], "決まりで選んだ"
        else:
            a = ans.get(q["to"]) or {}
            ch, ally, how = a.get(q["id"]), a.get("ally"), "集まり"
            if ch not in CHOICES["求められた"]:
                ch, ally, how = p["rule"], p["ally"], "決まりで選んだ"
        answer(R, setts, q, ch, ally, day, how, out, make)
    return out


def _move_out(R, setts, s, n, day, make, out, verb, how="決まり"):
    """分かれる・出ていく (5・5b): 行き先は 2 ます以内の空いたます。5 人以上なら新しい集落、5 人未満ならいちばん近い集落に加わる"""
    if n <= 0:
        return None
    c = near_cell(setts, cell_of(s))
    if c is None:
        _ev(out, "集落", f"{_name(s)} は人が多くなったが、まわりに空いた土地がなく、{verb.replace('た', 'られなかった') if verb == '分かれた' else '出ていけなかった'}",
            [s["id"]], how=how)
        return None
    share = n / s["people"] if s["people"] else 0
    s["people"] -= n
    if n >= NEW_MIN:
        o = make(s, c, n, "分かれた集落")
        for k in ("grain", "goats"):
            m = round(s.get(k, 0) * share)
            s[k] -= m
            o[k] = o.get(k, 0) + m
        if "cattle_f" in s:
            m = s["cattle_f"] * share
            s["cattle_f"] -= m
            o["cattle_f"] = m
        o["parent"] = s["id"]
        commit_add(o, s["id"], COMMIT_NEW)
        commit_add(s, o["id"], COMMIT_NEW)
        _ev(out, "集落", f"{_name(s)} から {n} 人が{verb}。{_name(o)} を作った", [s["id"], o["id"]], how=how, new=o["id"], people=n)
        return o
    near = min((x for x in _live(setts) if x["id"] != s["id"] and not x.get("village")), key=lambda x: (dist(cell_of(x), cell_of(s)), num(x["id"])), default=None)
    if near:
        near["people"] += n
        _ev(out, "集落", f"{_name(s)} から {n} 人が出ていき、{_name(near)} に加わった", [s["id"], near["id"]], how=how, people=n)
    return near


def end_tie(R, setts, t, day, why, out, how="決まり"):
    """つながりが切れる (崩れ)"""
    by = _by(setts)
    t.update(status="切れた", end=day, why=why)
    if t["payer"] in by and t["payee"] in by:
        _ev(out, "崩れ", f"{_name(by[t['payer']])} は、{_name(by[t['payee']])} に貢ぐのをやめた ({why}) [{t['id']}]", [t["payer"], t["payee"]], tie=t["id"], how=how, why=why)


def recheck(R, setts, payee, day, out):
    """貢ぐ集落が抜けたら、同じ相手に貢ぐ集落を番号の順に見なおす (変わらなくなるまで、10 回まで。集まりには聞かない)"""
    by = _by(setts)
    for _ in range(CASCADE):
        changed = False
        for t in sorted((t for t in ties_on(R) if t["payee"] == payee and t["payer"] != "V0"), key=lambda t: num(t["payer"])):
            if t["payer"] not in by:
                continue
            stop, pay = stop_costs(R, setts, t)
            if _stops(by[t["payer"]], t, stop, pay):
                end_tie(R, setts, t, day, "相手が弱くなった", out)
                changed = True
        if not changed:
            return


def answer(R, setts, q, ch, ally, day, how, out, make=None):
    """求めへの答えを当てる (8・8b): 払う → つながり / 戦う → 戦の日 / 逃げる → 集落ごと動く / 助けを頼む → 求めを取り下げる"""
    by = _by(setts)
    a, t = by[q["from"]], by[q["to"]]
    q.update(answer=ch, how=how, answer_day=day)
    old = next((x for x in ties_on(R) if x["id"] == q["raise"]), None) if q.get("raise") else None
    if ch == "払う" and old:  # G8 の重い押し (2026-10-25): 「増やせ」に払うと答えた: 今の貢ぎの量を、求めの量にする (新しいつながりは作らない)
        old.update(goods=dict(q["what"]), heavy=True, raised=day, raise_demand=q["id"])
        q["end"] = day
        _ev(out, "貢ぎ", f"{_name(t)} は、{_name(a)} の求め [{q['id']}] に、毎年 {_goods(q['what'])} に増やして出すと答えた ({how}) [{old['id']}]",
            [t["id"], a["id"]], demand=q["id"], tie=old["id"], how=how)
    elif ch == "払う":
        R["next_tie"] = R.get("next_tie", 1)
        tie = {"id": f"K{R['next_tie']}", "payer": t["id"], "payee": a["id"], "goods": dict(q["what"]), "since": day, "due": "夏の集まりの日",
               "paid": [], "missed": 0, "status": "続く", "end": None, "fixed": None, "demand": q["id"], **({"heavy": True} if q.get("heavy") else {})}
        R["next_tie"] += 1
        R.setdefault("ties", []).append(tie)
        q["end"] = day
        _ev(out, "貢ぎ", f"{_name(t)} は、{_name(a)} の求め [{q['id']}] に、毎年 {_goods(q['what'])} を出すと答えた ({how}) [{tie['id']}]",
            [t["id"], a["id"]], demand=q["id"], tie=tie["id"], how=how)
    elif ch == "戦う":
        R["next_war"] = R.get("next_war", 1)
        w = {"id": f"W{R['next_war']}", "att": a["id"], "def": t["id"], "day": q.get("war_day") or day + 9, "demand": q["id"], "done": None}
        R["next_war"] += 1
        R.setdefault("wars", []).append(w)
        _ev(out, "求め", f"{_name(t)} は、{_name(a)} の求め [{q['id']}] を断った ({how})", [t["id"], a["id"]], demand=q["id"], how=how, war=w["id"])
    elif ch == "助けを頼む" and ally and ally in by:
        q["end"] = day
        commit_add(by[ally], t["id"], COMMIT_WITH)
        commit_add(t, ally, COMMIT_WITH)
        _ev(out, "同盟", f"{_name(t)} は {_name(by[ally])} に助けを頼んだ。{_name(a)} は求め [{q['id']}] を取り下げた ({how})",
            [t["id"], ally, a["id"]], demand=q["id"], ally=ally, how=how)
    elif ch == "逃げる":
        q["end"] = day
        flee(R, setts, t, a, day, out, how)
    else:  # 助けを頼む相手がいない: 決まりの手 (払う > 戦う で小さいほう)
        c, al, ref = costs(R, setts, t, a, q["what"]["草の種"])
        answer(R, setts, q, pick(c, ("払う", "戦う")), None, day, how, out, make)


def flee(R, setts, s, a, day, out, how="決まり"):
    """集落ごと逃げる (8b): 求めた集落の届く範囲の外の空いたますへ。蓄えの 3 割と余り半年分を失う。自分が貢いでいたつながりは切れる。
    自分に貢いでいた集落は、新しいますから届けば続く"""
    c = refuge(setts, s, a)
    if c is None:
        return False
    by = _by(setts)
    old = cell_of(s)
    loss = round(0.3 * s.get("grain", 0) + 0.5 * surplus_pp(s, False) * s["people"])
    s["grain"] = max(0, s.get("grain", 0) - loss)
    s["cell"], s["land"] = list(c), land(c)
    for t in ties_on(R):
        if t["payer"] == s["id"]:
            end_tie(R, setts, t, day, "逃げた", out, how)
        elif t["payee"] == s["id"] and t["payer"] in by and dist(cell_of(by[t["payer"]]), c) > reach(s):
            end_tie(R, setts, t, day, "相手が遠くへ行った", out, how)
    _ev(out, "逃げる", f"{_name(s)} は、{_name(a)} の求めから逃げ、遠くの空いた土地へ移った", [s["id"], a["id"]], how=how, frm=list(old), to=list(c))
    return True


def pay_ties(R, setts, day, pay_hook=None, out=None, only=None):
    """続くつながりの今年の分を払う (夏の集まりの日)。pay_hook(tie, つかみ, "出す" | "受ける") は川辺の村 (V0) の出し入れ
    (戻り値: 出せた・受けた量。None なら V0 もほかの集落と同じに grain で数える (掃き出し))。払えなければ「切れた」(崩れ)。
    期日に 2 回続けて払われたら「決まった」(fixed にその日)"""
    out = [] if out is None else out
    by = _by(setts)

    def give(s, n, t):
        if s.get("village") and pay_hook:
            return pay_hook(t, n, "出す")
        n = min(n, s.get("grain", 0))
        s["grain"] = s.get("grain", 0) - n
        return n

    def take(s, n, t):
        if s.get("village") and pay_hook:
            pay_hook(t, n, "受ける")
        else:
            s["grain"] = s.get("grain", 0) + n
    for t in sorted(ties_on(R), key=lambda t: int(t["id"][1:])):
        if only is not None and t["id"] not in only:
            continue
        s, a = by.get(t["payer"]), by.get(t["payee"])
        if not s or not a or s.get("gone") or a.get("gone"):
            end_tie(R, setts, t, day, "相手がなくなった", out)
            continue
        want = t["goods"].get("草の種", 0)
        got = give(s, want, t)
        if got:
            take(a, got, t)
        if got < want:
            t["missed"] += 1
            end_tie(R, setts, t, day, "払えなかった", out)
            continue
        t["paid"].append(day)
        commit_add(s, a["id"], COMMIT_PAY)
        commit_add(a, s["id"], COMMIT_PAY)
        if len(t["paid"]) >= 2 and t.get("fixed") is None:
            t["fixed"] = day
        _ev(out, "貢ぎ", f"{_name(s)} が {_name(a)} に {_goods({'草の種': got})} を出した [{t['id']}]", [s["id"], a["id"]], tie=t["id"], amount=got)
    return out


# ---------------- 戦 (9) ----------------

def war_rng(world_seed, n):
    """戦ごとの乱数 (文字の種。Python は文字の種を SHA-512 で数に直すので、PYTHONHASHSEED によらない)"""
    return random.Random(f"G7|{world_seed}|戦|{n}")


def fight(R, setts, w, rng, day, own=None, out=None):
    """戦をする。own: 川辺の村が実際に出した {"S": 強さ (自分の兵だけ), "n": 戦った人の数} (日の戦では g7.py が数える。そのときは
    川辺の村の人と物を、ここではさわらない。呼んだ側が w の dead・loot を当てる)。own がなければ、川辺の村もほかの集落と同じ (掃き出し)。
    戻り値: w (att_win・dead {番号: 死んだ数}・fighters・loot を足したもの)"""
    out = [] if out is None else out
    by = _by(setts)
    a, d = by[w["att"]], by[w["def"]]
    ext = own is not None  # 川辺の村は呼んだ側が当てる

    def mine(s):
        return own if ext and s.get("village") else None
    Sa = strength(R, by, a, own=(mine(a) or {}).get("S"))
    Sd = strength(R, by, d, defend=True, own=(mine(d) or {}).get("S"))
    allies = {}
    for c in _live(setts):  # 結びつきが 0.5 以上なら加わる (結びつきの強いほうに)
        if c["id"] in (a["id"], d["id"]):
            continue
        ca, cd = (c.get("commit") or {}).get(a["id"], 0), (c.get("commit") or {}).get(d["id"], 0)
        if max(ca, cd) >= ALLY_AT:
            side = "att" if ca > cd else "def"
            allies[c["id"]] = side
            if side == "att":
                Sa += max(ca, cd) * base(c)
            else:
                Sd += max(ca, cd) * base(c)
    p = p_win(Sa, Sd)
    u = rng.random()
    win = u < p
    fa = (mine(a) or {}).get("n", round(FIGHT_SHARE * a["people"]))  # 戦った人の数
    fd = (mine(d) or {}).get("n", round(FIGHT_SHARE * d["people"]))
    ra, rd = rng.uniform(*(WIN_DEATH if win else LOSE_DEATH)), rng.uniform(*(LOSE_DEATH if win else WIN_DEATH))
    dead = {a["id"]: min(a["people"], round(fa * ra)), d["id"]: min(d["people"], round(fd * rd))}
    share = rng.uniform(*LOOT)
    loser, winner = (d, a) if win else (a, d)
    loot = {"草の種": round(loser.get("grain", 0) * share), "ヤギ": int(loser.get("goats", 0) * share), "share": round(share, 4)}
    for s in (a, d):
        if not (ext and s.get("village")):
            s["people"] -= dead[s["id"]]
        s["conflict"] = day // YEAR_DAYS
    if not (ext and loser.get("village")):
        loser["grain"] -= loot["草の種"]
        loser["goats"] = loser.get("goats", 0) - loot["ヤギ"]
    if not (ext and winner.get("village")):
        winner["grain"] = winner.get("grain", 0) + loot["草の種"]
        winner["goats"] = winner.get("goats", 0) + loot["ヤギ"]
    for c, side in allies.items():
        commit_add(by[c], a["id"] if side == "att" else d["id"], COMMIT_WITH)
        commit_add(by[c], d["id"] if side == "att" else a["id"], COMMIT_AGAINST)
    commit_add(a, d["id"], COMMIT_AGAINST)
    commit_add(d, a["id"], COMMIT_AGAINST)
    q = next((x for x in R.get("demands", []) if x["id"] == w.get("demand")), None)
    w.update(done=day, att_win=win, p=round(p, 4), u=round(u, 6), Sa=round(Sa, 3), Sd=round(Sd, 3), dead=dead, loot=loot, allies=allies,
             fighters={a["id"]: fa, d["id"]: fd})
    if q:
        q.update(end=day, result="勝った" if win else "負けた")
    old = next((x for x in ties_on(R) if x["id"] == q["raise"]), None) if q and q.get("raise") else None
    if win and q and old:  # G8 の重い押し (2026-10-25): 「増やせ」を断って負けた: 今の貢ぎの量を、求めの量にする (払うのは次の夏から)
        old.update(goods=dict(q["what"]), heavy=True, raised=day, raise_demand=q["id"])
        w["tie"] = old["id"]
    elif win and q:  # 守る側が負ければ貢ぐ集落になる (今年の分は取られた物。払うのは次の夏から)
        R["next_tie"] = R.get("next_tie", 1)
        tie = {"id": f"K{R['next_tie']}", "payer": d["id"], "payee": a["id"], "goods": dict(q["what"]), "since": day, "due": "夏の集まりの日",
               "paid": [], "missed": 0, "status": "続く", "end": None, "fixed": None, "demand": q["id"], "by_war": w["id"], **({"heavy": True} if q.get("heavy") else {})}
        R["next_tie"] += 1
        R.setdefault("ties", []).append(tie)
        w["tie"] = tie["id"]
    _ev(out, "戦", f"{_name(a)} が {_name(d)} を攻め、{_name(winner)} が勝った (死んだ人 {_name(a)} {dead[a['id']]}・{_name(d)} {dead[d['id']]})",
        [a["id"], d["id"]] + list(allies), war=w["id"], att_win=win)
    if not win and old:  # G8 の重い押し: 「増やせ」を断って勝った: 今の貢ぎもやめる
        end_tie(R, setts, old, day, "戦に勝った", out)
    if not win:
        recheck(R, setts, a["id"], day, out)
    collapse(R, setts, day, out)
    return w


def collapse(R, setts, day, out):
    """なくなる (11): 5 人未満の集落は、貢ぐ相手・もとの集落・いちばん近い集落の順に人が移り、なくなる (川辺の村は数えない)"""
    for s in _live(setts):
        if s.get("village") or s["people"] >= GONE_AT:
            continue
        by = _by(setts)
        cand = [x for x in payees(R, s["id"]) if x in by and not by[x].get("gone")] + ([s["parent"]] if s.get("parent") in by and not by[s["parent"]].get("gone") else [])
        if not cand:
            near = min((x for x in _live(setts) if x["id"] != s["id"]), key=lambda x: (dist(cell_of(x), cell_of(s)), num(x["id"])), default=None)
            cand = [near["id"]] if near else []
        to = by[cand[0]] if cand else None
        if to and not to.get("village"):
            to["people"] += s["people"]
            to["grain"] = to.get("grain", 0) + s.get("grain", 0)
        s["gone"] = day
        for t in ties_on(R):
            if s["id"] in (t["payer"], t["payee"]):
                end_tie(R, setts, t, day, "なくなった", out)
        for q in open_demands(R):
            if s["id"] in (q["from"], q["to"]):
                q.update(end=day, answer=q.get("answer") or "なくなった")
        R.setdefault("gone", []).append({"id": s["id"], "day": day, "to": to["id"] if to else None, "people": s["people"]})
        _ev(out, "集落", f"{_name(s)} は人が少なくなり、" + (f"{_name(to)} に移った" if to else "なくなった"), [s["id"]] + ([to["id"]] if to else []),
            gone=s["id"], to=to["id"] if to else None, people=s["people"])


def sick(rng, s, links, near_sick):
    """病 (4.F の 7。塩 71): 見込み p = min(0.15, 0.005 × 人/60 × (1 + つながりの数))。前の年に病がはやった集落と交換していれば ×2。
    戻り値: (はやったか, p)。引くのは 1 回 (はやったら、まわりの集落は死ぬ割合をもう 1 回引く)"""
    p = min(SICK_MAX, SICK_BASE * s["people"] / 60 * (1 + links) * (2 if near_sick else 1))
    return rng.random() < p, p


# ---------------- 決める段 (4.D.2) ----------------

def levels(setts, ties, day, officials=None, village_rules=False):
    """決める段 D を、集落・つながり・役の図の上で数える (4.D.2)。ties: この 1 年 (今日をふくむ 120 日) に渡した記録のある、続くつながり。
    葉 = 集落ごとの家々 (川辺の村もまとめて 1 つ)。決める人 = 集落の長 (段 2 の集落は長の下に、貢いでくる集落すべてから集める役が 1 つ) と、村の役の人。
    officials: 川辺の村の役の人 {名前: [下 (「V0」= 村の葉、または貢いでくる集落の番号)]} (取り立てた物を村の蓄えに入れた人。村の蓄えはまとめ役に渡したとみなす)。
    段: 自分の葉だけ → 0 / 別々の下を 2 つ以上 → 下でいちばん高い段 + 1 / 下が 1 つ → 段を足さない。輪になる矢印は、新しいほうを数えない。
    village_rules: 川辺の村も、ほかの集落と同じに役の段で数える (掃き出しと、2026-10-24 からの g7 の数え方 "v2")。
      村の役の段 (org) が 2 以上で貢いでくる集落があれば、村の長の下に、貢いでくる集落みなを下にもつ役 ("役", "V0") を置く (officials は使わない)。
      貢いでくる集落がない・org が 2 より下なら、前のまま (officials があれば officials で数える)
    戻り値: いちばん上の人ごとの {"top", "D", "T" (集落だけで数えた段 + 1), "office" (役の人が足した段), "members", "village" (中心 / 従う / 外), "B"}"""
    live = {s["id"]: s for s in setts if not s.get("gone")}
    edges = []  # (払う側, 受ける側)
    for t in sorted(ties, key=lambda t: (t.get("since", 0), int(str(t["id"])[1:]))):
        if t["payer"] not in live or t["payee"] not in live:
            continue
        up, todo = set(), [t["payee"]]
        while todo:  # 受ける側から上へたどって、払う側に着くなら輪になる (新しいほうを数えない)
            x = todo.pop()
            for p, q in edges:
                if p == x and q not in up:
                    up.add(q)
                    todo.append(q)
        if t["payer"] in up or t["payer"] == t["payee"]:
            continue
        edges.append((t["payer"], t["payee"]))
    officials = officials or {}
    kids = {}  # 決める人 → 下 (葉は ("葉", 番号)、人は ("長", 番号) か ("役", 番号) か ("村の役", 名前))
    for sid, s in live.items():
        subs = [p for p, q in edges if q == sid]
        leaf = [("葉", sid)]
        if sid == "V0" and officials and not (village_rules and s.get("org", 0) >= 2 and subs):
            covered = set()
            for n, src in sorted(officials.items()):
                kids[("村の役", n)] = [("葉", "V0") if x == "V0" else ("長", x) for x in sorted(set(src), key=num)]
                covered |= set(src)
            kids[("長", sid)] = ([] if "V0" in covered else leaf) + [("村の役", n) for n in sorted(officials)] + [("長", p) for p in subs if p not in covered]
        elif s.get("org", 0) >= 2 and subs and (sid != "V0" or village_rules):
            kids[("役", sid)] = [("長", p) for p in subs]
            kids[("長", sid)] = leaf + [("役", sid)]
        else:
            kids[("長", sid)] = leaf + [("長", p) for p in subs]
    memo = {}

    def lv(node, office_ok=True):
        key = (node, office_ok)
        if key in memo:
            return memo[key]
        if node[0] == "葉":
            return 0
        ch = kids.get(node, [])
        if not office_ok:  # 集落だけで数える (役の人をとばして、その下を見る)
            flat = []
            for c in ch:
                flat += kids.get(c, []) if c[0] in ("役", "村の役") else [c]
            ch = list(dict.fromkeys(flat))
        vals = [lv(c, office_ok) for c in ch]
        memo[key] = 0 if not vals else max(vals) + 1 if len(ch) >= 2 else vals[0]
        return memo[key]
    tops = [sid for sid in live if not any(p == sid for p, _ in edges)]
    out = []
    for sid in sorted(tops, key=num):
        mem, todo = set(), [sid]
        while todo:
            x = todo.pop()
            if x not in mem:
                mem.add(x)
                todo += [p for p, q in edges if q == x]
        D, T = lv(("長", sid)), lv(("長", sid), False)

        def depth(x):
            return max([1 + depth(p) for p, q in edges if q == x] or [0])
        out.append({"top": sid, "D": D, "T": T + 1, "office": D - T, "members": sorted(mem, key=num),
                    "village": "中心" if sid == "V0" else "従う" if "V0" in mem else "外",
                    "B": depth(sid) + (1 if live[sid].get("org", 0) >= 2 else 0)})
    return out
