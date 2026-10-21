// 프린트용 시험 조각(노즐 0.4·PLA): 조립도용 규격(cubo-part-maker.js)은 그대로 두고, 이 스크립트 안에서만 구멍 여유(L)를 키워 STL 을 만든다.
//   node scripts/make-print-test.mjs [저장 폴더]     (기본: 다운로드/큐보_3D모델_프린트용)
// 만드는 것: 여유 L = 0.15·0.25·0.35 마다 3구멍 프레임, 2단블록(구멍 쪽만 키움, 돌기는 표준) + 표준 리벳 1개.
//   목·입구(테두리 안쪽)·테두리 바깥을 모두 L 만큼 키워 테두리 폭 0.5 를 유지한다(사용자 지시 2026-10-22). 프레임 폭 10 은 그대로라 바깥 가장자리 벽 두께가 1−L 로 얇아진다(0.65 이상).
//   리벳·블록 돌기는 표준 그대로라 스냅 걸림(머리 3.2 ↔ 목 2.75+L)은 줄어든다.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { CUBO_FRAME_STD as S, CUBO_BLOCK_STD as B } from '../app/lib/cubo-part-maker.js'
import { frameTriangles } from '../app/lib/cubo-frame-mesh.js'
import { blockTriangles } from '../app/lib/cubo-block-mesh.js'
import { rivetTriangles } from '../app/lib/cubo-rivet-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const out = process.argv[2] || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용')
fs.mkdirSync(out, { recursive: true })
const save = (name, tris) => { const s = trianglesToStl(tris); fs.writeFileSync(path.join(out, name), s); console.log(name, '삼각형', tris.length / 9) }
const base = { ...S }
for (const L of [0.15, 0.25, 0.35]) {
  Object.assign(S, base, { boreR: base.boreR + L, rimInnerR: base.rimInnerR + L, rimOuterR: base.rimOuterR + L, edgeWall: base.edgeWall - L })
  const tag = `여유${L.toFixed(2)}`
  save(`프레임3_${tag}.stl`, frameTriangles(3))
  save(`2단블록_${tag}.stl`, blockTriangles(2, 20, 9, { entryR: B.holeEntryR + L, neckR: B.holeNeckR + L, chamberR: B.chamberR + L }))
}
Object.assign(S, base)
save('리벳_표준.stl', rivetTriangles())
