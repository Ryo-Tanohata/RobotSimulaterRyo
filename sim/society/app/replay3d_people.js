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

  window.Replay3DPeople = {
    camera: { min: 6, add: 4.5 },
    // 動画 D1V (2026-11-23 本人の絵コンテの直し) のしかけ。make_video.mjs の PEOPLE_VIEW で入れる。ないときは D1P と同じ
    //   noPlants: 木の実・芋の玉 (赤い玉) を見せない。split: 昼 (出発・活動・帰り) は、場所と活動ごとの組 (3 つまで) に画面を分け、組ごとのカメラで追う。
    //   夜明け・夕方・夜は 1 枚で、火のまわりの五人が全部入るように引いて、上から見る。fire・day: カメラの近さ
    opts: {},  // 人が近くに集まっているときは、カメラを寄せる (Replay3D の autoCamera が読む)
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
      if (this.opts.noPlants) { const pm = ctx.scene.getObjectByName("plants"); if (pm) pm.visible = false; }
      for (const n in this.loaded || {}) {
        if (!ctx.figs[n]) continue;
        const L = this.loaded[n], root = new THREE.Group();
        root.add(L.g.scene); root.scale.setScalar(ctx.K); ctx.scene.add(root);
        ctx.figs[n].userData.pelvis.visible = false;  // 棒の人は見せない (名前の札とカメラのために、場所だけ使う)
        M.people[n] = { ...L, root, head: L.g.scene.getObjectByName("J_Bip_C_Head") };
      }
    },
    // 画面を分けて描く (opts.split のとき。Replay3D.seek から。描いたら true)
    render(v) {
      if (!this.opts.split || !M || !M.P) return false;
      const P = M.P, R = M.renderer, el = R.domElement, W = el.clientWidth, H = el.clientHeight;
      const seg = P.segs.find((s) => v >= s.v0 && v < s.v1) || P.segs[P.segs.length - 1];
      const day = ["go", "work", "back"].includes(seg.key);
      const alive = Object.keys(M.people).filter((n) => M.people[n].root.visible);
      const groups = day ? dayGroups(P, alive) : [{ names: alive, title: "" }];
      const key = seg.key + "|" + groups.map((g) => g.names.join("・")).join("/");
      if (!M.view || M.view.key !== key) M.view = { key, panels: groups.map((g, i) => ({ ...g, cam: new THREE.PerspectiveCamera(45, 1, 0.1, 500), fresh: true })) };
      const ps = M.view.panels, n = ps.length, o = this.opts;
      ps.forEach((pn, i) => {
        pn.x = Math.round((W * i) / n); pn.w = Math.round((W * (i + 1)) / n) - pn.x; pn.y = 0; pn.h = H;
        pn.cam.aspect = pn.w / pn.h; pn.cam.updateProjectionMatrix();
        const pts = pn.names.map((m) => M.people[m].root.position);
        const c = pts.reduce((a, p) => a.add(p), new THREE.Vector3()).multiplyScalar(1 / Math.max(1, pts.length));
        const r = Math.max(0, ...pts.map((p) => p.distanceTo(c)));
        const C = day ? (o.day || { min: 4.2, add: 2.2, k: 2.2 }) : (o.fire || { min: 7, add: 3.5, k: 2.4 });
        const narrow = Math.min(1, pn.cam.aspect / (16 / 9));  // 細い画面は、そのぶん引く
        const dist = Math.min(60, Math.max(C.min, r * C.k + C.add) / Math.max(0.55, narrow));
        const dir = (day ? new THREE.Vector3(0.5, 0.62, 0.78) : new THREE.Vector3(0.35, 1.0, 0.6)).normalize();
        const want = c.clone().add(new THREE.Vector3(0, 0.8 * M.K, 0));
        if (!day) want.add(new THREE.Vector3(dir.x, 0, dir.z).multiplyScalar(r * (seg.key === "night" ? 0.9 : 0.35)));  // 火のまわり: 輪が字幕より上に来るよう、見る点を手前に
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
        const bw = L.el.offsetWidth || 0, xc = bw && bw < pn.w - 8 ? Math.min(pn.x + pn.w - bw / 2 - 4, Math.max(pn.x + bw / 2 + 4, x)) : x;  // 吹き出しは組の画面の中に
        L.el.style.transform = `translate(${xc}px, ${y}px) translate(-50%, -100%)`;
        const b = L.el.querySelector(".b"); if (b) b.style.opacity = M.fade && M.fade[m] != null ? String(Math.max(0, M.fade[m])) : "";
      }
      // 組の名前と境目の線 (DOM)
      const st = el.parentElement;
      if (!M.deco) { M.deco = document.createElement("div"); M.deco.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:40"; st.appendChild(M.deco); }
      if (M.deco.dataset.key !== key + W) {
        M.deco.dataset.key = key + W;
        M.deco.innerHTML = ps.map((pn, i) => (i ? `<div style="position:absolute;left:${pn.x - 2}px;top:0;width:4px;height:100%;background:#f4f1e8"></div>` : "")
          + (pn.title ? `<div style="position:absolute;left:${pn.x + pn.w / 2}px;top:${n > 1 ? 56 : 12}px;transform:translateX(-50%);background:rgba(12,16,13,.72);color:#fff;font-size:18px;padding:3px 12px;border-radius:8px;white-space:nowrap">${pn.title}</div>` : "")).join("");
      }
      return true;
    },
    // 絵コンテ用: 人 m の世界の点を、その人の組の画面の上の点 (px) に。画面を分けていないときは null
    project(m, p) {
      if (!this.opts.split || !M || !M.view) return null;
      const pn = M.view.panels.find((q) => q.names.includes(m)); if (!pn) return null;
      const q = p.clone().project(pn.cam);
      return [pn.x + (q.x * 0.5 + 0.5) * pn.w, pn.y + (-q.y * 0.5 + 0.5) * pn.h, q.z, pn.x, pn.x + pn.w];
    },
    panels() { return this.opts.split && M && M.view ? M.view.panels.map((p) => ({ names: p.names, title: p.title, x: p.x, w: p.w, dist: +p.cam.position.distanceTo(p.t).toFixed(1) })) : null; },
    clips() { return M ? Object.fromEntries(Object.entries(M.people).filter(([, R]) => R.root.visible).map(([n, R]) => [n, R.clip])) : {}; },  // 絵コンテ用: 今の動きの名前
    frame(P, v) {  // コマごと (Replay3D の frame の終わり。名前の札とカメラの前)
      if (!M) return;
      M.P = P;
      if (this.opts.bubbles) {  // 出来事の短い吹き出し (アプリの吹き出しを置きかえる)
        M.fade = {};
        for (const n in M.labels) M.labels[n].bubble = "";
        for (const b of bubblesFor(P)) if (v >= b.t0 && v < b.t1 && M.labels[b.who]) {
          M.labels[b.who].bubble = b.text; M.fade[b.who] = Math.min(1, (v - b.t0) / 0.25, (b.t1 - v) / FADEB);
        }
      }
      if (!sched.has(P)) sched.set(P, Object.fromEntries(Object.keys(M.people).filter((n) => P.plan[n]).map((n) => [n, planFor(P, M.D, n)])));
      const all = sched.get(P);
      for (const n in M.people) {
        const R = M.people[n], E = all[n], fig = M.figs[n];
        R.root.visible = !!(E && P.plan[n].alive);
        if (!R.root.visible) continue;
        let j = 0; while (j + 1 < E.length && E[j + 1].t0 <= v) j++;
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
        R.root.updateMatrixWorld(true);
        fig.position.copy(R.root.position); fig.rotation.y = hd;
        if (R.head && M.labels[n]) M.labels[n].pos = R.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.32 * M.K, 0));
      }
    },
  };
})();
