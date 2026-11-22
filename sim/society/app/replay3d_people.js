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
    const ring = lerp(fire, p.ring, RING), ringOf = (m) => (P.plan[m] ? lerp(fire, P.plan[m].ring, RING) : fire);  // 火のまわりの輪は、人の体の大きさに合わせて広げる
    let here = ring;
    const walkTo = (to, t0) => {
      const from = here, d = Math.hypot(to.x - from.x, to.y - from.y), dur = d / SPD, h = face(from, to);
      if (d < 0.05) return t0;
      add({ t0, clip: "walk", mode: "loop", rate: WALK / info.walk.speed, at: (v) => lerp(from, to, clamp((v - t0) / dur)), head: () => h });
      here = to; return t0 + dur;
    };
    // 夜明け: 火のまわりで見回す
    add({ t0: -1, clip: "idle", mode: "pp", rate: 0.8, off: p.i * 1.3, ...still(ring, face(ring, fire)) });
    // 出発: 人の速さで歩いて、着いたら仕事を始める
    let t = walkTo(p.spot, seg.go.v0 + 0.6 + 0.5 * p.i);
    const tLeave = Math.max(t + 2, seg.back.v1 - 0.6 - (p.dist + 2) / SPD);
    const out = face(ring, p.spot);
    if (p.activity === "採集") {
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
          const to = { x: p.spot.x + Math.cos(a) * r, y: p.spot.y + Math.sin(a) * r };
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
    } else {
      add({ t0: t, clip: "idle", mode: "pp", ...still(here, face(here, fire)) });
    }
    // 帰り: 帰りの終わりに火のまわりに着くように出る
    t = walkTo(ring, Math.max(t, tLeave));
    const atFire = face(ring, fire);
    add({ t0: t, clip: "idle", mode: "pp", ...still(ring, atFire) });
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
    const bed = lerp(fire, ring, 1.8);
    t = walkTo(bed, seg.night.v0 + 0.5 + 0.6 * p.i);
    add({ t0: t + 0.3, clip: "lie", mode: "rev", rate: 0.9, ...still(bed, face(fire, bed)) });
    return E;
  }

  function localTime(e, v, dur) {
    const lt = Math.max(0, (v - e.t0) * e.rate + e.off);
    if (e.mode === "loop") return lt % dur;
    if (e.mode === "pp") { const m = lt % (2 * dur); return m < dur ? m : 2 * dur - m; }
    if (e.mode === "once") return Math.min(lt, dur);
    return Math.max(0, dur - lt);  // rev
  }

  window.Replay3DPeople = {
    camera: { min: 6, add: 4.5 },  // 人が近くに集まっているときは、カメラを寄せる (Replay3D の autoCamera が読む)
    // 読む: base は glb と json のある場所 (例 "people/")。読めた人の名前を返す
    async load(base) {
      const got = {};
      for (const [n, f] of Object.entries(FILES)) {
        const [g, info] = await Promise.all([loadGlb(base + f + ".glb"), fetch(base + f + ".json").then((r) => r.json())]);
        g.scene.traverse((o) => {
          if (!o.isMesh) return;
          o.frustumCulled = false;
          const ms = Array.isArray(o.material) ? o.material : [o.material];
          for (const m of ms) {
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
      M = { ...ctx, people: {} };
      for (const n in this.loaded || {}) {
        if (!ctx.figs[n]) continue;
        const L = this.loaded[n], root = new THREE.Group();
        root.add(L.g.scene); root.scale.setScalar(ctx.K); ctx.scene.add(root);
        ctx.figs[n].userData.pelvis.visible = false;  // 棒の人は見せない (名前の札とカメラのために、場所だけ使う)
        M.people[n] = { ...L, root, head: L.g.scene.getObjectByName("J_Bip_C_Head") };
      }
    },
    frame(P, v) {  // コマごと (Replay3D の frame の終わり。名前の札とカメラの前)
      if (!M) return;
      if (!sched.has(P)) sched.set(P, Object.fromEntries(Object.keys(M.people).filter((n) => P.plan[n]).map((n) => [n, planFor(P, M.D, n)])));
      const all = sched.get(P);
      for (const n in M.people) {
        const R = M.people[n], E = all[n], fig = M.figs[n];
        R.root.visible = !!(E && P.plan[n].alive);
        if (!R.root.visible) continue;
        let j = 0; while (j + 1 < E.length && E[j + 1].t0 <= v) j++;
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
        R.root.updateMatrixWorld(true);
        fig.position.copy(R.root.position); fig.rotation.y = hd;
        if (R.head && M.labels[n]) M.labels[n].pos = R.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.32 * M.K, 0));
      }
    },
  };
})();
