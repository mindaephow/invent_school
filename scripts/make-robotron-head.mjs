// 에이스랩 머리(스카이블루): 12프레임(구멍 1×2, 폭 10·길이 20)을 두께 10 으로 만든다(사용자 2026-10-27 "머리 만들자, 12프레임 두께 10mm, 위아래 1mm 홈파줘"). 프레임 칸 주머니(위·아래 깊이 1 홈)가 그대로 위아래 1mm 홈이 되고 구멍은 두께 10 을 지나 뚫린다. 그 −z 쪽 긴 옆면에 11프레임(구멍 1개, 10×10×5)을 세워 붙이고 y 축으로 90° 돌린다("스샷 윗부분에 11프레임을 세워서 붙일꺼야", "붙이라고", "-X쪽을 말하는거야"): 높이 10 은 머리 위·아래와 맞추고, 돌린 뒤 폭 10 이 z −5~−15 로 뒤로 뻗고 두께 5 는 x ±2.5(두 구멍 사이 가운데)이다. 나머지 모양은 정해지면 추가.
//   node scripts/make-robotron-head.mjs [--write] [--name=머리]
import fs from 'node:fs'
import { ACELAB_FRAME_STD as S0 } from '../app/lib/acelab-frame-mesh.js'
import { createFrameGenerator } from '../app/lib/robotron-frame-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 스카이블루: '#82d0f8' }
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '머리'
const T = 10, NX = 2, NZ = 1, P = S0.pitch // 두께 10, 12프레임: 길이 구멍 2 · 폭 구멍 1
const S = { ...S0, thickness: T }
const { tris: headTris, holes } = createFrameGenerator(S).straight(NX, NZ)
const f11 = createFrameGenerator(S0).straight(1, 1) // 11프레임: 10×10×5, 구멍 1개(두께 5 짜리 프레임 규격)
const stand = (x, y, z) => [S0.thickness / 2 - y, x + 5, -NZ * P / 2 - NZ * P / 2 + z] // 11프레임을 −z 쪽 긴 옆면에 세우고 y 축으로 90° 돌린 자리(사용자 2026-10-27 "-Z쪽이야 미안", "11프레임을 90도 돌려줘 (y축으로)"): 두께 y → x ±2.5(머리 가운데 두 구멍 사이, 구멍 홈 있는 윗면이 −x), 폭 z → z −15~−5(머리 뒤쪽 면 z −5 에 맞닿아 뒤로 뻗음), 길이 x → 높이 y 0~10
const f11t = new Float32Array(f11.tris.length); for (let i = 0; i < f11.tris.length; i += 3) f11t.set(stand(f11.tris[i], f11.tris[i + 1], f11.tris[i + 2]), i)
const tris = Float32Array.from([...headTris, ...f11t]), stl = trianglesToStl(tris)
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const spec = { pitch: P, margin: S.margin, thickness: T, boreRadius: S.boreR, maxHolesPerArm: NX,
    shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_에이스랩.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }], holeCoords: [], holeLabels: [] }
  const hs = holes.map((q, j) => ({ id: 'h' + (j + 1), pos: [+q.x.toFixed(3), 0, +q.z.toFixed(3)], dir: [0, -1, 0], len: T, r: S.boreR, through: true }))
  f11.holes.forEach((q) => { const p = stand(q.x, 0, q.z); hs.push({ id: 'h' + (hs.length + 1), pos: p.map((v) => +v.toFixed(3)), dir: [-1, 0, 0], len: S0.thickness, r: S.boreR, through: true }) }) // 세운 11프레임 구멍(두께 x 방향)
  const worst = Math.max(...holes.map((q, j) => Math.hypot(q.x - hs[j].pos[0], q.z - hs[j].pos[2])))
  const connectors = { note: `${NAME}(12프레임 두께 ${T} + −z 쪽 옆면에 11프레임을 세워 붙임). 구멍은 두께(y) 방향으로 10mm 격자, 위·아래 면에 깊이 1 홈. through=true 면 양쪽에서 끼울 수 있다.`, pegs: [], size: [NX * P, T, NZ * P + NZ * P], holes: hs, confidence: 'draft' }
  const data = { ...r.data, size: `${NX * P}×${NZ * P}×${T}mm (에이스랩: 12프레임 두께 ${T}, 홀 규격사이즈 ${S.boreR * 2}, 구멍 ${NZ}×${NX}, 위·아래 면 1mm 홈) + −z 쪽 옆면에 11프레임(구멍 1개)을 세워 붙임`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  console.log(NAME, r.data.color, hex, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024), JSON.stringify(checkMesh(headTris)), JSON.stringify(checkMesh(f11t)), '구멍', hs.length, '위치차', worst.toFixed(3))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
