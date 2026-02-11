import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { navItems } from './Layout'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (!open) return null
  return (
    <div data-testid="command-palette" className="palette">
      {navItems.map((item) => (
        <button key={item} onClick={() => { navigate(`/${item}`); setOpen(false) }}>
          {item}
        </button>
      ))}
    </div>
  )
}
