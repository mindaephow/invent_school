// 프로보 커넥트 "바퀴" 부품 등록 = 휠블럭 + 타이어를 합친 것 (사용자 2026-10-30 "바퀴를 하나 등록해서 휠블록과 타이어를 합친 것을 하나 추가해줘").
//   node scripts/add-proboconnect-wheel-assembly.mjs   (휠블럭.stl·타이어.stl 을 먼저 make-proboconnect-wheel.mjs·make-proboconnect-tire.mjs 로 만들어 둔다)
// 모양: 휠블럭(흰색, 몸통) + 타이어(블랙 #555555, 색칠 조각). 두 STL 모두 가운데가 x·z 원점, 바닥 y 0 이라 위치 0 그대로 겹친다 —
//   타이어 입구 지름 46 = 휠블럭 가운데 원기둥(지름 46 × 높이 24), 타이어 안쪽 홈(지름 50 × 높이 20) = 휠블럭 몸통(지름 50 × 높이 20, y 2~22)이라 그대로 끼워진다.
// 새 행: 프로보 커넥트(권 미배정 = 키트 목록에 없는 조립품). 이미 같은 이름 행이 있으면 모양만 다시 넣는다.
import fs from 'node:fs'
import { lineColorFor } from '../app/lib/robotron-line-color.js'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = `${env.SUPABASE_URL}/rest/v1/ivs_part_catalog`
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b' // 프로보 커넥트
const NAME = '바퀴', SIZE = '지름 53 × 높이 25mm (휠블럭 + 타이어)'
const imp = (file, fileName, color, paint, at = { x: 0, y: 0, z: 0 }) => ({ x: at.x, y: at.y, z: at.z, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, ...(paint ? { paint: true } : {}), fileName, brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + fs.readFileSync(file).toString('base64') })
const shapes = [imp('프로보커넥트_블럭/휠블럭.stl', '바퀴_휠블럭.stl', '#ffffff', false), imp('프로보커넥트_블럭/타이어.stl', '바퀴_타이어.stl', '#555555', true),
  // 타이어 바깥 홈 가장자리 선(색칠 조각은 뷰어가 모서리 선을 안 그려 홈이 안 보인다 — 사용자 "옆에 아무것도 안 보인다고"). 위치는 make-proboconnect-tire.mjs 가 적어 둔 값.
  imp('프로보커넥트_블럭/타이어_선.stl', '바퀴_타이어선.stl', lineColorFor('#555555'), true, JSON.parse(fs.readFileSync('프로보커넥트_블럭/타이어_선.json', 'utf8')))]
const exist = await (await fetch(`${rest}?select=id,data&data->>category=eq.${CAT}&data->>name=eq.${encodeURIComponent(NAME)}`, { headers: H })).json()
if (!Array.isArray(exist)) { console.log('조회 실패', JSON.stringify(exist).slice(0, 200)); process.exit(1) }
if (exist.length > 1) { console.log(`"${NAME}" 행이 ${exist.length}개 → 멈춤`); process.exit(1) }
if (exist.length === 1) {
  const row = exist[0], data = { ...row.data, size: SIZE, spec: { ...(row.data.spec || {}), pitch: 10, margin: 5, shapes }, thumbnail3d: null }
  const r = await fetch(`${rest}?id=eq.${row.id}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) })
  console.log(NAME, '→', r.status, r.ok ? '다시 등록됨 id ' + row.id : await r.text())
} else {
  const data = { name: NAME, icon: '', subject: 'robot', category: CAT, volumes: [], color: null, size: SIZE, createdAt: Date.now(), spec: { pitch: 10, margin: 5, shapes } }
  const r = await fetch(rest, { method: 'POST', headers: { ...H, Prefer: 'return=representation' }, body: JSON.stringify({ data }) })
  const j = await r.json().catch(() => null)
  console.log(NAME, '→', r.status, r.ok ? '새로 등록됨 id ' + (j && j[0] && j[0].id) : JSON.stringify(j))
}
