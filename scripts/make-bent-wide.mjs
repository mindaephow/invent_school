// 135도 프레임을 구멍 목 지름 6.2(반지름 +0.35)로 다시 만든다 — 입구·테두리 바깥도 같이 +0.35(테두리 폭 0.5 유지), 가장자리 벽 1 → 0.65.  node scripts/make-bent-wide.mjs <저장.stl>
import fs from 'node:fs'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { bentFrameTriangles } from '../app/lib/cubo-bent-frame-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
const L = 0.35
Object.assign(S, { boreR: S.boreR + L, rimInnerR: S.rimInnerR + L, rimOuterR: S.rimOuterR + L, edgeWall: S.edgeWall - L })
const t = bentFrameTriangles(); fs.writeFileSync(process.argv[2], trianglesToStl(t)); console.log('삼각형', t.length / 9)
