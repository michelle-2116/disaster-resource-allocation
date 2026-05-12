import { Navigate, Outlet } from 'react-router-dom';

export default function ProtectedRoute() {
  const pin = localStorage.getItem('aria_pin');
  
  // Guarded by simple localStorage PIN check: "aria2026"
  if (pin !== 'aria2026') {
    return <Navigate to="/admin/login" replace />;
  }

  return <Outlet />;
}
