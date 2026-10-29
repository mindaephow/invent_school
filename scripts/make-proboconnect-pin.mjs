// 프로보 커넥트 2단핀(2)·3단핀(3) STL 만들기. 사용: node scripts/make-proboconnect-pin.mjs <층수 2|3> <저장할 파일.stl> [잠금(1이면 90° 돌린 모습)]
import fs from 'node:fs'
import { probo2nPinTriangles } from '../app/lib/proboconnect-pin-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'
const n = Number(process.argv[2]), out = process.argv[3], rot = Number(process.argv[4] || 0)
if (![2, 3].includes(n) || !out) { console.error('사용: node scripts/make-proboconnect-pin.mjs <2|3> <파일.stl> [1]'); process.exit(1) }
const t = probo2nPinTriangles(n, undefined, rot), s = trianglesToStl(t)
fs.writeFileSync(out, s)
console.log(`${n}단핀${rot ? '(잠금)' : ''}: 삼각형 ${t.length / 9}개, ${(s.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(t)), '→', out)
