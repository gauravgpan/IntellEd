import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Gates a route behind login, and optionally behind a set of roles.
 * Usage: <Route element={<ProtectedRoute roles={["founder","admin"]} />}>...</Route>
 */
export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="page-loading">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;

  return <Outlet />;
}
