# invent_school — 이 저장소를 처음 여는 Claude 에게

사용자는 한국어를 쓰고, 항상 **존댓말·짧게** 답한다. 말이 거칠어도 규칙대로 하나씩 정직하게(확인한 것/추정 구분) 보고하길 원한다.

## ★ 최우선 — 시킨 대로, 시킨 것만 한다 (사용자 지시 2026-10-30, 모든 규칙보다 앞선다)
- 새로운 것을 지시하면 추측하지 말고 말한 그대로만 한다. 버튼 이름·대상·방법까지 지시문 그대로 쓰고, 지시에 없는 덤 작업(전체 검사·다른 부품 수정·정리)을 붙이지 않는다.
- 궁금하거나 애매하면 묻고 나서 한다. 질문에는 답만 한다(질문은 작업 지시가 아니다).
- 사고 사례: "썸네일 골라서 다시 그려"라고 했는데 "바뀐 것만 그리기"를 눌러 164개를 검사하고 의도하지 않은 8개 부품 썸네일까지 갱신했다.

## 어디에 뭐가 있나 (상황별)
| 상황 | 볼 곳 |
|---|---|
| 조립도 규칙이 뭔지 | **`scripts/assembly-tools/process/00_규칙.md`** — 규칙의 유일한 원본. 새 교정은 여기 해당 문장을 덮어쓴다(기억 파일에만 적지 않는다) |
| 번호 하나를 시작 | `00_규칙.md` 맨 위 "0. 번호 하나 체크리스트" → `python number_start.py <이름> <번호>` |
| 조립도를 처음 시작 | `00_규칙.md` "00. 조립도를 시작할 때" → `process/01~04_*.md` |
| 코드 쓰는 법·도구 사용법 | `process/05_조립.md`, 화면 조작 코드는 `process/viewer_snippets.md` |
| 이 조립도가 어디까지 됐나 | `process/진행기록_<이름>.md` |
| 사용자가 바로잡은 기록 | `scripts/assembly-tools/user_diffs/요청차이.md`, `수정저장차이.md` |
| 대칭 조립·n족 로봇 | `process/ref_대칭조립.md`(모범 = 드롭체커), `process/ref_n족로봇.md`, `python symcheck.py <이름>` |
| 부품 면·구멍·돌기 사실 | MCP `get_assembly_guide` 3-1·4·4-1절, `get_part_connectors` |
| 3D 부품 만들기·등록 | 아래 "3D 부품" 절 |
| 어떤 내용을 어느 문서에 적나 | `process/문서지도.md` (문서를 고치기 전에 먼저 본다) |

안내서(`app/lib/cubo-assembly-guide.js`)와 `.claude/skills/cubo-assembly/SKILL.md` 는 설명·입구일 뿐 규칙을 담지 않는다. 어긋나면 `00_규칙.md` 가 우선이다(`.claude/` 는 ignore 라 없으면 `git show HEAD:.claude/skills/cubo-assembly/SKILL.md`).

## 세션을 시작할 때 (새 PC·새 세션)
1. `cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python session_start.py` — 최신 커밋을 받고(깨끗하면 fast-forward) 현재 커밋을 사용자에게 보고한다. 새 PC 면 이어서 `python setup_new_pc.py`(라이브러리·node_modules·launch.json·.env.local 점검, FAIL 은 사용자에게 한 줄로 요청). 푸시 원격 이름은 `newrepo`(`git remote -v`).
2. **개발 서버**: `http://localhost:3178/design.html?subject=robot` 하나만 쓴다. 응답하면 그대로 쓰고, 없으면 `preview_start invent-school-dev`(없는 PC 는 `scripts/assembly-tools/README.md` 새 PC 절 3번).
3. **로그인**: 설계 화면에 선생님 로그인이 보이면 사용자에게 요청한다(비밀번호는 대신 입력하지 않는다). 로그인 전에는 화면 비교·❄/📷 확인을 하지 않는다.
4. **현재 상태**: `진행기록_<이름>.md`·`user_diffs/요청차이.md` → `git log`/`git status` → `number_start.py` 맨 위 "세션 시작 체크"(서버·키·사용자 ✓). ❌ 는 먼저 해결하거나 한 줄로 요청한다.
5. **`process/00_규칙.md` 를 처음부터 읽고** 첫 보고에 "이번 번호에서 지킬 규칙 3개"를 적은 뒤 시작한다.
6. 막힘·시간 압박이 와도 규칙을 우회하지 않는다 — 막히면 `05_조립.md` 0-1절 순서(holefit → plate_match → infer_grid)로 푼다.

## 3D 부품을 만들거나 등록·고칠 때 (조립도와 별개)
큐보 → 에이스랩·로보타미주니어 → 프로보 커넥트 순으로 같은 흐름이다.
1. `.claude/skills/part-3d/SKILL.md` 를 읽는다(없으면 `git show HEAD:.claude/skills/part-3d/SKILL.md`).
2. `node scripts/part-start.mjs <부품이름>` — 서버·키·DB·브랜드별 현황·그 부품의 DB 행·생성기 목록·체크리스트를 한 번에 본다.
3. `process/06_3D부품_만들기_등록.md` 가 순서·금지·확인의 입구이고, 규격 숫자의 원본은 `get_part_standard`(`app/lib/cubo-part-maker.js`)다. 규격 메모는 `process/부품규격/`.
4. 보여 주는 곳은 **부품 관리 화면**(부품 수리실이 아니다). 모델 → 숫자 검증 → 등록 → 3D 썸네일 → 연결점까지 끝나야 끝이다.

**로버트론 부품(에이스랩·로보타미주니어) 3D 모델 규칙**
- **테두리 선(사용자 2026-10-27):** 모든 부품에 실제 윤곽을 따라 아주 얇은 선(0.1mm)을 긋는다 — 사각 상자 둘레가 아니라 바깥 둘레(둥근 모서리 포함)·구멍 둘레·붙은 부품의 경계. 색은 부품 색이 어두우면 조금 밝게, 밝으면 조금 어둡게(`app/lib/robotron-line-color.js` 의 `lineColorFor`). 본보기: `scripts/make-robotron-flatplate.mjs`.
- 부품 관리 3D 창에서 부품을 클릭하면 크기(가로×높이×세로 mm)가 창 위에 나온다.
- 3D 부품 모델을 새로 만들거나 고치기 전에 `get_part_standard` 의 '새 3D 부품을 만들거나 고칠 때 지킬 것'을 읽는다(큐보 전용이 아니다). 삼각형을 직접 짜서 몸통 2~3천 개·약 110KB 안팎(기준 비교 = 같은 크기 35프레임, 큐보 6,316개·308KB / 에이스랩 2,552개·125KB), 칸으로 나눈 면은 `conformTJunctions`, 끝나면 `checkMesh` 숫자(짝 없는 모서리 0·같은 방향 겹침 0·부피 양수)와 몸통/선 KB 를 보고한다. `make-robotron-*.mjs` 는 `assertPartMesh` 에 걸리면 등록하지 않는다 — 검사를 끄지 않는다.

## 환경에서 사람이 줘야 하는 것
- `.env.local`(git 에 없음): `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — `userdone.py`·`record_check.py`·`number_start.py`·`dbimgcheck.py` 가 사용자 ✓·❄·📷·올린 그림을 DB 에서 읽는 데 필요. 없으면 사용자에게 달라고 하거나 Vercel 환경변수에서 가져온다.
- 설계 화면 로그인(선생님 계정): 사용자가 직접 한다.
- 교재 PDF 는 조립도 작업에 필요 없다 — 단계별 책 그림은 `scripts/assembly-tools/refs/<이름>/NN.jpg` 에 이미 잘려 있다.

## 지킬 것
- **책 대조는 등록된 교재 PDF 로 한다(사용자 지시 2026-10-27):** "원본 PDF 가 없어서 못 한다"고 말하지 않는다. PDF 위치·받는 법은 `process/01_새조립도_시작_번호등록.md` 11·16행(`ivs_textbooks` → `data.files[0].url`). 조립도뿐 아니라 부품·수량·차시를 등록하거나 고칠 때도 먼저 읽고 대조한다.
- 나머지 조립도 규칙은 전부 `00_규칙.md` 에 있다 — 여기에 다시 적지 않는다. `[도구]` 표시가 붙은 규칙은 도구가 막는다.
- Windows 콘솔은 cp949 → 파이썬 실행 시 `PYTHONIOENCODING=utf-8`.
