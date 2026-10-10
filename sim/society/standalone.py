"""アプリ (app/index.html) を、データごと 1 つの HTML ファイルにまとめる (サーバーなしで開ける。three.js などは CDN から読む)

  python sim/society/standalone.py                          今の state.json から _site/society_view.html を作る
  python sim/society/standalone.py --state 別の/state.json --out 出力.html
"""
import argparse
import json
import pathlib
import tempfile

import archive
import step

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(HERE / "data" / "state.json"))
    ap.add_argument("--out", default=str(ROOT / "_site" / "society_view.html"))
    a = ap.parse_args()
    state = archive.full(json.loads(pathlib.Path(a.state).read_text(encoding="utf-8")), pathlib.Path(a.state).parent)  # しまった古い年も入れる (1 つの HTML にまとめるので)
    with tempfile.TemporaryDirectory() as tmp:
        step.DATA = pathlib.Path(tmp) / "data"
        step.DATA.mkdir()
        step.export(state)
        data = (step.DATA / "app_data.json").read_text(encoding="utf-8")
    app = HERE / "app"
    html = (app / "index.html").read_text(encoding="utf-8")
    walk = (app / "walk_cycle.json").read_text(encoding="utf-8")
    js = (app / "replay3d.js").read_text(encoding="utf-8")
    # fetch("app_data.json") などを、埋め込んだデータで答える
    shim = ("<script>(function(){const D={\"app_data.json\":%s,\"walk_cycle.json\":%s};const f=window.fetch.bind(window);"
            "window.fetch=(u,o)=>{const k=String(u).split('/').pop();return k in D?Promise.resolve(new Response(JSON.stringify(D[k]),"
            "{status:200,headers:{'Content-Type':'application/json'}})):f(u,o);};})();</script>\n") % (data.replace("</", "<\\/"), walk)
    html = html.replace('<script src="replay3d.js"></script>', shim + "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>", 1)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
