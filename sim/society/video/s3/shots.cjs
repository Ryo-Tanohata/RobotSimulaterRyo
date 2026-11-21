// 「Society 3.0 これまで」の動画の絵 (1 文 = 1 枚、1920x1080) を作る。node shots.cjs <作業フォルダ>。作りは part7/shots.cjs と同じ。
// 作業フォルダに facts.json と charts/*.png があること (make.sh が作る)。字は IPA ゴシック (Playwright の setContent で描く)。
// 年報の絵は sim/society/reports/year232.html の節「Society 3.0 フェーズ 3 (読み書きと知らせ板)」の表だけを撮る (読むだけ。幅だけ広げて撮る)。
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
h1{position:absolute;left:56px;top:28px;margin:0;font-size:34px}
ul.b{position:absolute;left:80px;top:116px;right:80px;margin:0;padding:0;list-style:none}
ul.b li{font-size:29px;line-height:1.45;margin:0 0 20px;padding-left:34px;position:relative}
ul.b li:before{content:"";position:absolute;left:0;top:16px;width:16px;height:16px;border-radius:4px;background:#2a78d6}
ul.sum li:before{background:#eb6834}
.big{position:absolute;left:80px;right:80px;top:150px;text-align:center}
.big div{font-size:48px;font-weight:700;margin-bottom:34px}
.note{position:absolute;left:80px;right:80px;top:470px;text-align:center;font-size:27px;color:#2a78d6;font-weight:700}
.quote{position:absolute;left:120px;right:120px;top:140px;font-size:40px;line-height:1.6;border-left:10px solid #eb6834;padding:10px 0 10px 40px}
.who{position:absolute;right:140px;top:470px;font-size:25px;color:#52514e}
.chart{position:absolute;left:50%;transform:translateX(-50%);top:24px;width:1150px}
.shot{position:absolute;left:50%;transform:translateX(-50%);top:70px;max-width:1180px;max-height:520px;border:1px solid #d8d6d0;box-shadow:0 4px 18px rgba(0,0,0,.08)}
.shotcap{position:absolute;left:50px;top:22px;font-size:24px;color:#52514e}
table{position:absolute;left:60px;top:110px;border-collapse:collapse;font-size:24px}
th{background:#eeede9;color:#52514e;text-align:left;padding:9px 16px;font-weight:600}
td{padding:11px 16px;border-bottom:1px solid #e6e4df;white-space:nowrap}
td.ok{color:#2a78d6;font-weight:700}
.names{position:absolute;left:30px;right:30px;top:88px;display:grid;grid-template-columns:repeat(4,1fr);grid-auto-flow:column;grid-template-rows:repeat(8,auto);column-gap:12px}
.names div{font-size:19px;padding:9px 4px;border-bottom:1px solid #e6e4df;white-space:nowrap}
.names div.ok{color:#2a78d6;font-weight:700;background:#eaf2fc}
.names span{color:#8a8882;display:inline-block;width:62px}
.title{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:60px}
.title .t{font-size:64px;font-weight:700} .title .s{font-size:28px;color:#52514e;margin-top:28px} .title .v{font-size:22px;color:#8a8882;margin-top:60px}
#capbar{position:fixed;left:0;right:0;bottom:0;background:rgba(20,24,32,.88);color:#fff;font:600 23px/1.5 ${FONT};padding:12px 48px 14px;text-align:center}
</style></head><body>${body}<div id="capbar">${esc(cap)}</div></body></html>`;

const phases = () => `<h1>Society 3.0 のながれ (200年120日目〜232年の終わり)</h1><table><tr><th>年</th><th>中身</th><th>どうなったか</th></tr>` +
  F.phases.map(([y, what, res]) => `<tr><td>${esc(y)}</td><td>${esc(what)}</td><td class="ok">${esc(res)}</td></tr>`).join('') + `</table>`;

const names = () => {
  const ys = Object.keys(F.names).map(Number).sort((a, b) => a - b);
  return `<h1 style="font-size:30px;top:24px">村の人がつけた年の名前 (${ys[0]}〜${ys[ys.length - 1]}年)</h1><div class="names">` +
    ys.map(y => `<div class="${F.work_names.includes(y) ? 'ok' : ''}"><span>${y}年</span>${esc(F.names[y])}</div>`).join('') + `</div>`;
};

(async () => {
  const b = await chromium.launch();
  // 年報 232年の、フェーズ 3 の表 (見出し・ひとこと・表)
  const t = await b.newPage({ viewport: { width: 1180, height: 900 }, deviceScaleFactor: 1.5 });
  await t.goto('file://' + path.join(ROOT, 'sim/society/reports/year232.html'));
  await t.addStyleTag({ content: 'main{max-width:1150px !important} table{font-size:16px !important}' });
  await t.waitForTimeout(400);
  const head = t.locator('p', { hasText: 'Society 3.0 フェーズ 3 (読み書きと知らせ板):' }).first();
  const tbl = head.locator('xpath=following-sibling::table[1]');
  await tbl.scrollIntoViewIfNeeded();
  const a = await head.boundingBox(), z = await tbl.boundingBox();
  const x0 = Math.min(a.x, z.x) - 8, y0 = a.y - 8;
  await t.screenshot({ path: path.join(OUT, 'report.png'), clip: { x: x0, y: y0, width: Math.max(a.x + a.width, z.x + z.width) - x0 + 8, height: z.y + z.height - y0 + 8 } });
  await t.close();

  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  for (const l of L) {
    const s = l.scene; let body = '<div class="tag">川辺の村 Society 3.0 これまで</div>';
    if (s.title) body = `<div class="title"><div class="t">${esc(s.title)}</div><div class="s">${esc(s.sub)}</div><div class="v">LLM の村のシミュレーションの記録から</div></div>`;
    else if (s.chart) body = `<img class="chart" src="${uri(path.join(OUT, 'charts', s.chart + '.png'))}">`;
    else if (s.shot) body = `<div class="shotcap">232年の年報から (フェーズ 3 の物差し。i3 = 字の仕事)</div><img class="shot" src="${uri(path.join(OUT, s.shot + '.png'))}">`;
    else if (s.names) body += names();
    else if (s.table === 'phases') body += phases();
    else {
      if (s.head) body += `<h1>${esc(s.head)}</h1>`;
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
  <div style="font-size:46px;font-weight:700">Society 3.0 これまで (約 32 年)</div>
  <div style="font-size:26px;margin-top:60px">ナレーション: VOICEVOX:ずんだもん</div>
  <div style="font-size:20px;margin-top:18px;color:#555">数: 川辺の村の記録 (200年120日目〜232年120日目)・年報 201〜232年</div></div></body></html>`);
  await p.screenshot({ path: path.join(OUT, 's99.png') });
  await b.close();
})();
