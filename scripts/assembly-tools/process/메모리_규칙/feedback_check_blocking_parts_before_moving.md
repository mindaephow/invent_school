---
name: check-blocking-parts-before-moving
description: 부품을 돌리거나 옮기는 단계는 책을 먼저 보고, 길을 막는 부품(2단블록 등)을 계산한 뒤 정한다; 겹침 경고는 넘기지 않는다
metadata:
  type: feedback
---

투석기 22번에서 책을 안 보고 팔을 90° 세워 2단블록을 뚫게 했다가 "책 안 보고 그냥 하는구나, 막고 있는데 어떻게 들어가"라고 지적받았다.

**Why:** "부품 없는 단계(noPart)"라도 실제로는 이동·회전 동작일 수 있고, 겹침 경고를 참고용으로 넘기면 물리적으로 불가능한 모양이 나온다.

**How to apply:** 단계 시작 때 책 그림에서 움직이는 부품을 찾고, 그 길에 막는 부품이 있는지 AABB·각도 스윕으로 계산해 한계 각도를 정한다. 고무줄처럼 규격 없는 것은 `step.bands`로 바깥·통과·8자·팽팽하게 그린다 ([[feedback_checklist_before_done]], [[feedback_read_neighbors_and_finished_photo]]).
