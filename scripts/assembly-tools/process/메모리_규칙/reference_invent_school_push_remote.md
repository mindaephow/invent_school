---
name: invent-school-push-remote
description: invent_school 저장소의 푸시 원격은 origin 이 아니라 newrepo (git push newrepo main)
metadata:
  node_type: memory
  type: reference
  originSessionId: 20534eb6-8a5c-4332-8a61-bbafcd8dbc0b
  modified: 2026-10-18T17:11:01.522Z
---

invent_school 저장소(C:\Users\user\Downloads\invent_school)에는 `origin` 원격이 없고 `newrepo`(https://github.com/mindaephow/invent_school.git)뿐이다. 문서(05_조립.md 12번·README)에는 `git push origin main` 으로 적혀 있지만 실제로는 `git push newrepo main`.

**Why:** 2026-10-19 오토타깃 12~15번 업로드 때 `origin` 으로 밀다 실패, `newrepo/main` 이 upstream 이었음.
**How to apply:** 사용자가 "업로드"라고 하면 `git add`(파일 지정)→`git commit`→`git push newrepo main`.
