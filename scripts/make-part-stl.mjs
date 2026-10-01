// 큐보 규격 부품 STL 만들기.  사용:  node scripts/make-part-stl.mjs <frame|block|bracket> <개수> <저장할 파일.stl>
//   frame 5 → 15프레임(구멍 5개),  block 3 → 3단블록(3칸),  bracket 1 → 1열브라켓(2 → 2열브라켓).  규격은 app/lib/cubo-part-maker.js 와 get_part_standard 참고.
// 만든 STL 은 부품 만들기에서 "STL 가져오기"로 등록한다(색은 등록할 때 정한다).
import fs from 'node:fs'
import { frameTriangles } from '../app/lib/cubo-frame-mesh.js'
import { blockTriangles } from '../app/lib/cubo-block-mesh.js'
import { bracketTriangles } from '../app/lib/cubo-bracket-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { arcFrameTriangles } from '../app/lib/cubo-arc-frame-mesh.js'
import { servoHornTriangles, roundHornTriangles } from '../app/lib/cubo-horn-mesh.js'

const [kind, countArg, out] = process.argv.slice(2)
const count = Number(countArg)
if (kind === 'servohorn' || kind === 'roundhorn') { // 서보혼(막대형)·둥근서보혼: node scripts/make-part-stl.mjs servohorn 1 <저장할 파일.stl>
  if (!out) { console.error(`사용: node scripts/make-part-stl.mjs ${kind} 1 <저장할 파일.stl>`); process.exit(1) }
  const t = kind === 'servohorn' ? servoHornTriangles() : roundHornTriangles()
  const s = trianglesToStl(t)
  fs.writeFileSync(out, s)
  console.log(`${kind}: 삼각형 ${t.length / 9}개, ${(s.length / 1024).toFixed(0)}KB → ${out}`)
  process.exit(0)
}
if (kind === 'arc') { // 반원프레임(구멍 9개 고정):  node scripts/make-part-stl.mjs arc 9 <저장할 파일.stl>
  if (count !== 9 || !out) { console.error('사용: node scripts/make-part-stl.mjs arc 9 <저장할 파일.stl>'); process.exit(1) }
  const t = arcFrameTriangles()
  const s = trianglesToStl(t)
  fs.writeFileSync(out, s)
  console.log(`arc 9: 삼각형 ${t.length / 9}개, ${(s.length / 1024).toFixed(0)}KB → ${out}`)
  process.exit(0)
}
if (!['frame', 'block', 'bracket'].includes(kind) || !Number.isInteger(count) || count < 1 || count > 30 || (kind === 'bracket' && count > 2) || !out) {
  console.error('사용: node scripts/make-part-stl.mjs <frame|block|bracket> <개수(프레임 구멍 수·블록 칸 수 1~30, 브라켓 열 수 1~2)> <저장할 파일.stl>')
  process.exit(1)
}
const tris = kind === 'block' ? blockTriangles(count) : kind === 'bracket' ? bracketTriangles(count) : frameTriangles(count)
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
console.log(`${kind} ${count}칸: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB → ${out}`)
