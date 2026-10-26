// 축리벳(에이스랩·로보타미주니어): 리벳의 반쪽(가운데 마디 + 갈라진 스냅핏 머리 한쪽)과 4×4 십자 축 16mm 를 한 몸으로 이은 부품(사용자 2026-10-26: "축 부분 16mm + 리벳 반").
// 좌표: 축 방향 y. 마디(두께 1)가 y −0.5~0.5, 리벳 머리가 +y 쪽(0.5~5), 십자 축이 −y 쪽(마디 아랫면 −0.5 에서 16 만큼, 끝 −16.5).
import { juniorRivetTriangles, JUNIOR_RIVET_STD } from './junior-rivet-mesh.js'
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'
import { AXLE_STD } from './robotron-axle-mesh.js'

export const AXLE_RIVET_STD = { axleLen: 16, collarR: 3 } // collarR: 마디(테두리) 반지름 — 지름 6 의 원(사용자 2026-10-26). 프레임 구멍(지름 4.5)보다 커서 프레임 면에 걸린다.

const crossPts = (span, arm) => { const a = span / 2, w = arm / 2; return [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] }

export function axleRivetTriangles(S = AXLE_RIVET_STD, A = AXLE_STD) {
  const full = juniorRivetTriangles(), half = JUNIOR_RIVET_STD.collarHalf
  const keep = []
  for (let i = 0; i < full.length; i += 9) { // 아래쪽 리벳 반쪽(마디 아랫면 포함)은 버린다 — 모두 y ≤ −collarHalf 인 삼각형
    const ys = [full[i + 1], full[i + 4], full[i + 7]]
    if (Math.max(...ys) <= -half + 1e-6) continue
    if (Math.max(...ys) > half - 0.1 && Math.min(...ys) < -half + 0.1) continue // 원래 마디(지름 4.4) 옆면은 더 큰 테두리로 바꾼다
    for (let k = 0; k < 9; k++) keep.push(full[i + k])
  }
  const kit = makeKit(20), { quad, tri, P } = kit
  const y0 = -half, tip = crossPts(A.tipSpan, A.arm), body = crossPts(A.span, A.arm)
  const rings = [[y0, body], [y0 - (S.axleLen - A.taper), body], [y0 - S.axleLen, tip]]
  const R2 = JUNIOR_RIVET_STD.collarR
  kit.cyl(0, 0, S.collarR, -half, half, 1) // 테두리 옆면
  kit.annulus(0, 0, R2, S.collarR, half, 1) // 윗면 바깥 고리(원래 마디 윗면 바깥으로 이어짐)
  ringFace(kit, circlePts(0, 0, S.collarR, 20), [body], y0, -1) // 아랫면(십자 축 자리는 뚫림)
  for (let r = 0; r < rings.length - 1; r++) {
    const [ya, pa] = rings[r], [yb, pb] = rings[r + 1], ny = r === 1 ? -0.5 : 0
    for (let i = 0; i < pa.length; i++) {
      const j = (i + 1) % pa.length, dx = pa[j][0] - pa[i][0], dz = pa[j][1] - pa[i][1], l = Math.hypot(dx, dz)
      quad(P(pa[i][0], ya, pa[i][1]), P(pa[j][0], ya, pa[j][1]), P(pb[j][0], yb, pb[j][1]), P(pb[i][0], yb, pb[i][1]), dz / l, ny, -dx / l)
    }
  }
  const yt = y0 - S.axleLen
  for (let i = 0; i < tip.length; i++) { const j = (i + 1) % tip.length; tri(P(0, yt, 0), P(tip[i][0], yt, tip[i][1]), P(tip[j][0], yt, tip[j][1]), 0, -1, 0) } // 축 끝면
  const add = kit.result(), out = new Float32Array(keep.length + add.length)
  out.set(keep); out.set(add, keep.length)
  return out
}
