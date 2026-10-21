---
name: feedback-reload-after-upload
description: 조립도 그림을 DB 에 올린 뒤 화면을 다시 불러와 🖼 배지로 보이는지 확인한다
metadata:
  type: feedback
---

번호의 이미지 작업을 DB 에 올렸으면 화면을 다시 불러와(차시 select 10→9 토글 + 번호 클릭) 🖼 배지에 장수가 뜨는지까지 확인해야 한다. 안 하면 사용자가 "이미지 작업이 안 보인다"고 지적한다(바이킹 15번, 2026-10-21).

**Why:** 🖼 배지는 차시를 열 때 한 번만 읽어 올린 직후엔 안 보인다. 사용자는 언제든 볼 수 있게 되길 원한다.
**How to apply:** vk_tools stage → refStore.save 뒤에 토글로 다시 불러오고 배지 숫자를 읽어 보고에 적는다. process/viewer_snippets.md 3-1 절.
