---
name: project-invent-school
description: "발명융합과학교실 (홍허브 발명학교) — live on mindaephow accounts: landing, 3D design tool (teacher+student save/load, submit, teacher rating+advice, movable start/goal, marbles), teacher dashboard, HQ admin page with teacher approval, Google login. As of 2026-09-20 everything is deployed (344fbee); test accounts await cleanup"
metadata: 
  node_type: memory
  type: project
  originSessionId: 66b15530-3124-4d75-84e3-f4a90cbda3aa
  modified: 2026-09-21T02:25:16.231Z
---

**Live:** https://invent-school-sigma.vercel.app — Next.js, repo `mindaephow/invent_school`, dedicated Supabase `brfeszcyjsaprbakqsjl`, all under `mindaephow@gmail.com`. Screen name **발명융합과학교실**; HongHub project 발명학교 (site id 4b18ca36-ee0d-4fac-80e0-44ef796196dd, connector 발명학교-Mcp, claude.ai connector 발명교실-Mcp, tools `mcp__da6d2e51-...`).

**Read the HongHub `plan_content` for 발명학교 first** — refreshed 2026-09-20 after the start/goal, sidebar and discard-button work (current state, architecture, auth/approval/admin/Google, data model, design-tool flow, working principles, pending list) with the decision history in `progress_log`. If code and doc disagree, trust `git log` in `C:\Users\user\Downloads\invent_school`. When the user says "홍허브 계획서에 업데이트", rewrite plan_content as current state (not date appends) and append decisions to progress_log.

**Pushing:** the user pushes (`cd C:\Users\user\Downloads\invent_school` → `git push newrepo main`). Claude pushing to another account's repo is blocked by the safety check — don't work around it. At 2026-09-20 local = remote = `344fbee`, nothing unpushed. Commit identity is passed per-command (`git -c user.name=invent-school -c user.email=mindaephow@gmail.com commit`). After the user says "올렸어요", verify with `git ls-remote newrepo main` + `curl` markers, then test the live site in the browser pane.

**User-run SQL:** schema changes go through the Supabase SQL editor (MCP run_sql is read-only): `setup.sql` → `approval.sql` → `teacher_projects.sql` → `feedback.sql`, all already run. Give the SQL as one block with the direct link, then verify the result myself via MCP run_sql + API tests.

**Pending (2026-09-21):** delete test teacher `mindaephow+t2@gmail.com` in the admin page (cascades; then confirm counts are 0); confirm who `testssam@naver.com` is; Google OAuth consent screen still "테스트 중" (publish before other teachers self-register); landing subject-tab content review; PIN lockout and saved-design delete UI not built.

**Idea backlog (not started — user said "일단 아이디어로만" 2026-09-21):** Minecraft-style UX for kids — hotbar-style quick part select (number keys) and a highlighted-cell placement preview cursor were the two low-risk candidates discussed. Explicitly ruled out: a full WASD/first-person camera (would fight the precise-rotation physics-puzzle nature of the tool). User admitted they haven't actually played Minecraft themselves — this is a hunch, not a spec; confirm direction before building.

**Design-tool physics/play system (design.html, current as of 2026-09-21, commit `436234a`):** basket goal detection uses a sensor-plane crossing check at the rim (not a loose bounding-radius check — that falsely triggered near the pole/rim). Marble entering the goal does NOT freeze play; it keeps rolling, the entry time is captured as a candidate record (shown live, frozen, in a "기록" badge) while the "초시계" keeps counting in real time below it; if the ball stays in for 3s the record confirms (success, confetti, play stops); bouncing back out before 3s cancels the candidate silently. Play controls: 재생 button toggles play/pause (퓨즈) and *resumes in place* rather than restarting; 초시계 has independent 퓨즈/중지/리셋 buttons that can decouple from the marble's play state. All of this lives in a single draggable, foldable (starts folded), fixed-width (400px) `.play-panel` — do not let it change size as rows show/hide, elements must stay always-rendered with placeholder text, not toggled via `hidden`. Basket physics floor uses `CANNON.Box` not `CANNON.Cylinder` (this cannon.js 0.6.2 build orients Cylinder's axis wrong, silently letting balls fall through — see [[feedback_verify_before_claiming]] pattern, confirmed by live play-testing twice).

**"따라하기" trace-guide feature (added 2026-09-21):** a "🖍 따라만들기" toggle in the scene view-tools renders the current lesson's `sample` array as a dashed/ghost THREE.js wireframe overlay (`guideGroup`, `buildGuideOutline()`) — like a handwriting-practice notebook's faint guide line, kids place real parts on top of it. The left lesson card has a "🖍 따라하기 시작" button embedded inline mid-list (via a `'__START_FOLLOW__'` sentinel string in `lesson.steps`, design.html moves the actual DOM button node into that `<li>` rather than cloning it) that clears the canvas and turns the guide on in one click. `lesson.steps` in design-lessons.js now has the full walkthrough for lesson 1 (drag panel → click 바닥 → axis X → 돌리기 → check 0° → ㄱ자연결대 ×2 → second panel as wall → clip → rail → basket + 도착 지점으로 정하기 → marble → 재생). The `.mission ol.lesson-steps` list is capped at `max-height:220px` with its own scroll so a long step list doesn't push the parts palette off-screen.

**Axis button labels:** X/Y/Z rotate-axis buttons now show a small hint under the letter — X=좌우, Y=위아래, Z=앞뒤 — confirmed correct for this app's coordinate convention (pos array is [x,y,z], y is height).

Never delete the user's designs or my test designs without telling them first (they objected once). When live-testing design.html in the browser, always use 불러오기 to load the user's actual saved project, never 샘플 열기/새 설계 while they're watching — see [[feedback_use_load_not_sample_invent_school]].

**Working style here:** never invent class facts — ask the user a question list and use their answers verbatim. Give exact links/buttons, one step at a time. Verify their steps myself. Teacher and student roles get the same tool capabilities — don't ship a reduced version for one role (see [[feedback-role-parity]]). For "should X be…?" questions answer in 2–3 sentences with a recommendation, implement once the user proposes/agrees.
