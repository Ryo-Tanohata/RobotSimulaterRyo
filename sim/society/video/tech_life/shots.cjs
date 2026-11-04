// 動画の絵 (1 文 = 1 枚、1920x1080) を作る。node shots.cjs <作業フォルダ> "<記録の日>"
// 作業フォルダに tt.html (データを入れたテクノロジーツリーのページ)・tt.json・charts/*.png があること (make.sh が作る)。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.resolve(process.argv[2] || '.');
const ASOF = process.argv[3] || '';
const L = JSON.parse(fs.readFileSync(path.join(__dirname, 'lines.json'), 'utf8'));
const TT = JSON.parse(fs.readFileSync(path.join(OUT, 'tt.json'), 'utf8'));
const tech = Object.fromEntries(TT.techs.map(t => [t.id, t]));
const uri = f => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const FONT = `"IPAPGothic","IPAGothic","Noto Sans CJK JP",sans-serif`;
const CAP = `#capbar{position:fixed;left:0;right:0;bottom:0;background:rgba(20,24,32,.88);color:#fff;font:600 23px/1.5 ${FONT};padding:12px 48px 14px;z-index:99999;text-align:center}`;
const page = (body, cap) => `<html><head><style>
body{margin:0;width:1280px;height:720px;background:#fcfcfb;color:#0b0b0b;font-family:${FONT};overflow:hidden;position:relative}
h1{position:absolute;left:40px;top:18px;margin:0;font-size:32px}
.sub{position:absolute;left:44px;top:62px;font-size:15px;color:#52514e}
.left{position:absolute;left:36px;top:96px;width:264px}
.left .lab{font-size:15px;color:#52514e;margin-bottom:6px}
.box{display:flex;flex-direction:column;align-items:flex-start;margin-bottom:12px}
.box img{width:150px}
.box .does{font-size:15px;line-height:1.45;color:#222;margin-top:4px;width:250px}
.chart{position:absolute;left:316px;top:84px;width:930px}
.grid{position:absolute;left:40px;top:90px;right:30px;display:grid;grid-template-columns:repeat(4,1fr);gap:6px 20px}
.grid .box img{width:190px}
.grid .box .does{font-size:17px;width:270px}
ul.sum{position:absolute;left:80px;top:120px;right:80px;margin:0;padding:0;list-style:none}
ul.sum li{font-size:34px;line-height:1.5;margin:0 0 22px;padding-left:34px;position:relative}
ul.sum li:before{content:"";position:absolute;left:0;top:18px;width:16px;height:16px;border-radius:4px;background:#2a78d6}
${CAP}</style></head><body>${body}<div id="capbar">${esc(cap)}</div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await p.goto('file://' + path.join(OUT, 'tt.html'));
  await p.waitForTimeout(1000);
  // 箱の絵
  const need = new Set();
  for (const l of L) for (const id of [...(l.scene.boxes || []), ...(l.scene.missing || [])]) need.add(id);
  for (const id of need) {
    const e = await p.$('#t-' + id);
    if (!e) throw new Error('箱がない: ' + id);
    await e.scrollIntoViewIfNeeded();
    await e.screenshot({ path: path.join(OUT, `box_${id}.png`) });
  }
  // ページそのものの絵
  await p.addStyleTag({ content: CAP });
  await p.evaluate(() => { const d = document.createElement('div'); d.id = 'capbar'; document.body.appendChild(d); });
  for (const l of L.filter(l => l.scene.page)) {
    const s = l.scene.page;
    await p.evaluate(s => { if (s === 'top') window.scrollTo(0, 0); else { const r = document.querySelector(s).getBoundingClientRect(); window.scrollTo(0, Math.max(0, r.top + scrollY - 10)); } }, s);
    await p.evaluate(t => { document.getElementById('capbar').textContent = t; }, l.text);
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(OUT, `${l.id}.png`) });
  }
  // 図の絵
  const boxHtml = id => { const t = tech[id]; const f = t.first ? `(村: ${t.first.date})` : `(${t.status})`;
    return `<div class="box"><img src="${uri(path.join(OUT, `box_${id}.png`))}"><div class="does">${esc(t.does)} ${esc(f)}</div></div>`; };
  for (const l of L.filter(l => !l.scene.page)) {
    const s = l.scene; let body = '';
    if (s.chart) {
      body = `<h1>${esc(s.title)}</h1>` + (s.boxes ? `<div class="sub">左: テクノロジーツリーの箱 / 右: 村の記録</div>
        <div class="left"><div class="lab">ツリーでは</div>${s.boxes.map(boxHtml).join('')}</div>` : '') +
        `<img class="chart" style="${s.boxes ? '' : 'left:175px'}" src="${uri(path.join(OUT, 'charts', s.chart + '.png'))}">`;
    } else if (s.missing) {
      body = `<h1>届かなかった箱・まだの箱</h1><div class="grid">${s.missing.map(boxHtml).join('')}</div>`;
    } else if (s.summary) {
      body = `<h1>${l.id === 's33' ? '歴史をそのままなぞってはいない' : 'まとめ'}</h1><ul class="sum">${s.summary.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
    }
    await p.setContent(page(body, l.text));
    await p.waitForTimeout(150);
    await p.screenshot({ path: path.join(OUT, `${l.id}.png`) });
  }
  // 終わりの札
  await p.setContent(`<html><body style="margin:0;background:#fcfcfb;font-family:${FONT};color:#222"><div style="width:1280px;height:720px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
  <div style="font-size:46px;font-weight:700">テクノロジーは、暮らしにどう出たか</div>
  <div style="font-size:26px;margin-top:60px">ナレーション: VOICEVOX:ずんだもん</div>
  <div style="font-size:20px;margin-top:18px;color:#555">数: 川辺の村の記録 (${esc(ASOF)})・テクノロジーツリー tech_tree.html</div></div></body></html>`);
  await p.screenshot({ path: path.join(OUT, 's99.png') });
  await b.close();
})();
