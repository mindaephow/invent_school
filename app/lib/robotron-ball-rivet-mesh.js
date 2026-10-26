// 볼리벳(에이스랩·로보타미주니어): 리벳의 반쪽(가운데 마디 + 갈라진 스냅핏 머리 한쪽) 아래에 반지름 ballR(지름 8) 반구(볼)를 붙인 부품(사용자 2026-10-27 "볼리벳 만들자, 리벳반쪽 +1.8mm 반구 붙여줘").
// 좌표: 축 방향 y. 마디(두께 1)가 y −0.5~0.5, 리벳 머리가 +y 쪽(0.5~5), 반구가 −y 쪽(마디 아랫면 −0.5 에서 1.8 만큼, 끝 −2.3). 반구가 마디보다 크면 반구 평평한 윗면(반지름 마디~ballR 고리, 위를 본다)이 마디 아래에 붙는다.
import { juniorRivetTriangles, JUNIOR_RIVET_STD } from './junior-rivet-mesh.js'
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const BALL_RIVET_STD = { ballR: 4 } // 반구 지름 8(사용자 2026-10-27 "8mm 지름", 처음 "+1.8mm", 그다음 "18mm(지름)")

export function ballRivetTriangles(S = BALL_RIVET_STD, seg = S.ballR > 3 ? 32 : 20, lat = S.ballR > 3 ? 16 : 10) {
  const full = juniorRivetTriangles(), half = JUNIOR_RIVET_STD.collarHalf
  const keep = []
  for (let i = 0; i < full.length; i += 9) { // 아래쪽 리벳 반쪽(마디 아랫면 포함)은 버린다 — 모두 y ≤ −collarHalf 인 삼각형
    if (Math.max(full[i + 1], full[i + 4], full[i + 7]) <= -half + 1e-6) continue
    for (let k = 0; k < 9; k++) keep.push(full[i + k])
  }
  const kit = makeKit(seg), { tri, P } = kit, y0 = -half, R = S.ballR
  const CR = JUNIOR_RIVET_STD.collarR
  if (R < CR) kit.annulus(0, 0, R, CR, y0, -1) // 마디 아랫면(반구 둘레 고리)
  else if (R > CR) ringFace(kit, circlePts(0, 0, R, seg), [circlePts(0, 0, CR, 20)], y0, 1) // (안쪽은 리벳 마디의 20분할에 맞춘다) 반구 평평한 윗면(마디 밖으로 나온 고리, 위를 본다)
  const pt = (i, j) => { const th = (Math.PI / 2) * i / lat, a = (2 * Math.PI * j) / seg; return P(R * Math.cos(th) * Math.cos(a), y0 - R * Math.sin(th), R * Math.cos(th) * Math.sin(a)) } // i=0 적도, i=lat 바닥 꼭짓점
  const nrm = (p) => [p[0], p[1] - y0, p[2]]
  for (let i = 0; i < lat; i++) for (let j = 0; j < seg; j++) {
    const a = pt(i, j), b = pt(i, j + 1), c = pt(i + 1, j + 1), d = pt(i + 1, j), n = nrm([(a[0] + b[0] + c[0] + d[0]) / 4, (a[1] + b[1] + c[1] + d[1]) / 4, (a[2] + b[2] + c[2] + d[2]) / 4])
    tri(a, b, c, n[0], n[1], n[2]); tri(a, c, d, n[0], n[1], n[2])
  }
  const add = kit.result(), out = new Float32Array(keep.length + add.length)
  out.set(keep); out.set(add, keep.length)
  return out
}
