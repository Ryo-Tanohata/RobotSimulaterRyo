# 陪審員へのお題 prompts/<id>.md を、prompt.md（ひな形）・personas.json・jobs.json から作る（D08・D10）
#   python3.13 docs/humanity/jury/make_prompts.py          … 全員分を書く
#   python3.13 docs/humanity/jury/make_prompts.py --check  … 書かずに、今の prompts/ と 1 バイトも違わないかだけ確かめる
# ひな形の {PERSONA} に人物（label）、{NOTE} に人物の説明（note）、{ID} に陪審員の ID、
# {JOBS} に仕事の一覧（jobs.json の順に 1 行ずつ「- {id} {title}: {desc}」）を入れる
import json, pathlib, sys
here = pathlib.Path(__file__).parent

tpl = (here / "prompt.md").read_text(encoding="utf-8")
jobs = json.loads((here / "jobs.json").read_text(encoding="utf-8"))
personas = json.loads((here / "personas.json").read_text(encoding="utf-8"))
job_lines = "\n".join(f"- {j['id']} {j['title']}: {j['desc']}" for j in jobs)
check = "--check" in sys.argv

diff = []
for p in personas:
    text = (tpl.replace("{PERSONA}", p["label"]).replace("{NOTE}", p["note"])
               .replace("{JOBS}", job_lines).replace("{ID}", p["id"]))
    f = here / "prompts" / f"{p['id']}.md"
    b = text.encode("utf-8")
    if check:
        if not f.exists() or f.read_bytes() != b:
            diff.append(f.name)
    else:
        f.write_bytes(b)  # 改行は \n のまま（Windows でも \r\n にしない）

if check:
    print("同じ" if not diff else "違う: " + "、".join(diff), f"({len(personas)} 人)")
    sys.exit(1 if diff else 0)
print("書いた", len(personas), "人")
