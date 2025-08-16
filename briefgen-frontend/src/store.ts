import { useEffect, useState } from 'react'
import { agentNext, AgentResponse } from './api'

export function useAgentFlow(draftId: string | null) {
  const [state, setState] = useState<AgentResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!draftId) return
    let cancelled = false
    const run = async () => {
      try {
        setLoading(true); setError(null)
        const resp = await agentNext(draftId)
        if (!cancelled) setState(resp)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Failed to load')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [draftId])

  async function answer(field: string, text: any) {
    if (!draftId) return
    setLoading(true); setError(null)
    try {
      const resp = await agentNext(draftId, { field, text })
      setState(resp)
    } catch (e: any) {
      setError(e?.message || 'Failed to answer')
    } finally {
      setLoading(false)
    }
  }

  return { state, loading, error, answer }
}