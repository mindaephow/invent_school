# 큐보 조립도 제작 도구

1. `python partlib.py` → `conn.json`·`dims.json`(부품 연결점·크기). 프레임은 규칙대로 만들고 나머지는 부품 DB 값을 적어 둔 것이다.
2. 교재 쪽을 PyMuPDF로 330dpi 이미지로 뽑아 단계 패널을 자른다(안내서 6-2절).
3. `pnp.py`·`camfit.py`: 판 모서리 점(3D↔화면 픽셀)으로 카메라를 맞춘다(solvePnP). 지금 번호 작업에서 축·카메라는 `axes_fit.py` 가 한다(`process/05_조립.md`).
4. `asmlib.py`(조립 프로그램): 설명서 번호를 코드(`<이름>.py`)로 옮기면 위치·회전·안내점이 계산된다. `emit.py` 가 그 결과를 `public/design-assemblies.js` 에 넣는다.
5. `check_local.js`: `public/design-mates.js`·`design-collision.js` 로 로컬 검사(`node check_local.js asm.json`, 작업 폴더에 `conn.json`·`dims.json` 필요).
6. 미리보기: 설계 화면의 조립 보기(개발 서버 주소는 `CLAUDE.md` 1번).

## 새 PC에서 조립도 작업 시작하기 (2026-10-02 정리 — ✔ 이 PC에서 확인한 것 / ? 새 PC에서 아직 안 해 본 것)
1. 준비물: Git, Node.js(npm), Python 3 + `pip install numpy opencv-python` (✔ 스크립트가 쓰는 라이브러리: numpy, cv2). Claude Code 데스크톱 앱.
2. 저장소 받기: `git clone https://github.com/mindaephow/invent_school.git` 후 폴더에서 `npm install` (✔ node_modules 는 .gitignore 라 git 에 없음). 푸시는 GitHub 로그인(계정 mindaephow)이 필요하다.
3. 로컬 서버: 프로젝트 `.claude/launch.json` 은 .gitignore(`.claude/`) 라서 **새 PC 에는 없다 → 직접 만든다.** 예:
   `{"version":"0.0.1","configurations":[{"name":"invent-school-dev","runtimeExecutable":"npm","runtimeArgs":["run","dev","--","-p","3178"],"port":3178}]}`
   그다음 `preview_start {name:"invent-school-dev"}` → 주소는 `CLAUDE.md` "새로 시작하거나 새 세션일 때" 1번. (`npm run start` 는 먼저 `npm run build` 가 필요 — 개발 서버 `npm run dev` 가 간단하다.) 같은 이름·포트를 다른 채팅이 쓰는 중이면 "Port in use" 가 나온다 → 그 서버 주소로 그냥 접속하거나 포트를 바꾼다.
4. 로그인: 설계 화면은 선생님 아이디/비밀번호 로그인이 필요하다(✔ 로그인 화면이 뜸). 로그인은 사용자가 직접 한다 — 비밀번호를 대신 입력하지 않는다. 화면의 DB 연결은 브라우저 쪽 설정(db-shim.js)이라 로컬에 `.env` 가 없어도 되는 것으로 보이나 ? 새 PC 에서 확인 필요.
5. `.env` 가 필요한 것: `/api/admin`·`/api/mcp`(서버 쪽, SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 등)은 키가 없으면 로컬에서 500 이다(✔ 안내서 7절). 조립도 화면 확인에는 필요 없다. 키는 Vercel 프로젝트 환경변수에 있다.
6. 조립도 만들기: `cd scripts/assembly-tools` → `python build.py <이름>` (부품 연결점 생성·스크립트 실행·검사). 결과를 화면에 넣으려면 `--write` (public/design-assemblies.js 수정). 로컬 서버가 public 파일을 바로 서빙하므로 새로고침하면 보인다 (✔).
7. 부품 3D 모델·연결점은 부품 DB(설계 화면)에 있고, 로컬 작업용 `conn.json`·`dims.json` 은 `python partlib.py` 로 만든다.
8. 시작 순서(안내서 10-1): 로컬 서버를 먼저 띄워 패널에 설계 화면을 열어 두고 → 조립도 작업 → 고칠 때마다 새로고침해 확인.
