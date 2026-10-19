---
name: feedback-new-warehouse-at-origin
description: 조립도의 새 창고(slot 2 이상)는 화면 가운데(원점)에 둔다 — 멀리 띄우는 오프셋 상수 금지; 어두운 판은 holesearch 먼저
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2642ae62-1c8a-4475-817f-8b0fc23f8fb0
  modified: 2026-10-17T17:54:52.912Z
---

배틀로봇 조립도에서 창고 2 번호들을 x 200·z 250·z 500·z 800 에 멀리 놓았다. 사용자: "작업장서들이 왜 중심이 아니라 스케치북 외곽이야??? xyz 축도 안보이고", "모두 중심으로 이동시켜", "규칙이 엉망이네"(2026-10-18).

**Why:** 규칙 6(새 창고는 원점)이 이미 있었는데 겹침 검사를 피하려고 상수로 띄웠고, 원점에서 벗어나 축 표시도 안 보였다.

**How to apply:** 새 창고는 원점(몸과 겹치면 5mm 어긋남)에 둔다. 스크립트 오프셋 상수(X2·Z24·Z26·Z30·Z33)를 0~5 로 둔다. 바꾼 뒤 links.json 의 낡은 place 잠금을 비운다. 어두운 판 holefit 미달 → holesearch.py(모서리 탐색, 약 5분)를 먼저, 그다음 링 앵커 유추. 05_조립.md 5-1 에 적었다. [[feedback-stop-when-big-mismatch]]
