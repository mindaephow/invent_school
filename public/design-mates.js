// 돌기↔구멍 "결합" 검사 — 조립 배치(부품 위치·회전)와 부품 DB의 연결점(data.connectors: pegs/holes)을 받아,
// 각 돌기가 다른 부품의 구멍 안에 정확히 들어가 있는지 계산한다(방향이 같고, 축이 겹치고, 깊이가 맞는지).
// 눈블록처럼 돌기가 바깥을 향해 뒤집힌 배치, 구멍에서 어긋난 배치를 자동으로 잡아낸다. three.js에 의존하지 않는 순수 수학.
// 조립 보기 화면·큐보 조립 MCP(validate_assembly)가 같은 파일을 쓴다.
(function () {
  const D2R = Math.PI / 180;
  // 오일러(도, ZYX: R = Rz·Ry·Rx) → 회전 행렬(3×3)
  function matFromEuler(r) {
    const cx = Math.cos(r[0] * D2R), sx = Math.sin(r[0] * D2R), cy = Math.cos(r[1] * D2R), sy = Math.sin(r[1] * D2R), cz = Math.cos(r[2] * D2R), sz = Math.sin(r[2] * D2R);
    return [
      [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
      [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
      [-sy, cy * sx, cy * cx],
    ];
  }
  const mulv = (m, v) => [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2], m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2], m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const scale = (a, k) => [a[0] * k, a[1] * k, a[2] * k];

  // 부품 하나(이름, 위치 p, 회전 r)의 연결점을 세계 좌표로
  function worldConnectors(part, conn) {
    const m = matFromEuler(part.r || [0, 0, 0]);
    const w = (c) => ({ id: c.id, pos: add(part.p, mulv(m, c.pos)), dir: mulv(m, c.dir), len: c.len || 0, r: c.r || 0, through: !!c.through });
    return { pegs: (conn.pegs || []).map(w), holes: (conn.holes || []).map(w) };
  }

  // parts: [{ key, n, p, r }], connectorsByName: { 이름: { pegs, holes } }
  // 반환: { mated:[…], free:[…], noData:[…] }
  //   mated: 돌기가 들어간 구멍 { part, peg, into, hole }
  //   free : 어느 구멍에도 안 들어간 돌기(방향·위치가 안 맞거나 그냥 비어 있는 것) — 같은 부품의 안 쓰는 돌기일 수도 있다
  function check(parts, connectorsByName, opt) {
    const tolAxis = (opt && opt.axisTol) || 1.2;   // 돌기 축과 구멍 축이 이 거리 안에서 겹쳐야 한다(mm)
    const tolDepth = (opt && opt.depthTol) || 1.0; // 돌기 뿌리가 구멍 끝을 이만큼까지 넘어가도 본다
    const minIn = (opt && opt.minIn) || 1.0;       // 돌기 끝이 구멍 안으로 들어가 있어야 하는 최소 깊이(mm)
    const W = parts.map((pt) => ({ pt, conn: connectorsByName[pt.n], world: connectorsByName[pt.n] ? worldConnectors(pt, connectorsByName[pt.n]) : null }));
    const mated = [], free = [], noData = [];
    W.forEach((a, ai) => {
      if (!a.world) { noData.push(a.pt.key || a.pt.n); return; }
      a.world.pegs.forEach((peg) => {
        const hits = []; // 축처럼 구멍 여러 개를 지나가는 돌기는 전부 센다
        W.forEach((b, bi) => {
          if (bi === ai || !b.world) return;
          b.world.holes.forEach((hole) => {
            // 돌기가 구멍으로 들어가는 방향: 돌기 방향 = 구멍의 "들어가는 방향"(관통 구멍은 반대쪽에서도 들어갈 수 있다)
            const aligned = dot(peg.dir, hole.dir);
            const okDir = aligned > 0.98 || (hole.through && aligned < -0.98);
            if (!okDir) return;
            const axis = aligned > 0 ? hole.dir : scale(hole.dir, -1);
            // 구멍 축 위 좌표(깊이)와 축에서 벗어난 거리
            const rel = sub(peg.pos, hole.pos);
            const along = dot(rel, axis);
            const lateral = Math.hypot(...sub(rel, scale(axis, along)));
            if (lateral > tolAxis) return;
            // 돌기 끝(tip)과 뿌리(base)가 구멍 깊이 범위 안에 있는가
            const half = (hole.len || 0) / 2;
            const tip = along + (peg.len || 0) / 2, base = along - (peg.len || 0) / 2;
            // 돌기 끝이 구멍 안으로 최소 minIn(mm)은 들어가 있어야 결합이다(입구에 닿기만 한 것·떠 있는 것은 제외)
            if (tip < -half + minIn || base > half - 0.5 + tolDepth) return;
            hits.push({ part: a.pt.key || a.pt.n, peg: peg.id, into: b.pt.key || b.pt.n, hole: hole.id, lateral: Math.round(lateral * 10) / 10 });
          });
        });
        if (hits.length) mated.push(...hits); else free.push({ part: a.pt.key || a.pt.n, peg: peg.id, dir: peg.dir.map((v) => Math.round(v * 100) / 100), pos: peg.pos.map((v) => Math.round(v * 10) / 10) });
      });
    });
    return { mated, free, noData };
  }


// ── 단계별 정밀 검사(사람이 놓치기 쉬운 실수를 잡는다) ──
// 1) 새 부품은 그 단계에서 실제 구멍에 끼워져야 한다  2) 안내(marks)가 실제 구멍/돌기 끝 위치와 맞아야 한다
// 3) 리벳은 마지막에 양 끝이 모두 구멍에 들어가야 한다  4) 방향이 정해진 부품(T축 머리 위 등)  5) 단계 설명의 개수가 데이터와 맞는지
  function checkSteps(list, conn) {
    const M = { worldConnectors, check, matFromEuler }
    const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
    const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
  const issues = []
  // move: 옆자리에서 다 만든 뒤 한 번 더 옮겨 붙는 부품(풍차 상자) — 그 단계 이후엔 옮긴 자리 기준으로 검사한다
  const posAfterMove = (pt, stepNo) => (pt.move && stepNo >= pt.move.at ? (pt.move.p || pt.p.map((v, k) => v + (pt.move.by || [0, 0, 0])[k])) : pt.p)
  const rotAfterMove = (pt, stepNo) => (pt.move && pt.move.r && stepNo >= pt.move.at ? pt.move.r : (pt.r || [0, 0, 0]))
  const worldOf = (pt) => (conn[pt.n] ? M.worldConnectors({ p: pt.p, r: pt.r || [0, 0, 0] }, conn[pt.n]) : null)
  list.forEach((st, si) => {
    const upto = []
    list.slice(0, si + 1).forEach((s, k) => (s.parts || []).forEach((pt, i) => upto.push({ key: `${k + 1}.${i} ${pt.n}`, n: pt.n, p: posAfterMove(pt, si + 1), r: rotAfterMove(pt, si + 1), ref: pt, step: k + 1 })))
    const res = M.check(upto, conn)
    const worlds = upto.map((u) => ({ u, w: worldOf(u) }))
    ;(st.parts || []).forEach((pt, i) => {
      const me = upto.find((u) => u.ref === pt)
      if (conn[pt.n] && me && !res.mated.some((m) => m.part === me.key || m.into === me.key)) issues.push(`${si + 1}단계 ${pt.n}: 어떤 구멍·돌기에도 끼워지지 않음(허공에 떠 있음)`)
      // 안내 위치: 고정된 쪽의 실제 구멍 축/돌기 끝과 맞는지(옆자리 조립품·분리 표시는 제외)
      if (pt.dir && pt.marks && !pt.side && !pt.explode) {
        pt.marks.forEach((m) => {
          const ok = worlds.some(({ u, w }) => w && u.ref !== pt && ((pt.recv || pt.pegTarget)
            ? w.pegs.some((pg) => { const tip = [pg.pos[0] + pg.dir[0] * pg.len / 2, pg.pos[1] + pg.dir[1] * pg.len / 2, pg.pos[2] + pg.dir[2] * pg.len / 2]; if (Math.hypot(...sub(tip, m)) <= 3) return true; const base = [pg.pos[0] - pg.dir[0] * pg.len / 2, pg.pos[1] - pg.dir[1] * pg.len / 2, pg.pos[2] - pg.dir[2] * pg.len / 2]; return pg.len >= 30 && Math.hypot(...sub(base, m)) <= 3 }) // 축처럼 길게 꽂히는 돌기는 양 끝 어느 쪽에서도 끼울 수 있다(부시는 아래 끝에서)
            : w.holes.some((h) => { const rel = sub(m, h.pos); const along = dot(rel, h.dir); return Math.hypot(...sub(rel, h.dir.map((x) => x * along))) <= 1.8 && Math.abs(along) <= h.len / 2 + 3 })))
          if (!ok) issues.push(`${si + 1}단계 ${pt.n}: 안내 위치 [${m}]에 ${(pt.recv || pt.pegTarget) ? '고정된 돌기 끝' : '받는 구멍'}이 없음(위치 어긋남)`)
        })
      }
      // 방향이 정해진 부품: T축 접시 머리(모델 −y)는 위로
      if (pt.n === 'T축' && !pt.headDown && !pt.horizontal) { // headDown: true — 로봇을 뒤집은 방향이라 머리가 아래가 맞는 T축
        const m = M.matFromEuler(pt.r || [0, 0, 0])
        if (!(m[1][1] < -0.9)) issues.push(`${si + 1}단계 T축: 접시 머리가 위로 오지 않음(r=[180,0,0] 이어야 함)`)
      }
    })
    // 설명 글의 "○○ N개"가 이 단계 부품 수와 맞는지
    const counts = {}; (st.parts || []).forEach((pt) => { counts[pt.n] = (counts[pt.n] || 0) + 1 })
    for (const m of String(st.note || '').matchAll(/([가-힣A-Za-z0-9]+?)\s*(\d+)개/g)) {
      const name = Object.keys(counts).find((n) => n === m[1] || m[1].endsWith(n))
      if (name && counts[name] !== Number(m[2])) issues.push(`${si + 1}단계 설명 "${m[0]}" ↔ 데이터 ${name} ${counts[name]}개`)
    }
    if (!(st.parts || []).length && !st.noPart && !list.some((s) => (s.parts || []).some((pt) => (pt.side && pt.side.until === si + 1) || (pt.move && pt.move.at === si + 1)))) issues.push(`${si + 1}단계: 부품이 하나도 없음`)
  })
  // 마지막 모양: 리벳은 양 끝 돌기가 모두 구멍에 들어가야 한다
  const all = []; list.forEach((s, k) => (s.parts || []).forEach((pt, i) => all.push({ key: `${k + 1}.${i} ${pt.n}`, n: pt.n, p: posAfterMove(pt, 1e9), r: rotAfterMove(pt, 1e9), ref: pt })))
  const fin = M.check(all, conn)
  all.filter((a) => a.n === '리벳' && !(a.ref && a.ref.openEnd)).forEach((a) => {
    const pegs = new Set(fin.mated.filter((m) => m.part === a.key).map((m) => m.peg))
    if (pegs.size < 2) issues.push(`${a.key}: 리벳 한쪽 끝만 구멍에 들어감(${pegs.size}/2)`)
  })
  return issues
}


  window.IVS_MATES = { matFromEuler, worldConnectors, check, checkSteps };
})();
