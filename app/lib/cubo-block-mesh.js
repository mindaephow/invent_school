// 큐보 블록(2단·3단 등)을 자르기 없이 삼각형으로 직접 짜는 생성기. 규격은 cubo-part-maker.js 의 CUBO_BLOCK_STD.
// 길이 x(가운데 0), 높이 y(바닥 0~10), 폭 z(가운데 0). 단위 mm.
//  - 위아래로 뚫린 구멍: 프레임 구멍과 같은 구조(입구 3.5, 가장 좁은 곳 2.75)
//  - 스냅핏 돌기: 구멍 칸마다 앞뒤 면에 1개씩 + 양 끝 1개씩. 십자 홈이 있어 4장의 꽃잎 모양이다.
import { CUBO_BLOCK_STD as B } from './cubo-part-maker.js'
import { makeKit } from './cubo-mesh-kit.js'

// 돌기 하나. 몸통 면 위의 점 base 에서 방향 (eu, ev, et)(오른손 좌표계: eu×ev=et)으로 뻗는다.
// 블록 돌기는 걸리는 방식이 아니라 끼우는 방식: 밑동(테두리에 얹힘) → 몸통(목에 살짝 겹쳐 끼워짐) → 끝 모따기. 십자 홈 폭 1.2 로 4장 꽃잎(눌렸다가 들어간다). 십자 홈 폭 1.2 로 4장 꽃잎.
export function addPeg(kit, base, eu, ev, et) {
  const g = B.peg, h = g.slit / 2, M = 2
  const xa = Math.sqrt(g.shaftR * g.shaftR - h * h) // 홈 가장자리 중간점 위치: 몸통 반지름 기준으로 모든 높이에서 같게(걸림턱·밑동 단에서 이웃 면과 모서리가 정확히 맞게)
  // 꽃잎 하나(첫째 사분면)의 단면 둘레: 모서리 → 홈 가장자리 중간점 → 호 → 반대쪽 홈 가장자리 중간점. 위에서(끝에서) 볼 때 반시계.
  const loop = (r) => {
    const a0 = Math.asin(h / r), a1 = Math.PI / 2 - a0, xe = Math.sqrt(r * r - h * h)
    const xm = r >= g.shaftR ? xa : (h + xe) / 2
    const pts = [[h, h], [xm, h]]
    for (let k = 0; k <= M; k++) { const a = a0 + ((a1 - a0) * k) / M; pts.push([r * Math.cos(a), r * Math.sin(a)]) }
    pts.push([h, xm])
    return pts
  }
  // 길이 방향 단계: [t, 반지름]
  // 돌기 끝 0.5mm 는 모서리를 둥글린 끝(반지름 shaftR → tipR 를 1/4 원호로 줄인다): 구멍에 잘 들어가고, 각진 화살처럼 걸리지 않는다.
  const stations = [[0, g.collarR], [g.collarLen, g.collarR], [g.collarLen, g.shaftR], [g.shaftEnd, g.shaftR]]
  for (let k = 1; k <= 3; k++) { const s = k / 3; stations.push([g.shaftEnd + s * (g.len - g.shaftEnd), g.shaftR - (g.shaftR - g.tipR) * (1 - Math.sqrt(1 - s * s))]) }
  const to = (u, v, t) => [base[0] + eu[0] * u + ev[0] * v + et[0] * t, base[1] + eu[1] * u + ev[1] * v + et[1] * t, base[2] + eu[2] * u + ev[2] * v + et[2] * t]
  for (const [su, sv] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
    const place = (r, t) => { const pts = loop(r).map(([u, v]) => to(su * u, sv * v, t)); return su * sv < 0 ? pts.reverse() : pts }
    const rings = stations.map(([t, r]) => place(r, t))
    for (let s = 0; s < rings.length - 1; s++) {
      const A = rings[s], C = rings[s + 1], n = A.length
      for (let k = 0; k < n; k++) { const k2 = (k + 1) % n; kit.raw(A[k], A[k2], C[k2]); kit.raw(A[k], C[k2], C[k]) }
    }
    const tip = rings[rings.length - 1], ap = 2 + Math.floor(M / 2) // 끝 면: 원호 가운데 점에서 부채꼴(모서리에서 펴면 홈 가장자리 세 점이 일직선이라 면이 사라진다)
    for (let k = 0; k < tip.length; k++) { const k2 = (k + 1) % tip.length; if (k === ap || k2 === ap) continue; kit.raw(tip[ap], tip[k], tip[k2]) }
  }
}

// 칸 수 n(2단=2, 3단=3)짜리 블록의 삼각형 목록: Float32Array(삼각형 수 × 9)
// holes: 등록된 3단블록처럼 구멍 치수가 규격과 다를 때만 {entryR, neckR, chamberR} 로 준다(기본은 규격 CUBO_BLOCK_STD).
export function blockTriangles(n, seg = 20, height = B.height, holes = {}) {
  const HE = holes.entryR ?? B.holeEntryR, HN = holes.neckR ?? B.holeNeckR, HC = holes.chamberR ?? B.chamberR
  const kit = makeKit(seg)
  const { quad, P } = kit
  const L = n * B.pitch, hx = L / 2, hz = B.width / 2, H = height
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
    kit.cell(cx, 0, HE, xlo, xhi, -hz, hz, 0, -1)
    kit.cell(cx, 0, HE, xlo, xhi, -hz, hz, H, 1)
    // 구멍 단면(아래에서 위로): 입구 3.5(깊이 1) → 목 2.75(길이 3) → 가운데 방 3.5(높이 H−8) → 목 → 입구. 방이 없으면(H≤8) 목이 이어진다.
    const N = D + 3, cH = H - 2 * N, hasChamber = cH > 1e-6
    const segs = hasChamber ? [[HE, 0, D], [HN, D, N], [HC, N, H - N], [HN, H - N, H - D], [HE, H - D, H]] : [[HE, 0, D], [HN, D, H - D], [HE, H - D, H]]
    segs.forEach(([r, y0, y1]) => kit.cyl(cx, 0, r, y0, y1, -1))
    for (let k = 0; k + 1 < segs.length; k++) { // 반지름이 바뀌는 곳의 단(고리): 위로 좁아지면 아래를, 위로 넓어지면 위를 본다
      const rl = segs[k][0], ru = segs[k + 1][0], y = segs[k][2]
      kit.annulus(cx, 0, Math.min(rl, ru), Math.max(rl, ru), y, ru < rl ? -1 : 1)
    }
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
