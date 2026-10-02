# 큐보 조립도 제작 도구 (로봇팽이에서 만든 것 — 다음 차시에 그대로 재사용)

1. `python extract_parts.py` (IVS_MCP_URL 필요) → parts/*.npy, conn.json, dims.json, viewer/parts.js
2. 교재 쪽을 PyMuPDF로 330dpi 이미지로 뽑아 단계 패널을 자른다(안내서 6-2절).
3. `pnp.py`/`camutil.py`/`ovl.py`: 판 모서리 4~6점으로 카메라를 맞추고(solvePnP), 초록 원을 판 윗면에 투영해 구멍 번호를 읽고, 와이어프레임을 교재 그림에 겹친다.
4. `rbtools.py`/`rbkit.py`: 돌기→구멍 결합 자세 계산(attach, block_R, frame_R, solve_p_pegs), `rbout.py` 바닥 올리기, `rbexport.py` 조립 데이터를 design-assemblies.js 항목으로 출력.
5. `check.js`: public/design-mates.js·design-collision.js 로 로컬 검사(`node check.js asm.json`).
6. `preview.html`(+ viewer/parts.js, da.js=design-assemblies.js 복사본): 드래그로 도는 실제 3D 미리보기. `python -m http.server` 로 띄워 `preview.html?step=N&id=...`.

## 새 PC에서 조립도 작업 시작하기 (2026-10-02 정리 — ✔ 이 PC에서 확인한 것 / ? 새 PC에서 아직 안 해 본 것)
1. 준비물: Git, Node.js(npm), Python 3 + `pip install numpy opencv-python` (✔ 스크립트가 쓰는 라이브러리: numpy, cv2). Claude Code 데스크톱 앱.
2. 저장소 받기: `git clone https://github.com/mindaephow/invent_school.git` 후 폴더에서 `npm install` (✔ node_modules 는 .gitignore 라 git 에 없음). 푸시는 GitHub 로그인(계정 mindaephow)이 필요하다.
3. 로컬 서버: 프로젝트 `.claude/launch.json` 은 .gitignore(`.claude/`) 라서 **새 PC 에는 없다 → 직접 만든다.** 예:
   `{"version":"0.0.1","configurations":[{"name":"invent-school-dev","runtimeExecutable":"npm","runtimeArgs":["run","dev","--","-p","3177"],"port":3177}]}`
   그다음 `preview_start {name:"invent-school-dev"}` → 브라우저 패널에서 `http://localhost:3177/design.html`. (`npm run start` 는 먼저 `npm run build` 가 필요 — 개발 서버 `npm run dev` 가 간단하다.) 같은 이름·포트를 다른 채팅이 쓰는 중이면 "Port in use" 가 나온다 → 그 서버 주소로 그냥 접속하거나 포트를 바꾼다.
4. 로그인: 설계 화면은 선생님 아이디/비밀번호 로그인이 필요하다(✔ 로그인 화면이 뜸). 로그인은 사용자가 직접 한다 — 비밀번호를 대신 입력하지 않는다. 화면의 DB 연결은 브라우저 쪽 설정(db-shim.js)이라 로컬에 `.env` 가 없어도 되는 것으로 보이나 ? 새 PC 에서 확인 필요.
5. `.env` 가 필요한 것: `/api/admin`·`/api/mcp`(서버 쪽, SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 등)은 키가 없으면 로컬에서 500 이다(✔ 안내서 7절). 조립도 화면 확인에는 필요 없다. 키는 Vercel 프로젝트 환경변수에 있다.
6. 조립도 만들기: `cd scripts/assembly-tools` → `python build.py <이름>` (부품 연결점 생성·스크립트 실행·검사). 결과를 화면에 넣으려면 `--write` (public/design-assemblies.js 수정). 로컬 서버가 public 파일을 바로 서빙하므로 새로고침하면 보인다 (✔).
7. 부품 3D 모델(STL)을 직접 뽑아 보는 `preview.html`·`extract_parts.py` 는 환경변수 `IVS_MCP_URL`(발명학교 MCP 주소)이 필요하다. 보통은 6번의 설계 화면으로 충분하다.
8. 시작 순서(안내서 10-1): 로컬 서버를 먼저 띄워 패널에 설계 화면을 열어 두고 → 조립도 작업 → 고칠 때마다 새로고침해 확인.
