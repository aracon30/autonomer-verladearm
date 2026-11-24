// Punktwolken-Betrachter (offline): .ply (aus tools/npy_zu_ply.py) oder .npy (Aufnahme) per Datei-Auswahl oder Drag & Drop.
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {PLYLoader} from 'three/examples/jsm/loaders/PLYLoader.js';

document.body.insertAdjacentHTML('beforeend', `<div id="bar"><b>Punktwolke</b><br>
<input type="file" id="f" accept=".ply,.npy"> <br>Punktgröße <input type="range" id="ps" min="1" max="8" value="2">
<label><input type="checkbox" id="flip"> 180° drehen</label>
<br>Farbe <label><input type="radio" name="fm" id="fmd" checked> Abstand</label> <label><input type="radio" name="fm" id="fmi"> Infrarot</label>
<br><button id="ex" disabled>Export für ReCap/Inventor (.pts)</button><div id="info">Datei wählen oder hierher ziehen.
Maus: links drehen, rechts schieben, Rad zoomen.
Doppelklick auf Punkt: Abstand zur Kamera.</div></div><div id="drop">.ply oder .npy hierher ziehen</div>`);
const r = new THREE.WebGLRenderer({antialias: true}); r.setPixelRatio(devicePixelRatio); document.getElementById('app').appendChild(r.domElement);
const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(55, 1, 0.01, 100); cam.position.set(0, 0, -0.5); cam.up.set(0, -1, 0);
const ctl = new OrbitControls(cam, r.domElement); ctl.target.set(0, 0, 3);
scene.add(new THREE.AxesHelper(0.5));
let pts = null; const info = document.getElementById('info');
const ramp = (t) => { const k = [[40,60,200],[40,170,220],[60,190,90],[240,210,40],[220,60,40]]; t = Math.min(1, Math.max(0, t)) * 4; const i = Math.min(3, t | 0), f = t - i; return k[i].map((v, j) => (v + (k[i+1][j] - v) * f) / 255); };
let ir = null; // Infrarot je Punkt (4. Spalte der .npy-Aufnahme)
const pct = (a, q) => { const s = Float32Array.from(a).sort(); return s[Math.floor((s.length - 1) * q)]; };
function colorize(geo) {
  const p = geo.attributes.position.array, n = p.length / 3, c = new Float32Array(n * 3);
  if (fmi.checked && ir) { const lo = pct(ir, 0.01), hi = pct(ir, 0.99) || 1;
    for (let i = 0; i < n; i++) { const g = Math.min(1, Math.max(0, (ir[i] - lo) / (hi - lo))); c[3*i] = c[3*i+1] = c[3*i+2] = 0.08 + 0.92 * g; }
  } else { const d = new Float32Array(n); for (let i = 0; i < n; i++) d[i] = Math.hypot(p[3*i], p[3*i+1], p[3*i+2]);
    const mx = pct(d, 0.98) || 1; for (let i = 0; i < n; i++) c.set(ramp(d[i] / mx), 3 * i); }
  geo.setAttribute('color', new THREE.BufferAttribute(c, 3));
}
function show(geo) {
  if (pts) scene.remove(pts);
  const n = geo.attributes.position.count;
  if (!geo.userData.plyColor) colorize(geo);
  fmi.disabled = !ir;
  pts = new THREE.Points(geo, new THREE.PointsMaterial({size: +ps.value, sizeAttenuation: false, vertexColors: true}));
  pts.rotation.z = flip.checked ? Math.PI : 0; scene.add(pts);
  geo.computeBoundingSphere(); const c = geo.boundingSphere.center; ctl.target.copy(c); cam.position.set(c.x, c.y, -0.5);
  info.textContent = `${n.toLocaleString('de-DE')} Punkte${ir ? ' · mit Infrarot' : ' · ohne Infrarot'}\nMitte ${c.toArray().map((v) => v.toFixed(2)).join(' / ')} m\nDoppelklick: Abstand messen`;
}
function npy(buf) { // einfacher .npy-Leser (float32/float64, C-Ordnung)
  const dv = new DataView(buf), hl = dv.getUint16(8, true), h = new TextDecoder().decode(new Uint8Array(buf, 10, hl));
  const shape = h.match(/\((\d+),\s*(\d+)\)/).map(Number).slice(1), off = 10 + hl;
  const src = h.includes('<f8') ? new Float64Array(buf.slice(off)) : new Float32Array(buf.slice(off)); const out = new Float32Array(shape[0] * 3);
  for (let i = 0; i < shape[0]; i++) for (let j = 0; j < 3; j++) out[3*i+j] = src[i*shape[1]+j];
  ir = shape[1] >= 4 ? Float32Array.from({length: shape[0]}, (_, i) => src[i*shape[1]+3]) : null;
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(out, 3)); return g;
}
async function load(file) { const b = await file.arrayBuffer(); let g;
  if (file.name.endsWith('.npy')) g = npy(b); else { ir = null; g = new PLYLoader().parse(b); g.userData.plyColor = !!g.attributes.color; }
  fname = file.name; show(g); ex.disabled = false; document.getElementById('drop').style.display = 'none'; document.title = file.name; }
f.onchange = () => f.files[0] && load(f.files[0]);
addEventListener('dragover', (e) => e.preventDefault()); addEventListener('drop', (e) => { e.preventDefault(); e.dataTransfer.files[0] && load(e.dataTransfer.files[0]); });
let fname = 'punktwolke';
ex.onclick = () => { // Leica-PTS: Anzahl, dann x y z [mm] Intensität r g b – ReCap liest es, Inventor hängt das .rcp an
  const g = pts.geometry, p = g.attributes.position.array, c = g.attributes.color.array, n = p.length / 3, rows = [String(n)];
  for (let i = 0; i < n; i++) { const r = Math.round(c[3*i] * 255), gg = Math.round(c[3*i+1] * 255), b = Math.round(c[3*i+2] * 255);
    rows.push(`${(p[3*i]*1000).toFixed(1)} ${(p[3*i+1]*1000).toFixed(1)} ${(p[3*i+2]*1000).toFixed(1)} ${Math.round((r+gg+b)/3)*8-1024} ${r} ${gg} ${b}`); }
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([rows.join('\n') + '\n'], {type: 'text/plain'}));
  a.download = fname.replace(/\.(npy|ply)$/i, '') + '.pts'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
};
fmd.onchange = fmi.onchange = () => { if (pts) { colorize(pts.geometry); } };
ps.oninput = () => pts && (pts.material.size = +ps.value); flip.onchange = () => pts && (pts.rotation.z = flip.checked ? Math.PI : 0);
const ray = new THREE.Raycaster(); ray.params.Points.threshold = 0.02;
r.domElement.ondblclick = (e) => { if (!pts) return; ray.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -e.clientY / innerHeight * 2 + 1), cam);
  const h = ray.intersectObject(pts)[0]; if (h) { const q = h.point; info.textContent = `Punkt ${q.toArray().map((v) => v.toFixed(3)).join(' / ')} m\nAbstand zur Kamera ${q.length().toFixed(3)} m`; } };
const size = () => { r.setSize(innerWidth, innerHeight); cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); }; addEventListener('resize', size); size();
r.setAnimationLoop(() => { ctl.update(); r.render(scene, cam); });
