import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api'

export default function Login() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      await login(password)
      nav('/wizard')
    } catch (e: any) {
      setError(e?.message || 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-semibold mb-4">Admin Login</h1>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-xl border p-3"
          placeholder="Enter admin password"
          required
        />
        <button className="w-full rounded-xl bg-slate-900 text-white px-4 py-2 disabled:opacity-50" disabled={busy}>
          {busy ? 'Signing in...' : 'Sign in'}
        </button>
        {error && <div className="text-red-600 text-sm">{error}</div>}
      </form>
    </div>
  )
}