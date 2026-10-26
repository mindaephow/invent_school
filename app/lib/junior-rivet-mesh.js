// 로보타미주니어 리벳(로버트론 제품). 큐보 리벳(cubo-rivet-mesh.js)과 같은 모양·길이(10)에 프레임이 바뀐 만큼만 맞춘다(사용자 2026-10-25).
// 큐보 프레임은 구멍 둘레 테두리(입구 반지름 3.5)가 있어 플랜지(반지름 3.3)가 그 안에 들어갔지만, 로버트론 프레임은 통판에 곧은 구멍(반지름 2.25)뿐이라
//  - 플랜지가 구멍 밖으로 나오면 프레임 두 장이 뜨므로, 플랜지는 프레임 칸(주머니, 8×8·깊이 1)에 들어가는 가운데 마디(반지름 2.7 = 지름 5.4, 두께 1)로 둔다(구멍보다 커서 빠지지 않고, 프레임 두 장은 틈 없이 붙는다. 사용자 2026-10-26: 처음 2.2 가 너무 얇았다).
//  - 구멍 반지름이 0.5 줄었으므로 몸통·머리·끝도 0.5 줄인다(몸통 2.1 = 구멍 2.25 에 0.15 여유, 머리 2.6 = 구멍보다 0.35 커서 십자 홈이 눌렸다가 낀다 — 큐보와 같은 여유).
// 길이 10(프레임 한 장 두께 5 씩), 머리 끝이 프레임 바깥 면과 같은 높이다.
import { RIVET_STD, rivetTriangles } from './cubo-rivet-mesh.js'

export const JUNIOR_RIVET_STD = { collarR: 3.1, collarHalf: 0.5, shaftR: 2.45, shaftTo: 4, backRamp: 0.3, headR: 2.95, headStraight: 0, tipR: 2.35, pegEnd: 5, slit: 1.2 } // 구멍 반지름 2.6(지름 5.2, 사용자 2026-10-27 "모든 프레임 홀사이즈 5.2")에 맞춤: 몸통 2.45(여유 0.15), 머리 2.95(구멍보다 0.35 큼), 끝 2.35, 가운데 마디 3.1(구멍보다 0.5 큼)

// 큐보 생성기가 모듈 값을 읽으므로, 만드는 동안만 로버트론 값으로 바꾸고 바로 되돌린다.
export function juniorRivetTriangles(seg = 20, n = 6) {
  const saved = { ...RIVET_STD }
  Object.assign(RIVET_STD, JUNIOR_RIVET_STD)
  try { return rivetTriangles(seg, n) } finally { Object.assign(RIVET_STD, saved) }
}
