# invent_school — 이 저장소를 처음 여는 Claude 에게

사용자는 한국어를 쓰고, 항상 **존댓말·짧게** 답한다. 말이 거칠어도 규칙대로 하나씩 정직하게(확인한 것/추정 구분) 보고하길 원한다.

**무엇이 어디에서 관리되는지(어디에 적어야 하는지)의 기준은 `scripts/assembly-tools/process/문서지도.md` 다. 문서를 고치거나 새로 적기 전에 먼저 본다.**

## 새로 시작하거나 새 세션일 때 — 맨 먼저 체크하고 요청한다 (사용자 지시 2026-10-13)
번호 계산·규칙 읽기보다 **먼저** 아래를 확인하고, 빠진 것은 사용자에게 한 줄로 요청한다(나머지 작업은 이어 간다).
1. **개발 서버**: `http://localhost:3178/design.html?subject=robot` 하나만 쓴다(포트·서버 이름은 여기서만 정한다). 응답하면 그대로 쓰고(다른 채팅이 띄운 것도 같은 서버), 없으면 `preview_start invent-school-dev`(`.claude/launch.json`, 없는 PC 는 README 새 PC 절 3번).
2. **로그인**: 브라우저 pane 에서 `design.html` 을 열어 선생님 로그인 화면이 보이면 **사용자에게 로그인을 요청**한다(비밀번호는 대신 입력하지 않는다). 로그인 전에는 화면 비교·❄/📷 확인을 하지 않는다.
3. **`.env.local`·DB 읽기**: `python number_start.py <이름> <번호>` 맨 위 "세션 시작 체크" 블록이 서버·키·사용자 ✓ 읽기를 한 번에 보여 준다. ❌ 는 먼저 해결하거나 요청한다.
4. **현재 상태 파악**: `process/진행기록_<이름>.md`·`user_diffs/요청차이.md`·메모리의 해당 조립도 진행 메모 → git log/status(미푸시·미추적 확인) → 사용자 ✓ 번호(DB).
5. 그다음 SKILL.md 를 처음부터 읽고 "이번 번호에서 지킬 규칙 3개"를 첫 보고에 적고 시작한다.

## 큐보 조립도(조립 보기) 작업을 이어받을 때 — 이 순서로 읽는다
0. **메모리 없는 처음 보는 Claude 는 `scripts/assembly-tools/process/05_조립.md` 맨 위 "★ 처음 보는 Claude 를 위한 실행 순서"(환경·번호 하나 12단계·코드 템플릿·함정·도구 지도)를 가장 먼저 읽고 그대로 따른다.** 화면 조작 코드는 `process/viewer_snippets.md`.
1. `scripts/assembly-tools/process/진행기록_<이름>.md` — 진행 중인 조립도의 현재 상태·다음 할 일(드롭체커: `진행기록_dropchecker.md`, 투석기: `진행기록_catapult.md`).
2. `scripts/assembly-tools/process/00_개선규칙.md` ~ `05_조립.md` — 조립 과정 규칙(이 저장소 사본이 기준이다. 번호를 하다 빈틈이 나오면 해당 파일을 **덮어써서** 고친다). **한 번호로 안 풀리면 멈추지 말고 `05_조립.md` 0-1 절(정보를 모아 유추: holefit 자동 DoG → infer_grid)대로 푼다.** **대부분 대칭형이다 — 대칭 쪽·다리(n족: 강아지 4족·꼬마기사 2족)를 만들 때는 `process/ref_대칭조립.md`(모범 = 드롭체커)·`process/ref_n족로봇.md` 를 먼저 본다(MCP: `get_assembly_reference` part="참고"). 대칭 검증·짝 없는 부품 찾기는 `python symcheck.py <이름>`.**
3. `.claude/skills/cubo-assembly/SKILL.md` (git 에 있으나 `.claude/` 는 ignore 설정 — 없으면 `git show HEAD:.claude/skills/cubo-assembly/SKILL.md`), `app/lib/cubo-assembly-guide.js`(MCP `get_assembly_guide` 가 돌려주는 안내서 — SKILL.md·README 와 겹치는 절은 그쪽을 가리키는 포인터다. 어느 글의 원본이 어디인지는 `process/문서지도.md`).
4. `scripts/assembly-tools/user_diffs/요청차이.md` — 사용자가 바로잡은 것 모음(같은 실수 반복 금지).
5. `scripts/assembly-tools/README.md` — 새 PC 준비(Python numpy·opencv, npm install, launch.json 만들기).

## 환경에서 사람이 줘야 하는 것
- `.env.local`(git 에 없음): `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — `userdone.py`·`record_check.py`·`number_start.py` 가 사용자 ✓·❄·📷 를 DB 에서 읽는 데 필요. 없으면 사용자에게 달라고 하거나 Vercel 환경변수에서 가져온다.
- 설계 화면 로그인(선생님 계정): 사용자가 직접 한다. 비밀번호를 대신 입력하지 않는다.
- 교재 PDF 는 필요 없다 — 단계별 책 그림은 `scripts/assembly-tools/refs/<이름>/NN.jpg` 에 이미 잘려 있다.

## 절대 규칙
- 모든 조립도는 완성 사진과 **방향선 그림**(앞 +Z · 뒤 −Z · 위 +Y · 왼쪽 +X · 오른쪽 −X, `refs/<이름>/00_1.jpg`)이 한 세트다 — 없으면 `number_start.py` 가 막는다(`process/00_개선규칙.md` 9번, `02_이미지_자르기.md` 3-2).
- ✓(완료)·"완료" 버튼은 절대 누르지 않는다. 사용자 ✓ 번호는 내용을 바꾸지 않는다(빌드가 막는다).
- `git push` 는 사용자가 "업로드"라고 말할 때만. 요청하지 않은 작업을 미리 하지 않는다.
- 빌드 확인 게이트 우회 금지(`build.py <이름> --write` 하나뿐). 검사가 경고하면 끄지 말고 보고.
- 질문엔 답만 한다(화면·값을 바꾸지 않는다). 범위 밖으로 넓히지 않는다.
- **사용자에게 보여 주는 화면은 평소 기본 모습 그대로(사용자 지시 2026-10-16):** 왼쪽 패널 펼침 + 1~N번·완성 번호판이 보이고(관리자 색 유지) + 카메라·패널·관절 표시는 건드리지 않은 상태. 확인용으로 패널을 접거나 카메라·관절 버튼을 바꿨으면 끝나고 반드시 이 기본 모습으로 되돌린다. 사용자가 시키지 않으면 화면을 조작하지 않고, 전체 새로고침(navigate)은 쓰지 않는다.
- **회전하는 곳은 항상 관절로 표시한다(사용자 지시 2026-10-16):** 조립도를 만들 때 도는 곳(바퀴 축·기어 축·팔 축·핀)이 나오면 그 번호에서 바로 관절(`ivs_assembly_joints`)과 움직이는 묶음(`ivs_assembly_joint_groups`)을 등록한다 — 나중에 사용자가 지적하기 전에. 모터에 직접 연결된 구동 축만 관절 메모에 `[모터직결]` 을 넣어 형광라임으로 보이게 하고, 다른 회전 관절은 그대로 분홍. 번호를 끝낼 때 체크: "이 번호에 도는 부품이 있나? 관절 등록했나?"
- Windows 콘솔은 cp949 → 파이썬 실행 시 `PYTHONIOENCODING=utf-8`.
