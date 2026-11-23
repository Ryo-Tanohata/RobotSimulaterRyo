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
  const WORK_EVENTS = ["採集", "探索", "狩り", "道具", "火", "種まき", "住まい", "けが", "畑", "畑仕事", "ヤギの世話", "ヤギを捕まえる", "土器", "交換に行く", "記録をつける",
    // G13・G15・Society 3.0 の仕事 (2026-11-22): 水の道・水の輪・水の作業場・燃える石・かまど・字の仕事
    "水の道を掘る", "水の輪を直す", "水の作業場で働く", "水の作業場を作る", "燃える石を掘る", "かまどを作りかえる", "知らせを書く", "字を教える", "帳をつける"];
  // 混んだ日の昼の知らせで先に見せる仕事 (この順。ほかの仕事は、その日に少ないものから)
  const NEW_WORK = ["燃える石を掘る", "知らせを書く", "字を教える", "帳をつける", "かまどを作りかえる", "水の作業場を作る", "水の輪を直す", "水の作業場で働く", "水の道を掘る"];
  const EVE_EVENTS = ["話す", "分ける", "蓄える", "蓄えから取る", "収穫", "木から取る"];
  // 夜の知らせ: G5 の出来事 (もめごと・祭り・まとめ役・分かれる など) と G6 の出来事 (ほかの村・交換・印・記録・町 など) も出す (2026-10-09 本人と決めた)
  const NIGHT_EVENTS = ["死", "けが", "夜", "掟", "腐る", "育つ", "干す", "フェーズ", "生まれる", "訪れる", "加わる", "去る", "ヤギ", "大人になる", "家族", "虫", "雨", "受けつぎ", "区切り",
    "もめごと", "収める", "裁き", "罰", "祭り", "まとめ役", "分かれる", "段階", "共同の仕事", "倉から取る",
    "よその村", "交換", "貸し借り", "覚え", "印", "封", "記録", "確かめる", "町",
    "市", "水", "見習い", "持ち場", "字を習う", "年の集まり", "年の名前", "頼み", "知らせ"];
  // 日付は「10年31日目」と表す (2026-10-09 本人の希望。年は過ぎた年の数で、最初の年は 0年。era2.py の day // YEAR と同じ)。この世界の 1 年は 120 日 (夏・秋・冬・春が 30 日ずつ、era2.py の YEAR) で、現実の 1 年とは違う
  const YEAR_DAYS = 120;
  const yearDay = (d) => ({ year: Math.floor(d / YEAR_DAYS), day: (d % YEAR_DAYS) + 1 });
  const dayLabel = (d) => { const y = yearDay(d); return `${y.year}年${y.day}日目`; };

  let S = null; // 状態

  // しまった年 (2026-10-10 本人が決めた「古い記録を年ごとのファイルに分ける」): D.events と D.days は、しまっていない年 (D.archive.since の日から) の分だけ。
  // しまった年の日は、その年の出来事と再生の行を loadYear で読んでから見せる (need)。亡くなった日・畑にまいた日・住まいができた日は、どの日にも使うので D.archive.keep にある
  const allEvents = (D) => ((D.archive && D.archive.keep) || []).concat(D.events);
  const oldYear = (D, day) => (D.archive && day < D.archive.since ? Math.floor(day / YEAR_DAYS) : null);
  function dayData(D, day) {  // その日の出来事と、再生の行 (だれがどの活動でどこへ)
    const y = oldYear(D, day);
    if (y === null) return { events: D.events.filter((e) => e.day === day), rows: (D.days && D.days[day]) || [] };
    const Y = S && S.years[y];
    return { events: Y ? Y.events.filter((e) => e.day === day) : [], rows: (Y && Y.days[day]) || [] };
  }
  function allDays(D) {  // 選べる日 (しまった年の日もふくむ)
    const out = [];
    for (const y of (D.archive && D.archive.years) || []) for (let d = y.first_day; d <= y.last_day; d++) out.push(d);
    return out.concat(Object.keys(D.days || {}).map(Number)).sort((a, b) => a - b);
  }

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

  // 建てた物の場所 (2026-11-22): 水の輪・水の作業場・燃える石の掘り場・知らせ板・畑・水の道の場所と、重なった家の並べ直し。
  // state には場所がない物が多いので、地図 (川・草地) とキャンプから決める (いつから見せるかは app/scene3d.json。tools/build_scene3d.py が作る)。
  // 村のデータは変えない。見せ方だけ
  const CROWD = 40;  // その日に村にいる人がこれより多いと「混んだ日」: 名前は話に出る人だけ・人を仕事の場所に広げる
  function layout(D) {
    if (D._lay3d) return D._lay3d;
    const T = D.map.terrain, W = D.map.w, H = D.map.h, SC = D.scene3d || {};
    const ter = (x, y) => (x < 0 || y < 0 || x >= W || y >= H ? null : T[Math.floor(y)][Math.floor(x)]);
    const cx = D.camp.x + 0.5, cy = D.camp.y + 0.5, dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    const L = { fields: { x0: cx - 13, x1: cx - 1.5, y0: cy + 2, y1: cy + 12 }, mills: {}, ws: {}, house: {} };
    const inFields = (q, m = 0) => q.x > L.fields.x0 - m && q.x < L.fields.x1 + m && q.y > L.fields.y0 - m && q.y < L.fields.y1 + m;
    const grassNear = (x, y, avoid) => {  // (x, y) にいちばん近い草地のマス (avoid に当たらないもの)
      let best = null;
      for (let r = 0; r <= 8 && !best; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        const q = { x: Math.floor(x) + dx + 0.5, y: Math.floor(y) + dy + 0.5 };
        if (ter(q.x, q.y) === "g" && !(avoid && avoid(q)) && (!best || dist(q, { x, y }) < dist(best, { x, y }))) best = q;
      }
      return best || { x, y };
    };
    if (SC.board) L.board = grassNear(cx - 2.5, cy - 2.6);
    // 水の輪: キャンプに近い川のマスから、2.2 マスずつあけて (岸に草地のあるマス)。作業場は、その輪の岸の、キャンプがわの草地
    const river = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (ter(x, y) === "r") river.push({ x: x + 0.5, y: y + 0.5 });
    river.sort((a, b) => dist(a, { x: cx, y: cy }) - dist(b, { x: cx, y: cy }));
    const spots = [];
    const bankOf = (q) => {
      let best = null;
      for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, 1], [-1, 1], [1, -1]]) {
        const b = { x: q.x + dx, y: q.y + dy };
        if (ter(b.x, b.y) === "g" && (!best || dist(b, { x: cx, y: cy }) < dist(best, { x: cx, y: cy }))) best = b;
      }
      return best;
    };
    for (const q of river) {
      if (spots.length >= ((SC.mills || []).length || 0) + 2) break;
      const bank = bankOf(q);
      if (!bank || dist(q, { x: cx, y: cy }) < 2.5 || spots.some((s) => dist(s, q) < 2.2)) continue;
      spots.push({ ...q, bank });
    }
    // 作業場のある輪を、キャンプにいちばん近いところに (作業場がよく見えるように)。ほかの輪はそのあとに並べる
    const wsIds = (SC.ws || []).map((w) => w.id), order = (SC.mills || []).slice().sort((a, b) => (wsIds.includes(b.id) ? 1 : 0) - (wsIds.includes(a.id) ? 1 : 0));
    order.forEach((m, i) => { if (spots[i]) L.mills[m.id] = spots[i]; });
    (SC.ws || []).forEach((w, i) => {
      const at = L.mills[w.id] || spots[i];
      if (at) L.ws[w.id] = { x: at.bank.x + (at.bank.x - at.x) * 0.6, y: at.bank.y + (at.bank.y - at.y) * 0.6, wheel: at };
    });
    // 水の道: 畑にいちばん近い水の輪から、畑の北東の角へ
    const fc = { x: L.fields.x1, y: L.fields.y0 };
    const src = spots.slice().sort((a, b) => dist(a, fc) - dist(b, fc))[0];
    if (src) L.canal = { a: { x: src.x, y: src.y }, b: { x: (L.fields.x0 + L.fields.x1) / 2, y: (L.fields.y0 + L.fields.y1) / 2 } };
    if (SC.pit) { const pl = (D.places || []).find((p) => p.id === SC.pit.place); if (pl) L.pit = { x: pl.x + 0.5, y: pl.y + 0.5 }; }
    // 家: 同じ場所に 2 軒以上ある家 (場所が見つからなかった家は同じ点に重なる) を、まわりの草地に 2 マスおきに並べ直す
    const hs = D.houses || [], groups = {};
    for (const v of hs) (groups[`${v.x},${v.y}`] = groups[`${v.x},${v.y}`] || []).push(v);
    const placed = hs.filter((v) => groups[`${v.x},${v.y}`].length === 1).map((v) => ({ x: v.x + 0.5, y: v.y + 0.5 }));
    const busy = (q) => dist(q, { x: cx, y: cy }) < 4.2 || inFields(q, 1.2) || (L.board && dist(q, L.board) < 2.6)
      || Object.values(L.ws).some((w) => dist(q, w) < 2.4) || spots.some((s) => dist(q, s) < 1.4) || (L.pit && dist(q, L.pit) < 3)
      || placed.some((p) => dist(q, p) < 1.9);
    for (const key in groups) {
      const g = groups[key];
      if (g.length < 2) continue;
      const o = { x: g[0].x + 0.5, y: g[0].y + 0.5 }, cand = [];
      for (let y = 1; y < H - 1; y += 2) for (let x = 1; x < W - 1; x += 2) if (ter(x, y) === "g") cand.push({ x: x + 0.5, y: y + 0.5 });
      cand.sort((a, b) => dist(a, o) - dist(b, o));
      let k = 0;
      for (const v of g) {
        while (k < cand.length && busy(cand[k])) k++;
        const q = cand[k++] || o;
        L.house[v.household] = { x: q.x - 0.5, y: q.y - 0.5 }; placed.push(q);
      }
    }
    D._lay3d = L;
    return L;
  }
  const houseXY = (D, v) => (layout(D).house[v.household] || v);

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
    root.userData = { J, pelvis, head, mat };
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
    const scene = new THREE.Scene(), SC = D.scene3d || {}, LAY = layout(D);
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

    // 住まい (建てた日から見せる。円い壁と草ぶきの屋根)
    const hut = new THREE.Group();
    const wall = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.4, 1.1, 12, 1, true), new THREE.MeshLambertMaterial({ color: T.tuber, side: THREE.DoubleSide }));
    wall.position.y = 0.55; hut.add(wall);
    const roof = new THREE.Mesh(new THREE.ConeGeometry(1.8, 1.5, 12), new THREE.MeshLambertMaterial({ color: T.hill }));
    roof.position.y = 1.85; hut.add(roof);
    hut.position.set(camp.x - 3.2, camp.y, camp.z - 2.2); hut.visible = false; scene.add(hut);
    const built = allEvents(D).find((e) => e.type === "住まい" && /住まいができた/.test(e.text));

    // 畑 (Society 2.0): 秋にまいた畑を、キャンプの南西に 1 枚ずつ並べる。色は季節で変える (fieldsOn で毎コマ決める)
    const plots = [];
    for (let k = 0; k < 40; k++) {  // 16 枚までは前と同じ並び。畑が多い村 (Society 3.0 のころは 1 季節に何百枚もまく) は、西と南に 40 枚まで
      const m = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.08, 1.1), new THREE.MeshLambertMaterial({ color: T.tuber }));
      const col = k < 16 ? k % 4 : k < 28 ? 4 + ((k - 16) % 2) : (k - 28) % 4, row = k < 16 ? Math.floor(k / 4) : k < 28 ? Math.floor((k - 16) / 2) : 4 + Math.floor((k - 28) / 4);
      const p = w2t(D, D.camp.x + 0.5 - 2.5 - col * 1.8, D.camp.y + 0.5 + 2.5 + row * 1.4, 0.05);
      m.position.copy(p); m.visible = false; scene.add(m); plots.push(m);
    }
    const sowings = allEvents(D).filter((e) => e.type === "畑" && /をまいた/.test(e.text));

    // 家族の住まい (G3 から): 四角い家。壁は土の色に家族の色をまぜ、平らな屋根。広さで大きさを変え、建てかけは低い壁だけ (housesOn で毎コマ決める)
    const houses = (D.houses || []).map((v) => {
      const g = new THREE.Group(), col = new THREE.Color(homeColor(Math.max(0, homesOf(D).indexOf(v.household))));
      const wall = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshLambertMaterial({ color: T.tuber.clone().lerp(col, 0.35) }));
      const roof = new THREE.Mesh(new THREE.BoxGeometry(1, 0.12, 1), new THREE.MeshLambertMaterial({ color: T.hill.clone().multiplyScalar(0.8) }));
      g.add(wall); g.add(roof);
      // 石のかまど (G15): 作りかえ終えた日から、屋根に石の煙突 (housesOn で毎コマ決める)
      const stove = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.6, 0.22), new THREE.MeshLambertMaterial({ color: new THREE.Color("#6b6b6b") }));
      stove.visible = false; g.add(stove);
      const at = houseXY(D, v);
      g.position.copy(w2t(D, at.x + 0.5, at.y + 0.5)); g.visible = false; scene.add(g);
      return { v, g, wall, roof, stove, stoveDay: (SC.stoves || {})[v.household] ?? null };
    });

    // ほかの村 (G6): 知っている村ごとに、地図の端の内がわに小さな家 3 つと、キャンプからのうすい道 (知った日から見せる。villagesOn で毎コマ決める)
    const villages = ((D.g6 && D.g6.others) || []).map((o) => {
      const g = new THREE.Group();
      const ex = Math.min(W - 2.5, Math.max(1.5, o.edge[0] + 0.5)), ey = Math.min(H - 2.5, Math.max(1.5, o.edge[1] + 0.5));
      for (let k = 0; k < 3; k++) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.6, 0.7), new THREE.MeshLambertMaterial({ color: T.hill.clone().multiplyScalar(0.65) }));
        m.position.copy(w2t(D, ex + Math.cos(k * 2.1) * 1.1, ey + Math.sin(k * 2.1) * 1.1, 0.3)); g.add(m);
      }
      const cx = D.camp.x + 0.5, cy = D.camp.y + 0.5, n = Math.max(4, Math.round(Math.hypot(ex - cx, ey - cy) / 2));
      for (let i = 1; i < n; i++) {  // 道: 平たい小さな板を点々と並べる
        const dot = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.03, 0.35), new THREE.MeshLambertMaterial({ color: T.tuber.clone().multiplyScalar(0.85) }));
        dot.position.copy(w2t(D, cx + (ex - cx) * i / n, cy + (ey - cy) * i / n, 0.04)); g.add(dot);
      }
      g.visible = false; scene.add(g);
      return { o, g, at: w2t(D, ex, ey, 1.4) };
    });

    // 建てた物 (2026-11-22。G13・G15・Society 3.0): 見せる日は scene3d.json、場所は layout。どれも簡単な形
    const things = [];  // { g, from: 見せはじめる日, label?: 名前の札, at?: 札の場所 }
    const lam = (c) => new THREE.MeshLambertMaterial({ color: new THREE.Color(c) });
    const wood = lam("#8a5a2b"), dark = lam("#3b3b3b"), stone = lam("#8d8d86"), water = lam("#4a90c2");
    const wheelGeo = new THREE.TorusGeometry(0.55, 0.07, 6, 16), paddle = new THREE.BoxGeometry(0.12, 0.3, 0.32);
    const makeWheel = (q, big) => {  // 水の輪: 川に立てた輪と羽
      const g = new THREE.Group(), w = new THREE.Group(), s = big ? 1.4 : 1;
      g.add(w); g.userData.spin = w;
      const rim = new THREE.Mesh(wheelGeo, wood); w.add(rim);
      for (let k = 0; k < 8; k++) { const b = new THREE.Mesh(paddle, wood); const a = k * Math.PI / 4; b.position.set(Math.cos(a) * 0.6, Math.sin(a) * 0.6, 0); b.rotation.z = a; w.add(b); }
      const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.9, 6), wood); axle.rotation.x = Math.PI / 2; w.add(axle);
      g.scale.setScalar(s); g.position.copy(w2t(D, q.x, q.y, 0.35 * s));
      g.lookAt(w2t(D, q.bank.x, q.bank.y, 0.35 * s));  // 輪の面を岸と同じ向きに (水は輪の下を流れる)
      g.rotateY(Math.PI / 2);
      scene.add(g); return g;
    };
    for (const m of SC.mills || []) {
      const q = LAY.mills[m.id];
      if (q) things.push({ g: makeWheel(q, (SC.ws || []).some((w) => w.id === m.id)), from: m.day, spin: true });
    }
    for (const [i, w] of (SC.ws || []).entries()) {  // 水の作業場: 板ぶきの小屋と、のこの台
      const q = LAY.ws[w.id];
      if (!q) continue;
      const g = new THREE.Group();
      const shed = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.2, 1.6), lam("#b08850")); shed.position.y = 0.6; g.add(shed);
      const roof = new THREE.Mesh(new THREE.ConeGeometry(1.75, 0.8, 4), lam("#6e4a28")); roof.rotation.y = Math.PI / 4; roof.scale.set(1, 1, 0.7); roof.position.y = 1.6; g.add(roof);
      for (let k = 0; k < 3; k++) { const log = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1.6, 6), wood); log.rotation.z = Math.PI / 2; log.position.set(0, 0.12 + k * 0.2, 1.2 + (k % 2) * 0.05); g.add(log); }
      g.position.copy(w2t(D, q.x, q.y)); g.lookAt(w2t(D, q.wheel.x, q.wheel.y)); scene.add(g);
      things.push({ g, from: w.done ?? w.day, label: `水の作業場 ${w.id}`, at: w2t(D, q.x, q.y, 3.0 + 1.2 * (i % 2)) });
    }
    if (SC.canal && LAY.canal) {  // 水の道: 川から畑へ、細い水の筋
      const { a, b } = LAY.canal, n = Math.max(3, Math.round(Math.hypot(b.x - a.x, b.y - a.y) / 0.8)), g = new THREE.Group();
      for (let i = 0; i <= n; i++) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.04, 0.85), water); m.position.copy(w2t(D, a.x + (b.x - a.x) * i / n, a.y + (b.y - a.y) * i / n, 0.03)); g.add(m); }
      scene.add(g); things.push({ g, from: SC.canal.day });
    }
    if (SC.pit && LAY.pit) {  // 燃える石の掘り場: 黒い穴と、掘った石の山と、木の枠
      const g = new THREE.Group(), q = LAY.pit;
      const hole = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 0.9, 0.3, 10), dark); hole.position.y = 0.05; g.add(hole);
      for (let k = 0; k < 9; k++) { const r = new THREE.Mesh(new THREE.DodecahedronGeometry(0.22 + (k % 3) * 0.06), lam("#1f1f1f")); r.position.set(1.9 + (k % 3) * 0.32, 0.18 + Math.floor(k / 3) * 0.2, -0.4 + (k % 4) * 0.25); g.add(r); }
      for (const [x, z] of [[-0.9, -0.9], [0.9, -0.9], [-0.9, 0.9], [0.9, 0.9]]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.4, 0.12), wood); p.position.set(x, 0.7, z); g.add(p); }
      const beam = new THREE.Mesh(new THREE.BoxGeometry(2, 0.12, 0.12), wood); beam.position.set(0, 1.4, 0); g.add(beam);
      g.position.copy(w2t(D, q.x, q.y)); scene.add(g);
      things.push({ g, from: SC.pit.day, label: "燃える石の掘り場", at: w2t(D, q.x, q.y, 3.2) });
    }
    if (SC.board && LAY.board) {  // 村の知らせ板: 2 本の柱と板。貼った知らせは白い紙
      const g = new THREE.Group(), q = LAY.board;
      for (const x of [-0.9, 0.9]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.14, 1.9, 0.14), wood); p.position.set(x, 0.95, 0); g.add(p); }
      const plank = new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.0, 0.1), lam("#a87b4f")); plank.position.y = 1.35; g.add(plank);
      const sheets = [];
      for (let k = 0; k < 12; k++) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.34, 0.02), lam("#f4efe0"));
        m.position.set(-0.8 + (k % 6) * 0.32, 1.58 - Math.floor(k / 6) * 0.44, 0.07); m.visible = false; g.add(m); sheets.push(m);
      }
      g.position.copy(w2t(D, q.x, q.y)); g.lookAt(w2t(D, D.camp.x + 0.5, D.camp.y + 0.5)); scene.add(g);
      things.push({ g, from: SC.board.day, board: sheets, label: "村の知らせ板", at: w2t(D, q.x, q.y, 3.8) });
    }

    const sun = new THREE.DirectionalLight(0xffffff, 0.9); sun.position.set(30, 50, 20); scene.add(sun);
    const amb = new THREE.AmbientLight(0xffffff, 0.55); scene.add(amb);
    return { scene, camp, flame, fireLight, sun, amb, hut, hutDay: built ? built.day : null, plots, sowings, houses, villages, things };
  }

  function placeOf(D, id) { return D.places.find((p) => p.id === id) || D.places[0]; }

  // 家族 (2026-10-08 追加): 家族ごとの色・家・朝夕と夜に集まる場所。家族は D.people の household (前からいる人とその子は「川辺の家」)
  const HOME_COLORS = ["#c2410c", "#7c3aed", "#0f766e", "#be185d", "#4d7c0f", "#1d4ed8", "#a16207", "#0e7490", "#9f1239", "#4338ca"];
  // 家族が 10 をこえたら (G6 で人が集まると)、色相を少しずつずらした色を足す (10 までは前と同じ色)
  const homeColor = (i) => (i < HOME_COLORS.length ? HOME_COLORS[i] : `hsl(${Math.round((i * 137.5) % 360)}, 55%, 38%)`);
  function homesOf(D) {
    const hs = [];
    for (const p of D.people) { const h = p.household || "-"; if (!hs.includes(h)) hs.push(h); }
    return hs;
  }
  function houseAt(D, h, day) {  // その日の家族の住まい: null (まだない) / {x, y, size, built}
    const v = (D.houses || []).find((x) => x.household === h);
    if (!v || v.start > day || (v.left != null && v.left <= day)) return null;  // 家ごと村を出た家は、出た日から描かない (2026-10-09 本人と決めた)
    const done = v.built != null && v.built <= day;
    const size = done ? (v.sizes.filter((s) => s[0] <= day).pop() || [0, 20])[1] : 0;
    const at = houseXY(D, v);
    return { x: at.x, y: at.y, size, built: done };
  }
  function homeSpot(D, h, day) {  // 家族の集まる場所: 家族の住まいができていればその前、なければキャンプの火のまわりの家族ごとの場所
    const hs = homesOf(D), i = Math.max(0, hs.indexOf(h));
    const v = houseAt(D, h, day);
    if (v && v.built) return { x: v.x + 0.5, y: v.y + 1.6 };
    const many = hs.filter((x) => D.people.some((p) => (p.household || "-") === x)).length;
    if (many <= 1) return { x: D.camp.x + 0.5, y: D.camp.y + 0.5 };
    const a = i * (2 * Math.PI / many) + 0.4;
    return { x: D.camp.x + 0.5 + Math.cos(a) * 3.0, y: D.camp.y + 0.5 + Math.sin(a) * 3.0 };
  }

  function planDay(D, day) {
    const { events: ev, rows } = dayData(D, day);
    const names = D.people.map((p) => p.name);
    const plan = {}, groups = {};
    names.forEach((n, i) => {
      const r = rows.find((x) => x.name === n), P = D.people[i];
      const died = S.died[n];
      const alive = !died || died.day >= day;  // 亡くなった日はまだ映す
      const here = day >= (P.since || 0) && !(P.left && P.left < day);  // 村に来る前・生まれる前・村を出たあとは映さない (Society 2.0)
      const pl = placeOf(D, r ? r.place : "camp");
      (groups[pl.id] = groups[pl.id] || []).push(n);
      const age = P.born_day != null ? (day - P.born_day) / YEAR_DAYS : 99;  // 子は小さく描く
      plan[n] = { name: n, i, alive: (!!r || alive) && here, activity: r ? r.activity : "休む", place: pl, size: age >= 15 ? 1 : 0.45 + 0.55 * Math.max(0, age) / 15,
        home: P.household || "-", child: age < 15 };
    });
    let maxDist = 1;
    const fams = {};  // 家族ごとの、その日にいる人 (家族の集まる場所で、まわりに並べるため)
    for (const n of names) if (plan[n].alive) (fams[plan[n].home] = fams[plan[n].home] || []).push(n);
    const oneHome = Object.keys(fams).length <= 1;
    const crowded = names.filter((n) => plan[n].alive).length > CROWD;
    // 仕事の場所 (2026-11-22): 記録の場所が「キャンプ」の仕事のうち、場所のある仕事は、その場所で (水の作業場・掘り場・知らせ板 など)。
    // 混んだ日は、畑仕事は畑に、ほかのキャンプの人もキャンプのまわりに広げる (人の山にならないように)
    const LAY = layout(D), st = {}, stKey = {};
    const stationOf = (p) => {
      const a = p.activity, wsIds = Object.keys(LAY.ws);
      if (/水の作業場/.test(a) && wsIds.length) return "ws:" + wsIds[p.i % wsIds.length];
      if (a === "水の輪を直す" && Object.keys(LAY.mills).length) return "mill";
      if (a === "燃える石を掘る" && LAY.pit && day >= ((D.scene3d || {}).pit || {}).day) return "pit";
      if (a === "知らせを書く" && LAY.board) return "board";
      if (/^(字を教える|字を習う|帳をつける)$/.test(a) && LAY.board) return "school";
      if (a === "水の道を掘る" && LAY.canal) return "canal";
      if (a === "かまどを作りかえる" && houseAt(D, p.home, day)) return "home";
      if (crowded && a === "畑仕事") return "fields";
      if (crowded) return "camp";
      return null;
    };
    for (const n of names) {
      const p = plan[n];
      if (!p.alive || p.place.id !== "camp") continue;
      const k = stationOf(p);
      if (k) { stKey[n] = k; (st[k] = st[k] || []).push(n); }
    }
    const sunflower = (c, k, r0, step) => { const r = r0 + step * Math.sqrt(k), a = k * 2.39996; return { x: c.x + Math.cos(a) * r, y: c.y + Math.sin(a) * r }; };
    const stationSpot = (n) => {
      const key = stKey[n], k = st[key].indexOf(n), m = st[key].length, p = plan[n];
      if (key.startsWith("ws:")) { const w = LAY.ws[key.slice(3)]; return sunflower({ x: w.x + (w.x - w.wheel.x) * 0.8, y: w.y + (w.y - w.wheel.y) * 0.8 }, k, 1.0, 0.5); }
      if (key === "mill") { const qs = Object.values(LAY.mills), q = qs[k % qs.length]; return { x: q.bank.x + 0.3 * Math.floor(k / qs.length), y: q.bank.y }; }
      if (key === "pit") return sunflower(LAY.pit, k, 1.4, 0.5);
      if (key === "board") return { x: LAY.board.x - 0.8 + 0.55 * k, y: LAY.board.y + 0.9 };
      if (key === "school") return sunflower({ x: LAY.board.x - 2.6, y: LAY.board.y + 0.4 }, k, 0.6, 0.55);
      if (key === "canal") { const { a, b } = LAY.canal, t = (k + 0.5) / m; return { x: a.x + (b.x - a.x) * t + 0.45 * (k % 2 ? 1 : -1), y: a.y + (b.y - a.y) * t }; }
      if (key === "home") { const h = houseAt(D, p.home, day); return { x: h.x + 0.5 + 0.9, y: h.y + 0.5 }; }
      if (key === "fields") { const F = LAY.fields, u = (k * 0.618034 + 0.31) % 1, w = (k + 0.5) / m; return { x: F.x0 + 0.3 + u * (F.x1 - F.x0 - 0.6), y: F.y0 + 0.3 + w * (F.y1 - F.y0 - 0.6) }; }
      return sunflower({ x: D.camp.x + 0.5, y: D.camp.y + 0.5 }, k, 1.6, 0.45);  // camp
    };
    for (const n of names) {
      const p = plan[n], k = groups[p.place.id].indexOf(n), a = k * 2.1;
      p.spot = { x: p.place.x + 0.5 + Math.cos(a) * 1.2 * (k > 0), y: p.place.y + 0.5 + Math.sin(a) * 1.2 * (k > 0) };
      if (p.place.id === "camp") p.spot = { x: D.camp.x + 0.5 + Math.cos(p.i * 1.26) * 2.2, y: D.camp.y + 0.5 + Math.sin(p.i * 1.26) * 2.2 };
      if (crowded && p.place.id !== "camp") p.spot = sunflower({ x: p.place.x + 0.5, y: p.place.y + 0.5 }, k, 0, 0.55);
      if (stKey[n]) p.spot = stationSpot(n);
      p.station = stKey[n] || null;
      if (oneHome) {  // 家族が 1 つ (Society 1.0) のときは、前と同じく火のまわり
        p.ring = { x: D.camp.x + 0.5 + Math.cos(p.i * 1.2566) * 1.3, y: D.camp.y + 0.5 + Math.sin(p.i * 1.2566) * 1.3 };
      } else {  // 朝・夕方・夜は、家族の集まる場所 (家族の住まいの前か、火のまわりの家族ごとの場所) に、家族で輪になる
        const c = homeSpot(D, p.home, day), mates = fams[p.home] || [n], j = Math.max(0, mates.indexOf(n));
        const r = mates.length > 1 ? 0.55 + 0.12 * mates.length : 0;
        p.ring = { x: c.x + Math.cos(j * 2 * Math.PI / mates.length) * r, y: c.y + Math.sin(j * 2 * Math.PI / mates.length) * r };
        if (crowded && mates.length > 8) p.ring = sunflower(c, j, 0.5, 0.42);  // 大きな家族 (何十人も) は、大きな輪でなく、家の前にかたまって座る
        if (p.child && p.activity === "休む" && !p.station) p.spot = p.ring;  // 子は昼も家族のところにいる
      }
      p.dist = Math.hypot(p.spot.x - p.ring.x, p.spot.y - p.ring.y);
      maxDist = Math.max(maxDist, p.dist);
    }
    let eve = ev.filter((e) => EVE_EVENTS.includes(e.type));
    if (crowded) {  // 混んだ日の夕方: 話は 6 つまで (動画の話に出る人の話を先に)・ほかは 4 つまで。吹き出しを読める長さで出すため
      const feat = (S && S.featured && S.featured[day]) || new Set();
      const talks = eve.filter((e) => e.type === "話す"), keep = new Set([...talks.filter((e) => feat.has(e.who)), ...talks.filter((e) => !feat.has(e.who))].slice(0, 6));
      eve.filter((e) => e.type !== "話す").slice(0, 4).forEach((e) => keep.add(e));
      eve = eve.filter((e) => keep.has(e));
    }
    let work = ev.filter((e) => WORK_EVENTS.includes(e.type));
    if (crowded) {  // 混んだ日の昼の知らせ: めずらしい仕事を先に、1 つの仕事から 2 つまで (畑仕事が何百も並ばないように)
      const cnt = {}, took = {};
      for (const e of work) cnt[e.type] = (cnt[e.type] || 0) + 1;
      const pri = (e) => { const i = NEW_WORK.indexOf(e.type); return (i < 0 ? 100 + Math.min(cnt[e.type], 99) : i) + (/いなかった|休んだ|できなかった/.test(e.text) ? 50 : 0); };
      work = work.slice().sort((a, b) => pri(a) - pri(b)).filter((e) => (took[e.type] = (took[e.type] || 0) + 1) <= 2).slice(0, 14);
    }
    const segs = SEG.map((s) => ({ ...s }));
    segs[4].sec = Math.max(10, Math.min(eve.length, 12) * 2.6 + 2);  // 人が増えても夕方が長くなりすぎないように
    const over = (S && S.segOverride && S.segOverride[day]) || {};  // 動画用: 場面ごとの秒数を指定できる
    for (const s of segs) if (over[s.key]) s.sec = over[s.key];
    let acc = 0; for (const s of segs) { s.v0 = acc; acc += s.sec; s.v1 = acc; }
    return { plan, maxDist, segs, total: acc, work, eve, crowded, oneHome,
      night: ev.filter((e) => NIGHT_EVENTS.includes(e.type)), fire: ev.some((e) => e.type === "火" && !/できなかった/.test(e.text)) || D.camp.fire > 0 };
  }

  // その日の畑: 秋にまいてから 30 日は土、次の 60 日 (冬・春) は芽、次の 30 日 (夏) は実り。そのあとは消える (era2.py の畑の育ち方と同じ)
  function fieldsOn(day) {
    const on = S.W.sowings.filter((e) => e.day <= day && day < e.day + 120);
    S.W.plots.forEach((m, k) => {
      const e = on[k];
      m.visible = !!e;
      if (!e) return;
      const age = day - e.day;
      m.material.color.copy(age < 30 ? S.T.tuber.clone().multiplyScalar(0.7) : age < 90 ? S.T.grass.clone().multiplyScalar(0.75) : new THREE.Color("#d9a520"));  // 実った畑は麦の金色 (木の実の赤とまぎれないように。2026-10-08)
    });
  }

  // その日の家族の住まい: 建てかけは低い壁、できたら広さに合わせた大きさ (20 m² → 1.8 マス幅)
  function housesOn(day) {
    for (const H of S.W.houses) {
      const v = houseAt(S.D, H.v.household, day);
      H.g.visible = !!v;
      if (!v) continue;
      const w = 0.9 + Math.sqrt(Math.max(v.size, 20)) / 5, d = w * 0.75, h = v.built ? 0.9 : 0.35;
      H.wall.scale.set(w, h, d); H.wall.position.y = h / 2;
      H.roof.visible = v.built; H.roof.scale.set(w + 0.2, 1, d + 0.2); H.roof.position.y = h + 0.06;
      H.stove.visible = v.built && H.stoveDay !== null && H.stoveDay <= day; H.stove.position.set(w * 0.3, h + 0.3, d * 0.25);
    }
  }

  // 知らせ板に貼ってある知らせ: その日までに書かれ、1 年 (120 日) のうちのもの。新しいほうから 12 枚 (i4.py の板と同じ数え方)
  function boardNotes(day) {
    const B = (S && S.D.scene3d && S.D.scene3d.board) || null;
    if (!B || day < B.day) return [];
    return B.notes.filter((n) => n.day <= day && n.day > day - YEAR_DAYS).slice(-12);
  }

  function lerp(a, b, u) { return { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u }; }

  function frame(v) {  // v = 再生の秒 (等倍)
    const P = S.day, D = S.D;
    const seg = P.segs.find((s) => v < s.v1) || P.segs[P.segs.length - 1];
    const u = Math.min(1, Math.max(0, (v - seg.v0) / seg.sec));
    const hour = seg.t0 + (seg.t1 - seg.t0) * u;
    S.clock.textContent = `${dayLabel(S.dayNum)} ${Math.floor(hour)}:${String(Math.floor((hour % 1) * 60)).padStart(2, "0")}  ${seg.label}`;
    // 明るさ (夜は暗く、焚き火が灯る)
    const light = hour < 6 ? 0.35 + (hour - 5.5) * 1.2 : hour > 19 ? Math.max(0.12, 0.9 - (hour - 19) * 0.35) : 0.9;
    S.W.sun.intensity = light; S.W.amb.intensity = 0.25 + light * 0.35;
    const lit = P.fire && (hour >= 18.5 || hour < 6);
    S.W.hut.visible = S.W.hutDay !== null && S.dayNum >= S.W.hutDay;
    fieldsOn(S.dayNum);
    housesOn(S.dayNum);
    for (const V of S.W.villages) V.g.visible = V.o.known != null && S.dayNum >= V.o.known;
    for (const X of S.W.things) {  // 建てた物 (見せはじめる日から)。水の輪は回し、知らせ板には 1 年のうちの知らせの紙を貼る
      X.g.visible = X.from != null && S.dayNum >= X.from;
      if (X.spin) X.g.userData.spin.rotation.z = -v * 0.9;
      if (X.board) { const n = boardNotes(S.dayNum).length; X.board.forEach((m, k) => (m.visible = k < n)); }
    }
    S.W.flame.visible = lit; S.W.fireLight.intensity = lit ? 1.6 + Math.sin(v * 13) * 0.3 : 0;
    S.W.scene.background = S.T.bg.clone().lerp(new THREE.Color(0x0b1220), 1 - Math.min(1, light / 0.9));

    for (const n in P.plan) {
      const p = P.plan[n], fig = S.figs[n];
      fig.visible = p.alive;
      if (!p.alive) continue;
      fig.scale.setScalar(p.size * (P.crowded ? 0.7 : 1));  // 混んだ日は人を少し小さく (重なりを減らす)
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
        const j = P.crowded ? 0.15 : 0.5;  // 混んだ日は、となりの人と重ならないように小さく動く
        at = { x: p.spot.x + Math.sin(v * 0.4 + p.i) * j, y: p.spot.y + Math.cos(v * 0.3 + p.i) * j };
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
      P.eve.slice(0, k + 1).forEach((e) => { if (e.type !== "話す") shown.push(e); });
      const e = P.eve[Math.min(k, P.eve.length - 1)];
      if (e && e.type === "話す") bubbles[e.who] = e.text.replace(/^.*?「/, "「");
      if (e && e.type === "分ける") bubbles[e.who] = `（${e.data.to} に ${e.data.food || "食べ物"} を分ける）`;
      if (e && e.type === "蓄える") bubbles[e.who] = `（蓄えに ${e.data.food || "食べ物"} を入れる）`;
      if (e && e.type === "蓄えから取る") bubbles[e.who] = `（蓄えから ${e.data.food || "食べ物"} を取る）`;
    }
    if (seg.key === "night") shown = P.night.length ? P.night : [{ text: "静かな夜" }];
    S.toast.innerHTML = shown.slice(-4).map((e) => `<div>${esc(plain(e.text))}</div>`).join("");
    S.toastWho = new Set(shown.slice(-4).map((e) => e.who).filter(Boolean));
    for (const n in S.labels) S.labels[n].bubble = bubbles[n] || "";
    if (S.people) S.people.frame(P, v);  // 人のモデル (setPeople。動画 D1P): 棒の人の代わりに動かし、名前の札の場所も合わせる
  }

  // 初期の記録 (1〜2 日目) にはカロリーの表記があるので、見せるときは言い換える
  const plain = (t) => String(t).replace(/で採集し ?[\d.]+ kcal 分を得た/, "で採集した").replace(/に食べ物を ?[\d.]+ kcal 分けた/, "に食べ物を分けた").replace(/ \([\d.]+ kcal の肉\)/, "");
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function placeLabels() {
    const r = S.renderer.domElement.getBoundingClientRect();
    for (const { el, V } of S.vlabels || []) {  // ほかの村の名前 (村が見えている日だけ)
      const p = V.at.clone().project(S.camera);
      el.hidden = !V.g.visible || p.z > 1;
      if (!el.hidden) el.style.transform = `translate(${(p.x * 0.5 + 0.5) * r.width}px, ${(-p.y * 0.5 + 0.5) * r.height}px) translate(-50%, -100%)`;
    }
    for (const X of S.tlabels || []) {  // 建てた物の名前 (見えている日だけ)。知らせ板は、いちばん新しい知らせの字も
      const p = X.at.clone().project(S.camera);
      X.el.hidden = !X.g.visible || p.z > 1;
      if (X.el.hidden) continue;
      if (X.board) { const ns = boardNotes(S.dayNum), last = ns[ns.length - 1]; X.el.querySelector("span").textContent = `知らせ板 ${ns.length} 枚` + (last ? `「${last.text.length > 16 ? last.text.slice(0, 16) + "…" : last.text}」` : ""); }
      X.el.style.transform = `translate(${(p.x * 0.5 + 0.5) * r.width}px, ${(-p.y * 0.5 + 0.5) * r.height}px) translate(-50%, -100%)`;
    }
    // 混んだ日 (2026-11-22): 名前は、話している人・動画の話に出る人 (setFeatured)・今の知らせに出る人だけ、カメラに近い順に 12 人まで
    let allow = null;
    if (S.day && S.day.crowded) {
      const feat = (S.featured && S.featured[S.dayNum]) || new Set(), want = [];
      for (const n in S.labels) {
        const L = S.labels[n];
        if (!S.figs[n].visible || !L.pos) continue;
        if (L.bubble || feat.has(n) || (S.toastWho && S.toastWho.has(n))) want.push([L.bubble ? -1 : feat.has(n) ? 0 : 1, L.pos.distanceTo(S.camera.position), n]);
      }
      want.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      allow = new Set(want.slice(0, 12).map((w) => w[2]));
    }
    for (const n in S.labels) {
      const L = S.labels[n], fig = S.figs[n];
      if (!fig.visible || !L.pos || (allow && !allow.has(n))) { L.el.hidden = true; continue; }
      const p = L.pos.clone().project(S.camera);
      if (p.z > 1) { L.el.hidden = true; continue; }
      L.el.hidden = false;
      L.el.style.transform = `translate(${(p.x * 0.5 + 0.5) * r.width}px, ${(-p.y * 0.5 + 0.5) * r.height}px) translate(-50%, -100%)`;
      L.el.querySelector(".b").textContent = L.bubble; L.el.querySelector(".b").hidden = !L.bubble;
      L.el.style.zIndex = L.bubble ? "55" : "10";  // 話している人の吹き出しを一番手前に (名前・出来事の一覧・時計・動画の字幕より上)
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
    let ps = Object.values(S.figs).filter((f) => f.visible).map((f) => f.position);
    if (!ps.length) return;
    let c = ps.reduce((a, p) => a.add(p), new THREE.Vector3()).multiplyScalar(1 / ps.length);
    let r = Math.max(...ps.map((p) => p.distanceTo(c)));
    if (S.day && S.day.crowded) {  // 混んだ日: 遠くの数人に合わせず、7 割の人が入る広さ (村のまん中と、仕事の場所が見える) にする
      const ds = ps.map((p) => p.distanceTo(c)).sort((a, b) => a - b);
      r = Math.min(r, ds[Math.floor(ds.length * 0.7)]);
    }
    const near = (S.people && S.people.camera) || { min: 13, add: 9 };  // 人のモデルのとき (D1P) は、集まっている人に寄る
    const dist = Math.min(near.max || 90, Math.max(near.min, r * (near.k || 2.3) + near.add));  // k・max は D1V (もっと寄る) から。ないときは前と同じ
    const dir = new THREE.Vector3(0.5, 0.62, 0.78).normalize();
    S.controls.target.lerp(c, 0.07);
    S.camera.position.lerp(S.controls.target.clone().add(dir.multiplyScalar(dist)), 0.07);
  }

  function setDay(d) {
    S.dayNum = d; S.day = planDay(S.D, d); S.v = 0; S.playing = true; S.playBtn.textContent = "一時停止";
    paint(S.day.oneHome);
  }
  // 人の色 (2026-11-22、1 日目の撮り直し D1): 村に家族が何十もあるデータで Society 1.0 の日 (その日にいるのが 1 つの家族だけ) を見ると、
  // 5 人がみな同じ家族の色になって見分けにくい。その日だけ、前の Society 1.0 と同じ人ごとの色にする。
  // 家族が 2 つ以上いる日は、今までどおり家族の色 (S3P34 などは変わらない)。データに家族が 1 つしかないときは、もともと人ごとの色
  function paint(solo) {
    if (S.solo === solo) return;
    S.solo = solo;
    for (const n in S.figs) {
      const c = S.figs[n].userData.cols, col = solo ? c.solo : c.home, hex = "#" + col.getHexString();
      S.figs[n].userData.mat.color.copy(col);
      const L = S.labels[n].el;
      L.querySelector("span").style.color = hex; L.querySelector(".b").style.borderColor = hex;
    }
  }

  window.Replay3D = {
    dayLabel, yearDay,
    // loadYear(年) → Promise<{events, days}>: しまった年のファイルを読む (index.html が渡す)
    start(root, D, walk, css, loadYear) {
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
      const hs = homesOf(D), seen = {};
      D.people.forEach((p, i) => {
        // 家族が 2 つ以上なら、家族ごとの色 (家族の中で明るさを少し変える)。1 つ (Society 1.0) なら前と同じ人ごとの色
        const h = p.household || "-", k = (seen[h] = (seen[h] ?? -1) + 1);
        const col = hs.length > 1 ? new THREE.Color(homeColor(hs.indexOf(h))).offsetHSL(0, 0, ((k % 3) - 1) * 0.09) : T.people[i % 5];
        const hex = "#" + col.getHexString();
        const f = makeFigure(col); W.scene.add(f); figs[p.name] = f;
        f.userData.cols = { home: col, solo: T.people[i % 5] };  // 家族の色と、人ごとの色 (家族が 1 つの日に使う。setDay の paint)
        const el = document.createElement("div"); el.className = "r3-label";
        el.innerHTML = `<div class="b" hidden style="border-color:${hex}"></div><span style="color:${hex}">${esc(p.name)}</span>`;
        stage.appendChild(el); labels[p.name] = { el, pos: null, bubble: "" };
      });
      const vlabels = W.villages.map((V) => {  // ほかの村の名前 (G6)
        const el = document.createElement("div"); el.className = "r3-label";
        el.innerHTML = `<span>${esc(V.o.name)} (歩いて ${V.o.days} 日)</span>`; el.hidden = true;
        stage.appendChild(el); return { el, V };
      });
      const tlabels = W.things.filter((X) => X.label).map((X) => {  // 建てた物の名前 (2026-11-22)
        const el = document.createElement("div"); el.className = "r3-label r3-thing";
        el.innerHTML = `<span>${esc(X.label)}</span>`; el.hidden = true;
        stage.appendChild(el); return { el, g: X.g, at: X.at, board: !!X.board };
      });
      const died = {};  // 人ごとの、亡くなった出来事 (しまった年もふくめて最初のもの)
      for (const e of allEvents(D)) if (e.type === "死" && !(e.who in died)) died[e.who] = e;
      S = { D, walk, T, W, renderer, camera, controls, figs, labels, vlabels, tlabels, featured: {}, v: 0, speed: 1, playing: true, loadYear: loadYear || null, years: {}, died,
        clock: stage.querySelector(".r3-clock"), toast: stage.querySelector(".r3-toast"),
        playBtn: root.querySelector("#r3-play"), slider: root.querySelector("#r3-slider"), follow: "" };
      const days = allDays(D);
      const daySel = root.querySelector("#r3-day");
      daySel.innerHTML = days.map((d) => `<option value="${d}">${dayLabel(d)}</option>`).join("") || `<option>―</option>`;
      const fol = root.querySelector("#r3-follow");
      fol.innerHTML += D.people.map((p) => `<option>${esc(p.name)}</option>`).join("");
      const resize = () => { const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
      S.ro = new ResizeObserver(resize); S.ro.observe(stage); resize();
      S.playBtn.addEventListener("click", () => {
        if (S.v >= S.day.total) S.v = 0;
        S.playing = !S.playing; S.playBtn.textContent = S.playing ? "一時停止" : "再生";
      });
      S.slider.addEventListener("input", () => { S.v = Number(S.slider.value) * S.day.total; });
      daySel.addEventListener("change", () => {
        const d = Number(daySel.value);
        if (oldYear(D, d) !== null && !S.years[oldYear(D, d)]) S.clock.textContent = `${dayLabel(d)} の記録を読み込んでいます…`;
        this.need([d]).then(() => { if (S && Number(daySel.value) === d) setDay(d); })
          .catch((e) => { if (S) S.clock.textContent = `${dayLabel(d)} の記録を読み込めませんでした (${e.message})`; });
      });
      root.querySelector("#r3-speed").addEventListener("change", (e) => (S.speed = Number(e.target.value)));
      fol.addEventListener("change", (e) => { S.follow = e.target.value; if (!S.follow) S.controls.target.copy(W.camp); });
      if (!days.length) { S.clock.textContent = "まだ再生できる日がありません"; return; }
      daySel.value = String(days[days.length - 1]);
      setDay(days[days.length - 1]);
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) { S.playing = false; S.playBtn.textContent = "再生"; S.v = S.day.segs[2].v0 + 4; }
      S.raf = requestAnimationFrame(loop);
    },
    // しまった年の日を見る前に、その年のファイルを読む (動画を撮るときは、撮る日をまとめて先に読む)
    need(days) {
      if (!S) return Promise.resolve();
      const ys = [...new Set(days.map((d) => oldYear(S.D, d)).filter((y) => y !== null && !S.years[y]))];
      if (ys.length && !S.loadYear) return Promise.reject(new Error("しまった年のファイルを読めない"));
      const s = S;
      return Promise.all(ys.map((y) => s.loadYear(y).then((r) => { s.years[y] = r; }))).then(() => undefined);
    },
    // 動画を作るとき用: 日と再生位置 (秒) を指定して 1 コマ描く
    setAutoCamera(on) { if (S) S.autoCam = !!on; },
    // 動画用 (2026-11-22): 混んだ日に名前を見せる人 (その日のナレーションに出る人)。namesIn(文) は、文の中に出る村の人の名前
    // 絵コンテ (storyboard.mjs、2026-11-23) 用: 今の絵のカメラと、人ごとの画面の上の場所・名前の札の四角・活動。読むだけ (絵は変えない)
    inspect() {
      if (!S) return null;
      const r = S.renderer.domElement.getBoundingClientRect(), px = (v) => { const p = v.clone().project(S.camera); return [(p.x * 0.5 + 0.5) * r.width, (-p.y * 0.5 + 0.5) * r.height, p.z]; };
      const motion = (S.people && S.people.clips && S.people.clips()) || {};
      const people = Object.keys(S.figs).map((n) => {
        const f = S.figs[n], L = S.labels[n], plan = S.day && S.day.plan[n];
        const head = L && L.pos ? px(L.pos) : px(f.position.clone().add(new THREE.Vector3(0, 1.7 * K, 0)));
        const foot = px(f.position), el = L && L.el, lr = el && !el.hidden ? el.getBoundingClientRect() : null;
        return { name: n, shown: !!(plan && plan.alive) && (f.visible || !!motion[n]), activity: plan ? plan.activity : null, motion: motion[n] || null,
          head, foot, label: lr ? [lr.left, lr.top, lr.right, lr.bottom] : null, bubble: !!(L && L.bubble) };
      });
      const cam = S.camera.position, tg = S.controls.target;
      return { w: r.width, h: r.height, camera: { pos: cam.toArray(), target: tg.toArray(), dist: cam.distanceTo(tg) / K }, people,
        featured: [...((S.featured && S.featured[S.dayNum]) || [])] };
    },
    setFeatured(day, names) { if (S) S.featured[day] = new Set(names); },
    namesIn(text) {
      if (!S) return [];
      const t = String(text || "");
      return S.D.people.map((p) => p.name).filter((n) => { const i = t.indexOf(n); return i >= 0 && !/[0-9０-９]/.test(t[i + n.length] || ""); });
    },
    // 動画用 (2026-11-23、D1P): 棒の人の代わりに人のモデルを動かす (replay3d_people.js の Replay3DPeople)。init を 1 回、frame(その日の見せ方, 秒) をコマごとに呼ぶ
    setPeople(hooks) {
      if (!S) return;
      S.people = hooks;
      hooks.init({ K, scene: S.W.scene, figs: S.figs, labels: S.labels, D: S.D, w2t: (x, y) => w2t(S.D, x, y) });
    },
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
