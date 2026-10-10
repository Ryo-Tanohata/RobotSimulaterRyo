"""古い記録を年ごとのファイルに分ける (2026-10-10 本人が決めた「古い記録を年ごとのファイルに分ける」。消さない)

4379 日目に state.json が 59 MB (出来事 29 MB・掟の投票の記録 12.5 MB・木から採った記録 10 MB・知識の移り変わり 2.5 MB)、app_data.json が 49 MB になり、
2 つ合わせて 1 季節に 約 1.7 MB ずつ増える (4049〜4379 日目の 11 季節で state.json +10.3 MB・app_data.json +8.3 MB)。【文献】GitHub は 50 MB をこえるファイルに注意を出し、100 MB をこえると受けとらない (GitHub Docs「About large files on GitHub」)。
Cloudflare Pages は 1 ファイル 25 MiB まで (tools/cloudflare/build.sh は、こえるファイルを入れない)。
そこで、世界の仕組みが読まない古い記録を data/archive/ の年ごとのファイル (1 行 = 1 件の JSONL。番号も中身もそのまま) に移す。
世界は変わらない (前のコードと、写しで季節を進めて比べた。docs/society2_phase_plan.md の 7.)。

- しまうもの: 出来事 events・掟の投票の記録 laws[].vote_log・木から採った記録 harvests・知識の移り変わり knowledge_log・日ごとの数 stats
- しまう年: 今の年と、その前の KEEP_YEARS 年より前の年。年が変わって最初の季節の終わりに、1 年分ずつ (step.py。移行のあとだけ)
- 読む人を調べた (2026-10-10。だれが、どこまで前を読むか):
  - 季節のお題・集まり・もめごと・町と記録 (era2): 前の季節・前の集まりから (番号が last_first・meet_first より大きいもの)。
    年の名前は、前の年の終わりの集まりから (meeting_first)。日ごとの数 stats は 1 年分 ([-YEAR:])。G3 の F1 (出来事の最後の 3000 件) は G3 のあいだだけ
  - 知識と掟の札 (knowledge・characters): きっかけの出来事の番号から、種類 (話すか、ほかか) と、話した人を読む。古い番号も → 話す を残す
  - 家族を決める (era2._sync_households)・来た日 (resume._joined_day): 加わる を全部 → 残す
  - お題の「種から育った木 (…が種を埋めた木)」(characters._sown_trees): 育つ を全部 → 残す
  - まとめ役なしの道の季節の数 (era2._g5_no_leader): まとめ役 をさかのぼる → 残す
  - 掟の投票の記録・知識の移り変わり: 書くだけ (世界は読まない)。木から採った記録: 同じ日に同じ木を 2 回数えないためだけ (F4 の条件は Society 1.0)
  - 試した活動 (world.tried_activities): state の tried_acts を読む (出来事から求めるのは、tried_acts がない古い state だけ)
  - Society 1.0 の段階 (step.py day・evening・night): 出来事をすべて読むので、step.py が戻してから進める (今は使わない)
  - 全部を読むもの (アプリ用のデータ・履歴書・ダッシュボードの記録・グラフ・1 つの HTML): full(state, data) か load_state(data) で読む
- 残す 4 種類 (KEEP_TYPES) は、年のファイルにも入れる (年のファイルは、その年の出来事がすべてそろう)。state.json には写しが残る
- しまったあとの state.json には "archive" がある (しまった最後の年・しまった出来事の数・件数)。全部を戻すと "archive" はなくなる
"""
import bisect
import json
import os
from pathlib import Path

YEAR = 120  # この世界の 1 年 (era2.YEAR と同じ。4 季節 × 30 日)
KEEP_YEARS = 2  # 【仮定】今の年のほかに、前の 2 年は state.json に残す (年の名前のお題は前の年の終わりの集まりから、日ごとの数は 1 年分を読むので、1 年より長く)
KEEP_TYPES = ("話す", "加わる", "育つ", "まとめ役")  # 世界の仕組みが、しまう年までさかのぼって読む出来事 (上の「読む人を調べた」)
LISTS = ("harvests", "knowledge_log", "stats")  # 日の順に並んだ記録 (前から順に移す)
KINDS = ("events",) + LISTS + ("vote_log",)
DIR = "archive"
V = 1
MOVED = "(しまった出来事)"  # しまった出来事の種類の代わり (KEEP_TYPES のどれでもない。知識の札は「話すか、ほかか」だけを見る)


class ArchiveError(Exception):
    pass


def path(data, kind, year):
    """年のファイル (例: data/archive/events_0030.jsonl = 30年 (3600〜3719 日目) の出来事)"""
    return Path(data) / DIR / f"{kind}_{year:04d}.jsonl"


def days_path(data, year):
    """しまった年の、アプリの 3D の再生の行 (step.py の export が作る。例: data/archive/days_0030.json)"""
    return Path(data) / DIR / f"days_{year:04d}.json"


def _dump(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))  # state.json と同じ書き方


def _write(f, rows):
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(_dump(r) + "\n")
    os.replace(tmp, f)


def _read(f):
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def _by_year(rows, what):
    """日の順に並んだ行 → {年: 行} (日が前にもどれば止める。戻したときに順が変わらないように。投票の記録を日の順に並べかえても、
    1 つの掟の中の順が変わらないように)"""
    out, last = {}, None
    for r in rows:
        if last is not None and r["day"] < last:
            raise ArchiveError(f"{what} が日の順に並んでいない ({r['day']} 日目)")
        out.setdefault(r["day"] // YEAR, []).append(r)
        last = r["day"]
    return out


def _head(xs, cut):
    """前から、cut 日より前の日のものの数"""
    i = 0
    while i < len(xs) and xs[i]["day"] < cut:
        i += 1
    return i


def last_year(state):
    """しまってよい最後の年 (今の年と、その前の KEEP_YEARS 年は残す)"""
    return state["day"] // YEAR - KEEP_YEARS - 1


def move(state, data, start=False):
    """しまってよい年の記録を年ごとのファイルに移し、state から除く (ファイルを書いてから state を変える。途中で止まっても state は前のまま)。
    戻り値: しまった年の一覧。start: まだ一度もしまっていない state でも始める (tools/archive_records.py の 1 回だけの移行。
    step.py は移行のあと ("archive" がある state) だけ動かす)"""
    a = state.get("archive")
    if a is None and not start:
        return []
    a = json.loads(_dump(a)) if a else {"v": V, "upto": -1, "event": 0, "n": {k: 0 for k in KINDS}}
    upto, base, last = a["upto"], a["event"], last_year(state)
    if last <= upto:
        return []
    cut = (last + 1) * YEAR  # この日より前の日のものを移す
    ev = state["events"]
    kept = [e for e in ev if e["id"] < base]  # 前にしまった年の、残した写し
    rest = [e for e in ev if e["id"] >= base]
    i = _head(rest, cut)
    moved, rest = rest[:i], rest[i:]
    nb = base + len(moved)
    if [e["id"] for e in moved] != list(range(base, nb)) or [e["id"] for e in rest] != list(range(nb, state["next_event"])):
        raise ArchiveError("出来事の番号が 0 から続いていない (しまわない)")
    out = {"events": _by_year(moved, "出来事")}
    cuts = {}
    for k in LISTS:
        xs = state.get(k)
        if xs:
            cuts[k] = _head(xs, cut)
            out[k] = _by_year(xs[:cuts[k]], k)
    votes, vcut, ids = [], {}, set()
    for law in state.get("laws", []):
        if law["id"] in ids:
            raise ArchiveError(f"掟の番号 {law['id']} が 2 つある")
        ids.add(law["id"])
        vl = law.get("vote_log")
        if vl:
            vcut[law["id"]] = j = _head(vl, cut)
            _by_year(vl[:j], f"{law['id']} の投票の記録")
            votes += [{"law": law["id"], "vote": v} for v in vl[:j]]
    votes.sort(key=lambda r: r["vote"]["day"])  # 日の順 (同じ日は掟の順。1 つの掟の中の順は変わらない)
    out["vote_log"] = {}
    for r in votes:
        out["vote_log"].setdefault(r["vote"]["day"] // YEAR, []).append(r)
    for k, ys in out.items():
        for y in ys:
            if not upto < y <= last:
                raise ArchiveError(f"{k} の {y} 年は、しまう年ではない ({upto + 1}〜{last} 年)")
    for k in KINDS:  # 書く (前に書きかけたファイルがあれば、同じ中身で書きなおす。その年に何もない種類の、前のファイルは消す)
        for y in range(upto + 1, last + 1):
            if y in out.get(k, {}):
                _write(path(data, k, y), out[k][y])
            elif path(data, k, y).exists():
                path(data, k, y).unlink()
    for y in range(upto + 1, last + 1):  # アプリの再生の行 (step.py が作る) も、前の試みや、戻してやり直す前の世界のものなら消す (作り直させる)
        days_path(data, y).unlink(missing_ok=True)
    for k in KINDS:  # 読みもどして確かめる (ちがえば state は変えない)
        for y, rows in out.get(k, {}).items():
            if path(data, k, y).read_text(encoding="utf-8") != "".join(_dump(r) + "\n" for r in rows):
                raise ArchiveError(f"{path(data, k, y)} を読みもどすと、書いたものと合わない")
    # ここから state を変える
    state["events"] = kept + [e for e in moved if e["type"] in KEEP_TYPES] + rest
    for k, j in cuts.items():
        state[k] = state[k][j:]
    for law in state.get("laws", []):
        if law["id"] in vcut:
            law["vote_log"] = law["vote_log"][vcut[law["id"]]:]  # 鍵は残す (空でも。戻したときに鍵の順が変わらないように)
    a["upto"], a["event"] = last, nb
    for k in KINDS:
        a["n"][k] = a["n"].get(k, 0) + sum(len(v) for v in out.get(k, {}).values())
    state["archive"] = a
    return list(range(upto + 1, last + 1))


def full(state, data):
    """しまった記録を戻した state (写し。state は変えない)。しまっていない state はそのまま返す。
    戻したものは、しまう前の state とまったく同じ (鍵の順も。"archive" はない)"""
    a = state.get("archive")
    if a is None:
        return state
    if a.get("v") != V:
        raise ArchiveError(f"しまい方の版 {a.get('v')} は読めない")
    years = range(a["upto"] + 1)
    st = {k: v for k, v in state.items() if k != "archive"}
    base = a["event"]
    old = [e for y in years for e in _read(path(data, "events", y))]
    if len(old) != base or any(e["id"] != i for i, e in enumerate(old)):
        raise ArchiveError(f"しまった出来事が足りない・多い ({len(old)} 件、{base} 件のはず。{Path(data) / DIR})")
    st["events"] = old + [e for e in state["events"] if e["id"] >= base]
    for k in LISTS:
        xs = [x for y in years for x in _read(path(data, k, y))]
        if len(xs) != a["n"].get(k, 0):
            raise ArchiveError(f"しまった {k} が {len(xs)} 件 ({a['n'].get(k, 0)} 件のはず)")
        if xs:
            st[k] = xs + state[k]
    votes, n = {}, 0
    for y in years:
        for r in _read(path(data, "vote_log", y)):
            votes.setdefault(r["law"], []).append(r["vote"])
            n += 1
    if n != a["n"].get("vote_log", 0):
        raise ArchiveError(f"しまった投票の記録が {n} 件 ({a['n'].get('vote_log', 0)} 件のはず)")
    if votes:
        laws = []
        for law in state["laws"]:
            if law["id"] in votes:
                law = dict(law, vote_log=votes.pop(law["id"]) + law["vote_log"])
            laws.append(law)
        if votes:
            raise ArchiveError(f"今の state にない掟の投票の記録がある ({', '.join(sorted(votes))})")
        st["laws"] = laws
    return st


def load_state(data, whole=True):
    """data/state.json を読む。whole なら、しまった記録も戻す (全部を読むもの: アプリ用のデータ・記録・ダッシュボード・グラフ)"""
    st = json.loads((Path(data) / "state.json").read_text(encoding="utf-8"))
    return full(st, data) if whole else st


# ---- 世界の仕組みが、しまった出来事の番号を読むとき (しまう前と同じ答えになるように) ----

def _is_id(i, n):
    """0〜n-1 の番号か (しまう前の「番号の集まりに入っているか」と同じ。番号は 0 から続いている)"""
    try:
        return 0 <= i < n and i == int(i)
    except (TypeError, ValueError, OverflowError):
        return False


class Events:
    """出来事の番号 → 出来事。しまった番号も「ある」(番号は 0 から続いているので)。しまった出来事の種類は MOVED
    (KEEP_TYPES のどれでもない。話すは残しているので、話した人もわかる)"""

    def __init__(self, state):
        self.ev = {e["id"]: e for e in state["events"]}
        a = state.get("archive")
        self.base = a["event"] if a else 0

    def __contains__(self, i):
        return i in self.ev or _is_id(i, self.base)

    def type(self, i):
        e = self.ev.get(i)
        return e["type"] if e is not None else MOVED

    def who(self, i):
        return self.ev[i]["who"]


def event_at(state, i):
    """番号 i の出来事 (state にあるものだけ。なければ None)"""
    ev = state["events"]
    if isinstance(i, int) and 0 <= i < len(ev) and ev[i]["id"] == i:  # しまっていない state (番号 = 並びの番号)
        return ev[i]
    j = bisect.bisect_left(ev, i, key=lambda e: e["id"])
    return ev[j] if j < len(ev) and ev[j]["id"] == i else None


def events_from(state, first):
    """番号 first からの出来事 (しまう前の state["events"][first:] と同じ)"""
    ev = state["events"]
    return ev[bisect.bisect_left(ev, first, key=lambda e: e["id"]):]
