import { useState } from "react";

import { api, setTokens } from "../lib/api";
import { Button, Card, Input } from "../components/ui";

export function AuthPage({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ ...form, role: "admin" }) });
      }
      const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.email, password: form.password })
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      onAuthenticated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <p className="text-sm font-semibold text-brand-700">AI Social Media Automation</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-950">{mode === "login" ? "Welcome back" : "Create your workspace"}</h1>
        <form onSubmit={submit} className="mt-6 grid gap-3">
          {mode === "register" ? <Input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /> : null}
          <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
          <Button disabled={loading}>{loading ? "Working..." : mode === "login" ? "Login" : "Register"}</Button>
        </form>
        <button className="mt-4 text-sm font-medium text-brand-700" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Create an account" : "Use an existing account"}
        </button>
      </Card>
    </main>
  );
}
