// 큐보 135도 프레임(구멍 9개: 꺾인 쪽 3 + 모서리 1 + 곧은 쪽 5)을 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD(판 3·테두리 1·구멍 구조·폭 10) 그대로.
// 모서리 구멍 C 에서 두 팔이 갈라진다: 곧은 팔(구멍 6개 = C 포함, +x 방향)과 꺾인 팔(구멍 4개 = C 포함, 위쪽 왼쪽으로 45° 꺾임 → 두 팔 사이 안쪽각 135°).
// 두 팔 모두 구멍 간격 10, 폭 10(구멍 중심 ±5), 끝 구멍 중심에서 끝까지 5, 구멍줄은 폭의 정확히 가운데. 곧은 팔 55mm · 꺾인 팔 35mm(교재 표기).
// 윤곽은 두 띠의 합집합(곧은 띠 ∪ 꺾인 띠). 등록된 135도프레임(Tinkercad)을 직접 재서 정한 구조이고, 그 모델에서 어긋나 있던 끝 여백(5.2·4.73)·구멍줄 치우침(0.19)·모서리 구멍 직선 이탈(0.07)을 규격값으로 바로잡았다(2026-10-20).
// 좌표: 판 위에서 보면 곧은 팔이 +x 로 뻗고, 꺾인 팔은 -x·-z 쪽(등록된 STL 방향과 같다). 두께 y 는 바닥 0~5. 전체 크기의 가운데가 (0,0).
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export { trianglesToStl }

export const BENT_STD = { straightHoles: 6, slantHoles: 4, bendDeg: 45 }
// RO·E 는 호출 때마다 규격(S)을 읽는다(프린트용 시험 조각이 값을 바꿔 만들 수 있게) — 아래 두 함수 첫 줄에서 정한다

// 평면 점은 (X,Y)(곧은 팔이 +X, 꺾인 팔이 -X +Y 쪽)로 만들고, 메시 좌표 (x,z) = (X,-Y) 로 옮긴다.
// 면은 다른 프레임 생성기(15프레임·반원프레임)처럼 구멍 한 칸씩 나눠 만든다. 칸 경계(구멍 사이 중간, 모서리 구멍 칸은 두 팔의 중간)에는 윤곽선에도 같은 점을 두어 이웃 칸·벽과 모서리가 정확히 맞는다.
export function bentGeometry() {
  const RO = S.rimOuterR - 0.01, E = S.edgeWall
  const th = (BENT_STD.bendDeg * Math.PI) / 180, c = Math.cos(th), s = Math.sin(th)
  const e2 = [-c, s], n2 = [s, c], W = S.width / 2, P = S.pitch
  const xEnd = (BENT_STD.straightHoles - 1) * P + S.margin
  const l2 = (BENT_STD.slantHoles - 1) * P + S.margin
  const sp = (t, off) => [t * e2[0] + off * n2[0], t * e2[1] + off * n2[1]] // 꺾인 팔 위의 점: 팔 방향으로 t, 옆으로 off
  const xs = [] // 곧은 팔 칸 경계 X (작은 쪽부터): 5, 15, …
  for (let k = 0; k < BENT_STD.straightHoles - 1; k++) xs.push(k * P + P / 2)
  const ss = [] // 꺾인 팔 칸 경계 t: 5, 15, …
  for (let k = 0; k < BENT_STD.slantHoles - 1; k++) ss.push(k * P + P / 2)
  const loop = (d) => { // d = 안쪽으로 줄이는 양(0 이면 바깥 윤곽, E 면 가장자리 테두리 안쪽 윤곽)
    const w = W - d, xe = xEnd - d, l = l2 - d
    const jx = (w * (1 - c)) / s
    const pts = [[xe, -w], [xe, w]]
    for (const x of [...xs].reverse()) pts.push([x, w])
    pts.push([jx, w])                                  // J1: 곧은 띠 윗변 ∩ 꺾인 띠 안쪽 변
    for (const t of ss) pts.push(sp(t, w))
    pts.push(sp(l, w), sp(l, -w))                      // 꺾인 팔 끝
    for (const t of [...ss].reverse()) pts.push(sp(t, -w))
    pts.push([-jx, -w])                                // J2
    for (const x of xs) pts.push([x, -w])
    return pts
  }
  const inner = loop(E), w = W - E, xe = xEnd - E, l = l2 - E
  const J1 = inner.find((q) => Math.abs(q[1] - w) < 1e-9 && q[0] < xs[0] && q[0] > 0), J2 = inner.find((q) => Math.abs(q[1] + w) < 1e-9 && q[0] < 0)
  const cells = [] // 칸 윤곽(안쪽 윤곽 기준), 구멍 중심, 구멍 id
  const hid = (n) => `h${n}`
  // 모서리 구멍 칸(h4): 곧은 쪽 첫 경계 x=5 와 꺾인 쪽 첫 경계 t=5 사이
  cells.push({ id: hid(BENT_STD.slantHoles), X: 0, Y: 0, poly: [[xs[0], -w], [xs[0], w], J1, sp(ss[0], w), sp(ss[0], -w), J2] })
  for (let k = 1; k < BENT_STD.straightHoles; k++) { // 곧은 팔 구멍 h5…
    const lo = xs[k - 1], hi = k === BENT_STD.straightHoles - 1 ? xe : xs[k]
    cells.push({ id: hid(BENT_STD.slantHoles + k), X: k * P, Y: 0, poly: [[lo, -w], [hi, -w], [hi, w], [lo, w]] })
  }
  for (let k = 1; k < BENT_STD.slantHoles; k++) { // 꺾인 팔 구멍 h3, h2, h1
    const lo = ss[k - 1], hi = k === BENT_STD.slantHoles - 1 ? l : ss[k]
    const [cx, cy] = sp(k * P, 0)
    cells.push({ id: hid(BENT_STD.slantHoles - k), X: cx, Y: cy, poly: [sp(lo, -w), sp(hi, -w), sp(hi, w), sp(lo, w)] })
  }
  return { outer: loop(0), inner, cells, holes: cells.map(({ id, X, Y }) => ({ id, X, Y })) }
}

export function bentFrameTriangles(seg = 20) {
  const RO = S.rimOuterR - 0.01, E = S.edgeWall
  const kit = makeKit(seg)
  const { quad, P } = kit
  const g = bentGeometry()
  const toXZ = (p) => [p[0], -p[1]]
  let O = g.outer.map(toXZ), I = g.inner.map(toXZ)
  const area = (pp) => pp.reduce((a, q, i) => { const r = pp[(i + 1) % pp.length]; return a + q[0] * r[1] - r[0] * q[1] }, 0) / 2
  if (area(O) < 0) { O = O.reverse(); I = I.reverse() } // 반시계(x,z)로 맞춘다
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const m = O.length
  const nrm = (A, B) => { const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); return [dz / l, -dx / l] } // 반시계 윤곽의 바깥쪽 법선
  for (let i = 0; i < m; i++) {
    const j = (i + 1) % m
    const [px, pz] = nrm(O[i], O[j])
    quad(P(O[i][0], Y0, O[i][1]), P(O[j][0], Y0, O[j][1]), P(O[j][0], Y5, O[j][1]), P(O[i][0], Y5, O[i][1]), px, 0, pz)
    if (S.slab) continue
    for (const [y, ny] of [[Y0, -1], [Y5, 1]]) quad(P(O[i][0], y, O[i][1]), P(O[j][0], y, O[j][1]), P(I[j][0], y, I[j][1]), P(I[i][0], y, I[i][1]), 0, ny, 0)
    for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) quad(P(I[i][0], y0, I[i][1]), P(I[j][0], y0, I[j][1]), P(I[j][0], y1, I[j][1]), P(I[i][0], y1, I[i][1]), -px, 0, -pz)
  }
  if (S.slab) { // 프린트용(선택): 통판(plate-mesh 의 S.slab 와 같은 모양, edgeWall 을 0 으로 두고 쓴다) — 칸마다 위·아래 면은 칸 윤곽 − 입구 원
    for (const cell of g.cells) {
      const [cx, cz] = toXZ([cell.X, cell.Y]), RE = S.rimInnerR, poly = cell.poly.map(toXZ).filter((q, i, a) => { const r = a[(i + a.length - 1) % a.length]; return Math.hypot(q[0] - r[0], q[1] - r[1]) > 1e-9 }), hole = circlePts(cx, cz, RE, seg) // 90° 에서 J1 과 꺾인 칸 경계점이 겹치므로 같은 점은 한 번만
      kit.cyl(cx, cz, RE, Y0, Y1, -1); kit.cyl(cx, cz, RE, Y4, Y5, -1)
      kit.annulus(cx, cz, S.boreR, RE, Y1, -1); kit.annulus(cx, cz, S.boreR, RE, Y4, 1)
      kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
      ringFace(kit, poly, [hole], Y0, -1); ringFace(kit, poly, [hole], Y5, 1)
    }
  } else
  for (const cell of g.cells) {
    const h = cell
    const [cx, cz] = toXZ([h.X, h.Y])
    kit.annulus(cx, cz, S.rimInnerR, RO, Y0, -1); kit.annulus(cx, cz, S.rimInnerR, RO, Y5, 1)
    kit.cyl(cx, cz, RO, Y0, Y1, 1); kit.cyl(cx, cz, RO, Y4, Y5, 1)
    kit.cyl(cx, cz, S.rimInnerR, Y0, Y1, -1); kit.cyl(cx, cz, S.rimInnerR, Y4, Y5, -1)
    kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y1, -1); kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y4, 1)
    kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
    const rim = circlePts(cx, cz, RO, seg) // 칸의 안쪽 윤곽에서 구멍 테두리 원을 뺀 면(새 점 없이 귀 자르기: cubo-face-mesh.js)
    const poly = cell.poly.map(toXZ)
    ringFace(kit, poly, [rim], Y1, -1); ringFace(kit, poly, [rim], Y4, 1)
  }
  // 전체 크기의 가운데가 (0,0)
  const out = kit.result()
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity
  for (let i = 0; i < out.length; i += 3) { x0 = Math.min(x0, out[i]); x1 = Math.max(x1, out[i]); z0 = Math.min(z0, out[i + 2]); z1 = Math.max(z1, out[i + 2]) }
  const xc = (x0 + x1) / 2, zc = (z0 + z1) / 2
  for (let i = 0; i < out.length; i += 3) { out[i] -= xc; out[i + 2] -= zc }
  out.center = [xc, zc]
  return out
}
