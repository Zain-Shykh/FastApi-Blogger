import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Avatar from './Avatar'
import Button from './Button'

function navClass({ isActive }) {
  return `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
  }`
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    setMenuOpen(false)
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg text-brand-700">
            <span className="text-2xl leading-none">📓</span>
            FastAPI Blogger
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            <NavLink to="/" className={navClass} end>
              Home
            </NavLink>
            {user?.is_admin && (
              <NavLink to="/admin" className={navClass}>
                Admin
              </NavLink>
            )}
            {user && (
              <Button to="/posts/new" size="sm" className="ml-2">
                + New Post
              </Button>
            )}
            {user ? (
              <>
                <NavLink to="/settings" className={navClass}>
                  Settings
                </NavLink>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  Log out
                </button>
                <Link to={`/users/${user.id}`} className="ml-1 shrink-0">
                  <Avatar user={user} size="sm" />
                </Link>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>
                  Log in
                </NavLink>
                <Button to="/register" size="sm" className="ml-1">
                  Sign up
                </Button>
              </>
            )}
          </nav>

          {/* Mobile menu toggle */}
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="md:hidden p-2 rounded-md text-slate-600 hover:bg-slate-100"
            aria-label="Toggle menu"
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <nav className="md:hidden border-t border-slate-200 px-4 py-3 flex flex-col gap-1 bg-white">
            <NavLink to="/" className={navClass} end onClick={() => setMenuOpen(false)}>
              Home
            </NavLink>
            {user?.is_admin && (
              <NavLink to="/admin" className={navClass} onClick={() => setMenuOpen(false)}>
                Admin
              </NavLink>
            )}
            {user ? (
              <>
                <NavLink to="/posts/new" className={navClass} onClick={() => setMenuOpen(false)}>
                  New Post
                </NavLink>
                <NavLink to={`/users/${user.id}`} className={navClass} onClick={() => setMenuOpen(false)}>
                  {user.username}
                </NavLink>
                <NavLink to="/settings" className={navClass} onClick={() => setMenuOpen(false)}>
                  Settings
                </NavLink>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-3 py-2 rounded-md text-sm font-medium text-left text-slate-600 hover:bg-slate-100"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass} onClick={() => setMenuOpen(false)}>
                  Log in
                </NavLink>
                <NavLink to="/register" className={navClass} onClick={() => setMenuOpen(false)}>
                  Sign up
                </NavLink>
              </>
            )}
          </nav>
        )}
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-8 text-center text-sm text-slate-400">
        Built with FastAPI + React · FastAPI Blogger
      </footer>
    </div>
  )
}
