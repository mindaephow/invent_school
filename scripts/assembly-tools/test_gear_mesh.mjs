// 기어 정상 물림은 겹침이 아니고, 이빨 깊이보다 더 파고들거나 벽·판을 뚫으면 그대로 겹침이다(design-collision.js gearPair). 실행: node scripts/assembly-tools/test_gear_mesh.mjs
import fs from 'node:fs'
const win = {}; new Function('window', fs.readFileSync(new URL('../../public/design-collision.js', import.meta.url), 'utf8'))(win)
const C = win.IVS_COLLISION
// 강아지 30번 실측: 큰기어 46(끝 반지름 23)·작은기어 17.6(8.8), 둘 다 축 z(회전 [90,0,z°])·중심 거리 30 = 피치 합 29.9
const mul = (a, b) => ({ w: a.w*b.w - a.x*b.x - a.y*b.y - a.z*b.z, x: a.w*b.x + a.x*b.w + a.y*b.z - a.z*b.y, y: a.w*b.y - a.x*b.z + a.y*b.w + a.z*b.x, z: a.w*b.z + a.x*b.y - a.y*b.x + a.z*b.w })
const q = (deg) => { const a = Math.PI / 4, h = deg * Math.PI / 360   // x축 90°(기어 축 y → z) 다음 월드 z축 deg°
  return mul({ x: 0, y: 0, z: Math.sin(h), w: Math.cos(h) }, { x: Math.sin(a), y: 0, z: 0, w: Math.cos(a) }) }
const big = C.coreBoxes('큰기어', [46, 9, 46]), small = C.coreBoxes('작은기어', [17.6, 8, 17.6]), wall = C.coreBoxes('315프레임', [150, 5, 30])
let fails = 0
const eq = (label, got, want) => { const ok = got === want; if (!ok) fails++; console.log((ok ? '✓ ' : '✗ ') + label, got, ok ? '' : '(기대 ' + want + ')') }
const hit = (dist, d1 = 42.37, d2 = 138.8) => C.boxesOverlap(big, { x: dist, y: 0, z: 82 }, q(d1), small, { x: 0, y: 0, z: 81.5 }, q(d2), 0.05)
eq('정상 물림(중심 30)', hit(30), false)
eq('정상 물림, 다른 회전각', hit(30, 0, 45), false)
eq('멀리 떨어짐(35)', hit(35), false)
eq('가짜로 5mm 가깝게(25) = 파고듦', hit(25), true)
eq('3mm 가깝게(27) = 파고듦', hit(27), true)
eq('기어 둘이 같은 자리(0)', hit(0), true)
const info = C.boxesOverlapInfo(big, { x: 25, y: 0, z: 82 }, q(42), small, { x: 0, y: 0, z: 81.5 }, q(139), 0.05)
eq('파고든 깊이 = 끝 합 − 거리(6.8)', info && Math.round(info.depth * 10) / 10, 6.8)
// 기어가 판(벽)을 뚫는 것은 그대로 겹침
eq('기어↔판 뚫음', C.boxesOverlap(big, { x: 0, y: 0, z: 0 }, q(0), wall, { x: 10, y: 0, z: 0 }, q(0), 0.05), true)
console.log(fails ? '실패 ' + fails : '모두 통과'); process.exit(fails ? 1 : 0)
