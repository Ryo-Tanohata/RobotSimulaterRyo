"""G7 (王と役所) から: まわりの集落が暮らす模型の土地 (docs/society_phase/G7_design.md 4.B)

作る側が与える「模型の土地」(11×11 ます。1 ます = 歩いて半日 (約 12 km)【仮定】)。走らせたあとは地図を変えない。
G6 までは使わない (era2・g7 が G7 に入ってから読みこむ)。ここは state を読み書きしない、決まりだけの関数にして、
地域の決まりだけの掃き出し (tools/region_sweep.py。6.3) からも同じ関数を使えるようにする。

- 座標は (x, y) = (列, 行)。y は北が 0。距離は、縦と横の大きいほうのます数 (斜めも 1 ます)
- 川は南北に流れる (村の地図の川と、era2.DIRS の「川にそって南へ・北へ」に合わせた)。北の丘は、黒曜石の北の村に合わせた
- 1 ますで暮らせる人数 K【仮定】: 川ぞい 120・雨で育つ畑 60・涸れ川ぞい 60・丘 30・草原 20 人。村のますを除くと合わせて 5,000 人
- 2026-10-16 本人の答え (7. の 10「G7 に入る日に集落を置く」)。置く量 (地域の人数を K の何割にするか) はまだ決めていない
  → step.py next_part --fill の数 (書かなければ 0 = 今のまま、何も置かない)。掃き出しの表 (3.4%・10%・30%・50%) を見て本人が決める
"""
import hashlib
import math

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
BAD_IN_BAD = {"r": 0.5, "a": 0.9, "w": 0.9, "h": 1.0, "s": 1.0}
BAD_IN_GOOD = 0.05
# はじめの集落 (4.B.1): 1 つの集落の人数は、そのますの K の 3〜6 割 (等しく引く)。村から 1 ます以内には置かない。2 ます以内なら村が知っている
FILL_SHARE = (0.3, 0.6)
FILL_NEAR, KNOWN_NEAR = 1, 2
CATTLE_PER = 8  # 牛は人 8 人に 1 頭 (小数。4.F の 5)


def map_hash():
    """地図のしるし (G7 に入る日に g7.region.map_hash に残す。札の表と同じ扱い)"""
    return hashlib.sha256(REGION_MAP.encode("utf-8")).hexdigest()


def land(cell):
    x, y = cell
    return GRID[y][x]


def cap(cell):
    return K[land(cell)]


def cells():
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
    return min(free, key=lambda c: (dist(c, want), c[1], c[0])) if want in used or want == VILLAGE else want


def fill_cells(used, people_now, share, rng):
    """はじめの集落を置く (塩 79 の列。G7 に入る日に 1 回だけ。4.B.1): 地域の人数 (村を除く) が「K の合計 (村のますを除く) × share」になるまで、
    空いたますを 1 つずつ K の重みで選び、そのますの K の 3〜6 割の人の集落を置く。村から 1 ます以内と、集落のあるますは選ばない。
    戻り値: [(ます, 人数)] (置いた順)。乱数は、集落ごとに ますを選ぶ 1 回・人数 1 回 (この順)"""
    target = round(k_total() * share)
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
