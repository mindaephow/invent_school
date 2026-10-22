// 프린트용 프레임(구멍 목 6.2·입구·테두리 같이 +0.35)을 원 둘레 64분할로 다시 만든다 — 20분할이면 구멍·테두리가 각져 "찌그러져" 보인다.
//   node scripts/make-print-frames.mjs [저장 폴더]   (기본: 다운로드/큐보_3D모델_프린트용/고해상도)
// 19프레임(구멍 9)·35프레임(5×3)·37프레임(7×3)·135도 프레임(생성기). STL 변환이 두께를 z(위)로 눕혀 주므로 따로 돌리지 않는다(바닥에 누운 채 출력). 90도 프레임은 꺾인 프레임 생성기를 90°(3+3칸)로 써서 만든다.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { addPlate } from '../app/lib/cubo-plate-mesh.js'
import { bentFrameTriangles, BENT_STD } from '../app/lib/cubo-bent-frame-mesh.js'
const out = process.argv[2] || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용', '고해상도'); fs.mkdirSync(out, { recursive: true })
const L = 0.35, SEG = 64
Object.assign(S, { boreR: 3.05, rimInnerR: 3.85, rimHeight: 1.1, plate: 2.8, total: 5, edgeWall: 0, slab: true }) // 확정 규격(사용자 2026-10-23): 목 지름 6.10, 입구 지름 7.7(깊이 1.1), 가장 얇은 곳(목) 2.8, 통판(테두리·고리 겹침 없음, 아래 면 평평)
const plate = (nx, nz) => {
  const kit = makeKit(SEG), hx = nx * S.pitch / 2, hz = nz * S.pitch / 2
  const xCells = Array.from({ length: nx }, (_, i) => ({ lo: -hx + i * S.pitch, hi: -hx + (i + 1) * S.pitch, c: -hx + S.margin + i * S.pitch }))
  const zCells = Array.from({ length: nz }, (_, i) => ({ lo: -hz + i * S.pitch, hi: -hz + (i + 1) * S.pitch, c: -hz + S.margin + i * S.pitch }))
  addPlate(kit, { xCells, zCells }); return kit.result()
}
const flat = (t) => { // 회전 없이 가운데 맞춤·바닥 0 만(두께는 STL 변환이 z 로 눕힌다)
  const a = Float32Array.from(t); const n = a.length / 3
  let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], a[i * 3 + k]); mx[k] = Math.max(mx[k], a[i * 3 + k]) }
  for (let i = 0; i < n; i++) { a[i * 3] -= (mn[0] + mx[0]) / 2; a[i * 3 + 2] -= (mn[2] + mx[2]) / 2; a[i * 3 + 1] -= mn[1] }   // 메쉬 좌표(두께 y)에서 가운데 맞춤·바닥 0 — STL 변환(trianglesToStl)이 두께를 z(위)로 눕힌다
  return a
}
const save = (name, t) => { const f = flat(t); fs.writeFileSync(path.join(out, name), trianglesToStl(f)); console.log(name, '삼각형', f.length / 9) }
save('19프레임.stl', plate(9, 1)); save('35프레임.stl', plate(5, 3)); save('37프레임.stl', plate(7, 3)); save('135도 프레임.stl', bentFrameTriangles(SEG))
Object.assign(BENT_STD, { straightHoles: 3, slantHoles: 3, bendDeg: 90 }) // 90도 프레임: 꺾인 프레임 생성기를 90° 로(곧은 팔 3칸 + 꺾인 팔 3칸, 모서리 구멍 공유 = 5구멍, 30×30)
save('90도 프레임.stl', bentFrameTriangles(SEG))
