// 人のモデル (2026-11-23、動画 D1P「1 日目を人のモデルで」): 棒の人の代わりに、VRoid で作った川辺の五人 (皮の服を着た形) を、記録した動き (CMU のモーションキャプチャー) で動かす。
// 撮影 (make_video.mjs の PEOPLE=フォルダ) のときだけ読む。アプリの画面では読まない。
// フォルダには <名前>.glb (動きつき。human-model/scripts/export_people_glb.py で作る) と <名前>.json (動きの長さ・進む速さ) を置く。
// 場所と向きは、ここで決める (棒の人の道筋の代わり。歩く速さは人の速さにして、着いたら仕事をする)。名前の札とカメラは、モデルに合わせる。
// 動きは、その日の場面 (夜明け・出発・活動・帰り・夕方・夜) と、記録の活動 (採集・探索)・夕方の出来事 (話す・分ける) から選ぶ
(function () {
  const FILES = { "ルオ": "ruo", "セナ": "sena", "タヒ": "tahi", "ウィロ": "wiro", "イサ": "isa" };
  const WALK = 1.25;   // 歩く速さ (m/秒)
  const FADE = 0.4;    // 動きを切りかえるときに混ぜる秒数
  const RING = 1.9;    // 火のまわりの輪を、棒の人のときの何倍に広げるか (体の大きさに合わせて)
  const GATHER = ["pick", "probe", "reach", "stretch"];  // 採集: かがんで拾う・地面を両手で調べる・身をのり出して取る・背のびして取る
  let M = null;
  const sched = new WeakMap();  // その日の見せ方 (P) ごとの、人ごとの予定

  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => ({ x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u });
  const face = (a, b) => Math.atan2(-(b.y - a.y), b.x - a.x);  // 棒の人と同じ向きの決め方 (+x が 0)
  const wrapA = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  const rnd = (i, k) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };

  function loadGlb(url) {
    return new Promise((ok, ng) => new THREE.GLTFLoader().load(url, ok, undefined, ng));
  }

  // v2 (2026-11-25 本人「人が家や木をすり抜けないように」): よける物 (住まい・林の木・育った木) の円 {x, y, r} (マス)。日ごとに 1 回
  const obstCache = new WeakMap();
  function groveList(P) {  // キャンプのそばに育った木 (growFrame と同じ並び)
    const D = M.D, fire = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 };
    const trees = (D.grow || []).filter((e) => e.day <= P.day && /木の実の木が育った/.test(e.text)).slice(-40);
    return trees.map((e, k) => {
      const dump = /殻を捨てた/.test(e.text), c = dump ? { x: fire.x + 2.5, y: fire.y - 7.5 } : { x: fire.x - 8.0, y: fire.y + 0.5 };  // カメラ (南東の上) から見て、キャンプの奥 (北と西) に
      const j = trees.filter((x, i) => i < k && /殻を捨てた/.test(x.text) === dump).length, a = j * 2.39996, r = 0.9 * Math.sqrt(j + 0.5);
      return { pt: { x: c.x + Math.cos(a) * r, y: c.y + Math.sin(a) * r }, sz: 0.8 * (0.25 + 0.75 * clamp((P.day - e.day + 1) / 30)), k };
    });
  }
  // v2 (2026-11-26 本人「家が１つしかないのも疑問です」): 家族ごとの皮張りの小屋 (記録にない、描きそえ)。家族の家 (houses) が建つまで。
  // 1 つめの家族 (川辺の家) は Society 1.0 の住まい。ほかの家族は、キャンプの奥 (北側。カメラから見て向こう) に、家族の数だけ小屋を建てる
  const tentCache = new WeakMap();
  function tentsFor(P) {
    if (tentCache.has(P)) return tentCache.get(P);
    const D = M.D, fire = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 }, first = (D.people[0] || {}).household;
    const homes = [...new Set(Object.keys(P.plan).filter((n) => P.plan[n].alive).map((n) => P.plan[n].home))].filter((h) => h && h !== "-" && h !== first);
    const built = new Set((D.houses || []).filter((v) => v.built != null && v.built <= P.day).map((v) => v.household));
    const T = [];
    tentCache.set(P, T);  // 下の pushOut が obstacles を呼ぶので、先に空で入れておく
    homes.filter((h) => !built.has(h)).forEach((h, k) => {
      const a = -Math.PI / 2 + (k % 2 ? 1 : -1) * (0.35 + 0.42 * Math.floor((k + 1) / 2)) * (k ? 1 : 0), r = 5.2 + 1.6 * Math.floor(k / 6);
      let pt = { x: fire.x + Math.cos(a) * r, y: fire.y + Math.sin(a) * r };
      for (let it = 0; it < 6; it++) {  // 小屋の大きさ (半径 1) のぶん、住まい・木・囲い・前の小屋から離す
        const o = [...obstacles(P), ...T.map((q) => ({ x: q.pt.x, y: q.pt.y, r: 1.2 }))].find((o) => Math.hypot(pt.x - o.x, pt.y - o.y) < o.r + 1.0);
        if (!o) break;
        const d = Math.hypot(pt.x - o.x, pt.y - o.y), b = d > 1e-3 ? Math.atan2(pt.y - o.y, pt.x - o.x) : a;
        pt = { x: o.x + Math.cos(b) * (o.r + 1.05), y: o.y + Math.sin(b) * (o.r + 1.05) };
      }
      T.push({ home: h, pt, door: lerp(pt, fire, 1.0 / Math.max(1, Math.hypot(fire.x - pt.x, fire.y - pt.y))) });
    });
    obstCache.delete(P);  // 小屋も、よける物に入れ直す
    return T;
  }
  function tentGroup(P) {
    const g = new THREE.Group(), hide = new THREE.MeshLambertMaterial({ color: 0x7a6248 }), pole = new THREE.MeshLambertMaterial({ color: 0x4a3420 }), dark = new THREE.MeshBasicMaterial({ color: 0x1c140e, side: THREE.DoubleSide });
    for (const t of tentsFor(P)) {
      const o = new THREE.Group(); o.position.copy(M.w2t(t.pt.x, t.pt.y));
      const c = new THREE.Mesh(new THREE.ConeGeometry(1.0, 1.7, 9, 1, true), hide); c.position.y = 0.85; o.add(c);
      for (let k = 0; k < 4; k++) { const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.03, 0.55, 4), pole); pl.position.set(Math.cos(k * 1.57) * 0.06, 1.85, Math.sin(k * 1.57) * 0.06); pl.rotation.set(Math.sin(k * 1.57) * 0.4, 0, -Math.cos(k * 1.57) * 0.4); o.add(pl); }
      const dr = new THREE.Mesh(new THREE.CircleGeometry(0.32, 3), dark), dir = Math.atan2(t.door.y - t.pt.y, t.door.x - t.pt.x);  // 戸口 (火のほう)
      dr.position.set(Math.cos(dir) * 0.78, 0.38, Math.sin(dir) * 0.78); dr.rotation.set(0, -dir + Math.PI / 2, Math.PI / 2); o.add(dr);
      g.add(o);
    }
    return g;
  }
  function obstacles(P) {
    if (obstCache.has(P)) return obstCache.get(P);
    const D = M.D, O = [], T = D.map.terrain, H = T.length, W = T[0].length;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (T[y][x] === "f" && ((x * 73856093) ^ (y * 19349663)) % 7 === 0) O.push({ x: x + 0.5, y: y + 0.5, r: 0.85 });  // replay3d.js の林の木 (円すい、半径 0.55) と同じ所
    if (M.world && M.world.hutDay !== null && P.day >= M.world.hutDay - 3) O.push({ x: D.camp.x + 0.5 - 3.2, y: D.camp.y + 0.5 - 2.2, r: 2.0 });  // 住まい (建てかけも)
    for (const g of groveList(P)) O.push({ x: g.pt.x, y: g.pt.y, r: 0.3 + 0.35 * g.sz });
    const gs = (D.goats || []).find((g) => P.day >= g.from && P.day <= g.to), ng = Math.min(30, D.goatDay && D.goatDay[P.day] != null ? D.goatDay[P.day] : gs ? gs.n : 0);
    if (ng > 0) O.push({ x: D.camp.x + 0.5 + 4.5, y: D.camp.y + 0.5 + 4.0, r: 1.5 + 0.25 * Math.sqrt(ng) });  // ヤギの囲い
    if (tentCache.has(P)) for (const t of tentCache.get(P)) O.push({ x: t.pt.x, y: t.pt.y, r: 1.25 });  // 家族の小屋
    obstCache.set(P, O);
    return O;
  }
  const pushOut = (P, pt) => {  // 円の中なら、外へ
    let q = pt;
    for (let it = 0; it < 4; it++) {
      const o = obstacles(P).find((o) => Math.hypot(q.x - o.x, q.y - o.y) < o.r);
      if (!o) break;
      const d = Math.hypot(q.x - o.x, q.y - o.y), a = d > 1e-3 ? Math.atan2(q.y - o.y, q.x - o.x) : 0.7;
      q = { x: o.x + Math.cos(a) * (o.r + 0.05), y: o.y + Math.sin(a) * (o.r + 0.05) };
    }
    return q;
  };
  function route(P, a, b, depth = 0) {  // a から b へ、円をよける道 (曲がり角の点の並び。b をふくむ)
    if (depth > 6) return [b];
    let hit = null, best = 1;
    const dx = b.x - a.x, dy = b.y - a.y, L2 = dx * dx + dy * dy || 1e-9;
    for (const o of obstacles(P)) {
      const u = clamp(((o.x - a.x) * dx + (o.y - a.y) * dy) / L2), cx = a.x + dx * u, cy = a.y + dy * u;
      if (Math.hypot(o.x - cx, o.y - cy) < o.r - 0.02 && u > 0.001 && u < 0.999 && u < best) { best = u; hit = { o, cx, cy }; }
    }
    if (!hit) return [b];
    const { o, cx, cy } = hit, L = Math.sqrt(L2);
    let nx = -dy / L, ny = dx / L;
    if ((cx - o.x) * nx + (cy - o.y) * ny < 0) { nx = -nx; ny = -ny; }  // 近いほうの側をまわる
    const w = pushOut(P, { x: o.x + nx * (o.r + 0.25), y: o.y + ny * (o.r + 0.25) });
    return [...route(P, a, w, depth + 1), ...route(P, w, b, depth + 1)];
  }

  // v2: 火をおこす人 (その日の記録で火をおこした人。いなければ、いちばん年上の大人)
  function lighterOf(P) {
    if (!M.lighter.has(P)) {
      const e = (P.work || []).find((e) => e.type === "火" && e.who && P.plan[e.who] && P.plan[e.who].alive);
      const adults = Object.keys(P.plan).filter((n) => P.plan[n].alive && !P.plan[n].child && M.people[n]).sort((a, b) => P.plan[a].i - P.plan[b].i);
      M.lighter.set(P, e && M.people[e.who] ? e.who : adults[0] || null);
    }
    return M.lighter.get(P);
  }
  // v2: 焚き火 (薪・何枚もの炎・火の粉・光・煙)。強さ 0〜1 は場面で決める (夕方に火をおこしてから大きくなり、夜は燃え、夜明けには小さくなる)
  function fireGlowTex() {
    const c = document.createElement("canvas"); c.width = c.height = 128;
    const g = c.getContext("2d"), r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    r.addColorStop(0, "rgba(255,220,140,1)"); r.addColorStop(0.35, "rgba(255,150,50,0.55)"); r.addColorStop(1, "rgba(255,100,20,0)");
    g.fillStyle = r; g.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }
  function buildFire() {
    const W = M.world, g = new THREE.Group(); g.position.copy(W.camp);
    const logM = new THREE.MeshLambertMaterial({ color: 0x4a3220 }), charM = new THREE.MeshLambertMaterial({ color: 0x1c1410 });
    for (let k = 0; k < 6; k++) {  // 円すいに組んだ薪 (下は石の輪の内側、先は真ん中で合わさる)
      const a = k * 1.0472 + 0.3, geo = new THREE.CylinderGeometry(0.04, 0.055, 0.62, 6); geo.translate(0, 0.31, 0);
      const lg = new THREE.Mesh(geo, k % 2 ? logM : charM);
      lg.position.set(Math.cos(a) * 0.3, 0.02, Math.sin(a) * 0.3);
      lg.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(-Math.cos(a) * 0.5, 0.86, -Math.sin(a) * 0.5).normalize());
      g.add(lg);
    }
    const emb = new THREE.Mesh(new THREE.CircleGeometry(0.28, 14), new THREE.MeshBasicMaterial({ color: 0xff5a14 })); emb.rotation.x = -Math.PI / 2; emb.position.y = 0.025; g.add(emb);  // 熾火
    const mat = (col, op) => new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op, depthWrite: false, side: THREE.DoubleSide });
    const add = (col, op) => new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op, blending: THREE.AdditiveBlending, depthWrite: false });
    const flames = [];
    [[0xd2400a, 0.8, 0.34, 1.25], [0xf06a12, 0.75, 0.27, 1.05], [0xffa020, 0.75, 0.19, 0.85], [0xffd870, 0.85, 0.1, 0.55]].forEach(([c, op, r, h], i) => {
      for (let k = 0; k < (i < 2 ? 3 : 2); k++) {
        const f = new THREE.Mesh(new THREE.ConeGeometry(r, h, 7, 1, true), mat(c, op)); f.geometry.translate(0, h / 2, 0);
        f.userData = { h, ph: i * 1.7 + k * 2.3 }; f.position.set((k - 1) * r * 0.4, 0.05, (k % 2 ? 1 : -1) * r * 0.25); g.add(f); flames.push(f);
      }
    });
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: fireGlowTex(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    glow.scale.set(1.8, 1.8, 1); glow.position.y = 0.5; g.add(glow);
    const sparks = [], sm = add(0xffb050, 1);
    for (let k = 0; k < 26; k++) { const sp = new THREE.Mesh(new THREE.SphereGeometry(0.02, 4, 3), sm); sp.userData = { ph: rnd(k, 3), x: (rnd(k, 5) - 0.5) * 0.4, z: (rnd(k, 7) - 0.5) * 0.4, sp: 0.6 + rnd(k, 9) * 0.8 }; g.add(sp); sparks.push(sp); }
    const smokes = [], smM = new THREE.MeshLambertMaterial({ color: 0x8a8a8a, transparent: true, opacity: 0.25, depthWrite: false });
    for (let k = 0; k < 7; k++) { const sk = new THREE.Mesh(new THREE.SphereGeometry(0.22, 7, 5), smM.clone()); sk.userData = { ph: k / 7 }; g.add(sk); smokes.push(sk); }
    M.scene.add(g);
    return { g, flames, glow, sparks, smokes };
  }
  function fireAmount(P, v) {
    const seg = P.segs.find((s) => v >= s.v0 && v < s.v1) || P.segs[P.segs.length - 1];
    if (seg.key === "dawn") return 0.45 * (1 - clamp((v - seg.v0) / Math.max(1, seg.sec)));
    if (seg.key === "night") return 1;
    const at = M.fireAt.get(P);
    if (at == null) return seg.key === "eve" ? clamp((v - seg.v0) / 3.5) : 0;
    return clamp((v - at) / 3.5);
  }
  function fireFrame(P, v) {
    const W = M.world;
    if (!M.fire) M.fire = buildFire();
    const F = M.fire, a = fireAmount(P, v);
    W.flame.visible = false;  // replay3d.js の円すいの炎の代わり
    W.fireLight.intensity = a * (1.2 + Math.sin(v * 13) * 0.18 + Math.sin(v * 7.3) * 0.1);
    W.fireLight.color.setHex(0xff9a40);
    F.g.visible = a > 0.01;
    if (!F.g.visible) return;
    const s = 0.15 + 0.85 * a;
    F.flames.forEach((f) => {
      const u = f.userData, fl = 1 + Math.sin(v * 11 + u.ph) * 0.18 + Math.sin(v * 17.3 + u.ph * 2) * 0.1;
      f.scale.set(s * (1 + Math.sin(v * 9 + u.ph) * 0.08), s * fl, s * (1 + Math.cos(v * 8 + u.ph) * 0.08));
      f.rotation.y = v * 0.8 + u.ph; f.rotation.z = Math.sin(v * 5 + u.ph) * 0.12;
    });
    F.glow.material.opacity = 0.32 * a; F.glow.scale.setScalar(1.0 + 1.0 * a);
    F.sparks.forEach((sp) => {
      const u = sp.userData, q = (v * u.sp * 0.5 + u.ph) % 1;
      sp.visible = a > 0.3; sp.position.set(u.x * (1 + q) + Math.sin(v * 3 + u.ph * 9) * 0.05, 0.3 + q * 1.6 * a, u.z * (1 + q)); sp.scale.setScalar(1 - q);
    });
    F.smokes.forEach((sk) => {
      const q = (v * 0.12 + sk.userData.ph) % 1;
      sk.position.set(Math.sin(q * 5 + sk.userData.ph * 6) * 0.15 + q * 0.5, 0.9 + q * 2.6, Math.cos(q * 4) * 0.1); sk.scale.setScalar(0.6 + q * 2.2);
      sk.material.opacity = 0.22 * a * (1 - q);
    });
  }

  // v2 (2026-11-25 本人「新しい人の作り方はおすすめで」): 2 歳になるまでの子は、人のモデルでなく、母が胸に抱く布の包みで見せる
  const isBaby = (P, n) => { const k = M.kin[n]; return !!(M.opts2.v2 && k && k.born != null && (P.day - k.born) / 120 < 2); };
  function bundleMesh() {
    const g = new THREE.Group(), K = M.K;
    const cloth = new THREE.Mesh(new THREE.SphereGeometry(0.11 * K, 10, 8), new THREE.MeshLambertMaterial({ color: 0x9a7a52 })); cloth.scale.set(1.5, 0.8, 0.85); g.add(cloth);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.055 * K, 10, 8), new THREE.MeshLambertMaterial({ color: 0xc08c6a })); head.position.set(0.15 * K, 0.03 * K, 0); g.add(head);
    return g;
  }
  function babiesFrame(P) {
    for (const n in M.figs) {
      const baby = P.plan[n] && P.plan[n].alive && isBaby(P, n);
      let B = M.bundles[n];
      if (baby) M.figs[n].userData.pelvis.visible = false;
      const mom = baby && M.people[M.kin[n].mother];
      if (!baby || !mom || !mom.root.visible) { if (B) B.visible = false; if (baby && M.labels[n]) M.labels[n].pos = null; continue; }
      if (!B) { B = M.bundles[n] = bundleMesh(); M.scene.add(B); }
      const ch = mom.g.scene.getObjectByName("J_Bip_C_UpperChest") || mom.head;
      const at = ch.getWorldPosition(new THREE.Vector3()), fw = new THREE.Vector3(Math.cos(mom.root.rotation.y - Math.PI / 2), 0, -Math.sin(mom.root.rotation.y - Math.PI / 2));
      B.position.copy(at).add(fw.multiplyScalar(0.14 * M.K)).add(new THREE.Vector3(0, -0.06 * M.K, 0)); B.rotation.y = mom.root.rotation.y; B.visible = true;
      M.figs[n].position.copy(B.position);
      if (M.labels[n]) M.labels[n].pos = B.position.clone().add(new THREE.Vector3(0, 0.25 * M.K, 0));
    }
  }

  // v2 (2026-11-26 本人「人同士もすり抜けます」): 見えている人どうしが体の幅より近いとき、横に押し離す (毎コマ。3 回くり返す)
  function separate() {
    const L = Object.entries(M.people).filter(([, R]) => R.root.visible).map(([n, R]) => ({ n, R }));
    const D0 = 0.62 * M.K / 1.4;  // 体の幅 (約 0.44 m) をマスに
    for (let it = 0; it < 3; it++) {
      for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) {
        const a = L[i].R.root.position, b = L[j].R.root.position, dx = b.x - a.x, dz = b.z - a.z, d = Math.hypot(dx, dz);
        if (d >= D0) continue;
        const ux = d > 1e-4 ? dx / d : Math.cos(i + j), uz = d > 1e-4 ? dz / d : Math.sin(i + j), m = (D0 - d) / 2;
        a.x -= ux * m; a.z -= uz * m; b.x += ux * m; b.z += uz * m;
      }
    }
    for (const { n, R } of L) {
      R.root.updateMatrixWorld(true);
      if (M.figs[n]) M.figs[n].position.copy(R.root.position);
      if (R.head && M.labels[n]) M.labels[n].pos = R.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.32 * M.K, 0));
    }
  }

  // 人ごとの予定: [{ t0, clip, mode, rate, off, at(v), head(v) }] を始まりの順に
  function planFor(P, D, n) {
    const p = P.plan[n], info = M.people[n].info, seg = {};
    for (const s of P.segs) seg[s.key] = s;
    const fire = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 }, SPD = WALK * M.K;  // 歩く速さ (マス/秒)
    const E = [], still = (pt, h) => ({ at: () => pt, head: () => h });
    const add = (e) => {
      const q = E[E.length - 1], x = { off: 0, rate: 1, ...e };
      if (q && x.t0 <= q.t0) x.t0 = q.t0 + 0.01;
      if (q && q.clip === x.clip && q.mode === x.mode && q.rate === x.rate && x.mode !== "once") x.off = (x.t0 - q.t0) * q.rate + q.off;  // 同じ動きが続くときは、途中から続ける
      E.push(x);
    };
    // opts.v2 (2026-11-25、S1V・G1 の F の撮り直しから。本人の直し): 住まいにめり込まない・夜は住まいに入る・同じ場所の人の間をあける。ないときは前と同じ
    const V2 = !!M.opts2.v2, hutOn = V2 && M.world && M.world.hutDay !== null && P.day >= M.world.hutDay;
    if (V2) tentsFor(P);
    const hutC = { x: fire.x - 3.2, y: fire.y - 2.2 }, HUT_R = 2.3;  // replay3d.js の住まい (キャンプから -3.2, -2.2。壁の半径 1.4・屋根 1.8)
    const out_ = (pt) => {  // 住まいの円の中なら、外へ押し出す
      if (!hutOn) return pt;
      const dx = pt.x - hutC.x, dy = pt.y - hutC.y, d = Math.hypot(dx, dy);
      if (d >= HUT_R) return pt;
      const a = d > 1e-3 ? Math.atan2(dy, dx) : Math.atan2(fire.y - hutC.y, fire.x - hutC.x);
      return { x: hutC.x + Math.cos(a) * HUT_R, y: hutC.y + Math.sin(a) * HUT_R };
    };
    const ringOf0 = (m) => (P.plan[m] ? lerp(fire, P.plan[m].ring, RING) : fire);
    const ring = V2 ? pushOut(P, out_(ringOf0(n))) : ringOf0(n), ringOf = (m) => (V2 ? pushOut(P, out_(ringOf0(m))) : ringOf0(m));  // 火のまわりの輪は、人の体の大きさに合わせて広げる
    if (V2 && p.place && p.place.id !== "camp") {  // 同じ場所の人: 場所のまん中からのはなれを、体の大きさに合わせて広げる
      const c = { x: p.place.x + 0.5, y: p.place.y + 0.5 };
      p.spot = lerp(c, p.spot, RING);
    }
    if (V2) p.spot = pushOut(P, out_(p.spot));
    const builds = V2 ? (P.work || []).filter((e) => e.type === "住まい" && /建て/.test(e.text)) : [];
    const builder = builds.some((e) => e.who === n || (e.text || "").startsWith(n + " "));
    if (builder) {  // v2: 住まいを建てた人は、住まいのまわりで柱を立てる・組む (のり出す・背のび・手渡し)
      const a = Math.atan2(fire.y - hutC.y, fire.x - hutC.x) + 0.9 + p.i * 1.1;
      p.spot = { x: hutC.x + Math.cos(a) * 2.0, y: hutC.y + Math.sin(a) * 2.0 };
    }
    let here = ring;
    const walk1 = (to, t0) => {
      const from = here, d = Math.hypot(to.x - from.x, to.y - from.y), dur = d / SPD, h = face(from, to);
      if (d < 0.05) return t0;
      add({ t0, clip: "walk", mode: "loop", rate: WALK / info.walk.speed, at: (v) => lerp(from, to, clamp((v - t0) / dur)), head: () => h });
      here = to; return t0 + dur;
    };
    const walkTo = (to, t0) => {  // v2: 住まい・木をよけて歩く
      if (!V2) return walk1(to, t0);
      let t = t0;
      for (const w of route(P, here, to)) t = walk1(w, t);
      return t;
    };
    // 夜明け: 火のまわりで見回す
    add({ t0: -1, clip: "idle", mode: "pp", rate: 0.8, off: p.i * 1.3, ...still(ring, face(ring, fire)) });
    // 出発: 人の速さで歩いて、着いたら仕事を始める
    let t = walkTo(p.spot, seg.go.v0 + 0.6 + 0.5 * p.i);
    const tLeave = Math.max(t + 2, seg.back.v1 - 0.6 - (p.dist + 2) / SPD);
    const out = face(ring, p.spot);
    if (builder) {
      // 2026-11-26 本人「家を建てるのもモーションが欲しい」: 持ち上げる → 杭を打つ → 結わえる (動きの記録にあれば。なければ前の 4 つ)
      const hd = face(p.spot, hutC), kinds = info.hammer ? ["lift", "hammer", "tie", "hammer"] : ["stretch", "reach", "give", "pick"];
      for (let k = 0; t < tLeave; k++) {
        const c = kinds[(k + p.i) % kinds.length];
        add({ t0: t, clip: c, mode: c === "lift" ? "once" : "pp", ...still(here, hd + (rnd(p.i, k) - 0.5) * 0.3) });
        t += Math.min(info[c].sec * (c === "lift" ? 1 : 1.4), 8);
      }
    } else if (p.activity === "採集" && V2) {  // v2: 採る場所に植物を置き、そちらを向いて採る。林は実のなる木 (のり出す・背のびして取る)、ほかは草むら (かがんで拾う・しゃがんで調べる)
      const tree = /林|森/.test(String((p.place && (p.place.label || p.place.id)) || ""));
      const kinds = tree ? ["reach", "stretch", "pick"] : ["pick", "probe"];
      // 植物は、カメラ (南東の上から見る) から見て人の向こう側に置く (手前に置くと、木が人をかくす。2026-11-26 見直し K10)
      const at = { x: here.x - 0.55, y: here.y - 0.78 }, look = face(here, at);
      (M.plants.get(P) || M.plants.set(P, []).get(P)).push({ at, tree, seed: p.i });
      for (let k = 0; t < tLeave; k++) {
        const c = kinds[(k + p.i) % kinds.length];
        add({ t0: t, clip: c, mode: "pp", ...still(here, look + (rnd(p.i, k) - 0.5) * 0.35) });
        t += Math.min(info[c].sec * 1.6, 7);
      }
    } else if (p.activity === "採集") {
      for (let k = 0; t < tLeave; k++) {
        const c = GATHER[(k + p.i) % GATHER.length];
        add({ t0: t, clip: c, mode: "pp", ...still(here, out + (rnd(p.i, k) - 0.5) * 1.6) });
        t += Math.min(info[c].sec * 1.6, 7);
      }
    } else if (p.activity === "探索") {  // 用心して歩きさがす → 地面をさがす → 見回す、をくり返す (場所のまわり 1.6 マスの中)
      const sp = Math.max(0.05, info.search.speed) * M.K;
      for (let k = 0; t < tLeave; k++) {
        if (k % 3 === 0) {
          const a = rnd(p.i, k) * Math.PI * 2, r = 0.6 + rnd(p.i, k + 50);
          const to = V2 ? pushOut(P, { x: p.spot.x + Math.cos(a) * r, y: p.spot.y + Math.sin(a) * r }) : { x: p.spot.x + Math.cos(a) * r, y: p.spot.y + Math.sin(a) * r };
          const from = here, d = Math.hypot(to.x - from.x, to.y - from.y), dur = Math.min(d / sp, Math.max(1, tLeave - t), 9), h = face(from, to);
          const end = lerp(from, to, clamp(dur * sp / Math.max(d, 1e-6))), t0 = t;
          add({ t0, clip: "search", mode: "loop", at: (v) => lerp(from, end, clamp((v - t0) / dur)), head: () => h });
          here = end; t += dur;
        } else {
          const c = k % 3 === 1 ? "look" : "idle";
          add({ t0: t, clip: c, mode: "pp", ...still(here, out + (rnd(p.i, k + 9) - 0.5) * 2.4) });
          t += Math.min(info[c].sec, 5);
        }
      }
    } else if (V2 && (p.activity === "畑仕事" || p.activity === "道具づくり" || p.activity === "土器づくり")) {
      // v2 (2026-11-26): 畑仕事は、かがんで地面を見る・しゃがんで手入れ・草を拾う。道具や土器づくりは、しゃがんで石を打つ・調べる (そばに石を置く)
      const farm = p.activity === "畑仕事", kinds = farm ? ["look", "probe", "pick"] : info.hammer ? ["probe", "hammer", "probe", "pick"] : ["probe", "pick"];
      const at = { x: here.x - 0.45, y: here.y - 0.6 }, look = face(here, at);
      if (!farm) (M.props.get(P) || M.props.set(P, []).get(P)).push({ at, kind: p.activity });
      for (let k = 0; t < tLeave; k++) {
        const c = kinds[(k + p.i) % kinds.length];
        add({ t0: t, clip: c, mode: "pp", ...still(here, look + (rnd(p.i, k + 3) - 0.5) * 0.4) });
        t += Math.min(info[c].sec * 1.5, 7);
      }
    } else {
      add({ t0: t, clip: "idle", mode: "pp", ...still(here, face(here, fire)) });
    }
    // 帰り: 帰りの終わりに火のまわりに着くように出る
    t = walkTo(ring, Math.max(t, tLeave));
    const atFire = face(ring, fire);
    add({ t0: t, clip: "idle", mode: "pp", ...still(ring, atFire) });
    if (V2 && lighterOf(P) === n) {  // v2 (本人「火をつけるところから」): 火をおこす人は、帰ったら火のそばにしゃがんで火をおこし、輪にもどる
      const side = lerp(fire, ring, 0.95 / Math.max(0.1, Math.hypot(ring.x - fire.x, ring.y - fire.y)));
      const t1 = walkTo(side, Math.max(t + 0.3, seg.eve.v0 - 5));
      add({ t0: t1, clip: "probe", mode: "pp", rate: 0.8, ...still(side, face(side, fire)) });
      M.fireAt.set(P, t1 + 1.2);
      t = walkTo(ring, t1 + 4.5);
      add({ t0: t, clip: "idle", mode: "pp", ...still(ring, atFire) });
    }
    // 夕方: 話す人は話し、ほかの人は話す人を向く。分ける人は相手を向いて手渡し、もらった人はそのあと食べる
    const eve = seg.eve, N = P.eve.length || 1, h = eve.sec / N;
    let eating = false, last = "";
    P.eve.forEach((e, k) => {
      const tk = Math.max(eve.v0 + k * h, t + 0.01);
      let clip = eating ? "eat" : "idle", hd = atFire;
      if (e.who === n && e.type === "話す") { clip = "talk"; hd = atFire; }
      else if (e.who === n && e.type === "分ける") { clip = "give"; hd = face(ring, ringOf(e.data && e.data.to)); }
      else if (e.type === "話す" && P.plan[e.who]) hd = face(ring, ringOf(e.who));
      else if (e.type === "分ける" && e.data && e.data.to === n) { clip = "idle"; hd = face(ring, ringOf(e.who)); eating = true; }
      const key = clip + ":" + hd.toFixed(2);
      if (key !== last || clip === "give") add({ t0: tk, clip, mode: clip === "give" ? "once" : "pp", rate: clip === "give" ? info.give.sec / Math.max(1, h * 0.9) : 1, ...still(ring, hd) });
      last = key;
    });
    if (P.eve.length) add({ t0: eve.v1, clip: eating ? "eat" : "idle", mode: "pp", ...still(ring, atFire) });
    // 夜: 火から少しはなれて、横になる (起き上がる記録を逆に流す)
    here = ring;
    const tent = V2 && tentsFor(P).find((q) => q.home === p.home);
    if (tent) {  // 家族の小屋がある夜: 戸口まで歩いて、中に入る
      t = walkTo(tent.door, seg.night.v0 + 0.5 + 0.35 * p.i);
      add({ t0: t + 0.1, clip: "idle", mode: "pp", hide: true, ...still(tent.door, face(tent.door, tent.pt)) });
      return E;
    }
    if (hutOn) {  // 住まいがある夜: 戸口まで歩いて、中に入る (見えなくなる)
      const a = Math.atan2(fire.y - hutC.y, fire.x - hutC.x), door = { x: hutC.x + Math.cos(a) * 1.5, y: hutC.y + Math.sin(a) * 1.5 };
      t = walkTo(door, seg.night.v0 + 0.5 + 0.6 * p.i);
      add({ t0: t + 0.1, clip: "idle", mode: "pp", hide: true, ...still(door, face(door, hutC)) });
      return E;
    }
    const bed = lerp(fire, ring, 1.8);
    t = walkTo(bed, seg.night.v0 + 0.5 + 0.6 * p.i);
    add({ t0: t + 0.3, clip: "lie", mode: "rev", rate: 0.9, ...still(bed, face(fire, bed)) });
    return E;
  }

  // v2: 採集の植物 (その日の採る場所ごと)。実のなる木 (幹・葉・赤い実) と、草むら (細い葉と穂)。大きさは人の体に合わせる (M.K)
  function plantGroup(list) {
    const g = new THREE.Group(), K = M.K;
    const trunkM = new THREE.MeshLambertMaterial({ color: 0x6b4a2e }), leafM = new THREE.MeshLambertMaterial({ color: 0x3f7a3a }),
      fruitM = new THREE.MeshLambertMaterial({ color: 0xb8322a }), grassM = new THREE.MeshLambertMaterial({ color: 0x7a9a3a }), seedM = new THREE.MeshLambertMaterial({ color: 0xc9a650 });
    for (const q of list) {
      const base = M.w2t(q.at.x, q.at.y), o = new THREE.Group(); o.position.copy(base);
      if (q.tree) {
        const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.06 * K, 0.09 * K, 1.3 * K, 7), trunkM); tr.position.y = 0.65 * K; o.add(tr);
        for (let k = 0; k < 4; k++) {
          const lf = new THREE.Mesh(new THREE.IcosahedronGeometry((0.5 - 0.06 * k) * K, 0), leafM);
          lf.position.set(Math.cos(k * 1.9 + q.seed) * 0.28 * K, (1.45 + 0.18 * k) * K, Math.sin(k * 1.9 + q.seed) * 0.28 * K); o.add(lf);
        }
        for (let k = 0; k < 9; k++) {
          const fr = new THREE.Mesh(new THREE.SphereGeometry(0.06 * K, 6, 5), fruitM), a = k * 2.4 + q.seed;
          fr.position.set(Math.cos(a) * 0.5 * K, (1.15 + rnd(q.seed, k) * 0.6) * K, Math.sin(a) * 0.5 * K); o.add(fr);
        }
      } else {
        for (let k = 0; k < 14; k++) {
          const a = k * 2.4 + q.seed, r = (0.1 + rnd(q.seed, k) * 0.45) * K, h = (0.35 + rnd(k, q.seed) * 0.25) * K;
          const bl = new THREE.Mesh(new THREE.ConeGeometry(0.03 * K, h, 4), grassM); bl.position.set(Math.cos(a) * r, h / 2, Math.sin(a) * r); bl.rotation.z = (rnd(q.seed, k + 7) - 0.5) * 0.5; o.add(bl);
          if (k % 2 === 0) { const sd = new THREE.Mesh(new THREE.SphereGeometry(0.035 * K, 5, 4), seedM); sd.scale.y = 2; sd.position.set(bl.position.x, h + 0.03 * K, bl.position.z); o.add(sd); }
        }
      }
      g.add(o);
    }
    return g;
  }

  // v2: 住まいを建てる日 (記録の「でき具合 約 N 割」と「住まいができた」) は、昼のあいだに柱 → 壁 → 屋根と少しずつできていく
  function hutGrowth(P, v) {
    const H = M.world.hut, ev = (P.work || []).filter((e) => e.type === "住まい");
    const steps = ev.map((e) => (/住まいができた/.test(e.text) ? 1 : (/でき具合 約 (\d+) 割/.exec(e.text) || [])[1] / 10)).filter((x) => x > 0);
    if (!H.userData.parts) {  // 柱 (8 本) を足して、壁と屋根をおぼえる
      const poleM = new THREE.MeshLambertMaterial({ color: 0x6b4a2e }), poles = new THREE.Group();
      for (let k = 0; k < 8; k++) { const pl = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.06, 2.0, 5), poleM); pl.position.set(Math.cos(k * 0.785) * 1.35, 1.0, Math.sin(k * 0.785) * 1.35); poles.add(pl); }
      poles.visible = false; H.add(poles);
      H.userData.parts = { wall: H.children[0], roof: H.children[1], poles };
    }
    const { wall, roof, poles } = H.userData.parts;
    if (!steps.length) { wall.scale.y = 1; wall.position.y = 0.55; roof.visible = true; roof.scale.setScalar(1); poles.visible = false; return; }
    // その日のはじめのでき具合 (前の日の記録の数。わからなければ、この日の数の 6 割) から、昼の終わりにこの日の数になる
    const end = Math.max(...steps), seg = P.segs.find((s) => s.key === "work") || P.segs[2];
    const start = end >= 1 ? 0.7 : Math.max(0, end - 0.3), u = clamp((v - seg.v0) / Math.max(1, seg.v1 - seg.v0));
    const g = start + (end - start) * u;
    H.visible = true; poles.visible = true;
    const w = clamp((g - 0.3) / 0.4);  // 3 割までは柱だけ、7 割で壁、そのあと屋根
    wall.visible = w > 0; wall.scale.y = Math.max(0.01, w); wall.position.y = 0.55 * w;
    const r = clamp((g - 0.7) / 0.3); roof.visible = r > 0; roof.scale.setScalar(Math.max(0.01, r));
  }

  // v2: 動物 (記録の日だけ)。村の木や丘と同じ、簡単な形の四つ足。ルク (狩りの獲物、鹿に似た草食の獣) と ザガ (夜にキャンプへ来る、狼に似た獣)
  function beast(kind) {
    const K = M.K, g = new THREE.Group(), legs = [];
    const C = kind === "zaga" ? { body: 0x3a3a3e, belly: 0x55555a, s: 1.0 } : kind === "goat" ? { body: 0xe8e2d4, belly: 0xb8ab94, s: 0.6 } : { body: 0x8a5a32, belly: 0xc8a27a, s: 1.15 };
    const m = new THREE.MeshLambertMaterial({ color: C.body }), mb = new THREE.MeshLambertMaterial({ color: C.belly }), s = C.s * K;
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.32 * s, 10, 8), m); body.scale.set(1.7, 0.85, 0.8); body.position.y = 0.72 * s; g.add(body);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.08 * s, 0.12 * s, 0.4 * s, 6), m); neck.position.set(0.5 * s, 0.95 * s, 0); neck.rotation.z = kind === "zaga" ? -0.9 : -0.5; g.add(neck);
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.12 * s, 0.38 * s, 7), kind === "zaga" ? m : mb); head.rotation.z = -Math.PI / 2;
    head.position.set(kind === "zaga" ? 0.78 * s : 0.7 * s, kind === "zaga" ? 1.0 * s : 1.15 * s, 0); g.add(head);
    for (const z of [-1, 1]) {  // 耳 (ルクは角も)
      const ear = new THREE.Mesh(new THREE.ConeGeometry(0.04 * s, 0.14 * s, 4), m); ear.position.set(head.position.x - 0.12 * s, head.position.y + 0.12 * s, z * 0.07 * s); g.add(ear);
      if (kind === "goat") { const hn = new THREE.Mesh(new THREE.ConeGeometry(0.03 * s, 0.22 * s, 5), new THREE.MeshLambertMaterial({ color: 0x6a5a48 })); hn.position.set(head.position.x - 0.16 * s, head.position.y + 0.18 * s, z * 0.06 * s); hn.rotation.z = 0.5; g.add(hn); }
      if (kind === "ruku") { const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.012 * s, 0.02 * s, 0.35 * s, 4), mb); ant.position.set(head.position.x - 0.14 * s, head.position.y + 0.3 * s, z * 0.1 * s); ant.rotation.x = z * 0.35; g.add(ant); }
    }
    if (kind === "zaga") { const tail = new THREE.Mesh(new THREE.ConeGeometry(0.06 * s, 0.45 * s, 5), m); tail.position.set(-0.62 * s, 0.75 * s, 0); tail.rotation.z = -2.2; g.add(tail); }
    for (const [x, z] of [[0.33, 0.13], [0.33, -0.13], [-0.33, 0.13], [-0.33, -0.13]]) {
      const pv = new THREE.Group(); pv.position.set(x * s, 0.62 * s, z * s);
      const lg = new THREE.Mesh(new THREE.CylinderGeometry(0.035 * s, 0.03 * s, 0.62 * s, 5), m); lg.position.y = -0.31 * s; pv.add(lg); g.add(pv); legs.push(pv);
    }
    g.userData.legs = legs;
    return g;
  }
  function animalsFor(P) {
    const D = M.D, fire = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 }, list = [];
    const seg = Object.fromEntries(P.segs.map((x) => [x.key, x]));
    for (const e of (P.work || []).filter((e) => e.type === "狩り")) {  // 狩り: 狩った人の場所の先に、ルクの群れ (3 頭)。しとめた日は 1 頭が昼の終わりに倒れる
      const who = Object.keys(P.plan).find((n) => (e.text || "").startsWith(n) && P.plan[n].spot);
      if (!who) continue;
      const sp = P.plan[who].spot, a = face(fire, sp), got = /しとめた/.test(e.text) && !/しとめられなかった/.test(e.text);
      for (let k = 0; k < 3; k++) {
        const c = { x: sp.x + Math.cos(a + (k - 1) * 0.5) * (3.2 + k * 0.6), y: sp.y - Math.sin(a + (k - 1) * 0.5) * (3.2 + k * 0.6) };
        const wob = (v) => ({ x: c.x + Math.sin(v * 0.13 + k) * 0.5, y: c.y + Math.cos(v * 0.11 + k * 2) * 0.5 });
        list.push({ kind: "ruku", at: wob, head: (v) => a + Math.sin(v * 0.2 + k) * 1.2, walk: (v) => v >= seg.go.v0 && v < seg.back.v1, from: seg.go.v0, to: seg.back.v1,
          down: got && k === 0 ? (v) => clamp((v - (seg.work.v0 + seg.work.sec * 0.7)) / 0.8) : null });
      }
    }
    // ヤギ (飼っている数。季節の記録): キャンプの南東の囲いの中で、草をはんで歩く。夜は囲いの中で止まる
    const gs = (D.goats || []).find((g) => P.day >= g.from && P.day <= g.to), ng = Math.min(30, D.goatDay && D.goatDay[P.day] != null ? D.goatDay[P.day] : gs ? gs.n : 0);
    if (ng > 0) {
      const pen = { x: fire.x + 4.5, y: fire.y + 4.0 }, R0 = 1.2 + 0.25 * Math.sqrt(ng);
      M.pen = { pen, r: R0 };
      for (let k = 0; k < ng; k++) {
        const ph = k * 2.39996, rr = R0 * 0.75 * Math.sqrt((k + 0.5) / ng);
        const c = { x: pen.x + Math.cos(ph) * rr, y: pen.y + Math.sin(ph) * rr };
        const at = (v) => { const day = v < seg.eve.v0; return day ? { x: c.x + Math.sin(v * 0.07 + k) * 0.5, y: c.y + Math.cos(v * 0.06 + k * 1.7) * 0.5 } : c; };
        list.push({ kind: "goat", at, head: (v) => k + v * 0.05, walk: (v) => v < seg.eve.v0 && Math.sin(v * 0.4 + k) > 0.3, from: -1, to: 1e9 });
      }
    } else M.pen = null;
    for (const e of (P.night || []).filter((e) => /ザガ/.test(e.text || ""))) {  // ザガ: 夜、遠くから火のほうへ来て、去る。火を嫌った夜は遠くで止まる
      const victim = Object.keys(P.plan).find((n) => (e.text || "").includes(n + " が") || (e.text || "").includes(" " + n + " "));
      const near = /近づかなかった/.test(e.text) || !victim ? null : lerp(fire, P.plan[victim].ring, RING * 1.6);
      const a = 2.2 + (e.id || 0) % 3, far = { x: fire.x + Math.cos(a) * 14, y: fire.y + Math.sin(a) * 14 };
      const stop = near || { x: fire.x + Math.cos(a) * 6, y: fire.y + Math.sin(a) * 6 };
      const n0 = seg.night.v0 + 1, n1 = seg.night.v1, d = n1 - n0;
      const at = (v) => { const u = (v - n0) / d; return u < 0.35 ? lerp(far, stop, clamp(u / 0.35)) : u < 0.6 ? stop : lerp(stop, far, clamp((u - 0.6) / 0.35)); };
      list.push({ kind: "zaga", at, head: (v) => ((v - n0) / d < 0.6 ? face(far, stop) : face(stop, far)), walk: (v) => { const u = (v - n0) / d; return (u < 0.35 || u > 0.6) && u < 0.95; }, from: n0, to: n1 - 0.3 });
    }
    return list;
  }
  function animalsFrame(P, v) {
    if (M.animP !== P) {
      if (M.animG) M.scene.remove(M.animG);
      M.animP = P; M.anims = animalsFor(P); M.animG = new THREE.Group(); M.scene.add(M.animG);
      for (const A of M.anims) { A.g = beast(A.kind); M.animG.add(A.g); }
      if (M.pen) {  // ヤギの囲い (杭と横木)
        const fm = new THREE.MeshLambertMaterial({ color: 0x6b4a2e }), n = Math.round(M.pen.r * 6);
        for (let k = 0; k < n; k++) {
          const a = (k / n) * Math.PI * 2, b = ((k + 1) / n) * Math.PI * 2;
          const p1 = M.w2t(M.pen.pen.x + Math.cos(a) * M.pen.r, M.pen.pen.y + Math.sin(a) * M.pen.r), p2 = M.w2t(M.pen.pen.x + Math.cos(b) * M.pen.r, M.pen.pen.y + Math.sin(b) * M.pen.r);
          const post = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.7, 5), fm); post.position.copy(p1).add(new THREE.Vector3(0, 0.35, 0)); M.animG.add(post);
          const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, p1.distanceTo(p2), 4), fm);
          rail.position.copy(p1).lerp(p2, 0.5).add(new THREE.Vector3(0, 0.5, 0)); rail.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), p2.clone().sub(p1).normalize()); M.animG.add(rail);
        }
      }
    }
    for (const A of M.anims) {
      A.g.visible = v >= A.from && v < A.to;
      if (!A.g.visible) continue;
      const pt = A.at(v); A.g.position.copy(M.w2t(pt.x, pt.y)); A.g.rotation.set(0, A.head(v), 0);
      const sw = A.walk(v) ? Math.sin(v * 9) * 0.5 : 0;
      A.g.userData.legs.forEach((lg, i) => (lg.rotation.z = (i % 2 ? sw : -sw) * (i < 2 ? 1 : -1)));
      if (A.down) { const dn = A.down(v); A.g.rotation.x = dn * Math.PI / 2; A.g.position.y += dn * 0.2 * M.K; }
    }
  }

  // v2: 植物が育つ。(1) キャンプのそばに「木の実の木が育った」木 (記録の日から 30 日で若木から大きな木に)。(2) 畑に、芽 → 伸びる → 実る穂
  function growFrame(P) {
    if (M.growP === P) return;
    M.growP = P;
    if (M.growG) M.scene.remove(M.growG);
    const g = M.growG = new THREE.Group(), K = M.K, D = M.D, fire = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 };
    const trunkM = new THREE.MeshLambertMaterial({ color: 0x6b4a2e }), leafM = new THREE.MeshLambertMaterial({ color: 0x4a8a3e }), fruitM = new THREE.MeshLambertMaterial({ color: 0xb8322a });
    groveList(P).forEach(({ pt, sz, k }) => {  // 殻を捨てた所と、種をまいた所に、ひまわりの並びで (groveList)
      const o = new THREE.Group(); o.position.copy(M.w2t(pt.x, pt.y)); o.scale.setScalar(sz);
      const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.05 * K, 0.08 * K, 1.1 * K, 6), trunkM); tr.position.y = 0.55 * K; o.add(tr);
      const lf = new THREE.Mesh(new THREE.IcosahedronGeometry(0.5 * K, 0), leafM); lf.position.y = 1.35 * K; o.add(lf);
      if (sz > 0.72) for (let q = 0; q < 6; q++) { const fr = new THREE.Mesh(new THREE.SphereGeometry(0.06 * K, 6, 5), fruitM); fr.position.set(Math.cos(q * 2.4 + k) * 0.48 * K, (1.15 + rnd(k, q) * 0.4) * K, Math.sin(q * 2.4 + k) * 0.48 * K); o.add(fr); }
      g.add(o);
    });
    // 畑: replay3d.js の畑の板 (plots) と同じ日の数え方 (まいて 30 日は土、90 日までは芽から伸びる、そのあと 120 日までは実る)
    const W = M.world, on = (W.sowings || []).filter((e) => e.day <= P.day && P.day < e.day + 120);
    const stemM = new THREE.MeshLambertMaterial({ color: 0x6a9a3a }), earM = new THREE.MeshLambertMaterial({ color: 0xd9a520 });
    on.forEach((e, k) => {
      const m = W.plots[k]; if (!m) return;
      const age = P.day - e.day; if (age < 12) return;
      const h = age < 30 ? 0.12 : age < 90 ? 0.12 + 0.45 * (age - 30) / 60 : 0.6, ripe = age >= 90;
      for (let q = 0; q < 24; q++) {
        const x = ((q % 6) / 5 - 0.5) * 1.3, z = (Math.floor(q / 6) / 3 - 0.5) * 0.9;
        const st = new THREE.Mesh(new THREE.ConeGeometry(0.035, h, 4), ripe ? earM : stemM); st.position.set(m.position.x + x, m.position.y + h / 2, m.position.z + z); g.add(st);
        if (ripe) { const ear = new THREE.Mesh(new THREE.SphereGeometry(0.05, 5, 4), earM); ear.scale.y = 2.2; ear.position.set(st.position.x, m.position.y + h + 0.05, st.position.z); g.add(ear); }
      }
    });
    M.scene.add(g);
  }

  function localTime(e, v, dur) {
    const lt = Math.max(0, (v - e.t0) * e.rate + e.off);
    if (e.mode === "loop") return lt % dur;
    if (e.mode === "pp") { const m = lt % (2 * dur); return m < dur ? m : 2 * dur - m; }
    if (e.mode === "once") return Math.min(lt, dur);
    return Math.max(0, dur - lt);  // rev
  }

  // 昼の組: 行く場所と活動が同じ人を 1 組に。4 組以上なら、行く場所の近い組をまとめて 3 組まで。組の名前は「ルオ・イサ — 東の林で採集」
  function dayGroups(P, alive) {
    let G = [];
    for (const n of alive) {
      const p = P.plan[n], k = (p.place ? p.place.id : "") + "|" + p.activity;
      let g = G.find((q) => q.k === k);
      if (!g) G.push(g = { k, names: [], spot: p.spot, place: p.place, acts: new Set() });
      g.names.push(n); g.acts.add(p.activity);
    }
    while (G.length > 3) {
      let best = null;
      for (let i = 0; i < G.length; i++) for (let j = i + 1; j < G.length; j++) {
        const d = Math.hypot(G[i].spot.x - G[j].spot.x, G[i].spot.y - G[j].spot.y);
        if (!best || d < best[0]) best = [d, i, j];
      }
      const [, i, j] = best; G[i].names.push(...G[j].names); G[j].acts.forEach((a) => G[i].acts.add(a)); G.splice(j, 1);
    }
    const short = (pl) => (pl ? String(pl.label || pl.id).replace(/\s*\(.*\)\s*$/, "") : "");
    return G.map((g) => ({ names: g.names, title: `${g.names.join("・")} — ${short(g.place)}${g.place && g.place.id !== "camp" ? "で" + [...g.acts].join("・") : ""}` }));
  }

  // 出来事の短い吹き出し (opts.bubbles、D1V。本人の選んだ案 C): 上に重なる出来事の帯の代わりに、した人の頭の上に 15 字ほどで 3.5 秒出して消す。
  // 長い元の字は出さない。夕方の話も同じ形 (最初の 1 文、長ければ 15 字で切る)。同じ組の画面の中で重ならないよう、前の吹き出しが消えてから出す
  const BUBBLE = 3.5, FADEB = 0.6;
  function shortText(e) {
    const t = String(e.text || "");
    if (e.type === "採集") return "食べ物を採る";
    if (e.type === "探索") {
      const h = t.match(/(ルクの群れ|[^\s:、]+の群れ) \((\d+) 頭\)/); if (h) return `${h[1]} ${h[2]} 頭を見つけた`;
      const f = t.match(/には (\S+) が多い/); if (f) return `${f[1]}が多い`;
      return "あたりをさがす";
    }
    if (e.type === "分ける") return `${(e.data && e.data.to) || ""}に分ける`;
    if (e.type === "話す") {
      const q = (t.match(/「(.*?)」?$/) || [, t])[1].replace(/」$/, ""), first = q.split(/[。！？!?]/)[0] || q;
      return "「" + (first.length > 16 ? first.slice(0, 15) + "…" : first) + "」";
    }
    if (e.type === "蓄える") return "蓄えに入れる";
    if (e.type === "蓄えから取る") return "蓄えから取る";
    const s = t.replace(new RegExp("^" + (e.who || "") + "\\s*(が|は)?\\s*"), "").replace(/\s*\(.*?\)/g, "");
    return s.length > 16 ? s.slice(0, 15) + "…" : s;
  }
  const bubbleSched = new WeakMap();
  function bubblesFor(P) {
    if (bubbleSched.has(P)) return bubbleSched.get(P);
    const seg = {}; for (const s of P.segs) seg[s.key] = s;
    const want = [];
    P.work.forEach((e, k) => { if (e.who) want.push({ who: e.who, t: seg.work.v0 + seg.work.sec * (k + 0.5) / (P.work.length + 1), len: BUBBLE, text: shortText(e) }); });
    const N = P.eve.length || 1, h = seg.eve.sec / N;
    P.eve.forEach((e, k) => { if (e.who) want.push({ who: e.who, t: seg.eve.v0 + k * h, len: e.type === "話す" ? Math.max(BUBBLE, h * 0.95) : Math.min(BUBBLE, h * 0.95), text: shortText(e), eve: true }); });
    (P.night || []).forEach((e, k) => { if (e.who) want.push({ who: e.who, t: seg.night.v0 + 0.5 + k * BUBBLE, len: BUBBLE, text: shortText(e) }); });
    const alive = Object.keys(P.plan).filter((n) => P.plan[n].alive);
    const grp = Object.fromEntries(dayGroups(P, alive).flatMap((g, i) => g.names.map((n) => [n, i])));
    const end = {}, out = [];
    for (const b of want.sort((a, c) => a.t - c.t)) {
      const g = b.eve ? "eve" : grp[b.who] ?? b.who;  // 同じ画面の中では、前の吹き出しが消えてから
      const t0 = b.eve ? b.t : Math.max(b.t, end[g] || -1);
      out.push({ ...b, t0, t1: t0 + b.len }); end[g] = t0 + b.len;
    }
    bubbleSched.set(P, out);
    return out;
  }

  const COLS = ["#f2b134", "#4cb3f0", "#f0609a"];
  // 人 n の、時刻 v の場所 (マス)。予定 (planFor) から決まるので、どの時刻からでも同じ答え
  function posAt(P, n, v) {
    const E = sched.get(P) && sched.get(P)[n]; if (!E) return null;
    let j = 0; while (j + 1 < E.length && E[j + 1].t0 <= v) j++;
    return E[j].at(v);
  }
  // カットごとの画面の分け方 (組・何枚・引きの絵)。opts.cuts[日] = カットの始まりの時刻 (その日の秒)
  const layouts = new WeakMap();
  function layoutAt(P, v, o) {
    if (!layouts.has(P)) {
      const cuts = [0, ...((o.cuts && o.cuts[P.day]) || []).filter((t) => t > 0)].sort((a, b) => a - b);
      const alive = Object.keys(M.people).filter((n) => P.plan[n] && P.plan[n].alive);
      const MERGE = o.merge || 5;  // 組どうしがこのマス数より近ければ、1 枚にまとめる
      let firstSplit = -1;
      const L = cuts.map((t0, i) => {
        const t1 = i + 1 < cuts.length ? cuts[i + 1] : P.total, tm = (t0 + t1) / 2;
        const sg = P.segs.find((s) => tm >= s.v0 && tm < s.v1) || P.segs[P.segs.length - 1];
        if (!["go", "work", "back"].includes(sg.key)) return { t0, groups: [{ names: alive, title: "" }] };
        let G = dayGroups(P, alive).map((g) => ({ ...g, ps: g.names.map((n) => posAt(P, n, tm)).filter(Boolean) }));
        const cen = (g) => ({ x: g.ps.reduce((a, p) => a + p.x, 0) / g.ps.length, y: g.ps.reduce((a, p) => a + p.y, 0) / g.ps.length });
        for (;;) {
          let best = null;
          for (let a = 0; a < G.length; a++) for (let b = a + 1; b < G.length; b++) {
            const A = cen(G[a]), B = cen(G[b]), d = Math.hypot(A.x - B.x, A.y - B.y);
            if (d < MERGE && (!best || d < best[0])) best = [d, a, b];
          }
          if (!best) break;
          const [, a, b] = best, A = G[a], B = G[b];
          G[a] = { names: [...A.names, ...B.names], ps: [...A.ps, ...B.ps], merged: true }; G.splice(b, 1);
        }
        G = G.map((g) => (g.merged ? { names: g.names, title: `${g.names.length >= 5 ? "五人" : g.names.join("・")} — ${sg.key === "go" ? "出かけるところ" : sg.key === "back" ? "キャンプへ帰るところ" : nearPlace(cen(g))}` } : { names: g.names, title: g.title }));
        if (G.length > 1 && firstSplit < 0) firstSplit = i;
        return { t0, groups: G };
      });
      layouts.set(P, { cuts, L, firstSplit, alive });
    }
    const X = layouts.get(P);
    let i = 0; while (i + 1 < X.cuts.length && X.cuts[i + 1] <= v) i++;
    const c = X.L[i];
    if (i === X.firstSplit && v < c.t0 + 1.5) return { key: "wide" + i, wide: true, groups: [{ names: X.alive, title: "" }], all: c.groups };  // 分ける前の、全体の引きの絵
    return { key: i + "|" + c.groups.map((g) => g.names.join("・")).join("/"), groups: c.groups };
  }
  function nearPlace(p) {
    if (Math.hypot(M.D.camp.x + 0.5 - p.x, M.D.camp.y + 0.5 - p.y) < 4) return "キャンプのまわり";
    let best = null;
    for (const q of M.D.places || []) { const d = Math.hypot(q.x + 0.5 - p.x, q.y + 0.5 - p.y); if (!best || d < best[0]) best = [d, q]; }
    const name = best ? String(best[1].label || best[1].id).replace(/\s*\(.*\)\s*$/, "") : "";
    if (best && best[1].id === "camp") return "キャンプのまわり";
    return best && best[0] > 3 ? name + "の近く" : name;
  }
  // 小さな地図: 川・林・草地・キャンプ、組の点、各画面の見えている範囲 (地面との交わり) の枠
  let mapBase = null;
  function drawMap(cv, ps, P, v) {
    const D = M.D, MW = D.map.w, MH = D.map.h;
    if (!mapBase) {
      mapBase = document.createElement("canvas"); mapBase.width = MW; mapBase.height = MH;
      const g = mapBase.getContext("2d"), C = { g: "#a9c97a", f: "#4f7a3a", r: "#4a9ad8", h: "#c9b48a" };
      for (let y = 0; y < MH; y++) for (let x = 0; x < MW; x++) { g.fillStyle = C[D.map.terrain[y][x]] || "#a9c97a"; g.fillRect(x, y, 1, 1); }
    }
    const toT = (p) => ({ x: p.x + MW / 2, y: p.z + MH / 2 });
    const quads = ps.map((pn) => {
      const gy = pn.t.y - 0.8 * M.K;
      return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) => {
        const d = new THREE.Vector3(x, y, 0.5).unproject(pn.cam).sub(pn.cam.position).normalize();
        const k = d.y < -0.05 ? (gy - pn.cam.position.y) / d.y : 30;
        return toT(pn.cam.position.clone().add(d.multiplyScalar(Math.min(k, 30))));
      });
    });
    const camp = { x: D.camp.x + 0.5, y: D.camp.y + 0.5 }, dots = [];
    ps.forEach((pn) => pn.names.forEach((n) => { const p = posAt(P, n, v); if (p) dots.push({ p, col: pn.col || "#fff" }); }));
    const all = [camp, ...dots.map((d) => d.p), ...quads.flat()];
    let x0 = Math.min(...all.map((p) => p.x)) - 3, x1 = Math.max(...all.map((p) => p.x)) + 3, y0 = Math.min(...all.map((p) => p.y)) - 3, y1 = Math.max(...all.map((p) => p.y)) + 3;
    const asp = cv.width / cv.height; let w = Math.max(16, x1 - x0), h = Math.max(12, y1 - y0);
    if (w / h < asp) w = h * asp; else h = w / asp;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2; x0 = cx - w / 2; y0 = cy - h / 2;
    const g = cv.getContext("2d"), sx = cv.width / w, sy = cv.height / h, X = (p) => (p.x - x0) * sx, Y = (p) => (p.y - y0) * sy;
    g.imageSmoothingEnabled = false; g.clearRect(0, 0, cv.width, cv.height);
    g.drawImage(mapBase, x0, y0, w, h, 0, 0, cv.width, cv.height);
    g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(0, 0, cv.width, cv.height);
    quads.forEach((q, i) => { g.strokeStyle = ps[i].col || "#fff"; g.lineWidth = 2.5; g.beginPath(); q.forEach((p, k) => (k ? g.lineTo(X(p), Y(p)) : g.moveTo(X(p), Y(p)))); g.closePath(); g.stroke(); });
    g.fillStyle = "#7a5230"; g.beginPath(); g.arc(X(camp), Y(camp), 5, 0, 7); g.fill();
    g.fillStyle = "#fff"; g.font = "bold 12px sans-serif"; g.fillText("キャンプ", X(camp) + 7, Y(camp) + 4);
    for (const d of dots) { g.fillStyle = d.col; g.strokeStyle = "#222"; g.lineWidth = 1.5; g.beginPath(); g.arc(X(d.p), Y(d.p), 4.5, 0, 7); g.fill(); g.stroke(); }
    g.strokeStyle = "rgba(0,0,0,.5)"; g.lineWidth = 2; g.strokeRect(1, 1, cv.width - 2, cv.height - 2);
  }

  window.Replay3DPeople = {
    camera: { min: 6, add: 4.5 },
    // 動画 D1V (2026-11-23 本人の絵コンテの直し) のしかけ。make_video.mjs の PEOPLE_VIEW で入れる。ないときは D1P と同じ
    //   noPlants: 木の実・芋の玉 (赤い玉) を見せない。split: 昼 (出発・活動・帰り) は、場所と活動ごとの組 (3 つまで) に画面を分け、組ごとのカメラで追う。
    //   夜明け・夕方・夜は 1 枚で、火のまわりの五人が全部入るように引いて、上から見る。fire・day: カメラの近さ
    opts: {},  // 人が近くに集まっているときは、カメラを寄せる (Replay3D の autoCamera が読む)
    // 読む: base は glb と json のある場所 (例 "people/")。読めた人の名前を返す
    async load(base) {
      const got = {};
      // opts.files (2026-11-25、G1F2V から): 五人のほかの人 {名前: ファイル名}。ないときは五人だけ (前と同じ)
      for (const [n, f] of Object.entries({ ...FILES, ...(this.opts.files || {}) })) {
        const [g, info] = await Promise.all([loadGlb(base + f + ".glb"), fetch(base + f + ".json").then((r) => r.json())]);
        const seen = new Set();  // 2026-11-25: いくつかの部品で同じ材質を使うとき (服)、色の変換を 1 回だけにする (前は部品の数だけかかって白くなった)
        g.scene.traverse((o) => {
          if (!o.isMesh) return;
          o.frustumCulled = false;
          const ms = Array.isArray(o.material) ? o.material : [o.material];
          for (const m of ms) {
            if (seen.has(m)) continue;
            seen.add(m);
            // アプリの絵は色をそのまま出す (出力の色の変換をしない) ので、画像も色もそれに合わせる
            if (m.map) m.map.encoding = THREE.LinearEncoding; else m.color.convertLinearToSRGB();
            if (m.transparent) { m.transparent = false; m.alphaTest = 0.5; }  // 髪・まつげ・目: 半透明の重なりの順で欠けないように
            m.needsUpdate = true;
          }
        });
        const mixer = new THREE.AnimationMixer(g.scene), acts = {};
        for (const c of g.animations) { const a = mixer.clipAction(c); a.setLoop(THREE.LoopOnce); a.enabled = false; a.play(); acts[c.name] = a; }
        got[n] = { g, mixer, acts, info: info.clips };
      }
      this.loaded = got;
      return Object.keys(got);
    },
    init(ctx) {  // Replay3D.setPeople から呼ばれる
      M = { ...ctx, people: {}, opts2: this.opts, plants: new Map(), plantG: null, plantP: null, lighter: new Map(), fireAt: new Map(), bundles: {}, props: new Map(),
        kin: Object.fromEntries((ctx.D.people || []).map((q) => [q.name, { born: q.born_day, mother: q.mother }])) };
      if (this.opts.noPlants) { const pm = ctx.scene.getObjectByName("plants"); if (pm) pm.visible = false; }
      for (const n in this.loaded || {}) {
        if (!ctx.figs[n]) continue;
        const L = this.loaded[n], root = new THREE.Group();
        root.add(L.g.scene); root.scale.setScalar(ctx.K); ctx.scene.add(root);
        ctx.figs[n].userData.pelvis.visible = false;  // 棒の人は見せない (名前の札とカメラのために、場所だけ使う)
        M.people[n] = { ...L, root, head: L.g.scene.getObjectByName("J_Bip_C_Head") };
      }
    },
    // 画面を分けて描く (opts.split のとき。Replay3D.seek から。描いたら true)。
    // 何枚に分けるかは、カット (ナレーションの 1 文。opts.cuts[日]) ごとに、カットのまん中の時刻の組どうしの近さで決める (カットの途中では変えない)。
    // 初めて分けるカットの頭 1.5 秒は、全体を見せる引きの絵。分けたときは、右上に小さな地図 (組の点と、各画面の見えている範囲の枠) と、画面の色の縁
    render(v) {
      if (!this.opts.split || !M || !M.P) return false;
      const P = M.P, R = M.renderer, el = R.domElement, W = el.clientWidth, H = el.clientHeight, o = this.opts;
      const seg = P.segs.find((s) => v >= s.v0 && v < s.v1) || P.segs[P.segs.length - 1];
      const day = ["go", "work", "back"].includes(seg.key);
      const lay = layoutAt(P, v, o);
      const key = lay.key;
      if (!M.view || M.view.key !== key) M.view = { key, panels: lay.groups.map((g, i) => ({ ...g, col: lay.groups.length > 1 || lay.wide ? COLS[i % COLS.length] : null, cam: new THREE.PerspectiveCamera(45, 1, 0.1, 500), fresh: true })) };
      const ps = M.view.panels, n = ps.length;
      ps.forEach((pn, i) => {
        pn.x = Math.round((W * i) / n); pn.w = Math.round((W * (i + 1)) / n) - pn.x; pn.y = 0; pn.h = H;
        pn.cam.aspect = pn.w / pn.h; pn.cam.updateProjectionMatrix();
        const pts = pn.names.filter((m) => M.people[m]).map((m) => M.people[m].root.position);
        const c = pts.reduce((a, p) => a.add(p), new THREE.Vector3()).multiplyScalar(1 / Math.max(1, pts.length));
        const r = Math.max(0, ...pts.map((p) => p.distanceTo(c)));
        const C = lay.wide ? { min: 8, add: 4, k: 2.4 } : day ? (o.day || { min: 4.2, add: 2.2, k: 2.2 }) : (o.fire || { min: 5.6, add: 2.6, k: 2.0 });
        const narrow = Math.min(1, pn.cam.aspect / (16 / 9));  // 細い画面は、そのぶん引く
        // o.fireMax (2026-11-25、G1F2V から): 夜明け・夕方・夜のカメラをこれより引かない (家が 2 つになり、離れた家の人に合わせて引きすぎたため)。ないときは前と同じ
        const far = !day && !lay.wide && o.fireMax ? o.fireMax : 80;
        const dist = Math.min(far, Math.max(C.min, r * C.k + C.add) / Math.max(0.55, narrow));
        const dir = (day || lay.wide ? new THREE.Vector3(0.5, lay.wide ? 0.9 : 0.62, 0.78) : new THREE.Vector3(0.4, 0.78, 0.72)).normalize();
        const want = c.clone().add(new THREE.Vector3(0, 0.8 * M.K, 0));
        if (!day && !lay.wide) want.add(new THREE.Vector3(dir.x, 0, dir.z).multiplyScalar(r * (seg.key === "night" ? 0.8 : 0.3)));  // 火のまわり: 輪が字幕より上に来るよう、見る点を手前に
        const at = want.clone().add(dir.multiplyScalar(dist));
        if (pn.fresh) { pn.t = want; pn.cam.position.copy(at); pn.fresh = false; } else { pn.t.lerp(want, 0.12); pn.cam.position.lerp(at, 0.12); }
        pn.cam.lookAt(pn.t);
      });
      R.setScissorTest(true);
      for (const pn of ps) { R.setViewport(pn.x, H - pn.y - pn.h, pn.w, pn.h); R.setScissor(pn.x, H - pn.y - pn.h, pn.w, pn.h); R.render(M.scene, pn.cam); }
      R.setScissorTest(false); R.setViewport(0, 0, W, H);
      M.placeLabels();  // 吹き出しの字などはアプリのまま。場所だけ組の画面に合わせて置き直す
      for (const m in M.labels) {
        const L = M.labels[m]; if (L.el.hidden || !L.pos) continue;
        const pn = ps.find((q) => q.names.includes(m)); if (!pn) { L.el.hidden = true; continue; }
        const q = L.pos.clone().project(pn.cam), x = pn.x + (q.x * 0.5 + 0.5) * pn.w, y = pn.y + (-q.y * 0.5 + 0.5) * pn.h;
        if (q.z > 1 || x < pn.x || x > pn.x + pn.w) { L.el.hidden = true; continue; }
        const b = L.el.querySelector(".b");
        if (b && o.bubbleFont) { b.style.fontSize = o.bubbleFont + "px"; b.style.maxWidth = "13em"; }
        const bw = L.el.offsetWidth || 0, xc = bw && bw < pn.w - 8 ? Math.min(pn.x + pn.w - bw / 2 - 4, Math.max(pn.x + bw / 2 + 4, x)) : x;  // 吹き出しは組の画面の中に
        // v2 (2026-11-25 本人「吹き出しが見切れている」): 吹き出しの上が画面の上からはみ出すときは、はみ出さない所まで下げる
        const bh = o.v2 ? L.el.offsetHeight || 0 : 0, yc = bh && y - bh < pn.y + 8 ? pn.y + 8 + bh : y;
        L.el.style.transform = `translate(${xc}px, ${yc}px) translate(-50%, -100%)`;
        if (b) b.style.opacity = M.fade && M.fade[m] != null ? String(Math.max(0, M.fade[m])) : "";
      }
      // 組の名前・色の縁 (DOM)
      const st = el.parentElement;
      if (!M.deco) { M.deco = document.createElement("div"); M.deco.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:40"; st.appendChild(M.deco); }
      if (M.deco.dataset.key !== key + W) {
        M.deco.dataset.key = key + W;
        M.deco.innerHTML = ps.map((pn) => (pn.col && n > 1 ? `<div style="position:absolute;left:${pn.x}px;top:0;width:${pn.w}px;height:100%;box-sizing:border-box;border:4px solid ${pn.col}"></div>` : "")
          + (pn.title ? `<div style="position:absolute;left:${pn.x + 12}px;top:56px;background:rgba(12,16,13,.76);color:#fff;font-size:18px;padding:3px 12px;border-radius:8px;white-space:nowrap;${pn.col ? `border-left:8px solid ${pn.col}` : ""}">${pn.title}</div>` : "")).join("")
          + `<canvas class="pv-map" width="220" height="165" style="position:absolute !important;inset:auto !important;right:12px !important;top:12px !important;width:220px !important;height:165px !important;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.4)"></canvas>`;
      }
      const mapEl = M.deco.querySelector(".pv-map");
      mapEl.style.display = n > 1 || lay.wide ? "" : "none";
      if (n > 1 || lay.wide) drawMap(mapEl, ps, P, v);
      return true;
    },
    // 絵コンテ用: 人 m の世界の点を、その人の組の画面の上の点 (px) に。画面を分けていないときは null
    project(m, p) {
      if (!this.opts.split || !M || !M.view) return null;
      const pn = M.view.panels.find((q) => q.names.includes(m)); if (!pn) return null;
      const q = p.clone().project(pn.cam);
      return [pn.x + (q.x * 0.5 + 0.5) * pn.w, pn.y + (-q.y * 0.5 + 0.5) * pn.h, q.z, pn.x, pn.x + pn.w];
    },
    panels() { return this.opts.split && M && M.view ? M.view.panels.map((p) => ({ names: p.names, title: p.title, color: p.col, x: p.x, w: p.w, dist: +p.cam.position.distanceTo(p.t).toFixed(1) })) : null; },
    clips() { return M ? Object.fromEntries(Object.entries(M.people).filter(([, R]) => R.root.visible).map(([n, R]) => [n, R.clip])) : {}; },  // 絵コンテ用: 今の動きの名前
    frame(P, v) {  // コマごと (Replay3D の frame の終わり。名前の札とカメラの前)
      if (!M) return;
      M.P = P;
      if (this.opts.nightLight && M.world) {  // 夜を少し明るく (月の光のような青白い光と、まわりの明るさ)
        const Wd = M.world, dark = Math.max(0, 0.9 - Wd.sun.intensity) / 0.78;
        if (!M.moon) { M.moon = new THREE.DirectionalLight(0xaec4ff, 0); M.moon.position.set(-20, 40, 10); M.scene.add(M.moon); }
        M.moon.intensity = 0.3 * dark; Wd.amb.intensity += 0.08 * dark;
      }
      if (this.opts.bubbles) {  // 出来事の短い吹き出し (アプリの吹き出しを置きかえる)
        M.fade = {};
        for (const n in M.labels) M.labels[n].bubble = "";
        for (const b of bubblesFor(P)) if (v >= b.t0 && v < b.t1 && M.labels[b.who]) {
          M.labels[b.who].bubble = b.text; M.fade[b.who] = Math.min(1, (v - b.t0) / 0.25, (b.t1 - v) / FADEB);
        }
      }
      if (!sched.has(P)) sched.set(P, Object.fromEntries(Object.keys(M.people).filter((n) => P.plan[n]).map((n) => [n, planFor(P, M.D, n)])));
      const all = sched.get(P);
      if (this.opts.v2 && M.world && M.world.hut) hutGrowth(P, v);
      if (this.opts.v2) {
        animalsFrame(P, v); growFrame(P); if (this.opts.fireNightly) fireFrame(P, v);
        if (M.tentP !== P) { if (M.tentG) M.scene.remove(M.tentG); M.tentP = P; M.tentG = tentGroup(P); M.scene.add(M.tentG); }
      }
      if (M.plantP !== P) {  // v2: その日の採集の植物を置きかえる
        if (M.plantG) M.scene.remove(M.plantG);
        M.plantG = null; M.plantP = P;
        const list = M.plants.get(P);
        if (list && list.length) { M.plantG = plantGroup(list); M.scene.add(M.plantG); }
        const pr = M.props.get(P);  // 道具づくりの石と、できた鎌
        if (pr && pr.length) {
          if (!M.plantG) { M.plantG = new THREE.Group(); M.scene.add(M.plantG); }
          const st = new THREE.MeshLambertMaterial({ color: 0x8a8378 }), wd = new THREE.MeshLambertMaterial({ color: 0x6b4a2e }), K = M.K;
          for (const q of pr) {
            const o = new THREE.Group(); o.position.copy(M.w2t(q.at.x, q.at.y));
            for (let k = 0; k < 5; k++) { const r = new THREE.Mesh(new THREE.DodecahedronGeometry((0.05 + 0.03 * rnd(k, 2)) * K), st); r.position.set((rnd(k, 5) - 0.5) * 0.3 * K, 0.04 * K, (rnd(k, 7) - 0.5) * 0.3 * K); o.add(r); }
            const h = new THREE.Mesh(new THREE.CylinderGeometry(0.015 * K, 0.015 * K, 0.35 * K, 5), wd); h.rotation.z = Math.PI / 2; h.position.set(0.12 * K, 0.03 * K, 0.1 * K); o.add(h);  // 鎌の柄
            M.plantG.add(o);
          }
        }
      }
      for (const n in M.people) {
        const R = M.people[n], E = all[n], fig = M.figs[n];
        R.root.visible = !!(E && P.plan[n].alive) && !isBaby(P, n);
        if (!R.root.visible) continue;
        let j = 0; while (j + 1 < E.length && E[j + 1].t0 <= v) j++;
        if (E[j].hide) { R.root.visible = false; if (M.labels[n]) M.labels[n].pos = M.w2t(E[j].at(v).x, E[j].at(v).y).add(new THREE.Vector3(0, 1.9 * M.K, 0)); continue; }  // 住まいの中
        R.clip = E[j].clip;  // 絵コンテ (clips) 用
        const cur = E[j], prev = j > 0 ? E[j - 1] : null, w = prev ? clamp((v - cur.t0) / FADE) : 1;
        for (const k in R.acts) R.acts[k].enabled = false;
        const use = (e, wt) => {
          const a = R.acts[e.clip]; if (!a || wt <= 0) return;
          a.enabled = true; a.setEffectiveWeight(wt); a.time = localTime(e, v, a.getClip().duration);
        };
        if (prev && w < 1 && prev.clip !== cur.clip) use(prev, 1 - w);
        use(cur, prev && prev.clip !== cur.clip ? w : 1);
        R.mixer.update(0);
        const at = prev && w < 1 ? lerp(prev.at(v), cur.at(v), w) : cur.at(v);
        const hd = prev && w < 1 ? prev.head(v) + wrapA(cur.head(v) - prev.head(v)) * w : cur.head(v);
        R.root.position.copy(M.w2t(at.x, at.y)); R.root.rotation.y = hd + Math.PI / 2;  // モデルは +z を向いているので、棒の人の向き (+x) にそろえる
        if (this.opts.v2 && R.head && M.kin[n] && M.kin[n].born != null) {  // v2: 子は頭を大きめに (体に対する頭の大きさを子どもらしく。15 歳で大人と同じ)
          const age = (P.day - M.kin[n].born) / 120;
          R.head.scale.setScalar(age < 15 ? 1 + 0.35 * (1 - Math.max(2, age) / 15) : 1);
        }
        R.root.updateMatrixWorld(true);
        fig.position.copy(R.root.position); fig.rotation.y = hd;
        if (R.head && M.labels[n]) M.labels[n].pos = R.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.32 * M.K, 0));
      }
      if (this.opts.v2) { separate(); babiesFrame(P); }
    },
  };
})();
