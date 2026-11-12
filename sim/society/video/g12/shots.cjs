// G12 の動画の絵 (1 文 = 1 枚、1920x1080) を作る。node shots.cjs <作業フォルダ>
// 作業フォルダに facts.json と charts/*.png があること (make.sh が作る)。字は IPA ゴシック (Playwright の setContent で描く)。
// テクノロジーツリーの絵は sim/society/app/tech_tree.html を開いて「帝国」を押して、横の欄の「要素」(倉の約束・倉から地域を養う) を見せたところ (読むだけ)。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.resolve(process.argv[2] || '.');
const ROOT = path.resolve(__dirname, '../../../..');
const L = JSON.parse(fs.readFileSync(path.join(__dirname, 'lines.json'), 'utf8'));
const F = JSON.parse(fs.readFileSync(path.join(OUT, 'facts.json'), 'utf8'));
const uri = f => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
const FONT = `"IPAPGothic","IPAGothic","Noto Sans CJK JP",sans-serif`;
const page = (body, cap) => `<html><head><style>
body{margin:0;width:1280px;height:720px;background:#fcfcfb;color:#0b0b0b;font-family:${FONT};overflow:hidden;position:relative}
.tag{position:absolute;right:36px;top:22px;font-size:15px;color:#8a8882}
h1{position:absolute;left:56px;top:28px;margin:0;font-size:36px}
ul.b{position:absolute;left:80px;top:120px;right:80px;margin:0;padding:0;list-style:none}
ul.b li{font-size:31px;line-height:1.45;margin:0 0 22px;padding-left:34px;position:relative}
ul.b li:before{content:"";position:absolute;left:0;top:17px;width:16px;height:16px;border-radius:4px;background:#2a78d6}
ul.sum li:before{background:#eb6834}
.big{position:absolute;left:80px;right:80px;top:150px;text-align:center}
.big div{font-size:50px;font-weight:700;margin-bottom:34px}
.note{position:absolute;left:80px;right:80px;top:470px;text-align:center;font-size:28px;color:#2a78d6;font-weight:700}
.quote{position:absolute;left:120px;right:120px;top:150px;font-size:42px;line-height:1.6;border-left:10px solid #eb6834;padding:10px 0 10px 40px}
.who{position:absolute;right:140px;top:470px;font-size:26px;color:#52514e}
.chart{position:absolute;left:50%;transform:translateX(-50%);top:24px;width:1150px}
.shot{position:absolute;left:50%;transform:translateX(-50%);top:14px;width:1110px;border:1px solid #d8d6d0;box-shadow:0 4px 18px rgba(0,0,0,.08)}
table{position:absolute;left:90px;top:100px;border-collapse:collapse;font-size:22px}
th{background:#eeede9;color:#52514e;text-align:left;padding:7px 14px;font-weight:600}
td{padding:7px 14px;border-bottom:1px solid #e6e4df;white-space:nowrap}
td.ok{color:#2a78d6;font-weight:700} td.no{color:#8a8882;font-weight:700}
.names{position:absolute;left:60px;right:60px;top:96px;display:grid;grid-template-columns:repeat(2,1fr);grid-auto-flow:column;grid-template-rows:repeat(4,auto);column-gap:28px}
.names div{font-size:24px;padding:8px 10px;border-bottom:1px solid #e6e4df;white-space:nowrap}
.names div.ok{color:#2a78d6;font-weight:700;background:#eaf2fc}
.names span{color:#8a8882;display:inline-block;width:80px}
.title{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:60px}
.title .t{font-size:64px;font-weight:700} .title .s{font-size:28px;color:#52514e;margin-top:28px} .title .v{font-size:22px;color:#8a8882;margin-top:60px}
#capbar{position:fixed;left:0;right:0;bottom:0;background:rgba(20,24,32,.88);color:#fff;font:600 23px/1.5 ${FONT};padding:12px 48px 14px;text-align:center}
</style></head><body>${body}<div id="capbar">${esc(cap)}</div></body></html>`;

const goals = () => `<h1>G12 の条件と F (172年120日目まで)</h1><table style="left:50px;font-size:19px"><tr><th></th><th>中身</th><th>届いた日</th><th>記録</th></tr>` +
  F.goals.map(([k, what, day, now]) => `<tr><td>${esc(k)}</td><td>${esc(what)}</td>` +
    `<td class="ok">${esc(day)}</td><td>${esc(now)}</td></tr>`).join('') + `</table>`;

const names = () => {
  const ys = Object.keys(F.names).map(Number).sort((a, b) => a - b);
  return `<h1>村の人がつけた年の名前 (${ys[0]}〜${ys[ys.length - 1]}年)</h1><div class="names">` +
    ys.map(y => `<div><span>${y}年</span>${esc(F.names[y])}</div>`).join('') +
    `</div><div class="note" style="top:430px;font-size:26px">案には「約束の種が届いた年」「約束の分が届いた年」「病と倉の約束の年」(169年)<br>もあったが、選ばれなかった (172年の名前は、まだ決めていない)</div>`;
};

(async () => {
  const b = await chromium.launch();
  // テクノロジーツリー (帝国を押して、横の欄を「要素」まで送ったところ)
  const t = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await t.goto('file://' + path.join(ROOT, 'sim/society/app/tech_tree.html'));
  await t.waitForTimeout(800);
  await t.locator('button.it', { hasText: '帝国' }).first().click();
  await t.waitForTimeout(300);
  await t.evaluate(() => { const h = document.querySelector('div.treehead h2'); window.scrollTo(0, h.getBoundingClientRect().top + window.scrollY - 10); });
  await t.waitForTimeout(300);
  await t.evaluate(() => {
    const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && /要素 \(押すと/.test(e.textContent));
    let p = h.parentElement; while (p && p.scrollHeight <= p.clientHeight + 2) p = p.parentElement;
    p.scrollTop += h.getBoundingClientRect().top - p.getBoundingClientRect().top - 150;
  });
  await t.waitForTimeout(300);
  await t.screenshot({ path: path.join(OUT, 'techtree.png') });
  await t.close();

  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  for (const l of L) {
    const s = l.scene; let body = '<div class="tag">川辺の村 G12「大きな都と帝国」</div>';
    if (s.title) body = `<div class="title"><div class="t">${esc(s.title)}</div><div class="s">${esc(s.sub)}</div><div class="v">LLM の村のシミュレーションの記録から</div></div>`;
    else if (s.chart) body = `<img class="chart" src="${uri(path.join(OUT, 'charts', s.chart + '.png'))}">`;
    else if (s.shot) body = `<img class="shot" src="${uri(path.join(OUT, s.shot + '.png'))}">`;
    else if (s.names) body += names();
    else if (s.table === 'goals') body += goals();
    else {
      body += `<h1>${esc(s.head)}</h1>`;
      if (s.bullets) body += `<ul class="b">${s.bullets.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
      if (s.summary) body += `<ul class="b sum">${s.summary.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
      if (s.big) body += `<div class="big">${s.big.map(x => `<div>${esc(x)}</div>`).join('')}</div>`;
      if (s.quote) body += `<div class="quote">「${esc(s.quote)}」</div><div class="who">— ${esc(s.who)}</div>`;
      if (s.note) body += `<div class="note">${esc(s.note)}</div>`;
    }
    await p.setContent(page(body, l.text));
    await p.waitForTimeout(120);
    await p.screenshot({ path: path.join(OUT, `${l.id}.png`) });
  }
  // 終わりの札
  await p.setContent(`<html><head><style>body{margin:0;background:#fcfcfb;font-family:${FONT};color:#222}</style></head><body><div style="width:1280px;height:720px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
  <div style="font-size:46px;font-weight:700">G12「大きな都と帝国」の 8 年</div>
  <div style="font-size:26px;margin-top:60px">ナレーション: VOICEVOX:ずんだもん</div>
  <div style="font-size:20px;margin-top:18px;color:#555">数: 川辺の村の記録 (164年120日目〜172年120日目)・年報 165〜172年</div></div></body></html>`);
  await p.screenshot({ path: path.join(OUT, 's99.png') });
  await b.close();
})();
