"""社会シミュレーションを 1 段階ずつ進めるコマンド (スケジュール実行の Claude が使う)。

  python sim/society/step.py init [--seed 1]     新しい世界。0 日目の夜のお題を作る
  python sim/society/step.py status              今どの段階か (次に何をするか) を表示
  python sim/society/step.py day                 1 日を進める → 夕方のお題を作る
  python sim/society/step.py evening             夕方の答えを反映 (話す・分ける・食事・夜の危険) → 夜のお題を作る
  python sim/society/step.py night               夜の答えを反映 (知識・掟・明日の予定) → アプリ用のデータを書き出す

お題は data/prompts/日/段階/名前.md、答えは data/answers/日/段階/名前.json に置く。
段階は state.json の phase に記録するので、途中で止まっても続きから再開できる。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import characters  # noqa: E402
import knowledge  # noqa: E402
import world  # noqa: E402

DATA = Path(__file__).parent / "data"
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
        if phase == "evening":
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
        if not p["alive"]:
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
    ev_recent = [e for e in state["events"] if e["day"] >= state["day"] - 30]
    data = {
        "day": state["day"], "season": world.season(max(1, state["day"])), "phase": state["phase"],
        "map": {"w": world.W, "h": world.H, "cell": world.CELL, "terrain": state["terrain"], "legend": world.TERRAIN},
        "camp": state["camp"], "places": state["places"],
        "plants": [{"x": q["x"], "y": q["y"], "kind": q["kind"], "amount": round(q["amount"], 1), "sown": q.get("sown", False)}
                   for q in state["plants"]],
        "herds": state["herds"], "predators": state["predators"], "planted": state["planted"],
        "people": [{k: p.get(k) for k in ("name", "alive", "age", "sex", "mass", "personality", "skills", "hunger", "fatigue",
                                          "injured", "items", "trust", "plan", "feeling")}
                   | {"food": sum(f["kcal"] for f in p["food"]), "food_words": world.food_words(world.holdings(p)), "today": p.get("today"),
                      "knowledge": p.get("knowledge", [])} for p in state["people"]],
        "events": ev_recent, "laws": state.get("laws", []),
        "knowledge_log": state.get("knowledge_log", [])[-300:], "stats": state["stats"],
        "days": day_summaries(state),
    }
    (DATA / "app_data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("アプリ用のデータ:", (DATA / "app_data.json").relative_to(DATA.parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "status", "day", "evening", "night", "export"])
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
        nxt = {"day": "day (1 日を進める)", "evening": "夕方の答えを集めて evening", "night": "夜の答えを集めて night"}[state["phase"]]
        alive = [p["name"] for p in state["people"] if p["alive"]]
        print(f"{state['day']} 日目 / 段階 {state['phase']} / 次: {nxt} / 生きている人: {'、'.join(alive)}")
        if state["phase"] in ("evening", "night"):
            print(f"お題: {pdir(state, state['phase'], 'prompts').relative_to(DATA.parent)}")
        return
    if a.cmd == "export":
        export(state)
        return
    if a.cmd != state["phase"]:
        sys.exit(f"今の段階は {state['phase']} です ({a.cmd} はまだできない)")

    if a.cmd == "day":
        ids = world.simulate_day(state)
        print(f"{state['day']} 日目: 出来事 {len(ids)} 件")
        state["phase"] = "evening"
        save(state)
        write_prompts(state, "evening")
    elif a.cmd == "evening":
        gives, tonight = characters.apply_evening(state, read_answers(state, "evening"))
        world.evening(state, gives)
        state["tonight"] = {n: h for n, h in tonight.items()}
        state["phase"] = "night"
        save(state)
        write_prompts(state, "night")
    elif a.cmd == "night":
        characters.apply_night(state, read_answers(state, "night"))
        state["phase"] = "day"
        state["tonight"] = {}
        save(state)
        export(state)
        for e in state["events"]:
            if e["day"] == state["day"] and e["type"] in ("掟", "死", "育つ"):
                print("*", e["text"])


if __name__ == "__main__":
    main()
