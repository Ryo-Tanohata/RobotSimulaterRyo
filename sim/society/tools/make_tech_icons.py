"""テクノロジーツリーのアイコン (SVG) を作る。2026-10-29 本人の希望「文字ではなくアイコンを」。項目を足したら、ここに絵を足して動かす
使い方: python3.13 sim/society/tools/make_tech_icons.py"""
import json, os, sys
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "techtree", "icons")
os.makedirs(OUT, exist_ok=True)
F = 'fill="currentColor"'
def P(d, fill=False, w=None):
    a = f' {F}' if fill else ''
    if w: a += f' stroke-width="{w}"'
    return f'<path d="{d}"{a}/>'
def C(cx, cy, r, fill=False, w=None):
    a = f' {F}' if fill else ''
    if w: a += f' stroke-width="{w}"'
    return f'<circle cx="{cx}" cy="{cy}" r="{r}"{a}/>'
def person(x, y, s=1.0, fill=True):
    # head at (x,y), shoulders below
    r = 5*s
    return C(x, y, r, fill) + P(f"M{x-9*s:g} {y+20*s:g}v-3a{9*s:g} {9*s:g} 0 0 1 {18*s:g} 0v3", fill)

I = {}
# ---------------- テクノロジー ----------------
I['t_forage'] = ('槍と木の葉', P("M8 56L40 24") + P("M36 20L54 10L44 28Z", True) + P("M30 58c0-14 10-24 26-24 0 14-10 24-26 24z") + P("M30 58l16-14"))
I['t_store'] = ('穀物の穂を盛ったかご', P("M12 32h40l-6 24H18z") + P("M15 42h34M17 50h30") + P("M24 30L20 10M32 30V8M40 30L44 10") + C(20,12,3,True)+C(32,9,3,True)+C(44,12,3,True)+C(22,18,2.5,True)+C(32,16,2.5,True)+C(42,18,2.5,True))
I['t_settle'] = ('丸い草ぶき小屋', P("M8 54C8 32 20 14 32 8c12 6 24 24 24 46z") + P("M4 54h56") + P("M13 36q19-6 38 0M10 46q22-6 44 0", w=2.5) + P("M26 54V46a6 6 0 0 1 12 0v8", True))
I['t_fire'] = ('炎とたき木', P("M32 6c3 9 13 14 13 26a13 13 0 0 1-26 0c0-7 4-11 6-16 2 4 4 6 7 7 1-6 0-11 0-17z") + P("M32 27c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11z", True) + P("M10 58l44-9M10 49l44 9"))
I['t_farm'] = ('畝から出た芽', P("M4 50q28-10 56 0M4 59q28-10 56 0") + P("M32 46V22") + P("M32 34c-9 0-15-6-15-15 9 0 15 6 15 15z", True) + P("M32 26c0-9 6-16 15-16 0 9-6 16-15 16z", True))
I['t_herd'] = ('ヤギの頭（角とあごひげ）', P("M24 18C18 6 8 6 6 16M40 18c6-12 16-12 18-2") + P("M22 24l-12 2 12 6M42 24l12 2-12 6") + P("M22 16h20l-3 28c-2 8-12 8-14 0z") + C(27,27,2,True)+C(37,27,2,True) + P("M28 50l4 9 4-9"))
I['t_pot'] = ('模様のついた土器のつぼ', P("M22 8h20M25 8v7C14 21 12 38 19 48c5 7 21 7 26 0 7-10 5-27-6-33V8") + P("M16 32l5-5 5 5 5-5 5 5 5-5 5 5", w=3) + P("M18 41h28", w=2.5))
I['t_sickle'] = ('鎌（三日月の刃と柄）', P("M24 42C8 24 24 2 48 8c8 2 12 10 9 17C52 15 40 11 31 17c-8 6-9 16-3 25z", True) + P("M26 42L12 58", w=6))
I['t_house'] = ('切妻屋根と煙突の家', P("M6 32L32 8l26 24") + P("M12 27v29h40V27") + P("M42 17V8h7v15") + P("M27 56V42h10v14") + P("M17 34h6v6h-6z", w=2.5) + P("M41 34h6v6h-6z", w=2.5))
I['t_weave'] = ('機（はた）と織り目', P("M6 10h52M6 54h52") + P("M16 10v44M26 10v44M38 10v44M48 10v44", w=2.5) + P("M10 22c4-4 6 4 10 0s6 4 10 0 6 4 10 0 6 4 10 0 6 4 10 0M10 32c4 4 6-4 10 0s6-4 10 0 6-4 10 0 6-4 10 0 6-4 10 0M10 42c4-4 6 4 10 0s6 4 10 0 6 4 10 0 6 4 10 0 6 4 10 0"))
I['t_irrig'] = ('水路の断面と両岸の芽', P("M4 30h12l6 24h20l6-24h12") + P("M23 40q4-4 8 0t8 0t8 0M25 48q4-4 7 0t7 0t7 0", w=3) + P("M10 30V16M54 30V16") + P("M10 22c-5 0-7-3-7-7 5 0 7 3 7 7zM54 22c5 0 7-3 7-7-5 0-7 3-7 7z", True))
I['t_copper'] = ('銅のしずくと牛皮形の延べ板', P("M32 4c4 6 7 9 7 13a7 7 0 0 1-14 0c0-4 3-7 7-13z", True) + P("M8 28q24 8 48 0-6 13 0 26-24-8-48 0 6-13 0-26z", True) + P("M18 37q14 4 28 0", w=3))
I['t_record'] = ('刻み目（数え線）の粘土板', '<rect x="13" y="6" width="38" height="52" rx="6"/>' + P("M21 16v12M27 16v12M33 16v12M39 16v12M18 27l25-10M21 38v12M27 38v12M33 38v12", w=3))
I['t_plough'] = ('犂（柄・はり・刃先）と畝', P("M4 58q14-6 28 0t28 0M30 47q12-5 28 0", w=2.5) + P("M6 26L40 34") + P("M28 48L46 12h10", w=4.5) + P("M30 46L12 50l20 4z", True) + P("M6 18v16", w=4.5))
I['t_bronze'] = ('青銅の剣（木の葉形の刃とつば）', P("M32 4c6 8 7 18 4 34h-8c-3-16-2-26 4-34z", True) + P("M32 12v22", w=2) + P("M20 40h24", w=5) + P("M32 42v12") + C(32,57,3.5,True))
I['t_writing'] = ('記号を書いた板と尖筆', '<rect x="6" y="8" width="36" height="48" rx="5"/>' + P("M13 15h9l-4.5 8z", True) + P("M30 15v9M26 19.5h9", w=3) + C(17.5,34,3.5,w=3) + P("M27 30l7 7M34 30l-7 7", w=3) + P("M13 47h22", w=3) + P("M40 52L58 18", w=4) + P("M38 57l-1-7 5 2z", True))
I['t_iron'] = ('金づちと金床', P("M6 34h40v6c-5 1-8 4-8 9h6v7H18v-7h6c0-5-4-8-9-9-6-1-9-3-9-6z", True) + '<g transform="rotate(-35 34 16)">' + '<rect x="24" y="8" width="12" height="16" rx="1.5" fill="currentColor"/>' + P("M36 16h22", w=4.5) + '</g>')
I['t_coin'] = ('積んだ硬貨と穴あき銭', P("M6 52h20M6 46h20M6 40h20M6 34h20", w=3) + '<rect x="6" y="28" width="20" height="30" rx="3"/>' + C(42,34,15) + P("M38 30h8v8h-8z", True))
I['t_sail'] = ('帆かけ舟と波', P("M6 40h52l-8 12H14z") + P("M30 40V6") + P("M34 8l18 26H34z", True) + P("M26 12L14 34h12", w=3) + P("M4 58q6-4 12 0t12 0t12 0t12 0t12 0", w=3))
I['t_mill'] = ('水車（羽根つきの輪）と流れ', C(32,28,20) + C(32,28,4,True) + P("M32 8v40M12 28h40M18 14l28 28M46 14L18 42", w=2.5) + P("M4 58q7-5 14 0t14 0t14 0t14 0", w=3.5))
I['t_paper'] = ('巻物（上下の軸と文字列）', '<rect x="8" y="6" width="48" height="9" rx="4.5"/><rect x="8" y="49" width="48" height="9" rx="4.5"/>' + P("M14 15v34M50 15v34") + P("M20 24h24M20 32h24M20 40h16", w=3))
I['t_print'] = ('ねじ式の印刷機', P("M10 58V8h44v50M10 14h44") + P("M32 14v14M22 22h20", w=4) + '<rect x="20" y="28" width="24" height="6" fill="currentColor"/>' + P("M14 44h36", w=4) + P("M20 39h24", w=2.5))
I['t_steam'] = ('蒸気機関車（煙突と煙）', '<rect x="6" y="26" width="34" height="18" rx="4"/>' + P("M12 26V14h10v12") + P("M40 44V16h18v28H6") + '<rect x="45" y="21" width="8" height="7" fill="currentColor"/>' + C(16,51,6,True) + C(32,51,6,True) + C(50,51,6,True) + C(22,6,4,w=3) + C(33,5,3,w=3))
# ---------------- 社会制度 ----------------
I['s_share'] = ('二人が食べ物を半分ずつ分ける', person(12,18,1.0) + person(52,18,1.0) + P("M30 30a10 10 0 0 0 0 20z", True) + P("M34 30a10 10 0 0 1 0 20z", True) + P("M22 44h4M38 44h4", w=3))
def ring():
    import math
    s = ''
    for k in range(6):
        a = math.pi*2*k/6 - math.pi/2
        s += C(round(32+22*math.cos(a),1), round(32+22*math.sin(a),1), 5.5, True)
    return s
I['s_law'] = ('輪になった人々と中央の掟の石', ring() + C(32,32,22,w=2) + '<rect x="26" y="25" width="12" height="15" rx="3" fill="currentColor"/>')
I['s_join'] = ('開いた戸口へ入る人と矢印', P("M34 58V8h22v50") + P("M34 8l-8 6v38l8 6", True) + C(12,22,5,True) + P("M4 46v-6a8 8 0 0 1 16 0v6", True) + P("M14 54h16m-5-5 5 5-5 5", w=3))
I['s_home'] = ('家とかぎ', P("M4 28L22 12l18 16") + P("M9 24v22h26V24") + P("M18 46v-9h8v9") + C(42,42,7) + P("M42 49v12M42 55h6M42 60h4", w=4))
I['s_craft'] = ('交差したのこぎりと金づち（別々の道具）', P("M10 54L46 18", w=3) + P("M10 54l6-6M46 18l4 4-30 30-6-2z", True) + P("M54 54L22 22", w=4) + '<rect x="12" y="10" width="20" height="9" rx="1.5" fill="currentColor" transform="rotate(45 22 14.5)"/>')
I['s_elder'] = ('杖をつく長老と祭りの火', C(22,12,5,True) + P("M14 54V30a8 8 0 0 1 16 0v8") + P("M22 17v6l-3 6 3 3 3-3-3-6", w=2) + P("M34 58V14c0-4 6-4 6 0") + P("M30 32l4-2") + P("M52 34c2 5 6 7 6 12a6 6 0 0 1-12 0c0-3 2-5 3-8 1 2 2 3 3 3 0-3 0-5 0-7z", True) + P("M44 58l14-4M44 54l14 4", w=3))
I['s_leader'] = ('羽根飾りのまとめ役と従う人々', P("M24 12l2-8 4 6 2-8 2 8 4-6 2 8", w=3) + C(32,20,6,True) + P("M20 50V40a12 12 0 0 1 24 0v10", True) + person(8,38,0.7,False) + person(56,38,0.7,False))
I['s_penal'] = ('手かせと鎖と重い鉄球', C(15,15,9,w=5) + P("M21 22l5 5M29 30l5 5", w=3) + '<ellipse cx="27.5" cy="28.5" rx="5" ry="3" transform="rotate(45 27.5 28.5)" stroke-width="3"/>' + C(44,44,13,True))
I['s_trade'] = ('逆向きに行き交う二本の矢印と品物', P("M14 22h36m-8-8 8 8-8 8") + P("M50 42H14m8-8-8 8 8 8") + C(8,22,4,True) + '<rect x="52" y="38" width="8" height="8" fill="currentColor"/>')
I['s_credit'] = ('袋と、出て行って戻る矢印', P("M24 20h12l-2-6h-8z") + P("M24 20c-10 6-14 16-12 26 2 8 34 8 36 0 2-10-2-20-12-26", True) + P("M44 10c10 2 16 10 16 20m-5-4 5 4 4-5", w=3) + P("M20 58c-8 0-14-4-16-10m4 3-4-3-3 5", w=3))
I['s_town'] = ('城壁（狭間つき）と家並み', P("M8 28L16 18l8 10M24 30L32 16l8 14M40 28l8-10 8 10") + P("M10 28v8M22 28v8M26 30v6M38 30v6M42 28v8M54 28v8", w=3) + P("M4 58V40h7v5h7v-5h7v5h7v-5h7v5h7v-5h7v5h8v13z", True))
I['s_tribute'] = ('穀物を盛ったかごをささげ上げる手', P("M32 3v8m-5-5 5-5 5 5", w=3) + P("M18 24c2-8 26-8 28 0z", True) + P("M14 26h36l-5 18H19z") + P("M17 35h30", w=2.5) + P("M8 58l10-14h4M56 58L46 44h-4"))
I['s_state'] = ('王冠と印章', P("M8 40L6 14l14 12 12-18 12 18 14-12-2 26z", True) + P("M8 48h48") + '<rect x="24" y="52" width="16" height="8" rx="2" fill="currentColor"/>')
I['s_wlaw'] = ('上が丸い石碑（法の条文と印）', P("M14 60V20a18 18 0 0 1 36 0v40z") + P("M22 22h20M22 30h20M22 38h20", w=3) + C(32,50,4.5,True))
I['s_empire'] = ('月桂冠に囲まれた地球', C(32,30,12) + P("M20 30h24M32 18c-6 8-6 16 0 24 6-8 6-16 0-24", w=2.5) + P("M14 50C4 40 4 20 14 10M50 50c10-10 10-30 0-40", w=3) + P("M8 40c-4-2-5-5-4-8 4 1 5 4 4 8zM7 26c-4-2-4-6-2-8 3 2 4 5 2 8zM56 40c4-2 5-5 4-8-4 1-5 4-4 8zM57 26c4-2 4-6 2-8-3 2-4 5-2 8z", True) + P("M14 50l10 6h16l10-6", w=3))
I['s_market'] = ('しま模様の日よけの屋台と品物', P("M6 22L12 8h40l6 14z") + P("M22 8l-4 14M32 8v14M42 8l4 14", w=3) + P("M6 22c0 5 8 5 8 0 0 5 9 5 9 0 0 5 9 5 9 0 0 5 9 5 9 0 0 5 9 5 9 0", w=3) + P("M10 30v28M54 30v28M10 44h44") + C(22,38,4,True) + C(32,38,4,True) + C(42,38,4,True))
I['s_teach'] = ('開いた本と光', P("M32 30c-8-4-18-4-26 0v26c8-4 18-4 26 0 8-4 18-4 26 0V30c-8-4-18-4-26 0zM32 30v26") + P("M32 4v12M18 10l5 8M46 10l-5 8M8 20l8 4M56 20l-8 4", w=3))
I['s_manor'] = ('柵で囲った畑と鍬を持つ人', P("M4 34h40M4 46h40M8 28v30M24 28v30M40 28v30", w=3) + P("M6 24l12-10 12 6 14-8", w=2.5) + C(52,20,5,True) + P("M44 44v-8a8 8 0 0 1 16 0v8", True) + P("M58 26V58M58 58h-6", w=3))
I['s_commerce'] = ('てんびんと袋と硬貨', P("M32 8v46M20 58h24M8 16h48") + C(32,8,3,True) + P("M8 16l-6 16h12zM56 16l-6 16h12z", w=2.5) + P("M2 32a6 6 0 0 0 12 0M50 32a6 6 0 0 0 12 0", w=2.5) + P("M5 26c-2-4 2-6 3-6s5 2 3 6z", True) + C(56,27,3.5,True))

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'
plan = json.load(open('/home/user/RobotSimulaterRyo/sim/society/techtree/plan.json'))
techs = plan['techs']
ids = [t['id'] for t in techs]
missing = [i for i in ids if i not in I]
assert not missing, missing
index = {}
for t in techs:
    i = t['id']; desc, body = I[i]
    svg = HEAD + body + '</svg>\n'
    assert len(svg.encode()) < 2048, (i, len(svg))
    open(f'{OUT}/{i}.svg', 'w').write(svg)
    index[i] = {'file': f'{i}.svg', 'name': t['name'], 'tree': t['tree'], 'desc': desc}
json.dump(index, open(f'{OUT}/index.json', 'w'), ensure_ascii=False, indent=1)
# preview
cells = lambda: ''.join(f'<div class="c"><div class="i">{HEAD.replace("<svg ", "<svg width=56 height=56 ")}{I[t["id"]][1]}</svg></div><div class="n">{t["name"]}</div><div class="d">{t["id"]}</div></div>' for t in techs)
html = f'''<!doctype html><meta charset="utf-8"><title>tech tree icons</title>
<style>body{{margin:0;font-family:sans-serif}} .s{{padding:12px;display:grid;grid-template-columns:repeat(11,96px);gap:6px}}
.c{{text-align:center;padding:6px 0;border-radius:8px}} .n{{font-size:12px}} .d{{font-size:9px;opacity:.6}}
.light{{background:#fff;color:#2a2a2a}} .light .c{{background:#f2efe8}} .dark{{background:#16181d;color:#e8e4da}} .dark .c{{background:#23262e}}
.light .c:nth-child(3n) .i{{color:#2f7d32}} .dark .c:nth-child(3n) .i{{color:#e0b84a}}</style>
<div class="s light">{cells()}</div><div class="s dark">{cells()}</div>'''
open(f'{OUT}/preview.html', 'w').write(html)
print(len(ids), 'icons')
