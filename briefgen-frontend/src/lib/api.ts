// src/lib/api.ts
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function api(path: string, init: RequestInit = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    credentials: "include", // send/receive the auth cookie
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    ...init,
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(text || `${resp.status} ${resp.statusText}`);
  }
  const ct = resp.headers.get("content-type") || "";
  return ct.includes("application/json") ? resp.json() : resp.text();
}
