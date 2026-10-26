---
name: feedback_3d_part_standard_check
description: 3D 부품 모델(큐보·에이스랩 모두)을 만들거나 고칠 때 get_part_standard 용량·검증 규칙을 시작 전에 읽고 숫자로 보고
metadata:
  type: feedback
---

3D 부품(평판·곡면판 등 에이스랩 포함)을 만들거나 고치기 전에 `get_part_standard`(원본 `app/lib/cubo-part-maker.js`)를 읽고, 끝나면 삼각형 수·KB(몸통/선 따로)·짝 없는 모서리·같은 방향 겹침·부피를 숫자로 보고한다. 같은 크기 비교 기준은 35프레임(큐보 6,316개·308KB / 에이스랩 2,552개·125KB).

**Why:** 2026-10-27 평판·곡면판을 "화면에서 맞으면 완료"로 만들다 곡면판 2.1MB·짝 없는 모서리 193개가 나왔고 사용자가 "큐보 기준이 아니고 3D 디자인 규칙인 거야"라며 화냈다. 규격 문서를 "큐보 전용"으로 치부한 것이 원인.
**How to apply:** 시작 전 규칙 3개를 적고, 칸으로 나눈 면은 `app/lib/cubo-mesh-repair.js` 의 conformTJunctions, 등록 전 assertPartMesh(스크립트에 이미 걸려 있음), 곡면 마디 각도 1° 미만, 뷰어는 STL 마다 x·z 가운데를 원점으로 옮기니 비대칭 모양은 미리 가운데 맞춤. 규칙 위반 시 문서·도구를 고친다 [[feedback_fix_rules_when_broken]] [[feedback_verify_before_claiming]].
