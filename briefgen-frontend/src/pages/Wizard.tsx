import { useEffect, useState } from 'react'
import TemplatePicker from '../components/TemplatePicker'
import QuestionForm from '../components/QuestionForm'
import FinalView from '../components/FinalView'
import { getTemplates, createDraft } from '../api'
import { useAgentFlow } from '../store'

export default function Wizard() {
  const [templates, setTemplates] = useState<string[] | null>(null)
  const [draftId, setDraftId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { state, loading, error: flowError, answer } = useAgentFlow(draftId)

  useEffect(() => {
    (async () => {
      try {
        setTemplates(await getTemplates())
      } catch (e: any) {
        setTemplates(['Legal Notice', 'Petition', 'Affidavit'])
      }
    })()
  }, [])

  async function start(template: string) {
    setError(null)
    try {
      const id = await createDraft(template)
      setDraftId(id)
    } catch (e: any) {
      setError(e?.message || 'Failed to create draft')
    }
  }

  return (
    <div className="space-y-6">
      {!draftId && (
        <>
          <h1 className="text-2xl font-semibold">Create a new legal document</h1>
          <p className="text-slate-600">Pick a template and answer a few questions. The AI agent will generate a complete draft you can export as .docx.</p>
          {templates ? (
            <TemplatePicker templates={templates} onPick={start} />
          ) : (
            <div>Loading templates…</div>
          )}
          {error && <div className="text-red-600 text-sm">{error}</div>}
        </>
      )}

      {draftId && (
        <div className="space-y-4">
          <div className="text-sm text-slate-600">Draft: <span className="font-mono">{draftId}</span></div>
          {flowError && <div className="text-red-600 text-sm">{flowError}</div>}

          {!state && <div>Loading…</div>}

          {state?.type === 'question' && (
            <QuestionForm q={state.question} onSubmit={(val) => answer(state.question.field, val)} busy={loading} />
          )}

          {state?.type === 'final' && (
            <FinalView draftId={draftId} data={state.draft} />
          )}
        </div>
      )}
    </div>
  )
}