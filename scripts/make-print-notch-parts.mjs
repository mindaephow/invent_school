// 이미 만든 새 규격 부품(기타부품_새규격)의 둥근 구멍 목 구간(지름 6.10)에 홈 8곳을 판다 — 사용자 2026-10-23 "홀을 사용하는 건 다 8곳 컷팅".
//   node scripts/make-print-notch-parts.mjs [저장 폴더]   (입력: 다운로드/큐보_3D모델_프린트용/기타부품_새규격/출력용-큰기어_*·작은바퀴_본체_*.stl, 환경변수 NOTCH(기본 8)·NOTCH_W(0.8)·NOTCH_D(0.3))
// DB 3D 파일(import) 부품을 출력용 규격으로 고쳐 만든다(3D 불리언, manifold-3d).
//   규칙(사용자 2026-10-23): ① 축·T축이 들어가는 열십자 구멍은 작은기어의 열십자 그대로 ② 축이 들어가는 둥근 구멍은 프레임 구멍 규격(목 6.10·입구 7.7·입구 깊이 1.1) 그대로
//   node scripts/make-print-parts.mjs [저장 폴더]      (입력: 다운로드/큐보_3D모델_프린트용/기타부품/출력용-*_원본(보정없음).stl — export-print-parts.mjs 가 만든다 — 와 큐보_3D모델/작은기어.stl)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import Module from 'manifold-3d'
const wasm = await Module(); wasm.setup(); const { Manifold, Mesh } = wasm
const home = path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용'), src = path.join(home, '기타부품_새규격'), out = process.argv[2] || path.join(home, '기타부품_홈8')
fs.mkdirSync(out, { recursive: true })
const NECK_R = 3.05, ENTRY_R = 3.85, RIM_H = 1.1, SEG = 64, EPS = 0.05
const NOTCH = Number(process.env.NOTCH || 8), NOTCH_W = Number(process.env.NOTCH_W || 0.8), NOTCH_D = Number(process.env.NOTCH_D || 0.3)
const loadStl = (p) => { const b = fs.readFileSync(p), n = b.readUInt32LE(80), vp = new Float32Array(n * 9), tv = new Uint32Array(n * 3)
  for (let i = 0; i < n; i++) for (let v = 0; v < 3; v++) { for (let k = 0; k < 3; k++) vp[i * 9 + v * 3 + k] = b.readFloatLE(84 + i * 50 + 12 + v * 12 + k * 4); tv[i * 3 + v] = i * 3 + v }
  const m = new Mesh({ numProp: 3, vertProperties: vp, triVerts: tv }); m.merge(); return new Manifold(m) }
const saveStl = (name, m) => { const mesh = m.getMesh(), v = mesh.vertProperties, n = mesh.numProp, t = mesh.triVerts, buf = Buffer.alloc(84 + (t.length / 3) * 50); buf.writeUInt32LE(t.length / 3, 80)
  const P = (i) => [v[i * n], v[i * n + 1], v[i * n + 2]]
  for (let f = 0; f < t.length / 3; f++) { const a = P(t[f * 3]), b = P(t[f * 3 + 1]), c = P(t[f * 3 + 2]), u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [c[0] - a[0], c[1] - a[1], c[2] - a[2]]
    let nx = u[1] * w[2] - u[2] * w[1], ny = u[2] * w[0] - u[0] * w[2], nz = u[0] * w[1] - u[1] * w[0]; const l = Math.hypot(nx, ny, nz) || 1
    ;[nx / l, ny / l, nz / l, ...a, ...b, ...c].forEach((q, k) => buf.writeFloatLE(q, 84 + f * 50 + k * 4)) }
  fs.writeFileSync(path.join(out, name), buf); return t.length / 3 }
const area = (p) => p.reduce((s, q, i) => { const r = p[(i + 1) % p.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) / 2
const bb = (p) => { const xs = p.map((q) => q[0]), ys = p.map((q) => q[1]); return { w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys), cx: (Math.max(...xs) + Math.min(...xs)) / 2, cy: (Math.max(...ys) + Math.min(...ys)) / 2 } }
const cyl = (x, y, z0, h, r) => Manifold.cylinder(h, r, r, SEG, false).translate([x, y, z0])
// 한 z 높이에서 (cx,cy) 가운데 구멍 모양(중심이 cx,cy 에서 0.5 안, 너비 25 미만 구멍) — 구멍은 시계 방향이라 넓이가 음수
const holeAt = (M, z, cx, cy) => { const out = []; for (const p of M.slice(z).toPolygons()) { const b = bb(p); if (Math.hypot(b.cx - cx, b.cy - cy) < 0.5 && b.w < 25 && area(p) < 0) out.push({ p, b, a: Math.abs(area(p)) }) } return out.sort((x, y) => x.a - y.a)[0] || null }
const sig = (h) => (h ? h.a.toFixed(1) : '-')
// 가운데(또는 (cx,cy)) 구멍이 같은 모양인 높이 구간들 — 모양이 바뀌는 높이는 이분법으로 0.005 까지 찾는다
function ranges(M, cx, cy, z0, z1) { const N = 60, zs = Array.from({ length: N + 1 }, (_, k) => z0 + 0.003 + ((z1 - z0 - 0.006) * k) / N), out = []; let cur = null
  const edge = (za, zb) => { let a = za, b = zb; const sa = sig(holeAt(M, a, cx, cy)); for (let i = 0; i < 14; i++) { const m = (a + b) / 2; if (sig(holeAt(M, m, cx, cy)) === sa) a = m; else b = m } return (a + b) / 2 }
  for (let k = 0; k <= N; k++) { const h = holeAt(M, zs[k], cx, cy), s = sig(h); if (!cur || cur.s !== s) { if (cur) { const e = edge(zs[k - 1], zs[k]); cur.z1 = e; out.push(cur); cur = { s, z0: e, h } } else cur = { s, z0: z0, h } } else cur.h = h }
  cur.z1 = z1; out.push(cur); return out }
const SPEC = '목6.10_입구7.7_입구깊이1.1_열십자작은기어'
for (const [key, file] of [['큰기어', '출력용-큰기어_' + SPEC + '.stl'], ['작은바퀴_본체', '출력용-작은바퀴_본체_' + SPEC + '.stl']]) {
  let M = loadStl(path.join(src, file)); const M0 = M, b = M0.boundingBox(), cx = (b.min[0] + b.max[0]) / 2, cy = (b.min[1] + b.max[1]) / 2, z0 = b.min[2], z1 = b.max[2], rep = []
  for (const [dx, dy] of [[10, 0], [-10, 0], [0, 10], [0, -10]]) {
    for (const r of ranges(M0, cx + dx, cy + dy, z0, z1)) { if (!r.h || Math.abs(r.h.b.w - r.h.b.h) > 0.05 || Math.abs(r.h.b.w - 6.1) > 0.06 || r.z1 - r.z0 < 0.3) continue   // 목(지름 6.10) 구간만
      for (let k = 0; k < NOTCH / 2; k++) M = M.subtract(Manifold.cube([2 * (NECK_R + NOTCH_D), NOTCH_W, r.z1 - r.z0 + 0.01], true).rotate([0, 0, (180 / (NOTCH / 2)) * k]).translate([cx + dx, cy + dy, (r.z0 + r.z1) / 2]))
      rep.push(`(${dx},${dy}) z ${(r.z0 - z0).toFixed(2)}~${(r.z1 - z0).toFixed(2)}`) } }
  const name = file.replace('.stl', `+홈${NOTCH}.stl`)
  console.log(key, M.status(), '부피', M0.volume().toFixed(0), '→', M.volume().toFixed(0), '목 구간', rep.length, rep.join(' | ')); console.log('   저장', name, saveStl(name, M), '삼각형')
}
