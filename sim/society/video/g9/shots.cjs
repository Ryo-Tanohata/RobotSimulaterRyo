// G9 の動画の絵 (1 文 = 1 枚、1920x1080) を作る。node shots.cjs <作業フォルダ>
// 作業フォルダに facts.json と charts/*.png があること (make.sh が作る)。字は IPA ゴシック (Playwright の setContent で描く)。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.resolve(process.argv[2] || '.');
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
ul.b li{font-size:32px;line-height:1.45;margin:0 0 22px;padding-left:34px;position:relative}
ul.b li:before{content:"";position:absolute;left:0;top:17px;width:16px;height:16px;border-radius:4px;background:#2a78d6}
ul.sum li:before{background:#eb6834}
.big{position:absolute;left:80px;right:80px;top:150px;text-align:center}
.big div{font-size:50px;font-weight:700;margin-bottom:34px}
.note{position:absolute;left:80px;right:80px;top:470px;text-align:center;font-size:28px;color:#2a78d6;font-weight:700}
.quote{position:absolute;left:120px;right:120px;top:150px;font-size:44px;line-height:1.6;border-left:10px solid #eb6834;padding:10px 0 10px 40px}
.who{position:absolute;right:140px;top:440px;font-size:26px;color:#52514e}
.chart{position:absolute;left:50%;transform:translateX(-50%);top:24px;width:1150px}
table{position:absolute;left:90px;right:90px;top:100px;border-collapse:collapse;font-size:22px;width:1100px}
th{background:#eeede9;color:#52514e;text-align:left;padding:7px 14px;font-weight:600}
td{padding:6px 14px;border-bottom:1px solid #e6e4df;white-space:nowrap}
td.ok{color:#2a78d6;font-weight:700} td.no{color:#8a8882;font-weight:700}
.title{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:60px}
.title .t{font-size:64px;font-weight:700} .title .s{font-size:28px;color:#52514e;margin-top:28px} .title .v{font-size:22px;color:#8a8882;margin-top:60px}
#capbar{position:fixed;left:0;right:0;bottom:0;background:rgba(20,24,32,.88);color:#fff;font:600 23px/1.5 ${FONT};padding:12px 48px 14px;text-align:center}
</style></head><body>${body}<div id="capbar">${esc(cap)}</div></body></html>`;

const table = (k, note) => {
  if (k === 'visits') {
    return `<h1>遠くの運ぶ人が来た 9 回</h1><table style="font-size:21px"><tr><th>来た日</th><th>申し出</th><th>決めた日</th><th>答え</th><th>票 / 大人</th></tr>` +
      F.rows.map(r => `<tr><td>${r.date}</td><td>[${r.id}] 鎌 2 本 ⇔ 種 1,600</td><td>${r.end}</td>` +
        `<td class="${r.answer === '受ける' ? 'ok' : 'no'}">${r.answer === '受ける' ? '替えた' : '受けない'}</td><td>${esc(r.votes)}</td></tr>`).join('') +
      `</table>` + (note ? `<div class="note" style="top:590px">${esc(note)}</div>` : '');
  }
  if (k === 'hints') {
    return `<h1>運ぶ人が話していった遠くの話 (9 回)</h1><table><tr><th>日</th><th>話</th><th>そのあと</th></tr>` +
      F.hints.map(h => `<tr><td>${h.date}</td><td>${esc(h.name)}</td>` +
        `<td class="${h.status === '忘れられた' ? 'no' : 'ok'}">${h.status === '忘れられた' ? '忘れられた' : '覚えられた (' + h.kept.join('・') + ')'}</td></tr>`).join('') + `</table>`;
  }
  if (k === 'names') {
    const ys = Object.keys(F.names).sort((a, b) => a - b);
    return `<h1>村の人がつけた年の名前</h1><table style="font-size:21px"><tr><th>年</th><th>名前</th><th>年</th><th>名前</th></tr>` +
      ys.slice(0, 7).map((y, i) => { const y2 = ys[i + 7]; const c = n => (/ヤギが.*やせ/.test(n) ? ' class="ok"' : '');
        return `<tr><td>${y}年</td><td${c(F.names[y])}>${esc(F.names[y])}</td><td>${y2}年</td><td${c(F.names[y2])}>${esc(F.names[y2])}</td></tr>`; }).join('') +
      `</table><div class="note" style="top:470px">青い字 = ヤギがやせた年 (5 つ)。運ぶ人・赤い金属・ザガの名前の年は 0</div>`;
  }
  throw new Error('表がない: ' + k);
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  for (const l of L) {
    const s = l.scene; let body = '<div class="tag">川辺の村 G9「遠くとの商い」</div>';
    if (s.title) body = `<div class="title"><div class="t">${esc(s.title)}</div><div class="s">${esc(s.sub)}</div><div class="v">LLM の村のシミュレーションの記録から</div></div>`;
    else if (s.chart) body = `<img class="chart" src="${uri(path.join(OUT, 'charts', s.chart + '.png'))}">`;
    else if (s.table) body += table(s.table, s.note);
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
  <div style="font-size:46px;font-weight:700">G9「遠くとの商い」の 14 年</div>
  <div style="font-size:26px;margin-top:60px">ナレーション: VOICEVOX:ずんだもん</div>
  <div style="font-size:20px;margin-top:18px;color:#555">数: 川辺の村の記録 (104年120日目〜118年120日目)・docs/society_phase/G9.md</div></div></body></html>`);
  await p.screenshot({ path: path.join(OUT, 's99.png') });
  await b.close();
})();
