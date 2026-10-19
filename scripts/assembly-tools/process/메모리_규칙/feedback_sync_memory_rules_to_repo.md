---
name: sync-memory-rules-to-repo
description: invent_school 조립도 관련 메모리를 새로 쓰거나 고치면 저장소 사본도 같은 턴에 동기화 — 외부 PC Claude 는 메모리가 없어 규칙을 어김
metadata:
  type: feedback
---

조립도·invent_school 관련 feedback_/project_ 메모리를 쓰거나 고친 턴 끝에 `cd C:\Users\user\Downloads\invent_school\scripts\assembly-tools && PYTHONIOENCODING=utf-8 python sync_memory_rules.py` 를 돌린다(저장소 `process/메모리_규칙/` 갱신, 푸시는 사용자가 "업로드"라 할 때만).

**Why:** 2026-10-19 외부 PC 에서 Claude 가 메모리 없이 규칙을 어겨 5시간 동안 번호 하나도 못 끝냈다. 사용자가 "작업하다 내용을 업데이트하면 외부 PC 도 같은 방식으로 작업하게 세팅"하라고 지시.
**How to apply:** 외부 PC 에서 고친 규칙이 푸시돼 오면 pull 후 `python sync_memory_rules.py --from-repo` 로 메모리에 가져온다. 자세한 절차는 저장소 `process/메모리_규칙/동기화.md`.
