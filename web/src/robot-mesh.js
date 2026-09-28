// ロボットの見た目 (Three.js)。デモ画面 (main.js) と動画 (film.js) で共通。
import * as THREE from 'three';

export function createRobotMeshFactory(config) {
  const legMat = new THREE.MeshStandardMaterial({ color: 0x2b2f36, roughness: 0.6 });
  const footMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
  const hipGeo = new THREE.SphereGeometry(0.04, 16, 12);
  const thighGeo = new THREE.CapsuleGeometry(config.thighRadius, config.thighLength, 6, 12);
  const calfGeo = new THREE.CapsuleGeometry(config.calfRadius, config.calfLength - config.calfRadius * 2, 6, 10);
  const footGeo = new THREE.SphereGeometry(config.footRadius, 12, 10);
  const trunkGeo = new THREE.BoxGeometry(config.trunkWidth, config.trunkHeight, config.trunkLength);
  const faceGeo = new THREE.BoxGeometry(config.trunkWidth * 0.6, config.trunkHeight * 0.4, 0.012);

  /** robot の各リンクに対応する Group の配列を作って scene に追加する */
  function create(scene, robot, color) {
    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.1 });
    return robot.links.map((l) => {
      const g = new THREE.Group();
      if (l.kind === 'trunk') {
        g.add(new THREE.Mesh(trunkGeo, bodyMat));
        const face = new THREE.Mesh(faceGeo, footMat);
        face.position.set(0, 0.01, config.trunkLength / 2 + 0.006);
        g.add(face);
      } else if (l.kind === 'hip') g.add(new THREE.Mesh(hipGeo, legMat));
      else if (l.kind === 'thigh') { const m = new THREE.Mesh(thighGeo, bodyMat); m.position.y = -config.thighLength / 2; g.add(m); }
      else {
        const m = new THREE.Mesh(calfGeo, legMat); m.position.y = -config.calfLength / 2; g.add(m);
        const f = new THREE.Mesh(footGeo, footMat); f.position.y = -config.calfLength; g.add(f);
      }
      g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
      scene.add(g);
      return g;
    });
  }
  return { create };
}

export function syncRobotMeshes(robot, meshes) {
  robot.links.forEach((l, i) => {
    const p = l.body.translation(), q = l.body.rotation();
    meshes[i].position.set(p.x, p.y, p.z);
    meshes[i].quaternion.set(q.x, q.y, q.z, q.w);
  });
}
