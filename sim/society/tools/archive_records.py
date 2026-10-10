"""古い年の記録を data/archive/ の年ごとのファイルにしまう、1 回だけの移行 (2026-10-10 本人が決めた「古い記録を年ごとのファイルに分ける」。消さない)

  python3.13 sim/society/tools/archive_records.py [--data DIR] [--dry-run]

季節を進めていないときに動かす (季節の答えを集めているあいだや、step.py season の最中は動かさない)。
1. state.json を読み、しまってよい年 (今の年と、その前の 2 年より前の年) の記録を、まず data/archive_new/archive/ に書く
2. しまったあとの state と年のファイルから戻したものが、もとの state.json と 1 バイトもちがわないことを確かめる (ちがえば何も書きかえない)
3. 年のファイルを data/archive/ に移し、state.json を書きかえ、アプリ用のデータ (app_data.json と archive/days_YYYY.json) を作り直す
移行のあとは、step.py が季節の終わりに 1 年分ずつしまう。しまう年がなければ何もしない (何度動かしてもよい)。
内側の記録 (records/) とダッシュボードは、しまった記録も戻して読むので、作り直さなくても中身は同じ。
--dry-run: 確かめて大きさを表示するだけで、何も書きかえない
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import archive  # noqa: E402


def mb(n):
    return f"{n / 1e6:.1f} MB"


def size(p):
    p = Path(p)
    if p.is_dir():
        return sum(f.stat().st_size for f in p.iterdir() if f.is_file())
    return p.stat().st_size if p.exists() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("SOC_DATA") or str(HERE.parent / "data"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    data = Path(a.data)
    t0 = time.time()
    text = (data / "state.json").read_text(encoding="utf-8")
    st = json.loads(text)
    before = {"state.json": len(text.encode("utf-8")), "app_data.json": size(data / "app_data.json"), "archive": size(data / archive.DIR)}
    ref = archive._dump(archive.full(st, data))  # しまう前の全部 (もうしまってある state なら、戻したもの)
    stage = data / (archive.DIR + "_new")  # 書きかけの置き場所 (この下の archive/ に書く)
    if stage.exists():
        shutil.rmtree(stage)
    if (data / archive.DIR).exists():  # 前にしまった年も、確かめるために並べる
        shutil.copytree(data / archive.DIR, stage / archive.DIR)
    try:
        new = json.loads(text)
        ys = archive.move(new, stage, start=True)
        if not ys:
            print(f"しまう年はない ({st['day']} 日目。今の年と前の {archive.KEEP_YEARS} 年は残す)")
            return
        if archive._dump(archive.full(new, stage)) != ref:
            sys.exit("戻したものが、もとの state.json と合わない。何も書きかえない")
        small = archive._dump(new)
        print(f"{ys[0]}年〜{ys[-1]}年をしまう: state.json {mb(before['state.json'])} → {mb(len(small.encode('utf-8')))} "
              f"(年のファイル {mb(size(stage / archive.DIR))}。戻すと、もとと 1 バイトもちがわない)")
        if a.dry_run:
            print("--dry-run なので書きかえない")
            return
        (data / archive.DIR).mkdir(exist_ok=True)
        for y in ys:
            for k in archive.KINDS:
                f = archive.path(stage, k, y)
                if f.exists():
                    os.replace(f, archive.path(data, k, y))
                elif archive.path(data, k, y).exists():  # 前の試みの残り (その年に何もない種類)
                    archive.path(data, k, y).unlink()
        tmp = data / "state.json.tmp"
        tmp.write_text(small, encoding="utf-8")
        os.replace(tmp, data / "state.json")
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    import step  # アプリ用のデータを作り直す (しまった年は archive/ の年のファイルから)
    step.DATA = data
    step.export(new)
    print(f"app_data.json {mb(before['app_data.json'])} → {mb(size(data / 'app_data.json'))} / "
          f"archive/ {mb(before['archive'])} → {mb(size(data / archive.DIR))} ({len(list((data / archive.DIR).iterdir()))} ファイル) / "
          f"{time.time() - t0:.0f} 秒")


if __name__ == "__main__":
    main()
