// 에이스랩 원판(스카이블루): 두께 3·폭 30 의 얇은 판을 가운데가 높이 15 가 되게 둥글게(원호) 올린 둥근 지붕이다. 좌우(x) 최대 길이 70(사용자 2026-10-27 "원판만들자, 두께3mm 폭30mm 얇은판을 가운데를 높이 15mm 로 올려서 지붕처럼 만들껀데 좌우최대 길이가 70mm 가 되면되", "지붕이 각이 지면안되고 이름처럼 원판이 되어야해", "둥근원판 둥근지붕이 되어야 함", "내가 사이즈 말 안했냐?"). 단면은 바깥(윗면) 원호 반지름 R = (35²+15²)/(2·15) 과 안쪽(아랫면) 반지름 R−3 의 호이고, 바닥(y 0)에서 수평으로 잘라 양 끝이 바닥에 닿는다. 높이 15 는 꼭대기 윗면까지. (지름 70 돔 버전은 make-robotron-disc-dome.mjs) 그 가운데(좌우·앞뒤 중심, x 0·z 0)에 22프레임(구멍 2×2, 20×20×5)을 세워 넣는다("이 안에 22프레임을 세운 형태로 넣어줘, 좌우 중심 앞뒤 중심에"): 폭 20 은 x, 높이 20 은 y(바닥 0~20), 두께 5 는 z ±2.5, 홈 있는 면이 앞(+z)을 본다. 구멍·모서리 둥글림은 정해지면 추가.
//   node scripts/make-robotron-disc.mjs [--write] [--name=원판]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { acelabFrame, ACELAB_FRAME_STD as FS } from '../app/lib/acelab-frame-mesh.js'
import { checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 스카이블루: '#82d0f8' }
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '원판'
const T = 3, W = 30, L = 70, HT = 15 // 두께·폭 z·좌우 최대 길이 x·전체 높이
const HX = L / 2
const TOTAL = 26, UP = TOTAL - HT // 합친 전체 높이 26 에 맞춰 판(지붕)을 올린다(사용자 2026-10-27 "지금 결합하면 23인데 26이 되어야 하니까~ 지붕을 26에 맞춰서 올리고~"): 판 양 끝은 바닥에서 UP 만큼 뜬다. 22프레임(높이 20) 윗면과 판 아랫면 사이는 채움 덩어리로 메워 붙인다("22프레임과 지붕부분을 채워서 붙여줘")
const R = (HX ** 2 + HT ** 2) / (2 * HT), CY = HT - R + UP, Ri = R - T // 바깥 반지름·호 중심 높이(중심 x 0)·안쪽 반지름
const phiO = Math.asin(HX / R), xi = Math.sqrt(Ri ** 2 - (HT - R) ** 2), phiI = Math.asin(xi / Ri) // 바깥 호 끝 각도(높이 0 에서), 안쪽 호가 바닥과 만나는 x 와 각도
const NSEG = Math.ceil((2 * phiO * 180 / Math.PI) / 1) // 1° 마다(뷰어는 1° 넘게 꺾인 모서리에 선을 그어 줄무늬가 생긴다)
const pt = (r, th) => [r * Math.sin(th), CY + r * Math.cos(th)]
const outer = Array.from({ length: NSEG + 1 }, (_, k) => pt(R, -phiO + 2 * phiO * k / NSEG)), inner = Array.from({ length: NSEG + 1 }, (_, k) => pt(Ri, -phiI + 2 * phiI * k / NSEG))
outer[0][1] = UP; outer[NSEG][1] = UP; inner[0][1] = UP; inner[NSEG][1] = UP // 끝 높이 오차 제거
const z0 = -W / 2, z1 = W / 2
const kit = makeKit(24), { quad, P } = kit
for (let k = 0; k < NSEG; k++) {
  const [o0, o1, i0, i1] = [outer[k], outer[k + 1], inner[k], inner[k + 1]], om = [(o0[0] + o1[0]) / 2, (o0[1] + o1[1]) / 2 - CY], im = [(i0[0] + i1[0]) / 2, (i0[1] + i1[1]) / 2 - CY]
  quad(P(o0[0], o0[1], z0), P(o1[0], o1[1], z0), P(o1[0], o1[1], z1), P(o0[0], o0[1], z1), om[0], om[1], 0) // 윗면(바깥을 본다)
  quad(P(i0[0], i0[1], z0), P(i1[0], i1[1], z0), P(i1[0], i1[1], z1), P(i0[0], i0[1], z1), -im[0], -im[1], 0) // 아랫면(원호 중심을 본다)
  quad(P(o0[0], o0[1], z0), P(o1[0], o1[1], z0), P(i1[0], i1[1], z0), P(i0[0], i0[1], z0), 0, 0, -1) // 앞쪽(−z) 옆면
  quad(P(o0[0], o0[1], z1), P(o1[0], o1[1], z1), P(i1[0], i1[1], z1), P(i0[0], i0[1], z1), 0, 0, 1) // 뒤쪽(+z) 옆면
}
quad(P(-HX, UP, z0), P(-xi, UP, z0), P(-xi, UP, z1), P(-HX, UP, z1), 0, -1, 0) // 왼쪽 바닥 끝면
quad(P(xi, UP, z0), P(HX, UP, z0), P(HX, UP, z1), P(xi, UP, z1), 0, -1, 0) // 오른쪽 바닥 끝면
const bodyTris = kit.result()
// 밝기 대비 테두리 선(0.1mm): 입체의 모든 모서리
const outlineBars = () => {
  const k = makeKit(24), t = LINE_THICKNESS / 2
  const bar = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const Aa = C.map(([su, sv]) => corner(s0, su, sv)), Bb = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(Aa[i], Aa[j], Bb[j], Bb[i], m[0], m[1], m[2]) } }
  const STEP = 3, thin = (arr) => arr.filter((p, i) => i % STEP === 0 || i === arr.length - 1) // 호는 3° 마디로 잇는다
  const loop = [...thin(outer), ...thin(inner).reverse()] // 바깥 호(왼→오) 다음 안쪽 호(오→왼): 닫힌 둘레
  for (const z of [z0, z1]) loop.forEach((p, i) => { const q = loop[(i + 1) % loop.length]; bar([p[0], p[1], z], [q[0], q[1], z]) }) // 앞뒤 옆면 둘레
  for (const p of [outer[0], inner[0], inner[NSEG], outer[NSEG]]) bar([p[0], p[1], z0], [p[0], p[1], z1]) // 바닥에 닿는 끝 모서리(폭 방향)
  return trianglesToStl(k.result())
}
const f22 = acelabFrame.straight(2, 2, undefined, 0, true) // 22프레임: 20×20×5, 구멍 2×2, 위쪽(+x 끝) 두 모서리는 둥글리지 않는다(채움과 빈틈 없이 이어지게 — 사용자 2026-10-27 "연결부분을 깔끔하게 연결해야지")
const stand = (x, y, z) => [z, x + 10, y - FS.thickness / 2] // 세운다(회전이라 면 방향 유지): 프레임 길이 x → 높이 y 0~20(둥글지 않은 +x 끝이 위), 폭 z → x ±10, 두께 y → z ±2.5(홈 있는 윗면이 +z)
const f22t = new Float32Array(f22.tris.length); for (let i = 0; i < f22.tris.length; i += 3) f22t.set(stand(f22.tris[i], f22.tris[i + 1], f22.tris[i + 2]), i)
// 채움(연결부): 22프레임 윗면(y 20)과 같은 단면(폭 20·두께 5, 모서리 직각)을 그대로 위로 올려 판 아랫면에 붙인다 — 프레임 옆면과 같은 평면이라 이음 표시가 없다(사용자 2026-10-27 "그냥 표시없이 연결을 하라고"). 윗면은 판 두께 안으로 1mm 파고들어(반지름 Ri+1 호) 틈이 없다.
const FX = 10, FZ = FS.thickness / 2, FY0 = 20, FN = 20, fillTop = (x) => CY + Math.sqrt((Ri + 1) ** 2 - x * x)
const fk = makeKit(24), fq = fk.quad, fP = fk.P
for (let i = 0; i < FN; i++) { const xa = -FX + 2 * FX * i / FN, xb = -FX + 2 * FX * (i + 1) / FN, ya = fillTop(xa), yb2 = fillTop(xb)
  fq(fP(xa, ya, -FZ), fP(xb, yb2, -FZ), fP(xb, yb2, FZ), fP(xa, ya, FZ), 0, 1, 0) // 윗면(판 속)
  fq(fP(xa, FY0, -FZ), fP(xb, FY0, -FZ), fP(xb, yb2, -FZ), fP(xa, ya, -FZ), 0, 0, -1) // 앞(−z) 옆면
  fq(fP(xa, FY0, FZ), fP(xb, FY0, FZ), fP(xb, yb2, FZ), fP(xa, ya, FZ), 0, 0, 1) // 뒤(+z) 옆면
  fq(fP(xa, FY0, -FZ), fP(xb, FY0, -FZ), fP(xb, FY0, FZ), fP(xa, FY0, FZ), 0, -1, 0) // 아랫면(프레임 윗면에 맞닿음)
}
fq(fP(-FX, FY0, -FZ), fP(-FX, FY0, FZ), fP(-FX, fillTop(-FX), FZ), fP(-FX, fillTop(-FX), -FZ), -1, 0, 0) // 왼쪽 끝면
fq(fP(FX, FY0, -FZ), fP(FX, FY0, FZ), fP(FX, fillTop(FX), FZ), fP(FX, fillTop(FX), -FZ), 1, 0, 0) // 오른쪽 끝면
const fillTris = fk.result()
const stl = trianglesToStl(Float32Array.from([...bodyTris, ...f22t, ...fillTris])), outlineStl = outlineBars(), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '몸통'), fileName: `${NAME}_에이스랩.stl` }, { ...mk(outlineStl, '바깥선', { paint: true, y: UP }), color: lineColorFor(hex) }] }
  const hs = f22.holes.map((q, j) => { const p = stand(q.x, 0, q.z); return { id: 'h' + (j + 1), pos: p.map((v) => +v.toFixed(3)), dir: [0, 0, 1], len: FS.thickness, r: FS.boreR, through: true } })
  const connectors = { note: `${NAME}(두께 ${T}·폭 ${W} 얇은 판을 가운데 높이 ${HT} 로 둥글게(원호) 올린 둥근 지붕, 좌우 최대 ${L}). 구멍 등은 정해지면 추가.`, pegs: [], holes: hs, size: [L, TOTAL, W], confidence: 'draft' }
  const data = { ...r.data, size: `${L}×${W}×${TOTAL}mm (에이스랩: 두께 ${T}·폭 ${W} 얇은 판을 가운데 높이 ${HT} 로 둥글게(원호, 바깥 반지름 ${R.toFixed(1)}) 올린 둥근 지붕, 좌우 최대 길이 ${L}, 밝은 테두리 선) + 가운데(좌우·앞뒤 중심)에 22프레임(20×20×5)을 세워 넣고 판을 ${UP}mm 위로 올리고 22프레임과 판 사이를 같은 단면으로 올려 표시 없이 이어 붙임(전체 높이 ${TOTAL})`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024), '반지름', R.toFixed(2), '안쪽 바닥 x', xi.toFixed(2), '분할', NSEG, '22프레임', JSON.stringify(checkMesh(f22t)), '채움', JSON.stringify(checkMesh(fillTris)))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
