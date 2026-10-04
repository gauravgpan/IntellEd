import { useEffect, useState } from "react";
import { api } from "../api/client";

/**
 * Review queue for uploaded assignments (design doc sections 6 and 8):
 * extraction never auto-commits, a tutor confirms or corrects each entry
 * first.
 */
export default function SubmissionReview() {
  const [submissions, setSubmissions] = useState(null);
  const [error, setError] = useState("");
  const [drafts, setDrafts] = useState({}); // submissionId -> { itemNo: value }

  function load() {
    api
      .get("/api/submissions/", { status: "needs_review" })
      .then((data) => setSubmissions(data.results || data))
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  function setDraftValue(submissionId, itemNo, value) {
    setDrafts((prev) => ({
      ...prev,
      [submissionId]: { ...prev[submissionId], [itemNo]: value },
    }));
  }

  async function handleConfirm(submission) {
    const draft = drafts[submission.id] || {};
    const entries = submission.entries.map((e) => ({
      item_no: e.item_no,
      confirmed_value: draft[e.item_no] ?? e.confirmed_value ?? e.extracted_value,
    }));
    try {
      await api.post(`/api/submissions/${submission.id}/confirm/`, { entries });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleWaive(submission) {
    const reason = window.prompt("Reason for waiving this student on this handout?") || "";
    try {
      await api.post(`/api/submissions/${submission.id}/waive/`, { reason });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <div className="page form-error">{error}</div>;
  if (!submissions) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <h1>Submissions to review</h1>
      {submissions.length === 0 && <p className="muted">Nothing waiting on review.</p>}

      {submissions.map((s) => (
        <div className="review-card" key={s.id}>
          <h3>{s.student_name || s.student}</h3>
          {s.image_ref ? (
            <a href={s.image_ref} target="_blank" rel="noreferrer">
              View uploaded image
            </a>
          ) : (
            <p className="muted">No image on file.</p>
          )}

          {s.entries.length === 0 && (
            <p className="muted">
              No extracted entries yet (extraction worker not wired up in this skeleton — confirm
              directly, or waive).
            </p>
          )}

          {s.entries.map((e) => (
            <label key={e.item_no} className="entry-row">
              Item {e.item_no}
              <input
                type="text"
                defaultValue={e.extracted_value}
                onChange={(ev) => setDraftValue(s.id, e.item_no, ev.target.value)}
              />
              {e.confidence != null && (
                <span className="muted">conf. {Math.round(e.confidence * 100)}%</span>
              )}
            </label>
          ))}

          <div className="review-actions">
            <button onClick={() => handleConfirm(s)}>Confirm</button>
            <button className="secondary" onClick={() => handleWaive(s)}>
              Waive
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
