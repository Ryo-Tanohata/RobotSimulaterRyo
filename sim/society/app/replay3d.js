/* 川辺の五人: 1 日を 3D で再生する (three.js r128)。
 * 動きは「その日の記録から作った再現」: 朝の出発 → 活動 → 帰り → 夕方の焚き火 → 夜 の順に見せる。
 * 棒人間の歩き方は、2 足歩行の物理シミュレーションで学習した関節角 (walk_cycle.json) をそのまま使う。
 * 座標: 1 マス (25 m) = 1。地図の x → three の x、地図の y → three の z。上は three の y。
 */
(function () {
  const K = 1.4;              // 棒人間の大きさ (1 m → 1.4 マス = 35 m。見やすいように大きくしている)
  const BODY = { thigh: 0.45, shank: 0.38, foot: 0.22, heel: 0.05, upper: 0.32, fore: 0.25, trunk: 0.5, hipW: 0.1, shW: 0.17 };
  const SEG = [                // 見せ方の区切り: 名前, 時刻 (始まり → 終わり), 再生の秒数 (等倍)
    { key: "dawn", label: "夜明け", t0: 5.5, t1: 6, sec: 3 },
    { key: "go", label: "出発", t0: 6, t1: 7, sec: 8 },
    { key: "work", label: "活動", t0: 7, t1: 18, sec: 14 },
    { key: "back", label: "帰り", t0: 18, t1: 19, sec: 8 },
    { key: "eve", label: "夕方の焚き火", t0: 19, t1: 21.5, sec: 12 },
    { key: "night", label: "夜", t0: 21.5, t1: 22.5, sec: 5 },
  ];
  const WORK_EVENTS = ["採集", "探索", "狩り", "道具", "火", "種まき", "けが"];
  const EVE_EVENTS = ["話す", "分ける"];
  const NIGHT_EVENTS = ["死", "けが", "夜", "掟", "腐る", "育つ"];

  let S = null; // 状態

  function hgt(D, x, y) {  // 地面の高さ
    const t = D.map.terrain, W = D.map.w, H = D.map.h;
    let sum = 0, n = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const xx = Math.min(W - 1, Math.max(0, Math.floor(x) + dx)), yy = Math.min(H - 1, Math.max(0, Math.floor(y) + dy));
      const c = t[yy][xx]; sum += c === "h" ? 1.6 : c === "r" ? -0.35 : c === "f" ? 0.25 : 0.1; n++;
    }
    return sum / n;
  }
  const w2t = (D, x, y, lift = 0) => new THREE.Vector3(x - D.map.w / 2, hgt(D, x, y) + lift, y - D.map.h / 2);

  function cyl(len, r, mat) {  // 上端を原点にして下へ伸びる棒
    const g = new THREE.CylinderGeometry(r, r, len, 8); g.translate(0, -len / 2, 0);
    return new THREE.Mesh(g, mat);
  }

  function makeFigure(color) {
    const mat = new THREE.MeshLambertMaterial({ color });
    const root = new THREE.Group(), pelvis = new THREE.Group(); root.add(pelvis);
    const J = {};
    for (const side of ["l", "r"]) {
      const s = side === "l" ? -1 : 1;  // three の z (横) の向き
      const hip = new THREE.Group(); hip.position.set(0, 0, s * BODY.hipW * K); pelvis.add(hip);
      hip.add(cyl(BODY.thigh * K * 0.92, 0.045 * K, mat));
      const knee = new THREE.Group(); knee.position.y = -BODY.thigh * K; hip.add(knee);
      knee.add(cyl(BODY.shank * K * 0.92, 0.045 * K, mat));
      const ankle = new THREE.Group(); ankle.position.y = -BODY.shank * K; knee.add(ankle);
      const foot = new THREE.Mesh(new THREE.BoxGeometry(BODY.foot * K, 0.05 * K, 0.07 * K), mat);
      foot.position.set((BODY.foot / 2 - BODY.heel) * K, -0.03 * K, 0); ankle.add(foot);
      J[side + "_hip_y"] = hip; J[side + "_knee"] = knee; J[side + "_ankle_y"] = ankle;
    }
    const chest = new THREE.Group(); chest.position.y = 0.05 * K; pelvis.add(chest); J.waist = chest;
    const spine = cyl(BODY.trunk * K * 0.9, 0.07 * K, mat); spine.rotation.z = Math.PI; spine.position.y = 0.02 * K; chest.add(spine);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.1 * K, 16, 12), mat); head.position.y = (BODY.trunk + 0.15) * K; chest.add(head);
    for (const side of ["l", "r"]) {
      const s = side === "l" ? -1 : 1;
      const sh = new THREE.Group(); sh.position.set(0, BODY.trunk * K, s * BODY.shW * K); chest.add(sh);
      sh.add(cyl(BODY.upper * K * 0.9, 0.045 * K, mat));
      const el = new THREE.Group(); el.position.y = -BODY.upper * K; sh.add(el);
      el.add(cyl(BODY.fore * K * 0.9, 0.045 * K, mat));
      J[side + "_shoulder_y"] = sh; J[side + "_elbow"] = el;
    }
    root.userData = { J, pelvis, head };
    return root;
  }

  const LEG = (BODY.thigh + BODY.shank + 0.05) * K;  // 立ったときの骨盤の高さ
  const POSES = {
    stand: { q: {}, h: LEG, pitch: 0 },
    work: { q: { l_hip_y: -1.1, r_hip_y: -1.2, l_knee: 1.5, r_knee: 1.6, l_ankle_y: -0.35, r_ankle_y: -0.35, waist: 0.35, l_shoulder_y: -0.9, r_shoulder_y: -0.7, l_elbow: -0.6, r_elbow: -0.5 }, h: LEG * 0.62, pitch: 0.25 },
    sit: { q: { l_hip_y: -1.45, r_hip_y: -1.45, l_knee: 1.1, r_knee: 1.2, l_ankle_y: -0.2, r_ankle_y: -0.2, waist: 0.1, l_shoulder_y: -0.4, r_shoulder_y: -0.4, l_elbow: -0.9, r_elbow: -0.9 }, h: 0.12 * K, pitch: 0 },
  };
  function applyPose(fig, q, h, pitch) {
    const { J, pelvis } = fig.userData;
    for (const k in J) J[k].rotation.z = -(q[k] || 0);  // MuJoCo の +(後ろ) → three の -z 回転
    pelvis.position.y = h; pelvis.rotation.z = -pitch;
  }
  function walkPose(fig, phase) {
    const W = S.walk, f = W.frames[Math.floor(phase * W.frames.length) % W.frames.length], q = {};
    W.names.forEach((n, i) => (q[n] = f.q[i]));
    applyPose(fig, q, LEG + f.bob * K, f.pitch);
  }

  function tokens(css) {
    const c = (v) => new THREE.Color(css(v) || "#888");
    return { grass: c("--grass"), forest: c("--forest"), river: c("--river"), hill: c("--hill"), fruit: c("--fruit"), tuber: c("--tuber"),
      accent: c("--accent"), danger: c("--danger"), bg: c("--bg"), fg: c("--fg"), people: [0, 1, 2, 3, 4].map((i) => c(`--p${i}`)) };
  }

  function buildWorld(D, T) {
    const scene = new THREE.Scene();
    const W = D.map.w, H = D.map.h;
    const geo = new THREE.PlaneGeometry(W, H, W, H); geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position, cols = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i) + W / 2, y = pos.getZ(i) + H / 2;
      pos.setY(i, hgt(D, x, y));
      const cx = Math.min(W - 1, Math.max(0, Math.floor(x))), cy = Math.min(H - 1, Math.max(0, Math.floor(y)));
      const col = { g: T.grass, f: T.forest, r: T.river, h: T.hill }[D.map.terrain[cy][cx]];
      cols.set([col.r, col.g, col.b], i * 3);
    }
    geo.setAttribute("color", new THREE.BufferAttribute(cols, 3)); geo.computeVertexNormals();
    scene.add(new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ vertexColors: true })));

    // 林の木 (マスごとに決まった乱数で置く)
    const trees = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (D.map.terrain[y][x] === "f" && ((x * 73856093) ^ (y * 19349663)) % 7 === 0) trees.push([x + 0.5, y + 0.5]);
    const cone = new THREE.ConeGeometry(0.55, 1.8, 7); cone.translate(0, 1.3, 0);
    const tm = new THREE.InstancedMesh(cone, new THREE.MeshLambertMaterial({ color: T.forest.clone().multiplyScalar(0.8) }), trees.length);
    const m4 = new THREE.Matrix4();
    trees.forEach(([x, y], i) => { const p = w2t(D, x, y); m4.makeTranslation(p.x, p.y, p.z); tm.setMatrixAt(i, m4); });
    scene.add(tm);

    // 木の実・芋
    const ps = D.plants.filter((p) => p.amount >= 0.5);
    const pm = new THREE.InstancedMesh(new THREE.SphereGeometry(0.18, 6, 5), new THREE.MeshLambertMaterial(), ps.length);
    ps.forEach((p, i) => { const v = w2t(D, p.x + 0.5, p.y + 0.5, 0.25); m4.makeTranslation(v.x, v.y, v.z); pm.setMatrixAt(i, m4); pm.setColorAt(i, p.kind === "木の実" ? T.fruit : T.tuber); });
    scene.add(pm);

    // ルクの群れ・ザガ
    for (const h of D.herds) {
      const g = new THREE.Group();
      for (let i = 0; i < Math.min(h.count, 12); i++) {
        const b = new THREE.Mesh(new THREE.SphereGeometry(0.28, 8, 6), new THREE.MeshLambertMaterial({ color: T.tuber }));
        b.scale.set(1.5, 0.8, 0.8); const a = i * 2.4, r = 0.6 + (i % 4) * 0.35;
        const p = w2t(D, h.x + 0.5 + Math.cos(a) * r, h.y + 0.5 + Math.sin(a) * r, 0.35); b.position.copy(p); b.rotation.y = a; g.add(b);
      }
      scene.add(g);
    }
    for (const pr of D.predators) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.5, 0.45), new THREE.MeshLambertMaterial({ color: T.danger }));
      b.position.copy(w2t(D, pr.x + 0.5, pr.y + 0.5, 0.35)); scene.add(b);
    }

    // キャンプ (石の輪と焚き火)
    const camp = w2t(D, D.camp.x + 0.5, D.camp.y + 0.5);
    for (let i = 0; i < 10; i++) {
      const s = new THREE.Mesh(new THREE.DodecahedronGeometry(0.16), new THREE.MeshLambertMaterial({ color: T.hill.clone().multiplyScalar(0.7) }));
      s.position.set(camp.x + Math.cos(i * 0.628) * 0.55, camp.y + 0.1, camp.z + Math.sin(i * 0.628) * 0.55); scene.add(s);
    }
    const flame = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.8, 8), new THREE.MeshBasicMaterial({ color: T.accent }));
    flame.position.set(camp.x, camp.y + 0.4, camp.z); scene.add(flame);
    const fireLight = new THREE.PointLight(T.accent, 0, 14); fireLight.position.set(camp.x, camp.y + 1, camp.z); scene.add(fireLight);

    const sun = new THREE.DirectionalLight(0xffffff, 0.9); sun.position.set(30, 50, 20); scene.add(sun);
    const amb = new THREE.AmbientLight(0xffffff, 0.55); scene.add(amb);
    return { scene, camp, flame, fireLight, sun, amb };
  }

  function placeOf(D, id) { return D.places.find((p) => p.id === id) || D.places[0]; }

  function planDay(D, day) {
    const rows = (D.days && D.days[day]) || [];
    const names = D.people.map((p) => p.name);
    const plan = {}, groups = {};
    names.forEach((n, i) => {
      const r = rows.find((x) => x.name === n);
      const alive = D.people[i].alive || D.events.some((e) => e.day > day && e.who === n);
      const pl = placeOf(D, r ? r.place : "camp");
      (groups[pl.id] = groups[pl.id] || []).push(n);
      plan[n] = { name: n, i, alive: !!r || alive, activity: r ? r.activity : "休む", place: pl };
    });
    let maxDist = 1;
    for (const n of names) {
      const p = plan[n], k = groups[p.place.id].indexOf(n), a = k * 2.1;
      p.spot = { x: p.place.x + 0.5 + Math.cos(a) * 1.2 * (k > 0), y: p.place.y + 0.5 + Math.sin(a) * 1.2 * (k > 0) };
      if (p.place.id === "camp") p.spot = { x: D.camp.x + 0.5 + Math.cos(p.i * 1.26) * 2.2, y: D.camp.y + 0.5 + Math.sin(p.i * 1.26) * 2.2 };
      p.ring = { x: D.camp.x + 0.5 + Math.cos(p.i * 1.2566) * 1.3, y: D.camp.y + 0.5 + Math.sin(p.i * 1.2566) * 1.3 };
      p.dist = Math.hypot(p.spot.x - p.ring.x, p.spot.y - p.ring.y);
      maxDist = Math.max(maxDist, p.dist);
    }
    const ev = D.events.filter((e) => e.day === day);
    const eve = ev.filter((e) => EVE_EVENTS.includes(e.type));
    const segs = SEG.map((s) => ({ ...s }));
    segs[4].sec = Math.max(10, eve.length * 2.6 + 2);
    const over = (S && S.segOverride && S.segOverride[day]) || {};  // 動画用: 場面ごとの秒数を指定できる
    for (const s of segs) if (over[s.key]) s.sec = over[s.key];
    let acc = 0; for (const s of segs) { s.v0 = acc; acc += s.sec; s.v1 = acc; }
    return { plan, maxDist, segs, total: acc, work: ev.filter((e) => WORK_EVENTS.includes(e.type)), eve,
      night: ev.filter((e) => NIGHT_EVENTS.includes(e.type)), fire: ev.some((e) => e.type === "火" && !/できなかった/.test(e.text)) || D.camp.fire > 0 };
  }

  function lerp(a, b, u) { return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u }; }

  function frame(v) {  // v = 再生の秒 (等倍)
    const P = S.day, D = S.D;
    const seg = P.segs.find((s) => v < s.v1) || P.segs[P.segs.length - 1];
    const u = Math.min(1, Math.max(0, (v - seg.v0) / seg.sec));
    const hour = seg.t0 + (seg.t1 - seg.t0) * u;
    S.clock.textContent = `${S.dayNum} 日目 ${Math.floor(hour)}:${String(Math.floor((hour % 1) * 60)).padStart(2, "0")}  ${seg.label}`;
    // 明るさ (夜は暗く、焚き火が灯る)
    const light = hour < 6 ? 0.35 + (hour - 5.5) * 1.2 : hour > 19 ? Math.max(0.12, 0.9 - (hour - 19) * 0.35) : 0.9;
    S.W.sun.intensity = light; S.W.amb.intensity = 0.25 + light * 0.35;
    const lit = P.fire && (hour >= 18.5 || hour < 6);
    S.W.flame.visible = lit; S.W.fireLight.intensity = lit ? 1.6 + Math.sin(v * 13) * 0.3 : 0;
    S.W.scene.background = S.T.bg.clone().lerp(new THREE.Color(0x0b1220), 1 - Math.min(1, light / 0.9));

    for (const n in P.plan) {
      const p = P.plan[n], fig = S.figs[n];
      fig.visible = p.alive;
      if (!p.alive) continue;
      let at = p.ring, heading = null, pose = "stand", moving = false;
      if (seg.key === "go" || seg.key === "back") {
        const need = p.dist / P.maxDist;
        let w = seg.key === "go" ? Math.min(1, u / need) : Math.max(0, (u - (1 - need)) / need);
        if (p.dist < 0.01) w = 1;
        at = seg.key === "go" ? lerp(p.ring, p.spot, w) : lerp(p.spot, p.ring, Math.min(1, w));
        moving = w > 0 && w < 1;
        const to = seg.key === "go" ? p.spot : p.ring, from = seg.key === "go" ? p.ring : p.spot;
        heading = Math.atan2(-(to.y - from.y), to.x - from.x);
        if (seg.key === "back" && w <= 0) at = p.spot;
      } else if (seg.key === "work") {
        at = { x: p.spot.x + Math.sin(v * 0.4 + p.i) * 0.5, y: p.spot.y + Math.cos(v * 0.3 + p.i) * 0.5 };
        pose = p.activity === "探索" ? "walk" : p.activity === "休む" ? "sit" : "work";
        moving = pose === "walk";
        heading = v * 0.4 + p.i;
      } else if (seg.key === "eve" || seg.key === "night") {
        pose = "sit";
      }
      if (heading === null) heading = Math.atan2(-(D.camp.y + 0.5 - at.y), D.camp.x + 0.5 - at.x);  // 焚き火を向く
      const pos = w2t(D, at.x, at.y);
      fig.position.copy(pos); fig.rotation.y = heading;
      if (moving) walkPose(fig, (v / 0.75 + p.i * 0.37) % 1);
      else { const Q = POSES[pose] || POSES.stand; applyPose(fig, Q.q, Q.h + (pose === "work" ? Math.sin(v * 5 + p.i) * 0.03 : 0), Q.pitch); }
      fig.updateMatrixWorld(true);  // 吹き出しと名前は、その時の頭の真上に付ける (座ると下がる)
      S.labels[n].pos = fig.userData.head.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.2 * K, 0));
    }

    // 出来事と会話
    let shown = [], bubbles = {};
    if (seg.key === "work") P.work.forEach((e, k) => { if (u >= (k + 0.5) / (P.work.length + 1)) shown.push(e); });
    if (seg.key === "back" || seg.key === "eve" || seg.key === "night") shown = P.work.slice(-3);
    if (seg.key === "eve") {
      const k = Math.floor(u * P.eve.length);
      P.eve.slice(0, k + 1).forEach((e) => { if (e.type === "分ける") shown.push(e); });
      const e = P.eve[Math.min(k, P.eve.length - 1)];
      if (e && e.type === "話す") bubbles[e.who] = e.text.replace(/^.*?「/, "「");
      if (e && e.type === "分ける") bubbles[e.who] = `（${e.data.to} に ${e.data.food || "食べ物"} を分ける）`;
    }
    if (seg.key === "night") shown = P.night.length ? P.night : [{ text: "静かな夜" }];
    S.toast.innerHTML = shown.slice(-4).map((e) => `<div>${esc(plain(e.text))}</div>`).join("");
    for (const n in S.labels) S.labels[n].bubble = bubbles[n] || "";
  }

  // 初期の記録 (1〜2 日目) にはカロリーの表記があるので、見せるときは言い換える
  const plain = (t) => String(t).replace(/で採集し ?[\d.]+ kcal 分を得た/, "で採集した").replace(/に食べ物を ?[\d.]+ kcal 分けた/, "に食べ物を分けた").replace(/ \([\d.]+ kcal の肉\)/, "");
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function placeLabels() {
    const r = S.renderer.domElement.getBoundingClientRect();
    for (const n in S.labels) {
      const L = S.labels[n], fig = S.figs[n];
      if (!fig.visible || !L.pos) { L.el.hidden = true; continue; }
      const p = L.pos.clone().project(S.camera);
      if (p.z > 1) { L.el.hidden = true; continue; }
      L.el.hidden = false;
      L.el.style.transform = `translate(${(p.x * 0.5 + 0.5) * r.width}px, ${(-p.y * 0.5 + 0.5) * r.height}px) translate(-50%, -100%)`;
      L.el.querySelector(".b").textContent = L.bubble; L.el.querySelector(".b").hidden = !L.bubble;
    }
  }

  function loop(now) {
    if (!S) return;
    const dt = Math.min(0.1, (now - (S.last || now)) / 1000); S.last = now;
    if (S.playing) {
      S.v += dt * S.speed;
      if (S.v >= S.day.total) { S.v = S.day.total; S.playing = false; S.playBtn.textContent = "もう一度"; }
      S.slider.value = String(S.v / S.day.total);
    }
    if (S.follow && S.figs[S.follow] && S.figs[S.follow].visible) {
      S.controls.target.lerp(S.figs[S.follow].position, 0.08);
    }
    frame(S.v); S.controls.update(); S.renderer.render(S.W.scene, S.camera); placeLabels();
    S.raf = requestAnimationFrame(loop);
  }

  // 動画用: 見えている全員が入るように、カメラの注視点と距離を少しずつ合わせる
  function autoCamera() {
    const ps = Object.values(S.figs).filter((f) => f.visible).map((f) => f.position);
    if (!ps.length) return;
    const c = ps.reduce((a, p) => a.add(p), new THREE.Vector3()).multiplyScalar(1 / ps.length);
    const r = Math.max(...ps.map((p) => p.distanceTo(c)));
    const dist = Math.min(90, Math.max(13, r * 2.3 + 9));
    const dir = new THREE.Vector3(0.5, 0.62, 0.78).normalize();
    S.controls.target.lerp(c, 0.07);
    S.camera.position.lerp(S.controls.target.clone().add(dir.multiplyScalar(dist)), 0.07);
  }

  function setDay(d) {
    S.dayNum = d; S.day = planDay(S.D, d); S.v = 0; S.playing = true; S.playBtn.textContent = "一時停止";
  }

  window.Replay3D = {
    start(root, D, walk, css) {
      this.stop();
      const T = tokens(css);
      root.innerHTML = `<div class="r3-bar">
          <button type="button" id="r3-play">一時停止</button>
          <input id="r3-slider" type="range" min="0" max="1" step="0.001" value="0" aria-label="時刻">
          <label>日 <select id="r3-day"></select></label>
          <label>速さ <select id="r3-speed"><option value="0.5">0.5 倍</option><option value="1" selected>1 倍</option><option value="2">2 倍</option><option value="4">4 倍</option></select></label>
          <label>カメラ <select id="r3-follow"><option value="">全体</option></select></label>
        </div>
        <div class="r3-stage"><div class="r3-clock"></div><div class="r3-toast"></div></div>`;
      const stage = root.querySelector(".r3-stage");
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      stage.prepend(renderer.domElement);
      const camera = new THREE.PerspectiveCamera(45, 16 / 10, 0.1, 500);
      const W = buildWorld(D, T);
      camera.position.set(W.camp.x + 9, W.camp.y + 10, W.camp.z + 14);
      const controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.target.copy(W.camp); controls.maxPolarAngle = Math.PI * 0.47; controls.minDistance = 4; controls.maxDistance = 120;
      const figs = {}, labels = {};
      D.people.forEach((p, i) => {
        const f = makeFigure(T.people[i % 5]); W.scene.add(f); figs[p.name] = f;
        const el = document.createElement("div"); el.className = "r3-label";
        el.innerHTML = `<div class="b" hidden style="border-color:${css(`--p${i % 5}`)}"></div><span style="color:${css(`--p${i % 5}`)}">${esc(p.name)}</span>`;
        stage.appendChild(el); labels[p.name] = { el, pos: null, bubble: "" };
      });
      S = { D, walk, T, W, renderer, camera, controls, figs, labels, v: 0, speed: 1, playing: true,
        clock: stage.querySelector(".r3-clock"), toast: stage.querySelector(".r3-toast"),
        playBtn: root.querySelector("#r3-play"), slider: root.querySelector("#r3-slider"), follow: "" };
      const days = Object.keys(D.days || {}).map(Number).sort((a, b) => a - b);
      const daySel = root.querySelector("#r3-day");
      daySel.innerHTML = days.map((d) => `<option value="${d}">${d} 日目</option>`).join("") || `<option>―</option>`;
      const fol = root.querySelector("#r3-follow");
      fol.innerHTML += D.people.map((p) => `<option>${esc(p.name)}</option>`).join("");
      const resize = () => { const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
      S.ro = new ResizeObserver(resize); S.ro.observe(stage); resize();
      S.playBtn.addEventListener("click", () => {
        if (S.v >= S.day.total) S.v = 0;
        S.playing = !S.playing; S.playBtn.textContent = S.playing ? "一時停止" : "再生";
      });
      S.slider.addEventListener("input", () => { S.v = Number(S.slider.value) * S.day.total; });
      daySel.addEventListener("change", () => setDay(Number(daySel.value)));
      root.querySelector("#r3-speed").addEventListener("change", (e) => (S.speed = Number(e.target.value)));
      fol.addEventListener("change", (e) => { S.follow = e.target.value; if (!S.follow) S.controls.target.copy(W.camp); });
      if (!days.length) { S.clock.textContent = "まだ再生できる日がありません"; return; }
      daySel.value = String(days[days.length - 1]);
      setDay(days[days.length - 1]);
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) { S.playing = false; S.playBtn.textContent = "再生"; S.v = S.day.segs[2].v0 + 4; }
      S.raf = requestAnimationFrame(loop);
    },
    // 動画を作るとき用: 日と再生位置 (秒) を指定して 1 コマ描く
    setAutoCamera(on) { if (S) S.autoCam = !!on; },
    setSegments(day, secByKey) { if (S) { S.segOverride = S.segOverride || {}; S.segOverride[day] = secByKey; } },
    timeline(day) { if (!S) return null; const P = planDay(S.D, day); return { total: P.total, segs: P.segs.map((s) => ({ key: s.key, v0: s.v0, v1: s.v1 })), eve: P.eve.length }; },
    seek(day, v) {
      if (!S) return;
      if (S.dayNum !== day || !S.day || S.day.segOverrideKey !== JSON.stringify((S.segOverride || {})[day] || {})) {
        setDay(day); S.day.segOverrideKey = JSON.stringify((S.segOverride || {})[day] || {});
      }
      S.playing = false; S.v = v; S.last = 0;
      frame(v); if (S.autoCam) autoCamera(); S.controls.update(); S.renderer.render(S.W.scene, S.camera); placeLabels();
    },
    stop() {
      if (!S) return;
      cancelAnimationFrame(S.raf); S.ro && S.ro.disconnect(); S.renderer.dispose(); S = null;
    },
  };
})();
