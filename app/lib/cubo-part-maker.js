// 큐보 부품 만들기 기본 규격 + 프레임 도형 생성기.
// 규격은 등록된 15프레임 3D 모델의 점 좌표를 직접 재서 정했다(2026-10-01, 사용자 확인):
//  - 판 두께 3mm, 구멍마다 위·아래 면에 1mm씩 솟은 테두리(바깥 반지름 4, 안쪽 반지름 3.5) → 전체 두께 5mm
//  - 가장 작은 구멍(판 안쪽 목) 반지름 2.75mm: 리벳 스냅핏이 걸리는 자리
//  - 폭 10mm, 구멍 중심은 폭의 가운데, 끝에서 첫 구멍까지 5mm(테두리), 구멍 간격 10mm
//  - 판 가장자리 둘레에도 폭 1mm·높이 1mm 테두리가 위·아래 면에 있다(모델 모서리 점 (±25,±5)·(±24,±4) 로 확인)
// 이 값으로 만든 15프레임(cubo-frame-mesh.js)의 높이별·반지름별 점 구조·전체 크기가 등록된 모델과 같고,
// 삼각형 2,280개·STL 111KB 로 등록된 15프레임(2,102개·105KB)과 비슷한 크기다. 구멍 테두리 바깥 반지름만 닿는 곳의 면 깨짐을 피하려 3.99 로 쓴다.
export const CUBO_FRAME_STD = {
  pitch: 10,        // 구멍 간격
  margin: 5,        // 끝에서 첫 구멍 중심까지 = 가장자리 여백
  width: 10,        // 프레임 폭
  plate: 3,         // 판 두께
  rimHeight: 1,     // 테두리가 면 위로 솟은 높이(위·아래 각각)
  edgeWall: 1,      // 판 가장자리 둘레 테두리 폭(위·아래 면에 높이 rimHeight 로 솟음)
  rimOuterR: 4,     // 테두리 바깥 반지름
  rimInnerR: 3.5,   // 테두리 안쪽 반지름(리벳·돌기가 처음 들어가는 입구)
  boreR: 2.75,      // 제일 작은 구멍 반지름(판 안쪽, 스냅핏 걸림)
  total: 5,         // plate + rimHeight*2
}

export const PART_STANDARD_TEXT = `# 큐보 부품 만들기 기본 규격 (프레임 기준)
등록된 15프레임 3D 모델을 직접 재서 정한 값이다. 새 프레임·판 부품을 만들 땐 이 값을 그대로 쓴다. 숫자는 mm.

| 항목 | 값 |
|---|---|
| 판 두께 | ${CUBO_FRAME_STD.plate} |
| 가장자리 테두리(판 둘레 한 바퀴, 위·아래 면) | 폭 ${CUBO_FRAME_STD.edgeWall}, 높이 ${CUBO_FRAME_STD.rimHeight} |
| 홀 테두리(구멍마다 위·아래 면에 솟은 고리) | 높이 ${CUBO_FRAME_STD.rimHeight}, 바깥 반지름 ${CUBO_FRAME_STD.rimOuterR}, 안쪽 반지름 ${CUBO_FRAME_STD.rimInnerR} (벽 0.5) |
| 전체 두께 | ${CUBO_FRAME_STD.total} (판 ${CUBO_FRAME_STD.plate} + 테두리 ${CUBO_FRAME_STD.rimHeight}×2) |
| 홀(제일 작은 구멍) | 반지름 ${CUBO_FRAME_STD.boreR} — 판 안쪽 ${CUBO_FRAME_STD.plate}mm 구간. 리벳 스냅핏이 걸리는 자리 |
| 폭 | ${CUBO_FRAME_STD.width} (구멍은 폭 가운데 한 줄) |
| 테두리(여백) | 끝 구멍 중심까지 ${CUBO_FRAME_STD.margin} |
| 구멍 간격 | ${CUBO_FRAME_STD.pitch} |

구멍 구조: 면에서 반지름 3.5 입구가 1mm 들어가고, 거기서 반지름 2.75 목(3mm)으로 한 단 좁아진다. 끼워지는 것은 스냅핏 리벳(돌기 반지름 3.2)과 블록 돌기(반지름 3.5~3.8, 높이 5)뿐이다.
좌표: 길이 x, 두께 y, 폭 z. 등록된 프레임과 같게 바닥이 y=0, x·z는 가운데가 0.
만드는 방법: make_frame_stl 로 크기를 확인하고, 사용자가 허락하면 apply_frame_to_part 로 부품 DB 행에 STL 을 넣는다(자르기 계산 없이 삼각형을 직접 짜서 팅커캐드 STL 정도로 가볍다). 넣은 뒤 부품 관리에서 열어 저장하면 썸네일이 다시 만들어진다.
부품 DB의 connectors 구멍 반지름 3.5/4 와 spec.boreRadius 2.73 이 서로 달라 보였던 것은 이 구조의 입구(3.5)와 목(2.75)이었다.
`
