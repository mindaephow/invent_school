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
    return { pk, holes: c.holes || [c.hole], holePolys: c.holePolys || [], cross: c.cross }
  })
  for (const { pk, holes: hl, holePolys, cross } of pockets) {
    wall(pk, Y0, Y1, -1); wall(pk, Y4, Y5, -1)
    const circles = []
    for (const poly of holePolys) { wall(poly, Y1, Y4, -1); circles.push(poly) } // 서로 겹쳐 하나로 이어진 구멍(반시계 윤곽)
    for (const [cx, cz] of hl) {
    let circle
    if (cross) { // 열십자 구멍(T축이 들어가는 구멍): 십자 전체 폭 crossSpan, 팔 폭 crossArm
      const a = S.crossSpan / 2, w = S.crossArm / 2
      circle = [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]].map(([x, z]) => [cx + x, cz + z])
      wall(circle, Y1, Y4, -1)
    } else if (S.notch) { // 출력용: 구멍 목 둘레에 홈 notch 곳(폭 notchW, 구멍 반지름 밖으로 notchD 만큼 판다)
      circle = notchedHole(cx, cz, S)
      wall(circle, Y1, Y4, -1)
    } else {
      kit.cyl(cx, cz, S.boreR, Y1, Y4, -1) // 곧은 구멍(판 3mm 를 지난다)
      circle = circlePts(cx, cz, S.boreR, S.seg)
    }
    circles.push(circle)
    }
    ringFace(kit, pk, circles, Y1, -1); ringFace(kit, pk, circles, Y4, 1) // 주머니 바닥(칸 − 구멍들)
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
// crossAt = [i, k] 이면 그 칸의 구멍을 열십자 구멍으로 만든다(3십자프레임).
// squareEnd 이면 +x 쪽 끝 두 모서리를 둥글리지 않는다(브라켓에서 다른 판·모서리 덩어리와 빈틈 없이 이어지게).
// ext(mm) > 0 이면 −x 쪽 끝 칸을 ext 만큼 늘인다(체어브라켓의 12프레임 +5mm = 길이 25: 구멍은 그대로 10mm 간격, −x 쪽 끝 여백만 5+ext).
function straightFrame(S, nx, nz, crossAt, squareEnd, ext = 0) {
  const hx = (nx * S.pitch + ext) / 2, hz = (nz * S.pitch) / 2
  const bx = (i) => (i === 0 ? -hx : -hx + ext + i * S.pitch) // 칸 경계 x
  const rect = [[-hx, -hz], [hx, -hz], [hx, hz], [-hx, hz]]
  const outlinePts = [] // 칸 경계마다 점이 있는 바깥 윤곽(타일 윗면과 옆면 모서리가 맞게)
  for (let i = 0; i <= nx; i++) outlinePts.push([bx(i), -hz])
  for (let k = 1; k <= nz; k++) outlinePts.push([hx, -hz + k * S.pitch])
  for (let i = nx - 1; i >= 0; i--) outlinePts.push([bx(i), hz])
  for (let k = nz - 1; k >= 1; k--) outlinePts.push([-hx, -hz + k * S.pitch])
  const E = S.edgeWall, cells = [], holes = []
  for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) {
    const x0 = bx(i), x1 = bx(i + 1), z0 = -hz + k * S.pitch, z1 = z0 + S.pitch, hxc = x0 + S.margin + (i === 0 ? ext : 0)
    const a = i === 0 ? x0 + E / 2 : x0, b = i === nx - 1 ? x1 - E / 2 : x1, c = k === 0 ? z0 + E / 2 : z0, d = k === nz - 1 ? z1 - E / 2 : z1
    cells.push({ tile: [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], poly: [[a, c], [b, c], [b, d], [a, d]], hole: [hxc, z0 + S.margin], cross: !!crossAt && crossAt[0] === i && crossAt[1] === k })
    holes.push({ x: hxc, z: z0 + S.margin })
  }
  const tgt = [[-hx + E, -hz + E], [hx - E, -hz + E], [hx - E, hz - E], [-hx + E, hz - E]]
  const keep = (q) => !squareEnd || q[0] < 0
  const round = rect.filter(keep)
  return { tris: build(S, roundCorners(outlinePts, round, S.cornerR, S.cornerSeg), cells, tgt.filter(keep), round), holes }
}

// 길이 len·폭 한 칸(10)의 프레임 한 장에 주머니 하나(칸 하나)를 두고 구멍을 원하는 x 자리(holeXs, 가운데가 0)에 뚫는다(10 간격이 아닌 구멍 배치용, 체어브라켓). 구멍끼리 5 간격처럼 가까워도 주머니 안에 모두 들어간다.
function slotFrame(S, len, holeXs) {
  const hx = len / 2, hz = S.pitch / 2, E = S.edgeWall, r = S.boreR, xs = holeXs.slice().sort((p, q) => p - q)
  const rect = [[-hx, -hz], [hx, -hz], [hx, hz], [-hx, hz]]
  const groups = []; xs.forEach((x, i) => { if (i && x - xs[i - 1] < 2 * r - 1e-9) groups[groups.length - 1].push(x); else groups.push([x]) }) // 이웃 구멍과 겹치는(간격 < 지름) 것끼리 한 덩어리
  const single = groups.filter((g) => g.length === 1).map((g) => [g[0], 0])
  const arcPts = (cx, a0, a1) => { const n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / (2 * Math.PI / S.seg))); return Array.from({ length: n + 1 }, (_, k) => { const a = a0 + (a1 - a0) * k / n; return [cx + r * Math.cos(a), r * Math.sin(a)] }) }
  const unionPoly = (g) => { // 한 줄로 늘어선 같은 크기 원들의 합집합 윤곽(반시계): 아래쪽 호들을 오른쪽으로, 오른쪽 끝을 돌아, 위쪽 호들을 왼쪽으로
    const n = g.length, phi = (i) => Math.acos(Math.min(1, (g[i + 1] - g[i]) / 2 / r)) // 이웃 두 원이 만나는 점의 각도(오른쪽 원 기준 i 번째 쌍)
    const out = []
    for (let i = 0; i < n; i++) { const fL = i ? phi(i - 1) : 0, fR = i < n - 1 ? phi(i) : 0
      const a0 = i ? Math.PI + fL : Math.PI, a1 = i === n - 1 ? 3 * Math.PI - fL : 2 * Math.PI - fR
      const arc = arcPts(g[i], a0, a1); out.push(...(out.length ? arc.slice(1) : arc)) }
    for (let i = n - 2; i >= 0; i--) { const fL = i ? phi(i - 1) : 0, fR = phi(i), arc = arcPts(g[i], fR, i ? Math.PI - fL : Math.PI); out.push(...arc.slice(1)) }
    out.pop() // 마지막 점은 시작점과 같다
    return out }
  const holePolys = groups.filter((g) => g.length > 1).map(unionPoly)
  const cells = [{ tile: rect, poly: [[-hx + E / 2, -hz + E / 2], [hx - E / 2, -hz + E / 2], [hx - E / 2, hz - E / 2], [-hx + E / 2, hz - E / 2]], holes: single, holePolys }]
  const tgt = [[-hx + E, -hz + E], [hx - E, -hz + E], [hx - E, hz - E], [-hx + E, hz - E]]
  return { tris: build(S, roundCorners(rect, rect, S.cornerR, S.cornerSeg), cells, tgt, rect), holes: holeXs.map((x) => ({ x, z: 0 })) }
}

// 칸 목록 [[i,k],…](i = 길이 x 방향, k = 폭 z 방향 칸 번호)으로 이루어진 프레임(T자 등). 윤곽은 칸들을 합친 바깥 둘레이고, 튀어나온(볼록) 모서리만 둥글게 한다.
// 좌표는 칸 전체를 감싸는 상자의 가운데가 (0,0). 구멍은 칸 목록 순서대로 돌려준다.
function gridFrame(S, cellList) {
  const P = S.pitch, E = S.edgeWall
  const has = (i, k) => cellList.some((c) => c[0] === i && c[1] === k)
  const xs = cellList.map((c) => c[0]), zs = cellList.map((c) => c[1])
  const cx = ((Math.min(...xs) + Math.max(...xs) + 1) * P) / 2, cz = ((Math.min(...zs) + Math.max(...zs) + 1) * P) / 2
  const edges = new Map() // 시작점 → 끝점 (칸 안쪽이 왼쪽에 오는 방향 = 반시계)
  const key = (p) => p[0] + ',' + p[1]
  const addEdge = (a, b) => edges.set(key(a), { a, b })
  const cells = [], holes = []
  for (const [i, k] of cellList) {
    const x0 = i * P - cx, x1 = x0 + P, z0 = k * P - cz, z1 = z0 + P
    const nb = { b: has(i, k - 1), r: has(i + 1, k), t: has(i, k + 1), l: has(i - 1, k) }
    if (!nb.b) addEdge([x0, z0], [x1, z0])
    if (!nb.r) addEdge([x1, z0], [x1, z1])
    if (!nb.t) addEdge([x1, z1], [x0, z1])
    if (!nb.l) addEdge([x0, z1], [x0, z0])
    const a = nb.l ? x0 : x0 + E / 2, b = nb.r ? x1 : x1 - E / 2, c = nb.b ? z0 : z0 + E / 2, d = nb.t ? z1 : z1 - E / 2
    cells.push({ tile: [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], poly: [[a, c], [b, c], [b, d], [a, d]], hole: [x0 + S.margin, z0 + S.margin] })
    holes.push({ x: x0 + S.margin, z: z0 + S.margin })
  }
  const first = edges.values().next().value
  const loop = [first.a]
  for (let e = edges.get(key(first.b)); e && key(e.a) !== key(first.a); e = edges.get(key(e.b))) loop.push(e.a)
  if (loop.length !== edges.size) throw new Error('칸 목록이 한 덩어리가 아니거나 구멍이 있다')
  const outer = [], tgt = []
  loop.forEach((V, n) => {
    const A = loop[(n + loop.length - 1) % loop.length], B = loop[(n + 1) % loop.length]
    const d1 = [V[0] - A[0], V[1] - A[1]], d2 = [B[0] - V[0], B[1] - V[1]]
    if (d1[0] * d2[1] - d1[1] * d2[0] > 0) { // 왼쪽으로 꺾임 = 볼록 모서리
      const l1 = Math.hypot(...d1), l2 = Math.hypot(...d2)
      outer.push(V)
      tgt.push([V[0] + E * (-d1[1] / l1 - d2[1] / l2), V[1] + E * (d1[0] / l1 + d2[0] / l2)])
    }
  })
  return { tris: build(S, roundCorners(loop, outer, S.cornerR, S.cornerSeg), cells, tgt, outer), holes }
}

// 각 브라켓: 13프레임 판(구멍 3개, 바깥 길이 35)과 12프레임 판(구멍 2개, 바깥 길이 25)이 안쪽각 innerDeg 로 붙고 모서리는 채워진 한 덩어리(사용자 2026-10-26).
// L브라켓 = 안쪽각 90°, V브라켓 = L브라켓을 안쪽각 135°로 벌린 것. 좌표: 긴 팔이 x(바닥 y=0), 폭 z, x 는 전체 상자의 가운데가 0.
// 긴 팔 구멍 3개는 위아래로, 짧은 팔 구멍 2개는 그 판의 두께 방향으로 끼운다.
function angleBracket(S, innerDeg) {
  const P = S.pitch, T = S.thickness, W = S.width
  const a = straightFrame(S, 3, 1, null, true), b = straightFrame(S, 2, 1, null, true) // 모서리 쪽 끝은 각지게
  const phi = ((180 - innerDeg) * Math.PI) / 180, d = [Math.cos(phi), Math.sin(phi)], n = [-Math.sin(phi), Math.cos(phi)] // d = 짧은 팔이 뻗는 방향, n = 안쪽을 향한 법선
  const I = [3 * P, T] // 안쪽 모서리(긴 팔 윗면 끝)
  const O = [I[0] - T * n[0], I[1] - T * n[1]] // 짧은 팔 시작선의 바깥쪽 끝
  const toB = (x, y) => [O[0] + (P + x) * d[0] + y * n[0], O[1] + (P + x) * d[1] + y * n[1]] // 짧은 팔 프레임 좌표(x 길이, y 두께 0=바깥면) → 옆모습 (X,Y)
  const out = []
  for (let i = 0; i < a.tris.length; i += 3) out.push(a.tris[i] + (3 * P) / 2, a.tris[i + 1], a.tris[i + 2])
  for (let i = 0; i < b.tris.length; i += 3) { const q = toB(-b.tris[i], b.tris[i + 1]); out.push(q[0], q[1], -b.tris[i + 2]) } // 짧은 팔은 y 축으로 180° 돌려(각진 끝이 모서리 쪽) 놓는다
  // 모서리: 안쪽 모서리 I 가 중심, 반지름 T(판 두께)인 부채꼴. 바깥 모서리가 반지름 T 로 둥글게 굽고, 긴 팔 바닥(Q)에서 짧은 팔 시작(O)까지 이어진다(끝이 서로 접선).
  const arcN = Math.max(4, Math.round((phi / (Math.PI / 2)) * 16))
  const poly = [I, [3 * P, 0]]
  for (let k = 1; k <= arcN; k++) { const ang = -Math.PI / 2 + (phi * k) / arcN; poly.push([I[0] + T * Math.cos(ang), I[1] + T * Math.sin(ang)]) }
  const kit = makeKit(S.seg), { quad, tri, P: Pt } = kit
  poly.forEach((A, i) => { const B = poly[(i + 1) % poly.length], dx = B[0] - A[0], dy = B[1] - A[1], l = Math.hypot(dx, dy); quad(Pt(A[0], A[1], -W / 2), Pt(B[0], B[1], -W / 2), Pt(B[0], B[1], W / 2), Pt(A[0], A[1], W / 2), dy / l, -dx / l, 0) })
  for (let k = 1; k < poly.length - 1; k++) for (const z of [-W / 2, W / 2]) tri(Pt(poly[0][0], poly[0][1], z), Pt(poly[k][0], poly[k][1], z), Pt(poly[k + 1][0], poly[k + 1][1], z), 0, 0, Math.sign(z))
  const block = kit.result()
  const tris = new Float32Array(out.length + block.length); tris.set(out); tris.set(block, out.length)
  let x0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (let i = 0; i < tris.length; i += 3) { x0 = Math.min(x0, tris[i]); x1 = Math.max(x1, tris[i]); y1 = Math.max(y1, tris[i + 1]) }
  const cx = (x0 + x1) / 2
  for (let i = 0; i < tris.length; i += 3) tris[i] -= cx
  const connHoles = [
    ...a.holes.map((h) => ({ pos: [h.x + (3 * P) / 2 - cx, 0, h.z], dir: [0, -1, 0] })), // 긴 팔 구멍 3개
    ...b.holes.map((h) => { const q = toB(-h.x, 0); return { pos: [q[0] - cx, q[1], -h.z], dir: [-n[0], -n[1], 0] } }), // 짧은 팔 구멍 2개(바깥면에서 안쪽으로)
  ]
  return { tris, holes: connHoles.map((h) => ({ x: h.pos[0], z: h.pos[2] })), connHoles, size: [x1 - x0, y1, W] }
}

// 꺾인 프레임(135도:곧은 팔 6 + 꺾인 팔 4 / 90도: 3 + 3). 팔 끝 네 모서리만 둥글게 한다.
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
    straight: (nx, nz, crossAt, ext, squareEnd) => straightFrame(S, nx, nz, crossAt, !!squareEnd, ext), // squareEnd: +x 쪽 끝 두 모서리를 둥글리지 않는다
    bent: (straightHoles, slantHoles, bendDeg) => bentFrame(S, straightHoles, slantHoles, bendDeg),
    arc: () => arcFrame(S),
    grid: (cellList) => gridFrame(S, cellList),
    slot: (len, holeXs) => slotFrame(S, len, holeXs),
    lBracket: () => angleBracket(S, 90),
    vBracket: () => angleBracket(S, 120),
  }
}
