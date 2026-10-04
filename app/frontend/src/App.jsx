import { Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import ClassView from "./pages/ClassView";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Schedule from "./pages/Schedule";
import StudentDetail from "./pages/StudentDetail";
import SubmissionReview from "./pages/SubmissionReview";
import TutorOnboarding from "./pages/TutorOnboarding";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <div className="page-loading">Loading…</div>;

  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/classes/:classId" element={<ClassView />} />
          <Route path="/students/:studentToken" element={<StudentDetail />} />
          <Route path="/submissions" element={<SubmissionReview />} />
        </Route>

        <Route element={<ProtectedRoute roles={["founder", "admin"]} />}>
          <Route path="/tutors" element={<TutorOnboarding />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
