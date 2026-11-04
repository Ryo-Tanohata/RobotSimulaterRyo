const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await p.setContent(`<body style="margin:0;background:#f8f7f4;font-family:sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:720px;color:#222">
  <div style="font-size:48px;font-weight:700">テクノロジーツリーの見方</div>
  <div style="font-size:26px;margin-top:60px">ナレーション: VOICEVOX:ずんだもん</div>
  <div style="font-size:20px;margin-top:18px;color:#666">画面: 川辺の村 tech_tree.html (${process.argv[3] || ''})</div></body>`);
  await p.screenshot({ path: require('path').join(process.argv[2] || '.', 's99.png') });
  await b.close();
})();
