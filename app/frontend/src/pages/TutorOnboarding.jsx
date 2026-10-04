import { useEffect, useState } from "react";
import { api } from "../api/client";

const ACTIONS = {
  applied: [{ action: "verify", label: "Mark verified" }],
  verified: [{ action: "approve", label: "Approve (make Active)" }],
  active: [{ action: "suspend", label: "Suspend" }],
  suspended: [{ action: "reactivate", label: "Reactivate" }],
  inactive: [{ action: "reactivate", label: "Reactivate" }],
};

export default function TutorOnboarding() {
  const [tutors, setTutors] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ full_name: "", email: "", phone: "" });

  function load() {
    api
      .get("/api/auth/tutors/")
      .then((data) => setTutors(data.results || data))
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.post("/api/auth/tutors/", form);
      setForm({ full_name: "", email: "", phone: "" });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAction(tutorId, action) {
    try {
      await api.post(`/api/auth/tutors/${tutorId}/${action}/`, {});
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h1>Tutors</h1>
      {error && <p className="form-error">{error}</p>}

      <form onSubmit={handleCreate} className="inline-form">
        <input
          placeholder="Full name"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          placeholder="Phone"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />
        <button type="submit">Add tutor</button>
      </form>

      {tutors === null && <p>Loading…</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>State</th>
            <th>Background check</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {tutors?.map((t) => (
            <tr key={t.user.id}>
              <td>{t.full_name}</td>
              <td>{t.user.email}</td>
              <td>{t.lifecycle_state}</td>
              <td>{t.background_check_status}</td>
              <td>
                {(ACTIONS[t.lifecycle_state] || []).map(({ action, label }) => (
                  <button key={action} onClick={() => handleAction(t.user.id, action)}>
                    {label}
                  </button>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
