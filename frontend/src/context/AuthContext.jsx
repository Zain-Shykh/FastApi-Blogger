import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { getMe, login as apiLogin } from '../api/auth'

const AuthContext = createContext(null)
const TOKEN_KEY = 'blog_token'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async (currentToken) => {
    if (!currentToken) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await getMe(currentToken)
      setUser(me)
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser(token)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function login(email, password) {
    const accessToken = await apiLogin({ email, password })
    localStorage.setItem(TOKEN_KEY, accessToken)
    setToken(accessToken)
    await loadUser(accessToken)
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  async function refreshUser() {
    if (token) await loadUser(token)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, refreshUser, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
