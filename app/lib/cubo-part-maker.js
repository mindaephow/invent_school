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

// 블록 규격(등록된 2단·3단블록 모델을 직접 재고 사용자가 정함, 2026-10-01):
//  - 몸통은 길이 10×칸 수, 높이 10, 폭 10. 구멍은 위아래로 뚫린 프레임 구멍과 같은 구조(입구 반지름 3.5·깊이 1, 가장 좁은 곳 2.75).
//  - 구멍에 끼우는 돌기(앞뒤 면 칸마다 1개씩, 양 끝 1개씩)는 스냅핏: 길이 5, 밑동 1mm 반지름 3.8, 몸통 반지름 3.0, 끝 0.5mm 가 반지름 2.5 로 가늘어짐, 중심을 가로지르는 십자 홈 폭 1.2.
//  - 돌기·구멍은 10mm 격자 위, 돌기 높이는 몸통 높이의 가운데(5).
export const CUBO_BLOCK_STD = {
  height: 10, width: 10, pitch: 10,
  holeEntryR: 3.5, holeEntryDepth: 1, holeNeckR: 2.75,
  peg: { len: 5, collarR: 3.8, collarLen: 1, shaftR: 3.0, shaftEnd: 4.5, tipR: 2.5, slit: 1.2 },
}

export const PART_STANDARD_TEXT = `# 큐보 부품 만들기 기본 규격 (프레임·블록)
등록된 15프레임·3단블록 3D 모델을 직접 재서 정했고 사용자가 확인했다(2026-10-01). **새 프레임·블록을 만들 땐 이 값을 그대로 쓴다.** 숫자는 mm.
좌표: 길이 x, 높이(두께) y, 폭 z. 바닥이 y=0, x·z는 가운데가 0(등록된 부품과 같은 방향).

## 공통: 구멍(홀)
구멍은 면에서 반지름 ${CUBO_FRAME_STD.rimInnerR} 입구가 1mm 들어가고, 거기서 반지름 ${CUBO_FRAME_STD.boreR} 가장 좁은 구멍으로 한 단 좁아진다. 스냅핏(리벳·블록 돌기)이 이 좁은 구멍 둘레에 걸린다. 구멍은 10mm 격자 위, 간격 10.

## 프레임 (직선)
| 항목 | 값 |
|---|---|
| 판 두께 | ${CUBO_FRAME_STD.plate} |
| 홀 테두리(구멍마다 위·아래 면에 솟은 고리) | 높이 ${CUBO_FRAME_STD.rimHeight}, 바깥 반지름 ${CUBO_FRAME_STD.rimOuterR}(실제 모델은 3.99), 안쪽 반지름 ${CUBO_FRAME_STD.rimInnerR} |
| 가장자리 테두리(판 둘레 한 바퀴, 위·아래 면) | 폭 ${CUBO_FRAME_STD.edgeWall}, 높이 ${CUBO_FRAME_STD.rimHeight} |
| 전체 두께 | ${CUBO_FRAME_STD.total} (판 ${CUBO_FRAME_STD.plate} + 테두리 ${CUBO_FRAME_STD.rimHeight}×2) |
| 가장 좁은 구멍 | 반지름 ${CUBO_FRAME_STD.boreR} (판 안쪽 ${CUBO_FRAME_STD.plate}mm 구간) |
| 폭 / 여백 / 간격 | ${CUBO_FRAME_STD.width} / 끝 구멍 중심까지 ${CUBO_FRAME_STD.margin} / ${CUBO_FRAME_STD.pitch} |
길이 = 구멍 수 × 10 (15프레임 = 구멍 5개).

## 블록 (2단·3단 …)
| 항목 | 값 |
|---|---|
| 몸통 | 길이 10×칸 수, 높이 ${CUBO_BLOCK_STD.height}, 폭 ${CUBO_BLOCK_STD.width} (돌기까지 합치면 폭 20, 길이 +10) |
| 구멍 | 위아래로 뚫림. 프레임 구멍과 같은 구조(입구 ${CUBO_BLOCK_STD.holeEntryR}·깊이 ${CUBO_BLOCK_STD.holeEntryDepth}, 가장 좁은 곳 ${CUBO_BLOCK_STD.holeNeckR}). 칸마다 1개 |
| 돌기 개수·위치 | 구멍 칸마다 앞뒤(±z) 면에 1개씩 + 양 끝(±x)에 1개씩. 높이는 몸통 가운데(y=5) |
| 돌기 모양(스냅핏) | 길이 ${CUBO_BLOCK_STD.peg.len}. 밑동 ${CUBO_BLOCK_STD.peg.collarLen}mm 는 반지름 ${CUBO_BLOCK_STD.peg.collarR}, 몸통 반지름 ${CUBO_BLOCK_STD.peg.shaftR}(${CUBO_BLOCK_STD.peg.shaftEnd}mm 지점까지), 끝 0.5mm 는 반지름 ${CUBO_BLOCK_STD.peg.tipR} 로 가늘어짐 |
| 십자 홈 | 돌기 중심을 가로지르는 십자, 폭 ${CUBO_BLOCK_STD.peg.slit}, 돌기 길이 전체. 눌렸다가 펴져서 구멍에 꽉 끼게 하는 부분 |
구멍에 끼워지는 것은 스냅핏 리벳(돌기 반지름 3.2)과 블록 돌기뿐이고, 돌기에 홈이 있어도 된다.

## 만드는 방법 (메모리 없는 클로드도 가능)
1. 저장소(mindaephow/invent_school)가 있으면 STL 파일을 바로 만든다:
   node scripts/make-part-stl.mjs frame 5 "C:/Users/user/Downloads/15프레임_규격.stl"   (kind 는 frame 또는 block, 두 번째는 구멍 수/칸 수. 블록 3 = 3단블록)
   코드는 app/lib/cubo-frame-mesh.js · cubo-block-mesh.js · cubo-mesh-kit.js. 구멍·테두리를 자르는 계산 없이 삼각형을 직접 짜서 팅커캐드 STL 정도로 가볍다(15프레임 2,280개·111KB, 3단블록 2,408개·118KB).
2. 파일 위치를 사용자에게 알려 주면 사용자가 부품 만들기에서 STL 가져오기로 직접 등록한다. 색은 STL 에 없으니 등록할 때 정한다(사용자에게 색을 물어 알려 준다).
3. 저장소가 없으면 make_part_stl 로 크기만 확인하고, 사용자가 허락했을 때만 apply_part_to_db 로 부품 DB 에 넣는다.
4. 만든 모양은 부품 만들기 에디터나 화면에서 사용자가 눈으로 확인하게 한다. 구멍 둘레가 뻥 뚫려 보이면 면 방향이 뒤집힌 것이니 모든 면이 서로 맞는지(뒤집힌 모서리 0) 검사한다.
5. 브라켓·기어·T축 같은 다른 모양은 규칙이 아직 없다. 이미지를 받아 사용자와 먼저 정한 뒤 같은 방식으로 추가한다.

## 알아 둘 것
- 부품 DB 의 connectors 구멍 반지름 3.5/4 와 spec.boreRadius 2.73 이 서로 달라 보였던 것은 이 구조의 입구(3.5)와 가장 좁은 곳(2.75)이었다.
- 새로 만든 부품은 연결점(돌기·구멍 좌표)도 기록해야 조립 보기·검사에 쓸 수 있다(get_assembly_guide 7장).
- 등록된 2단·3단블록의 구멍 안쪽에는 단이 더 있고 서로 달랐는데, 사용자가 "블록 구멍은 프레임 구멍과 같게"로 정했다.
`
