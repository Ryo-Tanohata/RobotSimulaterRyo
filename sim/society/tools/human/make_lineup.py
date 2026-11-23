"""川辺の五人を横に並べた絵を作る (PIL だけ。Blender はいらない)。

build_person_vroid.py の --only lineup が書いた部品
(/dev/shm/sena/vroid/lineup/<名前>_body.png = 同じ縮尺の正面・背景は透明、<名前>_face.png = 正面の顔)
を、people.LINEUP の順 (本人の絵と同じ: ルオ・セナ・タヒ・ウィロ・イサ) に並べる。

    python3 make_lineup.py [--out sim/society/out/human/kawabe_five_vroid.png]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from people import VROID, LINEUP  # noqa: E402

WORK = os.environ.get("VROID_WORK", "/dev/shm/sena/vroid")
BG = (174, 179, 187)
FONTS = ["/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"]


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "sim", "society", "out", "human", "kawabe_five_vroid.png"))
    ap.add_argument("--step", type=int, default=440, help="体どうしの間 (px)。腕は重なってよい")
    a = ap.parse_args()
    d = os.path.join(WORK, "lineup")
    bodies = [Image.open(os.path.join(d, n + "_body.png")).convert("RGBA") for n in LINEUP]
    faces = [Image.open(os.path.join(d, n + "_face.png")).convert("RGB") for n in LINEUP]
    bw, bh = bodies[0].size
    fs = a.step - 8
    W = a.step * (len(LINEUP) - 1) + bw
    lab = 60
    H = bh + lab + fs + 20
    sheet = Image.new("RGBA", (W, H), BG + (255,))
    # 体: 左から順に重ねる (となりの腕が手前に来るのは右の人)
    for i, im in enumerate(bodies):
        sheet.alpha_composite(im, (i * a.step, 0))
    dr = ImageDraw.Draw(sheet)
    f = font(30)
    for i, n in enumerate(LINEUP):
        cx = i * a.step + bw // 2
        label = VROID[n]["label"].split(" ")[0]
        sub = VROID[n]["label"].split("(")[-1].rstrip(")")
        tw = dr.textlength(label, font=f)
        dr.text((cx - tw / 2, bh - 10), label, fill=(30, 30, 34), font=f)
        tw2 = dr.textlength(sub, font=font(18))
        dr.text((cx - tw2 / 2, bh + 26), sub, fill=(60, 60, 66), font=font(18))
        fc = faces[i].resize((fs, fs), Image.LANCZOS)
        sheet.paste(fc, (cx - fs // 2, bh + lab + 10))
    sheet.convert("RGB").save(a.out)
    print("lineup", a.out, sheet.size)


if __name__ == "__main__":
    main()
