"""クラウドで作る軽い動画 (3D なし): 文ごとに 1 枚の絵 (日付・人と蓄えのグラフ・字幕) と声をつなぐ。2026-10-27 本人の希望 (3D の動画は本人の PC で撮る)
使い方: python3.13 lite_video.py <名前 (G7 など)> <題> [出力.mp4]
読むもの: narration_<名前>.json・voice/<名前>/nXX.wav・durations.json、記録 ../data/records/season_village.jsonl
【シ】の数は出さない (人の数と蓄えの日数だけ)"""
import json, os, subprocess, sys, tempfile, textwrap, wave

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
YEAR, GAP = 120, 0.6  # この世界の 1 年 = 120 日。文と文のあいだの間 (秒)
W, H, DPI = 1280, 720, 100
for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"):
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
INK, MUTED, GRID, BG = "#1f2328", "#6e7781", "#e6e8eb", "#ffffff"
C_POP, C_STORE, C_MARK = "#2f6db5", "#c2702a", "#b42318"


def date_label(d):
    return f"{d // YEAR}年{d % YEAR + 1}日目"


def series(lo, hi):
    rows = []
    with open(os.path.join(HERE, "..", "data", "records", "season_village.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if lo - YEAR <= r["season_end_day"] <= hi + 30:
                rows.append((r["season_end_day"], r["population"], r.get("store_days") or 0))
    return rows


def frame(path, title, line, day, rows, lo, hi):
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=BG)
    fig.text(0.04, 0.93, title, fontsize=20, color=INK)
    fig.text(0.96, 0.93, date_label(day), fontsize=20, color=INK, ha="right")
    fig.text(0.96, 0.895, "この世界の 1 年は 120 日", fontsize=10, color=MUTED, ha="right")
    xs = [r[0] / YEAR for r in rows]
    for i, (k, lab, col) in enumerate(((1, "村の人", C_POP), (2, "蓄え (日分)", C_STORE))):
        ax = fig.add_axes([0.06 + i * 0.48, 0.42, 0.40, 0.40])
        ax.plot(xs, [r[k] for r in rows], color=col, lw=2)
        ax.axvline(day / YEAR, color=C_MARK, lw=1.5)
        ys = [r[k] for r in rows if r[0] <= day]
        if ys:
            ax.plot([day / YEAR], [ys[-1]], "o", ms=8, color=col, mec=BG, mew=2)
            ax.annotate(f"{ys[-1]:,}", (day / YEAR, ys[-1]), xytext=(8, 8), textcoords="offset points", fontsize=12, color=INK)
        ax.set_title(lab, loc="left", fontsize=13, color=INK)
        ax.set_xlim(lo / YEAR, hi / YEAR)
        ax.set_ylim(bottom=0)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(True, color=GRID, lw=0.8)
        ax.set_xlabel("年", fontsize=10, color=MUTED)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=10)
    wrapped = "\n".join(textwrap.wrap(line, 38))
    fig.text(0.5, 0.17, wrapped, fontsize=19, color=INK, ha="center", va="center", linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.6", fc="#f6f8fa", ec=GRID))
    fig.savefig(path, dpi=DPI, facecolor=BG)
    plt.close(fig)


def main():
    name, title = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "..", "app", f"society_{name}_lite.mp4")
    narr = json.load(open(os.path.join(HERE, f"narration_{name}.json"), encoding="utf-8"))
    vdir = os.path.join(HERE, "voice", name)
    dur = json.load(open(os.path.join(vdir, "durations.json"), encoding="utf-8"))
    lo, hi = min(n["day"] for n in narr), max(n["day"] for n in narr)
    if hi - lo < 3 * YEAR:  # 短い動画 (1〜2 年) は、前の 15 年も映して、どこから来たかを見せる
        lo = hi - 15 * YEAR
    rows = series(lo, hi)
    tmp = tempfile.mkdtemp(prefix=f"lite_{name}_")
    lst, params, pcm = [], None, b""
    for n in narr:
        png = os.path.join(tmp, f"{n['id']}.png")
        frame(png, title, n["text"], n["day"], rows, lo, hi)
        with wave.open(os.path.join(vdir, f"{n['id']}.wav")) as w:
            params = params or w.getparams()
            pcm += w.readframes(w.getnframes())
            pcm += b"\0" * int(GAP * params.framerate) * params.sampwidth * params.nchannels
        lst.append(f"file '{png}'\nduration {dur[n['id']] + GAP:.3f}")
    lst.append(f"file '{png}'")  # concat の最後の絵は長さを持たないので、もう一度書く
    open(os.path.join(tmp, "list.txt"), "w").write("\n".join(lst) + "\n")
    with wave.open(os.path.join(tmp, "voice.wav"), "wb") as w:
        w.setparams(params)
        w.writeframes(pcm)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "list.txt"),
                    "-i", os.path.join(tmp, "voice.wav"), "-c:v", "libx264", "-r", "25", "-pix_fmt", "yuv420p", "-crf", "28",
                    "-c:a", "aac", "-b:a", "128k", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", out], check=True)
    print(out)


if __name__ == "__main__":
    main()
