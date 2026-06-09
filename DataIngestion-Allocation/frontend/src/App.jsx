import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getIncident, initDemoMode } from './services/api';

import PublicLayout from './layouts/PublicLayout';
import AdminLayout from './layouts/AdminLayout';
import ProtectedRoute from './components/ProtectedRoute';
import { ToastProvider } from './components/ToastProvider';

import IncidentSetupPage from './pages/IncidentSetupPage';
import PublicDashboard from './pages/PublicDashboard';
import ContributePage from './pages/ContributePage';
import AdminDashboard from './pages/AdminDashboard';
import NewIncidentPage from './pages/NewIncidentPage';
import AuditLogPage from './pages/AuditLogPage';
import AdminLogin from './pages/AdminLogin';
import NotFound from './pages/NotFound';
import LogisticsMap from './pages/LogisticsMap';

// Protected wrapper that checks for incident
function IncidentProtectedRoute({ children }) {
  const incident = getIncident();
  
  if (!incident) {
    return <Navigate to="/setup" replace />;
  }
  
  return children;
}

function App() {
  useEffect(() => {
    // Initialize demo mode from localStorage on app startup
    initDemoMode();
  }, []);

  return (
    <ToastProvider>
      <Router>
        <Routes>
          {/* Incident Setup */}
          <Route path="/setup" element={<IncidentSetupPage />} />

          {/* Public Routes - Protected by incident check */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={
              <IncidentProtectedRoute>
                <PublicDashboard />
              </IncidentProtectedRoute>
            } />
            <Route path="/contribute" element={<ContributePage />} />
            <Route path="/contribute/:needCardId" element={<ContributePage />} />
          </Route>

          {/* Admin Login Route */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* Protected Admin Routes */}
          <Route path="/admin" element={<ProtectedRoute />}>
            <Route element={<AdminLayout />}>
              <Route index element={<AdminDashboard />} />
              <Route path="new-incident" element={<NewIncidentPage />} />
              <Route path="map" element={<LogisticsMap />} />
              {/* Placeholder routes for layout links */}
              <Route path="audit-log" element={<AuditLogPage />} />
            </Route>
          </Route>

          {/* 404 Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
}

export default App;
