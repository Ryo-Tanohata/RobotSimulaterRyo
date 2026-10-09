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
import subprocess  # noqa: E402

try:
    import records  # noqa: E402  (ダッシュボードの内側の記録。読むだけで、世界の進み方には使わない)
except Exception as _ex:  # 記録の仕組みがこわれていても、季節は進める
    records = None
    print(f"記録: 記録の仕組みを読めなかった ({type(_ex).__name__}: {_ex})")

DATA = Path(os.environ["SOC_DATA"]) if os.environ.get("SOC_DATA") else Path(__file__).parent / "data"
STATE = DATA / "state.json"
RECORDS_ON = os.environ.get("SOC_RECORDS", "1") != "0"  # 0 なら記録を作らない (試し用)


def load():
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(state):
    DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _snap(state, before, first):
    """季節のあとの控え (records/snapshots.jsonl の 1 行。docs/dashboard_records_spec.md 2.)。state は読むだけ。失敗しても季節は進んだまま"""
    try:  # 書きとめを空にするのも、この中で (失敗で、保存の前に止まらないように)
        notes = era2.take_notes() if hasattr(era2, "take_notes") else None
        if not RECORDS_ON:
            return None
        return records.snapshot(state, meeting_first=before, event_first=first, notes=notes)
    except Exception as ex:  # 記録の失敗で、世界を止めない
        print(f"記録: 季節の終わりの控えを作れなかった ({type(ex).__name__}: {ex})")
        return None


def _records(snap):
    """控えを 1 行足して、記録を作り直す (保存のあと。別のプロセスで動かすので state にさわれない。失敗しても季節は進んだまま。終わりのコードも変えない)"""
    if not RECORDS_ON:
        return
    try:
        if snap:
            records.append_snapshot(DATA, snap)
        sys.stdout.flush()  # 表示の順を保つ (別のプロセスの表示より前に)
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "tools" / "build_records.py"), "--data", str(DATA), "--quiet"],
                           timeout=300)
        if r.returncode:
            print(f"記録: 記録を作れなかった (終わりのコード {r.returncode})。python3 sim/society/tools/build_records.py で作り直せる")
    except Exception as ex:
        print(f"記録: 記録を作れなかった ({type(ex).__name__}: {ex})。python3 sim/society/tools/build_records.py で作り直せる")


def _society2_end(state):
    """G6: 町と記録がそろって、Society 2.0 が終わったか (一時停止のわけ)"""
    return bool(((state.get("era2") or {}).get("g6") or {}).get("end"))


def _yd(day):
    """通しの日 → 「16年90日目 (2009 日目)」(本人に見せる日の書き方。daily_run.md の冒頭)"""
    return f"{day // era2.YEAR}年{day % era2.YEAR + 1}日目 ({day} 日目)"


def pdir(state, phase, kind):
    return DATA / kind / f"day{state['day']:03d}" / phase


def write_prompts(state, phase):
    d = pdir(state, phase, "prompts")
    d.mkdir(parents=True, exist_ok=True)
    who = set(era2.answerers(state)) if phase == "season" else None
    for p in state["people"]:
        if not p["alive"]:
            continue
        if p.get("child") or (who is not None and p["name"] not in who):
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
    if phase == "season" and era2.feelers(state):  # 代表でない大人は、気持ちと一言だけ答える (2026-10-09 本人の希望)
        fd, fa = pdir(state, "feeling", "prompts"), pdir(state, "feeling", "answers")
        fd.mkdir(parents=True, exist_ok=True)
        fa.mkdir(parents=True, exist_ok=True)
        for n in era2.feelers(state):
            p = next(q for q in state["people"] if q["name"] == n)
            (fd / f"{n}.md").write_text(era2.feeling_prompt(state, p, state["era2"].get("last_first", 0)), encoding="utf-8")
        print(f"気持ちのお題: {fd.relative_to(DATA.parent)}  →  答えの置き場所: {fa.relative_to(DATA.parent)}/<名前>.json")


def read_feelings(state):
    """代表でない大人の、気持ちと一言の答え (ない人は、気持ちが前のまま)"""
    d = pdir(state, "feeling", "answers")
    out = {}
    for n in era2.feelers(state):
        f = d / f"{n}.json"
        if f.exists():
            out[n] = f.read_text(encoding="utf-8")
    missing = [n for n in era2.feelers(state) if n not in out]
    if missing:
        print("気持ちの答えがない人:", "、".join(missing))
    return out


def read_answers(state, phase):
    d = pdir(state, phase, "answers")
    out, missing = {}, []
    who = set(era2.answerers(state)) if phase == "season" else None
    for p in state["people"]:
        if not p["alive"] or p.get("child") or (who is not None and p["name"] not in who):
            continue
        f = d / f"{p['name']}.json"
        if f.exists():
            out[p["name"]] = f.read_text(encoding="utf-8")
        else:
            missing.append(p["name"])
    if missing:
        print("答えがない人 (その人は何もしなかった扱い):", "、".join(missing))
    return out


ACT_BY_EVENT = {"採集": "採集", "探索": "探索", "休む": "休む", "道具": "道具づくり", "火": "火おこし", "種まき": "種まき",
                "畑仕事": "畑仕事", "ヤギの世話": "ヤギの世話", "ヤギを捕まえる": "ヤギを捕まえる", "土器": "土器づくり", "住まい": "住まいを建てる",
                "交換に行く": "交換に行く", "記録をつける": "記録をつける"}  # Society 2.0 の仕事 (交換に行く・記録をつけるは G6 から)


def day_summaries(state, extra=()):
    """3D 再生用: 日ごとに、誰がどの活動でどの場所へ行ったか (出来事の記録から組み立てる)"""
    labels = sorted(list(state["places"]) + list(extra), key=lambda p: -len(p["label"]))  # G6: ほかの村へ行く人は、地図の端へ歩く
    out = {}
    for d in range(1, state["day"] + 1):
        rows = {}
        for e in state["events"]:
            if e["day"] != d:
                continue
            names = e.get("data", {}).get("hunters") if e["type"] == "狩り" else [e["who"]]
            # G6: 向こうの村で交換した日も、その村にいる (集まりでの交換は who がない)
            act = "狩り" if e["type"] == "狩り" else "交換に行く" if e["type"] == "交換" and e.get("who") else ACT_BY_EVENT.get(e["type"])
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
    extra = era2.g6_places(state)  # G6: 知っているほかの村の、地図の端の場所 (G6 の前は空)
    left = {f["household"]: f["day"] for f in ((state.get("era2") or {}).get("g5") or {}).get("fissions", [])}  # 村を出た家 (3D でその日から描かない)
    data = {
        "day": state["day"], "season": world.season(max(1, state["day"])), "phase": state["phase"],
        "map": {"w": world.W, "h": world.H, "cell": world.CELL, "terrain": state["terrain"], "legend": world.TERRAIN},
        "camp": state["camp"], "places": state["places"] + extra,
        "plants": [{"x": q["x"], "y": q["y"], "kind": q["kind"], "amount": round(q["amount"], 1), "sown": q.get("sown", False)}
                   for q in state["plants"]],
        "herds": state["herds"], "predators": state["predators"], "planted": state["planted"],
        "people": [{k: p.get(k) for k in ("name", "alive", "age", "sex", "mass", "personality", "skills", "hunger", "fatigue",
                                          "injured", "items", "trust", "plan", "feeling", "feeling_day", "child", "mother", "origin", "left", "household", "born_day")}
                   | {"since": p.get("born_day", 0) if p.get("origin") == "生まれた" else resume._joined_day(state, p["name"]) if p.get("origin") == "よそから来た" else 0}
                   | {"food": sum(f["kcal"] for f in p["food"]), "food_words": world.food_words(world.holdings(p)), "today": p.get("today"),
                      "knowledge": p.get("knowledge", [])} for p in state["people"]],
        "events": ev_recent, "laws": state.get("laws", []),
        "knowledge_log": state.get("knowledge_log", [])[-300:], "stats": state["stats"],
        "days": day_summaries(state, extra),
        "era": state.get("era_info") or {"era": "F1", "name": phase.ERAS["F1"]}, "era_log": state.get("era_log", []),
        "hold": bool(state.get("hold")), "store": world.food_words(phase._store_kinds(state)),
        "resumes": resume.build(state),
        # G の中の小さな区切り F (G1・G2 は記録から決めた日、G3 からは見つけた日)
        "substeps": era2.RETRO_SUBSTEPS + (state.get("era2") or {}).get("substeps", []),
        # 家族の住まい (G3 から): 3D の再生で、家族ごとの家を描く
        # (2026-10-09 本人と決めた: 家ごと村を出た家は、出た日から描かない。left は村を出た家だけにつける)
        "houses": [{"household": h, "x": v["x"], "y": v["y"], "start": v["start"], "built": v["built"], "sizes": v["sizes"]}
                   | ({"left": left[h]} if h in left else {})
                   for h, v in sorted((state.get("era2") or {}).get("homes", {}).items())],
        **({"g6": era2.g6_export(state)} if (state.get("era2") or {}).get("g6") else {}),  # G6: ほかの村・印・記録 (G6 の前は鍵がない)
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
            print("一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち (再開は resume)" if _society2_end(state)
                  else "一時停止中: フェーズが進んだので評価待ち (再開は resume)")
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
            print("一時停止中: Society 2.0 が終わったので、第 4 部のまとめ待ち。進めない (再開は resume)" if _society2_end(state)
                  else f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
            sys.exit(3)
        before = state["next_event"]  # G5: 季節の集まりで起きたこと (収める・裁き・罰・祭り・まとめ役) は、30 日を進める前の出来事
        if hasattr(era2, "take_notes"):
            try:
                era2.take_notes()  # 記録のための書きとめ: 前のものを捨てる
            except Exception as ex:  # 記録の失敗で、世界を止めない
                print(f"記録: 書きとめを空にできなかった ({type(ex).__name__}: {ex})")
        feels = read_feelings(state)  # 代表を決める前の顔ぶれで読む (集まりで、まとめ役が変わることがあるため)
        era2.apply_answers(state, read_answers(state, "season"))
        era2.apply_feelings(state, feels)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        if not any(p["alive"] for p in state["people"]):
            snap = _snap(state, before, first)
            save(state)
            export(state)
            _records(snap)
            gone = [p for p in state["people"] if p.get("left")]
            print("生きている人がいない (亡くなった人と、村を出た人" + (f" {len(gone)} 人" if gone else " 0 人") + ")")
            sys.exit(4)
        r = era2.check(state)
        if r == "end":  # G6: 町と記録がそろった (「フェーズが…に進んだ」とは書かない。"end" も真なので、先に見る)
            state["hold"] = True
            g = state["era2"]["g6"]["end"]
            world.log(state, "フェーズ", None, f"Society 2.0 の終わり: 町 ({g['town']} 日目) と記録 ({g['record']} 日目) がそろった (先にそろったのは {g['first']})")
            print(f"* Society 2.0 が終わった: 町 ({_yd(g['town'])}) と記録 ({_yd(g['record'])}) がそろった → 一時停止 (第 4 部のまとめ待ち)")
        elif r:
            state["hold"] = True
            e = state["era_log"][-1]
            world.log(state, "フェーズ", None, f"フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ")
            print(f"* フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ → 一時停止 (評価待ち)")
        snap = _snap(state, before, first)  # 保存の前に読む (保存するのと同じ state)
        save(state)
        write_prompts(state, "season")
        export(state)
        _records(snap)
        for e in state["events"]:
            if (e["id"] >= first and e["type"] in ("掟", "死", "生まれる", "加わる", "去る", "訪れる", "畑", "ヤギ", "大人になる", "フェーズ", "家族", "虫", "受けつぎ", "区切り")) \
                    or (e["id"] >= before and (e["type"] in era2.G5_EVENTS + era2.G6_EVENTS or e["type"] == "年の名前")):
                print("*", e["text"][:120])
        harv = sum((e.get("data") or {}).get("amount", 0) for e in state["events"] if e["id"] >= first and e["type"] == "収穫")
        if harv:
            print(f"* 畑で刈った草の種: 合わせて {harv} つかみ")
        i = state["era_info"]["indicators"]
        print(f"{state['day']} 日目まで進んだ / 人 {i['population']} (大人 {i['adults']}・子 {i['children']}) / ヤギ {i['goats']} / 育てた食べ物 {i['farm_share']}")
        if i.get("g5_stage"):
            print(f"G5 第 {i['g5_stage']} 段 / 家族 {i['households']} / まとめ役 {i['leader'] or 'いない'} / もめごと 残り {i['disputes_open']} "
                  f"(まとめ役なしで収めた {i['settled']}・まとめ役の裁き {i['judged']}) / 罰のある掟 {i['penalty_laws']}・罰 {i['penalties']} / "
                  f"祭り {i['feasts']} / 分かれた家 {i['fissions']} / 共同の仕事 {i['joint']} / 第 1 段 {'済み' if i['stage1'] else 'まだ'}")
        if i.get("g6_on"):
            print(f"G6 / 人 {i['population']} (大人 {i['adults']}) / 知っている村 {i['g6_known']} (この 4 季節に交換した村 {i['g6_partners']}・いちばん大きい相手 {i['g6_biggest']} 人) / "
                  f"交換の続いた季節 {i['g6_run']} / 交換 {i['g6_exchanges']}・返されていない貸し借り {i['g6_debts_open']} / G6 で加わった人 {i['g6_joined']} / "
                  f"印 {i['g6_seals']} 家・封のかけら {i['g6_sealings']} (封をした季節 {i['g6_seal_seasons']}) / 記録の道具 {i['g6_tools']} / 記録した季節 {i['g6_records']} / "
                  f"確かめた {i['g6_checked']} (板 {i['g6_checked_tablet']})・覚え違い {i['g6_misremember']} / 食べ物をとらない人 {i['g6_nonfood']} / "
                  f"町 {_yd(i['g6_town_day']) if i['g6_town_day'] is not None else 'まだ'} / 記録 {_yd(i['g6_record_day']) if i['g6_record_day'] is not None else 'まだ'}")
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
