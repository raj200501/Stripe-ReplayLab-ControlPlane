import { Link } from 'react-router-dom'

export const navItems = [
  'overview','scenario-library','scenario-builder','run-explorer','run-detail','live-replay','findings','diff-viewer','merchant-sandbox','settings'
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="layout">
      <aside>
        <h1>ReplayLab</h1>
        <nav>
          {navItems.map((item) => (
            <Link key={item} to={`/${item}`}>{item.replace('-', ' ')}</Link>
          ))}
        </nav>
      </aside>
      <main>{children}</main>
    </div>
  )
}
