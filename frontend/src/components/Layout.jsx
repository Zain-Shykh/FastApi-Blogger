import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function navClass({ isActive }) {
  return `px-3 py-2 rounded-md text-sm font-medium ${
    isActive ? 'bg-brand-100 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
  }`
}

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
          <Link to="/" className="font-semibold text-lg text-brand-700">
            FastAPI Blogger
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/" className={navClass} end>
              Home
            </NavLink>
            {user && (
              <NavLink to="/posts/new" className={navClass}>
                New Post
              </NavLink>
            )}
            {user?.is_admin && (
              <NavLink to="/admin" className={navClass}>
                Admin
              </NavLink>
            )}
            {user ? (
              <>
                <NavLink to={`/users/${user.id}`} className={navClass}>
                  {user.username}
                </NavLink>
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
              </>
            ) : (
              <>
                <NavLink to="/login" className={navClass}>
                  Log in
                </NavLink>
                <NavLink to="/register" className={navClass}>
                  Sign up
                </NavLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-400">
        FastAPI Blogger
      </footer>
    </div>
  )
}
