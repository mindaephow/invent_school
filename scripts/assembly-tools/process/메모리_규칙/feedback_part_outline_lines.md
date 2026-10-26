---
name: part-outline-lines
description: 로버트론 부품 3D 모델 테두리 선 규칙 — 실제 윤곽을 따라 0.1mm, 어두운 색은 밝게/밝은 색은 어둡게
metadata:
  type: feedback
---

부품 모델에는 실제 윤곽(둥근 모서리·구멍 둘레·붙은 부품 경계)을 따라 아주 얇은 선(0.1mm)을 긋는다. 사각 상자 둘레로 긋거나 두껍게(0.5) 긋거나 흰색에 가까운 색으로 긋지 않는다. 색은 부품 색이 어두우면 조금 밝게, 밝으면 조금 어둡게.

**Why:** 평판(블루)에서 사각형 선·두꺼운 선·거의 흰 선이 "비어 보인다/족같이 그린다"고 연달아 지적받음(2026-10-27). 얇게 윤곽을 따라 그리니 "훨 낫다".
**How to apply:** `app/lib/robotron-line-color.js`의 `lineColorFor`, `scripts/make-robotron-flatplate.mjs`의 고리→막대 방식을 재사용. 판·프레임 경계선도 긋는다. 저장소 CLAUDE.md에도 규칙으로 기록함. [[reuse-existing-infra]]
