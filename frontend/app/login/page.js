"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { login } from "@/lib/apiClient";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setBusy(true);

    try {
      const response = await login(form);
      if (response?.success && response?.data?.token) {
        localStorage.setItem("auth_token", response.data.token);
        localStorage.setItem("auth_user", JSON.stringify(response.data.user));
        router.push("/");
      } else {
        setError(response?.message || "Falha ao autenticar.");
      }
    } catch (err) {
      setError(err.message || "Falha ao autenticar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="module-shell">
      <nav className="top-nav" aria-label="Navegacao principal">
        <Link className="nav-chip" href="/">
          Hub
        </Link>
      </nav>

      <header className="hero-panel">
        <span className="kicker">Acesso ao sistema</span>
        <h1>Login</h1>
        <p>Informe suas credenciais para acessar o sistema.</p>
      </header>

      <main className="layout-grid" style={{ maxWidth: "420px", margin: "0 auto" }}>
        <section className="surface-card">
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              E-mail
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busy}>
              {busy ? "Entrando..." : "Entrar"}
            </button>
          </form>

          {error && <div className="result-box error">{error}</div>}

          <p style={{ marginTop: "1rem", fontSize: "0.875rem" }}>
            Sem conta?{" "}
            <Link href="/registro" style={{ color: "var(--color-accent, #6366f1)" }}>
              Cadastre-se
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
