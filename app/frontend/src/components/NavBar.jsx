import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function NavBar() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const isFounderOrAdmin = user.role === "founder" || user.role === "admin";

  return (
    <nav className="navbar">
      <div className="navbar-brand">ThinkTurf</div>
      <div className="navbar-links">
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/schedule">Schedule</NavLink>
        <NavLink to="/submissions">Submissions</NavLink>
        {isFounderOrAdmin && <NavLink to="/tutors">Tutors</NavLink>}
      </div>
      <div className="navbar-user">
        <span>
          {user.email} · {user.role}
        </span>
        <button onClick={logout}>Log out</button>
      </div>
    </nav>
  );
}
