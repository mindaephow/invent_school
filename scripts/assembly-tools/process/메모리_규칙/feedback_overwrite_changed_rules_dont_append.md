---
name: feedback_overwrite_changed_rules_dont_append
description: 규칙·기능이 바뀌면 옛 문장을 지우고 덮어쓴다(추가된 기능만 남김) — 로그처럼 더하면 옛 방식을 다시 쓰게 됨
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3dd4888b-70a4-43c3-90e6-2b93bfcaa7b9
  modified: 2026-11-02T03:13:05.462Z
---

규칙·기능을 바꿀 때는 항목마다 판단한다: **새로 추가된 기능은 남기고, 방식이 바뀐 것은 옛 문장을 지우고 새 문장으로 덮어쓴다.** 정리 과정(충돌 목록·출처·"옛 문장 보관" 파일·날짜 덧붙임)을 문서에 쌓지 않는다. 바뀐 이유는 커밋 메시지에만 남긴다.

**Why:** 같은 내용이 여러 곳에 남으면 나중에 작업하다가 옛 방식을 쓰게 된다(2026-11-02 해머배틀 규칙 정리 중 "로그 남기듯 더해져서 혼란만 가중된다"). 안내서·SKILL·메모리 사본까지 읽다 영향을 받으니 다 같이 정리해야 한다.

**How to apply:** 규칙 원본은 `scripts/assembly-tools/process/00_규칙.md` 한 곳(C7). 고치기 전에 안내서(`app/lib/cubo-assembly-guide.js`)·`05_조립.md`·SKILL·CLAUDE.md 에 같은 말이 있는지 찾아 한꺼번에 덮어쓴다. 지우기 전에 마스터에 없는 내용(플래그·형식·도구 사용법)은 마스터로 옮긴다. 절 제목은 `get_assembly_guide` 코드(CATS·isCore: `★`·`작업 흐름`·`제1편`·`단계 N`)가 쓰니 바꾸면 깨지는지 본다. [[feedback_fix_rules_when_broken]]
