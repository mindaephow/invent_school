---
name: feedback_provo_parts_in_parts_screen
description: 프로보 커넥트 부품(블럭·핀·꺽쇠) 3D 작업은 내 미리보기 HTML 이 아니라 앱의 부품 화면(부품 관리 3D 창)에서 보여 주고 진행
metadata:
  node_type: memory
  type: feedback
  originSessionId: fa8369ea-e68b-49f7-af41-dbe232f681e9
  modified: 2026-10-29T14:25:13.795Z
---

프로보 커넥트 3D 부품은 임시 미리보기 페이지(public/_pc_preview)로 보여 주지 말고, 앱의 **부품 화면**에서 진행한다(2026-10-29 "제발 부품 화면에서 진행하자", "앞으로도 이 관련은 부품 화면에서 진행해줘").

**Why:** 사용자가 실제로 쓰는 화면에서 모양·구멍·색을 판단해야 하고, 내 미리보기는 제목·색·카메라가 달라 판단이 어긋났다.

**How to apply:** 부품 STL 을 만들면 부품 화면에서 볼 수 있게 등록 경로를 사용자와 정한다. 서비스 키로 DB 를 직접 바꾸는 스크립트는 자동 권한 검사에 막혔다(공유 자원 수정) — 우회하지 말고 사용자가 허락하는 경로(부품 화면 STL 가져오기, 또는 MCP apply_part_to_db confirm)를 쓴다. 블럭은 흰색(#ffffff). 관련: [[project_cubo_part_standard]]
