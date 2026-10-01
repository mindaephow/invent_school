// 큐보 규격 부품 STL 만들기.  사용:  node scripts/make-part-stl.mjs <frame|block> <개수> <저장할 파일.stl>
//   frame 5 → 15프레임(구멍 5개),  block 3 → 3단블록(3칸).  규격은 app/lib/cubo-part-maker.js 와 get_part_standard 참고.
// 만든 STL 은 부품 만들기에서 "STL 가져오기"로 등록한다(색은 등록할 때 정한다).
import fs from 'node:fs'
import { frameTriangles } from '../app/lib/cubo-frame-mesh.js'
import { blockTriangles } from '../app/lib/cubo-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const [kind, countArg, out] = process.argv.slice(2)
const count = Number(countArg)
if (!['frame', 'block'].includes(kind) || !Number.isInteger(count) || count < 1 || count > 30 || !out) {
  console.error('사용: node scripts/make-part-stl.mjs <frame|block> <개수 1~30> <저장할 파일.stl>')
  process.exit(1)
}
const tris = kind === 'block' ? blockTriangles(count) : frameTriangles(count)
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
console.log(`${kind} ${count}칸: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB → ${out}`)
