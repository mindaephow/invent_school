// 조립 보기 — 교재 차시의 조립 순서를 단계별로(앞으로/뒤로/자동재생/역재생/번호로 바로가기) 보여준다.
// 데이터는 design-assemblies.js, 설계 화면과의 연결(부품 놓기·카메라 등)은 design.html이 만드는 window.__ivsAssemblyBridge를 쓴다.
//
// 교재 그림처럼: 지금 단계에 새로 끼우는 부품은 제자리에서 살짝 띄워 두고(끼우기 직전) 초록 화살표와 구멍 원으로
// "여기에 꽂아요"를 보여준다. 다음 단계로 넘어가면 제자리에 끼워지고, 맨 끝 "완성"에서는 전부 제자리에 놓인다.
(function () {
  const $ = (id) => document.getElementById(id);
  const PLAY_MS = 1100;
  const HOVER_RECV = 20; // 프레임 같은 '구멍 받는 부품'이 움직일 때는 더 가까이 띄운다(너무 멀면 공중에 떠 보인다)
  const HOVER = 22;      // 끼우기 직전 부품을 띄우는 거리(mm)
  const PEG_DEPTH = 5;   // 돌기가 구멍 안으로 들어가는 깊이(mm) — 프레임 두께와 같다
  let def = null;        // 지금 고른 차시에 맞는 조립 데이터
  let catId = null;      // 지금 고른 카테고리 id (부품 이름으로 부품을 찾을 때 씀)
  let lastAxKey = '';
  let renderSeq = 0; // 단계를 다시 그릴 때마다 올려서, 늦게 도는 안내점 다시 붙이기가 옛 단계 것이면 건너뛴다
  let showHoleNums = true; // 프레임 구멍 번호(열-줄) 표시
  try { if (localStorage.getItem('ivs-asm-holenums') === '0') showHoleNums = false; } catch (e) { /* 저장 못 해도 기본값 */ }
  let lastCamKey = '';   // 지금 단계에서 맞춰 둔 카메라 각도(theta|phi) — 바뀔 때만 돌린다
  let viewing = false;   // 조립 보기 중인지
  let step = 0;          // 0 = 빈 판, 1..N = 각 단계, N+1 = 완성
  let snapshot = null;   // 조립 보기 들어가기 전 작업(닫으면 그대로 되돌린다)
  let timer = null;      // setInterval 번호
  let timerDir = 0;      // 자동재생 방향(1 앞으로, -1 뒤로, 0 멈춤)

  function bridge() { return window.__ivsAssemblyBridge; }
  function total() { return def ? def.steps.length : 0; }
  function last() { return total() + 1; } // "완성" 단계 번호
  const add = (p, d, k) => [p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k];
  // 회전 행렬 ↔ 오일러각(도, ZYX) — def.xform(몸체를 세우는 것처럼 어느 단계부터 전체를 통째로 돌리고 옮기는 변환)에 쓴다
  const DEG = Math.PI / 180;
  const mmul = (a, b) => [0, 1, 2].map((i) => [0, 1, 2].map((j) => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]));
  const mvec = (m, v) => [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2]);
  function eulerToMat(r) {
    const [a, b, c] = r.map((v) => v * DEG), ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b), cc = Math.cos(c), sc = Math.sin(c);
    return mmul([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]], mmul([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]], [[1, 0, 0], [0, ca, -sa], [0, sa, ca]]));
  }
  function matToEuler(m) {
    const sy = Math.max(-1, Math.min(1, -m[2][0])), ry = Math.asin(sy); let rx, rz;
    if (Math.abs(sy) > 0.99999) { rz = 0; rx = Math.atan2(m[0][1] / sy, m[0][2] / sy); } else { rx = Math.atan2(m[2][1], m[2][2]); rz = Math.atan2(m[1][0], m[0][0]); }
    const f = (v) => { v = Math.round(v / DEG * 10) / 10; return Object.is(v, -0) ? 0 : v; };
    return [f(rx), f(ry), f(rz)];
  }

  // ── 로봇 뒤집기(def.flip): 교재가 "반대로 뒤집기"로 로봇을 뒤집어 그리는 차시용 ──
  // 조립 데이터(p·r·marks·dir …)는 모두 "뒤집은 뒤(최종 방향)"로 적어 두고, def.flip.ranges 에 든 단계에서는 화면에 뒤집기 전 모양
  // (교재가 그린 방향)으로 바꿔 보여 준다. 변환: (x,y,z) → (x, flip.y − y, flip.z − z), 회전은 x축 180° 뒤집기 — 두 번 하면 제자리라 양쪽 어느 방향이든 같은 식이다.
  const D2R = Math.PI / 180;
  function matFromEuler(r) {
    const a = r[0] * D2R, b = r[1] * D2R, c = r[2] * D2R;
    const cx = Math.cos(a), sx = Math.sin(a), cy = Math.cos(b), sy = Math.sin(b), cz = Math.cos(c), sz = Math.sin(c);
    return [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx], [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx], [-sy, cy * sx, cy * cx]];
  }
  function eulerFromMat(R) {
    const sy = Math.max(-1, Math.min(1, -R[2][0]));
    const ry = Math.asin(sy);
    let rx, rz;
    if (Math.abs(sy) < 0.99999) { rx = Math.atan2(R[2][1], R[2][2]); rz = Math.atan2(R[1][0], R[0][0]); } else { rx = Math.atan2(-R[1][2], R[1][1]); rz = 0; }
    return [rx / D2R, ry / D2R, rz / D2R].map((v) => Math.round(v * 1e4) / 1e4 + 0);
  }
  function flipActive(target) { return !!(def && def.flip && (def.flip.ranges || []).some((rg) => target >= rg[0] && target <= rg[1])); }
  function flipPt(pt, target) {
    const f = def.flip;
    const rg = (f.ranges || []).find((r) => target >= r[0] && target <= r[1]);
    const fy = rg && rg[2] != null ? rg[2] : f.y; // 범위별로 바닥 기준이 다르면 ranges 의 [시작, 끝, y]
    const P = (p) => [p[0], fy - p[1], f.z - p[2]];
    const V = (v) => [v[0], -v[1], -v[2]];
    const R = (r) => { const A = matFromEuler(r || [0, 0, 0]); return eulerFromMat([A[0], [-A[1][0], -A[1][1], -A[1][2]], [-A[2][0], -A[2][1], -A[2][2]]]); };
    const o = Object.assign({}, pt);
    o.p = P(pt.p); o.r = R(pt.r);
    ['marks', 'faceMarks', 'settleMarks', 'holeMarks'].forEach((k) => { if (pt[k]) o[k] = pt[k].map(P); });
    ['dir', 'settleDir'].forEach((k) => { if (pt[k]) o[k] = V(pt[k]); });
    if (pt.side) o.side = Object.assign({}, pt.side, { p: P(pt.side.p), r: R(pt.side.r) });
    if (pt.explode) { const e = pt.explode; o.explode = Object.assign({}, e, { offset: e.offset ? V(e.offset) : e.offset, from: e.from ? P(e.from) : e.from, marks: e.marks ? e.marks.map(P) : e.marks }); }
    return o;
  }

  // target 단계까지의 부품 목록과, 이번 단계의 초록 안내(화살표·구멍 원)를 만든다.
  function buildList(target) {
    const b = bridge();
    const list = [];
    const guides = [];
    const missing = [];
    const n = total();
    const upTo = Math.min(target, n);
    const flipOn = flipActive(target);
    def.steps.slice(0, upTo).forEach((s, si) => {
      (s.parts || []).forEach((pt0) => {
        const pt = flipOn && !pt0.noflip ? flipPt(pt0, target) : pt0; // 뒤집기 전 방향으로 보여 주는 단계(noflip: 로봇과 따로 만드는 손잡이는 그대로)
        const type = b.resolve(pt.n, catId);
        if (!type) { if (!missing.includes(pt.n)) missing.push(pt.n); return; }
        const useSide = pt.side && upTo < pt.side.until;
        const moved = pt.move && upTo >= pt.move.at; // move: 옆자리에서 다 만든 뒤 다른 자리로 한 번 더 옮겨 붙는 단계(예: 풍차 상자를 몸체에 끼우기)
        // move: { at, by } 평행 이동 또는 { at, p, r } 새 자세로 옮기기(회전 포함 — 예: 3륜바이크 7단계 샌드위치를 뒤집어 올림)
        let base = useSide ? pt.side.p : (moved ? (pt.move.p || add(pt.p, pt.move.by || [0, 0, 0], 1)) : pt.p);
        // lift: 다 만든 묶음(총몸·기둥)이 받침 위에 띄워져 있다가(from~at 직전 단계) at 단계에 위에서 내려와 결합한다(교재 29) — { from, at, by, dir, hover, marks }
        if (pt.lift && !useSide && upTo >= (pt.lift.from || 0) && upTo < pt.lift.at) base = add(base, pt.lift.by || [0, 0, 0], 1);
        const rot = useSide ? pt.side.r : (moved && pt.move.r ? pt.move.r : pt.r);
        // 이번 단계에 새로 놓이거나(또는 옆자리에서 제자리로 들어가는) 부품 — 완성 단계에선 없다
        const isNew = target <= n && (si + 1 === target || (pt.side && pt.side.until === target) || (pt.move && pt.move.at === target) || (pt.lift && pt.lift.at === target));
        let pos = base;
        // 옆자리 조립품이 제자리로 합쳐지는 단계(settle)에는 settleDir(없으면 dir)로 띄우고, settleMarks(있는 부품만) 자리로 안내한다
        const lowering = !!(pt.lift && pt.lift.at === target); // 위에서 내려와 결합하는 단계
        const mvSrc = lowering ? pt.lift : pt.move;
        const moving = !!(pt.move && pt.move.at === target) || lowering;
        const settling = !!(pt.side && !useSide) || moving;
        const dirH = moving ? mvSrc.dir : (settling ? (pt.settleDir || pt.dir) : pt.dir);
        // 앞 단계에서 만든 부품을 이번 단계에서 "결합되기 전" 모습으로 띄워 보여준다(예: 14단계 T축+기어를 15프레임 위로)
        const ex = pt.explode && pt.explode.step === target ? pt.explode : null;
        if (ex) {
          pos = add(base, ex.offset, 1);
          (ex.marks || []).forEach((m) => guides.push({ from: ex.from, to: m, dir: [0, -1, 0], idx: list.length }));
        }
        if (isNew && pt.seated && !lowering) {
          // seated: 교재가 이미 꽂아 둔 모양으로 그리는 부품(리벳 등) — 떠서 내려오지 않고 제자리에 두고, 꽂힌 구멍에 초록 원만 칠한다(교재 23·25·27)
          (pt.marks || []).forEach((m) => guides.push({ from: m, to: m, dir: dirH || [0, 1, 0], idx: list.length, ringOnly: true }));
        } else if (isNew && dirH) {
          // 띄우는 거리·돌기가 들어가는 깊이·판 두께는 부품마다 정할 수 있다(T축처럼 길게 꽂히는 것, 두꺼운 부시)
          const hv = moving ? (mvSrc.hover || HOVER) : settling ? HOVER : (pt.hover || (pt.recv ? HOVER_RECV : HOVER)); // 합쳐지는 묶음은 모두 같은 거리로 띄워야 모양이 흐트러지지 않는다
          const depth = pt.pegDepth || PEG_DEPTH;
          pos = add(base, dirH, hv); // 끼우기 직전: 제자리에서 끼우는 방향으로 띄운다
          const targets = moving ? (mvSrc.marks || []) : settling ? (pt.settleMarks || []) : (pt.marks && pt.marks.length ? pt.marks : [base]);
          // 화살표는 띄워 놓은 부품의 돌기 끝(구멍에 들어갈 깊이만큼 아래)에서 시작해 구멍 위 원으로 들어간다
          if (pt.recv && !pt.pegTarget) { // pegTarget: 구멍 받는 부품이 움직여도 교재처럼 화살표가 고정된 돌기 끝을 향하게 그린다(marks = 고정된 돌기 끝)
            // 구멍을 받는 부품(프레임 등)이 움직일 때: 원은 떠 있는 부품의 구멍에, 화살표는 고정된 돌기 끝에서 그 구멍 쪽으로
            // faceMarks: 돌기 끝이 판 바깥 면과 같은 높이가 아닐 때, 제자리에 끼운 뒤 판 바깥 면의 구멍 자리
            const faces = !settling && pt.faceMarks ? pt.faceMarks : targets;
            targets.forEach((m, i) => guides.push({ from: m, to: add(faces[i] || m, dirH, hv), dir: dirH, idx: list.length, both: pt.thick || 5 }));
          } else {
            targets.forEach((m) => guides.push({ from: add(m, dirH, hv - depth), to: m, dir: dirH, idx: list.length }));
          }
        }
        // holeMarks: 프레임 구멍에 고정된 결합 위치 원(교재처럼 판 구멍에 표시, 부품이 움직여도 그 자리)
        if (isNew && !moving && pt.holeMarks) pt.holeMarks.forEach((m) => guides.push({ from: m, to: m, dir: dirH || [0, 1, 0], idx: list.length, ringOnly: true }));
        list.push({ name: pt.n, type, mount: 'floor', pos: pos.slice(), quat: b.quat(rot), rot: rot.slice(), isNew, final: (isNew && dirH) || ex ? base.slice() : null, order: settling ? 1 : (pt.joinOrder || (ex && ex.order) || 1) }); // 합쳐지는 묶음(settle)은 모두 한꺼번에 내려온다 // ex: 14단계처럼 "결합 전"으로 띄운 부품도 제자리(결합 후)가 있다
      });
    });
    // xform: 이 단계부터는 지금까지 만든 것 전체를 통째로 돌려서 놓는다(예: 풍차 몸체를 세워서 받침에 올리기). 부품 자리는 원래 좌표 그대로 두고 여기서 한꺼번에 변환한다.
    const xf = def.xform && target >= def.xform.at ? def.xform : null;
    if (xf) {
      const T = (v) => { const w = mvec(xf.m, v); return [w[0] + xf.t[0], w[1] + xf.t[1], w[2] + xf.t[2]]; };
      list.forEach((d) => {
        if (d.noXform) return;
        d.pos = T(d.pos); if (d.final) d.final = T(d.final);
        d.rot = matToEuler(mmul(xf.m, eulerToMat(d.rot))); d.quat = b.quat(d.rot);
      });
      guides.forEach((g) => { g.from = T(g.from); g.to = T(g.to); g.dir = mvec(xf.m, g.dir); });
    }
    return { list, guides, missing, targets: list.map((d) => d.final || null), orders: list.map((d) => d.order || 1) };
  }

  // 1, 2, 3 … 단계 번호 버튼(+ 마지막 "완성") — 눌러서 그 단계로 바로 가고, 지금 단계는 진하게 보인다.
  function buildStepButtons() {
    [$('asmSteps'), $('asmStageSteps')].forEach((box) => {
      box.innerHTML = '';
      for (let i = 1; i <= last(); i++) {
        const b = document.createElement('button');
        b.type = 'button';
        b.dataset.step = String(i);
        b.textContent = i === last() ? '완성' : String(i);
        b.title = i === last() ? '완성된 모습' : i + '단계: ' + (def.steps[i - 1].note || '');
        b.style.cssText = i === last() ? 'padding:5px 10px; font-size:13px;' : 'min-width:32px; padding:5px 0; font-size:13px;';
        box.appendChild(b);
      }
    });
  }
  // 왼쪽 카드의 "조립 순서" 목록 — 조립 보기를 열기 전에도 항상 보이고, 누르면 그 단계로 간다.
  function buildOrderList() {
    const ol = $('asmOrderList');
    ol.innerHTML = '';
    if (!def) return;
    def.steps.forEach((s, i) => {
      const li = document.createElement('li');
      const b = document.createElement('button');
      b.type = 'button';
      b.dataset.step = String(i + 1);
      b.className = 'ghost';
      b.style.cssText = 'width:100%; text-align:left; padding:3px 8px; border-radius:8px; font-size:12.5px; font-weight:400;';
      b.textContent = (i + 1) + '. ' + (s.note || '');
      li.appendChild(b);
      ol.appendChild(li);
    });
  }
  function markStepButtons() {
    document.querySelectorAll('#asmOrderList button').forEach((b) => {
      const cur = Number(b.dataset.step) === step;
      b.style.fontWeight = cur ? '800' : '400';
      b.style.background = cur ? 'var(--blueprint, #2b6be0)' : '';
      b.style.color = cur ? '#fff' : '';
      b.setAttribute('aria-current', cur ? 'step' : 'false');
    });
    document.querySelectorAll('#asmSteps button, #asmStageSteps button').forEach((b) => {
      const n = Number(b.dataset.step);
      const cur = n === step;
      b.className = cur ? 'primary' : 'ghost';
      b.style.opacity = n < step ? '0.75' : '1'; // 이미 지나온 단계는 살짝 연하게
      b.setAttribute('aria-current', cur ? 'step' : 'false');
    });
    // 화면 위 단계 줄: 지금 단계가 가운데 오게 옆으로 밀어 준다
    const box = $('asmStageSteps'), curBtn = box.querySelector('button[aria-current="step"]');
    if (curBtn) box.scrollLeft = curBtn.offsetLeft - box.clientWidth / 2 + curBtn.offsetWidth / 2;
  }

  function render() {
    const b = bridge();
    const { list, guides, missing, targets, orders } = buildList(step);
    b.show(list.map(({ isNew, name, final, order, ...d }) => d), targets, orders);
    // 지금 단계에 보이는 부품(끼우기 직전 위치 포함)에 카메라를 맞춘다 — 처음부터 너무 멀리서 보이지 않게
    // 이번 단계에 끼우는 부품과 그 끼워지는 자리를 화면 가운데에 크게 보여준다(나머지 부품은 배경)
    const focus = list.filter((d) => d.isNew).map((d) => d.pos).concat(guides.map((g) => g.to));
    const stc = (step > 0 && step < last()) ? def.steps[step - 1].cam : null; // cam.tight: 이번에 끼우는 부분만 크게(교재가 그 부분만 크게 그린 단계)
    { const axAt = stc && Array.isArray(stc.axes) ? stc.axes : null; const axKey = axAt ? axAt.join(',') : ''; // cam.axes: 이 단계의 기준점(방향선 원점)
      if (axKey !== lastAxKey) { lastAxKey = axKey; b.axes(true, axAt); } }
    const camFocus = stc && Array.isArray(stc.focus) && stc.focus.length ? stc.focus : null; // cam.focus: 부품이 없는 단계 등에서 이 점들을 화면 가운데에 크게(조립 프로그램이 지정)
    const axPt = stc && Array.isArray(stc.axes) ? stc.axes : [0, 0, 0]; // 바닥 기준선(방향선) 자리 — 카메라가 보는 범위에 항상 같이 들어오게 한다
    if (camFocus) b.frame(camFocus.concat([axPt]), camFocus.concat([axPt]));
    else {
      const f0 = focus.length ? focus : list.map((d) => d.pos);
      b.frame(f0.concat(stc && stc.tight ? [axPt] : []), stc && stc.tight ? f0.concat([axPt]) : list.map((d) => d.pos));
    }
    if (stc && Array.isArray(stc.rings)) stc.rings.forEach((m) => guides.push({ from: m, to: m, dir: [0, 1, 0], idx: -1, ringOnly: true })); // cam.rings: 이 단계에 고정으로 칠할 결합 점(예: 받침 흰 판 구멍)
    b.guides(guides);
    // 프레임 구멍 번호: 이번 단계에 결합 위치(초록 원·돌기 끝)가 걸리는 프레임에서, 같은 줄의 "이미 꽂힌 부품(블록 돌기·T축 등) 다음 구멍부터 1, 2, 3…"으로 센다
    // (두 부품 사이는 왼쪽 부품 다음부터 1, 2, 3…, 판 끝과 부품 사이는 부품 쪽에서부터) — 사용자 지시: "블록 다음부터 1,2,3 · T축과 T축 사이에 1,2,3"
    if (b.holeLabels) {
      const items = [];
      if (showHoleNums && stc && stc.holeNums && guides.length) { // cam.holeNums: 이 단계에서만 구멍 번호를 보여준다(단계마다 조립 데이터가 정함)
        const conns = b.connectorsByName ? b.connectorsByName() : {};
        const pts = []; guides.forEach((g) => { pts.push(g.to); pts.push(g.from); });
        // 다른 부품의 돌기(월드 좌표): 위치·방향·길이
        const pegs = [];
        list.forEach((d2) => {
          const c2 = conns[d2.name]; if (!c2 || !c2.pegs) return;
          const R2 = matFromEuler(d2.rot || [0, 0, 0]);
          c2.pegs.forEach((pg) => { const w = mvec(R2, pg.pos); pegs.push({ owner: d2, p: [d2.pos[0] + w[0], d2.pos[1] + w[1], d2.pos[2] + w[2]], len: pg.len || 5 }); });
        });
        list.forEach((d) => {
          const c = conns[d.name]; if (!c || !c.holes || !/프레임$/.test(d.name) || /도 프레임/.test(d.name)) return;
          const hs = c.holes.filter((h) => Math.abs(h.dir[1]) > 0.9); if (hs.length < 3) return; // 판 두께 방향으로 뚫린 구멍(프레임)
          const R = matFromEuler(d.rot || [0, 0, 0]); const Rt = [0, 1, 2].map((i) => [0, 1, 2].map((j) => R[j][i]));
          const xs = hs.map((h) => h.pos[0]), zs = hs.map((h) => h.pos[2]);
          const lo = [Math.min(...xs) - 8, Math.min(...zs) - 8], hi = [Math.max(...xs) + 8, Math.max(...zs) + 8];
          const hit = pts.some((q) => { const l = mvec(Rt, [q[0] - d.pos[0], q[1] - d.pos[1], q[2] - d.pos[2]]); return l[0] >= lo[0] && l[0] <= hi[0] && l[2] >= lo[1] && l[2] <= hi[1] && Math.abs(l[1]) <= 30; });
          if (!hit) return;
          const n = mvec(R, [0, 1, 0]); const sg = n[1] >= -0.01 ? 1 : -1; // 위를 보는 면에 붙인다
          const info = hs.map((h) => {
            const w = mvec(R, h.pos);
            const hw = [d.pos[0] + w[0], d.pos[1] + w[1], d.pos[2] + w[2]];
            // 이 구멍에 다른 부품의 돌기가 꽂혀 있나(구멍 축 위·판 가운데 평면이 돌기 길이 안)
            const occ = pegs.some((pg) => {
              if (pg.owner === d) return false;
              const v = [pg.p[0] - hw[0], pg.p[1] - hw[1], pg.p[2] - hw[2]]; const al = v[0] * n[0] + v[1] * n[1] + v[2] * n[2];
              const lat = Math.hypot(v[0] - al * n[0], v[1] - al * n[1], v[2] - al * n[2]);
              return lat <= 3.6 && Math.abs(al) <= pg.len / 2 + 1.5;
            });
            // 이번 단계에 이 구멍으로 꽂힐 부품(초록 결합 위치 — 예: 교재 18 의 T축 2개)도 기준 부품으로 본다
            const tgt = !d.isNew && guides.some((g) => {
              const v = [g.to[0] - hw[0], g.to[1] - hw[1], g.to[2] - hw[2]]; const al = v[0] * n[0] + v[1] * n[1] + v[2] * n[2];
              return Math.hypot(v[0] - al * n[0], v[1] - al * n[1], v[2] - al * n[2]) <= 3.6 && Math.abs(al) <= 8;
            });
            return { col: h.pos[0], row: Math.round(h.pos[2]), hw, occ: occ || tgt }; // 줄 = 판 폭 방향 위치, 열 = 길이 방향 위치(좌표)
          });
          const rows = {}; info.forEach((o) => { (rows[o.row] = rows[o.row] || []).push(o); });
          // 제일 윗줄만 번호를 붙인다(사용자 지시): 눕힌 판은 화면에서 먼 쪽(z 가 가장 작은) 줄, 세운 판은 가장 높은 줄
          const rowKeys = Object.keys(rows); const mean = (arr, i) => arr.reduce((a1, o) => a1 + o.hw[i], 0) / arr.length;
          const topKey = rowKeys.sort((ka, kb) => (Math.abs(n[1]) > 0.5 ? mean(rows[ka], 2) - mean(rows[kb], 2) : mean(rows[kb], 1) - mean(rows[ka], 1)))[0];
          [rows[topKey]].forEach((arr) => {
            arr.sort((a1, b1) => a1.col - b1.col);
            let i = 0;
            while (i < arr.length) {
              if (arr[i].occ) { i++; continue; }
              let j = i; while (j < arr.length && !arr[j].occ) j++;     // arr[i..j-1] 이 빈 구멍 구간
              const leftLm = i > 0, rightLm = j < arr.length;            // 양옆이 부품인지(아니면 판 끝)
              for (let k = i; k < j; k++) {
                const num = (!leftLm && rightLm) ? (j - k) : (k - i + 1); // 오른쪽 부품만 있으면 그쪽에서부터, 그 외엔 왼쪽 부품(또는 판 왼쪽 끝) 다음부터
                items.push({ pos: [arr[k].hw[0] + n[0] * 2.65 * sg, arr[k].hw[1] + n[1] * 2.65 * sg, arr[k].hw[2] + n[2] * 2.65 * sg], text: String(num), n: [n[0] * sg, n[1] * sg, n[2] * sg] });
              }
              i = j;
            }
          });
        });
      }
      b.holeLabels(items);
    }
    // 앞 벽이 뒤쪽 끝에 있는 단계(flip)는 반대편에서 보여준다
    // view: 기본 각도에서 90도×view 만큼 돌려서 보기 / cam: {theta, phi}로 교재 그림과 같은 각도를 직접 지정
    const st = (step > 0 && step < last()) ? def.steps[step - 1] : null;
    const view = (st && st.view) || 0;
    const th = st && st.cam ? st.cam.theta : (def.camera ? def.camera.theta : 0) + view * Math.PI / 2;
    const ph = st && st.cam ? st.cam.phi : (def.camera ? def.camera.phi : 1);
    const camKey = th.toFixed(3) + '|' + ph.toFixed(3);
    if (b.turn && def.camera && camKey !== lastCamKey) { b.turn(th, ph); lastCamKey = camKey; } // 각도가 바뀌는 단계에서만 돌린다(직접 돌린 화면은 그대로)
    const n = total();
    $('asmLabel').textContent = step === 0 ? '시작 전' : (step === last() ? '완성!' : step + ' / ' + n + ' 단계');
    $('asmNote').textContent = step === 0 ? '빈 판에서 시작해요. ▶ 를 눌러 한 단계씩 만들어 봐요.'
      : (step === last() ? '완성! 부품이 모두 제자리에 끼워졌어요.' : (def.steps[step - 1].note || ''));
    $('asmSlider').value = String(step);
    $('asmStageNote').textContent = step === last() ? $('asmNote').textContent : $('asmLabel').textContent + ' · ' + $('asmNote').textContent;
    markStepButtons();
    $('asmFirst').disabled = $('asmPrev').disabled = step === 0;
    $('asmNext').disabled = $('asmLast').disabled = step === last();
    if (missing.length) $('asmNote').textContent += ' (부품을 못 찾았어요: ' + missing.join(', ') + ')';
  }

  function stop() {
    clearInterval(timer); clearTimeout(timer); timer = null; timerDir = 0;
    $('asmPlay').textContent = '▶ 재생';
    $('asmReverse').textContent = '◀ 역재생';
    const br = bridge(); if (br && br.guideDots) br.guideDots(true); // 멈추면 초록 점이 다시 보인다
  }
  function go(target) {
    step = Math.max(0, Math.min(last(), target));
    render();
  }
  // 재생: 화살표 표시 → 결합 → 다음 단계 화살표 표시 → 결합 … 을 쭉 이어서 보여준다(재생 중에는 초록 점을 숨기고 화살표만).
  // 역재생은 단계를 거꾸로 한 칸씩 넘긴다.
  const ARROW_MS = 1100, JOIN_MS = 700;
  // 재생 속도(0.5×~3×): 숫자가 클수록 빠르다. 재생 도중에 바꿔도 다음 단계부터 바로 적용된다.
  let speed = 1;
  try { const v = Number(localStorage.getItem('ivs-asm-speed')); if (v >= 0.5 && v <= 3) speed = v; } catch (e) { /* 저장 못 해도 기본 속도 */ }
  const arrowMs = () => ARROW_MS / speed, joinMs = () => JOIN_MS / speed;
  function play(dir) {
    const wasPlaying = timerDir === dir;
    stop();
    if (wasPlaying) return; // 같은 재생 버튼을 다시 누르면 멈춤
    const b = bridge();
    if (dir > 0 && step >= last()) step = 0;
    if (dir < 0 && step <= 0) step = last();
    if (dir > 0 && step === 0) step = 1; // 빈 판에서 바로 첫 단계 화살표부터
    render();
    timerDir = dir;
    if (b && b.guideDots) b.guideDots(false); // 재생 중에는 화살표만(초록 점 숨김)
    if (dir > 0) {
      $('asmPlay').textContent = '⏸ 멈춤';
      const tick = () => {
        if (timerDir !== 1) return;
        // 결합: 부품마다 순서 번호(joinOrder)가 있으면 작은 번호부터 하나씩(14단계: 15프레임이 올라가 결합 → 그다음 부시)
        const orders = b.pendingOrders ? b.pendingOrders() : [1];
        const jm = joinMs();
        const joinOne = (k) => {
          if (timerDir !== 1) return;
          if (k >= orders.length) { afterJoin(); return; }
          b.combineNew(Math.max(150, jm - 150), orders[k]);
          timer = setTimeout(() => joinOne(k + 1), jm);
        };
        const afterJoin = () => {
          if (timerDir !== 1) return;
          const next = step + 1;
          if (next > last()) { stop(); return; }
          go(next); // 다음 단계 화살표 표시
          if (next === last()) { stop(); return; }
          timer = setTimeout(tick, arrowMs());
        };
        joinOne(0);
      };
      timer = setTimeout(tick, arrowMs());
    } else {
      $('asmReverse').textContent = '⏸ 멈춤';
      const back = () => {
        if (timerDir !== -1) return;
        const next = step - 1;
        if (next < 0) { stop(); return; }
        go(next);
        if (next === 0) { stop(); return; }
        timer = setTimeout(back, PLAY_MS / speed);
      };
      timer = setTimeout(back, PLAY_MS / speed);
    }
  }

  async function open() {
    const b = bridge();
    if (!def || !b) return;
    b.status('3D 부품을 불러오는 중이에요...', null);
    // 등록된 3D 모델을 먼저 받아 두면 부품이 처음부터 제 모양으로 나온다(받는 동안 단순 모양이 잠깐 보이는 것을 막음)
    const names = [...new Set(def.steps.flatMap((s) => (s.parts || []).map((pt) => pt.n)))];
    const pf = window.__ivsPerf = window.__ivsPerf || {}; pf.asmOpenStart = Math.round(performance.now());
    try { await b.preload(names, catId); } catch (e) { /* 못 받아도 단순 모양으로 계속 보여준다 */ }
    pf.asmPreloaded = Math.round(performance.now());
    if (!def || viewing) return;
    snapshot = b.serialize();
    viewing = true;
    lastCamKey = def.camera.theta.toFixed(3) + '|' + def.camera.phi.toFixed(3);
    b.setViewing(true);
    b.camera(def.camera);
    $('asmBar').hidden = false;
    { const adm = !!(window.__ivsIsAdmin && window.__ivsIsAdmin()); // 관리자만
      ['asmMarkMove2', 'asmMarkShot'].forEach((id) => { if ($(id)) $(id).hidden = !adm; }); }
    $('asmStageBar').hidden = false;
    $('historyPanel').hidden = true;
    b.axes(true);
    $('asmSlider').max = String(last());
    buildStepButtons();
    go(last()); // 처음엔 완성된 모습부터 보여준다
    pf.asmOpened = Math.round(performance.now());
    b.status('조립 보기 중이에요. 닫으면 하던 작업으로 돌아가요.', 'success');
  }
  function close() {
    const b = bridge();
    stop();
    if (!viewing) return;
    viewing = false;
    $('asmBar').hidden = true;
    const mm = $('asmMarkMove2'); if (mm && mm.dataset.on === '1') { mm.dataset.on = '0'; mm.textContent = '📍 표시하기'; mm.style.background = mm.style.color = ''; if (b) b.markMove(false); } // 닫을 땐 사진 없이 끈다
    if ($('asmMarkMove2')) $('asmMarkMove2').hidden = $('asmMarkShot').hidden = true;
    $('asmStageBar').hidden = true;
    $('historyPanel').hidden = false;
    if (b) b.axes(false);
    if (b) { b.guides([]); b.restore(snapshot || []); b.setViewing(false); }
    snapshot = null;
  }

  function stopPlayClick(fn) { return () => { stop(); fn(); }; }
  document.addEventListener('DOMContentLoaded', () => {
    if (!$('asmClose')) return;
    $('asmClose').addEventListener('click', close);
    const mm2 = $('asmMarkMove2');
    const toggleMark = () => { const on = mm2.dataset.on !== '1'; mm2.dataset.on = on ? '1' : '0'; mm2.style.background = on ? '#f97316' : ''; mm2.style.color = on ? '#fff' : ''; mm2.textContent = on ? '📍 끝내기' : '📍 표시하기'; bridge().markMove(on); };
    // 📸 수정스샷: 화면+번호+이동 목록을 한 장의 그림으로 만들어 클립보드에 복사하고 PNG로 내려받는다(번호 = 옮긴 순서)
    // 안내는 화면 아래쪽 글줄이라 눈에 안 띄므로, 스케치북 한가운데 위에 잠깐 큼직하게도 띄운다
    const toast = (msg, bad) => {
      let t = $('asmShotToast');
      if (!t) { t = document.createElement('div'); t.id = 'asmShotToast'; t.style.cssText = 'position:fixed;left:50%;top:20%;transform:translateX(-50%);z-index:60;max-width:80vw;padding:10px 16px;border-radius:12px;color:#fff;font:700 14px sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.3);pointer-events:none;'; document.body.appendChild(t); }
      t.style.background = bad ? '#dc2626' : '#16a34a'; t.textContent = msg; t.hidden = false;
      clearTimeout(t._h); t._h = setTimeout(() => { t.hidden = true; }, 4500);
    };
    const shot = async () => {
      const b = bridge();
      const header = (def ? def.chapter : '') + ' 조립도 · ' + (step === last() ? '완성' : step + '단계') + ' · 표시하기';
      let blob = null;
      try { blob = await b.markCapture(header); } catch (e) { toast('사진 만들기 실패: ' + (e && e.message || e), true); return; }
      if (!blob) { toast('표시가 없어요. 먼저 "📍 표시하기"를 누르고 화면의 부품을 눌러 주황 표시를 만든 뒤 눌러 주세요.', true); return; }
      let copied = false;
      try { await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]); copied = true; } catch (e) { /* 복사 권한이 없으면 다운로드만 */ }
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = '수정스샷_' + (def ? def.chapter : '') + '_' + (step === last() ? '완성' : step + '단계') + '.png';
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      toast(copied ? '📸 사진을 복사하고 내려받았어요 — Ctrl+V로 붙여넣어 보내 주세요' : '📸 사진을 내려받았어요(복사는 안 됐어요) — 파일을 보내 주세요');
      b.status(copied ? '사진을 복사하고 내려받았어요. 붙여넣기(Ctrl+V)로 보내 주세요.' : '사진을 내려받았어요(복사는 안 됐어요). 파일을 보내 주세요.', 'success');
    };

    if (mm2) mm2.addEventListener('click', toggleMark);
    if ($('asmMarkShot')) $('asmMarkShot').addEventListener('click', shot);
    $('asmFirst').addEventListener('click', stopPlayClick(() => go(0)));
    $('asmPrev').addEventListener('click', stopPlayClick(() => go(step - 1)));
    $('asmNext').addEventListener('click', stopPlayClick(() => go(step + 1)));
    $('asmLast').addEventListener('click', stopPlayClick(() => go(last())));
    const sp = $('asmSpeed'), spl = $('asmSpeedLabel');
    if (sp) { sp.value = String(speed); spl.textContent = speed + '×'; sp.addEventListener('input', () => { speed = Number(sp.value) || 1; spl.textContent = speed + '×'; try { localStorage.setItem('ivs-asm-speed', String(speed)); } catch (e) { /* 저장 못 해도 계속 */ } }); }
    // 결합 소리 볼륨(0~100%): 저장해 두고, 손을 뗄 때 한 번 들려준다
    const vol = $('asmVolume'), vl = $('asmVolumeLabel');
    if (vol) {
      let v = 50;
      try { const s = localStorage.getItem('ivs-asm-volume'); if (s !== null && Number(s) >= 0 && Number(s) <= 100) v = Number(s); } catch (e) { /* 저장 못 해도 기본 볼륨 */ }
      const apply = () => { window.__ivsSnapVolume = v / 100; vol.value = String(v); vl.textContent = v + '%'; };
      apply();
      vol.addEventListener('input', () => { v = Number(vol.value); apply(); try { localStorage.setItem('ivs-asm-volume', String(v)); } catch (e) { /* 계속 */ } });
      vol.addEventListener('change', () => { if (window.__ivsPlaySnap) window.__ivsPlaySnap(); });
    }
    $('asmPlay').addEventListener('click', () => play(1));
    $('asmReverse').addEventListener('click', () => play(-1));
    $('asmSlider').addEventListener('input', (e) => { stop(); go(Number(e.target.value)); });
    $('asmCombine').addEventListener('click', () => {
      const r = bridge().combineSelected();
      if (r === 'none') bridge().status('먼저 끼울 부품을 눌러서 고르세요.', 'warn');
      else if (r === 'notTarget') bridge().status('이 부품은 이번 단계에서 끼우는 부품이 아니에요. 떠 있는 부품을 눌러 보세요.', 'warn');
    });
    $('asmReset').addEventListener('click', () => { stop(); go(step); });
    $('asmOrderList').addEventListener('click', async (e) => {
      const b = e.target.closest('button[data-step]');
      if (!b) return;
      stop();
      const n = Number(b.dataset.step);
      if (!viewing) await open();
      if (viewing) go(n);
    });
    $('asmStagePrev').addEventListener('click', stopPlayClick(() => go(step - 1)));
    { // 프레임 구멍 번호 보이기/숨기기 버튼(#)
      const row = document.querySelector('#asmStageBar .asm-stage-row');
      if (row && !$('asmCamCopy')) { // 📷: 지금 보는 각도를 "카메라 N단계: theta … phi …"로 복사 — 교재와 같은 각도로 돌린 뒤 눌러 알려 주면 그 단계 카메라로 저장한다(camSrc user)
        const cb = document.createElement('button');
        cb.type = 'button'; cb.className = 'ghost asm-nav'; cb.id = 'asmCamCopy'; cb.textContent = '📷'; cb.title = '지금 각도를 이 단계 카메라로 복사'; cb.setAttribute('aria-label', '지금 카메라 각도 복사');
        cb.addEventListener('click', () => {
          const b2 = bridge(); if (!b2 || !b2.camState) return;
          const c = b2.camState(); const txt = '카메라 ' + step + '단계: theta ' + c.theta.toFixed(3) + ' phi ' + c.phi.toFixed(3);
          try { if (navigator.clipboard) navigator.clipboard.writeText(txt).catch(() => {}); } catch (e) { /* 복사 못 해도 아래 안내로 보인다 */ }
          b2.status(txt + ' (복사됨 — 채팅에 붙여 주세요)', 'success');
        });
        row.appendChild(cb);
      }
      if (row && !$('asmHoleNums')) {
        const hb = document.createElement('button');
        hb.type = 'button'; hb.className = 'ghost asm-nav'; hb.id = 'asmHoleNums'; hb.textContent = '#'; hb.title = '프레임 구멍 번호(열-줄) 보이기/숨기기'; hb.setAttribute('aria-label', '프레임 구멍 번호 보이기 숨기기');
        const paint = () => { hb.style.opacity = showHoleNums ? '1' : '0.45'; hb.setAttribute('aria-pressed', showHoleNums ? 'true' : 'false'); };
        hb.addEventListener('click', () => { showHoleNums = !showHoleNums; try { localStorage.setItem('ivs-asm-holenums', showHoleNums ? '1' : '0'); } catch (e) { /* 저장 못 해도 이번에는 적용 */ } paint(); render(); });
        paint(); row.appendChild(hb);
      }
    }
    $('asmStageNext').addEventListener('click', stopPlayClick(() => go(step + 1)));
    $('asmStageSteps').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-step]');
      if (b) { stop(); go(Number(b.dataset.step)); }
    });
    $('asmSteps').addEventListener('click', async (e) => {
      const b = e.target.closest('button[data-step]');
      if (!b) return;
      stop();
      const n = Number(b.dataset.step);
      if (!viewing) await open();
      if (viewing) go(n);
    });
  });

  // 차시 카드에서 카테고리·권·차시를 바꿀 때마다 design.html이 알려준다 — 맞는 조립 데이터가 있을 때만 버튼을 보여준다.
  window.__ivsAssembly = {
    onLessonChange(cat, volume, chapterTitle) {
      const box = $('assemblyBox');
      if (!box) return;
      const title = String(chapterTitle || '').trim();
      const found = (window.IVS_ASSEMBLIES || []).find((a) => a.category === cat.name && Number(a.volume) === Number(volume) && a.chapter === title) || null;
      if (viewing && found !== def) close();
      def = found;
      catId = found ? cat.id : null;
      box.hidden = !found;
      buildOrderList();
      if (def) buildStepButtons(); // 번호 줄도 조립 보기를 열기 전부터 보인다
      $('asmRules').innerHTML = (window.IVS_ASSEMBLY_RULES || []).map((r) => '<li>' + r + '</li>').join('');
    },
    isViewing() { return viewing; },
  };
})();
