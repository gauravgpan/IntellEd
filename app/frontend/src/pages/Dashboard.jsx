import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const now = new Date();
    const in7Days = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    api
      .get("/api/sessions/", { status: "scheduled" })
      .then((data) => {
        const items = data.results || data;
        setSessions(
          items
            .filter((s) => {
              const start = new Date(s.starts_at);
              return start >= now && start <= in7Days;
            })
            .slice(0, 10)
        );
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <h1>Welcome, {user?.email}</h1>
      <p className="muted">Upcoming sessions in the next 7 days.</p>

      {error && <p className="form-error">{error}</p>}
      {sessions === null && !error && <p>Loading…</p>}
      {sessions && sessions.length === 0 && <p>Nothing scheduled this week.</p>}

      <ul className="session-list">
        {sessions?.map((s) => (
          <li key={s.id}>
            <Link to={`/classes/${s.school_class}`}>
              <strong>{s.class_label}</strong>
              <span>{new Date(s.starts_at).toLocaleString()}</span>
            </Link>
          </li>
        ))}
      </ul>

      <Link to="/schedule" className="button-link">
        View full schedule
      </Link>
    </div>
  );
}
