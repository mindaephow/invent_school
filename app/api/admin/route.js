// 본사 관리자 + (부품 카탈로그 한정) 로그인한 선생님 (서버 전용: SERVICE_ROLE 키 사용)
//
// 관리자 = Supabase Auth 사용자 중 app_metadata.role = 'admin' 인 계정 (SQL 에디터에서만 지정 가능).
// 선생님 관리 액션(list/set_approved/create_teacher/delete_teacher)은 관리자만. 부품 카탈로그·로봇
// 카테고리 액션(list_parts~delete_robot_category)은 ivs_teachers에 등록된 로그인한 선생님이면 누구나.
//
// POST { action: 'list' }                                           선생님 전체 목록 (이메일, 수업/학생 수 포함) — 관리자만
// POST { action: 'set_approved', teacherId, approved }              선생님 승인 / 승인 취소 — 관리자만
// POST { action: 'create_teacher', name, email, phone?, password? } 본사에서 선생님 등록 (바로 승인됨) — 관리자만
// POST { action: 'delete_teacher', teacherId }                      선생님 삭제 (수업·학생·학생 로그인 계정·과제까지 함께 삭제) — 관리자만
// POST { action: 'list_parts' }                                      부품 카탈로그 목록 (이름·아이콘·과목만, 3D 모양은 코드로 별도 구현)
// POST { action: 'add_part', name, icon, subject, category?, volumes?: [{volume, qty?}], color?, size? } 부품 카탈로그에 등록
//   — volumes는 이 부품이 필요한 권과 그 권에서 필요한 수량 목록(비우면 전체 공통). 이름·이미지 등은 한 번만
//     등록하고 권마다 volumes 항목만 늘려서 쓴다 — 권마다 부품 전체를 새로 등록하지 않는다.
// POST { action: 'delete_part', partId }                             부품 카탈로그에서 삭제
// POST { action: 'list_robot_categories' }                           카테고리(브랜드·권 수) 목록 — 과목 상관없이 전체
// POST { action: 'add_robot_category', name, volumes, subject?, description? }               카테고리 등록(subject 생략 시 robot)
// POST { action: 'update_robot_category', categoryId, name, volumes, subject?, description? } 카테고리 수정
// POST { action: 'delete_robot_category', categoryId }                카테고리 삭제
// 헤더: Authorization: Bearer <관리자 또는 선생님 access_token>
//
// 환경변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

import { createClient } from '@supabase/supabase-js'
import crypto from 'crypto'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

function admin() {
  return createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

async function requireAdmin(sb, request) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : ''
  if (!token) return { error: json({ error: '로그인이 필요합니다.' }, 401) }
  const { data, error } = await sb.auth.getUser(token)
  if (error || !data?.user) return { error: json({ error: '로그인이 만료되었습니다. 다시 로그인해주세요.' }, 401) }
  if (data.user.app_metadata?.role !== 'admin') return { error: json({ error: '본사 관리자 계정이 아닙니다.' }, 403) }
  return { adminId: data.user.id }
}

// 부품 카탈로그/로봇 카테고리(부품 수리실)는 관리자가 아니어도 로그인한 선생님이면 쓸 수 있게 함
// — 사용자 지시: "버튼은 관리자에게만 보임, 링크 알면 로그인 한 선생님은 접속가능". 선생님 관리(list/
// set_approved/create_teacher/delete_teacher)는 여전히 requireAdmin으로 막아둔다.
async function requireTeacher(sb, request) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : ''
  if (!token) return { error: json({ error: '로그인이 필요합니다.' }, 401) }
  const { data, error } = await sb.auth.getUser(token)
  if (error || !data?.user) return { error: json({ error: '로그인이 만료되었습니다. 다시 로그인해주세요.' }, 401) }
  if (data.user.app_metadata?.role === 'admin') return { userId: data.user.id }
  const { data: teacher, error: tErr } = await sb.from('ivs_teachers').select('id').eq('id', data.user.id).maybeSingle()
  if (tErr) return { error: json({ error: tErr.message }, 500) }
  if (!teacher) return { error: json({ error: '선생님 계정이 아닙니다.' }, 403) }
  return { userId: data.user.id }
}

async function usersById(sb) {
  const map = {}
  for (let page = 1; page <= 20; page++) {
    const { data, error } = await sb.auth.admin.listUsers({ page, perPage: 1000 })
    if (error) throw new Error(error.message)
    const users = data?.users || []
    users.forEach((u) => { map[u.id] = { email: u.email, isAdmin: u.app_metadata?.role === 'admin' } })
    if (users.length < 1000) break
  }
  return map
}

async function inBatches(items, size, fn) {
  const out = []
  for (let i = 0; i < items.length; i += size) {
    out.push(...(await Promise.all(items.slice(i, i + size).map(fn))))
  }
  return out
}

async function listTeachers(sb) {
  const [rows, courses, students, users] = await Promise.all([
    sb.from('ivs_teachers').select('id, data, approved, created_at').order('created_at', { ascending: false }),
    sb.from('ivs_courses').select('id, teacher_id'),
    sb.from('ivs_students').select('course_id'),
    usersById(sb),
  ])
  if (rows.error) throw new Error(rows.error.message)
  const courseOwner = {}
  const courseCount = {}
  ;(courses.data || []).forEach((c) => { courseOwner[c.id] = c.teacher_id; courseCount[c.teacher_id] = (courseCount[c.teacher_id] || 0) + 1 })
  const studentCount = {}
  ;(students.data || []).forEach((s) => { const t = courseOwner[s.course_id]; if (t) studentCount[t] = (studentCount[t] || 0) + 1 })
  return (rows.data || []).map((r) => ({
    id: r.id,
    name: r.data?.name || '',
    phone: r.data?.phone || '',
    email: users[r.id]?.email || '',
    isAdmin: !!users[r.id]?.isAdmin,
    approved: r.approved === true,
    createdAt: r.created_at,
    courseCount: courseCount[r.id] || 0,
    studentCount: studentCount[r.id] || 0,
  }))
}

const PART_SUBJECTS = ['goldberg', 'robot', 'aviation']

// 부품 수리실에서 확정한 정확한 치수(외측 팔1/팔2/두께) — 자유 텍스트 size 문자열을 매번 다시 해석하지 않고
// 이 숫자를 그대로 저장해서 불러올 때마다 항상 똑같이 재현되게 함(사용자 지적: "불러올때마다 달라서 불편해").
function parseSpec(body) {
  const spec = body && body.spec
  if (!spec || typeof spec !== 'object') return null
  const armLen1 = Number(spec.armLen1), armLen2 = Number(spec.armLen2), armWidth = Number(spec.armWidth)
  const hasArmDims = [armLen1, armLen2, armWidth].every((n) => Number.isFinite(n) && n > 0)
  const holeLabels = Array.isArray(spec.holeLabels) && spec.holeLabels.every((s) => typeof s === 'string') ? spec.holeLabels : null
  // 도형 에디터(부품 수리실 스케치북 자리) — 도형 하나 이상의 위치·크기를 그대로 저장. svg 없이도 이
  // 숫자만으로 모양이 재현됨(브라켓의 armLen1/armLen2/armWidth와 같은 목적).
  // parts-lab-box-editor.js의 SHAPE_TYPES/BOX_LIKE/RADIUS_ONLY와 반드시 같이 맞춰야 한다.
  const SHAPE_TYPES = ['box', 'wheel', 'gear', 'sphere', 'cone', 'pyramid', 'torus', 'hexprism', 'icosahedron', 'dome', 'wedge', 'ring', 'star', 'heart', 'text', 'duplo', 'knexRod', 'knexConnector']
  const BOX_LIKE = ['box', 'wedge', 'duplo']
  const RADIUS_ONLY = ['sphere', 'icosahedron', 'dome']
  // op: 'add'(더하기)|'subtract'(빼기/뚫기) — 목록 순서대로 앞 결과에 CSG로 합치거나 깎아낸다. 첫 도형은
  // 기준(베이스)이라 op 의미가 없지만 필드는 그대로 두고 프론트에서 무시한다.
  const shapes = Array.isArray(spec.shapes)
    ? spec.shapes.map((s) => {
        if (!s || typeof s !== 'object' || !SHAPE_TYPES.includes(s.type)) return null
        const x = Number(s.x), y = Number(s.y), z = Number(s.z)
        if (![x, y, z].every(Number.isFinite)) return null
        const op = s.op === 'subtract' ? 'subtract' : 'add'
        // rx/ry/rz(라디안) — 마우스로 돌린 회전값. 없던 부품(예전에 저장된 도형)은 0으로 취급.
        const rx = Number.isFinite(Number(s.rx)) ? Number(s.rx) : 0
        const ry = Number.isFinite(Number(s.ry)) ? Number(s.ry) : 0
        const rz = Number.isFinite(Number(s.rz)) ? Number(s.rz) : 0
        if (BOX_LIKE.includes(s.type)) {
          const w = Number(s.w), h = Number(s.h), d = Number(s.d)
          if (![w, h, d].every((n) => Number.isFinite(n) && n > 0)) return null
          return { type: s.type, op, x, y, z, rx, ry, rz, w, h, d }
        }
        const radius = Number(s.radius)
        if (!Number.isFinite(radius) || radius <= 0) return null
        if (RADIUS_ONLY.includes(s.type)) return { type: s.type, op, x, y, z, rx, ry, rz, radius }
        const width = Number(s.width)
        if (!Number.isFinite(width) || width <= 0) return null
        const out = { type: s.type, op, x, y, z, rx, ry, rz, radius, width }
        if (s.type === 'gear') {
          const teeth = Number(s.teeth)
          out.teeth = Number.isFinite(teeth) && teeth >= 4 ? Math.round(teeth) : 12
        }
        if (s.type === 'text') out.text = String(s.text || 'A').trim().slice(0, 10) || 'A'
        if (s.type === 'knexConnector') {
          const holes = Number(s.holes)
          out.holes = Number.isFinite(holes) && holes >= 3 && holes <= 8 ? Math.round(holes) : 6
        }
        return out
      }).filter(Boolean)
    : []
  if (!hasArmDims && !holeLabels && !shapes.length) return null
  const result = hasArmDims ? { armLen1, armLen2, armWidth } : {}
  if (shapes.length) result.shapes = shapes
  // 구멍 번호(위에서 본 모습 기준 왼→오=숫자·위→아래=소문자, 브라켓은 정면A/뒷면B도 붙음) — 부품 수리실에서
  // 계산해서 넘겨준 값을 그대로 저장. 브라켓이 아닌 부품(프레임 등)도 팔 치수 없이 이 값만 올 수 있음.
  if (holeLabels) result.holeLabels = holeLabels
  // 여백·피치·구멍 반지름·두께 — 예전엔 코드에만 하드코딩돼 있고 저장은 안 됐음(사용자 지적: "구멍사이즈
  // 피치 테두리 간격 높이... 저장한게 없으니 뭐가 맞는지 알아?"). 부품 수리실이 계산해서 넘겨주면 그대로 저장.
  ;['thickness', 'margin', 'pitch', 'boreRadius', 'maxHolesPerArm'].forEach((key) => {
    const n = Number(spec[key])
    if (Number.isFinite(n) && n > 0) result[key] = n
  })
  // 라벨 문자열뿐 아니라 그 좌표(x,z,face)도 저장(사용자 지시: "넘버링 좌표도/구멍좌표도 모두 부품내역에
  // 다 저장해") — 각 항목이 {label, x, z, face} 형태인지만 검증.
  if (Array.isArray(spec.holeCoords)) {
    const holeCoords = spec.holeCoords
      .filter((h) => h && typeof h === 'object' && typeof h.label === 'string' && Number.isFinite(Number(h.x)) && Number.isFinite(Number(h.z)))
      .map((h) => ({ label: h.label, x: Number(h.x), z: Number(h.z), face: typeof h.face === 'string' ? h.face : null }))
    if (holeCoords.length) result.holeCoords = holeCoords
  }
  return result
}

// 확정된 렌더링 결과를 실제 이미지로도 같이 저장 — 숫자(spec)만이 아니라 눈으로 보이는 모습 자체를 남겨서
// 나중에 누가 다시 보더라도 재해석 없이 바로 확인 가능하게 함(사용자 지시: "설계도 보면 모든사람들이 다
// 알지?? 그렇게 저장을 하라고" / "수치랑 모든걸 저장하라고").
function parseOneSnapshot(snap) {
  if (typeof snap !== 'string' || !snap.startsWith('data:image/')) return null
  if (snap.length > 2_000_000) return null // 대략 1.5MB 넘는 이미지는 거절(비정상 입력 방지)
  return snap
}
// 위/정면/뒷면 3컷을 각각 저장 — 사용자 지시: "위에서 본거 정면 뒷면 모두 저장하고 스샷도 다 저장해놔,
// 불러올때 항상 똑같이". body.snapshots = { top, front, back } 형태로 오고, 각 값은 개별 검증한다.
function parseSnapshots(body) {
  const snaps = body && body.snapshots
  if (!snaps || typeof snaps !== 'object') return null
  const result = {}
  ;['top', 'front', 'back'].forEach((key) => {
    const s = parseOneSnapshot(snaps[key])
    if (s) result[key] = s
  })
  return Object.keys(result).length ? result : null
}

async function listParts(sb) {
  const { data, error } = await sb.from('ivs_part_catalog').select('id, data, created_at').order('created_at', { ascending: true })
  if (error) throw new Error(error.message)
  return (data || []).map((r) => ({ id: r.id, name: r.data?.name || '', icon: r.data?.icon || '', subject: r.data?.subject || '', category: r.data?.category || '', volumes: Array.isArray(r.data?.volumes) ? r.data.volumes : [], color: r.data?.color || '', size: r.data?.size || '', imageSvg: r.data?.image_svg || '', imageSvgDiagonal: r.data?.image_svg_diagonal || '', primaryImage: r.data?.primary_image === 'diagonal' ? 'diagonal' : 'front', spec: r.data?.spec || null, snapshot: r.data?.snapshot || null, snapshots: r.data?.snapshots || null, createdAt: r.created_at }))
}

// 부품 하나가 여러 권에 걸쳐 쓰이는 걸 표현 — 이름·아이콘·이미지 등 "부품 자체"는 한 번만 등록하고, 어느
// 권에서 몇 개가 필요한지만 이 배열에 쌓는다(권마다 전체를 다시 등록하던 예전 구조를 대체 — 사용자 지적:
// "부품 하나를 수정하면 모든 곳에 적용이 되어야 하는데 그게 아닌 방식").
function parseVolumes(body) {
  const raw = body && body.volumes
  if (raw == null) return { volumes: [] }
  if (!Array.isArray(raw)) return { error: '권 정보가 올바르지 않습니다.' }
  const out = []
  for (const v of raw) {
    if (!v || typeof v !== 'object') return { error: '권 정보가 올바르지 않습니다.' }
    const volumeRaw = v.volume
    if (volumeRaw === '' || volumeRaw == null) continue
    const volume = Number(volumeRaw)
    if (!Number.isInteger(volume) || volume < 1) return { error: '권은 1 이상 정수로 입력해주세요.' }
    const qtyRaw = v.qty
    const qty = qtyRaw === '' || qtyRaw == null ? null : Number(qtyRaw)
    if (qty != null && (!Number.isInteger(qty) || qty < 1)) return { error: '수량은 1 이상 정수로 입력해주세요.' }
    out.push({ volume, qty })
  }
  out.sort((a, b) => a.volume - b.volume)
  return { volumes: out }
}

async function listRobotCategories(sb) {
  const { data, error } = await sb.from('ivs_robot_categories').select('id, data, created_at').order('created_at', { ascending: true })
  if (error) throw new Error(error.message)
  return (data || []).map((r) => ({ id: r.id, name: r.data?.name || '', volumes: r.data?.volumes || 0, subject: r.data?.subject || 'robot', description: r.data?.description || '', createdAt: r.created_at }))
}

const TEACHER_ACTIONS = new Set([
  'list_parts', 'add_part', 'update_part', 'delete_part',
  'list_robot_categories', 'add_robot_category', 'update_robot_category', 'delete_robot_category',
])

export async function POST(request) {
  const sb = admin()

  let body
  try { body = await request.json() } catch { return json({ error: '잘못된 요청입니다.' }, 400) }

  const who = await (TEACHER_ACTIONS.has(body?.action) ? requireTeacher(sb, request) : requireAdmin(sb, request))
  if (who.error) return who.error

  try {
    if (body?.action === 'list') return json({ teachers: await listTeachers(sb) })

    if (body?.action === 'set_approved') {
      if (typeof body.teacherId !== 'string' || typeof body.approved !== 'boolean') return json({ error: '잘못된 요청입니다.' }, 400)
      const { data, error } = await sb.from('ivs_teachers').update({ approved: body.approved }).eq('id', body.teacherId).select('id').maybeSingle()
      if (error) throw new Error(error.message)
      if (!data) return json({ error: '선생님을 찾지 못했습니다.' }, 404)
      return json({ ok: true, teachers: await listTeachers(sb) })
    }

    if (body?.action === 'create_teacher') {
      const name = String(body.name || '').trim()
      const email = String(body.email || '').trim().toLowerCase()
      const phone = String(body.phone || '').trim()
      const password = String(body.password || '')
      if (!name) return json({ error: '성함을 입력해주세요.' }, 400)
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: '이메일 형식이 맞지 않아요.' }, 400)
      if (password && password.length < 6) return json({ error: '비밀번호는 6자 이상이어야 해요.' }, 400)
      // 비밀번호를 비워두면 아무도 모르는 임의 비밀번호로 만든다 (구글 로그인 전용). 같은 이메일의 구글 계정으로 로그인하면 이 계정과 연결된다.
      const { data, error } = await sb.auth.admin.createUser({
        email,
        password: password || crypto.randomBytes(24).toString('base64url'),
        email_confirm: true,
        user_metadata: { name, phone },
      })
      if (error) {
        if (/already|registered|exists/i.test(error.message)) return json({ error: '이미 등록된 이메일이에요.' }, 409)
        throw new Error(error.message)
      }
      const { error: insErr } = await sb.from('ivs_teachers').insert({ id: data.user.id, data: { name, phone, createdAt: Date.now() }, approved: true })
      if (insErr) {
        await sb.auth.admin.deleteUser(data.user.id)
        throw new Error(insErr.message)
      }
      return json({ ok: true, teacherId: data.user.id, teachers: await listTeachers(sb) })
    }

    if (body?.action === 'delete_teacher') {
      const teacherId = body.teacherId
      if (typeof teacherId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      if (teacherId === who.adminId) return json({ error: '본인 계정은 삭제할 수 없어요.' }, 400)
      const [{ data: t }, { data: target }, { data: courses }] = await Promise.all([
        sb.from('ivs_teachers').select('id').eq('id', teacherId).maybeSingle(),
        sb.auth.admin.getUserById(teacherId),
        sb.from('ivs_courses').select('id').eq('teacher_id', teacherId),
      ])
      if (!t) return json({ error: '선생님을 찾지 못했습니다.' }, 404)
      if (target?.user?.app_metadata?.role === 'admin') return json({ error: '본사 관리자 계정은 삭제할 수 없어요.' }, 400)

      // 학생 로그인 계정(Auth 사용자)은 DB 연쇄 삭제로 지워지지 않으므로 먼저 지운다 (프로젝트도 함께 삭제됨)
      const courseIds = (courses || []).map((c) => c.id)
      if (courseIds.length) {
        const { data: students } = await sb.from('ivs_students').select('user_id').in('course_id', courseIds).not('user_id', 'is', null)
        await inBatches(students || [], 10, (s) => sb.auth.admin.deleteUser(s.user_id))
      }
      // 선생님 계정 삭제 → 수업, 학생, 출석·과제 기록, 커리큘럼이 연쇄 삭제됨
      const { error } = await sb.auth.admin.deleteUser(teacherId)
      if (error) throw new Error(error.message)
      return json({ ok: true, teachers: await listTeachers(sb) })
    }

    if (body?.action === 'list_parts') return json({ parts: await listParts(sb) })

    if (body?.action === 'add_part') {
      const name = String(body.name || '').trim()
      const icon = String(body.icon || '').trim()
      const subject = String(body.subject || '')
      const category = String(body.category || '').trim()
      const color = String(body.color || '').trim()
      const size = String(body.size || '').trim()
      const imageSvg = String(body.imageSvg || '').trim()
      const imageSvgDiagonal = String(body.imageSvgDiagonal || '').trim()
      const primaryImage = body.primaryImage === 'diagonal' ? 'diagonal' : 'front'
      const spec = parseSpec(body)
      const snapshot = parseOneSnapshot(body.snapshot)
      const snapshots = parseSnapshots(body)
      const { volumes, error: volErr } = parseVolumes(body)
      if (!name) return json({ error: '부품 이름을 입력해주세요.' }, 400)
      if (!PART_SUBJECTS.includes(subject)) return json({ error: '과목을 선택해주세요.' }, 400)
      if (volErr) return json({ error: volErr }, 400)
      const { error } = await sb.from('ivs_part_catalog').insert({ data: { name, icon, subject, category: category || null, volumes, color: color || null, size: size || null, image_svg: imageSvg || null, image_svg_diagonal: imageSvgDiagonal || null, primary_image: primaryImage, spec, snapshot, snapshots, createdAt: Date.now() } })
      if (error) throw new Error(error.message)
      return json({ ok: true, parts: await listParts(sb) })
    }

    if (body?.action === 'update_part') {
      const partId = body.partId
      if (typeof partId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      const name = String(body.name || '').trim()
      const icon = String(body.icon || '').trim()
      const subject = String(body.subject || '')
      const category = String(body.category || '').trim()
      const color = String(body.color || '').trim()
      const size = String(body.size || '').trim()
      const imageSvg = String(body.imageSvg || '').trim()
      const imageSvgDiagonal = String(body.imageSvgDiagonal || '').trim()
      const primaryImage = body.primaryImage === 'diagonal' ? 'diagonal' : 'front'
      const spec = parseSpec(body)
      const snapshot = parseOneSnapshot(body.snapshot)
      const snapshots = parseSnapshots(body)
      const { volumes, error: volErr } = parseVolumes(body)
      if (!name) return json({ error: '부품 이름을 입력해주세요.' }, 400)
      if (!PART_SUBJECTS.includes(subject)) return json({ error: '과목을 선택해주세요.' }, 400)
      if (volErr) return json({ error: volErr }, 400)
      const { data: existing, error: fetchErr } = await sb.from('ivs_part_catalog').select('data').eq('id', partId).maybeSingle()
      if (fetchErr) throw new Error(fetchErr.message)
      if (!existing) return json({ error: '부품을 찾을 수 없어요.' }, 404)
      const createdAt = existing.data?.createdAt ?? Date.now()
      // spec/snapshot을 안 보내면(예: 다른 화면에서 저장) 기존 값을 그대로 유지 — 부품 수리실에서 한 번
      // 확정해둔 정확한 치수·이미지가 다른 저장 경로 때문에 사라지지 않게 함. snapshots(위/정면/뒷면)도
      // 마찬가지 — 사용자 지시: "위에서 본거 정면 뒷면 모두 저장하고 스샷도 다 저장해놔, 불러올때 항상 똑같이".
      const nextSpec = spec || existing.data?.spec || null
      const nextSnapshot = snapshot || existing.data?.snapshot || null
      const nextSnapshots = snapshots || existing.data?.snapshots || null
      // volumes도 안 보내면(예: 부품 수리실에서 스펙만 저장) 기존 권 배정을 그대로 유지한다.
      const nextVolumes = Array.isArray(body.volumes) ? volumes : (Array.isArray(existing.data?.volumes) ? existing.data.volumes : [])
      const { error } = await sb.from('ivs_part_catalog').update({ data: { name, icon, subject, category: category || null, volumes: nextVolumes, color: color || null, size: size || null, image_svg: imageSvg || null, image_svg_diagonal: imageSvgDiagonal || null, primary_image: primaryImage, spec: nextSpec, snapshot: nextSnapshot, snapshots: nextSnapshots, createdAt } }).eq('id', partId)
      if (error) throw new Error(error.message)
      return json({ ok: true, parts: await listParts(sb) })
    }

    if (body?.action === 'delete_part') {
      const partId = body.partId
      if (typeof partId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      const { error } = await sb.from('ivs_part_catalog').delete().eq('id', partId)
      if (error) throw new Error(error.message)
      return json({ ok: true, parts: await listParts(sb) })
    }

    if (body?.action === 'list_robot_categories') return json({ categories: await listRobotCategories(sb) })

    if (body?.action === 'add_robot_category') {
      const name = String(body.name || '').trim()
      const volumes = Number(body.volumes)
      const subject = String(body.subject || 'robot')
      const description = String(body.description || '').trim()
      if (!name) return json({ error: '카테고리 이름을 입력해주세요.' }, 400)
      if (!Number.isInteger(volumes) || volumes < 1) return json({ error: '권 수를 1 이상 정수로 입력해주세요.' }, 400)
      if (!PART_SUBJECTS.includes(subject)) return json({ error: '과목을 선택해주세요.' }, 400)
      const { error } = await sb.from('ivs_robot_categories').insert({ data: { name, volumes, subject, description: description || null, createdAt: Date.now() } })
      if (error) throw new Error(error.message)
      return json({ ok: true, categories: await listRobotCategories(sb) })
    }

    if (body?.action === 'update_robot_category') {
      const categoryId = body.categoryId
      const name = String(body.name || '').trim()
      const volumes = Number(body.volumes)
      const subject = String(body.subject || 'robot')
      const description = String(body.description || '').trim()
      if (typeof categoryId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      if (!name) return json({ error: '카테고리 이름을 입력해주세요.' }, 400)
      if (!Number.isInteger(volumes) || volumes < 1) return json({ error: '권 수를 1 이상 정수로 입력해주세요.' }, 400)
      if (!PART_SUBJECTS.includes(subject)) return json({ error: '과목을 선택해주세요.' }, 400)
      const { data: row, error: getErr } = await sb.from('ivs_robot_categories').select('data').eq('id', categoryId).maybeSingle()
      if (getErr) throw new Error(getErr.message)
      if (!row) return json({ error: '카테고리를 찾지 못했습니다.' }, 404)
      const { error } = await sb.from('ivs_robot_categories').update({ data: { ...row.data, name, volumes, subject, description: description || null, updatedAt: Date.now() } }).eq('id', categoryId)
      if (error) throw new Error(error.message)
      return json({ ok: true, categories: await listRobotCategories(sb) })
    }

    if (body?.action === 'delete_robot_category') {
      const categoryId = body.categoryId
      if (typeof categoryId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      const { error } = await sb.from('ivs_robot_categories').delete().eq('id', categoryId)
      if (error) throw new Error(error.message)
      return json({ ok: true, categories: await listRobotCategories(sb) })
    }

    return json({ error: '알 수 없는 요청입니다.' }, 400)
  } catch (e) {
    return json({ error: e.message || '처리 중 오류가 발생했습니다.' }, 500)
  }
}
