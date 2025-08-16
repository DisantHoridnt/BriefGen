import { useState } from 'react'
import type { AgentQuestion } from '../api'

export default function QuestionForm({ q, onSubmit, busy }: {
  q: AgentQuestion, onSubmit: (value: string) => void, busy?: boolean
}) {
  const [value, setValue] = useState('')

  return (
    <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); onSubmit(value); setValue('') }}>
      <div>
        <div className="text-sm text-slate-600 mb-1">{q.field}</div>
        <label className="block text-lg font-medium">{q.text}</label>
        {q.hint && <div className="text-xs text-slate-500 mt-1">{q.hint}</div>}
      </div>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full rounded-xl border p-3"
        rows={5}
        placeholder="Type your answer here..."
        required={!!q.required}
      />
      <button disabled={busy} className="rounded-xl bg-slate-900 text-white px-4 py-2 disabled:opacity-50">
        {busy ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  )
}