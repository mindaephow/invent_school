// 끼움/분리 가능 검사 + 조립 순서 추론 — design-collision.js 의 몸통 상자 겹침 검사 위에 얹는다.
// 알고리즘 아이디어(분해로 조립 순서 찾기: 부품을 한 방향으로 밀어 빼 보고, 막히지 않으면 그 부품을 먼저 뺀다 → 뺀 순서의 역순 = 조립 순서)만 참고해 직접 구현했다. 외부 코드는 쓰지 않았다.
// three.js 에 의존하지 않는 순수 수학. 부품 모양: { id, boxes(몸통 상자 목록|null), pos:{x,y,z}, q:{x,y,z,w} }.
// boxes 가 null 인 부품(몸통 규칙 없음)은 겹침 검사를 못 하므로 막지도 막히지도 않는다(= 분해 순서에서 맨 먼저 빠짐, stuck 에 안 들어감).
(function () {
  const C = (typeof window !== 'undefined' && window.IVS_COLLISION) || (typeof require === 'function' ? require('./design-collision.js') : null);

  const move = (pos, dir, t) => ({ x: pos.x + dir[0] * t, y: pos.y + dir[1] * t, z: pos.z + dir[2] * t });

  // 부품 i 를 dir(단위벡터) 방향으로 dist(mm)까지 1칸씩 밀어 본다. others = 이미 빠진 부품을 뺀 나머지 부품 목록.
  // 반환 { ok, at(막힌 거리), blockedBy(막은 부품 id) }
  function slideCheck(part, dir, dist, others, opts) {
    const tol = (opts && opts.tol) != null ? opts.tol : 0.6;
    const step = (opts && opts.step) || 1;
    if (!part.boxes) return { ok: true };
    for (let t = step; t <= dist + 1e-9; t += step) {
      const p = move(part.pos, dir, t);
      for (const o of others) {
        if (o === part || !o.boxes) continue;
        if (C.boxesOverlap(part.boxes, p, part.q, o.boxes, o.pos, o.q, tol)) return { ok: false, at: t, blockedBy: o.id };
      }
    }
    return { ok: true };
  }

  // 후보 방향: 부품 자신의 로컬 축 ±3개 + 세계 축 ±3개 (중복 제거). 끼우는 방향은 대개 돌기·구멍 축 = 로컬/세계 축이다.
  function candidateDirs(q) {
    const ax = C.axesFromQuat(q);
    const list = [];
    const add = (v) => { if (!list.some((u) => Math.abs(u[0] - v[0]) + Math.abs(u[1] - v[1]) + Math.abs(u[2] - v[2]) < 1e-6)) list.push(v); };
    for (const a of ax) { add(a); add([-a[0], -a[1], -a[2]]); }
    for (let k = 0; k < 3; k++) for (const s of [1, -1]) { const v = [0, 0, 0]; v[k] = s; add(v); }
    return list;
  }

  // 부품 하나가 빠질 수 있는 방향을 찾는다. 반환 { dir } | { dir:null, blockers:{방향별 막은 부품 id} }
  function findRemovalDir(part, others, opts) {
    const dist = (opts && opts.dist) || 300;
    const blockers = {};
    for (const d of candidateDirs(part.q)) {
      const r = slideCheck(part, d, dist, others, opts);
      if (r.ok) return { dir: d };
      blockers[d.map((x) => +x.toFixed(2)).join(',')] = r.blockedBy;
    }
    return { dir: null, blockers };
  }

  // 분해로 조립 순서 찾기. parts = 완성 자세의 전체 부품. 반환
  //  order: 조립 순서(부품 id, 먼저 끼울 것부터) / removeDirs: 부품별 빠지는 방향(조립 때는 반대로 끼움) / stuck: 끝까지 못 뺀 부품 id(조립 불가 설계 또는 상자 근사 한계)
  function planAssembly(parts, opts) {
    const remaining = parts.slice();
    const removed = [];
    const removeDirs = {};
    // 높은 부품부터 뺀다(중력 방향 선호) — 이걸 안 하면 바닥판이 아래로 먼저 "빠져" 순서가 거꾸로 나온다.
    const up = (opts && opts.up) || [0, 1, 0];
    const h = (p) => p.pos.x * up[0] + p.pos.y * up[1] + p.pos.z * up[2];
    let progress = true;
    while (remaining.length && progress) {
      progress = false;
      remaining.sort((a, b) => h(b) - h(a));
      for (let i = 0; i < remaining.length; i++) {
        const p = remaining[i];
        const r = findRemovalDir(p, remaining, opts);
        if (r.dir) {
          removed.push(p.id);
          removeDirs[p.id] = r.dir;
          remaining.splice(i, 1);
          progress = true;
          break; // 하나 빠졌으면 처음부터 다시 — 순서가 안정적이다
        }
      }
    }
    return { order: removed.reverse(), removeDirs, stuck: remaining.map((p) => p.id) };
  }

  // 단계 검사: 이미 놓인 부품(placed) 위로 새 부품을 insertDir 방향에서 distance 만큼 떨어진 곳에서 밀어 넣어 완성 자세까지 들어가는가.
  // 완성 자세에서 -insertDir 로 빼 보는 것과 같다(= slideCheck 를 반대로).
  function canInsert(newPart, placed, insertDir, opts) {
    const back = [-insertDir[0], -insertDir[1], -insertDir[2]];
    const r = slideCheck(newPart, back, (opts && opts.dist) || 60, placed, opts);
    return r.ok ? { ok: true } : { ok: false, blockedBy: r.blockedBy, atMm: r.at };
  }

  const api = { slideCheck, candidateDirs, findRemovalDir, planAssembly, canInsert };
  if (typeof window !== 'undefined') window.IVS_INSERTION = api;
  if (typeof module !== 'undefined') module.exports = api;
})();
