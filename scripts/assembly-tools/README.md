# 큐보 조립도 제작 도구 (로봇팽이에서 만든 것 — 다음 차시에 그대로 재사용)

1. `python extract_parts.py` (IVS_MCP_URL 필요) → parts/*.npy, conn.json, dims.json, viewer/parts.js
2. 교재 쪽을 PyMuPDF로 330dpi 이미지로 뽑아 단계 패널을 자른다(안내서 6-2절).
3. `pnp.py`/`camutil.py`/`ovl.py`: 판 모서리 4~6점으로 카메라를 맞추고(solvePnP), 초록 원을 판 윗면에 투영해 구멍 번호를 읽고, 와이어프레임을 교재 그림에 겹친다.
4. `rbtools.py`/`rbkit.py`: 돌기→구멍 결합 자세 계산(attach, block_R, frame_R, solve_p_pegs), `rbout.py` 바닥 올리기, `rbexport.py` 조립 데이터를 design-assemblies.js 항목으로 출력.
5. `check.js`: public/design-mates.js·design-collision.js 로 로컬 검사(`node check.js asm.json`).
6. `preview.html`(+ viewer/parts.js, da.js=design-assemblies.js 복사본): 드래그로 도는 실제 3D 미리보기. `python -m http.server` 로 띄워 `preview.html?step=N&id=...`.
