// 2&1 리벳(에이스랩): 한쪽은 프레임 한 장에 들어가는 리벳 반쪽(길이 5), 반대쪽은 프레임 두 장을 한 번에 지나 결합하는 긴 반쪽(길이 10) — 가운데 마디(두께 1)는 같다(사용자 2026-10-26).
// 로보타미주니어 리벳(junior-rivet-mesh.js)의 몸통·머리·십자 홈 규격 그대로, 길이만 다르다. 좌표: 축 y, 마디 −0.5~0.5, 짧은 쪽이 +y(0.5~5), 긴 쪽이 −y(−0.5~−10).
import { juniorRivetTriangles, JUNIOR_RIVET_STD } from './junior-rivet-mesh.js'

export const RIVET2IN1_STD = { shortFrames: 1, longFrames: 2, frameT: 5 }

// 같은 리벳을 몸통·머리 위치만 바꿔 만든다(한 쪽 길이 = 프레임 수 × 5, 머리 시작 = 길이 − 1).
function rivetWithPeg(frames, T) {
  const saved = { pegEnd: JUNIOR_RIVET_STD.pegEnd, shaftTo: JUNIOR_RIVET_STD.shaftTo }
  JUNIOR_RIVET_STD.pegEnd = frames * T; JUNIOR_RIVET_STD.shaftTo = frames * T - 1
  try { return juniorRivetTriangles() } finally { Object.assign(JUNIOR_RIVET_STD, saved) }
}

export function rivet2in1Triangles(S = RIVET2IN1_STD) {
  const half = JUNIOR_RIVET_STD.collarHalf
  const A = rivetWithPeg(S.shortFrames, S.frameT), B = rivetWithPeg(S.longFrames, S.frameT)
  const out = []
  const take = (arr, pred) => { for (let i = 0; i < arr.length; i += 9) { const mx = Math.max(arr[i + 1], arr[i + 4], arr[i + 7]); if (pred(mx)) for (let k = 0; k < 9; k++) out.push(arr[i + k]) } }
  take(A, (mx) => mx > -half + 1e-6) // 짧은 쪽(+y) + 마디 옆면·윗면
  take(B, (mx) => mx <= -half + 1e-6) // 긴 쪽(−y) + 마디 아랫면
  return Float32Array.from(out)
}
