// 프로보 커넥트 부품 STL 을 부품 DB(ivs_part_catalog) 행의 data.spec.shapes 에 넣는다(기존 부품과 같은 import 형식, 흰색). 다른 필드는 그대로 둔다.
// 사용(사용자가 "부품 등록은 알아서 하라"고 지시, 2026-10-29): node scripts/register-proboconnect-parts.mjs
import fs from 'node:fs'
const env = Object.fromEntries(fs.readFileSync('.env.local', 'utf8').split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`, 'Content-Type': 'application/json' }
const url = `${env.SUPABASE_URL}/rest/v1/ivs_part_catalog`
const B = '프로보커넥트_블럭/', P = '프로보커넥트_핀/'
const one = process.argv[2] ? [[process.argv[2], process.argv[3], process.argv[4], process.argv[5] || "#ffffff"]] : null   // 한 부품만: node scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기>
const parts = one || [
  ['514b68fe-09fe-4a14-8f44-d5be87af0ca9', B + '1X3블럭.stl', '30×10×5mm'], ['2f8ba1e3-0cd0-45a4-b9a9-b169f87e64b6', B + '1X5블럭.stl', '50×10×5mm'],
  ['b4dfc539-caa6-4977-bba7-1c0c7b16230a', B + '1X7블럭.stl', '70×10×5mm'], ['423ec239-187f-49af-90c3-1b9276ac196a', B + '1X9블럭.stl', '90×10×5mm'],
  ['55ef7186-f1d1-4c8f-855f-b269f7ee19b4', B + '2X5블럭.stl', '50×20×5mm'], ['1252b5ee-06fd-4a2a-b87e-ec19290f3142', B + '2X7블럭.stl', '70×20×5mm'],
  ['718fe6c0-bcdd-45f5-88e9-b87d49e7ced0', B + '2X9블럭.stl', '90×20×5mm'], ['50e6ac30-acdb-4d52-bc3a-5e66863e613b', B + '3X3블럭.stl', '30×30×5mm'],
  ['d211b84c-cedb-4169-b8e6-baefae43279e', B + '3X5블럭.stl', '50×30×5mm'], ['82ce66e9-9e2a-4751-9616-383e9244676b', B + '3X7블럭.stl', '70×30×5mm'],
  ['50e75e3f-bf79-4853-80ec-66859ed13df8', B + '5X7블럭.stl', '70×50×5mm'], ['0834bc9c-2f6e-4796-9aca-4d941e0c8f89', B + 'L2X2블럭.stl', '20×20×20mm'],
  ['164fa5e6-1c40-4996-9d15-3dd8738ff9f3', B + 'L2X4블럭.stl', '20×30×20mm'], ['3315dc02-1448-428c-9ccb-0a156a130561', B + 'L6X9블럭.stl', '30×40×30mm'],
  ['d0deffcb-05ae-43a8-a43b-7cacd17ff1e3', P + '2단핀.stl', '지름 7.2 · 길이 10mm', '#1e50b4'], ['57bcba72-0dcb-4fba-9591-593c725c6821', P + '3단핀.stl', '지름 7.2 · 길이 15mm', '#e6b800'],
]
for (const [id, file, size, color = '#ffffff'] of parts) {
  const row = (await (await fetch(`${url}?id=eq.${id}&select=id,data`, { headers: H })).json())[0]
  if (!row) { console.log('행 없음', id); continue }
  const stl = fs.readFileSync(file), name = file.split('/').pop()
  // 블라인드 홀 안쪽 회색 조각(색칠 조각 paint:true): 몸통과 같은 자리에 맞도록 make-proboconnect-block.mjs 가 계산한 위치(.json)를 쓴다.
  const linerFile = file.replace(/([^/]+)\.stl$/, '블라인드안쪽/$1_블라인드안쪽.stl'), paint = []
  if (fs.existsSync(linerFile)) { const off = JSON.parse(fs.readFileSync(linerFile.replace(/\.stl$/, '.json'), 'utf8')); paint.push({ x: off.x, y: off.y, z: off.z, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', paint: true, color: '#8c8c8c', fileName: linerFile.split('/').pop(), brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + fs.readFileSync(linerFile).toString('base64') }) }
  const data = { ...row.data, size, spec: { ...(row.data.spec || {}), pitch: 10, margin: 5, shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, fileName: name, brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + stl.toString('base64') }, ...paint] }, thumbnail3d: null }   // 썸네일은 비워 두어 "안 그려진 것만 그리기"로 다시 그리게 한다
  const r = await fetch(`${url}?id=eq.${id}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) })
  console.log(row.data.name, '→', r.status, r.ok ? '등록됨' : await r.text(), `(${(stl.length / 1024).toFixed(0)}KB)`)
}
