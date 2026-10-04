import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";

const STATUS_LABEL = { to_do: "To do", in_progress: "In progress", done: "Done" };

export default function ClassView() {
  const { classId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(`/api/classes/${classId}/class-view/`)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [classId]);

  if (error) return <div className="page form-error">{error}</div>;
  if (!data) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <h1>{data.label}</h1>
      <p className="muted">Strength: {data.strength}</p>

      <section>
        <h2>Handouts</h2>
        {data.handouts.length === 0 && <p className="muted">No lesson plan set for this class yet.</p>}
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Lesson</th>
              <th>Status</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {data.handouts.map((h) => (
              <tr key={h.handout_id}>
                <td>{h.seq_no}</td>
                <td>{h.lesson_header}</td>
                <td>
                  <span className={`badge badge-${h.status}`}>{STATUS_LABEL[h.status]}</span>
                </td>
                <td>
                  {h.confirmed} of {h.total} submitted
                  {h.waived > 0 && `, ${h.waived} waived`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Roster</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Handouts submitted</th>
            </tr>
          </thead>
          <tbody>
            {data.roster.map((s) => (
              <tr key={s.student_token}>
                <td>
                  <Link to={`/students/${s.student_token}`}>{s.display_name || s.student_token}</Link>
                </td>
                <td>
                  {s.handouts_submitted} of {s.handouts_planned}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
