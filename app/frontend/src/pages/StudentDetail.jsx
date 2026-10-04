import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

export default function StudentDetail() {
  const { studentToken } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(`/api/reports/student/${studentToken}/`)
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [studentToken]);

  if (error) return <div className="page form-error">{error}</div>;
  if (!report) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <h1>{report.display_name || "Student"}</h1>
      <p className="muted">{report.school_class}</p>

      <section>
        <h2>Attendance</h2>
        <p>
          Present {report.attendance.present} of {report.attendance.sessions_recorded} recorded sessions.
        </p>
      </section>

      <section>
        <h2>Latest cognitive snapshot</h2>
        {!report.latest_cognitive_snapshot && <p className="muted">No completed assessment yet.</p>}
        {report.latest_cognitive_snapshot && (
          <>
            <p className="muted">
              Cycle {report.latest_cognitive_snapshot.cycle_no} ·{" "}
              {new Date(report.latest_cognitive_snapshot.completed_at).toLocaleDateString()}
            </p>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Domain</th>
                  <th>Score</th>
                  <th>Band</th>
                </tr>
              </thead>
              <tbody>
                {report.latest_cognitive_snapshot.domain_scores.map((d) => (
                  <tr key={d.domain}>
                    <td>{d.domain}</td>
                    <td>{d.raw_score}</td>
                    <td>{d.band_label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      <section>
        <h2>Performance notes</h2>
        {report.performance_notes.length === 0 && <p className="muted">No notes yet.</p>}
        <ul className="note-list">
          {report.performance_notes.map((n, i) => (
            <li key={i}>
              <span className="muted">{new Date(n.created_at).toLocaleDateString()}</span>
              <p>{n.note}</p>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Handouts</h2>
        <ul className="note-list">
          {report.handouts.map((h) => (
            <li key={h.handout_id}>{h.status}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
