// 부품 정의(치수 등). design.html의 PART_DEFS와 100% 동일한 내용 — 새 부품을 추가할 땐 이 파일만 고치면 됨.
window.IVS_PART_DEFS = {
  panel:        { label: '타공판(12×12)', w: 250, h: 10, d: 250 }, // 구멍 12×12개(지름 10, 간격 20) + 사이사이·테두리 홈(폭 10) 13줄 = 한 변 25cm
  panelHalf:    { label: '타공판(6×12)',  w: 250, h: 10, d: 130 }, // half, cut along one axis
  panelQuarter: { label: '타공판(6×6)',   w: 130, h: 10, d: 130 }, // quartered
  pillar:       { label: '기둥(12칸)',    w: 240, h: 10, d: 20 },  // one full row of the panel: 12 holes
  pillarHalf:   { label: '기둥(6칸)',     w: 120, h: 10, d: 20 },  // half-length pillar: 6 holes
  hinge:    { label: '경첩',     w: 34,  h: 10, d: 26 },
  lbracket: { label: 'ㄱ자연결대', w: 16, h: 16, d: 16 }, // cube with a peg on all 6 faces
  tape:     { label: '종이테이프', w: 70, h: 4,  d: 20 },
  clip:     { label: '클립',     w: 20,  h: 8,  d: 34 }, // 아래쪽 핀은 타공판 구멍에, 위쪽 두 귀 사이에는 직선길 끝을 끼운다
  pin:      { label: '핀',       w: 10,  h: 40, d: 10 }, // 타공 구멍(지름 1cm)에 딱 맞는 핀. h가 길이이고 핀마다 바꿀 수 있다 (기본 4cm)
  straight:     { label: '직선길(12칸)', w: 240, h: 26, d: 26 }, // 기둥(12칸)과 같은 길이. h = 레일 높이(클립 홈 안쪽 높이와 같다), d = 폭
  straightHalf: { label: '직선길(6칸)',  w: 120, h: 26, d: 26 }, // 기둥(6칸)과 같은 길이
  halfRail: { label: '반원길', w: 120, h: 26, d: 73 }, // 반지름 60(지름 120=기둥 6칸과 같음), 레일 폭은 직선길과 같은 26(구슬 크기 호환). w=지름, d=중심~바깥레일까지. 지름 양 끝에 타공판 구멍에 꽂는 핀 — 두 개를 마주 놓으면 가운데에 구슬이 빠지는 구멍이 생긴다(치수는 사용자 확인 전 추정치)
  marble:   { label: '구슬',     w: 18,  h: 18, d: 18 }, // 재생하면 이 자리에서 굴러가기 시작하는 구슬
  start:    { label: '출발 지점', w: 40,  h: 40, d: 40 },  // 구슬이 없을 때 공이 시작하는 자리 (옮길 수 있음)
  goal:     { label: '도착 지점', w: 190, h: 14, d: 190 }  // 목표 깃발 (옮길 수 있음)
};
