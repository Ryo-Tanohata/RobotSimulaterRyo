"""Society 3.0 案 A の確かめ (2026-11-17。docs/society_phase/S3_check.md 1.): 前の歩が 1 バイトも変わらないか (トークン 0。本物の data にはさわらない)

  PYTHONUTF8=1 python3.13 sim/society/tools/s3_replay.py --old /tmp/s3work/oldcode/sim/society --commits 02168569,d85182fe [--work /tmp/s3_replay]

- 歩のコミット C ごとに、1 つ前のコミット (C^) の state.json・archive/・app_data.json と、C の answers/dayN を、写しのフォルダ 2 つに出す。
  1 つは今のコード (このファイルのとなりの step.py)、もう 1 つは前のコード (--old の step.py。git archive で出したもの) で、
  どちらも PYTHONHASHSEED=0・SOC_RECORDS=0 で step.py season を 1 回動かす。
- くらべるもの: 今のコード = 前のコード (state.json のバイト・app_data.json・archive/ のファイル・次の歩のお題 (季節・気持ち・まわりの集落))。
  本物 (C の state.json) とも、バイトと中身 (JSON を読んだもの) をくらべる (G15_push.md 7.2 の注意: 2 つめの作業場の家の表は set の順なので、
  バイトは PYTHONHASHSEED でかわることがある。中身は同じ)。
- 戻り値: 今のコード = 前のコードが、みな同じなら 0。
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOC = HERE.parent
ROOT = SOC.parent.parent
D = "sim/society/data"


def git_extract(rev, paths, dest):
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


def same_tree(a, b):
    fa, fb = files(a), files(b)
    return fa.keys() == fb.keys() and all(sha(fa[k]) == sha(fb[k]) for k in fa)


def run(code, data):
    env = dict(os.environ, SOC_DATA=str(data), SOC_RECORDS="0", PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0")
    return subprocess.run([sys.executable, str(Path(code) / "step.py"), "season"], capture_output=True, text=True, env=env, cwd=str(code))


def one(c, old, work):
    par = subprocess.run(["git", "-C", str(ROOT), "rev-parse", c + "^"], capture_output=True, text=True).stdout.strip()
    w = Path(work) / c
    if w.exists():
        shutil.rmtree(w)
    dn, do, ref = w / "new", w / "old", w / "ref"
    for x in (dn, do, ref):
        x.mkdir(parents=True)
    for x in (dn, do):
        git_extract(par, [f"{D}/state.json", f"{D}/archive", f"{D}/app_data.json"], x)
    day = json.loads((dn / "state.json").read_text(encoding="utf-8"))["day"]
    if has(c, f"{D}/answers/day{day:03d}"):
        for x in (dn, do):
            git_extract(c, [f"{D}/answers/day{day:03d}"], x)
    git_extract(c, [f"{D}/state.json"], ref)
    rn, ro = run(SOC, dn), run(old, do)
    st = json.loads((dn / "state.json").read_text(encoding="utf-8"))
    new = st["day"]
    out = {"commit": c, "day": day, "to": new, "rc": (rn.returncode, ro.returncode)}
    out["state"] = "同じ" if sha(dn / "state.json") == sha(do / "state.json") else "ちがう"
    out["app"] = "同じ" if sha(dn / "app_data.json") == sha(do / "app_data.json") else "ちがう"
    out["archive"] = "同じ" if same_tree(dn / "archive", do / "archive") else "ちがう"
    pn, po = files(dn / f"prompts/day{new:03d}"), files(do / f"prompts/day{new:03d}")
    diff = [k for k in sorted(set(pn) | set(po)) if k not in pn or k not in po or sha(pn[k]) != sha(po[k])]
    out["prompts"] = f"{len(pn)} 通" + (" 同じ" if not diff else f" ちがう {len(diff)}")
    out["real_bytes"] = "同じ" if sha(dn / "state.json") == sha(ref / "state.json") else "ちがう"
    out["real_json"] = "同じ" if st == json.loads((ref / "state.json").read_text(encoding="utf-8")) else "ちがう"
    out["sha"] = sha(dn / "state.json")[:16]
    out["s3"] = "s3" in st["era2"].get("g7", {}) if st.get("era2") else False
    out["ok"] = rn.returncode == ro.returncode == 0 and not diff and all(out[k] == "同じ" for k in ("state", "app", "archive")) and not out["s3"]
    if not out["ok"]:
        out["err"] = (rn.stderr[-300:], ro.stderr[-300:])
    if not os.environ.get("S3_KEEP"):
        shutil.rmtree(w)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commits", required=True)
    ap.add_argument("--old", required=True, help="前のコードの sim/society (step.py のあるフォルダ)")
    ap.add_argument("--work", default="/tmp/s3_replay")
    a = ap.parse_args()
    bad = 0
    print("| コミット | 歩の日 → 次 | 今のコード = 前のコード (state のバイト) | app_data | archive | 次のお題 | 本物とくらべて (中身) | 本物とくらべて (バイト) | sha256 (今のコード) | 結果 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for c in a.commits.split(","):
        o = one(c.strip(), a.old, a.work)
        bad += not o["ok"]
        print(f"| {o['commit']} | {o['day']} → {o['to']} | {o['state']} | {o['app']} | {o['archive']} | {o['prompts']} | {o['real_json']} | {o['real_bytes']} | "
              f"{o['sha']}… | {'OK' if o['ok'] else 'ちがう ' + str(o.get('err'))} |", flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
