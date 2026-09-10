import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { api, TOKEN_COOKIE } from './api'
import { deleteCookie, getCookie, setCookie } from './cookies'

const USER_KEY = 'spacematch_user'

const AuthContext = createContext(null)

/**
 * The API contract has no `GET /me`, so the user object returned by
 * register/login is cached next to the token. On reload we trust the pair;
 * if the token has actually expired the next API call returns 401 and the
 * caller signs out.
 */
function readStoredUser() {
  if (!getCookie(TOKEN_COOKIE)) return null
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser)

  const persist = useCallback(({ token, user: nextUser }) => {
    setCookie(TOKEN_COOKIE, token)
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
    return nextUser
  }, [])

  const login = useCallback(
    async (credentials) => persist(await api.login(credentials)),
    [persist]
  )

  const register = useCallback(
    async (payload) => persist(await api.register(payload)),
    [persist]
  )

  const logout = useCallback(() => {
    deleteCookie(TOKEN_COOKIE)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isAuthed: Boolean(user),
      isOwner: user?.role === 'owner',
      isBooker: user?.role === 'booker',
      login,
      register,
      logout,
    }),
    [user, login, register, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
