// Verladearm HETA – interaktive Erklärseite (intern). Maße aus vision/config/anlagen/heta_prototyp.yaml.
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';

const A = {base: 6.936, inner: 2.4, drop: 0.446, outer: 2.7, outlet: 3.7};
const RIM = 3.6 - A.base, DOM = {x: 3.2, y: 0}, DEPTH = 2.1, TANK_R = 1.1;
const TANK_BOT = RIM - 2.32, SENSOR = 0.12, STEP = 0.05;
const rad = (d) => d * Math.PI / 180, deg = (r) => r * 180 / Math.PI;
const PARK = [rad(70), rad(-135), rad(10)];

// Vorwärtsrechnung (vereinfacht): J1 dreht, innerer Ausleger, Fallrohr, J2 dreht, J3 hebt, Auslass hängt senkrecht
function fk([q1, q2, q3]) {
  const j2 = [A.inner * Math.cos(q1), A.inner * Math.sin(q1), -A.drop];
  const r = A.outer * Math.cos(q3);
  const e = [j2[0] + r * Math.cos(q1 + q2), j2[1] + r * Math.sin(q1 + q2), j2[2] + A.outer * Math.sin(q3)];
  return {j2, e, tip: [e[0], e[1], e[2] - A.outlet]};
}
// Rückwärtsrechnung für eine Auslassspitze (x, y, z)
function ik(x, y, z, elbow = -1) {
  const q3 = Math.asin((z + A.outlet + A.drop) / A.outer);
  const L2 = A.outer * Math.cos(q3), d = Math.hypot(x, y);
  const c = (d * d - A.inner ** 2 - L2 * L2) / (2 * A.inner * L2);
  const q2 = elbow * Math.acos(Math.max(-1, Math.min(1, c)));
  const q1 = Math.atan2(y, x) - Math.atan2(L2 * Math.sin(q2), A.inner + L2 * Math.cos(q2));
  return [q1, q2, q3];
}
const ABOVE = ik(DOM.x, DOM.y, RIM + 0.35), IN = (z) => ik(DOM.x, DOM.y, z);
const lerp = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u);
const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - (-2 * u + 2) ** 3 / 2);
const clamp = (u) => Math.max(0, Math.min(1, u));

// Ablauf: [Ende in s, Name]
const STEPS = [[3, 'Bereit – Fahrzeug steht, Start'], [6, 'Job 1: Kamera misst den Dom'], [12, 'Anfahrt über den Dom'],
  [14, 'Job 2: Auslass nachmessen'], [18, 'Eintauchen, Abdeckung setzt auf'], [19, 'Klappe auf – „Arm bereit“'],
  [33, 'Befüllung (Leitstelle), Arm zieht nach'], [35, 'Füllende: Pumpe aus, Spülen'], [37, 'Klappe zu, Abtropfen'],
  [41, 'Heraus, Pendelwanne schließt'], [47, 'Rückfahrt in die Parkstellung']];
const T = STEPS.at(-1)[0];
const t0 = (i) => (i ? STEPS[i - 1][0] : 0);
const FILL_END = TANK_BOT + 1.95; // Spiegel am Ende (95 %)

function state(t) {
  const i = STEPS.findIndex(([e]) => t < e), s = i < 0 ? STEPS.length - 1 : i;
  const u = clamp((t - t0(s)) / (STEPS[s][0] - t0(s)));
  let q = PARK, level = TANK_BOT + 0.03, klappe = false, pumpe = false, scan = 0, lifts = 0, spuelen = false;
  const fu = clamp((t - 19) / 14), lvl = TANK_BOT + 0.03 + (FILL_END - TANK_BOT - 0.03) * fu;
  const tipFor = (L) => { // Nachziehen: nass bei Spiegel ≥ Spitze + Sensor -> Hub 5 cm
    let z = RIM - DEPTH, n = 0;
    while (L >= z + SENSOR) { z += STEP; n++; }
    return [z, n];
  };
  if (s === 1) scan = u;
  if (s === 2) q = lerp(PARK, ABOVE, ease(u));
  if (s === 3) q = ABOVE;
  if (s === 4) q = IN(RIM + 0.35 - (0.35 + DEPTH) * ease(u));
  if (s >= 5 && s <= 8) {
    level = s >= 6 ? lvl : level; const [z, n] = tipFor(level); q = IN(z); lifts = n;
    klappe = s >= 5 && s <= 7; pumpe = s === 6; spuelen = s === 7;
  }
  if (s === 9) { level = FILL_END; const [z] = tipFor(level); q = IN(z + (RIM + 0.35 - z) * ease(u)); }
  if (s === 10) { level = FILL_END; q = lerp(ABOVE, PARK, ease(u)); }
  if (s > 8) level = FILL_END;
  return {s, q, level, klappe, pumpe, scan, lifts, spuelen, fill: (level - TANK_BOT) / (2 * TANK_R)};
}

// --- Szene (three: y oben; Arm: z oben) ---
const P = (x, y, z) => new THREE.Vector3(x, z, -y);
const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.shadowMap.enabled = true; app.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xeef1f4);
const cam = new THREE.PerspectiveCamera(40, 1, 0.1, 200); cam.position.set(9, 3, 11);
const ctl = new OrbitControls(cam, renderer.domElement); ctl.target.set(2, -3, 0); ctl.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0xb8c0c8, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 2); sun.position.set(6, 12, 8); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, {left: -10, right: 10, top: 10, bottom: -10}); scene.add(sun);
const M = (c, o = {}) => new THREE.MeshStandardMaterial({color: c, roughness: 0.55, metalness: 0.3, ...o});
const steel = M(0xb9c2cc), dark = M(0x4a5560), accent = M(0xe8590c, {emissive: 0xe8590c, emissiveIntensity: 0.25});
const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), M(0xd9dee3, {metalness: 0}));
ground.rotation.x = -Math.PI / 2; ground.position.y = -A.base; ground.receiveShadow = true; scene.add(ground);

function tube(a, b, r, mat) { // Rohr zwischen zwei Armpunkten
  const pa = P(...a), pb = P(...b), m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 1, 20), mat);
  m.castShadow = true; scene.add(m); m.userData.set = (a2, b2) => {
    const x = P(...a2), y = P(...b2); m.position.copy(x).add(y).multiplyScalar(0.5);
    m.scale.set(1, x.distanceTo(y), 1); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), y.clone().sub(x).normalize());
  }; m.userData.set(a, b); return m;
}
// Gerüst und feste Leitung
tube([0, 0, 0.6], [0, 0, 1.6], 0.09, dark); tube([-1.5, 0, 1.6], [0, 0, 1.6], 0.09, dark);
const ballJ = (mat) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.17, 20, 14), mat); scene.add(m); return m; };
const gJ1 = ballJ(accent), gJ2 = ballJ(accent), gJ3 = ballJ(accent);
const inner = tube([0, 0, 0], [1, 0, 0], 0.075, steel), dropT = tube([1, 0, 0], [1, 0, -1], 0.075, steel);
const outer = tube([1, 0, 0], [2, 0, 0], 0.075, steel), outlet = tube([2, 0, 0], [2, 0, -1], 0.07, steel);
const klappeM = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.12, 20), M(0x2b8a3e)); scene.add(klappeM);
const cover = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.34, 0.04, 32), dark); cover.castShadow = true; scene.add(cover);
const tray = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.05, 0.3), M(0x1971c2)); scene.add(tray);
// Tankwagen (Fahrtrichtung +y), 3 Dome
const tankMat = M(0xdfe5ea, {transparent: true, opacity: 0.35, metalness: 0.1, side: THREE.DoubleSide, depthWrite: false});
const tank = new THREE.Mesh(new THREE.CylinderGeometry(TANK_R, TANK_R, 8, 40, 1, true), tankMat);
tank.rotation.x = Math.PI / 2; tank.position.copy(P(DOM.x, 0.5, TANK_BOT + TANK_R)); scene.add(tank);
const cab = new THREE.Mesh(new THREE.BoxGeometry(2.4, 2.6, 2), M(0x495057)); cab.position.copy(P(DOM.x, 5.6, -A.base + 1.6)); scene.add(cab);
for (const y of [2.5, 0, -2.5]) {
  const d = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.24, 32, 1, true), M(0x868e96, {side: THREE.DoubleSide}));
  d.position.copy(P(DOM.x, y, RIM - 0.12)); scene.add(d);
}
const liquid = new THREE.Mesh(new THREE.PlaneGeometry(1, 2.5), M(0x74c0fc, {metalness: 0, roughness: 0.2, transparent: true, opacity: 0.85, side: THREE.DoubleSide}));
liquid.rotation.x = -Math.PI / 2;
scene.add(liquid);
const camBox = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.15, 0.2), dark); camBox.position.copy(P(DOM.x, 0, 1.2)); scene.add(camBox);
const cone = new THREE.Mesh(new THREE.ConeGeometry(2.6, 4.6, 40, 1, true), new THREE.MeshBasicMaterial({color: 0xe8590c, transparent: true, opacity: 0.12, side: THREE.DoubleSide}));
cone.position.copy(P(DOM.x, 0, 1.2 - 2.3)); scene.add(cone);

// --- Bedienoberfläche ---
const el = (h) => { const d = document.createElement('div'); d.innerHTML = h; document.body.appendChild(d.firstElementChild); return document.body.lastElementChild; };
const info = el(`<div id="info" class="pan"><h1>Autonomer Verladearm</h1><div class="hsub">HETA · Prototyp · intern</div><div id="vals"></div></div>`);
const stepP = el(`<div id="step" class="pan">Schritt<div class="cur"></div><ol>${STEPS.map((s) => `<li>${s[1]}</li>`).join('')}</ol></div>`);
const ctlP = el(`<div id="ctl" class="pan"><button id="pp">Pause</button><input id="tl" type="range" min="0" max="${T}" step="0.05"><button id="x">Tank aus</button></div>`);
let t = 0, play = true, last = performance.now();
const tl = ctlP.querySelector('#tl'), pp = ctlP.querySelector('#pp');
pp.onclick = () => { play = !play; pp.textContent = play ? 'Pause' : 'Weiter'; };
tl.oninput = () => { t = +tl.value; play = false; pp.textContent = 'Weiter'; };
ctlP.querySelector('#x').onclick = (e) => { tank.visible = !tank.visible; e.target.textContent = tank.visible ? 'Tank aus' : 'Tank ein'; };
stepP.querySelectorAll('li').forEach((li, i) => { li.style.cursor = 'pointer'; li.onclick = () => { t = t0(i) + 0.01; }; });

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (play) t = (t + dt) % T;
  const S = state(t), {j2, e, tip} = fk(S.q);
  gJ1.position.copy(P(0, 0, 0)); gJ2.position.copy(P(...j2)); gJ3.position.copy(P(j2[0], j2[1], j2[2]));
  inner.userData.set([0, 0, 0], [j2[0], j2[1], 0]); dropT.userData.set([j2[0], j2[1], 0], j2);
  outer.userData.set(j2, e); outlet.userData.set(e, tip); gJ2.position.copy(P(j2[0], j2[1], 0));
  klappeM.position.copy(P(e[0], e[1], e[2] - 0.35)); klappeM.material.color.set(S.klappe ? 0x2b8a3e : 0xc92a2a);
  const coverZ = Math.max(tip[2] + 1.2, RIM + 0.02); // Abdeckung gleitet am Rohr, setzt auf dem Dom auf
  cover.position.copy(P(tip[0], tip[1], coverZ));
  const open = tip[2] < RIM - 0.05; // Pendelwanne vom Rohrende aufgeschoben
  tray.position.copy(P(tip[0] + (open ? 0.35 : 0), tip[1], tip[2] - 0.12 + (open ? 0.25 : 0)));
  tray.rotation.z = open ? 1.3 : 0;
  const hh = S.level - TANK_BOT; liquid.visible = hh > 0.02; // Spiegel: Sehnenbreite im liegenden Zylinder
  liquid.scale.x = 2 * Math.sqrt(Math.max(0.0001, TANK_R ** 2 - (TANK_R - hh) ** 2)); liquid.position.copy(P(DOM.x, 0, S.level));
  cone.visible = S.scan > 0 || S.s === 3; cone.material.opacity = 0.1 + 0.08 * Math.sin(now / 120);
  const q = S.q.map(deg);
  info.querySelector('#vals').innerHTML = [
    ['J1 drehen', q[0].toFixed(1) + '°'], ['J2 drehen', q[1].toFixed(1) + '°'], ['J3 heben', q[2].toFixed(1) + '°'],
    ['Auslass unter Rand', (RIM - tip[2]).toFixed(2) + ' m'], ['Füllstand', Math.round(S.fill * 100) + ' %'],
    ['Nachzieh-Hübe', S.lifts], ['Klappe', S.klappe ? '<span class=on>AUF</span>' : 'zu'],
    ['Pumpe (Leitstelle)', S.pumpe ? '<span class=on>läuft</span>' : 'aus'], ['Spülen', S.spuelen ? '<span class=on>aktiv</span>' : '–'],
  ].map(([k, v]) => `<div class="row"><span>${k}</span><span>${v}</span></div>`).join('');
  stepP.querySelector('.cur').textContent = STEPS[S.s][1];
  stepP.querySelectorAll('li').forEach((li, i) => li.classList.toggle('a', i === S.s));
  if (play) tl.value = t;
  ctl.update(); renderer.render(scene, cam); requestAnimationFrame(frame);
}
function resize() { renderer.setSize(innerWidth, innerHeight); cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); }
addEventListener('resize', resize); resize(); requestAnimationFrame(frame);
