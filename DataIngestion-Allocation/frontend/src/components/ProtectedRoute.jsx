import { Navigate, Outlet } from 'react-router-dom';

export default function ProtectedRoute({ allowedRoles }) {
  const pin = localStorage.getItem('aria_pin');
  const role = localStorage.getItem('user_role');
  
  // If no auth token is present, redirect to the unified login page
  if (!pin) {
    return <Navigate to="/login" replace />;
  }
  
  // If the user's role is not authorized for this route, redirect to their home dashboard
  if (allowedRoles && !allowedRoles.includes(role)) {
    if (role === 'admin') {
      return <Navigate to="/admin/dashboard" replace />;
    } else if (role === 'volunteer') {
      return <Navigate to="/volunteer/dashboard" replace />;
    } else {
      return <Navigate to="/login" replace />;
    }
  }

  return <Outlet />;
}

