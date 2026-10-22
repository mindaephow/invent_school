// 프린트용 프레임 — 원래 디자인(가장자리 벽 + 구멍마다 솟은 고리 + 그 사이 움푹한 면)을 그대로 두고 3D 불리언(manifold-3d)으로 겹치는 부분을 한 덩어리로 합쳐 만든다.
//   확정 규격(사용자 2026-10-23): 노즐 0.4 PLA, 구멍 목 지름 6.10, 입구 지름 7.7(깊이 1.1), 고리 벽 0.8(가장자리 벽 1.0 과 겹쳐도 한 덩어리), 가장 얇은 곳(목) 2.8, 총 두께 5, 눕혀서 출력.
//   node scripts/make-print-csg.mjs [저장 폴더]   (기본: 다운로드/큐보_3D모델_프린트용/고해상도 — 프레임3 시험 조각은 립시험 폴더)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import Module from 'manifold-3d'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { bentGeometry } from '../app/lib/cubo-bent-frame-mesh.js'
import { BENT_STD } from '../app/lib/cubo-bent-frame-mesh.js'
import { arcGeometry } from '../app/lib/cubo-arc-frame-mesh.js'
const wasm = await Module(); wasm.setup()
const { Manifold } = wasm
const HORN = { pilotR: 1.1, hexR: 2.5, hexDepth: 4, hexAngle: 30 } // 서보혼 구멍(cubo-horn-mesh.js 의 HORN_STD 와 같은 값)
const hexPts = (cx, cy) => Array.from({ length: 6 }, (_, k) => { const a = ((HORN.hexAngle + 60 * k) * Math.PI) / 180; return [cx + HORN.hexR * Math.cos(a), cy + HORN.hexR * Math.sin(a)] })
const SEG = 64, NECK_R = 3.05, ENTRY_R = 3.85, RING_W = 0.8, RIM_H = 1.1, PLATE = 2.8, TOTAL = RIM_H * 2 + PLATE, EPS = 0.1
const home = path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용')
const out = process.argv[2] || path.join(home, '고해상도'); fs.mkdirSync(out, { recursive: true })
const area = (p) => p.reduce((s, q, i) => { const r = p[(i + 1) % p.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) / 2
const ccw = (p) => (area(p) > 0 ? p : p.slice().reverse())
const cyl = (x, y, z0, h, r) => Manifold.cylinder(h, r, r, SEG, false).translate([x, y, z0])
// outer: 바깥 윤곽, inner: 가장자리 벽 안쪽 윤곽, holes: 구멍 중심 [[x,y]] (좌표는 위에서 본 평면, 두께는 z)
function frame(outer, inner, holes, skin = 0) { // skin > 0: 위·아래 면 전체에 그 두께의 얇은 막을 덮는다(홈은 안쪽 빈 공간이 됨, 구멍은 그대로 뚫림)
  let m = Manifold.extrude([ccw(outer)], TOTAL)
  const rec = ccw(inner)
  m = m.subtract(Manifold.extrude([rec], RIM_H + EPS).translate([0, 0, TOTAL - RIM_H]))
  m = m.subtract(Manifold.extrude([rec], RIM_H + EPS).translate([0, 0, -EPS]))
  const ro = ENTRY_R + RING_W
  if (skin > 0) { const cap = ccw(outer); m = m.add(Manifold.extrude([cap], skin)).add(Manifold.extrude([cap], skin).translate([0, 0, TOTAL - skin])) }
  // 고리·구멍은 한꺼번에 합쳐(Manifold.union) 한 번만 더하고 뺀다 — 구멍이 70개 넘는 판(515·713프레임)에서 하나씩 하면 메모리가 모자라다
  const H = holes.map((h) => (Array.isArray(h) ? { x: h[0], y: h[1], type: 'through' } : h))
  m = m.add(Manifold.union(H.flatMap(({ x, y }) => [cyl(x, y, 0, RIM_H, ro), cyl(x, y, TOTAL - RIM_H, RIM_H, ro)])))
  const cut = []
  for (const { x, y, type } of H) {
    if (type === 'through') cut.push(cyl(x, y, -EPS, RIM_H + EPS, ENTRY_R), cyl(x, y, TOTAL - RIM_H, RIM_H + EPS, ENTRY_R), cyl(x, y, -EPS, TOTAL + 2 * EPS, NECK_R))
    else if (type === 'pilot') cut.push(cyl(x, y, RIM_H, TOTAL - RIM_H + EPS, ENTRY_R), cyl(x, y, -EPS, TOTAL + 2 * EPS, HORN.pilotR)) // 위만 열린 홈 + 나사 구멍, 아래는 막힘
    else if (type === 'hex') cut.push(Manifold.extrude([hexPts(x, y)], HORN.hexDepth + EPS).translate([0, 0, TOTAL - HORN.hexDepth]), cyl(x, y, -EPS, TOTAL + 2 * EPS, HORN.pilotR)) // 위 육각 구멍(깊이 4) + 나사 구멍
  }
  m = m.subtract(Manifold.union(cut))
  return m
}
// 파일명 규칙(사용자 2026-10-23): 출력용-<부품>_목6.10_입구7.7_고리벽0.8_목두께2.8_총5[+막0.2].stl — 규격 숫자를 이름에 다 적는다
const SPEC = `목${(NECK_R * 2).toFixed(2)}_입구${ENTRY_R * 2}_고리벽${RING_W}_목두께${PLATE}_총${TOTAL}`
const fname = (part, skin = 0) => `출력용-${part}_${SPEC}${skin ? `+막${skin}` : ''}.stl`
function save(name, m, dir = out) {
  const mesh = m.getMesh(), v = mesh.vertProperties, n = mesh.numProp, t = mesh.triVerts
  let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < v.length; i += n) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], v[i + k]); mx[k] = Math.max(mx[k], v[i + k]) }
  const buf = Buffer.alloc(84 + (t.length / 3) * 50); buf.writeUInt32LE(t.length / 3, 80)
  const P = (i) => [v[i * n] - (mn[0] + mx[0]) / 2, v[i * n + 1] - (mn[1] + mx[1]) / 2, v[i * n + 2] - mn[2]]
  for (let f = 0; f < t.length / 3; f++) {
    const a = P(t[f * 3]), b = P(t[f * 3 + 1]), c = P(t[f * 3 + 2])
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [c[0] - a[0], c[1] - a[1], c[2] - a[2]]
    let nx = u[1] * w[2] - u[2] * w[1], ny = u[2] * w[0] - u[0] * w[2], nz = u[0] * w[1] - u[1] * w[0]; const l = Math.hypot(nx, ny, nz) || 1
    const o = 84 + f * 50; ;[nx / l, ny / l, nz / l, ...a, ...b, ...c].forEach((q, k) => buf.writeFloatLE(q, o + k * 4))
  }
  fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(path.join(dir, name), buf); console.log(name, '삼각형', t.length / 3, '크기', mx.map((q, k) => +(q - mn[k]).toFixed(2)).join('×'))
}
const plate = (nx, nz, skin = 0) => { const hx = nx * S.pitch / 2, hz = nz * S.pitch / 2, E = S.edgeWall
  const rect = (d) => [[-hx + d, -hz + d], [hx - d, -hz + d], [hx - d, hz - d], [-hx + d, hz - d]], holes = []
  for (let i = 0; i < nx; i++) for (let j = 0; j < nz; j++) holes.push([-hx + S.margin + i * S.pitch, -hz + S.margin + j * S.pitch])
  return frame(rect(0), rect(E), holes, skin) }
const arc = () => { const g = arcGeometry(); return frame(g.outer, g.inner, g.holes) }
// 전체 모드: node scripts/make-print-csg.mjs <저장 폴더> all  — DB 부품 목록의 프레임 전부(직사각 15종·꺾인 프레임 2종·반원프레임). 이름 → 만든 STL 파일 이름은 index.json 에 적는다.
export const ALL = [['115프레임', 1, 15], ['15프레임', 1, 5], ['17프레임', 1, 7], ['19프레임', 1, 9], ['215프레임', 2, 15], ['25프레임', 2, 5], ['27프레임', 2, 7], ['29프레임', 2, 9], ['315프레임', 3, 15], ['35프레임', 3, 5], ['37프레임', 3, 7], ['39프레임', 3, 9], ['515프레임', 5, 15], ['59프레임', 5, 9], ['713프레임', 7, 13]]
const SKIN = process.argv[4] ? Number(process.argv[4]) : 0
const bent = () => { const g = bentGeometry(); return frame(g.outer, g.inner, g.holes.map((h) => [h.X, h.Y])) }
const servoHorn = (skin = 0) => { const hx = 5 * S.pitch / 2, hz = S.width / 2, E = S.edgeWall, rect = (a, b) => [[-a, -b], [a, -b], [a, b], [-a, b]]
  const types = ['through', 'through', 'pilot', 'pilot', 'hex']
  return frame(rect(hx, hz), rect(hx - E, hz - E), types.map((type, i) => ({ x: -hx + S.margin + i * S.pitch, y: 0, type })), skin) }
const roundHorn = (skin = 0) => { const R = 15, E = S.edgeWall, circ = (r, n = 96) => Array.from({ length: n }, (_, k) => [r * Math.cos((2 * Math.PI * k) / n), r * Math.sin((2 * Math.PI * k) / n)])
  return frame(circ(R), circ(R - E), [{ x: 0, y: 0, type: 'hex' }, ...[[10, 0], [0, 10], [-10, 0], [0, -10]].map(([x, y]) => ({ x, y, type: 'through' }))], skin) }
if (process.argv[3] === 'horn') { const idx = {}; save(fname('서보혼', SKIN), servoHorn(SKIN)); idx['서보혼'] = fname('서보혼', SKIN); save(fname('둥근서보혼', SKIN), roundHorn(SKIN)); idx['둥근서보혼'] = fname('둥근서보혼', SKIN); fs.writeFileSync(path.join(out, 'index.json'), JSON.stringify(idx, null, 1)) }
else if (process.argv[3] === 'all') {
  const idx = {}
  for (const [name, a, b] of ALL) { const f = fname(name, SKIN); save(f, plate(b, a, SKIN)); idx[name] = f }
  Object.assign(BENT_STD, { straightHoles: 6, slantHoles: 4, bendDeg: 45 }); save(fname('135도프레임', SKIN), bent()); idx['135도 프레임'] = fname('135도프레임', SKIN)
  Object.assign(BENT_STD, { straightHoles: 3, slantHoles: 3, bendDeg: 90 }); save(fname('90도프레임', SKIN), bent()); idx['90도 프레임'] = fname('90도프레임', SKIN)
  save(fname('반원프레임', SKIN), arc()); idx['반원프레임'] = fname('반원프레임', SKIN)
  fs.writeFileSync(path.join(out, 'index.json'), JSON.stringify(idx, null, 1))
} else if (process.argv[3] === 'test') save(fname('13프레임', SKIN), plate(3, 1, SKIN), path.join(home, '립시험'))
else {
  save(fname('19프레임', SKIN), plate(9, 1, SKIN)); save(fname('35프레임', SKIN), plate(5, 3, SKIN)); save(fname('37프레임', SKIN), plate(7, 3, SKIN))
  save(fname('135도프레임', SKIN), bent())
  Object.assign(BENT_STD, { straightHoles: 3, slantHoles: 3, bendDeg: 90 }); save(fname('90도프레임', SKIN), bent())
}
