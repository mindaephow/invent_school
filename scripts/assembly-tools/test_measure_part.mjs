// 부품 실측(app/lib/cubo-part-measure.js)을 가짜 부품으로 시험한다.   node scripts/assembly-tools/test_measure_part.mjs
// 가짜 부품: 상자 40×10×20 + 앞(+z)면 돌기(r3.8, 길이5, x=10) + 위(+y)면 구멍(r4, 깊이10, x=-10).
import { measureModel, formatMeasure } from '../../app/lib/cubo-part-measure.js'
const tris = []
const add = (a, b, c) => tris.push([a, b, c])
// 상자: 면마다 사각형 2삼각형, 바깥 방향으로 감기
const boxSize = [40, 10, 20]
const quad = (p0, p1, p2, p3) => {
  const cen = [(p0[0] + p1[0] + p2[0] + p3[0]) / 4, (p0[1] + p1[1] + p2[1] + p3[1]) / 4, (p0[2] + p1[2] + p2[2] + p3[2]) / 4]
  const u = p1.map((v, i) => v - p0[i]), w = p2.map((v, i) => v - p0[i])
  const n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
  const out = n[0] * cen[0] + n[1] * cen[1] + n[2] * cen[2] > 0
  if (out) { add(p0, p1, p2); add(p0, p2, p3) } else { add(p0, p2, p1); add(p0, p3, p2) }
}
const [X, Y, Z] = boxSize.map((v) => v / 2)
quad([-X, -Y, -Z], [X, -Y, -Z], [X, Y, -Z], [-X, Y, -Z]); quad([-X, -Y, Z], [X, -Y, Z], [X, Y, Z], [-X, Y, Z])
quad([-X, -Y, -Z], [X, -Y, -Z], [X, -Y, Z], [-X, -Y, Z]); quad([-X, Y, -Z], [X, Y, -Z], [X, Y, Z], [-X, Y, Z])
quad([-X, -Y, -Z], [-X, Y, -Z], [-X, Y, Z], [-X, -Y, Z]); quad([X, -Y, -Z], [X, Y, -Z], [X, Y, Z], [X, -Y, Z])
// 원통 벽 (축: 'z' | 'y', 중심 (c0,c1), 반지름 r, 축 방향 범위 [a,b], inward=구멍)
const tube = (axis, c0, c1, r, a, b, inward) => {
  const N = 20
  for (let i = 0; i < N; i++) {
    const t0 = (i / N) * 2 * Math.PI, t1 = ((i + 1) / N) * 2 * Math.PI
    const P = (t, h) => axis === 'z' ? [c0 + r * Math.cos(t), c1 + r * Math.sin(t), h] : [c0 + r * Math.cos(t), h, c1 + r * Math.sin(t)]
    const p0 = P(t0, a), p1 = P(t1, a), p2 = P(t1, b), p3 = P(t0, b)
    // 바깥 법선이 되는 순서(축 z 일 때 p0,p1,p2); y 축은 좌표계가 달라 순서를 뒤집는다
    const outward = axis === 'z'
    const flip = outward === inward ? true : false
    if (!flip) { add(p0, p1, p2); add(p0, p2, p3) } else { add(p0, p2, p1); add(p0, p3, p2) }
  }
}
tube('z', 10, 0, 3.8, Z, Z + 5, false)     // 돌기: 앞(+z) 면, 중심 (x=10, y=0), 길이 5
tube('y', -10, 0, 4, Y - 6, Y, true)       // 구멍: 위(+y) 면, 중심 (x=-10, z=0), 깊이 6 (끝까지 안 뚫림)
// 모델 좌표 (x,y,z) → STL 원본 좌표 (x, −z, y)  (설계 화면이 rotateX(−90°) 로 세우므로 거꾸로)
const buf = Buffer.alloc(84 + tris.length * 50)
buf.writeUInt32LE(tris.length, 80)
tris.forEach((t, i) => { const o = 84 + i * 50; t.forEach((p, k) => { buf.writeFloatLE(p[0], o + 12 + k * 12); buf.writeFloatLE(-p[2], o + 16 + k * 12); buf.writeFloatLE(p[1], o + 20 + k * 12) }) })
import { parseStl } from '../../app/lib/cubo-part-measure.js'
const raw = parseStl(buf)
const conn = { pegs: [{ id: 'p1', pos: [10, 0, 10], dir: [0, 0, 1], len: 5, r: 3.8 }, { id: 'p9', pos: [0, 0, -12.5], dir: [0, 0, -1], len: 5, r: 3.8 }], holes: [{ id: 'h1', pos: [-10, 2, -2.5], dir: [0, -1, 0], len: 6, r: 4 }] }
let fails = 0
const ok = (label, cond, extra = '') => { console.log((cond ? '✓ ' : '✗ ') + label + (extra ? ' ' + extra : '')); if (!cond) fails++ }
const m = measureModel(raw, {}, conn)
console.log(formatMeasure('가짜부품', m, true))
// 상자 + 돌기라서 z 방향 크기는 20 + 5 = 25, bbox 가운데가 z 로 2.5 이동
ok('크기 40 × 10 × 25', Math.abs(m.size[0] - 40) < 0.1 && Math.abs(m.size[1] - 10) < 0.1 && Math.abs(m.size[2] - 25) < 0.1, JSON.stringify(m.size.map((v) => +v.toFixed(1))))
ok('돌기 1개·구멍 1개를 찾음', m.features.filter((f) => f.kind === 'peg').length === 1 && m.features.filter((f) => f.kind === 'hole').length === 1)
const peg = m.features.find((f) => f.kind === 'peg'), hole = m.features.find((f) => f.kind === 'hole')
ok('돌기: 방향 +z, 반지름 3.8, 길이 5', peg && peg.dir === '+z' && Math.abs(peg.r - 3.8) < 0.2 && Math.abs(peg.len - 5) < 0.2, peg && JSON.stringify(peg.center.map((v) => +v.toFixed(1))))
ok('구멍: 방향 −y(안으로), 반지름 4, 깊이 6', hole && hole.dir === '-y' && Math.abs(hole.r - 4) < 0.2 && Math.abs(hole.len - 6) < 0.2)
ok('x 위치: 돌기 +10 / 구멍 −10', peg && hole && Math.abs(peg.center[0] - 10) < 0.2 && Math.abs(hole.center[0] + 10) < 0.2)
ok('대조: p1·h1 일치, p9(없는 돌기)는 못 찾음으로', m.cmp.matched === 2 && m.cmp.lines.some((l) => l.startsWith('✗ p9')))
// 회전(rz = 90°): 위(+y)였던 구멍이 −x 쪽으로 가야 한다
const rz = measureModel(raw, { rz: Math.PI / 2 }, null)
const h2 = rz.features.find((f) => f.kind === 'hole')
ok('z축 90° 회전하면 구멍 방향이 −y → +x', h2 && h2.dir === '+x', h2 && h2.dir)
console.log('실패', fails); process.exit(fails ? 1 : 0)
