// 본사 관리자 전용 (서버 전용: SERVICE_ROLE 키 사용)
//
// 관리자 = Supabase Auth 사용자 중 app_metadata.role = 'admin' 인 계정 (SQL 에디터에서만 지정 가능).
//
// POST { action: 'list' }                              선생님 전체 목록 (이메일 포함)
// POST { action: 'set_approved', teacherId, approved } 선생님 승인 / 승인 취소
// 헤더: Authorization: Bearer <관리자 access_token>
//
// 환경변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

import { createClient } from '@supabase/supabase-js'

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

async function emailsById(sb) {
  const map = {}
  for (let page = 1; page <= 20; page++) {
    const { data, error } = await sb.auth.admin.listUsers({ page, perPage: 1000 })
    if (error) throw new Error(error.message)
    const users = data?.users || []
    users.forEach((u) => { map[u.id] = u.email })
    if (users.length < 1000) break
  }
  return map
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
      const emails = await emailsById(sb)
      const teachers = (rows || []).map((r) => ({
        id: r.id,
        name: r.data?.name || '',
        phone: r.data?.phone || '',
        email: emails[r.id] || '',
        approved: r.approved === true,
        createdAt: r.created_at,
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

    return json({ error: '알 수 없는 요청입니다.' }, 400)
  } catch (e) {
    return json({ error: e.message || '처리 중 오류가 발생했습니다.' }, 500)
  }
}
