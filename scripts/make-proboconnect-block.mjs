// 프로보 커넥트 1XN블럭 STL 만들기(삼각형 직접 짜기). 사용: node scripts/make-proboconnect-block.mjs <구멍 수> <저장할 파일.stl>
//   1X5블럭 = 구멍 5개(길이 50 × 폭 10 × 두께 5). 만든 뒤 짝 없는 모서리·부피·삼각형 수를 보고한다(규격: get_part_standard '새 3D 부품을 만들거나 고칠 때 지킬 것').
import fs from 'node:fs'
import { probo1xNTriangles } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'

const n = Number(process.argv[2]), out = process.argv[3], rows = Number(process.argv[4] || 1)
if (!Number.isInteger(n) || n < 1 || n > 19 || !out) { console.error('사용: node scripts/make-proboconnect-block.mjs <구멍 수 1~19> <저장할 파일.stl> [줄 수=1]'); process.exit(1) }
const tris = conformTJunctions(probo1xNTriangles(n, undefined, rows))
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
console.log(`${rows}X${n}블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '→', out)
