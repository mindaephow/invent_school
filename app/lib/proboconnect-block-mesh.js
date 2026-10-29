// 프로보 커넥트 "1XN블럭"(한 줄 블럭)을 자르기 없이 삼각형으로 직접 짠다. 큐보 프레임과 같은 방식(cubo-mesh-kit·cubo-face-mesh)으로 가볍게 만든다.
// 규격(사용자 확인 2026-10-29): 길이 = 구멍 수 × 10, 폭 10, 두께 5(큐보 15프레임과 같은 크기), 구멍 간격 10. 길이 x, 두께 y(바닥 0~5), 폭 z, 가운데가 원점.
// 구멍 모양(교재 핀툴 사용법 7쪽 2D 그림 + 11쪽 3D 그림을 800dpi 로 확대해서 읽음): 위쪽은 둥근 입구(깊이 1.5)이고, 그 아래 가로 방향(x)으로 뚫린 **띠**가 있다(2D 그림의 흰 가운데 띠).
//   띠 위·아래(폭 z 방향)의 초승달 부분은 **턱**(그림의 회색 부분)이고, 턱 가운데에 사다리꼴 홈이 뚫려 있다. 턱 아래는 핀이 돌 수 있게 다시 둥글게 비어 있다.
//   핀 날개(발)를 사다리꼴 홈에 맞춰 끼운 다음 90° 돌리면 날개가 턱 아래에 걸린다(딸깍).
// ⚠ 추정(그림에서 비율만 읽음, 실물 치수가 오면 PROBO_STD 에서 바꾼다): 입구·아래 빈 곳 반지름 3.95, 턱 y 2~3.5(두께 1.5)·띠 반폭 1.45·사다리꼴 홈(밑 ±1.55 → 끝 ±0.8, z 3.1), 틈 바깥 반지름 3.85, 끝 둥근 반지름 5.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace } from './cubo-face-mesh.js'

export const PROBO_STD = { round: 0.6, toothN: 16, toothR: 4.3, pitch: 10, width: 10, thick: 5, boreR: 3.95, gapR: 3.75, barHalf: 2.65, keyBaseHalf: 1.55, keyTopHalf: 0.8, keyZ: 2.85, barY0: 2, barY1: 3.5, endR: 5, blindFloor: 1 }

// 톱니 구멍 입구(스텝핀이 딸깍딸깍 걸리는 곳): 1열 블럭의 맨 끝 구멍(사용자 설명 2026-10-29 + 책 9쪽 그림). 안쪽 반지름 boreR ~ 바깥 toothR 의 사다리꼴 톱니 toothN 개. ⚠ 톱니 수·깊이는 그림으로 못 읽은 추정.
export function toothPts(cx, cz, S = PROBO_STD) {
  const pts = [], n = S.toothN, step = (2 * Math.PI) / n
  for (let k = 0; k < n; k++) {
    const a = k * step
    for (const [f, r] of [[0.0, S.boreR], [0.18, S.boreR], [0.32, S.toothR], [0.68, S.toothR], [0.82, S.boreR]]) pts.push([cx + r * Math.cos(a + f * step), cz + r * Math.sin(a + f * step)])
  }
  return pts
}
// 꼭짓점 모서리를 둥글게(2차 곡선): 꺾인 각이 minTurn(도) 넘는 곳만 깎는다. 책 그림의 구멍 홈은 모서리가 둥글다(사용자 지적 2026-10-29 "내부 홀이 너무 각졌다").
export function roundPoly(pts, r = 0.55, steps = 4, minTurn = 25) {
  const n = pts.length, out = []
  for (let i = 0; i < n; i++) {
    const a = pts[(i + n - 1) % n], b = pts[i], c = pts[(i + 1) % n]
    const v1 = [a[0] - b[0], a[1] - b[1]], v2 = [c[0] - b[0], c[1] - b[1]], l1 = Math.hypot(...v1), l2 = Math.hypot(...v2)
    const cosA = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2), turn = 180 - (Math.acos(Math.max(-1, Math.min(1, cosA))) * 180) / Math.PI
    if (turn < minTurn) { out.push(b); continue }
    const d = Math.min(r, l1 / 2.2, l2 / 2.2), p0 = [b[0] + (v1[0] / l1) * d, b[1] + (v1[1] / l1) * d], p2 = [b[0] + (v2[0] / l2) * d, b[1] + (v2[1] / l2) * d]
    for (let s = 0; s <= steps; s++) { const u = s / steps; out.push([(1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * b[0] + u * u * p2[0], (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * b[1] + u * u * p2[1]]) }
  }
  return out
}
export function circlePtsC(cx, cz, r, seg = 24) {
  return Array.from({ length: seg }, (_, k) => [cx + r * Math.cos((2 * Math.PI * k) / seg), cz + r * Math.sin((2 * Math.PI * k) / seg)])
}
// 턱(막대 높이 층)에서 뚫린 부분 하나의 윤곽: 가운데 가로 띠(|z|≤barHalf) + 띠 위·아래 가운데의 사다리꼴 홈(핀 날개가 지나가는 자리). 반시계.
export function openPts(cx, cz, S = PROBO_STD, arcN = 6) {
  const th = Math.asin(S.barHalf / S.gapR), pts = []
  const arc = (from, to) => { for (let i = 0; i <= arcN; i++) { const a = from + ((to - from) * i) / arcN; pts.push([cx + S.gapR * Math.cos(a), cz + S.gapR * Math.sin(a)]) } }
  arc(-th, th) // 오른쪽 호(띠 오른쪽 끝)
  pts.push([cx + S.keyBaseHalf, cz + S.barHalf], [cx + S.keyTopHalf, cz + S.keyZ], [cx - S.keyTopHalf, cz + S.keyZ], [cx - S.keyBaseHalf, cz + S.barHalf]) // 위쪽 홈
  arc(Math.PI - th, Math.PI + th) // 왼쪽 호
  pts.push([cx - S.keyBaseHalf, cz - S.barHalf], [cx - S.keyTopHalf, cz - S.keyZ], [cx + S.keyTopHalf, cz - S.keyZ], [cx + S.keyBaseHalf, cz - S.barHalf]) // 아래쪽 홈
  return pts
}

// 양 끝이 둥근 납작한 윤곽(반시계). 구멍 n개 → 길이 n×10.
export function stadiumPts(n, S = PROBO_STD, seg = 12) {
  const hx = (n * S.pitch) / 2, cx = hx - S.endR, r = S.endR, pts = []
  for (let i = 0; i <= seg; i++) { const an = -Math.PI / 2 + (Math.PI * i) / seg; pts.push([cx + r * Math.cos(an), r * Math.sin(an)]) }
  for (let i = 0; i <= seg; i++) { const an = Math.PI / 2 + (Math.PI * i) / seg; pts.push([-cx + r * Math.cos(an), r * Math.sin(an)]) }
  return pts
}

// 두 줄 이상 블럭의 윤곽(반시계): 모서리 반지름 endR 의 둥근 직사각형. 구멍 n×rows 개 → 길이 n×10, 폭 rows×10. (책 11쪽 5X7블럭 그림: 구멍은 모두 둥근 입구, 모서리가 둥글다)
export function roundRectPts(n, rows, S = PROBO_STD, seg = 8) {
  const hx = (n * S.pitch) / 2, hz = (rows * S.pitch) / 2, r = S.endR, pts = []
  for (const [cx, cz, a0] of [[hx - r, -(hz - r), -Math.PI / 2], [hx - r, hz - r, 0], [-(hx - r), hz - r, Math.PI / 2], [-(hx - r), -(hz - r), Math.PI]])
    for (let i = 0; i <= seg; i++) { const an = a0 + (Math.PI / 2) * (i / seg); pts.push([cx + r * Math.cos(an), cz + r * Math.sin(an)]) }
  return pts
}

// 블럭(구멍 n개 × rows 줄)의 삼각형 목록: Float32Array(삼각형 수 × 9). 한 줄(rows=1)은 맨 끝 구멍이 톱니 입구.
export function probo1xNTriangles(n, S = PROBO_STD, rows = 1) {
  const outer = rows === 1 ? stadiumPts(n, S) : roundRectPts(n, rows, S)
  const xs = Array.from({ length: n }, (_, i) => -((n - 1) * S.pitch) / 2 + i * S.pitch)
  const zs = Array.from({ length: rows }, (_, j) => -((rows - 1) * S.pitch) / 2 + j * S.pitch)
  const holes = []
  for (const z of zs) xs.forEach((c, i) => holes.push({ c, z, tooth: rows === 1 && (i === 0 || i === n - 1) }))
  return plateTriangles(outer, holes, S)
}

// 윤곽(반시계)과 구멍 목록 {c: x, z, tooth, rot} 로 판을 짠다. rot=true 면 구멍의 띠 방향이 z 쪽(팔이 세로일 때).
export function plateTriangles(outer, holes, S = PROBO_STD) {
  const kit = makeKit(20), { quad, P } = kit
  const Y0 = 0, Yb0 = S.barY0, Yb1 = S.barY1, Y2 = S.thick
  const bores = holes.map((h) => circlePtsC(h.c, h.z, S.boreR))                   // 아래 빈 곳(둥근)
  const tops = holes.map((h, i) => h.tooth ? toothPts(h.c, h.z, S) : bores[i])  // 위 입구: 한 줄 블럭의 맨 끝 구멍은 톱니
  const opens = holes.map((h) => roundPoly(openPts(h.c, h.z, S).map(([x, z]) => h.rot ? [h.c - (z - h.z), h.z + (x - h.c)] : [x, z]), S.round))
  const m = holes.length
  const wall = (poly, outward, y0, y1) => {
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length], ex = b[0] - a[0], ez = b[1] - a[1]
      const nx = outward ? ez : -ez, nz = outward ? -ex : ex
      quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), nx, 0, nz)
    }
  }
  wall(outer, true, Y0, Y2)
  const F = S.blindFloor   // 블라인드 홀(꺽쇠 모서리 구멍)은 아래가 막혀 바닥 두께 F 가 남는다
  for (let i = 0; i < m; i++) { wall(bores[i], false, holes[i].blind ? F : Y0, Yb0); wall(tops[i], false, Yb1, Y2) }   // 아래 빈 곳·위 입구 벽(끝 구멍은 톱니)
  for (const o of opens) wall(o, false, Yb0, Yb1)   // 턱 층의 뚫린 부분 벽
  ringFace(kit, outer, tops, Y2, 1)                                   // 윗면(입구 뚫림)
  ringFace(kit, outer, bores.filter((_, i) => !holes[i].blind), Y0, -1)   // 아랫면(둥근 빈 곳 뚫림, 블라인드 홀은 막힘)
  holes.forEach((h, i) => { if (h.blind) ringFace(kit, bores[i], [], F, 1) })   // 블라인드 홀 바닥
  for (let i = 0; i < m; i++) {
    ringFace(kit, tops[i], [opens[i]], Yb1, 1)                        // 턱 윗면(띠·홈 뚫림)
    ringFace(kit, bores[i], [opens[i]], Yb0, -1)                      // 턱 아랫면(띠·홈 뚫림)
  }
  return kit.result()
}

// L2X2 꺽쇠(브라켓, 책 7쪽 부품표 그림): 폭 20 판 두 장(두께 5)이 직각으로 선다. 한 팔에 구멍 두 줄(폭 방향 나란히), 줄마다 모서리 칸(블라인드 홀) + 끝 쪽 뚫린 구멍.
// 팔 바깥 길이 20·20·두께 5(사용자 지시 2026-10-29, 25 로 만들었다가 "길이가 20 20 이야?" 지적). 큐보 브라켓(cubo-bracket-mesh.js)처럼 두 판이 모서리에서 겹쳐 이어진다.
// 좌표: 폭 x(가운데 0), 높이 y(바닥 0), 길이 z(세운 판 바깥면 0). 바닥 판 = z 0~25·y 0~5, 세운 판 = y 0~25·z 0~5.
// ⚠ 책 그림의 구멍은 모서리 칸과 끝 칸이 이어진 알약(타원)처럼 보이지만, 여기서는 구멍 둘을 따로 둔다(알약 모양은 추정 못 함).
export function endRoundRectPts(len, width, S = PROBO_STD, seg = 8) {
  const hx = len / 2, hz = width / 2, r = S.endR, pts = [[-hx, -hz]]
  for (const [cx, cz, a0] of [[hx - r, -(hz - r), -Math.PI / 2], [hx - r, hz - r, 0]])
    for (let i = 0; i <= seg; i++) { const an = a0 + (Math.PI / 2) * (i / seg); pts.push([cx + r * Math.cos(an), cz + r * Math.sin(an)]) }
  pts.push([-hx, hz])
  return pts
}
// 꺽쇠 일반형: cols = 폭 방향 구멍 줄 수(폭 = cols×10), db = 바닥 팔의 뚫린 구멍 칸 수(길이 방향), hw = 세운 팔의 뚫린 구멍 칸 수(높이 방향).
// 이름 L{벽 구멍 수}X{바닥 구멍 수} = L{cols×hw}X{cols×db}: L2X2 = (2,1,1), L2X4 = (2,2,1), L6X9 = (3,3,2). 팔마다 모서리 칸 하나가 더 있고, 모서리 칸은 블라인드 홀(바닥에서 열림).
export function proboBracketPieces(cols, db, hw, S = PROBO_STD) {   // 어긋남 없이 맞춘 판 조각들(합치기는 make-proboconnect-block.mjs 가 manifold-3d 로 한다)
  const arm = (cells, trim, shrink = 0) => {   // 팔 바깥 길이 = (칸 수+1)×10 (모서리 칸 + 뚫린 칸들). trim = 모서리 쪽에서 잘라 낼 길이, shrink = 폭을 줄일 양(판 면이 같은 평면에 겹치지 않게)
    const len = (cells + 1) * S.pitch - trim, width = cols * S.pitch - shrink
    const hx = len / 2, holes = []
    for (let j = 0; j < cols; j++) {
      const z = -((cols - 1) * S.pitch) / 2 + j * S.pitch
      for (let k = 1; k <= cells; k++) holes.push({ c: S.pitch * k + S.pitch / 2 - trim - hx, z })   // 모서리에서 10k+5 되는 곳
    }
    return { len, trim, plate: plateTriangles(endRoundRectPts(len, width, S), holes, S) }
  }
  // 모서리 칸(10×10×10 한 칸)의 블라인드 홀 둘(사용자 지시 2026-10-29 "꺽쇠 부분은 블라인드 홀", "바닥은 왜 안 만들었어?", "원래 만든 걸 없애라고 했어?"):
  //  · 뒤(바깥)면 z=0 에서 열리고 안쪽(z 4~5)이 막힌 구멍 — 세운 팔의 아래쪽 칸(y 0~10)
  //  · 바닥 y=0 에서 열리고 위쪽(y 4~5)이 막힌 구멍 — 바닥 팔의 모서리 칸(깊이 0~10)
  const cornerHoles = (axis) => plateTriangles([[-5, -cols * 5], [5, -cols * 5], [5, cols * 5], [-5, cols * 5]], Array.from({ length: cols }, (_, j) => ({ c: 0, z: -((cols - 1) * S.pitch) / 2 + j * S.pitch, blind: true })), S)
  const back = cornerHoles(), bottom = cornerHoles()
  const base = arm(db, 9.5), wall = arm(hw, 9.5), P = {}   // 바닥 판·세운 판은 모서리 칸 속 9.5 부터(모서리 칸 구멍 빈 곳은 8.95 까지)
  const put = (name, tris, f) => { const k = makeKit(20); k.append(tris, f); P[name] = k.result() }
  put('back', back, ([u, v, tt]) => [-tt, u + 5, 5 - v])                                  // 뒤 블라인드 칸(세운 판 아래 10): 열린 쪽이 바깥 z=0
  put('bottom', bottom, ([u, v, tt]) => [tt, 5 - v, u + 5])                               // 바닥 블라인드 칸(바닥 판 모서리 10): 열린 쪽이 바닥 y=0
  put('base', base.plate, ([u, v, tt]) => [-tt, v, u + base.len / 2 + base.trim])         // 바닥 판(깊이 9.5 부터)
  put('wall', wall.plate, ([u, v, tt]) => [tt, u + wall.len / 2 + wall.trim, v])          // 세운 판(높이 9.5 부터)
  P.width = cols * S.pitch
  return P
}
