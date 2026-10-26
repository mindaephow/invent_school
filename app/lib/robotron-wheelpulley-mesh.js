// 휠풀리(에이스랩·로보타미주니어, 그레이) — 우선 기본 모양(사용자 2026-10-26): 휠가이드와 크기가 비슷한 지름 30 원판, 원판(바닥) 두께 5, 옆면은 휠가이드와 같은 실타래(1·2·1 → 두께 5 에서는 1.5·2·1.5, 홈 깊이 1),
// 가운데 한쪽에 지름 10·높이 10 돌기(전체 높이 15)에 지름 8·깊이 10 원기둥 구멍을 돌기 끝에서 원판 윗면까지 뚫고(사용자 2026-10-26), 원판 가운데는 나사 구멍 대신 4×4 십자 축이 들어가는 열십자 홀(4.4×4.4, 팔 폭 1.4)이 원판을 관통해 원기둥 구멍과 이어진다. 그리고 중심에서 피치 10 떨어진 규격 홀(지름 4.5) 4개를 원판에 뚫는다 — 바닥 쪽에서 본 화면의 위·아래·좌·우 방향(모델 축 x·z 에 대해 45°, 좌표 (±7.07, ±7.07))(사용자 2026-10-26). 바닥에는 구멍 5곳(가운데 열십자 + 규격 홀 4개)마다, 윗면에는 중심을 뺀 규격 홀 4곳마다 깊이 1 사각 홈(8×8, 구멍 줄에 맞춰 모델 축에 대해 45° 돌림 = 프레임 칸처럼)을 판다(사용자 2026-10-26). 돌기에는 x 축 방향으로 폭(두께) 2·깊이 6 홈(돌기 끝에서 아래로)을 파서 돌기 벽이 ±x 쪽에서 갈라지고, 홈 끝(바닥)은 반지름 slotW/2 의 반원으로 둥글다(사용자 2026-10-26). 나머지 구멍·홈은 정해지면 추가.
// 좌표: 축 y, 원판 아랫면 y=0, 윗면 y=5, 돌기 끝 y=15.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const WHEELPULLEY_STD = { discR: 15, discH: 5, bossR: 5, bossH: 10, boreR: 4, grooveW: 2, grooveDepth: 1, crossSpan: 5, crossArm: 1.4, holeR: 2.6, holePitch: 10, pocketSide: 8, pocketDepth: 1, slotW: 2, slotDepth: 6, seg: 64 }

const diamond = (cx, cz, side) => { const d = side / Math.SQRT2; return [[cx + d, cz], [cx, cz + d], [cx - d, cz], [cx, cz - d]] } // 한 변 side 인 정사각형을 45° 돌린 모양(반시계)

export function wheelPulleyTriangles(S = WHEELPULLEY_STD) {
  const kit = makeKit(S.seg), { quad, P } = kit
  const a = S.crossSpan / 2, w = S.crossArm / 2, top = S.discH + S.bossH
  const cross = [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] // 열십자(반시계)
  const h = S.holePitch / Math.SQRT2, spots = [[h, h], [h, -h], [-h, h], [-h, -h]] // 규격 홀 4개(중심에서 피치 10, 모델 축에 대해 45° 방향)
  const g0 = (S.discH - S.grooveW) / 2, g1 = g0 + S.grooveW, rg = S.discR - S.grooveDepth
  kit.cyl(0, 0, S.discR, 0, g0, 1); kit.cyl(0, 0, rg, g0, g1, 1); kit.cyl(0, 0, S.discR, g1, S.discH, 1) // 원판 옆면(가운데 실타래 홈)
  kit.annulus(0, 0, rg, S.discR, g0, 1); kit.annulus(0, 0, rg, S.discR, g1, -1) // 홈 어깨
  // 돌기(관): 아래 구간 y 5~(15−slotDepth)은 온전한 관, 위 구간은 x 축 방향 홈(폭 slotW, z ±slotW/2)으로 +z·−z 두 조각 C 모양으로 갈라진다.
  const ys = top - S.slotDepth, sh = S.slotW / 2, ao = Math.asin(sh / S.bossR), ai = Math.asin(sh / S.boreR), NA = 24
  const NG = 12 // 홈 바닥 반원의 분할 수
  const yc = ys + sh // 반원 중심 높이(반원 바닥 = ys)
  const yp = (z) => yc - Math.sqrt(Math.max(0, sh * sh - z * z)) // 홈 바닥 둥근 모양: 높이(z 에 따라)
  const zs = Array.from({ length: NG + 1 }, (_, k) => -sh + (2 * sh * k) / NG) // 홈 폭 방향 표본(안·바깥이 같은 z 에서 맞게)
  const arc = (r, t0, t1, n = NA) => Array.from({ length: n + 1 }, (_, k) => { const t = t0 + ((t1 - t0) * k) / n; return [r * Math.cos(t), r * Math.sin(t)] })
  const gapR = (r) => zs.map((z) => [Math.sqrt(r * r - z * z), z]) // +x 쪽 홈 자리 선(z 증가 = 반시계)
  const gapL = (r) => zs.slice().reverse().map((z) => [-Math.sqrt(r * r - z * z), z]) // −x 쪽(z 감소 = 반시계)
  const arcWall = (pts, y0, y1, dir) => { for (let k = 0; k < pts.length - 1; k++) { const A = pts[k], B = pts[k + 1], mx = (A[0] + B[0]) / 2, mz = (A[1] + B[1]) / 2, l = Math.hypot(mx, mz); quad(P(A[0], y0, A[1]), P(B[0], y0, B[1]), P(B[0], y1, B[1]), P(A[0], y1, A[1]), (dir * mx) / l, 0, (dir * mz) / l) } }
  const parts = (r, a) => [arc(r, a, Math.PI - a), gapL(r), arc(r, Math.PI + a, 2 * Math.PI - a), gapR(r)] // 관 한 바퀴 = +z 조각 · 왼 홈 자리 · −z 조각 · 오른 홈 자리
  for (const pts of parts(S.bossR, ao)) arcWall(pts, S.discH, ys, 1)
  for (const pts of parts(S.boreR, ai)) arcWall(pts, S.discH, ys, -1) // 홈 아래 구간 옆면(온전한 관)
  const ring = (r, a) => { const q = parts(r, a); return [...q[0], ...q[1].slice(1), ...q[2].slice(1), ...q[3].slice(1, -1)] } // 관 한 바퀴를 같은 꼭짓점의 다각형으로(반시계)
  const bossPoly = ring(S.bossR, ao), borePoly = ring(S.boreR, ai)
  for (const [base] of [[0], [Math.PI]]) { // +z 조각, −z 조각(홈 위 구간)
    const oPts = arc(S.bossR, base + ao, base + Math.PI - ao), iPts = arc(S.boreR, base + ai, base + Math.PI - ai)
    arcWall(oPts, ys, yc, 1); arcWall(oPts, yc, top, 1); arcWall(iPts, ys, yc, -1); arcWall(iPts, yc, top, -1) // 홈 위 구간 바깥·안쪽 옆면(두 조각, 반원 중심 높이 yc 에서 한 번 나눠 홈 옆벽·홈 바닥 둥근 벽 조각과 꼭짓점이 맞게)
    ringFace(kit, [...oPts, ...iPts.slice().reverse()], [], top, 1) // 조각 끝면(C 모양)
    for (const sg of [1, -1]) { // 홈 옆벽(조각 쪽 평면 z = ±sh, 반원 중심 높이 yc 에서 끝까지), 홈 속을 향함
      const zz = base === 0 ? sh : -sh, ns = base === 0 ? -1 : 1, xo = sg * Math.sqrt(S.bossR ** 2 - sh ** 2), xi = sg * Math.sqrt(S.boreR ** 2 - sh ** 2)
      quad(P(xi, yc, zz), P(xo, yc, zz), P(xo, top, zz), P(xi, top, zz), 0, 0, ns)
    }
  }
  for (const sg of [1, -1]) { // ±x 홈 자리: 바깥·안쪽 벽 조각(홈 바닥 반원 곡선 아래)과 둥근 바닥 면
    for (const [r, dir] of [[S.bossR, 1], [S.boreR, -1]]) for (let k = 0; k < NG; k++) {
      const z0 = zs[k], z1 = zs[k + 1], x0 = sg * Math.sqrt(r * r - z0 * z0), x1 = sg * Math.sqrt(r * r - z1 * z1), mx = (x0 + x1) / 2, mz = (z0 + z1) / 2, l = Math.hypot(mx, mz)
      quad(P(x0, ys, z0), P(x1, ys, z1), P(x1, yp(z1), z1), P(x0, yp(z0), z0), (dir * mx) / l, 0, (dir * mz) / l)
    }
    for (let k = 0; k < NG; k++) { // 둥근 홈 바닥 면(반원 곡면, 안쪽 반지름 ~ 바깥 반지름 사이)
      const z0 = zs[k], z1 = zs[k + 1], xi0 = sg * Math.sqrt(S.boreR ** 2 - z0 * z0), xi1 = sg * Math.sqrt(S.boreR ** 2 - z1 * z1), xo0 = sg * Math.sqrt(S.bossR ** 2 - z0 * z0), xo1 = sg * Math.sqrt(S.bossR ** 2 - z1 * z1), zm = (z0 + z1) / 2
      quad(P(xi0, yp(z0), z0), P(xo0, yp(z0), z0), P(xo1, yp(z1), z1), P(xi1, yp(z1), z1), 0, yc - yp(zm), -zm) // 법선: 반원 중심 쪽(홈 속)
    }
  }
  const disc = circlePts(0, 0, S.discR, S.seg)
  const D = S.pocketDepth, circ = ([x, z]) => circlePts(x, z, S.holeR, S.seg)
  const wall = (pl, y0, y1) => pl.forEach((A, i) => { const B = pl[(i + 1) % pl.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], y0, A[1]), P(B[0], y0, B[1]), P(B[0], y1, B[1]), P(A[0], y1, A[1]), -dz / l, 0, dx / l) }) // 구멍·홈 속을 향한 벽
  const botSq = [[0, 0], ...spots].map(([x, z]) => diamond(x, z, S.pocketSide)), topSq = spots.map(([x, z]) => diamond(x, z, S.pocketSide))
  spots.forEach((c) => kit.cyl(c[0], c[1], S.holeR, D, S.discH - D, -1)) // 규격 홀 벽(아래·위 홈 바닥 사이)
  wall(cross, D, S.discH) // 열십자 홀 벽(아래 홈 바닥에서 원판 윗면까지)
  botSq.forEach((sq) => wall(sq, 0, D)); topSq.forEach((sq) => wall(sq, S.discH - D, S.discH)) // 아래·위 사각 홈 벽
  ringFace(kit, disc, botSq, 0, -1) // 바닥(홈 5곳 뚫림)
  ringFace(kit, disc, [bossPoly, ...topSq], S.discH, 1) // 원판 윗면(돌기 자리·위 홈 4곳 뚫림)
  botSq.forEach((sq, i) => ringFace(kit, sq, [i === 0 ? cross : circ(spots[i - 1])], D, -1)) // 아래 홈 바닥(열십자·규격 홀 뚫림)
  topSq.forEach((sq, i) => ringFace(kit, sq, [circ(spots[i])], S.discH - D, 1)) // 위 홈 바닥(규격 홀 뚫림)
  ringFace(kit, borePoly, [cross], S.discH, 1) // 원기둥 구멍 바닥(= 원판 윗면 높이, 열십자 홀 뚫림)
  return kit.result()
}
