import RAPIER from '@dimforge/rapier3d-compat';
import { createConfig, TrotGait, defaultGaitParams, GAIT_PARAMS } from '../src/core.js';
import { QuadrupedRobot, GROUND_GROUPS } from '../src/robot.js';
await RAPIER.init();
// 平地で歩容パラメータを遺伝的アルゴリズムで最適化する (Web 版「進化で学習」と同じ考え方)
//   node test/evolve.mjs [kp] [kd]
const KP = +process.argv[2] || 150, KD = +process.argv[3] || 2;
function sim(p, cmd, secs=6) {
  const world = new RAPIER.World({ x: 0, y: -9.81, z: 0 }); world.timestep = 1/200;
  world.createCollider(RAPIER.ColliderDesc.cuboid(50, 0.5, 50).setTranslation(0, -0.5, 0).setFriction(1).setCollisionGroups(GROUND_GROUPS));
  const c = createConfig(); c.kp=KP; c.kd=KD;
  const r = new QuadrupedRobot(RAPIER, world, c, { x: 0, y: c.spawnHeight, z: 0 }, 0);
  const g = new TrotGait(c, p); const t = new Float64Array(12); let minUp=1;
  const n = secs*200;
  for (let i=0;i<n;i++){ if(i%4===0){ r.readState(); g.step(0.02, i>100?cmd:{forward:0,side:0,yaw:0}, r.gravityCore(), t); r.setTargets(t); minUp=Math.min(minUp,r.upY());} world.step(); }
  const tt = secs-0.5; const pos = r.position;
  const err = Math.hypot(pos.z - cmd.forward*tt, -pos.x - cmd.side*tt);
  world.free();
  return -err - (minUp<0.5?5:0);
}
const tasks=[{forward:0.6,side:0,yaw:0},{forward:0,side:0,yaw:0},{forward:-0.4,side:0,yaw:0},{forward:0.3,side:0,yaw:0}];
const fitness = p => tasks.reduce((a,cmd)=>a+sim(p,cmd),0);
const clampP = p => { for (const [k,,lo,hi] of GAIT_PARAMS) p[k]=Math.min(hi,Math.max(lo,p[k])); return p; };
let pop = Array.from({length:16},(_,i)=>{ const p=defaultGaitParams(); if(i>0) for (const [k,,lo,hi] of GAIT_PARAMS) p[k]+= (Math.random()*2-1)*(hi-lo)*0.25; return clampP(p); });
let sigma=0.15, best=null;
for (let gen=0; gen<25; gen++){
  const scored = pop.map(p=>({p, f:fitness(p)})).sort((a,b)=>b.f-a.f);
  if(!best||scored[0].f>best.f) best=scored[0];
  console.log(`gen ${gen} best ${scored[0].f.toFixed(2)} median ${scored[8].f.toFixed(2)}`);
  const elite = scored.slice(0,4).map(s=>s.p);
  pop = [ ...elite.map(e=>({...e})) ];
  while (pop.length<16){ const e=elite[Math.floor(Math.random()*elite.length)]; const p={...e}; for (const [k,,lo,hi] of GAIT_PARAMS) p[k]+=(Math.random()*2-1)*(hi-lo)*sigma; pop.push(clampP(p)); }
  sigma*=0.93;
}
console.log('BEST', best.f.toFixed(2), JSON.stringify(best.p, (k,v)=>typeof v==='number'?+v.toFixed(3):v));
for (const cmd of tasks) console.log(JSON.stringify(cmd), 'score', sim(best.p,cmd).toFixed(2));
