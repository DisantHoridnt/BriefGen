import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Wizard from './pages/Wizard'
import TopNav from './components/TopNav'
import AuthPage from "./pages/Auth";

export default function App() {
  return (
    <div className="min-h-screen text-slate-900">
      <TopNav />
      <div className="mx-auto max-w-4xl p-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/wizard" element={<Wizard />} />
          <Route path="/" element={<Navigate to="/wizard" replace />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  )
}