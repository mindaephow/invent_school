// 교재 참고 그림 격자 로컬 MCP(stdio) — 사람이 하던 "부품 잘라 보기 → 구멍에 격자 맞추기 → 수평으로 돌려 그리기 → 등록" 과정을 도구로 만든 것.
//   실행: 프로젝트 루트 .mcp.json 이 `node scripts/assembly-tools/refs-mcp/server.mjs` 로 띄운다(Claude 가 자동으로 연결).
//   처리는 ../refs_auto.py(OpenCV)가 한다 — Vercel 의 배포 MCP 는 Python 을 못 돌려서 로컬 전용이다.
//   등록(refs_register)은 SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 가 환경변수나 프로젝트 루트 .env.local 에 있어야 한다(키는 출력하지 않는다).
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { z } from 'zod'
import { execFile } from 'node:child_process'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const TOOLS_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const ROOT = path.resolve(TOOLS_DIR, '..', '..')
const REFS = (name) => path.join(TOOLS_DIR, 'refs', name)
const PYTHON = process.env.PYTHON || [
  process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python312', 'python.exe'),
].filter((p) => p && existsSync(p))[0] || 'python'

function py(cmd, payload) {
  return new Promise((resolve, reject) => {
    const p = execFile(PYTHON, [path.join(TOOLS_DIR, 'refs_auto.py'), cmd], { cwd: TOOLS_DIR, env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 64 * 1024 * 1024, encoding: 'utf8' }, (err, stdout, stderr) => {
      if (err) return reject(new Error((stderr || err.message).split('\n').filter(Boolean).slice(-6).join('\n')))
      try { resolve(JSON.parse(stdout)) } catch { reject(new Error('처리 결과를 읽지 못했어요: ' + stdout.slice(0, 300))) }
    })
    p.stdin.end(JSON.stringify(payload))
  })
}

const img = async (file, mime = 'image/png') => ({ type: 'image', data: (await readFile(file)).toString('base64'), mimeType: mime })
const text = (o) => ({ type: 'text', text: typeof o === 'string' ? o : JSON.stringify(o, null, 1) })
const fail = (e) => ({ isError: true, content: [text('실패: ' + (e && e.message ? e.message : e))] })
const fitFile = (name, step, label) => path.join(REFS(name), 'fits', `${String(step).padStart(2, '0')}_${label}.json`)

const server = new McpServer({ name: 'refs-grid', version: '1.0.0' })

server.registerTool('refs_view', {
  description: '① 교재 그림(refs/<이름>/NN.jpg)에서 부품 부분만 잘라 확대하고 픽셀 눈금(원본 좌표)을 얹어 보여준다. 눈금을 보고 판의 모서리 구멍 4곳(칸1·줄1, 끝칸·줄1, 끝칸·끝줄, 칸1·끝줄)의 대략 좌표를 읽는다.',
  inputSchema: { name: z.string().describe('조립도 폴더 이름. 예: kidknight'), step: z.number().int().describe('단계 번호'), bbox: z.array(z.number()).length(4).optional().describe('자를 영역 [x0,y0,x1,y1] (원본 좌표). 생략하면 그림 전체'), scale: z.number().optional().describe('확대 배율(기본 1.6)'), every: z.number().int().optional().describe('눈금 간격 px(기본 50)') },
}, async (a) => { try { const r = await py('view', a); return { content: [await img(r.image), text({ bbox: r.bbox, size: r.size, note: r.note })] } } catch (e) { return fail(e) } })

server.registerTool('refs_fit', {
  description: '② 판의 모서리 구멍 4곳(대략)에서 시작해, 그림에서 자동으로 찾은 구멍 중심에 맞게 칸 격자(원근)를 반복 보정한다. 결과 미리보기를 보고 빨강 점이 구멍 한가운데에 앉았는지 눈으로 확인한다(어긋나면 corners 를 고쳐 다시). 맞춘 좌표는 label 이름으로 저장돼 refs_render 가 쓴다.',
  inputSchema: { name: z.string(), step: z.number().int(), label: z.string().describe('이 판의 이름표(저장 키). 예: top, left-arm'), cols: z.number().int().describe('칸(가로 구멍) 수'), rows: z.number().int().describe('줄(세로 구멍) 수'), corners: z.array(z.array(z.number()).length(2)).length(4).describe('[[칸1·줄1],[끝칸·줄1],[끝칸·끝줄],[칸1·끝줄]] 구멍 중심 대략 좌표(원본 픽셀)'), lo: z.number().optional().describe('구멍 안쪽 밝기 하한(기본 90) — 검은 판이면 낮춘다'), hi: z.number().optional().describe('구멍 안쪽 밝기 상한(기본 200)') },
}, async (a) => {
  try {
    const { label, ...rest } = a; const r = await py('fit', rest)
    await mkdir(path.dirname(fitFile(a.name, a.step, label)), { recursive: true })
    await writeFile(fitFile(a.name, a.step, label), JSON.stringify({ cols: a.cols, rows: a.rows, pts: r.pts, corners: r.corners }))
    const { pts, image, ...info } = r
    return { content: [await img(image), text({ label, ...info })] }
  } catch (e) { return fail(e) }
})

server.registerTool('refs_render', {
  description: '③ refs_fit 으로 맞춘 판들을 써서, 수평 기준 판(ref)의 가운데 줄이 가로선이 되게 그림을 돌리고 ④ 돌린 그림(NN_1)·돌린 그림+격자+파란 수평 기준선(NN_2)·원본+격자(NN_3)와 index.json 을 만든다(로컬 파일). 올리기는 refs_register.',
  inputSchema: { name: z.string(), step: z.number().int(), plates: z.array(z.object({ label: z.string().describe('refs_fit 에서 쓴 label'), name: z.string().optional().describe('화면에 쓸 판 이름. 예: 위판 59프레임'), ref: z.boolean().optional().describe('수평 기준 판(단계마다 정확히 1개)') })).min(1), note: z.string().optional().describe('설명에 덧붙일 말') },
}, async (a) => {
  try {
    const plates = []
    for (const p of a.plates) {
      const f = fitFile(a.name, a.step, p.label); if (!existsSync(f)) throw new Error(`label "${p.label}" 의 refs_fit 결과가 없어요(단계 ${a.step}).`)
      const j = JSON.parse(await readFile(f, 'utf8')); plates.push({ name: p.name || p.label, cols: j.cols, rows: j.rows, pts: j.pts, ref: !!p.ref })
    }
    if (plates.filter((p) => p.ref).length > 1) throw new Error('수평 기준 판(ref)은 하나만 정할 수 있어요.')
    const r = await py('render', { name: a.name, step: a.step, plates, note: a.note || '' })
    return { content: [await img(r.preview, 'image/jpeg'), await img(r.original_preview, 'image/jpeg'), text({ rotated_deg: r.rotated_deg, files: r.files, note: '첫 그림 = 돌린 그림(2차 격자), 둘째 그림 = 원본(1차 격자).' })] }
  } catch (e) { return fail(e) }
})

async function env(key) {
  if (process.env[key]) return process.env[key]
  const f = path.join(ROOT, '.env.local'); if (!existsSync(f)) return ''
  const m = (await readFile(f, 'utf8')).split(/\r?\n/).map((l) => l.match(new RegExp('^\\s*' + key + '\\s*=\\s*(.*)$'))).find(Boolean)
  return m ? m[1].trim().replace(/^["']|["']$/g, '') : ''
}

server.registerTool('refs_register', {
  description: '⑤ refs/<이름>/ 의 격자 그림(idx 1~3)을 표 ivs_assembly_refs 에 올린다(같은 단계·idx 는 덮어씀). 바깥에 올라가는 작업이라 먼저 dryRun:true 로 올릴 목록을 확인하고, 사용자 확인 뒤 dryRun:false 로 실행한다.',
  inputSchema: { name: z.string(), assemblyId: z.string().describe('조립도 id. 예: cubo-1-kidknight'), steps: z.array(z.number().int()).min(1).describe('올릴 단계 번호들'), dryRun: z.boolean().default(true) },
}, async (a) => {
  try {
    const index = JSON.parse(await readFile(path.join(REFS(a.name), 'index.json'), 'utf8')); const rows = index.filter((r) => a.steps.includes(r.step) && r.idx >= 1)
    if (!rows.length) throw new Error('올릴 그림이 index.json 에 없어요.')
    if (a.dryRun) return { content: [text({ dryRun: true, assemblyId: a.assemblyId, items: rows.map((r) => `단계 ${r.step} · idx ${r.idx} · ${r.file}`) })] }
    const url = await env('SUPABASE_URL'), key = await env('SUPABASE_SERVICE_ROLE_KEY'); if (!url || !key) throw new Error('SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 없어요(환경변수 또는 프로젝트 루트 .env.local).')
    const body = []
    for (const r of rows) body.push({ assembly_id: a.assemblyId, step: r.step, idx: r.idx, note: r.note || '', img: 'data:image/jpeg;base64,' + (await readFile(path.join(REFS(a.name), r.file))).toString('base64'), updated_at: new Date().toISOString() })
    const res = await fetch(`${url.replace(/\/$/, '')}/rest/v1/ivs_assembly_refs?on_conflict=assembly_id,step,idx`, { method: 'POST', headers: { apikey: key, Authorization: 'Bearer ' + key, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify(body) })
    if (!res.ok) throw new Error(`올리기 실패 ${res.status}: ${(await res.text()).slice(0, 300)}`)
    return { content: [text({ uploaded: body.length, items: rows.map((r) => `단계 ${r.step} · idx ${r.idx}`) })] }
  } catch (e) { return fail(e) }
})

server.registerTool('refs_pull', {
  description: '다른 PC에서 이어 작업할 때: 표 ivs_assembly_refs 의 그림을 refs/<이름>/ 로 내려받는다(NN.jpg·NN_k.jpg 와 index.json 갱신). 이미 있는 같은 이름 파일은 덮어쓰므로 먼저 dryRun:true 로 목록을 확인한다. 격자 좌표(grids_orig.json)는 올라가지 않아서 그림만 복원된다.',
  inputSchema: { name: z.string().describe('폴더 이름. 예: kidknight'), assemblyId: z.string().describe('조립도 id. 예: cubo-1-kidknight'), steps: z.array(z.number().int()).optional().describe('받을 단계들(생략하면 전부)'), dryRun: z.boolean().default(true) },
}, async (a) => {
  try {
    const url = await env('SUPABASE_URL'), key = await env('SUPABASE_SERVICE_ROLE_KEY'); if (!url || !key) throw new Error('SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 없어요(환경변수 또는 프로젝트 루트 .env.local).')
    const base = `${url.replace(/\/$/, '')}/rest/v1/ivs_assembly_refs`, h = { apikey: key, Authorization: 'Bearer ' + key }
    const q = `assembly_id=eq.${encodeURIComponent(a.assemblyId)}` + (a.steps && a.steps.length ? `&step=in.(${a.steps.join(',')})` : '')
    const metaRes = await fetch(`${base}?select=step,idx,note&order=step,idx&${q}`, { headers: h }); if (!metaRes.ok) throw new Error(`목록 실패 ${metaRes.status}`)
    const meta = await metaRes.json(); const fname = (s, i) => String(s).padStart(2, '0') + (i ? '_' + i : '') + '.jpg'
    if (a.dryRun) return { content: [text({ dryRun: true, count: meta.length, items: meta.map((m) => `단계 ${m.step} · idx ${m.idx} → ${fname(m.step, m.idx)}`) })] }
    await mkdir(REFS(a.name), { recursive: true }); const ip = path.join(REFS(a.name), 'index.json'); let index = existsSync(ip) ? JSON.parse(await readFile(ip, 'utf8')) : []; let n = 0
    for (const m of meta) {
      const r = await fetch(`${base}?select=img&assembly_id=eq.${encodeURIComponent(a.assemblyId)}&step=eq.${m.step}&idx=eq.${m.idx}`, { headers: h }); if (!r.ok) throw new Error(`단계 ${m.step} idx ${m.idx} 실패 ${r.status}`)
      const img64 = (await r.json())[0]?.img || ''; const b64 = img64.slice(img64.indexOf(',') + 1)
      await writeFile(path.join(REFS(a.name), fname(m.step, m.idx)), Buffer.from(b64, 'base64'))
      index = index.filter((x) => !(x.step === m.step && x.idx === m.idx)); index.push({ step: m.step, idx: m.idx, file: fname(m.step, m.idx), note: m.note || '' }); n++
    }
    index.sort((x, y) => x.step - y.step || x.idx - y.idx); await writeFile(ip, JSON.stringify(index, null, 1), 'utf8')
    return { content: [text({ downloaded: n, folder: `scripts/assembly-tools/refs/${a.name}` })] }
  } catch (e) { return fail(e) }
})

await server.connect(new StdioServerTransport())
