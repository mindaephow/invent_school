// 로버트론 제품(에이스랩·로보타미주니어) 볼트·너트 생성기(사용자 2026-10-26: 12볼트·16볼트는 길이, 나사선 부분 지름 4, 너트 가운데 구멍 지름 4).
// 값 중 사용자가 말한 것: 나사선 지름 4(홀 사이즈), 길이 12·16, 너트 구멍 지름 4. 나머지(머리·너트 바깥 크기·육각 홈)는 큐보 볼트를 로버트론 프레임 칸(주머니 8×8)에 들어가게 줄여 유추한 값이다.
// 볼트 좌표: 축 y, 머리 아랫면 y=0, 머리 위로 +y, 나사선이 −y 로 길이 L. 너트: 두께가 y(0~height), 가운데가 (0,0).
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const BOLT_STD = { threadR: 2, tipR: 1.6, tipLen: 0.4, headR: 3.5, headH: 1, socketFlat: 2.5, socketDepth: 0.6, seg: 40 }
export const NUT_STD = { flat: 6.5, height: 2.5, boreR: 2, seg: 40 }

const hexPts = (flat) => { const R = flat / Math.sqrt(3); return Array.from({ length: 6 }, (_, k) => [R * Math.cos((Math.PI / 3) * k), R * Math.sin((Math.PI / 3) * k)]) } // 반시계, 꼭짓점이 x 축 위

// 다각형 옆벽(y0~y1). dir=+1 바깥 / −1 안쪽(다각형 속을 향함). 다각형은 반시계.
function polyWall(kit, poly, y0, y1, dir) {
  poly.forEach((A, i) => { const B = poly[(i + 1) % poly.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz)
    kit.quad([A[0], y0, A[1]], [B[0], y0, B[1]], [B[0], y1, B[1]], [A[0], y1, A[1]], (dir * dz) / l, 0, (-dir * dx) / l) })
}

export function boltTriangles(L, S = BOLT_STD) {
  const kit = makeKit(S.seg), { tri, P } = kit
  const sock = hexPts(S.socketFlat).reverse().reverse() // 반시계
  kit.cyl(0, 0, S.threadR, -L + S.tipLen, 0, 1) // 나사선 옆면
  for (let k = 0; k < S.seg; k++) { // 끝 모따기(반지름 threadR → tipR)와 끝면
    const a0 = (2 * Math.PI * k) / S.seg, a1 = (2 * Math.PI * (k + 1)) / S.seg, am = (a0 + a1) / 2
    const p = (r, a, y) => P(r * Math.cos(a), y, r * Math.sin(a))
    kit.quad(p(S.threadR, a0, -L + S.tipLen), p(S.threadR, a1, -L + S.tipLen), p(S.tipR, a1, -L), p(S.tipR, a0, -L), Math.cos(am), -0.5, Math.sin(am))
    tri(P(0, -L, 0), p(S.tipR, a0, -L), p(S.tipR, a1, -L), 0, -1, 0)
  }
  kit.cyl(0, 0, S.headR, 0, S.headH, 1) // 머리 옆면
  kit.annulus(0, 0, S.threadR, S.headR, 0, -1) // 머리 아랫면
  ringFace(kit, circlePts(0, 0, S.headR, S.seg), [sock], S.headH, 1) // 머리 윗면(육각 홈 자리 뚫림)
  polyWall(kit, sock, S.headH - S.socketDepth, S.headH, -1) // 홈 벽
  for (let i = 1; i < sock.length - 1; i++) tri(P(sock[0][0], S.headH - S.socketDepth, sock[0][1]), P(sock[i][0], S.headH - S.socketDepth, sock[i][1]), P(sock[i + 1][0], S.headH - S.socketDepth, sock[i + 1][1]), 0, 1, 0) // 홈 바닥
  return kit.result()
}

export function nutTriangles(S = NUT_STD) {
  const kit = makeKit(S.seg)
  const hex = hexPts(S.flat), bore = circlePts(0, 0, S.boreR, S.seg)
  polyWall(kit, hex, 0, S.height, 1) // 바깥 육각 옆면
  kit.cyl(0, 0, S.boreR, 0, S.height, -1) // 가운데 구멍 벽
  ringFace(kit, hex, [bore], 0, -1); ringFace(kit, hex, [bore], S.height, 1)
  return kit.result()
}
