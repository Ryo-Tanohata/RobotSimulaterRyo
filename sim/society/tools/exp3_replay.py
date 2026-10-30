"""論文 2・実験 3 の確かめ: コミットした本物の歩を、今のコードで写しの中でやり直して、1 バイトも同じかをくらべる (トークン 0。本物の data にはさわらない)

  PYTHONUTF8=1 python3.13 sim/society/tools/exp3_replay.py --commits 689c3c0b,6d0aefc7 [--arm A2] [--work /tmp/exp3_replay]

- 歩のコミット C (「社会シミュレーション: N 日目から (…)」) ごとに、1 つ前のコミット (C^) の state.json・archive/・app_data.json を写しに出し、
  C の answers/dayN (季節・気持ち・まわりの集落・models.json) を置いて、SOC_RECORDS=0 で step.py season を 1 回動かす。
- くらべるもの: state.json (sha256)・app_data.json・archive/ のファイル・次の歩のお題 (prompts/dayM の季節・気持ち・まわりの集落)。
- --arm (A0・A1・A2) をつけると、step.py season の前に、写しの state に組を入れる (exp3.set_arm)。このとき:
  state は「g7.exp3 の 1 つの鍵のほかは同じ」か、季節のお題は「足した節 (exp3.strip) を除けば同じ」かを見る (気持ち・集まりのお題は同じはず)。
  A0 は、お題も同じはず (組を残すだけ)。
- 戻り値: みな同じなら 0、どこかがちがえば 1。表を出す。
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
ROOT = SOC.parent.parent
sys.path.insert(0, str(SOC))
import exp3  # noqa: E402

D = "sim/society/data"


def git_extract(rev, paths, dest):
    """rev の paths (リポジトリの根からの道) を dest に出す (sim/society/data/ の下を dest の直下に)"""
    r = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", rev, *paths], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode()[:400])
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
        for m in t.getmembers():
            if not m.name.startswith(D + "/"):
                continue
            m.name = m.name[len(D) + 1:]
            t.extract(m, dest, filter="data")


def has(rev, path):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{rev}:{path}"], capture_output=True).returncode == 0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def files(d):
    d = Path(d)
    return {str(f.relative_to(d)): f for f in sorted(d.rglob("*")) if f.is_file()} if d.exists() else {}


def one(c, arm, work):
    par = subprocess.run(["git", "-C", str(ROOT), "rev-parse", c + "^"], capture_output=True, text=True).stdout.strip()
    w = Path(work) / f"{c}_{arm or 'off'}"
    if w.exists():
        shutil.rmtree(w)
    data, ref = w / "data", w / "ref"
    data.mkdir(parents=True)
    ref.mkdir()
    git_extract(par, [f"{D}/state.json", f"{D}/archive", f"{D}/app_data.json"], data)
    st0 = json.loads((data / "state.json").read_text(encoding="utf-8"))
    day = st0["day"]
    if has(c, f"{D}/answers/day{day:03d}"):  # 集まりのない歩は答えがない
        git_extract(c, [f"{D}/answers/day{day:03d}"], data)
    git_extract(c, [f"{D}/state.json", f"{D}/archive", f"{D}/app_data.json"], ref)
    if arm:
        exp3.set_arm(st0, arm, "確かめ (exp3_replay)")
        (data / "state.json").write_text(json.dumps(st0, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    env = dict(os.environ, SOC_DATA=str(data), SOC_RECORDS="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(SOC / "step.py"), "season"], capture_output=True, text=True, env=env, cwd=str(SOC))
    out = {"commit": c, "day": day, "arm": arm or "off", "rc": r.returncode}
    st1 = json.loads((data / "state.json").read_text(encoding="utf-8"))
    new = st1["day"]
    if has(c, f"{D}/prompts/day{new:03d}"):
        git_extract(c, [f"{D}/prompts/day{new:03d}"], ref)
    # state
    if arm:
        x = st1["era2"]["g7"].pop("exp3", None)
        same_state = json.dumps(st1, ensure_ascii=False, separators=(",", ":")) == (ref / "state.json").read_text(encoding="utf-8")
        out["state"] = "同じ (exp3 の鍵のほか)" if same_state and x and x["arm"] == arm else "ちがう"
    else:
        out["state"] = "同じ" if sha(data / "state.json") == sha(ref / "state.json") else "ちがう"
    out["sha"] = sha(ref / "state.json")[:16]
    out["app_data"] = "同じ" if sha(data / "app_data.json") == sha(ref / "app_data.json") else "ちがう"
    a, b = files(data / "archive"), files(ref / "archive")
    out["archive"] = "同じ" if a.keys() == b.keys() and all(sha(a[k]) == sha(b[k]) for k in a) else "ちがう"
    pa, pb = files(data / f"prompts/day{new:03d}"), files(ref / f"prompts/day{new:03d}")
    diff, added = [], 0
    for k in sorted(set(pa) | set(pb)):
        if k not in pa or k not in pb:
            diff.append(k)
            continue
        ta, tb = pa[k].read_text(encoding="utf-8"), pb[k].read_text(encoding="utf-8")
        if arm and k.startswith("season/") and arm != "A0":
            added += ta != tb
            ta = exp3.strip(ta)
        if ta != tb:
            diff.append(k)
    out["prompts"] = f"{len(pb)} 通" + (" 同じ" if not diff else f" ちがう {len(diff)} ({', '.join(diff[:3])})") + (f" (節を足した {added} 通)" if arm else "")
    out["ok"] = r.returncode == 0 and not diff and all(out[k].startswith("同じ") for k in ("state", "app_data", "archive")) \
        and (not arm or arm == "A0" or added == sum(1 for k in pa if k.startswith("season/")))
    if not os.environ.get("EXP3_KEEP"):
        shutil.rmtree(w)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commits", required=True, help="歩のコミット (コンマでつなぐ)")
    ap.add_argument("--arm", default=None, choices=[None, "A0", "A1", "A2", "A3"])
    ap.add_argument("--work", default="/tmp/exp3_replay")
    a = ap.parse_args()
    bad = 0
    print("| コミット | 歩の日 | 組 | state | sha256 (本物) | app_data | archive | 次のお題 | 結果 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in a.commits.split(","):
        o = one(c.strip(), a.arm, a.work)
        bad += not o["ok"]
        print(f"| {o['commit']} | {o['day']} | {o['arm']} | {o['state']} | {o['sha']}… | {o['app_data']} | {o['archive']} | {o['prompts']} | {'OK' if o['ok'] else 'ちがう'} |",
              flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
