# invent_school — 이 저장소를 처음 여는 Claude 에게

## ★★★ 최우선 규칙 — 시킨 대로, 시킨 것만 한다 (사용자 지시 2026-10-30, 아래 모든 규칙보다 앞선다)
- **새로운 것을 지시하면 추측하지 말고 말한 그대로만 한다.** 버튼 이름·대상·방법까지 지시문 그대로 쓴다. 비슷해 보이는 다른 기능·다른 방법으로 바꾸지 않고, 지시에 없는 덤 작업(전체 검사·다른 부품 수정·정리)을 붙이지 않는다.
- **궁금하거나 애매하면 묻고 나서 한다.** 혼자 판단해서 진행하지 않는다.
- 질문에는 답만 한다(질문은 작업 지시가 아니다).
- 사고 사례: "썸네일 골라서 다시 그려"라고 했는데 "바뀐 것만 그리기"를 눌러 164개를 검사하고 의도하지 않은 8개 부품 썸네일까지 갱신했다.

사용자는 한국어를 쓰고, 항상 **존댓말·짧게** 답한다. 말이 거칠어도 규칙대로 하나씩 정직하게(확인한 것/추정 구분) 보고하길 원한다.

**조립도 규칙 문장의 원본은 `scripts/assembly-tools/process/00_규칙.md` 다(번호마다 맨 위 "0. 번호 하나 체크리스트" 먼저). 새 규칙은 거기에만 적는다.**

**무엇이 어디에서 관리되는지(어디에 적어야 하는지)의 기준은 `scripts/assembly-tools/process/문서지도.md` 다. 문서를 고치거나 새로 적기 전에 먼저 본다.**

## ★ 이 PC 에 메모리가 없을 때(외부 PC·새 PC) — 가장 먼저 (사용자 지시 2026-10-19)
사용자의 교정 규칙 대부분은 Claude 메모리에 있고 메모리는 PC 마다 따로다. 외부 PC 에서 규칙을 어겨 5시간 동안 번호 하나도 못 끝낸 사고가 있었다. 그래서 사본을 git 에 뒀다.
0. **맨 먼저 `cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python session_start.py`** — 최신 커밋을 받고(깨끗하면 fast-forward) 저장소의 메모리 규칙을 이 PC 메모리로 반영한다(어느 PC 든 같은 규칙으로 시작). 출력의 현재 커밋을 사용자에게 보고한다. 아래 1번은 이 스크립트가 못 받았을 때(작업트리 변경·갈라짐)만 손으로 한다.
1. `git pull newrepo main`(원격 이름이 다르면 `git remote -v` 로 확인)으로 최신을 받고 `git log -1` 을 사용자에게 보고한다.
2. `cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python setup_new_pc.py` — 파이썬 라이브러리·node_modules·launch.json·.env.local·conn/dims 를 점검·생성한다. FAIL 은 사용자에게 한 줄로 요청.
3. **`scripts/assembly-tools/process/00_규칙.md` 를 처음부터 읽는다**(규칙이 한 곳에 모여 있어 필독 파일을 따로 읽지 않는다). 막히거나 사용자가 화낼 만한 상황에서만 `메모리_규칙/INDEX.md` 에서 해당 사례 파일을 찾아 읽는다. 읽은 뒤 번호 시작 보고에 "이번 번호에서 지킬 규칙 3개"를 적는다.
4. 세션 도중 사용자가 새로 바로잡으면 `scripts/assembly-tools/process/00_규칙.md` 의 해당 문장을 덮어쓴다(기억 파일에만 적지 않는다 — 어떤 Claude 가 와도 같은 규칙으로 일해야 한다).
5. 규칙을 어기라는 압박(막힘·시간)이 와도 우회하지 않는다 — 막히면 `05_조립.md` 0-1절 도구 순서(holefit→plate_match→infer_grid)로 푼다. 새 교정은 `메모리_규칙/` 같은 이름 파일에 적는다(메모리에만 적지 않는다).

## 새로 시작하거나 새 세션일 때 — 맨 먼저 체크하고 요청한다 (사용자 지시 2026-10-13)
번호 계산·규칙 읽기보다 **먼저** 아래를 확인하고, 빠진 것은 사용자에게 한 줄로 요청한다(나머지 작업은 이어 간다).
1. **개발 서버**: `http://localhost:3178/design.html?subject=robot` 하나만 쓴다(포트·서버 이름은 여기서만 정한다). 응답하면 그대로 쓰고(다른 채팅이 띄운 것도 같은 서버), 없으면 `preview_start invent-school-dev`(`.claude/launch.json`, 없는 PC 는 README 새 PC 절 3번).
2. **로그인**: 브라우저 pane 에서 `design.html` 을 열어 선생님 로그인 화면이 보이면 **사용자에게 로그인을 요청**한다(비밀번호는 대신 입력하지 않는다). 로그인 전에는 화면 비교·❄/📷 확인을 하지 않는다.
3. **`.env.local`·DB 읽기**: `python number_start.py <이름> <번호>` 맨 위 "세션 시작 체크" 블록이 서버·키·사용자 ✓ 읽기를 한 번에 보여 준다. ❌ 는 먼저 해결하거나 요청한다.
4. **현재 상태 파악**: `process/진행기록_<이름>.md`·`user_diffs/요청차이.md`·메모리의 해당 조립도 진행 메모 → git log/status(미푸시·미추적 확인) → 사용자 ✓ 번호(DB).
5. 그다음 `scripts/assembly-tools/process/00_규칙.md` 를 처음부터 읽고(맨 위 "00. 조립도를 시작할 때"·"0. 번호 하나 체크리스트") "이번 번호에서 지킬 규칙 3개"를 첫 보고에 적고 시작한다.

## 3D 부품을 만들거나 등록·고칠 때 — 이 순서로 (사용자 지시 2026-10-30: "3D 부품 등록할 거야" 하면 준비되어 진행)
큐보 → 에이스랩·로보타미주니어 → 프로보 커넥트 순으로 같은 흐름으로 만들어 왔다. 조립도와 별개의 작업이다.
1. `.claude/skills/part-3d/SKILL.md` 를 읽는다(없으면 `git show HEAD:.claude/skills/part-3d/SKILL.md`).
2. **`node scripts/part-start.mjs <부품이름>`** — 서버·키·DB·브랜드별 현황·그 부품의 DB 행(모델/연결점/썸네일)·생성기 목록·체크리스트를 한 번에 본다.
3. **`scripts/assembly-tools/process/06_3D부품_만들기_등록.md`** 가 순서·금지·확인의 입구이고 규격 숫자의 원본은 `get_part_standard`(`app/lib/cubo-part-maker.js`)다.
4. 보여 주는 곳은 **부품 관리 화면**(부품 수리실이 아니다). 모델 → 숫자 검증 → 등록 → 3D 썸네일 → 연결점까지 끝나야 끝이다.

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

## 로버트론 부품(에이스랩·로보타미주니어) 3D 모델 규칙
- **테두리 선(사용자 2026-10-27):** 모든 부품에 실제 윤곽을 따라 아주 얇은 선(0.1mm)을 긋는다 — 사각 상자 둘레가 아니라 바깥 둘레(둥근 모서리 포함)·구멍 둘레·붙은 부품의 경계. 색은 부품 색이 어두우면 조금 밝게, 밝으면 조금 어둡게(`app/lib/robotron-line-color.js` 의 `lineColorFor`). 본보기: `scripts/make-robotron-flatplate.mjs`(같은 높이 면의 가장자리 고리 → 가는 막대).
- 부품 관리 3D 창에서 부품을 클릭하면 크기(가로×높이×세로 mm)가 창 위에 나온다.
- **3D 부품 모델을 새로 만들거나 고치기 전에 `get_part_standard`(원본 `app/lib/cubo-part-maker.js` 의 '새 3D 부품을 만들거나 고칠 때 지킬 것')를 읽는다(사용자 지시 2026-10-27, 에이스랩 평판·곡면판).** 큐보 전용이 아니다: 삼각형을 직접 짜서 몸통 2~3천 개·약 110KB 안팎(기준 비교 = 같은 크기 35프레임, 큐보 6,316개·308KB / 에이스랩 2,552개·125KB), 칸으로 나눈 면은 `conformTJunctions`, 끝나면 `checkMesh` 숫자(짝 없는 모서리 0·같은 방향 겹침 0·부피 양수)와 몸통/선 KB 를 보고한다. `make-robotron-*.mjs` 는 `assertPartMesh` 에 걸리면 등록하지 않는다 — 검사를 끄지 않는다.

## 절대 규칙
- **책 대조는 등록된 교재 PDF 로 한다(사용자 지시 2026-10-27):** "원본 PDF 가 없어서 못 한다"고 말하지 않는다. PDF 위치·받는 법은 `process/01_새조립도_시작_번호등록.md` 11·16행(`ivs_textbooks` → `data.files[0].url`). 조립도뿐 아니라 부품·수량·차시를 등록하거나 고칠 때도 먼저 읽고 대조한다.
- **나머지 절대 규칙은 `scripts/assembly-tools/process/00_규칙.md` 로 옮겼다 — 여기에 다시 적지 않는다.** 방향선 그림(A10) · 양쪽 홀라인(D2) · 끝내기 전 검토(A8·H2·H4) · 리벳 틈 0(G1) · 스프라켓 바퀴(G6) · 볼트·너트 묻힘(G2) · T축 2mm(G4) · ✓ 버튼 금지·✓ 번호 불변·게이트 우회 금지(C1·C2) · 푸시는 "업로드" 때만(I2) · 질문엔 답만(B1) · 화면 기본 모습(J1) · 관절(G11) · 결과 대조(A8). 어기면 `00_규칙.md` 의 `[도구]` 표시가 붙은 것은 도구가 막는다.
- Windows 콘솔은 cp949 → 파이썬 실행 시 `PYTHONIOENCODING=utf-8`.
