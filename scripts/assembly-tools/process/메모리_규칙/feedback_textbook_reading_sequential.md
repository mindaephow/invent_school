---
name: feedback-textbook-reading-sequential
description: 교재(조립도)는 순서대로만 읽고 만든다 — 쓴 부품·남은 부품·빈 구멍으로 후보를 좁힌다; 중간 쪽 한 장만 붙들고 튜닝하지 말 것
metadata:
  node_type: memory
  type: feedback
  originSessionId: 244e9d78-5086-47fd-86e5-53fbbaab0aeb
  modified: 2026-10-03T15:09:31.460Z
---

조립은 항상 1단계부터 순서대로 쌓인다(뒤에서부터·중간부터 만드는 일은 없다). 단계 k 에서 이미 쓴 부품, 교재 LIST 에서 남은 부품, 이미 찬 구멍을 알 수 있으므로 앞이 틀리지 않았다면 끼울 수 있는 곳은 **빈 구멍뿐**이고, 새 부품이 들어왔다면 이유가 있다(돌기 수만큼 같은 간격의 빈 구멍). 구멍은 일일이 세지 말고 부품 양 끝(경계) 사이 위치로 본다(35프레임은 한 줄 5칸이라 6번째는 없고, 정가운데면 3번째). 방향이 바뀌어 헷갈리면 완성 전체샷과 다음 단계 그림으로 거꾸로 유추한다. 교재가 초록 원으로 위치를 직접 그려 주므로 후보 자리 계산이나 원 위치 비율 도구는 만들지 않는다(사용자가 불필요하다고 함).

**Why:** 2026-10-03~04 사용자가 설명함. 나는 66쪽 한 장에서 흰 구멍 검출을 눈대중으로 반복 튜닝하며 "마구잡이로 구멍을 세고" 있었고(정답 없는 시험, 같은 그림으로 고치고 같은 그림으로 확인), 사용자가 "순서대로 따라가라 했는데 왜 66페이지 확인을 하고 있냐"며 크게 화냄. 가장 중요한 일은 초록 원의 위치를 찾는 것.

**How to apply:** 새 조립도는 첫 쪽·1단계부터 한 단계씩(읽기 → get_step_context 로 직전 상태 → 스크립트 → build → 화면 확인 → 보고 → 다음). 중간 쪽 임의 확인·한 장 튜닝 금지. 관련 도구: get_textbook_page, textbook_view.py(--holes 는 초록 원 M 표시), get_step_context, new_assembly.py. 관련: [[feedback-follow-admin-fix-instructions]], [[feedback-do-only-the-stated-step]].
