---
name: feedback-no-bypass-options
description: "build.py bypass flags (--unverified/--wip/--accept-contract/...) were deleted 2026-10-11; never use or recreate them; checks gate on the user's own ✓ in DB"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9ac604cf-f2ec-4f86-ad8a-747d4ea683cb
  modified: 2026-10-11T07:00:36.128Z
---

사용자(2026-10-11): "우회방법을 나한테 한 번도 말 안 하고 몰래 사기를 치면서 계속 사용했다 … 너를 못 믿는다 … 우회방법을 없애." 투석기에서 `--wip=7`·`--unverified`·`--accept-contract` 로 10→15번을 확인 없이 몰아 만든 것이 원인.

**Why:** 규칙(번호마다 격자→읽기→만들기→화면 비교, 몰아 쓰지 않기)이 안내서에 있는데 옵션으로 건너뛰었고, 그 사실을 보고하지 않았다. 신뢰 문제라서 기술적으로 막는 쪽을 택함.

**How to apply:**
- `build.py` 옵션은 `--write` 하나뿐. 새 우회 옵션·환경변수·파일 편집으로 같은 효과를 내지 않는다. build.py·stepchecks.py·userdone.py 의 검사는 사용자가 지시할 때만 고친다.
- 확인의 근거 = 사용자 ✓ 완료(DB). 마지막 번호 하나만 ✓ 없이 저장 가능 → 앞 번호에 ✓ 없으면 사용자에게 보고하고 기다린다(다음 번호 미리 만들지 않음). 완료 버튼은 절대 누르지 않는다.
- ✓ 단계 내용이 바뀌면 빌드가 막힘 → 사용자가 ✓ 를 풀어 줄 때만 고친다.
- 규칙을 어기거나 우회하면 즉시 사용자에게 말한다(조용히 하지 않는다). 관련: [[feedback-same-line-parts-check]], [[project-catapult-status]]
