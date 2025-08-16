type Props = {
  templates: string[]
  onPick: (name: string) => void
  disabled?: boolean
}

export default function TemplatePicker({ templates, onPick, disabled }: Props) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-3">Choose a template</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {templates.map(t => (
          <button key={t}
            disabled={disabled}
            onClick={() => onPick(t)}
            className="rounded-xl border bg-white p-4 text-left shadow-sm hover:shadow transition disabled:opacity-50">
            <div className="font-medium">{t}</div>
            <div className="text-xs text-slate-600 mt-1">Generate a {t} with the AI assistant.</div>
          </button>
        ))}
      </div>
    </div>
  )
}