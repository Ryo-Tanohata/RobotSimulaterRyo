"""社会シミュレーションを 1 段階ずつ進めるコマンド (スケジュール実行の Claude が使う)。

  python sim/society/step.py init [--seed 1]     新しい世界。0 日目の夜のお題を作る
  python sim/society/step.py status              今どの段階か (次に何をするか) を表示
  python sim/society/step.py day                 1 日を進める → 夕方のお題を作る
  python sim/society/step.py evening             夕方の答えを反映 (話す・分ける・食事・夜の危険) → 夜のお題を作る
  python sim/society/step.py night               夜の答えを反映 (知識・掟・明日の予定) → フェーズの判定 → アプリ用のデータを書き出す
  python sim/society/step.py resume              フェーズが進んで一時停止しているのを解く (本人が評価したあと)

お題は data/prompts/日/段階/名前.md、答えは data/answers/日/段階/名前.json に置く。
段階は state.json の phase に記録するので、途中で止まっても続きから再開できる。
フェーズ (狩猟採集 → 農耕、docs/society_phase_plan.md) が進むと state.json の hold が立ち、day は進まなくなる。
環境変数 SOC_DATA でデータの置き場所を変えられる (試験用)。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import characters  # noqa: E402
import era2  # noqa: E402
import knowledge  # noqa: E402
import phase  # noqa: E402
import resume  # noqa: E402
import world  # noqa: E402

import os  # noqa: E402

DATA = Path(os.environ["SOC_DATA"]) if os.environ.get("SOC_DATA") else Path(__file__).parent / "data"
STATE = DATA / "state.json"


def load():
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(state):
    DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def pdir(state, phase, kind):
    return DATA / kind / f"day{state['day']:03d}" / phase


def write_prompts(state, phase):
    d = pdir(state, phase, "prompts")
    d.mkdir(parents=True, exist_ok=True)
    for p in state["people"]:
        if not p["alive"]:
            continue
        if p.get("child"):
            continue
        if phase == "season":
            text = era2.season_prompt(state, p, state["era2"].get("last_first", 0))
        elif phase == "evening":
            text = characters.evening_prompt(state, p)
        else:
            text = characters.night_prompt(state, p, state.get("tonight", {}).get(p["name"], []),
                                           characters.gifts_for(state, p["name"]))
        (d / f"{p['name']}.md").write_text(text, encoding="utf-8")
    a = pdir(state, phase, "answers")
    a.mkdir(parents=True, exist_ok=True)
    print(f"お題: {d.relative_to(DATA.parent)}  →  答えの置き場所: {a.relative_to(DATA.parent)}/<名前>.json")


def read_answers(state, phase):
    d = pdir(state, phase, "answers")
    out, missing = {}, []
    for p in state["people"]:
        if not p["alive"] or p.get("child"):
            continue
        f = d / f"{p['name']}.json"
        if f.exists():
            out[p["name"]] = f.read_text(encoding="utf-8")
        else:
            missing.append(p["name"])
    if missing:
        print("答えがない人 (その人は何もしなかった扱い):", "、".join(missing))
    return out


ACT_BY_EVENT = {"採集": "採集", "探索": "探索", "休む": "休む", "道具": "道具づくり", "火": "火おこし", "種まき": "種まき"}


def day_summaries(state):
    """3D 再生用: 日ごとに、誰がどの活動でどの場所へ行ったか (出来事の記録から組み立てる)"""
    labels = sorted(state["places"], key=lambda p: -len(p["label"]))
    out = {}
    for d in range(1, state["day"] + 1):
        rows = {}
        for e in state["events"]:
            if e["day"] != d:
                continue
            names = e.get("data", {}).get("hunters") if e["type"] == "狩り" else [e["who"]]
            act = "狩り" if e["type"] == "狩り" else ACT_BY_EVENT.get(e["type"])
            if not act or not names:
                continue
            pid = next((p["id"] for p in labels if p["label"] in e["text"]), "camp")
            for n in names:
                rows.setdefault(n, {"name": n, "activity": act, "place": pid})
        out[d] = list(rows.values())
    return out


def export(state):
    """アプリ (Web ページ) 用のデータ"""
    ev_recent = state["events"]  # すべての日 (過去の日の 3D 再生と動画のため)
    data = {
        "day": state["day"], "season": world.season(max(1, state["day"])), "phase": state["phase"],
        "map": {"w": world.W, "h": world.H, "cell": world.CELL, "terrain": state["terrain"], "legend": world.TERRAIN},
        "camp": state["camp"], "places": state["places"],
        "plants": [{"x": q["x"], "y": q["y"], "kind": q["kind"], "amount": round(q["amount"], 1), "sown": q.get("sown", False)}
                   for q in state["plants"]],
        "herds": state["herds"], "predators": state["predators"], "planted": state["planted"],
        "people": [{k: p.get(k) for k in ("name", "alive", "age", "sex", "mass", "personality", "skills", "hunger", "fatigue",
                                          "injured", "items", "trust", "plan", "feeling", "child", "mother", "origin", "left")}
                   | {"food": sum(f["kcal"] for f in p["food"]), "food_words": world.food_words(world.holdings(p)), "today": p.get("today"),
                      "knowledge": p.get("knowledge", [])} for p in state["people"]],
        "events": ev_recent, "laws": state.get("laws", []),
        "knowledge_log": state.get("knowledge_log", [])[-300:], "stats": state["stats"],
        "days": day_summaries(state),
        "era": state.get("era_info") or {"era": "F1", "name": phase.ERAS["F1"]}, "era_log": state.get("era_log", []),
        "hold": bool(state.get("hold")), "store": world.food_words(phase._store_kinds(state)),
        "resumes": resume.build(state),
    }
    (DATA / "app_data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("アプリ用のデータ:", (DATA / "app_data.json").relative_to(DATA.parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "status", "day", "evening", "night", "export", "resume", "start2", "season"])
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--force", action="store_true", help="init で既存の世界を上書きする")
    a = ap.parse_args()

    if a.cmd == "init":
        if STATE.exists() and not a.force:
            sys.exit("世界はもうある (上書きするなら --force)")
        state = world.generate(a.seed)
        knowledge.init(state)
        state["phase"] = "night"
        state["tonight"] = {}
        save(state)
        write_prompts(state, "night")
        export(state)
        return

    state = load()
    if a.cmd == "status":
        nxt = {"day": "day (1 日を進める)", "evening": "夕方の答えを集めて evening", "night": "夜の答えを集めて night",
               "season": "季節の答えを集めて season (30 日進む)"}[state["phase"]]
        alive = [p["name"] for p in state["people"] if p["alive"]]
        print(f"{state['day']} 日目 / 段階 {state['phase']} / 次: {nxt} / 生きている人: {'、'.join(alive)}")
        info = state.get("era_info") or {}
        era = state.get("era", "F1")
        print(f"フェーズ: {era} {phase.ERAS.get(era) or era2.NAMES2.get(era)} / 次の条件: {info.get('next', '-')}")
        if state.get("hold"):
            print("一時停止中: フェーズが進んだので評価待ち (再開は resume)")
        if state["phase"] in ("evening", "night", "season"):
            print(f"お題: {pdir(state, state['phase'], 'prompts').relative_to(DATA.parent)}")
        return
    if a.cmd == "export":
        export(state)
        return
    if a.cmd == "resume":
        state["hold"] = False
        save(state)
        export(state)
        print("再開した")
        return
    if a.cmd == "start2":  # Society 2.0 を始める (F6 の世界を引きつぐ)
        if state.get("era2"):
            sys.exit("Society 2.0 はもう始まっている")
        era2.start(state)
        state["era2"]["last_first"] = state["next_event"]
        era2.check(state)
        save(state)
        write_prompts(state, "season")
        export(state)
        return
    if a.cmd == "season":
        if state["phase"] != "season":
            sys.exit(f"今の段階は {state['phase']} です")
        if state.get("hold"):
            print(f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
            sys.exit(3)
        era2.apply_answers(state, read_answers(state, "season"))
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        if not any(p["alive"] for p in state["people"]):
            save(state)
            export(state)
            gone = [p for p in state["people"] if p.get("left")]
            print("生きている人がいない (亡くなった人と、村を出た人" + (f" {len(gone)} 人" if gone else " 0 人") + ")")
            sys.exit(4)
        if era2.check(state):
            state["hold"] = True
            e = state["era_log"][-1]
            world.log(state, "フェーズ", None, f"フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ")
            print(f"* フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ → 一時停止 (評価待ち)")
        save(state)
        write_prompts(state, "season")
        export(state)
        for e in state["events"]:
            if e["id"] >= first and e["type"] in ("掟", "死", "生まれる", "加わる", "去る", "訪れる", "収穫", "ヤギ", "大人になる", "フェーズ"):
                print("*", e["text"][:120])
        i = state["era_info"]["indicators"]
        print(f"{state['day']} 日目まで進んだ / 人 {i['population']} (大人 {i['adults']}・子 {i['children']}) / ヤギ {i['goats']} / 育てた食べ物 {i['farm_share']}")
        return
    if a.cmd == "day" and not any(p["alive"] for p in state["people"]):
        print("生きている人がいないので、進めない")
        sys.exit(4)
    if a.cmd == "day" and state.get("hold"):
        print(f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
        sys.exit(3)
    if a.cmd != state["phase"]:
        sys.exit(f"今の段階は {state['phase']} です ({a.cmd} はまだできない)")

    if a.cmd == "day":
        ids = world.simulate_day(state)
        print(f"{state['day']} 日目: 出来事 {len(ids)} 件")
        state["phase"] = "evening"
        save(state)
        write_prompts(state, "evening")
    elif a.cmd == "evening":
        gives, tonight, stores, takes = characters.apply_evening(state, read_answers(state, "evening"))
        world.evening(state, gives, stores, takes)
        state["tonight"] = {n: h for n, h in tonight.items()}
        state["phase"] = "night"
        save(state)
        write_prompts(state, "night")
    elif a.cmd == "night":
        characters.apply_night(state, read_answers(state, "night"))
        state["phase"] = "day"
        state["tonight"] = {}
        if phase.check(state):
            state["hold"] = True
            e = state["era_log"][-1]
            world.log(state, "フェーズ", None, f"フェーズが {e['era']} ({phase.ERAS[e['era']]}) に進んだ")
            print(f"* フェーズが {e['era']} ({phase.ERAS[e['era']]}) に進んだ → 一時停止 (評価待ち)")
        save(state)
        export(state)
        for e in state["events"]:
            if e["day"] == state["day"] and e["type"] in ("掟", "死", "育つ"):
                print("*", e["text"])


if __name__ == "__main__":
    main()
