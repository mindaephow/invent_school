---
name: feedback-same-line-parts-check
description: "when reading a book picture, parts that sit on one line (axle + rivets, etc.) must resolve to the same column/row; check alignment before trusting grid conversion"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9ac604cf-f2ec-4f86-ad8a-747d4ea683cb
  modified: 2026-10-11T05:42:18.778Z
---

투석기 5번: 책 그림에서 리벳 둘이 4번 축과 같은 선 위에 있는데, 나는 05 격자 환산으로 "칸3"이라 읽어 한 칸 옆(−x)에 놓았다. 사용자가 내 작업 그림(축 선 겹쳐 그린 것)을 보여 주며 "한 라인인데 그렇게 안 그렸다"고 지적.

**Why:** 격자 환산(링 픽셀 → 가까운 점)만 믿고, 이미 읽어 둔 다른 부품(축 x=칸4)과 정렬 확인을 안 했다. 같은 선 위에 있는 부품은 사람 눈에 바로 보이는 정보다.

**How to apply:** 번호를 읽을 때 새 부품의 환산 칸을 앞 번호 부품의 선(축·프레임 가운데 등)과 겹쳐 확인하고, 같은 선이면 같은 열이어야 한다. 또 "이미 꽂힘/분리" 상태는 링 높이만으로 단정하지 말고 사용자 화면 기준으로 확인. 관련: [[feedback-direction-xyz-axes]], [[project-catapult-status]]

**사용자 보충(2026-10-11):** "내 말은 방향과 격자를 최대한 활용하라는 말이야" — 단순 정렬 확인이 아니라, 축선·격자를 위치 읽기의 주된 도구로 쓰라는 뜻. 가이드(cubo-assembly-guide.js) ★★★★ 8번에 규칙으로 추가함.
