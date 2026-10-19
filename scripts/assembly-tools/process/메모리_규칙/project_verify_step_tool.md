---
name: verify-step-tool
description: 번호 하나를 한 번에 점검하는 verify_step.py (홀라인·카메라·돌기↔구멍·번호 대조 그림·읽기 표·증거) — 번호를 끝낼 때마다 돌린다
metadata:
  type: project
---

2026-10-18 사용자 요청으로 `scripts/assembly-tools/verify_step.py <이름> <번호…>` 를 만들었다. 홀라인(blob-lattice/앵커/손), 카메라(오차 ≤2px·모델 cam=axes fit·앞뒤 번호 복사 여부·camSrc), `_mates_table` ⚠, 번호 대조 그림(index.json idx≥3), 읽기 표 빈 칸·근거, record_check 증거를 ✅/⚠/❌ 표로 낸다.

**Why:** 오토타깃 5~10번에서 같은 검사를 손으로 돌리다 빠뜨려(홀라인 손 점·카메라 복사·결합 칸 한 칸 어긋남) 사용자가 크게 화냈다.
**넘어가는 기준(사용자 2026-10-18):** 홀라인 ✅ + 번호 대조 그림 ✅ 이면 그 번호는 통과(번호판 파랑)하고 다음 번호로 간다. 카메라·돌기↔구멍·읽기 표·증거는 참고(⚠·❌ 보고만). 결과는 DB ivs_assembly_checks(auto:*)에 저장되고 조립 보기 ☑ 검증 체크 모달(관리자만)에서 본다.

**How to apply:** 번호를 "끝났다"고 하기 전에 돌려 ❌ 0건을 만든다(⚠ 는 이유를 보고). 2026-10-18 기준 오토타깃 5·7·9·10 전부 ✅, 8·11 ⚠(카메라 앵커 2px 초과), 2·3·4·6·12 는 ❌(홀라인·카메라 미해결). [[feedback-rules-are-the-fast-way]]
