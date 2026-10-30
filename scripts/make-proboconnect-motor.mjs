// 프로보 커넥트 모터블럭(DC모터) STL 만들기 + 부품 행에 등록.
//   node scripts/make-proboconnect-motor.mjs <저장 폴더> [--write]
// 사용자 지시(2026-10-30, 단계별로 하나씩): "모터 만들자 30, 50, 두께 40" / "원통을 세우라" / 앞부분은 지름 30 원통 /
//   "원통의 위아래 5mm씩 1X3블럭 홀이 45도 간격으로 돌아가면서 있음, 중심을 축으로 중심은 홀이 아니고 그냥 나사가 박혀있음" / "위아래 둘 중 윗부분은 불투명 옐로".
// 현재 모양: 뒤 네모 가로 30 × 앞뒤 35(원통 중심선까지, 원통을 감싸는 둥근 홈) × 높이 40 + 앞 세운 원통 지름 30 × 높이 40(중심 z 10) → 전체 30 × 50 × 40.
//   원통 아래 5mm(y 0~5)는 그레이, 위 5mm(y 35~40)는 옐로(뷰어에 투명도가 없어 "불투명"만 표현). 두 띠에 각각 프로보 블럭 구멍(PROBO_STD) 8개를 45° 간격으로.
// ⚠ 추정: 구멍 둘레 반지름 10.5 (45° 8개가 겹치지 않는 최소 ≈10.3, 원통 반지름 15 안쪽). 나사는 지름 4.4 검정 원기둥(띠 두께 5 전체, 홈 없음).
// 좌표: 가로 x, 높이 y(바닥 0), 앞뒤 z(앞이 +z). 원통 중심 (0, 10).
import fs from 'node:fs'
import path from 'node:path'
import Module from 'manifold-3d'
import { PROBO_STD, openPts, roundPoly } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl, makeKit } from '../app/lib/cubo-mesh-kit.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

// 모터 종류 — 모양은 모두 같고 윗띠 색만 다르다(사용자 2026-10-30 "옐로부분 => 레드(서보모터), 블루(고속모터블록)", DC모터는 옐로). 아랫띠는 모두 밝은 그레이.
// 홈 안의 핀 개수: DC모터·고속모터 2개, 서보모터 3개(사용자 2026-10-30 "서보모터는 3핀으로 수정해야해").
const KINDS = { DC모터: { row: 'DC모터', color: '#f2d21b', label: '옐로', pins: 2 }, 서보모터: { row: '서보모터', color: '#d62828', label: '레드', pins: 3 }, 고속모터: { row: '고속모터', color: '#1e50b4', label: '블루', pins: 2 } }
const kindArg = process.argv[3] && !process.argv[3].startsWith('--') ? process.argv[3] : 'DC모터', K = KINDS[kindArg]
const dir = process.argv[2], write = process.argv.includes('--write')
if (!dir || !K) { console.error('사용: node scripts/make-proboconnect-motor.mjs <저장 폴더> [DC모터|서보모터|고속모터] [--write]'); process.exit(1) }
fs.mkdirSync(dir, { recursive: true })
const S = PROBO_STD, W = 30, H = 40, BAND = S.thick, CZ = 10, RING = 10.5, SCREW_R = 2.2
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const toArr = (mf) => { const m = mf.getMesh(), t = new Float32Array(m.triVerts.length * 3); for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) t[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]; return t }
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const extrude = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])   // 2D y → −z
const box = (x0, x1, y0, y1, z0, z1) => M.cube([x1 - x0, y1 - y0, z1 - z0], false).translate([x0, y0, z0])
const cylY = (x, z, y0, y1, r) => M.cylinder(y1 - y0, r, r, 64, false).rotate([-90, 0, 0]).translate([x, y0, z])
// 구멍 1개 = 커넥트 리벳이 결합하는 규격 홀(사용자 "커넥트 리벳들 결합하는 홀이 아니고 그냥 홀을 뚫어놨잖아"): 프로보 블럭의 보통 홀(톱니 없음) 구조 그대로 —
//   바깥 둥근 입구(지름 7.9) + 가운데 띠 층(턱, 가운데만 openPts 모양으로 뚫림) + 안쪽 둥근 입구. make-proboconnect-triangle.mjs 의 PLAIN 구멍과 같은 구조.
//   바깥면 기준 깊이는 같게: 아래 띠(바깥면 y 0)는 y 0→5, 위 띠(바깥면 y 40)는 y 40→35 쪽으로 판다. 띠 층 = 바깥면에서 barY0~barY1.
const hole = (x, z, y0) => {
  const bot = y0 === 0, c2 = [x, -z], band = ccw(roundPoly(openPts(c2[0], c2[1], S), S.round)), E = 0.01
  return bot
    ? M.union([cylY(x, z, -1, S.barY0 + E, S.boreR), extrude(band, S.barY0 - E, S.barY1 + E), cylY(x, z, S.barY1 - E, BAND, S.boreR)])
    : M.union([cylY(x, z, H - S.barY0 - E, H + 1, S.boreR), extrude(band, H - S.barY1 - E, H - S.barY0 + E), cylY(x, z, H - BAND, H - S.barY1 + E, S.boreR)])
}
const ring = (y0) => M.union(Array.from({ length: 8 }, (_, k) => { const a = (k * Math.PI) / 4; return hole(RING * Math.cos(a), CZ + RING * Math.sin(a), y0) }))
// 그레이: 뒤 네모 + 원통 가운데(y 0~35), 아래 띠 구멍 8개, 아래 나사 자리(홈)
// 사용자 "아래 사각 기둥이 위 원기둥을 감싸준 모양, 틈 거의 없음 — 모터가 돌아가는 틈만": 사각 기둥(앞뒤 −25~10, 원통 중심선까지)에 원통을 감싸는 둥근 홈(반지름 15.3, 틈 0.3)을 판다.
const GAP = 0.3, dz = Math.sqrt((W / 2 + GAP) ** 2 - (W / 2) ** 2)   // dz = 홈과 기둥 옆면이 만나는 점의 중심선에서의 거리
let low = M.union([M.difference(box(-W / 2, W / 2, 0, H, -25, CZ), cylY(0, CZ, -1, H + 1, W / 2 + GAP)), cylY(0, CZ, BAND, H - BAND, W / 2)])   // 원통 가운데(y 5~35)만 몸통 — 아래 5mm 띠는 돌아가는 부분이라 따로(밝은 그레이)
// 뒷면(−z, 구멍 없는 평평한 면) 돌기(사용자 2026-10-30 "중심에 아래에서 6mm 위쪽에 5, 10, 높이 16짜리 직사각 기둥을 만들어서 붙여줘"): 가로 가운데 폭 10(x −5~5) × 뒤로 5 튀어나옴(z −30~−25) × 높이 16(y 6~22).
low = M.union([low, box(-5, 5, 6, 22, -25 - 5, -25)])
// 돌기 윗면에서 아래로 2단핀 홈(사용자 2026-10-30 "위에서 아래방향으로 끼울 수 있게 홈을 파 2단핀을 꽂을 수 있게", "커넥트 센서 3핀 소켓 참고"): 센서 소켓 폭 8 그대로(x −4~4), 깊이 = 2단핀 길이 10(y 12~22).
//   돌기 두께(5)가 핀 몸통(지름 5.2)보다 얇아서 뒤(−z)로 열린 홈으로 판다 — 몸통 벽(z −25)은 그대로 둔다. 센서처럼 홈이 한 색으로 칠해지니 짙은 바닥판·입구 띠를 색칠 조각으로 따로 얹는다.
//   (사용자 "다 뚫어버리면 어떻게 해" → 사방에 벽을 남기는 막힌 홈: 센서 소켓처럼 폭 8 × 두께 4, 돌기 두께 5 가운데라 앞뒤 벽 0.5·양옆 벽 1.)
const GROOVE = { w: 8, t: 4, d: 10, top: 22, z0: -30, z1: -25 }, GZ0 = (GROOVE.z0 + GROOVE.z1) / 2 - GROOVE.t / 2, GZ1 = GZ0 + GROOVE.t
low = M.difference(low, box(-GROOVE.w / 2, GROOVE.w / 2, GROOVE.top - GROOVE.d, GROOVE.top + 1, GZ0, GZ1))
// 직사각 기둥(가로 30 × 앞뒤 20) 위·아래 5mm 에는 2X3블럭 홀(사용자 "직사각 기둥 위아래 부분 5mm 에는 2X3블록 홀이 파여있음"): 가로 3 × 앞뒤 2, 간격 10 → 구멍 6개씩
const boxHoles = (y0) => M.union([-10, 0, 10].flatMap((x) => [-20, -10].map((z) => hole(x, z, y0))))
// 양 옆면(±x) 가운데 1X3 홀(사용자 "양 옆면의 위아래·좌우 중심에 1X3 홀 만들어줘" → "위아래로 파는 게 아니고 좌우로 파야 해"): 옆면의 가운데(전체 앞뒤 50 의 가운데 z 0, 높이 가운데 y 20)에 가로(앞뒤 방향)로 3개(z −10·0·10, 간격 10). 같은 규격 홀을 옆으로 눕혀 판다(바깥면 = 옆면).
//   시킨 그대로 3개 모두 온전하게 판다(앞 홀 z 1 은 원통 홈과 가까워 안쪽 끝이 틈과 이어질 수 있다).
const SIDE_Z = 0   // 사용자 "전체가 50이니까 그냥 시킨 대로 1X3 홀을 파라고": 전체 앞뒤 50(−25~25)의 가운데 z 0 기준
const sideHoles = [-1, 1].flatMap((sg) => [-10, 0, 10].map((dzz) => hole(0, 0, 0).rotate([0, 0, sg > 0 ? 90 : -90]).translate([sg * W / 2, 20, SIDE_Z + dzz])))
low = M.difference(low, M.union([boxHoles(0), boxHoles(H - BAND), ...sideHoles]))
// 아래 5mm 띠(사용자 2026-10-30 "옐로 아래 바닥쪽 5mm도 분리하고 밝은 그레이로, 옐로와 밝은 그레이 부분만 돌아가는 부분"): 옐로 윗띠와 같은 구조(구멍 8개 + 가운데 나사 자리), 색칠 조각.
const lowerBand = M.difference(M.difference(cylY(0, CZ, 0, BAND, W / 2), ring(0)), cylY(0, CZ, -1, BAND + 1, SCREW_R))   // 아래 나사 자리(띠 두께 전체)
// 옐로: 원통 위 5mm(y 35~40), 구멍 8개
const yel = M.difference(M.difference(cylY(0, CZ, H - BAND, H, W / 2), ring(H - BAND)), cylY(0, CZ, H - BAND - 1, H + 1, SCREW_R))   // 위 나사 자리
// 검정 나사(사용자 "중심에 검정나사 박혀있다고 했잖아"): 띠 두께 전체를 채워 윗면·아랫면과 같은 높이로 박혀 있다.
const screwTop = cylY(0, CZ, H - BAND, H, SCREW_R), screwBot = cylY(0, CZ, 0, BAND, SCREW_R)
// 옐로 윗면 테두리 선(사용자 "불투명 옐로엔 테두리 넣어주고"): 바깥 원 + 구멍 8개 입구(둥근 구멍) + 나사 둘레를 0.1mm 선으로(make-proboconnect-sensor.mjs 와 같은 가는 막대)
const LT = LINE_THICKNESS / 2, lineKit = makeKit(24), grayKit = makeKit(24)
let cur = lineKit
const bar = (a, b) => {
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
  const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
  const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
  let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => (c / ul) * LT); const v = cr(e, u).map((c) => c / LT * LT)
  const s0 = a.map((c, i) => c - e[i] * LT), s1 = b.map((c, i) => c + e[i] * LT)
  const corner = (q, su, sv) => q.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
  const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
  const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
  for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); cur.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
}
const ring3 = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
const circ = (cx, cz, r, n = 64) => Array.from({ length: n }, (_, i) => [cx + r * Math.cos((2 * Math.PI * i) / n), cz + r * Math.sin((2 * Math.PI * i) / n)])
const LY = H + 0.03
ring3(circ(0, CZ, W / 2), LY); ring3(circ(0, CZ, SCREW_R, 32), LY)
for (let k = 0; k < 8; k++) { const a = (k * Math.PI) / 4, x = RING * Math.cos(a), z = CZ + RING * Math.sin(a); ring3(circ(x, z, S.boreR, 32), LY)
  // 구멍 안 홈(사용자 "홀 안 부분에 홈들이 안 보인다는 건데, 옐로 부분"): 뷰어는 색칠 조각에는 모서리 선을 안 그려서 노란 구멍 안쪽 홈이 한 색으로 뭉개진다 → 띠 층 위·아래 둘레와 홈 모양(openPts)을 선으로 긋는다.
  const slot = roundPoly(openPts(x, -z, S), S.round).map(([px, py]) => [px, -py])
  for (const yy of [H - S.barY0, H - S.barY1]) { ring3(circ(x, z, S.boreR, 32), yy); ring3(slot, yy) }
}   // 2D y → −z
const linesT = lineKit.result()
// 그레이 사각 기둥 윗면 선(사용자 "라인을 안 그려놔서 안 보이네"): 기둥 윗면 윤곽(원통을 감싸는 둥근 홈 포함) + 2X3 구멍 입구 6개. 어두운 그레이라 선은 밝게(lineColorFor).
cur = grayKit
const a0 = Math.atan2(-dz, W / 2), a1 = Math.atan2(-dz, -W / 2) + 2 * Math.PI   // 홈과 기둥 옆면이 만나는 각(−11.3°, 191.3°→ 뒤쪽 −90° 를 지나 −168.7°)
const arc = Array.from({ length: 41 }, (_, i) => { const a = a0 - ((a0 - (Math.atan2(-dz, -W / 2) - 2 * Math.PI * (Math.atan2(-dz, -W / 2) > 0 ? 1 : 0))) * i) / 40; return [(W / 2 + GAP) * Math.cos(a), CZ + (W / 2 + GAP) * Math.sin(a)] })
ring3([[-W / 2, -25], [W / 2, -25], [W / 2, CZ - dz], ...arc.slice(1, -1), [-W / 2, CZ - dz]], LY)
for (const x of [-10, 0, 10]) for (const z of [-20, -10]) ring3(circ(x, z, S.boreR, 32), LY)
const grayLinesT = grayKit.result()
const gb = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < grayLinesT.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], grayLinesT[i + k]); mx[k] = Math.max(mx[k], grayLinesT[i + k]) } return { x: (mn[0] + mx[0]) / 2, y: mn[1], z: (mn[2] + mx[2]) / 2 } })()
const lb = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < linesT.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], linesT[i + k]); mx[k] = Math.max(mx[k], linesT[i + k]) } return { x: (mn[0] + mx[0]) / 2, y: mn[1], z: (mn[2] + mx[2]) / 2 } })()
const at = (mf) => { const b = mf.boundingBox(); return { x: (b.min[0] + b.max[0]) / 2, y: b.min[1], z: (b.min[2] + b.max[2]) / 2 } }
// 핀 홈 표시(센서 소켓 표시와 같은 방식, T 0.2·R 0.6): 안쪽 바닥판 + 입구 띠(홈 양옆, 윗면에서 0.2 올라온다). 몸통이 #555555 라 더 짙은 색.
const GT = 0.2, GR = 0.6, GHW = GROOVE.w / 2
const grooveDark = M.union([box(-GHW, GHW, GROOVE.top - GROOVE.d, GROOVE.top - GROOVE.d + GT, GZ0, GZ1),   // 안쪽 바닥판
  box(-GHW - GR, -GHW, GROOVE.top, GROOVE.top + GT, GROOVE.z0, GROOVE.z1), box(GHW, GHW + GR, GROOVE.top, GROOVE.top + GT, GROOVE.z0, GROOVE.z1),   // 입구 띠: 양옆
  box(-GHW, GHW, GROOVE.top, GROOVE.top + GT, GROOVE.z0, GZ0), box(-GHW, GHW, GROOVE.top, GROOVE.top + GT, GZ1, GROOVE.z1)])   // 앞뒤(벽 두께만큼)
// 홈 안의 금색 핀 2개(사용자 "핀두개는 어디갔어"): 센서 소켓 핀과 같은 값 — 지름 1(반지름 0.5)·간격 2.5, 입구에서 안쪽 바닥까지. 홈 가운데(x ±1.25).
const GPIN = { r: 0.5, pitch: 2.5 }, gzc = (GZ0 + GZ1) / 2
const grooveM = M.union(Array.from({ length: K.pins }, (_, i) => (i - (K.pins - 1) / 2) * GPIN.pitch).map((x) => cylY(x, gzc, GROOVE.top - GROOVE.d, GROOVE.top, GPIN.r)))
const pinsT = toArr(grooveM), pinsAt2 = at(grooveM)
const grooveT = toArr(grooveDark), grooveAt = at(grooveDark)
const bandT = toArr(lowerBand), bandAt = at(lowerBand)
const lowT = toArr(low), yelT = toArr(yel), stT = toArr(screwTop), sbT = toArr(screwBot)
const yelAt = at(yel), stAt = at(screwTop), sbAt = at(screwBot), lowAt = at(low)   // 몸통도 뷰어가 가운데(x·z)를 다시 맞추므로 실제 가운데 값을 위치로 준다(뒷면 돌기로 앞뒤 가운데가 −2.5 움직여 테두리 선이 어긋났다)
const report = (n, t) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < t.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], t[i + k]); mx[k] = Math.max(mx[k], t[i + k]) } console.log(`${n}: 삼각형 ${t.length / 9}개`, JSON.stringify(checkMesh(t)), '크기', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '범위 y', mn[1].toFixed(2), mx[1].toFixed(2)) }
report('그레이 몸통', lowT); report('옐로 윗띠', yelT); report('나사 위', stT); report('나사 아래', sbT); report('윗면 선', linesT); report('기둥 윗면 선', grayLinesT); report('핀 홈 표시', grooveT); report(`홈 핀 ${K.pins}개`, pinsT); report('밝은 그레이 아랫띠', bandT)
const sL = trianglesToStl(lowT), sY = trianglesToStl(yelT), sT = trianglesToStl(stT), sBt = trianglesToStl(sbT), sLn = trianglesToStl(linesT), sGl = trianglesToStl(grayLinesT), sGd = trianglesToStl(grooveT), sPn = trianglesToStl(pinsT), sBd = trianglesToStl(bandT)
for (const [n, b] of [['몸통', sL], ['윗띠', sY], ['아랫띠', sBd], ['나사위', sT], ['나사아래', sBt], ['윗면선', sLn], ['기둥윗면선', sGl], ['핀홈표시', sGd], ['홈핀2', sPn]]) fs.writeFileSync(path.join(dir, `모터블럭_${n}.stl`), b)
if (write) {
  const env = Object.fromEntries(fs.readFileSync('.env.local', 'utf8').split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
  const Hd = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`, 'Content-Type': 'application/json' }
  const rest = `${env.SUPABASE_URL}/rest/v1`
  const cat = (await (await fetch(`${rest}/ivs_robot_categories?select=id,data`, { headers: Hd })).json()).find((c) => c.data.name === '프로보 커넥트')
  const rows = await (await fetch(`${rest}/ivs_part_catalog?select=id,data&data->>category=eq.${cat.id}&data->>name=eq.${encodeURIComponent(K.row)}`, { headers: Hd })).json()
  if (rows.length !== 1) { console.log(`"${K.row}" 행이 ${rows.length}개 → 멈춤`); process.exit(1) }
  const row = rows[0]
  // 뷰어는 STL 마다 x·z 가운데를 0 으로 당겨 놓고 위치값만큼 옮긴다. 색칠 조각(paint)은 몸통(첫 도형)의 위치를 물려받으므로 몸통은 위치 0 으로 두고,
  //   몸통이 가운데로 당겨진 만큼(lowAt) 색칠 조각을 같이 옮겨야 선·띠가 몸통과 맞는다(뒷면 돌기로 몸통 앞뒤 가운데가 −2.5 움직였을 때 선이 어긋났다).
  const imp = (b, name, color, y, paint, x = 0, z = 0) => ({ x: x - (paint ? lowAt.x : 0), y, z: z - (paint ? lowAt.z : 0), op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, ...(paint ? { paint: true } : {}), fileName: name, brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64') })
  const shapes = [imp(sL, '모터블럭_몸통.stl', '#555555', 0, false), imp(sY, '모터블럭_윗띠.stl', K.color, yelAt.y, true, yelAt.x, yelAt.z), imp(sT, '모터블럭_나사위.stl', '#1c1c1c', stAt.y, true, stAt.x, stAt.z), imp(sBt, '모터블럭_나사아래.stl', '#1c1c1c', sbAt.y, true, sbAt.x, sbAt.z), imp(sLn, '모터블럭_윗면선.stl', lineColorFor(K.color), lb.y, true, lb.x, lb.z), imp(sGl, '모터블럭_기둥윗면선.stl', lineColorFor('#555555'), gb.y, true, gb.x, gb.z), imp(sBd, '모터블럭_아랫띠.stl', '#c8c8c8', bandAt.y, true, bandAt.x, bandAt.z), imp(sGd, '모터블럭_핀홈표시.stl', '#2b2b2b', grooveAt.y, true, grooveAt.x, grooveAt.z), imp(sPn, '모터블럭_홈핀2.stl', '#d4af37', pinsAt2.y, true, pinsAt2.x, pinsAt2.z)]
  const data = { ...row.data, size: `가로 30 × 앞뒤 50 × 높이 40mm (뒤 네모 + 앞 세운 지름 30 원통, 원통 위(${K.label})·아래 5mm 띠에 구멍 8개씩 45° + 가운데 검정 나사, 윗면 테두리 선, 직사각 기둥이 원통을 감싼다(틈 0.3) + 위·아래 2X3 배열 리벳 결합 규격 홀 6개씩(톱니 없음, 가운데 띠 있음), 12단계)`, spec: { ...(row.data.spec || {}), pitch: 10, margin: 5, shapes }, thumbnail3d: null }
  const r = await fetch(`${rest}/ivs_part_catalog?id=eq.${row.id}`, { method: 'PATCH', headers: { ...Hd, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) })
  console.log(row.data.name, '→', r.status, r.ok ? '등록됨 id ' + row.id : await r.text())
  for (const s of shapes) console.log('  ', s.fileName, 'fileDataUrl 길이', s.fileDataUrl.length)
}
