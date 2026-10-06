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
  let savedCams = {};    // 관리자가 📷 로 저장한 단계별 시점 { 단계: { theta, phi, radius, target } } (표 ivs_assembly_cams)
  let baseCam = null;    // 이 단계의 교재 시점(방향·높이각·보는 중심·거리) — 하단 카메라 표시줄용
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

  // 창고 카드: 이 단계에서 카메라에 안 보이게 치워 둔 부품을 게임 창고처럼 따로 보여 준다(사용자 지시 2026-10-04)
  // 오른쪽 패널: 위의 "창고"(메인)는 평소에 비어 있다. 지금 안 보이는 묶음(예: 새 조립품을 만드는 동안 본체)은 창고로 옮기지 않고 창고 N번 자리에 그대로 둔다(사용자 지시 2026-10-04).
  let storedSlotNow = 1;
  function renderStorage(stored, thumb, kinds, slot, slots, thumbBy) {
    storedSlotNow = slot === undefined ? 1 : slot;
    const box = $('storageList'); if (!box) return;
    const on = !!(def && def.guideMode === 'mates');
    box.hidden = !on;
    if (b_ready()) bridge().setStored && bridge().setStored(on ? { names: Object.keys(stored || {}), counts: stored || {}, thumb: thumb || null, slot: storedSlotNow, slots: slots || {}, thumbBy: thumbBy || {} } : null);
    if (!on) return;
    $('storageCount').textContent = '0';
    $('storageBody').innerHTML = '<div class="required-summary" style="opacity:.55">비어 있음</div>';
  }
  function b_ready() { try { return !!bridge(); } catch (e) { return false; } }

  // 창고 자리(사용자 지시 2026-10-04): 0번 = 메인(결합하는 곳), 1~5번 = 따로 만드는 자리. 부품이 지금 있는 자리 = 만든 단계의 자리, 합쳐지는 단계(side.until)가 지났으면 그 단계의 자리.
  function slotOfStep(n) { if (n > def.steps.length && def.finalSlot !== undefined) return def.finalSlot; const st = def.steps[n - 1]; return st && st.slot !== undefined && st.slot !== null ? st.slot : 1; }
  function effStepOf(pt, madeStep, upTo) { return pt.side && pt.side.until && upTo >= pt.side.until ? pt.side.until : madeStep; }
  // 맞물림 방식 안내(def.guideMode === 'mates'): 연결점은 부품에 붙어 있는 고정된 자리(부품 DB 의 돌기·구멍)이고, 이번 단계에 결합할 자리일 때만 보인다.
  // 제자리 자세로 돌기↔구멍이 맞물리는 쌍을 구하고, 그 쌍 중 지금 떨어져 있는(띄운 높이가 다른) 쌍만 안내한다. 마크·보정 값이 필요 없다.
  function mateGuides(list) {
    const b = bridge(), M = window.IVS_MATES;
    if (!M || !M.check) return [];
    const conn = {};
    list.forEach((d) => { if (d.type && !conn[d.name]) { const c = b.connectors && b.connectors(d.type); if (c) conn[d.name] = c; } });
    const keyed = list.map((d, i) => ({ key: '#' + i, n: d.name, p: d.final || d.pos, r: d.rot }));
    const res = M.check(keyed, conn);
    const off = (d) => (d.final ? [d.pos[0] - d.final[0], d.pos[1] - d.final[1], d.pos[2] - d.final[2]] : [0, 0, 0]);
    const out = [], seen = new Set();
    (res.mated || []).forEach((m) => {
      const i = Number(String(m.part).slice(1)), j = Number(String(m.into).slice(1));
      const a = list[i], c = list[j];
      if (!a || !c || !(a.isNew || c.isNew)) return;
      if (a.moveGroup && a.moveGroup === c.moveGroup) return; // moveGroup: 같은 단계에 한 덩어리로 같이 옮겨 붙는 부품끼리(머리·몸통 안쪽)는 안내하지 않는다 — 덩어리와 받는 판 사이만 안내(꼬마기사 14번)
      const skipM = (a.skipMates || []).concat(c.skipMates || []);
      if (skipM.length && (skipM.includes(a.name + '.' + m.peg) || skipM.includes(c.name + '.' + m.hole))) return; // skipMates: 교재가 안내 화살표를 그리지 않는 돌기(예: 3단블록 가운데 돌기)
      const oa = off(a), oc = off(c);
      if (Math.hypot(oa[0] - oc[0], oa[1] - oc[1], oa[2] - oc[2]) < 2) return; // 이미 붙어 있는(같이 움직이는) 쌍은 안내하지 않는다
      const key = i + ':' + m.peg + '>' + j + ':' + m.hole;
      if (seen.has(key)) return; seen.add(key);
      const la = Math.hypot(oa[0], oa[1], oa[2]), lc = Math.hypot(oc[0], oc[1], oc[2]);
      // 움직이는 쪽 = 나중에 결합하는 부품(순서가 큰 쪽), 같으면 더 멀리 띄운 쪽, 그것도 같으면 이번 단계에 새로 놓인 쪽
      const mover = (a.order || 1) !== (c.order || 1) ? ((a.order || 1) > (c.order || 1) ? i : j) : (Math.abs(la - lc) > 0.5 ? (la > lc ? i : j) : (a.isNew ? i : j));
      out.push({ mate: true, pegIdx: i, pegId: m.peg, holeIdx: j, holeId: m.hole, moverIdx: mover, idx: mover });
    });
    // 교재처럼 돌기·구멍 맞물림이 아닌 안내 화살표: 부품 데이터의 arrowFrom {name, hole, myHole} = 그 이름 부품의 hole 에서 출발해 이 부품의 myHole 로 도착(예: 1열브라켓 팔 구멍 → 부시)
    list.forEach((d, i) => {
      if (!d.arrowFrom || !d.isNew) return;
      const j = list.findIndex((x, k) => k !== i && x.name === d.arrowFrom.name && (d.arrowFrom.step === undefined || x.step === d.arrowFrom.step)); // step: 같은 이름 부품이 여럿일 때 그 단계에서 만든 것
      if (j < 0) return;
      out.push({ mate: true, pegKind: 'hole', pegIdx: j, pegId: d.arrowFrom.hole, holeIdx: i, holeId: d.arrowFrom.myHole, moverIdx: j, idx: i });
    });
    return out;
  }

  // 지금 화면 자세에서 맞물려 이어진 부품 덩어리(그룹) — [{ name, idx:[목록 번호…] }]. 떠 있는 새 부품은 맞물리지 않아 자동으로 빠지고, 옆자리 조립품은 따로 덩어리가 된다.
  function mateComponents(list) {
    const b = bridge(), M = window.IVS_MATES;
    if (!M || !M.check) return [];
    const conn = {};
    list.forEach((d) => { if (d.type && !conn[d.name]) { const c = b.connectors && b.connectors(d.type); if (c) conn[d.name] = c; } });
    const res = M.check(list.map((d, i) => ({ key: '#' + i, n: d.name, p: d.pos, r: d.rot })), conn);
    const par = list.map((_, i) => i);
    const find = (x) => { while (par[x] !== x) { par[x] = par[par[x]]; x = par[x]; } return x; };
    (res.mated || []).forEach((m) => { const i = Number(String(m.part).slice(1)), j = Number(String(m.into).slice(1)); if (!isNaN(i) && !isNaN(j)) par[find(i)] = find(j); });
    // 옆자리에서 따로 만드는 세트(같은 side.until)는 떠 있어서 맞물려 보이지 않아도 제자리에서 맞물리는 부품끼리 한 묶음이다 → 클릭하면 세트 전체가 잡힌다(사용자 지시 2026-10-04)
    { const resF = M.check(list.map((d, i) => ({ key: '#' + i, n: d.name, p: d.fin || d.pos, r: d.finRot || d.rot })), conn);
      (resF.mated || []).forEach((m) => { const i = Number(String(m.part).slice(1)), j = Number(String(m.into).slice(1)); if (!isNaN(i) && !isNaN(j) && list[i].sideUntil && list[i].sideUntil === list[j].sideUntil) par[find(i)] = find(j); }); }
    const groups = {};
    list.forEach((_, i) => { const r = find(i); (groups[r] = groups[r] || []).push(i); });
    // 이름: 1단계 부품이 들어 있으면 본체, 아니면 그 묶음이 처음 만들어진 단계 번호로 N번 조립품
    return Object.values(groups).filter((g) => g.length > 1).map((idx) => {
      const first = Math.min(...idx.map((i) => list[i].step || 1));
      const eff = Math.max(...idx.map((i) => list[i].eff || list[i].step || 1));
      return { name: first === 1 ? '본체' : stepTag(first) + '번 조립품', idx, origin: slotOfStep(first), slot: (viewSlot !== null && viewSlot !== slotOfStep(step)) ? viewSlot : slotOfStep(step) }; // 지금 화면에 보이는 묶음은 모두 이 단계가 작업하는 창고 자리에 있다(결합하는 단계는 1·2번에 있던 것을 0번으로 끌어와 결합한다 — 사용자 지시 2026-10-04)
    });
  }

  // target 단계까지의 부품 목록과, 이번 단계의 초록 안내(화살표·구멍 원)를 만든다.
  function buildList(target) {
    const b = bridge();
    const list = [];
    const guides = [];
    const missing = [];
    let storedThumb = null, storedEff = 0; const storedEffBy = {}, storedThumbBy = {};
    const storedTypes = {}; // 창고에 들어간 부품도 이미 쓴 부품이다 → 사용 부품 숫자·목록에 넣는다(종류 → 개수)
    const stored = {};
    const deferredShift = []; // 화살표 시작점을 먼저 결합하는 부품(리벳)의 떠 있는 자리로 옮기는 일 — 목록이 다 만들어진 뒤에 한다 // 이 단계에서 화면에서 치워 창고에 넣어 둔 부품(이름 → 개수)
    const n = total();
    const upTo = Math.min(target, n);
    const flipOn = flipActive(target);
    const viewS = (viewSlot !== null && viewSlot !== slotOfStep(upTo)) ? viewSlot : null; // 다른 창고 화면을 보는 중이면 그 창고에 있는 묶음만 그린다
    let viewEff = 0; // 보는 창고의 묶음이 마지막으로 만들어진 단계(예: 창고 0 = 14번) — 그 단계의 마지막 시점으로 보여 준다
    const slotByName = {};
    if (viewS !== null) def.steps.slice(0, upTo).forEach((s2, si2) => (s2.parts || []).forEach((p2) => { if (p2.hideAt && p2.hideAt.includes(upTo)) { const k2 = (p2.store && typeof p2.store === 'object' ? p2.store[upTo] : p2.store) || '보관 중'; slotByName[k2] = Math.max(slotByName[k2] || 0, effStepOf(p2, si2 + 1, upTo)); } }));
    // 부품 번호("리벳 3/14"): design-faces.js 의 규칙 — 조립 MCP(get_part_faces)와 같은 번호
    const { numOf } = window.IVS_FACES.numberParts(def.steps);
    def.steps.slice(0, upTo).forEach((s, si) => {
      (s.parts || []).forEach((pt0) => {
        const pt = flipOn && !pt0.noflip ? flipPt(pt0, target) : pt0; // 뒤집기 전 방향으로 보여 주는 단계(noflip: 로봇과 따로 만드는 손잡이는 그대로)
        const type = b.resolve(pt.n, catId);
        if (!type) { if (!missing.includes(pt.n)) missing.push(pt.n); return; }
        if (pt.finalOnly && target <= n) return; // finalOnly: 완성 화면에서만 보이는 부품(예: 롤링봇 장전한 작은바퀴)
        if (viewS !== null) { // 창고 화면 보기: 보관 중이던 묶음 중 이 창고에 있는 것만 보이고, 지금 작업하던 부품은 숨긴다
          if (!(pt.hideAt && pt.hideAt.includes(upTo))) return;
          const k3 = (pt.store && typeof pt.store === 'object' ? pt.store[upTo] : pt.store) || '보관 중';
          if (slotOfStep(slotByName[k3] || 0) !== viewS) return;
          viewEff = Math.max(viewEff, effStepOf(pt, si + 1, upTo));
        } else if (pt.hideAt && pt.hideAt.includes(upTo)) { const pick = (v) => (v && typeof v === 'object' ? v[upTo] : v); const k = pick(pt.store) || '보관 중'; stored[k] = (stored[k] || 0) + 1; storedTypes[type] = (storedTypes[type] || 0) + 1; storedEff = Math.max(storedEff, effStepOf(pt, si + 1, upTo)); storedEffBy[k] = Math.max(storedEffBy[k] || 0, effStepOf(pt, si + 1, upTo)); if (pick(pt.storeThumb)) { storedThumb = pick(pt.storeThumb); storedThumbBy[k] = storedThumb; } return; } // store·storeThumb 는 글자 하나 또는 {단계번호: 값} // hideAt: 이 단계에서는 따로 보관해 두고 안 보여준다(예: 비행기 6번은 5번까지 만든 본체와 따로 만드는 조립품)
        const useSide = pt.side && upTo < pt.side.until;
        const moved = pt.move && upTo >= pt.move.at; // move: 옆자리에서 다 만든 뒤 다른 자리로 한 번 더 옮겨 붙는 단계(예: 풍차 상자를 몸체에 끼우기)
        // move: { at, by } 평행 이동 또는 { at, p, r } 새 자세로 옮기기(회전 포함 — 예: 3륜바이크 7단계 샌드위치를 뒤집어 올림)
        let base = useSide ? pt.side.p : (moved ? (pt.move.p || add(pt.p, pt.move.by || [0, 0, 0], 1)) : pt.p);
        // lift: 다 만든 묶음(총몸·기둥)이 받침 위에 띄워져 있다가(from~at 직전 단계) at 단계에 위에서 내려와 결합한다(교재 29) — { from, at, by, dir, hover, marks }
        if (pt.lift && !useSide && upTo >= (pt.lift.from || 0) && upTo < pt.lift.at) base = add(base, pt.lift.by || [0, 0, 0], 1);
        if (pt.asideAt && pt.asideAt[upTo]) base = add(base, pt.asideAt[upTo], 1); // asideAt: 이 단계에서는 카메라 밖 옆자리에 치워 둔다(드라마 촬영처럼 화면엔 안 나오지만 옆에 있다) — 다음 단계에서 제자리
        let rot = useSide ? pt.side.r : (moved && pt.move.r ? pt.move.r : pt.r);
        if (pt.poseAt && pt.poseAt[target]) { base = pt.poseAt[target].p; rot = pt.poseAt[target].r; } // poseAt: 이 단계에서만 다른 자세(회전 포함)로 보여 준다(예: 롤링봇 27·28번은 팔 조립품을 눕혀서 조립 — 앞뒤 단계는 세운 자세)
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
        if (isNew && pt.seated && !lowering && !(moving && pt.moveGuide)) { // moveGuide: seated 부품이 move 로 옮겨 붙는 단계에서는 링만 칠하지 않고 화살표도 그린다(꼬마기사 14번 모터)
          // seated: 교재가 이미 꽂아 둔 모양으로 그리는 부품(리벳 등) — 떠서 내려오지 않고 제자리에 두고, 꽂힌 구멍에 초록 원만 칠한다(교재 23·25·27)
          (pt.marks || []).forEach((m) => guides.push({ from: m, to: m, dir: dirH || [0, 1, 0], idx: list.length, ringOnly: true }));
        } else if (isNew && dirH && pt.noGuide) {
          pos = add(base, dirH, pt.hover || HOVER); // noGuide: 받는 판과 함께 떠서 오는 부품(판에 이미 박힌 리벳) — 따로 안내 화살표·점이 없다
        } else if (isNew && dirH) {
          // 띄우는 거리·돌기가 들어가는 깊이·판 두께는 부품마다 정할 수 있다(T축처럼 길게 꽂히는 것, 두꺼운 부시)
          const hv = moving ? (mvSrc.hover || HOVER) : settling ? (pt.settleHover || HOVER) : (pt.hover || (pt.recv ? HOVER_RECV : HOVER)); // 합쳐지는 묶음은 모두 같은 거리로 띄워야 모양이 흐트러지지 않는다
          const depth = pt.pegDepth || PEG_DEPTH;
          pos = add(base, dirH, hv); // 끼우기 직전: 제자리에서 끼우는 방향으로 띄운다
          const targets = moving ? (mvSrc.marks || []) : settling ? (pt.settleMarks || []) : (pt.marks && pt.marks.length ? pt.marks : [base]);
          // 화살표는 띄워 놓은 부품의 돌기 끝(구멍에 들어갈 깊이만큼 아래)에서 시작해 구멍 위 원으로 들어간다
          const myOrder = settling ? (pt.settleOrder || 1) : (pt.joinOrder || 1); // settleOrder: 합쳐지는 묶음이 같은 단계의 다른 부품(리벳)보다 나중에 내려올 때 2
          // 받는 부품(호스트)이 이 점 근처인지: 끼우는 방향 축 위로 14 이내이고, 축에서 옆으로 4 이내(옆 구멍의 돌기를 잘못 잡지 않게)
          const near = (f, m) => { const d = [f[0] - m[0], f[1] - m[1], f[2] - m[2]]; const u = dirH || [0, 1, 0]; const ul = Math.hypot(u[0], u[1], u[2]) || 1; const al = (d[0] * u[0] + d[1] * u[1] + d[2] * u[2]) / ul; return Math.abs(al) < 14 && Math.hypot(d[0] - al * u[0] / ul, d[1] - al * u[1] / ul, d[2] - al * u[2] / ul) < 4; };
          const hostShift = pt.guideShift ? () => pt.guideShift : (m) => { const h = list.find((q) => q.isNew && q.final && (q.order || 1) < myOrder && near(q.final, m)); return h ? [h.pos[0] - h.final[0], h.pos[1] - h.final[1], h.pos[2] - h.final[2]] : null; };
          if (pt.recv && !pt.pegTarget) { // pegTarget: 구멍 받는 부품이 움직여도 교재처럼 화살표가 고정된 돌기 끝을 향하게 그린다(marks = 고정된 돌기 끝)
            // 구멍을 받는 부품(프레임 등)이 움직일 때: 원은 떠 있는 부품의 구멍에, 화살표는 고정된 돌기 끝에서 그 구멍 쪽으로
            // faceMarks: 돌기 끝이 판 바깥 면과 같은 높이가 아닐 때, 제자리에 끼운 뒤 판 바깥 면의 구멍 자리
            const faces = !settling && pt.faceMarks ? pt.faceMarks : targets;
            // 같은 단계에서 먼저 결합하는 부품(예: 리벳, joinOrder 가 더 작음)의 돌기에 끼우는 경우, 그 부품은 아직 떠 있으니 화살표는 떠 있는 돌기 끝에서 시작한다(사용자 지시 2026-10-04: 리벳이 중간에 보이고 위쪽 화살표는 리벳에서 끝난다)
            targets.forEach((m, i) => { const g = { from: m, to: add(faces[i] || m, dirH, hv), dir: dirH, idx: list.length, both: pt.thick || 5 }; guides.push(g); deferredShift.push(() => { const sh = hostShift(m); if (sh) g.from = add(m, sh, 1); }); }); // 호스트(리벳)가 이 부품보다 뒤 단계 목록에 있어도 찾도록 목록을 다 만든 뒤 옮긴다
          } else {
            targets.forEach((m) => { const sh = hostShift(m) || [0, 0, 0]; guides.push({ from: add(m, dirH, hv - depth), to: add(m, sh, 1), dir: dirH, idx: list.length, stop: hostShift(m) ? 2.5 : 0 }); }); // 받는 부품이 먼저 떠 있으면(예: 판 위 리벳) 점도 떠 있는 구멍에
          }
        }
        // holeMarks: 프레임 구멍에 고정된 결합 위치 원(교재처럼 판 구멍에 표시, 부품이 움직여도 그 자리)
        if (isNew && !moving && pt.holeMarks) pt.holeMarks.forEach((m) => guides.push({ from: m, to: m, dir: dirH || [0, 1, 0], idx: list.length, ringOnly: true }));
        list.push({ step: si + 1, eff: effStepOf(pt, si + 1, upTo), noFreeze: !!(pt.noFreeze && pt.noFreeze.includes(upTo)), name: pt.n, label: pt.n + ' ' + numOf.get(pt0) + '번', type, mount: 'floor', pos: pos.slice(), quat: b.quat(rot), rot: rot.slice(), isNew, final: (isNew && dirH) || ex ? base.slice() : null, order: settling ? (pt.settleOrder || 1) : (pt.joinOrder || (ex && ex.order) || 1), moveGroup: (moving && pt.moveGroup) || null, arrowFrom: pt.arrowFrom || null, skipMates: pt.skipMates || null, sideUntil: pt.side ? pt.side.until : null, fin: moved ? (pt.move.p || add(pt.p, pt.move.by || [0, 0, 0], 1)) : pt.p, finRot: (moved && pt.move.r) ? pt.move.r : pt.r }); // 합쳐지는 묶음(settle)은 모두 한꺼번에 내려온다 // ex: 14단계처럼 "결합 전"으로 띄운 부품도 제자리(결합 후)가 있다
      });
    });
    deferredShift.forEach((fn) => fn());
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
    const guidesOut = def.guideMode === 'mates' ? mateGuides(list) : guides;
    return { list, guides: guidesOut, missing, stored, storedThumb, storedSlot: storedEff ? slotOfStep(storedEff) : 1, viewEff, storedSlots: Object.fromEntries(Object.keys(storedEffBy).map((k) => [k, slotOfStep(storedEffBy[k])])), storedThumbBy, storedTypes, targets: list.map((d) => d.final || null), orders: list.map((d) => d.order || 1) };
  }

  // 단계 이름표: label 이 있는 단계(예: "창고")는 이름으로, 나머지는 label 없는 단계만 세어 번호를 붙인다
  function stepTag(i) { const st = def.steps[i - 1]; if (st && st.label) return st.label; let c = 0; for (let k = 0; k < i; k++) if (!(def.steps[k] && def.steps[k].label)) c++; return String(c); }
  // 1, 2, 3 … 단계 번호 버튼(+ 마지막 "완성") — 눌러서 그 단계로 바로 가고, 지금 단계는 진하게 보인다.
  // 관리자 전용 단계 상태(수정중/완료): DB(ivs_assembly_status)에 단계별로 저장하고, 단계 번호 버튼에 ✓(완료)·🛠(수정중)로 표시한다.
  let stepStatus = {};
  let posesDB = {}; // 단계별로 기록한 부품 모습 { 단계: { 부품 이름 번호: {p, q, r} } } (ivs_assembly_poses)
  let lastLabels = []; // 지금 화면 부품 순서의 이름(모습 기록에 쓴다)
  let thumbsDB = {}; // 창고 카드 썸네일 { '단계:창고': 사진 } (ivs_assembly_thumbs)
  // 지금 단계의 창고 카드마다 "그 창고에서 가장 최근에 저장한 사진"을 보낸다(단계 데이터 slotThumb 은 사진이 없을 때의 대비)
  function pushSlotThumbs() {
    const b = bridge(); if (!b || !b.setSlotThumbs || !def) return;
    const m = Object.assign({}, (step >= 1 && step < last() && def.steps[step - 1] && def.steps[step - 1].slotThumb) || {});
    for (let n = 0; n <= 5; n++) {
      for (let s2 = Math.min(step, last() - 1); s2 >= 1; s2--) {
        const sl = def.steps[s2 - 1] ? def.steps[s2 - 1].slot : undefined;
        if (sl === n && thumbsDB[s2 + ':' + n]) { m[n] = thumbsDB[s2 + ':' + n]; break; }
      }
    }
    b.setSlotThumbs(m);
  }
  const isAdm = () => !!(window.__ivsIsAdmin && window.__ivsIsAdmin());
  // 안내 모달(확인 버튼 하나): 모습·교재 샷을 저장했을 때 확실히 알려 준다(사용자 지시 2026-10-05)
  function notice(msg, onClose) {
    const ov = document.createElement('div');
    ov.style.cssText = 'position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;';
    const bx = document.createElement('div');
    bx.style.cssText = 'background:#fff;border-radius:16px;padding:22px 28px 18px;min-width:240px;max-width:80vw;text-align:center;box-shadow:0 12px 40px rgba(0,0,0,.3);font:700 15px sans-serif;color:#111827;';
    const p = document.createElement('div'); p.textContent = msg; p.style.cssText = 'margin-bottom:16px;line-height:1.5;';
    const ok = document.createElement('button'); ok.type = 'button'; ok.textContent = '확인';
    ok.style.cssText = 'padding:8px 32px;border-radius:999px;border:0;background:#2563eb;color:#fff;font:700 14px sans-serif;cursor:pointer;';
    const close = () => { ov.remove(); document.removeEventListener('keydown', onKey, true); if (onClose) onClose(); };
    const onKey = (e) => { if (e.key === 'Enter' || e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); } };
    ok.addEventListener('click', close); document.addEventListener('keydown', onKey, true);
    bx.appendChild(p); bx.appendChild(ok); ov.appendChild(bx); document.body.appendChild(ov); ok.focus();
  }
  window.__ivsNotice = notice;   // design-notes.js(그리기·메모)도 같은 안내 모달을 쓴다
  const STATUS_LABEL = { done: '✅ 완료', edit: '🛠 수정중' };
  function paintStatus() {
    const adm = isAdm();
    [$('asmSteps'), $('asmStageSteps')].forEach((box) => { if (!box) return;
      box.querySelectorAll('button[data-step]').forEach((b) => { const i = Number(b.dataset.step), st = adm ? stepStatus[i] : null, tag = i === last() ? '완성' : stepTag(i);
        b.textContent = tag + (st === 'done' ? ' ✓' : st === 'edit' ? ' 🛠' : ''); }); });
    const sb = $('asmStatusBtn'); if (!sb) return;
    sb.hidden = !adm || step < 1;   // 완성에도 체크·모습 기록 버튼을 보인다(사용자 지시 2026-10-05)
    { const tb = $('asmThumbBtn'); if (tb) tb.hidden = sb.hidden; }
    { const rb = $('asmReloadBtn'); if (rb) rb.hidden = !adm || step < 0; }
    { const fb = $('asmFreezeBtn'); if (fb) fb.hidden = sb.hidden; }
    const st = stepStatus[step]; sb.textContent = STATUS_LABEL[st] || '⬜ 상태 없음';
    sb.style.background = st === 'done' ? '#16a34a' : st === 'edit' ? '#f59e0b' : ''; sb.style.color = st ? '#fff' : '';
    sb.title = '이 단계의 상태(관리자만 보여요): 누를 때마다 상태 없음 → 수정중 → 완료 → 상태 없음. DB에 저장돼요';
  }
  function ensureStatusBtn() {
    if ($('asmStatusBtn') || !$('asmMarkMove2')) return;
    const sb = document.createElement('button'); sb.type = 'button'; sb.id = 'asmStatusBtn'; sb.hidden = true;
    sb.style.cssText = 'padding:6px 12px;font-size:12px;font-weight:600;border-radius:999px;background:var(--panel);border:1px solid var(--panel-border);color:var(--ink);';
    $('asmMarkMove2').parentNode.insertBefore(sb, $('asmMarkMove2'));
    { const fb = document.createElement('button'); fb.type = 'button'; fb.id = 'asmFreezeBtn'; fb.hidden = true; fb.textContent = '❄ 모습 기록';
      fb.style.cssText = sb.style.cssText; fb.title = '지금 부품들의 위치·회전을 이 단계의 모습으로 기록해요(관리자만). 기록한 단계는 열 때 이 모습으로 보여요';
      sb.parentNode.insertBefore(fb, sb);
      fb.addEventListener('click', async () => {
        const b2 = bridge(); if (!b2 || !b2.poseStore || !def || step < 1) return;
        const ser = b2.serialize();
        if (ser.length !== lastLabels.length) { b2.status('부품 수가 달라서 기록하지 못했어요. 단계를 다시 열고 눌러 주세요.', 'error'); return; }
        const r1 = (v) => Math.round(v * 100) / 100, poses = {};
        ser.forEach((x, i) => { poses[lastLabels[i]] = { p: x.pos.map(r1), q: (x.quat || []).map((v) => Math.round(v * 100000) / 100000), r: (x.rot || []).map(r1) }; });
        const mine = step;
        try { await b2.poseStore.save(def.id, mine, poses); posesDB[mine] = poses; paintStatus(); b2.status(mine + '단계 부품 모습을 기록했어요. 이제 이 단계를 열면 이 모습으로 보여요.', 'success'); notice('모습이 저장되었습니다.'); }
        catch (e) { b2.status('모습 기록 실패: ' + e.message + ' (supabase/assembly_poses.sql 을 실행했는지 확인)', 'error'); }
      });
    }
    { const rb = document.createElement('button'); rb.type = 'button'; rb.id = 'asmReloadBtn'; rb.hidden = true; rb.textContent = '↻ 새로고침';
      rb.style.cssText = sb.style.cssText; rb.title = '지금 보는 단계 하나만 데이터를 다시 불러와요(관리자만). Shift+클릭 = 페이지 전체 새로고침';
      sb.parentNode.insertBefore(rb, sb);
      // 지금 보는 단계 하나만 다시 불러온다(사용자 지시 2026-10-05: 15번을 고치면 15번만) — 페이지·다른 단계·카메라는 그대로. Shift 를 누르고 누르면 예전처럼 페이지 전체를 새로 불러온다.
      rb.addEventListener('click', async (ev) => {
        const fullReload = () => {
          try { sessionStorage.setItem('ivs-asm-restore', JSON.stringify({ sel: [...document.querySelectorAll('select')].slice(0, 3).map((x) => x.value), step })); } catch (e) { /* 저장 못 해도 새로고침은 한다 */ }
          notice('페이지를 새로 불러옵니다. 보던 차시와 단계는 다시 열려요.', () => location.reload());
        };
        if (ev.shiftKey || !def || step < 1 || step > def.steps.length) { fullReload(); return; }
        const mine = step;
        try {
          const res = await fetch('design-assemblies.js?ts=' + Date.now(), { cache: 'no-store' });
          if (!res.ok) throw new Error('데이터 파일을 못 읽었어요(' + res.status + ')');
          const fake = {}; new Function('window', await res.text())(fake); // 파일은 window.IVS_ASSEMBLIES 에 넣기만 한다 — 가짜 window 에 받아 이 단계만 꺼낸다
          const nd = (fake.IVS_ASSEMBLIES || []).find((x) => x.id === def.id), ns = nd && nd.steps && nd.steps[mine - 1];
          if (!ns) throw new Error('새 데이터에서 ' + mine + '단계를 못 찾았어요');
          const old = def.steps[mine - 1]; Object.keys(old).forEach((k) => delete old[k]); Object.assign(old, ns);
          go(mine);
          notice(mine + '단계만 다시 불러왔어요. 다른 단계와 화면 위치는 그대로예요. (Shift 를 누르고 누르면 페이지 전체를 새로 불러와요)');
        } catch (e) { notice(mine + '단계를 다시 불러오지 못했어요: ' + e.message); }
      });
    }
    { const tb = document.createElement('button'); tb.type = 'button'; tb.id = 'asmThumbBtn'; tb.hidden = true; tb.textContent = '📷 썸네일 저장';
      tb.style.cssText = sb.style.cssText; tb.title = '지금 3D 화면을 이 단계 작업 창고의 썸네일로 저장해요(관리자만, 누를 때만 찍어요)';
      sb.parentNode.insertBefore(tb, sb);
      tb.addEventListener('click', async () => {
        const b2 = bridge(); if (!b2 || !b2.thumbStore || !b2.snapshot || !def || curSlot < 0) return;
        const img = b2.snapshot(300); if (!img) { b2.status('사진을 만들지 못했어요.', 'error'); return; }
        const mine = step, mySlot = curSlot;
        try { await b2.thumbStore.save(def.id, mine, mySlot, img); thumbsDB[mine + ':' + mySlot] = img; pushSlotThumbs(); b2.status(mine + '단계 · 창고 ' + mySlot + ' 썸네일을 저장했어요.', 'success'); notice('썸네일이 저장되었습니다. (' + mine + '단계 · 창고 ' + mySlot + ')'); }
        catch (e) { b2.status('썸네일 저장 실패: ' + e.message + ' (supabase/assembly_thumbs.sql 을 실행했는지 확인)', 'error'); notice('썸네일 저장에 실패했습니다: ' + e.message); }
      });
    }
    { // 위 줄 버튼 순서(사용자 지시 2026-10-05): 체크(상태) → 카메라 → 모습 기록 → 나머지
      const par = sb.parentNode, first = $('asmFreezeBtn');
      if (par && first) { par.insertBefore(sb, first); const cam = $('asmCamCopy'); if (cam) par.insertBefore(cam, first); }
    }
    sb.addEventListener('click', async () => {
      const b2 = bridge(); if (!b2 || !b2.statusStore || !def) return;
      const cur = stepStatus[step], next = !cur ? 'edit' : cur === 'edit' ? 'done' : null, mine = step;
      try { await b2.statusStore.set(def.id, mine, next); if (next) stepStatus[mine] = next; else delete stepStatus[mine]; paintStatus(); notice(mine + '단계를 "' + (next === 'done' ? '완료' : next === 'edit' ? '수정중' : '상태 없음') + '"(으)로 저장했습니다.' + (next === 'done' ? ' 이제 이 단계는 확인이 끝난 단계로 보호돼요.' : '')); }
      catch (e) { b2.status('상태 저장 실패: ' + e.message + ' (supabase/assembly_status.sql 을 실행했는지 확인)', 'error'); notice('상태 저장에 실패했습니다: ' + e.message); }
    });
  }
  function buildStepButtons() {
    [$('asmSteps'), $('asmStageSteps')].forEach((box) => {
      box.innerHTML = '';
      for (let i = 1; i <= last(); i++) {
        const b = document.createElement('button');
        b.type = 'button';
        b.dataset.step = String(i);
        const tag = i === last() ? '완성' : stepTag(i), wide = tag.length > 1;
        b.textContent = tag;
        b.title = i === last() ? '완성된 모습' : tag + (wide ? ': ' : '단계: ') + (def.steps[i - 1].note || '');
        b.style.cssText = wide ? 'padding:5px 10px; font-size:13px;' : 'min-width:32px; padding:5px 0; font-size:13px;';
        box.appendChild(b);
      }
    });
    paintStatus();
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
      b.style.cssText = 'width:100%; text-align:left; padding:3px 8px; border-radius:8px; font-size:12.5px; font-weight:400; white-space:pre-line;';
      b.textContent = stepTag(i + 1) + '. ' + (s.note || '');
      li.appendChild(b);
      ol.appendChild(li);
    });
  }
  // 교재 참고 그림(관리자 전용, 표 ivs_assembly_refs): "조립 순서" 제목 오른쪽 "🖼 완성 사진"(교재 맨 앞 완성품 사진 = 앞·뒤·정면 기준)과, 그림이 있는 단계마다 목록 오른쪽 "🖼".
  // 단계 그림은 교재 쪽에서 잘라 낸 것(필요하면 돌리거나 확대해 칸을 센 그림도)이다. 그림 자체는 단계를 눌러 열 때만 받는다.
  let refsMeta = {}, refsFor = null;
  function refModal(title, rows) {
    const old = $('asmRefModal'); if (old) old.remove();
    const ov = document.createElement('div'); ov.id = 'asmRefModal';
    ov.style.cssText = 'position:fixed;inset:0;z-index:100000;background:rgba(15,23,42,.62);display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:16px;';
    const box = document.createElement('div');
    box.style.cssText = 'background:var(--panel,#fff);color:var(--ink,#111);border-radius:14px;max-width:min(1100px,100%);width:100%;padding:14px 16px 18px;box-shadow:0 12px 40px rgba(0,0,0,.35);';
    const hd = document.createElement('div'); hd.style.cssText = 'display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 0 10px;';
    const h = document.createElement('b'); h.textContent = title; h.style.fontSize = '15px';
    const x = document.createElement('button'); x.type = 'button'; x.textContent = '✕ 닫기'; x.className = 'ghost'; x.style.cssText = 'padding:4px 10px;font-size:12.5px;';
    hd.appendChild(h); hd.appendChild(x); box.appendChild(hd);
    if (!rows.length) { const p = document.createElement('p'); p.textContent = '등록된 그림이 없어요.'; box.appendChild(p); }
    rows.forEach((r) => {
      const fig = document.createElement('figure'); fig.style.cssText = 'margin:0 0 14px;';
      if (r.label) { const lb = document.createElement('div'); lb.textContent = r.label; lb.style.cssText = 'font-weight:700;font-size:13px;margin:0 0 4px;'; fig.appendChild(lb); }
      const im = document.createElement('img'); im.src = r.img; im.alt = r.label || '교재 그림'; im.style.cssText = 'display:block;max-width:100%;height:auto;border:1px solid var(--panel-border,#d6dce8);border-radius:8px;background:#fff;'; fig.appendChild(im);
      if (r.note) { const cp = document.createElement('figcaption'); cp.textContent = r.note; cp.style.cssText = 'font-size:12.5px;line-height:1.4;margin:6px 0 0;color:var(--ink-soft,#445);white-space:pre-line;'; fig.appendChild(cp); }
      box.appendChild(fig);
    });
    ov.appendChild(box); document.body.appendChild(ov);
    const closeIt = () => { ov.remove(); document.removeEventListener('keydown', onKey); };
    const onKey = (e) => { if (e.key === 'Escape') closeIt(); };
    document.addEventListener('keydown', onKey);
    x.addEventListener('click', closeIt); ov.addEventListener('click', (e) => { if (e.target === ov) closeIt(); });
  }
  async function showRefs(steps, title) {
    const b = bridge(); if (!b || !b.refStore || !def) return;
    refModal(title, [{ img: 'data:image/gif;base64,R0lGODlhAQABAAAAACw=', label: '불러오는 중…' }]);
    try {
      const rows = await b.refStore.get(def.id, steps);
      rows.sort((a, c) => (a.step - c.step) || (String(a.note) < String(c.note) ? -1 : String(a.note) > String(c.note) ? 1 : 0)); // 설명 앞 ①②③④ 순서: 원본 → 1차 격자(원본 위) → 돌린 그림 → 2차 격자(돌린 그림 + 수평 기준선)
      const KIND = { '①': '① 교재 원본', '②': '② 1차 격자(원본 위, 원근 그대로)', '③': '③ 수평으로 돌린 그림', '④': '④ 2차 격자(돌린 그림 위 + 수평 기준선)' };
      refModal(title, rows.map((r) => ({ img: r.img, note: String(r.note || '').replace(/^[①②③④]\s*/, ''), label: r.step === 0 ? '교재 맨 앞 완성품 사진' : r.step === 99 ? '교재 마지막 쪽 "완성" 그림' : (KIND[String(r.note || '').charAt(0)] || (r.idx ? '그림 ' + (r.idx + 1) : '교재 그림')) })));
    } catch (e) { refModal(title, []); const p = document.querySelector('#asmRefModal p'); if (p) p.textContent = '불러오지 못했어요: ' + e.message; }
  }
  function paintRefButtons() { // 관리자일 때만, 그림이 등록된 곳에만 버튼을 단다
    const head = $('asmOrderHead'), ol = $('asmOrderList');
    if (head) { const old = head.querySelector('.asm-ref-head'); if (old) old.remove(); head.style.cssText = 'margin:0 0 4px;display:flex;align-items:center;justify-content:space-between;gap:6px;'; }
    if (ol) ol.querySelectorAll('.asm-ref-btn').forEach((e) => e.remove());
    if (!def || !isAdm() || refsFor !== def.id) return;
    const mk = (txt, title, fn, cls) => { const bt = document.createElement('button'); bt.type = 'button'; bt.className = 'ghost ' + cls; bt.textContent = txt; bt.title = title; bt.style.cssText = 'flex:none;padding:2px 8px;font-size:12px;font-weight:600;border-radius:999px;'; bt.addEventListener('click', (e) => { e.stopPropagation(); fn(); }); return bt; };
    if (head && (refsMeta[0] || refsMeta[99])) head.appendChild(mk('🖼 완성 사진', '교재 맨 앞 완성품 사진과 마지막 "완성" 그림 보기(관리자 전용) — 앞·뒤·정면은 여기서 확인', () => showRefs([0, 99], '교재 완성품 사진'), 'asm-ref-head'));
    if (ol) ol.querySelectorAll('li').forEach((li, i) => {
      const n = i + 1; if (!refsMeta[n]) return;
      li.style.cssText = 'display:flex;align-items:flex-start;gap:4px;'; const bb = li.querySelector('button'); if (bb) bb.style.flex = '1 1 auto';
      li.appendChild(mk('🖼' + (refsMeta[n].length > 1 ? refsMeta[n].length : ''), n + '단계 교재 그림 보기(관리자 전용)', () => showRefs([n], n + '단계 교재 그림'), 'asm-ref-btn'));
    });
  }
  function loadRefs() { // 조립도가 정해지면 어느 단계에 그림이 있는지만 받아 온다(그림은 누를 때 받는다)
    const b = bridge(); refsMeta = {}; refsFor = null;
    if (!def || !isAdm() || !b || !b.refStore) { paintRefButtons(); return; }
    const mine = def.id;
    b.refStore.meta(mine).then((m) => { if (!def || def.id !== mine) return; refsMeta = m || {}; refsFor = mine; paintRefButtons(); });
  }
  function markStepButtons() {
    const myStep = step;
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
    // 왼쪽 "조립 순서" 목록: 지금 단계의 설명이 목록 맨 위에 오게 맞춘다(관리자 지시 2026-10-05)
    { const ol = $('asmOrderList'), cb = ol && ol.querySelector('button[aria-current="step"]');
      if (cb) ol.scrollTop += cb.getBoundingClientRect().top - ol.getBoundingClientRect().top; }
    // 오른쪽 작업 화면은 단계가 바뀔 때마다 맨 위로 되돌려, 3D 화면과 버튼 줄이 항상 같은 자리에 오게 한다(스크롤이 남아 밀려 보이던 문제)
    { const stg = document.querySelector('.stage'); if (stg) { stg.scrollTop = 0; [120, 500, 1200].forEach((ms) => setTimeout(() => { if (step === myStep) stg.scrollTop = 0; }, ms)); } }   // 화면이 늦게 자리 잡는 동안(모델·창고 카드) 밀려 올라가도 다시 맨 위로
    // 화면 위 단계 줄: 지금 단계가 가운데 오게 옆으로 밀어 준다
    const box = $('asmStageSteps'), curBtn = box.querySelector('button[aria-current="step"]');
    if (curBtn) box.scrollLeft = curBtn.offsetLeft - box.clientWidth / 2 + curBtn.offsetWidth / 2;
  }

  function render() {
    const b = bridge();
    const { list, guides, missing, stored, storedThumb, storedSlot, storedSlots, storedThumbBy, storedTypes, targets, orders, viewEff } = buildList(step);
    window.__asmStored = storedTypes; // design.html 의 사용 부품 목록이 읽는다
    { const sp = posesDB[step]; // ❄ 로 기록한 모습이 있으면 그 자리·자세로 보여 준다(제자리 target 은 그대로라 결합은 원래 자리로 된다)
      if (sp) list.forEach((d) => { const o = d.noFreeze ? null : sp[d.label]; if (o && Array.isArray(o.p)) { d.pos = o.p.slice(); if (Array.isArray(o.r)) d.rot = o.r.slice(); if (Array.isArray(o.q)) d.quat = o.q.slice(); } });
      lastLabels = list.map((d) => d.label); }
    // 다른 창고 화면을 보는 중에도 오른쪽 카드는 모든 창고의 내용을 그대로 보여 준다(화면에 그리는 것은 보는 창고뿐, 나머지 창고는 개수만 표시)
    const viewing0 = viewSlot !== null && viewSlot !== slotOfStep(step);
    let viewLabel = '', viewThumb = '';
    let storedP = stored, storedSlotP = storedSlot, storedSlotsP = storedSlots, storedThumbByP = storedThumbBy, kindsP = Object.keys(storedTypes || {}).length, ghostComps = [];
    if (viewing0) {
      const sv0 = viewSlot; viewSlot = null; let Rn, comps0 = []; try { Rn = buildList(step); comps0 = mateComponents(Rn.list); } finally { viewSlot = sv0; }
      storedP = {}; Object.keys(Rn.stored || {}).forEach((k) => { if ((Rn.storedSlots || {})[k] !== sv0) storedP[k] = Rn.stored[k]; });
      viewLabel = Object.keys(Rn.stored || {}).filter((k) => (Rn.storedSlots || {})[k] === sv0).join(', ');
      viewThumb = (Object.keys(Rn.stored || {}).filter((k) => (Rn.storedSlots || {})[k] === sv0).map((k) => (Rn.storedThumbBy || {})[k]).filter(Boolean))[0] || ''; // 보는 창고의 썸네일도 그대로
      storedSlotP = Rn.storedSlot; storedSlotsP = Rn.storedSlots; storedThumbByP = Rn.storedThumbBy; kindsP = Object.keys(Rn.storedTypes || {}).length;
      ghostComps = comps0.filter((g) => g.slot !== sv0).map((g) => ({ name: g.name, slot: g.slot, ghost: true, n: g.idx.length, idx: [] }));
    }
    renderStorage(storedP, storedThumb, kindsP, storedSlotP, storedSlotsP, storedThumbByP);
    pushSlotThumbs();
    if (b.setViewSlot) b.setViewSlot(viewSlot !== null && viewSlot !== slotOfStep(step) ? viewSlot : null, viewLabel, viewThumb);
    b.show(list.map(({ isNew, name, final, order, ...d }) => d), targets, orders, def.guideMode === 'mates' ? mateComponents(list).concat(ghostComps) : []);
    // 지금 단계에 보이는 부품(끼우기 직전 위치 포함)에 카메라를 맞춘다 — 처음부터 너무 멀리서 보이지 않게
    // 이번 단계에 끼우는 부품과 그 끼워지는 자리를 화면 가운데에 크게 보여준다(나머지 부품은 배경)
    const focus = list.filter((d) => d.isNew).map((d) => d.pos).concat(guides.filter((g) => g.to).map((g) => g.to)); // 맞물림 방식 안내는 좌표가 없다(연결점이 부품에 붙어 있다)
    const stc = (step > 0 && step < last()) ? def.steps[step - 1].cam : null; // cam.tight: 이번에 끼우는 부분만 크게(교재가 그 부분만 크게 그린 단계)
    { const axAt = stc && Array.isArray(stc.axes) ? stc.axes : null; const axKey = axAt ? axAt.join(',') : ''; // cam.axes: 이 단계의 기준점(방향선 원점)
      if (axKey !== lastAxKey) { lastAxKey = axKey; b.axes(true, axAt); } }
    const viewActive = viewSlot !== null && viewSlot !== slotOfStep(step); // 다른 창고 화면을 볼 땐 그 단계의 확대 설정을 쓰지 않고 보이는 부품 전체에 맞춘다
    const camFocus = !viewActive && stc && Array.isArray(stc.focus) && stc.focus.length ? stc.focus : null; // cam.focus: 부품이 없는 단계 등에서 이 점들을 화면 가운데에 크게(조립 프로그램이 지정)
    const axPt = stc && Array.isArray(stc.axes) ? stc.axes : [0, 0, 0]; // 바닥 기준선(방향선) 자리 — 카메라가 보는 범위에 항상 같이 들어오게 한다
    if (camFocus) b.frame(camFocus.concat([axPt]), camFocus.concat([axPt]));
    else {
      const f0 = focus.length ? focus : list.map((d) => d.pos);
      b.frame(f0.concat(stc && stc.tight && !viewActive ? [axPt] : []), stc && stc.tight && !viewActive ? f0.concat([axPt]) : list.map((d) => d.pos));
    }
    if (stc && Array.isArray(stc.rings)) stc.rings.forEach((m) => guides.push({ from: m, to: m, dir: [0, 1, 0], idx: -1, ringOnly: true })); // cam.rings: 이 단계에 고정으로 칠할 결합 점(예: 받침 흰 판 구멍)
    b.guides(guides);
    // 앞 벽이 뒤쪽 끝에 있는 단계(flip)는 반대편에서 보여준다
    // view: 기본 각도에서 90도×view 만큼 돌려서 보기 / cam: {theta, phi}로 교재 그림과 같은 각도를 직접 지정
    const camStep = (viewActive && viewEff >= 1) ? viewEff : step; // 창고 화면 보기: 그 묶음이 마지막으로 만들어진 단계의 시점
    const st = (camStep > 0 && camStep < last()) ? def.steps[camStep - 1] : null;
    const view = (st && st.view) || 0;
    const th = st && st.cam ? st.cam.theta : (def.camera ? def.camera.theta : 0) + view * Math.PI / 2;
    const ph = st && st.cam ? st.cam.phi : (def.camera ? def.camera.phi : 1);
    const camKey = th.toFixed(3) + '|' + ph.toFixed(3);
    if (b.turn && def.camera) { b.turn(th, ph); lastCamKey = camKey; } // 단계를 열 때마다 그 단계의 시점으로 — 돌려 놓은 각도는 다음 단계로 넘어가지 않는다(사용자 지시 2026-10-03)
    const sv = savedCams[camStep]; // 관리자가 저장한 시점(보는 중심·거리까지)이 있으면 그걸로 연다
    if (sv && b.camera && Array.isArray(sv.target)) b.camera({ target: sv.target, radius: sv.radius, theta: sv.theta, phi: sv.phi });
    { const myStep0 = step; setTimeout(() => { if (step === myStep0 && b.relabelGroups) b.relabelGroups(def.steps[myStep0 - 1] && def.steps[myStep0 - 1].groupSwap); }, 120); } // 그룹 이름은 왼쪽부터 1번
    { const myStep = step, myTh = sv ? sv.theta : th, myPh = sv ? sv.phi : ph, mySrc = sv ? 'admin' : (st && st.camSrc ? st.camSrc : ''); // 교재 시점 = 단계 데이터의 방향·높이각 + 화면에 맞춘 보는 중심·거리. 카메라가 자리 잡은 뒤(0.15초) 저장해 하단 표시줄이 지금 시점과 비교한다
      setTimeout(() => { if (step !== myStep || !b.camState) return; const cs = b.camState(); baseCam = { step: myStep, th: myTh, ph: myPh, target: cs.target, radius: cs.radius, src: mySrc }; }, 150); }
    const n = total();
    const curSt = step >= 1 ? def.steps[step - 1] : null, realN = def.steps.filter((q) => !q.label).length; // 창고·불러오기 같은 label 단계는 단계 번호에 넣지 않는다(사용자 지시 2026-10-04)
    $('asmLabel').textContent = step === 0 ? '시작 전' : (step === last() ? '완성!' : (curSt && curSt.label ? curSt.label : stepTag(step) + ' / ' + realN + ' 단계'));
    $('asmNote').textContent = step === 0 ? '빈 판에서 시작해요. ▶ 를 눌러 한 단계씩 만들어 봐요.'
      : (step === last() ? '완성! 부품이 모두 제자리에 끼워졌어요.' : (def.steps[step - 1].note || ''));
    { const adm2 = !!(window.__ivsIsAdmin && window.__ivsIsAdmin()); ['asmCamCopy', 'asmCamReset'].forEach((id) => { const e2 = $(id); if (e2) e2.hidden = !adm2; }); } // 📷(시점 맞춤)는 본사 관리자 로그인일 때만 보인다(사용자 지시 2026-10-03)
    $('asmSlider').value = String(step);
    $('asmStageNote').textContent = step === last() ? $('asmNote').textContent : $('asmLabel').textContent + ' · ' + $('asmNote').textContent;
    markStepButtons();
    $('asmFirst').disabled = $('asmPrev').disabled = step === 0;
    $('asmNext').disabled = $('asmLast').disabled = step === last();
    paintStatus();
    curSlot = (step >= 1 && step < last() && def.steps[step - 1] && def.steps[step - 1].slot !== undefined) ? def.steps[step - 1].slot : ((step === last() && step >= 1 && def.finalSlot !== undefined) ? def.finalSlot : -1); setStudioTitle(true); if (b.setSlot) b.setSlot(curSlot); // (완성 화면의 작업 창고는 조립도 데이터 finalSlot)
    { const hs = step >= 1 && def.steps[step - 1] ? def.steps[step - 1].history : ''; if (hs) $('asmNote').textContent += '  ▸ ' + hs; } // 내역: 창고로 갔는지 불러왔는지(단계 번호에는 넣지 않는다)
    if (missing.length) $('asmNote').textContent += ' (부품을 못 찾았어요: ' + missing.join(', ') + ')';
    // 화면 아래 단계 설명 칸에도 "작업 창고 N · 어디서 무엇을 가져오는지"를 한 줄 더 보여 준다(사용자 지시 2026-10-04: 각 번호마다 작업공간과 가져온 곳이 보여야 한다)
    { const sn = $('asmStageNote'); const hs2 = step >= 1 && def.steps[step - 1] ? def.steps[step - 1].history : '';
      if (sn && (curSlot >= 0 || hs2)) {
        const ln = document.createElement('div'); ln.style.cssText = 'margin-top:4px; font-weight:800; color:#1e3a8a; font-size:13px;';
        ln.textContent = (curSlot >= 0 ? '작업 창고 ' + curSlot : '') + (hs2 ? (curSlot >= 0 ? ' · ' : '') + hs2 : '');
        sn.appendChild(ln);
      } }
  }

  function stop() {
    clearInterval(timer); clearTimeout(timer); timer = null; timerDir = 0;
    $('asmPlay').textContent = '▶ 재생';
    $('asmReverse').textContent = '◀ 역재생';
    const br = bridge(); if (br && br.guideDots) br.guideDots(true); // 멈추면 초록 점이 다시 보인다
  }
  function go(target) {
    viewSlot = null;
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

  // 3D 작업 영역 제목: 평소엔 "스케치북". 큐보 조립도를 보는 동안만 "큐보 스튜디오"(다른 로봇은 이름이 달라서 바꾸지 않는다 - 사용자 지시 2026-10-03)
  let curSlot = -1;
  let viewSlot = null; // 오른쪽 창고 카드를 눌러 "그 창고 화면"을 보는 중(사용자 지시 2026-10-04). null = 지금 단계의 작업 창고 그대로 // 지금 단계가 작업하는 창고 자리(단계 데이터의 slot)
  function setStudioTitle(on) {
    const el = document.querySelector('.scene-title');
    if (!el) return;
    if (el.dataset.orig === undefined) el.dataset.orig = el.textContent;
    el.textContent = (on && def && def.category === '큐보') ? '큐보 스튜디오' + (curSlot >= 0 ? ' · 창고 ' + curSlot + '번' : '') : el.dataset.orig; // 지금 작업하는 창고 자리(사용자 지시 2026-10-04: 2번을 선택한 다음 조립한다)
  }
  // ── 큐보 부품 전체 리스트(사용자 지시 2026-10-03): 등록된 큐보 부품 전부를 한 화면에 펼쳐 둔다. 조립도 엔진을 그대로 써서(닫기·부품 창·번호·🟢 연결점) 단계 하나짜리 가짜 조립도로 연다.
  let catAny = null;
  let lessonFound = false;
  let connAutoOn = false; // 조립도를 열면서 연결점을 자동으로 켰는지(닫을 때 되돌리기 위해)
  // "큐보 부품 전체 리스트" 버튼은 큐보를 고른 관리자에게만 보인다(사용자 지시 2026-10-03). 조립도가 없는 차시에서도 열 수 있어야 해서 상자도 같이 맞춘다.
  function syncAllPartsBtn() {
    const box = $('assemblyBox'), btn = $('asmAllParts');
    if (!box || !btn) return;
    const admin = !!(window.__ivsIsAdmin && window.__ivsIsAdmin());
    const show = !!(catAny && catAny.name === '큐보' && admin);
    btn.hidden = !show;
    if (!viewing) box.hidden = !lessonFound && !show;
  }
  setInterval(syncAllPartsBtn, 1500); // 로그인이 늦게 끝나도 버튼이 맞게 나타난다
  const ALL_PARTS_ORDER = ['15프레임', '17프레임', '19프레임', '25프레임', '27프레임', '29프레임', '35프레임', '37프레임', '39프레임', '59프레임', '115프레임', '215프레임', '315프레임', '515프레임', '713프레임', '90도 프레임', '135도 프레임', '반원프레임', '2단블록', '3단블록', '1열브라켓', '2열브라켓', '리벳', '축', 'T축', '부시', '너트', '8볼트', '12볼트', '서보고정볼트', '작은기어', '큰기어', '육각큰기어', '작은바퀴', '중간바퀴', '데코바퀴', '눈블록', 'DC모터', '서보모터', '서보혼', '둥근서보혼', 'IR센서', 'LED센서', '터치센서', '메인보드', '스프라켓', '캐터필러', '큐보분리기'];
  const ALL_PARTS_FLIP = { '육각큰기어': [180, 0, 0] }; // 목록에서 육각이 위로 보이게 뒤집어 놓을 부품(사용자 지시 2026-10-03)
  function buildAllPartsDef() {
    const b = bridge();
    if (!b || !b.listParts || !catAny) return null;
    const all = b.listParts(catAny.id).filter((it) => it.size); // 3D 모델이 없는 부품(고무밴드·3P 케이블·리모컨 등 임시 상자 모양)은 목록에서 뺀다(사용자 지시 2026-10-03)
    const rank = (n) => { const i = ALL_PARTS_ORDER.indexOf(n); return i < 0 ? 999 : i; };
    all.sort((x, y) => rank(x.name) - rank(y.name) || String(x.name).localeCompare(String(y.name), 'ko'));
    // 3D 공간(가로세로 ±750mm) 안에, 모든 부품을 바닥(y=0)에 붙여 놓는다. 크기는 실제 모델 크기(없으면 등록 크기)를 쓰고, 프레임부터 정해 둔 순서대로 줄을 채운다.
    const HALF = 450, GAP = 20;
    let x = -HALF, z = -HALF, rowD = 0, maxX = -HALF;
    const parts = all.map((it) => {
      const d = (window.IVS_PART_DEFS || {})[it.type] || {};
      const sz = it.size || [d.w || 30, d.h || 10, d.d || 30];
      const w = Math.max(sz[0], 20), h = sz[1], dd = Math.max(sz[2], 20);
      if (x > -HALF && x + w > HALF) { x = -HALF; z += rowD + GAP; rowD = 0; }
      const pt = { n: it.name, p: [x + w / 2, h / 2 + 0.01, z + dd / 2], r: (ALL_PARTS_FLIP[it.name] || [0, 0, 0]) };
      x += w + GAP; rowD = Math.max(rowD, dd); maxX = Math.max(maxX, x);
      return pt;
    });
    if (!parts.length) return null;
    const cam = { theta: 0, phi: 0.45, focus: [[-HALF, 0, -HALF], [maxX, 0, z + rowD]], axes: [-HALF, 0, -HALF] };
    return { id: 'cubo-all-parts', category: '큐보', volume: 0, chapter: '큐보 부품 전체 리스트', camera: { theta: 0, phi: 0.45, radius: Math.max(520, (maxX + HALF + z + HALF + rowD) * 0.42), target: [(maxX - HALF) / 2, 0, (z + rowD - HALF) / 2] }, steps: [{ note: '큐보 부품 전체 리스트 (' + parts.length + '종) — 부품을 누르면 이름과 면 번호가 나와요. 🟢 연결점 버튼으로 구멍·돌기를 확인하세요.', parts, cam }] };
  }
  async function openAllParts() {
    if (viewing) close();
    const b0 = bridge();
    if (b0 && b0.listParts && catAny) { try { await b0.preload(b0.listParts(catAny.id).map((it) => it.name), catAny.id); } catch (e) { /* 못 받은 부품은 등록 크기로 */ } } // 실제 모델 크기를 알아야 바닥 아래로 안 내려간다
    const d = buildAllPartsDef();
    if (!d) { const b = bridge(); if (b) b.status('부품 목록을 아직 못 불러왔어요. 잠시 뒤에 다시 눌러 주세요.', 'warn'); return; }
    def = d; catId = catAny.id;
    buildOrderList(); buildStepButtons();
    await open();
    if (viewing) go(1); // 한 장짜리라 완성 화면 대신 1단계(펼친 전체 화면)로
    { const cb = $('connToggle'); if (viewing && cb && !cb.hidden && cb.getAttribute('aria-pressed') !== 'true') { cb.click(); connAutoOn = true; } } // 부품 전체 리스트에서만 연결점(구멍·돌기 초록 원판)을 처음부터 켠다 — 일반 조립도는 그 단계의 결합 점만 보인다
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
    setStudioTitle(true);   // 큐보 조립도를 열면 3D 영역 제목이 "스케치북" -> "큐보 스튜디오"
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
    savedCams = {};
    ensureStatusBtn(); posesDB = {}; if (b.poseStore) b.poseStore.load(def.id).then((m) => { posesDB = m || {}; paintStatus(); if (Object.keys(posesDB).length && viewing) render(); }); thumbsDB = {}; if (b.thumbStore) b.thumbStore.load(def.id).then((m) => { thumbsDB = m || {}; pushSlotThumbs(); }); stepStatus = {}; if (isAdm() && b.statusStore) b.statusStore.load(def.id).then((m) => { stepStatus = m || {}; paintStatus(); });
    if (b.camStore) b.camStore.load(def.id).then((m) => { savedCams = m || {}; if (viewing) render(); }); // 관리자가 저장한 단계별 시점
    if (refsFor !== def.id) loadRefs();
    go(last()); // 처음엔 완성된 모습부터 보여준다
    pf.asmOpened = Math.round(performance.now());
    b.status('조립 보기 중이에요. 닫으면 하던 작업으로 돌아가요.', 'success');
  }
  function close() {
    const b = bridge();
    stop();
    if (!viewing) return;
    viewing = false;
    setStudioTitle(false);
    $('asmBar').hidden = true;
    const mm = $('asmMarkMove2'); if (mm && mm.dataset.on === '1') { mm.dataset.on = '0'; mm.textContent = '📍 표시하기'; mm.style.background = mm.style.color = ''; if (b) b.markMove(false); } // 닫을 땐 사진 없이 끈다
    if ($('asmMarkMove2')) $('asmMarkMove2').hidden = $('asmMarkShot').hidden = true;
    $('asmStageBar').hidden = true;
    $('historyPanel').hidden = false;
    if (b) b.axes(false);
    if (b) { b.guides([]); b.restore(snapshot || []); b.setViewing(false); }
    { const cb = $('connToggle'); if (connAutoOn && cb && cb.getAttribute('aria-pressed') === 'true') cb.click(); connAutoOn = false; } // 자동으로 켠 연결점은 닫을 때 같이 끈다(손으로 켠 건 그대로)
    snapshot = null;
  }

  function stopPlayClick(fn) { return () => { stop(); fn(); }; }
  document.addEventListener('DOMContentLoaded', () => {
    if (!$('asmClose')) return;
    $('asmClose').addEventListener('click', close);
    if ($('asmAllParts')) $('asmAllParts').addEventListener('click', openAllParts);
    const mm2 = $('asmMarkMove2');
    const toggleMark = () => { const on = mm2.dataset.on !== '1'; mm2.dataset.on = on ? '1' : '0'; mm2.style.background = on ? '#f97316' : ''; mm2.style.color = on ? '#fff' : ''; mm2.textContent = on ? '📍 끝내기' : '📍 표시하기'; bridge().markMove(on); notice(on ? '표시 모드를 켰어요. 화면의 부품을 누르면 누른 자리에 주황 표시가 생기고, 다시 누르면 지워져요. 끝나면 [끝내기]를 누르세요.' : '표시 모드를 껐어요. 표시한 곳을 사진으로 남기려면 [수정스샷]을 누르세요.'); };
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
      const header = (def ? def.chapter : '') + ' 조립도 · ' + (step === last() ? '완성' : stepTag(step) + '단계') + ' · 표시하기';
      let blob = null;
      try { blob = await b.markCapture(header); } catch (e) { toast('사진 만들기 실패: ' + (e && e.message || e), true); notice('사진 만들기에 실패했습니다: ' + (e && e.message || e)); return; }
      if (!blob) { toast('표시가 없어요. 먼저 "📍 표시하기"를 누르고 화면의 부품을 눌러 주황 표시를 만든 뒤 눌러 주세요.', true); notice('표시가 없어요. 먼저 [표시하기]를 누르고 화면의 부품을 눌러 주황 표시를 만든 뒤 눌러 주세요.'); return; }
      let copied = false;
      try { await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]); copied = true; } catch (e) { /* 복사 권한이 없으면 다운로드만 */ }
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = '수정스샷_' + (def ? def.chapter : '') + '_' + (step === last() ? '완성' : stepTag(step) + '단계') + '.png';
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      toast(copied ? '📸 사진을 복사하고 내려받았어요 — Ctrl+V로 붙여넣어 보내 주세요' : '📸 사진을 내려받았어요(복사는 안 됐어요) — 파일을 보내 주세요');
      notice(copied ? '수정스샷이 복사되고 내려받아졌습니다. Ctrl+V로 붙여넣어 보내 주세요.' : '수정스샷이 내려받아졌습니다(복사는 안 됐어요). 파일을 보내 주세요.');
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
      if (r === 'none') bridge().status('먼저 끼울 부품 하나를 눌러서 고르세요. 그룹은 [그룹 결합] 을 쓰세요.', 'warn');
      else if (r === 'notTarget') bridge().status('이 부품은 이번 단계에서 끼우는 부품이 아니에요. 떠 있는 부품을 눌러 보세요.', 'warn');
    });
    $('asmCombineGroup').addEventListener('click', () => {
      const r = bridge().combineGroup();
      if (r === 'none') bridge().status('먼저 그룹을 눌러서 고르세요. 부품 하나는 [부품 결합] 을 쓰세요.', 'warn');
      else if (r === 'notTarget') bridge().status('이 그룹에는 이번 단계에서 끼우는 부품이 없어요. 떠 있는 그룹을 눌러 보세요.', 'warn');
    });
    const placeOn = (wantGroup) => {
      const r = bridge().placeOnPlane(wantGroup);
      if (r === 'none') bridge().status('먼저 ' + (wantGroup ? '그룹' : '부품 하나') + '을(를) 눌러서 고르세요.', 'warn');
      else if (r === 'wrong') bridge().status(wantGroup ? '그룹이 아니라 부품 하나를 골랐어요. 부품은 [부품 평면에 놓기] 를 쓰세요.' : '부품이 아니라 그룹을 골랐어요. 그룹은 [그룹 평면에 놓기] 를 쓰세요.', 'warn');
    };
    $('asmPlacePart').addEventListener('click', () => placeOn(false));
    $('asmPlaceGroup').addEventListener('click', () => placeOn(true));
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
    {
      const row = document.querySelector('#asmStageBar .asm-stage-row');
      if (row && !$('asmCamRead')) { // 현재 카메라: 방향(좌우)·높이(위아래 각도)·보고 있는 쪽·부품까지 거리 — 실시간(사용자 지시 2026-10-03)
        const bar = $('asmStageBar');
        const rd = document.createElement('div');
        rd.id = 'asmCamRead'; rd.style.cssText = 'font-size:11px; color:#6b7280; margin:3px 2px 0; line-height:1.3;';
        bar.appendChild(rd);
        let last = '';
        setInterval(() => {
          if (!viewing) return;
          const b3 = bridge(); if (!b3 || !b3.camState || !b3.camDistance) return;
          const c = b3.camState(), d = b3.camDistance();
          const deg = (r) => r * 180 / Math.PI;
          const wrap = (a) => ((a + 180) % 360 + 360) % 360 - 180;
          const f0 = (v) => Math.round(v);
          const posOf = (th, ph, tg, r) => [tg[0] + r * Math.sin(ph) * Math.sin(th), tg[1] + r * Math.cos(ph), tg[2] + r * Math.sin(ph) * Math.cos(th)];
          const sideOf = (th) => { const x = Math.sin(th), z = Math.cos(th); return (Math.abs(x) > 0.38 ? (x > 0 ? '+X' : '-X') : '') + (Math.abs(z) > 0.38 ? (z > 0 ? '+Z' : '-Z') : ''); };
          const line = (title, th, ph, pos, ctr, tail) => title + ' · 방향 ' + f0(wrap(deg(th))) + '° · 높이각 ' + f0(90 - deg(ph)) + '° · ' + sideOf(th) + ' 쪽에서 봄 · 카메라 x ' + f0(pos[0]) + ' y(높이) ' + f0(pos[1]) + ' z ' + f0(pos[2]) + ' / 보는 중심 x ' + f0(ctr[0]) + ' y ' + f0(ctr[1]) + ' z ' + f0(ctr[2]) + (tail || '');
          const lines = [];
          if (baseCam && baseCam.step === step) {
            const srcTxt = ''; // 카메라 출처 문구(눈대중·계산 등)는 화면에 적지 않는다 — 모든 카메라는 당연히 교재와 비슷하게 맞춘 것이다(사용자 지시 2026-10-04)
            lines.push(line('교재 시점', baseCam.th, baseCam.ph, posOf(baseCam.th, baseCam.ph, baseCam.target, baseCam.radius), baseCam.target, srcTxt ? ' · ' + srcTxt : ''));
          }
          lines.push(line('지금 시점', c.theta, c.phi, d.pos, d.center, ' · ' + (d.toPart ? d.label + '까지 ' : '화면 중심까지 ') + f0(d.mm) + 'mm'));
          if (baseCam && baseCam.step === step) {
            const dAz = wrap(deg(c.theta) - deg(baseCam.th)), dEl = (90 - deg(c.phi)) - (90 - deg(baseCam.ph));
            lines.push(Math.abs(dAz) < 1 && Math.abs(dEl) < 1 ? '교재 시점과 같은 각도입니다' : '교재 시점과 차이: 방향 ' + (dAz >= 0 ? '+' : '') + f0(dAz) + '° · 높이각 ' + (dEl >= 0 ? '+' : '') + f0(dEl) + '°');
          }
          const txt = lines.join('|');
          if (txt !== last) { rd.innerHTML = ''; lines.forEach((t) => { const dv = document.createElement('div'); dv.textContent = t; rd.appendChild(dv); }); last = txt; }
        }, 250);
      }
      if (row && !$('asmCamCopy')) { // 📷: 지금 보는 각도를 "카메라 N단계: theta … phi …"로 복사 — 교재와 같은 각도로 돌린 뒤 눌러 알려 주면 그 단계 카메라로 저장한다(camSrc user)
        const cb = document.createElement('button');
        cb.type = 'button'; cb.id = 'asmCamCopy'; cb.textContent = '📷 카메라';
        cb.style.cssText = 'padding:6px 12px;font-size:12px;font-weight:600;border-radius:999px;background:var(--panel);border:1px solid var(--panel-border);color:var(--ink);'; // 위 줄 버튼들과 같은 모양
        cb.title = '지금 각도를 이 단계 카메라로 복사'; cb.setAttribute('aria-label', '지금 카메라 각도 복사');
        cb.title = '지금 보이는 모습(방향·높이각·밀기·확대)을 이 단계의 시점으로 저장 — 관리자 전용';
        cb.addEventListener('click', async () => {
          const b2 = bridge(); if (!b2 || !b2.camState) return;
          const c = b2.camState(); const txt = '카메라 ' + step + '단계: theta ' + c.theta.toFixed(3) + ' phi ' + c.phi.toFixed(3);
          try { if (navigator.clipboard) navigator.clipboard.writeText(txt).catch(() => {}); } catch (e) { /* 복사 못 해도 상관없다 */ }
          if (!(window.__ivsIsAdmin && window.__ivsIsAdmin()) || !b2.camStore) { b2.status(txt + ' (복사됨)', 'success'); return; }
          const r3 = (v) => Math.round(v * 1000) / 1000, r1 = (v) => Math.round(v * 10) / 10;
          const cam = { theta: r3(c.theta), phi: r3(c.phi), radius: r1(c.radius), target: c.target.map(r1) };
          const myStep = step;
          try {
            await b2.camStore.save(def.id, myStep, cam);
            savedCams[myStep] = cam;
            baseCam = { step: myStep, th: cam.theta, ph: cam.phi, target: cam.target, radius: cam.radius, src: 'admin' };
            b2.status(myStep + '단계 시점을 저장했습니다. 이제 이 단계를 열면 이 모습으로 보여요.', 'success');
            notice('교재 샷이 저장되었습니다.');
          } catch (e) { b2.status('시점 저장에 실패했어요: ' + e.message, 'error'); }
        });
        { // 📷 카메라는 위 줄(체크·모습 기록 버튼이 있는 줄)로 옮겼다 — 체크 → 카메라 → 모습 기록 순서
          const host = $('asmMarkMove2'), fz = $('asmFreezeBtn'), st0 = $('asmStatusBtn');
          if (host) host.parentNode.insertBefore(cb, fz && fz.parentNode === host.parentNode ? fz : host); else row.appendChild(cb);
          if (st0 && fz && st0.parentNode === fz.parentNode) fz.parentNode.insertBefore(st0, cb);
        }
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
      window.__asmQtyOverride = (found && found.qtyOverride) || null; // 조립도 쪽 부품 개수가 책과 다를 때 {부품 이름: 개수}(design.html 의 필요 부품·사용 부품이 이 개수를 기준으로 하고 책 개수는 괄호로만 알린다)
      catId = found ? cat.id : null;
      catAny = cat;
      lessonFound = !!found;
      syncAllPartsBtn();
      ['asmOrderHead', 'asmOrderList', 'asmSteps'].forEach((id) => { if ($(id)) $(id).style.display = found ? '' : 'none'; });
      buildOrderList();
      loadRefs(); // 관리자 전용 교재 참고 그림 버튼(🖼) — 로그인 정보가 늦게 오면 조립 보기를 열 때 한 번 더 시도한다
      if (def) buildStepButtons(); // 번호 줄도 조립 보기를 열기 전부터 보인다
      $('asmRules').innerHTML = (window.IVS_ASSEMBLY_RULES || []).map((r) => '<li>' + r + '</li>').join('');
    },
    isViewing() { return viewing; },
    setViewSlot(n) { if (!viewing || !def || step < 1 || step >= last()) return; viewSlot = (n === slotOfStep(step) || n === viewSlot) ? null : n; render(); },
  };
  // 새로고침 버튼으로 다시 열었으면, 보던 차시(분류·권·차시 선택)와 단계를 자동으로 다시 연다
  (function restoreAfterReload() {
    let st = null; try { st = JSON.parse(sessionStorage.getItem('ivs-asm-restore') || 'null'); sessionStorage.removeItem('ivs-asm-restore'); } catch (e) { st = null; }
    if (!st || !Array.isArray(st.sel)) return;
    let tries = 0;
    const timer = setInterval(() => {
      tries++;
      const sels = [...document.querySelectorAll('select')].slice(0, 3);
      const ready = sels.length === 3 && sels[2].options.length > 1 && sels[0].querySelector('option[value="' + st.sel[0] + '"]');
      if (ready) {
        clearInterval(timer);
        [0, 1, 2].forEach((k) => { if (sels[k].value !== st.sel[k]) { sels[k].value = st.sel[k]; sels[k].dispatchEvent(new Event('change', { bubbles: true })); } });
        let t2 = 0; const timer2 = setInterval(() => { t2++; const b = document.querySelector('#asmSteps button[data-step="' + st.step + '"]'); if (b) { clearInterval(timer2); b.click(); } else if (t2 > 40) clearInterval(timer2); }, 250);
      } else if (tries > 60) clearInterval(timer);
    }, 250);
  })();
})();
