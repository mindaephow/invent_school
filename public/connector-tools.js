// 큐보 부품 돌기·구멍 "연결점" 생성 도구 — 3D 모델(부품 수리실 spec)에서 돌기와 구멍 위치를 찾아 부품 DB(ivs_part_catalog.data.connectors)에 기록한다.
// 브라우저(design.html, 로그인한 선생님 계정)에서 실행: 이 파일을 불러온 뒤 __buildAllConnectors() → __writeAllConnectors().
// 좌표는 3D 모델 bbox 가운데를 원점으로 한 모델 로컬 좌표(y 위). 기록 형식은 get_assembly_guide(큐보 조립 MCP) 7장.
//   - 구멍: 원통 벽 삼각형의 법선이 중심을 향하는 것을 이용한 허프 투표(프레임 12종으로 검증: 구멍 수가 이름의 칸 수와 모두 일치)
//   - 돌기: 몸통 상자(design-collision.js coreBoxes) 밖으로 튀어나온 부분을 묶고, 십자 홈으로 갈라진 조각은 4.5mm 안에서 합침(블록·눈블록)
//   - 브라켓·기어·바퀴·모터·메인보드·분리기는 자동 탐지 결과라 confidence:'auto'(확인 필요), 프레임·블록·눈블록·리벳은 'checked'
// 새 부품을 추가하면 __CONNECTOR_PARTS 에 [이름, id]를 더해 다시 실행한다.
// 3D 모델(삼각형 메시)에서 원통 돌기·구멍을 찾는다. 브라우저에서 실행(window.__partsLabViewer.buildPartGeometryData 결과를 받음).
window.__detectConnectors = function (d) {
  const pos = d.position, idx = d.index, bb = d.bbox;
  const nTri = (idx ? idx.length : pos.length / 3) / 3;
  const V = (i) => { const k = idx ? idx[i] : i; return [pos[k * 3], pos[k * 3 + 1], pos[k * 3 + 2]]; };
  const ctr = [0, 1, 2].map((i) => (bb.min[i] + bb.max[i]) / 2);
  const size = [0, 1, 2].map((i) => bb.max[i] - bb.min[i]);
  const tris = [];
  for (let t = 0; t < nTri; t++) {
    const a = V(t * 3), b = V(t * 3 + 1), c = V(t * 3 + 2);
    const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    let n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    const L = Math.hypot(n[0], n[1], n[2]); if (L < 1e-9) continue;
    n = n.map((v) => v / L);
    const cen = [0, 1, 2].map((i) => (a[i] + b[i] + c[i]) / 3);
    tris.push({ n, cen, lo: [0, 1, 2].map((i) => Math.min(a[i], b[i], c[i])), hi: [0, 1, 2].map((i) => Math.max(a[i], b[i], c[i])) });
  }
  const R = []; for (let r = 1.5; r <= 12; r += 0.25) R.push(r);
  const out = [];
  for (let ax = 0; ax < 3; ax++) {
    const u = (ax + 1) % 3, v = (ax + 2) % 3;
    const votes = new Map();
    for (const T of tris) {
      if (Math.abs(T.n[ax]) > 0.3) continue;
      const nu = T.n[u], nv = T.n[v], L = Math.hypot(nu, nv); if (L < 0.9) continue;
      const hu = nu / L, hv = nv / L, ang = Math.atan2(hv, hu);
      const bin = Math.floor(((ang + Math.PI) / (2 * Math.PI)) * 12) % 12;
      for (const r of R) for (const sgn of [1, -1]) { // sgn +1: 구멍(법선이 중심을 향함), −1: 돌기(법선이 바깥)
        const cu = Math.round((T.cen[u] + sgn * r * hu) * 2) / 2, cv = Math.round((T.cen[v] + sgn * r * hv) * 2) / 2;
        const key = sgn + '|' + r + '|' + cu + '|' + cv;
        let e = votes.get(key);
        if (!e) { e = { sgn, r, cu, cv, n: 0, bins: 0, lo: 1e9, hi: -1e9 }; votes.set(key, e); }
        e.n++; e.bins |= 1 << bin; e.lo = Math.min(e.lo, T.lo[ax]); e.hi = Math.max(e.hi, T.hi[ax]);
      }
    }
    const cand = [...votes.values()].filter((e) => e.n >= 10 && popcount(e.bins) >= 7);
    cand.sort((a, b) => b.n - a.n);
    const kept = [];
    for (const e of cand) {
      if (kept.some((k) => k.sgn === e.sgn && Math.hypot(k.cu - e.cu, k.cv - e.cv) < 2.0)) continue;
      if (e.hi - e.lo < 1.0) continue; // 너무 얕은 것(모따기 등)은 제외
      kept.push(e);
    }
    for (const e of kept) out.push({ ax, u, v, ...e });
  }
  function popcount(x) { let c = 0; while (x) { c += x & 1; x >>= 1; } return c; }
  const round = (x) => Math.round(x * 10) / 10;
  const pegs = [], holes = [];
  for (const e of out) {
    const center = [0, 0, 0]; center[e.u] = e.cu; center[e.v] = e.cv; center[e.ax] = (e.lo + e.hi) / 2;
    const rel = center.map((x, i) => x - ctr[i]);
    const len = e.hi - e.lo;
    const dirv = [0, 0, 0];
    if (e.sgn === -1) { // 돌기: 끝이 중심에서 먼 쪽
      const s = Math.abs(e.hi - ctr[e.ax]) >= Math.abs(e.lo - ctr[e.ax]) ? 1 : -1;
      dirv[e.ax] = s;
      pegs.push({ pos: rel.map(round), dir: dirv, len: round(len), r: round(e.r) });
    } else {
      const through = len >= size[e.ax] * 0.9;
      const s = Math.abs(e.hi - ctr[e.ax]) >= Math.abs(e.lo - ctr[e.ax]) ? -1 : 1; // 구멍이 들어가는 방향(입구 반대쪽)
      dirv[e.ax] = s;
      holes.push({ pos: rel.map(round), dir: dirv, r: round(e.r), through, len: round(len) });
    }
  }
  // 구멍 입구의 넓어지는 테두리가 돌기로 잘못 잡히는 것을 제거: 같은 축·같은 중심에서 구멍보다 굵은 "돌기"
  for (let i = pegs.length - 1; i >= 0; i--) {
    const p = pegs[i], pa = p.dir.findIndex((x) => x !== 0);
    if (holes.some((h) => h.dir.findIndex((x) => x !== 0) === pa && [0, 1, 2].filter((k) => k !== pa).every((k) => Math.abs(h.pos[k] - p.pos[k]) < 1.5) && p.r >= h.r - 0.1)) pegs.splice(i, 1);
  }
  const byPos = (a, b) => a.pos[1] - b.pos[1] || a.pos[0] - b.pos[0] || a.pos[2] - b.pos[2];
  pegs.sort(byPos); holes.sort(byPos);
  pegs.forEach((p, i) => { p.id = 'p' + (i + 1); }); holes.forEach((h, i) => { h.id = 'h' + (i + 1); });
  return { pegs, holes, size: size.map(round) };
};
'detect ready'

// 돌기 탐지(몸통 상자 밖으로 튀어나온 부분을 묶는다): core = design-collision.js 의 몸통 상자(로컬, 가운데 기준)
window.__detectPegsByCore = function (d, core) {
  const pos = d.position, bb = d.bbox;
  const ctr = [0, 1, 2].map((i) => (bb.min[i] + bb.max[i]) / 2);
  const N = pos.length / 3, TOL = 0.6, G = 1;
  const res = [];
  for (let ax = 0; ax < 3; ax++) for (const sgn of [1, -1]) {
    const face = core.c[ax] + sgn * core.h[ax];
    const u = (ax + 1) % 3, v = (ax + 2) % 3;
    const pts = [];
    for (let i = 0; i < N; i++) {
      const p = [pos[i * 3] - ctr[0], pos[i * 3 + 1] - ctr[1], pos[i * 3 + 2] - ctr[2]];
      if (sgn * (p[ax] - face) > TOL && Math.abs(p[u] - core.c[u]) <= core.h[u] + TOL && Math.abs(p[v] - core.c[v]) <= core.h[v] + TOL) pts.push(p);
    }
    // 격자 연결 성분으로 묶기
    const cells = new Map();
    pts.forEach((p) => { const k = Math.round(p[u] / G) + ',' + Math.round(p[v] / G); (cells.get(k) || cells.set(k, []).get(k)).push(p); });
    const seen = new Set(), lobes = [];
    for (const k of cells.keys()) {
      if (seen.has(k)) continue;
      const stack = [k], comp = []; seen.add(k);
      while (stack.length) { const c = stack.pop(); comp.push(...cells.get(c)); const [a, b] = c.split(',').map(Number);
        for (let da = -1; da <= 1; da++) for (let db = -1; db <= 1; db++) { const nk = (a + da) + ',' + (b + db); if (cells.has(nk) && !seen.has(nk)) { seen.add(nk); stack.push(nk); } } }
      if (comp.length < 6) continue;
      const cu = comp.reduce((s, p) => s + p[u], 0) / comp.length, cv = comp.reduce((s, p) => s + p[v], 0) / comp.length;
      let far = 0; comp.forEach((p) => { far = Math.max(far, sgn * (p[ax] - face)); });
      lobes.push({ cu, cv, n: comp.length, far, pts: comp });
    }
    // 십자 홈 때문에 한 돌기가 조각으로 나뉘므로, 4.5mm 안의 조각을 다시 합친다(이웃 돌기는 10mm 간격이라 안 합쳐짐)
    const grp = lobes.map((_, i) => i);
    const find = (i) => { while (grp[i] !== i) i = grp[i] = grp[grp[i]]; return i; };
    for (let i = 0; i < lobes.length; i++) for (let j = i + 1; j < lobes.length; j++) if (Math.hypot(lobes[i].cu - lobes[j].cu, lobes[i].cv - lobes[j].cv) <= 4.5) grp[find(i)] = find(j);
    const groups = new Map();
    lobes.forEach((l, i) => { const g = find(i); (groups.get(g) || groups.set(g, []).get(g)).push(l); });
    for (const g of groups.values()) {
      const all = g.flatMap((l) => l.pts);
      if (all.length < 12) continue;
      const cu = all.reduce((s, p) => s + p[u], 0) / all.length, cv = all.reduce((s, p) => s + p[v], 0) / all.length;
      const far = Math.max(...g.map((l) => l.far));
      const center = [0, 0, 0]; center[u] = cu; center[v] = cv; center[ax] = face + sgn * far / 2;
      const dir = [0, 0, 0]; dir[ax] = sgn;
      const rad = Math.max(...all.map((p) => Math.hypot(p[u] - cu, p[v] - cv)));
      res.push({ pos: center.map((x) => Math.round(x * 10) / 10), dir, len: Math.round(far * 10) / 10, r: Math.round(rad * 10) / 10 });
    }
  }
  return res;
};

window.__CONNECTOR_PARTS = [['15프레임','68eacee4-73c9-4690-965a-6fac456c677c'],['17프레임','56bced65-1769-4473-8f49-b5b8a5b02287'],['19프레임','1f35a634-9eee-409d-8b5a-f4aaeb8d0f6f'],['115프레임','00903854-de9b-4920-b249-4baf6f694e10'],['25프레임','bb7cc47f-e9b5-4e2f-923f-9b3c29df0b02'],['27프레임','d0b9c5be-a98b-4992-aef5-dc4491c31391'],['29프레임','d49ef761-ab6e-45ec-94eb-23b6a94940ea'],['35프레임','ec97c6a3-f0d1-41e8-92e1-c0ba0ea882fc'],['37프레임','25659ab3-c8be-4bb0-8bc3-4f72935c9225'],['39프레임','ac0a82e0-662a-4dc9-a8ba-6766596b5da9'],['315프레임','7ebf4def-3969-4bd9-b47e-8b23f20e467b'],['59프레임','33c9ad6e-671c-4cb8-8e46-f0ed42b51cb8'],['90도 프레임','b3728440-1496-4c4e-9593-e0cddf2de6ba'],['135도 프레임','ed3feaba-cfa8-4655-a7d7-24eae8b267d3'],['리벳','af9d6d08-204a-4817-ba16-9d61df0716f7'],['부시','b0a436b3-2ef5-4da6-b33d-a39d67d8f2c1'],['축','6b234eed-820f-4b90-96aa-1627a8fa0332'],['T축','8ce5b5ee-bfe1-44cb-aece-070c66e5028c'],['2단블록','9149e7e4-368c-455a-8de1-c364a0217a42'],['3단블록','8eb0a771-cdf6-481d-b8c5-e8a393d1d823'],['1열브라켓','b0ff316b-73f9-467a-8593-c85196fcf0cf'],['2열브라켓','792143c3-4555-431d-b72f-fa6cb8e7506c'],['눈블록','cff069a1-dfe6-4a77-8d72-935d655e5c82'],['작은바퀴','1bfa609d-b5b7-459a-8598-8fc07feafc3a'],['데코바퀴','c329ef7f-19ef-4284-a52e-551db3150c20'],['작은기어','ba2bd400-7e7e-44e5-a771-f2ad5dca2128'],['큰기어','473baf78-9c85-4ec6-9aa5-0dee33698c9e'],['DC모터','26551cb8-0032-4936-96e1-e0b06518f631'],['메인보드','5cc88969-77ed-4a57-8a66-0d38564d89db'],['큐보분리기','9bca1912-71b1-4162-a415-b87c90582229']];

// 부품 하나의 3D 모델(원시 배열) 받기 — 로그인한 선생님 토큰으로 REST 조회
window.__connectorModel = async function (id, env) {
  const r = await fetch(`${env.url}/rest/v1/ivs_part_catalog?select=spec:data->spec&id=eq.${id}`, { headers: { apikey: env.key, Authorization: 'Bearer ' + env.token } });
  const spec = (await r.json())[0].spec;
  return window.__partsLabViewer.buildPartGeometryData(spec.shapes);
};

window.__buildConnectorFor = async function (name, id, env) {
  const d = await window.__connectorModel(id, env);
  const size = [0, 1, 2].map((i) => d.bbox.max[i] - d.bbox.min[i]);
  const det = window.__detectConnectors(d);
  let pegs = det.pegs, holes = det.holes, note = '', conf = 'auto';
  const cores = window.IVS_COLLISION.coreBoxes(name, size);
  if (/단블록|눈블록/.test(name)) {
    pegs = window.__detectPegsByCore(d, cores[0]).map((p, i) => ({ ...p, id: 'p' + (i + 1) }));
    conf = 'checked';
    if (/눈블록/.test(name)) { holes = []; note = '얇은 원판(바깥쪽, 모델 아래 y 0~2.5)과 프레임 구멍에 꽂는 돌기(모델 위 +y). 원판이 바깥으로 오게 놓는다.'; }
    else note = '돌기: 앞뒤 면(±z)에 각 ' + (name === '3단블록' ? 3 : 2) + '개 + 양 끝(±x)에 십자 돌기 1개씩. 위·아래(±y)는 구멍이 있는 평면 → 돌기를 프레임 구멍에 꽂으려면 x축 90°로 눕힌다.';
  } else if (/프레임/.test(name) && !/도 프레임/.test(name)) { pegs = []; conf = 'checked'; note = '구멍이 두께(y) 방향으로 10mm 격자. through=true 면 양쪽에서 끼울 수 있다.'; }
  else if (/도 프레임/.test(name)) { pegs = []; note = '꺾인 프레임 — 구멍 위치는 자동 탐지(확인 필요).'; }
  else if (name === '리벳') { holes = []; pegs = [{ id: 'p1', pos: [0, -3, 0], dir: [0, -1, 0], len: 3, r: 3.2 }, { id: 'p2', pos: [0, 3, 0], dir: [0, 1, 0], len: 3, r: 3.2 }]; conf = 'checked'; note = '양 끝이 같은 체결 핀(축 y, 길이 9): 겹친 두 프레임(또는 부품) 구멍을 관통해 고정한다.'; }
  else if (name === '부시') { pegs = []; note = '스페이서. 가운데 구멍에 T축이 지나간다.'; }
  else if (name === 'T축' || name === '축') {
    // 십자 단면 축은 원통 탐지가 못 잡으므로, 축 전체를 "긴 돌기 하나"로 기록한다 — 지나가는 기어·부시·프레임의 가운데 구멍마다 결합으로 센다.
    holes = []; pegs = [{ id: 'p1', pos: [0, 0, 0], dir: [0, 1, 0], len: name === 'T축' ? 30 : 65, r: 3.5 }];
    note = '십자 단면 축(축 y, 길이 ' + (name === 'T축' ? 30 : 65) + '). 축 전체를 긴 돌기 하나로 기록: 기어·바퀴·부시의 가운데 구멍을 지나간다.' + (name === 'T축' ? ' 둥근 덮개가 모델 위(+y) 끝 — 기어 윗면과 같은 높이에 온다.' : '');
  }
  else if (/브라켓/.test(name)) { pegs = []; note = 'ㄴ자: 바닥 팔(y 0~5)과 세로 팔(z −15~−10). 구멍 위치는 자동 탐지(확인 필요).'; }
  else note = '자동 탐지 — 확인 필요.';
  const re = (a) => a.map(({ id, pos, dir, len, r, through }) => { const o = { id, pos, dir }; if (len != null) o.len = len; if (r != null) o.r = r; if (through != null) o.through = through; return o; });
  return { pegs: re(pegs), holes: re(holes), confidence: conf, note, size: size.map((v) => Math.round(v * 10) / 10) };
};

// 전부 만들기(읽기만, DB 안 건드림) → window.__conn
window.__buildAllConnectors = async function (env) {
  const conn = {};
  for (const [name, id] of window.__CONNECTOR_PARTS) conn[name] = { id, connectors: await window.__buildConnectorFor(name, id, env) };
  window.__conn = conn;
  return Object.entries(conn).map(([n, c]) => `${n}: 돌기 ${c.connectors.pegs.length} 구멍 ${c.connectors.holes.length} [${c.connectors.confidence}]`).join('\n');
};

// DB에 기록: 부품 수정 API(update_part)에 connectors 를 실어 보낸다 — 기존 필드는 get_part 로 받은 값을 그대로 다시 보낸다.
window.__writeAllConnectors = async function (adminToken, only) {
  const api = async (b) => { const r = await fetch('/api/admin', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + adminToken }, body: JSON.stringify(b) }); const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.error || r.status); return j; };
  const results = [];
  for (const [name, { id, connectors }] of Object.entries(window.__conn)) {
    if (only && !only.includes(name)) continue;
    try {
      const before = (await api({ action: 'get_part', partId: id })).part;
      try { await api({ action: 'update_part', partId: id, name: before.name, icon: before.icon, subject: before.subject, category: before.category || '', color: before.color || '', size: before.size || '', imageSvg: before.imageSvg || '', imageSvgDiagonal: before.imageSvgDiagonal || '', primaryImage: before.primaryImage || 'front', volumes: before.volumes || [], connectors }); }
      catch (e) { if (!/timeout/i.test(e.message)) throw e; } // 저장 뒤 응답 만드는 단계의 시간 초과는 무시(저장은 끝남)
      results.push(name + ' ✓');
    } catch (e) { results.push(name + ' ✗ ' + e.message); }
  }
  return results.join('\n');
};
