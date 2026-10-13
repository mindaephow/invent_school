# invent_school — 이 저장소를 처음 여는 Claude 에게

사용자는 한국어를 쓰고, 항상 **존댓말·짧게** 답한다. 말이 거칠어도 규칙대로 하나씩 정직하게(확인한 것/추정 구분) 보고하길 원한다.

## 큐보 조립도(조립 보기) 작업을 이어받을 때 — 이 순서로 읽는다
1. `scripts/assembly-tools/process/HANDOFF_catapult.md` — 투석기 현재 상태·다음 할 일·도구 순서(가장 먼저).
2. `scripts/assembly-tools/process/00_개선규칙.md` ~ `05_조립.md` — 조립 과정 규칙(이 저장소 사본이 기준이다. 번호를 하다 빈틈이 나오면 해당 파일을 **덮어써서** 고친다). **한 번호로 안 풀리면 멈추지 말고 `05_조립.md` 0-1 절(정보를 모아 유추: holefit 자동 DoG → infer_grid)대로 푼다.** **대부분 대칭형이다 — 대칭 쪽·다리(n족: 강아지 4족·꼬마기사 2족)를 만들 때는 `process/ref_대칭조립.md`(모범 = 드롭체커)·`process/ref_n족로봇.md` 를 먼저 본다(MCP: `get_assembly_reference` part="참고"). 대칭 검증·짝 없는 부품 찾기는 `python symcheck.py <이름>`.**
3. `.claude/skills/cubo-assembly/SKILL.md` (git 에 있으나 `.claude/` 는 ignore 설정 — 없으면 `git show HEAD:.claude/skills/cubo-assembly/SKILL.md`), `app/lib/cubo-assembly-guide.js`(MCP `get_assembly_guide` 와 같은 내용).
4. `scripts/assembly-tools/user_diffs/요청차이.md` — 사용자가 바로잡은 것 모음(같은 실수 반복 금지).
5. `scripts/assembly-tools/README.md` — 새 PC 준비(Python numpy·opencv, npm install, 로컬 서버 `npm run dev -p 3177`, 로그인은 사용자가 직접).

## 환경에서 사람이 줘야 하는 것
- `.env.local`(git 에 없음): `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — `userdone.py`·`record_check.py`·`number_start.py` 가 사용자 ✓·❄·📷 를 DB 에서 읽는 데 필요. 없으면 사용자에게 달라고 하거나 Vercel 환경변수에서 가져온다.
- 설계 화면 로그인(선생님 계정): 사용자가 직접 한다. 비밀번호를 대신 입력하지 않는다.
- 교재 PDF 는 필요 없다 — 단계별 책 그림은 `scripts/assembly-tools/refs/<이름>/NN.jpg` 에 이미 잘려 있다.

## 절대 규칙
- ✓(완료)·"완료" 버튼은 절대 누르지 않는다. 사용자 ✓ 번호는 내용을 바꾸지 않는다(빌드가 막는다).
- `git push` 는 사용자가 "업로드"라고 말할 때만. 요청하지 않은 작업을 미리 하지 않는다.
- 빌드 확인 게이트 우회 금지(`build.py <이름> --write` 하나뿐). 검사가 경고하면 끄지 말고 보고.
- 질문엔 답만 한다(화면·값을 바꾸지 않는다). 범위 밖으로 넓히지 않는다.
- Windows 콘솔은 cp949 → 파이썬 실행 시 `PYTHONIOENCODING=utf-8`.
