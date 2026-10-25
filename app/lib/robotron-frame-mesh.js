// 로버트론 제품(에이스랩·로보타미주니어) 프레임 생성기의 공통 틀. 브랜드마다 규격 파일을 따로 둔다(junior-frame-mesh.js, acelab-frame-mesh.js) — 한쪽 값이 바뀌어도 서로 영향이 없게.
// 큐보 프레임과 다른 점(사용자 2026-10-25):
//  - 큐보의 구멍 둘레 테두리(고리)·입구 홈이 없다. 구멍은 곧고 지름이 1mm 작다(큐보 목 지름 5.5 → 4.5).
//  - 대신 구멍 한 칸(10×10)마다 가장자리 테두리와 같은 폭·높이(1mm)의 네모 테두리로 칸을 두른다 — 구멍 사이에 선이 생기고(15프레임이면 4줄),
//    가운데 판이 테두리보다 1mm 들어가 있어도 바닥에 닿는 곳이 격자로 고르게 생긴다.
//  - 두께 5(판 3 + 위·아래 테두리 1), 크기·구멍 위치는 큐보와 같고, 팔 끝 모서리가 더 둥글다.
// 좌표: 길이 x, 두께 y(바닥 0~5), 폭 z. 전체 크기의 가운데가 (0,0) — 큐보 생성기와 같은 원점(연결점을 그대로 쓰려고, 모서리를 깎기 전 윤곽의 가운데로 맞춘다).
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'
import { CUBO_FRAME_STD } from './cubo-part-maker.js'
import { bentGeometry, BENT_STD } from './cubo-bent-frame-mesh.js'
import { solveArc, ARC_STD } from './cubo-arc-frame-mesh.js'

const area = (pp) => pp.reduce((s, q, i) => { const r = pp[(i + 1) % pp.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) / 2
const dedupe = (pp) => pp.filter((q, i, a) => { const r = a[(i + a.length - 1) % a.length]; return Math.hypot(q[0] - r[0], q[1] - r[1]) > 1e-9 })
const ccw = (pp) => (area(pp) > 0 ? pp.slice() : pp.slice().reverse())

// 윤곽 점 중 corners(좌표 목록)에 해당하는 꼭짓점을 반지름 r 의 둥근 모서리로 바꾼다.
export function roundCorners(poly, corners, r, nseg = 8) {
  const out = []
  const m = poly.length
  for (let i = 0; i < m; i++) {
    const V = poly[i]
    if (!corners.some((c) => Math.hypot(c[0] - V[0], c[1] - V[1]) < 1e-6)) { out.push(V); continue }
    const A = poly[(i + m - 1) % m], B = poly[(i + 1) % m]
    const ua = [A[0] - V[0], A[1] - V[1]], ub = [B[0] - V[0], B[1] - V[1]]
    const la = Math.hypot(...ua), lb = Math.hypot(...ub)
    ua[0] /= la; ua[1] /= la; ub[0] /= lb; ub[1] /= lb
    const theta = Math.acos(Math.max(-1, Math.min(1, ua[0] * ub[0] + ua[1] * ub[1])))
    let rr = r, t = rr / Math.tan(theta / 2)
    const tmax = Math.min(la, lb) - 1e-3
    if (t > tmax) { t = tmax; rr = t * Math.tan(theta / 2) } // 이웃 변이 짧으면(반원프레임 안쪽 발 모서리 4.24) 그 변에 맞는 가장 큰 반지름으로 줄인다
    const T1 = [V[0] + ua[0] * t, V[1] + ua[1] * t]
    const bis = [ua[0] + ub[0], ua[1] + ub[1]], lbis = Math.hypot(...bis)
    const d = rr / Math.sin(theta / 2)
    const C = [V[0] + (bis[0] / lbis) * d, V[1] + (bis[1] / lbis) * d]
    const T2 = [V[0] + ub[0] * t, V[1] + ub[1] * t]
    const a1 = Math.atan2(T1[1] - C[1], T1[0] - C[0])
    let da = Math.atan2(T2[1] - C[1], T2[0] - C[0]) - a1
    while (da > Math.PI) da -= 2 * Math.PI
    while (da < -Math.PI) da += 2 * Math.PI
    for (let k = 0; k <= nseg; k++) { const a = a1 + (da * k) / nseg; out.push([C[0] + rr * Math.cos(a), C[1] + rr * Math.sin(a)]) }
  }
  return out
}

// 다각형을 모두 안쪽으로 d 만큼 줄인다(꼭짓점마다 이웃 두 변의 평행선이 만나는 점, 모서리 이음).
export function insetPoly(poly, d) {
  const p = ccw(poly), m = p.length
  const nrm = (A, B) => { const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); return [-dz / l, dx / l] } // 반시계 다각형의 안쪽(왼쪽) 법선
  return p.map((V, i) => {
    const n1 = nrm(p[(i + m - 1) % m], V), n2 = nrm(V, p[(i + 1) % m])
    const k = d / (1 + n1[0] * n2[0] + n1[1] * n2[1])
    return [V[0] + (n1[0] + n2[0]) * k, V[1] + (n1[1] + n2[1]) * k]
  })
}

// 바깥 윤곽(outlineIn)과 칸 목록 cells = [{ poly, hole:[x,z] }] 로 프레임 한 장을 만든다.
// poly 는 바깥 윤곽에서 테두리 폭의 절반(0.5)만큼 들어온 칸 다각형 — 이 함수가 한 번 더 0.5 줄여 "움푹 들어간 칸(주머니)"으로 쓴다(이웃 칸과 사이에 폭 1 테두리가 남는다).
// 위·아래 테두리(높이 1)는 칸 타일 − 주머니이고, 주머니 바닥(가운데 판 3mm)에 곧은 구멍이 뚫린다.
function build(S, outlineIn, cells, cornerTargets, outerTargets) {
  const kit = makeKit(S.seg)
  const { quad, P } = kit
  const outline = ccw(outlineIn)
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.thickness - S.rimHeight, Y5 = S.thickness
  const wall = (poly, y0, y1, sign) => { // 윤곽 옆면. 반시계 다각형에서 sign=+1 바깥쪽을 향함, -1 다각형 속을 향함
    const m = poly.length
    for (let i = 0; i < m; i++) {
      const j = (i + 1) % m, A = poly[i], B = poly[j]
      const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz)
      quad(P(A[0], y0, A[1]), P(B[0], y0, B[1]), P(B[0], y1, B[1]), P(A[0], y1, A[1]), (sign * dz) / l, 0, (-sign * dx) / l)
    }
  }
  wall(outline, Y0, Y5, 1)
  const pockets = cells.map((c) => {
    let pk = insetPoly(dedupe(c.poly), S.edgeWall / 2)
    pk = ccw(roundCorners(pk, cornerTargets, S.cornerR - S.edgeWall, S.cornerSeg))
    return { pk, hole: c.hole }
  })
  for (const { pk, hole } of pockets) {
    wall(pk, Y0, Y1, -1); wall(pk, Y4, Y5, -1)
    const [cx, cz] = hole
    let circle
    if (S.notch) { // 출력용: 구멍 목 둘레에 홈 notch 곳(폭 notchW, 구멍 반지름 밖으로 notchD 만큼 판다)
      circle = notchedHole(cx, cz, S)
      wall(circle, Y1, Y4, -1)
    } else {
      kit.cyl(cx, cz, S.boreR, Y1, Y4, -1) // 곧은 구멍(판 3mm 를 지난다)
      circle = circlePts(cx, cz, S.boreR, S.seg)
    }
    ringFace(kit, pk, [circle], Y1, -1); ringFace(kit, pk, [circle], Y4, 1) // 주머니 바닥(칸 − 구멍)
  }
  // 테두리 윗면·아랫면: 칸마다(칸 타일 − 그 칸 주머니). 타일은 바깥 윤곽까지 이어진 칸이라 이웃 타일과 변이 정확히 맞는다(한 번에 다 나누면 격자 안쪽 주머니를 못 잇는다).
  cells.forEach((c, i) => {
    const tile = ccw(roundCorners(dedupe(c.tile), outerTargets, S.cornerR, S.cornerSeg))
    ringFace(kit, tile, [pockets[i].pk], Y0, -1); ringFace(kit, tile, [pockets[i].pk], Y5, 1)
  })
  return kit.result()
}


// 홈 notch 곳이 파인 구멍 윤곽(반시계). 홈은 구멍 중심에서 바깥쪽으로 뻗은 폭 notchW 의 직사각형이고, 각도는 180/(notch/2) 간격(8곳이면 0·45·90·135° 와 그 반대쪽).
function notchedHole(cx, cz, S) {
  const r = S.boreR, w = S.notchW / 2, far = r + S.notchD, n = S.notch
  const alpha = Math.asin(w / r), start = Math.sqrt(r * r - w * w)
  const pts = []
  for (let k = 0; k < n; k++) {
    const th = (2 * Math.PI * k) / n, th2 = (2 * Math.PI * (k + 1)) / n
    const u = [Math.cos(th), Math.sin(th)], v = [-Math.sin(th), Math.cos(th)]
    const at = (a, b) => [cx + u[0] * a + v[0] * b, cz + u[1] * a + v[1] * b]
    pts.push(at(start, -w), at(far, -w), at(far, w), at(start, w)) // 홈 한 개(반시계로 바깥으로 나갔다 돌아옴)
    const a0 = th + alpha, a1 = th2 - alpha, m = Math.max(2, Math.round((a1 - a0) / (2 * Math.PI / S.seg)))
    for (let j = 1; j < m; j++) { const a = a0 + ((a1 - a0) * j) / m; pts.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]) } // 홈 사이 둥근 벽
  }
  return pts
}

const recenter = (arr, cx, cz) => { for (let i = 0; i < arr.length; i += 3) { arr[i] -= cx; arr[i + 2] -= cz } return arr }

// 구멍 nx(길이) × nz(폭) 개의 직선 프레임. 15프레임 = (5,1), 215프레임 = (15,2) ...
function straightFrame(S, nx, nz) {
  const hx = (nx * S.pitch) / 2, hz = (nz * S.pitch) / 2
  const rect = [[-hx, -hz], [hx, -hz], [hx, hz], [-hx, hz]]
  const outlinePts = [] // 칸 경계마다 점이 있는 바깥 윤곽(타일 윗면과 옆면 모서리가 맞게)
  for (let i = 0; i <= nx; i++) outlinePts.push([-hx + i * S.pitch, -hz])
  for (let k = 1; k <= nz; k++) outlinePts.push([hx, -hz + k * S.pitch])
  for (let i = nx - 1; i >= 0; i--) outlinePts.push([-hx + i * S.pitch, hz])
  for (let k = nz - 1; k >= 1; k--) outlinePts.push([-hx, -hz + k * S.pitch])
  const E = S.edgeWall, cells = [], holes = []
  for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) {
    const x0 = -hx + i * S.pitch, x1 = x0 + S.pitch, z0 = -hz + k * S.pitch, z1 = z0 + S.pitch
    const a = i === 0 ? x0 + E / 2 : x0, b = i === nx - 1 ? x1 - E / 2 : x1, c = k === 0 ? z0 + E / 2 : z0, d = k === nz - 1 ? z1 - E / 2 : z1
    cells.push({ tile: [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], poly: [[a, c], [b, c], [b, d], [a, d]], hole: [x0 + S.margin, z0 + S.margin] })
    holes.push({ x: x0 + S.margin, z: z0 + S.margin })
  }
  const tgt = [[-hx + E, -hz + E], [hx - E, -hz + E], [hx - E, hz - E], [-hx + E, hz - E]]
  return { tris: build(S, roundCorners(outlinePts, rect, S.cornerR, S.cornerSeg), cells, tgt, rect), holes }
}

// 꺾인 프레임(135도: 곧은 팔 6 + 꺾인 팔 4 / 90도: 3 + 3). 팔 끝 네 모서리만 둥글게 한다.
function bentFrame(S, straightHoles, slantHoles, bendDeg) {
  Object.assign(BENT_STD, { straightHoles, slantHoles, bendDeg })
  const savedE = CUBO_FRAME_STD.edgeWall
  CUBO_FRAME_STD.edgeWall = S.edgeWall / 2 // 칸 다각형을 "윤곽에서 E/2 안쪽" 기준으로 받는다(큐보 생성기가 규격 값을 호출 때 읽는다)
  let g, gt
  try { g = bentGeometry(); CUBO_FRAME_STD.edgeWall = 0; gt = bentGeometry() } finally { CUBO_FRAME_STD.edgeWall = savedE } // gt: 윤곽까지 이어진 칸 타일
  const th = (bendDeg * Math.PI) / 180, c = Math.cos(th), s = Math.sin(th)
  const e2 = [-c, s], n2 = [s, c], W = S.width / 2, E = S.edgeWall
  const sp = (t, off) => [t * e2[0] + off * n2[0], t * e2[1] + off * n2[1]]
  const xEnd = (straightHoles - 1) * S.pitch + S.margin, l2 = (slantHoles - 1) * S.pitch + S.margin
  const toXZ = (p) => [p[0], -p[1]]
  const ends = [[xEnd, -W], [xEnd, W], sp(l2, W), sp(l2, -W)].map(toXZ)
  const tgt = [[xEnd - E, -(W - E)], [xEnd - E, W - E], sp(l2 - E, W - E), sp(l2 - E, -(W - E))].map(toXZ) // 테두리 안쪽(주머니) 끝 모서리
  const outer = dedupe(g.outer.map(toXZ))
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity
  for (const [x, z] of outer) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z) }
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2
  const cells = g.cells.map((cell, i) => ({ tile: gt.cells[i].poly.map(toXZ), poly: cell.poly.map(toXZ), hole: toXZ([cell.X, cell.Y]) }))
  const tris = build(S, roundCorners(outer, ends, S.cornerR, S.cornerSeg), cells, tgt, ends)
  recenter(tris, cx, cz)
  return { tris, holes: cells.map((q) => ({ x: q.hole[0] - cx, z: q.hole[1] - cz })) }
}

// 반원프레임(구멍 9개). 양 끝 발(아래쪽 두 모서리 네 곳)을 둥글게 한다. 칸 다각형은 큐보 반원프레임 생성기의 칸 나누기와 같다.
function arcFrame(S, sub = 4) {
  const n = ARC_STD.holes, W = S.width / 2, F = ARC_STD.foot, E = S.edgeWall, d = E / 2
  const { R, delta } = solveArc(), half = (n - 1) / 2
  const pt = (r, a) => [r * Math.sin(a), r * Math.cos(a)]
  const phiEnd = half * delta, holeX = R * Math.sin(phiEnd)
  const zb = R * Math.cos(phiEnd) - F
  const span = (outer2) => Array.from({ length: 2 * (half * sub - (outer2 ? 0 : 1)) + 1 }, (_, j) => (-(half * sub - (outer2 ? 0 : 1)) + j) * (delta / sub))
  const geo = (dd) => { const xod = holeX + W - dd, xid = holeX - W + dd, ro = R + W - dd, ri = R - W + dd; return { ro, ri, xod, xid, zbd: zb + dd, eo: Math.asin(xod / ro), ei: Math.asin(xid / ri) } }
  const loop = (dd) => { const g = geo(dd); const ang = (e, o) => [-e, ...span(o), e]
    return [[g.xod, g.zbd], ...ang(g.eo, true).reverse().map((a) => pt(g.ro, a)), [-g.xod, g.zbd], [-g.xid, g.zbd], ...ang(g.ei, false).map((a) => pt(g.ri, a)), [g.xid, g.zbd]] }
  const outer = loop(0)
  const cellsAt = (dd) => { // 윤곽에서 dd 안쪽 기준의 칸 다각형(칸마다)
    const g = geo(dd)
    const aO = [-g.eo, ...span(true), g.eo], aI = [-g.ei, ...span(false), g.ei]
    const out = []
    for (let k = 0; k < n; k++) {
      const phi = (k - half) * delta
      const lo = k === 0 ? -Infinity : phi - delta / 2, hi = k === n - 1 ? Infinity : phi + delta / 2
      const inR = (a) => a >= lo - 1e-9 && a <= hi + 1e-9
      const outerPts = aO.filter(inR).map((a) => pt(g.ro, a)), innerPts = aI.filter(inR).map((a) => pt(g.ri, a)).reverse()
      const poly = [...outerPts]
      if (k === n - 1) poly.push([g.xod, g.zbd], [g.xid, g.zbd])
      poly.push(...innerPts)
      if (k === 0) poly.push([-g.xid, g.zbd], [-g.xod, g.zbd])
      out.push(poly)
    }
    return out
  }
  const polys = cellsAt(d), tiles = cellsAt(0)
  const cells = polys.map((poly, k) => ({ tile: tiles[k], poly, hole: pt(R, (k - half) * delta) }))
  const feet = outer.filter((q) => Math.abs(q[1] - zb) < 1e-9)
  const tgt = [[holeX + W - E, zb + E], [holeX - W + E, zb + E], [-(holeX - W + E), zb + E], [-(holeX + W - E), zb + E]]
  const zc = (zb + R + W) / 2 // 큐보 생성기와 같은 원점: 발 바닥 ~ 호 꼭대기의 가운데(x 는 0)
  const tris = build(S, roundCorners(outer, feet, S.cornerR, S.cornerSeg), cells, tgt, feet)
  recenter(tris, 0, zc)
  return { tris, holes: cells.map((q) => ({ x: q.hole[0], z: q.hole[1] - zc })) }
}

// 브랜드 규격 S({ thickness, rimHeight, edgeWall, boreR, cornerR, pitch, width, margin, seg, cornerSeg })로 프레임 생성기 묶음을 만든다.
export function createFrameGenerator(S) {
  return {
    std: S,
    straight: (nx, nz) => straightFrame(S, nx, nz),
    bent: (straightHoles, slantHoles, bendDeg) => bentFrame(S, straightHoles, slantHoles, bendDeg),
    arc: () => arcFrame(S),
  }
}
