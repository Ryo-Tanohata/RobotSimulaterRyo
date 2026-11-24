"""年報の動画の絵コンテ (本番の前に本人に見てもらう。HANDOFF の §3 の決まり)。
   python3.13 storyboard.py <作業フォルダ> <出力の名前 (拡張子なし。例 sim/society/video/out/storyboard_yearly_250)> [小さな JSON の出力]
   作業フォルダには script.json・<id>.png・s99.png・voice/durations.json (声の長さ) が要る。
   → <名前>.html (1 行 1 文: 番号・時刻・話す人・顔・字幕・読み・図・絵。絵を中に入れるので git に入れない)
     <名前>.jpg (絵を並べた 1 枚。git に入れない)
     小さな JSON (絵のない版。git に入れてよい。既定 sim/society/video/storyboards/storyboard_yearly_<年>.json)
時刻は動画と同じ決め: 1 文 = 前に 0.3 秒 + 声の長さ + 後ろに 0.8 秒。最後にクレジット 5 秒。"""
import base64
import html
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PRE, POST, CREDIT = 0.3, 0.8, 5.0
EXPR_JA = {"neutral": "ふつう", "smile": "笑顔", "concern": "心配", "surprise": "おどろき"}
WORK = Path(sys.argv[1])
NAME = Path(sys.argv[2])
S = json.load(open(WORK / "script.json", encoding="utf-8"))
Y = S["year"]
SMALL = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parents[1] / "storyboards" / f"storyboard_yearly_{Y}.json"
DUR = json.load(open(WORK / "voice" / "durations.json", encoding="utf-8"))
FONT = next((f for f in ("/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf") if Path(f).exists()), None)

rows, t = [], 0.0
for ln in S["lines"]:
    d = PRE + DUR[ln["id"]] + POST
    rows.append({**ln, "start": round(t, 2), "end": round(t + d, 2), "voice_sec": round(DUR[ln["id"]], 2)})
    t += d
rows.append({"id": "s99", "who": None, "name": "", "role": "クレジット", "expr": None, "text": "クレジット (声と人の絵の出どころ)", "say": "", "chart": "credits",
             "kind": "credits", "start": round(t, 2), "end": round(t + CREDIT, 2), "voice_sec": 0})
total = t + CREDIT


def jpg(p, w=480):
    im = Image.open(p).convert("RGB")
    im = im.resize((w, w * im.height // im.width), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=80)
    return base64.b64encode(b.getvalue()).decode("ascii")


def mmss(s):
    return f"{int(s // 60)}:{s % 60:04.1f}"


by_who = {}
for r in rows:
    if r["who"]:
        by_who.setdefault(r["name"], 0)
        by_who[r["name"]] += r["end"] - r["start"]
tr = "\n".join(
    f'<tr><td>{i + 1}<br><span class="s">{r["id"]}</span></td><td class="s">{mmss(r["start"])}–{mmss(r["end"])}<br>({r["end"] - r["start"]:.1f} 秒)</td>'
    f'<td><b>{html.escape(r["name"])}</b><br>{html.escape(r["role"])}</td><td>{EXPR_JA.get(r["expr"], "")}</td>'
    f'<td>{html.escape(r["text"])}<div class="say">読み: {html.escape(r["say"])}</div></td><td class="s">{html.escape(r["chart"])}</td>'
    f'<td><img src="data:image/jpeg;base64,{jpg(WORK / (r["id"] + ".png"))}"></td></tr>' for i, r in enumerate(rows))
who = "・".join(f"{k} {v:.0f} 秒" for k, v in by_who.items())
NAME.parent.mkdir(parents=True, exist_ok=True)
NAME.with_suffix(".html").write_text(f"""<!doctype html><meta charset="utf-8"><title>絵コンテ 年報の動画 {Y}年</title>
<style>body{{font-family:sans-serif;margin:16px;color:#222}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:6px;vertical-align:top;font-size:14px}}
th{{background:#f3efe6}} img{{width:480px}} .s{{color:#666;font-size:12px;white-space:nowrap}} .say{{color:#777;font-size:12px;margin-top:4px}}</style>
<h1>絵コンテ: 川辺の村 {Y}年 年報の動画</h1>
<p>全体 {mmss(total)} ({total:.1f} 秒)・{len(rows) - 1} 文 + クレジット。1280×720。1 文 = 声の前 {PRE} 秒 + 声 + 後ろ {POST} 秒。話す長さ: {html.escape(who)}</p>
<p>見てほしいところ: 文の順と中身・話す人と顔つき・図が文に合っているか・字幕の折り方・読み (読みがおかしい言葉は tools/voicevox/user_dict.json に足す)。</p>
<table><tr><th>#</th><th>時刻</th><th>話す人</th><th>顔</th><th>字幕 (読み)</th><th>図</th><th>絵</th></tr>
{tr}
</table>""", encoding="utf-8")

# 絵を並べた 1 枚 (4 列)
cols, tw, th = 4, 400, 225
n = len(rows)
sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, ((n + cols - 1) // cols) * (th + 30) + 60), "#ffffff")
dr = ImageDraw.Draw(sheet)
f1 = ImageFont.truetype(FONT, 22) if FONT else None
f2 = ImageFont.truetype(FONT, 15) if FONT else None
dr.text((10, 14), f"絵コンテ 川辺の村 {Y}年 年報の動画 (全体 {mmss(total)})", font=f1, fill="#222")
for i, r in enumerate(rows):
    x, y = 8 + (i % cols) * (tw + 8), 56 + (i // cols) * (th + 30)
    sheet.paste(Image.open(WORK / (r["id"] + ".png")).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
    dr.text((x, y + th + 4), f"{i + 1}. {mmss(r['start'])} {r['name']} {EXPR_JA.get(r['expr'], '')} [{r['chart']}]", font=f2, fill="#333")
sheet.save(NAME.with_suffix(".jpg"), quality=85)

SMALL.parent.mkdir(parents=True, exist_ok=True)
SMALL.write_text(json.dumps({"item": f"yearly_{Y}", "year": Y, "duration": round(total, 2), "size": [1280, 720],
                             "cuts": [{k: r.get(k) for k in ("id", "start", "end", "voice_sec", "who", "name", "role", "expr", "chart", "kind", "text", "say")} for r in rows]},
                            ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"絵コンテ: {NAME.with_suffix('.html')} / {NAME.with_suffix('.jpg')} / {SMALL} (全体 {total:.1f} 秒)")
