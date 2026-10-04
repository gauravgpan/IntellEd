import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { requestOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState("identifier"); // "identifier" | "code"
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleRequestOtp(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await requestOtp(identifier);
      setStep("code");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleVerifyOtp(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await verifyOtp(identifier, code);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <h1>ThinkTurf</h1>
      <p className="login-subtitle">Tutor and admin sign-in</p>

      {step === "identifier" && (
        <form onSubmit={handleRequestOtp}>
          <label>
            Email or phone
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="you@school.org or phone"
              required
            />
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Sending…" : "Send code"}
          </button>
        </form>
      )}

      {step === "code" && (
        <form onSubmit={handleVerifyOtp}>
          <p>
            Code sent to <strong>{identifier}</strong>.
          </p>
          <label>
            6-digit code
            <input
              type="text"
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={6}
              required
            />
          </label>
          <button type="submit" disabled={busy}>
            {busy ? "Verifying…" : "Verify and sign in"}
          </button>
          <button type="button" className="link-button" onClick={() => setStep("identifier")}>
            Use a different email/phone
          </button>
        </form>
      )}

      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
