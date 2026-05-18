import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'

export function Login() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await authApi.post('/login', { username, password })
      login(username)
      navigate('/')
    } catch {
      setError('Invalid credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink-50 flex items-center justify-center">
      <div className="w-full max-w-sm">
        {/* Wordmark */}
        <div className="mb-8">
          <span className="text-lg font-medium text-ink-900 tracking-tight">funoon</span>
          <span className="ml-1.5 text-xs text-ink-400 font-normal">crm</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-ink-500 mb-1" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white border border-ink-200 rounded-md text-ink-800 placeholder-ink-400
                         focus:outline-none focus:ring-1 focus:ring-ink-400 focus:border-ink-400 transition-colors"
              placeholder="farzeel"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-ink-500 mb-1" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white border border-ink-200 rounded-md text-ink-800 placeholder-ink-400
                         focus:outline-none focus:ring-1 focus:ring-ink-400 focus:border-ink-400 transition-colors"
              required
            />
          </div>

          {error && (
            <p className="text-xs text-status-red">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-1 px-3 py-2 text-sm font-medium bg-ink-900 text-white rounded-md
                       hover:bg-ink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
