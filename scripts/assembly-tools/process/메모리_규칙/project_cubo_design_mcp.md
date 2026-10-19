---
name: project-cubo-design-mcp
description: 큐보 3D 디자인 MCP(자유 배치용) 도구 구성·저장 형식·한계 — app/lib/cubo-design-tools.js, 기존 /api/mcp에 통합
metadata:
  node_type: memory
  type: project
  originSessionId: 61098ce2-0dc0-4d37-a9f6-ac22679a9310
---

2026-10-01 사용자 요청("3D 디자인 MCP 만들자")으로 구현(커밋 06013c5). 조립 보기(교재 단계 재생)용이 아니라 **설계 화면에 놓을 부품 배치를 클로드가 직접 만드는** 도구. 기존 발명학교 MCP(/api/mcp)에 통합 — 별도 커넥터 없음. 새 도구는 커넥터 새로고침/새 세션에서 보인다.

**도구 8개**: get_design_guide(작업 순서), list_design_parts(부품·돌기 구멍 id), **compute_attach**(고정 부품 구멍/돌기 + 새 부품 돌기/구멍 → p·r 계산, roll 0/90/180/270, 결합 검사로 확인), validate_design(이름·겹침·허공 부품·리벳 양 끝·T축 방향), save_design(검사 통과해야 저장, force 예외), list_designs, get_design, list_teachers.
**배치 형식**: [{ n, p:[x,y,z], r:[rx,ry,rz] }](조립 데이터와 같음). 저장 형식: ivs_teacher_projects(teacher_id, data={name, parts:[{type:'robot:<partId>', mount:'floor', pos, rot, quat}], createdAt, updatedAt}) — 설계 화면 "불러오기"에서 열림. 로컬 테스트: 교재 1단계 배치(35프레임+3단블록)가 compute_attach·validate_design 에서 결합 3건/문제 0건으로 맞음, 떠 있는 부품은 "허공" 경고.

**한계·미정**: 기본 선생님 계정 없음(save_design 에 teacherId 필요 — 환경변수로 기본값 두는 건 미정). 겹침 검사는 몸통 상자 근사(프레임·블록·브라켓·눈블록·기어·부시만), 연결점은 1권 부품 30종, 'auto' 신뢰도 부품은 확인 필요. save_design 의 실제 DB 쓰기는 배포 후 첫 호출에서 검증 필요(로컬에선 가짜 DB로만 테스트). 설계 화면 미리보기(사용자가 보기 전 이미지) 도구는 없음. [[project_cubo_assembly_rules]]
