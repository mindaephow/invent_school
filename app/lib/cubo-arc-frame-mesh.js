// 큐보 반원프레임(구멍 9개)을 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD(판 3·테두리 1·구멍 구조·폭 10) 그대로.
// 구멍 9개는 호 위에서 서로 10mm(현) 간격, 양 끝 두 구멍 중심은 60mm 떨어짐(교재 11번 그림: 가운데 3개가 직선 프레임 10mm 격자에 맞고, 4·6번 구멍에 리벳이 꽂힌다).
// 호 띠 폭 10(구멍 중심 ±5), 양 끝 구멍 아래로 5mm 곧은 발. 판 위에서 보면 x 좌우, z 는 호가 솟는 쪽(+z). 두께 y 는 바닥 0~5. 좌표는 전체 크기의 가운데가 0.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'

export { trianglesToStl }

// 구멍 9개는 호 위에서 서로 10mm(현) 간격이고 양 끝 두 구멍 중심은 60mm 떨어진다(교재 11번 그림: 4·6번 구멍이 직선 프레임 바깥 열 ±10에 맞는다).
// 호 반지름 R 은 위 두 조건으로 정해진다(약 31.5). 호 띠 폭 10(R±5), 끝 구멍 아래로 5mm 곧은 발.
export const ARC_STD = { holes: 9, chord: 10, endSpan: 60, foot: S.margin }
export function solveArc() {
  const half = (ARC_STD.holes - 1) / 2 // 4
  const f = (R) => R * Math.sin(half * 2 * Math.asin(ARC_STD.chord / 2 / R)) - ARC_STD.endSpan / 2
  let lo = 26, hi = 60 // f(lo)<0<f(hi) 가 아니므로 부호가 바뀌는 곳을 훑어서 찾는다
  let prev = f(lo)
  for (let R = lo; R <= hi; R += 0.01) { const v = f(R); if (prev < 0 && v >= 0) { lo = R - 0.01; hi = R; break } prev = v }
  for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (f(m) < 0) lo = m; else hi = m }
  const R = (lo + hi) / 2
  return { R, delta: 2 * Math.asin(ARC_STD.chord / 2 / R) } // delta: 이웃 구멍 사이 각(라디안)
}
const RO = S.rimOuterR - 0.01
const E = S.edgeWall
const rad = (d) => (d * Math.PI) / 180

// 다각형(칸의 안쪽 윤곽)에서 중심 원(반지름 R)을 뺀 면. 새 점을 만들지 않고 다각형의 점과 원의 점만으로 삼각형을 나눈다(귀 자르기):
// 원 구멍을 다각형에 한 줄로 이어(브리지) 구멍 없는 하나의 다각형으로 만든 뒤 귀를 하나씩 잘라 낸다. 다각형 모서리가 이웃 면(벽·옆 칸)의 모서리와
// 정확히 같으므로 이음매가 어긋나지 않는다. 면 방향은 kit.tri 가 법선(ny)에 맞춰 정한다.
function polyCell(kit, cx, cz, R, poly, y, ny) {
  const { tri, P, seg } = kit
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const area = (pp) => pp.reduce((s, q, i) => { const r = pp[(i + 1) % pp.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) / 2
  const outer = area(poly) > 0 ? poly.slice() : poly.slice().reverse() // 반시계
  const circle = Array.from({ length: seg }, (_, k) => [cx + R * Math.cos((2 * Math.PI * k) / seg), cz + R * Math.sin((2 * Math.PI * k) / seg)]).reverse() // 시계
  // 브리지: 원의 x 가 가장 큰 점 → 바깥 다각형에서 구멍·다각형 모서리와 겹치지 않고 안쪽으로 이어지는 가장 가까운 점
  let hi = 0
  for (let k = 1; k < circle.length; k++) if (circle[k][0] > circle[hi][0]) hi = k
  const H = circle[hi]
  const segHit = (a, b, c, d) => { // 두 선분이 끝점 말고 서로 가로지르는가
    const d1 = cross(a, b, c), d2 = cross(a, b, d), d3 = cross(c, d, a), d4 = cross(c, d, b)
    return d1 * d2 < -1e-12 && d3 * d4 < -1e-12
  }
  const order = outer.map((q, i) => i).sort((i, j) => Math.hypot(outer[i][0] - H[0], outer[i][1] - H[1]) - Math.hypot(outer[j][0] - H[0], outer[j][1] - H[1]))
  let oi = -1
  for (const i of order) {
    const O = outer[i]
    let ok = true
    for (let k = 0; k < outer.length && ok; k++) if (segHit(H, O, outer[k], outer[(k + 1) % outer.length])) ok = false
    for (let k = 0; k < circle.length && ok; k++) if (segHit(H, O, circle[k], circle[(k + 1) % circle.length])) ok = false
    if (ok) { // 중간 점이 원 바깥이어야 한다
      const mx = (H[0] + O[0]) / 2, mz = (H[1] + O[1]) / 2
      if (Math.hypot(mx - cx, mz - cz) > R) { oi = i; break }
    }
  }
  const ring = [...outer.slice(0, oi + 1), ...circle.slice(hi), ...circle.slice(0, hi), H, ...outer.slice(oi)]
  // 귀 자르기
  const idx = ring.map((_, i) => i)
  const same = (a, b) => Math.abs(a[0] - b[0]) < 1e-9 && Math.abs(a[1] - b[1]) < 1e-9
  const inTri = (a, b, c, q) => !(same(q, a) || same(q, b) || same(q, c)) && cross(a, b, q) >= -1e-12 && cross(b, c, q) >= -1e-12 && cross(c, a, q) >= -1e-12
  let guard = 0
  while (idx.length > 3 && guard++ < 10000) {
    let cut = false
    for (let k = 0; k < idx.length; k++) {
      const a = ring[idx[(k + idx.length - 1) % idx.length]], b = ring[idx[k]], c = ring[idx[(k + 1) % idx.length]]
      if (cross(a, b, c) <= 1e-12) continue // 볼록한 꼭짓점만
      if (idx.some((m) => inTri(a, b, c, ring[m]))) continue
      tri(P(a[0], y, a[1]), P(b[0], y, b[1]), P(c[0], y, c[1]), 0, ny, 0)
      idx.splice(k, 1); cut = true; break
    }
    if (!cut) break
  }
  if (idx.length === 3) { const [a, b, c] = idx.map((m) => ring[m]); tri(P(a[0], y, a[1]), P(b[0], y, b[1]), P(c[0], y, c[1]), 0, ny, 0) }
}

export function arcFrameTriangles(seg = 20, sub = 4) {
  const kit = makeKit(seg)
  const { quad, P } = kit
  const n = ARC_STD.holes, W = S.width / 2, F = ARC_STD.foot
  const { R, delta } = solveArc()
  const half = (n - 1) / 2
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const pt = (r, a) => [r * Math.sin(a), r * Math.cos(a)] // 각도 a 는 +z 에서 +x 쪽으로
  const phiEnd = half * delta
  const holeX = R * Math.sin(phiEnd) // 끝 구멍 중심 x (= 30)
  const xo = holeX + W, xi = holeX - W // 발의 곧은 옆면 x: 구멍 중심에서 5mm(직선 프레임의 여백·폭과 같다)
  const zb = R * Math.cos(phiEnd) - F // 발 바닥 z
  // 호 위 각도 표본: 구멍 각도(±4δ)까지 잘게 나눈 것 + 양 끝(e). 구멍 둘레 테두리가 호 윤곽에 닿는 곳(구멍 중심 각도)에 점이 있어야 현이 구멍 테두리를 자르지 않는다.
  // 안쪽 호는 끝 각도(약 72.4°)가 ±4δ(73.6°)보다 작아서 ±(4δ−δ/sub)(69°)까지만 쓴다. 바깥·안쪽 윤곽(d=0, d=E)이 같은 개수가 되게 e 와 무관하게 정한다.
  const span = (outer) => Array.from({ length: 2 * (half * sub - (outer ? 0 : 1)) + 1 }, (_, j) => (-(half * sub - (outer ? 0 : 1)) + j) * (delta / sub))
  const angles = (e, outer) => [-e, ...span(outer), e]
  // 윤곽(반시계): 오른발 → 바깥 호(오른쪽→왼쪽) → 왼발 → 안쪽 호(왼쪽→오른쪽). d = 안쪽으로 줄이는 양(0 이면 바깥 윤곽, E 면 테두리 안쪽 윤곽)
  const geo = (d) => {
    const ro = R + W - d, ri = R - W + d, xod = xo - d, xid = xi + d, zbd = zb + d
    return { ro, ri, xod, xid, zbd, eo: Math.asin(xod / ro), ei: Math.asin(xid / ri) }
  }
  const loop = (d) => {
    const g = geo(d)
    return [[g.xod, g.zbd], ...angles(g.eo, true).reverse().map((a) => pt(g.ro, a)), [-g.xod, g.zbd], [-g.xid, g.zbd], ...angles(g.ei, false).map((a) => pt(g.ri, a)), [g.xid, g.zbd]]
  }
  const O = loop(0), I = loop(E)
  const m = O.length
  const nrm = (A, B) => { const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); return [dz / l, -dx / l] } // 반시계 윤곽의 바깥쪽 법선
  for (let i = 0; i < m; i++) {
    const j = (i + 1) % m
    const [px, pz] = nrm(O[i], O[j])
    quad(P(O[i][0], Y0, O[i][1]), P(O[j][0], Y0, O[j][1]), P(O[j][0], Y5, O[j][1]), P(O[i][0], Y5, O[i][1]), px, 0, pz)
    for (const [y, ny] of [[Y0, -1], [Y5, 1]]) quad(P(O[i][0], y, O[i][1]), P(O[j][0], y, O[j][1]), P(I[j][0], y, I[j][1]), P(I[i][0], y, I[i][1]), 0, ny, 0)
    for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) quad(P(I[i][0], y0, I[i][1]), P(I[j][0], y0, I[j][1]), P(I[j][0], y1, I[j][1]), P(I[i][0], y1, I[i][1]), -px, 0, -pz)
  }
  // 칸마다(구멍 하나씩): 안쪽 윤곽 조각 + 구멍 고리·벽
  const g = geo(E), aO = angles(g.eo, true), aI = angles(g.ei, false)
  for (let k = 0; k < n; k++) {
    const phi = (k - half) * delta
    const lo = k === 0 ? -Infinity : phi - delta / 2, hi = k === n - 1 ? Infinity : phi + delta / 2
    const inR = (a) => a >= lo - 1e-9 && a <= hi + 1e-9
    const outer = aO.filter(inR).map((a) => pt(g.ro, a)), inner = aI.filter(inR).map((a) => pt(g.ri, a)).reverse()
    const poly = [...outer]
    if (k === n - 1) poly.push([g.xod, g.zbd], [g.xid, g.zbd])
    poly.push(...inner)
    if (k === 0) poly.push([-g.xid, g.zbd], [-g.xod, g.zbd])
    const [cx, cz] = pt(R, phi)
    kit.annulus(cx, cz, S.rimInnerR, RO, Y0, -1); kit.annulus(cx, cz, S.rimInnerR, RO, Y5, 1)
    kit.cyl(cx, cz, RO, Y0, Y1, 1); kit.cyl(cx, cz, RO, Y4, Y5, 1)
    kit.cyl(cx, cz, S.rimInnerR, Y0, Y1, -1); kit.cyl(cx, cz, S.rimInnerR, Y4, Y5, -1)
    kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y1, -1); kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y4, 1)
    kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
    polyCell(kit, cx, cz, RO, poly, Y1, -1); polyCell(kit, cx, cz, RO, poly, Y4, 1)
  }
  // 전체 크기의 가운데가 (0,0): z 는 발 바닥 ~ 호 꼭대기(R+W)
  const zc = (zb + R + W) / 2
  const out = kit.result()
  for (let i = 2; i < out.length; i += 3) out[i] -= zc
  return out
}
