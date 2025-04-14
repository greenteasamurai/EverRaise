import React, { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout.jsx'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import Integrations from './pages/Integrations'
import ReportGeneration from './pages/ReportGeneration'
import KnowledgeSummary from './pages/KnowledgeSummary'
import Settings from './pages/Settings'
import SystemStatus from './pages/SystemStatus'
import NotFound from './pages/NotFound'
// Import from .jsx files
import Login from './pages/Login.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import './styles/globals.css'
import './styles/index.css'

function App() {
  useEffect(() => {
    console.log('App component mounted');
    
    // Check if styles are loaded
    const hasStyles = document.querySelectorAll('style').length > 0;
    console.log('Styles loaded:', hasStyles);
    
    // Log any potential errors
    window.onerror = (message, source, lineno, colno, error) => {
      console.error('Caught error:', { message, source, lineno, colno, error });
      return false;
    };
  }, []);

  console.log('App rendering');
  return (
    <Routes>
      {/* Add login route outside of the protected routes */}
      <Route path="/login" element={<Login />} />
      
      {/* Protect all app routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="reports" element={<Reports />} />
          <Route path="report-generation" element={<ReportGeneration />} />
          <Route path="knowledge-summary" element={<KnowledgeSummary />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="settings" element={<Settings />} />
          <Route path="system-status" element={<SystemStatus />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
    </Routes>
  )
}

export default App 