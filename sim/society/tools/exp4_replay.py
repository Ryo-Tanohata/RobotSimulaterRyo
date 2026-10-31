"""論文 2・実験 4 の確かめ: コミットした本物の歩を、今のコードで写しの中でやり直して、1 バイトも同じかをくらべる (トークン 0。本物の data にはさわらない)

  PYTHONUTF8=1 python3.13 sim/society/tools/exp4_replay.py --commits 689c3c0b,6d0aefc7 [--arm B0] [--work /tmp/exp4_replay]

- やり方は exp3_replay.py と同じ (歩のコミット C ごとに、C^ の state.json・archive/・app_data.json と C の答えを写しに置き、SOC_RECORDS=0 で step.py season を 1 回)。
- 組なし (--arm を書かない): state・app_data・archive・次の歩のお題が、本物と 1 バイトも同じか (exp3_replay.py の組なしと同じ確かめ)。
- --arm B0 / B1: step.py season の前に、写しの state に組を入れる (exp4.set_arm)。本物の答えには take の欄がないので、みな「取らない」になる。このとき:
  state は「g7.exp4 の 1 つの鍵のほかは同じ」か (だれも取らなければ、自動で取る決まりを止めても、この歩では世界は同じ)、
  次の歩のお題 (季節・気持ち) は「足した節と欄 (exp4.strip) を除けば同じ」か。まわりの集落のお題は同じはず。
- 戻り値: みな同じなら 0、どこかがちがえば 1。表を出す。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import exp3_replay as R  # noqa: E402
import exp4  # noqa: E402

D = R.D


def one(c, arm, work):
    par = subprocess.run(["git", "-C", str(R.ROOT), "rev-parse", c + "^"], capture_output=True, text=True).stdout.strip()
    w = Path(work) / f"{c}_{arm or 'off'}"
    if w.exists():
        shutil.rmtree(w)
    data, ref = w / "data", w / "ref"
    data.mkdir(parents=True)
    ref.mkdir()
    R.git_extract(par, [f"{D}/state.json", f"{D}/archive", f"{D}/app_data.json"], data)
    st0 = json.loads((data / "state.json").read_text(encoding="utf-8"))
    day = st0["day"]
    if R.has(c, f"{D}/answers/day{day:03d}"):
        R.git_extract(c, [f"{D}/answers/day{day:03d}"], data)
    R.git_extract(c, [f"{D}/state.json", f"{D}/archive", f"{D}/app_data.json"], ref)
    if arm:
        exp4.set_arm(st0, arm, "確かめ (exp4_replay)")
        (data / "state.json").write_text(json.dumps(st0, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    env = dict(os.environ, SOC_DATA=str(data), SOC_RECORDS="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(R.SOC / "step.py"), "season"], capture_output=True, text=True, env=env, cwd=str(R.SOC))
    out = {"commit": c, "day": day, "arm": arm or "off", "rc": r.returncode}
    st1 = json.loads((data / "state.json").read_text(encoding="utf-8"))
    new = st1["day"]
    if R.has(c, f"{D}/prompts/day{new:03d}"):
        R.git_extract(c, [f"{D}/prompts/day{new:03d}"], ref)
    if arm:
        x = st1["era2"]["g7"].pop("exp4", None)
        same = json.dumps(st1, ensure_ascii=False, separators=(",", ":")) == (ref / "state.json").read_text(encoding="utf-8")
        took = sum(v for s in (x or {}).get("acts", []) for row in s["rows"].values() for k, v in row.items() if k in ("村の蓄え", "よその家の倉"))
        out["state"] = "同じ (exp4 の鍵のほか)" if same and x and x["arm"] == arm and not took else "ちがう"
    else:
        out["state"] = "同じ" if R.sha(data / "state.json") == R.sha(ref / "state.json") else "ちがう"
    out["sha"] = R.sha(ref / "state.json")[:16]
    out["mine"] = R.sha(data / "state.json")[:16]
    out["app_data"] = "同じ" if R.sha(data / "app_data.json") == R.sha(ref / "app_data.json") else "ちがう"
    a, b = R.files(data / "archive"), R.files(ref / "archive")
    out["archive"] = "同じ" if a.keys() == b.keys() and all(R.sha(a[k]) == R.sha(b[k]) for k in a) else "ちがう"
    pa, pb = R.files(data / f"prompts/day{new:03d}"), R.files(ref / f"prompts/day{new:03d}")
    diff, added = [], 0
    for k in sorted(set(pa) | set(pb)):
        if k not in pa or k not in pb:
            diff.append(k)
            continue
        ta, tb = pa[k].read_text(encoding="utf-8"), pb[k].read_text(encoding="utf-8")
        if arm and not k.startswith("council/"):
            added += ta != tb
            ta = exp4.strip(ta)
        if ta != tb:
            diff.append(k)
    out["prompts"] = f"{len(pb)} 通" + (" 同じ" if not diff else f" ちがう {len(diff)} ({', '.join(diff[:3])})") + (f" (節を足した {added} 通)" if arm else "")
    out["ok"] = r.returncode == 0 and not diff and all(out[k].startswith("同じ") for k in ("state", "app_data", "archive"))
    if not os.environ.get("EXP4_KEEP"):
        shutil.rmtree(w)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commits", required=True, help="歩のコミット (コンマでつなぐ)")
    ap.add_argument("--arm", default=None, choices=[None, "B0", "B1"])
    ap.add_argument("--work", default="/tmp/exp4_replay")
    a = ap.parse_args()
    bad = 0
    print("| コミット | 歩の日 | 組 | state | sha256 (本物) | sha256 (やり直し) | app_data | archive | 次のお題 | 結果 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for c in a.commits.split(","):
        o = one(c.strip(), a.arm, a.work)
        bad += not o["ok"]
        print(f"| {o['commit']} | {o['day']} | {o['arm']} | {o['state']} | {o['sha']}… | {o['mine']}… | {o['app_data']} | {o['archive']} | {o['prompts']} | "
              f"{'OK' if o['ok'] else 'ちがう'} |", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
