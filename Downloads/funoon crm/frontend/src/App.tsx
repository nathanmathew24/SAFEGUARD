import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { useAuthStore } from './stores/authStore'
import { AIOps } from './pages/AIOps'
import { Financial } from './pages/Financial'
import { Library } from './pages/Library'
import { Login } from './pages/Login'
import { Pipeline } from './pages/Pipeline'
import { PipelineDeal } from './pages/PipelineDeal'
import { ProjectDetail } from './pages/ProjectDetail'
import { Projects } from './pages/Projects'
import { Settings } from './pages/Settings'
import { Workspace } from './pages/Workspace'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/pipeline" replace />} />
          <Route path="pipeline" element={<Pipeline />} />
          <Route path="pipeline/:id" element={<PipelineDeal />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="ai-ops" element={<AIOps />} />
          <Route path="financial" element={<Financial />} />
          <Route path="library" element={<Library />} />
          <Route path="workspace" element={<Workspace />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
