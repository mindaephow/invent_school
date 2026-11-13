// 부품끼리 겹침 검사 — 설계 화면에서 부품이 서로를 통과하지 못하게 한다(사용자 지시: "홀에 돌기가 끼워질 순
// 있지만 그 이상의 겹쳐짐은 안 된다"). 부품 몸통을 기울어진 상자(OBB)로 근사해서 검사하고, 돌기·리벳·축처럼
// 홀에 들어가는 부분은 몸통에 넣지 않는다(= 홀에 끼우는 것은 겹침으로 세지 않는다). three.js에 의존하지 않는 순수 수학.
(function () {
  // 부품 이름과 3D 모델 크기(가운데 기준)로 몸통 상자 목록을 만든다. 규칙이 없는 부품은 null(검사 안 함).
  // 상자: { c: [x, y, z](부품 가운데 기준 중심), h: [반치수 x, y, z] } — 모델 로컬 좌표.
  function coreBoxes(name, dims) {
    const n = String(name || '');
    const sx = dims[0], sy = dims[1], sz = dims[2];
    // 꺾인 프레임은 정사각·직사각 통상자로 보면 빈 모서리까지 몸통으로 계산돼 이웃 부품과 겹친 것으로 나온다 → 팔마다 상자로 나눈다.
    //   90도 프레임(30×5×30): 구멍 열이 x=−10(z 방향 팔)·z=−10(x 방향 팔), 팔 너비 10mm.
    if (/^90도 프레임/.test(n)) return [{ c: [-sx / 2 + 5, 0, 0], h: [5, sy / 2, sz / 2] }, { c: [0, 0, -sz / 2 + 5], h: [sx / 2, sy / 2, 5] }];
    //   135도 프레임(83.3×5×33.3): 곧은 팔 = 구멍 h4~h9(z=11.5, x −13.5~36.5), 꺾인 팔 = h4→h1 방향 45°(−0.707, −0.707)로 29.7mm + 끝 여백 5mm. 팔 너비 10mm. (연결점 구멍 좌표 기준)
    if (/^135도 프레임/.test(n)) return [{ c: [14.07, 0, 11.5], h: [27.43, sy / 2, 5] }, { c: [-25.77, 0, -0.77], h: [17.35, sy / 2, 5], ry: -45 }];   // 긴 팔 상자는 꺾임 구멍 h4(x −13.36)에서 시작한다 — 뒤로 5mm 더 두면 상자 모서리가 실제 둥근 꺾임보다 2mm 나와 판 위의 프레임이 판과 겹친다고 나왔다(배틀로봇 7·8번, 2026-11-13)
    if (/프레임/.test(n)) return [{ c: [0, 0, 0], h: [sx / 2, sy / 2, sz / 2] }];
    const block = n.match(/(\d+)단블록/);
    // N단블록: 몸통은 길이 10mm×N, 두께 10mm — 앞뒤 면의 돌기(양쪽 5mm)와 양 끝 돌기(5mm)는 제외
    if (block) return [{ c: [0, 0, 0], h: [Math.min(10 * Number(block[1]), sx) / 2, sy / 2, 5] }];
    // ㄴ자 브라켓: 바닥 팔(두께 5mm) + 세로 팔(두께 5mm, 모델 −z 끝). 안쪽 빈 공간은 비워 둔다.
    if (/브라켓/.test(n)) return [
      { c: [0, -sy / 2 + 2.5, 0], h: [sx / 2, 2.5, sz / 2] },
      { c: [0, 0, -sz / 2 + 2.5], h: [sx / 2, sy / 2, 2.5] },
    ];
    // 눈블록: 모델 아래쪽(y 0~2)의 둥근 판만 몸통 — 위쪽 돌기(프레임 구멍에 꽂는 쪽)는 제외. 판 두께는 등록 모델 실측 2mm(2026-11-05, 예전 2.5 는 프레임에 0.5mm 겹쳐 보였다)
    if (/눈블록/.test(n)) return [{ c: [0, -sy / 2 + 1, 0], h: [sx / 2, 1, sz / 2], rd: sx / 2 }];   // rd: 둥근 부품(원기둥 반지름, 축 = 모델 y) — 상자 모서리는 비어 있다
    // 기어: 이빨 끝까지 통짜 상자로 보면 맞물리는 두 기어(중심 간격 = 피치 반지름 합 < 상자 반폭 합)가 항상 겹쳐 막힌다 → 이빨 깊이(2.5mm)만큼 평면 반폭을 줄여 맞물림 높이까지 들어갈 수 있게 한다(사용자 지시 2026-10-12: 큰기어가 작은기어 높이까지 들어가야 한다).
    if (/기어/.test(n)) return [{ c: [0, 0, 0], h: [Math.max(sx / 2 - 2.5, 1), sy / 2, Math.max(sz / 2 - 2.5, 1)], rd: sx / 2 }];   // 상자는 이빨 깊이만큼 줄인 것(기어끼리 맞물림용), rd 는 이빨 끝까지의 실제 반지름 — 기어와 다른 부품은 원기둥으로 다시 본다
    if (/부시/.test(n)) return [{ c: [0, 0, 0], h: [sx / 2, sy / 2, sz / 2], rd: sx / 2 }];
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
    if (box.ry) { // 상자 하나만 부품 로컬 y축으로 돌린 것(꺾인 프레임의 비스듬한 팔)
      const r = box.ry * Math.PI / 180, cs = Math.cos(r), sn = Math.sin(r);
      return { c, axes: [[0, 1, 2].map((i) => cs * ax[0][i] - sn * ax[2][i]), ax[1], [0, 1, 2].map((i) => sn * ax[0][i] + cs * ax[2][i])], h: box.h };
    }
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
      for (const b of boxesB) {
        const wb = worldBox(b, posB, qB, axB);
        if (!obbOverlap(wa, wb, tol)) continue;
        if (!!a.rd !== !!b.rd && !cylinderHit(a.rd ? wa : wb, a.rd ? a.rd : b.rd, a.rd ? wb : wa, tol)) continue;   // 둥근 부품(기어·부시·눈블록)은 상자 모서리가 비어 있다 — 상대 상자가 원기둥 안에 들어와야 겹침(2026-11-08 로봇팽이 33번)
        return true;
      }
    }
    return false;
  }

  // 원기둥(상자 wc 의 중심·모델 y축, 반지름 R, 반길이 wc.h[1])과 상자 wo 가 tol(mm)보다 깊이 겹치는가 — wo 를 1mm 격자로 훑어 원기둥 안에 드는 점이 있으면 겹침
  function cylinderHit(wc, R, wo, tol) {
    const y = wc.axes[1], r = R - tol, t = wc.h[1] - tol;
    const nx = Math.max(1, Math.ceil(wo.h[0] * 2)), ny = Math.max(1, Math.ceil(wo.h[1] * 2)), nz = Math.max(1, Math.ceil(wo.h[2] * 2));
    for (let a = 0; a <= nx; a++) for (let b = 0; b <= ny; b++) for (let c = 0; c <= nz; c++) {
      const u0 = (a / nx * 2 - 1) * wo.h[0], u1 = (b / ny * 2 - 1) * wo.h[1], u2 = (c / nz * 2 - 1) * wo.h[2];
      const dx = wo.c[0] + u0 * wo.axes[0][0] + u1 * wo.axes[1][0] + u2 * wo.axes[2][0] - wc.c[0];
      const dy = wo.c[1] + u0 * wo.axes[0][1] + u1 * wo.axes[1][1] + u2 * wo.axes[2][1] - wc.c[1];
      const dz = wo.c[2] + u0 * wo.axes[0][2] + u1 * wo.axes[1][2] + u2 * wo.axes[2][2] - wc.c[2];
      const al = dx * y[0] + dy * y[1] + dz * y[2];
      if (Math.abs(al) >= t) continue;
      if (Math.hypot(dx - al * y[0], dy - al * y[1], dz - al * y[2]) < r) return true;
    }
    return false;
  }

  window.IVS_COLLISION = { coreBoxes, axesFromQuat, worldBox, obbOverlap, boxesOverlap };
})();
