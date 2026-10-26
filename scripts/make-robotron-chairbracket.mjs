// 에이스랩 체어브라켓(블랙): 22프레임(구멍 2×2, 20×20 두께 5)부터 그린다(사용자 2026-10-27 "체어브라켓 만들자, 22프레임 그려줘"). 그 +x 가장자리 바깥에 12프레임(구멍 1×2, 폭 10·길이 20 + 5 = 25·두께 5)을 세워 붙여 가로 25·세로 20·높이 25 가 된다("12프레임 붙일꺼야 +5mm => 총 25mm 세워서", "25 , 20 , 높이 25가 되는거야"). 오른쪽 아래(세운 프레임 바깥면과 바닥이 만나는 모서리)는 반지름 5 로 ")" 처럼 둥글게 한다("오른쪽 아래를 ) 부드럽게", "두개가 한부품으로 보이게"). 안쪽 모서리에 덩어리를 채우지 않는다(구멍을 막는다 — 사용자 지적). 나머지 모양은 정해지면 추가.
//   node scripts/make-robotron-chairbracket.mjs [--write] [--name=체어브라켓]
import fs from 'node:fs'
import { acelabFrame, ACELAB_FRAME_STD as S } from '../app/lib/acelab-frame-mesh.js'
import { createFrameGenerator } from '../app/lib/robotron-frame-mesh.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { conformTJunctions, checkMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블랙: '#555555' }
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '체어브라켓'
const NX = 2, NZ = 2 // 22프레임: 구멍 2×2
const T = S.thickness
const L12 = 25 // 12프레임 + 5mm = 길이 25(사용자 2026-10-27 "12프레임 붙일꺼야 +5mm => 총 25mm"), 구멍은 "홀과 홀사이에 똑같은 홀 하나더"로 높이 10·15·20 세 개이고, 세운 프레임 구멍 지름 약 5, 높이 10·15·20
const UR = S.boreR // 세운 프레임 구멍 반지름 = 홀 규격(지름 5.2). 구멍 간격 5 < 지름 5.2 라 이웃 구멍이 겹쳐 한 덩어리로 이어진다(홀 사이 벽 없어도 됨 — 사용자 2026-10-27)
const f12 = createFrameGenerator({ ...S, boreR: UR }).slot(L12, [-2.5, 2.5, 7.5]) // 세운 프레임: 길이 x 25 · 두께 y 5 · 폭 z 10, 구멍 3개를 주머니 하나에 뚫음
const stand = (x, y, z) => [NX * S.pitch / 2 + y, x + L12 / 2, -z] // 세운다(180° 회전이라 면 방향 유지): 길이는 y 0~25(바닥을 22프레임 바닥과 맞춤, 늘어난 5 가 아래), 두께는 22프레임 +x 가장자리 바깥 x 10~15, 구멍 홈 있는 윗면(y=5)이 바깥(+x)을 본다(사용자 2026-10-27 "아래꺼와 같은 스타일로")
const f12t = new Float32Array(f12.tris.length); for (let i = 0; i < f12.tris.length; i += 3) f12t.set(stand(f12.tris[i], f12.tris[i + 1], f12.tris[i + 2]), i)
// 오른쪽 아래 둥글림: 세운 프레임의 바깥 아래 모서리(x 15, y 0)를 중심 (10, 5)·반지름 5 의 호로 굴린다. 모서리 근처 삼각형을 잘게 나눈 뒤 호 밖 점을 중심 쪽 호 위로 당긴다(바닥 y 0 이 22프레임 바닥과 x 10 에서 접선으로 이어진다).
const RC = { cx: NX * S.pitch / 2, cy: T, r: T } // 호 중심(x 10, y 5)·반지름 5
const roundCorner = (arr) => {
  let T3 = []; for (let i = 0; i < arr.length; i += 9) T3.push([[arr[i], arr[i + 1], arr[i + 2]], [arr[i + 3], arr[i + 4], arr[i + 5]], [arr[i + 6], arr[i + 7], arr[i + 8]]])
  const hit = (t) => t.some((v) => v[0] > RC.cx - 1e-6) && Math.min(...t.map((v) => v[1])) < RC.cy + 1e-6
  const len = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]), mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]
  for (let pass = 0; pass < 12; pass++) { let any = false; const out = []
    for (const t of T3) { const e = [len(t[0], t[1]), len(t[1], t[2]), len(t[2], t[0])], m = Math.max(...e)
      if (!hit(t) || m <= 1.0) { out.push(t); continue }
      any = true; const k = e.indexOf(m), a = t[k], b = t[(k + 1) % 3], c = t[(k + 2) % 3], q = mid(a, b); out.push([a, q, c], [q, b, c]) } // 가장 긴 변을 반으로 나눈다(감는 방향 유지)
    T3 = out; if (!any) break }
  const pull = ([x, y, z]) => { if (x >= RC.cx - 1e-9 && y <= RC.cy + 1e-9) { const dx = x - RC.cx, dy = y - RC.cy, d = Math.hypot(dx, dy); if (d > RC.r) { x = RC.cx + dx * RC.r / d; y = RC.cy + dy * RC.r / d } } return [x, y, z] }
  const cr = (t) => { const u = [t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2]], v = [t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2]]; return Math.hypot(u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]) }
  const moved = T3.map((t) => t.map(pull)).filter((t) => cr(t) > 1e-9) // 호 밖에서 호 위로 눌려 납작해진 삼각형은 뺀다
  return conformTJunctions(Float32Array.from(moved.flat(2)))
}
const f12r = roundCorner(f12t)
// 22프레임과 세운 12프레임을 한 모양 파일에 같이 담는다(색칠 조각으로 따로 붙이면 홈·테두리 입체가 안 보인다 — 사용자 2026-10-27 "아래 바닥 22프레임 같은 스타일이 아닌데?").
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const { tris, holes } = acelabFrame.straight(NX, NZ), both = Float32Array.from([...tris, ...f12r]), stl = trianglesToStl(both), P = S.pitch
const bb = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < f12t.length; i += 3) for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], f12t[i + c]); mx[c] = Math.max(mx[c], f12t[i + c]) } return { x: (mn[0] + mx[0]) / 2, y: mn[1], z: (mn[2] + mx[2]) / 2, h: mx[1] } })() // 뷰어가 모양 파일마다 x·z 가운데를 원점·바닥을 y=0 으로 옮기므로 원래 자리로 되돌릴 값
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const spec = { pitch: P, margin: S.margin, thickness: S.thickness, boreRadius: S.boreR, maxHolesPerArm: NX,
    shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_에이스랩.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }], holeCoords: [], holeLabels: [] }
  const hs = []
  for (let i = 0; i < NX; i++) for (let k = 0; k < NZ; k++) { hs.push({ id: 'h' + (hs.length + 1), pos: [i * P - ((NX - 1) * P) / 2, 0, k * P - ((NZ - 1) * P) / 2], dir: [0, -1, 0], len: S.thickness, r: S.boreR, through: true }) }
  f12.holes.forEach((q) => { const p = stand(q.x, 0, q.z); hs.push({ id: 'h' + (hs.length + 1), pos: p.map((v) => +v.toFixed(3)), dir: [1, 0, 0], len: T, r: UR, through: true }) }) // 세운 12프레임 구멍 2개(두께 x 방향)
  const worst = Math.max(...holes.map((q, j) => Math.hypot(q.x - hs[j].pos[0], q.z - hs[j].pos[2])))
  const connectors = { note: `${NAME}(22프레임 20×20 두께 ${S.thickness} 한쪽(+x) 가장자리 바깥에 12프레임을 세워 붙임, 총 높이 ${bb.h}). 구멍이 두께(y) 방향으로 10mm 격자. through=true 면 양쪽에서 끼울 수 있다.`, pegs: [], size: [NX * P + T, bb.h, NZ * P], holes: hs, confidence: 'draft' }
  const data = { ...r.data, size: `${NX * P + T}×${NZ * P}×${bb.h}mm (에이스랩: 22프레임(구멍 ${NX}×${NZ}, ${P}mm 피치, 홀 규격사이즈 ${S.boreR * 2}) 한쪽 가장자리 바깥에 12프레임(구멍 1×2)을 세워 붙임, 총 높이 ${bb.h})`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  console.log(NAME, r.data.color, hex, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024), JSON.stringify(checkMesh(tris)), '12프레임 높이', bb.h, JSON.stringify(checkMesh(f12r)), '구멍', hs.length, '위치차', worst.toFixed(3))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
