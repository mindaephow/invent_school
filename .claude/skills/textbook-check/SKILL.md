---
name: textbook-check
description: 교재검사 — "교재검사", "교재검사 해줘", "교재 관찰 검사", "책 대조 검사" 라고 하면 이 스킬을 따른다. 사전작업(교재 읽기·격자·카메라·읽기 표·증거·그림 DB 업로드)이 맞는지만 검사한다. 조립도 자체의 겹침·틈은 assembly-check(조립검사)다.
---

# 교재검사 (사전작업: 책을 읽고 관찰·분석한 것이 맞는가)

규칙은 `scripts/assembly-tools/process/큐보 부품결합규칙.md` 의 "검사 지도"와 제1부(A·D·E·F·H, G7·G8읽기·G9·G10읽기·G18). 조립도 자체의 결합·겹침·틈은 보지 않는다(그것은 assembly-check).

사용: `교재검사 <조립도이름> [번호…]` — 이름은 `balance`, `rabbit` 처럼 스크립트 이름이다. 이름이 없으면 한 줄로 묻는다. 번호를 안 주면 전체.

**시작 전(시험·실전 똑같이, 건너뛰지 않는다):** ① `cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python session_start.py --아이디 <내 계정>` 으로 GitHub 최신본을 받고 로컬이 최신인지 본다(조립도 `.py` 가 최신본이어야 한다) ② `process/큐보 부품결합규칙.md` 를 처음부터 읽고 첫 보고에 '이번에 지킬 규칙 3개'를 적는다 ③ 그 뒤에 아래 점검을 돌린다.

`scripts/assembly-tools` 에서 `PYTHONIOENCODING=utf-8` 로 아래를 돌린다.
1. `python rulecheck.py <이름> [번호…]` — 격자 F · 카메라 C · 증거 E · 읽기 표 R · 증명 P (읽기만 한다).
2. `python verify_step.py <이름> <번호…>` — 홀라인·카메라·번호 대조 그림·읽기 표·증거. 번호를 꼭 줘야 하고, 결과를 `<이름>_verify.json` 에 저장하는 도구다(파일 하나가 바뀐다는 것을 보고에 적는다).
3. `python dbimgcheck.py <이름> [번호…]` — 그림이 DB 에 올라갔는지(읽기 전용, `.env.local` 필요).

보고는 번호별로 ✅/⚠/❌ 를 나눠 쓰고, 센 값·도구 계산·추정을 구분한다. 결합 위반(겹침·틈)은 이 보고에 섞지 않는다. 고치라고 하지 않으면 고치지 않는다.
