// 프린트용 프레임(구멍 목 6.2·입구·테두리 같이 +0.35)을 원 둘레 64분할로 다시 만든다 — 20분할이면 구멍·테두리가 각져 "찌그러져" 보인다.
//   node scripts/make-print-frames.mjs [저장 폴더]   (기본: 다운로드/큐보_3D모델_프린트용/고해상도)
// 19프레임(구멍 9)·35프레임(5×3)·37프레임(7×3)·135도 프레임(생성기). 두께가 z 가 되게(바닥에 눕혀 출력) x축 +90° 돌려 저장. 90도 프레임은 꺾인 프레임 생성기를 90°(3+3칸)로 써서 만든다.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { addPlate } from '../app/lib/cubo-plate-mesh.js'
import { bentFrameTriangles, BENT_STD } from '../app/lib/cubo-bent-frame-mesh.js'
const out = process.argv[2] || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용', '고해상도'); fs.mkdirSync(out, { recursive: true })
const L = 0.35, SEG = 64
Object.assign(S, { boreR: S.boreR + L, rimInnerR: S.rimInnerR + L, rimOuterR: S.rimOuterR + L, edgeWall: S.edgeWall - L })
const plate = (nx, nz) => {
  const kit = makeKit(SEG), hx = nx * S.pitch / 2, hz = nz * S.pitch / 2
  const xCells = Array.from({ length: nx }, (_, i) => ({ lo: -hx + i * S.pitch, hi: -hx + (i + 1) * S.pitch, c: -hx + S.margin + i * S.pitch }))
  const zCells = Array.from({ length: nz }, (_, i) => ({ lo: -hz + i * S.pitch, hi: -hz + (i + 1) * S.pitch, c: -hz + S.margin + i * S.pitch }))
  addPlate(kit, { xCells, zCells }); return kit.result()
}
const flat = (t) => { // (x,y,z) → (x,−z,y): 두께 y 가 z 로. 그다음 z 최솟값 0, xy 가운데 0
  const a = Float32Array.from(t); const n = a.length / 3
  for (let i = 0; i < n; i++) { const y = a[i * 3 + 1], z = a[i * 3 + 2]; a[i * 3 + 1] = -z; a[i * 3 + 2] = y }
  let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], a[i * 3 + k]); mx[k] = Math.max(mx[k], a[i * 3 + k]) }
  for (let i = 0; i < n; i++) { a[i * 3] -= (mn[0] + mx[0]) / 2; a[i * 3 + 1] -= (mn[1] + mx[1]) / 2; a[i * 3 + 2] -= mn[2] }
  return a
}
const save = (name, t) => { const f = flat(t); fs.writeFileSync(path.join(out, name), trianglesToStl(f)); console.log(name, '삼각형', f.length / 9) }
save('19프레임.stl', plate(9, 1)); save('35프레임.stl', plate(5, 3)); save('37프레임.stl', plate(7, 3)); save('135도 프레임.stl', bentFrameTriangles(SEG))
Object.assign(BENT_STD, { straightHoles: 3, slantHoles: 3, bendDeg: 90 }) // 90도 프레임: 꺾인 프레임 생성기를 90° 로(곧은 팔 3칸 + 꺾인 팔 3칸, 모서리 구멍 공유 = 5구멍, 30×30)
save('90도 프레임.stl', bentFrameTriangles(SEG))
