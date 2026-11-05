---
name: dev-server
description: 개발서버 열기 — "개발서버 열어줘", "서버 열어줘", "로컬 열어줘", "설계 화면 열어줘" 라고 하면 바로 이 스킬을 따른다. invent_school 개발 서버(포트 3178)를 확인·켜고 설계 화면을 브라우저 패널에 연다.
---

# 개발서버 열어줘 (invent_school, 포트 3178)

사용자가 "개발서버 열어줘"라고 하면 묻지 말고 아래 순서로 한 번에 한다.

1. 응답 확인: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3178/design.html` — 200 이면 이미 떠 있으니 2번으로 간다.
2. 안 떠 있으면 `preview_start` 의 `invent-school-dev` 로 켠다(Bash 로 서버를 직접 돌리지 않는다). 설정이 없는 PC 는 `scripts/assembly-tools/README.md` 새 PC 절 3번.
3. 브라우저 패널에서 `http://localhost:3178/design.html?subject=robot` 을 연다(이미 열려 있으면 다시 열지 않고 그 탭을 쓴다 — 사용자 화면을 요청 없이 새로고침하지 않는다).
4. 로그인 화면이면 "오른쪽 창에서 로그인해 주세요" 한 줄만 말하고 기다린다. 비밀번호는 대신 입력하지 않는다.
5. 보고는 한 줄: 포트, 켠 방법(이미 떠 있었는지/새로 켰는지), 로그인 필요 여부.
