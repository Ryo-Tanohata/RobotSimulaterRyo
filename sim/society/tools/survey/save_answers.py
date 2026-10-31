"""論文 2・実験 1: Workflow (survey_workflow.js) の答えを answers/<ID>.json に分けて書く。

    python3 save_answers.py [--dir answers_pilot] <file> [<file> ...]              # 実験 1 (C0〜C4 → answers/)
    python3 save_answers.py --exp 2 [--dir answers_exp2_pilot] <file> [<file> ...]  # 実験 2 (D1〜D3 → answers_exp2/)
    python3 save_answers.py --exp 2b [--dir answers_exp2b_pilot] <file> [<file> ...]  # 実験 2b (E1・D2r → answers_exp2b/)

<file> は、Workflow の返した値を書いた JSON か、Workflow の記録 (journal.jsonl)。どちらでも、中をたどって
{"respondent_id": "C1_001", "answers": {...}} の形のものを拾う (文字列の中の JSON も読む)。
台本が確かめて包んだ答え (ok: true) があれば、それだけを使う。形の合わないもの (問いが足りない・1〜5 でない・ID が違う) は書かずに数える。すでに answers/ にある ID は上書きしない。
実験 2b の D2r は、D2 の紙をそのまま読むので、agent の生の答えの ID は D2_k。包んだ答えがないときだけ、D2_k を D2r_k として読む。
"""
import json
import os
import re
import sys

from items import CONDITIONS, IDS, REASON_ITEMS, conditions_of

HERE = os.path.dirname(os.path.abspath(__file__))
RID = re.compile(r"^([A-Z]\d[a-z]?)_(\d{3})$")


def walk(x, found):
    if isinstance(x, str):
        s = x.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                walk(json.loads(s), found)
            except ValueError:
                pass
    elif isinstance(x, list):
        for v in x:
            walk(v, found)
    elif isinstance(x, dict):
        if isinstance(x.get("respondent_id"), str) and isinstance(x.get("answers"), dict):
            found.append(x)
        for v in x.values():
            walk(v, found)


def normalize(obj, conds=CONDITIONS):
    """正しい形なら {"id","condition","model","answers":{A01:int},"honne":{...}|None} を、だめなら (None, わけ) を返す。
    実験 2 (conds に "reasons" がある条件) は "honne" のかわりに "reasons": {A08: 文, …} (わけが欠けても数は使う。空として数える)。"""
    rid = obj["respondent_id"].strip()
    m = RID.match(rid)
    if not m or m.group(1) not in conds or int(m.group(2)) > conds[m.group(1)]["n"]:
        return None, f"bad id {rid!r}"
    cond = m.group(1)
    honne_cond = conds[cond].get("honne", False)
    a, h = {}, {}
    for i in IDS:
        v = obj["answers"].get(i)
        if honne_cond:
            if not isinstance(v, dict):
                return None, f"{rid}: {i} not an object"
            h[i] = str(v.get("honne", ""))
            v = v.get("answer")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v or not 1 <= v <= 5:
            return None, f"{rid}: {i} = {v!r}"
        a[i] = int(v)
    if conds[cond].get("reasons"):
        rs = obj.get("reasons") if isinstance(obj.get("reasons"), dict) else {}
        return {"id": rid, "condition": cond, "model": obj.get("model") or conds[cond]["model"],
                "answers": a, "reasons": {i: str(rs.get(i) or "") for i in REASON_ITEMS}}, None
    return {"id": rid, "condition": cond, "model": obj.get("model") or conds[cond]["model"],
            "answers": a, "honne": h if honne_cond else None}, None


def main(paths, sub=None, exp=1):
    conds = conditions_of(exp)
    is2b = str(exp).lower() == "2b"
    if sub is None:
        sub = "answers_exp2b" if is2b else "answers" if int(exp) == 1 else "answers_exp2"
    found = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            txt = f.read()
        try:
            walk(json.loads(txt), found)
        except ValueError:  # jsonl
            for line in txt.splitlines():
                if line.strip():
                    try:
                        walk(json.loads(line), found)
                    except ValueError:
                        pass
    # 台本が確かめて包んだもの ({"id": …, "ok": true, "respondent_id": 同じ ID, …}) があれば、それだけを使う。
    # journal には、台本がはねた agent の生の答え (ID の違うものなど) も残っているため。
    wrapped = [o for o in found if o.get("ok") is True and o.get("id") == o.get("respondent_id")]
    if wrapped:
        found = wrapped
    elif is2b:
        # 包んだ答えがない: D2r の生の答え (紙の ID D2_k) を D2r_k にする (実験 2b に D2 の条件はないので、まざらない)
        alias = {v["prompt_of"]: c for c, v in conds.items() if v.get("prompt_of")}
        for o in found:
            m = RID.match(str(o["respondent_id"]).strip())
            if m and m.group(1) in alias:
                o["respondent_id"] = f"{alias[m.group(1)]}_{m.group(2)}"
    d = os.path.join(HERE, sub)
    os.makedirs(d, exist_ok=True)
    wrote, kept, bad = 0, 0, []
    seen = set()
    for obj in found:
        r, why = normalize(obj, conds)
        if r is None:
            bad.append(why)
            continue
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out = os.path.join(d, f"{r['id']}.json")
        if os.path.exists(out):
            kept += 1
            continue
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=0)
        wrote += 1
    have = {fn[:-5] for fn in os.listdir(d) if fn.endswith(".json")}
    missing = [f"{c}_{k:03d}" for c, v in conds.items() for k in range(1, v["n"] + 1) if f"{c}_{k:03d}" not in have]
    print(f"found {len(found)} answer objects; wrote {wrote}; already there {kept}; invalid {len(bad)}")
    for b in sorted(set(bad))[:20]:
        print("  invalid:", b)
    print(f"{sub}/ has {len(have)} of {sum(v['n'] for v in conds.values())}; missing {len(missing)}")
    if missing:
        print("  missing:", " ".join(missing[:50]) + (" …" if len(missing) > 50 else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    argv = sys.argv[1:]
    sub, exp = None, 1
    while argv[:1] in (["--dir"], ["--exp"]):
        if argv[0] == "--dir":
            sub = argv[1]
        else:
            exp = argv[1] if argv[1].lower() == "2b" else int(argv[1])
        argv = argv[2:]
    main(argv, sub, exp)
