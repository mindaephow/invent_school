// 큐보 볼트(8·12)·너트·서보고정볼트를 삼각형으로 직접 짠다(자르기 계산 없음). 모두 y 축이 중심축인 회전체 + 위 면의 홈.
// 규격 근거(교재 큐보3 3쪽 그림의 비율 + 프레임 구멍 구조 CUBO_FRAME_STD):
//  - 볼트: 몸통 반지름 2.0(프레임 가장 좁은 구멍 2.75 를 통과), 머리는 접시 모양(바깥 반지름 4.5 > 구멍 입구 3.5 라 구멍을 통과하지 못하고 테두리 위에 얹힘).
//    8볼트는 프레임 2장, 12볼트는 프레임 3장을 겹쳐 꿰고(몸통 길이 8·12 = 머리 밑에서 끝까지), 맨 아래 프레임 구멍에 아래에서 끼운 너트와 맞물린다.
//  - 너트: 구멍에 들어가는 모양. 아래 턱(반지름 3.4, 두께 1)이 구멍 입구(반지름 3.5, 깊이 1)에 들어가고, 몸통(반지름 2.7, 길이 3)이 좁은 구멍(2.75)을 지나 위로 올라간다. 가운데 나사 구멍 반지름 1.6.
//  - 서보고정볼트: 서보혼 나사 구멍(반지름 1.1)에 조이는 작은 볼트. 머리 반지름 3.4 라 서보혼의 위쪽 홈(반지름 3.5)에 들어간다. 머리 위에 작은 네모 홈 3개.
// 좌표: 중심축이 x=z=0, 높이 y. 볼트·서보고정볼트는 머리 밑면이 y=0, 몸통이 아래(-y), 너트는 바닥이 y=0.
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export { trianglesToStl }

export const BOLT_STD = {
  shaftR: 2.0, tipChamfer: 0.4,                       // 볼트 몸통 반지름, 끝 모따기
  head: { r: 4.5, edge: 0.8, topR: 3.2, h: 1.8 },    // 접시 머리: 가장자리 두께, 위 평평한 면 반지름, 전체 높이
  cross: { len: 2.2, w: 0.5, depth: 0.7 },           // 십자 홈(반 길이, 반 폭, 깊이)
  nut: { flangeR: 3.4, flangeH: 1, bodyR: 2.7, bodyH: 3, boreR: 1.6 },
  servo: { shaftR: 1.3, len: 6, headR: 3.4, edge: 1.2, topR: 3.0, h: 1.6, sq: 0.6, depth: 0.6 }, // 서보고정볼트
}

// 회전체: profile 은 (r, y) 점 목록을 "안쪽(축)에서 시작해 바깥을 지나 위로" 한 방향으로 간다(재료가 왼쪽). 마지막이 축이 아니어도 된다(위 면을 따로 덮을 때).
function revolve(kit, profile) {
  const { quad, P, seg } = kit
  for (let i = 0; i + 1 < profile.length; i++) {
    const [r0, y0] = profile[i], [r1, y1] = profile[i + 1]
    const dr = r1 - r0, dy = y1 - y0, l = Math.hypot(dr, dy)
    if (l < 1e-9) continue
    const nr = dy / l, ny = -dr / l // 오른쪽 법선 = 바깥
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2
      quad(P(r0 * Math.cos(a0), y0, r0 * Math.sin(a0)), P(r0 * Math.cos(a1), y0, r0 * Math.sin(a1)), P(r1 * Math.cos(a1), y1, r1 * Math.sin(a1)), P(r1 * Math.cos(a0), y1, r1 * Math.sin(a0)), nr * Math.cos(am), ny, nr * Math.sin(am))
    }
  }
}

// 위 면(높이 y, 반지름 R 원)에 구멍 모양(평면 점 목록 여러 개)을 뚫고, 구멍 벽과 바닥(깊이 d)을 만든다.
function topWithRecesses(kit, R, y, recesses, depth) {
  const { quad, P, seg } = kit
  ringFace(kit, circlePts(0, 0, R, seg), recesses, y, 1)
  for (const poly of recesses) {
    const ccw = poly.reduce((s, q, i) => { const r = poly[(i + 1) % poly.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) > 0
    const pts = ccw ? poly : poly.slice().reverse()
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length]
      quad(P(a[0], y, a[1]), P(b[0], y, b[1]), P(b[0], y - depth, b[1]), P(a[0], y - depth, a[1]), -(b[1] - a[1]), 0, b[0] - a[0]) // 홈 안쪽을 향함
    }
    ringFace(kit, pts, [], y - depth, 1) // 홈 바닥
  }
}

const crossPoly = (L, w) => [[L, -w], [L, w], [w, w], [w, L], [-w, L], [-w, w], [-L, w], [-L, -w], [-w, -w], [-w, -L], [w, -L], [w, -w]]
const squarePoly = (cx, cz, s) => [[cx - s / 2, cz - s / 2], [cx + s / 2, cz - s / 2], [cx + s / 2, cz + s / 2], [cx - s / 2, cz + s / 2]]

// 볼트: len = 8 또는 12 (머리 밑면에서 끝까지의 몸통 길이)
export function boltTriangles(len, seg = 24) {
  const kit = makeKit(seg)
  const { shaftR: R, tipChamfer: c, head: h, cross } = BOLT_STD
  revolve(kit, [[0, -len], [R - c, -len], [R, -len + c], [R, 0], [h.r, 0], [h.r, h.edge], [h.topR, h.h]])
  topWithRecesses(kit, h.topR, h.h, [crossPoly(cross.len, cross.w)], cross.depth)
  return kit.result()
}

// 너트: 바닥 y=0 (아래 턱) → 위로 몸통, 가운데 나사 구멍
export function nutTriangles(seg = 24) {
  const kit = makeKit(seg)
  const n = BOLT_STD.nut
  revolve(kit, [[n.boreR, 0], [n.flangeR, 0], [n.flangeR, n.flangeH], [n.bodyR, n.flangeH], [n.bodyR, n.flangeH + n.bodyH], [n.boreR, n.flangeH + n.bodyH], [n.boreR, 0]])
  return kit.result()
}

// 서보고정볼트: 머리 밑면 y=0, 몸통이 아래
export function servoBoltTriangles(seg = 24) {
  const kit = makeKit(seg)
  const s = BOLT_STD.servo
  const c = 0.3
  revolve(kit, [[0, -s.len], [s.shaftR - c, -s.len], [s.shaftR, -s.len + c], [s.shaftR, 0], [s.headR, 0], [s.headR, s.edge], [s.topR, s.h]])
  const sq = [squarePoly(0, 1.5, 1.2), squarePoly(-1.5, -0.9, 1.2), squarePoly(1.5, -0.9, 1.2)]
  topWithRecesses(kit, s.topR, s.h, sq, s.depth)
  return kit.result()
}
