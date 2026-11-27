"""しくみの説明の動画 (2026-11-27 本人「このシミュレータとエージェントの説明をする動画を作って。音声はめたん」)。
   python3.13 make.py <作業フォルダ> [VOICEVOX の保存先 (既定 /tmp/vv)]
   台本は lines.json (id・title・bullets・img・text)。img は作業フォルダ/frames/<名前>.jpg (前に撮った動画から ffmpeg で取った 1 コマ。
   名前の最後が c なら下の字幕の帯を切る) か "diagram:<名前>" (ここで描く図)。
   → <作業フォルダ>/explainer.mp4 (1280x720・30 コマ/秒・音 -16 LUFS)。声・絵・動画はリポジトリに入れない。
   声: VOICEVOX:四国めたん (ノーマル、0.vvm の style 2)。村の記録 (data) は読まない。"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = Path(sys.argv[1]).resolve()
VV = sys.argv[2] if len(sys.argv) > 2 else "/tmp/vv"
W, H = 1280, 720
FONT = "/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf" if Path("/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf").exists() else "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
f = lambda s: ImageFont.truetype(FONT, s)
BG, INK, SUB, ACC, BOX = (250, 247, 240), (40, 36, 32), (110, 100, 90), (196, 84, 60), (255, 255, 255)
METAN = {"style": 2, "vvm": "0.vvm", "speed": 1.08, "pitch": 0.0, "intonation": 1.1}

lines = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))


def wrap(d, text, font, width):
    out, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > width:
            out.append(cur); cur = ch
        else:
            cur += ch
    return out + ([cur] if cur else [])


def boxes(d, items, y0, h=70, x0=40, x1=None):
    """縦に並んだ箱と矢印 (図)"""
    x1 = x1 or 660
    for i, (t, c) in enumerate(items):
        y = y0 + i * (h + 28)
        d.rounded_rectangle([x0, y, x1, y + h], 14, fill=c, outline=(120, 110, 100), width=2)
        for k, ln in enumerate(wrap(d, t, f(24), x1 - x0 - 30)[:2]):
            d.text((x0 + 16, y + 10 + k * 28), ln, font=f(24), fill=INK)
        if i < len(items) - 1:
            cx = (x0 + x1) // 2
            d.polygon([(cx - 10, y + h + 6), (cx + 10, y + h + 6), (cx, y + h + 22)], fill=SUB)


def diagram(name, size):
    im = Image.new("RGB", (700, 470), (244, 239, 228)); d = ImageDraw.Draw(im)
    G, B, Y, R = (214, 236, 214), (214, 226, 244), (248, 236, 200), (246, 216, 208)
    if name == "split":
        d.rounded_rectangle([20, 30, 330, 300], 18, fill=G, outline=SUB, width=2); d.rounded_rectangle([370, 30, 680, 300], 18, fill=B, outline=SUB, width=2)
        d.text((40, 50), "プログラム", font=f(32), fill=INK); d.text((390, 50), "AI (Claude)", font=f(32), fill=INK)
        for k, t in enumerate(["体・お腹・病気", "植物の実り", "動物の群れ", "天気・季節"]): d.text((50, 110 + k * 44), "・" + t, font=f(24), fill=INK)
        for k, t in enumerate(["仕事・行き先", "話すこと", "掟の提案と投票", "受け入れ・取引"]): d.text((400, 110 + k * 44), "・" + t, font=f(24), fill=INK)
        d.rounded_rectangle([170, 350, 530, 440], 18, fill=Y, outline=SUB, width=2); d.text((290, 378), "記録", font=f(32), fill=INK)
        d.line([(175, 300), (300, 350)], fill=SUB, width=4); d.line([(525, 300), (400, 350)], fill=SUB, width=4)
    elif name == "sources":
        for k, (t, s, c) in enumerate([("【体】", "2 足歩行のシミュレーションで測った値", G), ("【文献】", "研究の値 (狩猟採集民・江戸時代の村)", B), ("【仮定】", "試作のための置き値", R)]):
            y = 40 + k * 140; d.rounded_rectangle([30, y, 670, y + 110], 16, fill=c, outline=SUB, width=2)
            d.text((50, y + 14), t, font=f(34), fill=INK); d.text((50, y + 62), s, font=f(24), fill=INK)
    elif name == "prompt":
        d.rounded_rectangle([20, 30, 300, 430], 16, fill=BOX, outline=SUB, width=2); d.text((40, 45), "お題 (その人だけ)", font=f(24), fill=ACC)
        for k, t in enumerate(["いまのようす", "持ち物・蓄え", "覚えていること", "聞いた話", "家族", "決めること"]): d.text((40, 95 + k * 52), "・" + t, font=f(23), fill=INK)
        d.polygon([(310, 220), (370, 200), (370, 240)], fill=SUB); d.polygon([(390, 200), (390, 240), (450, 220)], fill=SUB)
        d.rounded_rectangle([460, 30, 680, 430], 16, fill=Y, outline=SUB, width=2); d.text((480, 45), "答え (JSON)", font=f(24), fill=ACC)
        for k, t in enumerate(['"仕事": 畑', '"行き先": 東の林', '"話": ...', '"掟": 賛成']): d.text((480, 100 + k * 52), t, font=f(22), fill=INK)
        d.text((330, 260), "AI", font=f(30), fill=INK)
    elif name == "time":
        for k, s in enumerate(["春", "夏", "秋", "冬"]):
            x = 30 + k * 165; d.rounded_rectangle([x, 60, x + 150, 200], 14, fill=[G, Y, R, B][k], outline=SUB, width=2)
            d.text((x + 55, 85), s, font=f(40), fill=INK); d.text((x + 35, 150), "30 日", font=f(26), fill=INK)
        d.text((40, 250), "1 年 = 120 日", font=f(40), fill=INK)
        d.text((40, 320), "年れい・子の間隔・寿命は", font=f(28), fill=SUB); d.text((40, 360), "縮めない", font=f(28), fill=SUB)
    elif name == "agents":
        d.rounded_rectangle([200, 20, 500, 100], 16, fill=Y, outline=SUB, width=2); d.text((225, 45), "まとめ役 (このセッション)", font=f(22), fill=INK)
        for k, (t, c) in enumerate([("進め役\n(haiku)", G), ("村人の係\n約 100", B), ("年報の係\n6 人", R), ("動画の係", G)]):
            x = 15 + k * 172; d.rounded_rectangle([x, 170, x + 155, 290], 14, fill=c, outline=SUB, width=2)
            for j, ln in enumerate(t.split("\n")): d.text((x + 14, 192 + j * 36), ln, font=f(24), fill=INK)
            d.line([(350, 100), (x + 77, 170)], fill=SUB, width=3)
        d.rounded_rectangle([150, 350, 550, 440], 16, fill=BOX, outline=SUB, width=2); d.text((175, 375), "本人 (大きな分かれ目で相談)", font=f(24), fill=ACC)
        d.line([(350, 100), (350, 350)], fill=ACC, width=3)
    elif name == "flow":
        boxes(d, [("① 進め役: 村のようすを読む (step.py who)", G), ("② 村人の係: 1 人に 1 つの AI が答える", B), ("③ 進め役: 30 日を計算して記録 (step.py season)", Y), ("④ 4 季節で 1 年 → 年報", R)], 15, h=82, x0=20, x1=680)
    elif name == "split2":
        d.rounded_rectangle([20, 30, 330, 360], 18, fill=B, outline=SUB, width=2); d.rounded_rectangle([370, 30, 680, 360], 18, fill=G, outline=SUB, width=2)
        d.text((40, 50), "クラウド (CPU)", font=f(28), fill=INK); d.text((390, 50), "本人の PC (GPU)", font=f(28), fill=INK)
        for k, t in enumerate(["村を回す", "年報・解説", "見せ方のコード", "絵コンテ"]): d.text((50, 110 + k * 50), "・" + t, font=f(24), fill=INK)
        for k, t in enumerate(["人のモデル作り", "本番の撮影", "撮影の報告"]): d.text((400, 110 + k * 50), "・" + t, font=f(24), fill=INK)
        d.text((150, 395), "同じブランチ: pull ⇄ push", font=f(28), fill=ACC)
    elif name == "faces":  # 年報の係の顔 (同じ作り方で作った村の人の絵)
        gd = ROOT / "sim/society/app/guide"
        for k, (n, lab) in enumerate([("sona85", "ソナ85 女 74 歳"), ("kio85", "キオ85 女 50 歳"), ("nase110", "ナセ110 女 30 歳"), ("nei75", "ネイ75 男 61 歳"), ("kese98", "ケセ98 男 39 歳")]):
            fp = gd / f"{n}_neutral.png"
            x, y = 20 + (k % 3) * 228, 20 + (k // 3) * 225
            if fp.exists():
                fc = Image.open(fp).convert("RGB").resize((170, 170)); im.paste(fc, (x + 20, y))
            d.text((x + 10, y + 178), lab, font=f(20), fill=INK)
        d.text((480, 280), "顔の絵も", font=f(22), fill=SUB); d.text((480, 310), "同じ作り方", font=f(22), fill=SUB)
    elif name == "build":
        boxes(d, [("VRoid のサンプル (体・顔・髪の部品)", B), ("記録から決めた設定 (顔・肌・体つき・年れい)", Y), ("Blender で組み立てて、服を着せる", G), ("人のモデル (glb) 1 人 1 つ", R)], 15, h=82, x0=20, x1=680)
    elif name == "rules":
        boxes(d, [("村のデータは手で書きかえない", R), ("記録にない絵は「描きそえ」と書く", Y), ("動画・モデルは公開の場に入れない", B), ("大きな分かれ目は本人に聞く", G)], 15, h=82, x0=20, x1=680)
    im.thumbnail(size)
    return im


def picture(spec, size):
    if spec.startswith("diagram:"):
        return diagram(spec[8:], size)
    name = spec[:-1] if spec.endswith("c") and not (OUT / "frames" / f"{spec}.jpg").exists() else spec
    im = Image.open(OUT / "frames" / f"{name}.jpg").convert("RGB")
    if name != spec:  # 下の字幕の帯を切る
        im = im.crop((0, 0, im.width, int(im.height * 0.78)))
    im.thumbnail(size)
    return im


def slide(ln, path):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 78], fill=(62, 54, 46)); d.text((36, 18), ln["title"], font=f(38), fill=(255, 250, 240))
    y = 120
    for b in ln["bullets"]:
        rows = wrap(d, b, f(27), 470)
        d.ellipse([36, y + 10, 48, y + 22], fill=ACC)
        for r in rows:
            d.text((60, y), r, font=f(27), fill=INK); y += 38
        y += 16
    pic = picture(ln["img"], (700, 470))
    x, py = 548 + (700 - pic.width) // 2, 100 + (470 - pic.height) // 2
    d.rectangle([x - 4, py - 4, x + pic.width + 3, py + pic.height + 3], fill=(200, 192, 180)); im.paste(pic, (x, py))
    d.rectangle([0, 586, W, H], fill=(30, 28, 26))  # 字幕 (入りきる大きさの字を選ぶ)
    for fs in (26, 23, 20):
        rows = wrap(d, ln["text"], f(fs), W - 70)
        if len(rows) * (fs + 7) <= H - 596:
            break
    for k, r in enumerate(rows):
        d.text((35, 594 + k * (fs + 7)), r, font=f(fs), fill=(255, 255, 255))
    im.save(path)


def run(cmd):
    subprocess.run(cmd, check=True)


OUT.mkdir(parents=True, exist_ok=True)
speak = [{"id": ln["id"], "text": ln["text"], **METAN} for ln in lines]
(OUT / "lines_voice.json").write_text(json.dumps(speak, ensure_ascii=False, indent=1), encoding="utf-8")
import os
SLIDES = os.environ.get("SLIDES_ONLY") == "1"  # 絵だけ作って見る
if not SLIDES and not (OUT / "voice" / "durations.json").exists():
    run(["nice", "-n", "19", f"{VV}/venv/bin/python", str(ROOT / "tools/voicevox/synth.py"), str(OUT / "lines_voice.json"), str(OUT / "voice"), VV])
for ln in lines:
    slide(ln, OUT / f"{ln['id']}.png")
end = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(end)
for k, t in enumerate(["川辺の村 ― しくみの説明", "", "ナレーション: VOICEVOX:四国めたん", "村の動画の人のモデル: VRoid の CC0 サンプル (pixiv) をもとに作成",
                       "動き: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)", "描画: three.js (MIT License)", "村の人の考え: Claude (Anthropic)"]):
    d.text((80, 160 + k * 52), t, font=f(34 if k == 0 else 26), fill=INK)
end.save(OUT / "s99.png")
if SLIDES:
    sys.exit(0)
lst = []
for ln in lines:
    i = ln["id"]
    run(["nice", "-n", "19", "ffmpeg", "-loglevel", "error", "-y", "-threads", "2", "-loop", "1", "-i", str(OUT / f"{i}.png"), "-i", str(OUT / "voice" / f"{i}.wav"),
         "-af", "adelay=300|300,apad=pad_dur=0.7", "-c:v", "libx264", "-threads", "2", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", "-shortest", str(OUT / f"seg_{i}.mp4")])
    lst.append(f"file 'seg_{i}.mp4'")
run(["nice", "-n", "19", "ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-i", str(OUT / "s99.png"), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "5",
     "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", str(OUT / "seg_99.mp4")])
lst.append("file 'seg_99.mp4'")
(OUT / "list.txt").write_text("\n".join(lst) + "\n")
run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "list.txt"), "-c", "copy", str(OUT / "raw.mp4")])
run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(OUT / "raw.mp4"), "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "48000", "-b:a", "160k", str(OUT / "explainer.mp4")])
print("できた:", OUT / "explainer.mp4")
