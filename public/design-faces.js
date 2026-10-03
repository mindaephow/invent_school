// 부품의 "면"과 "구멍·돌기 번호" — 부품에 고정된 이름 붙이기 (조립 보기 화면·큐보 조립 MCP 가 같은 파일을 쓴다)
// 규칙(사용자 지시 2026-10-03):
//   · 부품의 모델 축(+x −x +y −y +z −z)이 부품에 붙어 있다. 부품을 어떻게 돌려 놓든 "+y면"은 늘 그 부품의 같은 면이다.
//   · 면은 두 종류뿐: 홀면(구멍이 있는 면) / 돌기면(돌기가 나온 면). 같은 종류가 둘이면 +y·−y 처럼 축으로 구분한다.
//   · 면 안의 번호: 면에 수직인 축을 뺀 나머지 두 축을 x → y → z 순서로 놓고, 첫째 축이 "열", 둘째 축이 "줄"이다.
//     번호는 각 축의 − 끝에서부터 1, 2, 3… (프레임 구멍 id h{열}_{줄} 과 같은 방향).
//   · 같은 이름 부품의 번호("35프레임 2/2")는 조립도 전체에서 나온 순서(단계 → 부품 순)로 1, 2, 3….
//   · 지금은 프레임·블록(2단·3단)만 확정. 나머지 부품은 연결점에서 같은 규칙으로 계산해 주되 confirmed:false 로 표시한다.
(function () {
  const D2R = Math.PI / 180;
  const AX = ['x', 'y', 'z'];
  const UNIT = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] };
  const TOL = 2; // mm: 같은 열·줄로 묶는 허용 오차 (2단블록 돌기 x=−4.4/5.7 처럼 측정값이 살짝 어긋난 것을 한 열로 본다)
  const CONFIRMED = /^(\d\d+프레임|2단블록|3단블록)$/;

  function matFromEuler(r) {
    const [a, b, c] = (r || [0, 0, 0]).map((v) => v * D2R);
    const cx = Math.cos(a), sx = Math.sin(a), cy = Math.cos(b), sy = Math.sin(b), cz = Math.cos(c), sz = Math.sin(c);
    return [
      [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
      [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
      [-sy, cy * sx, cy * cx],
    ];
  }
  const mulv = (m, v) => [0, 1, 2].map((i) => m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2]);
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const r1 = (v) => Math.round(v * 10) / 10;

  // 방향 벡터가 가장 가까운 축 하나 → { axis:'y', sign:+1 }
  function dominant(d) {
    let k = 0;
    for (let i = 1; i < 3; i++) if (Math.abs(d[i]) > Math.abs(d[k])) k = i;
    return { axis: AX[k], sign: d[k] >= 0 ? 1 : -1 };
  }
  const worldAxisName = (v) => { const q = dominant(v); return (q.sign > 0 ? '+' : '-') + q.axis.toUpperCase(); };

  // 좌표 목록을 작은 것부터 묶어 순위(1부터)를 매긴다
  function ranks(vals) {
    const sorted = [...vals].sort((a, b) => a - b);
    const groups = [];
    sorted.forEach((v) => { const g = groups[groups.length - 1]; if (g && Math.abs(v - g[g.length - 1]) <= TOL) g.push(v); else groups.push([v]); });
    const centers = groups.map((g) => g.reduce((s, x) => s + x, 0) / g.length);
    return { of: (v) => centers.findIndex((c) => Math.abs(c - v) <= TOL) + 1, count: centers.length };
  }

  // 연결점({pegs, holes}) → 면 목록. 구멍의 dir 은 "끼워 들어가는 방향"이라 입구 면의 바깥쪽은 −dir, 돌기의 dir 은 바깥쪽이다.
  function facesOf(conn) {
    const raw = {}; // key → { kind, axis, sign, items:[{ids, pos}] }
    const put = (kind, axis, sign, c) => {
      const key = `${kind}면 ${sign > 0 ? '+' : '-'}${axis}`;
      (raw[key] = raw[key] || { key, kind, axis, sign, items: [] }).items.push({ id: c.id, pos: c.pos, len: c.len || 0 });
    };
    (conn.pegs || []).forEach((c) => { const d = dominant(c.dir); put('돌기', d.axis, d.sign, c); });
    (conn.holes || []).forEach((c) => {
      const d = dominant(c.dir);
      put('홀', d.axis, -d.sign, c); // 입구 면
      if (c.through) put('홀', d.axis, d.sign, c); // 관통 구멍은 반대쪽 면에도 열려 있다
    });
    return Object.values(raw).map((f) => {
      const [A, B] = AX.filter((a) => a !== f.axis); // 열 축, 줄 축 (x → y → z 순서)
      const ia = AX.indexOf(A), ib = AX.indexOf(B);
      const ra = ranks(f.items.map((it) => it.pos[ia])), rb = ranks(f.items.map((it) => it.pos[ib]));
      const items = f.items.map((it) => {
        const col = ra.of(it.pos[ia]), row = rb.of(it.pos[ib]);
        return { id: it.id, pos: it.pos, len: it.len, col, row, label: rb.count === 1 ? `${col}` : `열${col}·줄${row}` };
      }).sort((p, q) => p.row - q.row || p.col - q.col);
      const normal = UNIT[f.axis].map((v) => v * f.sign);
      return { key: f.key, kind: f.kind, axis: f.axis, sign: f.sign, normal, colAxis: A, rowAxis: B, cols: ra.count, rows: rb.count, items };
    }).sort((p, q) => (p.kind === q.kind ? 0 : p.kind === '홀' ? -1 : 1) || AX.indexOf(p.axis) - AX.indexOf(q.axis) || q.sign - p.sign);
  }

  // 조립도 전체에서 같은 이름 부품의 번호 매기기 → { total:{이름:개수}, numOf: Map(부품 데이터 → 번호) }
  function numberParts(steps) {
    const total = {}, seq = {}, numOf = new Map();
    (steps || []).forEach((s) => (s.parts || []).forEach((q) => { total[q.n] = (total[q.n] || 0) + 1; }));
    (steps || []).forEach((s) => (s.parts || []).forEach((q) => { seq[q.n] = (seq[q.n] || 0) + 1; numOf.set(q, seq[q.n]); }));
    return { total, numOf };
  }

  // 부품 하나(이름 n, 위치 p, 회전 r)를 세계 좌표로 풀어 설명한다. k/t = 부품 번호/전체 개수
  function describe(part, conn, k, t) {
    const m = matFromEuler(part.r);
    const world = (v) => mulv(m, v);
    const axes = {};
    ['+x', '-x', '+y', '-y', '+z', '-z'].forEach((a) => { const u = UNIT[a[1]].map((v) => v * (a[0] === '+' ? 1 : -1)); axes[a] = worldAxisName(world(u)); });
    const name = k ? `${part.n} ${k}번` : part.n;
    const faces = facesOf(conn).map((f) => ({
      key: f.key, kind: f.kind, 부품축: (f.sign > 0 ? '+' : '-') + f.axis, 월드방향: worldAxisName(world(f.normal)),
      열축: f.colAxis, 줄축: f.rowAxis, 열수: f.cols, 줄수: f.rows,
      items: f.items.map((it) => ({ label: it.label, id: it.id, 월드좌표: add(part.p, world(it.pos)).map(r1) })),
    }));
    return { name, confirmed: CONFIRMED.test(part.n), 부품축_월드방향: axes, faces };
  }

  // 월드 좌표 한 점이 이 부품의 어느 면·몇 번 구멍/돌기인지 (tol mm 안에서 가장 가까운 것)
  function locate(part, conn, point, tol, k, t) {
    const d = describe(part, conn, k, t);
    let best = null;
    d.faces.forEach((f) => f.items.forEach((it) => {
      const dist = Math.hypot(it.월드좌표[0] - point[0], it.월드좌표[1] - point[1], it.월드좌표[2] - point[2]);
      if (dist <= (tol || 6) && (!best || dist < best.dist)) best = { dist: r1(dist), 부품: d.name, 면: f.key, 번호: it.label, id: it.id, 월드좌표: it.월드좌표 };
    }));
    return best;
  }


  // 부품 하나의 돌기·구멍을 세계 좌표로 (kind: '돌기' | '홀')
  function worldConnectors(part, conn) {
    const m = matFromEuler(part.r);
    const w = (kind) => (c) => ({ kind, id: c.id, pos: add(part.p, mulv(m, c.pos)), dir: mulv(m, c.dir), len: c.len || 0, through: !!c.through });
    return { pegs: (conn.pegs || []).map(w('돌기')), holes: (conn.holes || []).map(w('홀')) };
  }
  const dotv = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  // 세계 좌표의 돌기 하나가 구멍 하나에 들어가 있나: 방향이 같고(관통 구멍은 반대도 가능), 축이 겹치고, 깊이 구간이 겹친다
  function mates(peg, hole) {
    const dd = dotv(peg.dir, hole.dir);
    if (!(dd > 0.9 || (hole.through && dd < -0.9))) return false;
    const rel = [peg.pos[0] - hole.pos[0], peg.pos[1] - hole.pos[1], peg.pos[2] - hole.pos[2]];
    const along = dotv(rel, hole.dir);
    const lat = Math.hypot(rel[0] - along * hole.dir[0], rel[1] - along * hole.dir[1], rel[2] - along * hole.dir[2]);
    return lat < 2 && Math.abs(along) <= (peg.len + hole.len) / 2 + 1;
  }
  // describe() 결과 안에서 연결점 하나의 이름 "홀면 +y 열5·줄1" / "돌기면 +z 1".
  // 관통 구멍은 면이 둘이라, 들어오는 돌기의 진행 방향(enterDir)을 주면 그 돌기가 들어온 입구 면 하나만 말한다.
  function nameWorldItem(rec, c, enterDir) {
    const want = enterDir ? worldAxisName([-enterDir[0], -enterDir[1], -enterDir[2]]) : null; // 입구 면의 바깥 방향 = 돌기 진행 방향의 반대
    const keys = [], labels = [];
    rec.faces.forEach((f) => {
      if (f.kind !== c.kind) return;
      if (want && c.kind === '홀' && f.월드방향 !== want) return;
      const it = f.items.find((x) => x.id === c.id);
      if (it) { keys.push(f.key.replace(/^(홀면|돌기면) /, '')); labels.push(it.label); }
    });
    if (!keys.length) return c.id;
    return `${c.kind === '돌기' ? '돌기면' : '홀면'} ${keys.join('/')} ${labels[0]}`;
  }

  window.IVS_FACES = { facesOf, numberParts, describe, locate, worldConnectors, mates, nameWorldItem, worldAxisName, CONFIRMED };
})();
