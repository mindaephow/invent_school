// 프로보 커넥트 "1XN블럭"(한 줄 블럭)을 자르기 없이 삼각형으로 직접 짠다. 큐보 프레임과 같은 방식(cubo-mesh-kit·cubo-face-mesh)으로 가볍게 만든다.
// 규격(사용자 확인 2026-10-29): 길이 = 구멍 수 × 10, 폭 10, 두께 5(큐보 15프레임과 같은 크기), 구멍 간격 10. 길이 x, 두께 y(바닥 0~5), 폭 z, 가운데가 원점.
// 구멍 모양(교재 핀툴 사용법 7쪽 2D 그림 + 11쪽 3D 그림을 800dpi 로 확대해서 읽음): 위쪽은 둥근 입구(깊이 1.5)이고, 그 아래 가로 방향(x)으로 뚫린 **띠**가 있다(2D 그림의 흰 가운데 띠).
//   띠 위·아래(폭 z 방향)의 초승달 부분은 **턱**(그림의 회색 부분)이고, 턱 가운데에 사다리꼴 홈이 뚫려 있다. 턱 아래는 핀이 돌 수 있게 다시 둥글게 비어 있다.
//   핀 날개(발)를 사다리꼴 홈에 맞춰 끼운 다음 90° 돌리면 날개가 턱 아래에 걸린다(딸깍).
// ⚠ 추정(그림에서 비율만 읽음, 실물 치수가 오면 PROBO_STD 에서 바꾼다): 입구·아래 빈 곳 반지름 3.95, 턱 y 2~3.5(두께 1.5)·띠 반폭 1.45·사다리꼴 홈(밑 ±1.55 → 끝 ±0.8, z 3.1), 틈 바깥 반지름 3.85, 끝 둥근 반지름 5.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace } from './cubo-face-mesh.js'

export const PROBO_STD = { round: 0.6, toothN: 16, toothR: 4.3, pitch: 10, width: 10, thick: 5, boreR: 3.95, gapR: 3.75, barHalf: 2.65, keyBaseHalf: 1.55, keyTopHalf: 0.8, keyZ: 2.85, barY0: 2, barY1: 3.5, endR: 5 }

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
  const kit = makeKit(20), { quad, P } = kit
  const Y0 = 0, Yb0 = S.barY0, Yb1 = S.barY1, Y2 = S.thick
  const outer = rows === 1 ? stadiumPts(n, S) : roundRectPts(n, rows, S)
  const xs = Array.from({ length: n }, (_, i) => -((n - 1) * S.pitch) / 2 + i * S.pitch)
  const zs = Array.from({ length: rows }, (_, j) => -((rows - 1) * S.pitch) / 2 + j * S.pitch)
  const holes = []
  for (const z of zs) xs.forEach((c, i) => holes.push({ c, z, tooth: rows === 1 && (i === 0 || i === n - 1) }))
  const bores = holes.map((h) => circlePtsC(h.c, h.z, S.boreR))                   // 아래 빈 곳(둥근)
  const tops = holes.map((h, i) => h.tooth ? toothPts(h.c, h.z, S) : bores[i])  // 위 입구: 한 줄 블럭의 맨 끝 구멍은 톱니
  const opens = holes.map((h) => roundPoly(openPts(h.c, h.z, S), S.round))
  const m = holes.length
  const wall = (poly, outward, y0, y1) => {
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length], ex = b[0] - a[0], ez = b[1] - a[1]
      const nx = outward ? ez : -ez, nz = outward ? -ex : ex
      quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), nx, 0, nz)
    }
  }
  wall(outer, true, Y0, Y2)
  for (let i = 0; i < m; i++) { wall(bores[i], false, Y0, Yb0); wall(tops[i], false, Yb1, Y2) }   // 아래 빈 곳·위 입구 벽(끝 구멍은 톱니)
  for (const o of opens) wall(o, false, Yb0, Yb1)   // 턱 층의 뚫린 부분 벽
  ringFace(kit, outer, tops, Y2, 1)                                   // 윗면(입구 뚫림)
  ringFace(kit, outer, bores, Y0, -1)                                 // 아랫면(둥근 빈 곳 뚫림)
  for (let i = 0; i < m; i++) {
    ringFace(kit, tops[i], [opens[i]], Yb1, 1)                        // 턱 윗면(띠·홈 뚫림)
    ringFace(kit, bores[i], [opens[i]], Yb0, -1)                      // 턱 아랫면(띠·홈 뚫림)
  }
  return kit.result()
}
