// 로봇 커리큘럼 카테고리(브랜드별 권 수). 종류(=회차) 개수는 권마다 10~12개라는데 정확한 값이 아직 없어
// 우선 12개씩 둔다 — 실제 값이 정해지면 이 파일의 IVS_ROBOT_SESSIONS_PER_VOLUME(또는 카테고리별 값)만 고치면 됨.
window.IVS_ROBOT_CATEGORIES = [
  { id: 'cubo', name: '큐보', volumes: 3 },
  { id: 'meta', name: '메타', volumes: 7 },
  { id: 'proboconnect', name: '프로보 커넥트', volumes: 7 },
  { id: 'skyrobo', name: '스카이 로보', volumes: 7 },
  { id: 'xrobo', name: 'X로보', volumes: 7 }
];
window.IVS_ROBOT_SESSIONS_PER_VOLUME = 12;
