'use client'

import { useEffect, useState } from 'react'

// 로그인 정보는 브라우저 탭(sessionStorage)에 있으므로, 서버가 그리는 랜딩은 마운트 후에 확인해서 버튼을 바꾼다.
function readSession(key) {
  try {
    const raw = window.sessionStorage.getItem(key)
    if (!raw) return null
    const s = JSON.parse(raw)
    if (!s || !s.user) return null
    const alive = (s.expires_at && s.expires_at * 1000 > Date.now()) || !!s.refresh_token
    return alive ? s : null
  } catch (e) {
    return null
  }
}

function detect() {
  const teacher = readSession('ivs-teacher-auth')
  const student = readSession('ivs-student-auth')
  return {
    teacher: !!teacher,
    admin: !!(teacher && teacher.user.app_metadata && teacher.user.app_metadata.role === 'admin'),
    student: !!student,
  }
}

// variant: 'nav' (상단 메뉴 버튼들) | 'hero' (첫 화면 큰 버튼 하나) | 'cta' (맨 아래 큰 버튼들)
export default function LoginLinks({ variant }) {
  const [s, setS] = useState(null)
  useEffect(() => { setS(detect()) }, [])

  const big = variant === 'nav' ? '' : ' big'
  const known = s || { teacher: false, admin: false, student: false }
  const loggedIn = known.teacher || known.student

  let content
  if (variant === 'hero') {
    if (known.teacher) content = <a className="btn primary big" href="/index.html">선생님 화면으로</a>
    else if (known.student) content = <a className="btn primary big" href="/design.html">설계하기로 이어가기</a>
    else content = <a className="btn primary big" href="/design.html">학생 로그인</a>
  } else if (!loggedIn) {
    content = (
      <>
        <a className={'btn' + (variant === 'cta' ? ' primary' : '') + big} href="/design.html">학생 로그인</a>
        <a className={'btn' + big} href="/index.html">선생님 로그인</a>
      </>
    )
  } else {
    content = (
      <>
        {known.teacher && <a className={'btn primary' + big} href="/index.html">선생님 화면</a>}
        {known.admin && <a className={'btn' + big} href="/admin.html">본사 관리자</a>}
        {known.student && <a className={'btn' + (known.teacher ? '' : ' primary') + big} href="/design.html">설계하기</a>}
      </>
    )
  }

  // 확인 전에는 숨겨 두어서 "로그인" 버튼이 잠깐 보였다가 바뀌는 깜빡임을 막는다
  return <span style={{ display: 'contents', visibility: s ? 'visible' : 'hidden' }}>{content}</span>
}
