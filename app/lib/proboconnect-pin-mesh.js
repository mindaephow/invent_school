// 프로보 커넥트 핀(2단핀·3단핀)을 삼각형으로 직접 짠다. 책 핀툴 사용법 9·11쪽 그림 + 사용자 설명(2026-10-29): 핀의 가운데는 원통이고, 다리(아래쪽 갈라진 부분)와 걸림(발)만 다르다.
// 길이 = 블럭 n 장 두께 합(2단핀 10, 3단핀 15) — 머리 윗면 = 첫 블럭 윗면, 발 아랫면 = 마지막 블럭 아랫면(프레임 밖으로 안 나온다).
// 좌표: 머리 윗면이 y=0, 아래로 갈수록 음수. 꽂을 때 발은 x 방향(띠 방향)으로 벌어져 띠를 지나가고, 90° 돌리면 z 방향이 되어 턱(|z|≥1.45) 아래에 걸린다.
// ⚠ 추정: 머리 반지름 3.6·두께 1.5, 가운데 원통 반지름 2.6(책 그림 비율: 머리 폭의 약 0.72, 사용자 지적 2026-10-29 '더 커야 한다') + 스냅핏 틈 폭 0.6(아래~높이의 60%), 발 = 길이 ±3.5·폭(z) 2.0·높이 1.5(머리 두께)·모서리 둥글게, 다리 사이 틈 0.6.
import { makeKit } from './cubo-mesh-kit.js'
import { PROBO_STD, roundPoly } from './proboconnect-block-mesh.js'
import { ringFace } from './cubo-face-mesh.js'

export function probo2nPinTriangles(layers = 2, S = PROBO_STD, rot = 0) {
  const kit = makeKit(24), { quad, tri, P } = kit
  const L = layers * S.thick, headH = 1.5, headR = 3.6, shaftR = 2.6, innerR = 1.5, footX = 3.5, footW = 1.0, footH = 1.5, slot = 0.3, seg = 24
  const yShaft = -L // 관(다리)은 맨 아래까지 내려와 평평하게 잘린다(사용자 지시 2026-10-29)
  const R = (x, z) => rot ? [-z, x] : [x, z]       // rot=1: 핀을 세로축 둘레로 90° 돌린(잠긴) 모습
  const nr = (nx, nz) => rot ? [-nz, nx] : [nx, nz]
  const disc = (r, y, ny) => { const z = R(0, 0); for (let k = 0; k < seg; k++) { const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, p0 = R(r * Math.cos(a0), r * Math.sin(a0)), p1 = R(r * Math.cos(a1), r * Math.sin(a1)); tri(P(z[0], y, z[1]), P(p0[0], y, p0[1]), P(p1[0], y, p1[1]), 0, ny, 0) } }
  const cyl = (r, y0, y1) => { for (let k = 0; k < seg; k++) { const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2, p0 = R(r * Math.cos(a0), r * Math.sin(a0)), p1 = R(r * Math.cos(a1), r * Math.sin(a1)), n = nr(Math.cos(am), Math.sin(am)); quad(P(p0[0], y0, p0[1]), P(p1[0], y0, p1[1]), P(p1[0], y1, p1[1]), P(p0[0], y1, p0[1]), n[0], 0, n[1]) } }
  const box = (x0, x1, y0, y1, z0, z1) => { // 닫힌 상자(바깥 법선)
    const c = (x, y, z) => { const [a, b] = R(x, z); return P(a, y, b) }
    const f = (a, b, d, e, nx, ny, nz) => { const n = nr(nx, nz); quad(a, b, d, e, n[0], ny, n[1]) }
    f(c(x1, y0, z0), c(x1, y0, z1), c(x1, y1, z1), c(x1, y1, z0), 1, 0, 0)
    f(c(x0, y0, z1), c(x0, y0, z0), c(x0, y1, z0), c(x0, y1, z1), -1, 0, 0)
    f(c(x0, y1, z0), c(x1, y1, z0), c(x1, y1, z1), c(x0, y1, z1), 0, 1, 0)
    f(c(x0, y0, z1), c(x1, y0, z1), c(x1, y0, z0), c(x0, y0, z0), 0, -1, 0)
    f(c(x0, y0, z1), c(x1, y0, z1), c(x1, y1, z1), c(x0, y1, z1), 0, 0, 1)
    f(c(x1, y0, z0), c(x0, y0, z0), c(x0, y1, z0), c(x1, y1, z0), 0, 0, -1)
  }
  // 머리: 원 둘레 양옆(발이 벌어지는 x 방향)에 핀툴 홈 둘 — 머리 두께의 절반 깊이(0.75)까지만 판다(사용자 지적 2026-10-29 "전체가 아니라 절반만"). 둘레까지 열린 홈(폭 1.4, 안쪽 반지름 1.9).
  const gw = 0.7, gx = 1.9, gd = headH / 2, th0 = Math.asin(gw / headR), xr = Math.sqrt(headR * headR - gw * gw), N = 16
  const pt = (x, z) => R(x, z)
  const arcPts = (from, to) => Array.from({ length: N + 1 }, (_, i) => { const an = from + ((to - from) * i) / N; return [headR * Math.cos(an), headR * Math.sin(an)] })
  const A1 = arcPts(th0, Math.PI - th0), A2 = arcPts(Math.PI + th0, 2 * Math.PI - th0) // 위쪽 호(z>0 쪽), 아래쪽 호(z<0 쪽)
  const top = [...A1, [-gx, gw], [-gx, -gw], ...A2, [gx, -gw], [gx, gw]]                // 윗면 윤곽(홈 포함)
  const bot = [...A1, ...A2]                                                             // 아랫면 윤곽(호 + 홈 자리는 곧은 변)
  const Tp = top.map(([x, z]) => pt(x, z)), Bp = bot.map(([x, z]) => pt(x, z))
  const edge = (p0, p1, y0, y1, out) => { const ex = p1[0] - p0[0], ez = p1[1] - p0[1]; quad(P(p0[0], y0, p0[1]), P(p1[0], y0, p1[1]), P(p1[0], y1, p1[1]), P(p0[0], y1, p0[1]), out ? ez : -ez, 0, out ? -ex : ex) }
  // 옆벽: 호 구간(바닥~위), 홈 구간은 홈 바닥(−gd)~위, 홈 아래 둘레는 곧은 변(바닥~−gd)
  for (let i = 0; i < A1.length - 1; i++) for (const A of [A1, A2]) {   // 호 옆벽. 홈과 닿는 끝 꼭짓점(A[0]·A[N])의 세로 모서리는 홈 바닥 높이에서 둘로 갈라지므로 그 칸만 다섯 점 다각형으로 삼각분할한다
    const p0 = pt(...A[i]), p1 = pt(...A[i + 1]), ex = p1[0] - p0[0], ez = p1[1] - p0[1], nx = ez, nz = -ex
    const V = (q, y) => P(q[0], y, q[1])
    if (i === 0) { const b0 = V(p0, -headH), m0 = V(p0, -gd), t0 = V(p0, 0), b1 = V(p1, -headH), t1 = V(p1, 0); tri(b0, b1, t1, nx, 0, nz); tri(b0, t1, m0, nx, 0, nz); tri(m0, t1, t0, nx, 0, nz) }
    else if (i === N - 1) { const b0 = V(p0, -headH), t0 = V(p0, 0), b1 = V(p1, -headH), m1 = V(p1, -gd), t1 = V(p1, 0); tri(b0, b1, m1, nx, 0, nz); tri(b0, m1, t1, nx, 0, nz); tri(b0, t1, t0, nx, 0, nz) }
    else edge(p0, p1, -headH, 0, true)
  }
  edge(pt(...A1[N]), pt(-gx, gw), -gd, 0, true); edge(pt(-gx, gw), pt(-gx, -gw), -gd, 0, true); edge(pt(-gx, -gw), pt(...A2[0]), -gd, 0, true)   // 왼쪽 홈 벽
  edge(pt(...A2[N]), pt(gx, -gw), -gd, 0, true); edge(pt(gx, -gw), pt(gx, gw), -gd, 0, true); edge(pt(gx, gw), pt(...A1[0]), -gd, 0, true)       // 오른쪽 홈 벽
  edge(pt(...A1[N]), pt(...A2[0]), -headH, -gd, true); edge(pt(...A2[N]), pt(...A1[0]), -headH, -gd, true)                                     // 홈 아래 둘레(곧은 변)
  for (const s of [-1, 1]) { // 홈 바닥(둘레까지)
    const a = s > 0 ? [[gx, -gw], [xr, -gw], [xr, gw], [gx, gw]] : [[-xr, gw], [-gx, gw], [-gx, -gw], [-xr, -gw]]
    const q = a.map(([x, z]) => pt(x, z)); quad(P(q[0][0], -gd, q[0][1]), P(q[1][0], -gd, q[1][1]), P(q[2][0], -gd, q[2][1]), P(q[3][0], -gd, q[3][1]), 0, 1, 0)
  }
  ringFace(kit, Tp, [], 0, 1)                                                                  // 머리 윗면
  ringFace(kit, Bp, [Array.from({ length: seg }, (_, k) => pt(shaftR * Math.cos((2 * Math.PI * k) / seg), shaftR * Math.sin((2 * Math.PI * k) / seg)))], -headH, -1) // 머리 아랫면(원통 자리 뚫림)
  // 가운데 원통: 속이 빈 관(바깥 shaftR·안쪽 innerR, 사용자 지시 2026-10-29 "원통 중심이 비어 있어야 한다"). 위쪽 40% 는 통관, 아래쪽 60% 는 가운데 틈(폭 2×slot)으로 갈라진 두 ㄷ자 기둥(스냅핏처럼 두 다리가 오므려진다).
  const yS = yShaft + 0.6 * (-headH - yShaft)   // 틈 윗끝
  cyl(shaftR, yS, -headH)                       // 바깥 벽
  for (let k = 0; k < seg; k++) { const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2, p0 = R(innerR * Math.cos(a0), innerR * Math.sin(a0)), p1 = R(innerR * Math.cos(a1), innerR * Math.sin(a1)), n = nr(Math.cos(am), Math.sin(am)); quad(P(p0[0], yS, p0[1]), P(p1[0], yS, p1[1]), P(p1[0], -headH, p1[1]), P(p0[0], -headH, p0[1]), -n[0], 0, -n[1]) }   // 안쪽 벽(구멍 쪽을 향함)
  disc(innerR, -headH, -1)                      // 속 빈 곳의 천장(머리 아래)
  { // 관 아랫면(고리): 틈에서 갈라지는 높이
    for (let k = 0; k < seg; k++) { const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg; const o0 = R(shaftR * Math.cos(a0), shaftR * Math.sin(a0)), o1 = R(shaftR * Math.cos(a1), shaftR * Math.sin(a1)), i0 = R(innerR * Math.cos(a0), innerR * Math.sin(a0)), i1 = R(innerR * Math.cos(a1), innerR * Math.sin(a1)); quad(P(i0[0], yS, i0[1]), P(o0[0], yS, o0[1]), P(o1[0], yS, o1[1]), P(i1[0], yS, i1[1]), 0, -1, 0) }
  }
  const aD = Math.acos(slot / shaftR), bI = Math.acos(slot / innerR), nD = 12
  for (const s of [-1, 1]) {
    const pts = []
    for (let i = 0; i <= nD; i++) { const an = -aD + ((2 * aD) * i) / nD; pts.push([s * shaftR * Math.cos(an), shaftR * Math.sin(an)]) } // 바깥 호
    for (let i = 0; i <= nD; i++) { const an = bI - ((2 * bI) * i) / nD; pts.push([s * innerR * Math.cos(an), innerR * Math.sin(an)]) }    // 안쪽 호(반대 방향)
    const ring = (s > 0 ? pts : pts.slice().reverse()).map(([x, z]) => R(x, z))
    for (let i = 0; i < ring.length; i++) { const p0 = ring[i], p1 = ring[(i + 1) % ring.length], ex = p1[0] - p0[0], ez = p1[1] - p0[1]; quad(P(p0[0], yShaft, p0[1]), P(p1[0], yShaft, p1[1]), P(p1[0], yS, p1[1]), P(p0[0], yS, p0[1]), ez, 0, -ex) }
    ringFace(kit, ring, [], yS, 1); ringFace(kit, ring, [], yShaft, -1)
  }
  // 발: 높이 = 머리 두께 1.5, 평면은 모서리를 둥글게 깎은 직사각형(돌려야 하므로 부드럽게, 사용자 지시 2026-10-29). 길이는 그대로(바깥으로 ±3.5, 머리 반지름 3.6 안).
  for (const s of [-1, 1]) {
    const x0 = s > 0 ? shaftR - 0.4 : -footX, x1 = s > 0 ? footX : -(shaftR - 0.4) // 관 바깥면에 0.4 파묻혀 붙는다
    const raw = [[x1, -footW], [x1, footW], [x0, footW], [x0, -footW]]
    const ring = roundPoly(raw, 0.5, 4, 25).map(([x, z]) => R(x, z))
    for (let i = 0; i < ring.length; i++) { const p0 = ring[i], p1 = ring[(i + 1) % ring.length], ex = p1[0] - p0[0], ez = p1[1] - p0[1]; quad(P(p0[0], -L, p0[1]), P(p1[0], -L, p1[1]), P(p1[0], -L + footH, p1[1]), P(p0[0], -L + footH, p0[1]), ez, 0, -ex) }
    ringFace(kit, ring, [], -L + footH, 1); ringFace(kit, ring, [], -L, -1)
  }
  return kit.result()
}
