// 학생 로그인 계정 관리 (서버 전용: SERVICE_ROLE 키 사용)
//
// 학생 계정 = Supabase Auth 사용자. 이메일은 사용하지 않는 가짜 주소(<아이디>@students.invent-school.app),
// 비밀번호 = 숫자 6자리. 선생님만 호출할 수 있고, 자기 수업의 학생에게만 적용된다.
//
// POST { action: 'create', courseId }   수업의 계정 없는 학생 전원에게 아이디+비밀번호 발급
// POST { action: 'reset', studentId }   비밀번호 재발급 (계정이 없으면 새로 발급)
// POST { action: 'remove_course', courseId }  수업 삭제 시 학생 로그인 계정까지 함께 정리
// 헤더: Authorization: Bearer <선생님 access_token>
//
// 환경변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

import { createClient } from '@supabase/supabase-js'
import crypto from 'crypto'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

const EMAIL_DOMAIN = 'students.invent-school.app'
const ID_CHARS = 'abcdefghjkmnpqrstuvwxyz23456789' // 헷갈리는 i l o 0 1 제외

function admin() {
  return createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY, {
    auth: { autoRefreshToken: false, persistSession: false },
  })
}

function genLoginId() {
  let s = ''
  for (let i = 0; i < 8; i++) s += ID_CHARS[crypto.randomInt(ID_CHARS.length)]
  return s
}
// 학교 영문 약어 + 학년·반·번호(각 2자리, 숫자 6자리) 로 아이디를 만든다. 예: cg + 3학년 4반 12번 → cg030412.
// 약어나 학년·반·번호가 없으면 null(무작위 아이디로 대신). 같은 아이디가 이미 있으면 뒤에 b, c… 를 붙인다.
function readableLoginId(code, data) {
  const digits = (v) => String(v ?? '').replace(/\D/g, '')
  const grade = digits(data?.grade), cls = digits(data?.classLabel), num = digits(data?.number)
  if (!code || !grade || !cls || !num) return null
  return `${code}${grade.padStart(2, '0')}${cls.padStart(2, '0')}${num.padStart(2, '0')}`
}
// 수업이 속한 학교의 영문 약어(학교 달력 문서 data.code). 없으면 ''.
async function schoolCodeOf(sb, courseId, teacherId) {
  const { data: c } = await sb.from('ivs_courses').select('data').eq('id', courseId).maybeSingle()
  const school = c?.data?.school
  if (!school) return ''
  const { data: cal } = await sb.from('ivs_school_calendars').select('data').eq('teacher_id', teacherId).eq('data->>school', school).limit(1)
  const code = String(cal?.[0]?.data?.code || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 6)
  return code
}
function genPin() {
  return String(crypto.randomInt(0, 1000000)).padStart(6, '0')
}
function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

async function requireTeacher(sb, request) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : ''
  if (!token) return { error: json({ error: '로그인이 필요합니다.' }, 401) }
  const { data, error } = await sb.auth.getUser(token)
  if (error || !data?.user) return { error: json({ error: '로그인이 만료되었습니다. 다시 로그인해주세요.' }, 401) }
  const { data: t } = await sb.from('ivs_teachers').select('id, approved').eq('id', data.user.id).maybeSingle()
  if (!t) return { error: json({ error: '선생님 계정만 사용할 수 있습니다.' }, 403) }
  if (t.approved !== true) return { error: json({ error: '본사 승인 후 사용할 수 있습니다.' }, 403) }
  return { teacherId: data.user.id }
}

async function ownedCourse(sb, courseId, teacherId) {
  const { data } = await sb.from('ivs_courses').select('id').eq('id', courseId).eq('teacher_id', teacherId).maybeSingle()
  return !!data
}

// 학생 한 명에게 계정을 만들어 준다. 아이디가 겹치면 새로 뽑아 다시 시도.
async function issueAccount(sb, student, code) {
  const pin = genPin()
  const base = readableLoginId(code, student.data)
  for (let attempt = 0; attempt < 6; attempt++) {
    const loginId = base && attempt < 3 ? base + ['', 'b', 'c'][attempt] : genLoginId()
    const { data, error } = await sb.auth.admin.createUser({
      email: `${loginId}@${EMAIL_DOMAIN}`,
      password: pin,
      email_confirm: true,
      app_metadata: { role: 'student' }, // 서버만 설정 가능 → 학생이 스스로 선생님으로 등록하지 못하게 하는 표식
    })
    if (error) {
      if (/already|registered|exists/i.test(error.message)) continue
      throw new Error(error.message)
    }
    const { error: upErr } = await sb.from('ivs_students').update({ user_id: data.user.id, login_id: loginId }).eq('id', student.id)
    if (upErr) {
      await sb.auth.admin.deleteUser(data.user.id)
      if (/duplicate|unique/i.test(upErr.message)) continue
      throw new Error(upErr.message)
    }
    return { studentId: student.id, name: student.data?.name || '', number: student.data?.number || '', loginId, pin }
  }
  throw new Error('아이디를 만들지 못했습니다. 다시 시도해주세요.')
}

// 학생 한 명의 비밀번호를 새로 만들고, 아이디도 현재 규칙(학교 약어 + 학년·반·번호)으로 맞춘다.
// 계정이 없으면 새로 만든다. 돌려주는 note 는 선생님이 확인해야 할 사유(없으면 빈 문자열).
async function resetOne(sb, s, code) {
  const want = readableLoginId(code, s.data)
  const noteFor = (loginId) => {
    if (!code) return '학교 영문 약어가 없어요'
    if (!want) return '학년·반·번호가 비어 있어요'
    if (loginId !== want) return '같은 아이디가 있어 "' + loginId + '"로 만들었어요'
    return ''
  }
  const info = (loginId, pin) => ({ studentId: s.id, name: s.data?.name || '', number: s.data?.number || '', loginId, pin })
  if (!s.user_id) {
    const issued = await issueAccount(sb, s, code)
    return { issued, name: issued.name, note: noteFor(issued.loginId) }
  }
  const pin = genPin()
  let loginId = s.login_id
  let changed = false
  if (want && want !== s.login_id) {
    for (const cand of [want, want + 'b', want + 'c']) {
      const { error: e1 } = await sb.auth.admin.updateUserById(s.user_id, { email: `${cand}@${EMAIL_DOMAIN}`, password: pin, email_confirm: true })
      if (e1) {
        if (/already|registered|exists/i.test(e1.message)) continue
        throw new Error(e1.message)
      }
      const { error: e2 } = await sb.from('ivs_students').update({ login_id: cand }).eq('id', s.id)
      if (e2) {
        await sb.auth.admin.updateUserById(s.user_id, { email: `${s.login_id}@${EMAIL_DOMAIN}` })
        if (/duplicate|unique/i.test(e2.message)) continue
        throw new Error(e2.message)
      }
      loginId = cand
      changed = true
      break
    }
  }
  if (!changed) {
    const { error } = await sb.auth.admin.updateUserById(s.user_id, { password: pin })
    if (error) throw new Error(error.message)
  }
  return { issued: info(loginId, pin), name: s.data?.name || '', note: noteFor(loginId) }
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
  const who = await requireTeacher(sb, request)
  if (who.error) return who.error

  let body
  try { body = await request.json() } catch { return json({ error: '잘못된 요청입니다.' }, 400) }
  const action = body?.action

  try {
    if (action === 'create') {
      if (!(await ownedCourse(sb, body.courseId, who.teacherId))) return json({ error: '내 수업이 아닙니다.' }, 403)
      const { data: students } = await sb.from('ivs_students').select('id, data').eq('course_id', body.courseId).is('user_id', null)
      const code = await schoolCodeOf(sb, body.courseId, who.teacherId)
      const issued = await inBatches(students || [], 5, (s) => issueAccount(sb, s, code))
      return json({ issued })
    }

    if (action === 'reset') {
      const { data: s } = await sb.from('ivs_students').select('id, data, course_id, user_id, login_id').eq('id', body.studentId).maybeSingle()
      if (!s || !(await ownedCourse(sb, s.course_id, who.teacherId))) return json({ error: '내 수업의 학생이 아닙니다.' }, 403)
      const code = await schoolCodeOf(sb, s.course_id, who.teacherId)
      return json({ issued: [(await resetOne(sb, s, code)).issued] })
    }

    // 새 학기: 이 수업 학생 전체의 비밀번호·아이디를 한 번에 새로 만든다. 확인이 필요한 학생(약어·학년반번호 없음, 아이디 겹침, 오류)은 issues 로 따로 돌려준다.
    if (action === 'reset_course') {
      if (!(await ownedCourse(sb, body.courseId, who.teacherId))) return json({ error: '내 수업이 아닙니다.' }, 403)
      const { data: students } = await sb.from('ivs_students').select('id, data, course_id, user_id, login_id').eq('course_id', body.courseId)
      const code = await schoolCodeOf(sb, body.courseId, who.teacherId)
      // 1단계: 아이디가 바뀔 학생은 먼저 임시 아이디로 옮겨 옛 아이디를 비운다(아이디를 서로 맞바꾸는 경우에도 겹치지 않게).
      await inBatches((students || []).filter((s) => s.user_id), 5, async (s) => {
        const want = readableLoginId(code, s.data)
        if (!want || want === s.login_id) return
        const tmp = 'tmp' + genLoginId()
        const { error: e1 } = await sb.auth.admin.updateUserById(s.user_id, { email: `${tmp}@${EMAIL_DOMAIN}` })
        if (e1) return
        const { error: e2 } = await sb.from('ivs_students').update({ login_id: tmp }).eq('id', s.id)
        if (e2) { await sb.auth.admin.updateUserById(s.user_id, { email: `${s.login_id}@${EMAIL_DOMAIN}` }); return }
        s.login_id = tmp
      })
      // 2단계: 비밀번호와 최종 아이디를 새로 정한다.
      const results = await inBatches(students || [], 5, async (s) => {
        try { return await resetOne(sb, s, code) }
        catch (e) { return { issued: null, studentId: s.id, name: s.data?.name || '', note: '오류: ' + (e.message || '처리하지 못했어요') } }
      })
      const issued = results.filter((r) => r.issued).map((r) => r.issued)
      const issues = results.filter((r) => r.note).map((r) => ({ studentId: r.studentId ?? r.issued?.studentId, name: r.name ?? r.issued?.name ?? '', loginId: r.issued?.loginId ?? '', note: r.note }))
      return json({ issued, issues })
    }

    if (action === 'remove_course') {
      if (!(await ownedCourse(sb, body.courseId, who.teacherId))) return json({ error: '내 수업이 아닙니다.' }, 403)
      const { data: students } = await sb.from('ivs_students').select('user_id').eq('course_id', body.courseId).not('user_id', 'is', null)
      // 학생 로그인 계정 삭제 시 그 학생의 프로젝트도 함께 삭제됨 (ON DELETE CASCADE)
      await inBatches(students || [], 5, (s) => sb.auth.admin.deleteUser(s.user_id))
      const { error } = await sb.from('ivs_courses').delete().eq('id', body.courseId)
      if (error) throw new Error(error.message)
      return json({ ok: true })
    }

    return json({ error: '알 수 없는 요청입니다.' }, 400)
  } catch (e) {
    return json({ error: e.message || '처리 중 오류가 발생했습니다.' }, 500)
  }
}
