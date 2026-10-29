"""社会シミュレーションを 1 段階ずつ進めるコマンド (スケジュール実行の Claude が使う)。

  python sim/society/step.py init [--seed 1]     新しい世界。0 日目の夜のお題を作る
  python sim/society/step.py status              今どの段階か (次に何をするか) を表示
  python sim/society/step.py day                 1 日を進める → 夕方のお題を作る
  python sim/society/step.py evening             夕方の答えを反映 (話す・分ける・食事・夜の危険) → 夜のお題を作る
  python sim/society/step.py night               夜の答えを反映 (知識・掟・明日の予定) → フェーズの判定 → アプリ用のデータを書き出す
  python sim/society/step.py resume              フェーズが進んで一時停止しているのを解く (本人が評価したあと)
  python sim/society/step.py ask_why [on|off]    季節のお題で、主な仕事にした理由を一言たずねる (off でやめる。理由は世界の計算には使わない)
  python sim/society/step.py next_part [--fill F] 部の終わり (か次の G を待つ) で止まっているときだけ、次の部 (次の G) に入る (本人と決めてから 1 回だけ。
                                                 G7 なら F は地域の人数を K の何割にするか。書かなければ 0 = 今のまま、集落を置かない)
  python sim/society/step.py next_part --closed-by-decision "<本人の言葉>" [--fill F]
                                                 G6 を、町の条件がそろわないまま本人の決めで閉じたとき (2026-10-17) に、G7 に入る。
                                                 閉じたことを出来事「フェーズ」と g6.closed に残してから入る (止まっていなくてよい。G6 のときだけ)
                                                 G7 から G8 (g7.closed)、G8 から G9 (2026-10-29。g7.closed8。重い押しを切り、G9 の仕組みを入れる) も同じ形
  python sim/society/step.py heavy on             G8 の続き「重い押し」を入れる (2026-10-25 本人の決め。docs/society_phase/G8_heavy_design.md。G8 のときだけ。
                                                 入れたら消さない)。強い集落の村への求めを「村の去年の刈り入れの 2 割」にする。年の集まりの歩で、
                                                 まだ答えがなければ、その日に「増やせ」の求めを出して、お題を書き直す (ほかの日なら、次の年の終わりに出す)
  python sim/society/step.py far_rate 0.5         G9 の遠くの町の運ぶ人の 1 年の見込み (重み。はじめ 0.1) を、今日から 0.5 にする (2026-10-29 本人の決め「来る見込みを 5 割に」。
                                                 G9 のときだけ。同じ重みなら何も変えない)。g7.g9.far_rate と出来事「目盛り」(村は見ない) に残す。年の終わりの日に
                                                 次の年の便りをもう引いていれば、差の分だけ遠くの商人を引き足す (別の乱数の列)。お題は変わらない
  python sim/society/step.py who                 ワークフローのための、読むだけの状態の行 (DAY・PHASE・HOLD・MODE・MEET・NAMES・FEEL・COUNCIL・ASKLOG)

お題は data/prompts/日/段階/名前.md、答えは data/answers/日/段階/名前.json に置く。
段階は state.json の phase に記録するので、途中で止まっても続きから再開できる。
フェーズ (狩猟採集 → 農耕、docs/society_phase_plan.md) が進むと state.json の hold が立ち、day は進まなくなる。
環境変数 SOC_DATA でデータの置き場所を変えられる (試験用)。
古い年の記録 (出来事など) は data/archive/ の年ごとのファイルにしまう (2026-10-10。archive.py。1 回だけの移行 tools/archive_records.py のあと、
季節の終わりに 1 年分ずつ。SOC_ARCHIVE=0 で止められる)。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import archive  # noqa: E402
import characters  # noqa: E402
import era2  # noqa: E402
import knowledge  # noqa: E402
import phase  # noqa: E402
import resume  # noqa: E402
import world  # noqa: E402

import hashlib  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

try:
    import records  # noqa: E402  (ダッシュボードの内側の記録。読むだけで、世界の進み方には使わない)
except Exception as _ex:  # 記録の仕組みがこわれていても、季節は進める
    records = None
    print(f"記録: 記録の仕組みを読めなかった ({type(_ex).__name__}: {_ex})")

DATA = Path(os.environ["SOC_DATA"]) if os.environ.get("SOC_DATA") else Path(__file__).parent / "data"
STATE = DATA / "state.json"
RECORDS_ON = os.environ.get("SOC_RECORDS", "1") != "0"  # 0 なら記録を作らない (試し用)
RECORDS_FAILED = []  # この歩で記録 (控え・作り直し) に失敗したわけ。歩の終わりに「RECORDS failed」の 1 行と終わりのコード 6 で知らせる (_records_exit)
ARCHIVE_ON = os.environ.get("SOC_ARCHIVE", "1") != "0"  # 0 なら古い年をしまわない (試し用)


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
        RECORDS_FAILED.append("snapshot")
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
            RECORDS_FAILED.append(f"build {r.returncode}")
    except Exception as ex:
        print(f"記録: 記録を作れなかった ({type(ex).__name__}: {ex})。python3 sim/society/tools/build_records.py で作り直せる")
        RECORDS_FAILED.append(type(ex).__name__)


def _records_exit():
    """記録に失敗していたら、機械用の 1 行「RECORDS failed …」を行の頭から出して、終わりのコード 6 で終わる (世界は進んで保存したまま)。
    2026-10-22: 前は表示だけで終わりのコードが 0 のままだったので、ワークフロー (tools/society2_seasons_workflow.js) が古い記録のままコミットして進んでいた"""
    if RECORDS_FAILED:
        print("RECORDS failed " + " ".join(x.replace(" ", "_") for x in RECORDS_FAILED))
        sys.exit(6)


def _archive(state):
    """年が変わっていれば、古い年の記録を data/archive/ の年ごとのファイルに移す (保存の前。1 回だけの移行のあと ("archive" がある) だけ。
    失敗しても季節は進んだまま。state はしまう前のまま)"""
    if not ARCHIVE_ON or "archive" not in state:
        return
    try:
        ys = archive.move(state, DATA)
        if ys:
            print(f"記録: {ys[0]}年" + (f"〜{ys[-1]}年" if len(ys) > 1 else "") + f"の記録を {DATA.name}/{archive.DIR}/ にしまった")
    except Exception as ex:  # しまえなくても、世界を止めない
        print(f"記録: 古い年をしまえなかった ({type(ex).__name__}: {ex})。state.json はしまう前のまま")


def _hold_text(state):
    """一時停止のわけ: (HOLD の言葉, 人が読む文)。止まっていなければ (None, "")。G6 は g6.end、G7 からは e2.g7.hold を見る (era2.hold_why)"""
    if not state.get("era2"):
        return ("phase", f"フェーズ {state.get('era')} に進んだので評価待ち (再開は resume)") if state.get("hold") else (None, "")
    return era2.hold_why(state)


def _next_part_refusal(state, fill, closed=None):
    """next_part ができないわけ (できるなら None)。docs/society_phase/G7_design.md 4.E.1 の 1。
    closed: G6 を本人の決めで閉じたときの本人の言葉 (このときは止まっていなくてよい。G6 で、町がそろっていないときだけ)"""
    if not state.get("era2") or state["phase"] != "season":
        return f"段階が season でない (今は {state['phase']})"
    if closed is not None:
        if not closed.strip():
            return "--closed-by-decision に本人の言葉がない"
        g7s = (state["era2"].get("g7") or {})
        if not ((state.get("era") == "G6" and not g7s) or (state.get("era") in ("G7", "G8") and g7s)):  # 2026-10-25: G7 から G8 も。2026-10-29: G8 から G9 も
            return f"本人の決めで閉じて入れるのは G6 から G7、G7 から G8、G8 から G9 だけ (今は {state.get('era')})"
        if state.get("hold"):
            return "一時停止している (部の終わりなら --closed-by-decision なしの next_part で入る)"
        if state["era"] == "G6" and ((state["era2"].get("g6") or {}).get("end") or (state["era2"].get("g6") or {}).get("closed")):
            return "G6 はもう閉じている"
        if state["era"] == "G7" and (g7s.get("closed") or g7s.get("ends")):
            return "G7 はもう閉じている"
        if state["era"] == "G8" and (g7s.get("closed8") or "G8" in (g7s.get("ends") or {})):
            return "G8 はもう閉じている"
    elif not state.get("hold"):
        return "一時停止していない"
    code, why = _hold_text(state)
    if code == "entrance":
        return "工業の入口では、次の部には進まない (Society 2.0 のまとめと、その先を本人と相談する)"
    if code not in ("part_end", "wait") and closed is None:
        return f"部の終わりか次の G を待つで止まっていない ({why})"
    i = era2.ORDER2.index(state["era"])
    if i + 1 >= len(era2.ORDER2):
        return f"次の G ({state['era']} の次) のコードがまだない"
    nxt = era2.ORDER2[i + 1]
    have = [f.name for kind in ("season", "feeling") for f in sorted(pdir(state, kind, "answers").glob("*.json"))]
    if have:
        return f"{state['day']} 日目の答えがもうある ({len(have)} 通。前の部のお題への答え)"
    if fill is not None and nxt != "G7":
        return "--fill は G7 に入るときだけ"
    if fill is not None and not 0 <= fill <= 0.9:
        return f"--fill は 0 から 0.9 まで (今 {fill})"
    if nxt == "G7":
        import g7  # noqa: E402
        return g7.can_enter(state)
    return None


def region_dist(o):
    import region  # noqa: E402
    return region.dist(tuple(o["cell"]), region.VILLAGE)


def _yd(day):
    """通しの日 → 「16年90日目 (2009 日目)」(本人に見せる日の書き方。daily_run.md の冒頭)"""
    return f"{day // era2.YEAR}年{day % era2.YEAR + 1}日目 ({day} 日目)"


def pdir(state, phase, kind):
    return DATA / kind / f"day{state['day']:03d}" / phase


def _g7(state):
    """G7 から働く仕組み (g7.py)。G7 に入ったあと (state["era2"] に "g7" がある) だけ読みこむ。G6 までは None"""
    if "g7" not in (state.get("era2") or {}):
        return None
    import g7  # noqa: E402
    return g7


def write_prompts(state, phase):
    g7 = _g7(state) if phase == "season" else None
    if g7 and not state["era2"]["g7"].get("ask"):  # G7: 集まりのない季節はお題を書かない (年の予定と方針で進む。docs/society_phase/G7_design.md 4.A.2)
        print("お題: この季節は集まらない (年の集まりの予定と方針で進む)。次: season")
        return
    first = g7.since(state) if g7 else (state.get("era2") or {}).get("last_first", 0)  # G7: この前の集まりの歩から
    d = pdir(state, phase, "prompts")
    d.mkdir(parents=True, exist_ok=True)
    who = set(era2.answerers(state)) if phase == "season" else None
    for p in state["people"]:
        if not p["alive"]:
            continue
        if p.get("child") or (who is not None and p["name"] not in who):
            continue
        if phase == "season":
            text = (g7.year_prompt(state, p, first) if g7 and state["era2"]["g7"]["ask"] == "年"  # G7 の年の集まり (寄る季節は季節のお題)
                    else era2.season_prompt(state, p, first))
        elif phase == "evening":
            text = characters.evening_prompt(state, p)
        else:
            text = characters.night_prompt(state, p, state.get("tonight", {}).get(p["name"], []),
                                           characters.gifts_for(state, p["name"]))
        (d / f"{p['name']}.md").write_text(text, encoding="utf-8")
    a = pdir(state, phase, "answers")
    a.mkdir(parents=True, exist_ok=True)
    print(f"お題: {d.relative_to(DATA.parent)}  →  答えの置き場所: {a.relative_to(DATA.parent)}/<名前>.json")
    if g7 and phase == "season":  # G7: まわりの集落の集まり (分かれ目の年だけ、集落ごとに 1 体。docs/society_phase/G7_design.md 4.B.6)
        ask = ((state["era2"]["g7"].get("region") or {}).get("councils") or {}).get("ask") or []
        if ask and (state["era2"]["g7"]["region"]["councils"].get("day") == state["day"]):
            cd, ca = pdir(state, "council", "prompts"), pdir(state, "council", "answers")
            cd.mkdir(parents=True, exist_ok=True)
            ca.mkdir(parents=True, exist_ok=True)
            for sid in ask:
                (cd / f"{sid}.md").write_text(g7.council_prompt(state, sid), encoding="utf-8")
            print(f"集まりのお題: {cd.relative_to(DATA.parent)}  →  答えの置き場所: {ca.relative_to(DATA.parent)}/<番号>.json ({len(ask)} 通)")
    if phase == "season" and era2.feelers(state):  # 代表でない大人は、気持ちと一言だけ答える (2026-10-09 本人の希望)
        fd, fa = pdir(state, "feeling", "prompts"), pdir(state, "feeling", "answers")
        fd.mkdir(parents=True, exist_ok=True)
        fa.mkdir(parents=True, exist_ok=True)
        for n in era2.feelers(state):
            p = next(q for q in state["people"] if q["name"] == n)
            (fd / f"{n}.md").write_text(era2.feeling_prompt(state, p, first), encoding="utf-8")
        print(f"気持ちのお題: {fd.relative_to(DATA.parent)}  →  答えの置き場所: {fa.relative_to(DATA.parent)}/<名前>.json")


def read_councils(state):
    """まわりの集落の集まりの答え {番号: 答えの文} (G7。分かれ目の年だけ。ない集落は決まりの手)"""
    c = (((state.get("era2") or {}).get("g7") or {}).get("region") or {}).get("councils") or {}
    if c.get("day") != state["day"]:
        return {}
    d = pdir(state, "council", "answers")
    out = {sid: (d / f"{sid}.json").read_text(encoding="utf-8") for sid in c.get("ask", []) if (d / f"{sid}.json").exists()}
    missing = [sid for sid in c.get("ask", []) if sid not in out]
    if missing:
        print("集まりの答えがない集落 (決まりで選ぶ):", "、".join(missing))
    return out


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
                "交換に行く": "交換に行く", "記録をつける": "記録をつける",
                "守る": "守る", "取り立てる": "取り立てる", "戦に出る": "戦に出る", "試す": "試す"}  # Society 2.0 の仕事 (交換に行く・記録をつけるは G6 から、後ろの 4 つは G7 から)


def day_labels(state, extra=()):
    return sorted(list(state["places"]) + list(extra), key=lambda p: -len(p["label"]))  # G6: ほかの村へ行く人は、地図の端へ歩く


def day_summaries(state, extra=(), days=None):
    """3D 再生用: 日ごとに、誰がどの活動でどの場所へ行ったか (出来事の記録から組み立てる)。days: 作る日 (なければ 1 日目から今日まで)
    (2026-10-10: 出来事を日ごとに分けてから組み立てる。前は 日 × 出来事 を見て 1 分以上かかった。中身は前と同じ)"""
    labels = day_labels(state, extra)
    by_day = {}
    for e in state["events"]:
        by_day.setdefault(e["day"], []).append(e)
    out = {}
    for d in (range(1, state["day"] + 1) if days is None else days):
        rows = {}
        for e in by_day.get(d, ()):
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


def _export_archive(whole, extra, upto):
    """しまった年の、アプリ用の目次 (年ごとの出来事の数) と、3D の再生がどの日でも使う出来事 (亡くなった・畑にまいた・住まいができた)。
    しまった年の再生の行は data/archive/days_YYYY.json に書く (まだないか、場所の名前が変わったときだけ。その年をしまうとき archive.move が前のものを消すので、
    state.json を戻してやり直した世界でも作り直す。出来事は events_YYYY.jsonl をそのまま読む)"""
    since = (upto + 1) * era2.YEAR
    labels = day_labels(whole, extra)
    sig = hashlib.sha1(json.dumps([[p["id"], p["label"]] for p in labels], ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    count, keep = {}, []
    for e in whole["events"]:
        if e["day"] >= since:
            break
        count[e["day"] // era2.YEAR] = count.get(e["day"] // era2.YEAR, 0) + 1
        if e["type"] == "死" or (e["type"] == "畑" and "をまいた" in e["text"]) or (e["type"] == "住まい" and "住まいができた" in e["text"]):
            keep.append(e)  # replay3d.js の 亡くなった日・畑 (sowings)・住まい (built) と同じ選び方
    todo = []
    for y in range(upto + 1):
        f = archive.days_path(DATA, y)
        try:
            ok = json.loads(f.read_text(encoding="utf-8")).get("labels") == sig
        except (OSError, ValueError):
            ok = False
        if not ok:
            todo.append(y)
    if todo:
        rows = day_summaries(whole, extra, [d for y in todo for d in range(max(1, y * era2.YEAR), (y + 1) * era2.YEAR)])
        for y in todo:
            f = archive.days_path(DATA, y)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({"labels": sig, "days": {d: rows[d] for d in range(max(1, y * era2.YEAR), (y + 1) * era2.YEAR)}},
                                    ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"upto": upto, "since": since, "dir": archive.DIR + "/",
            "years": [{"year": y, "first_day": max(1, y * era2.YEAR), "last_day": (y + 1) * era2.YEAR - 1, "events": count.get(y, 0)}
                      for y in range(upto + 1)],
            "keep": keep}


def export(state):
    """アプリ (Web ページ) 用のデータ。古い年をしまったあと (2026-10-10) は、しまっていない年の出来事と再生の行だけを入れ、
    しまった年の分は、アプリがその年を見るときに data/archive/ の年ごとのファイル (events_YYYY.jsonl・days_YYYY.json) を読む"""
    whole = archive.full(state, DATA)  # 履歴書・グラフ・知識の移り変わりは、しまった年もふくめた全部から (しまう前と同じ)
    upto = (state.get("archive") or {}).get("upto", -1)
    since = (upto + 1) * era2.YEAR  # この日からの出来事と再生の行を app_data.json に入れる
    ev_recent = [e for e in whole["events"] if e["day"] >= since]  # しまっていない年のすべての日 (過去の日の 3D 再生と動画のため)
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
                   | {"since": p.get("born_day", 0) if p.get("origin") == "生まれた" else resume._joined_day(whole, p["name"]) if p.get("origin") == "よそから来た" else 0}
                   | {"food": sum(f["kcal"] for f in p["food"]), "food_words": world.food_words(world.holdings(p)), "today": p.get("today"),
                      "knowledge": p.get("knowledge", [])} for p in state["people"]],
        # 掟の投票の記録 (vote_log) はアプリが使わないので入れない (2026-10-10。12 MB あった)
        "events": ev_recent, "laws": [{k: v for k, v in law.items() if k != "vote_log"} for law in state.get("laws", [])],
        "knowledge_log": whole.get("knowledge_log", [])[-300:], "stats": whole["stats"],
        "days": day_summaries(whole, extra, range(max(1, since), state["day"] + 1)),
        "era": state.get("era_info") or {"era": "F1", "name": phase.ERAS["F1"]}, "era_log": state.get("era_log", []),
        "hold": bool(state.get("hold")), "store": world.food_words(phase._store_kinds(state)),
        "resumes": resume.build(whole),
        # G の中の小さな区切り F (G1・G2 は記録から決めた日、G3 からは見つけた日)
        "substeps": era2.RETRO_SUBSTEPS + (state.get("era2") or {}).get("substeps", []),
        # 家族の住まい (G3 から): 3D の再生で、家族ごとの家を描く
        # (2026-10-09 本人と決めた: 家ごと村を出た家は、出た日から描かない。left は村を出た家だけにつける)
        "houses": [{"household": h, "x": v["x"], "y": v["y"], "start": v["start"], "built": v["built"], "sizes": v["sizes"]}
                   | ({"left": left[h]} if h in left else {})
                   for h, v in sorted((state.get("era2") or {}).get("homes", {}).items())],
        **({"g6": era2.g6_export(state)} if (state.get("era2") or {}).get("g6") else {}),  # G6: ほかの村・印・記録 (G6 の前は鍵がない)
        **({"hold_why": _hold_text(state)[1]} if (state.get("era2") or {}).get("g7") else {}),  # G7 から: 一時停止のわけ (G6 までは鍵を足さない)
        # しまった年の目次 (古い年をしまう前は鍵がない)。アプリは「archive/」を app_data.json と同じ場所から読む
        **({"archive": _export_archive(whole, extra, upto)} if upto >= 0 else {}),
    }
    (DATA / "app_data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("アプリ用のデータ:", (DATA / "app_data.json").relative_to(DATA.parent))


FAR_RATE_NOTE = "本人の決め 2026-10-29: 来る見込みを 5 割に"  # step.py far_rate の記録の言葉


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "status", "day", "evening", "night", "export", "resume", "start2", "season", "ask_why", "next_part", "who", "cards", "heavy", "far_rate"])
    ap.add_argument("onoff", nargs="?", help="ask_why で、たずねる (on。書かなければ on) か、やめる (off)。cards では、札の表を直したわけ (note)。heavy では on。far_rate では重み (0.5 など)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--force", action="store_true", help="init で既存の世界を上書きする")
    ap.add_argument("--closed-by-decision", dest="closed", default=None,
                    help="next_part で、G6 を本人の決めで閉じて G7 に入るとき: 本人の言葉 (記録に残す)")
    ap.add_argument("--fill", type=float, default=None,
                    help="next_part で G7 に入るとき: 地域の人数 (村を除く) を、暮らせる人数 K の合計の何割にするか (0〜0.9。書かなければ 0 = 今のまま)")
    ap.add_argument("--world", default=None,
                    help="next_part で G7 に入るとき (2026-10-24。実験 C): 世界の選び。desert (草原を砂地に) と no_flee (逃げ場なし) をコンマでつなぐ")
    ap.add_argument("--count", default=None, help="next_part で G7 に入るとき (2026-10-24。実験 C): 決める段の数え方 (v2 = 村もまわりの集落と同じに数える)")
    a = ap.parse_args()
    if (a.world is not None or a.count is not None) and a.cmd != "next_part":
        sys.exit("--world と --count は next_part のときだけ書く")
    if a.onoff and a.cmd not in ("ask_why", "cards", "heavy", "far_rate"):
        sys.exit(f"on / off は ask_why のときだけ書く ({a.cmd} {a.onoff} とは書けない)")
    if a.cmd == "ask_why" and a.onoff not in (None, "on", "off"):
        sys.exit(f"ask_why には on か off を書く ({a.onoff} とは書けない)")
    if a.fill is not None and a.cmd != "next_part":
        sys.exit("--fill は next_part のときだけ書く")
    if a.closed is not None and a.cmd != "next_part":
        sys.exit("--closed-by-decision は next_part のときだけ書く")

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
            print(f"一時停止中: {_hold_text(state)[1]}")
        g7 = (state.get("era2") or {}).get("g7")
        if g7:  # G7 から: 次の答え (年 1 回の答え。docs/society_phase/G7_design.md 4.A.2) と、G7 の行
            ask = {"年": "年の集まり", "寄る": "寄る季節", "集まり直し": "集まり直し", "秋": "秋の集まり"}.get(g7.get("ask"), "いらない")
            fl = (g7.get("region") or {}).get("fill")
            print(f"次の答え: {ask} / G7 に入った日 {_yd(g7['start'])} / 史実のずれの直し {g7['fix_from']} 日目から / "
                  f"まわりの集落 {len(era2._g6(state)['others'])} (はじめに置いた集落 {len(fl['placed']) if fl else 0})"
                  + (f" / 世界の選び {'・'.join(sorted(g7['world']))}" if g7.get("world") else "") + (f" / 段の数え方 {g7['count']}" if g7.get("count") else "")
                  + (f" / 重い押し {_yd(g7['heavy']['day'])}から (去年の刈り入れの {round(g7['heavy']['share'] * 10)} 割)"
                     + (f"、{_yd(g7['heavy']['end'])}に切った" if g7["heavy"].get("end") is not None else "") if g7.get("heavy") else ""))
        fr = ((g7 or {}).get("g9") or {}).get("far_rate")
        if fr:  # G9: 遠くの町の運ぶ人の重みを切り替えた (2026-10-29 本人の決め。step.py far_rate)
            print(f"遠くの町の運ぶ人の重み: {fr[-1]['rate']} ({_yd(fr[-1]['day'])}から。前は {fr[-1]['was']})")
        if state.get("era2"):  # 仕事の理由 (段階 1。2026-10-14 本人が決めた: 次に村を進めるときから。daily_run.md)
            log = state["era2"].get("ask_why_log")
            print(f"仕事の理由: {'たずねている' if state['era2'].get('ask_why') else 'たずねていない'} ({log[-1][0]} 日目のお題から)" if log
                  else "仕事の理由: まだ始めていない (村を進める前に step.py ask_why を 1 回動かす)")
        if state["phase"] in ("evening", "night", "season"):
            print(f"お題: {pdir(state, state['phase'], 'prompts').relative_to(DATA.parent)}")
        return
    if a.cmd == "export":
        export(state)
        return
    if a.cmd == "resume":
        code, why = _hold_text(state)
        if code in ("part_end", "wait", "entrance"):  # 部の終わり・待ち・入口では resume しない (G6 のまま止まらずに進まないように。4.E.2)
            print(f"一時停止中: {why}。resume では進めない (何も変えない)" + ("。次へは next_part (本人と決めてから)" if code != "entrance" else ""))
            sys.exit(3)
        state["hold"] = False
        if (state.get("era2") or {}).get("g7"):
            state["era2"]["g7"]["hold"] = None
        save(state)
        export(state)
        print("再開した")
        return
    if a.cmd == "who":  # 読むだけ (ワークフローのため。docs/society_phase/G7_design.md 4.E.5)
        e2 = state.get("era2") or {}
        g7 = e2.get("g7")
        code = _hold_text(state)[0]
        season_ok = bool(e2) and state["phase"] == "season"
        print(f"DAY {state['day']} {state['phase']} {bool(state.get('hold'))}")
        print(f"PHASE {state.get('era')}")
        print(f"HOLD {code or 'none'}")
        print(f"MODE {'year' if g7 else 'season'}")
        print(f"MEET {(g7.get('ask') or 'none') if g7 else '季節' if season_ok else 'none'}")
        meet = season_ok and (not g7 or bool(g7.get("ask")))  # G7: 答える人がいるのは集まりの歩だけ
        print("NAMES " + (" ".join(era2.answerers(state)) if meet else ""))
        print("FEEL " + (" ".join(era2.feelers(state)) if meet else ""))
        c = ((g7 or {}).get("region") or {}).get("councils") or {}  # G7: まわりの集落の集まり (分かれ目の年の、年の終わりの歩だけ)
        print("COUNCIL " + (" ".join(sorted(c.get("ask", []), key=lambda x: int(x[1:]))) if meet and c.get("day") == state["day"] else ""))
        print(f"ASKLOG {'ask_why_log' in e2}")
        return
    if a.cmd == "next_part":  # 部の終わり (か次の G を待つ) から、次の部 (次の G) に入る (docs/society_phase/G7_design.md 4.E.1)
        why = _next_part_refusal(state, a.fill, a.closed)
        if why:
            print(f"next_part はできない: {why} (何も変えない)")
            sys.exit(3)
        import g7  # noqa: E402  (G7 から働く仕組み。G6 までは読みこまない)
        nxt = era2.ORDER2[era2.ORDER2.index(state["era"]) + 1]
        if a.closed is not None and state["era"] == "G7":  # G7 を本人の決めで閉じた (2026-10-23 本人の決め。8519 日目): 閉じたことを残してから G8 に入る
            c = g7.close_g7(state, a.closed.strip())
            print(f"* G7 (王と役所): 3 つの条件はそろわないまま、本人の決めで閉じた ({_yd(c['day'])})")
        elif a.closed is not None and state["era"] == "G8":  # G8 を本人の決めで閉じた (2026-10-28 本人の決め。12599 日目): 閉じたことを残してから G9 に入る
            c = g7.close_g8(state, a.closed.strip())
            print(f"* G8 (外からの押し): 3 つの条件はそろわないまま、本人の決めで閉じた ({_yd(c['day'])})")
        elif a.closed is not None:  # G6 を本人の決めで閉じた (町の条件がそろわないまま。2026-10-17): 閉じたことを残してから G7 に入る
            c = g7.close_g6(state, a.closed.strip())
            print(f"* 第 4 部の終わり (G6): 町の条件はそろわないまま、本人の決めで閉じた ({_yd(c['day'])}。記録の条件 "
                  f"{_yd(c['record']) if c['record'] is not None else 'まだ'})")
        if nxt == "G7":
            wo = [x.strip() for x in (a.world or "").split(",") if x.strip()]
            if set(wo) - set(g7.WORLD_KEYS) or (a.count is not None and a.count not in g7.COUNTS):
                print(f"next_part はできない: --world は {'・'.join(g7.WORLD_KEYS)}、--count は {'・'.join(g7.COUNTS)} だけ (何も変えない)")
                sys.exit(3)
            g = g7.enter(state, a.fill or 0.0, {k: True for k in wo} or None, a.count)
            if a.closed is not None:
                state["era_log"][-1]["g6_closed"] = state["day"]
        else:
            if a.world is not None or a.count is not None:
                print("next_part はできない: --world と --count は G7 に入るときだけ (G8 の世界は決まっている。g7.G8_WORLD) (何も変えない)")
                sys.exit(3)
            was = state["era"]
            g7.enter_next(state)
            g = state["era2"]["g7"]
            if a.closed is not None:
                state["era_log"][-1]["g7_closed" if was == "G7" else "g8_closed"] = state["day"]
        for kind in ("season", "feeling"):  # 前の部のお題 (もうコミットしてある) を消して、新しい部のお題を書く (ask_why の作り直しと同じ)
            d = pdir(state, kind, "prompts")
            if d.exists():
                shutil.rmtree(d)
        save(state)
        write_prompts(state, "season")
        export(state)
        _records(None)  # 記録を作り直す (控えの行は足さない。控えは季節の終わりだけ)
        fl = (g.get("region") or {}).get("fill")
        print(f"* フェーズ {state['era']} ({era2.NAMES2[state['era']]}) に入った ({_yd(state['day'])}。G7 の史実のずれの直しは {g['fix_from']} 日目から)")
        if nxt == "G8":
            so = next(o for o in era2._g6(state)["others"] if o["id"] == g["strong"])
            print(f"* G8 の世界: 草原を砂地・逃げ場なし・悪い年 {g['world']['bad']}・段の数え方 {g['count']}。強い集落 {so['name']} ({so['id']}) {so['people']} 人 (ます {tuple(so['cell'])}。村から {region_dist(so)} ます)")
        if nxt == "G9":
            g9s = g["g9"]
            so = next((o for o in era2._g6(state)["others"] if o["id"] == g.get("strong")), None)
            print(f"* G9 の世界: G8 のまま (草原を砂地・逃げ場なし・悪い年 {g['world']['bad']}・段の数え方 {g['count']})。"
                  + (f"{so['name']} ({so['id']}) {so['people']} 人は残る。" if so else "")
                  + ("重い押しは切った (求めはふつうの量)。" if (g.get("heavy") or {}).get("end") == state["day"] else "")
                  + f"村の赤い金属の道具 {len(g9s['tools'])}。よその便りの札 2 枚を足した")
        if nxt == "G7":
            print(f"* まわりの集落: {len(era2._g6(state)['others'])} (はじめに置いた集落 {len(fl['placed'])}・{fl['people']} 人。地域の人数を K の {fl['share']:.0%} に)"
                  if fl else f"* まわりの集落: {len(era2._g6(state)['others'])} (はじめの集落は置かなかった。--fill なし = 今のまま)")
        print("次: 答えを集めて season")
        _records_exit()
        return
    if a.cmd == "cards":  # G7: よその便りの札の表を足した・直したとき (docs/society_phase/G7_design.md 4.C.1)。出来事「区切り」と新しいハッシュを残す
        if not (state.get("era2") or {}).get("g7"):
            sys.exit("G7 に入っていないので、札の表のハッシュはまだない (G7 に入る日に残す)")
        if not (a.onoff or "").strip():
            sys.exit('札の表を直したわけを書く (step.py cards "<note>")')
        import hints  # noqa: E402
        if not hints.cards_changed(state):
            print("札の表は変わっていない (何も変えない)")
            return
        why = hints.cards_note(state, a.onoff.strip())
        if why:
            sys.exit(why)
        save(state)
        export(state)
        print(f"札の表のハッシュを新しくした ({state['era2']['g7']['hints']['cards_sha'][:12]}…)。出来事「区切り」に残した")
        return
    if a.cmd == "heavy":  # 2026-10-25 (本人の決め): G8 の続き「重い押し」。g7.heavy に残し、出来事「集落」を書く。世界の乱数は引かない
        import g7  # noqa: E402
        if a.onoff != "on":
            sys.exit("heavy には on を書く (step.py heavy on。重い押しは、入れたら 1 回の走りの中では消さない)")
        why = g7.heavy_refusal(state)
        if why:
            print(f"heavy はできない: {why} (何も変えない)")
            sys.exit(3)
        if state["era2"]["g7"].get("heavy"):
            print(f"重い押しは、もう入っている ({_yd(state['era2']['g7']['heavy']['day'])}から。何も変えない)")
            return
        answered = any(pdir(state, "season", "answers").glob("*.json")) or any(pdir(state, "feeling", "answers").glob("*.json"))
        q = g7.heavy_on(state, g7.HEAVY_SHARE, answered)
        save(state)
        if not answered:
            write_prompts(state, "season")  # 今の歩のお題を書き直す (重い押しの出来事と、「増やせ」の求め)
        export(state)
        _records(None)  # 記録を作り直す (控えの行は足さない)
        print(f"* 重い押しを入れた ({_yd(state['day'])}): 強い集落の村への求めは、村の去年の刈り入れの {round(g7.HEAVY_SHARE * 10)} 割")
        print(f"* {q['to']} への「増やせ」の求め [{q['id']}]: 毎年 草の種 {q['what']['草の種']} つかみ (いま [{q['raise']}] で {q['old']['草の種']} つかみ。"
              f"この 1 年の刈り入れ {q['harvest']} つかみ)。この年の集まりで答える" if q else
              "* 「増やせ」の求めは、次の年の終わりに出す (今は年の集まりの答えを待つ歩でないか、もう答えがある。か、村が払っていない・強さが足りない)")
        _records_exit()
        return
    if a.cmd == "far_rate":  # 2026-10-29 (本人の決め「来る見込みを 5 割に」): 遠くの町の運ぶ人の重み。g7.g9.far_rate に残し、出来事「目盛り」(村は見ない) を書く
        #   世界の乱数の列にはさわらない。お題は変わらない (お題の文は「ときどき来る」のまま。便りは次の季節の終わりから届く) ので書き直さない
        try:
            rate = float(a.onoff)
        except (TypeError, ValueError):
            sys.exit("far_rate には重みを書く (step.py far_rate 0.5)")
        if not (state.get("era2") or {}).get("g7") or "g9" not in state["era2"]["g7"]:
            print(f"far_rate はできない: 遠くの町の運ぶ人の見込みは G9 のときだけ (今は {state.get('era')}) (何も変えない)")
            sys.exit(3)
        import g9  # noqa: E402
        why = g9.far_rate_refusal(state, rate)
        if why:
            print(f"far_rate はできない: {why} (何も変えない)")
            sys.exit(3)
        row = g9.set_far_rate(state, rate, FAR_RATE_NOTE)
        if row is None:
            print(f"遠くの町の運ぶ人の重みは、もう {rate} (何も変えない)")
            return
        save(state)
        export(state)
        _records(None)  # 記録を作り直す (控えの行は足さない)
        t = row.get("topup")
        print(f"* 遠くの町の運ぶ人の 1 年の見込み (重み) を {row['was']} から {rate} にした ({_yd(state['day'])}から)")
        print(f"* この日に引いた次の年の便りに、差 {t['lam']} で遠くの商人を引き足した: {t['n']} 人" + (f" ({'・'.join(t['rows'])})" if t["rows"] else "")
              if t else "* 次の年の便りは、次の年の終わりに新しい重みで引く")
        print("お題は書き直していない (変わらない)")
        _records_exit()
        return
    if a.cmd == "ask_why":  # 2026-10-14 (本人が決めた。docs/humanity の D09 の段階 1): 季節のお題で、主な仕事にした理由を一言たずねる
        #   このコマンドは世界 (乱数・出来事・蓄え) を変えない。why は世界の計算には使わない (同じ答えなら同じ世界。お題が変わるので、村の人の答えは変わりうる)。
        #   まだだれも答えていなければ、今の季節のお題から
        e2 = state.get("era2")
        if not e2:
            sys.exit("Society 2.0 が始まっていないので、仕事の理由はたずねられない")
        on = a.onoff != "off"
        what = "仕事の理由をたずねる" if on else "仕事の理由をたずねるのをやめる"
        past = e2.get("ask_why_log") or []  # 切り替えの控え: [その日のお題から, たずねるか] の並び (記録が、季節ごとにお題に理由の欄があったかを読む)
        if bool(e2.get("ask_why")) == on:
            print(f"仕事の理由は、もうたずねている ({past[-1][0] if past else '?'} 日目のお題から。何も変えない)" if on
                  else "仕事の理由は、たずねていない (何も変えない)")
            return
        now = state["phase"] == "season" and not any(pdir(state, "season", "answers").glob("*.json"))
        # もう答えがあれば、お題はそのままで、次の季節のはじめのお題 (季節の終わりの日に書く) から。途中で集まり直しても、記録は季節のはじめの答えから読む
        day = state["day"] if now else (state["day"] + 1) // era2.SEASON_DAYS * era2.SEASON_DAYS + era2.SEASON_DAYS - 1
        e2["ask_why"] = on
        e2["ask_why_log"] = past + [[day, on]]
        save(state)
        if now:
            write_prompts(state, "season")  # 今の季節のお題を作り直す (気持ちのお題は前と同じ)
        print(f"{what}: {day} 日目のお題から" + ("" if now else " (今の季節は、もう答えがあるので、お題はそのまま)"))
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
            code, why = _hold_text(state)
            print(f"一時停止中: {why}。進めない")
            print(f"HOLD {code}")  # ワークフローが読む機械用の 1 行 (行の頭から。4.E.2)
            sys.exit(3)
        if (state.get("era2") or {}).get("g7"):  # G7: 札の表 (よその便り) が G7 に入った日 (か step.py cards の日) と同じか (docs/society_phase/G7_design.md 4.C.1)
            import hints  # noqa: E402
            why = hints.cards_changed(state)
            if why:
                print(f"{why}。直したなら、わけを書いて step.py cards \"<note>\" を動かしてから進める (何も変えない)")
                sys.exit(5)
        before = state["next_event"]  # G5: 季節の集まりで起きたこと (収める・裁き・罰・祭り・まとめ役) は、30 日を進める前の出来事
        if hasattr(era2, "take_notes"):
            try:
                era2.take_notes()  # 記録のための書きとめ: 前のものを捨てる
            except Exception as ex:  # 記録の失敗で、世界を止めない
                print(f"記録: 書きとめを空にできなかった ({type(ex).__name__}: {ex})")
        g7 = _g7(state)
        met = not g7 or bool(state["era2"]["g7"].get("ask"))  # G7: 集まりの歩 (年の集まり・寄る季節・集まり直し・秋の集まり) か
        if g7 and not met:  # G7 の答えのない季節: 年の答えの、この季節の予定と 1 年の方針で進む (docs/society_phase/G7_design.md 4.A.6)
            print(f"この季節は集まらない (年の集まり {g7.plan_day(state)} 日目の予定と方針で進む)")
            g7.apply_plan(state)
        else:
            feels = read_feelings(state)  # 代表を決める前の顔ぶれで読む (集まりで、まとめ役が変わることがあるため)
            if g7:  # G7 の集まりの歩: 見本の家の答えを、見本でない家に広げる (まわりの集落の集まりの答えも、ここで先に読む)
                g7.apply_year(state, read_answers(state, "season"), read_councils(state))
            else:
                era2.apply_answers(state, read_answers(state, "season"))
            era2.apply_feelings(state, feels)
        first = era2.simulate_season(state)
        state["era2"]["last_first"] = first
        if g7:
            g7.after_season(state, first, met)
        if not any(p["alive"] for p in state["people"]):
            snap = _snap(state, before, first)
            _archive(state)
            save(state)
            export(state)
            _records(snap)
            gone = [p for p in state["people"] if p.get("left")]
            print("生きている人がいない (亡くなった人と、村を出た人" + (f" {len(gone)} 人" if gone else " 0 人") + ")")
            sys.exit(4)
        r = era2.check(state)
        hold = None  # 一時停止したときの、機械用の言葉 (最後に「HOLD …」の 1 行で出す。4.E.2)
        if r == "end" and state["era"] == "G6":  # G6: 町と記録がそろった (「フェーズが…に進んだ」とは書かない。"end" も真なので、先に見る)
            state["hold"] = True
            g = state["era2"]["g6"]["end"]
            # 2026-10-16: 本人が「G を付け足していく。工業社会に行き着くまで」と決めた (2026-10-15) ので、残す文は「Society 2.0 の終わり」ではなく「第 4 部の終わり」にする
            #   (state.json は手で直さないので、G7 を足す前に変えておく。docs/society2_extension_plan.md)
            world.log(state, "フェーズ", None, f"第 4 部の終わり (G6): 町 ({g['town']} 日目) と記録 ({g['record']} 日目) がそろった (先にそろったのは {g['first']})。Society 2.0 は G7 から続ける")
            # 2026-10-17: ワークフローは、最後の機械用の 1 行「HOLD part_end」で止まる (tools/society2_seasons_workflow.js と同じコミットで変えた)。
            #   前の合図「Society 2.0 が終わった」は、もう出さない (第 4 部の終わりは Society 2.0 の終わりではない。2026-10-15 本人「G を付け足していく」)
            print(f"* 第 4 部の終わり (G6): 町 ({_yd(g['town'])}) と記録 ({_yd(g['record'])}) がそろった → 一時停止 (第 4 部のまとめ待ち。次の部へは next_part)")
            hold = "part_end"
        elif r is True:
            state["hold"] = True
            e = state["era_log"][-1]
            world.log(state, "フェーズ", None, f"フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ")
            print(f"* フェーズが {e['era']} ({era2.NAMES2[e['era']]}) に進んだ → 一時停止 (評価待ち)")
            hold = "phase"
        elif r:  # G7 から: 部の終わり ("end")・工業の入口 ("entrance")・次の G を待つ ("wait")・止めて相談する ("consult")
            state["hold"] = True
            hold = _hold_text(state)[0]
            h = state["era2"]["g7"]["hold"]
            if r in ("end", "entrance"):  # 部の終わりは、G6 と同じく出来事に残す (待ちと相談は、作る側の都合なので残さない)
                n = era2.PART_END[h["era"]]
                world.log(state, "フェーズ", None, f"第 {n} 部の終わり ({h['era']}): {h['era']} の条件がそろった" + ("。工業の入口に着いた" if r == "entrance" else ""))
            print({"end": f"* 第 {era2.PART_END.get(h['era'])} 部の終わり ({h['era']}): {h['era']} の条件がそろった → 一時停止 (第 {era2.PART_END.get(h['era'])} 部のまとめ待ち。次の部へは next_part)",
                   "entrance": "* 工業の入口に着いた: Society 2.0 のまとめと、その先を本人と相談する → 一時停止 (next_part は受けつけない)",
                   "wait": f"* {h['era']} の条件がそろった: 次の G を作るまで一時停止 (次の G のコードを入れてから next_part)",
                   "consult": f"* 止めて相談する: {h.get('what', '')} → 一時停止 (相談のあと、続けるなら resume)"}[r])
        snap = _snap(state, before, first)  # 保存の前に読む (保存するのと同じ state)
        _archive(state)  # 年が変わっていれば、古い年をしまう (お題・控え・出来事の表示は、しまう前と同じ)
        save(state)
        write_prompts(state, "season")
        export(state)
        _records(snap)
        for e in state["events"]:
            if (e["id"] >= first and e["type"] in ("掟", "死", "生まれる", "加わる", "去る", "訪れる", "畑", "ヤギ", "大人になる", "フェーズ", "家族", "虫", "受けつぎ", "区切り",
                                                   "年の集まり", "よその便り", "きっかけ", "取り立て", "病")) \
                    or (e["id"] >= before and (e["type"] in era2.G5_EVENTS + era2.G6_EVENTS + era2.G7_EVENTS or e["type"] == "年の名前")):
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
        if "g9_c1_day" in i:  # G9 (2026-10-29): G9 の条件と F (G7 の物差しは下の 2 行に、ならべて出す)
            G9 = state["era2"]["g7"]["g9"]
            print(f"G9 / 条件: 赤い金属の道具を使う {_yd(i['g9_c1_day']) if i['g9_c1_day'] is not None else 'まだ'} (この年 {i['g9_used_year']} 人日) / "
                  f"商人の家 {_yd(i['g9_c2_day']) if i['g9_c2_day'] is not None else 'まだ'} (交換に行った日のいちばん多い家 {i['g9_trip_days_max']} 日) / "
                  f"遠くとの約束を書く {_yd(i['g9_c3_day']) if i['g9_c3_day'] is not None else 'まだ'} / F {'・'.join(sorted(G9['reached'])) or 'まだ'} / "
                  f"赤い金属の道具 {i['g9_tools']} ({i['g9_use']}) / 遠くの運ぶ人 {i['g9_far_visits']} 回・約束 {i['g9_promises']} (書いた {i['g9_written']}・守り合った {i['g9_kept']})")
        if i.get("g7_on"):
            print(f"{state['era']} / 役の人 {i['g7_role_people']} / まわりの集落 {i['g7_others']} (人 約 {i['g7_region_people']}) / "
                  f"{'G7 の物差し (ならべて測る)' if 'g9_c1_day' in i else '条件'}: 決める段 3 {_yd(i['g7_f3_day']) if i['g7_f3_day'] is not None else 'まだ'} / "
                  f"取り立ての記録 2 年 {_yd(i['g7_tribute2_day']) if i['g7_tribute2_day'] is not None else 'まだ'} / "
                  f"書いた決まりで裁く {_yd(i['g7_f4_day']) if i['g7_f4_day'] is not None else 'まだ'}")
            G = state["era2"]["g7"]
            led = (G.get("hints") or {}).get("ledger", [])
            ask = [k for k, v in sorted((G.get("stall") or {}).items()) if v.get("ask") and not v.get("done")]
            print(f"{state['era']} / 決める段 {i.get('g7_levels', 0)} (村は{i.get('g7_village', '外')}) / 取り立てを全部残せた年 {i.get('g7_tribute_years', 0)} / "
                  f"板に書いた掟 {i.get('g7_written_laws', 0)} / F {'・'.join(sorted(G.get('reached') or {})) or 'まだ'} / "
                  f"よその便り (村) 届いた {sum(1 for r in led if r['to'] == 'V0' and r['status'] in ('届いた', '忘れられた'))}・"
                  f"これから {sum(1 for r in led if r['to'] == 'V0' and r['status'] == '待つ')}"
                  + (f" / 8 年進まない条件 {'・'.join(ask)} (5 年ごとの報告で相談)" if ask else ""))
        if hold:
            print(f"HOLD {hold}")  # ワークフローが読む機械用の 1 行 (行の頭から。村の人の文 (出来事は「* 」で始まる) からは出ない。4.E.2)
        _records_exit()
        return
    if a.cmd == "day" and not any(p["alive"] for p in state["people"]):
        print("生きている人がいないので、進めない")
        sys.exit(4)
    if a.cmd == "day" and state.get("hold"):
        print(f"一時停止中: フェーズ {state.get('era')} に進んだので評価待ち。進めない (再開は resume)")
        sys.exit(3)
    if a.cmd != state["phase"]:
        sys.exit(f"今の段階は {state['phase']} です ({a.cmd} はまだできない)")
    if state.get("archive"):  # Society 1.0 の段階 (今は使わない) は、出来事をすべて読むので、しまった記録を戻してから (保存すると、しまう前の形になる)
        state = archive.full(state, DATA)

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
