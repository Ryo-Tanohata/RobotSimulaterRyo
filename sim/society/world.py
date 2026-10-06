"""世界 (階層 1): 2 km 四方の地図で、人・動物・植物が暮らす。Python の標準ライブラリだけで動く (クラウドの CPU 用)。

1 日の流れのうち、ここが受け持つのは「決まった手順」(docs/society_plan.md 4.3) だけ:
- 前の晩に各キャラクターが決めた予定 (活動・場所・一緒に行く人) を、1 時間ずつ実行する
- 歩く・採る・狩る・食べる・夜の危険・植物の実りと回復・動物の移動
誰に分けるか、何を話すか、何を学ぶかは決めない (それはキャラクター = Claude が決める)。

値の出どころは docs/society_plan.md 4 章 (【体】【文献】【仮定】)。
"""
import math
import random

CELL = 25                 # 1 マスの大きさ (m)
W = H = 80                # 2 km 四方
SEASONS = ["春", "夏", "秋", "冬"]
SEASON_DAYS = 30          # 【仮定】1 季節の日数 (試作なので短い)
SEASON_START = 1          # 【仮定】1 日目の季節 (0 = 春、1 = 夏)。食べ物の多い夏から始める
DAY_START, DAY_END = 6, 19  # 出発と帰る時刻

# 【体】2 足歩行 (sim/bipedal の人型 human2) で測った「1 m あたりの関節の仕事」[J/kg/m]
WALK_COT = {0.6: 1.33, 1.0: 1.45, 1.4: 1.94}
WALK_SPEED = 1.0          # 普段の歩く速さ (m/s)
COT_TO_METABOLIC = 1.5    # 【仮定】関節の仕事 → 筋肉の消費への換算の係数
BASE_KCAL = 1900          # 【文献】1 日の消費の土台 (歩く分は別に足す)
EAT_MAX = 4000            # 【仮定】1 日に食べられる上限 (kcal)
MEAT_KCAL = 18000         # 【仮定】大きな獲物 1 頭の肉
MEAT_DAYS = 2             # 【仮定】肉が食べられる日数 (その後は腐る)
FRUIT_KCAL, TUBER_KCAL = 100, 250  # 【仮定】1 つ (ひとつかみ) あたり
# キャラクターには kcal を見せず、狩猟採集民の研究で主な食べ物とされるものの数え方で見せる (kcal は内部の計算だけ)
UNITS = {"木の実": ("つかみ", FRUIT_KCAL), "芋": ("本", TUBER_KCAL), "肉": ("切れ", 600),
         "魚": ("匹", 300), "ピク": ("匹", 800), "草の種": ("つかみ", 80), "干し肉": ("切れ", 500)}
FOOD_NAME = {"木の実": "木の実", "芋": "芋", "肉": "ルクの肉", "魚": "魚", "ピク": "ピクの肉", "草の種": "草の種", "干し肉": "干し肉"}
# 【仮定】食べられる日数 (これを過ぎると腐る)。入れ物を持っていると、木の実・芋は 2 倍もつ。草の種は腐らない
SPOIL = {"木の実": 4, "芋": 8, "肉": 2, "魚": 1, "ピク": 2, "草の種": 9999, "干し肉": 30}
# 2026-10-06 追加 (F3 の評価 5-3。本人の了承「２つを直して再開」): 住まいの屋根の下の蓄えで夜をすごした木の実は乾き、採った日から DRIED_DAYS 日もつ。
#   乾いた木の実は、蓄えから取っても、人に分けても、キャンプを移しても乾いたまま (食べ物に印 "dry" がつく)。前は蓄えでも 8 日で腐り、秋の終わりに 1 日 50 つかみを超えて腐った
# 【文献】乾かして雨を避けて蓄えた木の実 (ドングリ・クルミ・ハシバミ・松の実) は、狩猟採集民の例で冬を越し、次の実りまで (ときに数年) もった
#   (カリフォルニア先住民のドングリの蓄え、グレートベースンの松の実の蓄え穴、縄文の貯蔵穴)。採ったばかりの木の実は水分が多く、乾かさないと数日〜2 週間ほどでかびる
# 【仮定】この世界の 1 季節は 30 日と短いので、文献の数か月〜1 年より短い 2 季節分 (60 日) にする。秋のどの日に採った分も冬の終わりまではもつ。芋は乾かす加工がないので入れない
DRIED_DAYS = {"木の実": 2 * SEASON_DAYS}
PLANT_FOODS = ("木の実", "芋", "草の種")
MEATS = ("肉", "魚", "ピク")


def count_of(kind, kcal):
    return int(round(kcal / UNITS[kind][1]))


def food_words(amounts):
    """{kind: kcal} → 「木の実 12 つかみ、芋 2 本」"""
    parts = [f"{FOOD_NAME[k]} {count_of(k, v)} {UNITS[k][0]}" for k, v in amounts.items() if count_of(k, v) > 0]
    return "、".join(parts) or "なし"


def holdings(person):
    out = {}
    for f in person["food"]:
        out[f["kind"]] = out.get(f["kind"], 0) + f["kcal"]
    return out
RESERVE_START, RESERVE_MAX, RESERVE_DEATH = 10000, 20000, -15000  # 【仮定】体の蓄え (kcal)。何も食べなくても数週間は生きられる

TERRAIN = {"g": "草原", "f": "林", "r": "川", "h": "丘"}
INITIAL_NAMES = ["ルオ", "セナ", "タヒ", "ウィロ", "イサ"]  # 現実の言葉と重ならない架空の名前
ACTIVITIES = ["採集", "狩り", "探索", "休む", "道具づくり", "火おこし", "種まき", "住まいを建てる", "キャンプを移す"]
DWELLING_HOURS = 20       # 住まいを建てるのに要る、のべの作業時間 (F2 の評価のあとで追加。Claude が決めた仮の数字)。
                          # 2026-10-06: F3 の 3 回目のあとで 40 → 20 (枝と草の簡単な小屋。本人の了承)
AUTUMN_GROW = 2           # 【仮定】秋の実りの回復の倍率 (2026-10-06: F3 の 3 回目のあとで 1 → 2。本人の了承)
GATHER_RADIUS = 8  # 採集で探せる範囲 (マス)。F2 の 1 回目の全滅を受けて 5 → 8 (2026-10-01)


def season(day):
    return SEASONS[(day // SEASON_DAYS + SEASON_START) % 4]


def _noise(rng, w, h, scale):
    """なめらかな乱数の地図 (値ノイズ)"""
    gw, gh = w // scale + 2, h // scale + 2
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            fx, fy = x / scale, y / scale
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0][x0] * (1 - tx) + g[y0][x0 + 1] * tx
            b = g[y0 + 1][x0] * (1 - tx) + g[y0 + 1][x0 + 1] * tx
            row.append(a * (1 - ty) + b * ty)
        out.append(row)
    return out


def generate(seed=1, names=INITIAL_NAMES):
    """新しい世界 (0 日目の夜) を作る"""
    rng = random.Random(seed)
    n1, n2 = _noise(rng, W, H, 12), _noise(rng, W, H, 6)
    terrain = []
    for y in range(H):
        row = ""
        rx = W / 2 + 14 * math.sin(y / 9 + seed) + 6 * (n2[y][0] - 0.5)  # 北から南へ蛇行する川
        for x in range(W):
            v = 0.7 * n1[y][x] + 0.3 * n2[y][x]
            if abs(x - rx) < 1.2:
                row += "r"
            elif v > 0.68:
                row += "h"
            elif v > 0.5:
                row += "f"
            else:
                row += "g"
        terrain.append(row)

    plants, pid = [], 0
    for y in range(H):
        for x in range(W):
            t = terrain[y][x]
            if t == "f" and rng.random() < 0.08:
                plants.append({"id": pid, "kind": "木の実", "x": x, "y": y, "amount": 20, "max": 30,
                               "seasons": ["春", "夏", "秋"], "regrow": 1.5})
                pid += 1
            elif t == "g" and rng.random() < 0.03:
                plants.append({"id": pid, "kind": "芋", "x": x, "y": y, "amount": 8, "max": 10,
                               "seasons": SEASONS, "regrow": 0.3})
                pid += 1

    # キャンプは川のそば、地図の真ん中あたり
    cy = H // 2
    cx = next(x for x in range(W) if terrain[cy][x] == "r") - 2
    herds = [{"id": i, "kind": "獲物", "name": "ルク", "x": rng.randrange(W), "y": rng.randrange(H), "count": 12}
             for i in range(3)]
    predators = [{"id": 0, "kind": "捕食者", "name": "ザガ", "x": rng.randrange(W), "y": rng.randrange(H)}]

    people = []
    for i, name in enumerate(names):
        people.append({
            "name": name, "alive": True, "age": rng.randint(18, 40), "sex": "女" if i % 2 else "男",
            "mass": round(rng.uniform(45, 55), 1),
            "personality": {k: round(rng.random(), 2) for k in ("協力", "大胆", "好奇心", "社交")},
            "skills": {k: round(rng.uniform(0.1, 0.3), 2) for k in ("採集", "狩り", "道具", "火")},
            "reserve": RESERVE_START, "hunger": 0.0, "fatigue": 0.0, "injured": 0,
            "food": [],            # 持っている食べ物 [{"kind", "kcal", "day"}]
            "items": [],           # 石・槍・種 など
            "trust": {n: 0.0 for n in names if n != name},
            "heard": [],           # 聞いた話 [{"day", "from", "text"}]
            "plan": {"activity": "探索", "place": "camp", "with": []},
            "today": None,         # 今日の行動の結果 (夜の振り返りに使う)
        })

    state = {
        "version": 1, "seed": seed, "day": 0, "terrain": terrain,
        "camp": {"x": cx, "y": cy, "fire": 0},  # fire = 火が残る日数
        "plants": plants, "herds": herds, "predators": predators,
        "planted": [],  # 種まき [{"x","y","day"}]
        "people": people, "events": [], "next_event": 0,
        "places": [], "stats": [],
    }
    state["places"] = make_places(state)
    return state


def make_places(state):
    """予定で選べる場所の一覧 (キャンプから見た方角と距離で、中立な名前を付ける)"""
    cx, cy, t = state["camp"]["x"], state["camp"]["y"], state["terrain"]
    places = [{"id": "camp", "label": "キャンプ", "x": cx, "y": cy}]
    for kind, code in (("林", "f"), ("草原", "g"), ("丘", "h"), ("川", "r")):
        for r in (12, 28, 45):
            for ang, dname in ((0, "東"), (90, "南"), (180, "西"), (270, "北")):
                a = math.radians(ang)
                best = None
                for dy in range(-10, 11):
                    for dx in range(-10, 11):
                        x, y = int(cx + r * math.cos(a)) + dx, int(cy + r * math.sin(a)) + dy
                        if 0 <= x < W and 0 <= y < H and t[y][x] == code:
                            d = dx * dx + dy * dy
                            if best is None or d < best[0]:
                                best = (d, x, y)
                if best:
                    x, y = best[1], best[2]
                    dist = round(math.hypot(x - cx, y - cy) * CELL / 100) * 100
                    label = f"{dname}の{kind} (キャンプから約 {dist} m)"
                    if all(abs(p["x"] - x) + abs(p["y"] - y) > 6 for p in places):
                        places.append({"id": f"{dname}{kind}{r}", "label": label, "x": x, "y": y})
    return places


def place_of(state, pid):
    for p in state["places"]:
        if p["id"] == pid:
            return p
    return state["places"][0]


def _rot(foods, day, container):
    """腐った食べ物を取り除く。戻り値 {kind: kcal}"""
    out, keep = {}, []
    for f in foods:
        if f.get("dry") and f["kind"] in DRIED_DAYS:  # 乾いた木の実 (DRIED_DAYS の説明)
            limit = DRIED_DAYS[f["kind"]]
        else:
            limit = SPOIL.get(f["kind"], 4) * (2 if container and f["kind"] in PLANT_FOODS else 1)
        if day - f["day"] >= limit:
            out[f["kind"]] = out.get(f["kind"], 0) + f["kcal"]
        else:
            keep.append(f)
    foods[:] = keep
    return out


def _small_catch(state, p, pl, hours, rng, factor, quiet=False):
    """魚 (川の近く) か小さな獲物 (ピク) をとる。1 人でもとれる"""
    river = any(state["terrain"][y][x] == "r" for y in range(max(0, pl["y"] - 2), min(H, pl["y"] + 3))
                for x in range(max(0, pl["x"] - 2), min(W, pl["x"] + 3)))
    kind = "魚" if river else "ピク"
    rate = factor * (0.12 if river else 0.06) * (1 + p["skills"]["狩り"] + (0.5 if "槍" in p["items"] else 0)) * (1 - 0.5 * max(0.0, p["fatigue"] - 0.4))
    caught = sum(1 for _ in range(int(hours)) if rng.random() < rate)
    if not quiet:
        p["skills"]["狩り"] = round(min(1, p["skills"]["狩り"] + 0.01 * hours), 3)
    if caught:
        p["food"].append({"kind": kind, "kcal": caught * UNITS[kind][1], "day": state["day"]})
        what = "魚をとった" if river else "小さな獲物 (ピク) をとった"
        text = f"{p['name']} が {pl['label']} で{what} ({FOOD_NAME[kind]} {caught} 匹)"
    elif quiet:
        return
    else:
        text = f"{p['name']} は {pl['label']} で狩りをしたが、何もとれなかった"
    p["today"]["events"].append(log(state, "狩り", p["name"], text, catch=kind if caught else None))


def _move_camp(state, day):
    """半分を超える人が同じ場所に「キャンプを移す」を選んでいたら、キャンプ (と蓄え) をそこへ移す"""
    alive = [p for p in state["people"] if p["alive"]]
    votes = {}
    for p in alive:
        p["moved_today"] = False
        plan = p.get("plan") or {}
        if plan.get("activity") == "キャンプを移す" and plan.get("place") not in (None, "camp"):
            votes.setdefault(plan["place"], []).append(p)
    if not votes:
        return
    pid, group = max(votes.items(), key=lambda kv: len(kv[1]))
    if len(group) * 2 <= len(alive):
        return
    pl = place_of(state, pid)
    x, y = pl["x"], pl["y"]
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0)):
        if 0 <= x + dx < W and 0 <= y + dy < H and state["terrain"][y + dy][x + dx] != "r":
            x, y = x + dx, y + dy
            break
    old = pl["label"]
    if state["camp"].get("dwelling", 0) > 0:
        log(state, "住まい", None, "キャンプを移したので、建てた (建てかけの) 住まいは置いていった")
    state["camp"].update({"x": x, "y": y, "fire": 0, "dwelling": 0, "dwelling_day": None})
    state["camp_moves"] = state.get("camp_moves", 0) + 1
    state["camp_since"] = day
    for p in alive:
        p["moved_today"] = True
        p["plan"] = {"activity": "キャンプを移す", "place": "camp", "with": []}
    state["places"] = make_places(state)
    log(state, "移る", None, f"{'、'.join(p['name'] for p in group)} の考えで、キャンプを {old} へ移した (蓄えも運んだ)", by=[p["name"] for p in group])


def log(state, kind, who, text, **data):
    e = {"id": state["next_event"], "day": state["day"], "type": kind, "who": who, "text": text}
    if data:
        e["data"] = data
    state["events"].append(e)
    state["next_event"] += 1
    return e["id"]


def _walk_kcal(person, dist_m):
    cot = WALK_COT[WALK_SPEED]
    return cot * COT_TO_METABOLIC * person["mass"] * dist_m / 4184


def _near(items, x, y, r):
    return [i for i in items if abs(i["x"] - x) <= r and abs(i["y"] - y) <= r]


ACT_EVENT = {"採集": "採集", "狩り": "狩り", "探索": "探索", "休む": "休む", "道具づくり": "道具", "火おこし": "火",
             "種まき": "種まき", "住まいを建てる": "住まい", "キャンプを移す": "移る"}


def tried_activities(state):
    """これまでに誰かが一度でも実際にした活動 (2026-10-05 追加。夜のお題で「まだ誰も試したことのない活動」を示すため)"""
    if "tried_acts" not in state:  # 追加する前の世界は、出来事の記録から求める
        types = {e["type"] for e in state["events"] if isinstance(e, dict) and e.get("who")} | {e["type"] for e in state["events"] if e.get("type") == "移る"}
        state["tried_acts"] = [a for a, t in ACT_EVENT.items() if t in types]
    return state["tried_acts"]


def simulate_day(state):
    """前の晩に決めた予定で、1 日を進める。戻り値: 今日の出来事の id の一覧"""
    state["day"] += 1
    day = state["day"]
    rng = random.Random(state["seed"] * 100003 + day)
    first = state["next_event"]
    sea = season(day)
    alive = [p for p in state["people"] if p["alive"]]
    camp = state["camp"]

    # 動物の移動 (獲物は草原へ、捕食者はうろつく)
    for hd in state["herds"]:
        for _ in range(6):
            nx = min(W - 1, max(0, hd["x"] + rng.randint(-2, 2)))
            ny = min(H - 1, max(0, hd["y"] + rng.randint(-2, 2)))
            if state["terrain"][ny][nx] in "gh":
                hd["x"], hd["y"] = nx, ny
        if hd["count"] < 20 and rng.random() < 0.1:
            hd["count"] += 1
    for pr in state["predators"]:
        pr["x"] = min(W - 1, max(0, pr["x"] + rng.randint(-8, 8)))
        pr["y"] = min(H - 1, max(0, pr["y"] + rng.randint(-8, 8)))

    # 草の種 (固い殻で腐りにくい) が実る草地。この仕組みを足す前の世界にも、同じ乱数で足す
    if not any(q["kind"] == "草の種" for q in state["plants"]):
        grng = random.Random(state["seed"] * 31 + 5)
        for y in range(H):
            for x in range(W):
                if state["terrain"][y][x] == "g" and grng.random() < 0.04:
                    state["plants"].append({"id": len(state["plants"]), "kind": "草の種", "x": x, "y": y, "amount": 10, "max": 15,
                                            "seasons": ["夏", "秋"], "regrow": 1.0})
    # 食べ物のつり合いの見直し (F2 の 1 回目で、キャンプの近くを採り尽くして全滅したため。2026-10-01)
    if not state.get("balance_v2"):
        for q in state["plants"]:
            if q["kind"] == "木の実":
                q["regrow"] = max(q["regrow"], 2.5)
            elif q["kind"] == "芋":
                q["regrow"] = max(q["regrow"], 0.6)
        state["balance_v2"] = True
        state["places"] = make_places(state)
    _move_camp(state, day)
    camp = state["camp"]
    # 植物の実りと回復。冬は木の実がしぼみ、芋も育ちにくい
    for pl in state["plants"]:
        if sea == "冬" and pl["kind"] == "木の実":
            pl["amount"] *= 0.9
        elif sea in pl["seasons"]:
            # 2026-10-06: F3 の 3 回目のあとで、秋の実りを 2 倍にした (秋の採集が食べる量とほぼ同じで、蓄えが増えなかったため。本人の了承)
            pl["amount"] = min(pl["max"], pl["amount"] + pl["regrow"] * {"冬": 0.3, "秋": AUTUMN_GROW}.get(sea, 1))
    for sd in list(state["planted"]):
        if day - sd["day"] >= 20:
            state["plants"].append({"id": len(state["plants"]), "kind": "木の実", "x": sd["x"], "y": sd["y"],
                                    "amount": 10, "max": 30, "seasons": ["夏", "秋"], "regrow": 1.5, "sown": True})
            state["planted"].remove(sd)
            log(state, "育つ", None, f"{sd['who']} が種をまいた場所に、木の実の木が育った", x=sd["x"], y=sd["y"], sower=sd["who"])

    # 各人の 1 日
    hunters = {}
    for p in alive:
        plan = p["plan"] or {"activity": "休む", "place": "camp", "with": []}
        act = plan.get("activity", "休む")
        if act not in ACTIVITIES:
            act = "休む"
        pl = place_of(state, plan.get("place", "camp"))
        if act == "住まいを建てる":  # 建てるのはキャンプ。材料は近くの林から運ぶ
            pl = place_of(state, "camp")
        if p["injured"] > 0:
            act, pl = "休む", place_of(state, "camp")
            p["injured"] -= 1
        dist = math.hypot(pl["x"] - camp["x"], pl["y"] - camp["y"]) * CELL * 2  # 往復
        travel_h = dist / WALK_SPEED / 3600
        work_h = max(0.0, (DAY_END - DAY_START) - travel_h - 1)
        # 疲れていると働ける時間が減り、疲れや空腹で手際が落ちる (評価 F1 の指摘)
        work_h *= 1 - 0.6 * max(0.0, p["fatigue"] - 0.5)
        knack = (1 - 0.5 * max(0.0, p["fatigue"] - 0.4)) * (1 - 0.5 * max(0.0, p["hunger"] - 0.7))  # ある程度を超えてから効く
        spent = BASE_KCAL + _walk_kcal(p, dist)
        res = {"activity": act, "place": pl["label"], "place_id": pl["id"], "walked_m": round(dist),
               "work_h": round(work_h, 1), "got": [], "spent": round(spent), "events": []}
        p["today"] = res
        tried = tried_activities(state)
        if act not in tried and not (act == "キャンプを移す" and not p.get("moved_today")):
            tried.append(act)
        p["fatigue"] = min(1.0, max(0.0, p["fatigue"] + (dist / 20000) + (0.1 if act != "休む" else -0.4)))

        if act == "採集":
            got, by_kind = 0, {}
            for _ in range(int(work_h)):
                cands = [q for q in _near(state["plants"], pl["x"], pl["y"], GATHER_RADIUS) if q["amount"] >= 1 and sea in q["seasons"]]
                if not cands:
                    break
                q = rng.choice(cands)
                if rng.random() < (0.5 + 0.4 * p["skills"]["採集"]) * knack:
                    n = min(q["amount"], rng.randint(2, 6))  # 1 時間に採れる量 (F2 の 1 回目の全滅を受けて 1〜4 → 2〜6)
                    q["amount"] -= n
                    kcal = n * UNITS[q["kind"]][1]
                    item = {"kind": q["kind"], "kcal": kcal, "day": day}
                    if q.get("sown"):  # 種をまいて育てた木からの実 (F4・F5 の判定用に印をつける。2026-10-05)
                        item["sown"] = True
                        near_camp = math.hypot(q["x"] - camp["x"], q["y"] - camp["y"]) <= GATHER_RADIUS
                        h = state.setdefault("harvests", [])
                        if near_camp and not any(r["day"] == day and r["plant"] == q["id"] for r in h):
                            h.append({"day": day, "plant": q["id"], "who": p["name"]})
                    p["food"].append(item)
                    got += kcal
                    by_kind[q["kind"]] = by_kind.get(q["kind"], 0) + kcal
                    if q["kind"] == "木の実" and "種" not in p["items"]:
                        p["items"].append("種")
            p["skills"]["採集"] = round(min(1, p["skills"]["採集"] + 0.01 * work_h), 3)
            words = food_words(by_kind)
            res["got"].append(words)
            res["events"].append(log(state, "採集", p["name"], f"{p['name']} が {pl['label']} で採集した ({words})" if got else
                                     f"{p['name']} は {pl['label']} で採集したが、何も見つからなかった", kcal=got))
        elif act == "狩り":
            hunters.setdefault(pl["id"], []).append((p, work_h))
        elif act == "キャンプを移す" and p.get("moved_today"):
            res["events"].append(log(state, "移る", p["name"], f"{p['name']} もみんなと新しいキャンプへ移った"))
        elif act in ("探索", "キャンプを移す"):  # キャンプを移す人が少なければ、その場所の下見になる
            found = []
            if rng.random() < 0.3:
                p["items"].append("鋭い石")
                found.append("割れると鋭くなる石")
            herd = _near(state["herds"], pl["x"], pl["y"], 14)
            if herd:
                found.append(f"ルクの群れ ({herd[0]['count']} 頭) が {pl['label']} の近くにいる")
            plants = [q for q in _near(state["plants"], pl["x"], pl["y"], 6) if sea in q["seasons"] and q["amount"] >= 3]
            if plants:
                found.append(f"{pl['label']} には {plants[0]['kind']} が多い ({sea})")
            near_river = any(state["terrain"][y][x] == "r" for y in range(max(0, pl["y"] - 2), min(H, pl["y"] + 3))
                             for x in range(max(0, pl["x"] - 2), min(W, pl["x"] + 3)))
            if near_river and rng.random() < 0.6:
                found.append("川に魚が泳いでいるのを見た")
            elif not near_river and rng.random() < 0.4:
                found.append("ピクという小さな獣が草むらを走るのを見た")
            res["got"] += found
            res["events"].append(log(state, "探索", p["name"], f"{p['name']} が {pl['label']} を探索した: " + ("、".join(found) or "特に何もなかった")))
        elif act == "道具づくり":
            if "鋭い石" in p["items"] and rng.random() < 0.3 + 0.5 * p["skills"]["道具"]:
                p["items"].remove("鋭い石")
                p["items"].append("槍")
                res["got"].append("槍")
                res["events"].append(log(state, "道具", p["name"], f"{p['name']} が槍を作った"))
            elif "鋭い石" not in p["items"] and "入れ物" not in p["items"] and rng.random() < 0.2 + 0.4 * p["skills"]["道具"]:
                p["items"].append("入れ物")  # 草や枝を編んだもの
                res["got"].append("入れ物")
                res["events"].append(log(state, "道具", p["name"], f"{p['name']} が草や枝を編んで入れ物を作った"))
            else:
                res["events"].append(log(state, "道具", p["name"], f"{p['name']} は道具づくりを試したがうまくいかなかった"
                                         + ("" if "鋭い石" in p["items"] else " (材料の石がない)")))
            p["skills"]["道具"] = round(min(1, p["skills"]["道具"] + 0.05), 3)
        elif act == "火おこし":
            if rng.random() < 0.08 + 0.4 * p["skills"]["火"]:
                camp["fire"] = 3
                res["got"].append("火")
                res["events"].append(log(state, "火", p["name"], f"{p['name']} がキャンプで火をおこした"))
            else:
                res["events"].append(log(state, "火", p["name"], f"{p['name']} は火をおこそうとしたが、できなかった"))
            p["skills"]["火"] = round(min(1, p["skills"]["火"] + 0.05), 3)
        elif act == "住まいを建てる":
            if camp.get("dwelling_day") is not None:
                res["events"].append(log(state, "住まい", p["name"], f"{p['name']} は住まいを手入れした"))
            else:
                forest = any(state["terrain"][y][x] == "f" for y in range(max(0, camp["y"] - 6), min(H, camp["y"] + 7))
                             for x in range(max(0, camp["x"] - 6), min(W, camp["x"] + 7)))
                before = camp.get("dwelling", 0)
                gain = work_h * (0.6 + 0.4 * p["skills"]["道具"]) * knack * (1 if forest else 0.5) / DWELLING_HOURS
                camp["dwelling"] = min(1.0, before + gain)
                if camp["dwelling"] >= 1:
                    camp["dwelling_day"] = day
                    res["got"].append("住まい")
                    res["events"].append(log(state, "住まい", p["name"], f"{p['name']} たちの手で、キャンプに屋根と壁のある住まいができた"))
                else:
                    # 2026-10-06: 半分前でも「屋根と壁をふいた」と書いていたのを、でき具合どおりの言い方に直した
                    how = ("柱を立て始めた" if before == 0 else "骨組みが半分ほどできた" if before < 0.5 <= camp["dwelling"]
                           else "骨組みを組んだ" if camp["dwelling"] < 0.5 else "枝や草で屋根と壁をふき始めた")
                    res["events"].append(log(state, "住まい", p["name"], f"{p['name']} がキャンプで住まいを建てた: {how}"
                                             f" (まだ建てかけ。でき具合 約 {max(1, round(camp['dwelling'] * 10))} 割)"
                                             + ("" if forest else " (林が遠く、材料を運ぶのに手間がかかる)")))
            p["skills"]["道具"] = round(min(1, p["skills"]["道具"] + 0.02), 3)
        elif act == "種まき":
            if "種" in p["items"]:
                p["items"].remove("種")
                state["planted"].append({"x": pl["x"], "y": pl["y"], "day": day, "who": p["name"]})
                res["events"].append(log(state, "種まき", p["name"], f"{p['name']} が {pl['label']} に種を埋めた"))
            else:
                res["events"].append(log(state, "種まき", p["name"], f"{p['name']} は種を持っていなかった"))
        else:
            res["events"].append(log(state, "休む", p["name"], f"{p['name']} はキャンプで休んだ"))
        # 昼間、遠くで一人だと捕食者に出会うことがある
        alone = sum(1 for q in alive if q is not p and (q["plan"] or {}).get("place") == pl["id"]) == 0
        if pl["id"] != "camp" and alone and _near(state["predators"], pl["x"], pl["y"], 10) and rng.random() < 0.15:
            p["injured"] = 2
            res["events"].append(log(state, "けが", p["name"], f"{p['name']} が {pl['label']} で一人のときザガに襲われ、けがをした"))

    # 狩り: 同じ場所に行った人たちが一緒に狩る。1 人だと成功しにくい
    for pid, group in hunters.items():
        pl = place_of(state, pid)
        herd = _near(state["herds"], pl["x"], pl["y"], 14)
        names = [p["name"] for p, _ in group]
        hours = min(h for _, h in group)
        if not herd or herd[0]["count"] < 2:  # ルクがいなければ、川の近くでは魚、ほかでは小さな獲物 (ピク) をとる。1 人でもとれる
            for p, h in group:
                _small_catch(state, p, pl, h, rng, 1.0)
            continue
        skill = sum(p["skills"]["狩り"] + (0.3 if "槍" in p["items"] else 0) for p, _ in group)
        per_h = 0.015 * (1 + 2 * skill) * (2.5 if len(group) >= 2 else 1)
        success = rng.random() < 1 - (1 - per_h) ** hours
        for p, _ in group:
            p["skills"]["狩り"] = round(min(1, p["skills"]["狩り"] + 0.01 * hours), 3)
        if success:
            herd[0]["count"] -= 1
            killer = rng.choice(group)[0]  # とどめを刺した人が肉を持つ (分けるかどうかは本人が決める)
            killer["food"].append({"kind": "肉", "kcal": MEAT_KCAL, "day": day})
            eid = log(state, "狩り", killer["name"], f"{'、'.join(names)} が {pl['label']} で狩りをし、{killer['name']} がルクをしとめた (肉 {count_of('肉', MEAT_KCAL)} 切れ)",
                      hunters=names, killer=killer["name"])
        else:
            eid = log(state, "狩り", names[0], f"{'、'.join(names)} は {pl['label']} で狩りをしたが、ルクはしとめられなかった", hunters=names)
        for p, _ in group:
            p["today"]["events"].append(eid)
            p["today"]["got"].append("ルクの肉" if success and p is killer else "")
            if not success:  # ルクに逃げられた日も、帰り道で魚や小さな獲物がとれることがある (F2 の 2 回目の評価で追加)
                _small_catch(state, p, pl, hours, rng, 0.5, quiet=True)

    # 火は日ごとに弱まる
    if camp["fire"] > 0:
        camp["fire"] -= 1
    return list(range(first, state["next_event"]))


def _move_food(src, dst, kind, kcal):
    """src の食べ物から kind を kcal 分、dst へ移す (古いものから)。戻り値: 移した量 {kind: kcal}"""
    moved, by = 0, {}
    for f in sorted(src, key=lambda f: f["day"]):
        if (kind and f["kind"] != kind) or moved >= kcal:
            continue
        take = min(f["kcal"], kcal - moved)
        f["kcal"] -= take
        dst.append({"kind": f["kind"], "kcal": take, "day": f["day"], **{k: True for k in ("sown", "dry") if f.get(k)}})
        moved += take
        by[f["kind"]] = by.get(f["kind"], 0) + take
    src[:] = [f for f in src if f["kcal"] > 0]
    return by


def _kcal_of(g):
    kind = {"ルクの肉": "肉", "ピクの肉": "ピク"}.get(g.get("food"), g.get("food"))
    if kind in UNITS:
        return kind, int(g.get("count", 0) or 0) * UNITS[kind][1]
    return None, int(g.get("kcal", 0) or 0)


def evening(state, gives, stores=(), takes=()):
    """夕方: 分け合い (gives = [{"from","to","food","count"}]、古い形の {"kcal"} も読める) → 食事 → 夜の危険 → 1 日の終わり"""
    day = state["day"]
    rng = random.Random(state["seed"] * 7919 + day)
    people = {p["name"]: p for p in state["people"] if p["alive"]}
    first = state["next_event"]
    shares = 0
    state.setdefault("store", [])
    stored_acts, took = 0, 0
    # キャンプの蓄えに入れる / 蓄えから取る (stores / takes = [{"who","food","count"}])
    for g in stores:
        p = people.get(g.get("who"))
        kind, kcal = _kcal_of(g)
        if p and kcal > 0:
            by = _move_food(p["food"], state["store"], kind, kcal)
            if by:
                stored_acts += 1
                log(state, "蓄える", p["name"], f"{p['name']} がキャンプの蓄えに {food_words(by)} を入れた", food=food_words(by))
    for g in takes:
        p = people.get(g.get("who"))
        kind, kcal = _kcal_of(g)
        if p and kcal > 0:
            by = _move_food(state["store"], p["food"], kind, kcal)
            if by:
                took += sum(by.values())
                log(state, "蓄えから取る", p["name"], f"{p['name']} がキャンプの蓄えから {food_words(by)} を取った", food=food_words(by))
    for g in gives:
        a, b = people.get(g.get("from")), people.get(g.get("to"))
        kind = {"ルクの肉": "肉"}.get(g.get("food"), g.get("food"))
        if kind in UNITS:
            kcal = int(g.get("count", 0)) * UNITS[kind][1]
        else:
            kind, kcal = None, int(g.get("kcal", 0) or 0)
        if not a or not b or a is b or kcal <= 0:
            continue
        moved, moved_by = 0, {}
        for f in sorted(a["food"], key=lambda f: f["day"]):  # 古いものから渡す
            if kind and f["kind"] != kind:
                continue
            if moved >= kcal:
                break
            take = min(f["kcal"], kcal - moved)
            f["kcal"] -= take
            b["food"].append({"kind": f["kind"], "kcal": take, "day": f["day"], **{k: True for k in ("sown", "dry") if f.get(k)}})
            moved += take
            moved_by[f["kind"]] = moved_by.get(f["kind"], 0) + take
        a["food"] = [f for f in a["food"] if f["kcal"] > 0]
        if moved:
            shares += 1
            b["trust"][a["name"]] = round(min(1, b["trust"].get(a["name"], 0) + 0.15), 2)
            words = food_words(moved_by)
            log(state, "分ける", a["name"], f"{a['name']} が {b['name']} に {words} を分けた", to=b["name"], kcal=moved, food=words)

    # ひどく空腹 (危ない) の人は、手元が足りなければキャンプの蓄えから食べる
    # (2026-10-06、本人の了承のうえ追加: 蓄えがあるのに何も取らずに飢え死にすることが 2 回あったため。作る側の仕組みの不足)
    for p in people.values():
        if p["hunger"] < 0.6:
            continue
        need = p["today"]["spent"] if p["today"] else BASE_KCAL
        short = min(EAT_MAX, need + 800) - sum(f["kcal"] for f in p["food"])
        if short > 0:
            by = _move_food(state["store"], p["food"], None, short)
            if by and food_words(by) != "なし":  # 蓄えが空・ごく少量なら書かない (「なし を取って食べた」にしない)
                took += sum(by.values())
                log(state, "蓄えから取る", p["name"], f"ひどく空腹の {p['name']} が、キャンプの蓄えから {food_words(by)} を取って食べた", food=food_words(by))

    eaten_total, eaten_by_kind, eaten_sown = 0, {}, 0
    for p in people.values():
        need = p["today"]["spent"] if p["today"] else BASE_KCAL
        eat = 0
        for f in sorted(p["food"], key=lambda f: f["day"]):  # 腐りやすい古いものから
            if eat >= min(EAT_MAX, need + 800):
                break
            take = min(f["kcal"], min(EAT_MAX, need + 800) - eat)
            f["kcal"] -= take
            eat += take
            eaten_by_kind[f["kind"]] = eaten_by_kind.get(f["kind"], 0) + take
            if f.get("sown"):
                eaten_sown += take
        p["food"] = [f for f in p["food"] if f["kcal"] > 0]
        # 火が残っているキャンプでは、食べ残した肉や魚が火のそばで干し肉になる (長くもつ)
        if state["camp"]["fire"] > 0:
            dried = {}
            for f in p["food"]:
                if f["kind"] in MEATS:
                    dried[f["kind"]] = dried.get(f["kind"], 0) + f["kcal"]
                    f["kind"], f["kcal"], f["day"] = "干し肉", round(f["kcal"] * 0.8), day
            if dried:
                stored_acts += 1
                log(state, "干す", p["name"], f"{p['name']} の食べ残した {food_words(dried)} が、火のそばで干し肉になった", food=food_words(dried))
        rotten = _rot(p["food"], day, "入れ物" in p["items"])
        if rotten and food_words(rotten) != "なし":  # ごく少量は記録しない (「なし」を果物の梨と取り違えたため)
            log(state, "腐る", p["name"], f"{p['name']} の {food_words(rotten)} が腐った", kcal=sum(rotten.values()))
        p["reserve"] = min(RESERVE_MAX, p["reserve"] + eat - need)
        p["hunger"] = round(min(1, max(0, (RESERVE_START - p["reserve"]) / (RESERVE_START - RESERVE_DEATH))), 2)
        eaten_total += eat
        if p["today"]:
            p["today"]["ate"] = eat
        if p["reserve"] < RESERVE_DEATH:
            p["alive"] = False
            log(state, "死", p["name"], f"{p['name']} は飢えで死んだ")

    # 夜: キャンプに捕食者が来ることがある。火と人数と住まいで守られる
    alive = [p for p in people.values() if p["alive"]]
    housed = state["camp"].get("dwelling_day") is not None
    # 雨や冷え込みの夜 (F3 で住まいが建たないため 2026-10-05 に追加。困ることだけ起き、どうすればよいかは書かない)
    # 乱数は別にして、ほかの出来事の乱数の並びを変えない
    wrng = random.Random(state["seed"] * 15485863 + day)
    rainy = wrng.random() < {"春": 0.2, "夏": 0.2, "秋": 0.3, "冬": 0.35}[season(day)]
    if rainy and alive:
        what = "冷たい雨" if season(day) == "冬" else "雨"
        if housed:
            log(state, "雨", None, f"夜、{what}が降ったが、住まいの中で濡れずに眠れた")
        else:
            wet = {}
            for f in state["store"]:
                if f["kind"] in PLANT_FOODS:
                    loss = round(f["kcal"] * 0.15)
                    f["kcal"] -= loss
                    wet[f["kind"]] = wet.get(f["kind"], 0) + loss
            state["store"][:] = [f for f in state["store"] if f["kcal"] > 0]
            text = f"夜、{what}が降り、キャンプで皆ずぶ濡れになって、よく眠れなかった"
            if wet and food_words(wet) != "なし":
                text += f"。蓄えの {food_words(wet)} が濡れて傷んだ"
            log(state, "雨", None, text, kcal=sum(wet.values()))
    for p in alive:  # 夜に眠ると疲れが少しとれる (41〜60 日目に、休まない人の疲れが 1.0 に張り付いたため追加)。屋根の下ならもう少し。雨の夜は外では眠れない
        rest = 0.0 if (rainy and not housed) else 0.15 + (0.1 if housed else 0)
        p["fatigue"] = round(max(0.0, p["fatigue"] - rest), 2)
    if _near(state["predators"], state["camp"]["x"], state["camp"]["y"], 20):
        risk = 0.12 * (0.2 if state["camp"]["fire"] > 0 else 1) * (0.6 if len(alive) >= 3 else 1) * (0.4 if housed else 1)
        if rng.random() < risk and alive:
            v = rng.choice(alive)
            if rng.random() < 0.15:
                v["alive"] = False
                log(state, "死", v["name"], f"夜、ザガがキャンプに来て {v['name']} が殺された")
            else:
                v["injured"] = 2
                log(state, "けが", v["name"], f"夜、ザガがキャンプに来て {v['name']} がけがをした")
        elif state["camp"]["fire"] > 0:
            log(state, "夜", None, "夜、ザガが近くに来たが、火を嫌って近づかなかった")

    if housed:  # 住まいの屋根の下の蓄えでは、木の実が乾く (DRIED_DAYS)
        for f in state["store"]:
            if f["kind"] in DRIED_DAYS:
                f["dry"] = True
    rotten = _rot(state["store"], day, housed)  # 住まいがあれば、芋は入れ物に入れたのと同じだけもち、木の実は乾いて DRIED_DAYS 日もつ
    if rotten and food_words(rotten) != "なし":
        log(state, "腐る", None, f"キャンプの蓄えの {food_words(rotten)} が腐った", kcal=sum(rotten.values()))
    state["stats"].append({"day": day, "alive": len(alive), "eaten": eaten_total, "shares": shares,
                           "fire": state["camp"]["fire"] > 0, "eaten_by_kind": eaten_by_kind, "stored_acts": stored_acts,
                           "store": sum(f["kcal"] for f in state["store"]), "took": took,
                           "store_lasting": sum(f["kcal"] for f in state["store"] if f["kind"] in ("草の種", "干し肉")),
                           "dwelling": round(state["camp"].get("dwelling", 0), 2), "housed": housed,
                           "eaten_sown": eaten_sown, "rain": bool(rainy and alive)})
    return list(range(first, state["next_event"]))
