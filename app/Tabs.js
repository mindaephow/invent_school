'use client'

import { useRef, useState } from 'react'

// items: [{ id, label, content }]  — content is any React node rendered by the server page
export default function Tabs({ items, label, panelClass = '' }) {
  const [active, setActive] = useState(items[0].id)
  const btnRefs = useRef([])

  function onKeyDown(e, index) {
    let next = null
    if (e.key === 'ArrowRight') next = (index + 1) % items.length
    else if (e.key === 'ArrowLeft') next = (index - 1 + items.length) % items.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = items.length - 1
    if (next === null) return
    e.preventDefault()
    setActive(items[next].id)
    if (btnRefs.current[next]) btnRefs.current[next].focus()
  }

  const current = items.find((t) => t.id === active) || items[0]

  return (
    <div className="tabs-wrap">
      <div className="tablist" role="tablist" aria-label={label}>
        {items.map((t, i) => (
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
      <div
        className={'tabpanel ' + panelClass}
        role="tabpanel"
        id={'panel-' + current.id}
        aria-labelledby={'tab-' + current.id}
        key={current.id}
      >
        {current.content}
      </div>
    </div>
  )
}
