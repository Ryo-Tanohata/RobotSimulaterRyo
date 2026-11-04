const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = process.argv[2] || '.';
const L = JSON.parse(fs.readFileSync(require('path').join(__dirname,'lines.json'),'utf8'));
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await p.goto('file://' + path.resolve(__dirname, '../../app/tech_tree.html'));
  await p.waitForTimeout(1000);
  await p.addStyleTag({content: `#capbar{position:fixed;left:0;right:0;bottom:0;background:rgba(20,24,32,.86);color:#fff;font:600 22px/1.45 "Noto Sans CJK JP",sans-serif;padding:12px 40px 14px;z-index:99999;text-align:center}
  .hl{outline:4px solid #e8590c!important;outline-offset:4px;border-radius:6px}`});
  await p.evaluate(()=>{const d=document.createElement('div');d.id='capbar';document.body.appendChild(d);});
  for (const l of L) {
    const a = l.act;
    await p.evaluate(()=>document.querySelectorAll('.hl').forEach(e=>e.classList.remove('hl')));
    // close any open panel
    await p.keyboard.press('Escape');
    const closeBtn = await p.$('text=閉じる');
    if (closeBtn && await closeBtn.isVisible()) await closeBtn.click();
    await p.waitForTimeout(200);
    if (a.top) await p.evaluate(()=>window.scrollTo(0,0));
    if (a.show) {
      await p.evaluate(([s,o])=>{const e=document.querySelector(s);const r=e.getBoundingClientRect();window.scrollTo(0, Math.max(0, r.top+scrollY-(o===false?70:90))); if(o!==false) e.classList.add('hl');}, [a.show, a.outline]);
    }
    if (a.click) {
      await p.evaluate(s=>{const e=document.querySelector(s).closest(".tree");const r=e.getBoundingClientRect();window.scrollTo(0, Math.max(0, r.top+scrollY-70));}, a.click);
      await p.waitForTimeout(150);
      await p.click(a.click);
    }
    await p.evaluate(t=>{document.getElementById('capbar').textContent=t;}, l.text);
    await p.waitForTimeout(500);
    await p.screenshot({ path: require('path').join(OUT, `${l.id}.png`) });
  }
  await b.close();
})();
