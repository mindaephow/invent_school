// 부품끼리 겹침 검사 — 설계 화면에서 부품이 서로를 통과하지 못하게 한다(사용자 지시: "홀에 돌기가 끼워질 순
// 있지만 그 이상의 겹쳐짐은 안 된다"). 부품 몸통을 기울어진 상자(OBB)로 근사해서 검사하고, 돌기·리벳·축처럼
// 홀에 들어가는 부분은 몸통에 넣지 않는다(= 홀에 끼우는 것은 겹침으로 세지 않는다). three.js에 의존하지 않는 순수 수학.
(function () {
  // 부품 이름과 3D 모델 크기(가운데 기준)로 몸통 상자 목록을 만든다. 규칙이 없는 부품은 null(검사 안 함).
  // 상자: { c: [x, y, z](부품 가운데 기준 중심), h: [반치수 x, y, z] } — 모델 로컬 좌표.
  function coreBoxes(name, dims) {
    const n = String(name || '');
    const sx = dims[0], sy = dims[1], sz = dims[2];
    if (/프레임/.test(n)) return [{ c: [0, 0, 0], h: [sx / 2, sy / 2, sz / 2] }];
    const block = n.match(/(\d+)단블록/);
    // N단블록: 몸통은 길이 10mm×N, 두께 10mm — 앞뒤 면의 돌기(양쪽 5mm)와 양 끝 돌기(5mm)는 제외
    if (block) return [{ c: [0, 0, 0], h: [Math.min(10 * Number(block[1]), sx) / 2, sy / 2, 5] }];
    // ㄴ자 브라켓: 바닥 팔(두께 5mm) + 세로 팔(두께 5mm, 모델 −z 끝). 안쪽 빈 공간은 비워 둔다.
    if (/브라켓/.test(n)) return [
      { c: [0, -sy / 2 + 2.5, 0], h: [sx / 2, 2.5, sz / 2] },
      { c: [0, 0, -sz / 2 + 2.5], h: [sx / 2, sy / 2, 2.5] },
    ];
    // 눈블록: 위쪽 둥근 판(두께 4mm)만 몸통 — 아래로 꽂는 돌기는 제외
    if (/눈블록/.test(n)) return [{ c: [0, sy / 2 - 2, 0], h: [sx / 2, 2, sz / 2] }];
    if (/기어|부시/.test(n)) return [{ c: [0, 0, 0], h: [sx / 2, sy / 2, sz / 2] }];
    return null;
  }

  // 쿼터니언 {x,y,z,w} → 회전 행렬의 열(= 모델 x·y·z축이 세계에서 향하는 방향)
  function axesFromQuat(q) {
    const x = q.x, y = q.y, z = q.z, w = q.w;
    return [
      [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)],
      [2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)],
      [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)],
    ];
  }
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const crs = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

  // 로컬 상자를 세계 기울어진 상자로
  function worldBox(box, pos, q, axes) {
    const ax = axes || axesFromQuat(q);
    const c = [pos.x, pos.y, pos.z];
    for (let k = 0; k < 3; k++) for (let i = 0; i < 3; i++) c[i] += ax[k][i] * box.c[k];
    return { c, axes: ax, h: box.h };
  }

  // 두 기울어진 상자가 tol(mm)보다 더 깊이 겹치는가 — 분리축 검사(SAT). 맞닿기만 하면 겹침이 아니다.
  function obbOverlap(A, B, tol) {
    const d = [B.c[0] - A.c[0], B.c[1] - A.c[1], B.c[2] - A.c[2]];
    const cand = [];
    for (let i = 0; i < 3; i++) { cand.push(A.axes[i]); cand.push(B.axes[i]); }
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      const c = crs(A.axes[i], B.axes[j]);
      const len = Math.hypot(c[0], c[1], c[2]);
      if (len > 1e-6) cand.push([c[0] / len, c[1] / len, c[2] / len]);
    }
    for (const L of cand) {
      let ra = 0, rb = 0;
      for (let k = 0; k < 3; k++) { ra += A.h[k] * Math.abs(dot(L, A.axes[k])); rb += B.h[k] * Math.abs(dot(L, B.axes[k])); }
      if (ra + rb - Math.abs(dot(L, d)) <= tol) return false; // 이 축으로 떨어져 있다
    }
    return true;
  }

  // 부품 하나(몸통 상자 목록 + 위치 + 회전)끼리 겹치는가
  function boxesOverlap(boxesA, posA, qA, boxesB, posB, qB, tol) {
    const axA = axesFromQuat(qA), axB = axesFromQuat(qB);
    for (const a of boxesA) {
      const wa = worldBox(a, posA, qA, axA);
      for (const b of boxesB) if (obbOverlap(wa, worldBox(b, posB, qB, axB), tol)) return true;
    }
    return false;
  }

  window.IVS_COLLISION = { coreBoxes, axesFromQuat, worldBox, obbOverlap, boxesOverlap };
})();
