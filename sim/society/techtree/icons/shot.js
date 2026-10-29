const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1150,height:800}, deviceScaleFactor:1.5});
await p.goto('file:///home/user/RobotSimulaterRyo/sim/society/techtree/icons/preview.html');
await p.screenshot({path:'/home/user/RobotSimulaterRyo/sim/society/techtree/icons/preview.png', fullPage:true}); await b.close(); })();
