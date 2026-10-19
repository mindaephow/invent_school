---
name: reference-user-diffs
description: 사용자 교정 기록 두 파일 — 요청차이(말로 바로잡은 것)·수정저장차이(화면에서 고쳐 저장한 ❄·📷); 큐보 조립도 작업 전에 읽고, 바로잡히면 추가
metadata:
  type: reference
---

`C:\Users\user\Downloads\invent_school\scripts\assembly-tools\user_diffs\` 에 있다(저장소 안, "업로드" 때 함께 올라감).
- `요청차이.md` — 내 결정 → 사용자 요청 → 배운 것 → 반영한 곳. 사용자가 말로 바로잡으면 맨 아래에 한 항목 추가한다(수동).
- `수정저장차이.md` — 내 코드 값과 사용자가 화면에서 저장한 ❄ 자세·📷 카메라의 차이. `python collect_diffs.py` 로 DB 에서 다시 만든다(2026-10-12 기준 자세 276건 중 10건 고침: 부시·리벳·메인보드·판 묶음; 카메라는 사용자가 번호마다 직접 정함).

**Why:** 사용자가 "내가 한 걸 보고 너를 업그레이드하라, 공부하라" 고 함(2026-10-12). **How to apply:** 큐보 조립도 번호를 시작하기 전에 두 파일을 훑고, number_start.py 가 보여 주는 사용자 ❄·📷 기록을 코드 값보다 우선한다. 관련: [[feedback-fix-rules-when-broken]].
