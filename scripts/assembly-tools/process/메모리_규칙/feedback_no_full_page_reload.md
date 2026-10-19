---
name: feedback-no-full-page-reload
description: 뷰어 확인할 때 location.reload 전체 새로고침 금지 — 빌드 뒤 차시 select 12→13 토글(데이터 다시 읽음) 후 번호 버튼 클릭
metadata:
  node_type: memory
  type: feedback
  originSessionId: 50862ad9-50eb-4885-b715-6f38d175acd9
  modified: 2026-10-08T16:40:10.548Z
---

강아지로봇 작업 중 build 마다 location.reload() 로 전체 새로고침을 하자 사용자가 "전체 새로 고침을 하지 말고 번호 새로고침을 해"라고 두 번 말함(2026-10-09, 한글 자판 오타로 입력).

**Why:** 전체 새로고침은 화면 상태·차시 선택을 날리고 느리며, 사용자가 같은 창을 같이 보고 있다.

**How to apply:** build --write 뒤에 (1) design-assemblies.js·design-assembly.js 를 fetch(cache:'reload') 해 두고 (2) 차시 select 를 12 로 바꿨다가 13 으로 되돌려(change 이벤트) 데이터를 다시 읽게 한 다음 (3) 단계 번호 버튼(왼쪽 목록의 정확히 그 숫자 버튼)을 눌러 연다. "↻ 새로고침" 버튼은 눌러 봤지만 데이터가 안 바뀌었다 — 그래도 사용자가 말한 "번호 새로고침"이 그 버튼이면 사용자에게 한 줄로 물어본다. 격자 이미지 등록(refStore.save)은 페이지 안에서 하므로 reload 가 필요 없다. 관련: [[feedback-camera-direction-from-book]]
