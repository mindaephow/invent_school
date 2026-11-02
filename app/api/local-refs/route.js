// 조립도 교재 참고 그림을 이 컴퓨터의 저장소 파일에서 바로 준다 — 개발 서버(localhost) 전용.
// 작업 중인 차시는 그림이 scripts/assembly-tools/refs/<이름>/ 에 파일로 있으므로(index.json 이 단계·번호·설명을 가진다), 설계 화면이 라이브 DB(ivs_assembly_refs)에서 매번 받지 않게 한다(사용자 지시 2026-11-03).
//
// GET /api/local-refs?id=cubo-3-hammerbattle&steps=19,20   → { rows: [{ step, idx, note, img }] }  (img = data URL)
// GET /api/local-refs?id=cubo-3-hammerbattle&meta=1        → { rows: [{ step, idx, note }] }       (그림 없이 목록만)
// 파일이 없으면 404 { rows: null } — 설계 화면이 DB 로 되돌아간다. 배포(Vercel)·localhost 가 아닌 주소에서는 항상 404.

import fs from 'node:fs'
import path from 'node:path'

export const dynamic = 'force-dynamic'

const MIME = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png' }
const none = () => Response.json({ rows: null }, { status: 404 })

export async function GET(req) {
  if (process.env.VERCEL) return none()
  const host = (req.headers.get('host') || '').replace(/:\d+$/, '')
  if (!['localhost', '127.0.0.1', '[::1]'].includes(host)) return none()
  const { searchParams } = new URL(req.url)
  const name = String(searchParams.get('id') || '').replace(/^cubo-\d+-/, '')
  if (!/^[A-Za-z0-9_]+$/.test(name)) return none()
  const base = path.join(process.cwd(), 'scripts', 'assembly-tools', 'refs', name)
  let index
  try { index = JSON.parse(fs.readFileSync(path.join(base, 'index.json'), 'utf8')) } catch { return none() }
  const steps = searchParams.get('steps') ? new Set(searchParams.get('steps').split(',').map(Number)) : null
  const meta = searchParams.get('meta') === '1'
  const rows = []
  for (const e of index) {
    if (steps && !steps.has(e.step)) continue
    if (meta) { rows.push({ step: e.step, idx: e.idx, note: e.note || '' }); continue }
    const file = path.resolve(base, e.file)
    if (!file.startsWith(base + path.sep)) continue
    let buf; try { buf = fs.readFileSync(file) } catch { continue }
    rows.push({ step: e.step, idx: e.idx, note: e.note || '', img: 'data:' + (MIME[path.extname(file).toLowerCase()] || 'image/jpeg') + ';base64,' + buf.toString('base64') })
  }
  rows.sort((a, b) => a.step - b.step || a.idx - b.idx)
  return Response.json({ rows })
}
