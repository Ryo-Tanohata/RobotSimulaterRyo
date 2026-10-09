"""過去の季節の終わりの控えを、git に残る state.json から作る (1 回だけ使う。docs/dashboard_records_spec.md 2.5)

  python3 sim/society/tools/backfill_snapshots.py [--data DIR] [--repo ROOT] [--path sim/society/data/state.json] [--dry-run]

季節を進めるたびに state.json を git にコミットしてきたので、Society 2.0 のすべての季節の終わりの state が git に残っている。
今の state.json の出来事とつながっている state (取りやめた回は入らない) を、日ごとに最初のコミットだけ使い、records/snapshots.jsonl に書き足す。
git を読むだけで、state.json は変えない。もう控えのある日には足さない (何度動かしても同じ)。--dry-run なら何も書かない
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import records  # noqa: E402

DAY_RE = re.compile(rb'"day":(-?\d+)')


def _same(a, b):
    return all(a.get(k) == b.get(k) for k in ("day", "type", "who", "text"))


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _day_of(repo, sha, path):
    """そのコミットの state の日 (はじめの数百字だけ読む。読めなければ None)"""
    p = subprocess.Popen(["git", "-C", str(repo), "show", f"{sha}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    head = p.stdout.read(400)
    p.stdout.close()
    p.wait()
    m = DAY_RE.search(head)
    return int(m.group(1)) if m else None


def _commits(repo, path, start):
    """古いコミットから順に。Society 2.0 の前 (日が start より前) のコミットは、二分探索で飛ばす
    (日は Society 2.0 の前は start より小さく、そのあとはいつも start 以上なので)"""
    shas = _git(repo, "log", "--format=%H", "--reverse", "--", path).decode().split()
    lo, hi = 0, len(shas)
    while lo < hi:
        mid = (lo + hi) // 2
        d = _day_of(repo, shas[mid], path)
        if d is not None and d >= start:
            hi = mid
        else:
            lo = mid + 1
    return shas[lo:]


def _blobs(repo, path, shas):
    """(コミット, 中身の番号, state の中身のバイト列)。前と同じ中身はバイト列を None にする (読み直さない)"""
    p = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    seen = set()
    try:
        for sha in shas:
            p.stdin.write(f"{sha}:{path}\n".encode())
            p.stdin.flush()
            head = p.stdout.readline().split()
            if len(head) < 3 or head[1] != b"blob":  # そのコミットでは消えていた
                continue
            data = p.stdout.read(int(head[2]))
            p.stdout.read(1)
            yield sha, head[0], (None if head[0] in seen else data)
            seen.add(head[0])
    finally:
        p.stdin.close()
        p.wait()


def backfill(data_dir, repo, path, dry_run=False, quiet=False):
    state = json.loads((Path(data_dir) / "state.json").read_text(encoding="utf-8"))
    e2 = state.get("era2") or {}
    start = e2.get("start_day")
    if start is None:
        print("Society 2.0 がまだ始まっていない (控えは作らない)")
        return []
    have, _ = records.load_snapshots(data_dir, state, warn=False)
    cur = state["events"]
    kept = {}  # 日 → (区切りの番号, コミット, 控えの行, next_event)
    epoch = 0  # 今の記録につながらないコミット (取りやめた回) が出るたびに 1 増やす
    known = {}  # 中身の番号 → (日, 控えの行, next_event) か None (使わない中身)
    for sha, oid, data in _blobs(repo, path, _commits(repo, path, start)):
        if data is None:  # 前と同じ中身 (やり直しで同じ state をコミットしたなど)
            if known.get(oid) is None:
                continue
            day, row, n = known[oid]
        else:
            known[oid] = None
            m = DAY_RE.search(data[:400])
            if m and int(m.group(1)) < start:
                continue
            old = json.loads(data)
            day, oe = old.get("day"), old.get("era2")
            if not oe or day is None or day < start:
                continue
            n = old.get("next_event", len(old.get("events", [])))
            if n < 1 or n > len(cur) or not _same(old["events"][n - 1], cur[n - 1]):  # 今の記録につながらない (取りやめた回)
                epoch += 1
                continue
            row = records.snapshot(old, meeting_first=None, event_first=oe.get("last_first"), source="git", notes=None)
            known[oid] = (day, row, n)
            del old
        # 同じ日は最初のコミット (季節を進めた結果。あとの「再開」は使わない)。ただし、取りやめた回のあとでやり直した日は、やり直しのほう
        if day in kept and kept[day][0] == epoch:
            continue
        kept[day] = (epoch, sha, dict(row, source=f"git:{sha[:7]}"), n)
    rows, prev_end = [], None
    for day in sorted(kept):
        _, sha, row, n = kept[day]
        row["meeting_first"] = prev_end  # この回をはじめた集まりの最初の出来事 = 前の控えの state の next_event
        prev_end = n
        add = day not in have
        if not quiet:
            print(f"{day}\t{sha[:7]}\t{1 if add else 0}")
        if add:
            rows.append(row)
    if not dry_run:
        for row in rows:
            records.append_snapshot(data_dir, row)
    print(f"控え: git から {len(kept)} 日分を読み、{len(rows)} 行を足した" + (" (--dry-run なので書いていない)" if dry_run else ""))
    return rows


def main():
    root = HERE.parents[2]
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    ap.add_argument("--repo", default=str(root))
    ap.add_argument("--path", default="sim/society/data/state.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    backfill(a.data, a.repo, a.path, a.dry_run, a.quiet)


if __name__ == "__main__":
    main()
