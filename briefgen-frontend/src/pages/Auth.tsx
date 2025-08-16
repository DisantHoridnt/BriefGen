import { useState } from "react";
import { api } from "../lib/api";

export default function AuthPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
      e.preventDefault();
      setErr(null);
      setBusy(true);
      try {
        if (mode === "signup") {
          await api("/api/signup", { method: "POST", body: JSON.stringify({ email, password }) });
        } else {
          await api("/api/login", { method: "POST", body: JSON.stringify({ email, password }) });
        }
        window.location.href = "/"; // go to app
      } catch (e: any) {
        setErr(e.message || "Failed");
      } finally {
        setBusy(false);
      }
  }

  return (
    <div style={{ maxWidth: 420, margin: "64px auto", padding: 24, border: "1px solid #ddd", borderRadius: 12 }}>
      <h2 style={{ marginTop: 0 }}>{mode === "signup" ? "Create your account" : "Sign in"}</h2>
      <div style={{ marginBottom: 16 }}>
        <button onClick={() => setMode("signin")} disabled={mode==="signin"}>Sign in</button>{" "}
        <button onClick={() => setMode("signup")} disabled={mode==="signup"}>Sign up</button>
      </div>
      {mode === "signup" && (
        <p style={{ color: "#555", fontSize: 12 }}>
          Sign-up is allowed only for the first user. If someone already signed up, you must sign in.
        </p>
      )}
      <form onSubmit={onSubmit}>
        <label>Email<br/>
          <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} style={{ width: "100%" }}/>
        </label>
        <br/><br/>
        <label>Password<br/>
          <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} style={{ width: "100%" }}/>
        </label>
        <br/><br/>
        <button type="submit" disabled={busy}>{busy ? "Please wait..." : (mode==="signup" ? "Create account" : "Sign in")}</button>
      </form>
      {err && <p style={{ color: "crimson" }}>{err}</p>}
    </div>
  );
}
