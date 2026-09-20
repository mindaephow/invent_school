// 차시 카드(왼쪽 메뉴 맨 위) 내용. 배열이라 차시가 늘어나도 이 파일에 항목만 추가하면 됨.
// 지금은 design.html이 배열의 첫 번째 항목만 화면에 보여준다(여러 차시를 넘겨보는 화면은 아직 없음).
window.IVS_LESSONS = [
  {
    tag: '1분기 1차시',
    title: '중력',
    sub: '지구가 끌어당기는 힘',
    concept: '지구는 모든 것을 아래로 끌어당겨요. 그래서 구슬은 높은 곳에서 낮은 곳으로 굴러 내려와요.',
    mission: '중력의 에너지를 이용하여 구슬을 목표한 곳까지 도착하게 합니다.',
    steps: [
      '베이스 타공판을 클릭하고, 축 Z → 돌리기 → 0을 차례로 클릭해요.'
    ],
    // "샘플 열기" 버튼을 누르면 이 부품 배치를 스케치북에 그대로 보여준다 (design.html의 serializeParts()가 저장하는 형식과 같다)
    sample: [
      { type: 'panel', mount: 'floor', pos: [-110, 5, -110], quat: [0, 0, 0, 1], rot: [0, 0, 0], set: [1, 'ㄴ셋'] },
      { type: 'lbracket', mount: 'floor', pos: [-220, 28, -220], quat: [0, 0, 0.70711, 0.70711], rot: [0, 0, 90], set: [1, 'ㄴ셋'] },
      { type: 'lbracket', mount: 'floor', pos: [0, 28, -220], quat: [0, 0, 0.70711, 0.70711], rot: [0, 0, 90], set: [1, 'ㄴ셋'] },
      { type: 'panel', mount: 'floor', pos: [-110, 138, -233], quat: [0.70711, 0, 0, 0.70711], rot: [90, 0, 0], set: [1, 'ㄴ셋'] },
      { type: 'clip', mount: 'floor', pos: [-220, 248, -224], quat: [0.70711, 0, 0, 0.70711], rot: [90, 0, 0] },
      { type: 'straight', mount: 'floor', pos: [-220, 248, -206.8], quat: [0, 0, -0.08716, 0.99619], rot: [0, 0, -10] },
      { type: 'basket', mount: 'floor', pos: [-40, 188, -195], quat: [0, -0.70711, 0, 0.70711], rot: [0, -90, 0], goal: true }
    ]
  }
];
