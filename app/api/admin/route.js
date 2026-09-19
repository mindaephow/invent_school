// 본사 관리자 전용 (서버 전용: SERVICE_ROLE 키 사용)
//
// 관리자 = Supabase Auth 사용자 중 app_metadata.role = 'admin' 인 계정 (SQL 에디터에서만 지정 가능).
//
// POST { action: 'list' }                                           선생님 전체 목록 (이메일, 수업/학생 수 포함)
// POST { action: 'set_approved', teacherId, approved }              선생님 승인 / 승인 취소
// POST { action: 'create_teacher', name, email, phone?, password? } 본사에서 선생님 등록 (바로 승인됨)
// POST { action: 'delete_teacher', teacherId }                      선생님 삭제 (수업·학생·학생 로그인 계정·과제까지 함께 삭제)
// 헤더: Authorization: Bearer <관리자 access_token>
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

export async function POST(request) {
  const sb = admin()
  const who = await requireAdmin(sb, request)
  if (who.error) return who.error

  let body
  try { body = await request.json() } catch { return json({ error: '잘못된 요청입니다.' }, 400) }

  try {
    if (body?.action === 'list') {
      const { data: rows, error } = await sb.from('ivs_teachers').select('id, data, approved, created_at').order('created_at', { ascending: false })
      if (error) throw new Error(error.message)
      const { data: courses } = await sb.from('ivs_courses').select('id, teacher_id')
      const { data: students } = await sb.from('ivs_students').select('course_id')
      const courseOwner = {}
      const courseCount = {}
      ;(courses || []).forEach((c) => { courseOwner[c.id] = c.teacher_id; courseCount[c.teacher_id] = (courseCount[c.teacher_id] || 0) + 1 })
      const studentCount = {}
      ;(students || []).forEach((s) => { const t = courseOwner[s.course_id]; if (t) studentCount[t] = (studentCount[t] || 0) + 1 })
      const users = await usersById(sb)
      const teachers = (rows || []).map((r) => ({
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
      return json({ teachers })
    }

    if (body?.action === 'set_approved') {
      if (typeof body.teacherId !== 'string' || typeof body.approved !== 'boolean') return json({ error: '잘못된 요청입니다.' }, 400)
      const { data, error } = await sb.from('ivs_teachers').update({ approved: body.approved }).eq('id', body.teacherId).select('id').maybeSingle()
      if (error) throw new Error(error.message)
      if (!data) return json({ error: '선생님을 찾지 못했습니다.' }, 404)
      return json({ ok: true })
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
      return json({ ok: true, teacherId: data.user.id })
    }

    if (body?.action === 'delete_teacher') {
      const teacherId = body.teacherId
      if (typeof teacherId !== 'string') return json({ error: '잘못된 요청입니다.' }, 400)
      if (teacherId === who.adminId) return json({ error: '본인 계정은 삭제할 수 없어요.' }, 400)
      const { data: t } = await sb.from('ivs_teachers').select('id').eq('id', teacherId).maybeSingle()
      if (!t) return json({ error: '선생님을 찾지 못했습니다.' }, 404)
      const { data: target } = await sb.auth.admin.getUserById(teacherId)
      if (target?.user?.app_metadata?.role === 'admin') return json({ error: '본사 관리자 계정은 삭제할 수 없어요.' }, 400)

      // 학생 로그인 계정(Auth 사용자)은 DB 연쇄 삭제로 지워지지 않으므로 먼저 지운다 (프로젝트도 함께 삭제됨)
      const { data: courses } = await sb.from('ivs_courses').select('id').eq('teacher_id', teacherId)
      const courseIds = (courses || []).map((c) => c.id)
      if (courseIds.length) {
        const { data: students } = await sb.from('ivs_students').select('user_id').in('course_id', courseIds).not('user_id', 'is', null)
        await inBatches(students || [], 5, (s) => sb.auth.admin.deleteUser(s.user_id))
      }
      // 선생님 계정 삭제 → 수업, 학생, 출석·과제 기록, 커리큘럼이 연쇄 삭제됨
      const { error } = await sb.auth.admin.deleteUser(teacherId)
      if (error) throw new Error(error.message)
      return json({ ok: true })
    }

    return json({ error: '알 수 없는 요청입니다.' }, 400)
  } catch (e) {
    return json({ error: e.message || '처리 중 오류가 발생했습니다.' }, 500)
  }
}
