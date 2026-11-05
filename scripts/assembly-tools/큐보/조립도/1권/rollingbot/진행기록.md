# 롤링봇(cubo-1-rollingbot, 큐보 1권) 진행기록

쓰는 법: `문서지도.md` "진행 기록". 이 문서는 2026-10-14 에 Claude 메모리에서 옮겼다(메모리 원본 기록 시점 2026-10-05).

## 현재 상태 (2026-10-14, 도구로 확인)
- 조립도 31단계+완성(32) 작성됨(`rollingbot_asm.json`, 마지막 수정 10-05). 사용자 ✓: 1~32번 전부(완성 포함).
- 정확한 현황은 `python number_start.py rollingbot <번호>`·`python rulecheck.py rollingbot` 으로 본다.

## 이 조립도의 구조·고유 사실
- 스크립트 `scripts/assembly-tools/rollingbot.py`.
- 완성 "장전" 모습은 바퀴를 칸 단위(1칸 = 10mm)로 사용자가 지시해 확정했다: −Z 2칸, −Y 1칸. 브라켓 팔 `PHI_W` = 32.
- 이 조립도에서 쓴 새 기법(안내서 5-9절): `poseAt`, `finalOnly`, `loose`, `noMarkCheck`, `_abs_place`.

## 알아 둘 것
- 속이 빈 부품(바퀴·ㄱ자 브라켓)의 간격은 상자/원판 계산을 믿지 말고 화면으로 보고 사용자 지시대로 맞춘다.
