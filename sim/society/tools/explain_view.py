"""解説の係の文 (reports/explain/year<年>.json) を、年報のダッシュボードと統計のページに出すための小さな部品。

- 図の見かた (a): 図の下に小さな文 (図が変わらないかぎり毎年同じ)。
- 今年のポイント (b): 案内役 (いまの村の人) の顔の絵 + 吹き出し。顔は吹き出しごと (neutral・smile・concern・surprise)。
- まとめ役の 3 つ: ダッシュボードのいちばん上の箱。
絵は app/guide/guide_<名前>_<顔>.png (ほかの係が作る)。なければ仮の絵 (SVG)。年報は 1 つのファイルで送るので、絵は小さくして中に入れる (base64)。
解説の JSON がない年は何も出さない (前の年報は 1 バイトも変わらない)。作り: tools/explain_data.py・tools/explainer_workflow.js。
"""
import base64
import html
import io
import json
from pathlib import Path

import explain_data as XD

CSS = """
.xnote{font-size:11.5px;color:var(--ink2);line-height:1.45;margin:4px 0 2px;padding:3px 7px;border-left:3px solid var(--grid);background:transparent}
.xnote b{font-weight:600;color:var(--ink2)}
.xb{display:flex;gap:7px;align-items:flex-start;margin:6px 0 2px}
.xb img{width:40px;height:40px;border-radius:50%;flex:none;border:1px solid var(--ring);background:#f3efe6;object-fit:cover}
.xb .bl{position:relative;background:#fff7e0;border:1px solid #e9d39a;border-radius:10px;padding:5px 9px;font-size:12.5px;line-height:1.5;color:var(--ink)}
.xb .bl:before{content:"";position:absolute;left:-6px;top:12px;width:10px;height:10px;background:#fff7e0;border-left:1px solid #e9d39a;border-bottom:1px solid #e9d39a;transform:rotate(45deg)}
.xb .bl .who{display:block;font-size:10.5px;color:var(--muted)}
.xbs{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:2px 10px;margin-top:6px}
.x3{background:var(--surface);border:2px solid #e9d39a;border-radius:12px;padding:8px 10px 6px;margin:4px 0 10px}
.x3>b{font-size:14.5px;color:var(--ink)}
.x3 ol{margin:6px 0 2px;padding-left:22px}
.x3 li{margin:3px 0 6px;font-size:13.5px;line-height:1.5;color:var(--ink)}
.x3 li b{display:block;font-size:14px}
.x3 .xb{margin:2px 0 4px}
@media (prefers-color-scheme:dark){
 .xb .bl,.xb .bl:before{background:#2b2615;border-color:#6b5a2a}
 .xb img{background:#2b2615}
 .x3{border-color:#6b5a2a}
}
"""

FACE = {"neutral": "M17 29 q7 3 14 0", "smile": "M16 28 q8 7 16 0", "concern": "M17 31 q7 -4 14 0", "surprise": None}
BROW = {"neutral": "", "smile": "", "concern": '<path d="M14 16 l6 2 M34 16 l-6 2" stroke="#5a4632" stroke-width="1.6" fill="none"/>', "surprise": '<path d="M14 14 q4 -2 7 0 M27 14 q4 -2 7 0" stroke="#5a4632" stroke-width="1.6" fill="none"/>'}


def placeholder_svg(expr):
    """仮の顔の絵 (案内役の絵ができるまで)。顔つきだけ変える"""
    mouth = '<ellipse cx="24" cy="30" rx="3" ry="4" fill="#5a4632"/>' if FACE.get(expr) is None else f'<path d="{FACE[expr]}" stroke="#5a4632" stroke-width="2" fill="none" stroke-linecap="round"/>'
    s = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="#efe4cc"/>'
         '<path d="M6 48 q18 -14 36 0z" fill="#7a9a5a"/><circle cx="24" cy="22" r="13" fill="#f2cfa5"/>'
         '<path d="M11 19 q13 -14 26 0 q-2 -9 -13 -9 q-11 0 -13 9z" fill="#3d2f22"/>'
         f'<circle cx="19" cy="22" r="1.6" fill="#3d2f22"/><circle cx="29" cy="22" r="1.6" fill="#3d2f22"/>{BROW.get(expr, "")}{mouth}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode("utf-8")).decode("ascii")


def _embed(p, px=96):
    p = Path(p)
    if p.suffix == ".svg":
        return "data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    try:
        from PIL import Image
        im = Image.open(p).convert("RGBA")
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, 0, (w - s) // 2 + s, s)).resize((px, px), Image.LANCZOS)  # 顔は上のほうにあるので、上から四角く切る
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:  # noqa: BLE001  (絵が読めなければ仮の絵)
        return None


def guide_imgs():
    """顔 → 埋めこむ絵 (data: URL)。名前"""
    gi = XD.guide_info()
    out = {}
    for ex in XD.EXPRS:
        src = gi["imgs"].get(ex) or gi["imgs"].get("neutral")
        out[ex] = (_embed(src) if src else None) or placeholder_svg(ex)
    return gi["name"], out


def load(y):
    return XD.load_explain(y)


class View:
    """1 つの年の解説を HTML の部品にする。ex が None なら、どの部品も空 (年報は前と同じ)"""

    def __init__(self, ex):
        self.ex = ex
        self.placed = set()
        if ex:
            self.name, self.imgs = guide_imgs()
            if self.name == XD.PLACEHOLDER_NAME and (ex.get("guide") or {}).get("name"):
                self.name = ex["guide"]["name"]

    def note(self, cid):
        if not self.ex:
            return ""
        n = (self.ex.get("notes") or {}).get(cid)
        return f'<div class="xnote"><b>図の見かた</b> {html.escape(n["text"])}</div>' if n else ""

    def bubble(self, b):
        ex = b.get("expr") if b.get("expr") in self.imgs else "neutral"
        return (f'<div class="xb"><img src="{self.imgs[ex]}" alt="{html.escape(self.name)}"><div class="bl"><span class="who">{html.escape(self.name)}</span>'
                f'{html.escape(b["text"])}</div></div>')

    def bubbles(self, *cids):
        if not self.ex:
            return ""
        bs = [b for b in self.ex.get("bubbles") or [] if b["chart"] in cids]
        self.placed.update(cids)
        return "".join(self.bubble(b) for b in bs)

    def under(self, cid):
        """図の下: 図の見かた + その図の吹き出し"""
        return self.note(cid) + self.bubbles(cid)

    def rest(self):
        """まだ出していない図の吹き出し (統計のページの分野の話など) をまとめて"""
        if not self.ex:
            return ""
        bs = [b for b in self.ex.get("bubbles") or [] if b["chart"] not in self.placed]
        return ('<div class="xbs">' + "".join(self.bubble(b) for b in bs) + "</div>") if bs else ""

    def top3(self):
        if not self.ex or not self.ex.get("top3"):
            return ""
        li = "".join(f'<li><b>{html.escape(h["title"])}</b>{html.escape(h["text"])}</li>' for h in self.ex["top3"])
        first = self.ex["top3"][0]
        return (f'<div class="x3"><b>{self.ex["year"]}年の大事なこと 3 つ (解説の係のまとめ)</b>'
                + self.bubble({"expr": first.get("expr"), "text": f"{self.ex['year']}年の見どころを 3 つにまとめました。くわしくは下の図と、図の下の吹き出しで。"})
                + f"<ol>{li}</ol></div>")


def stats_payload(y_last):
    """統計のページに入れる解説 (いちばん新しい年の吹き出しと、図の見かた)。なければ None"""
    ex = None
    y = None
    for yy in range(y_last, y_last - 6, -1):  # 年の終わりのすぐあとで、まだ解説がないときは、近い年のもの
        ex = load(yy)
        if ex:
            y = yy
            break
    if not ex:
        return None
    name, imgs = guide_imgs()
    if name == XD.PLACEHOLDER_NAME and (ex.get("guide") or {}).get("name"):
        name = ex["guide"]["name"]
    used = {b.get("expr") for b in ex.get("bubbles") or []} | {"neutral"}
    by_field = {}
    for b in ex.get("bubbles") or []:
        if b.get("field"):
            by_field.setdefault(b["field"], []).append({"expr": b["expr"], "text": b["text"]})
    notes = {cid[2:]: n["text"] for cid, n in (ex.get("notes") or {}).items() if cid.startswith("f_")}
    return {"year": y, "name": name, "imgs": {k: v for k, v in imgs.items() if k in used}, "notes": notes, "bubbles": by_field,
            "top3": [{"title": h["title"], "text": h["text"]} for h in ex.get("top3") or []]}


if __name__ == "__main__":
    import sys
    print(json.dumps(stats_payload(int(sys.argv[1])), ensure_ascii=False)[:2000])
