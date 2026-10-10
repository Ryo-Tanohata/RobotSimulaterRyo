"""ダッシュボードの内側の記録 (docs/dashboard_records_spec.md)。世界の進み方には使わない: state を読むだけで、変えない・乱数を使わない

- 季節の終わりの控え (records/snapshots.jsonl の 1 行): 今の値しか残らないもの (家ごとのヤギ・家の倉・持ち物・技能・空腹・土器・鎌・条件の値など)
- 控えの読み込みと確かめ (今の出来事の記録とつながっているものだけ使う)
- 年齢の区分・死因の種類・日と季節の呼び方
(2026-10-09 追加。本人と決めたこと: docs/dashboard_data_model.md の 5.)
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import archive  # noqa: E402
import era2  # noqa: E402
import world  # noqa: E402

SNAP_V = 1
SNAP_FILE = "snapshots.jsonl"

# 【仮定】年齢の区分 (2026-10-09 本人と決めた。境目は仮)。正確な年齢は内側の記録にだけ持つ
AGE_CLASSES = (("乳飲み子", 0, 2), ("子", 3, 11), ("手伝える子", 12, 14), ("大人", 15, 54), ("年寄り", 55, None))
DEATH_CAUSES = (("飢え", r"飢えで死んだ"), ("ザガ", r"ザガ.*殺された"), ("病", r"病で亡くなった"), ("年", r"年をとって亡くなった"),
                ("子", r"\(\d+ 歳\) が亡くなった$"))  # 子の死 (病・けが・飢えの区別は記録にない)


def _age_class(age):
    if age is None or age < 0:
        return None
    return next(n for n, lo, hi in AGE_CLASSES if age >= lo and (hi is None or age <= hi))


def age_class(age):
    """年齢 (歳) → 区分 (生まれる前は None)。era2 に同じものがあれば、そちらを使う (決まりを 1 か所にするため)"""
    f = getattr(era2, "age_class", None)
    if f and age is not None and age >= 0:
        try:
            c = f(age)
            if isinstance(c, str):
                return c
        except Exception:  # 形のちがう関数なら、ここの決まりを使う
            pass
    return _age_class(age)


def age_on(p, day):
    """その日の年齢 (era2 の季節の終わりの年のとり方と同じ: (日 − 生まれた日) // 1 年)"""
    return None if p.get("born_day") is None else (day - p["born_day"]) // era2.YEAR


def death_cause(text):
    """出来事「死」の文 → 死因の種類"""
    return next((n for n, pat in DEATH_CAUSES if re.search(pat, text or "")), "その他")


def day_label(day):
    return f"{day // era2.YEAR}年{day % era2.YEAR + 1}日目"


def season_label(day):
    return f"{day // era2.YEAR}年の{world.season(day)}"


def season_end(day):
    """その日をふくむ季節の終わりの日"""
    return day + world.SEASON_DAYS - 1 - day % world.SEASON_DAYS


# ---- 季節の集まりの区切り (決まりは era2.meeting_first の 1 か所だけ。spec 3.4) ----

def meeting_first(state, day):
    """day 日の終わりの季節の集まりの、最初の出来事の id (読むだけ)"""
    return era2.meeting_first(state, day)


# ---- フェーズの条件の中身 (era2 にあればそれを使う。spec 7.2) ----

CRITERIA_PARTS = {
    "G1": [("population", ">=", 10, "人 (子をふくむ)"), ("children_1y", ">=", 2, "村で生まれて 1 歳をこえた子"), ("joined", ">=", 1, "よそから来た人")],
    "G2": [("harvest_2y", "is", True, "畑の収穫が 2 年続く"), ("goats", ">=", 5, "飼うヤギ"), ("farm_share", ">=", 0.5, "1 年に食べた量のうち育てたものの割合")],
    "G3": [("surplus_2y", "is", True, "余りの年が 2 年続く"), ("specialists", ">=", 1, "作ることに 20 日以上使った人")],
    "G4": [("owned", "is", True, "家ごとの持ち物がある"), ("inherits", ">=", 1, "受けつぎ")],
    "G5": [("g5_stage", ">=", 2, "第 2 段"), ("households", ">=", 6, "家族"),
           ("g5_path", "set", None, "まとめ役が 2 回以上裁いた、か、まとめ役なしで 8 季節もめごとを収め続けた")],  # 2026-10-09 本人と決めた (era2.CRITERIA と同じ)
    # G6: 町と記録に、それぞれ一度でも届いた (届いた日は区切り F3・F4。era2.CRITERIA と同じ。両方そろうと Society 2.0 の終わり)
    "G6": [("g6_town_day", "set", None, "町に届いた (50 人以上・4 季節続けて交換・相手の村 2 つ以上・いちばん大きい相手の 2 倍以上・食べ物をとらない人が大人の 1 割以上)"),
           ("g6_record_day", "set", None, "記録に届いた (粘土の板で量を確かめた)")],
}


# 条件を変えた日より前の季節は、そのときの条件で記録する (era: [(この日までの季節は, その条件)])
CRITERIA_BEFORE = {
    "G5": [(3359, [("g5_stage", ">=", 2, "第 2 段"), ("households", ">=", 6, "家族"), ("leader", "set", None, "まとめ役がいる"),
                   ("penalty_laws", ">=", 3, "罰のある掟"), ("judged", ">=", 2, "まとめ役の裁き"), ("penalties", ">=", 1, "罰を払わせた")]),
           (3509, [("g5_stage", ">=", 2, "第 2 段"), ("households", ">=", 6, "家族"), ("leader", "set", None, "まとめ役がいる"),
                   ("judged", ">=", 2, "まとめ役の裁き")])],
}


def _criteria_progress(era, ind, day=None):
    ok = {">=": lambda v, t: v is not None and v >= t, "is": lambda v, t: v is t or v == t, "set": lambda v, t: bool(v)}
    parts = getattr(era2, "CRITERIA_PARTS", CRITERIA_PARTS)
    if day is not None:
        old = next((p for until, p in CRITERIA_BEFORE.get(era, []) if day <= until), None)
        if old:
            parts = dict(parts, **{era: old})
    items = [{"key": k, "label": lab, "op": op, "target": t, "value": ind.get(k), "met": ok[op](ind.get(k), t)}
             for k, op, t, lab in parts.get(era, [])]
    return {"era": era, "items": items, "all_met": bool(items) and all(x["met"] for x in items)}


def criteria_progress(era, ind, day=None):
    """条件ごとの、今の値・目標・そろったか (読むだけ)。day を渡すと、その季節に使っていた条件で見る"""
    return getattr(era2, "criteria_progress", _criteria_progress)(era, ind, day)


# ---- 季節の終わりの控え ----

def _copy(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def _kinds(foods):
    """食べ物の一覧 → {物: kcal} (物の名前の順)"""
    out = {}
    for f in foods or []:
        out[f["kind"]] = out.get(f["kind"], 0) + f["kcal"]
    return {k: out[k] for k in sorted(out)}


def event_sig(state, eid):
    """出来事 1 つのしるし (控えが今の記録とつながっているかを見る)"""
    if eid is None or eid < 0:
        return None
    e = archive.event_at(state, eid)  # 古い年をしまった state でも、番号で探す (しまった出来事は None。全部を読むときは archive.full)
    if e is None:
        return None
    return hashlib.sha1(f"{e['day']}|{e['type']}|{e.get('who')}|{e['text']}".encode("utf-8")).hexdigest()[:16]


def snapshot(state, meeting_first=None, event_first=None, source="live", notes=None):
    """季節の終わりの控え (1 行)。state は読むだけ (.get と写しだけ。era2 の呼び出しは store_days と _reps だけ)"""
    e2 = state.get("era2") or {}
    g = e2.get("g5") or {}
    end = state.get("next_event", len(state.get("events", [])))
    rep_mode = bool(e2.get("rep_mode"))
    people = {}
    for p in state.get("people", []):
        row = {"alive": bool(p.get("alive")), "age": p.get("age"), "household": p.get("household"), "child": bool(p.get("child")),
               "left": p.get("left"), "food": _kinds(p.get("food"))}
        if p.get("alive"):
            row.update({"hunger": p.get("hunger"), "fatigue": p.get("fatigue"), "injured": p.get("injured"), "reserve": p.get("reserve"),
                        "skills": _copy(p.get("skills") or {}), "items": _copy(p.get("items") or []),
                        "pot_work": p.get("pot_work"), "sickle_work": p.get("sickle_work"),
                        "knowledge": len(p.get("knowledge") or []), "last_birth": p.get("last_birth")})
        row["plan"] = _copy(p.get("plan"))
        people[p["name"]] = row
    homes = {h: {"start": v.get("start"), "built": v.get("built"), "size": v.get("size"), "work": v.get("work")}
             for h, v in sorted((e2.get("homes") or {}).items())}
    houses = {h: {"keep": bool(v.get("keep")), "store": _kinds(v.get("store"))} for h, v in sorted((e2.get("house") or {}).items())}
    try:
        sdays = era2.store_days(state) if state.get("era2") else None
    except Exception:  # 古い state で数えられないとき
        sdays = None
    try:
        reps = sorted(era2._reps(state)) if rep_mode else []
    except Exception:
        reps = []
    g5 = None
    if g:
        g5 = {"stage": g.get("stage"), "stage1": g.get("stage1"), "stage_open": _copy(g.get("open")), "leader": g.get("leader"),
              "leader_day": g.get("leader_day"), "last_flow": _copy(g.get("last_flow") or {}), "feast_day": g.get("feast_day"),
              "feasts": g.get("feasts"), "settled": g.get("settled"), "judged": g.get("judged"), "penalties": g.get("penalties"),
              "joint": g.get("joint"), "votes": _copy(g.get("votes")), "call": _copy(g.get("call")), "next": g.get("next"),
              "open": [d["id"] for d in g.get("disputes", []) if d.get("status") == "収まっていない"],
              "fissions": len(g.get("fissions") or []), "meet_first": g.get("meet_first")}
    return {
        "v": SNAP_V, "day": state["day"], "season_end": season_end(state["day"]), "source": source,
        "meeting_first": meeting_first, "event_first": event_first if event_first is not None else e2.get("last_first"),
        "event_end": end, "sig": event_sig(state, end - 1),
        "era": state.get("era"), "era_info": _copy(state.get("era_info")), "hold": bool(state.get("hold")),
        "village": {"store": _kinds(state.get("store")), "store_days": sdays, "pots": e2.get("pots", 0), "sickles": e2.get("sickles", 0),
                    "wild_goats": (e2.get("wild_goats") or {}).get("count"), "next_goat": e2.get("next_goat", 0)},
        "goats": [{"id": x.get("id"), "sex": x.get("sex"), "born": x.get("born"), "owner": x.get("owner")} for x in e2.get("goats", [])],
        "houses": houses, "homes": homes,
        "fields": [_copy(f) for f in e2.get("fields", []) if f.get("state") in ("育つ", "実った")],
        "people": people,
        "season": {"jobs": _copy(e2.get("jobs") or {}), "craft_days": _copy(e2.get("craft_days") or {}),
                   "specialists": _copy(e2.get("specialists") or []), "tended_run": e2.get("tended_run"), "step_day": e2.get("step_day"),
                   "rep_mode": rep_mode, "reps": reps},
        "g5": g5,
        "laws": {l["id"]: l.get("status") for l in state.get("laws", [])},
        "year_names": len(e2.get("year_names") or []),
        "notes": _copy(notes) if notes is not None else None,
    }


def append_snapshot(data_dir, row):
    """控えを 1 行足す (書き足すだけ。書きかえない)"""
    d = Path(data_dir) / "records"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / SNAP_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        f.flush()


def load_snapshots(data_dir, state, warn=True):
    """控えを読む。今の出来事の記録とつながっているもの (valid) だけを、日ごとに 1 つ返す。
    同じ日に 2 つ以上あれば、live を git より先に。戻り値: ({日: 行}, 数のまとめ)"""
    f = Path(data_dir) / "records" / SNAP_FILE
    stats = {"valid": 0, "invalid": 0, "malformed": 0, "live": 0, "git": 0}
    best = {}
    if not f.exists():
        return {}, stats
    nxt = state.get("next_event", len(state["events"]))
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            ok = isinstance(row, dict) and isinstance(row.get("day"), int) and isinstance(row.get("event_end"), int)
        except json.JSONDecodeError:
            ok = False
        if not ok:
            stats["malformed"] += 1
            if warn:
                print(f"記録: 控えの {i + 1} 行目が読めない (使わない)", file=sys.stderr)
            continue
        if row["event_end"] > nxt or event_sig(state, row["event_end"] - 1) != row.get("sig"):
            stats["invalid"] += 1  # 取りやめた回や巻き戻した回の控え
            continue
        stats["valid"] += 1
        live = row.get("source") == "live"
        stats["live" if live else "git"] += 1
        key = (live, row["event_end"], json.dumps(row, ensure_ascii=False, sort_keys=True))  # 行の並びによらず同じものを選ぶ
        if row["day"] not in best or key > best[row["day"]][0]:
            best[row["day"]] = (key, row)
    return {d: best[d][1] for d in sorted(best)}, stats
