import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function Schedule() {
  const [sessions, setSessions] = useState(null);
  const [query, setQuery] = useState("");
  const [classResults, setClassResults] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/sessions/")
      .then((data) => setSessions(data.results || data))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setClassResults(null);
      return;
    }
    const handle = setTimeout(() => {
      api
        .get("/api/classes/", { search: query })
        .then((data) => setClassResults(data.results || data))
        .catch((err) => setError(err.message));
    }, 300);
    return () => clearTimeout(handle);
  }, [query]);

  return (
    <div className="page">
      <h1>Schedule</h1>

      <input
        type="search"
        placeholder="Search a class — school, grade or section…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="search-input"
      />

      {error && <p className="form-error">{error}</p>}

      {classResults && (
        <>
          <h2>Classes</h2>
          {classResults.length === 0 && <p className="muted">No matching classes.</p>}
          <ul className="session-list">
            {classResults.map((c) => (
              <li key={c.id}>
                <Link to={`/classes/${c.id}`}>
                  <strong>{c.school_name}</strong>
                  <span>
                    Grade {c.grade}
                    {c.section} · {c.academic_year}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2>Sessions</h2>
      {sessions === null && <p>Loading…</p>}
      {sessions && sessions.length === 0 && <p className="muted">No sessions yet.</p>}
      <ul className="session-list">
        {sessions?.map((s) => (
          <li key={s.id}>
            <Link to={`/classes/${s.school_class}`}>
              <strong>{s.class_label}</strong>
              <span>
                {new Date(s.starts_at).toLocaleString()} · {s.status}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
