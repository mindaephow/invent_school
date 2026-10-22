// DB 3D 파일(import) 부품을 출력용 규격으로 고쳐 만든다(3D 불리언, manifold-3d).
//   규칙(사용자 2026-10-23): ① 축·T축이 들어가는 열십자 구멍은 작은기어의 열십자 그대로 ② 축이 들어가는 둥근 구멍은 프레임 구멍 규격(목 6.10·입구 7.7·입구 깊이 1.1) 그대로
//   node scripts/make-print-parts.mjs [저장 폴더]      (입력: 다운로드/큐보_3D모델_프린트용/기타부품/출력용-*_원본(보정없음).stl — export-print-parts.mjs 가 만든다 — 와 큐보_3D모델/작은기어.stl)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import Module from 'manifold-3d'
const wasm = await Module(); wasm.setup(); const { Manifold, Mesh } = wasm
const home = path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용'), src = path.join(home, '기타부품'), out = process.argv[2] || path.join(home, '기타부품_새규격')
fs.mkdirSync(out, { recursive: true })
const NECK_R = 3.05, ENTRY_R = 3.85, RIM_H = 1.1, SEG = 64, EPS = 0.05
const SPEC = '목6.10_입구7.7_입구깊이1.1_열십자작은기어'
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
// 새 열십자: 작은기어 가운데 구멍(작은기어는 한 가지 모양)
const gear = loadStl(path.join(os.homedir(), 'Downloads', '큐보_3D모델', '작은기어.stl')), gb = gear.boundingBox(), gcx = (gb.min[0] + gb.max[0]) / 2, gcy = (gb.min[1] + gb.max[1]) / 2
const gh = holeAt(gear, (gb.min[2] + gb.max[2]) / 2, gcx, gcy)
const CROSS = gh.p.map(([x, y]) => [x - gh.b.cx, y - gh.b.cy]).reverse() // 반시계(양수 넓이)
console.log('작은기어 열십자: 넓이', gh.a.toFixed(2), '크기', gh.b.w.toFixed(2) + '×' + gh.b.h.toFixed(2), '점', CROSS.length)
const prism = (poly, cx, cy, za, zb) => Manifold.extrude([poly.map(([x, y]) => [x + cx, y + cy])], zb - za).translate([0, 0, za])
const report = []
function fixCross(M, cx, cy, z0, z1) { // 열십자 구간(가로·세로 6.4 안팎)이 작은기어 열십자와 다르면 채우고 다시 판다
  for (const r of ranges(M, cx, cy, z0, z1)) { if (!r.h || Math.abs(r.h.b.w - 6.4) > 0.3 || Math.abs(r.h.b.h - 6.4) > 0.3 || Math.abs(r.h.a - gh.a) < 0.05) continue
    const old = r.h.p.slice().reverse().map(([x, y]) => [x - cx, y - cy]); const za = r.z0 - EPS * 0, zb = r.z1
    M = M.add(prism(old, cx, cy, za, zb)).subtract(prism(CROSS, cx, cy, za - 0.001, zb + 0.001)); report.push(`열십자 z ${(za - z0).toFixed(2)}~${(zb - z0).toFixed(2)}: 넓이 ${r.h.a.toFixed(1)} → ${gh.a.toFixed(1)}`) }
  return M }
function fixRound(M0, M, cx, cy, z0, z1) { // 둥근 구멍은 높이 구간마다 지름을 바꾼다: 입구(지름 약 8.0) → 7.7, 목(지름 약 6.2) → 6.10. 구간은 원래 3D 파일의 구멍 모양 그대로(막힌 구멍·한쪽만 입구인 구멍도 그대로).
  for (const r of ranges(M0, cx, cy, z0, z1)) { if (!r.h || Math.abs(r.h.b.w - r.h.b.h) > 0.05 || Math.abs(r.h.a / (Math.PI * r.h.b.w * r.h.b.w / 4) - 1) > 0.03 || r.h.b.w < 5.9 || r.h.b.w > 8.2) continue
    const rOld = r.h.b.w / 2, rNew = r.h.b.w > 7 ? ENTRY_R : NECK_R
    M = M.add(prism(r.h.p.slice().reverse().map(([x, y]) => [x - cx, y - cy]), cx, cy, r.z0, r.z1)).subtract(cyl(cx, cy, r.z0 - 0.0005, r.z1 - r.z0 + 0.001, rNew)); report.push(`둥근 구멍 (${(cx).toFixed(1)}, ${(cy).toFixed(1)}) z ${(r.z0 - z0).toFixed(2)}~${(r.z1 - z0).toFixed(2)}: 지름 ${(rOld * 2).toFixed(2)} → ${(rNew * 2).toFixed(2)}`) }
  return M }
const PARTS = [['큰기어', true, true], ['작은바퀴_본체', true, true], ['스프라켓', true, false], ['데코바퀴', true, false]] // 부시는 열십자가 이미 작은기어와 같고 입구 쪽 모서리 경사(0.8mm)가 있어 그대로 둔다
for (const [key, cross, round] of PARTS) {
  const M0 = loadStl(path.join(src, `출력용-${key}_원본(보정없음).stl`)), b = M0.boundingBox(), cx = (b.min[0] + b.max[0]) / 2, cy = (b.min[1] + b.max[1]) / 2, z0 = b.min[2], z1 = b.max[2]
  report.length = 0; let M = M0
  if (round) for (const [dx, dy] of [[10, 0], [-10, 0], [0, 10], [0, -10]]) { const h = holeAt(M0, z0 + 0.25 * (z1 - z0), cx + dx, cy + dy); if (h && Math.abs(h.b.w - 6.2) < 0.1) M = fixRound(M0, M, cx + dx, cy + dy, z0, z1) }
  if (cross) M = fixCross(M, cx, cy, z0, z1)
  { const keep = M.decompose().filter((q) => q.volume() > 5); if (keep.length !== M.decompose().length) { report.push(`떠 있는 부스러기 ${M.decompose().length - keep.length}개 제거(각 0.3mm³ 이하)`); M = keep.length === 1 ? keep[0] : Manifold.union(keep) } } // 채움·파냄 경계에서 생기는 아주 작은 조각을 지운다
  const name = `출력용-${key.replace('_본체', '')}${key === '작은바퀴_본체' ? '_본체' : ''}_${SPEC}.stl`
  { // float32 로 저장한 뒤 다시 읽으면 아주 가까운 점들이 갈라져 부스러기 조각이 생긴다 — 저장→읽기→작은 덩어리 제거를 한 번 거친다
    const tmp = path.join(out, '_tmp.stl'); const keepOut = out; saveStl('_tmp.stl', M); const R = loadStl(tmp), comps = R.decompose(), big = comps.filter((q) => q.volume() > 5)
    if (comps.length !== big.length) { report.push(`저장 뒤 부스러기 ${comps.length - big.length}개 제거`); M = big.length === 1 ? big[0] : Manifold.union(big) }; fs.rmSync(tmp) }
  console.log(key, M.status(), '부피', M0.volume().toFixed(0), '→', M.volume().toFixed(0), report.join(' | ')); const n = saveStl(name, M); console.log('   저장', name, n, '삼각형')
}
