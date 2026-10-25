// 큐보 리벳(스냅핏 리벳)을 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD(구멍 입구 3.5·목 2.75·판 3·테두리 1)에 맞춘다(2026-10-20).
// 프레임 두 장이 맞닿고(테두리끼리 마주 봄), 리벳 가운데가 맞닿는 면에 온다. 한쪽 끝이 프레임 한 장(두께 5)에 들어간다.
//  - 플랜지(가운데): 반지름 3.4(마주 본 테두리 안쪽 3.5 에 들어감), 두께 2(양쪽 테두리 높이 1 씩)
//  - 몸통: 반지름 2.65(목 2.75 에 여유 0.1), 플랜지에서 판 바깥 면까지 길이 3
//  - 머리: 반지름 3.2(목보다 0.45 큼 → 십자 홈이 눌렸다가 목을 지나 아랫 입구 3.5 에서 퍼짐), 길이 1. 앞 0.7 은 모따기(3.2→2.4), 뒷면은 비스듬한 경사(0.3 길이)라서 판 바깥 면에 걸리되 힘을 주면 눌려서 빠진다(분리 가능, 학생들이 끼웠다 뺐다 한다)
//  - 십자 홈 폭 1.2: 한쪽 끝 전체 길이(플랜지 윗면까지). 한쪽 길이 5, 전체 10 = 프레임 두 장 두께
// 좌표: 축 y(긴 방향), 가운데가 (0,0,0). 홈은 x 축·z 축 방향.
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export { trianglesToStl }

export const RIVET_STD = { collarR: 3.3, collarHalf: 1, shaftR: 2.6, shaftTo: 4, backRamp: 0.3, headR: 3.1, headStraight: 0, tipR: 2.5, pegEnd: 5, slit: 1.2 }
const R_ = RIVET_STD

// 한 갈래(사분면)의 단면 다각형: 홈 모서리 (w,w) → 홈 가장자리 중간점 → 반지름 R 원호(n 구간) → 반대쪽 홈 가장자리 중간점.
// 중간점은 몸통 반지름의 홈 가장자리 끝 위치로 모든 높이에서 같게 둔다(걸림턱 단에서 이웃 면과 모서리가 정확히 맞게). 몸통보다 작은 끝(모따기 끝)은 가운데로.
function legPoly(R, n, dedupe = false) {
  const w = R_.slit / 2, a0 = Math.asin(w / R), a1 = Math.acos(w / R)
  const xa = Math.sqrt(R_.shaftR * R_.shaftR - w * w), xe = Math.sqrt(R * R - w * w)
  const xm = R >= R_.shaftR ? xa : (w + xe) / 2
  const pts = [[w, w], [xm, w]]
  for (let k = 0; k <= n; k++) { const a = a0 + ((a1 - a0) * k) / n; pts.push([R * Math.cos(a), R * Math.sin(a)]) }
  pts.push([w, xm])
  if (!dedupe) return pts
  return pts.filter((q, i) => { const r = pts[(i + pts.length - 1) % pts.length]; return Math.hypot(q[0] - r[0], q[1] - r[1]) > 1e-9 })
}
const rotQ = (p, k) => { const c = Math.cos((k * Math.PI) / 2), s = Math.sin((k * Math.PI) / 2); return [Math.round((p[0] * c - p[1] * s) * 1e9) / 1e9, Math.round((p[0] * s + p[1] * c) * 1e9) / 1e9] }
export const legPolys = (R, n) => [0, 1, 2, 3].map((k) => legPoly(R, n, true).map((p) => rotQ(p, k)))

export function rivetTriangles(seg = 20, n = 6) {
  const kit = makeKit(seg)
  const peg = makeKit(seg)
  const { quad, P } = peg
  const levels = [
    { y: R_.collarHalf, R: R_.shaftR }, { y: R_.shaftTo, R: R_.shaftR }, // 몸통
    { y: R_.shaftTo + R_.backRamp, R: R_.headR }, // 머리 뒷면 경사(비스듬해서 힘을 주면 눌려서 빠진다)
    { y: R_.shaftTo + R_.backRamp + R_.headStraight, R: R_.headR }, // 머리 곧은 부분
    { y: R_.pegEnd, R: R_.tipR }, // 앞 모따기(끼울 때 안내) 끝
  ]
  for (let i = levels.length - 1; i > 0; i--) if (levels[i].y === levels[i - 1].y && levels[i].R === levels[i - 1].R) levels.splice(i, 1) // 곧은 부분이 0 이면 같은 단이 겹친다
  for (let k = 0; k < 4; k++) {
    const polys = levels.map((L) => legPoly(L.R, n).map((p) => rotQ(p, k)))
    for (let li = 0; li + 1 < levels.length; li++) {
      const A = polys[li], B = polys[li + 1], ya = levels[li].y, yb = levels[li + 1].y
      const m = A.length
      const cen = (pp) => [pp.reduce((s, q) => s + q[0], 0) / pp.length, pp.reduce((s, q) => s + q[1], 0) / pp.length]
      const ca = cen(A)
      for (let i = 0; i < m; i++) {
        const j = (i + 1) % m
        if (ya === yb) { // 걸림턱: 평평한 면(아래를 향함). 안쪽 다각형 A 와 바깥 다각형 B 사이
          quad(P(A[i][0], ya, A[i][1]), P(A[j][0], ya, A[j][1]), P(B[j][0], yb, B[j][1]), P(B[i][0], yb, B[i][1]), 0, -1, 0)
        } else { // 옆면: 다각형 바깥쪽을 향함
          const mx = (A[i][0] + A[j][0] + B[i][0] + B[j][0]) / 4 - ca[0], mz = (A[i][1] + A[j][1] + B[i][1] + B[j][1]) / 4 - ca[1]
          const ex = (A[j][0] - A[i][0]) + (B[j][0] - B[i][0]), ez = (A[j][1] - A[i][1]) + (B[j][1] - B[i][1]) // 아래 둘레 모서리가 한 점으로 모이면(뒷면 경사 시작) 위 모서리 방향도 함께 쓴다
          let nx = ez, nz = -ex
          if (nx * mx + nz * mz < 0) { nx = -nx; nz = -nz }
          const sl = Math.hypot(nx, nz) || 1
          const nyy = (levels[li].R - levels[li + 1].R) / (yb - ya) // 모따기면은 위를 향하는 성분이 생긴다
          quad(P(A[i][0], ya, A[i][1]), P(A[j][0], ya, A[j][1]), P(B[j][0], yb, B[j][1]), P(B[i][0], yb, B[i][1]), nx / sl, nyy, nz / sl)
        }
      }
    }
    const top = polys[polys.length - 1], yt = levels[levels.length - 1].y // 끝 면(위를 향함)
    const ap = 2 + Math.floor(n / 2) // 원호 가운데 점에서 부채꼴(모서리에서 펴면 홈 가장자리 세 점이 일직선이라 면이 사라진다)
    for (let i = 0; i < top.length; i++) {
      const j = (i + 1) % top.length
      if (i === ap || j === ap) continue
      peg.tri(P(top[ap][0], yt, top[ap][1]), P(top[i][0], yt, top[i][1]), P(top[j][0], yt, top[j][1]), 0, 1, 0)
    }
  }
  const pegArr = peg.result()
  kit.append(pegArr, (p) => p)
  kit.append(pegArr, (p) => [p[0], -p[1], -p[2]]) // x 축으로 180° 돌린 아래쪽 끝(회전이라 면 방향 유지)
  // 플랜지: 옆면 + 위·아래 면(갈래 단면 네 개를 뺀 원판)
  kit.cyl(0, 0, R_.collarR, -R_.collarHalf, R_.collarHalf, 1)
  const circle = circlePts(0, 0, R_.collarR, seg)
  const holes = legPolys(R_.shaftR, n)
  ringFace(kit, circle, holes, R_.collarHalf, 1)
  ringFace(kit, circle, holes, -R_.collarHalf, -1)
  return kit.result()
}
