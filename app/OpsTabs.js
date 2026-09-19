'use client'

import { useRef, useState } from 'react'

const TABS = [
  { id: 'type', label: '수업 형태', chips: ['특강형', '방과후형'] },
  {
    id: 'after',
    label: '방과후 운영',
    rows: [
      ['분기제', '12회 × 4분기'],
      ['학기제', '24회 × 2학기'],
      ['방학', '방학특강'],
    ],
  },
  { id: 'place', label: '진행 장소', chips: ['방과후', '문화센터'] },
  { id: 'level', label: '수업 대상', chips: ['초등', '중등', '고등', '대학', '기업'] },
]

export default function OpsTabs() {
  const [active, setActive] = useState(TABS[0].id)
  const btnRefs = useRef([])

  function onKeyDown(e, index) {
    let next = null
    if (e.key === 'ArrowRight') next = (index + 1) % TABS.length
    else if (e.key === 'ArrowLeft') next = (index - 1 + TABS.length) % TABS.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = TABS.length - 1
    if (next === null) return
    e.preventDefault()
    setActive(TABS[next].id)
    btnRefs.current[next] && btnRefs.current[next].focus()
  }

  const tab = TABS.find((t) => t.id === active)

  return (
    <div className="tabs-wrap">
      <div className="tablist" role="tablist" aria-label="수업 운영 안내">
        {TABS.map((t, i) => (
          <button
            key={t.id}
            ref={(el) => (btnRefs.current[i] = el)}
            role="tab"
            id={'tab-' + t.id}
            aria-selected={active === t.id}
            aria-controls={'panel-' + t.id}
            tabIndex={active === t.id ? 0 : -1}
            className={'tab' + (active === t.id ? ' on' : '')}
            onClick={() => setActive(t.id)}
            onKeyDown={(e) => onKeyDown(e, i)}
            type="button"
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="tabpanel" role="tabpanel" id={'panel-' + tab.id} aria-labelledby={'tab-' + tab.id} key={tab.id}>
        {tab.chips && (
          <div className="bigchips">
            {tab.chips.map((c) => (
              <span className="bigchip" key={c}>{c}</span>
            ))}
          </div>
        )}
        {tab.rows && (
          <div className="stats">
            {tab.rows.map(([label, value]) => (
              <div className="stat" key={label}>
                <div className="stat-label">{label}</div>
                <div className="stat-value">{value}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
