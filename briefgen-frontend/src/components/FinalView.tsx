import { exportDocx } from '../api'

export default function FinalView({ draftId, data }: { draftId: string, data: any }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-xl font-semibold">Final Draft</h2>
        <button onClick={() => exportDocx(draftId)} className="rounded-xl bg-emerald-600 text-white px-4 py-2">
          Download .docx
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="text-sm text-slate-500 mb-2">Title</div>
        <div className="font-medium">{data.title}</div>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        <section className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="font-semibold mb-2">Parties</div>
          <ul className="list-disc list-inside space-y-1">
            {(data.parties || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
          </ul>
        </section>
        <section className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="font-semibold mb-2">Grounds</div>
          <ul className="list-disc list-inside space-y-1">
            {(data.grounds || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="font-semibold mb-2">Facts</div>
        <ul className="list-disc list-inside space-y-1">
          {(data.facts || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
        </ul>
      </section>

      <section className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="font-semibold mb-2">Prayer</div>
        <ul className="list-disc list-inside space-y-1">
          {(data.prayer || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
        </ul>
      </section>

      <div className="grid sm:grid-cols-2 gap-3">
        <section className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="font-semibold mb-2">Annexures</div>
          <ul className="list-disc list-inside space-y-1">
            {(data.annexures || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
          </ul>
        </section>
        <section className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="font-semibold mb-2">Citations</div>
          <ul className="list-disc list-inside space-y-1">
            {(data.citations || []).map((p: string, i: number) => <li key={i}>{p}</li>)}
          </ul>
        </section>
      </div>

      <section className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="font-semibold mb-2">Notes</div>
        <pre className="whitespace-pre-wrap text-sm">{String(data.notes ?? '')}</pre>
      </section>
    </div>
  )
}