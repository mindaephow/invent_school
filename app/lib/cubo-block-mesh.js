// 큐보 블록(2단·3단 등)을 자르기 없이 삼각형으로 직접 짜는 생성기. 규격은 cubo-part-maker.js 의 CUBO_BLOCK_STD.
// 길이 x(가운데 0), 높이 y(바닥 0~10), 폭 z(가운데 0). 단위 mm.
//  - 위아래로 뚫린 구멍: 프레임 구멍과 같은 구조(입구 3.5, 가장 좁은 곳 2.75)
//  - 스냅핏 돌기: 구멍 칸마다 앞뒤 면에 1개씩 + 양 끝 1개씩. 십자 홈이 있어 4장의 꽃잎 모양이다.
import { CUBO_BLOCK_STD as B } from './cubo-part-maker.js'
import { makeKit } from './cubo-mesh-kit.js'

// 돌기 하나. 몸통 면 위의 점 base 에서 방향 (eu, ev, et)(오른손 좌표계: eu×ev=et)으로 뻗는다.
function addPeg(kit, base, eu, ev, et) {
  const g = B.peg, h = g.slit / 2, M = 4
  // 꽃잎 하나(첫째 사분면)의 단면 둘레: 모서리 → 홈 벽을 따라 바깥 → 호 → 홈 벽을 따라 안쪽. 위에서(끝에서) 볼 때 반시계.
  const loop = (r) => {
    const a0 = Math.asin(h / r), a1 = Math.PI / 2 - a0, pts = [[h, h]]
    for (let k = 0; k <= M; k++) { const a = a0 + ((a1 - a0) * k) / M; pts.push([r * Math.cos(a), r * Math.sin(a)]) }
    return pts
  }
  // 길이 방향 단계: [t, 반지름]
  const stations = [[0, g.collarR], [g.collarLen, g.collarR], [g.collarLen, g.shaftR], [g.shaftEnd, g.shaftR], [g.len, g.tipR]]
  const to = (u, v, t) => [base[0] + eu[0] * u + ev[0] * v + et[0] * t, base[1] + eu[1] * u + ev[1] * v + et[1] * t, base[2] + eu[2] * u + ev[2] * v + et[2] * t]
  for (const [su, sv] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
    const place = (r, t) => { const pts = loop(r).map(([u, v]) => to(su * u, sv * v, t)); return su * sv < 0 ? pts.reverse() : pts }
    const rings = stations.map(([t, r]) => place(r, t))
    for (let s = 0; s < rings.length - 1; s++) {
      const A = rings[s], C = rings[s + 1], n = A.length
      for (let k = 0; k < n; k++) { const k2 = (k + 1) % n; kit.raw(A[k], A[k2], C[k2]); kit.raw(A[k], C[k2], C[k]) }
    }
    const tip = rings[rings.length - 1]
    for (let k = 1; k < tip.length - 1; k++) kit.raw(tip[0], tip[k], tip[k + 1])
  }
}

// 칸 수 n(2단=2, 3단=3)짜리 블록의 삼각형 목록: Float32Array(삼각형 수 × 9)
export function blockTriangles(n, seg = 20) {
  const kit = makeKit(seg)
  const { quad, P } = kit
  const L = n * B.pitch, hx = L / 2, hz = B.width / 2, H = B.height
  const cxs = Array.from({ length: n }, (_, i) => -hx + B.pitch / 2 + i * B.pitch)
  const D = B.holeEntryDepth
  // 몸통 옆면 4개(앞뒤 ±z, 양 끝 ±x)
  quad(P(-hx, 0, hz), P(hx, 0, hz), P(hx, H, hz), P(-hx, H, hz), 0, 0, 1)
  quad(P(hx, 0, -hz), P(-hx, 0, -hz), P(-hx, H, -hz), P(hx, H, -hz), 0, 0, -1)
  quad(P(hx, 0, -hz), P(hx, 0, hz), P(hx, H, hz), P(hx, H, -hz), 1, 0, 0)
  quad(P(-hx, 0, hz), P(-hx, 0, -hz), P(-hx, H, -hz), P(-hx, H, hz), -1, 0, 0)
  // 구멍마다: 위·아래 면(원이 뚫린 칸), 입구 벽, 입구 바닥 고리, 가장 좁은 구멍 벽
  cxs.forEach((cx, i) => {
    const xlo = cx - B.pitch / 2, xhi = cx + B.pitch / 2
    kit.cell(cx, 0, B.holeEntryR, xlo, xhi, -hz, hz, 0, -1)
    kit.cell(cx, 0, B.holeEntryR, xlo, xhi, -hz, hz, H, 1)
    kit.cyl(cx, 0, B.holeEntryR, 0, D, -1); kit.cyl(cx, 0, B.holeEntryR, H - D, H, -1)
    kit.annulus(cx, 0, B.holeNeckR, B.holeEntryR, D, -1); kit.annulus(cx, 0, B.holeNeckR, B.holeEntryR, H - D, 1) // 입구 바닥: 아래 입구의 바닥은 아래를, 위 입구의 바닥은 위를 본다
    kit.cyl(cx, 0, B.holeNeckR, D, H - D, -1)
  })
  // 돌기: 앞뒤 면 칸마다, 양 끝 하나씩(높이 가운데). 방향마다 오른손 좌표계가 되게 축을 고른다.
  const yc = H / 2
  cxs.forEach((cx) => {
    addPeg(kit, [cx, yc, hz], [1, 0, 0], [0, 1, 0], [0, 0, 1])
    addPeg(kit, [cx, yc, -hz], [0, 1, 0], [1, 0, 0], [0, 0, -1])
  })
  addPeg(kit, [hx, yc, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0])
  addPeg(kit, [-hx, yc, 0], [0, 0, 1], [0, 1, 0], [-1, 0, 0])
  return kit.result()
}
