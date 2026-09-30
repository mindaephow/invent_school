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
        let hit = null;
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
            hit = { part: a.pt.key || a.pt.n, peg: peg.id, into: b.pt.key || b.pt.n, hole: hole.id, lateral: Math.round(lateral * 10) / 10 };
          });
        });
        if (hit) mated.push(hit); else free.push({ part: a.pt.key || a.pt.n, peg: peg.id, dir: peg.dir.map((v) => Math.round(v * 100) / 100), pos: peg.pos.map((v) => Math.round(v * 10) / 10) });
      });
    });
    return { mated, free, noData };
  }

  window.IVS_MATES = { matFromEuler, worldConnectors, check };
})();
