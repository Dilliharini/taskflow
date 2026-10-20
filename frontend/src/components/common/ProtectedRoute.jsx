import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="grid min-h-[60vh] place-items-center text-slate-300" role="status">Loading your account…</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace state={{ from: location }} />;
}