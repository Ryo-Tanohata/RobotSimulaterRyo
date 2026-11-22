"""3D で見る (app/replay3d.js) のための、建てた物の一覧 (見るだけ。2026-11-22)

data/state.json を読むだけで、app/scene3d.json を書く。村の動き・state.json・data/ には一切さわらない。
中身 (どれも「いつから見せるか」の日):
  mills  水の輪 (G13 の粉ひきの輪。era2.g7.g13.mill.mills の id と作った日)
  ws     水の作業場 (G15。era2.g7.g15.ws の id・道具・作り始めた日・できた日。水の輪 M? の横に建つ)
  pit    燃える石の掘り場 (G15。掘る場所の id と、初めて掘った年のはじめの日)
  canal  水の道 (G13。初めて掘った年のはじめの日)
  board  村の知らせ板 (Society 3.0 フェーズ 3 の i4。立てた日と、季節ごとの知らせ: 日・家・字)
  stoves 石のかまど (G15。家ごとの、作りかえ終えた日)
state.json に鍵がなければ、その物は入れない (アプリはその物を描かない)。場所は state にないので、アプリが地図から決める。

使い方: cd sim/society && python3.13 tools/build_scene3d.py [state.json の場所]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
YEAR = 120  # era2.YEAR (4 季節 × 30 日)
OUT = os.path.join(ROOT, "app", "scene3d.json")


def build(S):
    g = ((S.get("era2") or {}).get("g7")) or {}
    out = {"made_day": S.get("day")}
    g13 = g.get("g13") or {}
    mills = ((g13.get("mill") or {}).get("mills")) or []
    if mills:
        out["mills"] = [{"id": m["id"], "day": m["day"]} for m in mills if m.get("day") is not None]
    dug = (g13.get("canal") or {}).get("dug") or {}
    if dug:
        out["canal"] = {"day": min(int(y) for y in dug) * YEAR}
    g15 = g.get("g15") or {}
    ws = g15.get("ws") or {}
    if ws:
        out["ws"] = [{"id": k, "tool": v.get("tool"), "day": v.get("day"), "done": v.get("done")} for k, v in sorted(ws.items(), key=lambda kv: kv[1].get("day") or 0)]
    coal = g15.get("coal") or {}
    if coal.get("placed") and coal.get("dug"):
        out["pit"] = {"place": coal.get("place"), "day": min(int(y) for y in coal["dug"]) * YEAR}
    st = g15.get("stoves") or {}
    if st:
        out["stoves"] = {h: v["done"] for h, v in sorted(st.items()) if v.get("done") is not None}
    i4 = g.get("i4") or {}
    if i4.get("day") is not None:
        notes = [{"day": n["day"], "house": n.get("house"), "text": n.get("text", "")}
                 for y in sorted(i4.get("notes") or {}, key=int) for n in i4["notes"][y]]
        out["board"] = {"day": i4["day"], "notes": notes}
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "state.json")
    with open(src, encoding="utf-8") as f:
        S = json.load(f)
    data = build(S)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"→ {os.path.relpath(OUT, ROOT)} ({S.get('day')} 日目まで。"
          + "・".join(f"{k} {len(v) if isinstance(v, (list, dict)) else 1}" for k, v in data.items() if k != "made_day") + ")")


if __name__ == "__main__":
    main()
