---
name: project-hammerbattle-status
description: "해머배틀(3권 3차시, cubo-3-hammerbattle) 조립도 진행 — 1~10번 완료(푸시 전), 11번부터, 함정·교훈 요약"
metadata:
  node_type: memory
  type: project
  originSessionId: 3dd4888b-70a4-43c3-90e6-2b93bfcaa7b9
  modified: 2026-11-01T15:54:29.165Z
---

해머배틀(3권 3차시) 조립도: 2026-11-02 기준 **1~15번 끝**(15번 = 14번 조립 Z축 180° 뒤집기 + 새 부품 215프레임, 증거·그림 10장·관찰·rulecheck ✅), 16번 진행 중(713프레임 홀라인 미달 → infer_grid)(읽기 표·6방향·observe·record_check·그림 DB 업로드·rulecheck ❌0), 푸시 전. 상세는 저장소 `scripts/assembly-tools/process/진행기록_hammerbattle.md` 맨 위 절.

**Why:** 사용자가 "규칙대로 읽고 10번까지 멈추지 마"라고 해 번호마다 규칙 체크리스트 전부 수행하며 이어 만듦.

**How to apply (다음 세션, 11번부터):**
- 막대 3번은 T축(30)이고 4번 막대가 축(65) — USED 표 정정됨. 35번의 T축 추정은 다시 읽어야 함.
- 8번 둘째 벌은 회전 복사가 아니라 z 거울상(책 22번이 확인). 같은 조립 둘이면 같은 방향/대칭부터 센다.
- 한 번호 책 한 장으로 방향이 안 정해지면(9번) 뒤 번호 책(10·13번)을 읽어 정한다 — 거울 해(카메라가 아래)가 나오면 방향을 의심.
- `observe.py add` 재기록은 `hammerbattle_obs.json` 해당 번호를 지운 뒤 처음부터(이미지 번호 어긋남 버그). 앞 번호 부품(copy)을 뒤 번호에서 고치면 그 앞 번호 record_check 를 다시.
- 새 창고(slot≥2) 부품은 숨은 몸과 우연한 맞물림 검사에 걸림 — 어긋남 (2.5,0,2.5) 만 통과, `hideMade` 로 몸 숨김.
- lift: 6번~끝·완성 18, 7번 45, 10번 40(번호별 hovering 때문). 끝 번호·완성은 같은 값으로.
- 푸시는 "업로드" 때만(`sync_memory_rules.py` 먼저).
