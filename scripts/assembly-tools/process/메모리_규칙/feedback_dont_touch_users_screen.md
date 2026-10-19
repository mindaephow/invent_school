---
name: feedback-dont-touch-users-screen
description: "브라우저 pane/개발서버 화면은 사용자가 보는 화면 — 요청 없이 조작(패널 접기·카메라·관절 버튼·전체 새로고침) 금지, 필요하면 먼저 허락"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1f667c85-0cb9-4898-9d92-6ba90f4d189a
  modified: 2026-10-16T12:46:42.143Z
---

사용자가 같이 보고 있는 브라우저 pane(3178 설계 화면)을 내 확인 용도로 마음대로 조작하지 않는다. 패널 접기(«), 카메라 변경, 🔩 관절 토글, 번호 클릭, navigate 전체 새로고침을 요청 없이 해서 "왜 자꾸 지멋대로 화면을 보이게 하냐"고 화냄(2026-10-16, 사마귀로봇 35~40번 작업 중).

**Why:** 내가 접어 둔 패널이 사용자 화면에 남아 "번호가 없어"라는 오해를 만들었고, 사용자가 보던 상태를 바꿈. 저장소 규칙(CLAUDE.md "질문엔 답만, 화면을 바꾸지 않는다")·[[feedback_no_full_page_reload]]·[[feedback_answer_questions_dont_change_things]] 와 같은 줄기.

**How to apply:** 증거 사진(record_check)처럼 화면 확인이 꼭 필요하면 먼저 "화면을 잠깐 열어 확인해도 될까요" 묻고, 끝나면 패널·카메라를 원래대로 돌린다. 전체 새로고침 금지(차시 select 토글 + 번호 클릭). 질문·보고 턴에는 pane 을 열지 않는다.

**기본 모습(사용자가 지금 상태로 보여 주라고 지정, 2026-10-16):** 왼쪽 패널 펼침 + 1~N·완성 번호판 보임(파랑·주황 색 유지) + 카메라·관절 표시 건드리지 않음. 저장소 CLAUDE.md·viewer_snippets.md 에도 적어 둠.
