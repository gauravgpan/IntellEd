import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("thinkturf_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me/")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function requestOtp(identifier) {
    await api.post("/api/auth/otp/request/", { identifier });
  }

  async function verifyOtp(identifier, code) {
    const data = await api.post("/api/auth/otp/verify/", { identifier, code });
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, requestOtp, verifyOtp, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
