import { Link } from 'react-router-dom'

export default function TopNav() {
  return (
    <header className="border-b bg-white/80 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-4xl px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-semibold">BriefGen</Link>
        <nav className="text-sm flex items-center gap-4">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer" className="text-slate-600 hover:text-slate-900">API Docs</a>
        </nav>
      </div>
    </header>
  )
}