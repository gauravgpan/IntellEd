// Thin fetch wrapper: adds the auth token, the JSON content type, and turns
// a non-2xx response into a thrown error the pages can display.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

function getToken() {
  return localStorage.getItem("thinkturf_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("thinkturf_token", token);
  else localStorage.removeItem("thinkturf_token");
}

async function request(path, { method = "GET", body, params } = {}) {
  let url = `${BASE_URL}${path}`;
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
    ).toString();
    if (qs) url += `?${qs}`;
  }

  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Token ${token}`;

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message = (data && (data.detail || JSON.stringify(data))) || res.statusText;
    throw new Error(message);
  }
  return data;
}

export const api = {
  get: (path, params) => request(path, { method: "GET", params }),
  post: (path, body) => request(path, { method: "POST", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  del: (path) => request(path, { method: "DELETE" }),
};
